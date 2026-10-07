import json
import os
import re
import socket
import secrets
import sqlite3
import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

import config
import datasets_reader
import downloads
import environment
import hparam_sweeps
import in_context_reader
import launches
import models_reader
import db
import gpu_status
import archive
import causal_tracing_reader
import mechanistic_reader
import registry
import results_reader
import slurm
from schemas import ArchiveRequest, DownloadRequest, PromoteRequest, SubmitExperimentRequest, SweepRequest

app = FastAPI(title="Knowledge-Editing Dashboard")

# Harmless even though the Vite dev proxy makes this same-origin in
# practice — keeps direct-to-backend requests (curl, debugging) working too.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

db.init()


# ---------------------------------------------------------------- auth
#
# Now reachable beyond GPU57's own loopback (see dashboard/README.md), so
# this stops a casual/opportunistic request from anyone else who can reach
# this IP on the cluster's internal network. It is a shared secret over
# plain HTTP on that internal hop, not real security against a targeted
# attacker with access to that network — good enough for "not wide open",
# not a substitute for putting this behind real auth if it ever needs to be
# reachable more broadly than that.

_TOKEN_PATH = config.DASHBOARD_DIR / "backend" / ".auth_token"
if _TOKEN_PATH.exists():
    AUTH_TOKEN = _TOKEN_PATH.read_text().strip()
else:
    AUTH_TOKEN = secrets.token_urlsafe(24)
    _TOKEN_PATH.write_text(AUTH_TOKEN)
    _TOKEN_PATH.chmod(0o600)

print(f"\n=== dashboard auth token (paste into the frontend once): {AUTH_TOKEN} ===\n", flush=True)

# A second token for agents (scripts/dash.py reads it). Requests with it are
# recorded as launched_by "agent", show as such on the progress sections,
# and cannot reach the routes in AGENT_BLOCKED or cancel what a person
# launched. See dashboard/AGENTS.md.
_AGENT_TOKEN_PATH = config.DASHBOARD_DIR / "backend" / ".agent_token"
if _AGENT_TOKEN_PATH.exists():
    AGENT_TOKEN = _AGENT_TOKEN_PATH.read_text().strip()
else:
    AGENT_TOKEN = secrets.token_urlsafe(24)
    _AGENT_TOKEN_PATH.write_text(AGENT_TOKEN)
    _AGENT_TOKEN_PATH.chmod(0o600)

# Where this backend answers, for agents on other nodes (scripts/dash.py).
try:
    (config.DASHBOARD_DIR / "backend" / ".backend_url").write_text(
        f"http://{socket.getfqdn()}:{os.environ.get('DASHBOARD_PORT', '8000')}\n")
except OSError:
    pass

# Changes that are the user's call: promoting a setting into the main
# configuration, deleting or archiving results, downloads, the hand-run
# queue, and hiding sweeps.
AGENT_BLOCKED = [
    ("POST", re.compile(r"^/api/hparams/promote$")),
    ("DELETE", re.compile(r"^/api/hparams/sweeps/")),
    ("POST", re.compile(r"^/api/hparams/sweeps/[^/]+/[^/]+/hide$")),
    ("POST", re.compile(r"^/api/downloads")),
    ("DELETE", re.compile(r"^/api/downloads/")),
    ("POST", re.compile(r"^/api/results/archive")),
    ("POST", re.compile(r"^/api/queue/")),
]


@app.middleware("http")
async def check_auth(request: Request, call_next):
    if request.url.path.startswith("/api"):
        token = request.headers.get("x-dashboard-token")
        if token == AUTH_TOKEN:
            request.state.role = "user"
        elif token == AGENT_TOKEN:
            request.state.role = "agent"
            if any(request.method == method and pattern.match(request.url.path) for method, pattern in AGENT_BLOCKED):
                return JSONResponse({"detail": "the agent token cannot do this; ask the user to do it in the dashboard"},
                                    status_code=403)
        else:
            return JSONResponse({"detail": "unauthorized"}, status_code=401)
    return await call_next(request)


def _role(request):
    return getattr(request.state, "role", "user")


def _require_owner(request, owner):
    """An agent may cancel or rerun only what an agent launched."""
    if _role(request) == "agent" and owner != "agent":
        raise HTTPException(403, "this was launched by the user; the agent token can only change agent launches")


@app.get("/api/whoami")
def whoami(request: Request):
    return {"role": _role(request)}


# ---------------------------------------------------------------- capabilities


@app.get("/api/capabilities")
def get_capabilities():
    """What this machine can run: scheduler, GPUs, and per experiment type
    whether launching is possible (and why not). Lets the page grey out
    Launch on a checkout without SLURM, a GPU or the experiment env."""
    return environment.capabilities(registry.list_experiment_types())


# ---------------------------------------------------------------- downloads


@app.get("/api/downloads")
def get_downloads():
    """Everything downloadable (components, datasets, models) with size and
    on-disk status, plus the download task list and free disk space."""
    return downloads.overview()


@app.post("/api/downloads")
def start_downloads(req: DownloadRequest):
    try:
        return downloads.start([item.model_dump() for item in req.items])
    except (KeyError, ValueError) as exc:
        raise HTTPException(400, str(exc).strip("'\""))


@app.get("/api/downloads/{task_id}/log")
def get_download_log(task_id: str):
    try:
        return {"log": downloads.log(task_id)}
    except KeyError:
        raise HTTPException(404, "no such download")


@app.delete("/api/downloads/{task_id}")
def cancel_download(task_id: str):
    try:
        downloads.cancel(task_id)
    except KeyError:
        raise HTTPException(404, "no such download")
    return downloads.task(task_id)


@app.post("/api/downloads/clear")
def clear_downloads():
    return {"removed": downloads.clear_finished()}


