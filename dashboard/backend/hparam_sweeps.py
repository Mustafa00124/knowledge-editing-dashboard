"""Hyperparameter investigations: catalog, sweep launches, results, promotion.

An investigation is one kind of setting (experiments/run_experiment/
investigations.json) and the methods that have it. A sweep varies one or
more of those settings for chosen methods, models and datasets; every
point is an ordinary run_experiment job (same submission path, logs and
job table as the Experiments page) with three differences: it edits dev
records only (--split dev), evaluates only before editing and at the end
(--final_only), and passes the swept values as --hparam overrides.

On disk, one folder per sweep:
    results/hyperparameters/<investigation>/sweeps/<sweep_id>/
        sweep.json          what was varied and fixed, and every run's job id
        runs/<run>/...      the runner's usual files (hparams, checkpoints, summary)

Scores for ranking are the four criteria on a 0..1 scale: reliability
(edit success), generalizability (portability), locality, and fluency as
the final value over the unedited model's (step 0), capped at 1. The
default ranking is by the weakest of those a run has, so a configuration
cannot rank well by giving one of them up.
"""
import itertools
import json
import re
import secrets
import shlex
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
INT_FACTORS = (0.5, 1, 2)


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


def _traced_peak(model):
    path = config.HPARAM_RESULTS_DIR / "edit_layers" / "causal_tracing" / "traced_layers.json"
    if not path.exists():
        return None
    entry = json.loads(path.read_text()).get(model)
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
    return [default]


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
                    hp = _read_hparams(method, model)
                    if hp is None or key not in hp:
                        continue
                    defaults[model] = hp[key]
                    suggestions[model] = suggest(spec["kind"], hp[key], spec, model)
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
        out.append({**{k: v for k, v in inv.items() if k != "methods"}, "methods": methods})
    return out


def _sweep_dir(investigation, sweep_id):
    return config.HPARAM_RESULTS_DIR / investigation / "sweeps" / sweep_id


def _slug(value):
    text = json.dumps(value) if not isinstance(value, str) else value
    return re.sub(r"[^A-Za-z0-9.]+", "-", text).strip("-") or "x"


def _dataset_slug(exp_cfg, data_path):
    _, subset = slurm._dataset_meta(exp_cfg, {"data_path": data_path})
    return slurm._slug(subset or Path(data_path).stem)


def _grid(knob_values):
    keys = sorted(knob_values)
    for combo in itertools.product(*(knob_values[k] for k in keys)):
        yield dict(zip(keys, combo))


def plan(req):
    """Every run a launch request would submit, and every point skipped with
    the reason, without submitting anything."""
    exp_cfg = _exp_cfg()
    inv = next((i for i in _load_catalog()["investigations"] if i["id"] == req["investigation"]), None)
    if inv is None:
        raise ValueError(f"unknown investigation {req['investigation']!r}")
    runs, skipped = [], []
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
            for data_path in req["data_paths"]:
                params = slurm._prepare_params(exp_cfg, {
                    "method": method, "model": model, "data_path": data_path,
                    "ds_size": req.get("ds_size", "full"), "edit_mode": req.get("edit_mode"),
                    "seed": req.get("seed", 0), "evaluation_modes": "original",
                })
                if not slurm._combo_supported(exp_cfg, params):
                    skipped.append({"method": method, "model": model, "data_path": data_path,
                                    "reason": "this method cannot run on this dataset"})
                    continue
                for overrides in _grid(knob_values):
                    name = "_".join([method, model, _dataset_slug(exp_cfg, data_path)]
                                    + [f"{k}{_slug(v)}" for k, v in overrides.items()])
                    runs.append({"run_name": name, "method": method, "model": model,
                                 "data_path": data_path, "overrides": overrides, "params": params})
    return exp_cfg, inv, runs, skipped


