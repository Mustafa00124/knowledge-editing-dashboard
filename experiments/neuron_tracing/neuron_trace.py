"""Neuron attribution: which individual MLP neurons carry a fact the model
knows, and does knocking them out actually take the fact away?

Knowledge Neurons (Dai et al., 2022), FiNE and NMKE all edit single MLP
neurons, chosen by how much each one is credited with the answer. Causal
tracing (causal_trace.py) stops at the layer; this goes one level down, with
the same facts, prompt formats and known-fact filter, so the two compare.

Per fact:

  1. Clean run. Record the answer token the model gives (the same filter as
     causal tracing: top non-whitespace token, starting an accepted answer,
     probability >= --min_prob) and every MLP neuron's activation at the last
     prompt token: the input to each layer's down projection.
  2. Integrated gradients (Dai et al.'s attribution). For each layer, scale
     that layer's activations at the last token from 0 to their real value in
     --ig_steps steps and accumulate the gradient of the answer probability:
         attribution_i = a_i * mean_k dP(answer | k/m * a) / da_i
     The attributions of one layer sum (approximately, by completeness) to
     what that layer's activations add to the answer probability over
     switching them all off.
  3. Selection. A fact's neurons are those above --threshold times its largest
     attribution (Dai's 0.2; EasyEdit's adaptive threshold), at most
     --max_neurons of them.
  4. Is it causal? Three extra forward passes:
       suppress  the selected neurons set to 0 at the last token
       control   the same number of random neurons, layer for layer, set to 0
       enhance   the selected neurons doubled
     and one on a different fact (another relation where possible) with this
     fact's neurons suppressed: specificity, the cross-talk an edit at these
     neurons would cause.

Aggregates (summary.json): where the selected neurons sit (share per layer,
attribution mass per layer, the peak, the share in the early-to-mid band next
to causal tracing's peak for the same model), how concentrated a fact's
attribution is, how much suppression removes against the random control, and
how much facts share neurons (within a relation against across relations,
plus the neurons selected for many facts). Known caveat, kept visible rather
than tuned away: attribution of this kind tends to favour late layers (Niu et
al., 2024, "What does the knowledge neuron thesis have to do with
knowledge?"), so the peak is reported next to the traced peak, not instead of
it.

Output layout is causal_trace.py's, so the dashboard's progress, log and
manifest machinery read it unchanged:

    <out_root>/runs/<run_name>/hparams.yaml, checkpoints.jsonl, summary.json
    <out_root>/runs/<run_name>/neurons.json   every fact's selection and layer mass
    <out_root>/manifest.json                  rebuilt from every runs/*/summary.json
"""
import argparse
import itertools
import json
import os
import sys
import time

import numpy as np
import torch
import yaml
from transformers import AutoModelForCausalLM, AutoTokenizer

EXP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(EXP_DIR))
sys.path.append(os.path.join(PROJECT_ROOT, "experiments"))
import launch_guard  # noqa: E402  (refuses untracked runs into results/)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "experiments", "causal_tracing"))
import causal_trace as CT  # noqa: E402
import components as C  # noqa: E402
import formats as F  # noqa: E402
import knowledge as KN  # noqa: E402

DEFAULT_OUT_ROOT = f"{PROJECT_ROOT}/results/investigations/neuron_tracing"
TRACED_LAYERS = f"{PROJECT_ROOT}/results/investigations/causal_tracing/traced_layers.json"
MIN_FACTS = CT.MIN_FACTS
# Selected for at least this many facts: a neuron shared that widely is more
# likely about the relation or the output format than about any one fact.
HUB_MIN_FACTS = 3

