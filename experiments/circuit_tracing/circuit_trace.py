"""Circuit tracing: which attention heads and MLPs, and which paths between
them, carry a fact from the subject to the answer?

Causal tracing (causal_trace.py) restores one site at a time and finds the
layer. This scores every component at once, finer than the layer: each
attention head, each MLP, at each kind of token position, and every
residual-stream path from one block to a later one. Same facts, prompt
formats, known-fact filter and corruption as causal tracing (Gaussian noise
on the subject's input embeddings), so the two read side by side.

Per fact, one batch: row 0 clean, rows 1.. corrupted (one per noise sample).

  Node attribution (attribution patching; Nanda 2023, Kramar et al. 2024).
     The effect of patching a component's clean activation into the
     corrupted run, to first order:
         (a_clean - a_corrupt) . d metric / d a      (on the corrupted run)
     with metric = log P(answer). Heads are scored on their slice of the
     attention output projection's input, MLPs on what they write to the
     residual. Scores are kept per position: the corrupted (subject) tokens,
     the last token, and the rest. Geva et al. (2023) find MLPs enriching the
     subject at its own tokens and attention moving the attribute to the
     last token; the split is what shows whether a model does that.
  Edge attribution (EAP; Syed et al., 2023). For every sender (embedding,
     attention block L, MLP L) and every later receiver (attention L', MLP
     L', the unembedding), the same product with the receiver's own input
     gradient: the gradient through that receiver only, taken on a zero
     added to its input rather than on the shared residual stream.
  Check. Attribution patching is an approximation, and it misses some
     effects (Kramar et al., 2024). The --verify_k components it ranks
     highest for the fact are actually patched, and estimate and real
     effect are compared (rank correlation, reported).

Then the circuit (after all facts): components are ranked by their mean
normalised score on half the facts (even positions) and tested on the other
half, so a circuit is not graded on the facts it was chosen from:

  sufficiency  patch the top K clean into the corrupted run: share of the
               lost probability recovered, against K random components of
               the same mix (heads and MLPs)
  necessity    run clean but hold the top K at their corrupted values:
               share of the probability lost

once over every component and once over heads alone: a whole MLP outweighs
a single head, so the mixed ranking fills with MLPs, and the heads-only test
is what says whether attention by itself moves the fact to the answer.

summary.json: per-layer MLP and attention scores by position, the top heads,
the top edges, the sufficiency/necessity curves over K, the smallest K that
recovers 80% on held-out facts, and the verdict (compact, distributed,
not_found). circuit.json adds the full head grid, the edge matrix and every
fact's own top components.

Output layout is causal_trace.py's (runs/<name>/hparams.yaml,
checkpoints.jsonl, summary.json; manifest.json rebuilt from summaries), so
the dashboard machinery reads it unchanged.
"""
import argparse
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
sys.path.insert(0, os.path.join(PROJECT_ROOT, "experiments", "causal_tracing"))
import causal_trace as CT  # noqa: E402
import components as C  # noqa: E402
import formats as F  # noqa: E402

DEFAULT_OUT_ROOT = f"{PROJECT_ROOT}/results/investigations/circuit_tracing"
TRACED_LAYERS = f"{PROJECT_ROOT}/results/investigations/causal_tracing/traced_layers.json"
MIN_FACTS = CT.MIN_FACTS
POSITIONS = ("subject", "last", "other")
# The corruption must take a fact away for there to be anything to restore:
# at least this much log-probability lost.
MIN_GAP = 0.1
# A circuit this size or smaller that recovers 80% is "compact".
COMPACT_K = 20

