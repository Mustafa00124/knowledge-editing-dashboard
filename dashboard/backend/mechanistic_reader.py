"""Reads the neuron attribution and circuit tracing experiments' output:
per model, no editing method, one summary per run and one detail file
(neurons.json, circuit.json) with every fact's own result.

Both trace the same facts as causal tracing (its fact sets), so the overview
carries each model's traced layer from traced_layers.json for comparison,
and the fact sets on disk for the launch form. Read only.
"""
import json
from pathlib import Path

import causal_tracing_reader
import registry
import results_reader

DETAIL_FILES = {"neuron_tracing": "neurons.json", "circuit_tracing": "circuit.json"}


def _root(experiment):
    root = results_reader.out_root(experiment)
    return Path(root) if root else None


def _read_json(path):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def _model_options(experiment):
    try:
        cfg = registry.get_experiment_type(experiment)
    except KeyError:
        return []
    field = next((f for f in cfg.get("fields", []) if f["name"] == "model"), None)
    return field.get("options", []) if field else []


def overview(experiment):
    if experiment not in DETAIL_FILES:
        raise KeyError(experiment)
    runs = sorted(results_reader.get_manifest(experiment), key=lambda row: row.get("finished_at") or "",
                  reverse=True)
    tracing_root = _root(causal_tracing_reader.EXPERIMENT)
    traced = (_read_json(tracing_root / "traced_layers.json") if tracing_root else None) or {}
    models = []
    for option in _model_options(experiment):
        model = option["value"]
        mine = [row for row in runs if row.get("model") == model]
        models.append({
            "value": model, "label": option.get("label", model), "note": option.get("note"),
            "available": option.get("available", True),
            "latest": mine[0]["run"] if mine else None, "runs": len(mine),
            "traced_peak_layer": (traced.get(model) or {}).get("peak_layer"),
        })
    return {
        "models": models,
        "runs": runs,
        "fact_sets": causal_tracing_reader.fact_sets(tracing_root),
    }


def detail(experiment, run):
    """One run's detail file, or None. ValueError for a bad run name."""
    if experiment not in DETAIL_FILES:
        raise KeyError(experiment)
    root = _root(experiment)
    if not root:
        return None
    path = results_reader.run_path(root / "runs", run) / DETAIL_FILES[experiment]
    return _read_json(path) if path.exists() else None
