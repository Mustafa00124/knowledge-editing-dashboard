"""The dashboard's SLURM submissions share one global four-GPU cap."""
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import config
import db
import environment
import slurm


class GPUJobCapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.patchers = [
            patch.object(config, "DB_PATH", self.root / "dashboard.db"),
            patch.object(config, "SUBMITTED_SBATCH_DIR", self.root / "submitted"),
            patch.object(config, "GPU_LANE_LOCK_PATH", self.root / ".gpu_lane.lock"),
            patch.object(environment, "scheduler", return_value="slurm"),
            patch.object(environment, "launch_blockers", return_value=[]),
            patch.object(environment, "runner_python", return_value="/usr/bin/python3"),
        ]
        for patcher in self.patchers:
            patcher.start()
            self.addCleanup(patcher.stop)
        db.init()
        self.next_job_id = 100

    def fake_sbatch(self, args, **kwargs):
        self.assertEqual(args[0], "sbatch")
        self.next_job_id += 1
        return subprocess.CompletedProcess(args, 0, f"Submitted batch job {self.next_job_id}\n", "")

    def config(self, gres="gpu:1"):
        exp_dir = self.root / "experiment"
        exp_dir.mkdir(exist_ok=True)
        return {
            "name": "experiment",
            "script": "run.py",
            "_dir": str(exp_dir),
            "fields": [],
            "resources": {"gres": gres},
        }

    def test_fifth_and_later_gpu_jobs_wait_in_four_shared_lanes(self):
        scripts = []
        with patch.object(slurm.subprocess, "run", side_effect=self.fake_sbatch):
            for index in range(6):
                result = slurm._submit_one(self.config(), {}, f"run_{index}")
                scripts.append(Path(result["sbatch_path"]).read_text())

        self.assertTrue(all("--dependency" not in script for script in scripts[:4]))
        self.assertIn("#SBATCH --dependency=afterany:101", scripts[4])
        self.assertIn("#SBATCH --dependency=afterany:102", scripts[5])

    def test_after_ok_jobs_are_waited_for_alongside_the_lane(self):
        with patch.object(slurm.subprocess, "run", side_effect=self.fake_sbatch):
            first = [slurm._submit_one(self.config(), {}, f"run_{i}", after_ok=["77"]) for i in range(5)]
        scripts = [Path(r["sbatch_path"]).read_text() for r in first]
        self.assertIn("#SBATCH --dependency=afterok:77\n", scripts[0])
        self.assertIn("#SBATCH --dependency=afterany:101,afterok:77", scripts[4])

    def test_cpu_jobs_do_not_consume_gpu_lanes(self):
        with patch.object(slurm.subprocess, "run", side_effect=self.fake_sbatch):
            cpu = slurm._submit_one(self.config(""), {}, "cpu")
            gpu = slurm._submit_one(self.config(), {}, "gpu")

        self.assertNotIn("--dependency", Path(cpu["sbatch_path"]).read_text())
        self.assertNotIn("--dependency", Path(gpu["sbatch_path"]).read_text())
        lane, tail, _ = db.next_gpu_lane()
        self.assertEqual((lane, tail), (1, None))

    def test_old_lane_tails_are_kept_only_while_slurm_still_has_them(self):
        old = "2000-01-01T00:00:00+00:00"
        absent = subprocess.CompletedProcess([], 0, "", "")
        active = subprocess.CompletedProcess([], 0, "999\n", "")
        with patch.object(slurm.subprocess, "run", return_value=absent):
            self.assertIsNone(slurm._live_lane_tail("999", old))
        with patch.object(slurm.subprocess, "run", return_value=active):
            self.assertEqual(slurm._live_lane_tail("999", old), "999")
        # Long gone from slurmctld: squeue refuses the id instead of listing nothing.
        aged_out = subprocess.CompletedProcess([], 1, "", "slurm_load_jobs error: Invalid job id specified")
        with patch.object(slurm.subprocess, "run", return_value=aged_out):
            self.assertIsNone(slurm._live_lane_tail("999", old))
        broken = subprocess.CompletedProcess([], 1, "", "slurm_load_jobs error: Unable to contact slurm controller")
        with patch.object(slurm.subprocess, "run", return_value=broken):
            with self.assertRaises(RuntimeError):
                slurm._live_lane_tail("999", old)

    def test_multi_gpu_jobs_cannot_bypass_the_four_gpu_limit(self):
        with self.assertRaisesRegex(RuntimeError, "only one GPU per job"):
            slurm._submit_one(self.config("gpu:2"), {}, "too_many")


if __name__ == "__main__":
    unittest.main()
