"""Tracks jobs launched from the dashboard, and the 8 fixed "queue slots"
shown on the Experiments page. Not the source of truth for results —
results/*/manifest.json and checkpoints.jsonl are — this only exists so the
dashboard knows which SLURM job ids/run directories to poll, and what each
queue card currently holds (staged config, or the jobs it launched).
"""
import json
import sqlite3
from datetime import datetime, timezone

import config

NUM_SLOTS = 8
GPU_JOB_LANES = 4


def _conn():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init():
    with _conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                experiment_type TEXT NOT NULL,
                run_name TEXT,
                params_json TEXT,
                submitted_at TEXT,
                sbatch_path TEXT,
                out_path TEXT,
                err_path TEXT,
                out_root TEXT,
                sweep_id TEXT,
                queue_slot INTEGER,
                testing_id TEXT,
                retry_of TEXT,
                pause_requested INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        # Migrations for a db file created before these existed.
        cols = {row[1] for row in conn.execute("PRAGMA table_info(jobs)").fetchall()}
        if "sweep_id" not in cols:
            conn.execute("ALTER TABLE jobs ADD COLUMN sweep_id TEXT")
        if "queue_slot" not in cols:
            conn.execute("ALTER TABLE jobs ADD COLUMN queue_slot INTEGER")
        if "testing_id" not in cols:
            conn.execute("ALTER TABLE jobs ADD COLUMN testing_id TEXT")
        if "retry_of" not in cols:
            conn.execute("ALTER TABLE jobs ADD COLUMN retry_of TEXT")
        if "pause_requested" not in cols:
            conn.execute("ALTER TABLE jobs ADD COLUMN pause_requested INTEGER NOT NULL DEFAULT 0")
        # Which investigation a launch is for, the batch it was submitted in,
        # its label and note, and who launched it (user or agent): what the
        # investigation pages' progress sections group and show.
        for col in ("investigation", "batch_id", "label", "launched_by", "note", "extra_args_json"):
            if col not in cols:
                conn.execute(f"ALTER TABLE jobs ADD COLUMN {col} TEXT")
        # Set by a page's Clear button: the job stays in this table (and its
        # logs and results on disk) but no longer lists or gets polled.
        if "cleared_at" not in cols:
            conn.execute("ALTER TABLE jobs ADD COLUMN cleared_at TEXT")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS queue_slots (
                slot_index INTEGER PRIMARY KEY,
                experiment_type TEXT,
                params_json TEXT,
                staged_at TEXT
                ,save_results INTEGER NOT NULL DEFAULT 1
                ,paused INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        for i in range(NUM_SLOTS):
            conn.execute("INSERT OR IGNORE INTO queue_slots (slot_index) VALUES (?)", (i,))
        slot_cols = {row[1] for row in conn.execute("PRAGMA table_info(queue_slots)").fetchall()}
        if "save_results" not in slot_cols:
            conn.execute("ALTER TABLE queue_slots ADD COLUMN save_results INTEGER NOT NULL DEFAULT 1")
        if "paused" not in slot_cols:
            conn.execute("ALTER TABLE queue_slots ADD COLUMN paused INTEGER NOT NULL DEFAULT 0")

        # Every dashboard-submitted GPU job belongs to one of four serial
        # dependency lanes.  SLURM may run one job from each lane, so main
        # experiments and hyperparameter sweeps together can never occupy
        # more than four GPUs.  Keeping the lane tails in SQLite preserves
        # the throttle across dashboard restarts.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS gpu_job_lanes (
                lane INTEGER PRIMARY KEY,
                tail_job_id TEXT,
                updated_at TEXT
            )
            """
        )
        for i in range(GPU_JOB_LANES):
            conn.execute("INSERT OR IGNORE INTO gpu_job_lanes (lane) VALUES (?)", (i,))


def insert_job(job_id, experiment_type, run_name, params, sbatch_path, out_path, err_path, out_root, sweep_id=None, queue_slot=None, testing_id=None, retry_of=None,
               investigation=None, batch_id=None, label=None, launched_by=None, note=None, extra_args=None):
    with _conn() as conn:
        conn.execute(
            """
            INSERT INTO jobs
                (job_id, experiment_type, run_name, params_json, submitted_at,
                 sbatch_path, out_path, err_path, out_root, sweep_id, queue_slot, testing_id, retry_of,
                 investigation, batch_id, label, launched_by, note, extra_args_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_id,
                experiment_type,
                run_name,
                json.dumps(params),
                datetime.now(timezone.utc).isoformat(),
                sbatch_path,
                out_path,
                err_path,
                out_root,
                sweep_id,
                queue_slot,
                testing_id,
                retry_of,
                investigation,
                batch_id,
                label,
                launched_by,
                note,
                json.dumps(extra_args) if extra_args else None,
            ),
        )


