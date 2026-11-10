#!/usr/bin/env python3
"""Write the step-3 sweep specs: coordinate descent, one setting at a time,
on Sid's 40 dev edits. Launches nothing. Run from the project root:

    python3 scripts/make_step3_specs.py --round 1

Each method has an order of settings (ORDER: where to edit, then how hard,
then the training signal; inert settings from step 1 stay frozen). Round r
sweeps the r-th setting of every method with 8-10 values while every other
setting is held at its current value in docs/hparam_step3/state.json. After
a round, the winner (final selection rule: pass the gates, then maximise the
objective; within 3 points of the best, keep the value closest to the
current one) is written back into state.json, and the next round is
generated from the updated state.

state.json starts from START: the step-2 values (docs/hparam_selection.md,
"Step 2 -> step 3"). The script writes it only when it does not exist yet,
so the picks of earlier rounds are never overwritten.

Values: numeric settings 8 values on a x1.5 log grid around the current
value (shifted down or up where the current value sat at the edge of step 2
or nothing passed there: SHIFT); single layers every layer within 4 of the
current one; layer windows of the same width slid by 1 (by 2 for LoRA's
half-depth windows) up to 4 positions either side. Out-of-range values are
dropped and the grid shifted so it keeps its size.

One seed per run: step 2's 40 edits put seed noise at 1.8 points (AlphaEdit
2.7) on the objective, under the 3-point tie margin; the final settings get
extra seeds once the descent ends.
"""
import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "hparam_step3"
STATE = OUT / "state.json"
SIDS = "datasets/SidsDataset/records"
MODELS = ["qwen3-4b-instruct-2507", "olmo-3-7b-instruct", "llama-3.1-8b-instruct", "mistral-7b-instruct-v0.1"]
SHORT = {"qwen3-4b-instruct-2507": "Qwen", "olmo-3-7b-instruct": "Olmo", "llama-3.1-8b-instruct": "Llama",
         "mistral-7b-instruct-v0.1": "Mistral"}
N_LAYERS = {"Qwen": 36, "Olmo": 32, "Llama": 32, "Mistral": 32}
LABEL = {"ft": "FT-M", "lora": "LoRA", "rome": "ROME", "fidal": "FiDAL", "fine": "FiNE", "ifmet": "IFMET",
         "lti": "LTI", "loco": "LoCo", "alphaedit": "AlphaEdit"}
INVESTIGATION = {"ft": "finetuning", "lora": "finetuning", "rome": "locate_edit", "fidal": "dynamic_locate_edit",
                 "fine": "neuron_editors", "ifmet": "portability", "lti": "portability", "loco": "portability",
                 "alphaedit": "locate_edit"}
MLP = ["up_proj", "down_proj", "gate_proj"]
ATTN = ["q_proj", "k_proj", "v_proj", "o_proj"]


def w(a, b):
    return list(range(a, b + 1))


def per_model(**by):
    """by: setting -> {model short: value} or a value shared by all models."""
    return {m: {k: (v[SHORT[m]] if isinstance(v, dict) else v) for k, v in by.items()} for m in MODELS}


