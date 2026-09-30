#!/bin/bash
# Runs the dashboard backend+frontend as their own SLURM job, independent of
# whatever interactive job your VS Code session happens to be using. That
# session's job can end (you close VS Code, it gets killed, whatever) without
# taking the dashboard down with it — closing the interactive session tears
# down its own cgroup, not this one.
#
# Submit:   sbatch dashboard/scripts/dashboard.sbatch
#           (from the project root: the log paths below are relative to it)
# Check:    squeue -u $USER -n ke_dashboard
# Stop:     scancel <jobid>
# Logs:     dashboard/logs/job_<jobid>.out (sbatch-level) and
#           dashboard/logs/backend.log / frontend.log (app-level)
#
#SBATCH --job-name=ke_dashboard
#SBATCH --partition=AAIL
#SBATCH --output=dashboard/logs/job_%j.out
#SBATCH --error=dashboard/logs/job_%j.err
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=0

set -euo pipefail
DASH="$SLURM_SUBMIT_DIR/dashboard"
mkdir -p "$DASH/logs"

"$DASH/scripts/start_backend.sh" > "$DASH/logs/backend.log" 2>&1 &
BACKEND_PID=$!

"$DASH/scripts/start_frontend.sh" > "$DASH/logs/frontend.log" 2>&1 &
FRONTEND_PID=$!

trap 'kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null' TERM EXIT

# If either dies, bring the whole job down rather than limping along with
# only half the dashboard working silently.
wait -n "$BACKEND_PID" "$FRONTEND_PID"
