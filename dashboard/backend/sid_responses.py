"""Post-edit answers on Sid's Dataset, for the Results page's "Sid's Dataset"
view: one run per method x main instruct model, every query's answer after
the edit as a coloured dot, and per dot the answer before and after.

Where the runs come from is a *source* (SOURCES below):

  sweep_current  the default-settings run (``<method>_<model>_records_current``)
                 of the hyperparameter screen sweeps under
                 results/investigations/<family>/sweeps/<sweep>/runs/.
                 Anything under a ``deleted/`` folder is left out. Used while
                 the main experiments have not run.
  main           results/main/run_experiment/runs/: the main experiments,
                 which run each method at its tuned (best) settings.

Within a source, each (method, model) gets one run: the finished one
(summary.json present) whose summary is for Sid's Dataset, newest by
``finished_at``. To switch the default once the main experiments exist, set
DEFAULT_SOURCE = "main" (the page also has a source switch).

Colours follow the scoring in experiments/run_experiment/sid_evaluation.py
(scored_items, score_answer) and sid_eval/judge.py (score, locality_score),
read from each answer's stored judge label and score:

  answer queries (direct, paraphrase, cross-lingual, propositional, derived)
    pass      the stored score is 1: NEW for an ordinary edit; NONE (abstains)
              for a delete record; for an indeterminate derived question,
              an answer matching some world's answer (or abstaining where a
              world abstains)
    original  judge label ORIGINAL and no pass (the edit did not take)
    none      NONE and no pass (no answer)
    other     OTHER or WORLD (or NEW where it does not pass): something else
    unclear   UNCLEAR, or not judged: excluded from the scores
  locality queries (unrelated near, far)
    kept      SAME as the model's own step-0 answer
    changed   DIFFERENT; ``leak`` says whether the new answer leaked in
    unclear   UNCLEAR or not judged

A determinate derived question whose step-0 answer was not ORIGINAL carries
``counted: false``: the sweeps' generalizability (hparam_sweeps._scores) is
the determinate derived questions the model knew before the edit, so it
leaves such a question out.
"""
import json
import re
from pathlib import Path

import config

MAIN_MODELS = ["qwen3-4b-instruct-2507", "olmo-3-7b-instruct", "llama-3.1-8b-instruct", "mistral-7b-instruct-v0.1"]
METHODS = [
    ("ft", "FT-M"), ("lora", "LoRA"), ("rome", "ROME"), ("alphaedit", "AlphaEdit"), ("fidal", "FiDAL"),
    ("fine", "FiNE"), ("ifmet", "IFMET"), ("lti", "LTI"), ("loco", "LoCo"),
]
METHOD_KEYS = [m for m, _ in METHODS]
BENCHMARK = "SidsDataset"
SAMPLE_GLOB = "sid_step_*.json"
LOCALITY = ("unrelated_near", "unrelated_far")
INDETERMINATE = ("background_beliefs", "derived_beliefs")


def _sweep_current_runs():
    root = config.INVESTIGATIONS_DIR
    for path in sorted(root.glob("*/sweeps/*/runs/*_records_current")):
        if "deleted" in path.relative_to(root).parts:
            continue
        yield path


def _main_runs():
    root = config.MAIN_RESULTS_DIR / "run_experiment" / "runs"
    return sorted(p for p in root.iterdir() if p.is_dir()) if root.is_dir() else []


SOURCES = {
    "sweep_current": {
        "label": "Sweep defaults",
        "description": "The default-settings run of each hyperparameter screen sweep (dev records), "
                       "until the main experiments have run.",
        "runs": _sweep_current_runs,
    },
    "main": {
        "label": "Main experiments",
        "description": "The main experiments (test records), each method at its tuned settings.",
        "runs": _main_runs,
    },
}
DEFAULT_SOURCE = "sweep_current"


