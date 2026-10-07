"""Hyperparameter investigations: catalog, sweep launches, results, promotion.

An investigation is one method family (experiments/run_experiment/
investigations.json) and every tunable setting of its methods; the earlier
investigations by kind of setting are kept as `legacy` so their results stay
readable, but are no longer launched. A sweep varies some of those settings
for chosen methods, models and datasets, either one setting at a time around
a single run at the current settings (`design: one_at_a_time`) or every
combination (`grid`); every
point is an ordinary run_experiment job (same submission path, logs and
job table as the Experiments page) with three differences: it edits dev
records only (--split dev), evaluates only before editing and at the end
(--final_only), and passes the swept values as --hparam overrides.

On disk, one folder per sweep:
    results/investigations/<investigation>/sweeps/<sweep_id>/
        sweep.json          what was varied and fixed, and every run's job id
        runs/<run>/...      the runner's usual files (hparams, checkpoints, summary)

Scores are the four criteria on a 0..1 scale: fluency as the final
value over the unedited model's (step 0), capped at 1, reliability (edit
success), locality, and generalizability (portability). Tuning aims for
high reliability without losing fluency, so the best value found is the
highest reliability among runs that keep fluency at FLUENCY_DROP or above.
"""
import itertools
import json
import re
import secrets
import shlex
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import yaml

import config
import db
import registry
import slurm

CATALOG_PATH = config.EXPERIMENTS_DIR / "run_experiment" / "investigations.json"
HPARAMS_DIR = config.EXPERIMENTS_DIR / "run_experiment" / "hparams"
TUNED_PATH = HPARAMS_DIR / "TUNED.json"
EXPERIMENT = "run_experiment"
SWEEP_PREFIX = "hp-"
LOG_FACTORS = (0.1, 0.3, 1, 3, 10)

# hparams keys that are plumbing rather than tuning: names, paths, devices,
# and module-name templates fixed by the architecture.
HIDDEN_KEYS = {"alg_name", "model_name", "device", "stats_dir", "P_loc", "model_parallel", "mom2_dtype",
               "fp16", "delta_dtype", "base_method", "data_path", "seed"}
HIDDEN_SUFFIXES = ("_tmp", "_tmps", "_module")

# Experiments-page fields that override an hparams-file setting when the
# field applies to the method (run_experiment.py sets hparams from them).
FIELD_OVERRIDES = {
    "lr": {"ft": "lr", "lora": "lr"},
    "num_steps": {"ft": "num_steps", "lora": "num_steps"},
    "mom2_n_samples": {"memit": "mom2_n_samples", "pmet": "mom2_n_samples", "alphaedit": "mom2_n_samples"},
    "retrieval_k": {"scr": "retrieval_k", "ike": "k"},
}
# Set by the runner itself, never from a file or a sweep.
RUNNER_SET = {("ft", "batch_size"): "every record at once (the runner sets it to the record count)",
              ("lora", "batch_size"): "every record at once (the runner sets it to the record count)"}
INT_FACTORS = (0.25, 0.5, 1, 2, 4)


def _load_catalog():
    return json.loads(CATALOG_PATH.read_text())


def _exp_cfg():
    return registry.get_experiment_type(EXPERIMENT)


def _method_options(exp_cfg):
    field = next(f for f in exp_cfg["fields"] if f["name"] == "method")
    return {m["value"]: m for cat in field["categories"] for m in cat["methods"]}


def _hparams_dirs():
    """method value -> hparams folder, from the runner's own table."""
    src = (config.EXPERIMENTS_DIR / "run_experiment" / "run_experiment.py").read_text()
    block = re.search(r"METHOD_HPARAMS_DIR = \{(.*?)\n\}", src, re.S).group(1)
    return dict(re.findall(r'"([^"]+)":\s*"([^"]+)"', block))


def _hparams_file(method, model):
    folder = _hparams_dirs().get(method)
    return HPARAMS_DIR / folder / f"{model}.yaml" if folder else None


def _read_hparams(method, model):
    path = _hparams_file(method, model)
    if not path or not path.exists():
        return None
    return yaml.safe_load(path.read_text())


def _model_layers(model):
    """Layer count from the weights' config.json, when downloaded."""
    dirs = registry.model_dirs(str(config.EXPERIMENTS_DIR / EXPERIMENT), "run_experiment.py")
    directory = dirs.get(model)
    cfg_path = config.MODELS_DIR / directory / "config.json" if directory else None
    if not cfg_path or not cfg_path.exists():
        return None
    cfg = json.loads(cfg_path.read_text())
    return cfg.get("num_hidden_layers") or cfg.get("n_layer")


def _traced():
    """model -> its causal trace (peak layer, prompts, ...), from the
    Knowledge localisation investigation."""
    path = config.INVESTIGATIONS_DIR / "causal_tracing" / "traced_layers.json"
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {}


def _traced_peak(model):
    entry = _traced().get(model)
    return entry.get("peak_layer") if entry else None


def _number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _round(x):
    return float(f"{x:.3g}")