# Read by the dashboard (registry.model_dirs); the same table as causal_trace.py.
MODEL_PATHS = {
    "qwen3-4b-base": f"{PROJECT_ROOT}/models/Qwen3-4B-Base",
    "qwen3-4b": f"{PROJECT_ROOT}/models/Qwen3-4B",
    "qwen3-4b-instruct-2507": f"{PROJECT_ROOT}/models/Qwen3-4B-Instruct-2507",
    "qwen3-4b-thinking-2507": f"{PROJECT_ROOT}/models/Qwen3-4B-Thinking-2507",
    "olmo-3-7b-base": f"{PROJECT_ROOT}/models/Olmo-3-7B-Base",
    "olmo-3-7b-instruct": f"{PROJECT_ROOT}/models/Olmo-3-7B-Instruct",
    "olmo-3-7b-think": f"{PROJECT_ROOT}/models/Olmo-3-7B-Think",
    "llama-3.1-8b": f"{PROJECT_ROOT}/models/Llama-3.1-8B",
    "llama-3.1-8b-instruct": f"{PROJECT_ROOT}/models/Llama-3.1-8B-Instruct",
    "deepseek-r1-distill-llama-8b": f"{PROJECT_ROOT}/models/DeepSeek-R1-Distill-Llama-8B",
    "mistral-7b-v0.1": f"{PROJECT_ROOT}/models/Mistral-7B-v0.1",
    "mistral-7b-instruct-v0.1": f"{PROJECT_ROOT}/models/Mistral-7B-Instruct-v0.1",
    "gpt-j-6b": f"{PROJECT_ROOT}/models/GPT-J-6B",
    "olmo-2-7b": f"{PROJECT_ROOT}/models/OLMo-2-7B",
    "gpt-neox-20b": f"{PROJECT_ROOT}/models/GPT-NeoX-20B",
    "gpt-oss-20b": f"{PROJECT_ROOT}/models/GPT-OSS-20B",
}


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Circuit tracing: heads, MLPs and paths from subject to answer")
    p.add_argument("--model", required=True, choices=sorted(MODEL_PATHS))
    p.add_argument("--data_path", default=CT.DEFAULT_DATA_PATH)
    p.add_argument("--dataset_benchmark", default=None, help="human label, passed by the dashboard")
    p.add_argument("--dataset_subset", default=None, help="human label, passed by the dashboard")
    p.add_argument("--split", default="nontest", choices=F.SPLIT_CHOICES)
    p.add_argument("--fact_set", default="", help="trace this fixed fact list (select_facts.py)")
    p.add_argument("--allow_thin", type=int, default=0, help=f"1 traces a fact set below {MIN_FACTS} facts")
    p.add_argument("--format", default="completion", choices=sorted(F.FORMATS))
    p.add_argument("--n_prompts", type=int, default=100, help="facts to trace, after the known-fact filter")
    p.add_argument("--max_candidates", type=int, default=2000)
    p.add_argument("--min_prob", type=float, default=0.1)
    p.add_argument("--noise_scale", type=float, default=3.0, help="as causal tracing: x embedding std")
    p.add_argument("--n_noise_samples", type=int, default=10, help="corrupted rows per fact")
    p.add_argument("--verify_k", type=int, default=10,
                   help="components per fact actually patched to check the attribution (0 = off)")
    p.add_argument("--circuit_sizes", default="1,2,5,10,20,50,100",
                   help="circuit sizes K tested for sufficiency and necessity on held-out facts")
    p.add_argument("--band", default=f"{CT.DEFAULT_BAND[0]},{CT.DEFAULT_BAND[1]}",
                   help="early-to-mid band as a share of depth, 'low,high'")
    p.add_argument("--dtype", default="bfloat16", choices=["bfloat16", "float16", "float32"])
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--checkpoint_every", type=int, default=10)
    p.add_argument("--run_name", default=None)
    p.add_argument("--out_root", default=DEFAULT_OUT_ROOT)
    args = p.parse_args(argv)
    args.band = tuple(float(x) for x in args.band.split(","))
    args.circuit_sizes = [int(k) for k in args.circuit_sizes.split(",") if k.strip()]
    return args


# ---------------------------------------------------------------- components

def senders(table):
    """("emb",) then attention and MLP of every layer, in residual order."""
    out = [("emb", -1)]
    for L in range(table["n_layers"]):
        out += [("attn", L), ("mlp", L)]
    return out


def receivers(table):
    """Attention and MLP inputs of every layer (one "block" input where they
    share it), then the unembedding."""
    out = []
    for L in range(table["n_layers"]):
        if table["mlp_read"]:
            out += [("attn", L), ("mlp", L)]
        else:
            out.append(("block", L))
    out.append(("logits", table["n_layers"]))
    return out


def edge_valid(sender, receiver, parallel):
    """Can what `sender` writes reach `receiver`'s input at all?"""
    kind, layer = sender
    r_kind, r_layer = receiver
    if kind == "emb" or r_kind == "logits":
        return True
    if r_layer > layer:
        return True
    # Same layer: only a sequential block's attention feeds its own MLP.
    return r_layer == layer and kind == "attn" and r_kind == "mlp" and not parallel


def label(component):
    kind, layer = component[0], component[1]
    if kind == "head":
        return f"L{layer}.H{component[2]}"
    if kind in ("emb", "logits"):
        return kind
    return f"{kind[0]}{layer}" if kind != "block" else f"b{layer}"


