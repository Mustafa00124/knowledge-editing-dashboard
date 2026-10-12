"""NMKE: neuron-specific masked knowledge editing (NeurIPS 2025, arXiv:2510.22139).

Ported from github.com/LiuJinzhe-Keepgoing/NMKE. Upstream ships NMKE as a
drop-in replacement for EasyEdit's AlphaEdit_main.py plus a patched
transformers modeling_llama.py, and says outright that the released code
is not the cleaned-up version. So this is a port of the algorithm rather
than of the file:

  - The masking logic (attribution scores, entropy-adaptive ratios, the
    resonance/burst mask) is reproduced as they wrote it, including their
    AMPLIFY_FACTOR of 30 and their 1e-8 clamps.
  - The AlphaEdit machinery it wraps comes from our own
    external/EasyEdit rather than from their copy, so NMKE inherits the
    local AlphaEdit fixes already made there (the P cache path and the
    GPT-J cache_c shape rule) instead of reintroducing the bugs those
    fixed.
  - Their attribution reads per-layer FFN activations and residual
    streams out of the patched modeling file. capture.py gets the same
    tensors with hooks and output_hidden_states, which is what makes this
    runnable on Qwen3, Olmo-3 and Mistral - upstream is Llama-only, and
    their GPT branch reads fields the Llama patch does not expose.

What NMKE adds to AlphaEdit is one line in the insert loop: the
closed-form update matrix is multiplied row-wise by a 0/1 neuron mask, so
only neurons the attribution keeps are allowed to move. The mask is
recomputed per edit batch, which is what makes the edit site fact-
dependent rather than fixed by hparams.layers.

The insert loop below is a copy of execute_AlphaEdit from
external/EasyEdit/easyeditor/models/alphaedit/AlphaEdit_main.py with that
one masking step added, mirroring how upstream distributes it. Copied
rather than called because the mask has to be applied *inside* the loop:
AlphaEdit writes each layer's update before computing the next layer's
keys, so masking the deltas afterwards would give a different result
whenever hparams.layers has more than one layer.
"""
import os
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
import yaml

from . import hparams_yaml

from . import capture, locations

P = None
P_LOADED = False
CACHE_C = None


@dataclass
class NMKEHyperParams:
    """AlphaEdit's fields plus NMKE's mask knobs."""

    layers: list
    clamp_norm_factor: float
    layer_selection: str
    fact_token: str
    v_num_grad_steps: int
    v_lr: float
    v_loss_layer: int
    v_weight_decay: float
    kl_factor: float
    mom2_adjustment: bool
    mom2_update_weight: int
    rewrite_module_tmp: str
    layer_module_tmp: str
    mlp_module_tmp: str
    attn_module_tmp: str
    ln_f_module: str
    lm_head_module: str
    mom2_dataset: str
    mom2_n_samples: int
    mom2_dtype: str
    alg_name: str
    device: int
    model_name: str
    stats_dir: str
    P_loc: str
    nullspace_threshold: float
    L2: float
    # NMKE's own knobs. The bounds and gammas are upstream's defaults in
    # entropy_adaptive_mask_ratio; amplify_factor is its AMPLIFY_FACTOR,
    # which upstream notes it lowered from 100 to 30.
    resonance_bounds: tuple = (0.3, 0.4)
    burst_bounds: tuple = (0.3, 0.4)
    gamma_r: float = 3.0
    gamma_b: float = 2.0
    entropy_alpha: float = 30.0
    amplify_factor: float = 30.0
    use_resonance: bool = True
    use_burst: bool = True
    max_length: int = 40
    model_parallel: bool = False
    fp16: bool = False

    @classmethod
    def from_hparams(cls, path):
        if not str(path).endswith(".yaml"):
            path = f"{path}.yaml"
        config = hparams_yaml.load(path)  # "5e-1" read as a number, as EasyEdit's loaders do
        assert config.get("alg_name") == "NMKE", f"not an NMKE hparams file: {path}"
        for key in ("resonance_bounds", "burst_bounds"):
            if key in config and config[key] is not None:
                config[key] = tuple(config[key])
        return cls(**config)

    def to_dict(self):
        return dict(self.__dict__)


