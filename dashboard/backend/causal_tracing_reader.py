"""Reads the causal tracing experiment's output: which layer each model's
trace chose, and what the edit hparams currently say instead.

The mapping itself (traced_layers.json) is written by
experiments/causal_tracing/causal_trace.py, rebuilt from its run summaries.
Nothing here writes to it - this module only reads, and pairs each model with
the `layers` its locate-and-edit hparams use today, which is the comparison
the whole experiment exists to make.
"""
import json
from pathlib import Path

import yaml

import config
import registry
import results_reader

EXPERIMENT = "causal_tracing"

# The methods whose hparams carry a `layers` value a trace could inform.
LOCATE_METHODS = ("ROME", "MEMIT", "PMET", "AlphaEdit")
HPARAMS_DIR = config.EXPERIMENTS_DIR / "run_experiment" / "hparams"


def _root():
    root = results_reader.out_root(EXPERIMENT)
    return Path(root) if root else None


def _read_json(path):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def _hparams_layers(model):
    """What each locate-and-edit method would edit for this model today.

    Read straight out of the yaml the run would load, so this can never
    disagree with what an edit actually does.
    """
    out = {}
    for method in LOCATE_METHODS:
        path = HPARAMS_DIR / method / f"{model}.yaml"
        if not path.exists():
            continue
        try:
            hparams = yaml.safe_load(path.read_text()) or {}
        except (OSError, yaml.YAMLError):
            continue
        if hparams.get("layers") is not None:
            out[method] = hparams["layers"]
    return out


def _model_options():
    """The models this experiment can trace, from its own dashboard.json, so
    the picker and the runner can't drift apart."""
    try:
        cfg = registry.get_experiment_type(EXPERIMENT)
    except KeyError:
        return []
    field = next((f for f in cfg.get("fields", []) if f["name"] == "model"), None)
    return field.get("options", []) if field else []


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
            "hparams_layers": _hparams_layers(model),
            "traced": mapping.get(model),
            "runs": sum(1 for row in runs if row.get("model") == model),
        })
    return {
        "models": models,
        "mapping": mapping,
        "mapping_path": str(root / "traced_layers.json") if root else None,
        "runs": sorted(runs, key=lambda row: row.get("finished_at") or "", reverse=True),
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
