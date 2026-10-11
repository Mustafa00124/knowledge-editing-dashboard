"""Model audit results (experiments/model_audit): for each model, whether it
already gives Sid's Dataset's original answers before any editing. Read from
<out_root>/runs/<run>/summary.json (counts) and responses.jsonl (every query,
response and judge label)."""
import json
from pathlib import Path

import results_reader

EXPERIMENT = "model_audit"


def _runs_dir():
    root = results_reader.out_root(EXPERIMENT)
    return Path(root) / "runs" if root else None


def runs():
    runs_dir = _runs_dir()
    out = []
    for path in sorted(runs_dir.glob("*/summary.json")) if runs_dir and runs_dir.is_dir() else []:
        try:
            summary = json.loads(path.read_text())
        except (OSError, ValueError):
            continue
        summary.pop("facts", None)
        summary["run"] = path.parent.name
        summary["finished_at"] = path.stat().st_mtime
        out.append(summary)
    return out


def run(name):
    runs_dir = _runs_dir()
    folder = runs_dir / name if runs_dir else None
    if not folder or folder.parent != runs_dir or not (folder / "summary.json").exists():
        raise KeyError(name)
    summary = json.loads((folder / "summary.json").read_text())
    responses = [json.loads(line) for line in (folder / "responses.jsonl").read_text().splitlines() if line.strip()]
    return {"run": name, "summary": summary, "responses": responses}
