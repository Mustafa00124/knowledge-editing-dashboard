"""Which prompt formats does a model show its knowledge in?

The Prompt format investigation's main measurement. For one model, every
dataset in --datasets is sampled once (the same facts for every model: a
fixed, relation-balanced sample), and each fact is asked in every format
that dataset supports. A fact counts as known in a format when the model's
most likely next token, setting whitespace aside, starts an accepted answer
with probability >= --min_prob: the same test causal tracing and fact
selection apply (causal_trace.recall_target). Also recorded: the answer's
own first-token probability whatever is on top, a softer measure.

Base models are asked the chat_* formats through their instruct sibling's
chat template (INSTRUCT_SIBLING), so base and instruct read byte-identical
prompts and any difference is the tuning, not the text.

    <out_root>/runs/<run_name>/checkpoints.jsonl  step = (dataset, format) pairs scored
    <out_root>/runs/<run_name>/scores.json        dataset -> format -> rates and per-fact results
    <out_root>/runs/<run_name>/summary.json       dataset -> format -> rates

Run with the experiment environment, one model per job:
    venvs/easyedit_venv/bin/python experiments/format_knowledge/score_formats.py \\
        --model llama-3.1-8b --run_name llama-3.1-8b
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime

import numpy as np
import torch
import yaml
from transformers import AutoModelForCausalLM, AutoTokenizer

EXP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(EXP_DIR))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "experiments", "causal_tracing"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "experiments", "fact_selection"))
import causal_trace as ct  # noqa: E402
import formats as F  # noqa: E402
from select_facts import balanced_sample, load_candidates  # noqa: E402

DEFAULT_OUT_ROOT = f"{PROJECT_ROOT}/results/investigations/format_knowledge"
D = f"{PROJECT_ROOT}/datasets"

# dataset -> (files, formats it can be asked in)
DATASETS = {
    "mquake": ([f"{D}/MQuAKE/datasets/{f}.json" for f in ("MQuAKE-CF-3k-v2", "MQuAKE-CF", "MQuAKE-T")],
               ["completion", "chat_complete", "question", "chat_question", "chat_prefill"]),
    "uniedit": (None, ["completion", "chat_complete"]),  # every domain file, filled in below
    "zsre": ([f"{D}/KnowEdit/benchmark/ZsRE/ZsRE-test-all.json"], ["question", "chat_question"]),
    "realtimeqa": (None, ["question", "chat_question", "mcq", "chat_mcq"]),
    "riddles": ([f"{D}/AlteredRiddles/benchmark.jsonl"], ["riddle", "chat_riddle"]),
}

INSTRUCT_SIBLING = {
    "qwen3-4b-base": "qwen3-4b-instruct-2507",
    "olmo-3-7b-base": "olmo-3-7b-instruct",
    "llama-3.1-8b": "llama-3.1-8b-instruct",
    "mistral-7b-v0.1": "mistral-7b-instruct-v0.1",
}


def dataset_files(name):
    import glob
    files, fmts = DATASETS[name]
    if name == "uniedit":
        files = sorted(glob.glob(f"{D}/UniEdit/test/*.json"))
    elif name == "realtimeqa":
        files = sorted(glob.glob(f"{D}/RealTimeQA/by_question_type/*.json"))
    return files, fmts


def parse_args():
    p = argparse.ArgumentParser(description="Score what a model knows in each prompt format")
    p.add_argument("--model", required=True, choices=sorted(ct.MODEL_PATHS))
    p.add_argument("--datasets", default=",".join(DATASETS), help="comma-separated: " + ", ".join(DATASETS))
    p.add_argument("--n", type=int, default=500, help="facts sampled per dataset (the same for every model)")
    p.add_argument("--min_prob", type=float, default=0.1)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--dtype", default="bfloat16", choices=["bfloat16", "float16", "float32"])
    p.add_argument("--run_name", required=True)
    p.add_argument("--out_root", default=DEFAULT_OUT_ROOT)
    return p.parse_args()


def _now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def main():
    args = parse_args()
    names = [n.strip() for n in args.datasets.split(",") if n.strip()]
    unknown = [n for n in names if n not in DATASETS]
    if unknown:
        raise SystemExit(f"unknown datasets: {unknown}")
    run_dir = os.path.join(args.out_root, "runs", args.run_name)
    os.makedirs(run_dir, exist_ok=True)
    sibling = INSTRUCT_SIBLING.get(args.model)
    with open(os.path.join(run_dir, "hparams.yaml"), "w") as f:
        yaml.safe_dump({**vars(args), "datasets": names, "chat_template_from": sibling or args.model}, f, sort_keys=True)

    # The same facts for every model: a fixed sample per dataset.
    samples = {}
    for name in names:
        files, fmts = dataset_files(name)
        rows = load_candidates(files, "all")
        samples[name] = (balanced_sample(rows, args.n, args.seed) if len(rows) > args.n else rows, fmts)
        print(f"[{args.run_name}] {name}: {len(samples[name][0])} facts of {len(rows)}, formats {fmts}", flush=True)

    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    path = ct.MODEL_PATHS[args.model]
    tok = AutoTokenizer.from_pretrained(path)
    template = AutoTokenizer.from_pretrained(ct.MODEL_PATHS[sibling]) if sibling else None
    model = AutoModelForCausalLM.from_pretrained(path, dtype=getattr(torch, args.dtype)).to(device).eval()

    total = sum(len(fmts) for _, fmts in samples.values())
    started_at, t_start = _now(), time.time()
    ckpt = open(os.path.join(run_dir, "checkpoints.jsonl"), "w")
    scores, step = {}, 0

    def checkpoint(dataset=None, fmt=None, result=None):
        line = {"step": step, "total_steps": total, "at": _now(), "elapsed_sec": round(time.time() - t_start, 2),
                "dataset": dataset, "format": fmt, "known_rate": (result or {}).get("known_rate")}
        ckpt.write(json.dumps(line) + "\n")
        ckpt.flush()
        print(f"[{args.run_name}] " + " ".join(f"{k}={v}" for k, v in line.items()), flush=True)

    checkpoint()
    with torch.no_grad():
        for name, (rows, fmts) in samples.items():
            scores[name] = {}
            for fmt in fmts:
                facts, known, p_answer = [], [], []
                for row in rows:
                    item = F.build(row, fmt, tok, need_spans=False, template=template)
                    if item is None:
                        continue
                    encoded = F.encode(tok, item, return_tensors="pt").to(device)
                    logits = model(input_ids=encoded["input_ids"], attention_mask=encoded["attention_mask"]).logits
                    probs = torch.softmax(logits[0, -1].float(), dim=-1)
                    target = ct.recall_target(tok, probs, item["answers"], args.min_prob)
                    ids = list(ct.answer_ids(tok, item["answers"]))
                    p_ans = float(probs[ids].max()) if ids else 0.0
                    top = int(probs.argmax())
                    known.append(target is not None)
                    p_answer.append(p_ans)
                    facts.append({"id": row["id"], "known": target is not None, "p_answer": round(p_ans, 4),
                                  "top": tok.decode([top])})
                result = {
                    "n": len(facts), "n_sampled": len(rows),
                    "known_rate": round(float(np.mean(known)), 4) if known else None,
                    "mean_p_answer": round(float(np.mean(p_answer)), 4) if p_answer else None,
                    "facts": facts,
                }
                scores[name][fmt] = result
                step += 1
                checkpoint(name, fmt, result)
    ckpt.close()

    with open(os.path.join(run_dir, "scores.json"), "w") as f:
        json.dump(scores, f)
    summary = {
        "run": args.run_name, "model": args.model, "chat_template_from": sibling or args.model,
        "n_per_dataset": args.n, "min_prob": args.min_prob, "seed": args.seed,
        "rates": {name: {fmt: {k: v for k, v in r.items() if k != "facts"} for fmt, r in by_fmt.items()}
                  for name, by_fmt in scores.items()},
        "started_at": started_at, "finished_at": _now(), "total_sec": round(time.time() - t_start, 2),
    }
    with open(os.path.join(run_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(f"[{args.run_name}] done in {summary['total_sec']:.0f}s", flush=True)


if __name__ == "__main__":
    main()
