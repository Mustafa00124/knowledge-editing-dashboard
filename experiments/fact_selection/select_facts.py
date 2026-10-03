"""Pick one fact set that every model to be traced already knows.

Causal tracing keeps only facts a model gives the answer to, so tracing
models one at a time gives each a different fact set, and two traces then
differ partly because of the facts. This script fixes the facts first: it
asks every model, in every requested prompt format, for its clean
next-token prediction on every candidate (the same
causal_trace.recall_target test the trace applies), keeps the facts all of
them know in all of those formats, and samples them evenly across relations
(or UniEdit domains) so no one kind decides the peak. causal_trace.py
--fact_set then traces exactly that list on each model.

Candidates come from the --split records of each --data_paths file. The
default, nontest (dev + demo of splits/), keeps every record a main
experiment is scored on out of reach. Tracing only locates where facts are
recalled and tests whether that is early-to-mid; it does not choose a
setting by score, so the tracing studies use --split all, with
--max_candidates sampling a relation-balanced pool to score.
A set below causal_trace.MIN_FACTS is still written, flagged "below_min";
the traces refuse it unless told otherwise.

A dashboard experiment type (its own dashboard.json), so a selection job
shows its progress like any other: one checkpoint line per model scored.

    <out_root>/runs/<run_name>/checkpoints.jsonl  step = models scored so far
    <out_root>/runs/<run_name>/known.json         model -> format -> fact id -> {known, p, top},
                                                  written after each model, so a
                                                  rerun skips models already scored
    <out_root>/runs/<run_name>/fact_set.json      the set: {"name", "facts": [...], ...}
    <out_root>/runs/<run_name>/summary.json       counts, written at the end

Run with the experiment environment, on one GPU (the models load one after
another):
    venvs/easyedit_venv/bin/python experiments/fact_selection/select_facts.py \\
        --models qwen3-4b-base,qwen3-4b-instruct-2507 --formats completion \\
        --data_paths datasets/MQuAKE/datasets/MQuAKE-CF-3k-v2.json --n 100 \\
        --run_name mquake_shared
"""
import argparse
import gc
import json
import os
import random
import sys
import time
from collections import defaultdict
from datetime import datetime

import torch
import yaml
from transformers import AutoModelForCausalLM, AutoTokenizer

EXP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(EXP_DIR))
sys.path.append(os.path.join(PROJECT_ROOT, "experiments"))
import launch_guard  # noqa: E402  (refuses untracked runs into results/)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "experiments", "causal_tracing"))
import causal_trace as ct  # noqa: E402
import formats as F  # noqa: E402

DEFAULT_OUT_ROOT = f"{PROJECT_ROOT}/results/investigations/causal_tracing/fact_sets"


def parse_args():
    p = argparse.ArgumentParser(description="Choose the facts every traced model knows")
    p.add_argument("--models", required=True, help="comma-separated model keys")
    p.add_argument("--data_paths", required=True, help="comma-separated dataset files")
    p.add_argument("--formats", default="completion",
                   help="comma-separated prompt formats a fact must be known in (formats.FORMATS)")
    p.add_argument("--instruct_models", default="",
                   help="comma-separated models that must also know facts in the chat_* formats; "
                        "others are held to the plain formats only")
    p.add_argument("--groups", default="",
                   help="'name:model,model;name:model,model' writes one set per group (each from the facts "
                        "that group's models share) from the same scoring pass; empty = one set over all models")
    p.add_argument("--split", default="nontest", choices=F.SPLIT_CHOICES)
    p.add_argument("--n", type=int, default=100, help="facts in the set (fewer if fewer are shared)")
    p.add_argument("--max_candidates", type=int, default=0,
                   help="score at most this many candidates, sampled evenly across relations/domains "
                        "(0 = all). Keeps --split all affordable: MQuAKE alone has ~18k facts")
    p.add_argument("--min_prob", type=float, default=0.1)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--dtype", default="bfloat16", choices=["bfloat16", "float16", "float32"])
    p.add_argument("--run_name", required=True, help="the fact set's name")
    p.add_argument("--out_root", default=DEFAULT_OUT_ROOT)
    launch_guard.add_argument(p)
    return p.parse_args()


