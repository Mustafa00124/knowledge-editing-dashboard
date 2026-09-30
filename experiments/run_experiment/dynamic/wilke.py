"""WilKE: Wise-Layer Knowledge Editor (ACL Findings 2024, arXiv:2402.10987).

Ported from the authors' code at github.com/ChenhuiHu/WilKE rather than
reimplemented: their wilke/compute_u.py and wilke/compute_v.py are
byte-identical to the ROME files they sit next to (diff shows only the
import lines and the HyperParams type annotation), so the algorithm that
is actually WilKE's own is just the layer scan in wilke_main.py. That
scan is what this module reproduces, on top of the ROME primitives our
own external/EasyEdit already ships - which means WilKE inherits every
model fix that lives there, including the Qwen layer-stat cap.

The selection rule, from their code rather than the paper's prose: for
each candidate layer, compute and apply the full ROME rank-one update,
measure

    LA = ||W_edited - W_original||_F / ||W_original||_F

restore the weights, and finally edit at the layer with the smallest LA.
So "pattern match degree" is operationalised as *how little the layer has
to move* to absorb the fact: the layer that already almost represents the
new association is the layer that matches its pattern. The paper's
motivation for this is lifelong editing - editing a mismatched layer is
what builds up the toxicity they document.

Cost: one full ROME edit per candidate layer per fact. With the authors'
scanning_ceiling of 7 that is 7x ROME, and every candidate layer needs
its own cached mom2 statistics because mom2_adjustment is on (their own
hparams set it true). The first run against a model therefore pays for
`scanning_ceiling` layer-stat computations, not one. Their own
implementation then recomputes the winning layer's update an eighth time;
this port caches the scan's (u, v) pair and reuses it, which is
arithmetically identical because the model is restored to the same state
before the final write.
"""
from copy import deepcopy
from dataclasses import dataclass

import torch
import yaml

from . import locations


@dataclass
class WilKEHyperParams:
    """Deliberately not a subclass of ROMEHyperParams.

    It has to satisfy the same field reads that compute_u/compute_v make,
    but importing the EasyEdit class at module import time would make
    this file unimportable without EasyEdit on sys.path - which the unit
    tests need. The fields below are ROME's, plus scanning_ceiling.
    """

    layers: list
    fact_token: str
    v_num_grad_steps: int
    v_lr: float
    v_loss_layer: int
    v_weight_decay: float
    clamp_norm_factor: float
    kl_factor: float
    mom2_adjustment: bool
    context_template_length_params: list
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
    # WilKE's own knob: candidate layers are range(scanning_ceiling).
    scanning_ceiling: int = 7
    max_length: int = 40
    model_parallel: bool = False
    fp16: bool = False

    @classmethod
    def from_hparams(cls, path):
        if not str(path).endswith(".yaml"):
            path = f"{path}.yaml"
        with open(path) as f:
            config = yaml.safe_load(f)
        assert config.get("alg_name") == "WilKE", f"not a WilKE hparams file: {path}"
        return cls(**config)

    def to_dict(self):
        return dict(self.__dict__)


def candidate_layers(hparams):
    """range(scanning_ceiling), matching wilke_main.py's own loop."""
    return list(range(hparams.scanning_ceiling))


def _rome_update(model, tok, request, hparams, layer):
    """One layer's ROME rank-one update, as (u, v), computing nothing else."""
    from easyeditor.models.rome.compute_u import compute_u
    from easyeditor.models.rome.compute_v import compute_v
    from easyeditor.models.rome.rome_main import get_context_templates

    templates = get_context_templates(model, tok, hparams.context_template_length_params)
    left_vector = compute_u(model, tok, request, hparams, layer, templates)
    right_vector = compute_v(model, tok, request, hparams, layer, left_vector, templates)
    return left_vector, right_vector


def _match_shape(matrix, shape):
    if matrix.shape == shape:
        return matrix
    if matrix.T.shape == shape:
        return matrix.T
    raise ValueError(f"rank-one update {tuple(matrix.shape)} matches neither {tuple(shape)} nor its transpose")


def apply_wilke_to_model(
    model,
    tok,
    request,
    hparams,
    copy=False,
    return_orig_weights=False,
    keep_original_weight=False,
    **kwargs,
):
    """Edit one fact at the layer whose relative weight change is smallest.

    Signature and return value match EasyEdit's apply_rome_to_model, so
    run_experiment.py's LOCATE_AND_EDIT dispatch drives this unchanged.
    Registered in "single" mode there: like ROME, this only ever edits
    one fact per call.
    """
    from easyeditor.util import nethook

    if copy:
        model = deepcopy(model)

    request = request[0] if isinstance(request, (list, tuple)) else request
    request = deepcopy(request)
    if request["target_new"] != " ":
        request["target_new"] = " " + request["target_new"]
    if "{}" not in request["prompt"]:
        assert request["subject"] in request["prompt"], (
            f"subject {request['subject']!r} does not occur in prompt {request['prompt']!r}"
        )
        request["prompt"] = request["prompt"].replace(request["subject"], "{}")

    scan = []
    updates = {}
    for layer in candidate_layers(hparams):
        weight_name = f"{hparams.rewrite_module_tmp.format(layer)}.weight"
        weight = nethook.get_parameter(model, weight_name)
        original = weight.detach().clone()

        left_vector, right_vector = _rome_update(model, tok, request, hparams, layer)
        update = _match_shape(left_vector.unsqueeze(1) @ right_vector.unsqueeze(0), weight.shape)

        with torch.no_grad():
            # LA is measured on the applied weight rather than on the raw
            # update so that the dtype rounding a real write incurs is
            # part of the number being compared, exactly as upstream.
            weight[...] += update
            relative_change = torch.norm((weight - original) / torch.norm(original)).item()
            weight[...] = original

        scan.append({"layer": layer, "la": relative_change})
        updates[layer] = (left_vector.detach(), right_vector.detach())
        print(f"[WilKE] candidate layer {layer}: LA={relative_change:.6g}")
        torch.cuda.empty_cache()

    chosen = min(scan, key=lambda row: row["la"])["layer"]
    print(f"[WilKE] editing layer {chosen} (lowest LA of {len(scan)} candidates)")

    weight_name = f"{hparams.rewrite_module_tmp.format(chosen)}.weight"
    weight = nethook.get_parameter(model, weight_name)
    weights_copy = {weight_name: weight.detach().clone()} if return_orig_weights else {}

    left_vector, right_vector = updates[chosen]
    with torch.no_grad():
        weight[...] += _match_shape(left_vector.unsqueeze(1) @ right_vector.unsqueeze(0), weight.shape)

    locations.record(
        "wilke",
        prompt=request["prompt"],
        subject=request.get("subject"),
        layer=chosen,
        layers=[chosen],
        scan=scan,
    )

    if not keep_original_weight and not return_orig_weights:
        weights_copy = {}
    return model, weights_copy
