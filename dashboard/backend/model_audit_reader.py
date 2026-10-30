"""Model audit results (experiments/model_audit): for each model, whether it
already gives Sid's Dataset's original answers before any editing. Read from
<out_root>/runs/<run>/summary.json (counts) and responses.jsonl (every query,
response and judge label).

audit_status() turns the newest run per model into a status per Sid's Dataset
record and query (green, red, yellow) for the Datasets page; which queries
the audit asks, their keys and hashes come from
experiments/model_audit/audit_queries.py, the file the audit itself uses."""
import importlib.util
import json
import threading
from datetime import datetime, timezone
from pathlib import Path

import config
import results_reader

EXPERIMENT = "model_audit"
AUDIT_QUERIES = config.EXPERIMENTS_DIR / "model_audit" / "audit_queries.py"
SIDS_RECORDS = config.DATASETS_DIR / "SidsDataset" / "records"
# The status columns open on the four main instruct models (CRITERIA's
# AUDIT_MODELS), then the others in family order, then anything else.
MAIN_MODELS = ["qwen3-4b-instruct-2507", "olmo-3-7b-instruct", "llama-3.1-8b-instruct", "mistral-7b-instruct-v0.1"]
OTHER_ORDER = ["qwen3-4b-base", "olmo-3-7b-base", "llama-3.1-8b", "mistral-7b-v0.1", "smollm3-3b-base", "smollm3-3b",
               "map-neo-7b", "map-neo-7b-instruct"]
GREEN, RED, YELLOW, NOT_ASKED = "green", "red", "yellow", "na"


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
    _annotate(responses)
    return {"run": name, "summary": summary, "responses": responses}


def _newest_runs():
    """model -> (summary mtime, run folder) of its newest audit run."""
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
    return newest


def check_results():
    """The newest audit run per model, reduced to its checks: every fact check
    (record_id, fact) and relation check (relation, tag) with its score and the
    model's response, for the Datasets page's derivation view."""
    out = []
    for model, (mtime, folder) in sorted(_newest_runs().items()):
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


# ---------------------------------------------------------------- per-query status
#
# Rules (one model, one query of the current record):
#   green   the newest run asked it and the judge's label passes (score 1)
#   red     it was asked and fails (score 0)
#   yellow  not asked (no run, record or query absent from the run), stale
#           (the stored hash of prompt and expected answer differs from the
#           current record's), or the judge could not label it (score None)
#   na      the audit never asks it (no pre-edit answer: a fictional insert's
#           own questions, a derived query without original_answer)
# A fact is na when none of its fact queries (direct and paraphrase; RBox:
# direct and the instance questions) is asked; otherwise yellow if any is
# yellow, green if every asked one is green, else red.

_lock = threading.Lock()
_cache = {}


def _audit_queries():
    """experiments/model_audit/audit_queries.py, reloaded when it changes."""
    mtime = AUDIT_QUERIES.stat().st_mtime
    hit = _cache.get("aq")
    if hit and hit[0] == mtime:
        return hit[1]
    spec = importlib.util.spec_from_file_location("audit_queries", AUDIT_QUERIES)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _cache["aq"] = (mtime, module)
    return module


def _records():
    """Current Sid's Dataset records by id, reread when any file changes."""
    paths = sorted(SIDS_RECORDS.glob("*/*/*.json")) if SIDS_RECORDS.is_dir() else []
    stamps = []
    for p in paths:
        try:
            stamps.append((str(p), p.stat().st_mtime))
        except OSError:
            continue
    sig = tuple(stamps)
    hit = _cache.get("records")
    if hit and hit[0] == sig:
        return hit[1]
    out = {}
    for path, _ in stamps:
        try:
            rec = json.loads(Path(path).read_text())
        except (OSError, ValueError):
            continue
        if rec.get("id"):
            out[rec["id"]] = rec
    _cache["records"] = (sig, out)
    return out


def _row_hash(aq, row):
    """The hash a row was asked under: stored, or (older runs) recomputed from
    its prompt and the answer the judge was shown."""
    if row.get("query_hash"):
        return row["query_hash"]
    shown = row.get("original_answer") if row.get("original_answer") is not None else row.get("new_answer")
    return aq.query_hash(row.get("prompt", ""), shown)


def _run_rows(folder):
    """record_id -> [rows] of one run's dataset queries (checks left out),
    cached on responses.jsonl's mtime."""
    path = folder / "responses.jsonl"
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return {}
    hit = _cache.get(("rows", str(path)))
    if hit and hit[0] == mtime:
        return hit[1]
    aq = _audit_queries()
    out = {}
    for line in path.read_text().splitlines():
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if not r.get("record_id") or str(r.get("query_type", "")).startswith("check_"):
            continue
        out.setdefault(r["record_id"], []).append({
            "key": r.get("query_key"), "hash": _row_hash(aq, r), "query_type": r.get("query_type"),
            "language": r.get("language"), "score": r.get("score")})
    _cache[("rows", str(path))] = (mtime, out)
    return out