def _now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def score_model(model_key, rows, fmts, args, device):
    """format -> fact id -> {known, p, top} for one model, in `fmts`."""
    path = ct.MODEL_PATHS[model_key]
    tok = AutoTokenizer.from_pretrained(path)
    missing = [f for f in fmts if f in F.CHAT_FORMATS and not F.has_chat_template(tok)]
    if missing:
        raise SystemExit(f"{model_key} has no chat template, so it cannot be scored in {missing}")
    model = AutoModelForCausalLM.from_pretrained(path, dtype=getattr(torch, args.dtype)).to(device).eval()
    out = {}
    with torch.no_grad():
        for fmt in fmts:
            scores = out[fmt] = {}
            for row in rows:
                item = F.build(row, fmt, tok)
                if item is None:
                    scores[row["id"]] = {"known": False, "p": None, "top": None, "why": "not writable in this format"}
                    continue
                encoded = F.encode(tok, item, return_tensors="pt").to(device)
                logits = model(input_ids=encoded["input_ids"], attention_mask=encoded["attention_mask"]).logits
                probs = torch.softmax(logits[0, -1].float(), dim=-1)
                target = ct.recall_target(tok, probs, item["answers"], args.min_prob)
                top_id = int(probs.argmax())
                scores[row["id"]] = {"known": target is not None,
                                     "p": round(float(probs[target if target is not None else top_id]), 4),
                                     "top": tok.decode([top_id])}
    del model
    gc.collect()
    torch.cuda.empty_cache()
    return out


def balanced_sample(rows, n, seed):
    """Round-robin over relations (UniEdit: domains), each one's facts
    shuffled, so the set spreads across as many kinds of fact as it can
    before repeating any."""
    rng = random.Random(seed)
    by_kind = defaultdict(list)
    for row in rows:
        by_kind[row.get("domain") or row.get("relation") or "none"].append(row)
    queues = []
    for kind in sorted(by_kind):
        facts = by_kind[kind][:]
        rng.shuffle(facts)
        queues.append(facts)
    rng.shuffle(queues)
    picked = []
    while len(picked) < n and any(queues):
        for queue in queues:
            if queue and len(picked) < n:
                picked.append(queue.pop())
    return picked


def load_candidates(data_paths, split):
    rows, seen = [], set()
    for path in data_paths:
        for row in F.load_rows(os.path.abspath(path), split):
            # MQuAKE-CF-3k-v2 is drawn from MQuAKE-CF and RealTimeQA repeats
            # questions across files, so facts recur.
            key = (row["cloze"], row["question"], row["riddle"], row["answer"])
            if key not in seen:
                seen.add(key)
                rows.append(row)
    return rows


def _known(known, model, fmt, fact_id):
    return known[model][fmt][fact_id]["known"]


def required(model, fmts, instruct):
    """The formats `model` must know a fact in: chat formats only for instruct models."""
    return [f for f in fmts if f not in F.CHAT_FORMATS or model in instruct]


def shared_by(known, rows, models, fmts, instruct):
    return [r for r in rows if all(_known(known, m, f, r["id"]) for m in models for f in required(m, fmts, instruct))]


def parse_groups(spec, models):
    if not spec:
        return {"all": models}
    groups = {}
    for part in spec.split(";"):
        name, _, members = part.partition(":")
        groups[name.strip()] = [m.strip() for m in members.split(",") if m.strip()]
    stray = [m for g in groups.values() for m in g if m not in models]
    if stray:
        raise SystemExit(f"group members not in --models: {stray}")
    return groups


def write_set(path, name, rows, picked_from, models, fmts, instruct, known, args, data_paths, extra):
    picked = balanced_sample(picked_from, args.n, args.seed)
    kinds = defaultdict(int)
    for row in picked:
        kinds[row.get("domain") or row.get("relation") or "none"] += 1
    summary = {
        "name": name, "models": models, "formats": fmts, "instruct_models": [m for m in models if m in instruct],
        "data_paths": data_paths, "split": args.split, "min_prob": args.min_prob, "seed": args.seed,
        "candidates": len(rows),
        "known_per_model": {m: {f: sum(v["known"] for v in known[m][f].values()) for f in required(m, fmts, instruct)}
                            for m in models},
        "shared": len(picked_from), "picked": len(picked), "n_relations": len(kinds),
        "relations": dict(sorted(kinds.items(), key=lambda kv: -kv[1])),
        "min_facts": ct.MIN_FACTS, "below_min": len(picked) < ct.MIN_FACTS, **extra,
    }
    with open(path, "w") as f:
        json.dump({**summary, "facts": picked}, f, indent=1)
    return summary