def entropy_adaptive_mask_ratio(score_matrix, hparams):
    """Upstream's entropy_adaptive_mask_ratio, verbatim in behaviour.

    The flatter the attribution is across neurons (high entropy), the
    larger a share of them the mask keeps - the idea being that a fact
    whose evidence is spread thin needs a wider edit than one that is
    concentrated in a few neurons.
    """
    d_ff = score_matrix.shape[1]
    log_d = np.log(d_ff)

    shifted = score_matrix - score_matrix.max(dim=1, keepdim=True)[0]
    softmax_scores = torch.softmax(shifted * hparams.entropy_alpha, dim=1)
    entropy_prompt = -(softmax_scores * (softmax_scores + 1e-8).log()).sum(dim=1)
    entropy_r = entropy_prompt.mean() / log_d

    low, high = hparams.resonance_bounds
    resonance_ratio = low + (high - low) * entropy_r.clamp(0, 1).pow(hparams.gamma_r)

    max_acts = torch.clamp(score_matrix.max(dim=0).values, min=0.0)
    if max_acts.sum() < 1e-8:
        # Every neuron scored <= 0: no burst signal to threshold on, so
        # fall back to the narrow end of the burst range.
        print("[NMKE] all attribution scores non-positive, using fallback burst ratio")
        return float(resonance_ratio), float(hparams.burst_bounds[0])

    burst_probs = max_acts / (max_acts.sum() + 1e-8)
    entropy_burst = -(burst_probs * (burst_probs + 1e-8).log()).sum()
    entropy_b = entropy_burst / log_d
    low, high = hparams.burst_bounds
    burst_ratio = low + (high - low) * entropy_b.clamp(0, 1).pow(hparams.gamma_b)
    return float(resonance_ratio), float(burst_ratio)


def hybrid_resonant_mask(score_matrix, resonance_ratio, burst_ratio,
                         use_resonance=True, use_burst=True):
    """Union of the two neuron sets NMKE calls knowledge-general and knowledge-specific.

    Resonance: neurons that score above their prompt's mean for many
    prompts (consistent contributors). Burst: neurons with a high peak
    score on any single prompt (prompt-specific contributors).

    Upstream's use_resonance/use_burst arguments are dead there - the
    branch that reads them is commented out and the union is taken
    unconditionally - so they are wired up here, defaulting to the union
    that upstream actually runs.
    """
    normalized = (score_matrix - score_matrix.mean(dim=1, keepdim=True)) / (
        score_matrix.std(dim=1, keepdim=True) + 1e-6
    )
    resonance_counts = (normalized > 0.0).float().sum(dim=0)
    resonance_cut = torch.quantile(resonance_counts, 1 - resonance_ratio)
    resonance_mask = (resonance_counts >= resonance_cut).float()

    burst_score = score_matrix.max(dim=0).values
    burst_cut = torch.quantile(burst_score, 1 - burst_ratio)
    burst_mask = (burst_score >= burst_cut).float()

    if use_resonance and use_burst:
        final_mask = torch.clamp(resonance_mask + burst_mask, max=1.0)
    elif use_resonance:
        final_mask = resonance_mask
    elif use_burst:
        final_mask = burst_mask
    else:
        final_mask = torch.ones_like(resonance_mask)
    return final_mask, resonance_mask, burst_mask


def importance_scores(model, hparams, layer, activations, hidden_states, predicted_ids):
    """Per-neuron attribution: how much amplifying that neuron alone moves the top token.

    Upstream computes this from its patched modeling file's per-layer
    tuples; the quantities are the layer's FFN activations, the residual
    stream at that layer, and the final hidden state's variance. Same
    arithmetic here, including the fixed variance (every probe is
    normalised by the *final* state's scale rather than its own, which
    keeps the perturbed and unperturbed logits comparable).
    """
    weight = capture.get_module(model, capture.module_name(hparams, layer)).weight
    scores = []
    for batch in range(activations.shape[0]):
        coefficients = activations[batch, -1].float()
        # (d_ff, hidden): each row is one neuron's contribution vector.
        subvalues = (coefficients * weight.float()).T
        residual = hidden_states[layer][batch, -1].float()
        final_variance = hidden_states[-1][batch, -1].float().pow(2).mean(-1, keepdim=True)

        with torch.no_grad():
            base = torch.softmax(
                capture.logits_from_residual(model, hparams, residual, final_variance), dim=-1
            )[predicted_ids[batch]]
            probes = subvalues * hparams.amplify_factor + residual
            probe_probs = torch.softmax(
                capture.logits_from_residual(model, hparams, probes, final_variance), dim=-1
            )[:, predicted_ids[batch]]
            base = base.clamp(min=1e-8, max=1.0)
            probe_probs = probe_probs.clamp(min=1e-8, max=1.0)
            scores.append(torch.log(probe_probs) - torch.log(base))

    stacked = torch.stack(scores)
    return torch.nan_to_num(stacked, nan=0.0, posinf=0.0, neginf=0.0)