# Current values when step 3 starts: step 2's picks (values that held up
# across the other swept setting) on top of step 2's held values.
START = {
    "ft": per_model(
        layers={"Llama": [13], "Mistral": [8], "Olmo": [21], "Qwen": [24]},
        # Llama: only 2.74e-4 passed; Mistral: nothing passed, so below the range.
        norm_constraint={"Llama": 2.74e-4, "Mistral": 1e-4, "Olmo": 1e-3, "Qwen": 1e-3},
        lr=4.74e-4, num_steps=24, weight_decay=0.005),
    "lora": per_model(
        layers={"Llama": w(0, 15), "Mistral": w(0, 15), "Olmo": w(16, 31), "Qwen": w(9, 26)},
        lr={"Llama": 5e-5, "Mistral": 2e-5, "Olmo": 5e-5, "Qwen": 1.58e-4},
        num_steps=50, target_modules=MLP, lora_alpha=23, rank=11, weight_decay=0.0316, lora_dropout=0),
    "loco": per_model(
        lr={"Llama": 9e-5, "Mistral": 2e-5, "Olmo": 9e-5, "Qwen": 9e-5},
        num_steps=50, constraint="all", target_modules=ATTN, lora_alpha=15.2, rank=128, lora_dropout=0.05,
        n_implications=5, completion_weight=1.0, implication_max_new_tokens=30),
    "rome": per_model(
        layers={"Llama": [5], "Mistral": [5], "Olmo": [2], "Qwen": [7]},
        clamp_norm_factor={"Llama": 3.79, "Mistral": 12.0, "Olmo": 3.79, "Qwen": 3.79},
        v_lr=0.866, v_num_grad_steps=50, kl_factor=0.0625, v_weight_decay=0.001),
    "alphaedit": per_model(
        layers={"Llama": w(2, 6), "Mistral": w(2, 6), "Olmo": w(6, 10), "Qwen": w(6, 10)},
        clamp_norm_factor={"Llama": 3.79, "Mistral": 1.2, "Olmo": 3.79, "Qwen": 3.79},
        v_lr={"Llama": 0.05, "Mistral": 0.05, "Olmo": 0.158, "Qwen": 0.158},
        nullspace_threshold={"Llama": 0.002, "Mistral": 0.02, "Olmo": 0.02, "Qwen": 0.02},
        v_num_grad_steps={"Llama": 12, "Mistral": 12, "Olmo": 12, "Qwen": 50},
        L2=0.1, kl_factor=0.0625, mom2_update_weight=8220.0, v_weight_decay=0.001),
    "fidal": per_model(
        candidate_layers={"Llama": w(2, 8), "Mistral": w(2, 8), "Olmo": w(2, 8), "Qwen": w(5, 11)},
        clamp_norm_factor=2.19,
        v_lr={"Llama": 0.866, "Mistral": 5.0, "Olmo": 0.15, "Qwen": 0.866},
        probe_steps=10, probe_lr=0.01, mom2_update_weight=1500.0, kl_factor=0.188, v_num_grad_steps=25, top_k=10),
    "fine": per_model(
        neuron_num={"Llama": 15, "Mistral": 10, "Olmo": 15, "Qwen": 15},
        lr={"Llama": 0.003, "Mistral": 0.0015, "Olmo": 0.006, "Qwen": 0.006},
        epochs=200, early_stop_prob=0.99, last_layer=2, alpha=1.0, beta=9.49, gamma=0.0316),
    "ifmet": per_model(
        layers=w(2, 6),
        v_lr={"Llama": 0.2, "Mistral": 0.2, "Olmo": 0.0632, "Qwen": 0.2},
        nll_loss_factor=30.0, clamp_norm_factor=1.2, v_num_grad_steps=60, mom2_update_weight=4740.0,
        kl_factor=0.548, deep_layers={"Llama": w(18, 22), "Mistral": w(18, 22), "Olmo": w(18, 22),
                                      "Qwen": w(20, 24)},
        n_support=5, support_temperature=0.7),
    "lti": per_model(
        layers=w(4, 8), v_lr=0.5, nll_factor=9.0, clamp_norm_factor=1.2, v_num_grad_steps=50,
        last_kl_factor=0.00725, midlayers={"Llama": [14], "Mistral": [14], "Olmo": [14], "Qwen": [16]},
        mid_kl_factor=0.0134, mom2_update_weight=4740.0, kl_factor=0.0343),
}

# Setting order per method: where, then how hard, then training signal. Of
# a substituting pair (lr and steps) only one is swept.
ORDER = {
    "ft": ["layers", "norm_constraint", "lr"],
    "lora": ["layers", "lr"],
    "loco": ["lr", "num_steps"],
    "rome": ["layers", "clamp_norm_factor", "v_lr"],
    "alphaedit": ["layers", "clamp_norm_factor", "v_lr"],
    "fidal": ["candidate_layers", "clamp_norm_factor", "v_lr"],
    "fine": ["neuron_num", "lr"],
    "ifmet": ["layers", "v_lr", "nll_loss_factor"],
    "lti": ["layers", "v_lr", "nll_factor"],
}
# Qwen's AlphaEdit failed rewrite everywhere in step 2, best at the lowest
# nullspace_threshold: its strength setting is the threshold, not clamp.
ORDER_MODEL = {("alphaedit", "Qwen"): ["layers", "nullspace_threshold", "v_lr"]}

