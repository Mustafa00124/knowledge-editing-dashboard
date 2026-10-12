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


def check_results():
    """The newest audit run per model, reduced to its checks: every fact check
    (record_id, fact) and relation check (relation, tag) with its score and the
    model's response, for the Datasets page's derivation view."""
    runs_dir = _runs_dir()
    newest = {}
    for path in sorted(runs_dir.glob("*/summary.json")) if runs_dir and runs_dir.is_dir() else []:
        try:
            summary = json.loads(path.read_text())
        except (OSError, ValueError):
            continue
        model, mtime = summary.get("model"), path.stat().st_mtime
        if model and (model not in newest or mtime > newest[model][0]):
            newest[model] = (mtime, path.parent)
    out = []
    for model, (mtime, folder) in sorted(newest.items()):
        facts, relations = [], []
        try:
            lines = (folder / "responses.jsonl").read_text().splitlines()
        except OSError:
            lines = []
        for line in lines:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            keep = {"score": r.get("score"), "label": r.get("label"), "response": r.get("response")}
            if r.get("query_type") == "check_fact":
                facts.append({"record_id": r["record_id"], "fact": r["fact"], **keep})
            elif r.get("query_type") == "check_relation":
                relations.append({"relation": r["relation"], "tag": r["tag"], **keep})
        out.append({"model": model, "run": folder.name, "finished_at": mtime, "has_checks": bool(facts or relations),
                    "facts": facts, "relations": relations})
    return out
