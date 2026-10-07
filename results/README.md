# Results

Experiment output is written here and is not tracked by git. Two trees:

- `main/`: the reported experiments, run on test records.
  - `run_experiment/`: one directory per run under `runs/`, a `manifest.json`
    index the Results page reads, and `archive/` for retired runs.
  - `in_context/`: the In context experiment (SCR against a knowledge base
    of `kb_size` facts), laid out like `run_experiment/`.
  - `trial_runs/`: launches made with "Save to main Results" turned off, one
    timestamped folder each.
- `investigations/`: experiments that set up the main runs (sweeps on dev records only, causal tracing, fact sets).
  One folder per investigation (a method family such as `locate_edit/`, or
  an earlier by-setting one such as `edit_layers/`), then by sweep. `causal_tracing/` holds the causal
  tracing runs (per model, no method), `traced_layers.json`, and
  `fact_sets/runs/<name>/` (shared fact lists from
  `experiments/fact_selection/select_facts.py`).
  `neuron_tracing/` and `circuit_tracing/` hold the neuron attribution and
  circuit tracing runs (per model, no method; `runs/<run>/neurons.json`,
  `circuit.json`).

Each run directory has the same files in both trees (`hparams.yaml`,
`checkpoints.jsonl`, `summary.json`, `samples/`), so the same readers work on
both.
