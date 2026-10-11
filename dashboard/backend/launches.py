"""Launches: every batch of jobs submitted at once, whichever way it came in.

A hyperparameter sweep (hparam_sweeps.py, its own sweep.json) and a plain
experiment submission (POST /api/experiments, a row per job in the jobs
table) are both a launch here, summarised the same way: how many runs,
their states, overall progress, what each running run is doing and why
waiting ones wait. Each investigation page's progress section and the
agent CLI (scripts/dash.py) read this one view, so a launch shows up the
same way whether a person clicked it or an agent sent it.

Also here: turning an agent's arguments into fields (resolve_params), the
investigation a launch belongs to, and a dry run that shows what would be
submitted.
"""
import json
import secrets
import shlex
from datetime import datetime, timedelta, timezone
from pathlib import Path

import db
import environment
import hparam_sweeps
import registry
import slurm

# Flags the dashboard sets itself on every run; never taken from a request.
RESERVED_FLAGS = {"run_name", "out_root", "dataset_benchmark", "dataset_subset", "untracked"}

# The investigation a launch of each experiment type is for, when the
# request does not say. Causal tracing in a format other than completion is
# the prompt format investigation; see default_investigation().
DEFAULT_INVESTIGATION = {
    "causal_tracing": "causal_tracing",
    "neuron_tracing": "neuron_tracing",
    "circuit_tracing": "circuit_tracing",
    "fact_selection": "causal_tracing",
    "format_knowledge": "format_knowledge",
    # Not an investigation: the second kind of main experiment, with its own
    # page and progress section (Experiments -> In context).
    "in_context": "in_context",
    # Not an investigation either: the pre-edit check of Sid's Dataset, with
    # its own page (Model audit).
    "model_audit": "model_audit",
}

ACTIVE = hparam_sweeps.ACTIVE
FAILED = set(hparam_sweeps.RETRYABLE)


def new_batch_id():
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-") + secrets.token_hex(2)


def investigations():
    return {i["id"]: i for i in hparam_sweeps._load_catalog()["investigations"]}


def default_investigation(experiment_type, param_lists):
    if experiment_type == "causal_tracing":
        formats = [f for f in (param_lists.get("format") or []) if f not in (None, "")]
        if any(f != "completion" for f in formats):
            return "tracing_formats"
    return DEFAULT_INVESTIGATION.get(experiment_type)


def check_investigation(investigation, experiment_type, param_lists):
    """The investigation a launch is recorded under. None is a main
    experiment (run_experiment through the queue or the API)."""
    if not investigation:
        return default_investigation(experiment_type, param_lists)
    known = investigations()
    if investigation not in known:
        raise ValueError(f"unknown investigation {investigation!r}; one of: {', '.join(sorted(known))}")
    inv = known[investigation]
    if inv.get("status") == "planned":
        raise ValueError(f"{inv['label']} is planned, not built yet")
    if inv.get("group") == "sweep" or inv.get("methods"):
        # Method sweeps must go through the sweep path, which holds them to
        # dev records and records what was swept.
        raise ValueError(f"{inv['label']} is a hyperparameter sweep: launch it with POST /api/hparams/sweeps "
                         "(scripts/dash.py sweep), which runs on dev records only")
    return investigation


# ---------------------------------------------------------------- arguments

def _flag_groups(tokens):
    """['--a', '1', '--b=2', '--c'] -> [('a', ['1']), ('b', ['2']), ('c', [])]."""
    groups = []
    for token in tokens:
        if token.startswith("--"):
            name, eq, value = token[2:].partition("=")
            if not name:
                raise ValueError(f"bad flag {token!r}")
            groups.append((name, [value] if eq else []))
        elif groups:
            groups[-1][1].append(token)
        else:
            raise ValueError(f"{token!r} comes before any --flag")
    return groups


def parse_args_string(exp_cfg, text):
    """Arguments written as on the runner's command line, split into form
    fields (name -> values; a flag given more than once is swept) and flags
    the experiment type has no field for (left for extra_args)."""
    fields = {f["name"]: f for f in exp_cfg["fields"]}
    params, unknown = {}, []
    for name, values in _flag_groups(shlex.split(text or "")):
        if name in fields:
            if len(values) != 1:
                raise ValueError(f"--{name} takes one value (repeat the flag to sweep it)")
            params.setdefault(name, []).append(values[0])
        else:
            unknown.append((name, values))
    return params, unknown