def nodes(table):
    """Every node a circuit can contain: each head, and each MLP."""
    out = [("head", L, h) for L in range(table["n_layers"]) for h in range(table["n_heads"])]
    return out + [("mlp", L) for L in range(table["n_layers"])]


# ---------------------------------------------------------------- runs

def _embed_noise(noise, noise_tokens, leaf=None):
    """Forward hook adding noise to rows 1.. of the embedding. With `leaf`
    (a dict) the result becomes a leaf that requires grad and is stored
    there, which is what lets gradients flow with the weights frozen."""
    def hook(module, args, output):
        e = output.detach().clone()
        if noise is not None and noise_tokens:
            e[1:, noise_tokens] += noise.to(e.device, e.dtype)
        if leaf is not None:
            e.requires_grad_(True)
            leaf["emb"] = e
        return e
    return hook


def attribute(model, inputs, table, target, noise, noise_tokens):
    """One forward/backward pass: node scores by position, the edge matrix,
    and the clean/corrupted log-probabilities."""
    n_layers, n_heads, head_dim = table["n_layers"], table["n_heads"], table["head_dim"]
    z, writes, reads = {}, {}, {}

    def keep_z(layer):
        def hook(module, args, kwargs):
            z[layer] = C.get_input(args, kwargs)
        return hook

    def keep_write(key):
        def hook(module, args, output):
            writes[key] = C.out_tensor(output)
        return hook

    def add_read(key):
        def hook(module, args, kwargs):
            x = C.get_input(args, kwargs)
            d = torch.zeros_like(x, requires_grad=True)
            reads[key] = d
            return C.set_input(args, kwargs, x + d)
        return hook

    forward = [(table["embed"], _embed_noise(noise, noise_tokens, leaf=writes))]
    pre = []
    for L in range(n_layers):
        pre.append((table["heads"].format(L), keep_z(L)))
        forward.append((table["attn_write"].format(L), keep_write(("attn", L))))
        forward.append((table["mlp_write"].format(L), keep_write(("mlp", L))))
    for key in receivers(table):
        kind, L = key
        if kind == "logits":
            name = table["final_read"]
        elif kind in ("attn", "block"):
            name = table["attn_read"].format(L)
        else:
            name = table["mlp_read"].format(L)
        pre.append((name, add_read(key)))

    with torch.enable_grad(), C.hooks(model, forward=forward, pre=pre):
        logits = model(**inputs).logits[:, -1].float()
        logp = torch.log_softmax(logits, dim=-1)[:, target]
        metric = logp[1:].mean()
        send = senders(table)
        recv = receivers(table)
        tensors = [z[L] for L in range(n_layers)] + [writes[s if s[0] != "emb" else "emb"] for s in send] \
            + [reads[r] for r in recv]
        grads = torch.autograd.grad(metric, tensors)

    n = logp.shape[0] - 1
    g_z = grads[:n_layers]
    g_send = grads[n_layers:n_layers + len(send)]
    g_recv = grads[n_layers + len(send):]

    def delta(t):
        t = t.detach().float()
        return t[:1] - t[1:]

    # The metric is already a mean over the corrupted rows, so each row's
    # gradient carries its 1/n: summing over rows gives the mean effect.
    with torch.no_grad():
        # heads: [n_layers, T, H]
        heads = torch.stack([
            (delta(z[L]) * g_z[L][1:].float()).view(n, -1, n_heads, head_dim).sum(-1).sum(0)
            for L in range(n_layers)])
        sender_deltas = [delta(writes[s if s[0] != "emb" else "emb"]) for s in send]
        # writer node scores: [len(send), T]
        writer = torch.stack([(d * g[1:].float()).sum(-1).sum(0) for d, g in zip(sender_deltas, g_send)])
        D = torch.stack([d.reshape(-1) for d in sender_deltas])                 # [S, n*T*d]
        G = torch.stack([g[1:].float().reshape(-1) for g in g_recv])           # [R, n*T*d]
        edges = D @ G.T                                                         # [S, R]
        mask = torch.tensor([[edge_valid(s, r, table["parallel"]) for r in recv] for s in send], device=edges.device)
        edges = torch.where(mask, edges, torch.zeros_like(edges))
    return {
        "logp_clean": float(logp[0].detach()), "logp_corrupt": float(logp[1:].detach().mean()),
        "heads": heads.cpu(), "writer": writer.cpu(), "edges": edges.cpu(),
    }


