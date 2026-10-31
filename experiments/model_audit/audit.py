"""Model audit: does a model already know Sid's Dataset's facts, before editing?

For one model, every query of every record is asked as a free-form question
(base models: a few-shot "Question:/Answer:" template that stops at the first
line break; chat models: their chat template). The model is then unloaded and
the SID judge (experiments/sid_eval/judge.py) labels each answer. Which
queries are asked, and what each expects, is audit_queries.py (shared with
the dashboard): every query with a pre-edit answer. Replace/delete direct,
paraphrase and cross-lingual queries pass when the model gives
original_answer; insert ones pass when it does not already give new_answer.
Every derived query with an original_answer is asked and passes on it,
determinate or not (before the edit there is one world): a wrong answer there
says the logical structure is hard for the model, not that the query goes.
Locality queries (unrelated near and far) pass on their reference. Fictional
inserts (reality: fictional) are made up, so no model can hold them: their own
questions are not asked (their locality, checks and any derived query with an
original answer are), and they are counted apart like fixtures. A fact counts
as known when its direct and paraphrase queries both pass (RBox: direct and
both instance questions). The judge is shown only the answer the pass rule
needs (original_answer or reference; new_answer for insert's own questions).
Each response row carries its query_key (e.g. derived[2], cross_lingual[zh],
unrelated_near[0]) and query_hash (prompt and expected answer), so a reader
can tell when the record changed after the audit.

It also asks the checks behind each derivation: every fact a derived query or
the edit's premises rely on (the record's "checks") and every relation
property a derivation uses (relation_checks.json, asked once per model). These
are scored like original answers and summarised apart from the dataset's own
queries, together with how many derived queries have their whole chain known
("derived_supported"): only those are fair to score after editing.

Writes <out_root>/runs/<run_name>/responses.jsonl and summary.json.
"""
import argparse
import gc
import glob
import json
import os
import sys
import time
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "sid_eval"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "datasets", "SidsDataset"))
import launch_guard  # noqa: E402
import judge as J  # noqa: E402
import audit_queries as AQ  # noqa: E402  (which queries are asked, their keys and hashes)
import validate as SID  # noqa: E402  (facts_to_check, relation_property)

MODEL_PATHS = {
    "qwen3-4b-base": f"{PROJECT_ROOT}/models/Qwen3-4B-Base",
    "qwen3-4b-instruct-2507": f"{PROJECT_ROOT}/models/Qwen3-4B-Instruct-2507",
    "olmo-3-7b-base": f"{PROJECT_ROOT}/models/Olmo-3-7B-Base",
    "olmo-3-7b-instruct": f"{PROJECT_ROOT}/models/Olmo-3-7B-Instruct",
    "llama-3.1-8b": f"{PROJECT_ROOT}/models/Llama-3.1-8B",
    "llama-3.1-8b-instruct": f"{PROJECT_ROOT}/models/Llama-3.1-8B-Instruct",
    "mistral-7b-v0.1": f"{PROJECT_ROOT}/models/Mistral-7B-v0.1",
    "mistral-7b-instruct-v0.1": f"{PROJECT_ROOT}/models/Mistral-7B-Instruct-v0.1",
    "smollm3-3b-base": f"{PROJECT_ROOT}/models/SmolLM3-3B-Base",
    "smollm3-3b": f"{PROJECT_ROOT}/models/SmolLM3-3B",
    "map-neo-7b": f"{PROJECT_ROOT}/models/MAP-Neo-7B",
    "map-neo-7b-instruct": f"{PROJECT_ROOT}/models/MAP-Neo-7B-Instruct",
}
CHAT_MODELS = {"qwen3-4b-instruct-2507", "olmo-3-7b-instruct", "llama-3.1-8b-instruct", "mistral-7b-instruct-v0.1",
               "smollm3-3b", "map-neo-7b-instruct"}
JUDGE_PATH = f"{PROJECT_ROOT}/models/{J.JUDGE_MODEL}"
DEFAULT_RECORDS = f"{PROJECT_ROOT}/datasets/SidsDataset/records"
DEFAULT_OUT_ROOT = f"{PROJECT_ROOT}/results/model_audit"

# Neutral worked examples for base models, outside the dataset.
FEW_SHOT = ("Question: What is the capital of Japan?\nAnswer: Tokyo\n\n"
            "Question: How many legs does a spider have?\nAnswer: 8\n\n"
            "Question: Is the Sun a star?\nAnswer: Yes\n\n")
