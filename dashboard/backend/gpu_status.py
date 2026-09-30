"""Read-only SLURM GPU allocation snapshot for the Experiments page.

Without SLURM, local_snapshot() reports this machine's own GPUs from
nvidia-smi in the same shape, with local jobs in place of SLURM ones.
"""

import getpass
import platform
import re
import subprocess
from datetime import datetime, timezone

import environment
import local_jobs


def _run(*args):
    proc = subprocess.run(args, capture_output=True, text=True, timeout=12)
    if proc.returncode:
        raise RuntimeError(proc.stderr.strip() or f"{' '.join(args)} failed")
    return proc.stdout


def _indices(spec):
    indices = set()
    for part in spec.split(","):
        if re.fullmatch(r"\d+", part):
            indices.add(int(part))
        elif re.fullmatch(r"\d+-\d+", part):
            start, end = map(int, part.split("-"))
            indices.update(range(start, end + 1))
    return indices


def _node(name):
    info = _run("scontrol", "show", "node", "-dd", "-o", name)
    gres = re.search(r"\bGres=gpu:(?:(?P<type>[^:\s]+):)?(?P<count>\d+)", info)
    if not gres:
        return None
    used = re.search(r"\bGresUsed=gpu:[^\s]*?\(IDX:([\d,-]+)\)", info)
    used_count = re.search(r"\bGresUsed=gpu:(?:[^:\s]+:)?(\d+)", info)
    state = re.search(r"\bState=([^\s]+)", info)
    return {
        "name": name,
        "gpu_type": gres.group("type") or "GPU",
        "state": state.group(1) if state else "UNKNOWN",
        "total": int(gres.group("count")),
        "used": _indices(used.group(1)) if used else set(),
        "usage_known": bool(used or (used_count and int(used_count.group(1)) == 0)),
    }


def _display_user(user, account):
    """
    SLURM prints `nobody` for a UID this node's name service cannot resolve,
    which is the case for most people outside our own group. The SLURM
    account name is the useful identifier when that happens.
    """
    name = user.split("@")[0]
    if name in ("", "nobody", "unknown"):
        return account.split("@")[0] or "unknown user"
    return name


def _allocations(node_names):
    """
    Maps (node, gpu index) -> the SLURM job holding that GPU, for every user
    on the node rather than only this dashboard's own jobs. One `scontrol
    show job` call covers the whole cluster, so this costs a single
    subprocess no matter how many jobs are running.
    """
    try:
        info = _run("scontrol", "show", "job", "-dd", "-o")
    except (RuntimeError, subprocess.TimeoutExpired):
        return {}

    me = getpass.getuser()
    allocations = {}
    for line in info.splitlines():
        job_id = re.search(r"\bJobId=(\d+)", line)
        if not job_id:
            continue
        user = re.search(r"\bUserId=([^(\s]+)\(", line)
        account = re.search(r"\bAccount=(\S+)", line)
        job_name = re.search(r"\bJobName=(\S+)", line)
        raw_user = user.group(1) if user else ""
        owner = {
            "job_id": job_id.group(1),
            "user": _display_user(raw_user, account.group(1) if account else ""),
            "job_name": job_name.group(1) if job_name else "",
            "is_self": raw_user == me,
        }
        for node, indices in re.findall(r"\bNodes=([^\s]+).*?\bGRES=gpu:[^\s]*?\(IDX:([\d,-]+)\)", line):
            if node in node_names:
                for index in _indices(indices):
                    allocations[(node, index)] = owner
    return allocations


