"""Sid's Dataset's own evaluation for editing runs (evaluation mode "sid").

The dataset README (Evaluation; Answering and judging) defines how an edit is
scored; this module applies it to run_experiment.py's checkpoints:

1. Generation, at every checkpoint the runner evaluates (step 0, before any
   edit, included): every query of every edited record (direct, paraphrase,
   cross_lingual, propositional, unrelated_near, unrelated_far, derived) is
   asked in the run's prompt format through sids_requests.render_prompt, the
   same text the edit was trained on and the model audit asks (chat template
   for instruct models, few-shot Question:/Answer: for base models). Greedy,
   at most MAX_NEW_TOKENS tokens, few-shot stopping at the first line break,
   and cut by sids_requests.clean_answer, as the audit does. The answers are
   written to samples/sid_step_<step>.json, keyed by the audit's query keys
   (experiments/model_audit/audit_queries.py: direct, paraphrase,
   cross_lingual[zh], propositional[0], unrelated_near[0], derived[2], ...).
2. Judging, once, after the run: the edited model is unloaded first (as the
   audit does), so only the judge is on the GPU. The SID judge
   (experiments/sid_eval/judge.py, Qwen3-4B-Instruct-2507) labels every stored
   answer; identical (query, answer) pairs are judged once. What it is shown:
     replace / insert   original_answer (if any) and new_answer
     delete             original_answer only: abstaining, or only denying
                        it, is NONE, which is the pass label. The "I don't
                        know" training target is not shown as a candidate,
                        because NONE already is that answer and two labels
                        for one outcome would split the votes.
     indeterminate      original_answer plus every world's answer
     derived            (judge.py side WORLD for one that is neither)
     locality           the post-edit answer against the model's own
                        step-0 answer (SAME / DIFFERENT / UNCLEAR)
3. Scoring, in code (judge.score and the rules below), never by the judge:
     an answer query    passes on NEW; under delete (new_answer null, or the
                        "I don't know" of propositional queries) on NONE
     indeterminate      passes when the answer matches some world: the
                        candidate it matched is some world's answer, or NONE
                        and some world's answer is null (abstain); the
                        matched worlds are recorded
     locality           passes on SAME
     UNCLEAR            excluded from scores and counted apart
   Metrics (percent, None when nothing was scored): reliability (direct +
   paraphrase), cross_lingual (+ per language), logical_consistency
   (propositional, + per form), generalization (derived, split by
   determinacy, belief-revision problem, logic and derivation, with the
   worlds picked), locality (+ near, far), delete_abstention (a delete
   record's direct, paraphrase and cross-lingual answers that abstain), and
   fluency. Each metric block also carries "known": the same tally over the
   queries whose step-0 answer the judge labelled ORIGINAL (the model held
   the fact before the edit; the README drops the others per model).

The headline keys edit_succ / portability / locality / fluency of the "sid"
evaluation are reliability / generalization / locality / fluency, so the
dashboard and the sweeps read Sid's Dataset runs like any other.

Standard library only, except generate_answers (torch) and load_judge.
"""
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(HERE))
for _p in (os.path.join(PROJECT_ROOT, "experiments", "sid_eval"), os.path.join(PROJECT_ROOT, "experiments", "model_audit")):
    if _p not in sys.path:
        sys.path.append(_p)
import judge as J  # noqa: E402
import audit_queries as AQ  # noqa: E402  (query keys shared with the audit and the dashboard)
import sids_requests  # noqa: E402

JUDGE_PATH = os.path.join(PROJECT_ROOT, "models", J.JUDGE_MODEL)
MAX_NEW_TOKENS = 64          # the audit's --max_new_tokens
GENERATE_BATCH_SIZE = 32     # the audit's --batch_size
JUDGE_BATCH_SIZE = 32        # the audit's --judge_batch_size
FEWSHOT_STOPS = ["\n", "Question:"]  # the audit's BASE_STOPS
SAMPLE_PREFIX = "sid_step_"
ENGLISH = ("direct", "paraphrase", "propositional", "unrelated_near", "unrelated_far", "derived")
OWN = ("direct", "paraphrase", "cross_lingual")