def run_patched(model, inputs, table, target, noise, noise_tokens, restore=(), freeze=None, capture=(),
                noisy=True):
    """Answer probability on rows 1.. with nodes patched.

    restore  nodes whose clean activation (row 0) is copied into rows 1..
    freeze   {node: tensor} rows 1.. set to these (recorded) values
    capture  nodes whose rows 1.. values are recorded and returned
    noisy    False runs every row clean (the necessity test)
    Returns (mean probability over rows 1.., captured)."""
    freeze = freeze or {}
    head_dim = table["head_dim"]
    by_layer = {}
    for node in set(restore) | set(freeze) | set(capture):
        by_layer.setdefault((node[0], node[1]), []).append(node)
    captured = {}

    def apply(x, node):
        sl = (slice(None), slice(node[2] * head_dim, (node[2] + 1) * head_dim)) if node[0] == "head" else (slice(None),)
        if node in capture:
            captured[node] = x[(slice(1, None),) + sl].detach().clone()
        if node in restore:
            x[(slice(1, None),) + sl] = x[(slice(0, 1),) + sl]
        if node in freeze:
            x[(slice(1, None),) + sl] = freeze[node].to(x.device, x.dtype)

    def head_hook(group):
        def hook(module, args, kwargs):
            x = C.get_input(args, kwargs).clone()
            for node in group:
                apply(x, node)
            return C.set_input(args, kwargs, x)
        return hook

    def mlp_hook(group):
        def hook(module, args, output):
            x = C.out_tensor(output).clone()
            for node in group:
                apply(x, node)
            return C.replace_output(output, x)
        return hook

    forward = [(table["embed"], _embed_noise(noise if noisy else None, noise_tokens))]
    pre = []
    for (kind, L), group in by_layer.items():
        if kind == "head":
            pre.append((table["heads"].format(L), head_hook(group)))
        else:
            forward.append((table["mlp_write"].format(L), mlp_hook(group)))
    with torch.no_grad(), C.hooks(model, forward=forward, pre=pre):
        logits = model(**inputs).logits[1:, -1].float()
    return float(torch.softmax(logits, dim=-1)[:, target].mean()), captured


def run_patched_logp(model, inputs, table, target, noise, noise_tokens, restore):
    """Mean log P(answer) over rows 1.. with `restore` patched clean: the
    quantity attribution patching estimates."""
    head_dim = table["head_dim"]
    heads = {}
    mlps = []
    for node in restore:
        if node[0] == "head":
            heads.setdefault(node[1], []).append(node[2])
        else:
            mlps.append(node[1])

    def head_hook(hs):
        def hook(module, args, kwargs):
            x = C.get_input(args, kwargs).clone()
            for h in hs:
                x[1:, :, h * head_dim:(h + 1) * head_dim] = x[:1, :, h * head_dim:(h + 1) * head_dim]
            return C.set_input(args, kwargs, x)
        return hook

    def mlp_hook(module, args, output):
        x = C.out_tensor(output).clone()
        x[1:] = x[:1]
        return C.replace_output(output, x)

    forward = [(table["embed"], _embed_noise(noise, noise_tokens))]
    forward += [(table["mlp_write"].format(L), mlp_hook) for L in mlps]
    pre = [(table["heads"].format(L), head_hook(hs)) for L, hs in heads.items()]
    with torch.no_grad(), C.hooks(model, forward=forward, pre=pre):
        logits = model(**inputs).logits[1:, -1].float()
    return float(torch.log_softmax(logits, dim=-1)[:, target].mean())


# ---------------------------------------------------------------- per fact

def position_masks(n_tokens, noise_tokens):
    """[3, T] masks: corrupted (subject) tokens, the last token, the rest."""
    masks = torch.zeros(len(POSITIONS), n_tokens)
    masks[0, noise_tokens] = 1
    masks[0, n_tokens - 1] = 0
    masks[1, n_tokens - 1] = 1
    masks[2] = 1 - masks[0] - masks[1]
    return masks


def node_totals(att, table):
    """Each node's score summed over positions: {node: score}."""
    heads = att["heads"].sum(1)                     # [L, H]
    out = {("head", L, h): float(heads[L, h]) for L in range(table["n_layers"]) for h in range(table["n_heads"])}
    for i, (kind, L) in enumerate(senders(table)):
        if kind == "mlp":
            out[("mlp", L)] = float(att["writer"][i].sum())
    return out


