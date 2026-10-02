"""FiNE: fine-grained neuron-level knowledge editing (ICLR 2025, arXiv:2503.01090).

Ported from github.com/opanhw/FiNE (easyeditor/models/fine/), keeping the
algorithm intact and replacing only the parts that cannot run here:

  - Activation capture. Upstream calls model.set_get_activations() and
    reads model.activations, which exist only in the patched
    transformers modeling files their repo inherits from MM_Neurons, and
    only for Llama and GPT-J. capture.FFNActivations hooks the module
    hparams.rewrite_module_tmp already names, which is the same tensor
    and works for every model registered in run_experiment.py.
  - Device handling. Upstream hardcodes .cuda(); everything here follows
    the model's own device, since jobs get one GPU as cuda:0 but the
    hparams still carry a device index.
  - Architecture branching. Upstream branches on model.config.model_type
    to pick between transformer.h.{}.mlp.fc_out and
    model.layers.{}.mlp.down_proj; both are already in hparams.

The algorithm itself, unchanged: for each token the model currently
predicts where the new target should go, score every neuron in every
unfrozen layer by

    c(i, l) = a_l,i * (W_out^l[:, i] . U[:, t])

the neuron's activation times how much its output direction projects
onto the unembedding of that token. Take the top `neuron_num` neurons
per token position, pooled across all layers at once - which is where
the per-fact dynamic localisation comes from, since nothing constrains
the winners to one layer. Then learn a delta vector per selected neuron
by gradient descent on the FFN output, under an NLL term for the target,
a KL term pinning the prefix distribution, a penalty term discouraging
the target at the final position, and an L2 norm term.

Only the selected rows of the down-projection change: roughly 20 neurons
per fact against ROME/MEMIT's whole matrix, which is why upstream reports
it running 4-6x faster than they do.
"""
from copy import deepcopy
from dataclasses import dataclass, field

import numpy as np
import torch
import torch.nn.functional as F
import yaml

from . import capture, locations
import loss_log


@dataclass
class FiNEHyperParams:
    alg_name: str
    model_name: str
    device: int
    rewrite_module_tmp: str
    layer_module_tmp: str
    mlp_module_tmp: str
    attn_module_tmp: str
    ln_f_module: str
    lm_head_module: str
    # Method knobs, upstream's hparams/FINE/*.yaml values as defaults.
    epochs: int = 50
    lr: float = 1e-3
    alpha: float = 1.0      # KL term, holds the prefix distribution still
    beta: float = 10.0      # penalty term, discourages target repetition
    gamma: float = 0.1      # L2 on the deltas
    neuron_num: int = 5     # per target token, pooled over all layers
    last_layer: int = 3     # top N layers frozen, never selected
    early_stop_prob: float = 0.9
    add_eos: bool = False
    layer: int = None       # ablation: confine selection to one layer
    random: bool = False    # ablation: pick neurons at random
    # Upstream allocates the learnable deltas in bfloat16. float32 is the
    # default here because Adam at lr=1e-3 on bf16 parameters rounds a
    # large share of each update away; set to "bfloat16" to reproduce
    # their numerics exactly.
    delta_dtype: str = "float32"
    max_length: int = 40
    model_parallel: bool = False
    fp16: bool = False

    @classmethod
    def from_hparams(cls, path):
        if not str(path).endswith(".yaml"):
            path = f"{path}.yaml"
        with open(path) as f:
            config = yaml.safe_load(f)
        assert config.get("alg_name") == "FiNE", f"not a FiNE hparams file: {path}"
        return cls(**config)

    def to_dict(self):
        return dict(self.__dict__)


