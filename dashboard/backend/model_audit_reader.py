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


# The audit's default chat prompt (experiments/model_audit/audit.py,
# --instruction few_words, --chat_shots 0). Runs with another instruction or
# with chat shots are prompt variants: the Model audit page lists them, but
# the Datasets page's status, checks and dot detail read only default runs.
DEFAULT_INSTRUCTIONS = (None, "few_words", "Answer the question in a few words, without explanation.")


def is_default_prompt(summary):
    """Whether a run's summary.json used the default prompt (fields absent in
    older runs mean the default)."""
    return summary.get("instruction") in DEFAULT_INSTRUCTIONS and not summary.get("chat_shots")


def _newest_runs():
    """model -> (summary mtime, run folder) of its newest default-prompt audit
    run (is_default_prompt)."""
    runs_dir = _runs_dir()
    newest = {}
    for path in sorted(runs_dir.glob("*/summary.json")) if runs_dir and runs_dir.is_dir() else []:
        try:
            summary = json.loads(path.read_text())
        except (OSError, ValueError):
            continue
        if not is_default_prompt(summary):
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
    for r in responses:
        if str(r.get("query_type", "")).startswith("check_"):
            r["status"] = _score_status(r.get("score"))
        elif r.get("record_id"):
            by_record.setdefault(r["record_id"], []).append(r)
    for rid, rows in by_record.items():
        _resolve_rows(aq, records.get(rid), rows)


def _score_status(score):
    return GREEN if score == 1 else RED if score == 0 else YELLOW


def _resolve_rows(aq, rec, rows):
    """Set query_key, stale and status on one record's dataset query rows
    (in place), against the current record `rec` (None: every row stale)."""
    current = {}
    if rec is not None:
        for key, qtype, lang, item in aq.all_queries(rec):
            answer, _ = aq.expected(rec, qtype, item)
            if answer is not None:
                current[key] = (qtype, lang, aq.query_hash(item.get("prompt", ""), answer))
    lookup = {v: k for k, v in current.items()}
    for r in rows:
        h = _row_hash(aq, r)
        key = r.get("query_key") or lookup.get((r.get("query_type"), r.get("language"), h))
        fresh = key is not None and current.get(key, (None, None, None))[2] == h
        r["query_key"] = key
        r["stale"] = not fresh
        r["status"] = YELLOW if not fresh else _score_status(r.get("score"))


# ---------------------------------------------------------------- one dot, explained
#
# audit_detail() backs the Datasets page's audit-dot modal: one model's
# newest-run rows for one record, and per query the knowledge parts its
# answer rests on, each with that model's check status. The parts follow
# validate.py and the audit (experiments/model_audit/audit.py):
#   the fact itself (direct, paraphrase, cross-lingual): edit.premises
#   a propositional query: the premises and its side fact (when it has a check)
#   a derived query: the original fact (its direct and paraphrase status;
#     not for insert or RBox), every bridge and revision fact
#     (validate.unstated_facts; ones stated in the prompt are listed as
#     "given" and not counted) and the relation property its derivation
#     relies on (validate.relation_property)
#   locality queries: none
# A check part is green or red by its score; yellow when not asked, unclear,
# or stale (the run asked a different prompt or answer than the record's
# check, or relation_checks.json, holds now).
#
# Verdict (diagnose()), for a red answer:
#   any red part        "missing"      Missing knowledge: <the red parts>
#   else a yellow part  "not_audited"  Some parts not audited: <those parts>
#   else all green      "not_combined" Knew every part but did not combine them
#   else (no parts)     "no_parts"     No parts listed: the model does not know this fact
# A green answer: "ok" (or "green_despite" when some part is red); a yellow
# answer: "answer_not_audited"; a query the audit never asks: "na".

SIDS_DIR = config.DATASETS_DIR / "SidsDataset"
COUNTED = (GREEN, RED, YELLOW)  # part statuses that count; "given" does not


