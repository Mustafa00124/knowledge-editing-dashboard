"""Model audit: does a model already know Sid's Dataset's facts, before editing?

For one model, every query of every record is asked as a free-form question
(base models: a few-shot "Question:/Answer:" template that stops at the first
line break; chat models: their chat template). The model is then unloaded and
the SID judge (experiments/sid_eval/judge.py) labels each answer. Pre-edit
pass rules: replace/delete queries pass when the model gives original_answer,
insert queries pass when it does not already give new_answer. A fact counts as
known when its direct and paraphrase queries both pass. Locality answers are
stored as the model's pre-edit baseline and not judged.

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
import launch_guard  # noqa: E402
import judge as J  # noqa: E402

MODEL_PATHS = {
    "qwen3-4b-base": f"{PROJECT_ROOT}/models/Qwen3-4B-Base",
    "qwen3-4b-instruct-2507": f"{PROJECT_ROOT}/models/Qwen3-4B-Instruct-2507",
    "olmo-3-7b-base": f"{PROJECT_ROOT}/models/Olmo-3-7B-Base",
    "olmo-3-7b-instruct": f"{PROJECT_ROOT}/models/Olmo-3-7B-Instruct",
    "gpt-j-6b": f"{PROJECT_ROOT}/models/GPT-J-6B",
    "llama-3.1-8b": f"{PROJECT_ROOT}/models/Llama-3.1-8B",
    "llama-3.1-8b-instruct": f"{PROJECT_ROOT}/models/Llama-3.1-8B-Instruct",
    "mistral-7b-v0.1": f"{PROJECT_ROOT}/models/Mistral-7B-v0.1",
    "mistral-7b-instruct-v0.1": f"{PROJECT_ROOT}/models/Mistral-7B-Instruct-v0.1",
}
CHAT_MODELS = {"qwen3-4b-instruct-2507", "olmo-3-7b-instruct", "llama-3.1-8b-instruct", "mistral-7b-instruct-v0.1"}
JUDGE_PATH = f"{PROJECT_ROOT}/models/{J.JUDGE_MODEL}"
DEFAULT_RECORDS = f"{PROJECT_ROOT}/datasets/SidsDataset/records"
DEFAULT_OUT_ROOT = f"{PROJECT_ROOT}/results/model_audit"

# Neutral worked examples for base models, outside the dataset.
FEW_SHOT = ("Question: What is the capital of Japan?\nAnswer: Tokyo\n\n"
            "Question: How many legs does a spider have?\nAnswer: 8\n\n"
            "Question: Is the Sun a star?\nAnswer: Yes\n\n")
CHAT_INSTRUCTION = "Answer the question in a few words, without explanation."


def queries(record):
    """Yield (query_type, language, query) for every query in a record."""
    q = record["queries"]
    yield "direct", "en", q["direct"]
    yield "paraphrase", "en", q["paraphrase"]
    for item in q.get("cross_lingual", []):
        yield "cross_lingual", item["language"], item
    for item in q.get("derived", []):
        yield "derived", "en", item
    for kind in ("unrelated_near", "unrelated_far"):
        for item in q.get(kind, []):
            yield kind, "en", item


def load_records(root):
    return [json.load(open(p)) for p in sorted(glob.glob(os.path.join(root, "*", "*", "*.json")))]


def prompt_text(tok, question, chat):
    if chat:
        return tok.apply_chat_template([{"role": "user", "content": f"{CHAT_INSTRUCTION}\n\n{question}"}],
                                       tokenize=False, add_generation_prompt=True)
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

    judged = [r for r in rows if r["judged"]]
    by = defaultdict(lambda: defaultdict(list))
    for r in judged:
        for key in ("query_type", "topic", "box", "edit_operation", "language"):
            by[key][r[key]].append(r)
        by["fixture"][str(r["fixture"]).lower()].append(r)
    facts = []
    for rec in records:
        mine = {r["query_type"]: r for r in judged if r["record_id"] == rec["id"] and r["query_type"] in ("direct", "paraphrase")}
        scores = [mine[k]["score"] for k in ("direct", "paraphrase") if k in mine]
        known = None if None in scores or len(scores) < 2 else int(all(scores))
        facts.append({"record_id": rec["id"], "topic": rec["topic"], "box": rec["box"],
                      "edit_operation": rec["edit_operation"], "fixture": bool(rec["edit"].get("fixture")),
                      "known": known,
                      "queries_passed": sum(r["score"] or 0 for r in judged if r["record_id"] == rec["id"]),
                      "queries_scored": sum(r["score"] is not None for r in judged if r["record_id"] == rec["id"])})
    real = [f for f in facts if not f["fixture"]]
    return {
        "facts_known": sum(f["known"] == 1 for f in real),
        "facts_total": len(real),
        "facts_unclear": sum(f["known"] is None for f in real),
        "fixtures": len(facts) - len(real),
        "queries": tally([r for r in judged if not r["fixture"]]),
        "by": {k: {v: tally(rs) for v, rs in sorted(groups.items())} for k, groups in by.items()},
        "facts": facts,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model", required=True, choices=sorted(MODEL_PATHS))
    p.add_argument("--records", default=DEFAULT_RECORDS)
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
    records = load_records(args.records)
    rows = []
    for rec in records:
        for qtype, lang, q in queries(rec):
            locality = qtype.startswith("unrelated")
            rows.append({
                "record_id": rec["id"], "topic": rec["topic"], "box": rec["box"],
                "edit_operation": rec["edit_operation"], "fixture": bool(rec["edit"].get("fixture")),
                "query_type": qtype, "language": lang, "prompt": q["prompt"],
                "original_answer": None if locality else q.get("original_answer"),
                "new_answer": None if locality else q.get("new_answer"),
                "derivation": q.get("derivation"),
                # Pre-edit there is nothing to check when the old world has no answer.
                "judged": not locality and (rec["edit_operation"] == "insert" or q.get("original_answer") is not None),
            })
    print(f"{len(records)} records, {len(rows)} queries, {sum(r['judged'] for r in rows)} to judge", flush=True)

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
        r["score"] = J.score("audit", r["edit_operation"], v["label"])
    for r in rows:
        r.setdefault("label", None), r.setdefault("reason", None), r.setdefault("score", None)
    timings["judge_s"] = round(time.time() - began, 1)
    timings["total_s"] = round(time.time() - t0, 1)

    with open(os.path.join(out_dir, "responses.jsonl"), "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    summary = {"model": args.model, "chat": args.model in CHAT_MODELS, "judge": J.JUDGE_MODEL,
               "rubric": J.RUBRIC_VERSION, "records": len(records), "queries_total": len(rows),
               "queries_judged": len(todo), "timings": timings, **summarise(rows, records)}
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=1, ensure_ascii=False)
    print(f"known {summary['facts_known']}/{summary['facts_total']} facts; "
          f"queries {summary['queries']['pass']}/{summary['queries']['scored']}; timings {timings}", flush=True)


if __name__ == "__main__":
    main()