def score_neurons(model, hparams, activations, token_ids, layers):
    """c(i, l) = activation * (down_proj column . unembedding column).

    activations: (layers, positions, d_ff) for the positions being scored.
    Returns (positions, layers, d_ff) scores.
    """
    unembed = capture.unembedding(model)
    scores = []
    for position, token_id in enumerate(token_ids):
        target_direction = unembed[token_id].float()
        per_layer = []
        for index, layer in enumerate(layers):
            weight = capture.get_module(model, capture.module_name(hparams, layer)).weight
            # weight is (hidden, d_ff) for every nn.Linear FFN output
            # projection, so weight.T @ direction gives one scalar per
            # neuron: how much that neuron pushes toward this token.
            projection = (weight.T.float() @ target_direction.to(weight.device))
            per_layer.append(activations[index, position].float().to(projection.device) * projection)
        scores.append(torch.stack(per_layer))
    return torch.stack(scores)


def select_neurons(scores, neuron_num, layers, generator=None, random_choice=False):
    """Top-k neurons per position, pooled across layers -> [(layer, neuron)]."""
    selected = []
    positions, n_layers, d_ff = scores.shape
    for position in range(positions):
        if random_choice:
            layer_index = torch.randint(0, n_layers, (neuron_num,), generator=generator)
            neuron = torch.randint(0, d_ff, (neuron_num,), generator=generator)
            selected.extend((layers[int(l)], int(n)) for l, n in zip(layer_index, neuron))
            continue
        flat = scores[position].flatten()
        _, top = torch.topk(flat, neuron_num)
        for index in top.tolist():
            selected.append((layers[index // d_ff], index % d_ff))
    return selected


def apply_fine_to_model(
    model,
    tok,
    request,
    hparams,
    copy=False,
    return_orig_weights=False,
    keep_original_weight=False,
    **kwargs,
):
    """Locate and edit one fact's neurons. EasyEdit-compatible signature."""
    from easyeditor.util import nethook

    if copy:
        model = deepcopy(model)

    requests = request if isinstance(request, (list, tuple)) else [request]
    weights_copy = {}
    for single in requests:
        touched = _execute_fine(model, tok, single, hparams, nethook)
        for name, original in touched.items():
            weights_copy.setdefault(name, original)

    if not keep_original_weight and not return_orig_weights:
        weights_copy = {}
    return model, weights_copy


def _execute_fine(model, tok, request, hparams, nethook):
    device = next(model.parameters()).device
    request = deepcopy(request)
    if request["target_new"] != " ":
        request["target_new"] = " " + request["target_new"]
    if "{}" not in request["prompt"]:
        assert request["subject"] in request["prompt"], (
            f"subject {request['subject']!r} does not occur in prompt {request['prompt']!r}"
        )
        request["prompt"] = request["prompt"].replace(request["subject"], "{}")

    prompt = request["prompt"].format(request["subject"])
    print(f"[FiNE] {prompt} -> {request['target_new']}")

    # Llama-2's tokenizer emits a leading-space token upstream strips;
    # every other model keeps the space, which is what makes the target
    # tokenise as a continuation rather than a sentence start.
    target_text = request["target_new"].strip() if "llama-2" in hparams.model_name.lower() else request["target_new"]
    target_ids = tok.encode(target_text, add_special_tokens=False, return_tensors="pt")
    if hparams.add_eos:
        target_ids = torch.cat([target_ids, torch.tensor([[tok.eos_token_id]])], dim=-1)
    target_len = target_ids.shape[-1]

    prompt_ids = tok.encode(prompt, add_special_tokens=True, return_tensors="pt")
    if getattr(model.config, "model_type", "") == "gptj":
        # GPT-J's tokenizer adds no BOS; upstream prepends one so the
        # first prompt token has something to attend to.
        prompt_ids = torch.cat([torch.tensor([[tok.eos_token_id]], dtype=torch.long), prompt_ids], dim=-1)
    input_ids = torch.cat([prompt_ids, target_ids], dim=-1).to(device)
    attention_mask = torch.ones_like(input_ids)

    model.eval()
    frozen = [(param, param.requires_grad) for _, param in model.named_parameters()]
    for param, _ in frozen:
        param.requires_grad_(False)

    layers = list(range(capture.num_layers(model) - hparams.last_layer))
    if hparams.layer is not None:
        layers = [hparams.layer]

    with torch.no_grad(), capture.FFNActivations(model, hparams, layers) as acts:
        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
        activations = acts.stack()[:, 0, -target_len - 1 : -1, :]

    original_distribution = outputs.logits[0, : -target_len - 1]
    predicted_ids = outputs.logits[0, -target_len - 1 : -1].argmax(-1)

    generator = torch.Generator(device="cpu").manual_seed(0) if hparams.random else None
    scores = score_neurons(model, hparams, activations, predicted_ids.tolist(), layers)
    neurons = select_neurons(scores, hparams.neuron_num, layers,
                             generator=generator, random_choice=hparams.random)
    del scores

    by_layer = {}
    for index, (layer, neuron) in enumerate(neurons):
        entry = by_layer.setdefault(layer, {"neurons": [], "slots": []})
        entry["neurons"].append(neuron)
        entry["slots"].append(index)

    print(f"[FiNE] editing {len(neurons)} neurons across layers {sorted(by_layer)}")

    delta_dtype = getattr(torch, hparams.delta_dtype)
    deltas = torch.zeros(len(neurons), model.config.hidden_size,
                         dtype=delta_dtype, device=device).requires_grad_(True)
    optimizer = torch.optim.Adam([deltas], lr=hparams.lr)

    handles = []

    def make_hook(layer):
        entry = by_layer[layer]
        neuron_index = torch.tensor(entry["neurons"], device=device)
        slot_index = torch.tensor(entry["slots"], device=device)

        def hook(module, args, output):
            activation = args[0][..., neuron_index].to(deltas.dtype)
            return output + (activation @ deltas[slot_index]).to(output.dtype)

        return hook

    for layer in by_layer:
        module = capture.get_module(model, capture.module_name(hparams, layer))
        handles.append(module.register_forward_hook(make_hook(layer)))

    try:
        for epoch in range(hparams.epochs):
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits[0, -target_len - 1 : -1].float()

            nll = F.nll_loss(F.log_softmax(logits, dim=-1),
                             target_ids[0].to(logits.device), reduction="none").max()
            kl = F.kl_div(F.log_softmax(outputs.logits[0, : -target_len - 1], dim=-1),
                          F.softmax(original_distribution, dim=-1),
                          reduction="batchmean") * hparams.alpha
            final = F.softmax(outputs.logits[0, -1].float(), dim=-1)[target_ids[0].to(logits.device)]
            penalty = (-torch.log(1 - final)).max() * hparams.beta
            norm = torch.norm(deltas, p=2) * hparams.gamma
            loss = nll + norm + kl + penalty

            print(f"[FiNE] epoch {epoch + 1} loss={loss.item():.4f} nll={nll.item():.4f} "
                  f"kl={kl.item():.4f} pen={penalty.item():.4f} norm={norm.item():.4f}")
            if epoch == 0:
                fact_index = loss_log.new_fact()
            loss_log.record("train", epoch + 1, loss, fact=fact_index, nll=nll.item(), kl=kl.item())

            stop = hparams.early_stop_prob is not None and nll < -np.log(hparams.early_stop_prob)
            if stop or bool(torch.isnan(nll)):
                break

            loss.backward()
            optimizer.step()
            optimizer.zero_grad()
    finally:
        for handle in handles:
            handle.remove()

    weights_copy = {}
    with torch.no_grad():
        for layer, entry in by_layer.items():
            name = f"{capture.module_name(hparams, layer)}.weight"
            weight = nethook.get_parameter(model, name)
            weights_copy[name] = weight.detach().clone()
            for neuron, slot in zip(entry["neurons"], entry["slots"]):
                # weight is (hidden, d_ff): a neuron owns one column, and
                # its delta is the hidden-space direction that column adds.
                weight[:, neuron] += deltas[slot].detach().to(weight.dtype)

    for param, requires_grad in frozen:
        param.requires_grad_(requires_grad)

    locations.record(
        "fine",
        prompt=request["prompt"],
        subject=request.get("subject"),
        layers=sorted(by_layer),
        neurons=[[int(layer), int(neuron)] for layer, neuron in neurons],
        neurons_per_layer={int(layer): len(entry["neurons"]) for layer, entry in by_layer.items()},
    )
    return weights_copy
