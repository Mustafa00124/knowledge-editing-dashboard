"""FiDAL: Fisher-driven adaptive locating (ACL 2026, aclanthology.org/2026.acl-long.957).

Reimplemented from the paper. There is no released code: the paper links
none, and searches turned up no repository under the authors' names, so
unlike the other three methods in this package nothing here is a port.
What it follows is Algorithm 1 and Section 3.2, and the deviations it was
forced into are listed at the bottom of this docstring.

FiDAL is a *locator*, not an editor. The paper's own framing: it "can be
computed using existing editing methods, including closed-form solutions
(e.g., ROME, MEMIT, and AlphaEdit)". So this module decides which weight
matrices to edit for a given fact and then hands that decision to one of
the editors already registered in run_experiment.py, which is why the
hparams file carries a base_method field.

Probing stage, per fact:
  1. Freeze every weight.
  2. Give each candidate matrix W (m x n) two proxy vectors, dH in R^m
     and dW in R^n, and modulate it as W_tilde = W * (1 + dH (x) dW).
     The identity term makes the modulation residual, so an already
     well-suited matrix can be left alone.
  3. Take T gradient steps on the edit target's cross-entropy, training
     only the proxy vectors.
  4. Score each matrix by the Fisher Information of its proxies,
     estimated as the mean squared gradient:
         F(W) = mean_j F(dH_j) + mean_k F(dW_k)
  5. Edit the top-K matrices.

The modulation is never materialised as a dense m x n matrix. Since
(W * (1 + dH dW^T)) x = W x + dH * (W (dW * x)), one extra matmul per
probed layer reproduces it exactly, which is what keeps the probing stage
as cheap as the paper claims.

Deviations, all forced and all recorded in the run's hparams.yaml:
  - The paper probes "linear layers within the FFNs" generally. The
    candidate set here is the matrix hparams.rewrite_module_tmp names at
    each candidate layer, because that is the matrix the base editors can
    actually write to: selecting a gate or up projection would produce a
    decision no closed-form editor in this project could act on.
  - The paper does not state the probing learning rate, step count T,
    proxy initialisation scale, or K. They are hparams here, with
    defaults chosen to be lightweight (T=10, K=1 for single-layer bases).
  - Fisher is the empirical Fisher (squared gradient of the loss on the
    edit pair), the estimator the paper's Eq. 3 reduces to for a
    cross-entropy loss at the observed label.
"""
from copy import deepcopy
from dataclasses import dataclass

import torch
import torch.nn.functional as F
import yaml

from . import capture, locations

BASE_EDITORS = {
    "rome": ("easyeditor.models.rome.rome_hparams", "ROMEHyperParams",
             "easyeditor.models.rome.rome_main", "apply_rome_to_model", "ROME"),
    "memit": ("easyeditor.models.memit.memit_hparams", "MEMITHyperParams",
              "easyeditor.models.memit.memit_main", "apply_memit_to_model", "MEMIT"),
    "pmet": ("easyeditor.models.pmet.pmet_hparams", "PMETHyperParams",
             "easyeditor.models.pmet.pmet_main", "apply_pmet_to_model", "PMET"),
    "alphaedit": ("easyeditor.models.alphaedit.AlphaEdit_hparams", "AlphaEditHyperParams",
                  "easyeditor.models.alphaedit.AlphaEdit_main", "apply_AlphaEdit_to_model", "AlphaEdit"),
}

# Keys that configure FiDAL itself; everything else in the yaml is
# forwarded to the base editor's HyperParams class untouched.
FIDAL_ONLY = {
    "base_method", "candidate_layers", "top_k", "probe_steps", "probe_lr",
    "probe_init", "alg_name",
}


@dataclass
class FiDALHyperParams:
    """FiDAL's own knobs plus the whole base editor's config.

    The yaml is self-contained - it carries every field the base editor
    needs - so a FiDAL run records exactly one hparams file, the same way
    every other method in this project does, instead of pointing at a
    second one that could drift.
    """

    alg_name: str
    base_method: str
    model_name: str
    device: int
    candidate_layers: list
    top_k: int = 1
    probe_steps: int = 10
    probe_lr: float = 1e-2
    probe_init: float = 1e-3
    base_config: dict = None

    @classmethod
    def from_hparams(cls, path):
        if not str(path).endswith(".yaml"):
            path = f"{path}.yaml"
        with open(path) as f:
            config = yaml.safe_load(f)
        assert config.get("alg_name") == "FiDAL", f"not a FiDAL hparams file: {path}"
        base_method = config["base_method"]
        if base_method not in BASE_EDITORS:
            raise ValueError(
                f"base_method {base_method!r} is not one of {sorted(BASE_EDITORS)} - FiDAL selects "
                "layers, it does not edit, so it needs an editor to hand them to"
            )
        base_config = {k: v for k, v in config.items() if k not in FIDAL_ONLY}
        base_config["alg_name"] = BASE_EDITORS[base_method][4]
        return cls(
            alg_name=config["alg_name"],
            base_method=base_method,
            model_name=config["model_name"],
            device=config["device"],
            candidate_layers=list(config["candidate_layers"]),
            top_k=config.get("top_k", 1),
            probe_steps=config.get("probe_steps", 10),
            probe_lr=config.get("probe_lr", 1e-2),
            probe_init=config.get("probe_init", 1e-3),
            base_config=base_config,
        )

    def to_dict(self):
        fields = dict(self.__dict__)
        fields["base_config"] = dict(self.base_config or {})
        return fields

    def base_hparams(self):
        """Instantiate the base editor's HyperParams from this file's fields."""
        import importlib

        module_name, class_name = BASE_EDITORS[self.base_method][:2]
        hparams_cls = getattr(importlib.import_module(module_name), class_name)
        return hparams_cls(**self.base_config)