def spearman(a, b):
    if len(a) < 3:
        return None
    ra = np.argsort(np.argsort(a))
    rb = np.argsort(np.argsort(b))
    if ra.std() == 0 or rb.std() == 0:
        return None
    return float(np.corrcoef(ra, rb)[0, 1])


def trace_prompt(model, tok, device, row, args, table, rng):
    item = F.build(row, args.format, tok)
    if item is None:
        return None, "unbuildable"
    spans = F.token_spans(tok, item)
    if not spans:
        return None, "unbuildable"
    encoded = F.encode(tok, item, return_tensors="pt")
    batch = 1 + args.n_noise_samples
    inputs = {k: encoded[k].repeat(batch, 1).to(device) for k in ("input_ids", "attention_mask")}

    with torch.no_grad():
        clean_logits = model(**{k: v[:1] for k, v in inputs.items()}).logits[0, -1].float()
    probs = torch.softmax(clean_logits, dim=-1)
    target = CT.recall_target(tok, probs, item["answers"], args.min_prob)
    if target is None:
        return None, "unknown"

    n_tokens = inputs["input_ids"].shape[1]
    noise_tokens = sorted({i for start, end in spans for i in range(start, end)})
    noise = torch.from_numpy(
        args.noise_level * rng.standard_normal((args.n_noise_samples, len(noise_tokens), model.config.hidden_size))
    ).float()

    att = attribute(model, inputs, table, target, noise, noise_tokens)
    gap = att["logp_clean"] - att["logp_corrupt"]
    if gap < MIN_GAP:
        return None, "uncorrupted"
    p_clean = float(probs[target])
    p_corrupt, _ = run_patched(model, inputs, table, target, noise, noise_tokens)

    masks = position_masks(n_tokens, noise_tokens)
    heads_pos = torch.einsum("pt,lth->plh", masks, att["heads"]) / gap           # [3, L, H]
    writer_pos = torch.einsum("pt,st->ps", masks, att["writer"]) / gap          # [3, S]
    totals = node_totals(att, table)

    check = None
    if args.verify_k:
        ranked = sorted(totals, key=lambda node: -abs(totals[node]))[:args.verify_k]
        actual = [run_patched_logp(model, inputs, table, target, noise, noise_tokens, [node]) - att["logp_corrupt"]
                  for node in ranked]
        check = {"nodes": [label(node) for node in ranked],
                 "estimate": [round(totals[node], 5) for node in ranked],
                 "actual": [round(a, 5) for a in actual]}

    return {
        "id": row.get("id"), "relation": row.get("relation"), "domain": row.get("domain"),
        "prompt": item["text"], "subject": row.get("subject"), "answer": tok.decode([target]),
        "p_clean": p_clean, "p_corrupt": p_corrupt,
        "logp_clean": att["logp_clean"], "logp_corrupt": att["logp_corrupt"], "gap": gap,
        "n_tokens": n_tokens, "corrupt_spans": [list(s) for s in spans],
        "top": [[label(node), round(totals[node] / gap, 4)]
                for node in sorted(totals, key=lambda node: -totals[node])[:15]],
        "check": check,
        # kept in memory for aggregation and the circuit test, not written per fact
        "_heads_pos": heads_pos, "_writer_pos": writer_pos, "_edges": att["edges"] / gap,
        "_totals": {node: v / gap for node, v in totals.items()},
        "_replay": (inputs, target, noise, noise_tokens),
    }, None


# ---------------------------------------------------------------- the circuit

def rank_nodes(facts, table):
    if not facts:
        return []
    mean = {node: float(np.mean([f["_totals"][node] for f in facts])) for node in nodes(table)}
    return sorted(mean, key=lambda node: -mean[node])


def random_circuit(circuit, table, rng):
    """As many random heads and MLPs as `circuit` has."""
    n_heads = sum(1 for node in circuit if node[0] == "head")
    pool_heads = [node for node in nodes(table) if node[0] == "head"]
    pool_mlps = [node for node in nodes(table) if node[0] == "mlp"]
    picked = [pool_heads[i] for i in rng.choice(len(pool_heads), size=n_heads, replace=False)]
    picked += [pool_mlps[i] for i in rng.choice(len(pool_mlps), size=len(circuit) - n_heads, replace=False)]
    return picked


