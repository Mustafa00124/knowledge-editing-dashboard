"""local_jobs stands in for sbatch/sacct/scancel on a machine without SLURM.

Runs real background processes (short bash scripts, no GPU), so these check
the states the queue cards depend on: one job at a time, sacct-spelled
states, a cancel that sticks, and a dead supervisor reading as FAILED.
"""
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

import config
import local_jobs
import slurm


def wait_for(job_id, states, timeout=20):
    deadline = time.time() + timeout
    while time.time() < deadline:
        current = local_jobs.status(job_id)["state"]
        if current in states:
            return current
        time.sleep(0.1)
    raise AssertionError(f"{job_id} never reached {states}, last {current}")


class LocalJobsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        patcher = mock.patch.object(config, "LOCAL_JOBS_DIR", self.tmp / "local_jobs")
        patcher.start()
        self.addCleanup(patcher.stop)

    def submit(self, body):
        job_id = local_jobs.new_job_id()
        script = self.tmp / f"{job_id}.sh"
        script.write_text(f"#!/bin/bash\n#SBATCH --job-name=ignored\nset -euo pipefail\n{body}\n")
        local_jobs.submit(job_id, script, self.tmp / f"{job_id}.out", self.tmp / f"{job_id}.err")
        return job_id

    def test_completed_job_reports_exit_code_and_output(self):
        job_id = self.submit("echo hello")
        self.assertEqual(wait_for(job_id, {"COMPLETED", "FAILED"}), "COMPLETED")
        self.assertEqual(local_jobs.status(job_id)["exit_code"], "0:0")
        self.assertIn("hello", (self.tmp / f"{job_id}.out").read_text())

    def test_failing_script_is_failed(self):
        job_id = self.submit("exit 3")
        self.assertEqual(wait_for(job_id, {"COMPLETED", "FAILED"}), "FAILED")
        self.assertEqual(local_jobs.status(job_id)["exit_code"], "3:0")

    def test_jobs_run_one_at_a_time(self):
        first = self.submit("sleep 2")
        wait_for(first, {"RUNNING"})
        second = self.submit("echo second")
        time.sleep(0.5)
        self.assertEqual(local_jobs.status(second)["state"], "PENDING")
        wait_for(second, {"COMPLETED"})
        self.assertEqual(local_jobs.status(first)["state"], "COMPLETED")

    def test_cancel_stops_a_running_job_and_sticks(self):
        job_id = self.submit("sleep 30")
        wait_for(job_id, {"RUNNING"})
        self.assertEqual(slurm.cancel_many([job_id]), "")
        self.assertEqual(local_jobs.status(job_id)["state"], "CANCELLED")
        time.sleep(0.5)
        self.assertEqual(local_jobs.status(job_id)["state"], "CANCELLED")

    def test_status_routes_local_ids_without_sacct(self):
        job_id = self.submit("true")
        wait_for(job_id, {"COMPLETED"})
        self.assertEqual(slurm.sacct_statuses([job_id])[job_id]["state"], "COMPLETED")
        self.assertEqual(slurm.sacct_status(job_id)["state"], "COMPLETED")

    def test_dead_supervisor_reads_as_failed(self):
        job_id = local_jobs.new_job_id()
        config.LOCAL_JOBS_DIR.mkdir(parents=True)
        local_jobs._write(job_id, {"state": "RUNNING", "pid": 2 ** 22 + 12345, "started": time.time()})
        self.assertEqual(local_jobs.status(job_id)["state"], "FAILED")


if __name__ == "__main__":
    unittest.main()
