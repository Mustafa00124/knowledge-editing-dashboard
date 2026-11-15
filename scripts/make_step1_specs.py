#!/usr/bin/env python3
"""Write the step-1 (two-level factorial) sweep specs: one JSON file per
method and main instruct model, ready for

    python scripts/dash.py sweep docs/hparam_step1/specs/<file>.json --estimate
    python scripts/dash.py sweep docs/hparam_step1/specs/<file>.json

plus docs/hparam_step1/README.md with run counts and GPU time. Launches
nothing. Run from the project root:

    python3 scripts/make_step1_specs.py

Low and high values are the user's step-1 plan (2026-11-04); AlphaEdit was
added 2026-11-07 by the same rules (docs/hparam_selection.md). Since
2026-11-15 each method's main layer setting takes three values (early,
middle, late): the two-level design of the other settings runs at each
(dashboard/backend/hparam_sweeps.factorial_designs); IFMET's deep_layers and
LTI's midlayers keep two. Layer settings
are per model: from its depth (models/<dir>/config.json), its traced peak
(results/investigations/causal_tracing/traced_layers.json) and the windows
the step-0 Latin hypercube screen tried (its sweep.json files), as noted
beside each below.
"""
import json
import math
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "hparam_step1"
SIDS = "datasets/SidsDataset/dev"  # relative to the project root; the backend resolves it

MODELS = {
    "qwen3-4b-instruct-2507": "Qwen3-4B-Instruct-2507",
    "olmo-3-7b-instruct": "Olmo-3-7B-Instruct",
    "llama-3.1-8b-instruct": "Llama-3.1-8B-Instruct",
    "mistral-7b-instruct-v0.1": "Mistral-7B-Instruct-v0.1",
}
INVESTIGATION = {"ft": "finetuning", "lora": "finetuning", "rome": "locate_edit", "fidal": "dynamic_locate_edit",
                 "fine": "neuron_editors", "ifmet": "portability", "lti": "portability", "loco": "portability",
                 "alphaedit": "locate_edit"}
LABEL = {"ft": "FT-M", "lora": "LoRA", "rome": "ROME", "fidal": "FiDAL", "fine": "FiNE", "ifmet": "IFMET",
         "lti": "LTI", "loco": "LoCo", "alphaedit": "AlphaEdit"}
# Median minutes per run in the step-0 screen.
# AlphaEdit: 2.8 min once its null-space projection for the run's (layers,
# threshold) is cached; building one takes about 30 min (step 0 built one per
# run), so its step 1 is preceded by a warm-up that builds the 5 it needs.
MINUTES = {"ft": 2.0, "lora": 3.2, "rome": 9.1, "fidal": 3.6, "fine": 1.7, "loco": 5.9, "ifmet": 10.9, "lti": 3.5,
           "alphaedit": 2.8}
# The fraction p of each method's two-level part. With a three-value layer
# setting it covers the other settings (2^(k-1-p) rows, run at all three
# layer values). Resolution IV for the 9-10 setting methods (2026-11-05, for
# cost); resolution V or more for the rest, the smallest such fraction
# (2026-11-15: ROME, LoRA and FiDAL drop from the full design to it).
FRACTION = {"ifmet": 3, "loco": 3, "lti": 3, "alphaedit": 3, "rome": 1, "lora": 1, "fidal": 1}
CENTRE_POINTS = 3

ATTENTION = ["q_proj", "k_proj", "v_proj", "o_proj"]
MLP = ["gate_proj", "up_proj", "down_proj"]


def depth(model):
    return json.loads((ROOT / "models" / MODELS[model] / "config.json").read_text())["num_hidden_layers"]


def traced_peak(model):
    traced = json.loads((ROOT / "results/investigations/causal_tracing/traced_layers.json").read_text())
    return traced[model]["peak_layer"]


def screened(investigation, method, model, knob):
    """Values the step-0 screen tried for one setting on one model."""
    for path in sorted((ROOT / "results/investigations" / investigation / "sweeps").glob("*/sweep.json")):
        sweep = json.loads(path.read_text())
        request = sweep.get("request") or {}
        if sweep.get("step") == 0 and request.get("models") == [model] and knob in (request.get("methods") or {}).get(method, {}):
            return request["methods"][method][knob]
    raise LookupError(f"no step-0 screen of {method}.{knob} on {model}")


def window(start, end):
    return list(range(start, end + 1))


def middle(low, high):
    """The layer, or window, halfway between two (first and last layers
    averaged, halves rounded up), as the backend's centre value."""
    half = lambda a, b: int(math.floor((a + b) / 2 + 0.5))
    return window(half(low[0], high[0]), half(low[-1], high[-1]))