def test_circuit(model, table, ranking, held_out, sizes, rng):
    """Sufficiency, its random baseline and necessity at each size K, on
    facts the ranking was not chosen from."""
    out = []
    total_nodes = len(nodes(table))
    for K in sizes:
        if K > total_nodes:
            continue
        circuit = ranking[:K]
        control = random_circuit(circuit, table, rng)
        rec, rnd, nec = [], [], []
        for f in held_out:
            inputs, target, noise, noise_tokens = f["_replay"]
            lost = f["p_clean"] - f["p_corrupt"]
            if lost <= 1e-6:
                continue
            p_suff, _ = run_patched(model, inputs, table, target, noise, noise_tokens, restore=circuit)
            p_rand, _ = run_patched(model, inputs, table, target, noise, noise_tokens, restore=control)
            _, corrupted = run_patched(model, inputs, table, target, noise, noise_tokens, capture=circuit)
            p_nec, _ = run_patched(model, inputs, table, target, noise, noise_tokens, freeze=corrupted, noisy=False)
            rec.append((p_suff - f["p_corrupt"]) / lost)
            rnd.append((p_rand - f["p_corrupt"]) / lost)
            nec.append((f["p_clean"] - p_nec) / lost)
        if not rec:
            continue
        out.append({
            "k": K, "heads": sum(1 for node in circuit if node[0] == "head"),
            "recovery": round(float(np.mean(rec)), 4), "recovery_ci": _ci(rec),
            "random": round(float(np.mean(rnd)), 4), "random_ci": _ci(rnd),
            "necessity": round(float(np.mean(nec)), 4), "necessity_ci": _ci(nec),
            "n_facts": len(rec),
        })
    return out


def _ci(values, n_boot=1000, seed=0):
    values = np.asarray(values, dtype=float)
    if len(values) < 2:
        return None
    rng = np.random.default_rng(seed)
    means = values[rng.integers(0, len(values), size=(n_boot, len(values)))].mean(axis=1)
    return [round(float(np.percentile(means, 2.5)), 4), round(float(np.percentile(means, 97.5)), 4)]


def traced_peak(model):
    try:
        with open(TRACED_LAYERS) as f:
            entry = json.load(f).get(model)
    except (OSError, json.JSONDecodeError):
        return None
    return entry.get("peak_layer") if entry else None


def aggregate(facts, table, band, model=None, top_heads=20, top_edges=40):
    out = {"n_prompts": len(facts)}
    if not facts:
        return out
    n_layers = table["n_layers"]
    send, recv = senders(table), receivers(table)
    heads_pos = torch.stack([f["_heads_pos"] for f in facts]).mean(0)          # [3, L, H]
    writer_pos = torch.stack([f["_writer_pos"] for f in facts]).mean(0)        # [3, S]
    edges = torch.stack([f["_edges"] for f in facts]).mean(0)                  # [S, R]
    mlp_idx = [i for i, s in enumerate(send) if s[0] == "mlp"]
    attn_idx = [i for i, s in enumerate(send) if s[0] == "attn"]
    mlp_pos = writer_pos[:, mlp_idx]                                            # [3, L]
    attn_pos = writer_pos[:, attn_idx]
    heads_total = heads_pos.sum(0)                                              # [L, H]

    def share(pos, which):
        positive = pos.clamp(min=0)
        return round(float(positive[which].sum() / max(float(positive.sum()), 1e-12)), 4)

    flat = heads_total.flatten()
    order = flat.argsort(descending=True)[:top_heads]
    head_list = []
    for i in order.tolist():
        L, h = divmod(i, table["n_heads"])
        where = heads_pos[:, L, h]
        head_list.append({"layer": L, "head": h, "score": round(float(flat[i]), 4),
                          "position": POSITIONS[int(where.argmax())],
                          "by_position": [round(float(v), 4) for v in where]})
    e_flat = edges.flatten()
    e_order = e_flat.abs().argsort(descending=True)[:top_edges]
    edge_list = []
    for i in e_order.tolist():
        s, r = divmod(i, len(recv))
        edge_list.append({"from": label(send[s]), "to": label(recv[r]), "score": round(float(e_flat[i]), 4)})

    low, high = band
    in_band = [L for L in range(n_layers) if low <= L / n_layers < high]
    mlp_subject = mlp_pos[0]
    checks = [f["check"] for f in facts if f.get("check")]
    rho = [spearman(c["estimate"], c["actual"]) for c in checks]
    rho = [r for r in rho if r is not None]
    est = np.concatenate([c["estimate"] for c in checks]) if checks else np.array([])
    act = np.concatenate([c["actual"] for c in checks]) if checks else np.array([])
    out.update({
        "p_clean": round(float(np.mean([f["p_clean"] for f in facts])), 4),
        "p_corrupt": round(float(np.mean([f["p_corrupt"] for f in facts])), 4),
        "gap": round(float(np.mean([f["gap"] for f in facts])), 4),
        "positions": list(POSITIONS),
        "mlp_by_position": [[round(float(v), 5) for v in row] for row in mlp_pos],
        "attn_by_position": [[round(float(v), 5) for v in row] for row in attn_pos],
        "heads_by_layer": [round(float(v), 5) for v in heads_total.clamp(min=0).sum(1)],
        "top_heads": head_list,
        "top_edges": edge_list,
        "mlp_subject_share": share(mlp_pos, 0),
        "heads_last_share": share(heads_pos.sum(2), 1),
        "peak_layer": int(mlp_subject.argmax()),
        "mlp_subject_in_band": round(float(mlp_subject.clamp(min=0)[in_band].sum()
                                           / max(float(mlp_subject.clamp(min=0).sum()), 1e-12)), 4),
        "band": [low, high], "baseline": round(len(in_band) / n_layers, 4),
        "attribution_check": {
            "n_facts": len(checks),
            "spearman_median": round(float(np.median(rho)), 4) if rho else None,
            "pearson_pooled": round(float(np.corrcoef(est, act)[0, 1]), 4) if len(est) > 2 and est.std() and act.std() else None,
        },
    })
    out["layers"] = [out["peak_layer"]]
    if model:
        out["traced_peak_layer"] = traced_peak(model)
    return out