# ---------------------------------------------------------------- hyperparameters


@app.get("/api/hparams/investigations")
def get_investigations():
    """Each kind of setting, the methods that have it, and their current
    values and suggested sweep values per model."""
    return hparam_sweeps.catalog()


@app.get("/api/hparams/settings")
def get_held_settings(investigation: str, methods: str, models: str):
    """What a sweep holds constant: every other setting of the chosen
    methods per model, its effective value and source, the investigation
    that tunes it, and the best value that investigation found so far."""
    return hparam_sweeps.settings(investigation, [m for m in methods.split(",") if m],
                                  [m for m in models.split(",") if m])


@app.post("/api/hparams/estimate")
def estimate_sweep(req: SweepRequest):
    try:
        return hparam_sweeps.estimate(req.model_dump())
    except (KeyError, ValueError) as exc:
        raise HTTPException(400, str(exc).strip("'\""))


@app.post("/api/hparams/sweeps")
def launch_sweep(req: SweepRequest, request: Request):
    if _role(request) == "agent" and not req.label.strip():
        raise HTTPException(400, "give the sweep a label saying what it is for")
    try:
        return hparam_sweeps.launch(req.model_dump(), launched_by=_role(request))
    except (KeyError, ValueError) as exc:
        raise HTTPException(400, str(exc).strip("'\""))


@app.get("/api/hparams/sweeps")
def list_sweeps(investigation: Optional[str] = None, include_hidden: bool = False):
    return hparam_sweeps.list_sweeps(investigation, include_hidden)


@app.post("/api/hparams/sweeps/{investigation}/{sweep_id}/cancel")
def cancel_sweep(investigation: str, sweep_id: str, request: Request):
    try:
        _require_owner(request, hparam_sweeps.sweep_owner(investigation, sweep_id))
    except KeyError:
        raise HTTPException(404, "no such sweep")
    ids = [str(j["job_id"]) for j in db.list_jobs(include_cleared=True) if j.get("sweep_id") == hparam_sweeps.SWEEP_PREFIX + sweep_id]
    if not ids:
        raise HTTPException(404, "no such sweep")
    statuses = slurm.sacct_statuses(ids)
    active = [i for i in ids if statuses.get(i, {}).get("state") in ("PENDING", "RUNNING", "REQUEUED", "SUSPENDED")]
    return {"cancelled": len(active), "error": slurm.cancel_many(active) or None}


@app.get("/api/hparams/hidden-sweeps")
def get_hidden_sweep_count(investigation: Optional[str] = None):
    """How many sweeps are hidden, so a page can offer to show them without
    loading (and polling SLURM for) every one."""
    return {"hidden": hparam_sweeps.hidden_count(investigation)}


@app.post("/api/hparams/sweeps/{investigation}/clear-finished")
def clear_finished_sweeps(investigation: str):
    """Hide every sweep of an investigation with nothing queued or running."""
    return {"hidden": hparam_sweeps.hide_finished(investigation)}


@app.get("/api/hparams/sweeps/{investigation}/{sweep_id}")
def get_sweep_detail(investigation: str, sweep_id: str):
    """One sweep's request and every run's state, progress and scores."""
    try:
        return hparam_sweeps.sweep_detail(investigation, sweep_id)
    except KeyError:
        raise HTTPException(404, "no such sweep")


@app.post("/api/hparams/sweeps/{investigation}/{sweep_id}/hide")
def hide_sweep(investigation: str, sweep_id: str, hidden: bool = True):
    """Clear a finished sweep off the sweep lists (hidden=false brings it
    back). Its results stay on Results · Investigations."""
    try:
        return hparam_sweeps.set_hidden(investigation, sweep_id, hidden)
    except KeyError:
        raise HTTPException(404, "no such sweep")
    except ValueError as exc:
        raise HTTPException(409, str(exc))


@app.delete("/api/hparams/sweeps/{investigation}/{sweep_id}")
def delete_sweep(investigation: str, sweep_id: str):
    """Hide a finished sweep (moved to <investigation>/deleted/, not erased)."""
    try:
        return hparam_sweeps.delete_sweep(investigation, sweep_id)
    except KeyError:
        raise HTTPException(404, "no such sweep")
    except ValueError as exc:
        raise HTTPException(409, str(exc))


@app.post("/api/hparams/sweeps/{investigation}/{sweep_id}/rerun-failed")
def rerun_failed_sweep_runs(investigation: str, sweep_id: str, request: Request):
    """Resubmit a sweep's failed or cancelled runs with the same settings."""
    try:
        _require_owner(request, hparam_sweeps.sweep_owner(investigation, sweep_id))
    except KeyError:
        raise HTTPException(404, "no such sweep")
    try:
        return hparam_sweeps.rerun_failed(investigation, sweep_id)
    except FileNotFoundError:
        raise HTTPException(404, "no such sweep")


@app.get("/api/hparams/failures")
def get_sweep_failures():
    """Failed sweep runs across every investigation, with their errors."""
    return hparam_sweeps.failures()


@app.post("/api/hparams/failures/clear")
def clear_sweep_failures():
    """Clear the Failures view (kept in each sweep.json; a run that fails
    again after a rerun shows again)."""
    return hparam_sweeps.clear_failures()


@app.get("/api/hparams/results")
def get_sweep_results(investigation: str):
    return hparam_sweeps.results(investigation)


@app.post("/api/hparams/promote")
def promote_config(req: PromoteRequest):
    """Use a sweep run's settings as the main configuration for its
    method and model (rewrites that hparams file)."""
    try:
        return hparam_sweeps.promote(req.investigation, req.sweep_id, req.run)
    except KeyError:
        raise HTTPException(404, "no such run")
    except ValueError as exc:
        raise HTTPException(400, str(exc))


