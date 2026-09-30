#!/usr/bin/env bash
# Run inside tmux so it survives your VS Code session disconnecting.
set -euo pipefail

# On gaivi the system-wide `node` (anaconda3/bin) is v6, too old for Vite,
# so a dedicated conda env provides it there. Anywhere else, the node on
# PATH is used as long as it is new enough.
if command -v conda >/dev/null 2>&1 && conda env list 2>/dev/null | grep -q '^ke-dashboard-node '; then
  source "$(conda info --base)/etc/profile.d/conda.sh"
  conda activate ke-dashboard-node
fi
if ! command -v node >/dev/null 2>&1 || [ "$(node -p 'process.versions.node.split(".")[0]')" -lt 18 ]; then
  echo "Node.js 18 or newer is required (found: $(node -v 2>/dev/null || echo none))." >&2
  exit 1
fi

cd "$(dirname "$0")/../frontend"

if [ ! -d node_modules ]; then
  npm install
fi

exec npm run dev
