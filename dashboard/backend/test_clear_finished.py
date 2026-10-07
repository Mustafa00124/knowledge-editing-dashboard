"""Clear buttons: finished jobs, sweeps and failures leave the dashboard's
lists but stay recorded (database rows, sweep.json)."""
import contextlib
import importlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

with contextlib.redirect_stdout(io.StringIO()):
    main = importlib.import_module("main")
hparam_sweeps = main.hparam_sweeps


class ClearTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.states = {}
        fake_sacct = lambda ids: {str(i): {"state": self.states.get(str(i), "UNKNOWN")} for i in ids}
        for p in (patch.object(main.db.config, "DB_PATH", root / "dash.db"),
                  patch.object(hparam_sweeps.config, "INVESTIGATIONS_DIR", root / "investigations"),
                  patch.object(main.slurm, "sacct_statuses", side_effect=fake_sacct)):
            p.start()
            self.addCleanup(p.stop)
        main.db.init()

    def add_job(self, job_id, state, experiment_type="causal_tracing", **extra):
        self.states[job_id] = state
        main.db.insert_job(job_id=job_id, experiment_type=experiment_type, run_name=f"run{job_id}", params={},
                           sbatch_path="x", out_path="x.out", err_path="x.err", out_root="x", **extra)

    def add_sweep(self, sweep_id, runs, investigation="edit_layers"):
        sweep_dir = hparam_sweeps.config.INVESTIGATIONS_DIR / investigation / "sweeps" / sweep_id
        sweep_dir.mkdir(parents=True)
        sweep = {"id": sweep_id, "investigation": investigation, "runs": runs}
        (sweep_dir / "sweep.json").write_text(json.dumps(sweep))
        return sweep_dir / "sweep.json"

    def test_only_finished_jobs_of_the_type_are_cleared(self):
        self.add_job("1", "FAILED")
        self.add_job("2", "COMPLETED")
        self.add_job("3", "RUNNING")
        self.add_job("4", "FAILED", experiment_type="neuron_tracing")
        self.add_job("5", "FAILED", sweep_id=hparam_sweeps.SWEEP_PREFIX + "s")

        result = main.clear_experiments("causal_tracing")
        self.assertEqual(result, {"jobs_cleared": 2, "still_active": 1})
        listed = {j["job_id"] for j in main.db.list_jobs()}
        self.assertEqual(listed, {"3", "4", "5"})
        # Still recorded, just not listed.
        self.assertEqual(len(main.db.list_jobs(include_cleared=True)), 5)

    def test_trial_runs_clear_only_finished(self):
        self.add_job("1", "COMPLETED", experiment_type="run_experiment", testing_id="t1")
        self.add_job("2", "PENDING", experiment_type="run_experiment", testing_id="t2")
        self.add_job("3", "COMPLETED", experiment_type="run_experiment")
        self.assertEqual(main.clear_testing_results()["jobs_cleared"], 1)
        self.assertEqual({j["job_id"] for j in main.db.list_jobs()}, {"2", "3"})

    def test_clear_finished_sweeps_leaves_running_ones(self):
        self.states.update({"10": "COMPLETED", "11": "FAILED", "20": "RUNNING"})
        done = self.add_sweep("a", [{"run_name": "r1", "job_id": "10"}, {"run_name": "r2", "job_id": "11"}])
        going = self.add_sweep("b", [{"run_name": "r1", "job_id": "20"}])

        self.assertEqual(main.clear_finished_sweeps("edit_layers"), {"hidden": 1})
        self.assertTrue(json.loads(done.read_text())["hidden"])
        self.assertNotIn("hidden", json.loads(going.read_text()))
        self.assertEqual(main.get_hidden_sweep_count("edit_layers"), {"hidden": 1})

    def test_clearing_failures_marks_the_attempt_and_sets_earlier_ones_aside(self):
        self.states.update({"30": "FAILED", "31": "COMPLETED"})
        path = self.add_sweep("c", [
            {"run_name": "bad", "job_id": "30", "earlier_jobs": ["29"]},
            {"run_name": "fixed", "job_id": "31", "earlier_jobs": ["28"]},
            {"run_name": "fine", "job_id": "32"},
        ])
        listed = {
            "open": [{"investigation": "edit_layers", "sweep_id": "c", "run": "bad", "job_id": "30", "state": "FAILED"}],
            "resolved": [{"investigation": "edit_layers", "sweep_id": "c", "run": "fixed", "job_id": "31", "state": "COMPLETED"}],
        }
        with patch.object(hparam_sweeps, "failures", return_value=listed):
            self.assertEqual(main.clear_sweep_failures(), {"cleared": 2})
        runs = {r["run_name"]: r for r in json.loads(path.read_text())["runs"]}
        self.assertEqual(runs["bad"]["cleared_failures"], ["30"])
        self.assertEqual(runs["bad"]["cleared_earlier_jobs"], ["29"])
        self.assertNotIn("earlier_jobs", runs["bad"])
        self.assertEqual(runs["fixed"]["cleared_earlier_jobs"], ["28"])
        self.assertNotIn("cleared_failures", runs["fine"])

    def test_failures_skip_cleared_runs(self):
        rows = [{"run": "a", "state": "FAILED", "flags": [], "earlier": [], "failure_cleared": True, "baseline_copy": False},
                {"run": "b", "state": "FAILED", "flags": [], "earlier": [], "failure_cleared": False, "baseline_copy": False}]
        with patch.object(hparam_sweeps, "_load_catalog", return_value={"investigations": [{"id": "x", "label": "X"}]}), \
             patch.object(hparam_sweeps, "results", return_value=rows) as results:
            out = hparam_sweeps.failures()
        self.assertEqual([r["run"] for r in out["open"]], ["b"])
        results.assert_called_with("x", include_hidden=False)


if __name__ == "__main__":
    unittest.main()
