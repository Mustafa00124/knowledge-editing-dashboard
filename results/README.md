# Results

Experiment output is written here and is not tracked by git. Two trees:

- `main/`: the reported experiments, run on test records.
  - `run_experiment/`: one directory per run under `runs/`, a `manifest.json`
    index the Results page reads, and `archive/` for retired runs.
  - `trial_runs/`: launches made with "Save to main Results" turned off, one
    timestamped folder each.
- `hyperparameters/`: sweeps that pick settings, run on dev records only.
  Organised by what they tune (one folder per investigation, such as
  `edit_layers/`), then by sweep. `edit_layers/causal_tracing/` holds the
  causal tracing runs and `traced_layers.json`.

Each run directory has the same files in both trees (`hparams.yaml`,
`checkpoints.jsonl`, `summary.json`, `samples/`), so the same readers work on
both.