def local_snapshot(jobs, metrics_for=None):
    gpus = environment.local_gpus()
    if not gpus:
        raise RuntimeError("no NVIDIA GPU detected on this machine (nvidia-smi found nothing)")
    active = dict(local_jobs.active_jobs())
    rows = {str(job["job_id"]): job for job in jobs if str(job["job_id"]) in active}
    pending, running = [], None
    for job_id, job in rows.items():
        item = {"job_id": job_id, "slot_index": job.get("queue_slot"), "run_name": job.get("run_name")}
        if active[job_id] == "PENDING":
            pending.append({**item, "reason": "Waiting for the running local job to finish"})
        else:
            running = item
            if metrics_for:
                item["metrics"] = metrics_for(job)
    host = platform.node() or "this machine"
    # Local jobs run one at a time on the runner's default device (cuda:0).
    owner = {"job_id": running["job_id"], "user": getpass.getuser(), "job_name": running["run_name"] or "",
             "is_self": True} if running else None
    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "partition": "local",
        "nodes": [{
            "name": host,
            "gpu_type": gpus[0]["name"],
            "state": "MIXED" if running else "IDLE",
            "total": len(gpus),
            "gpus": [{
                "index": gpu["index"],
                "status": "dashboard" if running and gpu["index"] == 0 else
                          "allocated" if gpu["memory_used_mb"] > 1024 else "available",
                "job": running if gpu["index"] == 0 else None,
                "owner": owner if gpu["index"] == 0 else None,
            } for gpu in gpus],
            "gpu_memory_total_mb": gpus[0]["memory_total_mb"],
        }],
        "running_jobs": 1 if running else 0,
        "pending_jobs": pending,
    }


def snapshot(jobs, partition="AAIL", metrics_for=None, gpu_memory_total_mb=None):
    if environment.scheduler() == "local":
        return local_snapshot(jobs, metrics_for)
    names = list(dict.fromkeys(_run("sinfo", "-N", "-p", partition, "-h", "-o", "%N").split()))
    nodes = [node for name in names if (node := _node(name))]
    if not nodes:
        raise RuntimeError(f"No GPU nodes reported for partition {partition}")

    active = {}
    for line in _run("squeue", "-u", getpass.getuser(), "-h", "-o", "%i|%T|%N|%r").splitlines():
        parts = line.split("|", 3)
        if len(parts) == 4:
            active[parts[0]] = {"state": parts[1], "node": parts[2], "reason": parts[3].strip("()")}

    allocations = _allocations({node["name"] for node in nodes})

    dashboard_jobs = {}
    job_rows = {}
    pending = []
    running_count = 0
    for job in jobs:
        current = active.get(str(job["job_id"]))
        if not current:
            continue
        item = {
            "job_id": str(job["job_id"]),
            "slot_index": job.get("queue_slot"),
            "run_name": job.get("run_name"),
        }
        if current["state"] == "PENDING":
            pending.append({**item, "reason": current["reason"] or "Waiting for scheduling"})
        elif current["state"] in ("RUNNING", "COMPLETING"):
            running_count += 1
            dashboard_jobs[item["job_id"]] = item
            job_rows[item["job_id"]] = job

    owners = {
        key: dashboard_jobs[owner["job_id"]]
        for key, owner in allocations.items()
        if owner["job_id"] in dashboard_jobs
    }

    # Attach each GPU-resident job's latest checkpoint metrics here rather
    # than letting the page join them against /api/queue. That join used to
    # miss two ways: a job unlinked from its slot by a restage is absent from
    # the queue entirely, and the two endpoints are fetched on separate timers
    # so they disagree about which job holds a GPU whenever one ends between
    # calls. At most 8 jobs are mapped, so this costs 8 checkpoint reads.
    if metrics_for:
        for item in {id(i): i for i in owners.values()}.values():
            row = job_rows.get(item["job_id"])
            item["metrics"] = metrics_for(row) if row else None
            total = (item["metrics"] or {}).get("gpu_mem_total_mb")
            if total and not gpu_memory_total_mb:
                gpu_memory_total_mb = total

    result_nodes = []
    for node in nodes:
        unavailable = not any(s in node["state"] for s in ("IDLE", "MIXED", "ALLOCATED"))
        gpus = []
        for index in range(node["total"]):
            owner = owners.get((node["name"], index))
            status = (
                "unavailable" if unavailable else
                "unknown" if not node["usage_known"] else
                "dashboard" if owner else
                "allocated" if index in node["used"] else "available"
            )
            gpus.append({
                "index": index,
                "status": status,
                "job": owner,
                "owner": allocations.get((node["name"], index)),
            })
        result_nodes.append(
            {k: v for k, v in node.items() if k not in ("used", "usage_known")}
            | {"gpus": gpus, "gpu_memory_total_mb": gpu_memory_total_mb}
        )

    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "partition": partition,
        "nodes": result_nodes,
        "running_jobs": running_count,
        "pending_jobs": pending,
    }