def _sid():
    """(validate module, relations, relation_checks) from datasets/SidsDataset,
    reloaded when validate.py, RELATIONS.md or relation_checks.json changes."""
    paths = [SIDS_DIR / "validate.py", SIDS_DIR / "RELATIONS.md", SIDS_DIR / "relation_checks.json"]
    sig = tuple(_mtime(p) for p in paths)
    hit = _cache.get("sid")
    if hit and hit[0] == sig:
        return hit[1]
    spec = importlib.util.spec_from_file_location("sids_validate_audit", paths[0])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    value = (module, module.load_relations()[0], module.load_relation_checks())
    _cache["sid"] = (sig, value)
    return value


_KEEP = ("record_id", "query_type", "language", "prompt", "query_key", "query_hash", "rule", "original_answer",
         "new_answer", "fact", "relation", "tag", "response", "label", "reason", "score")


def _run_detail_rows(folder):
    """(record_id -> [rows], (relation, tag) -> row) of one run, with the
    fields the modal shows, cached on responses.jsonl's mtime."""
    path = folder / "responses.jsonl"
    mtime = _mtime(path)
    if mtime is None:
        return {}, {}
    hit = _cache.get(("detail", str(path)))
    if hit and hit[0] == mtime:
        return hit[1]
    by_record, relations = {}, {}
    for line in path.read_text().splitlines():
        try:
            r = json.loads(line)
        except ValueError:
            continue
        r = {k: r.get(k) for k in _KEEP}
        if r["query_type"] == "check_relation":
            relations[(r["relation"], r["tag"])] = r  # asked once per run; the last wins
        elif r["record_id"]:
            by_record.setdefault(r["record_id"], []).append(r)
    _cache[("detail", str(path))] = (mtime, (by_record, relations))
    return by_record, relations


def _check_part(kind, text, row, current):
    """One knowledge part with a check: its status from the run's row, yellow
    when not asked, unclear or asked differently than `current` (prompt, answer)."""
    part = {"kind": kind, "text": text, "prompt": current[0] if current else None,
            "expected": current[1] if current else None, "response": None, "label": None, "reason": None,
            "stale": False}
    if row is None:
        part["status"] = YELLOW
        return part
    stale = current is None or (row.get("prompt"), row.get("original_answer")) != tuple(current)
    part.update(response=row.get("response"), label=row.get("label"), reason=row.get("reason"), stale=stale,
                status=YELLOW if stale else _score_status(row.get("score")))
    return part


def diagnose(status, parts, fact_like=True):
    """The verdict for one answer's status given its knowledge parts (rules above)."""
    counted = [p for p in parts if p["status"] in COUNTED]
    red = [p["text"] for p in counted if p["status"] == RED]
    yellow = [p["text"] for p in counted if p["status"] == YELLOW]
    if status == NOT_ASKED:
        return {"kind": "na", "text": "Not asked: the query has no pre-edit answer to check.", "parts": []}
    if status == YELLOW:
        return {"kind": "answer_not_audited",
                "text": "Answer not audited (or stale since the record changed, or the judge could not label it).",
                "parts": []}
    if status == GREEN:
        if red:
            return {"kind": "green_despite", "text": "Answered as expected, although these parts failed", "parts": red}
        return {"kind": "ok", "text": "Answered as expected.", "parts": []}
    if red:
        return {"kind": "missing", "text": "Missing knowledge", "parts": red}
    if yellow:
        return {"kind": "not_audited", "text": "Some parts not audited", "parts": yellow}
    if counted:
        return {"kind": "not_combined", "text": "Knew every part but did not combine them", "parts": []}
    if fact_like:
        return {"kind": "no_parts", "text": "No parts listed: the model does not know this fact", "parts": []}
    return {"kind": "no_parts",
            "text": "No parts to check: everything this answer uses is given in the prompt, so the model did not draw the inference",
            "parts": []}


