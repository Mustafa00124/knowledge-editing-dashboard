"""Causal tracing: which layer should ROME/MEMIT/PMET/AlphaEdit edit, for a
given model?

Those methods all take a `layers` hyperparameter naming the site they write
to. That number is not a free choice - it comes from causal tracing (Meng et
al., 2022), which measures where in the network a factual prediction is
actually decided. Every ROME/MEMIT yaml under
experiments/run_experiment/hparams/ that we did not inherit from a published
config is currently guessing: hparams/ROME/qwen3-4b.yaml says so in its own
header ("layers -> [5] kept as upstream's qwen2.5-7b.yaml value ... inherited,
not independently re-validated for Qwen3 specifically"). This script produces
the measurement those files should be quoting.

The method, per prompt:

  1. Clean run. Feed "The Space Needle is in downtown" and record the
     probability of the token the model actually recalls ("Seattle").
  2. Corrupted run. Add Gaussian noise to the *subject* token embeddings
     ("The Space Needle"), which collapses that probability: the model can no
     longer tell which entity is being asked about.
  3. Restored runs. Re-run corrupted, but copy one clean activation back in -
     at one token position, at one layer - and see how much of the lost
     probability returns. A site that restores the answer is a site where the
     fact was stored.

The indirect effect of a site is (restored probability - corrupted
probability), averaged over prompts. The layer with the largest average
indirect effect is the layer to edit.

Three kinds of site are traced, all at the last subject token (the position
ROME identifies as the one carrying the resolved entity):

  hidden - the residual stream after a whole transformer block, restored one
           layer at a time. Shows *where* along the depth the fact lives.
  mlp    - the MLP output, restored over a window of `--window` layers
           centred on each layer. Single-layer MLP restoration barely moves
           the probability because neighbouring layers re-supply the same
           information; the window is how ROME gets past that redundancy,
           and it is this curve's peak that names the layer to edit.
  attn   - the attention output, same windowing. Peaks later than mlp, at the
           site where the answer is read out rather than stored.

Only prompts the model already gets right are traced. A fact the model cannot
recall has no recall to localize, so it would contribute noise to the average.
Records are kept when the model's greedy next token matches the dataset's
true answer with probability >= --min_prob; datasets that carry no true
answer fall back to tracing the model's own confident prediction.

Output layout matches run_experiment's, so the dashboard's existing job
progress, log and manifest machinery work unchanged:

    <out_root>/runs/<run_name>/hparams.yaml      resolved config
    <out_root>/runs/<run_name>/checkpoints.jsonl one line per --checkpoint_every prompts
    <out_root>/runs/<run_name>/summary.json      written once, at the end
    <out_root>/runs/<run_name>/trace.json        full curves, and the token grid if asked
    <out_root>/manifest.json                     rebuilt from every runs/*/summary.json
    <out_root>/traced_layers.json                model -> traced layer, the point of all this

traced_layers.json is what the hparams read when we wire this in. It is
rebuilt from the summaries rather than appended to, so re-tracing a model
replaces its entry and archiving a trace run removes it.
"""
import argparse
import json
import os
import time
from datetime import datetime

import numpy as np
import psutil
import torch
import yaml
from transformers import AutoModelForCausalLM, AutoTokenizer

EXP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(EXP_DIR))
DEFAULT_OUT_ROOT = f"{PROJECT_ROOT}/results/hyperparameters/edit_layers/causal_tracing"
DEFAULT_DATA_PATH = f"{PROJECT_ROOT}/datasets/KnowEdit/benchmark/wiki_counterfact/test_cf.json"
ROME_HPARAMS_DIR = f"{PROJECT_ROOT}/experiments/run_experiment/hparams/ROME"

MODEL_PATHS = {
    "qwen3-4b": f"{PROJECT_ROOT}/models/Qwen3-4B",
    "mistral-7b-v0.1": f"{PROJECT_ROOT}/models/Mistral-7B-v0.1",
    "gpt-j-6b": f"{PROJECT_ROOT}/models/GPT-J-6B",
    "olmo-2-7b": f"{PROJECT_ROOT}/models/OLMo-2-7B",
    "gpt-neox-20b": f"{PROJECT_ROOT}/models/GPT-NeoX-20B",
    "gpt-oss-20b": f"{PROJECT_ROOT}/models/GPT-OSS-20B",
}

