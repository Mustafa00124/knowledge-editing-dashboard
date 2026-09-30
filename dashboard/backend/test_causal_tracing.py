"""The causal tracing reader: pairing a model's traced layer with the layer its edit hparams use today."""
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

reader = main.causal_tracing_reader


class CausalTracingReaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.out_root = root / "results" / "causal_tracing"
        (self.out_root / "runs").mkdir(parents=True)
        self.hparams = root / "experiments" / "run_experiment" / "hparams"

        for method, layers in [("ROME", "[5]"), ("MEMIT", "[4, 5, 6, 7, 8]")]:
            path = self.hparams / method / "qwen3-4b.yaml"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"alg_name: {method}\nlayers: {layers}\ndevice: 0\n")
        # Block-style list, and a model with no hparams at all.
        rome_gptj = self.hparams / "ROME" / "gpt-j-6b.yaml"
        rome_gptj.write_text("alg_name: ROME\nlayers:\n  - 3\n  - 4\n")

        self.config = {
            "name": "causal_tracing",
            "out_root": str(self.out_root),
            "fields": [{"name": "model", "options": [
                {"label": "Qwen3-4B", "value": "qwen3-4b", "note": "inherited"},
                {"label": "GPT-J-6B", "value": "gpt-j-6b"},
                {"label": "OLMo-2-7B", "value": "olmo-2-7b"},
            ]}],
        }
        self.patch_types = patch.object(main.registry, "list_experiment_types", return_value=[self.config])
        self.patch_types.start()
        self.addCleanup(self.patch_types.stop)
        self.patch_get = patch.object(main.registry, "get_experiment_type", return_value=self.config)
        self.patch_get.start()
        self.addCleanup(self.patch_get.stop)
        self.patch_hparams = patch.object(reader, "HPARAMS_DIR", self.hparams)
        self.patch_hparams.start()
        self.addCleanup(self.patch_hparams.stop)

    def write_trace(self, model, layer, run="run1", n_prompts=200):
        (self.out_root / "manifest.json").write_text(json.dumps([
            {"run": run, "model": model, "peak_layer": layer, "layers": [layer], "peak_aie": 0.1,
             "effect": "mlp", "window": 10, "n_prompts": n_prompts, "n_layers": 36,
             "dataset_benchmark": "KnowEdit", "dataset_subset": "wiki_counterfact",
             "finished_at": "2026-09-20T01:00:00-04:00"}
        ]))
        (self.out_root / "traced_layers.json").write_text(json.dumps({
            model: {"layers": [layer], "peak_layer": layer, "peak_aie": 0.1, "effect": "mlp",
                    "window": 10, "n_prompts": n_prompts, "n_layers": 36,
                    "dataset": "KnowEdit / wiki_counterfact", "run": run,
                    "traced_at": "2026-09-20T01:00:00-04:00"}
        }))

    def test_reads_the_layer_each_method_would_edit_today(self):
        overview = main.get_causal_tracing()
        models = {m["value"]: m for m in overview["models"]}

        self.assertEqual(models["qwen3-4b"]["hparams_layers"], {"ROME": [5], "MEMIT": [4, 5, 6, 7, 8]})
        # Block-style yaml reads the same as the inline form.
        self.assertEqual(models["gpt-j-6b"]["hparams_layers"], {"ROME": [3, 4]})
        self.assertEqual(models["olmo-2-7b"]["hparams_layers"], {})

    def test_untraced_models_are_listed_with_no_answer_rather_than_omitted(self):
        overview = main.get_causal_tracing()

        self.assertEqual([m["value"] for m in overview["models"]], ["qwen3-4b", "gpt-j-6b", "olmo-2-7b"])
        self.assertTrue(all(m["traced"] is None for m in overview["models"]))
        self.assertEqual(overview["mapping"], {})
        self.assertEqual(overview["runs"], [])

    def test_a_traced_model_carries_its_measurement(self):
        self.write_trace("qwen3-4b", 3)
        models = {m["value"]: m for m in main.get_causal_tracing()["models"]}

        self.assertEqual(models["qwen3-4b"]["traced"]["layers"], [3])
        self.assertEqual(models["qwen3-4b"]["runs"], 1)
        self.assertIsNone(models["gpt-j-6b"]["traced"])

    def test_trace_refuses_a_run_name_that_leaves_the_runs_directory(self):
        with self.assertRaises(ValueError):
            reader.trace("../manifest.json")

    def test_missing_trace_reads_as_missing_not_as_an_error(self):
        self.assertIsNone(reader.trace("never-ran"))


if __name__ == "__main__":
    unittest.main()