def metadata():
    return {"judge_model": J.JUDGE_MODEL, "rubric": J.RUBRIC_VERSION, "max_new_tokens": MAX_NEW_TOKENS,
            "do_sample": False, "fewshot_stops": FEWSHOT_STOPS, "units": "percent passed",
            "headline": {"edit_succ": "reliability", "portability": "generalization", "locality": "locality",
                         "fluency": "fluency"}}


def sample_path(run_dir, step):
    return os.path.join(run_dir, "samples", f"{SAMPLE_PREFIX}{step:06d}.json")


# ------------------------------------------------------------------ queries

def _expects_abstain(new):
    return new is None or sids_requests._norm(new) == sids_requests._norm(sids_requests.ABSTAIN_TARGET)


def record_queries(rec):
    """Every query of a record as asked after the edit: dicts with key,
    query_type, language, question and what scoring needs."""
    out = []
    for key, qtype, lang, item in AQ.all_queries(rec):
        q = {"key": key, "query_type": qtype, "language": lang, "question": item["prompt"]}
        if qtype in AQ.LOCALITY:
            q["rule"] = "locality"
        else:
            worlds = item.get("world_answers")
            new = item.get("new_answer")
            q.update(original_answer=item.get("original_answer"))
            if qtype == "derived" and worlds:
                q.update(rule="worlds", world_answers={w: (a or {}).get("answer") for w, a in worlds.items()})
            elif _expects_abstain(new):
                q.update(rule="abstain")
            else:
                q.update(rule="new", new_answer=new)
            if qtype == "derived":
                det = item.get("determinacy")
                q.update(logic=item.get("logic"), derivation=item.get("derivation"), determinacy=det,
                         problem=det or "unlabelled",
                         indeterminate=det in ("background_beliefs", "derived_beliefs"))
            if qtype == "propositional":
                q.update(form=item.get("form"))
        out.append(q)
    return out


def judge_query(q):
    """What the judge is shown for one answer query (judge.answer_candidates)."""
    out = {"prompt": q["question"], "original_answer": q.get("original_answer"), "new_answer": None}
    if q["rule"] == "new":
        out["new_answer"] = q["new_answer"]
    elif q["rule"] == "worlds":
        out["world_answers"] = q["world_answers"]
    return out


def score_answer(q, verdict, operation):
    """(score, worlds): 1 pass, 0 fail, None excluded; and for a world query
    the worlds the answer matches."""
    label = verdict["label"]
    if label == "UNCLEAR":
        return None, None
    if q["rule"] == "new":
        return J.score("edit", "replace", label), None
    if q["rule"] == "abstain":
        return J.score("edit", "delete", label), None
    worlds = q["world_answers"]
    if label == "NONE":
        matched = sorted(w for w, a in worlds.items() if a is None)
    elif label in ("ORIGINAL", "NEW", "WORLD") and verdict.get("answer") is not None:
        target = J._norm(verdict["answer"])
        matched = sorted(w for w, a in worlds.items() if a is not None and J._norm(a) == target)
    else:
        matched = []
    return int(bool(matched)), matched


# ---------------------------------------------------------------- generation

def generate_answers(model, tok, prompts, device, fmt, max_new_tokens=MAX_NEW_TOKENS,
                     batch_size=GENERATE_BATCH_SIZE):
    """Greedy answers to rendered prompts, batched with left padding (longest
    first), cut like the audit's. Returns [(answer, raw generation)]."""
    import torch
    if not prompts:
        return []
    side = tok.padding_side
    tok.padding_side = "left"
    out = [None] * len(prompts)
    order = sorted(range(len(prompts)), key=lambda i: -len(prompts[i]))
    try:
        for start in range(0, len(order), batch_size):
            idx = order[start:start + batch_size]
            # render_prompt drops the template's BOS text when the tokenizer
            # adds one itself, so special tokens stay on (the audit's ids).
            enc = tok([prompts[i] for i in idx], return_tensors="pt", padding=True).to(device)
            kwargs = {"stop_strings": FEWSHOT_STOPS, "tokenizer": tok} if fmt == "fewshot" else {}
            with torch.no_grad():
                gen = model.generate(**enc, max_new_tokens=max_new_tokens, do_sample=False,
                                     pad_token_id=tok.pad_token_id, **kwargs)
            tails = tok.batch_decode(gen[:, enc["input_ids"].shape[1]:], skip_special_tokens=True)
            for i, text in zip(idx, tails):
                out[i] = (sids_requests.clean_answer(text, fmt), text)
    finally:
        tok.padding_side = side
    return out


