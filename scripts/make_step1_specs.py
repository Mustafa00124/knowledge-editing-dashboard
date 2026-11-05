#!/usr/bin/env python3
"""Write the step-1 (two-level factorial) sweep specs: one JSON file per
method and main instruct model, ready for

    python scripts/dash.py sweep docs/hparam_step1/specs/<file>.json --estimate
    python scripts/dash.py sweep docs/hparam_step1/specs/<file>.json

plus docs/hparam_step1/README.md with run counts and GPU time. Launches
nothing. Run from the project root:

    python3 scripts/make_step1_specs.py

Low and high values are the user's step-1 plan (2026-11-04). Layer settings
are per model: from its depth (models/<dir>/config.json), its traced peak
(results/investigations/causal_tracing/traced_layers.json) and the windows
the step-0 Latin hypercube screen tried (its sweep.json files), as noted
beside each below.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "hparam_step1"
SIDS = "datasets/SidsDataset/records"  # relative to the project root; the backend resolves it

MODELS = {
    "qwen3-4b-instruct-2507": "Qwen3-4B-Instruct-2507",
    "olmo-3-7b-instruct": "Olmo-3-7B-Instruct",
    "llama-3.1-8b-instruct": "Llama-3.1-8B-Instruct",
    "mistral-7b-instruct-v0.1": "Mistral-7B-Instruct-v0.1",
}
INVESTIGATION = {"ft": "finetuning", "lora": "finetuning", "rome": "locate_edit", "fidal": "dynamic_locate_edit",
                 "fine": "neuron_editors", "ifmet": "portability", "lti": "portability", "loco": "portability"}
LABEL = {"ft": "FT-M", "lora": "LoRA", "rome": "ROME", "fidal": "FiDAL", "fine": "FiNE", "ifmet": "IFMET",
         "lti": "LTI", "loco": "LoCo"}
# Median minutes per run in the step-0 screen.
MINUTES = {"ft": 2.0, "lora": 3.2, "rome": 9.1, "fidal": 3.6, "fine": 1.7, "loco": 5.9, "ifmet": 10.9, "lti": 3.5}
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


def values(method, model):
    """(swept {setting: [low, high]}, held {setting: value}, notes)."""
    n = depth(model)
    inv = INVESTIGATION[method]
    if method == "ft":
        late = round(2 * n / 3)
        return ({
            # Early: the traced peak (step 0's early candidate); late: the
            # middle of step 0's late window, two thirds of the way up.
            "layers": [[traced_peak(model)], [late]],
            "lr": [1.5e-4, 1.5e-3], "num_steps": [12, 50],
            "norm_constraint": [1.5e-4, 5e-4], "weight_decay": [0, 0.01],
        }, {}, [f"layers: traced peak {traced_peak(model)} vs layer {late} (two thirds of {n})"])
    if method == "lora":
        half = n // 2
        return ({
            "lr": [5e-5, 5e-4], "num_steps": [12, 50], "rank": [4, 32], "lora_alpha": [8, 64],
            "target_modules": [["q_proj", "v_proj"], ["up_proj", "down_proj", "gate_proj"]],
            "layers": [window(0, half - 1), window(half, n - 1)],
            "weight_decay": [0.01, 0.1],
        }, {"lora_dropout": 0}, [f"layers: first half 0-{half - 1} vs second half {half}-{n - 1}"])
    if method == "rome":
        tried = sorted(v[0] for v in screened(inv, method, model, "layers"))
        return ({
            # The shallowest and deepest layer step 0 tried.
            "layers": [[tried[0]], [tried[-1]]],
            "v_lr": [0.15, 5.0], "v_num_grad_steps": [12, 50], "kl_factor": [0.00625, 0.625],
            "clamp_norm_factor": [1.2, 12.0], "v_weight_decay": [1e-4, 1e-2],
        }, {}, [f"layers: {tried[0]} vs {tried[-1]}, the ends of step 0's range"])
    if method == "fidal":
        return ({
            # Never layer 1 or below: bug 10 (layer 1 breaks Qwen).
            "candidate_layers": [window(2, 8), window(7, 13)],
            "mom2_update_weight": [1500.0, 15000.0], "v_lr": [0.15, 5.0], "v_num_grad_steps": [25, 100],
            "top_k": [5, 20], "kl_factor": [0.00625, 0.188], "clamp_norm_factor": [1.2, 4.0],
        }, {"probe_steps": 10, "probe_lr": 0.01},
            ["candidate_layers: 2-8 vs 7-13 on every model (bug 10: no band starts below layer 2)",
             "top_k 20 is more than the 7 candidate layers, so the high level edits every candidate layer"])
    if method == "fine":
        return ({
            "lr": [3e-4, 3e-3], "epochs": [25, 200], "neuron_num": [2, 10], "alpha": [0.1, 10.0],
            "beta": [3.0, 30.0], "gamma": [0.01, 0.1], "last_layer": [1, 6], "early_stop_prob": [0.7, 0.99],
        }, {}, [])
    if method == "ifmet":
        first = sorted(screened(inv, method, model, "layers"))
        # Middle: 16-20 on every model (about half depth); late: the deepest
        # window step 0 tried (20-24 on the 32-layer models, 23-27 on Qwen).
        deep = [window(16, 20), max(screened(inv, method, model, "deep_layers"))]
        return ({
            "v_lr": [0.02, 0.2], "v_num_grad_steps": [15, 60], "clamp_norm_factor": [1.2, 4.0],
            "mom2_update_weight": [1500.0, 15000.0], "kl_factor": [0.1, 3.0], "nll_loss_factor": [0.3, 10.0],
            "layers": [first[0], first[-1]], "deep_layers": [deep[0], deep[-1]], "n_support": [2, 12],
        }, {"support_temperature": 0.7},
            [f"layers: {first[0][0]}-{first[0][-1]} vs {first[-1][0]}-{first[-1][-1]}; deep_layers: "
             f"{deep[0][0]}-{deep[0][-1]} vs {deep[-1][0]}-{deep[-1][-1]} (the latter step 0's deepest window)"])
    if method == "lti":
        first = sorted(screened(inv, method, model, "layers"))
        mid = 15 if n >= 36 else 13
        return ({
            "midlayers": [[mid], [mid + 2]],
            "last_kl_factor": [0.00725, 0.0725], "mid_kl_factor": [0.00425, 0.0425], "nll_factor": [0.375, 3.0],
            "v_lr": [0.05, 0.5], "v_num_grad_steps": [12, 50], "mom2_update_weight": [1500.0, 15000.0],
            "clamp_norm_factor": [1.2, 12.0], "kl_factor": [0.00625, 0.188],
            "layers": [first[0], first[-1]],
        }, {}, [f"midlayers: {mid} vs {mid + 2}; layers: {first[0][0]}-{first[0][-1]} vs {first[-1][0]}-{first[-1][-1]}"])
    if method == "loco":
        return ({
            "lr": [9e-5, 9e-4], "num_steps": [6, 50], "completion_weight": [0.5, 2.0],
            "constraint": ["implication", "all"], "n_implications": [2, 12], "rank": [64, 256],
            "lora_alpha": [4.8, 48.0], "target_modules": [ATTENTION, ATTENTION + MLP],
            "implication_max_new_tokens": [15, 60],
        }, {"lora_dropout": 0.05}, ["constraint and target_modules have no middle: the centre runs use the low level"])
    raise KeyError(method)


STATS_METHODS = {"rome": "ROME", "fidal": "FiDAL", "ifmet": "IFMET", "lti": "LTI"}


def missing_stats(method, model, swept):
    """Layers the spec edits (corners; centres lie between them) that have no
    covariance statistics yet; the first run to need one computes it."""
    if method not in STATS_METHODS:
        return []
    import yaml
    hp = yaml.safe_load((ROOT / "experiments/run_experiment/hparams" / STATS_METHODS[method] / f"{model}.yaml").read_text())
    stats = ROOT / "experiments/run_experiment/data/stats" / MODELS[model] / "wikipedia_stats"
    layers = set()
    for key in ("layers", "deep_layers", "candidate_layers"):
        for value in swept.get(key) or [hp.get(key) or []]:
            layers.update(value)
    name = lambda layer: f"{hp['rewrite_module_tmp'].format(layer)}_{hp.get('mom2_dtype', 'float32')}_mom2_{hp['mom2_n_samples']}.npz"
    return sorted(layer for layer in layers if not (stats / name(layer)).exists())


def roman(r):
    return {4: "IV", 5: "V", 6: "VI", 7: "VII"}.get(r, str(r))


# Corner runs per number of settings at the default fraction, and the
# 64-run alternative where the default is 128 (matches dashboard/backend/
# factorial.py; the backend recomputes them on --estimate).
DEFAULT_DESIGN = {5: (32, "full 2^5"), 6: (64, "full 2^6"), 7: (64, "2^(7-1), resolution VII"),
                  8: (64, "2^(8-2), resolution V"), 9: (128, "2^(9-2), resolution VI"),
                  10: (128, "2^(10-3), resolution V")}
SMALLER = {9: (64, 3, "2^(9-3), resolution IV"), 10: (64, 4, "2^(10-4), resolution IV")}


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
                "fraction": None,
                "label": f"Step 1 factorial: {LABEL[method]}, {model}, Sid's screen (10 edits)",
                "note": "two-level factorial over every setting (low/high) plus centre runs; "
                        + "; ".join(notes) if notes else
                        "two-level factorial over every setting (low/high) plus centre runs",
            }
            name = f"{method}__{model}.json"
            (specs_dir / name).write_text(json.dumps(spec, indent=1) + "\n")
            corners, design = DEFAULT_DESIGN[k]
            runs = corners + CENTRE_POINTS
            smaller = SMALLER.get(k)
            rows.append({"method": method, "model": model, "file": name, "k": k, "design": design, "runs": runs,
                         "missing": missing_stats(method, model, swept),
                         "minutes": runs * MINUTES[method],
                         "smaller": (smaller[0] + CENTRE_POINTS, smaller[1], smaller[2]) if smaller else None})
    write_readme(rows)
    print(f"wrote {len(rows)} specs to {specs_dir.relative_to(ROOT)}")


def hours(minutes):
    return f"{minutes / 60:.1f}"


def write_readme(rows):
    by_method = {}
    for r in rows:
        by_method.setdefault(r["method"], []).append(r)
    lines = [
        "# Step 1: two-level factorial specs (prepared, not launched)",
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
        "`fraction` is null, the default: the full design up to 6 settings, otherwise the smallest",
        "fraction of resolution V or more. For IFMET, LTI and LoCo set `\"fraction\": 3` (IFMET, LoCo)",
        "or `4` (LTI) for 64 corner runs at resolution IV: main effects stay clear, but pairs of",
        "settings are aliased with other pairs.",
        "",
        "GPU time is runs x the step-0 median minutes per run; it leaves out covariance statistics",
        "for layers that have none yet (`--estimate` lists them).",
        "",
        "## Per method (each of the 4 models)",
        "",
        "| Method | Settings | Design | Runs per model | Min per run | GPU hours per model | GPU hours, 4 models | 64-run option, 4 models |",
        "|---|---|---|---|---|---|---|---|",
    ]
    total = total_small = 0.0
    for method, group in by_method.items():
        r = group[0]
        all_minutes = sum(g["minutes"] for g in group)
        total += all_minutes
        if r["smaller"]:
            small_minutes = sum(g["smaller"][0] * MINUTES[method] for g in group)
            small = f"{r['smaller'][0]} runs, {hours(small_minutes)} h"
        else:
            small_minutes = all_minutes
            small = "same"
        total_small += small_minutes
        lines.append(f"| {LABEL[method]} | {r['k']} | {r['design']} + 3 centre | {r['runs']} | {MINUTES[method]} | "
                     f"{hours(r['minutes'])} | {hours(all_minutes)} | {small} |")
    n_runs = sum(r["runs"] for r in rows)
    n_small = sum((r["smaller"] or (r["runs"],))[0] for r in rows)
    lines += [
        f"| **All** | | | {n_runs // 4} | | {hours(total / 4)} | **{hours(total)}** | {n_small} runs, {hours(total_small)} h |",
        "",
        f"Total: {n_runs} runs, about {hours(total)} GPU hours ({hours(total / 4)} hours of wall clock at the",
        "dashboard's four GPU jobs at once). With the 64-run fractions for IFMET, LTI and LoCo:",
        f"{n_small} runs, about {hours(total_small)} GPU hours.",
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