# ---------------------------------------------------------------- experiment types

@app.get("/api/experiment-types")
def get_experiment_types():
    return [{k: v for k, v in t.items() if k != "_dir"} for t in registry.list_experiment_types()]


# ---------------------------------------------------------------- experiments (jobs)
# All launch surfaces below ultimately call slurm._submit_one(), where the
# shared four-GPU dependency lanes are applied.  Do not add a direct sbatch
# path here or in the hyperparameter routes, or it would bypass that cap.

def _output_target(exp_cfg, save_results):
    if save_results:
        return None, exp_cfg.get("out_root")
    testing_id = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S-%f_UTC")
    return testing_id, str(config.TRIAL_RUNS_DIR / testing_id)

_job_progress = launches.job_progress


@app.post("/api/experiments")
def submit_experiment(req: SubmitExperimentRequest, request: Request):
    """Launch one run, or a sweep of runs over every field given more than
    one value. Takes fields as params ({field: [values]}) and/or as a
    command-line style args string; extra_args passes flags the experiment
    type has no field for. dry_run says what would run without submitting."""
    try:
        exp_cfg = registry.get_experiment_type(req.experiment_type)
    except KeyError:
        types = ", ".join(t["name"] for t in registry.list_experiment_types())
        raise HTTPException(404, f"unknown experiment type {req.experiment_type}; one of: {types}")

    role = _role(request)
    try:
        params, extra_args = launches.resolve_params(exp_cfg, req.params, req.args, req.extra_args,
                                                     allow_extra=bool(req.extra_args))
        investigation = launches.check_investigation(req.investigation, req.experiment_type, params)
        if any(not str(job).isdigit() for job in req.after_ok):
            raise ValueError("after_ok takes SLURM job ids")
        if role == "agent" and not req.label.strip() and not req.dry_run:
            raise ValueError("give the launch a label saying what it is for")
        if req.dry_run:
            return {"investigation": investigation, **launches.preview(
                exp_cfg, params, extra_args, None if req.save_results else "<trial run folder>")}
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(400, str(exc))

    testing_id, out_root = _output_target(exp_cfg, req.save_results)
    try:
        results = slurm.submit_sweep(exp_cfg, params, out_root if testing_id else None, req.after_ok,
                                     extra_args=extra_args)
    except RuntimeError as e:
        raise HTTPException(500, str(e))

    sweep_id = secrets.token_hex(4) if len(results) > 1 else None
    batch_id = launches.new_batch_id()
    for result in results:
        db.insert_job(
            job_id=result["job_id"],
            experiment_type=req.experiment_type,
            run_name=result["run_name"],
            params=result["params"],
            sbatch_path=result["sbatch_path"],
            out_path=result["out_path"],
            err_path=result["err_path"],
            out_root=out_root,
            sweep_id=sweep_id,
            testing_id=testing_id,
            investigation=investigation,
            batch_id=batch_id,
            label=req.label,
            launched_by=role,
            note=req.note,
            extra_args=extra_args,
        )
    return {"launch_id": batch_id, "investigation": investigation, "sweep_id": sweep_id, "jobs": results}


UNKNOWN_STATUS = {"state": "UNKNOWN", "elapsed": None, "exit_code": None}


@app.get("/api/experiments")
def list_experiments(experiment_type: Optional[str] = None):
    jobs = [j for j in db.list_jobs() if not experiment_type or j["experiment_type"] == experiment_type]
    # One sacct call for the whole list rather than one per job: this table
    # is hundreds of rows deep now, and the per-job version spawned a
    # subprocess for every one of them.
    try:
        statuses = slurm.sacct_statuses([job["job_id"] for job in jobs]) if jobs else {}
    except (RuntimeError, OSError, subprocess.SubprocessError):
        statuses = {}
    out = []
    for job in jobs:
        try:
            exp_cfg = registry.get_experiment_type(job["experiment_type"])
        except KeyError:
            exp_cfg = {}
        out.append(
            {
                **job,
                "params": json.loads(job["params_json"]),
                "status": statuses.get(str(job["job_id"]), dict(UNKNOWN_STATUS)),
                "progress": _job_progress(job, exp_cfg),
            }
        )
    return out


@app.post("/api/experiments/clear")
def clear_experiments(experiment_type: Optional[str] = None):
    """Clear finished jobs off the job tables (kept in the database, logs
    and results untouched). Sweep jobs are cleared with their sweep."""
    jobs = [j for j in db.list_jobs()
            if (not experiment_type or j["experiment_type"] == experiment_type)
            and not (j.get("sweep_id") or "").startswith(hparam_sweeps.SWEEP_PREFIX)]
    try:
        return launches.clear_finished_jobs(jobs)
    except RuntimeError as exc:
        raise HTTPException(503, str(exc))


@app.get("/api/experiments/{job_id}")
def get_experiment(job_id: str):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    try:
        exp_cfg = registry.get_experiment_type(job["experiment_type"])
    except KeyError:
        exp_cfg = {}
    return {
        **job,
        "params": json.loads(job["params_json"]),
        "status": slurm.sacct_status(job_id),
        "progress": _job_progress(job, exp_cfg),
        "log_tail": slurm.tail_file(job["out_path"]),
        "err_tail": slurm.tail_file(job["err_path"]),
    }


@app.delete("/api/experiments/{job_id}")
def cancel_experiment(job_id: str, request: Request):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    _require_owner(request, job.get("launched_by") or "user")
    slurm.cancel(job_id)
    return {"ok": True}


# ---------------------------------------------------------------- launches
# Every batch submitted at once (a sweep, or an experiment submission), with
# progress: what each investigation page's progress section and the agent
# CLI show. See launches.py.

