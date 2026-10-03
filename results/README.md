# Results

Experiment output is written here and is not tracked by git. Two trees:

- `main/`: the reported experiments, run on test records.
  - `run_experiment/`: one directory per run under `runs/`, a `manifest.json`
    index the Results page reads, and `archive/` for retired runs.
  - `trial_runs/`: launches made with "Save to main Results" turned off, one
    timestamped folder each.
- `investigations/`: experiments that set up the main runs (sweeps on dev records only, causal tracing, fact sets).
  Organised by what they tune (one folder per investigation, such as
  `edit_layers/`), then by sweep. `causal_tracing/` holds the causal
  tracing runs (per model, no method), `traced_layers.json`, and
  `fact_sets/runs/<name>/` (shared fact lists from
  `experiments/fact_selection/select_facts.py`).

Each run directory has the same files in both trees (`hparams.yaml`,
`checkpoints.jsonl`, `summary.json`, `samples/`), so the same readers work on
both.