class _Modulation:
    """W * (1 + dH (x) dW), applied by hook rather than by rewriting W."""

    def __init__(self, module, scale, device, dtype):
        self.module = module
        out_features, in_features = module.weight.shape
        self.dh = (torch.randn(out_features, device=device, dtype=dtype) * scale).requires_grad_(True)
        self.dw = (torch.randn(in_features, device=device, dtype=dtype) * scale).requires_grad_(True)
        self.handle = module.register_forward_hook(self._hook)

    def _hook(self, module, args, output):
        x = args[0]
        extra = F.linear(x * self.dw.to(x.dtype), module.weight)
        return output + self.dh.to(output.dtype) * extra.to(output.dtype)

    def parameters(self):
        return [self.dh, self.dw]

    def fisher(self):
        """mean(dL/ddH ^ 2) + mean(dL/ddW ^ 2), the paper's Eq. 4."""
        scores = []
        for proxy in (self.dh, self.dw):
            if proxy.grad is None:
                scores.append(torch.zeros((), device=proxy.device))
            else:
                scores.append(proxy.grad.float().pow(2).mean())
        return float(scores[0] + scores[1])

    def remove(self):
        self.handle.remove()


def _edit_loss(model, tok, requests, device):
    """Cross-entropy of the new targets given their prompts."""
    total = 0.0
    for request in requests:
        prompt = request["prompt"].replace("{}", request["subject"])
        target = request["target_new"]
        if not target.startswith(" "):
            target = " " + target
        prompt_ids = tok.encode(prompt, add_special_tokens=True, return_tensors="pt").to(device)
        target_ids = tok.encode(target, add_special_tokens=False, return_tensors="pt").to(device)
        input_ids = torch.cat([prompt_ids, target_ids], dim=-1)
        logits = model(input_ids=input_ids, attention_mask=torch.ones_like(input_ids)).logits
        target_len = target_ids.shape[-1]
        predicted = logits[0, -target_len - 1 : -1].float()
        total = total + F.cross_entropy(predicted, target_ids[0])
    return total / len(requests)


def probe(model, tok, requests, hparams):
    """Rank candidate matrices by the Fisher Information of their modulations."""
    device = next(model.parameters()).device
    dtype = torch.float32

    frozen = [(param, param.requires_grad) for _, param in model.named_parameters()]
    for param, _ in frozen:
        param.requires_grad_(False)

    base_hparams = hparams.base_hparams()
    modulations = {}
    for layer in hparams.candidate_layers:
        module = capture.get_module(model, capture.module_name(base_hparams, layer))
        modulations[layer] = _Modulation(module, hparams.probe_init, device, dtype)

    proxies = [proxy for modulation in modulations.values() for proxy in modulation.parameters()]
    optimizer = torch.optim.Adam(proxies, lr=hparams.probe_lr)

    try:
        for step in range(hparams.probe_steps):
            loss = _edit_loss(model, tok, requests, device)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            print(f"[FiDAL] probe step {step + 1}/{hparams.probe_steps} loss={loss.item():.4f}")

        # Fisher is measured after probing, on the modulated model, as
        # Algorithm 1 line 9 specifies - hence one final backward pass
        # whose gradients are read but never applied.
        optimizer.zero_grad()
        _edit_loss(model, tok, requests, device).backward()
        scores = {layer: modulation.fisher() for layer, modulation in modulations.items()}
    finally:
        for modulation in modulations.values():
            modulation.remove()
        for param, requires_grad in frozen:
            param.requires_grad_(requires_grad)
        torch.cuda.empty_cache()

    ranked = sorted(scores, key=lambda layer: scores[layer], reverse=True)
    return ranked[: hparams.top_k], scores


def apply_fidal_to_model(
    model,
    tok,
    requests,
    hparams,
    copy=False,
    return_orig_weights=False,
    keep_original_weight=False,
    **kwargs,
):
    """Probe, pick the top-K matrices, then let the base editor write them."""
    import importlib

    if copy:
        model = deepcopy(model)

    requests = requests if isinstance(requests, (list, tuple)) else [requests]
    chosen, scores = probe(model, tok, requests, hparams)
    print(f"[FiDAL] Fisher scores {scores}")
    print(f"[FiDAL] editing layers {chosen} with {hparams.base_method}")

    base_hparams = hparams.base_hparams()
    base_hparams.layers = sorted(chosen)

    apply_module, apply_name = BASE_EDITORS[hparams.base_method][2:4]
    apply_fn = getattr(importlib.import_module(apply_module), apply_name)
    model, weights_copy = apply_fn(
        model, tok, list(requests), base_hparams,
        copy=False, return_orig_weights=return_orig_weights,
        keep_original_weight=keep_original_weight,
    )

    for request in requests:
        locations.record(
            "fidal",
            prompt=request.get("prompt"),
            subject=request.get("subject"),
            layers=sorted(chosen),
            fisher={int(layer): score for layer, score in scores.items()},
            base_method=hparams.base_method,
        )
    return model, weights_copy