@app.get("/api/launches")
def get_launches(investigation: Optional[str] = None, active: bool = False, days: int = 7, limit: int = 50):
    """Newest first. investigation=main lists main experiments; active=true
    only launches with queued or running jobs; days bounds finished ones."""
    return launches.list_launches(investigation, active_only=active, days=days, limit=limit)


@app.post("/api/launches/clear")
def clear_launches(investigation: Optional[str] = None):
    """Clear an investigation's finished launches off its progress section."""
    try:
        return launches.clear_finished(investigation)
    except RuntimeError as exc:
        raise HTTPException(503, str(exc))


@app.get("/api/launches/summary")
def get_launches_summary():
    """Active launches, running and waiting runs per investigation."""
    return launches.summary()


@app.get("/api/launches/{launch_id}")
def get_launch(launch_id: str):
    try:
        return launches.detail(launch_id)
    except KeyError:
        raise HTTPException(404, "no such launch")


@app.post("/api/launches/{launch_id}/cancel")
def cancel_launch(launch_id: str, request: Request):
    try:
        _require_owner(request, launches.owner(launch_id))
        return launches.cancel(launch_id)
    except KeyError:
        raise HTTPException(404, "no such launch")


# ---------------------------------------------------------------- queue (8 fixed cards)
#
# A config chosen in the New Experiment drawer is *staged* onto a slot, not
# submitted immediately - sbatch only runs once Launch is clicked on that
# slot's card. A slot is exactly one of: empty, staged (configured, not
# launched), running, completed, or failed (any job in it failed).

FAIL_STATES = {"FAILED", "CANCELLED", "TIMEOUT", "OUT_OF_MEMORY", "NODE_FAIL", "REVOKED", "PREEMPTED", "BOOT_FAIL", "DEADLINE"}

# States a scancel would still act on. PENDING counts: a job sitting in the
# queue waiting for a GPU is just as cancellable as one already running.
ACTIVE_STATES = {"RUNNING", "PENDING", "COMPLETING", "CONFIGURING", "REQUEUED", "RESIZING", "SUSPENDED"}
_rerun_lock = threading.Lock()
_pause_lock = threading.Lock()


def _slot_view(slot_index, slot_jobs=None, statuses=None):
    slot = db.get_slot(slot_index)
    jobs = []
    for job in (db.jobs_for_slot(slot_index) if slot_jobs is None else slot_jobs):
        try:
            exp_cfg = registry.get_experiment_type(job["experiment_type"])
        except KeyError:
            exp_cfg = {}
        jobs.append(
            {
                **job,
                "params": json.loads(job["params_json"]),
                "status": slurm.sacct_status(job["job_id"]) if statuses is None else statuses[str(job["job_id"])],
                "progress": _job_progress(job, exp_cfg),
            }
        )

    retried_by = {str(job["retry_of"]): job["job_id"] for job in jobs if job.get("retry_of")}
    for job in jobs:
        job["retried_by"] = retried_by.get(str(job["job_id"]))
    current_jobs = [job for job in jobs if not job["retried_by"]]

    staged = None
    if slot and slot.get("experiment_type"):
        staged = {"experiment_type": slot["experiment_type"], "params": json.loads(slot["params_json"]), "save_results": bool(slot["save_results"])}

    if slot and slot.get("paused") and current_jobs:
        status = "paused"
    elif current_jobs:
        states = [j["status"]["state"] for j in current_jobs]
        if any(s in ACTIVE_STATES for s in states):
            status = "running"
        elif any(s in FAIL_STATES for s in states):
            status = "failed"
        elif all(s == "COMPLETED" for s in states):
            status = "completed"
        else:
            status = "running"
    elif staged:
        status = "staged"
    else:
        status = "empty"

    return {"slot_index": slot_index, "status": status, "staged": staged, "jobs": jobs}


@app.get("/api/queue")
def get_queue():
    jobs_by_slot = [db.jobs_for_slot(i) for i in range(db.NUM_SLOTS)]
    try:
        statuses = slurm.sacct_statuses(job["job_id"] for jobs in jobs_by_slot for job in jobs)
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as e:
        raise HTTPException(503, f"Could not read SLURM queue status: {e}")
    return [_slot_view(i, jobs, statuses) for i, jobs in enumerate(jobs_by_slot)]


# Per-GPU VRAM for this node. SLURM reports how many GPUs a node has but not
# how much memory each one holds, so this comes from the most recent run that
# recorded gpu_mem_total_mb. Cached because it describes the hardware, which
# does not change while the dashboard is up.
_gpu_capacity_mb = None


def _latest_metrics(job):
    """Latest checkpoint row for a db job row, or None if it has none yet."""
    try:
        exp_cfg = registry.get_experiment_type(job["experiment_type"])
    except KeyError:
        exp_cfg = {}
    return _job_progress(job, exp_cfg)["latest_metrics"]


def _gpu_capacity(jobs):
    global _gpu_capacity_mb
    if _gpu_capacity_mb:
        return _gpu_capacity_mb
    recent = sorted(jobs, key=lambda j: j["submitted_at"] or "", reverse=True)[:12]
    for job in recent:
        total = (_latest_metrics(job) or {}).get("gpu_mem_total_mb")
        if total:
            _gpu_capacity_mb = total
            break
    return _gpu_capacity_mb


@app.get("/api/queue/gpu-status")
def get_gpu_status():
    types = registry.list_experiment_types()
    partition = types[0].get("resources", {}).get("partition", "AAIL") if types else "AAIL"
    try:
        jobs = db.list_jobs()
        return gpu_status.snapshot(
            jobs,
            partition,
            metrics_for=_latest_metrics,
            gpu_memory_total_mb=_gpu_capacity(jobs),
        )
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as e:
        source = "SLURM" if environment.scheduler() == "slurm" else "local"
        raise HTTPException(503, f"Could not read {source} GPU status: {e}")


