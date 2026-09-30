"""Download tasks for the Downloads page.

Each selected item (a dataset, a model, EasyEdit or the experiment
environment) becomes one background task that runs scripts/setup.py for
just that item, so the page and the command line do exactly the same
thing. Tasks run one at a time on their own lock (see local_jobs.py) and
survive backend reloads; the page polls list_tasks() for progress.

Progress is measured, not reported: bytes now on disk under the item's
folder against the size recorded in the catalog. pip gives no size up
front, so the experiment environment shows as indeterminate.
"""
import shlex
import shutil
import sys
import time

import config
import local_jobs
import sources

PREFIX = "download"
LOCK = "download"
STATE_LABELS = {"PENDING": "queued", "RUNNING": "downloading", "COMPLETED": "done",
                "FAILED": "failed", "CANCELLED": "cancelled", "UNKNOWN": "unknown"}


def _item(kind, name):
    for item in sources.catalog():
        if item["kind"] == kind and item["name"] == name:
            return item
    raise KeyError(f"no {kind} named {name}")


def _setup_args(kind, name, parts):
    if kind == "dataset":
        return ["--datasets", name] + (["--parts", *parts] if parts else [])
    if kind == "model":
        return ["--models", name]
    if kind == "component":
        return {"easyedit": ["--external"], "cake-data": ["--cake"], "experiment-env": ["--venv"]}[name]
    raise KeyError(kind)


def _folder(kind, name):
    if kind == "dataset":
        return sources.DATASETS_DIR / name
    if kind == "model":
        return sources.MODELS_DIR / name
    return None


def _tree_bytes(path):
    if not path or not path.exists():
        return 0
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def active_tasks():
    return [t for t in list_tasks() if t["state"] in ("queued", "downloading")]


def start(requests):
    """requests: [{kind, name, parts?}]. Returns the new tasks. Refuses the
    whole batch, before starting any of it, if it would not fit on disk or
    names something unknown or already queued."""
    busy = {(t["kind"], t["name"]) for t in active_tasks()}
    plan, needed = [], 0
    for request in requests:
        kind, name, parts = request["kind"], request["name"], list(request.get("parts") or [])
        item = _item(kind, name)
        if (kind, name) in busy:
            raise ValueError(f"{item['label']} is already queued")
        wanted_parts = [p for p in parts if p in item.get("parts", {})]
        if item["installed"] and all(item["parts"][p]["installed"] for p in wanted_parts):
            continue
        size = item.get("bytes") or 0
        size += sum(item["parts"][p]["bytes"] for p in wanted_parts)
        needed += max(size - item.get("present_bytes", 0), 0)
        plan.append((kind, name, wanted_parts, item, size))
    free = sources.disk_free_bytes()
    if needed > free:
        raise ValueError(f"not enough disk space: the selection needs about {needed / 1e9:.1f} GB "
                         f"and {free / 1e9:.1f} GB is free")

    logs = config.DASHBOARD_DIR / "logs" / "downloads"
    logs.mkdir(parents=True, exist_ok=True)
    started = []
    for kind, name, parts, item, size in plan:
        job_id = local_jobs.new_job_id(PREFIX)
        script = config.LOCAL_JOBS_DIR / f"{job_id}.sh"
        config.LOCAL_JOBS_DIR.mkdir(parents=True, exist_ok=True)
        command = [sys.executable, "-u", str(sources.ROOT / "scripts" / "setup.py"), *_setup_args(kind, name, parts)]
        script.write_text(f"#!/bin/bash\nset -euo pipefail\ncd {shlex.quote(str(sources.ROOT))}\n"
                          + " ".join(shlex.quote(c) for c in command) + "\n")
        meta = {"kind": kind, "name": name, "label": item["label"], "parts": parts, "bytes": size}
        local_jobs.submit(job_id, script, logs / f"{job_id}.out", logs / f"{job_id}.out", lock=LOCK, meta=meta)
        started.append(job_id)
    return [task(job_id) for job_id in started]


def task(job_id):
    state = local_jobs.read_state(job_id)
    if state is None:
        raise KeyError(job_id)
    meta = state.get("meta", {})
    label = STATE_LABELS.get(state["state"], state["state"].lower())
    total = meta.get("bytes") or 0
    progress = None
    if label == "done":
        progress = 1.0
    elif label == "downloading" and total and meta.get("kind") != "component":
        progress = min(_tree_bytes(_folder(meta["kind"], meta["name"])) / total, 0.99)
    return {
        "id": job_id,
        "kind": meta.get("kind"),
        "name": meta.get("name"),
        "label": meta.get("label"),
        "parts": meta.get("parts", []),
        "bytes": total,
        "state": label,
        "progress": progress,
        "elapsed": state.get("elapsed"),
        "submitted": state.get("submitted"),
        "last_line": _last_line(state.get("out"), failed=label == "failed"),
    }


def _last_line(path, failed=False):
    """The line to show under a task: its latest output, or for a failure
    the most telling error line (pip's "ERROR: ..." says why; setup.py's own
    FAILED line only repeats the command)."""
    lines = [line.strip() for line in _tail(path, 200).splitlines() if line.strip()]
    if failed:
        errors = [line for line in lines if line.startswith(("ERROR", "error:", "RuntimeError"))]
        if errors:
            return errors[-1]
    return lines[-1] if lines else ""


def _tail(path, n=200):
    try:
        with open(path, errors="replace") as handle:
            return "".join(handle.readlines()[-n:])
    except (OSError, TypeError):
        return ""


def list_tasks(limit=50):
    if not config.LOCAL_JOBS_DIR.exists():
        return []
    ids = sorted((p.stem for p in config.LOCAL_JOBS_DIR.glob(f"{PREFIX}-*.json")), reverse=True)[:limit]
    tasks = []
    for job_id in ids:
        try:
            tasks.append(task(job_id))
        except KeyError:
            continue
    return tasks


def log(job_id):
    state = local_jobs.read_state(job_id)
    if state is None:
        raise KeyError(job_id)
    return _tail(state.get("out"))


def cancel(job_id):
    if local_jobs.read_state(job_id) is None:
        raise KeyError(job_id)
    return local_jobs.cancel(job_id)


def clear_finished():
    """Forget finished tasks so the list only shows what matters. Leaves
    their logs; never touches downloaded files."""
    removed = 0
    for t in list_tasks(limit=10_000):
        if t["state"] not in ("queued", "downloading"):
            for suffix in (".json", ".sh", ".lock"):
                (config.LOCAL_JOBS_DIR / f"{t['id']}{suffix}").unlink(missing_ok=True)
            removed += 1
    return removed


def overview():
    items = sources.catalog()
    queued = {(t["kind"], t["name"]): t for t in active_tasks()}
    for item in items:
        item["task"] = queued.get((item["kind"], item["name"]))
    return {
        "disk_free_bytes": sources.disk_free_bytes(),
        "git_available": shutil.which("git") is not None,
        "checked_at": time.time(),
        "items": items,
        "tasks": list_tasks(),
    }
