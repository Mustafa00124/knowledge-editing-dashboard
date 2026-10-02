"""CaKE: Circuit-aware Knowledge Editing (Yao et al. 2025), ported from
github.com/zjunlp/CaKE (edit_utils.py::cake at commit df528e1).

Multi-hop reasoning reads the first hop's answer in later layers, so an
edit written into one layer is often never picked up downstream. CaKE
trains a LoRA adapter on every attention and MLP projection of every layer,
on the edit prompt plus circuit-guided training data: rephrasings of the
edit and reasoning tasks that use the new fact as an intermediate step.

What is faithful to upstream:
  - LoRA on q/k/v/o and up/down/gate projections, rank 8, alpha 32,
    dropout 0.05 (create_lora_model).
  - Training text is "<question> <answer>" for the edit and its rephrasings
    and "<question> <answer>." for the reasoning examples, shuffled, the
    loss taken over the whole sequence (labels = input_ids).
  - 40 epochs, learning rate 1e-4, batch size 4, bf16, max length 256,
    with HF Trainer's default optimiser (AdamW without weight decay,
    linear decay to zero, gradient clipping at 1.0).
  - One edit per call; the adapter is merged into the weights afterwards
    (upstream unloads it after scoring each case, which is this runner's
    reset between edits).

What differs:
  - The circuit-guided data is not generated here: upstream releases only
    pre-generated files for MQuAKE (CF-3k, CF-3k-v2, T) and not the code
    that makes them, so CaKE runs only on those subsets
    (external/CaKE/datasets/*-cake.json, matched to our records by subject,
    prompt and target).
  - Upstream pads with the EOS token and trains on the padding too, which
    teaches the model to emit EOS. `mask_padding: true` excludes padding
    from the loss; the default keeps upstream's behaviour.
"""
import ast
import json
import os
import random
from dataclasses import asdict, dataclass, field
from typing import Dict, List

import yaml

EXP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(EXP_DIR))
CAKE_DATA_DIR = os.path.join(PROJECT_ROOT, "external", "CaKE", "datasets")
# Our MQuAKE file -> the CaKE release built from it.
CAKE_DATA = {
    "MQuAKE-CF-3k.json": "MQuAKE-CF-3k-cake.json",
    "MQuAKE-CF-3k-v2.json": "MQuAKE-CF-3k-v2-cake.json",
    "MQuAKE-T.json": "MQuAKE-T-cake.json",
}


@dataclass
class CaKEHyperParams:
    alg_name: str
    model_name: str
    device: int
    rank: int = 8
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    target_modules: List[str] = field(default_factory=lambda: [
        "q_proj", "v_proj", "k_proj", "o_proj", "up_proj", "down_proj", "gate_proj"])
    num_epochs: int = 40
    lr: float = 1e-4
    batch_size: int = 4
    max_length: int = 256
    mask_padding: bool = False
    seed: int = 0

    @classmethod
    def from_hparams(cls, path):
        with open(path) as handle:
            cfg = yaml.safe_load(handle)
        assert cfg.get("alg_name") == "CaKE", f"not a CaKE hparams file: {path}"
        return cls(**cfg)

    def to_dict(self):
        return asdict(self)


def _key(subject, prompt, target):
    return (str(subject).strip().lower(), str(prompt).strip().lower(), str(target).strip().lower())


def _parse(value):
    # The CaKE release stores nested fields as Python-literal strings.
    return ast.literal_eval(value) if isinstance(value, str) else value


_training_cache: Dict[str, Dict] = {}


def training_data(data_path):
    """(subject, prompt, target) -> CaKE's examples for that edit, or None
    when this dataset has no CaKE release."""
    name = CAKE_DATA.get(os.path.basename(data_path))
    if not name:
        return None
    if name in _training_cache:
        return _training_cache[name]
    path = os.path.join(CAKE_DATA_DIR, name)
    if not os.path.exists(path):
        raise FileNotFoundError(f"CaKE's training data is missing ({path}): download CaKE on the Downloads page")
    with open(path) as handle:
        items = json.load(handle)
    table = {}
    for item in items:
        rewrite = _parse(item["requested_rewrite"])[0]
        prompt = rewrite["prompt"].format(rewrite["subject"])
        table[_key(rewrite["subject"], prompt, rewrite["target_new"]["str"])] = rewrite
    _training_cache[name] = table
    return table


