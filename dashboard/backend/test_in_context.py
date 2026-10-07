"""The In-context experiment: its type is registered, launches are recorded
under its own id, and its runs are scored per evaluation mode."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import in_context_reader
import launches
import registry


class InContextTests(unittest.TestCase):
    def test_type_and_launch_id(self):
        cfg = registry.get_experiment_type("in_context")
        self.assertEqual({f["name"] for f in cfg["fields"]} >= {"method", "model", "data_path", "kb_size"}, True)
        self.assertIn("data_path", cfg["run_name_always"])  # datasets never share a run directory
        self.assertEqual(launches.default_investigation("in_context", {}), "in_context")

    def test_runs_are_scored_against_the_empty_knowledge_base(self):
        root = Path(tempfile.mkdtemp())
        run = root / "runs" / "scr_qwen3-4b-base_ZsRE_kb100"
        run.mkdir(parents=True)
        (run / "checkpoints.jsonl").write_text(json.dumps({"step": 0, "fluency": 500.0}) + "\n")
        (run / "summary.json").write_text(json.dumps({
            "run": run.name, "model": "qwen3-4b-base", "dataset_subset": "ZsRE", "kb_size": 100,
            "kb_distractors": {"same dataset": 99},
            "evaluations": {"original": {"edit_succ": 80.0, "portability": 40.0, "locality": 90.0, "fluency": 450.0},
                            "bertscore": {"edit_succ": 0.7, "portability": 0.5, "locality": 0.9, "fluency": None}},
        }))
        with patch.object(in_context_reader.results_reader, "out_root", return_value=str(root)):
            rows = in_context_reader.runs()
        self.assertEqual(len(rows), 1)
        scores = rows[0]["scores"]
        self.assertEqual(scores["original"], {"fluency": 0.9, "reliability": 0.8, "locality": 0.9,
                                              "generalizability": 0.4})
        self.assertEqual(scores["bertscore"]["reliability"], 0.7)
        self.assertEqual(rows[0]["kb_size"], 100)


if __name__ == "__main__":
    unittest.main()