def collect_generations(requests, records, fmt, tok, generate, step, case_offset=0, answer_one=None):
    """Ask every query of every request's record. `generate(prompts)` answers
    a list of rendered prompts at once ([(answer, raw)]); `answer_one(request,
    prompt)` instead asks one at a time (SCR and IKE, which answer through
    their own context). Returns the step's payload for samples/."""
    rows, prompts = [], []
    for i, request in enumerate(requests):
        rid = request["sids"]["id"]
        rec = records[rid]
        for q in record_queries(rec):
            prompt = sids_requests.render_prompt(q["question"], fmt, tok)
            rows.append((i, request, rid, rec, q, prompt))
            prompts.append(prompt)
    if answer_one is not None:
        answers = []
        for (_, request, _, _, _, prompt) in rows:
            text = answer_one(request, prompt)
            answers.append((sids_requests.clean_answer(text, fmt), text))
    else:
        answers = generate(prompts)
    by_record = {}
    for (i, request, rid, rec, q, prompt), (answer, raw) in zip(rows, answers):
        entry = by_record.setdefault(rid, {"record_id": rid, "case_id": case_offset + i,
                                           "edit_operation": rec["edit_operation"], "box": rec["box"],
                                           "topic": rec["topic"], "queries": {}})
        entry["queries"][q["key"]] = {"query_type": q["query_type"], "language": q["language"],
                                      "question": q["question"], "response": answer, "raw": raw}
    return {"step": step, "prompt_format": fmt, "evaluation": "sid", "judged": False,
            "records": list(by_record.values())}


# ------------------------------------------------------------------ judging

def judge_steps(payloads, records, judge, salt=""):
    """Label every stored answer of every step in place (one judge pass for
    the whole run). Locality compares with the same record's step-0 answer;
    at step 0 itself it is SAME by definition and not sent to the judge.
    Returns {"answer_calls", "locality_calls"}."""
    payloads = sorted(payloads, key=lambda p: p["step"])
    baseline = {}
    if payloads and payloads[0]["step"] == 0:
        for entry in payloads[0]["records"]:
            for key, a in entry["queries"].items():
                baseline[(entry["record_id"], key)] = a["response"]
    answer_jobs, locality_jobs = {}, {}
    pending = []
    for payload in payloads:
        for entry in payload["records"]:
            rec = records[entry["record_id"]]
            for q in record_queries(rec):
                a = entry["queries"].get(q["key"])
                if a is None:
                    continue
                if q["rule"] == "locality":
                    before = baseline.get((entry["record_id"], q["key"]))
                    a["before"] = before
                    if payload["step"] == 0:
                        a["verdict"] = {"label": "SAME", "reason": "step 0 is the baseline"}
                        continue
                    job = (q["question"], before, a["response"])
                    locality_jobs.setdefault(job, None)
                else:
                    job = (json.dumps(judge_query(q), sort_keys=True, ensure_ascii=False), a["response"])
                    answer_jobs.setdefault(job, judge_query(q))
                if q["rule"] != "locality":
                    # What passes, for readers (the dashboard's Responses view).
                    a["expected"] = {k: q[k] for k in ("rule", "original_answer", "new_answer", "world_answers")
                                     if k in q}
                pending.append((q, a, job))
    akeys, lkeys = list(answer_jobs), list(locality_jobs)
    averdicts = judge.label_answers([(answer_jobs[k], k[1]) for k in akeys], salt=salt) if akeys else []
    lverdicts = judge.label_locality(list(lkeys)) if lkeys else []
    got = dict(zip(akeys, averdicts))
    got.update(zip(lkeys, lverdicts))
    for q, a, job in pending:
        a["verdict"] = dict(got[job])
    for payload in payloads:
        payload["judged"] = True
    return {"answer_calls": len(akeys), "locality_calls": len(lkeys)}