# Where the three traceable sites live, per HF architecture. Keyed on
# config.model_type so a newly downloaded model of a known family needs no
# change here. Every template is checked against the loaded model before
# tracing starts, so a wrong guess fails in seconds rather than an hour in.
ARCHS = {
    "gptj": {
        "embed": "transformer.wte",
        "layer": "transformer.h.{}",
        "mlp": "transformer.h.{}.mlp",
        "attn": "transformer.h.{}.attn",
    },
    "gpt_neox": {
        "embed": "gpt_neox.embed_in",
        "layer": "gpt_neox.layers.{}",
        "mlp": "gpt_neox.layers.{}.mlp",
        "attn": "gpt_neox.layers.{}.attention",
    },
}
# llama-shaped: everything else we have downloaded.
for _model_type in ("llama", "mistral", "qwen2", "qwen3", "olmo2", "gpt_oss"):
    ARCHS[_model_type] = {
        "embed": "model.embed_tokens",
        "layer": "model.layers.{}",
        "mlp": "model.layers.{}.mlp",
        "attn": "model.layers.{}.self_attn",
    }

KINDS = ("hidden", "mlp", "attn")


def parse_args():
    p = argparse.ArgumentParser(description="Causal tracing for edit-layer selection")
    p.add_argument("--model", required=True, choices=sorted(MODEL_PATHS))
    p.add_argument("--data_path", default=DEFAULT_DATA_PATH)
    p.add_argument("--dataset_benchmark", default=None, help="human label, passed by the dashboard")
    p.add_argument("--dataset_subset", default=None, help="human label, passed by the dashboard")
    p.add_argument("--n_prompts", type=int, default=200, help="prompts to trace, after the known-fact filter")
    p.add_argument("--max_candidates", type=int, default=2000, help="records to scan looking for those prompts")
    p.add_argument("--min_prob", type=float, default=0.1,
                   help="skip a record unless the model recalls the answer with at least this probability")
    p.add_argument("--noise_scale", type=float, default=3.0,
                   help="subject-embedding noise, in units of the embedding standard deviation (ROME uses 3)")
    p.add_argument("--window", type=int, default=10, help="layers restored together for the mlp/attn curves")
    p.add_argument("--effect", default="mlp", choices=KINDS,
                   help="which curve names the edit layer written to traced_layers.json")
    p.add_argument("--n_noise_samples", type=int, default=10, help="corrupted runs averaged per measurement")
    p.add_argument("--token_grid", type=int, default=0,
                   help="also trace every token position, not just the last subject token, for this many prompts "
                        "(0 = off). Produces the token x layer heatmap, and costs prompt_length times more per prompt.")
    p.add_argument("--dtype", default="bfloat16", choices=["bfloat16", "float16", "float32"])
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--checkpoint_every", type=int, default=10, help="prompts between checkpoint lines")
    p.add_argument("--run_name", default=None)
    p.add_argument("--out_root", default=DEFAULT_OUT_ROOT)
    return p.parse_args()


def _now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def memory_snapshot(device):
    """Same fields run_experiment records, so both experiments' checkpoints
    read the same way in the dashboard."""
    snapshot = {"host_rss_mb": round(psutil.Process().memory_info().rss / 1e6, 1)}
    if torch.cuda.is_available():
        snapshot.update({
            "gpu_mem_alloc_mb": round(torch.cuda.memory_allocated(device) / 1e6, 1),
            "gpu_mem_peak_mb": round(torch.cuda.max_memory_allocated(device) / 1e6, 1),
            "gpu_mem_total_mb": round(torch.cuda.get_device_properties(device).total_memory / 1e6, 1),
        })
    return snapshot


# ---------------------------------------------------------------- data

def _true_answer(record):
    """The answer the *model* is expected to already know.

    Not target_new: that is the counterfactual an edit would install, which
    the model by construction does not believe. Tracing needs the fact it
    does.
    """
    value = record.get("ground_truth")
    if isinstance(value, list):
        value = next((v for v in value if isinstance(v, str) and v.strip()), None)
    if isinstance(value, str) and value.strip():
        return value.strip()
    # ZsRE carries the original answer inside "cond": "Geometridae >> Noctuidae || ..."
    cond = record.get("cond")
    if isinstance(cond, str) and ">>" in cond:
        return cond.split(">>")[0].strip() or None
    return None


