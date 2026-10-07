"""In-context experiment results (experiments/in_context): SCR asked with the
needed fact among kb_size-1 distractors, one run per model, dataset and
knowledge-base size. Read from <out_root>/runs/*/summary.json, scored on the
same 0..1 criteria as the sweeps: fluency against the empty-knowledge-base
baseline (step 0), reliability, locality, generalizability."""
import json
from pathlib import Path

import hparam_sweeps
import results_reader

EXPERIMENT = "in_context"
# Generation-based modes report percentages, BERTScore a raw F1.
_SCALE = {"exact_match": 100.0, "llm_judge": 100.0, "bertscore": 1.0}


def _mode_scores(mode, values, baseline):
    if mode == "original":
        return hparam_sweeps._scores(values, baseline)
    scale = _SCALE.get(mode, 100.0)
    pct = lambda v: None if v is None else v / scale
    return {"fluency": None, "reliability": pct(values.get("edit_succ")),
            "locality": pct(values.get("locality")), "generalizability": pct(values.get("portability"))}


def runs():
    root = results_reader.out_root(EXPERIMENT)
    runs_dir = Path(root) / "runs" if root else None
    out = []
    for path in sorted(runs_dir.glob("*/summary.json")) if runs_dir and runs_dir.is_dir() else []:
        try:
            summary = json.loads(path.read_text())
        except (OSError, ValueError):
            continue
        baseline = hparam_sweeps._first_row(path.parent / "checkpoints.jsonl")
        evaluations = summary.get("evaluations") or {"original": summary}
        out.append({
            "run": summary.get("run") or path.parent.name,
            "model": summary.get("model"),
            "dataset_benchmark": summary.get("dataset_benchmark"),
            "dataset_subset": summary.get("dataset_subset"),
            "kb_size": summary.get("kb_size"),
            "kb_distractors": summary.get("kb_distractors"),
            "ds_size": summary.get("ds_size"),
            "split": summary.get("split"),
            "seed": summary.get("seed"),
            "finished_at": summary.get("finished_at"),
            "total_sec": summary.get("total_sec"),
            "scores": {mode: _mode_scores(mode, values or {}, baseline)
                       for mode, values in evaluations.items()},
        })
    return out