# Read by the dashboard (registry.model_dirs) to grey out models whose weights
# are missing; the same table as causal_trace.py.
MODEL_PATHS = {
    "qwen3-4b-base": f"{PROJECT_ROOT}/models/Qwen3-4B-Base",
    "qwen3-4b": f"{PROJECT_ROOT}/models/Qwen3-4B",
    "qwen3-4b-instruct-2507": f"{PROJECT_ROOT}/models/Qwen3-4B-Instruct-2507",
    "qwen3-4b-thinking-2507": f"{PROJECT_ROOT}/models/Qwen3-4B-Thinking-2507",
    "olmo-3-7b-base": f"{PROJECT_ROOT}/models/Olmo-3-7B-Base",
    "olmo-3-7b-instruct": f"{PROJECT_ROOT}/models/Olmo-3-7B-Instruct",
    "olmo-3-7b-think": f"{PROJECT_ROOT}/models/Olmo-3-7B-Think",
    "smollm3-3b-base": f"{PROJECT_ROOT}/models/SmolLM3-3B-Base",
    "smollm3-3b": f"{PROJECT_ROOT}/models/SmolLM3-3B",
    "map-neo-7b": f"{PROJECT_ROOT}/models/MAP-Neo-7B",
    "map-neo-7b-instruct": f"{PROJECT_ROOT}/models/MAP-Neo-7B-Instruct",
    "llama-3.1-8b": f"{PROJECT_ROOT}/models/Llama-3.1-8B",
    "llama-3.1-8b-instruct": f"{PROJECT_ROOT}/models/Llama-3.1-8B-Instruct",
    "deepseek-r1-distill-llama-8b": f"{PROJECT_ROOT}/models/DeepSeek-R1-Distill-Llama-8B",
    "mistral-7b-v0.1": f"{PROJECT_ROOT}/models/Mistral-7B-v0.1",
    "mistral-7b-instruct-v0.1": f"{PROJECT_ROOT}/models/Mistral-7B-Instruct-v0.1",
    "gpt-j-6b": f"{PROJECT_ROOT}/models/GPT-J-6B",
    "olmo-2-7b": f"{PROJECT_ROOT}/models/OLMo-2-7B",
    "gpt-neox-20b": f"{PROJECT_ROOT}/models/GPT-NeoX-20B",
}


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Neuron attribution: which MLP neurons carry a fact")
    p.add_argument("--model", required=True, choices=sorted(MODEL_PATHS))
    p.add_argument("--data_path", default=CT.DEFAULT_DATA_PATH)
    p.add_argument("--dataset_benchmark", default=None, help="human label, passed by the dashboard")
    p.add_argument("--dataset_subset", default=None, help="human label, passed by the dashboard")
    p.add_argument("--split", default="nontest", choices=F.SPLIT_CHOICES)
    p.add_argument("--fact_set", default="", help="trace this fixed fact list (select_facts.py)")
    p.add_argument("--allow_thin", type=int, default=0, help=f"1 traces a fact set below {MIN_FACTS} facts")
    p.add_argument("--format", default="completion", choices=sorted(F.FORMATS))
    p.add_argument("--n_prompts", type=int, default=100, help="facts to attribute, after the known-fact filter")
    p.add_argument("--max_candidates", type=int, default=2000)
    p.add_argument("--min_prob", type=float, default=0.1)
    p.add_argument("--ig_steps", type=int, default=20, help="integrated-gradient steps (Dai et al. use 20)")
    p.add_argument("--layer_batch", type=int, default=8,
                   help="layers attributed in one forward/backward pass (memory against speed)")
    p.add_argument("--threshold", type=float, default=0.2,
                   help="a fact's neurons: attribution above this share of its largest (Dai: 0.2)")
    p.add_argument("--max_neurons", type=int, default=50, help="at most this many neurons per fact")
    p.add_argument("--band", default=f"{CT.DEFAULT_BAND[0]},{CT.DEFAULT_BAND[1]}",
                   help="early-to-mid band as a share of depth, 'low,high'")
    p.add_argument("--dtype", default="bfloat16", choices=["bfloat16", "float16", "float32"])
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--checkpoint_every", type=int, default=10)
    p.add_argument("--run_name", default=None)
    p.add_argument("--out_root", default=DEFAULT_OUT_ROOT)
    launch_guard.add_argument(p)
    KN.add_arguments(p)
    args = p.parse_args(argv)
    args.band = tuple(float(x) for x in args.band.split(","))
    return args


# ---------------------------------------------------------------- attribution

def neuron_activations(model, inputs, table):
    """Clean run: last-token logits and every layer's neuron activations
    there, as [n_layers, d_neurons]."""
    acts = {}

    def capture(layer):
        def hook(module, args, kwargs):
            acts[layer] = C.get_input(args, kwargs)[0, -1].detach().clone()
        return hook

    with torch.no_grad(), C.hooks(model, pre=[(table["neurons"].format(L), capture(L))
                                              for L in range(table["n_layers"])]):
        logits = model(**inputs).logits[0, -1].float()
    return logits, torch.stack([acts[L] for L in range(table["n_layers"])])