def _read_json(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return None


def _step_of(path):
    m = re.search(r"sid_step_(\d+)\.json$", path.name)
    return int(m.group(1)) if m else None


def pick_runs(source=DEFAULT_SOURCE):
    """{method: {model: run info}}: one finished Sid's Dataset run per pair."""
    if source not in SOURCES:
        raise KeyError(source)
    best = {}
    for path in SOURCES[source]["runs"]():
        summary = _read_json(path / "summary.json")
        if not summary or summary.get("dataset_benchmark") != BENCHMARK:
            continue
        method, model = summary.get("method"), summary.get("model")
        if method not in METHOD_KEYS or model not in MAIN_MODELS:
            continue
        steps = sorted(s for s in (_step_of(p) for p in (path / "samples").glob(SAMPLE_GLOB)) if s is not None)
        if not steps:
            continue
        info = {"run": path.name, "path": str(path.relative_to(config.PROJECT_ROOT)),
                "finished_at": summary.get("finished_at") or "", "edit_mode": summary.get("edit_mode"),
                "reset_every": summary.get("reset_every"), "split": summary.get("split"), "steps": steps,
                "_dir": path}
        old = best.get((method, model))
        if old is None or (info["finished_at"], info["path"]) > (old["finished_at"], old["path"]):
            best[(method, model)] = info
    out = {}
    for (method, model), info in best.items():
        out.setdefault(method, {})[model] = info
    return out


def _public(info):
    return {k: v for k, v in info.items() if not k.startswith("_")}


def overview(source=DEFAULT_SOURCE):
    runs = pick_runs(source)
    return {
        "source": source, "default_source": DEFAULT_SOURCE,
        "sources": [{"key": k, "label": v["label"], "description": v["description"]} for k, v in SOURCES.items()],
        "methods": [{"key": m, "label": label, "models": sorted(runs.get(m, {}), key=MAIN_MODELS.index)}
                    for m, label in METHODS],
        "models": MAIN_MODELS,
        "runs": {m: {model: _public(i) for model, i in per.items()} for m, per in runs.items()},
    }


# ------------------------------------------------------------------ answers

_cache = {}


def _load_steps(run_dir):
    """{step: payload} of a run's sid samples, cached until a file changes."""
    files = sorted((run_dir / "samples").glob(SAMPLE_GLOB))
    sig = tuple((f.name, f.stat().st_mtime_ns) for f in files)
    hit = _cache.get(run_dir)
    if hit and hit[0] == sig:
        return hit[1]
    steps = {}
    for f in files:
        step, data = _step_of(f), _read_json(f)
        if step is not None and data:
            steps[step] = data
    _cache[run_dir] = (sig, steps)
    return steps


def _records():
    """{record id: dataset record}: determinacy of derived questions and the
    edit's new object (to tell a locality answer that took the new answer)."""
    root = config.DATASETS_DIR / BENCHMARK / "records"
    out = {}
    for path in sorted(root.glob("*/*/*.json")) if root.is_dir() else []:
        rec = _read_json(path)
        if rec and rec.get("id"):
            out[rec["id"]] = rec
    return out


def _norm(text):
    return re.sub(r"\s+", " ", str(text or "")).strip().casefold()


def _determinacy(rec, key):
    m = re.fullmatch(r"derived\[(\d+)\]", key)
    if not m or not rec:
        return None
    items = (rec.get("queries") or {}).get("derived") or []
    i = int(m.group(1))
    return items[i].get("determinacy") if i < len(items) else None


def _leak(rec, before, after):
    """True when the changed answer now names the edit's new object (and the
    step-0 answer did not); None when the record has no single new object."""
    new = ((rec or {}).get("edit") or {}).get("object")
    if not new or not after:
        return None
    n = _norm(new)
    return n in _norm(after) and n not in _norm(before)


def _score(answer):
    """The stored score, or for an answer judged before scores were stored,
    the same rule (sid_evaluation.score_answer)."""
    if "score" in answer:
        return answer["score"]
    label = (answer.get("verdict") or {}).get("label")
    rule = (answer.get("expected") or {}).get("rule")
    if label in (None, "UNCLEAR"):
        return None
    if rule == "new":
        return int(label == "NEW")
    if rule == "abstain":
        return int(label == "NONE")
    if rule == "worlds":
        return int(bool(answer.get("worlds")))
    return None


def classify(answer, query_type, baseline=None, rec=None, key=None):
    """One dot: {status, label, form, ...} for one stored answer."""
    verdict = answer.get("verdict") or {}
    label = verdict.get("label")
    form = (answer.get("form") or {}).get("label")
    out = {"label": label, "form": form}
    if query_type in LOCALITY:
        out["kind"] = "locality"
        if label == "SAME":
            out["status"] = "kept"
        elif label == "DIFFERENT":
            out["status"] = "changed"
            out["leak"] = _leak(rec, answer.get("before"), answer.get("response"))
        else:
            out["status"] = "unclear"
        return out
    rule = (answer.get("expected") or {}).get("rule")
    out["kind"] = {"abstain": "delete", "worlds": "worlds"}.get(rule, "edit")
    score = _score(answer)
    if label is None or label == "UNCLEAR" or score is None:
        out["status"] = "unclear"
    elif score == 1:
        out["status"] = "pass"
    elif label == "ORIGINAL":
        out["status"] = "original"
    elif label == "NONE":
        out["status"] = "none"
    else:
        out["status"] = "other"
    has_original = (answer.get("expected") or {}).get("original_answer") is not None
    if has_original and baseline is not None:
        base_label = ((baseline.get("verdict") or {}).get("label"))
        out["known"] = base_label == "ORIGINAL"
        if query_type == "derived" and _determinacy(rec, key) == "determinate" and not out["known"]:
            out["counted"] = False
    return out


def _by_record(payload):
    return {e["record_id"]: e for e in (payload or {}).get("records") or []}


def _record_steps(steps):
    """{record id: [post-edit steps holding it]} in step order."""
    out = {}
    for step in sorted(steps):
        if step == 0:
            continue
        for e in steps[step].get("records") or []:
            out.setdefault(e["record_id"], []).append(step)
    return out


def method_dots(method, source=DEFAULT_SOURCE):
    """The edited records of one method's runs, and per record and query a
    dot per model (models without a run, or that did not edit the record,
    are left out: the page draws an empty ring)."""
    if method not in METHOD_KEYS:
        raise KeyError(method)
    runs = pick_runs(source).get(method, {})
    recs = _records()
    records, edited = {}, {}
    for model in MAIN_MODELS:
        info = runs.get(model)
        if not info:
            continue
        steps = _load_steps(info["_dir"])
        base = _by_record(steps.get(0))
        per_record = _record_steps(steps)
        edited[model] = sorted(per_record)
        for rid, held in per_record.items():
            end = _by_record(steps[held[-1]])[rid]
            b = base.get(rid, {}).get("queries", {})
            slot = records.setdefault(rid, {"queries": {}})
            for key, answer in end["queries"].items():
                dot = classify(answer, answer.get("query_type"), b.get(key), recs.get(rid), key)
                slot["queries"].setdefault(key, {})[model] = dot
    method_label = dict(METHODS)[method]
    return {"source": source, "method": method, "label": method_label, "models": MAIN_MODELS,
            "runs": {m: _public(i) for m, i in runs.items()}, "edited": edited, "records": records}


def _answer_view(answer, query_type, baseline=None, rec=None, key=None, step=None):
    if answer is None:
        return None
    return {"step": step, "response": answer.get("response"), "verdict": answer.get("verdict"),
            "form": answer.get("form"), "score": _score(answer) if query_type not in LOCALITY else None,
            "worlds": answer.get("worlds"),
            "dot": classify(answer, query_type, baseline, rec, key)}


def detail(method, model, record, key, source=DEFAULT_SOURCE):
    """One dot explained: the question, the answer before the edit (step 0 of
    the same run), the answer at the end of the run, and under a protocol
    that asks a record again later, the answer right after its own edit."""
    if method not in METHOD_KEYS or model not in MAIN_MODELS:
        raise KeyError(method)
    info = pick_runs(source).get(method, {}).get(model)
    if not info:
        return {"run": None, "record": record, "key": key}
    steps = _load_steps(info["_dir"])
    held = _record_steps(steps).get(record)
    if not held:
        return {"run": _public(info), "record": record, "key": key, "edited": False}
    rec = _records().get(record)
    before = _by_record(steps.get(0)).get(record, {}).get("queries", {}).get(key)
    end = _by_record(steps[held[-1]])[record]["queries"].get(key)
    first = _by_record(steps[held[0]])[record]["queries"].get(key) if len(held) > 1 else None
    any_answer = end or before or {}
    qtype = any_answer.get("query_type")
    return {
        "run": _public(info), "record": record, "key": key, "edited": True,
        "question": any_answer.get("question"), "query_type": qtype, "language": any_answer.get("language"),
        "expected": (end or {}).get("expected"),
        "determinacy": _determinacy(rec, key),
        "new_object": ((rec or {}).get("edit") or {}).get("object"),
        "before": _answer_view(before, qtype, None, rec, key, 0) if before else None,
        "after": _answer_view(end, qtype, before, rec, key, held[-1]) if end else None,
        "after_own_edit": _answer_view(first, qtype, before, rec, key, held[0]) if first else None,
    }