@app.post("/api/queue/{slot_index}/stage")
def stage_queue_slot(slot_index: int, req: SubmitExperimentRequest):
    if not 0 <= slot_index < db.NUM_SLOTS:
        raise HTTPException(404, "no such slot")
    current_status = _slot_view(slot_index)["status"]
    if current_status in {"running", "paused"}:
        raise HTTPException(409, f"that slot is currently {current_status} - use its controls or pick another slot")
    try:
        registry.get_experiment_type(req.experiment_type)
    except KeyError:
        raise HTTPException(404, f"unknown experiment type {req.experiment_type}")
    if "evaluation_modes" in req.params:
        try:
            choices = req.params["evaluation_modes"]
            if len(choices) != 1:
                raise ValueError("Evaluation modes must be one combined selection, not a sweep")
            registry.validate_modes(choices[0])
        except ValueError as exc:
            raise HTTPException(400, str(exc))
    # Restaging over a finished (completed/failed) slot just un-links its
    # old jobs from this card's display - their rows/results are untouched.
    db.clear_slot_jobs(slot_index)
    db.set_slot_paused(slot_index, False)
    db.stage_slot(slot_index, req.experiment_type, req.params, req.save_results)
    return _slot_view(slot_index)


@app.post("/api/queue/{slot_index}/launch")
def launch_queue_slot(slot_index: int):
    if not 0 <= slot_index < db.NUM_SLOTS:
        raise HTTPException(404, "no such slot")
    slot = db.get_slot(slot_index)
    if not slot or not slot.get("experiment_type"):
        raise HTTPException(400, "nothing staged in that slot")

    try:
        exp_cfg = registry.get_experiment_type(slot["experiment_type"])
    except KeyError:
        raise HTTPException(
            404,
            f"experiment type {slot['experiment_type']!r} is no longer registered - clear this slot and reconfigure",
        )
    raw_params = json.loads(slot["params_json"])
    testing_id, out_root = _output_target(exp_cfg, bool(slot["save_results"]))
    try:
        results = slurm.submit_sweep(exp_cfg, raw_params, out_root if testing_id else None)
    except RuntimeError as e:
        raise HTTPException(500, str(e))

    sweep_id = secrets.token_hex(4) if len(results) > 1 else None
    for result in results:
        db.insert_job(
            job_id=result["job_id"],
            experiment_type=slot["experiment_type"],
            run_name=result["run_name"],
            params=result["params"],
            sbatch_path=result["sbatch_path"],
            out_path=result["out_path"],
            err_path=result["err_path"],
            out_root=out_root,
            sweep_id=sweep_id,
            queue_slot=slot_index,
            testing_id=testing_id,
        )
    db.clear_slot_staged(slot_index)
    return _slot_view(slot_index)


@app.post("/api/queue/{slot_index}/rerun-failed")
def rerun_failed_queue_slot(slot_index: int):
    """Retry only failed terminal attempts, keeping prior jobs and results visible."""
    if not 0 <= slot_index < db.NUM_SLOTS:
        raise HTTPException(404, "no such slot")
    with _rerun_lock:
        view = _slot_view(slot_index)
        if view["status"] == "paused":
            raise HTTPException(409, "resume this paused slot before rerunning failures")
        current = [job for job in view["jobs"] if not job["retried_by"]]
        if view["staged"] or not current:
            raise HTTPException(409, "this slot has no launched jobs to rerun")
        if any(job["status"]["state"] in ACTIVE_STATES | {"UNKNOWN"} for job in current):
            raise HTTPException(409, "wait for all jobs in this slot to finish before rerunning failures")
        failed = [job for job in current if job["status"]["state"] in FAIL_STATES]
        if not failed:
            raise HTTPException(409, "this slot has no failed jobs to rerun")
        types = {job["experiment_type"] for job in failed}
        trial_modes = {bool(job["testing_id"]) for job in failed}
        if len(types) != 1 or len(trial_modes) != 1:
            raise HTTPException(409, "failed jobs on this card have incompatible configurations")
        experiment_type = types.pop()
        try:
            exp_cfg = registry.get_experiment_type(experiment_type)
        except KeyError:
            raise HTTPException(404, f"experiment type {experiment_type!r} is no longer registered")

        is_trial = trial_modes.pop()
        testing_id, trial_root = _output_target(exp_cfg, not is_trial)
        batch = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
        sweep_id = secrets.token_hex(4) if len(failed) > 1 else None
        submitted = []
        error = None
        for job in failed:
            base_name = re.sub(r"_rerun\d{8}T\d{12}_\d+$", "", job["run_name"] or f"job_{job['job_id']}")
            run_name = f"{base_name}_rerun{batch}_{job['job_id']}"
            out_root = trial_root if is_trial else job["out_root"] or exp_cfg.get("out_root")
            try:
                result = slurm.submit_exact(exp_cfg, job["params"], run_name, out_root)
                try:
                    db.insert_job(
                        job_id=result["job_id"], experiment_type=experiment_type,
                        run_name=result["run_name"], params=result["params"],
                        sbatch_path=result["sbatch_path"], out_path=result["out_path"],
                        err_path=result["err_path"], out_root=out_root,
                        sweep_id=sweep_id, queue_slot=slot_index,
                        testing_id=testing_id, retry_of=job["job_id"],
                    )
                except sqlite3.Error:
                    slurm.cancel(result["job_id"])
                    raise
                submitted.append(result["job_id"])
            except (RuntimeError, OSError, sqlite3.Error) as exc:
                error = str(exc)
                break
        if error and not submitted:
            raise HTTPException(500, error)
        return {**_slot_view(slot_index), "rerun_submitted": submitted, "rerun_error": error}