def record_status(aq, rec, rows):
    """{"fact": status, "queries": {key: status}} for one model on one
    current record, given that model's rows for it (the rules above)."""
    rows = rows or []
    keyed = {r["key"]: r for r in rows if r.get("key")}
    unkeyed = {(r["query_type"], r["language"], r["hash"]): r for r in rows if not r.get("key")}
    queries = {}
    for key, qtype, lang, item in aq.all_queries(rec):
        answer, _ = aq.expected(rec, qtype, item)
        if answer is None:
            queries[key] = NOT_ASKED
            continue
        h = aq.query_hash(item.get("prompt", ""), answer)
        row = keyed.get(key)
        if row is not None and row["hash"] != h:
            row = None  # stale: the record changed after the audit
        if row is None:
            row = unkeyed.get((qtype, lang, h))  # a run from before query keys
        score = None if row is None else row["score"]
        queries[key] = GREEN if score == 1 else RED if score == 0 else YELLOW
    got = [queries[k] for k in aq.fact_keys(rec) if queries.get(k, NOT_ASKED) != NOT_ASKED]
    fact = (NOT_ASKED if not got else YELLOW if YELLOW in got else GREEN if all(s == GREEN for s in got) else RED)
    return {"fact": fact, "queries": queries}


def _model_rank(model):
    if model in MAIN_MODELS:
        return (0, MAIN_MODELS.index(model), model)
    if model in OTHER_ORDER:
        return (1, OTHER_ORDER.index(model), model)
    return (2, 0, model)


def audit_status():
    """For the newest audit run per model, a status per current record: its
    fact and every query (green, red, yellow, na; rules above).

    {"models": [ordered], "main_models": [...], "runs": {model: run},
     "audited_at": {model: iso}, "records": {id: {"fact": {model: status},
     "queries": {key: {model: status}}}}}, status green, red or yellow; a
    model left out of a map: the audit never asks that query (na).

    Cached on the records' and the newest runs' modification times."""
    with _lock:
        newest = _newest_runs()
        records = _records()
        sig = (id(records), AUDIT_QUERIES.stat().st_mtime,
               tuple((m, mt, str(f), _mtime(f / "responses.jsonl")) for m, (mt, f) in sorted(newest.items())))
        hit = _cache.get("status")
        if hit and hit[0] == sig:
            return hit[1]
        aq = _audit_queries()
        models = sorted(newest, key=_model_rank)
        rows = {m: _run_rows(newest[m][1]) for m in models}
        out = {}
        for rid, rec in records.items():
            fact, queries = {}, {}
            for m in models:
                st = record_status(aq, rec, rows[m].get(rid))
                # "na" is left out to keep the payload small: a model missing
                # from a map means the audit never asks that query.
                if st["fact"] != NOT_ASKED:
                    fact[m] = st["fact"]
                for key, s in st["queries"].items():
                    if s != NOT_ASKED:
                        queries.setdefault(key, {})[m] = s
            out[rid] = {"fact": fact, "queries": queries}
        result = {
            "models": models,
            "main_models": [m for m in MAIN_MODELS],
            "runs": {m: newest[m][1].name for m in models},
            "audited_at": {m: datetime.fromtimestamp(newest[m][0], timezone.utc).isoformat(timespec="seconds")
                           for m in models},
            "records": out,
        }
        _cache["status"] = (sig, result)
        return result


def restrict(data, keep):
    """audit_status() reduced to the models in `keep` (a copy; the cache stays whole)."""
    models = [m for m in data["models"] if m in keep]
    pick = lambda d: {m: d[m] for m in models if m in d}  # noqa: E731
    return {**data, "models": models, "all_models": data["models"], "runs": pick(data["runs"]), "audited_at": pick(data["audited_at"]),
            "records": {rid: {"fact": pick(v["fact"]), "queries": {k: pick(q) for k, q in v["queries"].items()}}
                        for rid, v in data["records"].items()}}


def _mtime(path):
    try:
        return path.stat().st_mtime
    except OSError:
        return None


def _annotate(responses):
    """Give each dataset row of a run its query_key (resolved for runs from
    before keys) and status against the current record; checks get a status
    from their score."""
    aq = _audit_queries()
    records = _records()
    by_record = {}
    for i, r in enumerate(responses):
        if str(r.get("query_type", "")).startswith("check_"):
            s = r.get("score")
            r["status"] = GREEN if s == 1 else RED if s == 0 else YELLOW
        elif r.get("record_id"):
            by_record.setdefault(r["record_id"], []).append(i)
    for rid, idx in by_record.items():
        rec = records.get(rid)
        current = {}
        if rec is not None:
            for key, qtype, lang, item in aq.all_queries(rec):
                answer, _ = aq.expected(rec, qtype, item)
                if answer is not None:
                    current[key] = (qtype, lang, aq.query_hash(item.get("prompt", ""), answer))
        lookup = {v: k for k, v in current.items()}
        for i in idx:
            r = responses[i]
            h = _row_hash(aq, r)
            key = r.get("query_key") or lookup.get((r.get("query_type"), r.get("language"), h))
            fresh = key is not None and current.get(key, (None, None, None))[2] == h
            s = r.get("score")
            r["query_key"] = key
            r["stale"] = not fresh
            r["status"] = YELLOW if not fresh else GREEN if s == 1 else RED if s == 0 else YELLOW
