"""Sid's Dataset's evaluation for the main experiments (evaluation mode "sid_main").

It extends the "sid" evaluation (sid_evaluation.py), whose generations, judge
pass and reliability / locality / fluency it reuses unchanged, and replaces
how derived queries are read. Hyperparameter sweeps keep "sid" for now.

Why: under "sid" an indeterminate derived query passes when the answer
matches any world, and in 503 of 572 indeterminate queries some world's
answer is the original answer (77 of 123 replace and 92 of 129 delete
records with worlds have a world that keeps every original answer), so a
model that never applied the edit passes most of them.

1. Portability (the headline) = determinate derived queries only, one
   answer reachable only by using the edit, counted over the "known" ones
   (the unedited model gave the original answer at step 0): the definition
   hyperparameter selection already uses (dashboard/backend/hparam_sweeps.py,
   decided 2026-11-03, docs/bug_log.md bug 8), where an unedited model
   otherwise "passes" about 15% by a lucky yes/no. The block also holds all
   determinate queries, and RBox records' derived queries (no determinacy)
   apart under "rbox". With no step 0 the headline is over all determinate
   queries.

2. Indeterminate derived queries measure change, not correctness. Each
   answer is one of
     unchanged          the judge says it gives the original answer
     changed_to_world   another answer that is some world's (abstaining
                        counts where a world's answer is null)
     changed_other      an answer no world gives
   with the rates over judged answers (UNCLEAR left out), and also over the
   "known" answers (the model gave the original answer at step 0; changing
   an answer the model never held means little). Every unchanged answer is
   then diagnosed from its record at the same step:
     fits_world_propagated      the record's indeterminate answers all fit
                                one world, and every determinate derived
                                query of the record passed: the edit spread,
                                and the answer is what a world that stored
                                the fact by name predicts
     fits_world_not_propagated  they fit one world, but some determinate
                                query failed: more likely the edit did not
                                spread at all
     mixed_worlds               the record's answers fit no single world
     no_determinate             the record has no judged determinate query
   Which world a model is in can't be read off its weights; this is the
   behavioural evidence there is. (A world's `assumes` sentences describe
   the world, "'X' gives way: ...", and are not facts to hint with.)

3. Hinted determinate queries (extra probes): the question asked again with
   the query's bridge premises in front ("Sydney is in New South Wales. In
   which state or territory is the capital of Australia?"). The edited fact
   itself is never given: it must come from the weights. Queries with no
   bridge (one hop from the edit) get no hint, and neither do queries whose
   bridge the question already states (bridge_in_prompt): their plain
   answer already is the hinted test, reported apart as premises_in_prompt
   (a failure there means the edit is not integrated). Of 1,468 determinate
   queries, 554 get a hint and 754 state their premises. Known limit: a
   bridge can hold a fact only the pre-edit answer uses (literature_arts-
   replace-0001: "No part of Romeo and Juliet is set in Florence"); such a
   hint pulls toward the original, which the control below does not catch.
   Per query, at a step with probes:
     propagated       the plain question passes
     retrieval        only the hinted one passes: the model holds the edit
                      but does not bring the bridge fact to it unprompted
     not_integrated   both fail: even with the premises given, the edit is
                      not used
   Control: the same hinted questions at step 0, before any edit. A hint
   that already yields the new answer there gives the answer away; such
   queries are counted under hint_leak and left out of the split.

4. Reasoning prompts (extra probes, replace and insert only: a delete's
   answer is "does not know", which no chain reasons to): each determinate
   derived question with an instruction to list the facts needed, reason
   step by step and end with "Answer: <answer>", without the short-answer
   instruction, up to REASONING_MAX_NEW_TOKENS tokens. The final answer is
   labelled by the answer judge (passes like the plain query), and the
   whole reasoning by the reasoning judge (judge.label_reasoning) against
   the record's chain: CORRECT, MISSED_EDIT, MISSED_FACT, WRONG_STEP,
   WRONG_FINAL or UNCLEAR, with the first reference step it gets wrong.

The extra probes are generated at step 0 (the control) and at the final
checkpoint, or every group's checkpoint under an edit protocol, into
samples/sid_main_step_<step>.json; they are not asked by SCR/IKE, which
answer through their own context. Judging runs after "sid"'s judging, with
the same judge. finalize() writes evaluations["sid_main"] into each
checkpoint row and returns the summary entry, whose headline portability is
the determinate one.

Standard library only (the judge and generation are passed in).
"""
import json
import os
import re
from collections import Counter, defaultdict