def normalise_extra_args(exp_cfg, extra_args, from_args=()):
    """Quoted "--flag value" strings for flags with no form field."""
    fields = {f["name"] for f in exp_cfg["fields"]}
    groups = list(from_args)
    for item in extra_args or []:
        groups.extend(_flag_groups(shlex.split(item)))
    out = []
    for name, values in groups:
        if name in RESERVED_FLAGS:
            raise ValueError(f"--{name} is set by the dashboard and cannot be passed")
        if name in fields:
            raise ValueError(f"--{name} is a field of {exp_cfg['name']}: give it in params or args, not extra_args")
        out.append(" ".join([f"--{name}"] + [shlex.quote(v) for v in values]))
    return out


def resolve_params(exp_cfg, params, args="", extra_args=(), allow_extra=False):
    """Merge params and an args string into {field: [values]}, and collect
    extra flags. Unknown fields are an error that names the valid ones,
    never silently dropped. Flags with no field are refused unless the
    caller passed them in extra_args (allow_extra)."""
    fields = {f["name"]: f for f in exp_cfg["fields"]}
    unknown = sorted(set(params) - set(fields))
    if unknown:
        raise ValueError(f"{exp_cfg['name']} has no field {', '.join(unknown)}; its fields are: "
                         f"{', '.join(fields)} (flags without a field go in extra_args)")
    from_args, unknown_flags = parse_args_string(exp_cfg, args)
    both = sorted(set(from_args) & {k for k, v in params.items() if v not in (None, [], "")})
    if both:
        raise ValueError(f"{', '.join(both)} given in both params and args")
    if unknown_flags and not allow_extra:
        names = ", ".join(f"--{n}" for n, _ in unknown_flags)
        raise ValueError(f"{exp_cfg['name']} has no field {names}; its fields are: {', '.join(fields)}. "
                         "To pass a flag the runner takes but the form does not, put it in extra_args")
    merged = {k: (v if isinstance(v, list) else [v]) for k, v in params.items()}
    merged.update(from_args)
    return merged, normalise_extra_args(exp_cfg, extra_args, unknown_flags)


def preview(exp_cfg, param_lists, extra_args, out_root=None):
    """What a launch would submit: each run's name, settings and command,
    anything that would stop it here, and runs that already have output."""
    runs, skipped = slurm.plan_sweep(exp_cfg, param_lists, extra_args)
    root = Path(out_root or exp_cfg.get("out_root") or ".")
    out = []
    for run in runs:
        command = " ".join([str(exp_cfg["script"])] + slurm.command_args(
            exp_cfg, run["params"], run["run_name"], out_root, extra_args))
        row = {"run_name": run["run_name"], "params": run["params"], "command": command,
               "blockers": environment.launch_blockers(exp_cfg, run["params"])}
        if (root / "runs" / run["run_name"]).exists():
            row["warning"] = "a run with this name already has output; launching writes over it"
        out.append(row)
    gpu = slurm._uses_gpu(exp_cfg.get("resources", {}))
    return {"dry_run": True, "runs": out, "skipped_combinations": skipped,
            "gpu_jobs": len(out) if gpu else 0,
            "note": "GPU jobs run at most four at a time across the whole dashboard; the rest wait in order."}


# ---------------------------------------------------------------- progress

def job_progress(job, exp_cfg):
    params = json.loads(job["params_json"])
    # Which field says how long this run is. FT counts gradient steps, causal
    # tracing counts prompts; each experiment type names its own rather than
    # the dashboard guessing from the field list.
    num_steps = params.get(exp_cfg.get("progress_field", "num_steps"))
    out_root = job.get("out_root") or exp_cfg.get("out_root")
    run_name = job.get("run_name")
    latest = None
    if out_root and run_name:
        ckpt_path = Path(out_root) / "runs" / run_name / "checkpoints.jsonl"
        if ckpt_path.exists():
            lines = ckpt_path.read_text().splitlines()
            if lines:
                try:
                    latest = json.loads(lines[-1])
                except ValueError:
                    latest = None
    return {
        # A run that knows its own length says so in its checkpoints, and that
        # wins: an edit-protocol run is as long as its dataset, not as long as
        # the FT step count sitting in its submitted params, and "full" has no
        # number in the params at all.
        "num_steps": (latest or {}).get("total_steps") or num_steps,
        "current_step": latest.get("step") if latest else None,
        "latest_metrics": latest,
    }


