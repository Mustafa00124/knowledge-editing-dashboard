"""Keep runs that write into results/ visible on the dashboard.

A run launched by hand (python on a GPU node, or a hand-written sbatch) never
reaches the dashboard's job table, so no investigation page can show its
progress and nobody can see what is holding a GPU. The runners call
require_dashboard() first thing: writing into the project's results/ tree is
refused unless the dashboard launched the run, or --untracked says this is
deliberate. Output anywhere else (a temporary directory, a test) is never
checked.

The dashboard marks its launches with KE_DASHBOARD_JOB in the job script.
Jobs queued before that existed are recognised by their SLURM job id, which
the dashboard recorded when it submitted them.
"""
import os
import sqlite3
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
DB_PATH = os.path.join(PROJECT_ROOT, "dashboard", "dashboard.db")

MESSAGE = """refusing to write into {out_root}: this run was not launched by the dashboard,
so no investigation page would show its progress. Launch it through the dashboard
instead, for example

    python scripts/dash.py launch {experiment} --investigation <id> --label "<what it is>" -- <arguments>

(see dashboard/AGENTS.md), or pass --untracked to run it outside the dashboard on purpose."""


def _inside(path, root):
    path, root = os.path.realpath(path), os.path.realpath(root)
    return path == root or path.startswith(root + os.sep)


def _known_slurm_job(job_id):
    if not job_id or not os.path.exists(DB_PATH):
        return False
    try:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, timeout=5)
        try:
            return conn.execute("SELECT 1 FROM jobs WHERE job_id = ?", (str(job_id),)).fetchone() is not None
        finally:
            conn.close()
    except sqlite3.Error:
        return False


def launched_by_dashboard(environ=None):
    environ = os.environ if environ is None else environ
    return bool(environ.get("KE_DASHBOARD_JOB")) or _known_slurm_job(environ.get("SLURM_JOB_ID"))


def require_dashboard(out_root, untracked=False, experiment="<experiment>", environ=None):
    """Exit with an explanation when a run outside the dashboard would write
    into results/. Returns quietly otherwise."""
    if untracked or not _inside(out_root, RESULTS_DIR) or launched_by_dashboard(environ):
        return
    sys.exit(MESSAGE.format(out_root=out_root, experiment=experiment))


def add_argument(parser):
    parser.add_argument("--untracked", action="store_true",
                        help="allow writing into results/ without the dashboard having launched this run "
                             "(it will not show on any progress panel)")
