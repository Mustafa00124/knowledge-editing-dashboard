#!/bin/bash
# Justifications for every formally checked derived query (justify.py,
# HermiT) as its own CPU job. Submit from the project root:
#   sbatch datasets/SidsDataset/owl/justify.sbatch
# Report: datasets/SidsDataset/owl/justifications.json; log: owl/logs/justify_<jobid>.out
#SBATCH --job-name=sids_justify
#SBATCH --partition=AAIL
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=0
#SBATCH --output=datasets/SidsDataset/owl/logs/justify_%j.out
#SBATCH --error=datasets/SidsDataset/owl/logs/justify_%j.out
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
venvs/easyedit_venv/bin/python datasets/SidsDataset/justify.py --jobs "${SLURM_CPUS_PER_TASK:-4}"
