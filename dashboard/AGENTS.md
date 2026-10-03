# Running experiments as an agent

Every experiment goes through the dashboard, so that it shows on its
investigation's **Progress** section (and in the "Running now" strip on
Experiments → Investigations) while it runs, labelled as yours. Use
`scripts/dash.py`, a small command-line client for the dashboard's API. Do
not run `run_experiment.py`, `causal_trace.py`, `neuron_trace.py`,
`circuit_trace.py` or `select_facts.py` yourself, and do not write sbatch
files: a runner refuses to write into `results/` unless the dashboard
launched it (`experiments/launch_guard.py`).

## Connecting

Run everything from the project root, `/AAIL/msiddiqui146/knowledge-editing`.

```bash
python scripts/dash.py whoami          # {"role": "agent"} when connected
```

- **Address.** `KE_DASHBOARD_URL` if set. Otherwise `dashboard/backend/.backend_url`,
  which the backend writes when it starts. Otherwise the node of the user's
  running `ke_dashboard` SLURM job, port 8000. Otherwise `http://localhost:8000`.
- **Token.** `KE_DASHBOARD_TOKEN` if set, otherwise `dashboard/backend/.agent_token`.
  This is the agent token: your launches are recorded as `launched_by: agent`
  and shown with an "agent" badge. Never use `.auth_token` (the user's).
- "cannot reach the dashboard": the backend is not running. Ask the user to
  start it (`dashboard/README.md`); do not start your own copy.

## The loop

1. **Look up** what exists:
   ```bash
   python scripts/dash.py investigations       # ids, group, sweep or launch, what runs now
   python scripts/dash.py types                # experiment types
   python scripts/dash.py fields causal_tracing
   ```
   `fields` lists every field with its type, default and allowed values. A
   field's name is the runner's flag (`--n_prompts`), so `python
   <runner> --help` in the experiment's folder explains the rest.
2. **Dry run.** Always first. It resolves every value and prints each run's
   name and exact command, anything that would block it on this machine
   (missing weights, dataset or environment), and runs whose output already
   exists:
   ```bash
   python scripts/dash.py launch causal_tracing --label "Qwen3 question format" --dry-run \
       -- --model qwen3-4b --format question --fact_set <path from fields>
   ```
3. **Launch**: the same command without `--dry-run`. Give a `--label` that
   says what the launch is for (required) and a `--note` saying why. The
   output names the launch id.
4. **Follow it**:
   ```bash
   python scripts/dash.py status                     # every active launch
   python scripts/dash.py status <launch-id> --wait  # poll until it ends; exit 1 if a run failed
   ```
   A finished launch lists every run's state, and for failed runs the last
   lines of the error log.
5. **Read the results** (below), then report to the user what ran, the launch
   id, and what came out.

## Launching an experiment type

`dash.py launch TYPE [options] -- <runner flags>`. Everything after `--` is
written as on the runner's command line.

- **Sweep a field** by repeating its flag: `-- --model qwen3-4b --model llama-3.1-8b`
  is two runs. Every combination of repeated flags runs.
- **Unknown flags are errors**, never dropped silently. The error lists the
  type's fields.
- **A flag the runner takes but the form has no field for** goes in
  `--extra="--flag value"` (repeatable). It is passed through as given,
  recorded with the job, and gives the run name a `_x<hash>` suffix so it never
  writes over an ordinary run.
- `--investigation ID` sets which investigation's page shows the launch.
  Left out, it follows from the type:

  | Type | Investigation |
  | --- | --- |
  | `causal_tracing` | `causal_tracing`; `tracing_formats` when any `--format` other than `completion` is given |
  | `neuron_tracing` | `neuron_tracing` |
  | `circuit_tracing` | `circuit_tracing` |
  | `fact_selection` | `causal_tracing` (fact sets serve the tracing studies) |
  | `run_experiment` | none: a main experiment |

  A hyperparameter sweep investigation cannot be given here (see below).
- `--trial` writes to `results/main/trial_runs/` instead of the real results:
  for checking that something runs at all.
- `--after JOBID` makes the runs wait until that SLURM job succeeded (e.g.
  traces on a fact set whose selection is still running).

## Hyperparameter sweeps

Sweep investigations (`dash.py investigations` shows "sweep") tune an editing
method's settings, and only ever on **dev records**. They take a JSON spec:

```json
{
 "investigation": "edit_layers",
 "methods": {"memit": {"layers": [[3, 4, 5, 6, 7], [5, 6, 7, 8, 9]]}},
 "models": ["qwen3-4b"],
 "data_paths": ["<a data_path value from: dash.py fields run_experiment>"],
 "ds_size": "full",
 "edit_mode": "batch",
 "label": "MEMIT window either side of the default, Qwen3",
 "note": "checks whether the traced peak is the best window"
}
```

```bash
python scripts/dash.py sweep spec.json --estimate   # runs, GPU hours, statistics still to compute
python scripts/dash.py sweep spec.json              # launch
```

- Which settings each investigation sweeps for which method, their current
  values and suggested values: `dash.py get /api/hparams/investigations`.
- What the sweep holds constant: `dash.py get "/api/hparams/settings?investigation=edit_layers&methods=memit&models=qwen3-4b"`.
  Change a held value with `"fixed": {"memit": {"qwen3-4b": {"kl_factor": 0.1}}}`.
- Rerun a sweep's failed runs: `dash.py post /api/hparams/sweeps/<investigation>/<sweep-id>/rerun-failed`.

## Reading results

| What | Command |
| --- | --- |
| Sweep runs, scored | `dash.py get "/api/hparams/results?investigation=edit_layers"` |
| Failed sweep runs and their errors | `dash.py get /api/hparams/failures` |
| Causal tracing (runs, peaks, verdicts) | `dash.py get /api/causal-tracing`, then `/api/causal-tracing/runs/<run>` |
| Neuron attribution, circuit tracing | `dash.py get /api/mechanistic/neuron_tracing` (or `circuit_tracing`), then `/runs/<run>` |
| Main experiments | `dash.py get "/api/results/manifest?type=run_experiment"`, `/api/results/runs/<run>/checkpoints` |

On disk, every run is `results/<...>/runs/<run_name>/` with `hparams.yaml`,
`checkpoints.jsonl` and, once finished, `summary.json`; `results/README.md`
maps the tree.

## What the agent token can and cannot do

| Allowed | Refused with 403: ask the user |
| --- | --- |
| Read everything: investigations, types, fields, models, datasets, results, queue and GPU status | Promote a sweep result into the main configuration (`/api/hparams/promote`) |
| Dry runs and estimates | Archive or restore results, delete or hide sweeps |
| Launch experiments and sweeps | Downloads |
| Follow, cancel and rerun **its own** launches | The Experiments page's queue slots (stage, launch, pause, cancel) |
| | Cancel or rerun what the user launched |

## Rules

- **Never tune on test records.** Settings are chosen by sweeps, which run on
  dev records only. Tracing runs use `nontest` or `all` (see their `--split`
  field), never `test`.
- **Dry-run first, then launch with a label.** Keep launches small enough to
  read: a few models or values at a time.
- **Mind the GPUs.** The dashboard runs at most four GPU jobs at once across
  everyone's launches, and the user has six SLURM job slots in total; the
  rest wait (status shows why). Do not launch more to get ahead in the queue.
- **Do not run the runners by hand.** If something truly has to run outside
  the dashboard, ask the user first; then `--untracked` lets it write into
  `results/`, and it will not show on any progress section.
- **Cancel only your own launches**, and say so when you do.
- The user decides what becomes the main configuration: report the best
  settings, do not promote them.

## API reference

All under `/api`, header `x-dashboard-token`. `dash.py get` and `dash.py post`
reach any of them.

| Endpoint | |
| --- | --- |
| `GET /whoami` | `{"role": "agent" or "user"}` |
| `GET /experiment-types` | types and their fields |
| `POST /experiments` | launch: `experiment_type`, `params` (`{field: [values]}`) and/or `args` (a command-line string), `extra_args`, `investigation`, `label`, `note`, `save_results`, `after_ok`, `dry_run` |
| `GET /launches?investigation=&active=&days=&limit=` | launches newest first, with progress; `investigation=main` for main experiments |
| `GET /launches/summary` | active launches, running and waiting runs per investigation |
| `GET /launches/{id}` | one launch and every run (state, settings, error tail) |
| `POST /launches/{id}/cancel` | cancel its queued and running jobs |
| `GET /hparams/investigations` | investigations, the settings each sweeps, current and suggested values |
| `POST /hparams/estimate`, `POST /hparams/sweeps` | estimate, launch a sweep |
| `GET /queue/gpu-status` | GPUs on the node and what holds them |