@app.post("/api/queue/{slot_index}/pause")
def pause_queue_slot(slot_index: int):
    """Stop this card's unfinished SLURM jobs and remember which attempts
    Play must restart. This deliberately frees their allocations; it is not
    `scontrol suspend`, which would leave their GPUs occupied."""
    if not 0 <= slot_index < db.NUM_SLOTS:
        raise HTTPException(404, "no such slot")
    with _pause_lock:
        view = _slot_view(slot_index)
        if view["status"] == "paused":
            return view
        current = [job for job in view["jobs"] if not job["retried_by"]]
        active = [job for job in current if job["status"]["state"] in ACTIVE_STATES]
        if not active:
            raise HTTPException(409, "nothing running or queued in that slot")
        job_ids = [job["job_id"] for job in active]
        # Persist intent before scancel. If the backend dies between these
        # operations the card still knows which attempts Play should restart.
        db.mark_pause_requested(job_ids)
        db.set_slot_paused(slot_index, True)
        err = slurm.cancel_many(job_ids)
        return {**_slot_view(slot_index), "pause_requested": job_ids, "scancel_error": err or None}


@app.post("/api/queue/{slot_index}/resume")
def resume_queue_slot(slot_index: int):
    """Restart only attempts interrupted by Pause, from their original
    resolved settings. The runner has metric checkpoints, not restorable
    execution state, so every replacement starts that experiment over."""
    if not 0 <= slot_index < db.NUM_SLOTS:
        raise HTTPException(404, "no such slot")
    with _pause_lock:
        view = _slot_view(slot_index)
        if view["status"] != "paused":
            raise HTTPException(409, "that slot is not paused")
        current = [job for job in view["jobs"] if not job["retried_by"]]
        # A job can finish naturally in the small race between the status
        # snapshot and scancel. Never repeat a result that made it to
        # COMPLETED despite having been marked for pause.
        interrupted = [
            job for job in current
            if job.get("pause_requested") and job["status"]["state"] != "COMPLETED"
        ]
        if not interrupted:
            db.set_slot_paused(slot_index, False)
            return {**_slot_view(slot_index), "resume_submitted": [], "resume_error": None}
        still_stopping = [
            job["job_id"] for job in interrupted
            if job["status"]["state"] in ACTIVE_STATES | {"UNKNOWN"}
        ]
        if still_stopping:
            raise HTTPException(409, "SLURM is still stopping job(s) " + ", ".join(still_stopping) + "; try Play again in a few seconds")

        batch = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
        sweep_id = secrets.token_hex(4) if len(interrupted) > 1 else None
        submitted = []
        error = None
        for job in interrupted:
            try:
                exp_cfg = registry.get_experiment_type(job["experiment_type"])
            except KeyError:
                error = f"experiment type {job['experiment_type']!r} is no longer registered"
                break
            base_name = re.sub(r"_(?:rerun|resume)\d{8}T\d{12,}_\d+$", "", job["run_name"] or f"job_{job['job_id']}")
            run_name = f"{base_name}_resume{batch}_{job['job_id']}"
            try:
                result = slurm.submit_exact(exp_cfg, job["params"], run_name, job["out_root"] or exp_cfg.get("out_root"))
                try:
                    db.insert_job(
                        job_id=result["job_id"], experiment_type=job["experiment_type"],
                        run_name=result["run_name"], params=result["params"],
                        sbatch_path=result["sbatch_path"], out_path=result["out_path"],
                        err_path=result["err_path"], out_root=job["out_root"] or exp_cfg.get("out_root"),
                        sweep_id=sweep_id, queue_slot=slot_index,
                        testing_id=job["testing_id"], retry_of=job["job_id"],
                    )
                except sqlite3.Error:
                    slurm.cancel(result["job_id"])
                    raise
                submitted.append(result["job_id"])
            except (RuntimeError, OSError, sqlite3.Error) as exc:
                error = str(exc)
                break

        if error and not submitted:
            raise HTTPException(500, error)
        # If submission was partial, leave the card paused so Play can retry
        # the remaining interrupted attempt(s). Successfully submitted jobs
        # are linked through retry_of and will not be submitted twice.
        remaining = len(interrupted) - len(submitted)
        db.set_slot_paused(slot_index, remaining > 0)
        return {**_slot_view(slot_index), "resume_submitted": submitted, "resume_error": error}


@app.post("/api/queue/{slot_index}/cancel")
def cancel_queue_slot(slot_index: int):
    """scancels every still-active job on this card. The slot keeps its jobs
    afterwards (so the card can show them as CANCELLED) - clearing it is a
    separate, deliberate step, same as for a completed or failed card."""
    if not 0 <= slot_index < db.NUM_SLOTS:
        raise HTTPException(404, "no such slot")
    view = _slot_view(slot_index)
    jobs = view["jobs"]
    job_ids = [j["job_id"] for j in jobs if j["status"]["state"] in ACTIVE_STATES]
    if not job_ids:
        if view["status"] == "paused":
            db.set_slot_paused(slot_index, False)
            return {**_slot_view(slot_index), "cancelled": [], "scancel_error": None}
        raise HTTPException(409, "nothing running in that slot")
    err = slurm.cancel_many(job_ids)
    db.set_slot_paused(slot_index, False)
    # sacct can still report the old state for a moment after scancel, so
    # the returned view may briefly show them as running - the frontend's
    # 5s poll settles it, and this way a partial scancel failure still
    # returns a usable view instead of a 500.
    return {**_slot_view(slot_index), "cancelled": job_ids, "scancel_error": err or None}


