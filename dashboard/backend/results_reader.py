"""Reads the existing <out_root>/manifest.json + runs/*/checkpoints.jsonl
convention directly - no separate dashboard-owned copy of results data.

out_root comes from the *registered* experiment type (its dashboard.json),
not from scanning results/ for arbitrary folders that happen to contain a
manifest.json - those aren't guaranteed to be the same thing (e.g. an old,
no-longer-registered experiment's leftover output directory).

Archived runs live under <out_root>/archive/ in exactly the same shape (see
archive.py), so every reader here takes an `archived` flag and serves both
trees from one code path."""
import json
from pathlib import Path

import registry

# One name for the retired-runs subtree, used by archive.py too.
ARCHIVE_DIRNAME = "archive"


def list_experiment_types():
    return [t["name"] for t in registry.list_experiment_types()]


def out_root(exp_type=None):
    types = registry.list_experiment_types()
    if not types:
        return None
    cfg = next((t for t in types if t["name"] == exp_type), None) if exp_type else None
    # Asked for no type in particular, the Results page means the main
    # results experiment, not whichever directory happens to sort first:
    # causal_tracing sorts before run_experiment and its manifest is a
    # different shape entirely. So the default is declared, not positional.
    cfg = cfg or next((t for t in types if t.get("results_default")), None) or types[0]
    return cfg.get("out_root")


def run_path(parent, name):
    """One run directory directly inside `parent`, or ValueError.

    Run names arrive from the browser, so this trusts none of them: no path
    separators, no dot-segments, and the resolved path's parent has to be
    `parent` itself.
    """
    if not name or not isinstance(name, str) or name.startswith(".") or "/" in name or "\\" in name or "\0" in name:
        raise ValueError(f"invalid run name: {name!r}")
    path = (Path(parent) / name).resolve()
    if path.parent != Path(parent).resolve():
        raise ValueError(f"invalid run name: {name!r}")
    return path


def _base(exp_type=None, archived=False):
    """The tree a run lives in: <out_root>, or <out_root>/archive."""
    root = out_root(exp_type)
    if not root:
        return None
    return Path(root) / ARCHIVE_DIRNAME if archived else Path(root)


def get_manifest(exp_type=None, archived=False):
    base = _base(exp_type, archived)
    if not base:
        return []
    path = base / "manifest.json"
    if not path.exists():
        return []
    return json.loads(path.read_text())


def get_checkpoints(run, exp_type=None, archived=False):
    base = _base(exp_type, archived)
    if not base:
        return []
    path = base / "runs" / run / "checkpoints.jsonl"
    if not path.exists():
        return []
    rows = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def list_samples(run, exp_type=None, archived=False):
    base = _base(exp_type, archived)
    if not base:
        return []
    samples_dir = base / "runs" / run / "samples"
    if not samples_dir.exists():
        return []
    steps = []
    for f in samples_dir.glob("step_*.json"):
        try:
            steps.append(int(f.stem.split("_")[1]))
        except (IndexError, ValueError):
            continue
    return sorted(steps)


def get_sample(run, step, exp_type=None, archived=False):
    base = _base(exp_type, archived)
    if not base:
        return None
    path = base / "runs" / run / "samples" / f"step_{step:06d}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def _evaluation_dir(run, exp_type=None, archived=False):
    base = _base(exp_type, archived)
    if base is None or Path(run).name != run or run in (".", ".."):
        raise ValueError("Invalid run")
    return base / "runs" / run / "evaluations"


def list_evaluations(run, exp_type=None, archived=False):
    return sorted(int(p.stem.split("_")[1]) for p in
                  _evaluation_dir(run, exp_type, archived).glob("step_[0-9]*.json"))


def get_evaluation(run, step, exp_type=None, archived=False):
    path = _evaluation_dir(run, exp_type, archived) / f"step_{step:06d}.json"
    return json.loads(path.read_text()) if path.exists() else None