# Log-grid exponents (current x 1.5^k): default k = -3..4. "down" for
# settings whose step-2 best sat at the bottom edge or where nothing passed.
SHIFT = {
    ("ft", "Llama", "norm_constraint"): "down", ("ft", "Mistral", "norm_constraint"): "down",
    ("ft", "Olmo", "norm_constraint"): "up", ("ft", "Qwen", "norm_constraint"): "up",
    ("lora", "Llama", "lr"): "down", ("lora", "Mistral", "lr"): "down", ("lora", "Olmo", "lr"): "down",
    ("loco", "Llama", "lr"): "down", ("loco", "Mistral", "lr"): "down", ("loco", "Olmo", "lr"): "down",
    ("loco", "Qwen", "lr"): "down",
    ("fine", "Mistral", "lr"): "down", ("fine", "Olmo", "lr"): "up", ("fine", "Qwen", "lr"): "up",
    ("ifmet", "Llama", "v_lr"): "up", ("ifmet", "Mistral", "v_lr"): "up", ("ifmet", "Qwen", "v_lr"): "up",
    ("alphaedit", "Olmo", "v_lr"): "up", ("alphaedit", "Qwen", "nullspace_threshold"): "down",
    ("lti", "Qwen", "v_lr"): "up",
}
K = {None: range(-3, 5), "down": range(-5, 3), "up": range(-2, 6)}
# Explicit value lists where a log grid is the wrong shape.
EXPLICIT = {
    # Llama's FT-M layer was unsettled in step 2 (L13 best on the objective
    # but -16 specificity, L21 the only pass): a wide sweep.
    ("ft", "Llama", "layers"): [[3], [5], [8], [10], [13], [16], [19], [21], [24], [27]],
    ("fine", None, "neuron_num"): [3, 5, 8, 10, 12, 15, 20, 25],
    ("loco", None, "num_steps"): [10, 15, 20, 30, 40, 50, 70, 100],
    ("ifmet", None, "nll_loss_factor"): [3.0, 5.0, 10.0, 20.0, 30.0, 50.0, 80.0, 120.0],
    ("lti", None, "nll_factor"): [1.0, 2.0, 3.0, 5.0, 9.0, 15.0, 25.0, 40.0],
}
INTEGER = {"v_num_grad_steps", "num_steps", "neuron_num", "epochs", "top_k"}


def sig(x):
    return float(f"{x:.3g}")


def log_grid(cur, shift):
    return sorted({sig(cur * 1.5 ** k) for k in K[shift]})


def slide(seq, lo, hi, size):
    """Keep `size` items of the integer positions seq inside [lo, hi], shifting instead of dropping."""
    seq = sorted(seq)
    while seq[0] < lo:
        seq = [s + (seq[1] - seq[0]) for s in seq]
    while seq[-1] > hi:
        seq = [s - (seq[1] - seq[0]) for s in seq]
    return seq[:size]


def layer_values(method, cur, n):
    if len(cur) == 1:
        starts = slide(list(range(cur[0] - 4, cur[0] + 5)), 0, n - 1, 9)
        return [[s] for s in starts]
    width = len(cur)
    step = 2 if method == "lora" else 1
    starts = slide([cur[0] + step * i for i in range(-4, 5)], 0, n - width, 9)
    return [w(s, s + width - 1) for s in starts]


def values(method, model, setting, cur):
    m = SHORT[model]
    for key in ((method, m, setting), (method, None, setting)):
        if key in EXPLICIT:
            return EXPLICIT[key]
    if setting in ("layers", "candidate_layers"):
        return layer_values(method, cur, N_LAYERS[m])
    vals = log_grid(cur, SHIFT.get((method, m, setting)))
    if setting in INTEGER:
        vals = sorted({max(1, round(v)) for v in vals})
    return vals