def verdict(faithfulness):
    """compact: some circuit of at most COMPACT_K components recovers 80% of
    the lost probability on held-out facts, and beats random components;
    distributed: only a larger one does; not_found: none tested does."""
    hits = [row for row in faithfulness if row["recovery"] >= 0.8 and row["recovery"] > row["random"]]
    if not hits:
        return "not_found", None
    k80 = min(row["k"] for row in hits)
    return ("compact" if k80 <= COMPACT_K else "distributed"), k80


# ---------------------------------------------------------------- run

def main(argv=None):
    args = parse_args(argv)
    torch.manual_seed(args.seed)
    rng = np.random.default_rng(args.seed)

    fact_set_info = None
    if args.fact_set:
        fact_set_info, rows = CT.load_fact_set(args.fact_set)
        if len(rows) < MIN_FACTS and not args.allow_thin:
            raise SystemExit(f"fact set {fact_set_info.get('name')} has {len(rows)} facts, below the {MIN_FACTS} "
                             f"minimum; pass --allow_thin 1 to trace it anyway")
    else:
        rows = F.load_rows(args.data_path, args.split, args.max_candidates)
    if not rows:
        raise SystemExit(f"no usable records in {args.fact_set or args.data_path}")

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
    table = C.resolve(model)
    n_layers = table["n_layers"]
    print(f"[{run_name}] {n_layers} layers x {table['n_heads']} heads, format {args.format}", flush=True)

    # Causal tracing's noise level, measured the same way, so the corrupted
    # runs here are the ones its curves were measured on.
    with torch.no_grad():
        embed = model.get_submodule(table["embed"])
        texts = [item["text"] for item in (F.build(row, args.format, tok) for row in rows[:1000]) if item]
        sample_ids = [i for text in texts for i in tok(text, add_special_tokens=False)["input_ids"]]
        embedding_std = float(embed(torch.tensor(sample_ids[:20000], device=device)).float().std())
    args.noise_level = args.noise_scale * embedding_std

    config = {
        "run": run_name, "model": args.model, "model_path": model_path,
        "model_type": model.config.model_type, "n_layers": n_layers,
        "n_heads": table["n_heads"], "parallel": table["parallel"],
        "data_path": args.data_path, "split": args.split, "format": args.format,
        "fact_set": args.fact_set or None,
        "fact_set_name": fact_set_info.get("name") if fact_set_info else None,
        "fact_set_size": len(rows) if fact_set_info else None,
        "dataset_benchmark": args.dataset_benchmark, "dataset_subset": args.dataset_subset,
        "n_prompts": args.n_prompts, "max_candidates": args.max_candidates, "min_prob": args.min_prob,
        "noise_scale": args.noise_scale, "noise_level": args.noise_level, "embedding_std": embedding_std,
        "n_noise_samples": args.n_noise_samples, "verify_k": args.verify_k,
        "circuit_sizes": args.circuit_sizes, "band": list(args.band), "dtype": args.dtype, "seed": args.seed,
    }
    with open(os.path.join(run_dir, "hparams.yaml"), "w") as f:
        yaml.safe_dump(config, f, sort_keys=True)

    started_at, t_start = CT._now(), time.time()
    ckpt_file = open(os.path.join(run_dir, "checkpoints.jsonl"), "w")
    facts, scanned = [], 0
    skipped = {"unknown": 0, "uncorrupted": 0, "unbuildable": 0}
    total = min(args.n_prompts, len(rows))

    def checkpoint(stage="attribution"):
        summary = aggregate(facts, table, args.band)
        row = {
            "step": len(facts), "total_steps": total, "stage": stage, "at": CT._now(),
            "elapsed_sec": round(time.time() - t_start, 2), "scanned": scanned,
            "skipped_unknown": skipped["unknown"], "skipped_uncorrupted": skipped["uncorrupted"],
            "peak_layer": summary.get("peak_layer"),
            "top_head": (summary.get("top_heads") or [{}])[0].get("layer"),
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
        fact, reason = trace_prompt(model, tok, device, row, args, table, rng)
        if fact is None:
            skipped[reason] += 1
            continue
        facts.append(fact)
        if len(facts) % args.checkpoint_every == 0:
            checkpoint()

    # The circuit: chosen on even-position facts, tested on the odd ones.
    chosen_on, held_out = facts[0::2], facts[1::2]
    ranking = rank_nodes(chosen_on, table)
    print(f"[{run_name}] testing circuits of {args.circuit_sizes} on {len(held_out)} held-out facts", flush=True)
    faithfulness = test_circuit(model, table, ranking, held_out, args.circuit_sizes, rng) if held_out else []
    # Heads only: a whole MLP outweighs one head, so the mixed ranking fills
    # with MLPs. This asks whether attention alone carries the fact over.
    head_ranking = [node for node in ranking if node[0] == "head"]
    faithfulness_heads = test_circuit(model, table, head_ranking, held_out, args.circuit_sizes, rng) if held_out else []
    checkpoint("circuit")
    ckpt_file.close()

    found, k80 = verdict(faithfulness)
    found_heads, k80_heads = verdict(faithfulness_heads)
    final_ranking = rank_nodes(facts, table)
    summary = {
        **config,
        **aggregate(facts, table, args.band, args.model),
        "faithfulness": faithfulness, "k80": k80, "verdict": found,
        "faithfulness_heads": faithfulness_heads, "k80_heads": k80_heads, "verdict_heads": found_heads,
        "circuit": [label(node) for node in final_ranking[:COMPACT_K]],
        "circuit_heads": [label(node) for node in final_ranking if node[0] == "head"][:COMPACT_K],
        "circuit_held_out": [label(node) for node in ranking[:COMPACT_K]],
        "thin": len(facts) < MIN_FACTS,
        "scanned": scanned, "skipped": skipped,
        "known_rate": round(len(facts) / scanned, 4) if scanned else None,
        "started_at": started_at, "finished_at": CT._now(),
        "total_sec": round(time.time() - t_start, 2),
        **CT.memory_snapshot(device),
    }
    with open(os.path.join(run_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    heads_total = torch.stack([f["_heads_pos"] for f in facts]).mean(0) if facts else None
    edges = torch.stack([f["_edges"] for f in facts]).mean(0) if facts else None
    with open(os.path.join(run_dir, "circuit.json"), "w") as f:
        json.dump({
            "run": run_name, "summary": summary,
            "heads_by_position": [[[round(float(v), 5) for v in row] for row in grid] for grid in heads_total]
            if heads_total is not None else None,
            "senders": [label(s) for s in senders(table)],
            "receivers": [label(r) for r in receivers(table)],
            "edges": [[round(float(v), 5) for v in row] for row in edges] if edges is not None else None,
            "facts": [{k: v for k, v in fact.items() if not k.startswith("_")} for fact in facts],
        }, f)

    CT.rebuild_manifest(args.out_root)
    print(f"[{run_name}] done: {len(facts)} facts; MLP peak at the subject: layer {summary.get('peak_layer')} "
          f"(traced {summary.get('traced_peak_layer')}); top head "
          f"{(summary.get('top_heads') or [{}])[0]}; circuit {found}, K80 {k80}; heads only {found_heads}, K80 {k80_heads}"
          + (" THIN" if summary["thin"] else ""), flush=True)


if __name__ == "__main__":
    main()
