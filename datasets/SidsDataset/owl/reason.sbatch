#!/bin/bash
# Full formal check of Sid's Dataset (reason.py, HermiT) as its own CPU job,
# so it doesn't depend on an interactive session. Submit from the project root:
#   sbatch datasets/SidsDataset/owl/reason.sbatch
# Report: datasets/SidsDataset/owl/reason_report.json; log: owl/logs/reason_<jobid>.out
#SBATCH --job-name=sids_reason
#SBATCH --partition=AAIL
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=0
#SBATCH --output=datasets/SidsDataset/owl/logs/reason_%j.out
#SBATCH --error=datasets/SidsDataset/owl/logs/reason_%j.out
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
venvs/easyedit_venv/bin/python datasets/SidsDataset/reason.py --jobs "${SLURM_CPUS_PER_TASK:-4}"