def record_detail(aq, sid, relations, relation_checks, rec, rows, relation_rows):
    """One model on one current record: every query with its row and status,
    and the knowledge parts and verdict behind it, plus the fact itself.
    `rows`: the model's rows for the record (queries and check_fact rows);
    `relation_rows`: (relation, tag) -> the model's check_relation row."""
    query_rows = [dict(r) for r in rows or [] if not str(r.get("query_type", "")).startswith("check_")]
    fact_rows = {r.get("fact"): r for r in rows or [] if r.get("query_type") == "check_fact"}
    _resolve_rows(aq, rec, query_rows)
    by_key = {}
    for r in query_rows:  # a fresh row beats a stale one; the last wins
        if r["query_key"] is not None and (r["query_key"] not in by_key or not r["stale"] or by_key[r["query_key"]]["stale"]):
            by_key[r["query_key"]] = r
    status = record_status(aq, rec, [{"key": r["query_key"], "hash": _row_hash(aq, r), "query_type": r.get("query_type"),
                                      "language": r.get("language"), "score": r.get("score")} for r in query_rows])
    checks = {c.get("fact"): (c.get("prompt"), c.get("answer")) for c in rec.get("checks") or []}

    def fact_part(kind, fact, stated=False):
        if stated:
            return {"kind": kind, "text": fact, "status": "given"}
        return _check_part(kind, fact, fact_rows.get(fact), checks.get(fact))

    premises = [fact_part("premise", p) for p in (rec.get("edit") or {}).get("premises") or []]
    insert, rbox = rec.get("edit_operation") == "insert", rec.get("box") == "rbox"
    fact_keys = aq.fact_keys(rec)
    e = rec.get("edit") or {}
    fact_text = e.get("original") or e.get("statement")
    queries = {}
    for key, qtype, lang, item in aq.all_queries(rec):
        answer, rule = aq.expected(rec, qtype, item)
        if qtype in ("direct", "paraphrase", "cross_lingual"):
            parts = list(premises)
        elif qtype == "propositional":
            side = item.get("side_fact")
            parts = list(premises) + ([fact_part("side_fact", side)] if side in checks else [])
        elif qtype == "derived":
            parts = []
            if not insert and not rbox and status["fact"] != NOT_ASKED:
                parts.append({"kind": "fact", "text": fact_text, "status": status["fact"],
                              "keys": [k for k in fact_keys if k in status["queries"]]})
            for b in item.get("bridge") or []:
                parts.append(fact_part("bridge", b, stated=bool(item.get("bridge_in_prompt"))))
            for b in item.get("revision_facts") or []:
                parts.append(fact_part("revision", b, stated=sid.revision_in_prompt(item)))
            prop = sid.relation_property(rec, item, relations)
            if prop:
                entry = (relation_checks.get(prop[0]) or {}).get(prop[1])
                part = _check_part("relation", f"{prop[0]}: {prop[1]}", relation_rows.get(prop),
                                   entry and (entry.get("prompt"), entry.get("answer")))
                part.update(relation=prop[0], tag=prop[1])
                parts.append(part)
        else:
            parts = []
        st = status["queries"].get(key, NOT_ASKED)
        row = by_key.get(key)
        queries[key] = {
            "key": key, "query_type": qtype, "language": lang, "prompt": item.get("prompt"),
            "expected": answer, "rule": rule, "status": st,
            "response": row and row.get("response"), "label": row and row.get("label"),
            "reason": row and row.get("reason"), "score": row and row.get("score"), "stale": bool(row and row["stale"]),
            "asked": row is not None, "parts": parts,
            "verdict": diagnose(st, parts, fact_like=qtype != "derived"),
        }
    fact = {"text": fact_text, "status": status["fact"], "keys": fact_keys, "parts": premises,
            "verdict": diagnose(status["fact"], premises)}
    return {"fact": fact, "queries": queries}


def audit_detail(record_id, model):
    """audit_detail payload for one record and one model's newest run:
    {"record", "model", "run", "audited_at", "fact": {text, status, keys,
    parts, verdict}, "queries": {key: {prompt, expected, rule, status,
    response, label, reason, score, stale, asked, parts, verdict}}}.
    KeyError when the record does not exist."""
    with _lock:
        rec = _records().get(record_id)
        if rec is None:
            raise KeyError(record_id)
        aq = _audit_queries()
        sid, relations, relation_checks = _sid()
        newest = _newest_runs().get(model)
        by_record, relation_rows = ({}, {}) if newest is None else _run_detail_rows(newest[1])
        rows = by_record.get(record_id, [])
    detail = record_detail(aq, sid, relations, relation_checks, rec, rows, relation_rows)
    return {"record": record_id, "model": model, "run": newest and newest[1].name,
            "audited_at": newest and datetime.fromtimestamp(newest[0], timezone.utc).isoformat(timespec="seconds"),
            **detail}