def _parse_time(text):
    try:
        stamp = datetime.fromisoformat(str(text).replace("Z", "+00:00"))
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
    return stamp if stamp.tzinfo else stamp.replace(tzinfo=timezone.utc)


def job_investigation(job):
    if job.get("investigation"):
        return job["investigation"]
    params = json.loads(job.get("params_json") or "{}")
    return default_investigation(job["experiment_type"], {k: [v] for k, v in params.items()})


def _batch_key(job):
    return job.get("batch_id") or job.get("sweep_id") or f"job-{job['job_id']}"


def _activity(job, exp_cfg, params):
    """(text, done, total, unit) for one running job."""
    if job["experiment_type"] == hparam_sweeps.EXPERIMENT and job.get("out_root") and job.get("run_name"):
        p = hparam_sweeps._run_progress(Path(job["out_root"]) / "runs" / job["run_name"], job.get("out_path"))
        where = f"{p.get('unit', 'step')} {p['done']}/{p['total']}" if p.get("done") is not None and p.get("total") else p.get("phase")
        return where, p.get("done"), p.get("total"), p.get("unit")
    p = job_progress(job, exp_cfg)
    done, total = p["current_step"], p["num_steps"]
    unit = exp_cfg.get("progress_unit") or exp_cfg.get("progress_field") or "step"
    try:
        total = int(total) if total not in (None, "", "full") else None
    except (TypeError, ValueError):
        total = None
    where = f"{done}/{total} {unit}" if done is not None and total else ("started" if done is not None else "loading")
    return where, done, total, unit


def _describe(params, swept):
    keys = [k for k in ("model", "method", "format") if k in params] + [k for k in swept if k not in ("model", "method", "format")]
    return " · ".join(str(params[k]) for k in dict.fromkeys(keys) if params.get(k) not in (None, ""))


def _summarise_batch(batch_id, jobs, statuses, queue):
    retried = {str(j["retry_of"]) for j in jobs if j.get("retry_of")}
    current = [j for j in jobs if str(j["job_id"]) not in retried]
    first = min(jobs, key=lambda j: j.get("submitted_at") or "")
    exp_type = first["experiment_type"]
    try:
        exp_cfg = registry.get_experiment_type(exp_type)
    except KeyError:
        exp_cfg = {}
    all_params = [json.loads(j.get("params_json") or "{}") for j in current]
    swept = sorted({k for k in set().union(*all_params) if len({json.dumps(p.get(k)) for p in all_params}) > 1}) if all_params else []
    states, running, waiting, overall = {}, [], {}, 0.0
    start_estimates = []
    for job, params in zip(current, all_params):
        jid = str(job["job_id"])
        status = statuses.get(jid, {})
        state = status.get("state", "UNKNOWN")
        states[state] = states.get(state, 0) + 1
        if state not in ACTIVE:
            overall += 1
        elif state == "RUNNING":
            where, done, total, unit = _activity(job, exp_cfg, params)
            if done is not None and total:
                overall += min(float(done) / float(total), 1.0)
            running.append({"run": job["run_name"], "job_id": jid, "what": _describe(params, swept), "activity": where,
                            "done": done, "total": total, "unit": unit,
                            "elapsed_sec": hparam_sweeps._seconds(status.get("elapsed"))})
        elif state == "PENDING":
            info = queue.get(jid) or {}
            text = info.get("reason_text", "queued")
            waiting[text] = waiting.get(text, 0) + 1
            if info.get("start_estimate"):
                start_estimates.append(info["start_estimate"])
    active = sum(c for s, c in states.items() if s in ACTIVE)
    return {
        "id": batch_id, "kind": "experiments", "experiment_type": exp_type,
        "investigation": job_investigation(first),
        "label": first.get("label") or "", "note": first.get("note") or "",
        "launched_by": first.get("launched_by") or "user",
        "created_at": first.get("submitted_at"),
        "runs": len(current), "states": states, "active": active, "finished": len(current) - active,
        "failed": sum(c for s, c in states.items() if s in FAILED),
        "overall": round(overall / len(current), 4) if current else 0.0,
        "running": running, "waiting": [{"text": t, "count": c} for t, c in waiting.items()],
        "start_estimate": min(start_estimates) if start_estimates else None,
        "swept": swept,
    }


