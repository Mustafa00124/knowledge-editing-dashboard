"""Exercise runner output and mode selection with fake editing/model inference."""
import contextlib
import io
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import torch
import run_experiment as runner


class RunnerEvaluationTests(unittest.TestCase):
    def run_modes(self, modes):
        requests = [{"prompt": "Capital?", "target_new": "Paris", "ground_truth": "Rome",
                     "locality": {"other": {"prompt": ["Unrelated?"], "ground_truth": ["London"]}},
                     "portability": {"hop": {"prompt": ["Related?"], "ground_truth": ["France"]}}}]
        model = Mock(training=False)
        model.to.return_value = model
        model.generate.return_value = torch.tensor([[1, 2]])
        class Inputs(dict):
            def to(self, device):
                return self
        tok = Mock(pad_token="pad", eos_token="eos", eos_token_id=0)
        tok.return_value = Inputs(input_ids=torch.tensor([[1]]))
        tok.decode.return_value = "Paris"
        hp = types.SimpleNamespace(device=0, model_name="fake", layers=[0], num_steps=1)
        hp.to_dict = lambda: {"model_name": "fake", "device": 0}
        hparams_module = types.ModuleType("easyeditor.models.ft.ft_hparams")
        hparams_module.FTHyperParams = Mock()
        hparams_module.FTHyperParams.from_hparams.return_value = hp
        eval_module = types.ModuleType("eval_utils")
        eval_module.load_requests = Mock(return_value=requests)
        eval_module.evaluate_requests = Mock(return_value=([{}], [{}]))
        eval_module.aggregate_metrics = lambda _: {"edit_succ": 50, "portability": 25, "locality": 100, "fluency": None}
        eval_module.memory_snapshot = lambda _: {}
        eval_module.sample_generations = Mock(return_value=[])
        training = types.ModuleType("checkpointed_ft")
        def edit(model, tok, requests, hp, interval, checkpoint):
            checkpoint(0, None)
            checkpoint(1, 0.1)
        training.execute_ft_checkpointed = Mock(side_effect=edit)
        samples = types.ModuleType("response_samples")
        samples.method_samples = Mock(return_value=[])
        modules = {"eval_utils": eval_module, "easyeditor.models.ft.ft_hparams": hparams_module,
                   "checkpointed_ft": training, "response_samples": samples}
        with tempfile.TemporaryDirectory() as tmp, patch.dict(sys.modules, modules), \
             patch.object(runner.AutoModelForCausalLM, "from_pretrained", return_value=model), \
             patch.object(runner.AutoTokenizer, "from_pretrained", return_value=tok), \
             patch("evaluation_config.judge_configured", return_value=True), \
             patch("semantic_evaluation.SemanticEvaluator.bertscore", side_effect=lambda probes: [0.9] * len(probes)), \
             patch("semantic_evaluation.SemanticEvaluator.judge_probe", return_value={"verdict": "pass", "reason": "Equivalent"}), \
             patch.object(sys, "argv", ["run_experiment.py", "--method", "ft", "--model", "gpt-j-6b",
                 "--evaluation_modes", modes, "--out_root", tmp, "--run_name", "test", "--ds_size", "1",
                 "--num_steps", "1", "--checkpoint_every", "1", "--sample_every", "1", "--fluency_every", "1"]), \
             contextlib.redirect_stdout(io.StringIO()):
            runner.main()
            path = Path(tmp) / "runs/test"
            summary = json.loads((path / "summary.json").read_text())
            checkpoints = [json.loads(line) for line in (path / "checkpoints.jsonl").read_text().splitlines()]
            self.assertEqual(len(checkpoints), 2)
            self.assertEqual(set(summary["evaluations"]), set(modes.split(",")))
            self.assertEqual(training.execute_ft_checkpointed.call_count, 1)
            if "original" in modes:
                self.assertEqual(summary["edit_succ"], 50)
            else:
                self.assertIsNone(summary["edit_succ"])
                eval_module.evaluate_requests.assert_not_called()
            if "bertscore" in modes:
                self.assertEqual(summary["evaluations"]["bertscore"]["edit_succ"], 0.9)
                self.assertEqual(summary["evaluations"]["exact_match"]["edit_succ"], 100)
                payload = json.loads((path / "evaluations/step_000001.json").read_text())
                self.assertEqual(len(payload["probes"]), 3)
                self.assertEqual(payload["probes"][-1]["before_answer"], "Paris")
                # Three probes at two checkpoints, shared by all generated-answer scorers.
                self.assertEqual(model.generate.call_count, 6)
            self.assertNotIn("api_key", (path / "hparams.yaml").read_text())
            self.assertEqual(len(json.loads((Path(tmp) / "manifest.json").read_text())), 1)

    def test_all_three_share_one_edit_run(self):
        self.run_modes("original,exact_match,bertscore,llm_judge")

    def test_generated_scores_without_original(self):
        self.run_modes("exact_match,bertscore")


if __name__ == "__main__":
    unittest.main()
