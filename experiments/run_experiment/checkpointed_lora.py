"""
Checkpointed fork of EasyEdit's LoRA training loop.

Forked from external/EasyEdit/easyeditor/models/lora/lora_main.py::execute_lora
for the exact same reason checkpointed_ft.py forks execute_ft: the stock
function trains for the full `hparams.num_steps` in one uninterruptible
loop and only returns at the end - no hook to pause, evaluate, and
resume. Deviations from the original, everything else (the per-batch loss
computation, the chunking) is unchanged:

  1. Dropped the T5 special-case branch (`if 't5' in hparams.model_name`).
     Not needed for our decoder-only models, same rationale as
     checkpointed_ft.py's fork.
  2. The PEFT wrapping (`get_peft_model`) happens in run_experiment.py,
     not in here - this function is handed an *already-wrapped*
     peft_model and just trains it. Kept out of this fork because
     wrapping only needs to happen once, before the first checkpoint (at
     step 0), whereas this function is the training loop that runs
     between checkpoints.
  3. Added the checkpoint callback (same signature/contract as
     checkpointed_ft.py's: `on_checkpoint(step, loss)`, called once
     before training at step 0 with loss=None, then again after every
     `checkpoint_every` steps).
  4. The early-stop-on-low-loss check upstream already has commented out
     (`# if loss_meter.avg < 1e-3: break`) - nothing to remove, and this
     fork doesn't add one either, for the same reason checkpointed_ft.py
     doesn't: the whole point is the full step-scaling curve.

Note there's no "restore pre-edit weights" step here (unlike upstream,
which doesn't have one for LoRA either - `execute_lora` already just
returns the live peft_model, matching this project's convention of
handing back the trained model directly rather than a delta to reapply).
"""
from typing import Callable, Dict, List, Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from easyeditor.models.lora.lora_hparams import LoRAHyperParams
from easyeditor.models.lora.lora_main import chunks, AverageMeter
import loss_log


def execute_lora_checkpointed(
    peft_model,
    tok: AutoTokenizer,
    requests: List[Dict],
    hparams: LoRAHyperParams,
    checkpoint_every: int,
    on_checkpoint: Callable[[int, Optional[float]], None],
) -> None:
    """Trains `peft_model` (already wrapped via get_peft_model - see
    run_experiment.py) in place for `hparams.num_steps` steps. Calls
    on_checkpoint(0, loss=None) once before training, then again every
    `checkpoint_every` steps with that interval's average loss."""
    mask_token = -100
    device = next(peft_model.parameters()).device
    requests = [dict(r) for r in requests]
    for request in requests:
        if "{}" in request["prompt"]:
            request["prompt"] = request["prompt"].format(request["subject"])

    texts = [r["prompt"] for r in requests]
    targets = [r["target_new"] for r in requests]

    opt = torch.optim.Adam(peft_model.parameters(), lr=hparams.lr, weight_decay=hparams.weight_decay)

    # eval()/train() toggling matters here (unlike checkpointed_ft.py,
    # where it's a formality) - LoRA's dropout is nonzero, so leaving the
    # model in train() mode during on_checkpoint's evaluation would leave
    # dropout active and make eval noisy/wrong.
    peft_model.eval()
    on_checkpoint(0, loss=None)
    peft_model.train()

    loss_meter = AverageMeter()
    for step in range(1, hparams.num_steps + 1):
        loss_meter.reset()

        for txt, tgt in zip(chunks(texts, hparams.batch_size), chunks(targets, hparams.batch_size)):
            opt.zero_grad()
            full_prompt = [f"{p} {l}" for p, l in zip(txt, tgt)]
            prompt_ids = tok(list(txt), return_tensors="pt", padding=True, truncation=True)["input_ids"]
            num_prompt_toks = [int((i != tok.pad_token_id).sum()) for i in prompt_ids]
            tokens = tok(full_prompt, return_tensors="pt", padding=True, truncation=True)
            bs = tokens["input_ids"].shape[0]
            tokens["labels"] = tokens["input_ids"].clone()
            num_pad_toks = [int((i == tok.pad_token_id).sum()) for i in tokens["labels"]]
            for i in range(len(txt)):
                tokens["labels"][i][num_pad_toks[i] : num_pad_toks[i] + num_prompt_toks[i]] = mask_token
            tokens["labels"][tokens["input_ids"] == tok.pad_token_id] = mask_token
            tokens = tokens.to(device)

            loss = peft_model(**tokens).loss
            loss_meter.update(loss.item(), n=bs)
            loss.backward()
            opt.step()

        loss_log.record("train", step, loss_meter.avg)
        if step % checkpoint_every == 0 or step == hparams.num_steps:
            peft_model.eval()
            on_checkpoint(step, loss=loss_meter.avg)
            peft_model.train()