def launch(req):
    exp_cfg, inv, runs, skipped = plan(req)
    if not runs:
        raise ValueError("nothing to run: every point was skipped" if skipped else "choose at least one value")
    sweep_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-") + secrets.token_hex(2)
    out_root = _sweep_dir(inv["id"], sweep_id)
    out_root.mkdir(parents=True, exist_ok=True)
    submitted, errors = [], []
    for run in runs:
        extra = ["--split dev", "--final_only"] + [
            f"--hparam {shlex.quote(f'{k}={json.dumps(v)}')}" for k, v in run["overrides"].items()]
        try:
            result = slurm._submit_one(exp_cfg, run["params"], run["run_name"], out_root, extra_args=extra)
        except RuntimeError as exc:
            errors.append({"run_name": run["run_name"], "error": str(exc)})
            continue
        db.insert_job(
            job_id=result["job_id"], experiment_type=EXPERIMENT, run_name=run["run_name"],
            params=run["params"], sbatch_path=result["sbatch_path"], out_path=result["out_path"],
            err_path=result["err_path"], out_root=str(out_root), sweep_id=SWEEP_PREFIX + sweep_id)
        submitted.append({k: run[k] for k in ("run_name", "method", "model", "data_path", "overrides")}
                         | {"job_id": result["job_id"]})
    (out_root / "sweep.json").write_text(json.dumps({
        "id": sweep_id, "investigation": inv["id"], "label": req.get("label") or "",
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "request": {k: v for k, v in req.items() if k != "label"},
        "split": "dev", "runs": submitted, "skipped": skipped, "errors": errors,
    }, indent=1) + "\n")
    return {"sweep_id": sweep_id, "submitted": len(submitted), "skipped": skipped, "errors": errors}


def _sweeps(investigation=None):
    root = config.HPARAM_RESULTS_DIR
    pattern = f"{investigation}/sweeps/*/sweep.json" if investigation else "*/sweeps/*/sweep.json"
    for path in sorted(root.glob(pattern), reverse=True):
        try:
            yield path.parent, json.loads(path.read_text())
        except (OSError, ValueError):
            continue


def _statuses(sweeps):
    ids = [run["job_id"] for _, sweep in sweeps for run in sweep["runs"]]
    try:
        return slurm.sacct_statuses(ids) if ids else {}
    except (RuntimeError, OSError):
        return {}


def list_sweeps(investigation=None):
    sweeps = list(_sweeps(investigation))
    statuses = _statuses(sweeps)
    out = []
    for _, sweep in sweeps:
        counts = {}
        for run in sweep["runs"]:
            state = statuses.get(str(run["job_id"]), {}).get("state", "UNKNOWN")
            counts[state] = counts.get(state, 0) + 1
        out.append({k: sweep[k] for k in ("id", "investigation", "label", "created_at")}
                   | {"runs": len(sweep["runs"]), "states": counts, "skipped": len(sweep.get("skipped", [])),
                      "methods": sorted({r["method"] for r in sweep["runs"]}),
                      "models": sorted({r["model"] for r in sweep["runs"]})})
    return out


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
    scores = {"reliability": pct(summary.get("edit_succ")), "generalizability": pct(summary.get("portability")),
              "locality": pct(summary.get("locality")), "fluency": ratio}
    present = [v for v in scores.values() if v is not None]
    return scores, (min(present) if present else None)


def results(investigation):
    """One row per run of every sweep in an investigation."""
    exp_cfg = _exp_cfg()
    sweeps = list(_sweeps(investigation))
    statuses = _statuses(sweeps)
    rows = []
    for sweep_dir, sweep in sweeps:
        for run in sweep["runs"]:
            run_dir = sweep_dir / "runs" / run["run_name"]
            summary_path = run_dir / "summary.json"
            summary = json.loads(summary_path.read_text()) if summary_path.exists() else None
            baseline = _first_row(run_dir / "checkpoints.jsonl")
            scores, worst = _scores(summary, baseline) if summary else ({}, None)
            benchmark, subset = slurm._dataset_meta(exp_cfg, {"data_path": run["data_path"]})
            rows.append({
                "sweep_id": sweep["id"], "sweep_label": sweep.get("label", ""), "run": run["run_name"],
                "method": run["method"], "model": run["model"], "data_path": run["data_path"],
                "dataset": f"{benchmark} / {subset}" if benchmark else Path(run["data_path"]).stem,
                "overrides": run["overrides"],
                "state": statuses.get(str(run["job_id"]), {}).get("state", "UNKNOWN"),
                "records": summary.get("ds_size") if summary else None,
                "scores": scores, "worst": worst,
                "fluency_raw": summary.get("fluency") if summary else None,
                "fluency_baseline": (baseline or {}).get("fluency"),
                "total_sec": summary.get("total_sec") if summary else None,
            })
    return rows


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