import sid_evaluation as SE

J, AQ, sids_requests = SE.J, SE.AQ, SE.sids_requests

SAMPLE_PREFIX = "sid_main_step_"
REASONING_MAX_NEW_TOKENS = 384
REASONING_INSTRUCTION = ("Answer the question. First list the facts you need to answer it, one per line. "
                         "Then reason step by step from those facts. End with a last line of the form "
                         "\"Answer: <your answer>\".")
UNCHANGED_DIAGNOSES = ("fits_world_propagated", "fits_world_not_propagated", "mixed_worlds", "no_determinate")
HINT_DIAGNOSES = ("propagated", "retrieval", "not_integrated", "hint_leak", "unclear")


def metadata():
    return {"evaluation": "sid_main", "extends": "sid", "reasoning_rubric": J.REASONING_RUBRIC_VERSION,
            "reasoning_max_new_tokens": REASONING_MAX_NEW_TOKENS, "reasoning_instruction": REASONING_INSTRUCTION,
            "headline": {"edit_succ": "reliability (sid)", "portability": "known determinate derived queries",
                         "locality": "locality (sid)", "fluency": "fluency (sid)"}}


def sample_path(run_dir, step):
    return os.path.join(run_dir, "samples", f"{SAMPLE_PREFIX}{step:06d}.json")


def probe_steps_wanted(step, total_steps, edit_mode):
    """Whether a checkpoint asks the extra probes: step 0 (the control), the
    final step, and under an edit protocol every group's checkpoint."""
    return step == 0 or step == total_steps or bool(edit_mode)


# ------------------------------------------------------------------ probes

def hint_question(bridge, question):
    """The question with its bridge premises in front, as one line (so the
    few-shot Question:/Answer: format still holds)."""
    facts = " ".join(s.strip() for s in bridge if s and s.strip())
    return f"{facts} {question}" if facts else None


def render_reasoning(question, fmt, tok=None):
    """A reasoning prompt: chat models get one user turn with
    REASONING_INSTRUCTION and the question (no worked examples and no
    short-answer instruction, which would forbid the reasoning); other
    formats a plain Question: block followed by the instruction."""
    if fmt == "chat":
        return sids_requests.render_chat([{"role": "user", "content": f"{REASONING_INSTRUCTION}\n\n{question}"}], tok)
    return f"Question: {question}\n{REASONING_INSTRUCTION}\nFacts:"


_FINAL = re.compile(r"^\W*(?:final\s+)?answer\W*:\s*(.+?)\s*$", re.I | re.M)


def final_answer(text):
    """(answer, found): the last "Answer: ..." line of a reasoning
    generation, else its last non-empty line (found False)."""
    matches = _FINAL.findall(text or "")
    if matches:
        return matches[-1].strip().strip("*").strip(), True
    lines = [l.strip() for l in (text or "").splitlines() if l.strip()]
    return (lines[-1] if lines else ""), False


def record_probes(rec):
    """The extra probes of one record: (key, kind, base_key, question). kind
    is "hinted" or "reasoning"; base_key is the derived query's audit key."""
    out = []
    op = rec["edit_operation"]
    for key, qtype, _, item in AQ.all_queries(rec):
        if qtype != "derived" or item.get("world_answers"):
            continue
        hinted = None if item.get("bridge_in_prompt") else hint_question(item.get("bridge") or [], item["prompt"])
        if hinted:
            out.append((f"hinted:{key}", "hinted", key, hinted))
        if op != "delete" and item.get("chain"):
            out.append((f"reasoning:{key}", "reasoning", key, item["prompt"]))
    return out


def collect_probes(requests, records, fmt, tok, generate, step, case_offset=0):
    """Ask every extra probe of every request's record. `generate(prompts,
    long)` answers rendered prompts at once ([(answer, raw)]); long=True is
    the reasoning batch (no cut, REASONING_MAX_NEW_TOKENS). Returns the
    step's payload for samples/."""
    rows = {"hinted": [], "reasoning": []}
    for i, request in enumerate(requests):
        rid = request["sids"]["id"]
        rec = records[rid]
        for key, kind, base, question in record_probes(rec):
            prompt = (render_reasoning(question, fmt, tok) if kind == "reasoning"
                      else sids_requests.render_prompt(question, fmt, tok))
            rows[kind].append((i, rid, rec, key, kind, base, question, prompt))
    by_record = {}
    for kind, long in (("hinted", False), ("reasoning", True)):
        if not rows[kind]:
            continue
        answers = generate([r[-1] for r in rows[kind]], long)
        for (i, rid, rec, key, _, base, question, _), (answer, raw) in zip(rows[kind], answers):
            entry = by_record.setdefault(rid, {"record_id": rid, "case_id": case_offset + i,
                                               "edit_operation": rec["edit_operation"], "probes": {}})
            probe = {"kind": kind, "base_key": base, "question": question, "raw": raw}
            if kind == "reasoning":
                probe["reasoning"] = answer
                probe["response"], probe["final_found"] = final_answer(answer)
            else:
                probe["response"] = answer
            entry["probes"][key] = probe
    return {"step": step, "prompt_format": fmt, "evaluation": "sid_main", "judged": False,
            "records": list(by_record.values())}


