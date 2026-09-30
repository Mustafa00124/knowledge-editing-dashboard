"""
Checkpointed fork of EasyEdit's FT training loop.

Forked from external/EasyEdit/easyeditor/models/ft/ft_main.py::execute_ft
because the stock function offers no way to pause mid-training. Three
deliberate deviations from the original, everything else is unchanged:

  1. Dropped the T5 / ChatGLM special-case branches. Not needed for a
     decoder-only Qwen model, and cutting them makes this fork a lot
     shorter than the original to read.
  2. Removed the epoch-level early stop (`if loss_meter.avg < 1e-2: break`).
     We want the full step-scaling curve out to `num_steps`, not an early
     exit the moment average loss dips below 0.01.
  3. Added a checkpoint callback, and the function no longer restores the
     model to its pre-edit state before returning (the original computes a
     "delta" and hands it back for the caller to re-apply; here we just
     leave the live, progressively-edited model in place — there's only
     ever one caller and it wants the trained model, not a delta).

Note the per-*batch* guard `if loss.item() >= 1e-2: backward(); step()` is
kept as-is (still stock EasyEdit behavior): once a batch's loss drops below
that threshold, gradient updates stop being applied for it. With
batch_size == ds_size (one batch per step, see run_experiment.py) this
means training effectively freezes once the model has memorized the batch
— checkpoints after that point will show flat metrics, not further
drift/forgetting. That's expected, not a bug; it's what tells you "this is
the step count where it converged."
"""
from typing import Callable, Dict, List, Optional

import torch
from torch.nn import CrossEntropyLoss
from transformers import AutoModelForCausalLM, AutoTokenizer

from easyeditor.util.device import normalize_device
from easyeditor.models.ft.ft_hparams import FTHyperParams
from easyeditor.models.ft.ft_main import chunks, AverageMeter


def execute_ft_checkpointed(
    model: AutoModelForCausalLM,
    tok: AutoTokenizer,
    requests: List[Dict],
    hparams: FTHyperParams,
    checkpoint_every: int,
    on_checkpoint: Callable[[int, Optional[float]], None],
) -> None:
    """
    Runs FT training on `model` in place for `hparams.num_steps` steps.
    Calls `on_checkpoint(step, loss)` once before training starts
    (step=0, loss=None) and again after every `checkpoint_every` steps
    (loss = that step's training loss). model.eval() is set before the
    call and model.train() restored right after — the callback itself
    just needs to run its forward passes under torch.no_grad().
    The callback closes over the model/tokenizer/requests it needs (see
    run_experiment.py) rather than taking them as arguments here.
    """
    device = normalize_device(getattr(hparams, "device", None))
    requests = [dict(r) for r in requests]
    for request in requests:
        if request["target_new"] != " ":
            request["target_new"] = " " + request["target_new"]

    weights = {
        n: p
        for n, p in model.named_parameters()
        for layer in hparams.layers
        if hparams.rewrite_module_tmp.format(layer) in n
    }
    weights_copy = {k: v.detach().clone() for k, v in weights.items()}
    print(f"[FT] Tuning weights: {list(weights.keys())}")

    texts = [r["prompt"] for r in requests]
    targets = [r["target_new"] for r in requests]

    opt = torch.optim.Adam(
        list(weights.values()), lr=hparams.lr, weight_decay=hparams.weight_decay
    )
    for name, w in model.named_parameters():
        w.requires_grad = name in weights

    on_checkpoint(0, loss=None)
    model.train()

    loss_meter = AverageMeter()
    for step in range(1, hparams.num_steps + 1):
        loss_meter.reset()

        for txt, tgt in zip(
            chunks(texts, hparams.batch_size), chunks(targets, hparams.batch_size)
        ):
            inputs = tok(txt, return_tensors="pt", padding=True).to(device)
            target_ids = tok(tgt, return_tensors="pt", padding=True)["input_ids"].to(device)

            if hparams.objective_optimization == "prompt_last":
                last_token_inds = inputs["attention_mask"].sum(dim=1) - 1
                if tok.unk_token_id is not None:
                    loss_mask = torch.ne(target_ids, tok.unk_token_id)
                else:
                    loss_mask = torch.ones_like(target_ids, dtype=torch.bool)
            elif hparams.objective_optimization == "target_new":
                inputs_targets = [t + g for t, g in zip(txt, tgt)]
                inputs_targets = tok(inputs_targets, return_tensors="pt", padding=True).to(device)
                num_prompt_toks = [int((i != tok.pad_token_id).sum()) for i in inputs["input_ids"].cpu()]
                num_pad_toks = [int((i == tok.pad_token_id).sum()) for i in inputs_targets["input_ids"].cpu()]
                prompt_len = [x + y for x, y in zip(num_pad_toks, num_prompt_toks)]
                prompt_target_len = inputs_targets["input_ids"].size(1)
                label_mask = torch.tensor(
                    [[False] * length + [True] * (prompt_target_len - length) for length in prompt_len]
                ).to(device)
            else:
                raise NotImplementedError(hparams.objective_optimization)

            opt.zero_grad()
            bs = inputs["input_ids"].shape[0]

            if hparams.objective_optimization == "prompt_last":
                probs = torch.nn.functional.log_softmax(
                    model(**inputs).logits[torch.arange(bs), last_token_inds], dim=-1
                )
                loss = -(torch.gather(probs, 1, target_ids) * loss_mask).sum(1) / loss_mask.sum(1)
                loss = loss.mean()
            else:  # target_new
                logits = model(**inputs_targets).logits
                shift_logits = logits[..., :-1, :].contiguous()
                shift_labels = inputs_targets["input_ids"][..., 1:].contiguous()
                loss_fct = CrossEntropyLoss(reduction="none")
                loss = loss_fct(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1))
                loss = loss.view(bs, -1)
                loss = (loss * label_mask[:, 1:]).sum(1) / label_mask[:, 1:].sum(1)
                loss = loss.mean()

            loss_meter.update(loss.item(), n=bs)

            if loss.item() >= 1e-2:
                loss.backward()
                opt.step()

            if isinstance(hparams.norm_constraint, float):
                eps = hparams.norm_constraint
                with torch.no_grad():
                    for k, v in weights.items():
                        v[...] = torch.clamp(v, min=weights_copy[k] - eps, max=weights_copy[k] + eps)

        if step % checkpoint_every == 0 or step == hparams.num_steps:
            model.eval()
            on_checkpoint(step, loss=loss_meter.avg)
            model.train()