CHAT_INSTRUCTION = "Answer the question in a few words, without explanation."


def load_records(root, topics=None):
    records = [json.load(open(p)) for p in sorted(glob.glob(os.path.join(root, "*", "*", "*.json")))]
    return [r for r in records if not topics or r["topic"] in topics]


def check_rows(records, relation_checks, relations):
    """Rows for the checks: each record's fact checks, then each relation
    property the loaded records' derivations use, asked once."""
    rows, props = [], set()
    for rec in records:
        for c in rec.get("checks", []):
            rows.append({"record_id": rec["id"], "topic": rec["topic"], "box": rec["box"],
                         "edit_operation": rec["edit_operation"], "fixture": bool(rec["edit"].get("fixture")),
                         "query_type": "check_fact", "language": "en", "prompt": c["prompt"],
                         "original_answer": c["answer"], "new_answer": None, "fact": c["fact"],
                         "derivation": None, "judged": True})
        for q in rec["queries"].get("derived", []):
            prop = SID.relation_property(rec, q, relations)
            if prop:
                props.add(prop)
    for name, tag in sorted(props):
        entry = relation_checks.get(name, {}).get(tag)
        if not entry:
            continue
        rows.append({"record_id": None, "topic": None, "box": None, "edit_operation": None, "fixture": False,
                     "query_type": "check_relation", "language": "en", "prompt": entry["prompt"],
                     "original_answer": entry["answer"], "new_answer": None, "relation": name, "tag": tag,
                     "derivation": None, "judged": True})
    return rows


def is_check(row):
    return row["query_type"].startswith("check_")


is_fictional = AQ.is_fictional


def is_locality(row):
    return row["query_type"] in AQ.LOCALITY


def summarise_checks(rows, records, relations):
    """Check tallies, and per derived query whether its chain is known: every
    unstated bridge and revision fact and the relation property it relies on
    pass."""
    facts = {(r["record_id"], r["fact"]): r["score"] for r in rows if r["query_type"] == "check_fact"}
    props = {(r["relation"], r["tag"]): r["score"] for r in rows if r["query_type"] == "check_relation"}

    def tally(scores):
        scores = list(scores)
        return {"pass": sum(s == 1 for s in scores), "scored": sum(s is not None for s in scores),
                "unclear": sum(s is None for s in scores)}

    support = {"supported": 0, "unsupported": 0, "unclear": 0}
    premises = {"known": 0, "unknown": 0, "unclear": 0}
    for rec in records:
        if rec["box"] == "rbox":
            continue
        if rec["edit"].get("premises"):
            got = [facts.get((rec["id"], p)) for p in rec["edit"]["premises"]]
            premises["unclear" if None in got else "known" if all(got) else "unknown"] += 1
        for q in rec["queries"].get("derived", []):
            # unstated bridge and revision facts (validate.unstated_facts)
            got = [facts.get((rec["id"], b)) for b in SID.unstated_facts(q)]
            prop = SID.relation_property(rec, q, relations)
            if prop:
                got.append(props.get(prop))
            support["unclear" if None in got else "supported" if all(got) else "unsupported"] += 1
    return {"facts": tally(facts.values()), "relations": tally(props.values()),
            "derived_supported": support, "premises_known": premises}


def query_rows(records):
    """One row per query the audit asks (audit_queries.audited_queries)."""
    rows = []
    for rec in records:
        for a in AQ.audited_queries(rec):
            q, not_new = a["query"], a["rule"] == "not_new"
            rows.append({
                "record_id": rec["id"], "topic": rec["topic"], "box": rec["box"],
                "edit_operation": rec["edit_operation"], "fixture": bool(rec["edit"].get("fixture")),
                "query_type": a["query_type"], "language": a["language"], "prompt": q["prompt"],
                "query_key": a["key"], "query_hash": a["hash"], "rule": a["rule"],
                # What the judge sees: only the answer the pass rule needs
                # (the reference, for a locality query).
                "original_answer": None if not_new else a["expected"],
                "new_answer": a["expected"] if not_new else None,
                "derivation": q.get("derivation"), "determinacy": q.get("determinacy"),
                "judged": True,
            })
    return rows


def row_score(row, label):
    """Pass/fail for one row. Checks, derived and locality queries pass on the
    answer they expect (scored like a replace query's original); insert's own
    questions pass when the model does not already give the new answer."""
    if is_check(row) or row.get("rule", "original") == "original":
        return J.score("audit", "replace", label)
    return J.score("audit", "insert", label)