def load_prompts(data_path, limit):
    """(prompt, subject, answer-or-None) triples from a KnowEdit-shaped file.

    Deliberately not run_experiment's eval_utils.load_requests: that builds
    EasyEdit edit requests, whose ground_truth is None for the recent-shaped
    files, and pulls in the whole easyeditor package to do it. Tracing needs
    three plain strings.
    """
    with open(data_path) as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = data.get("data", [])
    rows = []
    for record in data[:limit]:
        if not isinstance(record, dict):
            continue
        prompt, subject = record.get("prompt"), record.get("subject")
        if not prompt or not subject or subject not in prompt:
            continue  # the noise has to land on the subject, so it has to be locatable
        rows.append({"prompt": prompt, "subject": subject, "answer": _true_answer(record)})
    return rows


def subject_token_range(tok, prompt, subject):
    """Token index range [start, end) covering the subject inside the prompt."""
    start_char = prompt.index(subject)
    end_char = start_char + len(subject)
    encoded = tok(prompt, return_offsets_mapping=True)
    spans = encoded["offset_mapping"]
    indices = [i for i, (a, b) in enumerate(spans) if a < end_char and b > start_char]
    if not indices:
        return None
    return indices[0], indices[-1] + 1


# ---------------------------------------------------------------- tracing

class Patch:
    """Forward hooks implementing one traced run.

    Row 0 of the batch is the clean run and is never touched. Rows 1.. are
    corrupted: noise is added to their subject embeddings, and then whichever
    sites are being restored have row 0's activation copied back over them.
    Everything is done in place on the module's own output, which keeps this
    agnostic to whether a module returns a tensor or a tuple.
    """

    def __init__(self, model, embed_name, noise=None, subject_range=None, restore=()):
        self.model = model
        self.handles = []
        self.noise = noise
        self.subject_range = subject_range
        self.embed_name = embed_name
        self.restore = {}
        for token_index, module_name in restore:
            self.restore.setdefault(module_name, []).append(token_index)

    def __enter__(self):
        names = set(self.restore)
        if self.noise is not None:
            names.add(self.embed_name)
        for name in names:
            self.handles.append(self.model.get_submodule(name).register_forward_hook(self._hook(name)))
        return self

    def __exit__(self, *exc):
        for handle in self.handles:
            handle.remove()
        self.handles = []
        return False

    def _hook(self, name):
        def hook(module, inputs, output):
            hidden = output[0] if isinstance(output, tuple) else output
            if name == self.embed_name and self.noise is not None:
                start, end = self.subject_range
                hidden[1:, start:end] += self.noise.to(hidden.device, hidden.dtype)
            for token_index in self.restore.get(name, []):
                hidden[1:, token_index] = hidden[0, token_index]
            return output
        return hook


def traced_prob(model, inputs, answer_id, embed_name, noise, subject_range, restore=()):
    """Mean probability of `answer_id` across the corrupted rows."""
    with torch.no_grad(), Patch(model, embed_name, noise, subject_range, restore):
        logits = model(**inputs).logits
    # softmax in fp32: the differences being measured are smaller than
    # bfloat16 resolves, even though the forward pass itself is fine in it.
    probs = torch.softmax(logits[1:, -1, :].float(), dim=-1)
    return probs[:, answer_id].mean().item()


