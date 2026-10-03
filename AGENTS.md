# Knowledge-editing project: notes for agents

- **Running experiments:** only through the dashboard, with `scripts/dash.py`.
  Read `dashboard/AGENTS.md` first. Runs launched any other way do not show
  on the investigations' progress sections, and the runners refuse to write
  into `results/` unless the dashboard launched them.
- **Never tune on test records.** Hyperparameter sweeps run on dev records
  only; the user decides what becomes the main configuration.
- **Layout:** `README.md` (project), `dashboard/README.md` (dashboard),
  `results/README.md` (results tree). Paths in tracked files stay relative to
  the project root (`hparams/*.yaml`) or use `${PROJECT_ROOT}` (`dashboard.json`).
- **Never commit** `dashboard/backend/.auth_token`, `.agent_token`,
  `experiments/run_experiment/evaluation.local.json`, models, datasets or
  results.
