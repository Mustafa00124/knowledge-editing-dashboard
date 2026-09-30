"""Queue retry behavior without submitting real SLURM jobs."""
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


class RerunFailedTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db_path = Path(self.temp.name) / "queue.db"
        self.patch_db = patch.object(main.db.config, "DB_PATH", self.db_path)
        self.patch_db.start()
        self.addCleanup(self.patch_db.stop)
        main.db.init()
        self.out_root = str(Path(self.temp.name) / "results")
        self.config = {
            "name": "run_experiment",
            "fields": [{"name": "method"}, {"name": "seed"}],
            "out_root": self.out_root,
        }
        self.states = {"101": "COMPLETED", "102": "FAILED", "103": "OUT_OF_MEMORY"}
        self.submissions = []

        def fake_submit(exp_cfg, params, run_name, out_root):
            job_id = str(201 + len(self.submissions))
            self.submissions.append((dict(params), run_name, out_root))
            self.states[job_id] = "PENDING"
            return {
                "job_id": job_id, "run_name": run_name, "params": params,
                "sbatch_path": "fake.sbatch", "out_path": "fake.out", "err_path": "fake.err",
            }

        self.patch_registry = patch.object(main.registry, "get_experiment_type", return_value=self.config)
        self.patch_status = patch.object(main.slurm, "sacct_status", side_effect=lambda job_id: {"state": self.states[str(job_id)]})
        self.patch_submit = patch.object(main.slurm, "submit_exact", side_effect=fake_submit)
        for p in (self.patch_registry, self.patch_status, self.patch_submit):
            p.start()
            self.addCleanup(p.stop)

    def add_job(self, job_id, seed, testing_id=None):
        main.db.insert_job(
            job_id=job_id, experiment_type="run_experiment",
            run_name=f"ft_model_seed{seed}", params={"method": "ft", "seed": seed},
            sbatch_path="original.sbatch", out_path="original.out", err_path="original.err",
            out_root=self.out_root if testing_id is None else str(Path(self.temp.name) / "Trial Runs" / testing_id),
            queue_slot=0, testing_id=testing_id,
        )

    def test_only_failed_attempts_are_retried_and_history_remains(self):
        for job_id, seed in (("101", 0), ("102", 1), ("103", 2)):
            self.add_job(job_id, seed)

        result = main.rerun_failed_queue_slot(0)
        self.assertEqual(result["rerun_submitted"], ["201", "202"])
        self.assertEqual([item[0]["seed"] for item in self.submissions], [1, 2])
        self.assertEqual(result["status"], "running")
        jobs = {job["job_id"]: job for job in result["jobs"]}
        self.assertIsNone(jobs["101"]["retried_by"])
        self.assertEqual(jobs["102"]["retried_by"], "201")
        self.assertEqual(jobs["103"]["retried_by"], "202")
        self.assertEqual(jobs["201"]["retry_of"], "102")
        self.assertEqual(jobs["202"]["retry_of"], "103")
        self.assertTrue(all(name != jobs[source]["run_name"] for (_, name, _), source in zip(self.submissions, ("102", "103"))))

        with self.assertRaises(HTTPException) as error:
            main.rerun_failed_queue_slot(0)
        self.assertEqual(error.exception.status_code, 409)
        self.assertEqual(len(self.submissions), 2)

        self.states["201"] = self.states["202"] = "COMPLETED"
        self.assertEqual(main._slot_view(0)["status"], "completed")

    def test_trial_retry_uses_new_trial_folder(self):
        self.add_job("102", 1, testing_id="old-trial")
        result = main.rerun_failed_queue_slot(0)
        retry = next(job for job in result["jobs"] if job["job_id"] == "201")
        self.assertNotEqual(retry["testing_id"], "old-trial")
        self.assertIn("Trial Runs", retry["out_root"])
        self.assertEqual(self.submissions[0][2], retry["out_root"])

    def test_partial_submission_keeps_launched_retry_and_unsubmitted_failure(self):
        self.add_job("102", 1)
        self.add_job("103", 2)
        calls = []

        def submit(exp_cfg, params, run_name, out_root):
            calls.append(params["seed"])
            if len(calls) == 2:
                raise RuntimeError("SLURM temporarily unavailable")
            self.states["201"] = "PENDING"
            return {
                "job_id": "201", "run_name": run_name, "params": params,
                "sbatch_path": "fake.sbatch", "out_path": "fake.out", "err_path": "fake.err",
            }

        with patch.object(main.slurm, "submit_exact", side_effect=submit):
            result = main.rerun_failed_queue_slot(0)
        self.assertEqual(calls, [1, 2])
        self.assertEqual(result["rerun_submitted"], ["201"])
        self.assertIn("SLURM temporarily unavailable", result["rerun_error"])
        jobs = {job["job_id"]: job for job in result["jobs"]}
        self.assertEqual(jobs["102"]["retried_by"], "201")
        self.assertIsNone(jobs["103"]["retried_by"])


if __name__ == "__main__":
    unittest.main()