# ------------------------------------------------------------------ judging

def _base_queries(rec):
    """{audit key: sid_evaluation query} of a record's derived queries."""
    return {q["key"]: q for q in SE.record_queries(rec) if q["query_type"] == "derived"}


def _items(rec):
    return {key: item for key, qtype, _, item in AQ.all_queries(rec) if qtype == "derived"}


def judge_probes(payloads, records, judge, salt=""):
    """Label every stored probe in place: the final answer of every probe by
    the answer judge (as its derived query is judged), and every reasoning
    trace by the reasoning judge. Returns the call counts."""
    answer_jobs, reasoning_jobs, pending = {}, {}, []
    for payload in payloads:
        for entry in payload["records"]:
            rec = records[entry["record_id"]]
            base, items = _base_queries(rec), _items(rec)
            for key, p in entry["probes"].items():
                q = base[p["base_key"]]
                jq = SE.judge_query(q)  # the bare question and candidates, as the plain query is judged
                ajob = (json.dumps(jq, sort_keys=True, ensure_ascii=False), p["response"])
                answer_jobs.setdefault(ajob, jq)
                rjob = None
                if p["kind"] == "reasoning":
                    edit, item = rec["edit"], items[p["base_key"]]
                    ritem = {"question": q["question"], "new_fact": edit["statement"],
                             "old_fact": edit.get("original"), "chain": item["chain"],
                             "answer": q.get("new_answer"), "reasoning": p.get("reasoning") or ""}
                    rjob = json.dumps(ritem, sort_keys=True, ensure_ascii=False)
                    reasoning_jobs.setdefault(rjob, ritem)
                pending.append((p, q, ajob, rjob))
    akeys, rkeys = list(answer_jobs), list(reasoning_jobs)
    averdicts = judge.label_answers([(answer_jobs[k], k[1]) for k in akeys], salt=salt) if akeys else []
    rverdicts = judge.label_reasoning([reasoning_jobs[k] for k in rkeys]) if rkeys else []
    agot, rgot = dict(zip(akeys, averdicts)), dict(zip(rkeys, rverdicts))
    for p, q, ajob, rjob in pending:
        p["verdict"] = dict(agot[ajob])
        p["expected"] = {k: q[k] for k in ("rule", "original_answer", "new_answer") if k in q}
        if rjob is not None:
            p["trace"] = dict(rgot[rjob])
    for payload in payloads:
        payload["judged"] = True
    return {"probe_answer_calls": len(akeys), "reasoning_calls": len(rkeys)}


# ------------------------------------------------------------------ scoring

def change_class(item):
    """unchanged / changed_to_world / changed_other for an indeterminate
    item of sid_evaluation.scored_items, None when UNCLEAR."""
    if item["score"] is None:
        return None
    if item["label"] == "ORIGINAL":
        return "unchanged"
    return "changed_to_world" if item["worlds"] else "changed_other"


def _rates(classes):
    counts = Counter(c for c in classes if c is not None)
    judged = sum(counts.values())
    out = {k: SE._pct(counts[k], judged) for k in ("unchanged", "changed_to_world", "changed_other")}
    out["changed"] = SE._pct(counts["changed_to_world"] + counts["changed_other"], judged)
    out.update(counts={k: counts[k] for k in ("unchanged", "changed_to_world", "changed_other")},
               judged=judged, unclear=sum(c is None for c in classes), total=len(classes))
    return out


