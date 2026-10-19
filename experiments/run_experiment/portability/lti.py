"""LTI, "Learn to Inference" (Zhang et al., "Uncovering Overfitting in Large
Language Model Editing", ICLR 2025, arXiv:2410.07819), ported from
github.com/Acruxos/EVOKE (experiment/memit_lti/, MIT licence).

Edited models overfit: they push the new target up on the edit prompt
itself, but a question that needs the new fact as one step of a longer
inference still gets the old answer. The unedited model does not have that
problem when the new fact is simply written in its context: it reasons
with it. LTI makes the weight edit imitate that. MEMIT's target vector v*
is fitted so that the edited model, *without* the fact in context,
reproduces the unedited model *with* the fact in context ("Imagine that
<new fact>"):

    loss = nll_factor      * NLL(new target | edit prompt)
         + last_kl_factor  * KL at the output, on the target tokens and
                             on "<subject> is a"
         + mid_kl_factor   * KL of the logit lens at a middle layer, at
                             the subject's last token
         + v_weight_decay  * |delta| / |v_init|^2

Everything else - the key computation, the covariance-weighted closed-form
update, the layers - is the base editor's own (MEMIT by default, or
AlphaEdit, whose target-vector step is the same function). Only the
target-vector objective is replaced, by patching the base editor module's
compute_z for the duration of one call.

What is faithful to upstream (memit_lti/compute_z.py, context.py):
  - The context prefix "Imagine that {new fact}\\n" (get_edit_prefix).
  - The three loss terms and their weights; the in-context targets are
    computed once, before optimisation, from the same model.
  - The "<subject> is a" prompt is not prefixed, so its term holds the
    subject's general description where the unedited model had it, in
    place of MEMIT's own kl_factor term (which LTI drops).
  - constr_pos "subject": the middle-layer constraint at the subject's
    last token (every upstream hparams file uses it).

What differs:
  - Positions in the in-context run. Upstream reads the prefixed run's
    logits and hidden states at the token positions of the *un-prefixed*
    prompts, which lands inside the "Imagine that ..." prefix; here every
    position is recomputed for the prefixed prompt, so the target tokens
    and the subject are compared with themselves.
  - midlayers may list several layers; their KL terms are averaged.
    Upstream lists one, so the two agree on every shipped config.
  - Only the base editors whose target step is compute_z (MEMIT,
    AlphaEdit). Upstream's ROME-LTI rewrites ROME's compute_v and is not
    ported.
"""
import importlib
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass, field

import numpy as np
import torch
import torch.nn.functional as F

from . import base

OWN_KEYS = {"alg_name", "model_name", "device", "midlayers", "constr_pos", "mid_kl_factor",
            "last_kl_factor", "nll_factor", "context_template"}
PATCHED_MODULES = {"memit": "easyeditor.models.memit.memit_main",
                   "alphaedit": "easyeditor.models.alphaedit.AlphaEdit_main"}


@dataclass
class LTIHyperParams:
    alg_name: str
    model_name: str
    device: int
    base_method: str
    midlayers: list = field(default_factory=list)
    constr_pos: str = "subject"
    mid_kl_factor: float = 0.0425
    last_kl_factor: float = 0.0725
    nll_factor: float = 0.125
    context_template: str = "Imagine that {fact}\n"
    base_config: dict = None
    max_length: int = 40  # read by EasyEdit's evaluator

    @classmethod
    def from_hparams(cls, path):
        own, base_method, base_config = base.load_config(path, "LTI", OWN_KEYS)
        if base_method not in PATCHED_MODULES:
            raise ValueError(f"LTI replaces compute_z, which only {sorted(PATCHED_MODULES)} use; "
                             f"base_method {base_method!r} is not supported")
        if own.get("constr_pos", "subject") != "subject":
            raise ValueError("only constr_pos: subject is implemented (every upstream config uses it)")
        base_config.update(model_name=own["model_name"], device=own["device"])
        return cls(base_method=base_method, base_config=base_config, **own)

    def to_dict(self):
        fields_ = dict(self.__dict__)
        fields_["base_config"] = dict(self.base_config or {})
        return fields_


def _target_spans(attention_mask, lengths):
    """[start, end) of the last `length` real tokens of each row (right padding,
    as EasyEdit's compute_z assumes)."""
    spans = []
    for row, length in zip(attention_mask, lengths):
        end = int(row.sum())
        spans.append((end - length, end))
    return spans