def prompt_text(tok, question, chat):
    if chat:
        # enable_thinking: SmolLM3-3B is a hybrid whose template reasons by
        # default; templates without the switch ignore it. Only a user turn is
        # sent, so Mistral-Instruct-v0.1 (no system role) works as the others.
        return tok.apply_chat_template([{"role": "user", "content": f"{CHAT_INSTRUCTION}\n\n{question}"}],
                                       tokenize=False, add_generation_prompt=True, enable_thinking=False)
    return f"{FEW_SHOT}Question: {question}\nAnswer:"


# Some tokenizers (OLMo 3) decode the line break between examples away, so a
# base model's answer can run straight into the next "Question:".
BASE_STOPS = ["\n", "Question:"]


def clean(text, chat):
    text = text.strip()
    if not chat:
        for stop in BASE_STOPS:
            text = text.split(stop, 1)[0]
        return text.strip()
    return text.split("\n\n", 1)[0].strip()


def generate_all(model_key, prompts, batch_size, max_new_tokens, timings):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    chat = model_key in CHAT_MODELS
    began = time.time()
    tok = AutoTokenizer.from_pretrained(MODEL_PATHS[model_key], padding_side="left")
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    lm = AutoModelForCausalLM.from_pretrained(MODEL_PATHS[model_key], dtype=torch.bfloat16).to("cuda").eval()
    torch.cuda.synchronize()
    timings["model_load_s"] = round(time.time() - began, 1)
    began = time.time()
    texts = [prompt_text(tok, p, chat) for p in prompts]
    # Longest prompts first so each batch pads little.
    order = sorted(range(len(texts)), key=lambda i: -len(texts[i]))
    out, new_tokens = [None] * len(texts), 0
    for start in range(0, len(order), batch_size):
        idx = order[start:start + batch_size]
        enc = tok([texts[i] for i in idx], return_tensors="pt", padding=True,
                  add_special_tokens=not chat).to("cuda")
        with torch.no_grad():
            gen = lm.generate(**enc, max_new_tokens=max_new_tokens, do_sample=False,
                              pad_token_id=tok.pad_token_id,
                              stop_strings=None if chat else BASE_STOPS, tokenizer=tok)
        tail = gen[:, enc["input_ids"].shape[1]:]
        new_tokens += int((tail != tok.pad_token_id).sum())
        for i, text in zip(idx, tok.batch_decode(tail, skip_special_tokens=True)):
            out[i] = clean(text, chat)
    torch.cuda.synchronize()
    timings["generate_s"] = round(time.time() - began, 1)
    timings["generated_tokens"] = new_tokens
    began = time.time()
    del lm
    gc.collect()
    torch.cuda.empty_cache()
    timings["unload_s"] = round(time.time() - began, 1)
    return out