@app.post("/api/queue/{slot_index}/clear")
def clear_queue_slot(slot_index: int):
    if not 0 <= slot_index < db.NUM_SLOTS:
        raise HTTPException(404, "no such slot")
    view = _slot_view(slot_index)
    if view["status"] == "running":
        raise HTTPException(409, "can't clear a running slot - pause it first")

    # A paused slot used to be refused here too, which left it with no way
    # out: Play was its only action, and the refusal told you to "cancel its
    # jobs first" when nothing in the UI could. Pause already scancels, so
    # clearing a paused slot only discards the "Play should restart these"
    # list - that plus Pause is the cancel this card never had.
    #
    # Pause can partly fail though (it returns scancel_error), so anything
    # still alive is cancelled here rather than left running with nothing
    # pointing at it.
    stragglers = [
        job["job_id"]
        for job in view["jobs"]
        if not job["retried_by"] and job["status"]["state"] in ACTIVE_STATES
    ]
    err = slurm.cancel_many(stragglers) if stragglers else None

    db.clear_slot_staged(slot_index)
    db.clear_slot_jobs(slot_index)
    db.set_slot_paused(slot_index, False)
    return {**_slot_view(slot_index), "cancelled": stragglers, "scancel_error": err or None}


# ---------------------------------------------------------------- results

def _testing_job(job):
    run_dir = Path(job["out_root"]) / "runs" / job["run_name"]
    summary_path = run_dir / "summary.json"
    summary = json.loads(summary_path.read_text()) if summary_path.exists() else None
    ckpt_path = run_dir / "checkpoints.jsonl"
    checkpoints = [json.loads(line) for line in ckpt_path.read_text().splitlines() if line.strip()] if ckpt_path.exists() else []
    sample_files = sorted((run_dir / "samples").glob("step_*.json"))
    return {
        "job_id": job["job_id"], "run_name": job["run_name"],
        "params": json.loads(job["params_json"]), "submitted_at": job["submitted_at"],
        "status": slurm.sacct_status(job["job_id"]),
        "summary": summary, "latest_checkpoint": checkpoints[-1] if checkpoints else None,
        "checkpoint_count": len(checkpoints),
        "sample_steps": [int(p.stem.split("_")[1]) for p in sample_files if p.stem.split("_")[1].isdigit()],
        "latest_sample": json.loads(sample_files[-1].read_text()) if sample_files else None,
        "log_tail": slurm.tail_file(job["out_path"], 40),
        "err_tail": slurm.tail_file(job["err_path"], 40),
    }


@app.get("/api/results/testing")
def list_testing_results():
    groups = {}
    for job in db.list_jobs():
        if not job.get("testing_id"):
            continue
        group = groups.setdefault(job["testing_id"], {"id": job["testing_id"], "submitted_at": job["submitted_at"], "jobs": []})
        group["jobs"].append(_testing_job(job))
    return sorted(groups.values(), key=lambda group: group["id"], reverse=True)


@app.post("/api/results/testing/clear")
def clear_testing_results():
    """Clear finished trial runs off the Trial Runs tab (their folders stay
    in results/main/trial_runs/)."""
    try:
        return launches.clear_finished_jobs([j for j in db.list_jobs() if j.get("testing_id")])
    except RuntimeError as exc:
        raise HTTPException(503, str(exc))


@app.get("/api/results/testing/{testing_id}")
def get_testing_result(testing_id: str):
    jobs = [job for job in db.list_jobs() if job.get("testing_id") == testing_id]
    if not jobs:
        raise HTTPException(404, "testing result not found")
    return {"id": testing_id, "submitted_at": jobs[0]["submitted_at"], "jobs": [_testing_job(job) for job in jobs]}
#
# "type" is a registered experiment type's name (its dashboard.json), not an
# arbitrary results/ folder - see results_reader.py. Optional everywhere
# since there's normally exactly one registered type; it exists so a second
# experiment type can be added later without a route change.

@app.get("/api/results/types")
def get_result_types():
    return results_reader.list_experiment_types()


@app.get("/api/results/manifest")
def get_manifest(type: Optional[str] = None):
    return results_reader.get_manifest(type)


# archived=true reads the same run out of <out_root>/archive instead, so the
# Archive page can show a retired run's metrics without restoring it first.

@app.get("/api/results/runs/{run}/checkpoints")
def get_checkpoints(run: str, type: Optional[str] = None, archived: bool = False):
    return results_reader.get_checkpoints(run, type, archived)


@app.get("/api/results/runs/{run}/samples")
def get_samples(run: str, type: Optional[str] = None, archived: bool = False):
    return results_reader.list_samples(run, type, archived)


@app.get("/api/results/runs/{run}/samples/{step}")
def get_sample(run: str, step: int, type: Optional[str] = None, archived: bool = False):
    sample = results_reader.get_sample(run, step, type, archived)
    if sample is None:
        raise HTTPException(404, "sample not found")
    return sample


# ---------------------------------------------------------------- archive
#
# Retiring a run means moving its directory, never editing manifest.json -
# see archive.py for why that is the only thing that sticks.

def _busy_runs():
    """Run names a SLURM job is still writing to.

    Archiving one of those would have the job recreate runs/<name> and carry
    on writing into it, leaving half the run in each tree. Only genuinely
    live states count: an old job whose accounting record has aged out of
    sacct reads as UNKNOWN, and treating that as busy would pin every run
    ever launched.
    """
    jobs = [job for job in db.list_jobs() if job.get("run_name")]
    if not jobs:
        return set()
    statuses = slurm.sacct_statuses([job["job_id"] for job in jobs])
    return {
        job["run_name"] for job in jobs
        if statuses.get(str(job["job_id"]), {}).get("state") in ACTIVE_STATES
    }