def integrated_gradients(model, inputs, table, acts, target, steps, layer_batch):
    """[n_layers, d_neurons] attributions to the answer probability.

    Several layers share one pass: each gets its own `steps` rows of the
    batch, and only its own rows are scaled, so rows never mix."""
    n_layers = table["n_layers"]
    alphas = (torch.arange(steps, device=acts.device, dtype=torch.float32) + 0.5) / steps
    out = torch.zeros(acts.shape, dtype=torch.float32, device=acts.device)
    for start in range(0, n_layers, layer_batch):
        layers = list(range(start, min(n_layers, start + layer_batch)))
        rows = steps * len(layers)
        batch = {k: v[:1].repeat(rows, 1) for k, v in inputs.items()}
        scaled = {L: (alphas[:, None] * acts[L].float()[None]).to(acts.dtype).requires_grad_(True) for L in layers}

        def scale(group, layer):
            def hook(module, args, kwargs):
                x = C.get_input(args, kwargs).clone()
                x[group * steps:(group + 1) * steps, -1] = scaled[layer]
                return C.set_input(args, kwargs, x)
            return hook

        with torch.enable_grad(), C.hooks(model, pre=[(table["neurons"].format(L), scale(g, L))
                                                      for g, L in enumerate(layers)]):
            logits = model(**batch).logits[:, -1].float()
            prob = torch.softmax(logits, dim=-1)[:, target].sum()
            grads = torch.autograd.grad(prob, [scaled[L] for L in layers])
        for L, grad in zip(layers, grads):
            out[L] = acts[L].float() * grad.float().mean(0)
    return out


