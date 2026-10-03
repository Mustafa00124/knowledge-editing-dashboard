"""The neuron and circuit tracing reader: runs per model, the traced layer
alongside for comparison, and one run's detail file."""
import contextlib
import importlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

with contextlib.redirect_stdout(io.StringIO()):
    main = importlib.import_module("main")

reader = main.mechanistic_reader


class MechanisticReaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.roots = {name: root / name for name in ("causal_tracing", "neuron_tracing", "circuit_tracing")}
        for path in self.roots.values():
            (path / "runs").mkdir(parents=True)
        (self.roots["causal_tracing"] / "traced_layers.json").write_text(json.dumps({"qwen3-4b": {"peak_layer": 7}}))
        models = {"name": "model", "options": [{"label": "Qwen3-4B", "value": "qwen3-4b"},
                                               {"label": "GPT-J-6B", "value": "gpt-j-6b"}]}
        self.types = [{"name": name, "out_root": str(path), "fields": [models]} for name, path in self.roots.items()]
        for target, value in (("list_experiment_types", self.types),):
            p = patch.object(main.registry, target, return_value=value)
            p.start()
            self.addCleanup(p.stop)
        p = patch.object(main.registry, "get_experiment_type",
                         side_effect=lambda name: next(t for t in self.types if t["name"] == name))
        p.start()
        self.addCleanup(p.stop)
        self.client = TestClient(main.app, headers={"x-dashboard-token": main.AUTH_TOKEN})

    def write_run(self, experiment, run, model, finished, detail_file):
        run_dir = self.roots[experiment] / "runs" / run
        run_dir.mkdir()
        summary = {"run": run, "model": model, "finished_at": finished, "peak_layer": 3}
        (run_dir / "summary.json").write_text(json.dumps(summary))
        (run_dir / detail_file).write_text(json.dumps({"run": run, "summary": summary, "facts": []}))
        manifest = self.roots[experiment] / "manifest.json"
        rows = json.loads(manifest.read_text()) if manifest.exists() else []
        manifest.write_text(json.dumps(rows + [summary]))

    def test_overview_lists_models_newest_run_first(self):
        self.write_run("neuron_tracing", "old", "qwen3-4b", "2026-10-01T00:00:00", "neurons.json")
        self.write_run("neuron_tracing", "new", "qwen3-4b", "2026-10-02T00:00:00", "neurons.json")
        data = self.client.get("/api/mechanistic/neuron_tracing").json()
        qwen = next(m for m in data["models"] if m["value"] == "qwen3-4b")
        self.assertEqual((qwen["latest"], qwen["runs"], qwen["traced_peak_layer"]), ("new", 2, 7))
        gptj = next(m for m in data["models"] if m["value"] == "gpt-j-6b")
        self.assertEqual((gptj["latest"], gptj["traced_peak_layer"]), (None, None))
        self.assertEqual([r["run"] for r in data["runs"]], ["new", "old"])

    def test_detail_reads_each_experiments_own_file(self):
        self.write_run("circuit_tracing", "c1", "qwen3-4b", "2026-10-02T00:00:00", "circuit.json")
        self.assertEqual(self.client.get("/api/mechanistic/circuit_tracing/runs/c1").json()["run"], "c1")
        self.assertEqual(self.client.get("/api/mechanistic/neuron_tracing/runs/c1").status_code, 404)
        self.assertEqual(self.client.get("/api/mechanistic/causal_tracing").status_code, 404)
        self.assertEqual(self.client.get("/api/mechanistic/circuit_tracing/runs/..%2Fx").status_code, 404)
        self.assertEqual(self.client.get("/api/mechanistic/circuit_tracing/runs/.hidden").status_code, 400)


if __name__ == "__main__":
    unittest.main()