def order(method, model):
    return ORDER_MODEL.get((method, SHORT[model]), ORDER[method])


def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({"round": 0, "values": START, "picks": []}, indent=1) + "\n")
    return json.loads(STATE.read_text())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    r = ap.parse_args().round
    state = load_state()
    cur_all = state["values"]
    rdir = OUT / f"round{r}"
    specs_dir = rdir / "specs"
    specs_dir.mkdir(parents=True, exist_ok=True)
    for old in specs_dir.glob("*.json"):
        old.unlink()
    rows, warm = [], {}
    for method in LABEL:
        for model in MODELS:
            seq = order(method, model)
            if r > len(seq):
                continue
            setting = seq[r - 1]
            cur = cur_all[method][model]
            vals = values(method, model, setting, cur[setting])
            fixed = {k: v for k, v in cur.items() if k != setting}
            label = f"Step 3 round {r} ({setting}): {LABEL[method]}, {model}, Sid's dev (40 edits)"
            spec = {"investigation": INVESTIGATION[method], "design": "grid", "step": 3,
                    "methods": {method: {setting: vals}}, "fixed": {method: {model: fixed}},
                    "models": [model], "data_paths": [SIDS], "split": "dev", "ds_size": "full",
                    "edit_mode": "single", "seed": 0, "label": label,
                    "note": f"coordinate descent round {r}: {setting} with every other setting at its current value"}
            name = f"{method}__{model}__r{r}_{setting}.json"
            (specs_dir / name).write_text(json.dumps(spec, indent=1) + "\n")
            rows.append(dict(method=method, model=model, setting=setting, cur=cur[setting], vals=vals, file=name))
            if method == "alphaedit" and setting in ("layers", "nullspace_threshold"):
                warm[model] = {"layers": vals if setting == "layers" else [cur["layers"]],
                               "nullspace_threshold": vals if setting == "nullspace_threshold"
                               else [cur["nullspace_threshold"]]}
    wdir = rdir / "warmup"
    if wdir.exists():
        for old in wdir.glob("*.json"):
            old.unlink()
    for model, swept in warm.items():
        wdir.mkdir(parents=True, exist_ok=True)
        spec = {"investigation": "locate_edit", "data_paths": [SIDS], "ds_size": "1", "edit_mode": "single",
                "seed": 0, "split": "dev", "purpose": "setup", "design": "grid", "models": [model],
                "methods": {"alphaedit": swept},
                "label": f"AlphaEdit step 3 round {r} warm-up: null-space projections, {model}",
                "note": "one edit per projection the round needs, so its runs never build the same one at once"}
        (wdir / f"alphaedit_projections_{model}.json").write_text(json.dumps(spec, indent=1) + "\n")
    write_readme(r, rows, rdir)
    print(f"round {r}: {len(rows)} specs, {sum(len(x['vals']) for x in rows)} runs, {len(warm)} warm-ups")


def fmt(v):
    if isinstance(v, list) and v and all(isinstance(i, int) for i in v):
        return f"L{v[0]}-{v[-1]}" if len(v) > 1 else f"L{v[0]}"
    return f"{v:g}" if isinstance(v, float) else str(v)


def write_readme(r, rows, rdir):
    lines = [f"# Step 3, round {r}: one setting at a time on the 40 dev edits", "",
             "Written by `scripts/make_step3_specs.py --round {r}` from `docs/hparam_step3/state.json`.".format(r=r),
             "Every other setting is held at its current value in the state file. Method: docs/hparam_selection.md.",
             "", "| Method | Model | Setting | Current | Values | Runs |", "|---|---|---|---|---|---|"]
    for x in rows:
        lines.append(f"| {LABEL[x['method']]} | {SHORT[x['model']]} | `{x['setting']}` | {fmt(x['cur'])} | "
                     f"{', '.join(fmt(v) for v in x['vals'])} | {len(x['vals'])} |")
    lines += ["", f"Total: {len(rows)} specs, {sum(len(x['vals']) for x in rows)} runs.", ""]
    (rdir / "README.md").write_text("\n".join(lines))


if __name__ == "__main__":
    main()
