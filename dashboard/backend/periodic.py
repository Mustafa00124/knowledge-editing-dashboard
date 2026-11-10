"""Run local maintenance commands on a timer inside the backend process, so
they live as long as the dashboard job (an interactive SLURM job dies with
VS Code, cron is not allowed on gaivi, and a separate job would take one of
the 6 per-user slots).

Configured by dashboard/backend/periodic.local.json (not tracked), e.g.

    [{"name": "step3", "command": ["python3", "scripts/step3_advance.py"], "every_min": 10}]

Commands run from the project root, one at a time per entry, and append to
dashboard/logs/periodic_<name>.log. No file, no commands. The file is reread
every minute, so entries can be added or removed without a restart.
"""
import json
import subprocess
import threading
import time
from pathlib import Path

BACKEND = Path(__file__).resolve().parent
ROOT = BACKEND.parent.parent
CONFIG = BACKEND / "periodic.local.json"
LOGS = ROOT / "dashboard" / "logs"

_started = False
_last = {}


def _entries():
    try:
        data = json.loads(CONFIG.read_text())
    except (OSError, ValueError):
        return []
    return [e for e in data if isinstance(e, dict) and e.get("name") and e.get("command")]


def _run(entry):
    LOGS.mkdir(parents=True, exist_ok=True)
    with open(LOGS / f"periodic_{entry['name']}.log", "a") as fh:
        try:
            subprocess.run(entry["command"], cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT,
                           timeout=int(entry.get("timeout_min", 30)) * 60)
        except Exception as e:  # keep the loop alive whatever a command does
            fh.write(f"periodic: {entry['name']} failed to run: {e!r}\n")


def _loop():
    while True:
        for entry in _entries():
            every = float(entry.get("every_min", 10)) * 60
            if time.time() - _last.get(entry["name"], 0) >= every:
                _last[entry["name"]] = time.time()
                _run(entry)
        time.sleep(60)


def start():
    """Start the timer thread once per process."""
    global _started
    if _started:
        return
    _started = True
    threading.Thread(target=_loop, name="periodic", daemon=True).start()