def indeterminate_metrics(items):
    """Change rates and the diagnosis of unchanged answers, from one step's
    sid items."""
    by_record = defaultdict(list)
    for i in items:
        if i["query_type"] == "derived":
            by_record[i["record_id"]].append(i)
    classes, known, diagnosis, worlds_fit = [], [], Counter(), Counter()
    for rid, rec_items in by_record.items():
        ind = [i for i in rec_items if i["indeterminate"]]
        if not ind:
            continue
        det = [i for i in rec_items if not i["indeterminate"] and i["score"] is not None]
        sets = [set(i["worlds"] or ()) for i in ind if i["score"] is not None]
        fit = set.intersection(*sets) if sets else set()
        worlds_fit["one_world" if fit else "mixed"] += 1
        for i in ind:
            c = change_class(i)
            classes.append(c)
            if i.get("known"):
                known.append(c)
            if c != "unchanged":
                continue
            if not det:
                diagnosis["no_determinate"] += 1
            elif not fit:
                diagnosis["mixed_worlds"] += 1
            elif all(d["score"] == 1 for d in det):
                diagnosis["fits_world_propagated"] += 1
            else:
                diagnosis["fits_world_not_propagated"] += 1
    out = _rates(classes)
    out["known"] = _rates(known)
    out["unchanged_diagnosis"] = {k: diagnosis[k] for k in UNCHANGED_DIAGNOSES}
    out["records"] = dict(worlds_fit)
    return out


def probe_items(payload, records):
    """One flat item per judged probe of a step."""
    out = []
    for entry in (payload or {}).get("records", []):
        rec = records[entry["record_id"]]
        base = _base_queries(rec)
        for key, p in entry["probes"].items():
            if "verdict" not in p:
                continue
            score, _ = SE.score_answer(base[p["base_key"]], p["verdict"], rec["edit_operation"])
            p["score"] = score
            out.append({"record_id": entry["record_id"], "key": key, "kind": p["kind"], "base_key": p["base_key"],
                        "operation": rec["edit_operation"], "label": p["verdict"]["label"], "score": score,
                        "trace": (p.get("trace") or {}).get("label"), "trace_step": (p.get("trace") or {}).get("step"),
                        "final_found": p.get("final_found")})
    return out


def premises_in_prompt(records):
    """{(record id, audit key)} of determinate derived queries whose question
    already states their bridge (bridge_in_prompt)."""
    return {(rid, key) for rid, rec in records.items() for key, qtype, _, item in AQ.all_queries(rec)
            if qtype == "derived" and not item.get("world_answers") and item.get("bridge")
            and item.get("bridge_in_prompt")}


def hinted_metrics(items, probes, control, in_prompt=frozenset()):
    """Hinted answers' pass rate and, per determinate query with a hint, the
    propagated / retrieval / not_integrated split. control: step 0's probe
    items (None at step 0 itself, or when there is no step 0). in_prompt:
    premises_in_prompt's keys, whose plain answers are reported apart."""
    hinted = [p for p in probes if p["kind"] == "hinted"]
    plain = {(i["record_id"], i["key"]): i for i in items if i["query_type"] == "derived"}
    leaked = {(c["record_id"], c["base_key"]) for c in (control or ())
              if c["kind"] == "hinted" and c["label"] == "NEW"}
    split = Counter()
    for h in hinted:
        base = plain.get((h["record_id"], h["base_key"]))
        if base is None or base["score"] is None or h["score"] is None:
            split["unclear"] += 1
        elif base["score"] == 1:
            split["propagated"] += 1
        elif (h["record_id"], h["base_key"]) in leaked:
            split["hint_leak"] += 1
        elif h["score"] == 1:
            split["retrieval"] += 1
        else:
            split["not_integrated"] += 1
    out = {**SE.block(hinted), "diagnosis": {k: split[k] for k in HINT_DIAGNOSES},
           "premises_in_prompt": SE.block([i for i in items if (i["record_id"], i["key"]) in in_prompt])}
    if control is not None:
        ctrl = [c for c in control if c["kind"] == "hinted" and c["operation"] != "delete"]
        judged = [c for c in ctrl if c["score"] is not None]
        out["control_leak"] = {"score": SE._pct(sum(c["label"] == "NEW" for c in judged), len(judged)),
                               "leaked": sum(c["label"] == "NEW" for c in judged), "judged": len(judged)}
    return out


def reasoning_metrics(probes):
    r = [p for p in probes if p["kind"] == "reasoning"]
    traces = Counter(p["trace"] for p in r if p["trace"])
    return {**SE.block(r), "traces": {k: traces[k] for k in J.REASONING_LABELS},
            "first_wrong_step": dict(sorted(Counter(str(p["trace_step"]) for p in r
                                                    if p["trace"] not in (None, "CORRECT", "UNCLEAR")).items())),
            "no_answer_line": sum(p["final_found"] is False for p in r)}