def summarise(rows, records):
    def tally(rs):
        scored = [r["score"] for r in rs if r["score"] is not None]
        return {"pass": sum(scored), "scored": len(scored), "unclear": sum(r["label"] == "UNCLEAR" for r in rs)}

    # The dataset's own queries; locality is tallied apart (and by query_type).
    judged = [r for r in rows if r["judged"] and not is_check(r) and not is_locality(r)]
    locality = [r for r in rows if r["judged"] and is_locality(r)]
    by = defaultdict(lambda: defaultdict(list))
    for r in judged + locality:
        for key in ("query_type", "topic", "box", "edit_operation", "language"):
            by[key][r[key]].append(r)
        by["fixture"][str(r["fixture"]).lower()].append(r)
    facts = []
    for rec in records:
        # Known: direct and paraphrase both pass. An RBox fact (a relation's
        # property, no paraphrase) is known when the direct question and both
        # instance questions (derived, English) pass.
        if rec["box"] == "rbox" and "paraphrase" not in rec["queries"]:
            keys = ("direct", "derived")
        else:
            keys = ("direct", "paraphrase")
        scores = [r["score"] for r in judged if r["record_id"] == rec["id"] and r["query_type"] in keys]
        need = 1 + len(rec["queries"].get("derived", [])) if keys[1] == "derived" else 2
        known = None if None in scores or len(scores) < need else int(all(scores))
        facts.append({"record_id": rec["id"], "topic": rec["topic"], "box": rec["box"],
                      "edit_operation": rec["edit_operation"], "fixture": bool(rec["edit"].get("fixture")),
                      "fictional": is_fictional(rec), "known": known,
                      "queries_passed": sum(r["score"] or 0 for r in judged if r["record_id"] == rec["id"]),
                      "queries_scored": sum(r["score"] is not None for r in judged if r["record_id"] == rec["id"])})
    real = [f for f in facts if not f["fixture"] and not f["fictional"]]
    return {
        "facts_known": sum(f["known"] == 1 for f in real),
        "facts_total": len(real),
        "facts_unclear": sum(f["known"] is None for f in real),
        "fixtures": sum(f["fixture"] for f in facts),
        "fictional": sum(f["fictional"] for f in facts),
        "queries": tally([r for r in judged if not r["fixture"]]),
        "locality": tally([r for r in locality if not r["fixture"]]),
        "by": {k: {v: tally(rs) for v, rs in sorted(groups.items())} for k, groups in by.items()},
        "facts": facts,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model", required=True, choices=sorted(MODEL_PATHS))
    p.add_argument("--records", default=DEFAULT_RECORDS)
    p.add_argument("--topics", default="", help="comma-separated topics to audit (empty: all)")
    p.add_argument("--batch_size", type=int, default=32)
    p.add_argument("--max_new_tokens", type=int, default=64)
    p.add_argument("--judge_batch_size", type=int, default=32)
    p.add_argument("--run_name", required=True)
    p.add_argument("--out_root", default=DEFAULT_OUT_ROOT)
    launch_guard.add_argument(p)
    args = p.parse_args()
    launch_guard.require_dashboard(args.out_root, args.untracked, "model_audit")
    out_dir = os.path.join(args.out_root, "runs", args.run_name)
    os.makedirs(out_dir, exist_ok=True)

    t0 = time.time()
    timings = {}
    topics = {t.strip() for t in args.topics.split(",") if t.strip()}
    records = load_records(args.records, topics)
    rows = query_rows(records)
    relations, _ = SID.load_relations()
    relation_checks = SID.load_relation_checks(os.path.join(os.path.dirname(os.path.abspath(args.records)),
                                                            "relation_checks.json"))
    checks = check_rows(records, relation_checks, relations)
    rows += checks
    print(f"{len(records)} records, {len(rows) - len(checks)} queries (locality included), {len(checks)} checks",
          flush=True)

    responses = generate_all(args.model, [r["prompt"] for r in rows], args.batch_size, args.max_new_tokens, timings)
    for r, resp in zip(rows, responses):
        r["response"] = resp
    print(f"generated: {timings}", flush=True)

    began = time.time()
    judge = J.LocalJudge(JUDGE_PATH, batch_size=args.judge_batch_size)
    timings["judge_load_s"] = round(time.time() - began, 1)
    began = time.time()
    todo = [r for r in rows if r["judged"]]
    for r, v in zip(todo, judge.label_answers([(r, r["response"]) for r in todo], salt=args.model)):
        r["label"], r["reason"] = v["label"], v["reason"]
        r["score"] = row_score(r, v["label"])
    for r in rows:
        r.setdefault("label", None), r.setdefault("reason", None), r.setdefault("score", None)
    timings["judge_s"] = round(time.time() - began, 1)
    began = time.time()
    judge_check = J.self_check(judge)
    timings["judge_check_s"] = round(time.time() - began, 1)
    print(f"judge check: {judge_check['agree']}/{judge_check['total']} agree", flush=True)
    timings["total_s"] = round(time.time() - t0, 1)

    with open(os.path.join(out_dir, "responses.jsonl"), "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    summary = {"model": args.model, "topics": sorted(topics), "chat": args.model in CHAT_MODELS, "judge": J.JUDGE_MODEL,
               "rubric": J.RUBRIC_VERSION, "judge_check": judge_check, "records": len(records),
               "queries_total": sum(not is_check(r) and not is_locality(r) for r in rows),
               "queries_judged": sum(not is_check(r) and not is_locality(r) for r in todo),
               "locality_asked": sum(map(is_locality, rows)), "checks_asked": sum(map(is_check, rows)), "timings": timings, **summarise(rows, records),
               "checks": summarise_checks(rows, records, relations)}
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=1, ensure_ascii=False)
    print(f"known {summary['facts_known']}/{summary['facts_total']} facts; "
          f"queries {summary['queries']['pass']}/{summary['queries']['scored']}; timings {timings}", flush=True)


if __name__ == "__main__":
    main()