def _experiment_batches(days=None):
    """{batch id: [jobs]} for submissions that are not hyperparameter
    sweeps (those are read from their sweep.json)."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days) if days else None
    batches = {}
    for job in db.list_jobs():
        if (job.get("sweep_id") or "").startswith(hparam_sweeps.SWEEP_PREFIX):
            continue
        if cutoff and _parse_time(job.get("submitted_at")) < cutoff:
            continue
        batches.setdefault(_batch_key(job), []).append(job)
    return batches


def _sweep_launch(row):
    running = [{"run": r["run"], "job_id": r["job_id"],
                "what": " · ".join(x for x in (r.get("method"), r.get("model"), r.get("dataset_short")) if x)
                        + "".join(f" · {k} {v}" for k, v in (r.get("overrides") or {}).items()),
                "activity": (f"{r['progress'].get('unit', 'step')} {r['progress']['done']}/{r['progress']['total']}"
                             if (r.get("progress") or {}).get("done") is not None and (r.get("progress") or {}).get("total")
                             else (r.get("progress") or {}).get("phase")),
                "done": (r.get("progress") or {}).get("done"), "total": (r.get("progress") or {}).get("total"),
                "unit": (r.get("progress") or {}).get("unit"), "elapsed_sec": r.get("elapsed_sec")}
               for r in row["running"]]
    return {
        "id": row["id"], "kind": "sweep", "experiment_type": hparam_sweeps.EXPERIMENT,
        "investigation": row["investigation"], "label": row.get("label") or "", "note": row.get("note") or "",
        "launched_by": row.get("launched_by") or "user", "created_at": row.get("created_at"),
        "runs": row["runs"], "states": row["states"], "active": row["active"], "finished": row["finished"],
        "failed": row["retryable"], "overall": row["overall"], "running": running, "waiting": row["waiting"],
        "start_estimate": row.get("start_estimate"), "methods": row.get("methods"), "models": row.get("models"),
        "hidden": row.get("hidden", False),
    }


def list_launches(investigation=None, active_only=False, days=7, limit=50):
    """Launches newest first: sweeps and experiment batches together.
    investigation="main" lists main experiments (no investigation)."""
    out = []
    want_sweeps = investigation in (None, "") or investigations().get(investigation, {}).get("group") == "sweep" \
        or bool(investigations().get(investigation, {}).get("methods"))
    if want_sweeps:
        for row in hparam_sweeps.list_sweeps(investigation or None, include_hidden=False):
            launch = _sweep_launch(row)
            if days and not launch["active"] and _parse_time(launch["created_at"]) < datetime.now(timezone.utc) - timedelta(days=days):
                continue
            out.append(launch)
    batches = _experiment_batches(None if active_only else days)
    if investigation:
        target = None if investigation == "main" else investigation
        batches = {k: v for k, v in batches.items() if job_investigation(v[0]) == target}
    ids = [str(j["job_id"]) for jobs in batches.values() for j in jobs]
    try:
        statuses = slurm.sacct_statuses(ids) if ids else {}
    except (RuntimeError, OSError):
        statuses = {}
    pending = [i for i in ids if statuses.get(i, {}).get("state") == "PENDING"]
    queue = hparam_sweeps._queue(pending) if pending else {}
    out.extend(_summarise_batch(k, v, statuses, queue) for k, v in batches.items())
    if active_only:
        out = [launch for launch in out if launch["active"]]
    out.sort(key=lambda launch: _parse_time(launch["created_at"]), reverse=True)
    return out[:limit] if limit else out


def clear_finished(investigation=None):
    """The progress section's Clear: hide its finished sweeps and clear its
    finished experiment jobs (investigation="main" for main experiments).
    Queued or running launches are left alone; nothing is deleted."""
    want_sweeps = investigation in (None, "") or investigations().get(investigation, {}).get("group") == "sweep" \
        or bool(investigations().get(investigation, {}).get("methods"))
    sweeps = hparam_sweeps.hide_finished(None if investigation in (None, "", "main") else investigation) if want_sweeps else 0
    jobs = [j for batch in _experiment_batches().values() for j in batch]
    if investigation:
        target = None if investigation == "main" else investigation
        jobs = [j for j in jobs if job_investigation(j) == target]
    return {"sweeps_hidden": sweeps, **clear_finished_jobs(jobs)}


def clear_finished_jobs(jobs):
    """Clear the jobs that are no longer queued or running (db.clear_jobs)."""
    ids = [str(j["job_id"]) for j in jobs]
    try:
        statuses = slurm.sacct_statuses(ids) if ids else {}
    except (RuntimeError, OSError) as exc:
        raise RuntimeError(f"could not read job states, nothing cleared: {exc}")
    done = [i for i in ids if statuses.get(i, {}).get("state") not in hparam_sweeps.ACTIVE]
    db.clear_jobs(done)
    return {"jobs_cleared": len(done), "still_active": len(ids) - len(done)}


def summary():
    """Active launches and runs per investigation ("main" for none)."""
    counts = {}
    for launch in list_launches(active_only=True, limit=0):
        key = launch["investigation"] or "main"
        row = counts.setdefault(key, {"launches": 0, "running": 0, "waiting": 0, "by_agent": 0})
        row["launches"] += 1
        row["running"] += launch["states"].get("RUNNING", 0)
        row["waiting"] += launch["states"].get("PENDING", 0)
        row["by_agent"] += launch["launched_by"] == "agent"
    return counts


def _find(launch_id):
    """("sweep", (investigation, sweep)) or ("experiments", jobs), or None."""
    batches = _experiment_batches()
    if launch_id in batches:
        return "experiments", batches[launch_id]
    found = hparam_sweeps.find_sweep(launch_id)
    return ("sweep", found) if found else None


def detail(launch_id):
    """One launch with every run: state, progress, settings, and the end of
    the error log for runs that failed."""
    found = _find(launch_id)
    if not found:
        raise KeyError(launch_id)
    kind, value = found
    if kind == "sweep":
        investigation, _ = value
        return {"kind": "sweep", "launch": next((_sweep_launch(r) for r in hparam_sweeps.list_sweeps(investigation, True)
                                                 if r["id"] == launch_id), None),
                **hparam_sweeps.sweep_detail(investigation, launch_id)}
    jobs = value
    ids = [str(j["job_id"]) for j in jobs]
    try:
        statuses = slurm.sacct_statuses(ids)
    except (RuntimeError, OSError):
        statuses = {}
    queue = hparam_sweeps._queue([i for i in ids if statuses.get(i, {}).get("state") == "PENDING"])
    launch = _summarise_batch(launch_id, jobs, statuses, queue)
    runs = []
    for job in sorted(jobs, key=lambda j: j.get("submitted_at") or ""):
        try:
            exp_cfg = registry.get_experiment_type(job["experiment_type"])
        except KeyError:
            exp_cfg = {}
        status = statuses.get(str(job["job_id"]), {"state": "UNKNOWN"})
        row = {"run": job["run_name"], "job_id": str(job["job_id"]), "state": status.get("state"),
               "elapsed": status.get("elapsed"), "exit_code": status.get("exit_code"),
               "params": json.loads(job.get("params_json") or "{}"),
               "extra_args": json.loads(job["extra_args_json"]) if job.get("extra_args_json") else [],
               "out_root": job.get("out_root"), "out_path": job.get("out_path"), "err_path": job.get("err_path"),
               "retry_of": job.get("retry_of")}
        if row["state"] == "RUNNING":
            row["activity"] = _activity(job, exp_cfg, row["params"])[0]
        if row["state"] == "PENDING":
            row["waiting"] = queue.get(row["job_id"])
        if row["state"] in FAILED:
            row["err_tail"] = "\n".join(slurm.tail_file(job.get("err_path"), 30).splitlines()[-30:]) if job.get("err_path") else ""
        runs.append(row)
    return {"kind": "experiments", "launch": launch, "runs": runs}


def owner(launch_id):
    found = _find(launch_id)
    if not found:
        raise KeyError(launch_id)
    kind, value = found
    if kind == "sweep":
        return value[1].get("launched_by") or "user"
    return "agent" if all(j.get("launched_by") == "agent" for j in value) else "user"


def cancel(launch_id):
    """Cancel every queued or running job of a launch."""
    found = _find(launch_id)
    if not found:
        raise KeyError(launch_id)
    kind, value = found
    if kind == "sweep":
        _, sweep = value
        ids = [str(r["job_id"]) for r in sweep["runs"]]
    else:
        ids = [str(j["job_id"]) for j in value]
    statuses = slurm.sacct_statuses(ids) if ids else {}
    active = [i for i in ids if statuses.get(i, {}).get("state") in ACTIVE]
    return {"cancelled": len(active), "error": slurm.cancel_many(active) or None}
