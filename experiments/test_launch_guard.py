"""launch_guard: a run outside the dashboard may not write into results/."""
import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import launch_guard as G


class LaunchGuardTests(unittest.TestCase):
    def setUp(self):
        self.results = os.path.join(G.RESULTS_DIR, "investigations", "neuron_tracing")

    def blocked(self, out_root, untracked=False, environ=None):
        try:
            G.require_dashboard(out_root, untracked, "neuron_tracing", environ=environ or {})
        except SystemExit as exc:
            self.assertIn("dash.py launch neuron_tracing", str(exc))
            return True
        return False

    def test_outside_results_is_never_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(self.blocked(tmp))

    def test_results_need_the_dashboard_or_untracked(self):
        with patch.object(G, "DB_PATH", "/nonexistent.db"):
            self.assertTrue(self.blocked(self.results))
            self.assertTrue(self.blocked(G.RESULTS_DIR))
            self.assertFalse(self.blocked(self.results, untracked=True))
            self.assertFalse(self.blocked(self.results, environ={"KE_DASHBOARD_JOB": "1"}))
            self.assertTrue(self.blocked(self.results, environ={"SLURM_JOB_ID": "123"}))

    def test_jobs_the_dashboard_recorded_pass(self):
        # Jobs queued before the dashboard set KE_DASHBOARD_JOB.
        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "dashboard.db")
            with sqlite3.connect(db) as conn:
                conn.execute("CREATE TABLE jobs (job_id TEXT PRIMARY KEY)")
                conn.execute("INSERT INTO jobs VALUES ('506203')")
            with patch.object(G, "DB_PATH", db):
                self.assertFalse(self.blocked(self.results, environ={"SLURM_JOB_ID": "506203"}))
                self.assertTrue(self.blocked(self.results, environ={"SLURM_JOB_ID": "999"}))

    def test_a_sibling_directory_is_not_results(self):
        with patch.object(G, "DB_PATH", "/nonexistent.db"):
            self.assertFalse(self.blocked(G.RESULTS_DIR + "_elsewhere"))


if __name__ == "__main__":
    unittest.main()
