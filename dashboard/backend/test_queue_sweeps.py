"""Hyperparameter sweeps on GPU queue cards: staged and launched like any
experiment, and rerun or resumed through the sweep so run names and
sweep.json stay intact. No real SLURM jobs."""
import contextlib
import importlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

with contextlib.redirect_stdout(io.StringIO()):
    main = importlib.import_module("main")

DATASET = os.path.join(str(main.config.PROJECT_ROOT), "datasets/KnowEdit/benchmark/wiki_counterfact/test_cf.json")
SPEC = {"investigation": "locate_edit", "design": "one_at_a_time",
        "methods": {"rome": {"v_lr": [0.05, 5.0]}}, "models": ["qwen3-4b"],
        "data_paths": [DATASET], "ds_size": "2", "edit_mode": "single"}


class SweepSlotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.states = {}
        self.submitted = []

        def fake_submit(exp_cfg, params, run_name, out_root, extra_args=None, after_ok=()):
            job_id = str(300 + len(self.submitted))
            self.submitted.append((run_name, list(extra_args or [])))
            self.states[job_id] = "PENDING"
            return {"job_id": job_id, "run_name": run_name, "params": params,
                    "sbatch_path": "x.sbatch", "out_path": "x.out", "err_path": "x.err"}

        def statuses(ids):
            return {str(i): {"state": self.states.get(str(i), "UNKNOWN")} for i in ids}

        patches = [
            patch.object(main.db.config, "DB_PATH", root / "queue.db"),
            patch.object(main.hparam_sweeps.config, "INVESTIGATIONS_DIR", root / "investigations"),
            patch.object(main.slurm, "_submit_one", side_effect=fake_submit),
            patch.object(main.slurm, "sacct_status", side_effect=lambda i: {"state": self.states.get(str(i), "UNKNOWN")}),
            patch.object(main.slurm, "sacct_statuses", side_effect=statuses),
            patch.object(main.hparam_sweeps, "_statuses", side_effect=lambda sweeps: statuses(
                [r["job_id"] for _, s in sweeps for r in s["runs"]])),
        ]
        for item in patches:
            item.start()
            self.addCleanup(item.stop)
        main.db.init()

    def test_stage_then_launch(self):
        staged = main.stage_sweep_on_queue_slot(2, dict(SPEC))
        self.assertEqual(staged["status"], "staged")
        self.assertEqual(staged["staged"]["experiment_type"], main.SWEEP_SLOT_TYPE)
        self.assertEqual(staged["staged"]["params"]["planned_runs"], 3)  # current settings + two values
        self.assertEqual(self.submitted, [])

        launched = main.launch_queue_slot(2)
        self.assertEqual(len(self.submitted), 3)
        self.assertTrue(all("--split dev" in extra for _, extra in self.submitted))
        self.assertEqual({j["queue_slot"] for j in launched["jobs"]}, {2})
        self.assertIsNone(launched["staged"])
        self.assertEqual(launched["status"], "running")

    def test_a_bad_spec_fails_at_staging(self):
        with self.assertRaises(HTTPException) as error:
            main.stage_sweep_on_queue_slot(0, {**SPEC, "investigation": "nope"})
        self.assertEqual(error.exception.status_code, 400)

    def test_rerun_keeps_the_run_name_and_follows_in_sweep_json(self):
        main.stage_sweep_on_queue_slot(1, dict(SPEC))
        main.launch_queue_slot(1)
        first = self.submitted[0][0]
        for job_id in list(self.states):
            self.states[job_id] = "COMPLETED"
        self.states["300"] = "FAILED"
        view = main.rerun_failed_queue_slot(1)
        self.assertEqual(view["rerun_submitted"], ["303"])
        self.assertEqual(self.submitted[-1][0], first)  # same run name, not *_rerun...
        sweep = next(main.hparam_sweeps._sweeps("locate_edit"))[1]
        run = next(r for r in sweep["runs"] if r["run_name"] == first)
        self.assertEqual((run["job_id"], run["earlier_jobs"]), ("303", ["300"]))
        retry = next(j for j in view["jobs"] if j["job_id"] == "303")
        self.assertEqual((retry["queue_slot"], retry["retry_of"]), (1, "300"))


if __name__ == "__main__":
    unittest.main()
