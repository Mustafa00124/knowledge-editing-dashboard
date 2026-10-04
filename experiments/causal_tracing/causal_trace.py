"""Causal tracing: where in a given model is a fact recalled, and how reliably
is that in early-to-mid MLP layers?

A property of the model alone: no editing method is involved, and one trace
per model serves every method. ROME/MEMIT/PMET/AlphaEdit all take a `layers`
hyperparameter naming the site they write to, and causal tracing (Meng et
al., 2022) is where that number is supposed to start from. Which layer each
method should edit is a separate, per-method question (the Edit layers
sweeps), since a traced peak need not be the best edit site (Hase et al.,
2023). So besides a peak layer, every trace reports how reliable the
"facts live in early-to-mid MLPs" picture is for this model (see
reliability()).

The method, per fact:

  1. Clean run. Feed "The Space Needle is in downtown" and record the
     probability of the answer token the model gives ("Seattle").
  2. Corrupted run. Add Gaussian noise to the input embeddings of the
     corrupted span (the subject, or for multiple choice the question, or for
     a riddle the clue it added), which collapses that probability.
  3. Restored runs. Re-run corrupted, but copy one clean activation back in -
     at the last corrupted token, at one layer - and see how much of the lost
     probability returns.

The indirect effect (AIE) of a site is (restored probability - corrupted
probability), averaged over facts. Three kinds of site:

  hidden - the residual stream after a whole block, one layer at a time.
  mlp    - the MLP output, over a window of `--window` layers centred on each
           layer (neighbouring layers re-supply the same information, so one
           layer alone barely moves the probability; --window 1 shows that).
  attn   - the attention output, same windowing.

--sever adds ROME's necessity test: restore the hidden state at layer L as
above, but hold every later layer's MLP (or attention) output at the token
to its corrupted value. If recovery collapses, those MLPs are needed to
carry the fact on, not just correlated with it.

Only facts the model already gives are traced: its most likely next token,
setting aside whitespace-only tokens (a newline is not an answer), must be
the start of an accepted answer with probability >= --min_prob, and that
answer token is what gets traced.

Which facts and how they are written: --fact_set traces a fixed list from
experiments/fact_selection/select_facts.py (the same facts for every model
in a group), else the --split records of --data_path (nontest = dev + demo:
the trace that informs edit layers never sees a test record). --format
writes each fact as a completion, a question, through the chat template,
as multiple choice or as a riddle; formats.py has the loaders and formats.
A fact set below MIN_FACTS facts is refused unless --allow_thin.

Output layout matches run_experiment's, so the dashboard's existing job
progress, log and manifest machinery work unchanged:

    <out_root>/runs/<run_name>/hparams.yaml      resolved config
    <out_root>/runs/<run_name>/checkpoints.jsonl one line per --checkpoint_every facts
    <out_root>/runs/<run_name>/summary.json      written once, at the end
    <out_root>/runs/<run_name>/trace.json        mean curves, every fact's own curves,
                                                 and the token grid if asked
    <out_root>/manifest.json                     rebuilt from every runs/*/summary.json
    <out_root>/traced_layers.json                model -> traced layer

traced_layers.json is what the Edit layers sweeps read to suggest layers
around each model's peak. Only the plain-completion, window-10 trace of a
model feeds it (the form edits are written in); the other formats and
windows are comparisons. It is rebuilt from the summaries rather than
appended to, so re-tracing a model replaces its entry and archiving a trace
run removes it.
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime

import numpy as np
import psutil
import torch
import yaml
from transformers import AutoModelForCausalLM, AutoTokenizer

import formats as F
import knowledge as KN  # noqa: E402  (which facts a model knows, and their lead-ins)

EXP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(EXP_DIR))
sys.path.append(os.path.join(PROJECT_ROOT, "experiments"))
import launch_guard  # noqa: E402  (refuses untracked runs into results/)
DEFAULT_OUT_ROOT = f"{PROJECT_ROOT}/results/investigations/causal_tracing"
DEFAULT_DATA_PATH = f"{PROJECT_ROOT}/datasets/MQuAKE/datasets/MQuAKE-CF-3k-v2.json"
ROME_HPARAMS_DIR = f"{PROJECT_ROOT}/experiments/run_experiment/hparams/ROME"
SPLIT_CHOICES = F.SPLIT_CHOICES

# Fewer facts than this and a peak or a reliability share is noise. A fact
# set below it is refused (--allow_thin overrides); a trace that ends below
# it is flagged "thin".
MIN_FACTS = 50
# "Early-to-mid" as a share of depth, so 32- and 36-layer models compare.
DEFAULT_BAND = (0.0, 0.5)

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
for _model_type in ("llama", "mistral", "qwen2", "qwen3", "olmo2", "olmo3", "gpt_oss"):
    ARCHS[_model_type] = {
        "embed": "model.embed_tokens",
        "layer": "model.layers.{}",
        "mlp": "model.layers.{}.mlp",
        "attn": "model.layers.{}.self_attn",
    }

KINDS = ("hidden", "mlp", "attn")
SEVER_KINDS = ("sever_mlp", "sever_attn")


def parse_args():
    p = argparse.ArgumentParser(description="Causal tracing: where a model recalls facts, and how reliably")
    p.add_argument("--model", required=True, choices=sorted(MODEL_PATHS))
    p.add_argument("--data_path", default=DEFAULT_DATA_PATH)
    p.add_argument("--dataset_benchmark", default=None, help="human label, passed by the dashboard")
    p.add_argument("--dataset_subset", default=None, help="human label, passed by the dashboard")
    p.add_argument("--split", default="nontest", choices=SPLIT_CHOICES,
                   help="records of --data_path to draw from: nontest = dev + demo, never test")
    p.add_argument("--fact_set", default="",
                   help="trace this fixed fact list (select_facts.py) instead of scanning --data_path")
    p.add_argument("--allow_thin", type=int, default=0, help=f"1 traces a fact set below {MIN_FACTS} facts")
    p.add_argument("--format", default="completion", choices=sorted(F.FORMATS),
                   help="how each fact is written as a prompt (formats.FORMATS)")
    p.add_argument("--n_prompts", type=int, default=200, help="facts to trace, after the known-fact filter")
    p.add_argument("--max_candidates", type=int, default=2000, help="records to scan looking for those facts")
    p.add_argument("--min_prob", type=float, default=0.1,
                   help="skip a fact unless the model gives the answer with at least this probability")
    p.add_argument("--noise_scale", type=float, default=3.0,
                   help="input-embedding noise, in units of the embedding standard deviation (ROME uses 3)")
    p.add_argument("--window", type=int, default=10, help="layers restored together for the mlp/attn curves")
    p.add_argument("--effect", default="mlp", choices=KINDS,
                   help="which curve names the layer written to traced_layers.json")
    p.add_argument("--sever", type=int, default=0,
                   help="1 adds the severing test: hidden-state restoration with later MLPs/attention frozen")
    p.add_argument("--band", default=f"{DEFAULT_BAND[0]},{DEFAULT_BAND[1]}",
                   help="early-to-mid band as a share of depth, 'low,high' (layer/n_layers in [low, high))")
    p.add_argument("--n_noise_samples", type=int, default=10, help="corrupted runs averaged per measurement")
    p.add_argument("--token_grid", type=int, default=0,
                   help="also trace every token position, not just the last corrupted token, for this many facts "
                        "(0 = off). Produces the token x layer heatmap, and costs prompt_length times more per fact.")
    p.add_argument("--dtype", default="bfloat16", choices=["bfloat16", "float16", "float32"])
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--checkpoint_every", type=int, default=10, help="facts between checkpoint lines")
    p.add_argument("--run_name", default=None)
    p.add_argument("--out_root", default=DEFAULT_OUT_ROOT)
    launch_guard.add_argument(p)
    KN.add_arguments(p)
    args = p.parse_args()
    low, high = (float(x) for x in args.band.split(","))
    args.band = (low, high)
    return args


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


# ---------------------------------------------------------------- facts

def load_fact_set(path):
    with open(path) as f:
        fact_set = json.load(f)
    return fact_set, [F.normalize(row) for row in fact_set["facts"]]


def answer_ids(tok, answers):
    """First-token ids that count as giving one of `answers`: both spacings,
    since tokenizers disagree about the leading space."""
    ids = set()
    for answer in answers:
        for variant in (" " + answer, answer):
            encoded = tok(variant, add_special_tokens=False)["input_ids"]
            if encoded:
                ids.add(encoded[0])
    return ids


_WHITESPACE_IDS = {}


def whitespace_ids(tok):
    """Token ids that decode to nothing but whitespace (newlines, spaces).

    Some models (Olmo-3) read "The official language of Japan is" as a
    finished line and put their top probability on a newline, with the
    answer close behind. Such a token says nothing about the fact, so it is
    skipped when asking which answer the model would give."""
    key = id(tok)
    if key not in _WHITESPACE_IDS:
        texts = tok.batch_decode([[i] for i in range(len(tok))])
        _WHITESPACE_IDS[key] = torch.tensor([i for i, t in enumerate(texts) if t and not t.strip()], dtype=torch.long)
    return _WHITESPACE_IDS[key]


def recall_target(tok, probs, answers, min_prob):
    """The token to trace if the model knows this fact, else None.

    The model's most likely next token once whitespace-only tokens are set
    aside. With dataset answers it must start one of them; either way its own
    probability (not renormalised) must reach min_prob."""
    masked = probs.clone()
    masked[whitespace_ids(tok).to(masked.device)] = -1.0
    target = int(masked.argmax())
    if answers and target not in answer_ids(tok, answers):
        return None
    return target if float(probs[target]) >= min_prob else None


# ---------------------------------------------------------------- tracing

class Patch:
    """Forward hooks implementing one traced run.

    Row 0 of the batch is the clean run and is never touched. Rows 1.. are
    corrupted: noise is added to their embeddings at `noise_tokens`, then
    whichever sites are being restored get row 0's activation copied back,
    `freeze` holds sites at given (already recorded) corrupted values, and
    `capture` records sites' corrupted values for a later freeze. All in
    place on the module's own output, so it does not matter whether a module
    returns a tensor or a tuple.
    """

    def __init__(self, model, embed_name, noise=None, noise_tokens=(), restore=(), freeze=None, capture=None):
        self.model = model
        self.handles = []
        self.noise = noise
        self.noise_tokens = list(noise_tokens)
        self.embed_name = embed_name
        self.restore = {}
        for token_index, module_name in restore:
            self.restore.setdefault(module_name, []).append(token_index)
        self.freeze = freeze or {}     # module -> (token, tensor[n_samples, hidden])
        self.capture = capture         # module -> token; filled with module -> tensor
        self.captured = {}

    def __enter__(self):
        names = set(self.restore) | set(self.freeze) | set(self.capture or {})
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
                hidden[1:, self.noise_tokens] += self.noise.to(hidden.device, hidden.dtype)
            for token_index in self.restore.get(name, []):
                hidden[1:, token_index] = hidden[0, token_index]
            if name in self.freeze:
                token_index, value = self.freeze[name]
                hidden[1:, token_index] = value.to(hidden.device, hidden.dtype)
            if self.capture and name in self.capture:
                self.captured[name] = hidden[1:, self.capture[name]].detach().clone()
            return output
        return hook


def traced_prob(model, inputs, answer_id, embed_name, noise, noise_tokens, restore=(), freeze=None):
    """Mean probability of `answer_id` across the corrupted rows."""
    with torch.no_grad(), Patch(model, embed_name, noise, noise_tokens, restore, freeze):
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


def sever_curves(model, inputs, target, embed_name, noise, noise_tokens, token, templates, n_layers):
    """ROME's severing test. For each layer L: restore the hidden state at L,
    but hold the MLP (or attention) output of every later layer at the token
    to its corrupted value. If the restored information needs those modules
    to reach the answer, recovery collapses."""
    out = {}
    for sever, kind in (("sever_mlp", "mlp"), ("sever_attn", "attn")):
        names = [templates[kind].format(L) for L in range(n_layers)]
        with torch.no_grad(), Patch(model, embed_name, noise, noise_tokens,
                                    capture={name: token for name in names}) as patch:
            model(**inputs)
        corrupted = patch.captured
        out[sever] = [
            traced_prob(model, inputs, target, embed_name, noise, noise_tokens,
                        [(token, templates["layer"].format(L))],
                        freeze={names[k]: (token, corrupted[names[k]]) for k in range(L + 1, n_layers)})
            for L in range(n_layers)
        ]
    return out


def trace_prompt(model, tok, device, row, args, templates, n_layers, rng):
    """One fact: clean, corrupted, and the restored curves.

    Returns None when the fact cannot be written in this format, or when the
    model does not give its answer confidently enough to be worth tracing.
    """
    item = KN.prepare(model, tok, device, row, F.build(row, args.format, tok), args)
    if item is None:
        return None
    spans = F.token_spans(tok, item)
    if not spans:
        return None

    batch = 1 + args.n_noise_samples
    encoded = F.encode(tok, item, return_tensors="pt")
    inputs = {k: encoded[k].repeat(batch, 1).to(device) for k in ("input_ids", "attention_mask")}

    with torch.no_grad():
        clean_logits = model(**inputs).logits[0, -1, :].float()
    clean_probs = torch.softmax(clean_logits, dim=-1)
    # The traced probability is the answer's, not a newline's.
    target = recall_target(tok, clean_probs, item["answers"], args.min_prob)
    if target is None:
        return None
    p_clean = float(clean_probs[target])

    n_tokens = inputs["input_ids"].shape[1]
    embed_name = templates["embed"]
    noise_tokens = sorted({i for start, end in spans for i in range(start, end)})
    noise = torch.from_numpy(
        args.noise_level * rng.standard_normal((args.n_noise_samples, len(noise_tokens), model.config.hidden_size))
    ).float()

    corrupted = traced_prob(model, inputs, target, embed_name, noise, noise_tokens)

    # The last corrupted token: ROME's "last subject token", where the
    # resolved entity (or clue, or question) is carried forward.
    token = spans[-1][1] - 1
    curves = {}
    for kind in KINDS:
        curves[kind] = [
            traced_prob(model, inputs, target, embed_name, noise, noise_tokens,
                        window_sites(kind, layer, n_layers, args.window, token, templates))
            for layer in range(n_layers)
        ]
    if args.sever:
        curves.update(sever_curves(model, inputs, target, embed_name, noise, noise_tokens, token, templates, n_layers))

    grid = None
    if args.token_grid:
        grid = {kind: [[
            traced_prob(model, inputs, target, embed_name, noise, noise_tokens,
                        window_sites(kind, layer, n_layers, args.window, token_index, templates))
            for layer in range(n_layers)] for token_index in range(n_tokens)]
            for kind in KINDS}

    return {
        "id": row.get("id"),
        "relation": row.get("relation"),
        "domain": row.get("domain"),
        "prompt": item["text"],
        "subject": row.get("subject"),
        "answer": tok.decode([target]),
        "lead_in": item.get("lead_in", ""),
        "p_clean": p_clean,
        "p_corrupt": corrupted,
        "n_tokens": n_tokens,
        "subject_range": [spans[-1][0], spans[-1][1]],
        "corrupt_spans": [list(s) for s in spans],
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
    "first corrupted token", "middle corrupted tokens", "last corrupted token",
    "first token after it", "further tokens", "last token",
]


def aggregate(traces, n_layers, effect):
    """Mean indirect effect per layer, and the peak of the chosen curve."""
    out = {"n_prompts": len(traces)}
    if not traces:
        return out
    out["p_clean"] = float(np.mean([t["p_clean"] for t in traces]))
    out["p_corrupt"] = float(np.mean([t["p_corrupt"] for t in traces]))
    for kind in KINDS + SEVER_KINDS:
        if kind not in traces[0]["curves"]:
            continue
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


def _ci(values):
    return [round(float(np.percentile(values, 2.5)), 4), round(float(np.percentile(values, 97.5)), 4)]


def reliability(traces, n_layers, band, kind="mlp", n_boot=1000, seed=0):
    """How reliably this model recalls facts in the early-to-mid band of
    `kind` layers, rather than just where the averaged curve peaks.

    share_peak_in_band   share of facts whose own curve peaks in the band
    mass_in_band         per fact, the share of its positive effect that lies
                         in the band (uniform spread would give `baseline`)
    peak_ci              where the averaged curve peaks, across resampled facts
    sever_drop_mlp/attn  how much hidden-state recovery in the band falls when
                         later MLPs (or attention) are frozen: necessity
    Each with a 95% bootstrap interval over facts, and a one-word verdict."""
    if not traces:
        return None
    low, high = band
    in_band = [layer for layer in range(n_layers) if low <= layer / n_layers < high]
    curves = np.array([np.array(t["curves"][kind]) - t["p_corrupt"] for t in traces])
    peaks = curves.argmax(axis=1)
    hits = np.isin(peaks, in_band).astype(float)
    positive = np.clip(curves, 0, None)
    mass = positive[:, in_band].sum(axis=1) / np.maximum(positive.sum(axis=1), 1e-9)
    rng = np.random.default_rng(seed)
    boots = rng.integers(0, len(traces), size=(n_boot, len(traces)))
    mean_peaks = [int(curves[idx].mean(axis=0).argmax()) for idx in boots]
    out = {
        "kind": kind,
        "band": [low, high],
        "band_layers": [in_band[0], in_band[-1]] if in_band else None,
        "n_facts": len(traces),
        "share_peak_in_band": round(float(hits.mean()), 4),
        "share_peak_in_band_ci": _ci(hits[boots].mean(axis=1)),
        "mass_in_band": round(float(mass.mean()), 4),
        "mass_in_band_ci": _ci(mass[boots].mean(axis=1)),
        "baseline": round(len(in_band) / n_layers, 4),
        "peak_median": int(np.median(peaks)),
        "peak_iqr": [int(np.percentile(peaks, 25)), int(np.percentile(peaks, 75))],
        "peak_ci": [int(np.percentile(mean_peaks, 2.5)), int(np.percentile(mean_peaks, 97.5))],
    }
    if "sever_mlp" in traces[0]["curves"] and in_band:
        hidden = np.array([np.array(t["curves"]["hidden"]) - t["p_corrupt"] for t in traces])[:, in_band].mean()
        for name in SEVER_KINDS:
            severed = np.array([np.array(t["curves"][name]) - t["p_corrupt"] for t in traces])[:, in_band].mean()
            out[f"{name.replace('sever_', 'sever_drop_')}"] = round(float(1 - severed / hidden), 4) if hidden > 0 else None
    out["verdict"] = _verdict(out)
    return out


def _verdict(r):
    """strong: most facts peak in the band (lower bound >= 0.6) and the band
    holds clearly more than its share of the effect; moderate: a majority
    and more than its share; weak otherwise. Severing, when run, must also
    show the MLPs are needed (a drop of at least 0.3) for strong."""
    share_low = r["share_peak_in_band_ci"][0]
    above = r["mass_in_band"] - r["baseline"]
    needed = r.get("sever_drop_mlp")
    if share_low >= 0.6 and above >= 0.15 and (needed is None or needed >= 0.3):
        return "strong"
    if r["share_peak_in_band"] >= 0.5 and above > 0:
        return "moderate"
    return "weak"


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


def feeds_traced_layers(row):
    """Only the form edits are written in, at the standard window: the other
    formats and windows are comparisons, not the model's edit-layer hint."""
    return (row.get("format") or "completion") == "completion" and row.get("window", 10) == 10


