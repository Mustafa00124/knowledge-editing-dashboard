#!/usr/bin/env bash
# Run inside tmux so it survives your VS Code session disconnecting.
set -euo pipefail
cd "$(dirname "$0")/../backend"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q -r requirements.txt

# 0.0.0.0: on gaivi the login node can only reach GPU57 over the internal
# 10.10.10.0/24 network, not loopback. See dashboard/README.md for the
# reachability story and the auth this requires. DASHBOARD_HOST=127.0.0.1
# keeps a laptop copy private to that machine.
exec python -m uvicorn main:app --host "${DASHBOARD_HOST:-0.0.0.0}" --port 8000 --reload
