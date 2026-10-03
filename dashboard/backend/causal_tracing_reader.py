"""Reads the causal tracing experiment's output: where each model recalls
facts, per model. No editing method is involved.

The mapping itself (traced_layers.json) is written by
experiments/causal_tracing/causal_trace.py, rebuilt from its run summaries.
Nothing here writes to it - this module only reads. Comparing a traced peak
with the layers each method edits is the Edit layers investigation's job
(hparam_sweeps.catalog), not this one's.
"""
import json
from pathlib import Path

import config
import registry
import results_reader

EXPERIMENT = "causal_tracing"

def _root():
    root = results_reader.out_root(EXPERIMENT)
    return Path(root) if root else None


def _read_json(path):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def _model_options():
    """The models this experiment can trace, from its own dashboard.json, so
    the picker and the runner can't drift apart."""
    try:
        cfg = registry.get_experiment_type(EXPERIMENT)
    except KeyError:
        return []
    field = next((f for f in cfg.get("fields", []) if f["name"] == "model"), None)
    return field.get("options", []) if field else []


def fact_sets(root):
    """Every fact set on disk, newest first: single-set runs' fact_set.json
    and grouped runs' sets/<group>.json, with what the page needs to offer
    and flag them (below_min sets are refused by the tracer)."""
    base = root / "fact_sets" / "runs" if root else None
    if not base or not base.is_dir():
        return []
    out = []
    for path in list(base.glob("*/fact_set.json")) + list(base.glob("*/sets/*.json")):
        data = _read_json(path)
        if not data:
            continue
        out.append({
            "path": str(path), "name": data.get("name") or path.parent.name,
            "models": data.get("models", []), "formats": data.get("formats") or ["completion"],
            "picked": data.get("picked", len(data.get("facts", []))), "shared": data.get("shared"),
            "below_min": data.get("below_min", data.get("picked", len(data.get("facts", []))) < 50),
            "finished_at": data.get("finished_at"), "_mtime": path.stat().st_mtime,
        })
    out.sort(key=lambda s: -s.pop("_mtime"))
    return out


def overview():
    root = _root()
    mapping = _read_json(root / "traced_layers.json") if root else None
    mapping = mapping or {}
    runs = results_reader.get_manifest(EXPERIMENT)

    models = []
    for option in _model_options():
        model = option["value"]
        models.append({
            "value": model,
            "label": option.get("label", model),
            "note": option.get("note"),
            "available": option.get("available", True),
            "traced": mapping.get(model),
            "runs": sum(1 for row in runs if row.get("model") == model),
        })
    return {
        "models": models,
        "mapping": mapping,
        "mapping_path": str(root / "traced_layers.json") if root else None,
        "runs": sorted(runs, key=lambda row: row.get("finished_at") or "", reverse=True),
        "fact_sets": fact_sets(root),
    }


def trace(run):
    """One run's full curves, plus the token grid when it recorded one."""
    root = _root()
    if not root:
        return None
    path = results_reader.run_path(root / "runs", run) / "trace.json"
    if not path.exists():
        return None
    return _read_json(path)