def neuron_masks(model, tok, requests, hparams, context_templates):
    """One 0/1 mask per edited layer, computed from this batch's facts."""
    device = next(model.parameters()).device
    prompts = [
        context.format(request["prompt"].replace("{}", request["subject"]))
        for request in requests
        for context_list in context_templates
        for context in context_list
    ]
    inputs = tok(prompts, return_tensors="pt", padding=True).to(device)

    with torch.no_grad(), capture.FFNActivations(model, hparams, hparams.layers) as acts:
        outputs = model(**inputs, output_hidden_states=True)
    predicted_ids = outputs.logits[:, -1].argmax(-1).tolist()

    masks, report = {}, {}
    for layer in hparams.layers:
        scores = importance_scores(model, hparams, layer, acts.at(layer),
                                   outputs.hidden_states, predicted_ids)
        resonance_ratio, burst_ratio = entropy_adaptive_mask_ratio(scores, hparams)
        mask, _, _ = hybrid_resonant_mask(scores, resonance_ratio, burst_ratio,
                                          hparams.use_resonance, hparams.use_burst)
        masks[layer] = mask
        report[layer] = {
            "kept": int(mask.sum().item()),
            "total": int(mask.numel()),
            "resonance_ratio": round(resonance_ratio, 4),
            "burst_ratio": round(burst_ratio, 4),
        }
        print(f"[NMKE] layer {layer}: keeping {report[layer]['kept']}/{report[layer]['total']} neurons "
              f"(resonance {resonance_ratio:.3f}, burst {burst_ratio:.3f})")
        del scores
        torch.cuda.empty_cache()

    del outputs
    torch.cuda.empty_cache()
    return masks, report


def _ensure_projection(model, tok, hparams, nethook):
    """AlphaEdit's null-space projection P and its running key cache.

    Same logic as our patched AlphaEdit_main, including the local fixes:
    P is saved to hparams.P_loc rather than a hardcoded filename, and
    GPT-J is covered by the cache_c shape rule.
    """
    global P, P_LOADED, CACHE_C
    from easyeditor.models.alphaedit.AlphaEdit_main import get_project

    name = hparams.model_name.lower()
    out = nethook.get_parameter(model, f"{hparams.rewrite_module_tmp.format(hparams.layers[-1])}.weight")
    if "gpt2-xl" in name:
        size = out.shape[0]
    elif any(family in name for family in ("llama", "qwen", "gpt-j-6b", "mistral", "olmo", "smollm3", "map-neo")):
        size = out.shape[1]
    else:
        raise ValueError(
            f"NMKE has no cache_c/P shape rule for {hparams.model_name!r}; add it here the same "
            "way AlphaEdit_main.py does rather than failing later with a NameError"
        )
    del out

    if not P_LOADED:
        if os.path.exists(hparams.P_loc):
            P = torch.load(hparams.P_loc)
        else:
            print("[NMKE] null-space projection not cached, computing it")
            P = torch.zeros((len(hparams.layers), size, size), device="cpu")
            for i, layer in enumerate(hparams.layers):
                P[i, :, :] = get_project(model, tok, layer, hparams)
            os.makedirs(os.path.dirname(os.path.abspath(hparams.P_loc)), exist_ok=True)
            torch.save(P, hparams.P_loc)
        P_LOADED = True
    if CACHE_C is None:
        CACHE_C = torch.zeros((len(hparams.layers), size, size), device="cpu")


def apply_nmke_to_model(
    model,
    tok,
    requests,
    hparams,
    copy=False,
    return_orig_weights=False,
    keep_original_weight=False,
    cache_template=None,
    **kwargs,
):
    """AlphaEdit's batched closed-form edit, restricted to the masked neurons."""
    from easyeditor.util import nethook

    if copy:
        model = deepcopy(model)

    _ensure_projection(model, tok, hparams, nethook)
    deltas = _execute_nmke(model, tok, requests, hparams, nethook, cache_template)

    weights_copy = {}
    device = next(model.parameters()).device
    with torch.no_grad():
        for name, update in deltas.items():
            weight = nethook.get_parameter(model, name)
            if return_orig_weights and name not in weights_copy:
                weights_copy[name] = weight.detach().clone()
            weight[...] += update.to(device=weight.device, dtype=weight.dtype)

    if not keep_original_weight and not return_orig_weights:
        weights_copy = {}
    return model, weights_copy