def next_gpu_lane():
    """Return the least-recently-used dependency lane and its current tail."""
    with _conn() as conn:
        row = conn.execute(
            """
            SELECT lane, tail_job_id, updated_at
            FROM gpu_job_lanes
            ORDER BY updated_at IS NOT NULL, updated_at, lane
            LIMIT 1
            """
        ).fetchone()
        return (row["lane"], row["tail_job_id"], row["updated_at"])


def set_gpu_lane_tail(lane, job_id):
    with _conn() as conn:
        conn.execute(
            "UPDATE gpu_job_lanes SET tail_job_id = ?, updated_at = ? WHERE lane = ?",
            (str(job_id), datetime.now(timezone.utc).isoformat(), lane),
        )


def list_jobs(include_cleared=False):
    """Newest first. Cleared jobs are left out unless asked for."""
    where = "" if include_cleared else " WHERE cleared_at IS NULL"
    with _conn() as conn:
        rows = conn.execute(f"SELECT * FROM jobs{where} ORDER BY submitted_at DESC").fetchall()
        return [dict(r) for r in rows]


def clear_jobs(job_ids):
    """Take finished jobs off the dashboard's lists without deleting them."""
    if not job_ids:
        return
    placeholders = ",".join("?" for _ in job_ids)
    with _conn() as conn:
        conn.execute(
            f"UPDATE jobs SET cleared_at = ? WHERE job_id IN ({placeholders}) AND cleared_at IS NULL",
            (datetime.now(timezone.utc).isoformat(), *(str(job_id) for job_id in job_ids)),
        )


def jobs_for_slot(slot_index):
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM jobs WHERE queue_slot = ? ORDER BY submitted_at", (slot_index,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_job(job_id):
    with _conn() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        return dict(row) if row else None


def get_slot(slot_index):
    with _conn() as conn:
        row = conn.execute("SELECT * FROM queue_slots WHERE slot_index = ?", (slot_index,)).fetchone()
        return dict(row) if row else None


def stage_slot(slot_index, experiment_type, params, save_results=True):
    with _conn() as conn:
        conn.execute(
            "UPDATE queue_slots SET experiment_type = ?, params_json = ?, staged_at = ?, save_results = ? WHERE slot_index = ?",
            (experiment_type, json.dumps(params), datetime.now(timezone.utc).isoformat(), int(save_results), slot_index),
        )


def clear_slot_staged(slot_index):
    with _conn() as conn:
        conn.execute(
            "UPDATE queue_slots SET experiment_type = NULL, params_json = NULL, staged_at = NULL WHERE slot_index = ?",
            (slot_index,),
        )


def clear_slot_jobs(slot_index):
    # Un-links this slot's display from those jobs - doesn't delete them or
    # their results, they still show in the full experiment grid regardless.
    with _conn() as conn:
        conn.execute("UPDATE jobs SET queue_slot = NULL WHERE queue_slot = ?", (slot_index,))


def set_slot_paused(slot_index, paused):
    with _conn() as conn:
        conn.execute(
            "UPDATE queue_slots SET paused = ? WHERE slot_index = ?",
            (int(paused), slot_index),
        )


def mark_pause_requested(job_ids):
    if not job_ids:
        return
    placeholders = ",".join("?" for _ in job_ids)
    with _conn() as conn:
        conn.execute(
            f"UPDATE jobs SET pause_requested = 1 WHERE job_id IN ({placeholders})",
            tuple(str(job_id) for job_id in job_ids),
        )