def _logit_lens(hidden, ln_f, lm_w, lm_b):
    return torch.log_softmax(ln_f(hidden) @ lm_w.to(hidden.device) + lm_b.to(hidden.device), dim=-1)


def compute_z_lti(model, tok, request, hparams, layer, context_templates, lti):
    """compute_z's signature and contract (the target vector v* at `layer`),
    with LTI's objective. `hparams` is the base editor's; `lti` the LTI ones."""
    from easyeditor.models.memit.compute_z import find_fact_lookup_idx
    from easyeditor.util import nethook
    from easyeditor.util.device import get_module_device, normalize_device

    device = normalize_device(getattr(hparams, "device", None))
    lm_w = nethook.get_module(model, hparams.lm_head_module).weight.T
    ln_f = nethook.get_module(model, hparams.ln_f_module)
    try:
        lm_b = nethook.get_parameter(model, f"{hparams.lm_head_module}.bias")
    except LookupError:
        lm_b = next(model.parameters()).new_zeros(model.config.vocab_size)

    print("Computing right vector (v)")
    rewrite_module_name = hparams.layer_module_tmp.format(layer)
    rewrite_device = get_module_device(nethook.get_module(model, rewrite_module_name), device)
    subject = request["subject"]

    target_ids = tok.encode(request["target_new"], return_tensors="pt", add_special_tokens=False).to(device)[0]
    if target_ids[0] == tok.bos_token_id or target_ids[0] == tok.unk_token_id:
        target_ids = target_ids[1:]
    rewriting_prompts = [context.format(request["prompt"]) + tok.decode(target_ids[:-1])
                         for context_types in context_templates for context in context_types]
    kl_prompts = ["{} is a"]
    all_prompts = rewriting_prompts + kl_prompts
    lengths = [len(target_ids)] * len(rewriting_prompts) + [1] * len(kl_prompts)

    # The new fact as the unedited model would read it in context. Braces
    # are escaped because the prompts are .format()ed with the subject.
    fact = base.fact_sentence({**request, "target_new": request["target_new"].strip()})
    prefix = lti.context_template.format(fact=fact).replace("{", "{{").replace("}", "}}")
    context_prompts = [prefix + p for p in rewriting_prompts] + kl_prompts

    def encode(prompts):
        with base.padding(tok, "right"):
            return tok([p.format(subject) for p in prompts], return_tensors="pt", padding=True).to(device)

    def lookups(prompts):
        return [find_fact_lookup_idx(p, subject, tok, hparams.fact_token, verbose=False) for p in prompts]

    input_tok, context_tok = encode(all_prompts), encode(context_prompts)
    spans = _target_spans(input_tok["attention_mask"], lengths)
    context_spans = _target_spans(context_tok["attention_mask"], lengths)
    lookup_idxs = [find_fact_lookup_idx(p, subject, tok, hparams.fact_token, verbose=(i == 0))
                   for i, p in enumerate(all_prompts)]
    context_lookup_idxs = lookups(context_prompts)

    rewriting_targets = torch.tensor(-100, device=device).repeat(len(rewriting_prompts), *input_tok["input_ids"].shape[1:])
    for i in range(len(rewriting_prompts)):
        start, end = spans[i]
        rewriting_targets[i, start:end] = target_ids

    mid_names = [hparams.layer_module_tmp.format(mid) for mid in lti.midlayers]

    def gather_last(logits, spans_):
        return torch.log_softmax(torch.cat([logits[i, s:e] for i, (s, e) in enumerate(spans_)], dim=0).float(), dim=-1)

    def gather_mid(trace, idxs):
        out = []
        for name in mid_names:
            hidden = nethook.get_hidden_state(trace[name].output)
            picked = torch.stack([hidden[i, idx] for i, idx in enumerate(idxs)], dim=0)
            out.append(_logit_lens(picked, ln_f, lm_w, lm_b).float())
        return out

    # Targets: the unedited model reasoning with the fact in context.
    with torch.no_grad(), nethook.TraceDict(module=model, layers=mid_names, retain_output=True) as trace:
        context_logits = model(**context_tok).logits
        target_last = gather_last(context_logits, context_spans)
        target_mid = gather_mid(trace, context_lookup_idxs)

    loss_layer = max(hparams.v_loss_layer, layer)
    print(f"Rewrite layer is {layer}")
    print(f"Tying optimization objective to {loss_layer}")
    hidden_size = getattr(model.config, "n_embd", None) or model.config.hidden_size
    delta = torch.zeros((hidden_size,), requires_grad=True, device=rewrite_device)
    target_init = None

    def edit_output_fn(cur_out, cur_layer):
        nonlocal target_init
        if cur_layer == rewrite_module_name:
            layer_output = nethook.get_hidden_state(cur_out)
            delta_for_hidden = delta.to(device=layer_output.device, dtype=layer_output.dtype)
            if target_init is None:
                print("Recording initial value of v*")
                target_init = layer_output[0, lookup_idxs[0]].detach().clone()
            for i, idx in enumerate(lookup_idxs):
                layer_output[i, idx, :] += delta_for_hidden
            return nethook.replace_hidden_state(cur_out, layer_output)
        return cur_out

    opt = torch.optim.Adam([delta], lr=hparams.v_lr)
    nethook.set_requires_grad(False, model)
    for it in range(hparams.v_num_grad_steps):
        opt.zero_grad()
        with nethook.TraceDict(module=model, layers=[rewrite_module_name] + mid_names,
                               retain_input=False, retain_output=True, edit_output=edit_output_fn) as trace:
            logits = model(**input_tok).logits
            current_mid = gather_mid(trace, lookup_idxs)
        log_probs = torch.log_softmax(logits.float(), dim=2)
        picked = torch.gather(log_probs[:len(rewriting_prompts)], 2,
                              torch.where(rewriting_targets != -100, rewriting_targets, 0).unsqueeze(2)).squeeze(2)
        mask = (rewriting_targets != -100).float()
        nll_each = -(picked * mask).sum(1) / target_ids.size(0)
        nll_loss = lti.nll_factor * nll_each.mean()
        last_kl = lti.last_kl_factor * F.kl_div(target_last, gather_last(logits, spans),
                                                log_target=True, reduction="batchmean")
        mid_kl = lti.mid_kl_factor * torch.stack([
            F.kl_div(t, c, log_target=True, reduction="batchmean") for t, c in zip(target_mid, current_mid)
        ]).mean() if mid_names else torch.zeros((), device=nll_loss.device)
        weight_decay = hparams.v_weight_decay * (torch.norm(delta) / torch.norm(target_init) ** 2)
        kl_total = last_kl + mid_kl.to(last_kl.device)
        loss = nll_loss + kl_total.to(nll_loss.device) + weight_decay.to(nll_loss.device)
        # The line loss_log.py reads; the two KL terms are reported together.
        print(f"loss {np.round(loss.item(), 3)} = {np.round(nll_loss.item(), 3)} + "
              f"{np.round(kl_total.item(), 3)} + {np.round(weight_decay.item(), 3)} "
              f"avg prob of [{request['target_new']}] {torch.exp(-nll_each).mean().item()}")
        if loss < 5e-2 or it == hparams.v_num_grad_steps - 1:
            break
        loss.backward()
        opt.step()
        max_norm = hparams.clamp_norm_factor * target_init.norm()
        if delta.norm() > max_norm:
            with torch.no_grad():
                delta[...] = delta * max_norm / delta.norm()

    target = target_init + delta.to(device=target_init.device, dtype=target_init.dtype)
    print(f"Init norm {target_init.norm()} | Delta norm {delta.norm()} | Target norm {target.norm()}")
    return target


@contextmanager
def _lti_objective(base_method, lti):
    module = importlib.import_module(PATCHED_MODULES[base_method])
    original = module.compute_z

    def compute_z(model, tok, request, hparams, layer, context_templates, *args, **kwargs):
        return compute_z_lti(model, tok, request, hparams, layer, context_templates, lti)

    module.compute_z = compute_z
    try:
        yield
    finally:
        module.compute_z = original


def apply_lti_to_model(model, tok, requests, hparams, copy=False, return_orig_weights=False, **kwargs):
    if copy:
        model = deepcopy(model)
    requests = requests if isinstance(requests, (list, tuple)) else [requests]
    weights_copy = {}
    base_hparams = base.base_hparams(hparams.base_method, hparams.base_config)
    with _lti_objective(hparams.base_method, hparams):
        model = base.apply_base(hparams.base_method, model, tok, requests, base_hparams,
                                return_orig_weights, weights_copy)
    return model, weights_copy