def _execute_nmke(model, tok, requests, hparams, nethook, cache_template=None):
    from easyeditor.models.alphaedit.AlphaEdit_main import (
        get_context_templates,
        upd_matrix_match_shape,
    )
    from easyeditor.models.alphaedit.compute_ks import compute_ks
    from easyeditor.models.alphaedit.compute_z import (
        compute_z,
        get_module_input_output_at_words,
    )
    from easyeditor.util.device import copy_to_param, get_module_device, normalize_device

    deltas = {}
    device = normalize_device(getattr(hparams, "device", None))

    requests = deepcopy(requests)
    for i, request in enumerate(requests):
        if request["target_new"][0] != " ":
            requests[i]["target_new"] = " " + request["target_new"]
        if "{}" not in request["prompt"]:
            assert request["subject"] in request["prompt"], (
                f"subject {request['subject']!r} does not occur in prompt {request['prompt']!r}"
            )
        requests[i]["prompt"] = requests[i]["prompt"].replace(requests[i]["subject"], "{}")
        print(f"[NMKE] {request['prompt']} -> {request['target_new']}")

    weights = {
        f"{hparams.rewrite_module_tmp.format(layer)}.weight": nethook.get_parameter(
            model, f"{hparams.rewrite_module_tmp.format(layer)}.weight"
        )
        for layer in hparams.layers
    }
    weights_copy = {k: v.detach().clone() for k, v in weights.items()}

    context_templates = get_context_templates(model, tok)
    z_layer = hparams.layers[-1]
    z_device = get_module_device(nethook.get_module(model, hparams.layer_module_tmp.format(z_layer)), device)

    z_list = []
    for request in requests:
        cache_fname = (
            Path(str(cache_template).format(z_layer, hparams.clamp_norm_factor, request["case_id"]))
            if cache_template is not None
            else None
        )
        loaded = False
        if cache_fname is not None and cache_fname.exists():
            try:
                z_list.append(torch.from_numpy(np.load(cache_fname)["v_star"]).to(z_device))
                loaded = True
            except Exception as error:
                print(f"[NMKE] could not read {cache_fname} ({error}), recomputing")
        if not loaded:
            cur_z = compute_z(model, tok, request, hparams, z_layer, context_templates)
            z_list.append(cur_z)
            if cache_fname is not None:
                cache_fname.parent.mkdir(exist_ok=True, parents=True)
                np.savez(cache_fname, **{"v_star": cur_z.detach().cpu().numpy()})
    zs = torch.stack(z_list, dim=1)

    # NMKE's contribution: which neurons this batch of facts is allowed to
    # move, decided from the facts themselves rather than from hparams.
    masks, report = neuron_masks(model, tok, requests, hparams, context_templates)

    for i, layer in enumerate(hparams.layers):
        print(f"\n[NMKE] LAYER {layer}")
        layer_ks = compute_ks(model, tok, requests, hparams, layer, context_templates).T
        cur_zs = get_module_input_output_at_words(
            model,
            tok,
            z_layer,
            context_templates=[request["prompt"] for request in requests],
            words=[request["subject"] for request in requests],
            module_template=hparams.layer_module_tmp,
            fact_token_strategy=hparams.fact_token,
        )[1].T
        cur_zs = cur_zs.to(device=zs.device, dtype=zs.dtype)
        targets = zs - cur_zs
        print("z error", torch.linalg.norm(targets, dim=0).mean())

        repeat_factor = layer_ks.size(1) // targets.size(1)
        targets = targets.repeat_interleave(repeat_factor, dim=1)
        resid = targets / (len(hparams.layers) - i)

        proj = P[i, :, :].to(device).float()
        layer_ks = layer_ks.to(device).float()
        resid = resid.to(device).float()
        cache = CACHE_C[i, :, :].to(device).float()
        upd_matrix = torch.linalg.solve(
            proj @ (layer_ks @ layer_ks.T + cache)
            + hparams.L2 * torch.eye(layer_ks.shape[0], dtype=proj.dtype, device=device),
            proj @ layer_ks @ resid.T,
        )

        # The one line that makes this NMKE rather than AlphaEdit. Rows of
        # upd_matrix are neurons, so zeroing a row freezes that neuron.
        mask = masks[layer].to(device=upd_matrix.device, dtype=upd_matrix.dtype)
        upd_matrix = mask[:, None] * upd_matrix

        weight_name = f"{hparams.rewrite_module_tmp.format(layer)}.weight"
        upd_matrix = upd_matrix_match_shape(upd_matrix, weights[weight_name].shape)
        print("orig norm", torch.linalg.norm(weights[weight_name]))
        print("upd norm", torch.linalg.norm(upd_matrix))

        with torch.no_grad():
            updated = weights[weight_name].to(device=upd_matrix.device, dtype=upd_matrix.dtype) + upd_matrix
            copy_to_param(weights[weight_name], updated)
            deltas[weight_name] = upd_matrix.detach().cpu()

        for tensor in (layer_ks, cur_zs, targets):
            tensor.cpu()
        torch.cuda.empty_cache()

    for i, layer in enumerate(hparams.layers):
        layer_ks = compute_ks(model, tok, requests, hparams, layer, context_templates).T
        CACHE_C[i, :, :] += layer_ks.cpu() @ layer_ks.cpu().T

    with torch.no_grad():
        for name, original in weights_copy.items():
            copy_to_param(weights[name], original)

    for request in requests:
        locations.record(
            "nmke",
            prompt=request["prompt"],
            subject=request.get("subject"),
            layers=list(hparams.layers),
            neurons_per_layer={int(layer): stats["kept"] for layer, stats in report.items()},
            mask=report,
        )
    return deltas
