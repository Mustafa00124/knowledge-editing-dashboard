#!/bin/bash
# CRITERIA.md Rule 3, the LLM judge's part (rule3_judge.py): one GPU job
# that labels the records not yet judged, or changed since, with the
# project's judge model (Qwen3-4B-Instruct-2507). Submit from the project root:
#   sbatch datasets/SidsDataset/rule3_judge.sbatch            # missing and changed records
#   sbatch datasets/SidsDataset/rule3_judge.sbatch --all      # every record again
# Labels: datasets/SidsDataset/rule3_judge.json (criteria.py reads it);
# log: datasets/SidsDataset/logs/rule3_judge_<jobid>.out
#SBATCH --job-name=sids_rule3_judge
#SBATCH --partition=AAIL
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=32G
#SBATCH --output=datasets/SidsDataset/logs/rule3_judge_%j.out
#SBATCH --error=datasets/SidsDataset/logs/rule3_judge_%j.out
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
exec venvs/easyedit_venv/bin/python -u datasets/SidsDataset/rule3_judge.py "$@"