def _examples(rewrite, prompt, target, rng):
    case = [f"{prompt} {target}"]
    case += [f"{r['question']} {r['answer']}" for r in rewrite.get("rephrase_prompt", [])]
    learning = [f"{r['question']} {r['answer']}." for r in rewrite.get("learning_prompt", [])]
    rng.shuffle(case)
    rng.shuffle(learning)
    return case + learning


def apply_cake_to_model(model, tok, requests, hparams, copy=False, return_orig_weights=False, **kwargs):
    """One edit: train a LoRA adapter on its CaKE examples, then merge it.
    run_experiment.py sets hparams.data_path, which picks the CaKE file."""
    import torch
    from peft import LoraConfig, TaskType, get_peft_model
    from torch.utils.data import DataLoader

    request = requests[0]
    table = training_data(getattr(hparams, "data_path", ""))
    if table is None:
        raise ValueError(f"CaKE has training data only for {', '.join(CAKE_DATA)}")
    rewrite = table.get(_key(request["subject"], request["prompt"], request["target_new"]))
    if rewrite is None:
        raise ValueError(f"no CaKE training data for the edit {request['prompt']!r} -> {request['target_new']!r}")

    rng = random.Random(hparams.seed)
    texts = _examples(rewrite, request["prompt"], request["target_new"], rng)
    batch = tok(texts, padding=True, truncation=True, max_length=hparams.max_length, return_tensors="pt")
    labels = batch["input_ids"].clone()
    if hparams.mask_padding:
        labels[batch["attention_mask"] == 0] = -100

    # The edit protocols restore weights between groups, so hand back the
    # pre-edit value of every projection the merged adapter will change.
    # Kept on the CPU: with all seven projections this is most of the model.
    originals = {}
    if return_orig_weights:
        suffixes = tuple(f"{module}.weight" for module in hparams.target_modules)
        originals = {name: param.detach().to("cpu", copy=True)
                     for name, param in model.named_parameters() if name.endswith(suffixes)}

    peft_model = get_peft_model(model, LoraConfig(
        r=hparams.rank, lora_alpha=hparams.lora_alpha, lora_dropout=hparams.lora_dropout,
        bias="none", target_modules=list(hparams.target_modules), task_type=TaskType.CAUSAL_LM))
    peft_model.enable_input_require_grads()
    # The optimiser HF Trainer uses by default, which is what upstream ran:
    # AdamW without weight decay, linear decay to zero, gradient clipping 1.0.
    from transformers import get_linear_schedule_with_warmup

    optimizer = torch.optim.AdamW((p for p in peft_model.parameters() if p.requires_grad),
                                  lr=hparams.lr, weight_decay=0.0)
    rows = list(range(len(texts)))
    steps_per_epoch = -(-len(rows) // hparams.batch_size)
    schedule = get_linear_schedule_with_warmup(optimizer, 0, steps_per_epoch * hparams.num_epochs)
    trainable = [p for p in peft_model.parameters() if p.requires_grad]
    device = next(peft_model.parameters()).device
    peft_model.train()
    generator = torch.Generator().manual_seed(hparams.seed)
    import loss_log
    fact_index, step = loss_log.new_fact(), 0
    for _ in range(hparams.num_epochs):
        for index in DataLoader(rows, batch_size=hparams.batch_size, shuffle=True, generator=generator):
            with torch.autocast(device_type=device.type, dtype=torch.bfloat16):
                loss = peft_model(input_ids=batch["input_ids"][index].to(device),
                                  attention_mask=batch["attention_mask"][index].to(device),
                                  labels=labels[index].to(device)).loss
            loss.backward()
            step += 1
            loss_log.record("train", step, loss, fact=fact_index)
            torch.nn.utils.clip_grad_norm_(trainable, 1.0)
            optimizer.step()
            schedule.step()
            optimizer.zero_grad()
    peft_model.eval()
    merged = peft_model.merge_and_unload()
    return merged, originals
