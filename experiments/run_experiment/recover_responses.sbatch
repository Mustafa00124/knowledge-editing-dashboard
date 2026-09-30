#!/bin/bash
#SBATCH --job-name=recover_responses
#SBATCH --partition=AAIL
#SBATCH --output=experiments/run_experiment/logs/%x_%j.out
#SBATCH --error=experiments/run_experiment/logs/%x_%j.err
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=32G

# Submit from the project root: the log paths above are relative to it.
set -euo pipefail
ROOT="$SLURM_SUBMIT_DIR"
cd "$ROOT/experiments/run_experiment"
exec "$ROOT/venvs/easyedit_venv/bin/python" -u recover_responses.py