def compute_metrics(sid, items, probes=None, control=None, in_prompt=frozenset()):
    """The sid_main evaluation of one step: sid's metrics for that step
    (edit success, locality, fluency), its items, and the step's judged
    probe items if it asked them."""
    derived = [i for i in items if i["query_type"] == "derived"]
    determinate = [i for i in derived if i["problem"] == "determinate"]
    portability = {**SE.block(determinate), "by_logic": SE._by(determinate, "logic"),
                   "by_derivation": SE._by(determinate, "derivation"), "by_operation": SE._by(determinate, "operation"),
                   "rbox": SE.block([i for i in derived if not i["indeterminate"] and i["problem"] != "determinate"])}
    headline = portability["known"] if "known" in portability else portability
    metrics = {"portability": portability, "indeterminate": indeterminate_metrics(items)}
    if probes is not None:
        metrics["hinted"] = hinted_metrics(items, probes, control, in_prompt)
        metrics["reasoning"] = reasoning_metrics(probes)
    return {
        "edit_succ": sid["edit_succ"], "portability": headline["score"], "locality": sid["locality"],
        "fluency": sid["fluency"], "well_formed": sid.get("well_formed"),
        "coverage": {**sid["coverage"], "portability": {"scored": headline.get("scored"), "total": headline["total"]}},
        "metrics": metrics, "records": sid["records"],
    }


# ------------------------------------------------------------------ the run

def _load(paths):
    out = []
    for p in paths:
        with open(p) as f:
            out.append(json.load(f))
    return out


def finalize(run_dir, ckpt_path, records, judge, salt="", grouped=False):
    """After sid_evaluation.finalize (whose judged samples it reads): judge
    the extra probes, write evaluations["sid_main"] into each checkpoint row,
    and return (summary entry, info). The summary entry is the last
    checkpoint's, or under an edit protocol every group's items pooled."""
    samples = os.path.join(run_dir, "samples")
    names = sorted(os.listdir(samples))
    sid_paths = [os.path.join(samples, f) for f in names if f.startswith(SE.SAMPLE_PREFIX) and f.endswith(".json")]
    main_paths = [os.path.join(samples, f) for f in names if f.startswith(SAMPLE_PREFIX) and f.endswith(".json")]
    sid_payloads, main_payloads = _load(sid_paths), _load(main_paths)
    calls = judge_probes(main_payloads, records, judge, salt=salt)
    by_step = {p["step"]: p for p in main_payloads}
    base = SE.baseline_labels(sid_payloads[0] if sid_payloads and sid_payloads[0]["step"] == 0 else None)
    control = probe_items(by_step.get(0), records) if 0 in by_step else None
    in_prompt = premises_in_prompt(records)
    per_step, pooled, pooled_probes, pooled_sid = {}, [], [], []
    for payload in sid_payloads:
        step = payload["step"]
        items = SE.scored_items(payload, records, base)
        main = by_step.get(step)
        probes = probe_items(main, records) if main is not None else None
        sid = payload.get("metrics") or SE.compute_metrics(items, [payload])
        per_step[step] = compute_metrics(sid, items, probes, None if step == 0 else control, in_prompt)
        if step != 0:
            pooled += items
            pooled_sid.append(payload)
            if probes is not None:
                pooled_probes += probes
    for path, payload in zip(main_paths, main_payloads):
        payload["metrics"] = per_step.get(payload["step"])
        with open(path, "w") as f:
            json.dump(payload, f, indent=1, ensure_ascii=False)
    with open(ckpt_path) as f:
        rows = [json.loads(line) for line in f if line.strip()]
    for row in rows:
        m = per_step.get(row["step"])
        if m is None:
            continue
        row.setdefault("evaluations", {})["sid_main"] = m
        row.update({k: m[k] for k in ("edit_succ", "portability", "locality", "fluency", "well_formed")},
                   headline_evaluation="sid_main")
    with open(ckpt_path, "w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    if grouped and pooled:
        sid = SE.compute_metrics(pooled, pooled_sid)
        final = compute_metrics(sid, pooled, pooled_probes if pooled_probes else None, control, in_prompt)
    else:
        final = per_step[max(per_step)] if per_step else None
    info = {**metadata(), **calls, "steps": sorted(per_step), "probe_steps": sorted(by_step)}
    return final, info
