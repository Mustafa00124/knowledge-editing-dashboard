"""Retiring finished runs out of the live results tree, and putting them back.

manifest.json is *derived*, not authoritative: run_experiment.py rebuilds it
by rescanning runs/*/summary.json at the end of every job. An "archived"
flag written into that file would be silently erased the next time anything
finished. The only durable way to retire a run is to move its directory out
of runs/ - the next rebuild then simply doesn't see it. That rebuild globs
runs/ alone, so an archive/ sitting next to it under the same out_root stays
invisible to the runner.

Layout mirrors the live tree, so results_reader can serve both from one code
path:

    <out_root>/runs/<run>/                         live
    <out_root>/manifest.json                       live, rebuilt by the runner
    <out_root>/archive/runs/<run>/                 archived, same contents
    <out_root>/archive/runs/<run>/archived.json    when, why, + its summary row
    <out_root>/archive/manifest.json               archived counterpart
    <out_root>/archive/log.jsonl                   append-only history

Nothing here deletes anything. Every operation is a rename between those two
directories, and refuses rather than overwrites.
"""
import json
import os
from datetime import datetime
from pathlib import Path

import yaml

import results_reader

# Path layout lives in results_reader, which reads both trees.
ARCHIVE_DIRNAME = results_reader.ARCHIVE_DIRNAME

# Config recorded in hparams.yaml that says what a run *was*. The only way to
# describe a run that never wrote a summary.json, which is exactly the kind
# this page exists to sweep up.
FACT_KEYS = ("method", "model", "dataset_benchmark", "dataset_subset", "ds_size", "lr", "num_steps", "seed")


def _roots(exp_type=None):
    """(out_root, live runs dir, archived runs dir) for a registered type."""
    root = results_reader.out_root(exp_type)
    if not root:
        raise LookupError("no registered experiment type to archive runs for")
    root = Path(root)
    return root, root / "runs", root / ARCHIVE_DIRNAME / "runs"


def rebuild_manifest(runs_dir, manifest_path):
    """Full rescan of runs_dir into manifest_path.

    Deliberately the same scan as run_experiment._rebuild_manifest, so the
    live manifest this writes is byte-identical to the one the runner would
    write next. That keeps the Results page correct the instant a run is
    archived, instead of stale until the next job happens to finish.

    Both are whole-directory rescans rather than read-modify-write, so a job
    finishing mid-archive can at worst re-list a run that just moved (its
    listdir ran before the rename, its write after); the following rebuild
    corrects it, and archive_runs() refuses to touch a run with a live job
    anyway.
    """
    manifest = []
    if runs_dir.exists():
        for name in sorted(os.listdir(runs_dir)):
            summary = runs_dir / name / "summary.json"
            if summary.exists():
                try:
                    manifest.append(json.loads(summary.read_text()))
                except json.JSONDecodeError:
                    continue
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return manifest


def _dir_stats(path):
    files = 0
    size = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            files += 1
            try:
                size += os.path.getsize(os.path.join(dirpath, f))
            except OSError:
                pass
    return files, size


def _run_facts(run_dir):
    path = run_dir / "hparams.yaml"
    if not path.exists():
        return {}
    try:
        data = yaml.safe_load(path.read_text()) or {}
    except (yaml.YAMLError, OSError):
        return {}
    return {k: data.get(k) for k in FACT_KEYS if k in data}


def _checkpoint_count(run_dir):
    path = run_dir / "checkpoints.jsonl"
    if not path.exists():
        return 0
    try:
        return sum(1 for line in path.read_text().splitlines() if line.strip())
    except OSError:
        return 0


def _read_json(path):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def _log(out_root, entries):
    path = out_root / ARCHIVE_DIRNAME / "log.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------- planning

def _plan(names, src_dir, dst_dir):
    """What a move would do, per run, without doing any of it.

    Always returns one row per requested name, `ok` false with a `problem`
    string rather than raising, so one bad name in a batch of twenty doesn't
    cost you the other nineteen.
    """
    rows = []
    for name in dict.fromkeys(names):
        row = {"run": name, "ok": False, "problem": None, "from": None, "to": None, "files": None, "size_mb": None}
        try:
            source = results_reader.run_path(src_dir, name)
            dest = results_reader.run_path(dst_dir, name)
        except ValueError as exc:
            row["problem"] = str(exc)
            rows.append(row)
            continue
        row["from"], row["to"] = str(source), str(dest)
        if not source.is_dir():
            row["problem"] = "no such run"
        elif dest.exists():
            row["problem"] = "a run of that name is already on the other side - rename or move that one first"
        else:
            row["ok"] = True
            files, size = _dir_stats(source)
            row["files"], row["size_mb"] = files, round(size / 1e6, 1)
        rows.append(row)
    return rows


