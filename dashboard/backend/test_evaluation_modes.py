import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import registry
import results_reader
import slurm


class EvaluationWiringTests(unittest.TestCase):
    def setUp(self):
        self.cfg = {"name": "test", "fields": [
            {"name": "method", "default": "ft", "type": "string"},
            {"name": "evaluation_modes", "default": "original", "type": "string"},
        ]}

    def test_multiple_modes_are_one_job(self):
        with patch.object(slurm, "_submit_one", return_value={}) as submit:
            slurm.submit_sweep(self.cfg, {"method": ["ft", "rome"],
                                       "evaluation_modes": ["exact_match,bertscore"]})
        self.assertEqual(submit.call_count, 2)
        for call in submit.call_args_list:
            self.assertEqual(call.args[1]["evaluation_modes"], "exact_match,bertscore")
            self.assertIn("eval-exact_match-bertscore", call.args[2])

    def test_placeholder_blocks_submission_before_sbatch(self):
        with patch("evaluation_config.judge_configured", return_value=False), patch.object(slurm, "_submit_one") as submit:
            with self.assertRaises(RuntimeError):
                slurm.submit_sweep(self.cfg, {"evaluation_modes": ["llm_judge"]})
            submit.assert_not_called()

    def test_retry_old_job_defaults_to_original(self):
        with patch.object(slurm, "_submit_one", return_value={}) as submit:
            slurm.submit_exact(self.cfg, {"method": "ft"}, "old_retry")
        self.assertEqual(submit.call_args.args[1]["evaluation_modes"], "original")

    def test_registry_never_exposes_key(self):
        cfg = registry.get_experiment_type("run_experiment")
        field = next(f for f in cfg["fields"] if f["name"] == "evaluation_modes")
        self.assertEqual(len(field["options"]), 4)
        self.assertNotIn("YOUR_API_KEY_HERE", json.dumps(cfg))
        self.assertNotIn('"api_key"', json.dumps(cfg))

    def test_read_saved_evaluation(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(results_reader, "_base", return_value=Path(tmp)):
            path = Path(tmp) / "runs/example/evaluations"
            path.mkdir(parents=True)
            payload = {"probes": [{"answer": "Paris"}]}
            (path / "step_000050.json").write_text(json.dumps(payload))
            self.assertEqual(results_reader.list_evaluations("example"), [50])
            self.assertEqual(results_reader.get_evaluation("example", 50), payload)
            with self.assertRaises(ValueError):
                results_reader.list_evaluations("../outside")


if __name__ == "__main__":
    unittest.main()
