"""What this machine can actually run, so the dashboard can grey out what it
can't instead of failing a job after it has been queued.

On gaivi everything is present and nothing here changes behaviour. On a
fresh clone (a laptop, a lab workstation) the usual gaps are: no SLURM, no
NVIDIA GPU, no experiment Python environment, no EasyEdit checkout. The
Results and Datasets pages work regardless; only launching is gated.
"""
import os
import shutil
import subprocess
import time

import config
import sources

SETUP_HINT = "python scripts/setup.py"
_cache = {"at": 0.0, "gpus": None}


def scheduler():
    if config.SCHEDULER in ("slurm", "local"):
        return config.SCHEDULER
    return "slurm" if shutil.which("sbatch") else "local"


def local_gpus():
    """[{index, name, memory_total_mb, memory_used_mb}] from nvidia-smi, cached
    briefly because the GPU panel polls it. Empty when there is no NVIDIA GPU."""
    if _cache["gpus"] is not None and time.time() - _cache["at"] < 10:
        return _cache["gpus"]
    gpus = []
    if shutil.which("nvidia-smi"):
        try:
            out = subprocess.run(
                ["nvidia-smi", "--query-gpu=index,name,memory.total,memory.used", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=10,
            ).stdout
            for line in out.splitlines():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) == 4 and parts[0].isdigit():
                    gpus.append({
                        "index": int(parts[0]), "name": parts[1],
                        "memory_total_mb": int(float(parts[2])), "memory_used_mb": int(float(parts[3])),
                    })
        except (OSError, subprocess.SubprocessError, ValueError):
            gpus = []
    _cache.update(at=time.time(), gpus=gpus)
    return gpus


def runner_python(exp_cfg):
    """The interpreter experiment jobs run under: dashboard.json's venv, or
    KE_PYTHON for a checkout that keeps its environment somewhere else."""
    for candidate in (os.environ.get("KE_PYTHON"), exp_cfg.get("venv")):
        if candidate and (os.path.exists(candidate) or shutil.which(candidate)):
            return candidate
    return None


def machine_blockers(exp_cfg=None):
    """Reasons no experiment can launch here at all, in plain words."""
    blockers = []
    if exp_cfg is not None and (not runner_python(exp_cfg) or (
            not os.environ.get("KE_PYTHON") and not sources.experiment_env_ready())):
        blockers.append(
            "The experiment Python environment is not installed (Downloads page, or "
            f"`{SETUP_HINT} --venv`; KE_PYTHON can point at an existing interpreter instead)."
        )
    if not (config.EXTERNAL_DIR / "EasyEdit").exists():
        blockers.append(f"EasyEdit is not downloaded (Downloads page, or `{SETUP_HINT} --external`).")
    if scheduler() == "local" and not local_gpus():
        blockers.append("No SLURM and no NVIDIA GPU on this machine, so experiments cannot run here.")
    return blockers


def launch_blockers(exp_cfg, params):
    """Machine-level blockers plus anything this particular job needs that
    is missing: its model's weights or its dataset file."""
    blockers = machine_blockers(exp_cfg)
    for field in exp_cfg.get("fields", []):
        value = params.get(field["name"])
        if field["name"] == "model":
            option = next((o for o in field.get("options", []) if o.get("value") == value), None)
            if option and option.get("available") is False:
                blockers.append(f"Model {option.get('label', value)} is unavailable: {option.get('note', 'not installed')}.")
        if field.get("control") == "dataset" and value and not os.path.exists(str(value)):
            blockers.append(f"Dataset file {value} is not downloaded (Downloads page, or `{SETUP_HINT} --datasets`).")
    return blockers


def capabilities(experiment_types):
    gpus = local_gpus() if scheduler() == "local" else []
    per_type = {t["name"]: machine_blockers(t) for t in experiment_types}
    return {
        "scheduler": scheduler(),
        "gpus": gpus,
        "can_launch": {name: not blockers for name, blockers in per_type.items()},
        "blockers": per_type,
    }
