"""Shared plumbing for the portability editors.

IFMET and LTI each sit on top of one of EasyEdit's closed-form
editors, the way FiDAL does (dynamic/fidal.py): their hparams file holds
their own settings plus the base editor's whole config, so a run records a
single self-contained hparams file. IFMET and LoCo also ask the unedited
model for text (another name for the subject; implications of the new
fact), which generate() does.
"""
import importlib
from contextlib import contextmanager

import torch

from dynamic import hparams_yaml
from dynamic.fidal import BASE_EDITORS


def load_config(path, alg_name, own_keys):
    """(own settings, base editor config) from one hparams file.

    `own_keys` are the method's own settings; every other key belongs to
    the base editor and is forwarded to its HyperParams class untouched.
    """
    if not str(path).endswith(".yaml"):
        path = f"{path}.yaml"
    config = hparams_yaml.load(path)  # "5e-1" read as a number, as EasyEdit's loaders do
    assert config.get("alg_name") == alg_name, f"not a {alg_name} hparams file: {path}"
    base_method = config.get("base_method")
    if base_method not in BASE_EDITORS:
        raise ValueError(f"{alg_name}: base_method {base_method!r} is not one of {sorted(BASE_EDITORS)}")
    own = {k: v for k, v in config.items() if k in own_keys}
    base_config = {k: v for k, v in config.items() if k not in own_keys and k != "base_method"}
    base_config["alg_name"] = BASE_EDITORS[base_method][4]
    return own, base_method, base_config


def base_hparams(base_method, base_config, **changes):
    module_name, class_name = BASE_EDITORS[base_method][:2]
    hparams_cls = getattr(importlib.import_module(module_name), class_name)
    hparams = hparams_cls(**base_config)
    for key, value in changes.items():
        setattr(hparams, key, value)
    return hparams


def apply_base(base_method, model, tok, requests, hparams, return_orig_weights, weights_copy):
    """One base-editor call. Its pre-edit weights are folded into
    `weights_copy`, keeping the first copy of each parameter, so restoring
    after several stages reaches the weights from before the first."""
    module_name, function_name = BASE_EDITORS[base_method][2:4]
    apply_fn = getattr(importlib.import_module(module_name), function_name)
    model, copied = apply_fn(model, tok, list(requests), hparams, copy=False,
                             return_orig_weights=return_orig_weights)
    for name, value in (copied or {}).items():
        weights_copy.setdefault(name, value)
    return model


def filled_prompt(request):
    prompt = request["prompt"]
    return prompt.replace("{}", request["subject"]) if "{}" in prompt else prompt


def fact_sentence(request):
    """The edit as a plain statement: "The capital of Spain is Lisbon."."""
    text = f"{filled_prompt(request).rstrip()} {str(request['target_new']).strip()}"
    return text if text.endswith((".", "!", "?")) else text + "."


@contextmanager
def padding(tok, side):
    """Pad on `side` for the duration: left to generate, right wherever a
    row's last real token is found from its attention mask."""
    previous = tok.padding_side
    tok.padding_side = side
    try:
        yield
    finally:
        tok.padding_side = previous


def generate(model, tok, prompts, max_new_tokens, num_return_sequences=1, temperature=None, seed=0):
    """Continuations of each prompt, cut at the first newline.

    Greedy unless `temperature` is given, in which case it samples
    `num_return_sequences` continuations per prompt from a fixed seed, so a
    rerun generates the same text. Returns one list per prompt.
    """
    device = next(model.parameters()).device
    sampling = temperature is not None
    was_training = model.training
    model.eval()
    try:
        with padding(tok, "left"), torch.no_grad():
            inputs = tok(prompts, return_tensors="pt", padding=True).to(device)
            if sampling:
                torch.manual_seed(seed)
            output = model.generate(
                **inputs, max_new_tokens=max_new_tokens, pad_token_id=tok.pad_token_id or tok.eos_token_id,
                do_sample=sampling, temperature=temperature if sampling else None,
                top_p=None, top_k=None,
                num_return_sequences=num_return_sequences if sampling else 1,
            )
    finally:
        model.train(was_training)
    width = inputs["input_ids"].shape[1]
    texts = [tok.decode(row[width:], skip_special_tokens=True).split("\n")[0].strip() for row in output]
    per_prompt = num_return_sequences if sampling else 1
    return [texts[i * per_prompt:(i + 1) * per_prompt] for i in range(len(prompts))]