def values(method, model):
    """(swept {setting: [low, high]}, held {setting: value}, notes)."""
    n = depth(model)
    inv = INVESTIGATION[method]
    if method == "ft":
        late = round(2 * n / 3)
        return ({
            # Early: the traced peak (step 0's early candidate); late: the
            # middle of step 0's late window, two thirds of the way up.
            "layers": [[traced_peak(model)], middle([traced_peak(model)], [late]), [late]],
            "lr": [1.5e-4, 1.5e-3], "num_steps": [12, 50],
            "norm_constraint": [1.5e-4, 5e-4], "weight_decay": [0, 0.01],
        }, {}, [f"layers: traced peak {traced_peak(model)} vs layer {late} (two thirds of {n})"])
    if method == "lora":
        third = round(n / 3)
        return ({
            "lr": [5e-5, 5e-4], "num_steps": [12, 50], "rank": [4, 32], "lora_alpha": [8, 64],
            "target_modules": [["q_proj", "v_proj"], ["up_proj", "down_proj", "gate_proj"]],
            "layers": [window(0, third - 1), window(third, 2 * third - 1), window(2 * third, n - 1)],
            "weight_decay": [0.01, 0.1],
        }, {"lora_dropout": 0}, [f"layers: thirds 0-{third - 1}, {third}-{2 * third - 1}, {2 * third}-{n - 1}"])
    if method == "rome":
        tried = sorted(v[0] for v in screened(inv, method, model, "layers"))
        return ({
            # The shallowest and deepest layer step 0 tried.
            "layers": [[tried[0]], middle([tried[0]], [tried[-1]]), [tried[-1]]],
            "v_lr": [0.15, 5.0], "v_num_grad_steps": [12, 50], "kl_factor": [0.00625, 0.625],
            "clamp_norm_factor": [1.2, 12.0], "v_weight_decay": [1e-4, 1e-2],
        }, {}, [f"layers: {tried[0]}, {middle([tried[0]], [tried[-1]])[0]}, {tried[-1]}: the ends of step 0's range and the middle"])
    if method == "fidal":
        return ({
            # Never layer 1 or below: bug 10 (layer 1 breaks Qwen).
            "candidate_layers": [window(2, 8), middle(window(2, 8), window(7, 13)), window(7, 13)],
            "mom2_update_weight": [1500.0, 15000.0], "v_lr": [0.15, 5.0], "v_num_grad_steps": [25, 100],
            "top_k": [5, 20], "kl_factor": [0.00625, 0.188], "clamp_norm_factor": [1.2, 4.0],
        }, {"probe_steps": 10, "probe_lr": 0.01},
            ["candidate_layers: 2-8, 5-11, 7-13 on every model (bug 10: no band starts below layer 2)",
             "top_k 20 is more than the 7 candidate layers, so the high level edits every candidate layer"])
    if method == "fine":
        return ({
            # last_layer: how many top layers are frozen (never selected); 3 is the paper's default.
            "lr": [3e-4, 3e-3], "epochs": [25, 200], "neuron_num": [2, 10], "alpha": [0.1, 10.0],
            "beta": [3.0, 30.0], "gamma": [0.01, 0.1], "last_layer": [1, 3, 6], "early_stop_prob": [0.7, 0.99],
        }, {}, ["last_layer (top layers frozen): 1, 3, 6"])
    if method == "ifmet":
        first = sorted(screened(inv, method, model, "layers"))
        # Middle: 16-20 on every model (about half depth); late: the deepest
        # window step 0 tried (20-24 on the 32-layer models, 23-27 on Qwen).
        deep = [window(16, 20), max(screened(inv, method, model, "deep_layers"))]
        return ({
            "v_lr": [0.02, 0.2], "v_num_grad_steps": [15, 60], "clamp_norm_factor": [1.2, 4.0],
            "mom2_update_weight": [1500.0, 15000.0], "kl_factor": [0.1, 3.0], "nll_loss_factor": [0.3, 10.0],
            "layers": [first[0], middle(first[0], first[-1]), first[-1]], "deep_layers": [deep[0], deep[-1]],
            "n_support": [2, 12],
        }, {"support_temperature": 0.7},
            [f"layers: {first[0][0]}-{first[0][-1]}, {middle(first[0], first[-1])[0]}-{middle(first[0], first[-1])[-1]}, "
             f"{first[-1][0]}-{first[-1][-1]}; deep_layers: "
             f"{deep[0][0]}-{deep[0][-1]} vs {deep[-1][0]}-{deep[-1][-1]} (the latter step 0's deepest window)"])
    if method == "lti":
        first = sorted(screened(inv, method, model, "layers"))
        mid = 15 if n >= 36 else 13
        return ({
            "midlayers": [[mid], [mid + 2]],
            "last_kl_factor": [0.00725, 0.0725], "mid_kl_factor": [0.00425, 0.0425], "nll_factor": [0.375, 3.0],
            "v_lr": [0.05, 0.5], "v_num_grad_steps": [12, 50], "mom2_update_weight": [1500.0, 15000.0],
            "clamp_norm_factor": [1.2, 12.0], "kl_factor": [0.00625, 0.188],
            "layers": [first[0], middle(first[0], first[-1]), first[-1]],
        }, {}, [f"midlayers: {mid} vs {mid + 2}; layers: {first[0][0]}-{first[0][-1]}, "
                f"{middle(first[0], first[-1])[0]}-{middle(first[0], first[-1])[-1]}, {first[-1][0]}-{first[-1][-1]}"])
    if method == "loco":
        return ({
            "lr": [9e-5, 9e-4], "num_steps": [6, 50], "completion_weight": [0.5, 2.0],
            "constraint": ["implication", "all"], "n_implications": [2, 12], "rank": [64, 256],
            "lora_alpha": [4.8, 48.0], "target_modules": [ATTENTION, ATTENTION + MLP],
            "implication_max_new_tokens": [15, 60],
        }, {"lora_dropout": 0.05}, ["constraint and target_modules have no middle: the centre runs use the low level"])
    if method == "alphaedit":
        first = sorted(screened(inv, method, model, "layers"))
        return ({
            # Step 0 (17 runs per model): clamp 40 kept fluency in 25% of runs
            # and 0.4 gave the lowest portability; v_lr 1.5 and 5 kept 62% and
            # 58% (0.05 and 0.5: 100%); 100 grad steps gained only 0.04 rewrite
            # over 12 (time rule); mom2 150,000 kept 58% with the weakest edits.
            # The other settings kept fluency at both ends of their range.
            "layers": [first[0], middle(first[0], first[-1]), first[-1]],
            "v_lr": [0.05, 0.5], "v_num_grad_steps": [12, 50], "kl_factor": [0.00625, 0.625],
            "clamp_norm_factor": [1.2, 12.0], "mom2_update_weight": [1500.0, 45000.0],
            "nullspace_threshold": [0.002, 0.2], "L2": [0.1, 10.0], "v_weight_decay": [1e-4, 1e-2],
        }, {}, [f"layers: {first[0][0]}-{first[0][-1]}, {middle(first[0], first[-1])[0]}-{middle(first[0], first[-1])[-1]}, "
                f"{first[-1][0]}-{first[-1][-1]}: the ends of step 0's range and the middle"])
    raise KeyError(method)


