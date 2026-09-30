"""Queue pause/resume behavior without touching real SLURM jobs."""
import contextlib
import importlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

with contextlib.redirect_stdout(io.StringIO()):
    main = importlib.import_module("main")


class PauseResumeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db_path = Path(self.temp.name) / "queue.db"
        self.db_patch = patch.object(main.db.config, "DB_PATH", self.db_path)
        self.db_patch.start()
        self.addCleanup(self.db_patch.stop)
        main.db.init()

        self.out_root = str(Path(self.temp.name) / "results")
        self.config = {
            "name": "run_experiment",
            "fields": [{"name": "method"}, {"name": "seed"}],
            "out_root": self.out_root,
        }
        self.states = {"101": "COMPLETED", "102": "RUNNING", "103": "PENDING"}
        self.submissions = []
        self.cancelled = []

        def fake_submit(exp_cfg, params, run_name, out_root):
            job_id = str(201 + len(self.submissions))
            self.submissions.append((dict(params), run_name, out_root))
            self.states[job_id] = "PENDING"
            return {
                "job_id": job_id, "run_name": run_name, "params": params,
                "sbatch_path": "fake.sbatch", "out_path": "fake.out", "err_path": "fake.err",
            }

        patches = [
            patch.object(main.registry, "get_experiment_type", return_value=self.config),
            patch.object(main.slurm, "sacct_status", side_effect=lambda job_id: {"state": self.states[str(job_id)]}),
            patch.object(main.slurm, "submit_exact", side_effect=fake_submit),
            patch.object(main.slurm, "cancel_many", side_effect=lambda ids: self.cancelled.extend(ids) or ""),
        ]
        for item in patches:
            item.start()
            self.addCleanup(item.stop)

        for job_id, seed in (("101", 0), ("102", 1), ("103", 2)):
            main.db.insert_job(
                job_id=job_id, experiment_type="run_experiment",
                run_name=f"ft_model_seed{seed}", params={"method": "ft", "seed": seed},
                sbatch_path="original.sbatch", out_path="original.out", err_path="original.err",
                out_root=self.out_root, queue_slot=0,
            )

    def test_pause_cancels_only_unfinished_and_play_restarts_only_them(self):
        paused = main.pause_queue_slot(0)
        self.assertEqual(paused["status"], "paused")
        self.assertEqual(self.cancelled, ["102", "103"])
        marked = {job["job_id"] for job in paused["jobs"] if job["pause_requested"]}
        self.assertEqual(marked, {"102", "103"})

        self.states["102"] = self.states["103"] = "CANCELLED"
        resumed = main.resume_queue_slot(0)
        self.assertEqual(resumed["status"], "running")
        self.assertEqual([item[0]["seed"] for item in self.submissions], [1, 2])
        self.assertTrue(all("_resume" in item[1] for item in self.submissions))
        self.assertEqual({job["retry_of"] for job in resumed["jobs"] if job["job_id"] in {"201", "202"}}, {"102", "103"})

    def test_play_waits_until_slurm_has_finished_cancelling(self):
        main.pause_queue_slot(0)
        with self.assertRaises(HTTPException) as error:
            main.resume_queue_slot(0)
        self.assertEqual(error.exception.status_code, 409)
        self.assertIn("still stopping", error.exception.detail)
        self.assertEqual(self.submissions, [])

    def test_cancel_permanently_releases_paused_card(self):
        main.pause_queue_slot(0)
        self.states["102"] = self.states["103"] = "CANCELLED"
        result = main.cancel_queue_slot(0)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(self.submissions, [])

    def test_play_does_not_repeat_a_job_that_finished_during_pause(self):
        main.pause_queue_slot(0)
        self.states["102"] = "COMPLETED"
        self.states["103"] = "CANCELLED"
        result = main.resume_queue_slot(0)
        self.assertEqual([item[0]["seed"] for item in self.submissions], [2])
        self.assertEqual(result["status"], "running")


if __name__ == "__main__":
    unittest.main()