def suggest(kind, default, spec=None, model=None):
    """Sweep values to prefill, centred on the current default."""
    spec = spec or {}
    if kind == "log":
        base = _number(default)
        if not base:
            return [default]
        return [_round(base * f) for f in LOG_FACTORS]
    if kind == "int":
        base = _number(default)
        if base is None:
            return [default]
        if base == 0:
            return [0, 1, 2]
        return sorted({max(1, int(round(base * f))) for f in INT_FACTORS})
    if kind == "bool":
        return [False, True]
    if kind == "choice":
        options = list(spec.get("options", []))
        return options if default in options else [default] + options
    n_layers = _model_layers(model) if model else None
    layers = list(default or [])
    if kind == "layer":
        centre = layers[0] if layers else (_traced_peak(model) or 0)
        candidates = set(range(centre - 2, centre + 3))
        peak = _traced_peak(model)
        if peak is not None:
            candidates.add(peak)
        return [[layer] for layer in sorted(candidates) if layer >= 0 and (n_layers is None or layer < n_layers)]
    if kind == "layer_window":
        if not layers:
            return [layers]
        width, start = len(layers), layers[0]
        starts = set(range(start - 2, start + 3))
        peak = _traced_peak(model)
        if peak is not None:
            starts.add(peak - width // 2)
        return [list(range(s, s + width)) for s in sorted(starts)
                if s >= 0 and (n_layers is None or s + width <= n_layers)]
    if kind == "layer_span":
        # Where adapters go: every layer ([], the usual LoRA setting), each
        # half, the middle half, and a quarter of the model around its
        # traced peak.
        if not n_layers:
            return [layers]
        half, quarter = n_layers // 2, max(1, n_layers // 4)
        spans = [[], list(range(0, half)), list(range(quarter, quarter + half)), list(range(half, n_layers))]
        peak = _traced_peak(model)
        if peak is not None:
            start = min(max(0, peak - quarter // 2), n_layers - quarter)
            spans.append(list(range(start, start + quarter)))
        if layers not in spans:
            spans.insert(0, layers)
        out = []
        for span in spans:
            if span not in out:
                out.append(span)
        return out
    return [default]


def _has_dev_split(data_path):
    """Whether scripts/make_splits.py made a split for this file (a sweep
    runs on its dev records, so a file without one cannot be swept)."""
    try:
        rel = Path(data_path).resolve().relative_to((config.PROJECT_ROOT / "datasets").resolve())
    except ValueError:
        return False
    return (config.PROJECT_ROOT / "splits" / rel).exists()


def default_datasets(inv, exp_cfg=None):
    """The datasets a sweep of this investigation starts with: for
    `datasets: all`, every runnable subset with dev records, less those
    matching `datasets_except`. None when the investigation sets none."""
    if inv.get("datasets") != "all":
        return None
    exp_cfg = exp_cfg or _exp_cfg()
    field = next(f for f in exp_cfg["fields"] if f.get("control") == "dataset")
    skip = inv.get("datasets_except") or []
    return [s["value"] for b in field["benchmarks"] for s in b["subsets"]
            if s.get("available") is not False and s.get("value") and _has_dev_split(s["value"])
            and not any(part in s["value"] for part in skip)]


def tuned():
    return json.loads(TUNED_PATH.read_text()) if TUNED_PATH.exists() else {}


def catalog():
    """Investigations with each method's knobs, per-model defaults and
    suggestions, and which settings were tuned by a sweep."""
    exp_cfg = _exp_cfg()
    options = _method_options(exp_cfg)
    model_field = next(f for f in exp_cfg["fields"] if f["name"] == "model")
    models = [o["value"] for o in model_field["options"]]
    tuned_settings = tuned()
    out = []
    for inv in _load_catalog()["investigations"]:
        methods = []
        for method, entry in inv["methods"].items():
            option = options.get(method)
            if not option:
                continue
            knobs = []
            for key, spec in entry["knobs"].items():
                defaults, suggestions = {}, {}
                for model in models:
                    # The value runs really get, which for a few settings is
                    # an Experiments-page default rather than the file's.
                    current = {r["key"]: r["value"] for r in effective_settings(method, model, exp_cfg) or []}
                    if key not in current:
                        continue
                    defaults[model] = current[key]
                    suggestions[model] = suggest(spec["kind"], current[key], spec, model)
                knobs.append({
                    "key": key, **spec, "defaults": defaults, "suggestions": suggestions,
                    "tuned": {m: tuned_settings.get(method, {}).get(m, {}).get(key) for m in defaults
                              if tuned_settings.get(method, {}).get(m, {}).get(key)},
                })
            methods.append({
                "method": method, "label": option.get("label", method),
                "available": option.get("available", True) is not False,
                "note": option.get("note"), "knobs": knobs,
            })
        row = {**{k: v for k, v in inv.items() if k != "methods"}, "methods": methods,
               "default_datasets": default_datasets(inv, exp_cfg)}
        if any(k["kind"] in ("layer", "layer_window", "layer_span")
               for entry in inv["methods"].values() for k in entry["knobs"].values()):
            # Each model's traced peak beside the layers every method edits,
            # so the per-method sweep can be read against the per-model trace.
            row["traced"] = {m: {k: t.get(k) for k in ("peak_layer", "layers", "n_prompts", "effect", "dataset", "run")}
                             for m, t in _traced().items()}
        out.append(row)
    return out


def _owners():
    """(method, key) -> the investigation that tunes it (never a legacy one)."""
    owners = {}
    for inv in _load_catalog()["investigations"]:
        if inv.get("legacy"):
            continue
        for method, entry in inv["methods"].items():
            for key in entry["knobs"]:
                owners[(method, key)] = {"id": inv["id"], "label": inv["label"]}
    return owners


def effective_settings(method, model, exp_cfg=None):
    """Every tunable setting a run of this method on this model gets, with
    the value it really runs with and where that value comes from."""
    exp_cfg = exp_cfg or _exp_cfg()
    hp = _read_hparams(method, model)
    if hp is None:
        return None
    fields = {f["name"]: f for f in exp_cfg["fields"]}
    from_fields = {}
    for field_name, per_method in FIELD_OVERRIDES.items():
        key = per_method.get(method)
        if key and field_name in fields:
            from_fields[key] = slurm._cast(fields[field_name]["default"], fields[field_name]["type"])
    tuned_here = tuned().get(method, {}).get(model, {})
    out = []
    for key, value in hp.items():
        if key in HIDDEN_KEYS or key.endswith(HIDDEN_SUFFIXES):
            continue
        if (method, key) in RUNNER_SET:
            out.append({"key": key, "value": None, "source": "runner", "note": RUNNER_SET[(method, key)],
                        "editable": False})
            continue
        if key in from_fields:
            out.append({"key": key, "value": from_fields[key], "source": "experiment_default", "editable": True,
                        "note": f"the Experiments page default; the hparams file says {json.dumps(value)}"})
        elif key in tuned_here:
            t = tuned_here[key]
            out.append({"key": key, "value": value, "source": "tuned", "editable": True,
                        "note": f"tuned in {t['investigation']} (sweep {t['sweep']})"})
        else:
            out.append({"key": key, "value": value, "source": "hparams", "editable": True})
    return out


def _earlier(method, key):
    """Legacy investigations that swept this setting of this method."""
    return [inv["id"] for inv in _load_catalog()["investigations"]
            if inv.get("legacy") and key in (inv["methods"].get(method) or {}).get("knobs", {})]


def settings(investigation, methods, models):
    """Held-constant candidates for a sweep: each method's settings per
    model, which investigation tunes each one, and the best value that
    investigation has found so far (highest reliability among runs that
    keep fluency, any dataset)."""
    exp_cfg = _exp_cfg()
    owners = _owners()
    results_cache = {}

    def best(method, model, key, owner):
        if not owner or owner["id"] == investigation:
            return None
        # The family's own sweeps and the earlier by-setting ones alike.
        rows = [r for inv_id in [owner["id"]] + _earlier(method, key)
                for r in results_cache.setdefault(inv_id, results(inv_id))]
        candidates = [r for r in rows if r["method"] == method and r["model"] == model
                      and list(r["overrides"]) == [key] and _keeps_fluency(r["scores"])]
        if not candidates:
            return None
        top = max(candidates, key=lambda r: r["scores"]["reliability"])
        return {"value": top["overrides"][key], "reliability": top["scores"]["reliability"],
                "fluency": top["scores"].get("fluency"), "dataset": top["dataset"],
                "sweep": top["sweep_id"], "run": top["run"]}

    out = {}
    for method in methods:
        out[method] = {}
        for model in models:
            rows = effective_settings(method, model, exp_cfg)
            if rows is None:
                continue
            for row in rows:
                owner = owners.get((method, row["key"]))
                row["owner"] = owner
                row["best"] = best(method, model, row["key"], owner) if row["editable"] else None
            out[method][model] = rows
    return out


def _sweep_dir(investigation, sweep_id):
    return config.INVESTIGATIONS_DIR / investigation / "sweeps" / sweep_id


def _slug(value):
    if isinstance(value, list) and len(value) > 5 and all(isinstance(v, int) for v in value) \
            and value == list(range(value[0], value[0] + len(value))):
        return f"{value[0]}to{value[-1]}"  # a long run of layers
    if value == []:
        return "all"  # adapters on every layer
    if isinstance(value, (int, float)) and not isinstance(value, bool) and value < 0:
        return "neg" + _slug(-value)  # the "-" would be stripped below: -2.0 and 2.0 must differ
    text = json.dumps(value) if not isinstance(value, str) else value
    return re.sub(r"[^A-Za-z0-9.]+", "-", text).strip("-") or "x"


def _dataset_slug(exp_cfg, data_path):
    _, subset = slurm._dataset_meta(exp_cfg, {"data_path": data_path})
    return slurm._slug(subset or Path(data_path).stem)


def _grid(knob_values):
    keys = sorted(knob_values)
    for combo in itertools.product(*(knob_values[k] for k in keys)):
        yield dict(zip(keys, combo))


def _one_at_a_time(knob_values, current):
    """None (one run at the current settings) then {key: value} for every
    picked value that differs from the current one, one setting at a time."""
    points = [None]
    for key in sorted(knob_values):
        for value in knob_values[key]:
            if json.dumps(value) != json.dumps(current.get(key)):
                points.append({key: value})
    return points


def _skip_reason(exp_cfg, params):
    spec = _method_options(exp_cfg).get(params["method"], {})
    if params.get("edit_mode") in ("batch", "sequential_batch") and spec.get("no_joint_batch"):
        return f"{spec.get('label', params['method'])} edits one fact at a time; choose the single or sequential protocol"
    if params.get("edit_mode") == "sequential_batch" and int(params.get("edit_batch_size", 1)) > int(params.get("reset_every", 1)):
        return "the batch size is larger than the reset interval"
    return "this method cannot run on this dataset"


def plan(req):
    """Every run a launch request would submit, and every point skipped with
    the reason, without submitting anything."""
    exp_cfg = _exp_cfg()
    inv = next((i for i in _load_catalog()["investigations"] if i["id"] == req["investigation"]), None)
    if inv is None:
        raise ValueError(f"unknown investigation {req['investigation']!r}")
    if inv.get("legacy"):
        raise ValueError(f"{inv['label']} is an earlier sweep by kind of setting; sweep its methods "
                         "from their family's investigation instead")
    design = req.get("design") or inv.get("design") or "grid"
    if design not in ("grid", "one_at_a_time"):
        raise ValueError(f"design must be grid or one_at_a_time, not {design!r}")
    runs, skipped = [], []
    if list(req.get("data_paths") or []) == ["default"]:
        req["data_paths"] = default_datasets(inv, exp_cfg) or []
        if not req["data_paths"]:
            raise ValueError(f"{inv['label']} has no default datasets; list data_paths")
    fixed_all = req.get("fixed") or {}
    for method, knob_values in req["methods"].items():
        if method not in inv["methods"]:
            raise ValueError(f"{method} has no setting in the {inv['label']} investigation")
        allowed = set(inv["methods"][method]["knobs"])
        unknown = set(knob_values) - allowed
        if unknown:
            raise ValueError(f"{method} has no {', '.join(sorted(unknown))} in {inv['label']}")
        knob_values = {k: v for k, v in knob_values.items() if v}
        if not knob_values:
            continue
        for model in req["models"]:
            if _read_hparams(method, model) is None:
                skipped.append({"method": method, "model": model, "reason": "no hparams for this model"})
                continue
            # Held-constant settings changed from their current value; applied
            # to every run of this method and model, never part of a run name.
            fixed = dict((fixed_all.get(method) or {}).get(model) or {})
            editable = {r["key"] for r in effective_settings(method, model, exp_cfg) if r["editable"]}
            bad = set(fixed) - editable
            if bad:
                raise ValueError(f"{method} on {model} has no adjustable setting {', '.join(sorted(bad))}")
            clash = set(fixed) & set(knob_values)
            if clash:
                raise ValueError(f"{', '.join(sorted(clash))} is being swept, so it cannot also be held at a value")
            for data_path in req["data_paths"]:
                params = slurm._prepare_params(exp_cfg, {
                    "method": method, "model": model, "data_path": data_path,
                    "ds_size": req.get("ds_size", "full"), "edit_mode": req.get("edit_mode"),
                    "seed": req.get("seed", 0), "evaluation_modes": "original",
                })
                if not slurm._combo_supported(exp_cfg, params):
                    skipped.append({"method": method, "model": model, "data_path": data_path,
                                    "reason": _skip_reason(exp_cfg, params)})
                    continue
                stem = [method, model, _dataset_slug(exp_cfg, data_path)]
                current = {r["key"]: r["value"] for r in effective_settings(method, model, exp_cfg)}
                current.update(fixed)
                points = list(_grid(knob_values)) if design == "grid" else _one_at_a_time(knob_values, current)
                for overrides in points:
                    run = {"method": method, "model": model, "data_path": data_path,
                           "overrides": overrides, "fixed": fixed, "params": params}
                    if overrides is None:
                        # The one run at the current settings, standing in for
                        # every swept setting's current value.
                        run.update(overrides={}, baseline_for={k: current.get(k) for k in knob_values})
                        name = "_".join(stem + ["current"])
                    else:
                        name = "_".join(stem + [f"{k}{_slug(v)}" for k, v in overrides.items()])
                    runs.append({"run_name": name, **run})
    # Two runs with one name would write into one directory at once.
    names = [r["run_name"] for r in runs]
    clash = sorted({n for n in names if names.count(n) > 1})
    if clash:
        raise ValueError(f"these runs would share a directory: {', '.join(clash[:3])}; use values that name apart")
    return exp_cfg, inv, runs, skipped


def launch(req, launched_by="user"):
    exp_cfg, inv, runs, skipped = plan(req)
    if not runs:
        raise ValueError("nothing to run: every point was skipped" if skipped else "choose at least one value")
    sweep_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-") + secrets.token_hex(2)
    out_root = _sweep_dir(inv["id"], sweep_id)
    out_root.mkdir(parents=True, exist_ok=True)
    submitted, errors = [], []
    for run in runs:
        extra = ["--split dev", "--final_only"] + [
            f"--hparam {shlex.quote(f'{k}={json.dumps(v)}')}" for k, v in {**run["fixed"], **run["overrides"]}.items()]
        try:
            result = slurm._submit_one(exp_cfg, run["params"], run["run_name"], out_root, extra_args=extra)
        except RuntimeError as exc:
            errors.append({"run_name": run["run_name"], "error": str(exc)})
            continue
        db.insert_job(
            job_id=result["job_id"], experiment_type=EXPERIMENT, run_name=run["run_name"],
            params=run["params"], sbatch_path=result["sbatch_path"], out_path=result["out_path"],
            err_path=result["err_path"], out_root=str(out_root), sweep_id=SWEEP_PREFIX + sweep_id,
            investigation=inv["id"], batch_id=sweep_id, label=req.get("label") or "", launched_by=launched_by,
            note=req.get("note") or "")
        submitted.append({k: run[k] for k in ("run_name", "method", "model", "data_path", "overrides", "fixed")}
                         | ({"baseline_for": run["baseline_for"]} if "baseline_for" in run else {})
                         | {"job_id": result["job_id"]})
    (out_root / "sweep.json").write_text(json.dumps({
        "id": sweep_id, "investigation": inv["id"], "label": req.get("label") or "",
        "launched_by": launched_by, "note": req.get("note") or "",
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "request": {k: v for k, v in req.items() if k not in ("label", "note")},
        "split": "dev", "runs": submitted, "skipped": skipped, "errors": errors,
    }, indent=1) + "\n")
    return {"sweep_id": sweep_id, "submitted": len(submitted), "skipped": skipped, "errors": errors}


RETRYABLE = ("FAILED", "CANCELLED", "TIMEOUT", "OUT_OF_MEMORY", "NODE_FAIL", "BOOT_FAIL", "PREEMPTED")


def rerun_failed(investigation, sweep_id):
    """Resubmit every run of a sweep that ended without finishing, with the
    same settings and run name. Earlier job ids are kept per run."""
    exp_cfg = _exp_cfg()
    sweep_dir = _sweep_dir(investigation, sweep_id)
    path = sweep_dir / "sweep.json"
    sweep = json.loads(path.read_text())
    statuses = _statuses([(sweep_dir, sweep)])
    rerun, errors = [], []
    for run in sweep["runs"]:
        if statuses.get(str(run["job_id"]), {}).get("state") not in RETRYABLE:
            continue
        params = slurm._prepare_params(exp_cfg, {
            "method": run["method"], "model": run["model"], "data_path": run["data_path"],
            "ds_size": sweep["request"].get("ds_size", "full"), "edit_mode": sweep["request"].get("edit_mode"),
            "seed": sweep["request"].get("seed", 0), "evaluation_modes": "original"})
        extra = ["--split dev", "--final_only"] + [
            f"--hparam {shlex.quote(f'{k}={json.dumps(v)}')}"
            for k, v in {**(run.get("fixed") or {}), **run["overrides"]}.items()]
        try:
            result = slurm._submit_one(exp_cfg, params, run["run_name"], sweep_dir, extra_args=extra)
        except RuntimeError as exc:
            errors.append({"run_name": run["run_name"], "error": str(exc)})
            continue
        db.insert_job(
            job_id=result["job_id"], experiment_type=EXPERIMENT, run_name=run["run_name"], params=params,
            sbatch_path=result["sbatch_path"], out_path=result["out_path"], err_path=result["err_path"],
            out_root=str(sweep_dir), sweep_id=SWEEP_PREFIX + sweep_id,
            investigation=investigation, batch_id=sweep_id, label=sweep.get("label") or "",
            launched_by=sweep.get("launched_by") or "user", note=sweep.get("note") or "")
        run.setdefault("earlier_jobs", []).append(run["job_id"])
        run["job_id"] = result["job_id"]
        rerun.append(run["run_name"])
    path.write_text(json.dumps(sweep, indent=1) + "\n")
    return {"rerun": rerun, "errors": errors}


def _sweeps(investigation=None):
    root = config.INVESTIGATIONS_DIR
    pattern = f"{investigation}/sweeps/*/sweep.json" if investigation else "*/sweeps/*/sweep.json"
    for path in sorted(root.glob(pattern), reverse=True):
        try:
            yield path.parent, json.loads(path.read_text())
        except (OSError, ValueError):
            continue


def _statuses(sweeps):
    ids = [job for _, sweep in sweeps for run in sweep["runs"]
           for job in [run["job_id"], *run.get("earlier_jobs", [])]]
    try:
        return slurm.sacct_statuses(ids) if ids else {}
    except (RuntimeError, OSError):
        return {}


ACTIVE = ("PENDING", "RUNNING", "REQUEUED", "SUSPENDED", "CONFIGURING", "COMPLETING")

# SLURM's pending reasons in plain words.
PENDING_REASONS = {
    "Priority": "queued behind other waiting jobs (yours or others')",
    "Resources": "waiting for a free GPU",
    "QOSMaxJobsPerUserLimit": "your other jobs are using all of your job slots",
    "AssocMaxJobsLimit": "your other jobs are using all of your job slots",
    "QOSMaxGRESPerUser": "your other jobs are using all of your GPU allowance",
    "Dependency": "waiting for another job to finish",
    "BeginTime": "scheduled to start later",
    "JobHeldUser": "held",
    "JobHeldAdmin": "held by an administrator",
    "ReqNodeNotAvail": "the GPU node is unavailable",
    "PartitionDown": "the partition is down",
}


def _queue(job_ids):
    """Why each pending job is waiting, and SLURM's start estimate."""
    ids = [str(j) for j in job_ids if not str(j).startswith(("local-", "download-"))]
    out = {}
    if ids and shutil.which("squeue"):
        try:
            text = subprocess.run(["squeue", "-h", "-j", ",".join(ids), "-o", "%i|%T|%r|%S"],
                                  capture_output=True, text=True, timeout=10).stdout
        except (OSError, subprocess.SubprocessError):
            text = ""
        for line in text.splitlines():
            parts = line.strip().split("|")
            if len(parts) == 4 and parts[1] == "PENDING":
                reason = parts[2].strip("()")
                out[parts[0]] = {"reason": reason, "reason_text": PENDING_REASONS.get(reason, reason or "queued"),
                                 "start_estimate": None if parts[3] in ("N/A", "") else parts[3]}
    for job_id in job_ids:
        if str(job_id).startswith("local-") and str(job_id) not in out:
            out[str(job_id)] = {"reason": "local", "reason_text": "waiting for the running local job to finish",
                                "start_estimate": None}
    return out


def _run_progress(run_dir, out_path=None):
    """What a running run is doing, from files it already writes: its
    phase, and how far through its facts or training steps it is."""
    hp_path = run_dir / "hparams.yaml"
    if not hp_path.exists():
        return {"phase": "starting", "done": None, "total": None}
    try:
        hp = yaml.safe_load(hp_path.read_text()) or {}
    except (OSError, yaml.YAMLError):
        hp = {}
    total_facts = hp.get("ds_size")
    last = None
    loss_path = run_dir / "loss.jsonl"
    if loss_path.exists():
        lines = _tail_lines(loss_path, 400)
        for line in reversed(lines):
            try:
                last = json.loads(line)
                break
            except ValueError:
                continue
        if last is not None and "fact" in last and total_facts:
            return {"phase": "editing", "unit": "fact", "done": min(int(last["fact"]) + 1, total_facts), "total": total_facts}
        if last is not None and last.get("kind") == "train" and hp.get("num_steps"):
            return {"phase": "training", "unit": "step", "done": int(last["step"]), "total": int(hp["num_steps"])}
    # Nothing logged yet: loading, computing covariance statistics, or the
    # before-editing evaluation.
    tail = "".join(_tail_lines(out_path, 60)) if out_path else ""
    if (run_dir / "checkpoints.jsonl").exists() and (run_dir / "checkpoints.jsonl").stat().st_size:
        phase = "computing covariance statistics" if "Computing Cov locally" in tail else "editing"
    elif "loading model" in tail:
        phase = "evaluating before editing"
    else:
        phase = "loading the model"
    return {"phase": phase, "done": None, "total": total_facts}


def _run_states(sweep_dir, sweep, statuses, queue, jobs):
    exp_cfg = _exp_cfg()
    rows = []
    for position, run in enumerate(sweep["runs"], 1):
        benchmark, subset = slurm._dataset_meta(exp_cfg, {"data_path": run["data_path"]})
        job_id = str(run["job_id"])
        state = statuses.get(job_id, {}).get("state", "UNKNOWN")
        row = {"position": position, "run": run["run_name"], "method": run["method"], "model": run["model"],
               "data_path": run["data_path"], "dataset_short": subset or Path(run["data_path"]).stem, "overrides": run["overrides"], "fixed": run.get("fixed") or {},
               "job_id": job_id, "state": state, "elapsed_sec": _seconds(statuses.get(job_id, {}).get("elapsed"))}
        if state == "PENDING":
            row["waiting"] = queue.get(job_id)
        elif state == "RUNNING":
            row["progress"] = _run_progress(sweep_dir / "runs" / run["run_name"], jobs.get(job_id, {}).get("out_path"))
        rows.append(row)
    return rows


def _overall(rows):
    """0..1 across the sweep: finished runs count fully, running ones by
    their own progress where it is known."""
    if not rows:
        return 0.0
    total = 0.0
    for r in rows:
        if r["state"] not in ACTIVE:
            total += 1
        elif r.get("progress", {}).get("done") and r["progress"].get("total"):
            total += r["progress"]["done"] / r["progress"]["total"]
    return round(total / len(rows), 4)


def list_sweeps(investigation=None, include_hidden=False):
    sweeps = [(d, s) for d, s in _sweeps(investigation) if include_hidden or not s.get("hidden")]
    statuses = _statuses(sweeps)
    pending = [str(r["job_id"]) for _, s in sweeps for r in s["runs"]
               if statuses.get(str(r["job_id"]), {}).get("state") == "PENDING"]
    queue = _queue(pending)
    jobs = {str(j["job_id"]): j for j in db.list_jobs(include_cleared=True)} if any(
        statuses.get(str(r["job_id"]), {}).get("state") == "RUNNING" for _, s in sweeps for r in s["runs"]) else {}
    out = []
    for sweep_dir, sweep in sweeps:
        counts = {}
        for run in sweep["runs"]:
            state = statuses.get(str(run["job_id"]), {}).get("state", "UNKNOWN")
            counts[state] = counts.get(state, 0) + 1
        counts_retry = sum(c for state, c in counts.items() if state in RETRYABLE)
        # Scheduler time of every run so far (finished or not), for the sweep's cost.
        gpu_seconds = sum(_seconds(statuses.get(str(r["job_id"]), {}).get("elapsed")) or 0 for r in sweep["runs"])
        runs = _run_states(sweep_dir, sweep, statuses, queue, jobs)
        waiting = [r for r in runs if r["state"] == "PENDING"]
        reasons = {}
        for r in waiting:
            text = (r.get("waiting") or {}).get("reason_text", "queued")
            reasons[text] = reasons.get(text, 0) + 1
        out.append({k: sweep[k] for k in ("id", "investigation", "label", "created_at")}
                   | {"launched_by": sweep.get("launched_by") or "user", "note": sweep.get("note") or ""}
                   | {"hidden": bool(sweep.get("hidden")), "retryable": counts_retry, "gpu_seconds": gpu_seconds}
                   | {"runs": len(sweep["runs"]), "states": counts, "skipped": len(sweep.get("skipped", [])),
                      "methods": sorted({r["method"] for r in sweep["runs"]}),
                      "models": sorted({r["model"] for r in sweep["runs"]}),
                      "active": sum(1 for r in runs if r["state"] in ACTIVE),
                      "finished": sum(1 for r in runs if r["state"] not in ACTIVE),
                      "overall": _overall(runs),
                      "running": [r for r in runs if r["state"] == "RUNNING"],
                      "waiting": [{"text": t, "count": c} for t, c in reasons.items()],
                      "start_estimate": min((w["waiting"] or {}).get("start_estimate") or "9999" for w in waiting)
                      if waiting else None})
    for row in out:
        if row["start_estimate"] == "9999":
            row["start_estimate"] = None
    return out


def find_sweep(sweep_id):
    """(investigation, sweep.json contents) of a sweep by id alone, or None."""
    for _, sweep in _sweeps():
        if sweep.get("id") == sweep_id:
            return sweep["investigation"], sweep
    return None


def sweep_owner(investigation, sweep_id):
    """Who launched a sweep: "user" or "agent" (sweeps from before this was
    recorded count as the user's)."""
    path = _sweep_dir(investigation, sweep_id) / "sweep.json"
    if not path.exists():
        raise KeyError(sweep_id)
    return json.loads(path.read_text()).get("launched_by") or "user"


def sweep_detail(investigation, sweep_id):
    """Everything about one sweep: its full request, what was skipped, and
    every run with its state, waiting reason or progress, scores and error."""
    sweep_dir = _sweep_dir(investigation, sweep_id)
    path = sweep_dir / "sweep.json"
    if not path.exists():
        raise KeyError(sweep_id)
    sweep = json.loads(path.read_text())
    statuses = _statuses([(sweep_dir, sweep)])
    pending = [str(r["job_id"]) for r in sweep["runs"] if statuses.get(str(r["job_id"]), {}).get("state") == "PENDING"]
    jobs = {str(j["job_id"]): j for j in db.list_jobs(include_cleared=True)}
    runs = _run_states(sweep_dir, sweep, statuses, _queue(pending), jobs)
    scored = {r["run"]: r for r in results(investigation) if r["sweep_id"] == sweep_id}
    for run in runs:
        extra = scored.get(run["run"], {})
        run.update({k: extra.get(k) for k in ("scores", "dataset", "model_label", "model_variant",
                                               "model_type", "wall_sec", "total_sec", "records", "error",
                                               "flags", "loss", "earlier")})
    labels = {i["id"]: i["label"] for i in _load_catalog()["investigations"]}
    return {"id": sweep["id"], "investigation": investigation, "investigation_label": labels.get(investigation),
            "label": sweep.get("label"), "created_at": sweep.get("created_at"), "request": sweep["request"],
            "skipped": sweep.get("skipped", []), "errors": sweep.get("errors", []), "runs": runs,
            "overall": _overall(runs)}


def set_hidden(investigation, sweep_id, hidden):
    """Clear a finished sweep off the sweep lists, or bring it back. Only a
    flag in sweep.json changes: its runs stay where they are and keep
    showing on Results · Investigations."""
    sweep_dir = _sweep_dir(investigation, sweep_id)
    path = sweep_dir / "sweep.json"
    if not path.exists():
        raise KeyError(sweep_id)
    sweep = json.loads(path.read_text())
    if hidden:
        statuses = _statuses([(sweep_dir, sweep)])
        if any(statuses.get(str(r["job_id"]), {}).get("state") in ACTIVE for r in sweep["runs"]):
            raise ValueError("this sweep still has queued or running runs: cancel them first")
        sweep["hidden"] = True
        sweep["hidden_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    else:
        sweep.pop("hidden", None)
        sweep.pop("hidden_at", None)
    path.write_text(json.dumps(sweep, indent=1) + "\n")
    return {"hidden": hidden}


def delete_sweep(investigation, sweep_id):
    """Take a sweep off every page. Refused while any run is queued or
    running. Moved to <investigation>/deleted/, not erased, so it can be
    put back by moving the folder back into sweeps/."""
    sweep_dir = _sweep_dir(investigation, sweep_id)
    if not (sweep_dir / "sweep.json").exists():
        raise KeyError(sweep_id)
    sweep = json.loads((sweep_dir / "sweep.json").read_text())
    statuses = _statuses([(sweep_dir, sweep)])
    if any(statuses.get(str(r["job_id"]), {}).get("state") in ACTIVE for r in sweep["runs"]):
        raise ValueError("this sweep still has queued or running runs: cancel them first")
    trash = config.INVESTIGATIONS_DIR / investigation / "deleted"
    trash.mkdir(parents=True, exist_ok=True)
    target = trash / f"{sweep_id}--deleted-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    shutil.move(str(sweep_dir), str(target))
    return {"moved_to": str(target.relative_to(config.PROJECT_ROOT))}


def _first_row(path):
    try:
        with open(path) as handle:
            line = handle.readline()
        return json.loads(line) if line.strip() else None
    except (OSError, ValueError):
        return None


def _scores(summary, baseline):
    """The four criteria on 0..1 (None where the dataset has no such probe)."""
    pct = lambda v: None if v is None else v / 100.0
    fluency = summary.get("fluency")
    base = (baseline or {}).get("fluency")
    ratio = min(fluency / base, 1.0) if fluency is not None and base else None
    return {"fluency": ratio, "reliability": pct(summary.get("edit_succ")),
            "locality": pct(summary.get("locality")), "generalizability": pct(summary.get("portability"))}


# Lines in a job's stderr that are noise rather than the reason it failed.
_NOISE = re.compile(r"Warning|warnings\.warn|it/s\]|s/it\]|%\||TOKENIZERS_PARALLELISM|huggingface/tokenizers|"
                    r"Avoid using `tokenizers`|Explicitly set the environment")
_ERROR = re.compile(r"^(\w+\.)*\w*(Error|Exception|Exit)\b|^RuntimeError|^error:|CUDA out of memory")
FLUENCY_DROP = 0.85  # flag when fluency falls below this share of the unedited model's


def _keeps_fluency(scores):
    """A scored run whose fluency did not drop (no fluency probe counts as kept)."""
    fluency = (scores or {}).get("fluency")
    return (scores or {}).get("reliability") is not None and (fluency is None or fluency >= FLUENCY_DROP)


def _tail_lines(path, n=300):
    try:
        with open(path, errors="replace") as handle:
            return handle.readlines()[-n:]
    except (OSError, TypeError):
        return []


def _error_line(err_path):
    """The most telling line of a failed run's stderr, without warnings and
    progress bars: the exception if there is one, else the last real line."""
    lines = [l.strip() for l in _tail_lines(err_path) if l.strip() and not _NOISE.search(l)]
    errors = [l for l in lines if _ERROR.search(l)]
    line = errors[-1] if errors else (lines[-1] if lines else "")
    return line[:400]


def _downsample(values, limit=40):
    if len(values) <= limit:
        return values
    stride = len(values) / limit
    return [values[int(i * stride)] for i in range(limit)] + [values[-1]]


def _loss_summary(run_dir):
    """A run's loss.jsonl reduced to what the table shows: the curve (mean
    over facts at each step), first and last values, NaN, and for
    value-vector optimisation the new answer's final probability."""
    path = run_dir / "loss.jsonl"
    if not path.exists():
        return None
    by_step, last_prob, has_nan, kinds = {}, {}, False, set()
    with open(path) as handle:
        for line in handle:
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            kinds.add(entry.get("kind"))
            value = entry.get("loss")
            if isinstance(value, str):
                has_nan = True
                continue
            if value is None:
                continue
            by_step.setdefault(entry["step"], []).append(value)
            if entry.get("target_prob") is not None and isinstance(entry["target_prob"], (int, float)):
                last_prob[entry.get("fact", 0)] = entry["target_prob"]
    if not by_step and not has_nan:
        return None
    curve = [sum(v) / len(v) for _, v in sorted(by_step.items())]
    return {
        "kind": "value_vector" if "value_vector" in kinds else "train",
        "curve": [round(v, 4) for v in _downsample(curve)],
        "first": round(curve[0], 4) if curve else None,
        "last": round(curve[-1], 4) if curve else None,
        "nan": has_nan,
        "final_prob": round(sum(last_prob.values()) / len(last_prob), 4) if last_prob else None,
    }


def _flags(state, error, loss, scores):
    flags = []
    if error and "out of memory" in error.lower():
        flags.append({"level": "error", "text": "out of GPU memory"})
    elif state == "FAILED" and error:
        flags.append({"level": "error", "text": "failed"})
    if loss:
        if loss["nan"]:
            flags.append({"level": "error", "text": "loss became NaN"})
        elif loss["first"] is not None and loss["last"] is not None and loss["last"] > loss["first"] * 1.05:
            flags.append({"level": "warn", "text": "loss rose"})
        if loss["final_prob"] is not None and loss["final_prob"] < 0.1:
            flags.append({"level": "warn", "text": f"target probability only {loss['final_prob']:.2f} after optimisation"})
    fluency = (scores or {}).get("fluency")
    if fluency is not None and fluency < FLUENCY_DROP:
        flags.append({"level": "warn", "text": f"fluency fell {round((1 - fluency) * 100)}%"})
    return flags


def _seconds(clock):
    """sacct's [D-]HH:MM:SS (or MM:SS) as seconds."""
    if not clock:
        return None
    days, _, rest = clock.rpartition("-")
    parts = [int(p) for p in rest.split(":") if p.isdigit()]
    while len(parts) < 3:
        parts.insert(0, 0)
    return (int(days) if days else 0) * 86400 + parts[0] * 3600 + parts[1] * 60 + parts[2]


def _wall_seconds(summary):
    """Start to finish, model load included (total_sec starts after it)."""
    try:
        start = datetime.fromisoformat(summary["started_at"])
        end = datetime.fromisoformat(summary["finished_at"])
    except (KeyError, TypeError, ValueError):
        return None
    return round((end - start).total_seconds(), 1)


def protocol_label(mode, reset_every=None, batch_size=None):
    """The editing protocol in words (see edit_protocol.py)."""
    if not mode:
        return "no protocol (older runs)"
    if mode == "single":
        return "single"
    if mode == "batch":
        return f"batch of {batch_size}"
    if mode == "sequential":
        return f"sequential, reset every {reset_every}"
    return f"batches of {batch_size}, reset every {reset_every}"


def _protocol(exp_cfg, request, summary):
    """A run's protocol: from its summary when finished, else what its sweep
    asked for (reset interval and batch size at the page's defaults)."""
    if summary:
        mode, reset, batch = summary.get("edit_mode"), summary.get("reset_every"), summary.get("edit_batch_size")
    else:
        params = slurm._prepare_params(exp_cfg, {"edit_mode": request.get("edit_mode"), "evaluation_modes": "original"})
        mode, reset, batch = params.get("edit_mode"), params.get("reset_every"), params.get("edit_batch_size")
        reset = reset if mode in ("sequential", "sequential_batch") else None
        batch = batch if mode in ("batch", "sequential_batch") else None
    return {"edit_mode": mode, "reset_every": reset, "edit_batch_size": batch,
            "label": protocol_label(mode, reset, batch)}


MODEL_TYPE_LABEL = {"raw": "base", "chat": "instruct", "reasoning": "reasoning"}


def _model_info(exp_cfg):
    """Model value -> display name, tuning stage, type and family, from the
    picker's own catalog (dashboard.json)."""
    field = next(f for f in exp_cfg["fields"] if f["name"] == "model")
    family = {m: fam["label"] for fam in field.get("families", []) for m in fam["models"]}
    return {o["value"]: {"label": o.get("label", o["value"]), "variant": o.get("variant"),
                         "type": MODEL_TYPE_LABEL.get(o.get("model_type"), o.get("model_type")),
                         "family": family.get(o["value"], o.get("label", o["value"]))}
            for o in field["options"]}


def results(investigation, include_hidden=True):
    """One row per run of every sweep in an investigation."""
    exp_cfg = _exp_cfg()
    models = _model_info(exp_cfg)
    sweeps = [(d, s) for d, s in _sweeps(investigation) if include_hidden or not s.get("hidden")]
    statuses = _statuses(sweeps)
    jobs = {str(j["job_id"]): j for j in db.list_jobs(include_cleared=True)}
    rows = []
    for sweep_dir, sweep in sweeps:
        for run in sweep["runs"]:
            run_dir = sweep_dir / "runs" / run["run_name"]
            summary_path = run_dir / "summary.json"
            summary = json.loads(summary_path.read_text()) if summary_path.exists() else None
            baseline = _first_row(run_dir / "checkpoints.jsonl")
            scores = _scores(summary, baseline) if summary else {}
            benchmark, subset = slurm._dataset_meta(exp_cfg, {"data_path": run["data_path"]})
            state = statuses.get(str(run["job_id"]), {}).get("state", "UNKNOWN")
            job = jobs.get(str(run["job_id"]), {})
            error = _error_line(job.get("err_path")) if state in ("FAILED", "OUT_OF_MEMORY", "CANCELLED", "TIMEOUT") else None
            loss = _loss_summary(run_dir)
            # Earlier attempts replaced by "Rerun failed", with why each ended.
            earlier = []
            for job_id in run.get("earlier_jobs", []):
                old_state = statuses.get(str(job_id), {}).get("state", "UNKNOWN")
                old_job = jobs.get(str(job_id), {})
                earlier.append({"job_id": str(job_id), "state": old_state,
                                "error": _error_line(old_job.get("err_path")),
                                "submitted_at": old_job.get("submitted_at")})
            # A one-at-a-time sweep's run at the current settings is every
            # swept setting's current value: one row per setting, so each
            # setting's comparison includes it (copies after the first are
            # marked, so failures and counts see the run once).
            shown = [({k: v}, i > 0) for i, (k, v) in enumerate(run["baseline_for"].items())] \
                if run.get("baseline_for") else [(run["overrides"], False)]
            for overrides, copy in shown:
                rows.append({
                    "sweep_id": sweep["id"], "sweep_label": sweep.get("label", ""), "run": run["run_name"],
                    "method": run["method"], "model": run["model"], "data_path": run["data_path"],
                    # Each tuning stage is its own model value, so runs never
                    # overwrite each other; these say which stage it is.
                    "model_label": models.get(run["model"], {}).get("label", run["model"]),
                    "model_variant": models.get(run["model"], {}).get("variant"),
                    "model_type": models.get(run["model"], {}).get("type"),
                    "model_family": models.get(run["model"], {}).get("family"),
                    # Single, batch and sequential runs live in separate sweeps and
                    # never overwrite each other; this keeps them apart in tables.
                    **(lambda p: {"protocol": p["label"], "protocol_detail": p})(_protocol(exp_cfg, sweep["request"], summary)),
                    "dataset": f"{benchmark} / {subset}" if benchmark else Path(run["data_path"]).stem,
                    "overrides": overrides, "fixed": run.get("fixed") or {},
                    "current_settings": bool(run.get("baseline_for")), "baseline_copy": copy,
                    "state": state, "job_id": str(run["job_id"]), "error": error, "loss": loss,
                    "flags": _flags(state, error, loss, scores),
                    "earlier": earlier, "submitted_at": job.get("submitted_at"),
                    "investigation": investigation,
                    # Its current failure was cleared off the Failures view.
                    "failure_cleared": str(run["job_id"]) in map(str, run.get("cleared_failures", [])),
                    "records": summary.get("ds_size") if summary else None,
                    "scores": scores,
                    "fluency_raw": summary.get("fluency") if summary else None,
                    "fluency_baseline": (baseline or {}).get("fluency"),
                    # Time: editing and evaluation (after the model loaded), the
                    # whole run start to finish, and for unfinished runs what
                    # the scheduler reports so far.
                    "total_sec": summary.get("total_sec") if summary else None,
                    "wall_sec": _wall_seconds(summary) if summary else None,
                    "elapsed_sec": _seconds(statuses.get(str(run["job_id"]), {}).get("elapsed")),
                })
    return rows


def failures():
    """Across every investigation: runs that are failing now (ended without
    finishing, or finished with an error flag such as a NaN loss), and runs
    that failed before and were fixed by a rerun."""
    labels = {i["id"]: i["label"] for i in _load_catalog()["investigations"]}
    open_rows, resolved = [], []
    for investigation in labels:
        # Hidden sweeps and cleared failures stay off this list.
        for row in results(investigation, include_hidden=False):
            if row["failure_cleared"] or row["baseline_copy"]:
                continue
            row["investigation_label"] = labels[investigation]
            failing = row["state"] in RETRYABLE or any(f["level"] == "error" for f in row["flags"])
            if failing:
                open_rows.append(row)
            elif any(e["state"] in RETRYABLE for e in row["earlier"]):
                resolved.append(row)
    newest = lambda r: r.get("submitted_at") or ""
    return {"open": sorted(open_rows, key=newest, reverse=True),
            "resolved": sorted(resolved, key=newest, reverse=True)}


def clear_failures():
    """Clear the Failures view: each failing run's current attempt is marked
    cleared (a later rerun that fails shows again), and every listed run's
    earlier attempts move to cleared_earlier_jobs, so neither is listed or
    polled again. Everything stays in sweep.json."""
    listed = failures()
    by_sweep = {}
    for row in listed["open"] + listed["resolved"]:
        by_sweep.setdefault((row["investigation"], row["sweep_id"]), {})[row["run"]] = row
    for (investigation, sweep_id), rows in by_sweep.items():
        path = _sweep_dir(investigation, sweep_id) / "sweep.json"
        sweep = json.loads(path.read_text())
        for run in sweep["runs"]:
            row = rows.get(run["run_name"])
            if not row:
                continue
            if str(row["job_id"]) == str(run["job_id"]) and row["state"] not in ACTIVE:
                run.setdefault("cleared_failures", []).append(run["job_id"])
            if run.get("earlier_jobs"):
                run.setdefault("cleared_earlier_jobs", []).extend(run.pop("earlier_jobs"))
        path.write_text(json.dumps(sweep, indent=1) + "\n")
    return {"cleared": len(listed["open"]) + len(listed["resolved"])}


def hide_finished(investigation=None):
    """Hide every sweep with nothing queued or running (see set_hidden);
    sweeps still going are left alone. Returns how many were hidden."""
    sweeps = [(d, s) for d, s in _sweeps(investigation) if not s.get("hidden")]
    statuses = _statuses(sweeps)
    hidden = 0
    for sweep_dir, sweep in sweeps:
        if any(statuses.get(str(r["job_id"]), {}).get("state") in ACTIVE for r in sweep["runs"]):
            continue
        sweep["hidden"] = True
        sweep["hidden_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
        (sweep_dir / "sweep.json").write_text(json.dumps(sweep, indent=1) + "\n")
        hidden += 1
    return hidden


def hidden_count(investigation=None):
    """How many sweeps are hidden, without asking SLURM about them."""
    return sum(1 for _, s in _sweeps(investigation) if s.get("hidden"))


def _yaml_value(value):
    return json.dumps(value)


def promote(investigation, sweep_id, run_name):
    """Write a run's swept values into its method's hparams file for that
    model, so main experiments use them, and record where they came from."""
    sweep_dir = _sweep_dir(investigation, sweep_id)
    sweep = json.loads((sweep_dir / "sweep.json").read_text())
    run = next((r for r in sweep["runs"] if r["run_name"] == run_name), None)
    if run is None:
        raise KeyError(run_name)
    if not (sweep_dir / "runs" / run_name / "summary.json").exists():
        raise ValueError("this run has not finished")
    path = _hparams_file(run["method"], run["model"])
    lines = path.read_text().splitlines()
    for key, value in run["overrides"].items():
        pattern = re.compile(rf"^{re.escape(key)}\s*:")
        line = f"{key}: {_yaml_value(value)}  # tuned: sweep {sweep_id} ({investigation})"
        for i, existing in enumerate(lines):
            if pattern.match(existing):
                lines[i] = line
                break
        else:
            lines.append(line)
    path.write_text("\n".join(lines) + "\n")
    record = tuned()
    stamp = datetime.now().astimezone().isoformat(timespec="seconds")
    for key, value in run["overrides"].items():
        record.setdefault(run["method"], {}).setdefault(run["model"], {})[key] = {
            "value": value, "investigation": investigation, "sweep": sweep_id, "run": run_name, "at": stamp}
    TUNED_PATH.write_text(json.dumps(record, indent=1, sort_keys=True) + "\n")
    return {"file": str(path.relative_to(config.PROJECT_ROOT)), "settings": run["overrides"]}


def estimate(req):
    """Rough cost before launching: runs, GPU-hours, missing covariance stats."""
    _, inv, runs, skipped = plan(req)
    per_record = {"ft": 1.0, "lora": 1.5, "fine": 20, "cake": 60, "kn": 25, "ike": 3, "scr": 3}
    records = req.get("ds_size", "full")
    n = 100 if records in ("full", None) else int(records)
    seconds = sum(90 + n * per_record.get(r["method"], 15) for r in runs)
    missing = set()
    for r in runs:
        hp = _read_hparams(r["method"], r["model"]) or {}
        if not hp.get("mom2_adjustment") and r["method"] not in ("memit", "pmet", "alphaedit", "nmke"):
            continue
        layers = r["overrides"].get("layers", hp.get("layers") or [])
        samples = r["overrides"].get("mom2_n_samples", hp.get("mom2_n_samples"))
        template = hp.get("rewrite_module_tmp")
        if not template or not samples:
            continue
        directory = Path(str(hp.get("model_name", ""))).name
        stats = config.EXPERIMENTS_DIR / "run_experiment" / "data" / "stats" / directory / "wikipedia_stats"
        dtype = hp.get("mom2_dtype", "float32")
        for layer in layers:
            name = f"{template.format(layer)}_{dtype}_mom2_{samples}.npz"
            if not (stats / name).exists():
                missing.add((directory, layer, samples))
    seconds += 600 * len(missing)
    return {"runs": len(runs), "skipped": skipped, "gpu_hours": round(seconds / 3600, 1),
            "missing_stats": [{"model": m, "layer": l, "samples": s} for m, l, s in sorted(missing)],
            "note": "rough: assumes 100 dev records and typical per-edit times; covariance statistics about 10 minutes per layer"}