STATS_METHODS = {"rome": "ROME", "fidal": "FiDAL", "ifmet": "IFMET", "lti": "LTI", "alphaedit": "AlphaEdit"}


def missing_stats(method, model, swept):
    """Layers the spec edits (corners; centres lie between them) that have no
    covariance statistics yet; the first run to need one computes it."""
    if method not in STATS_METHODS:
        return []
    import yaml
    hp = yaml.safe_load((ROOT / "experiments/run_experiment/hparams" / STATS_METHODS[method] / f"{model}.yaml").read_text())
    # Statistics are not in git: a worktree reads the main checkout's (KE_STATS_ROOT).
    stats = Path(os.environ.get("KE_STATS_ROOT", ROOT)) / "experiments/run_experiment/data/stats" / MODELS[model] / "wikipedia_stats"
    layers = set()
    for key in ("layers", "deep_layers", "candidate_layers"):
        for value in swept.get(key) or [hp.get(key) or []]:
            layers.update(value)
    name = lambda layer: f"{hp['rewrite_module_tmp'].format(layer)}_{hp.get('mom2_dtype', 'float32')}_mom2_{hp['mom2_n_samples']}.npz"
    return sorted(layer for layer in layers if not (stats / name(layer)).exists())


def design_of(method, swept):
    """(corner and middle runs, description), as the backend builds it."""
    import sys
    sys.path.insert(0, str(ROOT / "dashboard" / "backend"))
    import factorial
    three = [k for k, v in swept.items() if len(v) == 3]
    k2 = len(swept) - len(three)
    p = FRACTION.get(method)
    p = factorial.default_fraction(k2) if p is None else p
    option = next(o for o in factorial.fractions(k2) if o["p"] == p)
    base = (f"full 2^{k2}" if p == 0 else f"2^({k2}-{p}), resolution {factorial.roman(option['resolution'])}")
    if three:
        return 3 * option["runs"], f"{base} x 3 {three[0]}"
    return option["runs"], base