def _apply_move(req, plan_rows, move, busy_check):
    if busy_check:
        try:
            busy = _busy_runs()
        except (RuntimeError, OSError, subprocess.SubprocessError) as exc:
            # Refusing beats guessing: without a job list we cannot tell a
            # finished run from one being written to right now.
            raise HTTPException(503, f"could not check for running jobs, nothing moved: {exc}")
        for row in plan_rows:
            if row["ok"] and row["run"] in busy:
                row["ok"] = False
                row["problem"] = "a SLURM job is still writing this run - cancel or wait for it first"

    movable = [row["run"] for row in plan_rows if row["ok"]]
    if req.dry_run or not movable:
        return {"applied": False, "plan": plan_rows, "moved": [], "skipped": [r for r in plan_rows if not r["ok"]]}
    moved, skipped = move(movable)
    return {
        "applied": True,
        "plan": plan_rows,
        "moved": moved,
        "skipped": skipped + [r for r in plan_rows if not r["ok"]],
    }


@app.get("/api/results/archive")
def list_archived(type: Optional[str] = None):
    try:
        return archive.list_archived(type)
    except LookupError as exc:
        raise HTTPException(404, str(exc))


@app.get("/api/results/incomplete")
def list_incomplete(type: Optional[str] = None):
    try:
        return archive.list_incomplete(type)
    except LookupError as exc:
        raise HTTPException(404, str(exc))


@app.post("/api/results/archive")
def archive_results(req: ArchiveRequest, type: Optional[str] = None):
    try:
        plan_rows = archive.plan_archive(req.runs, type)
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    return _apply_move(req, plan_rows, lambda runs: archive.archive_runs(runs, req.reason, type), busy_check=True)


@app.post("/api/results/archive/restore")
def restore_results(req: ArchiveRequest, type: Optional[str] = None):
    try:
        plan_rows = archive.plan_restore(req.runs, type)
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    return _apply_move(req, plan_rows, lambda runs: archive.restore_runs(runs, type), busy_check=False)


# ---------------------------------------------------------------- causal tracing
#
# Tracing runs are submitted through the ordinary /api/experiments path (it is
# a registered experiment type like any other, just one the queue drawer
# hides). These two endpoints are only about its output: the model -> layer
# mapping, and one run's curves.

@app.get("/api/in-context")
def get_in_context():
    """In-context experiment runs (SCR among distractors), scored per
    evaluation mode on the four criteria."""
    return {"runs": in_context_reader.runs()}


@app.get("/api/format-knowledge")
def get_format_knowledge():
    """Every finished format-knowledge run's rates (no per-fact detail):
    model -> dataset -> format -> {known_rate, mean_p_answer, n}."""
    root = config.INVESTIGATIONS_DIR / "format_knowledge" / "runs"
    runs = []
    for path in sorted(root.glob("*/summary.json")) if root.is_dir() else []:
        try:
            runs.append(json.loads(path.read_text()))
        except (OSError, ValueError):
            continue
    return {"runs": runs}


@app.get("/api/causal-tracing")
def get_causal_tracing():
    return causal_tracing_reader.overview()


@app.get("/api/causal-tracing/runs/{run}")
def get_causal_trace(run: str):
    try:
        trace = causal_tracing_reader.trace(run)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    if trace is None:
        raise HTTPException(404, "no trace for that run")
    return trace


# ---------------------------------------------------------------- neuron and circuit tracing
#
# Submitted like causal tracing; these only read the output. {experiment} is
# neuron_tracing or circuit_tracing.

@app.get("/api/mechanistic/{experiment}")
def get_mechanistic(experiment: str):
    try:
        return mechanistic_reader.overview(experiment)
    except KeyError:
        raise HTTPException(404, f"unknown experiment {experiment}")


@app.get("/api/mechanistic/{experiment}/runs/{run}")
def get_mechanistic_run(experiment: str, run: str):
    try:
        data = mechanistic_reader.detail(experiment, run)
    except KeyError:
        raise HTTPException(404, f"unknown experiment {experiment}")
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    if data is None:
        raise HTTPException(404, "no result for that run")
    return data


# ---------------------------------------------------------------- datasets

@app.get("/api/datasets")
def get_datasets():
    return datasets_reader.list_benchmarks()


@app.get("/api/datasets/record-count")
def get_dataset_record_count(path: str):
    """What "full" means for one dataset file - the drawer caps the reset
    interval with it. Declared before the /{benchmark}/... routes so
    "record-count" is not read as a benchmark name."""
    try:
        return {"path": path, "count": datasets_reader.record_count(path)}
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@app.get("/api/datasets/{benchmark}/files")
def get_dataset_files(benchmark: str):
    return datasets_reader.list_files(benchmark)


@app.get("/api/datasets/{benchmark}/preview")
def get_dataset_preview(benchmark: str, file: str, offset: int = 0, limit: int = 20, key: Optional[str] = None):
    return datasets_reader.preview(benchmark, file, offset, limit, key)


# ---------------------------------------------------------------- models

@app.get("/api/models")
def get_models():
    return models_reader.list_models()


@app.get("/api/results/runs/{run}/evaluations")
def list_evaluations(run: str, type: Optional[str] = None, archived: bool = False):
    try:
        return results_reader.list_evaluations(run, type, archived)
    except ValueError:
        raise HTTPException(400, "Invalid run")


@app.get("/api/results/runs/{run}/evaluations/{step}")
def get_evaluation(run: str, step: int, type: Optional[str] = None, archived: bool = False):
    try:
        result = results_reader.get_evaluation(run, step, type, archived)
    except ValueError:
        raise HTTPException(400, "Invalid run")
    if result is None:
        raise HTTPException(404, "No saved evaluation for this checkpoint")
    return result
