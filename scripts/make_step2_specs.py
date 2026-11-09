#!/usr/bin/env python3
"""Write the step-2 sweep specs: small grids (3 values of 2 settings) and
short one-setting sweeps per method and main instruct model, on Sid's 40 dev
edits, ready for

    python scripts/dash.py sweep docs/hparam_step2/specs/<file>.json --estimate
    python scripts/dash.py sweep docs/hparam_step2/specs/<file>.json

plus docs/hparam_step2/README.md. Launches nothing. Run from the project root:

    python3 scripts/make_step2_specs.py

How the values follow from step 1 is in docs/hparam_selection.md. In short:
every setting is one of
  - grid: crossed with one other setting at 3 values (the pair interacts in
    step 1, or the models disagree on it);
  - sweep: 3 values one at a time (a training-signal setting, which
    interacted with nothing in step 1);
  - pivot: held at the step-1 level that won on every model (or at a value
    past it, when the winner sat at the edge of the range);
  - frozen: held at the step-1 centre value (no effect in step 1).
Middle values are the step-1 centre values (dashboard/backend/factorial.py
centre_value: log midpoint for rates and weights, middle window for layers).

ROME, FiDAL and LTI build their edit over context prefixes sampled from the
model, so their step-1 centre runs moved up to 33 rewrite points with the
seed alone: their sweeps run at seeds 0 and 1 (one spec each); the other
methods were deterministic to within a few points and run once.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "dashboard" / "backend"))
from factorial import centre_value  # noqa: E402

OUT = ROOT / "docs" / "hparam_step2"
STEP1 = ROOT / "docs" / "hparam_step1" / "specs"
SIDS = "datasets/SidsDataset/records"
MODELS = ["qwen3-4b-instruct-2507", "olmo-3-7b-instruct", "llama-3.1-8b-instruct", "mistral-7b-instruct-v0.1"]
SHORT = {"qwen3-4b-instruct-2507": "Qwen", "olmo-3-7b-instruct": "Olmo", "llama-3.1-8b-instruct": "Llama",
         "mistral-7b-instruct-v0.1": "Mistral"}
LABEL = {"ft": "FT-M", "lora": "LoRA", "rome": "ROME", "fidal": "FiDAL", "fine": "FiNE", "ifmet": "IFMET",
         "lti": "LTI", "loco": "LoCo", "alphaedit": "AlphaEdit"}
SEEDS = {"rome": [0, 1], "fidal": [0, 1], "lti": [0, 1], "alphaedit": [0, 1]}
# Step-1 median minutes per run on 10 edits; step 2 has 40 (see README for the scaling).
MINUTES_10 = {"ft": 2.0, "lora": 3.2, "rome": 9.1, "fidal": 3.6, "fine": 1.7, "loco": 5.9, "ifmet": 10.9, "lti": 3.5,
              "alphaedit": 2.8}
MLP = ["up_proj", "down_proj", "gate_proj"]


def window(a, b):
    return list(range(a, b + 1))


def step1(method, model):
    spec = json.loads((STEP1 / f"{method}__{model}.json").read_text())
    levels = spec["methods"][method]
    held = ((spec.get("fixed") or {}).get(method) or {}).get(model) or {}
    return levels, held


def centre(levels, key):
    return centre_value(*levels[key])[0]


def plan(method, model):
    """[(name, swept {setting: values}, held {setting: value}, why)] for one method and model."""
    lv, held = step1(method, model)
    c = lambda k: centre(lv, k)
    lo = lambda k: lv[k][0]
    hi = lambda k: lv[k][1]
    m = SHORT[model]

    if method == "rome":
        layers = [[5], [7], [9]] if m == "Qwen" else [[2], [3], [5]]
        swept = {"layers": layers, "clamp_norm_factor": [lo("clamp_norm_factor"), c("clamp_norm_factor"), hi("clamp_norm_factor")]}
        fixed = {"v_num_grad_steps": hi("v_num_grad_steps"),
                 **{k: c(k) for k in ("v_lr", "kl_factor", "v_weight_decay")}}
        return [("grid", swept, fixed, "where x clamp: layers x clamp interacted in step 1; Qwen preferred layer 7, "
                 "the others layer 3, so each model's window brackets its winner")]

    if method == "fidal":
        frozen = {k: c(k) for k in ("v_num_grad_steps", "top_k", "kl_factor", "mom2_update_weight")}
        if m in ("Llama", "Mistral"):
            swept = {"clamp_norm_factor": [0.8, lo("clamp_norm_factor"), c("clamp_norm_factor")],
                     "v_lr": [lo("v_lr"), c("v_lr"), hi("v_lr")]}
            fixed = {"candidate_layers": lo("candidate_layers"), **frozen}
            why = "early layers won clearly on this model; clamp x v_lr interacted, clamp low won at the edge so it extends below 1.2"
        else:
            swept = {"candidate_layers": [lo("candidate_layers"), c("candidate_layers"), hi("candidate_layers")],
                     "clamp_norm_factor": [lo("clamp_norm_factor"), c("clamp_norm_factor"), hi("clamp_norm_factor")]}
            fixed = {"v_lr": c("v_lr"), **frozen}
            why = "layers undecided on this model and layers x clamp was FiDAL's largest interaction"
        return [("grid", swept, {**held, **fixed}, why)]

    if method == "fine":
        swept = {"lr": [lo("lr"), c("lr"), hi("lr")], "neuron_num": [lo("neuron_num"), c("neuron_num"), hi("neuron_num")]}
        fixed = {"epochs": hi("epochs"), "early_stop_prob": hi("early_stop_prob"), "last_layer": hi("last_layer"),
                 **{k: c(k) for k in ("alpha", "beta", "gamma")}}
        return [("grid", swept, fixed, "lr and neuron_num substitute for each other and Mistral prefers both low")]

    if method == "ft":
        layers = {"Llama": [[5], [13], [21]], "Mistral": [[4], [8], [14]], "Olmo": [[14], [21], [27]],
                  "Qwen": [[16], [24], [32]]}[m]
        swept = {"layers": layers, "norm_constraint": [c("norm_constraint"), hi("norm_constraint"), 1e-3]}
        fixed = {k: c(k) for k in ("lr", "num_steps", "weight_decay")}
        return [("grid", swept, fixed, "layer choice differs by model; norm_constraint high won on every model at the "
                 "edge, so its values extend past 5e-4; layers x norm_constraint interacted")]

    if method == "lora":
        n = 36 if m == "Qwen" else 32
        half, quarter = n // 2, n // 4
        swept = {"layers": [window(0, half - 1), window(quarter, quarter + half - 1), window(half, n - 1)],
                 "lr": [lo("lr"), c("lr"), hi("lr")]}
        fixed = {"num_steps": hi("num_steps"), "target_modules": MLP,
                 **{k: c(k) for k in ("lora_alpha", "rank", "weight_decay")}}
        return [("grid", swept, {**held, **fixed}, "layer choice differs by model; lr is the strength dial "
                 "(steps are free so held high, alpha substitutes for lr so held at centre)")]

    if method == "loco":
        frozen = {k: c(k) for k in ("lora_alpha", "rank", "n_implications", "completion_weight",
                                    "implication_max_new_tokens")}
        swept = {"lr": [lo("lr"), c("lr"), hi("lr")], "num_steps": [lo("num_steps"), c("num_steps"), hi("num_steps")]}
        fixed = {"constraint": "implication", "target_modules": lo("target_modules"), **frozen}
        signal = {"constraint": ["all"]}
        sig_fixed = {"lr": c("lr"), "num_steps": c("num_steps"), "target_modules": lo("target_modules"), **frozen}
        return [("grid", swept, {**held, **fixed}, "lr x steps was LoCo's largest interaction and the models disagree "
                 "on strength; centre runs beat the corners by 7-16 points"),
                ("constraint", signal, {**held, **sig_fixed}, "training signal: interacts with nothing, so one extra run "
                 "at the grid centre (implication is the grid's centre cell)")]

    if method == "ifmet":
        frozen = {k: c(k) for k in ("mom2_update_weight", "kl_factor", "deep_layers", "n_support")}
        base = {"clamp_norm_factor": lo("clamp_norm_factor"), "v_num_grad_steps": hi("v_num_grad_steps"),
                "layers": lo("layers"), **frozen, **held}
        return [("v_lr", {"v_lr": [lo("v_lr"), c("v_lr"), hi("v_lr")]}, {**base, "nll_loss_factor": hi("nll_loss_factor")},
                 "clamp fixed low (won on every model) removes the v_lr x clamp interaction, so v_lr alone"),
                ("nll", {"nll_loss_factor": [3.0, 30.0]}, {**base, "v_lr": c("v_lr")},
                 "training signal: nll high won on every model at the edge; 10 is the v_lr sweep's centre run")]

    if method == "lti":
        layers = [window(1, 5), lo("layers"), window(4, 8)] if m in ("Llama", "Mistral") else \
            [lo("layers"), window(4, 8), hi("layers")]
        frozen = {"midlayers": c("midlayers"), **{k: c(k) for k in ("mid_kl_factor", "mom2_update_weight", "kl_factor")}}
        base = {"clamp_norm_factor": lo("clamp_norm_factor"), "v_num_grad_steps": hi("v_num_grad_steps"),
                "last_kl_factor": lo("last_kl_factor"), **frozen}
        return [("grid", {"layers": layers, "v_lr": [lo("v_lr"), c("v_lr"), hi("v_lr")]},
                 {**base, "nll_factor": hi("nll_factor")},
                 "Qwen disagrees with the others on v_lr and layers; clamp fixed low removes clamp x v_lr"),
                ("nll", {"nll_factor": [c("nll_factor"), 9.0]}, {**base, "layers": layers[1], "v_lr": c("v_lr")},
                 "training signal: 3.0 is the grid's centre cell")]
    if method == "alphaedit":
        # Added 2026-11-08 after AlphaEdit's step 1 (locality ranked last).
        # Llama and Mistral: v_lr and clamp both won low, at the edge, and
        # interact; early layers. Olmo: v_lr low; clamp trades portability
        # for rewrite (full range); later layers slightly. Qwen: v_lr,
        # nullspace_threshold and grad steps all won high, at the edge.
        # Grad steps by the time rule: 50 only where it gained rewrite (Qwen).
        frozen = {k: c(k) for k in ("kl_factor", "mom2_update_weight", "v_weight_decay")}
        v_lr_low = [0.016, lo("v_lr"), c("v_lr")]
        if m in ("Llama", "Mistral"):
            swept = {"clamp_norm_factor": [0.8, lo("clamp_norm_factor"), c("clamp_norm_factor")], "v_lr": v_lr_low}
            fixed = {"layers": lo("layers"), "v_num_grad_steps": lo("v_num_grad_steps"), "L2": lo("L2"),
                     "nullspace_threshold": lo("nullspace_threshold") if m == "Llama" else c("nullspace_threshold")}
            why = "clamp and v_lr both won low at the edge and interact; early layers won"
        elif m == "Olmo":
            swept = {"clamp_norm_factor": [lo("clamp_norm_factor"), c("clamp_norm_factor"), hi("clamp_norm_factor")],
                     "v_lr": v_lr_low}
            fixed = {"layers": hi("layers"), "v_num_grad_steps": lo("v_num_grad_steps"), "L2": lo("L2"),
                     "nullspace_threshold": c("nullspace_threshold")}
            why = "v_lr won low at the edge; clamp trades portability against rewrite, so its full range"
        else:
            swept = {"v_lr": [c("v_lr"), hi("v_lr"), 1.58],
                     "nullspace_threshold": [c("nullspace_threshold"), hi("nullspace_threshold"), 0.6]}
            fixed = {"layers": hi("layers"), "v_num_grad_steps": hi("v_num_grad_steps"), "L2": lo("L2"),
                     "clamp_norm_factor": c("clamp_norm_factor")}
            why = "v_lr and nullspace_threshold both won high at the edge on Qwen, which needs a harder push"
        return [("grid", swept, {**held, **fixed, **frozen}, why)]
    raise KeyError(method)


INVESTIGATION = {"ft": "finetuning", "lora": "finetuning", "rome": "locate_edit", "fidal": "dynamic_locate_edit",
                 "fine": "neuron_editors", "ifmet": "portability", "lti": "portability", "loco": "portability",
                 "alphaedit": "locate_edit"}


def runs_of(swept):
    n = 1
    for v in swept.values():
        n *= len(v)
    return n


def main():
    specs_dir = OUT / "specs"
    specs_dir.mkdir(parents=True, exist_ok=True)
    for old in specs_dir.glob("*.json"):
        old.unlink()
    rows = []
    for method in LABEL:
        for model in MODELS:
            for part, swept, fixed, why in plan(method, model):
                clash = set(swept) & set(fixed)
                assert not clash, (method, model, clash)
                for seed in SEEDS.get(method, [0]):
                    spec = {
                        "investigation": INVESTIGATION[method], "design": "grid", "step": 2,
                        "methods": {method: swept}, "fixed": {method: {model: fixed}},
                        "models": [model], "data_paths": [SIDS], "split": "dev", "ds_size": "full",
                        "edit_mode": "single", "seed": seed,
                        "label": f"Step 2 {part}: {LABEL[method]}, {model}, Sid's dev (40 edits), seed {seed}",
                        "note": why,
                    }
                    name = f"{method}__{model}__{part}__seed{seed}.json"
                    (specs_dir / name).write_text(json.dumps(spec, indent=1) + "\n")
                    rows.append({"method": method, "model": model, "part": part, "seed": seed, "file": name,
                                 "swept": swept, "fixed": fixed, "runs": runs_of(swept), "why": why})
    write_readme(rows)
    print(f"wrote {len(rows)} specs, {sum(r['runs'] for r in rows)} runs, to {specs_dir.relative_to(ROOT)}")


def fmt(v):
    if isinstance(v, list) and v and all(isinstance(i, int) for i in v):
        return f"{v[0]}-{v[-1]}" if len(v) > 1 else str(v[0])
    if isinstance(v, list):
        return "+".join(str(i).replace("_proj", "") for i in v)
    return f"{v:g}" if isinstance(v, float) else str(v)


def write_readme(rows):
    lines = [
        "# Step 2: small grids on the 40 dev edits",
        "",
        "Written by `scripts/make_step2_specs.py`; rerun it to regenerate. Why each setting is swept, held",
        "or frozen, and how the values follow from step 1: `docs/hparam_selection.md`.",
        "",
        "Every spec is a `grid` sweep on Sid's dev split (40 replace edits, single edits). ROME, FiDAL and",
        "LTI run twice (seeds 0 and 1) because their edits depend on sampled context prefixes.",
        "",
        "```bash",
        "python scripts/dash.py sweep docs/hparam_step2/specs/<file>.json --estimate",
        "python scripts/dash.py sweep docs/hparam_step2/specs/<file>.json",
        "```",
        "",
        "| Method | Model | Part | Swept | Held | Runs x seeds |",
        "|---|---|---|---|---|---|",
    ]
    seen = set()
    for r in rows:
        key = (r["method"], r["model"], r["part"])
        if key in seen:
            continue
        seen.add(key)
        seeds = len(SEEDS.get(r["method"], [0]))
        swept = "; ".join(f"`{k}` {{{', '.join(fmt(v) for v in vals)}}}" for k, vals in r["swept"].items())
        held = ", ".join(f"`{k}` {fmt(v)}" for k, v in r["fixed"].items())
        lines.append(f"| {LABEL[r['method']]} | {SHORT[r['model']]} | {r['part']} | {swept} | {held} | {r['runs']} x {seeds} |")
    total = sum(r["runs"] for r in rows)
    lines += ["", f"Total: {len(rows)} specs, {total} runs.", ""]
    (OUT / "README.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