def main():
    specs_dir = OUT / "specs"
    specs_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for method in MINUTES:
        for model in MODELS:
            swept, held, notes = values(method, model)
            k = len(swept)
            spec = {
                "investigation": INVESTIGATION[method],
                "design": "factorial2",
                "step": 1,
                "methods": {method: swept},
                "fixed": {method: {model: held}} if held else {},
                "models": [model],
                "data_paths": [SIDS],
                "split": "screen",
                "ds_size": "full",
                "edit_mode": "single",
                "seed": 0,
                "centre_points": CENTRE_POINTS,
                "fraction": FRACTION.get(method),
                "label": f"Step 1 factorial: {LABEL[method]}, {model}, Sid's screen (10 edits)",
                "note": "two-level factorial over every setting (low/high) plus centre runs; "
                        + "; ".join(notes) if notes else
                        "two-level factorial over every setting (low/high) plus centre runs",
            }
            name = f"{method}__{model}.json"
            (specs_dir / name).write_text(json.dumps(spec, indent=1) + "\n")
            corners, design = design_of(method, swept)
            runs = corners + CENTRE_POINTS
            rows.append({"method": method, "model": model, "file": name, "k": k, "design": design, "runs": runs,
                         "missing": missing_stats(method, model, swept),
                         "minutes": runs * MINUTES[method]})
    write_readme(rows)
    print(f"wrote {len(rows)} specs to {specs_dir.relative_to(ROOT)}")


def hours(minutes):
    return f"{minutes / 60:.1f}"


def write_readme(rows):
    by_method = {}
    for r in rows:
        by_method.setdefault(r["method"], []).append(r)
    lines = [
        "# Step 1: factorial specs (prepared, not launched)",
        "",
        "Written by `scripts/make_step1_specs.py`; rerun it to regenerate. One spec per method and",
        "main instruct model, on Sid's 10-edit screen split (dev records, single edits, seed 0), with",
        "3 centre runs each (seeds 0, 1, 2). Check and launch one with",
        "",
        "```bash",
        "python scripts/dash.py sweep docs/hparam_step1/specs/<file>.json --estimate",
        "python scripts/dash.py sweep docs/hparam_step1/specs/<file>.json",
        "```",
        "",
        "Every setting takes a low and a high value, except each method's main layer setting, which",
        "takes three (early, middle, late; LoCo has none). The two-level design of the other settings",
        "runs at each of the three: early and late together form an ordinary two-level design (main",
        "effects and interactions as before), and the middle block shows whether the layer bends.",
        "`fraction` is that two-level part's p: resolution V or more, except resolution IV for the",
        "9-10 setting methods (IFMET, LTI, LoCo, AlphaEdit; for cost: main effects stay clear, but",
        "pairs of settings are aliased with other pairs).",
        "",
        "GPU time is runs x the step-0 median minutes per run; it leaves out covariance statistics",
        "for layers that have none yet (`--estimate` lists them).",
        "",
        "## Per method (each of the 4 models)",
        "",
        "| Method | Settings | Design | Runs per model | Min per run | GPU hours per model | GPU hours, 4 models |",
        "|---|---|---|---|---|---|---|",
    ]
    total = 0.0
    for method, group in by_method.items():
        r = group[0]
        all_minutes = sum(g["minutes"] for g in group)
        total += all_minutes
        lines.append(f"| {LABEL[method]} | {r['k']} | {r['design']} + 3 centre | {r['runs']} | {MINUTES[method]} | "
                     f"{hours(r['minutes'])} | {hours(all_minutes)} |")
    n_runs = sum(r["runs"] for r in rows)
    lines += [
        f"| **All** | | | {n_runs // 4} | | {hours(total / 4)} | **{hours(total)}** |",
        "",
        f"Total: {n_runs} runs, about {hours(total)} GPU hours ({hours(total / 4)} hours of wall clock at the",
        "dashboard's four GPU jobs at once).",
        "",
        "## Covariance statistics",
        "",
    ]
    gaps = [r for r in rows if r["missing"]]
    lines += [f"- {LABEL[r['method']]} on {r['model']}: none yet for layers "
              f"{', '.join(map(str, r['missing']))}. Compute them before launching (a covariance warm-up, as for step 0), "
              "or the first runs compute them, several at once." for r in gaps] or ["- Present for every layer the specs edit."]
    lines += [
        "",
        "## Spec files",
        "",
        "| File | Runs | GPU hours |",
        "|---|---|---|",
    ]
    for r in rows:
        lines.append(f"| `specs/{r['file']}` | {r['runs']} | {hours(r['minutes'])} |")
    (OUT / "README.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