def plan_archive(names, exp_type=None):
    _, runs, archived = _roots(exp_type)
    return _plan(names, runs, archived)


def plan_restore(names, exp_type=None):
    _, runs, archived = _roots(exp_type)
    return _plan(names, archived, runs)


# ---------------------------------------------------------------- moving

def _move(rows, record):
    moved, skipped = [], []
    for row in rows:
        if not row["ok"]:
            skipped.append(row)
            continue
        try:
            os.rename(row["from"], row["to"])
        except OSError as exc:
            row["ok"] = False
            row["problem"] = str(exc)
            skipped.append(row)
            continue
        try:
            record(Path(row["to"]), row["run"])
        except OSError:
            # The move is what matters and it already happened; a missing
            # sidecar is cosmetic, and list_archived() copes with one.
            pass
        moved.append(row["run"])
    return moved, skipped


def archive_runs(names, reason="", exp_type=None):
    out_root, runs, archived = _roots(exp_type)
    archived.mkdir(parents=True, exist_ok=True)
    at = datetime.now().astimezone().isoformat(timespec="seconds")

    def record(dest, name):
        summary = _read_json(dest / "summary.json")
        (dest / "archived.json").write_text(json.dumps(
            {"run": name, "archived_at": at, "reason": reason, "summary": summary}, indent=2))

    moved, skipped = _move(_plan(names, runs, archived), record)
    if moved:
        rebuild_manifest(runs, out_root / "manifest.json")
        rebuild_manifest(archived, out_root / ARCHIVE_DIRNAME / "manifest.json")
        _log(out_root, [{"action": "archive", "run": n, "at": at, "reason": reason} for n in moved])
    return moved, skipped


def restore_runs(names, exp_type=None):
    out_root, runs, archived = _roots(exp_type)
    runs.mkdir(parents=True, exist_ok=True)
    at = datetime.now().astimezone().isoformat(timespec="seconds")

    def record(dest, name):
        # The sidecar describes an archived run; a live one shouldn't carry
        # it around. The log keeps the history.
        sidecar = dest / "archived.json"
        if sidecar.exists():
            sidecar.unlink()

    moved, skipped = _move(_plan(names, archived, runs), record)
    if moved:
        rebuild_manifest(runs, out_root / "manifest.json")
        rebuild_manifest(archived, out_root / ARCHIVE_DIRNAME / "manifest.json")
        _log(out_root, [{"action": "restore", "run": n, "at": at} for n in moved])
    return moved, skipped


# ---------------------------------------------------------------- listing

def list_archived(exp_type=None):
    """Built by scanning archive/runs/, not by reading archive/manifest.json.

    A run archived before it ever wrote a summary.json has no manifest row
    to show, and those are exactly the ones worth listing.
    """
    _, _, archived = _roots(exp_type)
    rows = []
    if not archived.exists():
        return rows
    for name in sorted(os.listdir(archived)):
        run_dir = archived / name
        if not run_dir.is_dir():
            continue
        info = _read_json(run_dir / "archived.json") or {}
        summary = info.get("summary") or _read_json(run_dir / "summary.json")
        rows.append({
            "run": name,
            "archived_at": info.get("archived_at"),
            "reason": info.get("reason") or "",
            "summary": summary,
            "facts": _run_facts(run_dir),
            "checkpoints": _checkpoint_count(run_dir),
        })
    rows.sort(key=lambda r: (r["archived_at"] or "", r["run"]), reverse=True)
    return rows


def list_incomplete(exp_type=None):
    """Live runs with no summary.json.

    The runner's manifest rebuild skips these, so the Results page can never
    show them however long they sit there - they are runs that died before
    finishing. `superseded_by` names any *_rerun* sibling that covers the
    same configuration, which is what makes most of them safe to sweep.
    """
    _, runs, _ = _roots(exp_type)
    rows = []
    if not runs.exists():
        return rows
    names = sorted(n for n in os.listdir(runs) if (runs / n).is_dir())
    for name in names:
        run_dir = runs / name
        if (run_dir / "summary.json").exists():
            continue
        rows.append({
            "run": name,
            "modified_at": datetime.fromtimestamp(run_dir.stat().st_mtime).astimezone().isoformat(timespec="seconds"),
            "facts": _run_facts(run_dir),
            "checkpoints": _checkpoint_count(run_dir),
            "superseded_by": [n for n in names if n.startswith(f"{name}_rerun")],
        })
    return rows
