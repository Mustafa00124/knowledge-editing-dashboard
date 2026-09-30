"""Batch queue reads without launching or changing SLURM jobs."""
import contextlib
import importlib
import io
import subprocess
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import slurm

with contextlib.redirect_stdout(io.StringIO()):
    main = importlib.import_module("main")


class BatchStatusTests(unittest.TestCase):
    def test_matches_ids_normalizes_cancellation_and_keeps_missing_unknown(self):
        output = "102|CANCELLED by 123|00:01:02|0:15\n101|COMPLETED|00:00:10|0:0\n101.batch|FAILED|00:00:10|1:0\n"
        with patch.object(slurm.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout=output)) as run:
            statuses = slurm.sacct_statuses(["101", "102", "103", "101"])
        run.assert_called_once()
        self.assertEqual(run.call_args.args[0][2], "101,102,103")
        self.assertEqual(statuses["101"]["state"], "COMPLETED")
        self.assertEqual(statuses["102"], {"state": "CANCELLED", "elapsed": "00:01:02", "exit_code": "0:15"})
        self.assertEqual(statuses["103"], {"state": "UNKNOWN", "elapsed": None, "exit_code": None})

    def test_empty_queue_does_not_query_all_slurm_jobs(self):
        with patch.object(slurm.subprocess, "run") as run:
            self.assertEqual(slurm.sacct_statuses([]), {})
        run.assert_not_called()

    def test_failed_command_is_not_reported_as_valid_unknown_status(self):
        with patch.object(slurm.subprocess, "run", return_value=SimpleNamespace(returncode=1, stderr="Accounting unavailable")):
            with self.assertRaisesRegex(RuntimeError, "Accounting unavailable"):
                slurm.sacct_statuses(["101"])

    def test_queue_batches_across_slots_and_preserves_card_states(self):
        def job(job_id):
            return {"job_id": job_id, "experiment_type": "test", "params_json": "{}"}
        groups = [[job("101")], [job("102")]] + [[] for _ in range(6)]
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(main.db, "jobs_for_slot", side_effect=lambda i: groups[i]))
            stack.enter_context(patch.object(main.db, "get_slot", return_value=None))
            stack.enter_context(patch.object(main.registry, "get_experiment_type", return_value={}))
            single = stack.enter_context(patch.object(slurm, "sacct_status"))
            batch = stack.enter_context(patch.object(slurm, "sacct_statuses", return_value={"101": {"state": "COMPLETED"}, "102": {"state": "PENDING"}}))
            cards = main.get_queue()
        single.assert_not_called()
        batch.assert_called_once()
        self.assertEqual(list(batch.call_args.args[0]), ["101", "102"])
        self.assertEqual([card["status"] for card in cards], ["completed", "running"] + ["empty"] * 6)

    def test_timeout_returns_retryable_service_error(self):
        with patch.object(main.db, "jobs_for_slot", return_value=[]), patch.object(slurm, "sacct_statuses", side_effect=subprocess.TimeoutExpired("sacct", 15)):
            with self.assertRaises(main.HTTPException) as caught:
                main.get_queue()
        self.assertEqual(caught.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()
