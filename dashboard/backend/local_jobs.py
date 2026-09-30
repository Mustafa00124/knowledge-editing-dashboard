"""Runs experiment jobs as background processes when there is no SLURM.

Covers the small slice of sbatch/sacct/scancel that slurm.py needs, so the
rest of the dashboard (queue cards, pause/resume, retries) works unchanged
on a single machine. Job ids look like "local-<timestamp>-<n>", which is how
slurm.py tells them apart from SLURM's numeric ids.

Jobs run one at a time per lock: each waits on an exclusive lock before
starting, because two experiments sharing one GPU would both run out of
memory. Experiments use the "gpu" lock; downloads (downloads.py) use their
own, so a download never waits behind an experiment. A waiting job reports
PENDING, a started one RUNNING, then COMPLETED, FAILED or CANCELLED, spelled
as sacct spells them.

Each job is supervised by this module run as a script (see `_supervise`).
It is started in its own session, so it outlives backend reloads, and
cancelling a job signals that whole process group.
"""
import itertools
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime

import config

try:
    import fcntl
except ImportError:  # Windows: no locking, jobs may overlap
    fcntl = None

_counter = itertools.count()
ACTIVE_STATES = ("PENDING", "RUNNING")
# A just-submitted supervisor has not recorded its pid yet; give it this
# long before a missing pid means it died.
STARTUP_GRACE_SEC = 60
# Supervisors this backend process spawned. Polled so exited ones are
# reaped instead of lingering as zombies (which would still look alive).
_children = []


def _state_path(job_id):
    return config.LOCAL_JOBS_DIR / f"{job_id}.json"


def _read(job_id):
    try:
        return json.loads(_state_path(job_id).read_text())
    except (OSError, ValueError):
        return None


def _write(job_id, state):
    path = _state_path(job_id)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state))
    os.replace(tmp, path)


def _update(job_id, **changes):
    # The backend (cancel) and the supervisor (state changes) both
    # read-modify-write the same file; a per-job lock keeps either from
    # overwriting the other's change.
    with open(config.LOCAL_JOBS_DIR / f"{job_id}.lock", "w") as lock:
        if fcntl:
            fcntl.flock(lock, fcntl.LOCK_EX)
        state = _read(job_id) or {}
        state.update(changes)
        _write(job_id, state)
    return state


def _alive(pid):
    _children[:] = [child for child in _children if child.poll() is None]
    if not pid:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def new_job_id(prefix="local"):
    return f"{prefix}-{time.strftime('%Y%m%d%H%M%S')}-{os.getpid()}{next(_counter)}"


def submit(job_id, script_path, out_path, err_path, lock="gpu", meta=None):
    """`meta` is stored alongside the state for the caller's own use."""
    config.LOCAL_JOBS_DIR.mkdir(parents=True, exist_ok=True)
    _write(job_id, {"state": "PENDING", "submitted": time.time(), "script": str(script_path),
                    "out": str(out_path), "err": str(err_path), "meta": meta or {}})
    # The supervisor records its own pid; writing it from here as well would
    # race the supervisor's own state updates.
    _children.append(subprocess.Popen(
        [sys.executable, os.path.abspath(__file__), str(config.LOCAL_JOBS_DIR),
         job_id, str(script_path), str(out_path), str(err_path), lock],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True,
    ))
    return job_id


def _elapsed(state):
    start = state.get("started")
    if not start:
        return "00:00:00"
    seconds = int((state.get("finished") or time.time()) - start)
    days, rest = divmod(seconds, 86400)
    hours, rest = divmod(rest, 3600)
    clock = f"{hours:02d}:{rest // 60:02d}:{rest % 60:02d}"
    return f"{days}-{clock}" if days else clock


def status(job_id):
    state = _read(job_id)
    if not state:
        return {"state": "UNKNOWN", "elapsed": None, "exit_code": None}
    name = state.get("state", "UNKNOWN")
    starting = not state.get("pid") and time.time() - state.get("submitted", 0) < STARTUP_GRACE_SEC
    if name in ACTIVE_STATES and not starting and not _alive(state.get("pid")):
        # The supervisor died without recording an outcome (machine reboot,
        # killed by hand). sacct would call this NODE_FAIL; FAILED is what
        # the queue cards already treat as retryable.
        name = "FAILED"
        state = _update(job_id, state=name, finished=state.get("finished") or time.time())
    code = state.get("exit_code")
    return {
        "state": name,
        "elapsed": _elapsed(state),
        "exit_code": None if code is None else f"{code}:0",
    }


def active_jobs():
    """(job_id, state) for every local job still pending or running."""
    if not config.LOCAL_JOBS_DIR.exists():
        return []
    jobs = []
    for path in config.LOCAL_JOBS_DIR.glob("local-*.json"):  # not *.lock / *.tmp
        job_id = path.stem
        current = status(job_id)["state"]
        if current in ACTIVE_STATES:
            jobs.append((job_id, current))
    return jobs


def cancel(job_id):
    state = _read(job_id)
    if not state or state.get("state") not in ACTIVE_STATES:
        return f"job {job_id} is not active"
    _update(job_id, state="CANCELLED", finished=time.time())
    pid = state.get("pid")
    if not pid:
        # Cancelled before the supervisor recorded itself: it will see
        # CANCELLED once it has the lock and exit without running.
        return ""
    if _alive(pid):
        try:
            os.killpg(pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError, AttributeError):
            pass
    return ""


def read_state(job_id):
    """The full stored state (including `meta`), with the live status merged in."""
    state = _read(job_id)
    if state is None:
        return None
    return {**state, **status(job_id)}


def _supervise(job_id, script_path, out_path, err_path, lock_name="gpu"):
    config.LOCAL_JOBS_DIR.mkdir(parents=True, exist_ok=True)
    _update(job_id, pid=os.getpid())
    lock = open(config.LOCAL_JOBS_DIR / f"{lock_name}.lock", "w")
    if fcntl:
        fcntl.flock(lock, fcntl.LOCK_EX)  # held until this process exits
    if (_read(job_id) or {}).get("state") == "CANCELLED":
        return
    _update(job_id, state="RUNNING", started=time.time())
    with open(out_path, "a") as out, open(err_path, "a") as err:
        out.write(f"[local job {job_id} started {datetime.now().astimezone().isoformat(timespec='seconds')}]\n")
        out.flush()
        code = subprocess.run(["bash", script_path], stdout=out, stderr=err).returncode
    if (_read(job_id) or {}).get("state") == "CANCELLED":
        return
    _update(job_id, state="COMPLETED" if code == 0 else "FAILED", exit_code=code, finished=time.time())


if __name__ == "__main__":
    # The state directory is passed explicitly so the supervisor and the
    # backend that spawned it always agree on it.
    from pathlib import Path
    config.LOCAL_JOBS_DIR = Path(sys.argv[1])
    _supervise(*sys.argv[2:7])
