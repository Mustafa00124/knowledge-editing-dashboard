# Knowledge Editing

Compares knowledge editing methods (fine-tuning, LoRA, ROME, MEMIT, PMET,
AlphaEdit, WilKE, FiNE, NMKE, FiDAL, Knowledge Neurons, CaKE, SCR, IKE)
across language models and benchmarks. SNKE and MCircKE are listed but not
implemented: no public implementation was found. It records checkpointed metrics and generated answers, and ships
a web dashboard for launching experiments and browsing results and datasets.

It was built on USF's gaivi SLURM cluster, but a clone runs anywhere. The
repo holds code and configs only. Datasets, models and the experiment
tooling are downloaded on request, choosing exactly which ones, from the
dashboard's **Downloads** page or `scripts/setup.py`.

| You have | You can |
| --- | --- |
| Just the clone | Open the dashboard, see the Methods and Models pages, and pick what to download |
| + some datasets | Browse those benchmarks on the Datasets page |
| + EasyEdit, the experiment environment, a model, and an NVIDIA GPU | Launch experiments; they run one at a time as local background jobs |
| + SLURM | Launch sweeps as SLURM jobs, the way gaivi does |

Anything the machine lacks is greyed out in the dashboard, with the reason
and a way to get it.

## Quick start

Needs Python 3.10+ (3.11 is what the project uses), Node.js 18+, and git.

```bash
git clone <this repo> knowledge-editing
cd knowledge-editing

# Dashboard (two terminals). The backend makes its own small venv; the
# frontend runs npm install on first start.
DASHBOARD_HOST=127.0.0.1 dashboard/scripts/start_backend.sh
dashboard/scripts/start_frontend.sh
```

Open http://localhost:5173. The first load asks for the auth token, which the
backend prints on startup and saves in `dashboard/backend/.auth_token`.

Then open **Downloads** and tick what you want. It lists every dataset,
model and setup component with its size and your free disk space, has quick
picks ("Every dataset", "A first experiment", "Everything for the main
experiments"), and shows progress as items download one at a time. A
cancelled or interrupted download resumes from where it stopped.

The same from a terminal:

```bash
python scripts/setup.py --status                     # what is present, with sizes
python scripts/setup.py --datasets KnowEdit MQuAKE   # just these (no names = every dataset)
python scripts/setup.py --external --venv            # EasyEdit + the experiment environment
python scripts/setup.py --models Qwen3-4B            # or --models main for the main set (~95 GB)
```

A 4B model needs roughly a 24 GB GPU; the 7B models need more. Gated models
(Llama, Gemma) need their license accepted on huggingface.co and
`hf auth login` on the machine first.

## What gets downloaded

| Piece | Size | Where it comes from |
| --- | --- | --- |
| Datasets, 15 benchmarks | 1 MB to 1.3 GB each (UniEdit's optional train split adds 2.5 GB) | Each benchmark's original release at a pinned version, listed with sha256s in `datasets/<name>/SOURCE.json` and checked on download |
| EasyEdit | 200 MB | GitHub at a pinned commit, plus this project's AlphaEdit fix from `patches/` |
| Experiment environment (`venvs/easyedit_venv`) | about 6.5 GB | pip, from EasyEdit's requirements and `requirements-evaluation.txt` |
| Models | 8 to 24 GB each for the main set | Hugging Face, skipping duplicate weight formats |

Not downloaded, but produced locally:

| Piece | Notes |
| --- | --- |
| `results/*` | written by experiments |
| `experiments/run_experiment/data/stats` | covariance statistics, computed on the first locate-and-edit run per model and layer (up to ~20 GB) |
| `experiments/run_experiment/evaluation.local.json` | copy `evaluation.example.json` and add an API key, only for the LLM Judge evaluation mode |

## Dev and test records

Every runnable dataset subset is split once, for good, into dev and test
records (`splits/`, built by `scripts/make_splits.py`). Hyperparameter
sweeps use only dev records (100 per subset, fewer for small ones); main
experiments use only test records. Records are grouped by subject, and a
subject that is dev anywhere is excluded from every test set, so
overlapping benchmarks cannot leak a tuned fact into a reported score.
Datasets without a train file also get a separate demo portion, IKE's
demonstration pool, so IKE never draws demonstrations from the records it
is scored on. `experiments/run_experiment/test_splits.py` checks all of it.

## Layout

| Path | What it is |
| --- | --- |
| `dashboard/` | FastAPI backend and React frontend. `dashboard/README.md` covers features, gaivi deployment and access. |
| `experiments/run_experiment/` | The unified runner (`run_experiment.py`), per-method, per-model `hparams/`, and evaluation code. |
| `experiments/causal_tracing/` | Causal tracing to locate where a model stores facts. |
| `experiments/neuron_tracing/`, `experiments/circuit_tracing/` | Neuron attribution and circuit tracing: which MLP neurons, and which heads and paths, carry a fact. |
| `datasets/` | One folder per benchmark. Git tracks only each one's `SOURCE.json` manifest; the data is downloaded into it. |
| `scripts/setup.py` | Command-line version of the Downloads page. |
| `splits/` | The fixed dev/test split, one file per dataset subset. |
| `experiments/run_experiment/investigations.json` | The investigations (mechanistic, hyperparameter sweeps per method family, input and context) on the dashboard's Experiments → Investigations page. |
| `experiments/in_context/dashboard.json` | The In context main experiment: SCR asked against `--kb_size` facts (its own plus distractors), on Experiments → In context. |
| `patches/` | Local fixes applied on top of pinned upstream repos. |

Paths in configs are relative to the repo root (`hparams/*.yaml`) or written
as `${PROJECT_ROOT}` (`dashboard.json`), so the checkout can live anywhere.

## Running an experiment from a shell

Launch through the dashboard so the run shows on its investigation's
progress section; `scripts/dash.py` does that from a shell (the guide is
`dashboard/AGENTS.md`):

```bash
python scripts/dash.py launch run_experiment --label "ROME on Qwen3, 20 facts" --dry-run \
    -- --method rome --model qwen3-4b --ds_size 20
```

The runners refuse to write into `results/` when the dashboard did not
launch them. To run one by hand anyway, pass `--untracked` (it will not show
on the dashboard), or point `--out_root` outside `results/`:

```bash
cd experiments/run_experiment
../../venvs/easyedit_venv/bin/python run_experiment.py --method rome --model qwen3-4b --ds_size 20 --untracked
```

`--split test` is the default; pass `--split dev --final_only --hparam layers=[4]`
to reproduce a hyperparameter sweep point by hand. Output lands in
`results/main/run_experiment/runs/<run_name>/`. See
`python run_experiment.py --help` for every option.

## Tests

```bash
cd dashboard/backend && .venv/bin/python -m unittest discover -p 'test_*.py'
```