def rebuild_traced_layers(out_root, manifest):
    """model -> the layer its most recent finished plain-completion trace chose.

    Derived from the summaries, never appended to, so re-tracing a model
    replaces its entry and archiving a trace run drops it - the same rule the
    results manifest follows.
    """
    latest = {}
    for row in manifest:
        model = row.get("model")
        if not model or row.get("peak_layer") is None or not feeds_traced_layers(row):
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
            "fact_set": row.get("fact_set_name"),
            "verdict": (row.get("reliability") or {}).get("verdict"),
            "share_peak_in_band": (row.get("reliability") or {}).get("share_peak_in_band"),
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


def _round_curves(curves):
    return {kind: [round(float(v), 5) for v in values] for kind, values in curves.items()}


def main():
    args = parse_args()
    launch_guard.require_dashboard(args.out_root, args.untracked, "causal_tracing")
    torch.manual_seed(args.seed)
    rng = np.random.default_rng(args.seed)

    fact_set_info = None
    if args.fact_set:
        fact_set_info, rows = load_fact_set(args.fact_set)
        if len(rows) < MIN_FACTS and not args.allow_thin:
            raise SystemExit(f"fact set {fact_set_info.get('name')} has {len(rows)} facts, below the {MIN_FACTS} "
                             f"minimum; add facts from another dataset, or pass --allow_thin 1 to trace it anyway")
        if fact_set_info.get("formats") and args.format not in fact_set_info["formats"]:
            print(f"warning: fact set was selected for formats {fact_set_info['formats']}, "
                  f"tracing as {args.format}; some facts may drop out", flush=True)
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

    templates, template_source = resolve_modules(model, args.model)
    n_layers = getattr(model.config, "num_hidden_layers", None) or model.config.n_layer
    print(f"[{run_name}] {n_layers} layers, modules from {template_source}, format {args.format}", flush=True)

    # ROME's noise level: 3x the standard deviation of this model's own token
    # embeddings, measured over the candidate prompts rather than the whole
    # vocabulary, so it is scaled to the tokens actually being corrupted.
    with torch.no_grad():
        embed = model.get_submodule(templates["embed"])
        texts = [item["text"] for item in (F.build(row, args.format, tok) for row in rows[:1000]) if item]
        sample_ids = [i for text in texts for i in tok(text, add_special_tokens=False)["input_ids"]]
        embeddings = embed(torch.tensor(sample_ids[:20000], device=device))
        embedding_std = float(embeddings.float().std())
    args.noise_level = args.noise_scale * embedding_std
    print(f"[{run_name}] embedding std {embedding_std:.4f}, noise {args.noise_level:.4f}", flush=True)

    config = {
        "run": run_name, "model": args.model, "model_path": model_path,
        "model_type": model.config.model_type, "n_layers": n_layers,
        "modules": templates, "module_source": template_source,
        "data_path": args.data_path, "split": args.split, "format": args.format,
        "fact_set": args.fact_set or None,
        "fact_set_name": fact_set_info.get("name") if fact_set_info else None,
        "fact_set_size": len(rows) if fact_set_info else None,
        "dataset_benchmark": args.dataset_benchmark, "dataset_subset": args.dataset_subset,
        "n_prompts": args.n_prompts, "max_candidates": args.max_candidates,
        "min_prob": args.min_prob, "noise_scale": args.noise_scale,
        "noise_level": args.noise_level, "embedding_std": embedding_std,
        "window": args.window, "effect": args.effect, "sever": args.sever, "band": list(args.band),
        "n_noise_samples": args.n_noise_samples, "token_grid": args.token_grid,
        "dtype": args.dtype, "seed": args.seed,
    }
    with open(os.path.join(run_dir, "hparams.yaml"), "w") as f:
        yaml.safe_dump(config, f, sort_keys=True)

    started_at, t_start = _now(), time.time()
    ckpt_file = open(os.path.join(run_dir, "checkpoints.jsonl"), "w")
    traces, scanned, skipped = [], 0, 0
    total = min(args.n_prompts, len(rows))

    def checkpoint():
        summary = aggregate(traces, n_layers, args.effect)
        row = {
            "step": len(traces), "total_steps": total, "at": _now(), "elapsed_sec": round(time.time() - t_start, 2),
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
        # only the first --token_grid facts pay for it.
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
        "reliability": reliability(traces, n_layers, args.band, seed=args.seed),
        "thin": len(traces) < MIN_FACTS,
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
            # Every fact's own curves: what reliability() was computed from,
            # and what any later breakdown (by relation, domain, ...) needs.
            "prompts": [{**{k: t[k] for k in ("id", "relation", "domain", "prompt", "subject", "answer",
                                              "p_clean", "p_corrupt", "corrupt_spans")},
                         "curves": _round_curves(t["curves"])} for t in traces],
        }, f)

    manifest = rebuild_manifest(args.out_root)
    mapping = rebuild_traced_layers(args.out_root, manifest)
    verdict = (summary["reliability"] or {}).get("verdict")
    print(f"[{run_name}] done: {args.model} -> layer {summary.get('peak_layer')} "
          f"(AIE {summary.get('peak_aie')}, {len(traces)} prompts, early-to-mid: {verdict})"
          + (" THIN" if summary["thin"] else ""), flush=True)
    print(f"[{run_name}] traced_layers.json now covers {sorted(mapping)}", flush=True)


if __name__ == "__main__":
    main()