def select(attr, threshold, max_neurons):
    """Dai et al.'s selection: above `threshold` x the largest attribution,
    capped at the top `max_neurons`. Returns [(layer, index, score)]."""
    peak = float(attr.max())
    if peak <= 0:
        return []
    flat = attr.flatten()
    keep = torch.nonzero(flat > threshold * peak).flatten()
    keep = keep[flat[keep].argsort(descending=True)][:max_neurons]
    d = attr.shape[1]
    return [(int(i) // d, int(i) % d, round(float(flat[i]), 6)) for i in keep]


def set_neurons(model, table, inputs, row_edits):
    """Last-token answer probabilities with neurons overwritten, one batch
    row per edit. row_edits: list of {layer: (indices, factor)}; factor 0
    suppresses, 2 doubles."""
    batch = {k: v[:1].repeat(len(row_edits), 1) for k, v in inputs.items()}
    layers = sorted({L for edits in row_edits for L in edits})

    def edit(layer):
        def hook(module, args, kwargs):
            x = C.get_input(args, kwargs).clone()
            for row, edits in enumerate(row_edits):
                if layer in edits:
                    indices, factor = edits[layer]
                    x[row, -1, indices] = x[row, -1, indices] * factor
            return C.set_input(args, kwargs, x)
        return hook

    with torch.no_grad(), C.hooks(model, pre=[(table["neurons"].format(L), edit(L)) for L in layers]):
        logits = model(**batch).logits[:, -1].float()
    return torch.softmax(logits, dim=-1)


def by_layer(neurons, device):
    out = {}
    for layer, index, _ in neurons:
        out.setdefault(layer, []).append(index)
    return {L: torch.tensor(ix, device=device) for L, ix in out.items()}


def random_like(neurons, d_neurons, rng, device):
    """As many random neurons per layer as `neurons` has, none of them."""
    chosen = by_layer(neurons, "cpu")
    out = {}
    for layer, indices in chosen.items():
        pool = np.setdiff1d(np.arange(d_neurons), indices.numpy())
        out[layer] = torch.tensor(rng.choice(pool, size=len(indices), replace=False), device=device)
    return out


# ---------------------------------------------------------------- per fact

def trace_prompt(model, tok, device, row, args, table, rng, others):
    item = KN.prepare(model, tok, device, row, F.build(row, args.format, tok), args)
    if item is None:
        return None
    encoded = F.encode(tok, item, return_tensors="pt")
    inputs = {k: encoded[k].to(device) for k in ("input_ids", "attention_mask")}

    logits, acts = neuron_activations(model, inputs, table)
    probs = torch.softmax(logits, dim=-1)
    target = CT.recall_target(tok, probs, item["answers"], args.min_prob)
    if target is None:
        return None
    p_clean = float(probs[target])

    attr = integrated_gradients(model, inputs, table, acts, target, args.ig_steps, args.layer_batch)
    neurons = select(attr, args.threshold, args.max_neurons)
    positive = attr.clamp(min=0)
    total = float(positive.sum())
    layer_mass = (positive.sum(1) / max(total, 1e-12)).tolist()
    top10 = float(positive.flatten().topk(min(10, positive.numel())).values.sum()) / max(total, 1e-12)

    out = {
        "id": row.get("id"), "relation": row.get("relation"), "domain": row.get("domain"),
        "prompt": item["text"], "lead_in": item.get("lead_in", ""), "subject": row.get("subject"),
        "answer": tok.decode([target]),
        "target": target, "p_clean": p_clean,
        "neurons": neurons, "layer_mass": [round(v, 5) for v in layer_mass],
        "top10_share": round(top10, 4), "attr_positive": round(total, 6),
        # completeness: what the attributions add up to, per layer
        "layer_sum": [round(float(v), 6) for v in attr.sum(1)],
        "top": [(L, i, s) for L, i, s in select(attr, 0.0, 20)],
    }
    if neurons:
        chosen = by_layer(neurons, device)
        control = random_like(neurons, table["d_neurons"], rng, device)
        p = set_neurons(model, table, inputs, [
            {L: (ix, 0.0) for L, ix in chosen.items()},
            {L: (ix, 0.0) for L, ix in control.items()},
            {L: (ix, 2.0) for L, ix in chosen.items()},
        ])[:, target]
        out.update({"p_suppress": float(p[0]), "p_control": float(p[1]), "p_enhance": float(p[2])})
        # Specificity: this fact's neurons switched off on someone else's fact.
        other = next((o for o in reversed(others) if o["relation"] != row.get("relation")), None) \
            or (others[-1] if others else None)
        if other is not None:
            p_other = set_neurons(model, table, other["inputs"], [{L: (ix, 0.0) for L, ix in chosen.items()}])
            out["other_id"] = other["id"]
            out["other_p_clean"] = other["p_clean"]
            out["other_p_suppress"] = float(p_other[0, other["target"]])
    others.append({"id": row.get("id"), "relation": row.get("relation"), "inputs": inputs,
                   "target": target, "p_clean": p_clean})
    del others[:-20]
    return out


# ---------------------------------------------------------------- aggregation

def _ci(values, n_boot=1000, seed=0):
    values = np.asarray(values, dtype=float)
    if len(values) < 2:
        return None
    rng = np.random.default_rng(seed)
    means = values[rng.integers(0, len(values), size=(n_boot, len(values)))].mean(axis=1)
    return [round(float(np.percentile(means, 2.5)), 4), round(float(np.percentile(means, 97.5)), 4)]


def _mean(values):
    return round(float(np.mean(values)), 4) if len(values) else None


def overlap(facts):
    """Mean Jaccard overlap of selected neuron sets between pairs of facts of
    the same relation, and of different relations."""
    sets = [(f.get("relation"), {(L, i) for L, i, _ in f["neurons"]}) for f in facts if f["neurons"]]
    same, diff = [], []
    for (ra, a), (rb, b) in itertools.combinations(sets, 2):
        j = len(a & b) / len(a | b)
        (same if ra is not None and ra == rb else diff).append(j)
    return {"same_relation": _mean(same), "n_same": len(same), "other_relation": _mean(diff), "n_other": len(diff)}


def hubs(facts, limit=25):
    counts, relations = {}, {}
    for f in facts:
        for L, i, _ in f["neurons"]:
            counts[(L, i)] = counts.get((L, i), 0) + 1
            relations.setdefault((L, i), set()).add(f.get("relation"))
    ranked = sorted(((n, key) for key, n in counts.items() if n >= HUB_MIN_FACTS), reverse=True)[:limit]
    return [{"layer": L, "neuron": i, "facts": n, "relations": sorted(r for r in relations[(L, i)] if r)}
            for n, (L, i) in ranked]


def traced_peak(model):
    try:
        with open(TRACED_LAYERS) as f:
            entry = json.load(f).get(model)
    except (OSError, json.JSONDecodeError):
        return None
    return entry.get("peak_layer") if entry else None


def aggregate(facts, n_layers, band, model=None, seed=0):
    out = {"n_prompts": len(facts)}
    if not facts:
        return out
    low, high = band
    in_band = [L for L in range(n_layers) if low <= L / n_layers < high]
    counts = np.zeros(n_layers)
    for f in facts:
        for L, _, _ in f["neurons"]:
            counts[L] += 1
    n_selected = int(counts.sum())
    mass = np.mean([f["layer_mass"] for f in facts], axis=0)
    per_fact = [len(f["neurons"]) for f in facts]
    out.update({
        "p_clean": _mean([f["p_clean"] for f in facts]),
        "neurons_per_fact": _mean(per_fact),
        "neurons_per_fact_median": int(np.median(per_fact)),
        "facts_without_neurons": sum(1 for n in per_fact if n == 0),
        "layer_share": [round(float(c / max(n_selected, 1)), 5) for c in counts],
        "layer_mass": [round(float(v), 5) for v in mass],
        "peak_layer": int(np.argmax(mass)),
        "peak_layer_count": int(np.argmax(counts)),
        "band": [low, high],
        "band_layers": [in_band[0], in_band[-1]] if in_band else None,
        "share_in_band": round(float(counts[in_band].sum() / max(n_selected, 1)), 4),
        "mass_in_band": round(float(mass[in_band].sum()), 4),
        "baseline": round(len(in_band) / n_layers, 4),
        "share_last_quarter": round(float(counts[int(0.75 * n_layers):].sum() / max(n_selected, 1)), 4),
        "top10_share": _mean([f["top10_share"] for f in facts]),
        "overlap": overlap(facts),
        "hubs": hubs(facts),
    })
    out["layers"] = [out["peak_layer"]]
    tested = [f for f in facts if "p_suppress" in f]
    if tested:
        drop = [(f["p_clean"] - f["p_suppress"]) / f["p_clean"] for f in tested]
        control = [(f["p_clean"] - f["p_control"]) / f["p_clean"] for f in tested]
        gain = [(f["p_enhance"] - f["p_clean"]) / f["p_clean"] for f in tested]
        out["ablation"] = {
            "n_facts": len(tested),
            "suppress_drop": _mean(drop), "suppress_drop_ci": _ci(drop, seed=seed),
            "control_drop": _mean(control), "control_drop_ci": _ci(control, seed=seed),
            "enhance_gain": _mean(gain), "enhance_gain_ci": _ci(gain, seed=seed),
        }
        crossed = [f for f in tested if "other_p_suppress" in f]
        if crossed:
            spill = [(f["other_p_clean"] - f["other_p_suppress"]) / f["other_p_clean"] for f in crossed]
            out["ablation"]["other_fact_drop"] = _mean(spill)
            out["ablation"]["other_fact_drop_ci"] = _ci(spill, seed=seed)
        out["ablation"]["verdict"] = _verdict(out["ablation"])
    peak = traced_peak(model) if model else None
    out["traced_peak_layer"] = peak
    return out


def _verdict(a):
    """causal: suppression clearly beats the random control (interval above
    the control's) and removes at least a third of the probability while
    leaving other facts mostly alone (under half the fact's own drop);
    partial: beats the control; not_causal otherwise."""
    if not a.get("suppress_drop_ci") or not a.get("control_drop_ci"):
        return None
    beats = a["suppress_drop_ci"][0] > a["control_drop_ci"][1]
    spill = a.get("other_fact_drop")
    specific = spill is None or spill < 0.5 * a["suppress_drop"]
    if beats and a["suppress_drop"] >= 0.33 and specific:
        return "causal"
    if beats:
        return "partial"
    return "not_causal"


# ---------------------------------------------------------------- run

def main(argv=None):
    args = parse_args(argv)
    launch_guard.require_dashboard(args.out_root, args.untracked, "neuron_tracing")
    torch.manual_seed(args.seed)
    rng = np.random.default_rng(args.seed)

    fact_set_info = None
    if args.fact_set:
        fact_set_info, rows = CT.load_fact_set(args.fact_set)
        if len(rows) < MIN_FACTS and not args.allow_thin:
            raise SystemExit(f"fact set {fact_set_info.get('name')} has {len(rows)} facts, below the {MIN_FACTS} "
                             f"minimum; pass --allow_thin 1 to attribute it anyway")
    else:
        rows = F.load_rows(args.data_path, args.split, args.max_candidates)
    if not rows:
        raise SystemExit(f"no usable records in {args.fact_set or args.data_path}")
    KN.setup(args, fact_set_info, args.model, args.format)

    run_name = args.run_name or f"{args.model}_{args.format}_n{args.n_prompts}"
    run_dir = os.path.join(args.out_root, "runs", run_name)
    os.makedirs(run_dir, exist_ok=True)

    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    model_path = MODEL_PATHS[args.model]
    print(f"[{run_name}] loading {model_path}", flush=True)
    tok = AutoTokenizer.from_pretrained(model_path)
    if args.format in F.CHAT_FORMATS and not F.has_chat_template(tok):
        raise SystemExit(f"{args.model} has no chat template, so it cannot be traced as {args.format}")
    model = AutoModelForCausalLM.from_pretrained(model_path, dtype=getattr(torch, args.dtype)).to(device)
    model.eval()
    model.requires_grad_(False)
    table = C.resolve(model, need=("neurons",))
    n_layers = table["n_layers"]
    print(f"[{run_name}] {n_layers} layers x {table['d_neurons']} neurons, format {args.format}", flush=True)

    config = {
        "run": run_name, "model": args.model, "model_path": model_path,
        "model_type": model.config.model_type, "n_layers": n_layers, "d_neurons": table["d_neurons"],
        "neuron_module": table["neurons"],
        "data_path": args.data_path, "split": args.split, "format": args.format,
        "fact_set": args.fact_set or None,
        "fact_set_name": fact_set_info.get("name") if fact_set_info else None,
        "fact_set_size": len(rows) if fact_set_info else None,
        "dataset_benchmark": args.dataset_benchmark, "dataset_subset": args.dataset_subset,
        "n_prompts": args.n_prompts, "max_candidates": args.max_candidates, "min_prob": args.min_prob,
        "ig_steps": args.ig_steps, "threshold": args.threshold, "max_neurons": args.max_neurons,
        "band": list(args.band), "dtype": args.dtype, "seed": args.seed,
    }
    with open(os.path.join(run_dir, "hparams.yaml"), "w") as f:
        yaml.safe_dump(config, f, sort_keys=True)

    started_at, t_start = CT._now(), time.time()
    ckpt_file = open(os.path.join(run_dir, "checkpoints.jsonl"), "w")
    facts, others, scanned, skipped = [], [], 0, 0
    total = min(args.n_prompts, len(rows))

    def checkpoint():
        summary = aggregate(facts, n_layers, args.band)
        row = {
            "step": len(facts), "total_steps": total, "at": CT._now(),
            "elapsed_sec": round(time.time() - t_start, 2), "scanned": scanned, "skipped_unknown": skipped,
            "peak_layer": summary.get("peak_layer"), "neurons_per_fact": summary.get("neurons_per_fact"),
            "suppress_drop": (summary.get("ablation") or {}).get("suppress_drop"),
            **CT.memory_snapshot(device),
        }
        ckpt_file.write(json.dumps(row) + "\n")
        ckpt_file.flush()
        print(f"[{run_name}] " + " ".join(f"{k}={v}" for k, v in row.items()), flush=True)

    checkpoint()
    for row in rows:
        if len(facts) >= args.n_prompts:
            break
        scanned += 1
        fact = trace_prompt(model, tok, device, row, args, table, rng, others)
        if fact is None:
            skipped += 1
            continue
        facts.append(fact)
        if len(facts) % args.checkpoint_every == 0:
            checkpoint()
    if len(facts) % args.checkpoint_every:
        checkpoint()
    ckpt_file.close()

    summary = {
        **config,
        **aggregate(facts, n_layers, args.band, args.model, args.seed),
        "thin": len(facts) < MIN_FACTS,
        "scanned": scanned, "skipped_unknown": skipped,
        "known_rate": round(len(facts) / scanned, 4) if scanned else None,
        "started_at": started_at, "finished_at": CT._now(),
        "total_sec": round(time.time() - t_start, 2),
        **CT.memory_snapshot(device),
    }
    with open(os.path.join(run_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    with open(os.path.join(run_dir, "neurons.json"), "w") as f:
        json.dump({"run": run_name, "summary": summary,
                   "facts": [{k: v for k, v in fact.items() if k != "target"} for fact in facts]}, f)

    CT.rebuild_manifest(args.out_root)
    ablation = summary.get("ablation") or {}
    print(f"[{run_name}] done: {len(facts)} facts, {summary.get('neurons_per_fact')} neurons each, "
          f"peak layer {summary.get('peak_layer')} (traced {summary.get('traced_peak_layer')}), "
          f"suppression drop {ablation.get('suppress_drop')} vs control {ablation.get('control_drop')}: "
          f"{ablation.get('verdict')}" + (" THIN" if summary["thin"] else ""), flush=True)


if __name__ == "__main__":
    main()