def window_sites(kind, layer, n_layers, window, token_index, templates):
    """The (token, module) sites restored together for one point on a curve."""
    if kind == "hidden":
        return [(token_index, templates["layer"].format(layer))]
    low = max(0, layer - window // 2)
    high = min(n_layers, layer - (-window // 2))
    return [(token_index, templates[kind].format(L)) for L in range(low, high)]


def trace_prompt(model, tok, device, row, args, templates, n_layers, rng):
    """One prompt: clean, corrupted, and the restored curves.

    Returns None when the model does not recall this fact confidently enough
    to be worth tracing.
    """
    prompt, subject = row["prompt"], row["subject"]
    span = subject_token_range(tok, prompt, subject)
    if span is None:
        return None

    batch = 1 + args.n_noise_samples
    encoded = tok([prompt] * batch, return_tensors="pt").to(device)
    inputs = {k: v for k, v in encoded.items() if k in ("input_ids", "attention_mask")}

    with torch.no_grad():
        clean_logits = model(**inputs).logits[0, -1, :].float()
    clean_probs = torch.softmax(clean_logits, dim=-1)
    top_id = int(clean_probs.argmax())
    top_prob = float(clean_probs[top_id])

    if row["answer"]:
        # A dataset answer only counts when the model actually produces it:
        # both spacings, since tokenizers disagree about the leading space.
        wanted = {tok(variant, add_special_tokens=False)["input_ids"][0]
                  for variant in (" " + row["answer"], row["answer"])
                  if tok(variant, add_special_tokens=False)["input_ids"]}
        if top_id not in wanted:
            return None
    if top_prob < args.min_prob:
        return None

    n_tokens = inputs["input_ids"].shape[1]
    embed_name = templates["embed"]
    noise = torch.from_numpy(
        args.noise_level * rng.standard_normal((args.n_noise_samples, span[1] - span[0], model.config.hidden_size))
    ).float()

    corrupted = traced_prob(model, inputs, top_id, embed_name, noise, span)

    last_subject = span[1] - 1
    curves = {}
    for kind in KINDS:
        curves[kind] = [
            traced_prob(model, inputs, top_id, embed_name, noise, span,
                        window_sites(kind, layer, n_layers, args.window, last_subject, templates))
            for layer in range(n_layers)
        ]

    grid = None
    if args.token_grid:
        grid = {kind: [[
            traced_prob(model, inputs, top_id, embed_name, noise, span,
                        window_sites(kind, layer, n_layers, args.window, token_index, templates))
            for layer in range(n_layers)] for token_index in range(n_tokens)]
            for kind in KINDS}

    return {
        "prompt": prompt,
        "subject": subject,
        "answer": tok.decode([top_id]),
        "p_clean": top_prob,
        "p_corrupt": corrupted,
        "n_tokens": n_tokens,
        "subject_range": list(span),
        "curves": curves,
        "grid": grid,
    }


# ---------------------------------------------------------------- aggregation

def token_bucket(token_index, span, n_tokens):
    """ROME's six positions, so grids over prompts of different lengths can be
    averaged: prompts share these roles, not absolute indices."""
    start, end = span
    if token_index == start:
        return 0
    if start < token_index < end - 1:
        return 1
    if token_index == end - 1:
        return 2
    if token_index == n_tokens - 1:
        return 5
    if token_index == end:
        return 3
    return 4


BUCKET_LABELS = [
    "first subject token", "middle subject tokens", "last subject token",
    "first token after subject", "further tokens", "last token",
]


def aggregate(traces, n_layers, effect):
    """Mean indirect effect per layer, and the peak of the chosen curve."""
    out = {"n_prompts": len(traces)}
    if not traces:
        return out
    out["p_clean"] = float(np.mean([t["p_clean"] for t in traces]))
    out["p_corrupt"] = float(np.mean([t["p_corrupt"] for t in traces]))
    for kind in KINDS:
        # Indirect effect, not raw probability: how much of what the noise
        # destroyed this site puts back.
        aie = np.mean([np.array(t["curves"][kind]) - t["p_corrupt"] for t in traces], axis=0)
        out[f"aie_{kind}"] = [round(float(v), 6) for v in aie]
        out[f"peak_layer_{kind}"] = int(np.argmax(aie))
        out[f"peak_aie_{kind}"] = round(float(np.max(aie)), 6)
    out["effect"] = effect
    out["peak_layer"] = out[f"peak_layer_{effect}"]
    out["peak_aie"] = out[f"peak_aie_{effect}"]
    out["layers"] = [out["peak_layer"]]
    return out


def aggregate_grid(traces, n_layers):
    graded = [t for t in traces if t.get("grid")]
    if not graded:
        return None
    grids = {}
    for kind in KINDS:
        total = np.zeros((len(BUCKET_LABELS), n_layers))
        count = np.zeros((len(BUCKET_LABELS), 1))
        for trace in graded:
            for token_index, row in enumerate(trace["grid"][kind]):
                bucket = token_bucket(token_index, trace["subject_range"], trace["n_tokens"])
                total[bucket] += np.array(row) - trace["p_corrupt"]
                count[bucket] += 1
        with np.errstate(invalid="ignore"):
            mean = np.divide(total, count, out=np.full_like(total, np.nan), where=count > 0)
        grids[kind] = [[None if np.isnan(v) else round(float(v), 6) for v in row] for row in mean]
    return {"buckets": BUCKET_LABELS, "n_prompts": len(graded), "grids": grids}


# ---------------------------------------------------------------- output

def rebuild_manifest(out_root):
    """Same full-rescan contract as run_experiment._rebuild_manifest."""
    runs_dir = os.path.join(out_root, "runs")
    manifest = []
    for name in sorted(os.listdir(runs_dir)):
        path = os.path.join(runs_dir, name, "summary.json")
        if os.path.exists(path):
            with open(path) as f:
                manifest.append(json.load(f))
    with open(os.path.join(out_root, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    return manifest


def rebuild_traced_layers(out_root, manifest):
    """model -> the layer its most recent finished trace chose.

    Derived from the summaries, never appended to, so re-tracing a model
    replaces its entry and archiving a trace run drops it - the same rule the
    results manifest follows.
    """
    latest = {}
    for row in manifest:
        model = row.get("model")
        if not model or row.get("peak_layer") is None:
            continue
        current = latest.get(model)
        if current is None or (row.get("finished_at") or "") >= (current.get("finished_at") or ""):
            latest[model] = row
    mapping = {
        model: {
            "layers": row["layers"],
            "peak_layer": row["peak_layer"],
            "peak_aie": row["peak_aie"],
            "effect": row["effect"],
            "window": row["window"],
            "n_prompts": row["n_prompts"],
            "n_layers": row["n_layers"],
            "dataset": " / ".join(x for x in (row.get("dataset_benchmark"), row.get("dataset_subset")) if x),
            "run": row["run"],
            "traced_at": row.get("finished_at"),
        }
        for model, row in sorted(latest.items())
    }
    with open(os.path.join(out_root, "traced_layers.json"), "w") as f:
        json.dump(mapping, f, indent=2)
    return mapping


def resolve_modules(model, model_key):
    """Module name templates for this architecture, checked against the model.

    Prefers the ROME hparams already in this project when one exists for the
    model: those templates are what the edit will actually write through, so
    tracing has to measure the same modules, not a lookalike.
    """
    model_type = getattr(model.config, "model_type", None)
    if model_type not in ARCHS:
        raise SystemExit(
            f"no module templates for model_type {model_type!r}. Add it to ARCHS in {__file__}."
        )
    templates = dict(ARCHS[model_type])
    rome_path = os.path.join(ROME_HPARAMS_DIR, f"{model_key}.yaml")
    source = "architecture table"
    if os.path.exists(rome_path):
        with open(rome_path) as f:
            rome = yaml.safe_load(f) or {}
        for key, field in (("layer", "layer_module_tmp"), ("mlp", "mlp_module_tmp"), ("attn", "attn_module_tmp")):
            if rome.get(field):
                templates[key] = rome[field]
        source = f"hparams/ROME/{model_key}.yaml"

    for key, template in templates.items():
        name = template.format(0) if "{}" in template else template
        try:
            model.get_submodule(name)
        except AttributeError as exc:
            raise SystemExit(f"module {name!r} ({key}, from {source}) not found on this model: {exc}")
    return templates, source


def main():
    args = parse_args()
    torch.manual_seed(args.seed)
    rng = np.random.default_rng(args.seed)

    run_name = args.run_name or f"{args.model}_n{args.n_prompts}"
    run_dir = os.path.join(args.out_root, "runs", run_name)
    os.makedirs(run_dir, exist_ok=True)

    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    model_path = MODEL_PATHS[args.model]
    print(f"[{run_name}] loading {model_path}", flush=True)
    tok = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(model_path, dtype=getattr(torch, args.dtype)).to(device)
    model.eval()

    templates, template_source = resolve_modules(model, args.model)
    n_layers = getattr(model.config, "num_hidden_layers", None) or model.config.n_layer
    print(f"[{run_name}] {n_layers} layers, modules from {template_source}", flush=True)

    rows = load_prompts(args.data_path, args.max_candidates)
    if not rows:
        raise SystemExit(f"no usable prompt/subject records in {args.data_path}")

    # ROME's noise level: 3x the standard deviation of this model's own token
    # embeddings, measured over the candidate prompts rather than the whole
    # vocabulary, so it is scaled to the tokens actually being corrupted.
    with torch.no_grad():
        embed = model.get_submodule(templates["embed"])
        sample_ids = [i for row in rows[:1000] for i in tok(row["prompt"], add_special_tokens=False)["input_ids"]]
        embeddings = embed(torch.tensor(sample_ids[:20000], device=device))
        embedding_std = float(embeddings.float().std())
    args.noise_level = args.noise_scale * embedding_std
    print(f"[{run_name}] embedding std {embedding_std:.4f}, noise {args.noise_level:.4f}", flush=True)

    config = {
        "run": run_name, "model": args.model, "model_path": model_path,
        "model_type": model.config.model_type, "n_layers": n_layers,
        "modules": templates, "module_source": template_source,
        "data_path": args.data_path,
        "dataset_benchmark": args.dataset_benchmark, "dataset_subset": args.dataset_subset,
        "n_prompts": args.n_prompts, "max_candidates": args.max_candidates,
        "min_prob": args.min_prob, "noise_scale": args.noise_scale,
        "noise_level": args.noise_level, "embedding_std": embedding_std,
        "window": args.window, "effect": args.effect,
        "n_noise_samples": args.n_noise_samples, "token_grid": args.token_grid,
        "dtype": args.dtype, "seed": args.seed,
    }
    with open(os.path.join(run_dir, "hparams.yaml"), "w") as f:
        yaml.safe_dump(config, f, sort_keys=True)

    started_at, t_start = _now(), time.time()
    ckpt_file = open(os.path.join(run_dir, "checkpoints.jsonl"), "w")
    traces, scanned, skipped = [], 0, 0

    def checkpoint():
        summary = aggregate(traces, n_layers, args.effect)
        row = {
            "step": len(traces), "at": _now(), "elapsed_sec": round(time.time() - t_start, 2),
            "scanned": scanned, "skipped_unknown": skipped,
            "peak_layer": summary.get("peak_layer"), "peak_aie": summary.get("peak_aie"),
            "p_clean": summary.get("p_clean"), "p_corrupt": summary.get("p_corrupt"),
            **memory_snapshot(device),
        }
        ckpt_file.write(json.dumps(row) + "\n")
        ckpt_file.flush()
        print(f"[{run_name}] " + " ".join(f"{k}={v}" for k, v in row.items()), flush=True)

    checkpoint()
    for row in rows:
        if len(traces) >= args.n_prompts:
            break
        scanned += 1
        # The grid is only for the heatmap, and it is the expensive part, so
        # only the first --token_grid prompts pay for it.
        args_for_row = argparse.Namespace(**vars(args))
        args_for_row.token_grid = 1 if len(traces) < args.token_grid else 0
        trace = trace_prompt(model, tok, device, row, args_for_row, templates, n_layers, rng)
        if trace is None:
            skipped += 1
            continue
        traces.append(trace)
        if len(traces) % args.checkpoint_every == 0:
            checkpoint()

    if len(traces) % args.checkpoint_every:
        checkpoint()
    ckpt_file.close()

    summary = {
        **{k: v for k, v in config.items() if k not in ("modules",)},
        **aggregate(traces, n_layers, args.effect),
        "scanned": scanned, "skipped_unknown": skipped,
        "known_rate": round(len(traces) / scanned, 4) if scanned else None,
        "started_at": started_at, "finished_at": _now(),
        "total_sec": round(time.time() - t_start, 2),
        **memory_snapshot(device),
    }
    with open(os.path.join(run_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    with open(os.path.join(run_dir, "trace.json"), "w") as f:
        json.dump({
            "run": run_name,
            "summary": summary,
            "token_grid": aggregate_grid(traces, n_layers),
            "prompts": [{k: t[k] for k in ("prompt", "subject", "answer", "p_clean", "p_corrupt")} for t in traces],
        }, f, indent=2)

    manifest = rebuild_manifest(args.out_root)
    mapping = rebuild_traced_layers(args.out_root, manifest)
    print(f"[{run_name}] done: {args.model} -> layer {summary.get('peak_layer')} "
          f"(AIE {summary.get('peak_aie')}, {len(traces)} prompts)", flush=True)
    print(f"[{run_name}] traced_layers.json now covers {sorted(mapping)}", flush=True)


if __name__ == "__main__":
    main()
