import os
from pathlib import Path

# The one seam into the actual project. Defaults to the checkout this file
# lives in (dashboard/backend/ -> two levels up), so a clone anywhere works;
# KE_PROJECT_ROOT overrides it for an unusual layout.
PROJECT_ROOT = Path(os.environ.get("KE_PROJECT_ROOT") or Path(__file__).resolve().parents[2])

EXPERIMENTS_DIR = PROJECT_ROOT / "experiments"
RESULTS_DIR = PROJECT_ROOT / "results"
# Two trees: main experiments (the reported results) and hyperparameter
# investigations (sweeps on dev records, organised by what they tune).
MAIN_RESULTS_DIR = RESULTS_DIR / "main"
TRIAL_RUNS_DIR = MAIN_RESULTS_DIR / "trial_runs"
INVESTIGATIONS_DIR = RESULTS_DIR / "investigations"
DATASETS_DIR = PROJECT_ROOT / "datasets"
MODELS_DIR = PROJECT_ROOT / "models"
EXTERNAL_DIR = PROJECT_ROOT / "external"

DASHBOARD_DIR = Path(__file__).resolve().parent.parent
DB_PATH = DASHBOARD_DIR / "dashboard.db"
SUBMITTED_SBATCH_DIR = DASHBOARD_DIR / "backend" / "submitted"
GPU_LANE_LOCK_PATH = DASHBOARD_DIR / "backend" / ".gpu_lane.lock"
# State files for jobs run without SLURM (see local_jobs.py).
LOCAL_JOBS_DIR = DASHBOARD_DIR / "backend" / "local_jobs"

# "slurm" or "local". Unset means: SLURM if sbatch is on PATH, else local.
SCHEDULER = os.environ.get("KE_SCHEDULER", "").strip().lower() or None