def main():
    args = parse_args()
    launch_guard.require_dashboard(args.out_root, args.untracked, "fact_selection")
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    data_paths = [p.strip() for p in args.data_paths.split(",") if p.strip()]
    fmts = [f.strip() for f in args.formats.split(",") if f.strip()]
    instruct = {m.strip() for m in args.instruct_models.split(",") if m.strip()}
    groups = parse_groups(args.groups, models)
    unknown = [m for m in models if m not in ct.MODEL_PATHS] + [f for f in fmts if f not in F.FORMATS]
    if unknown:
        raise SystemExit(f"unknown models or formats: {unknown}")
    run_dir = os.path.join(args.out_root, "runs", args.run_name)
    os.makedirs(run_dir, exist_ok=True)
    with open(os.path.join(run_dir, "hparams.yaml"), "w") as f:
        yaml.safe_dump({**vars(args), "models": models, "data_paths": data_paths, "formats": fmts}, f, sort_keys=True)

    rows = load_candidates(data_paths, args.split)
    if args.max_candidates and len(rows) > args.max_candidates:
        rows = balanced_sample(rows, args.max_candidates, args.seed)
    ids = {r["id"] for r in rows}
    print(f"[{args.run_name}] {len(rows)} candidate facts, formats {fmts}", flush=True)

    known_path = os.path.join(run_dir, "known.json")
    known = {}
    if os.path.exists(known_path):
        with open(known_path) as f:
            known = json.load(f)
    started_at, t_start = _now(), time.time()
    ckpt = open(os.path.join(run_dir, "checkpoints.jsonl"), "w")

    def checkpoint(step, model_key=None):
        scored = [m for m in models if m in known]
        # Per group, the facts its scored members share so far: the number
        # that decides whether a group reaches the minimum.
        shared = {g: len(shared_by(known, rows, [m for m in ms if m in scored], fmts, instruct))
                  for g, ms in groups.items() if any(m in scored for m in ms)}
        line = {"step": step, "total_steps": len(models), "at": _now(),
                "elapsed_sec": round(time.time() - t_start, 2), "model": model_key,
                "known": min(sum(v["known"] for v in known[model_key][f].values())
                             for f in required(model_key, fmts, instruct)) if model_key else None,
                "candidates": len(rows), "shared_so_far": shared or None}
        ckpt.write(json.dumps(line) + "\n")
        ckpt.flush()
        print(f"[{args.run_name}] " + " ".join(f"{k}={v}" for k, v in line.items()), flush=True)

    checkpoint(0)
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    for step, model_key in enumerate(models, start=1):
        need = required(model_key, fmts, instruct)
        done = model_key in known and all(f in known[model_key] and set(known[model_key][f]) >= ids for f in need)
        if not done:
            known.setdefault(model_key, {}).update(score_model(model_key, rows, need, args, device))
            with open(known_path, "w") as f:
                json.dump(known, f, indent=1)
        checkpoint(step, model_key)
    ckpt.close()

    sets_dir = os.path.join(run_dir, "sets")
    os.makedirs(sets_dir, exist_ok=True)
    timing = {"started_at": started_at, "finished_at": _now(), "total_sec": round(time.time() - t_start, 2)}
    sets = {}
    for name, members in groups.items():
        shared = shared_by(known, rows, members, fmts, instruct)
        path = os.path.join(sets_dir, f"{name}.json")
        sets[name] = write_set(path, f"{args.run_name}/{name}", rows, shared, members, fmts, instruct,
                               known, args, data_paths, timing)
        sets[name]["path"] = path
        print(f"[{args.run_name}] {name}: shared {len(shared)}, picked {sets[name]['picked']} across "
              f"{sets[name]['n_relations']} kinds" + ("  BELOW THE MINIMUM" if sets[name]["below_min"] else ""),
              flush=True)
    if len(groups) == 1:
        # One set: also at the run's top level, where single-set runs always kept it.
        only = next(iter(groups))
        with open(os.path.join(sets_dir, f"{only}.json")) as f:
            content = json.load(f)
        content["name"] = args.run_name
        with open(os.path.join(run_dir, "fact_set.json"), "w") as f:
            json.dump(content, f, indent=1)
    summary = {"run": args.run_name, "name": args.run_name, "models": models, "formats": fmts,
               "instruct_models": sorted(instruct), "data_paths": data_paths, "split": args.split,
               "candidates": len(rows), "min_facts": ct.MIN_FACTS,
               "sets": {name: {k: v for k, v in info.items() if k not in ("relations",)} for name, info in sets.items()},
               "below_min": sorted(name for name, info in sets.items() if info["below_min"]), **timing}
    with open(os.path.join(run_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