def scored_items(payload, records, baseline_labels=None):
    """One flat item per judged query of a step: everything metrics slice by."""
    items = []
    for entry in payload["records"]:
        rec = records[entry["record_id"]]
        op = rec["edit_operation"]
        for q in record_queries(rec):
            a = entry["queries"].get(q["key"])
            if a is None or "verdict" not in a:
                continue
            v = a["verdict"]
            if q["rule"] == "locality":
                score, worlds = J.locality_score(v["label"]), None
            else:
                score, worlds = score_answer(q, v, op)
            a["score"] = score
            if worlds is not None:
                a["worlds"] = worlds
            pre = (baseline_labels or {}).get((entry["record_id"], q["key"]))
            items.append({"record_id": entry["record_id"], "operation": op, "box": rec["box"],
                          "key": q["key"], "query_type": q["query_type"], "language": q["language"],
                          "label": v["label"], "score": score, "worlds": worlds,
                          "known": pre == "ORIGINAL" if q.get("original_answer") is not None else None,
                          "form": q.get("form"), "logic": q.get("logic"), "derivation": q.get("derivation"),
                          "problem": q.get("problem"), "indeterminate": q.get("indeterminate"),
                          "response": a["response"]})
    return items


def baseline_labels(payload):
    """{(record_id, key): label} of the step-0 answers: was the original held?"""
    if not payload or payload["step"] != 0:
        return {}
    return {(e["record_id"], k): (a.get("verdict") or {}).get("label")
            for e in payload["records"] for k, a in e["queries"].items()}


# ------------------------------------------------------------------ metrics

def _pct(passed, scored):
    return round(100.0 * passed / scored, 4) if scored else None


def block(items):
    scores = [i["score"] for i in items]
    passed, scored = sum(s == 1 for s in scores), sum(s is not None for s in scores)
    out = {"score": _pct(passed, scored), "pass": passed, "scored": scored,
           "unclear": sum(s is None for s in scores), "total": len(items)}
    known = [i for i in items if i.get("known")]
    if any(i.get("known") is not None for i in items):
        kp = sum(i["score"] == 1 for i in known)
        ks = sum(i["score"] is not None for i in known)
        out["known"] = {"score": _pct(kp, ks), "pass": kp, "scored": ks, "total": len(known)}
    return out


def _by(items, field):
    groups = defaultdict(list)
    for i in items:
        groups[str(i[field])].append(i)
    return {k: block(v) for k, v in sorted(groups.items())}


_TOKEN = re.compile(r"\w+|[^\w\s]")


def ngram_entropy(text, ns=(2, 3), weights=(2 / 3, 4 / 3)):
    """EasyEdit's compute_n_gram_entropy (bigram and trigram entropy in bits,
    weighted, averaged), with a regex word tokenizer in place of nltk's.
    None when the text has too few tokens for a bigram."""
    tokens = _TOKEN.findall(text)
    values = []
    for n, w in zip(ns, weights):
        grams = Counter(tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1))
        total = sum(grams.values())
        if not total:
            return None
        values.append(w * -sum(c / total * math.log2(c / total) for c in grams.values()))
    return sum(values) / len(values)


def fluency(payload):
    """Per record, the n-gram entropy of its English answers joined (README:
    fluency over the English generations; cross-lingual left out), averaged
    over records and scaled by 100 like the original mode's."""
    values = []
    for entry in payload["records"]:
        text = " ".join(a["response"] for a in entry["queries"].values()
                        if a["query_type"] in ENGLISH and a["response"])
        v = ngram_entropy(text)
        if v is not None:
            values.append(v)
    return round(100 * sum(values) / len(values), 4) if values else None


def world_picks(items):
    """How a run's indeterminate answers pick worlds: matches per world id,
    and per record whether the worlds its passed answers pick agree (some
    world matches all of them) or not (an inconsistency, README Worlds and
    chains). Records with fewer than two passed indeterminate answers are
    not counted either way."""
    per_world = Counter()
    per_record = defaultdict(list)
    for i in items:
        if i["query_type"] == "derived" and i["worlds"]:
            per_world.update(i["worlds"])
            per_record[i["record_id"]].append(set(i["worlds"]))
    consistent = mixed = 0
    for sets in per_record.values():
        if len(sets) < 2:
            continue
        if set.intersection(*sets):
            consistent += 1
        else:
            mixed += 1
    return {"matches": dict(sorted(per_world.items())), "records_consistent": consistent, "records_mixed": mixed}


