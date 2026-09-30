"""Discovers experiment types by scanning experiments/*/dashboard.json.

Adding a new experiment type to the dashboard means adding one such file
next to the experiment's existing run script/sbatch — no backend code
changes. See dashboard/README.md for the schema.

Paths inside dashboard.json are written as ${PROJECT_ROOT}/... and expanded
here, so the same file works in any checkout. Models and dataset subsets
whose files are not on disk are reported as unavailable (greyed out in the
picker) instead of failing once a job reaches a GPU.
"""
import json
import os
import re
import sys

import config
import models_reader
sys.path.insert(0, str(config.EXPERIMENTS_DIR / "run_experiment"))
from evaluation_config import options as evaluation_options, validate_modes

# Both spellings the run scripts use for a model's weights directory:
#   "qwen3-4b": os.path.join(PROJECT_ROOT, "models/Qwen3-4B"),
#   "qwen3-4b": f"{PROJECT_ROOT}/models/Qwen3-4B",
_MODEL_PATH_RE = re.compile(
    r'"([^"]+)":\s*(?:os\.path\.join\(PROJECT_ROOT,\s*"models/([^"]+)"\)|f"\{PROJECT_ROOT\}/models/([^"]+)")'
)


def _expand(value):
    if isinstance(value, str):
        return value.replace("${PROJECT_ROOT}", str(config.PROJECT_ROOT))
    if isinstance(value, list):
        return [_expand(v) for v in value]
    if isinstance(value, dict):
        return {k: _expand(v) for k, v in value.items()}
    return value


def model_dirs(exp_dir, script):
    """Model value -> weights directory name, read from the run script's own
    MODEL_PATHS table rather than duplicated here. Reading the source keeps
    the backend free of the script's torch/transformers imports."""
    path = os.path.join(exp_dir, script)
    if not os.path.exists(path):
        return {}
    with open(path) as handle:
        src = handle.read()
    block = re.search(r"MODEL_PATHS = \{(.*?)\n\}", src, re.S)
    if not block:
        return {}
    return {key: a or b for key, a, b in _MODEL_PATH_RE.findall(block.group(1))}


def benchmark_name(path):
    """datasets/<Benchmark>/... -> Benchmark, as the Downloads page names it."""
    try:
        return os.path.relpath(path, config.DATASETS_DIR).split(os.sep)[0]
    except ValueError:
        return "it"


def _mark_missing_files(cfg):
    dirs = model_dirs(cfg["_dir"], cfg.get("script", ""))
    for field in cfg.get("fields", []):
        if field["name"] == "model":
            for option in field.get("options", []):
                directory = dirs.get(option.get("value"))
                if option.get("available") is False or not directory:
                    continue
                if not models_reader.installed(config.MODELS_DIR / directory):
                    option["available"] = False
                    option["note"] = f"weights not downloaded: get {directory} on the Downloads page"
        if field.get("control") == "dataset":
            for benchmark in field.get("benchmarks", []):
                for subset in benchmark.get("subsets", []):
                    if subset.get("available") is False or not subset.get("value"):
                        continue
                    if not os.path.exists(subset["value"]):
                        subset["available"] = False
                        subset["note"] = f"not downloaded: get {benchmark_name(subset['value'])} on the Downloads page"


def list_experiment_types():
    types = []
    if not config.EXPERIMENTS_DIR.exists():
        return types
    for d in sorted(config.EXPERIMENTS_DIR.iterdir()):
        cfg_path = d / "dashboard.json"
        if cfg_path.exists():
            cfg = _expand(json.loads(cfg_path.read_text()))
            cfg["_dir"] = str(d)
            for field in cfg.get("fields", []):
                if field.get("control") == "evaluation":
                    field["options"] = evaluation_options()
            _mark_missing_files(cfg)
            types.append(cfg)
    return types


def get_experiment_type(name):
    for t in list_experiment_types():
        if t["name"] == name:
            return t
    raise KeyError(name)
