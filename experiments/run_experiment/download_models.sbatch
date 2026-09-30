#!/bin/bash
# Downloads the base/instruct/reasoning variant sets for the Qwen3-4B and
# Olmo-3-7B families, so tuning stage can be isolated against a fixed
# pretrain. Runs as its own SLURM job for the same reason the dashboard does:
# an interactive VS Code session's job can die without taking this with it.
#
# Submit:   sbatch experiments/run_experiment/download_models.sbatch
#           (from the project root: the log paths below are relative to it)
# Check:    squeue -u $USER -n ke_download
# Logs:     experiments/run_experiment/logs/download_<jobid>.out
#
# Local dir names follow the existing models/ convention (the date stamp in
# allenai/Olmo-3-1025-7B is dropped the same way OLMo-2-1124-7B became
# OLMo-2-7B). The name matters: ROME/MEMIT/PMET/AlphaEdit key their cached
# mom2 covariance stats by this directory's basename.
#
#SBATCH --job-name=ke_download
#SBATCH --partition=AAIL
#SBATCH --output=experiments/run_experiment/logs/download_%j.out
#SBATCH --error=experiments/run_experiment/logs/download_%j.err
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=0

set -uo pipefail
ROOT="$SLURM_SUBMIT_DIR"
HF="$ROOT/venvs/easyedit_venv/bin/hf"
mkdir -p "$ROOT/experiments/run_experiment/logs"

# repo -> local directory name
PAIRS=(
  "Qwen/Qwen3-4B-Base|Qwen3-4B-Base"
  "Qwen/Qwen3-4B-Instruct-2507|Qwen3-4B-Instruct-2507"
  "Qwen/Qwen3-4B-Thinking-2507|Qwen3-4B-Thinking-2507"
  "allenai/Olmo-3-1025-7B|Olmo-3-7B-Base"
  "allenai/Olmo-3-7B-Instruct|Olmo-3-7B-Instruct"
  "allenai/Olmo-3-7B-Think|Olmo-3-7B-Think"
)

failed=()
for pair in "${PAIRS[@]}"; do
  repo="${pair%%|*}"
  dir="${pair##*|}"
  echo "=== $(date -Is)  $repo -> models/$dir"
  # hf download resumes, so a re-submit after an interruption is cheap.
  if "$HF" download "$repo" --local-dir "$ROOT/models/$dir" --exclude "original/*"; then
    echo "--- ok: $dir ($(du -sh "$ROOT/models/$dir" | cut -f1))"
  else
    echo "--- FAILED: $repo"
    failed+=("$repo")
  fi
done

echo "=== $(date -Is) done"
if ((${#failed[@]})); then
  printf 'failed: %s\n' "${failed[@]}"
  exit 1
fi