def compute_metrics(items, payloads_for_fluency=()):
    """The sid evaluation of one checkpoint (or pooled groups) from its items."""
    of = lambda *types: [i for i in items if i["query_type"] in types]
    derived = of("derived")
    locality = of("unrelated_near", "unrelated_far")
    metrics = {
        "reliability": block(of("direct", "paraphrase")),
        "cross_lingual": {**block(of("cross_lingual")), "by_language": _by(of("cross_lingual"), "language")},
        "logical_consistency": {**block(of("propositional")), "by_form": _by(of("propositional"), "form")},
        "generalization": {
            **block(derived),
            "determinate": block([i for i in derived if i["problem"] == "determinate"]),
            "indeterminate": block([i for i in derived if i["indeterminate"]]),
            "by_problem": _by(derived, "problem"),
            "by_logic": _by(derived, "logic"),
            "by_derivation": _by(derived, "derivation"),
            "worlds": world_picks(derived),
        },
        "locality": {**block(locality), "near": block(of("unrelated_near")), "far": block(of("unrelated_far"))},
        "delete_abstention": block([i for i in of(*OWN) if i["operation"] == "delete"]),
    }
    flu = [f for f in (fluency(p) for p in payloads_for_fluency) if f is not None]
    flu = round(sum(flu) / len(flu), 4) if flu else None
    by_operation = {}
    for op in sorted({i["operation"] for i in items}):
        sub = [i for i in items if i["operation"] == op]
        o = lambda *types: [i for i in sub if i["query_type"] in types]
        by_operation[op] = {"reliability": block(o("direct", "paraphrase")), "cross_lingual": block(o("cross_lingual")),
                            "logical_consistency": block(o("propositional")), "generalization": block(o("derived")),
                            "locality": block(o("unrelated_near", "unrelated_far"))}
    labels = Counter(i["label"] for i in items)
    return {
        "edit_succ": metrics["reliability"]["score"],
        "portability": metrics["generalization"]["score"],
        "locality": metrics["locality"]["score"],
        "fluency": flu,
        "coverage": {"edit_succ": {k: metrics["reliability"][k] for k in ("scored", "total")},
                     "portability": {k: metrics["generalization"][k] for k in ("scored", "total")},
                     "locality": {k: metrics["locality"][k] for k in ("scored", "total")}},
        "metrics": metrics,
        "by_operation": by_operation,
        "labels": dict(sorted(labels.items())),
        "records": len({i["record_id"] for i in items}),
    }


# ------------------------------------------------------------------ the run

def load_judge(device):
    return J.LocalJudge(JUDGE_PATH, device=device, batch_size=JUDGE_BATCH_SIZE)


def finalize(run_dir, ckpt_path, records, judge, salt="", grouped=False, judge_check=True):
    """Judge every stored step, then write the "sid" evaluation into each
    checkpoints.jsonl row (matched by step) and return the run's summary
    entry: the last checkpoint's, or under an edit protocol (grouped) every
    group's items pooled, which weights groups by their size."""
    samples = os.path.join(run_dir, "samples")
    paths = sorted(os.path.join(samples, f) for f in os.listdir(samples)
                   if f.startswith(SAMPLE_PREFIX) and f.endswith(".json"))
    payloads = []
    for p in paths:
        with open(p) as f:
            payloads.append(json.load(f))
    calls = judge_steps(payloads, records, judge, salt=salt)
    base = baseline_labels(payloads[0] if payloads else None)
    per_step, pooled, pooled_payloads = {}, [], []
    for path, payload in zip(paths, payloads):
        items = scored_items(payload, records, base)
        payload["metrics"] = per_step[payload["step"]] = compute_metrics(items, [payload])
        if payload["step"] != 0:
            pooled += items
            pooled_payloads.append(payload)
        with open(path, "w") as f:
            json.dump(payload, f, indent=1, ensure_ascii=False)
    with open(ckpt_path) as f:
        rows = [json.loads(line) for line in f if line.strip()]
    for row in rows:
        sid = per_step.get(row["step"])
        if sid is None:
            continue
        row.setdefault("evaluations", {})["sid"] = sid
        # Sid's Dataset has no original-mode scores; its headline fields are
        # the sid evaluation's, and say so.
        row.update({k: sid[k] for k in ("edit_succ", "portability", "locality", "fluency")},
                   headline_evaluation="sid")
    with open(ckpt_path, "w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    if grouped and pooled:
        final = compute_metrics(pooled, pooled_payloads)
    else:
        final = per_step[max(per_step)] if per_step else None
    info = {**metadata(), **calls, "steps": sorted(per_step)}
    if judge_check:
        info["judge_check"] = J.self_check(judge)
    return final, info
