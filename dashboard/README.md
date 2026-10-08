# Knowledge-Editing Dashboard

## Evaluation modes

The New Experiment sidebar supports selecting one or more evaluation modes.
The selection belongs to one editing run; it does not multiply the sweep size.

- **Original** keeps the existing EasyEdit token metrics and SCR/IKE matching
  metrics, including the original fluency schedule.
- **Exact Match** compares normalized generated answers with their references.
  It ignores case, punctuation, articles, and extra whitespace, following the
  WILD evaluation's exact-match normalization. For locality, it compares the
  post-edit answer to the step-zero answer.
- **BERTScore** uses token-level contextual embeddings with the cached
  `sentence-transformers/all-MiniLM-L6-v2` model on CPU. It reports raw F1
  similarity, not an accuracy percentage. The BERTScore view explains that
  factual errors can still receive high similarity scores.
- **LLM Judge** scores reference correctness for edit success/generalizability
  and factual answer preservation for locality. It accepts paraphrases and
  treats edited facts as authoritative hypothetical facts. Uncertain judgments
  and errors are excluded from the scored denominator; coverage is saved.

All three generated-answer modes share answers at every evaluation checkpoint.
Locality compares each answer with its step-zero answer, rather than using the
dataset answer as a correctness test. IKE's semantic baseline is an unedited
completion without the new fact in the prompt; its Original mode retains the
existing IKE evaluation protocol. Semantic modes do not produce a fluency score.

The runner environment has `bert-score==0.3.13` installed; for another
environment, install `../experiments/run_experiment/requirements-evaluation.txt`.
Settings and the placeholder API key live in
`../experiments/run_experiment/evaluation.local.json` (ignored by Git, owner-only
permissions). Replace `YOUR_API_KEY_HERE` there, or set `KE_JUDGE_API_KEY` for both
the dashboard and experiment jobs. `KE_JUDGE_BASE_URL` and `KE_JUDGE_MODEL` can
override the endpoint/model. The defaults use DeepSeek's OpenAI-compatible API.
Only key-presence/placeholder validation is performed before launch; provider
authentication is checked when the judge is called. Refresh the page after
changing configuration. The key is never sent to the browser or saved in run
settings, summaries, or generated SLURM scripts.

Select a mode in Results to view its table, graph, and response details. Older
runs have Original scores only. The Responses view for semantic modes includes
every probe's reference, before/after text, score, and judge verdict/reason.
Trial Runs also has a mode selector. New per-checkpoint data is saved as:

```
runs/<run>/evaluations/step_<step>.json
```

`checkpoints.jsonl` and `summary.json` contain an `evaluations` object keyed by
mode, plus `evaluation_modes`. Legacy top-level quality fields remain
Original-only, and are null if Original was not selected. Model/rubric settings
are recorded without credentials. Generation is greedy; normal completion
prompts also support the base models without chat templates. Default output
length is 80 tokens; SCR/IKE use their method's configured output length.

A small internal dashboard for launching experiments on SLURM and browsing
results, without leaving the browser. Backend (FastAPI) runs on gaivi and
wraps `sbatch`/`sacct`/`scancel`; frontend (React) talks to it over `/api`.
It reads/writes nothing outside this repo except submitting SLURM jobs and
reading `../experiments/`, `../results/`, `../datasets/`.

## Running it

**Important**: your VS Code session on gaivi runs *inside its own SLURM
interactive job*. Closing VS Code (or that job otherwise dying) kills
everything in that job's cgroup — including anything you launched from
its terminal, even with `nohup`/`disown`. `nohup` only protects against a
terminal hangup, not the whole job being torn down.

So run the dashboard as its **own** SLURM job instead, decoupled from
whatever interactive job your editor happens to be using:

```bash
sbatch dashboard/scripts/dashboard.sbatch   # from the project root
# Submitted batch job <id>

squeue -u $USER -n ke_dashboard   # check it's running
scancel <id>                       # stop it
```

Logs: `dashboard/logs/job_<id>.out|.err` (sbatch-level) and
`dashboard/logs/backend.log` / `frontend.log` (the actual app output).

It requests no GPU, 2 CPUs, 4G mem, no time limit — it'll keep running
until you `scancel` it or the node reboots, independent of your VS Code
session's own job cycling.

First run will be slow (backend creates a local venv + installs
fastapi/uvicorn; frontend runs `npm install`) — both already ran once, so
should be fast now. If you'd rather run it directly in a terminal instead
(e.g. while actively developing it, to see errors live), `start_backend.sh`
/ `start_frontend.sh` still work standalone — just know they die with your
interactive job.

## Running it off gaivi

The same code runs on any machine; see the repo's top-level README for
setup. Two things differ:

- **No SLURM.** When `sbatch` is not on PATH (or `KE_SCHEDULER=local` is
  set), a launch runs the generated script as a background process
  (`backend/local_jobs.py`). Jobs run one at a time, since they would share
  one GPU, and report sacct-style states, so queue cards, pause/resume and
  retries behave as on gaivi. State lives in `backend/local_jobs/`.
- **Missing pieces are greyed out.** `/api/capabilities` reports what the
  machine lacks (NVIDIA GPU, `venvs/easyedit_venv`, `external/EasyEdit`), and
  the Experiments and Causal Tracing pages show it and disable Launch. Models
  without weights under `models/` and dataset subsets without files are
  disabled in the picker. The backend refuses such a launch too, with the
  same reasons.

- **Nothing is downloaded up front.** The **Downloads** page (`/downloads`)
  lists every dataset, model and setup component (EasyEdit, the experiment
  environment) with its size, status and free disk space. Ticked items
  become background tasks that run `scripts/setup.py` for one item each,
  one at a time on their own lock, so they never wait behind an
  experiment. Progress is bytes on disk against the recorded size; cancel
  keeps what was fetched, and starting again resumes. The Datasets and
  Models pages also have a Download button on anything missing.
  `backend/sources.py` is the catalog both the page and `setup.py` use;
  `backend/downloads.py` runs the tasks. Task logs are in
  `logs/downloads/`.

`KE_PYTHON` points jobs at a different interpreter than
`venvs/easyedit_venv`, and `DASHBOARD_HOST=127.0.0.1` keeps the backend off
the network on a personal machine.

## Reaching it from your laptop

**VS Code's built-in port forwarding doesn't work for this.** It tunnels
to whatever host your Remote-SSH session actually terminates on — the
login node, since gaivi only allows direct SSH there and puts you on a
GPU node via Slurm (`srun`/`salloc`), not a second SSH hop. GPU57 has no
route out to the wider internet either. So the app has to be reachable
*from the login node*, over the cluster's internal network — which is why
both processes bind to `0.0.0.0` (all interfaces) rather than `127.0.0.1`.

That does mean the app is now reachable by anything else that can route
to GPU57 on the internal network — not just you. Since it can submit
SLURM jobs on your behalf, `main.py` gates every `/api/*` request behind
a random shared-secret token (`backend/.auth_token`, generated on first
run, gitignored, also printed to `backend.log`/the sbatch job log). It's
a deterrent against casual/opportunistic access on that internal network,
not real security against a targeted attacker who's already on it.

Vite proxies `/api` calls to the backend *inside the GPU57 process*, so
your laptop only ever needs to reach port **5173** — never 8000 directly.
One SSH hop, authenticating only against the login node (no SSH to GPU57
needed at all — this is a plain TCP relay, not a second SSH login):

```bash
# from a terminal ON YOUR LAPTOP (not through VS Code)
ssh -L 5173:10.10.10.57:5173 msiddiqui146@gaivi.cse.usf.edu
```

Leave that running, then open `http://localhost:5173`. First load prompts
for the auth token (see above for where to find it) and remembers it in
the browser's localStorage after that.

(`10.10.10.57` is GPU57's current internal IP — reconfirm with `ip addr`
on GPU57 if it's ever reassigned a different one.)

## Pages

The Datasets page includes downloaded ConflictEdit (GPT-J and GPT2-XL
splits), ReCoE (six reasoning schemes), and the 700-item public Altered Riddles
auxiliary set. Their original files live under `datasets/` with a pinned
`SOURCE.json` manifest, and the page adapts each source schema for browsing.
These additions are browse-only in the experiment picker: ConflictEdit and
ReCoE need benchmark-specific multi-edit evaluation, while Altered Riddles is
a reasoning probe rather than a knowledge-editing request.

**One GPU queue, the same on every page.** The 8 GPU queue cards are shared:
Main experiments, In context, every hyperparameter sweep page and every
per-model page (knowledge localisation, neuron attribution, circuit tracing,
knowledge by format) show the same cards, the GPU panel below them and the
page's progress section, and each has the same slide-out drawer (`+ New ...`
button or the tab on the left edge) for its own kind of experiment. The drawer
stages onto a card (`QueueDrawer.jsx`: pick the card, fill the form); nothing
runs until Launch on the card. The shared pieces are `lib/useQueue.js` (polling
and card actions), `GpuQueue.jsx` (cards, detail modal, GPU panel),
`ExperimentDrawer.jsx` (any type's dashboard.json fields) and
`MechanisticDrawer.jsx` (per-model pages: models plus their settings). A
hyperparameter sweep is staged as a card of type `hparam_sweep`
(`POST /api/queue/{slot}/stage-sweep` with the sweep spec, planned at staging
so a bad spec fails there); Launch submits it through `hparam_sweeps.launch`,
and Rerun failed or Play resubmit its runs through the sweep
(`hparam_sweeps.resubmit`) under their own run names, so `sweep.json` and the
results follow them. Sweeps an agent launches through `/api/hparams/sweeps`
do not sit on a card; they show in the progress section and the sweep list.

The Experiments page includes a read-only GPU allocation panel below the
queue cards. It shows which physical GPU indices SLURM reports as free or
allocated, maps running dashboard jobs to their assigned GPU when available,
and opens a scrollable pending-jobs modal with their SLURM reasons. The physical
GPU tiles show a circular PyTorch memory gauge from the latest checkpoint of a
dashboard job; new runs also record device capacity for a used/total display.
These samples are not live whole-device utilization, and memory for other jobs
is unavailable. The allocation panel refreshes on demand and every minute while
the Experiments page is open. Queue card
numbers do not pin jobs to matching physical GPU numbers.

A failed queue card can rerun only its failed or cancelled terminal jobs from
the detail modal. Retries reuse each job's resolved settings, submit new SLURM
jobs on the same card, and write to distinct run names. Completed siblings and
older attempt logs stay visible; the card status reflects the latest attempt
of each job. Trial Run retries get a new timestamped Trial Runs folder.

A running queue card can also be **paused**. Pause records which experiments
are unfinished and cancels their SLURM jobs, freeing their CPU/GPU allocations;
completed experiments on the same card are left alone. Play resubmits only the
interrupted experiments with the exact resolved settings and distinct
`_resume...` run names. This is restart-from-the-previous-experiment behavior,
not process-level continuation: `checkpoints.jsonl` stores evaluation metrics,
not model/optimizer/RNG state. SLURM's native suspend/resume is intentionally
not used because a suspended job keeps its allocation (including its GPU) and
continues consuming wall-clock time. Immediately after Pause, Play may ask you
to wait a few seconds for `scancel` to reach a terminal state.

In New Experiment, **Save to main Results** is on by default. Turn it off
before staging to send that launch to `results/Trial Runs/<UTC timestamp>/`
instead. Each testing launch gets its own output root, including checkpoints,
samples, summary, and manifest; it never enters the organized main manifest.
The Results → Trial Runs tab lists these launches newest first and shows
their live SLURM status, settings, metrics, summary, samples, and logs.

Runs can be **archived** rather than left to clutter the table forever. On
Results → Table, "Select runs" turns each cell into a toggle over the runs it
averages (a row label selects the whole row), and the tray that appears
archives whatever you picked. The Results → Archive tab lists what has been
retired and puts anything back. Archiving *moves the run's directory* from
`results/<type>/runs/<run>/` to `results/<type>/archive/runs/<run>/`; it never
edits `manifest.json`, because the runner rebuilds that file from
`runs/*/summary.json` at the end of every job and would simply undo any flag
written into it. Moving the directory is the only thing that sticks. Nothing
is deleted: `archive/runs/<run>/archived.json` records when and why, the moves
are logged to `archive/log.jsonl`, and Restore is the same move backwards.

A run a SLURM job is still writing cannot be archived (the job would recreate
the directory and carry on writing into it), and a move never overwrites a run
of the same name on the other side. Every archive/restore shows exactly which
directories will move before it commits.

- **Experiments** (`/`) — a "+ New Experiment" button opens a sliding
  drawer with a form (built from each experiment type's declared fields);
  submitting it calls `sbatch`. The main area shows a card per job you've
  launched from the dashboard, with live status (`sacct`) and progress
  read from that run's `checkpoints.jsonl`.
- **Results · Metrics** (`/results/metrics`) — pick a results group
  (e.g. `run_experiment`), compare its `manifest.json` summary table
  across runs, and plot any checkpointed metric over steps.
- **Results · Responses** (`/results/responses`) — browse the qualitative
  generation samples (`samples/step_*.json`) for a given run/step.
- **Experiments → In context** (`/experiments/in-context`): the second
  kind of main experiment, in-context editing (SCR) against a knowledge base
  of distractors. A weight-edited model has to find a fact among everything
  it knows, while a knowledge base holding only that fact makes retrieval
  trivial, so each fact is asked once against its own fact plus
  `kb_size - 1` other facts (the same dataset first, then its training
  file, then other datasets; `scr.distractor_entries`). With one seed the
  bases are nested (100 inside 1,000 inside 10,000). Experiment type
  `in_context` (`../experiments/in_context/dashboard.json`, `"queue":
  false`) runs `run_experiment.py --method scr --kb_size N` on test
  records; results go to `results/main/in_context/` and the page tables
  each criterion by knowledge-base size (`GET /api/in-context`). Launches
  are recorded under `in_context`, which has its own progress section.
- **Experiments → Investigations** (`/experiments/investigations`; the old
  `/hyperparameters` addresses redirect): experiments that set up the main
  experiments' configuration, in three groups. **Mechanistic**: measure the
  model itself, per model, no method involved (Knowledge localisation, on
  its own page below; Neuron attribution and Circuit tracing, on
  theirs). **Input and context**: whether what the model is given
  changes a result, both how the prompt is written (format conditions of
  causal tracing) and what context is added to it (retrieval and
  demonstrations, a per-method sweep that works like those below).
  **Hyperparameter
  sweeps**: one per method family (defined in
  `../experiments/run_experiment/investigations.json`): **Finetuning** (FT,
  LoRA), **Locate-and-Edit** (ROME, MEMIT, PMET, AlphaEdit), **Dynamic
  Locate-and-Edit** (WilKE, FiDAL) and **Neuron editors** (FiNE, Knowledge
  Neurons, NMKE). Each lists every tunable setting of its methods, under
  their own setting names (a setting two methods share appears under each),
  with the current value, the authors' stability tag and five suggested
  values spread around the current one. Family sweeps vary **one setting at
  a time** by default (`design: one_at_a_time`): each picked value is one
  run with only that setting changed, and one shared run at the current
  settings (named `..._current`) stands in for every setting's current
  value, shown once per setting in the results. "Every combination"
  (`grid`) is still available. They start as a quick check: two single
  edits, or two batches of ten. To tune FT-M and FT-L separately, hold
  `objective_optimization` fixed in each sweep; sweep it to compare them.
  CaKE, IKE and SCR are not in the family sweeps. The earlier sweeps by kind
  of setting (edit layers, value-vector optimisation, adapter placement and
  the others) were retired on 2026-10-07: their results are in
  `results/archive/investigations-by-setting-2026-10-07/`, outside the
  dashboard. An investigation marked `legacy: true` would be listed under
  "Earlier sweeps", readable but not launched; none is now. **SCR** has its own investigation,
  now under Input and context:
  its retriever (`retrieval_k`, the embedding model, a similarity floor,
  facts found by sentence or subject, latest edit wins), its confirmation
  (on or off, the Yes margin, worked examples, a cap on confirmed facts) and
  its answer prompt (fact order, an instruction, and the framing when no
  fact is confirmed). The defaults in `hparams/SCR/*.yaml` are the original
  behaviour. Its page starts with every runnable dataset that has dev
  records, less subsets that repeat another's records (`datasets: all` and
  `datasets_except` in investigations.json; `"data_paths": ["default"]` in a
  sweep spec). IKE's `k` is now the "IKE demonstrations" investigation.
  A sweep picks methods, values, models and datasets and launches through
  the normal job path, but on **dev records only** (`--split dev`), with
  evaluation only before editing and at the end (`--final_only`), and the
  values passed as `--hparam` overrides. The page estimates runs, GPU-hours
  and missing covariance statistics before launch. A sweep with layer
  settings shows each model's traced peak beside the layers every method
  edits today, and adds
  the peak to the suggested layers; an untraced model gets suggestions
  around its default only. A "Held constant" block
  lists everything the sweep does not vary: the run-level settings (dev
  split, protocol, records, seed, evaluation) and every other setting of
  each chosen method per model, at the value runs really get (the
  hparams file, an Experiments-page default such as IKE's k, or a value
  tuned by an earlier sweep), with the investigation that tunes it and
  the best value that investigation has found. Any of them can be changed
  for one sweep (sent as extra --hparam overrides, recorded as `fixed` in
  sweep.json, not part of run names). Each sweep in an investigation's
  list shows, before it starts, why SLURM is holding it (in words: waiting
  for a free GPU, your job slots are all in use, ...) and SLURM's start
  estimate; once running, a bar and which run it is on with that run's
  fact or step count, from the files it already writes. Clicking a sweep
  opens its full request and every run's state, scores, time and error.
  A finished sweep can be hidden, which clears it from the sweep list
  (a `hidden` flag in its `sweep.json`; nothing moves) while its runs stay
  on Results · Investigations. "Show N hidden" lists them again, with
  Unhide. Removing a sweep from every page is API-only
  (`DELETE /api/hparams/sweeps/<investigation>/<id>`), which moves its
  folder to `<investigation>/deleted/` rather than erasing it. Backend:
  `backend/hparam_sweeps.py`, results under
  `results/investigations/<investigation>/sweeps/<sweep>/`.
- **Results · Investigations** (`/results/investigations`): every sweep
  run of an investigation, filterable by method, model, dataset and sweep,
  scored on fluency (final over the unedited model's), reliability,
  locality and generalizability on a 0 to 1 scale, and ranked by default
  by reliability (the goal is reliability without losing fluency). Cells are
  coloured by editable thresholds (colour only, nothing is hidden). A chart
  plots the criteria across the swept value when one setting varies. "Use
  as main config" writes a run's values into that method's hparams file for
  that model and records it in `hparams/TUNED.json`. A factor panel lists dataset, protocol, method, model,
  model type, model family and every swept setting; opening one shows all
  its values to include or leave out (with a select-all circle), and
  everything included is averaged together. One factor is the table's rows
  ("Rows"), or "Each run" for no averaging: one row per included value,
  mean ± standard deviation over the included values of every other
  factor, with the run count and the variance on hover. Only finished runs
  are averaged. The chart's x-axis is
  the rows factor: a line across a setting's values, grouped bars across
  the rest. Every tuning stage is its own model value (so runs never
  overwrite each other) and is labelled with its stage, here and in Main
  results; Main results can also use Protocol as a row or column. The **Failures** view
  (`/results/investigations?view=failures`) lists, across every
  investigation, runs failing now (ended without finishing, or finished
  with an error flag such as a NaN loss) with their error line and log,
  and runs fixed by "Rerun failed" together with each earlier attempt's
  error. Results · Main and
  Results · Investigations are separate pages that load only their own data.
- **Downloads** (`/downloads`): choose which datasets, models and setup
  components to fetch; see "Running it off gaivi" above.
- **Datasets** (`/datasets`) — browse the benchmarks under `../datasets/`
  (DUnE, KnowEdit, and anything added later) and preview records from
  their json/jsonl files.
- **Knowledge localisation** (`/experiments/investigations/causal_tracing`): causal
  tracing, per model. It locates where each model recalls facts and records
  the peak in `results/investigations/causal_tracing/traced_layers.json`.
  No editing method is involved: one trace per model serves every method.
  Which layer each method should edit is the separate, per-method Edit
  layers investigation, which reads this mapping to suggest layers (it never
  changes an hparams file by itself). The dynamic methods below give the other half of
  that comparison: they record the layer they picked for each individual fact,
  so a traced peak can be checked against what an editor actually chose.
- **Results · Archive** — archived runs with when/why they were retired and
  a Restore button (their checkpoints stay readable in place, without
  restoring first), plus every *incomplete* run: live directories with no
  `summary.json`, which the manifest skips and so the other Results tabs can
  never show. Those are runs that died part-way; the tab flags any later
  `_rerun` of the same configuration that did finish, and archives them in
  one go.

## Dynamic locate-and-edit

`experiments/run_experiment/dynamic/` adds four methods whose edit site is
decided per fact instead of being fixed by `hparams.layers`:

| Method | Chooses | Source |
| --- | --- | --- |
| `wilke` | one layer per fact, the one needing the smallest relative weight change | ported from github.com/ChenhuiHu/WilKE |
| `fine` | the top-k FFN neurons anywhere in the unfrozen layers | ported from github.com/opanhw/FiNE |
| `nmke` | which neurons inside AlphaEdit's layers may move | ported from github.com/LiuJinzhe-Keepgoing/NMKE |
| `fidal` | the top-K layers by Fisher Information, then hands them to a base editor | reimplemented, no code released |

They register in the same `LOCATE_AND_EDIT` table as ROME and MEMIT and need
no special handling to run. Two things are worth knowing before launching one:

- **Per-fact choices are recorded.** Each run writes
  `runs/<run_name>/locations.jsonl` (one record per fact: the layer or neuron
  set, plus the method's own scores), and every checkpoint row carries a
  `chosen_layers` histogram.
- **Covariance statistics cost more.** WilKE evaluates every candidate layer
  with `mom2_adjustment` on, and FiDAL can select any layer in its candidate
  range, so both need cached statistics for layers the fixed-layer methods
  never touch. Only layers 3-8 (GPT-J) and 4-8 (Qwen3-4B) are cached today, at
  roughly 6-12 minutes and 0.4-1 GB per layer, so a first WilKE or FiDAL run
  pays for the rest.

`dynamic/capture.py` exists because the FiNE and NMKE reference code both read
their activations out of patched transformers modeling files (Llama-only, or
Llama and GPT-J only). It recovers the same tensors with forward hooks, which
is what lets these run on Qwen3, Olmo-3 and Mistral.

## Knowledge by prompt format

`experiments/format_knowledge/score_formats.py` (its own experiment type,
launched from Experiments → Investigations → Knowledge by prompt format;
one job per model) asks which prompt formats a model shows its knowledge
in. It samples the same 500 facts per dataset for every model (MQuAKE,
UniEdit, ZsRE, RealTimeQA, altered riddles; all records, relation-balanced)
and asks each in every format the dataset allows (`completion`,
`chat_complete`, `question`, `chat_question`, `chat_prefill`, `mcq`,
`chat_mcq`, `riddle`, `chat_riddle`; formats.py). Known means the same test
tracing uses: the top non-whitespace token starts an accepted answer with
at least 10% probability; the answer's own first-token probability is kept
too. Base models read the chat formats through their instruct sibling's
template (`INSTRUCT_SIBLING`), so base and instruct see identical prompts.
Results: `results/investigations/format_knowledge/runs/<model>/`, served by
`/api/format-knowledge`. The other investigations default to base models
(a project decision of 2026-10-03: settings found on a base model are
assumed to carry to its instruct sibling).

## Causal tracing

`experiments/causal_tracing/causal_trace.py` is a second experiment type,
registered the same way as `run_experiment` (its own `dashboard.json`), so it
reuses the whole sbatch/sacct/progress path. Two flags in that file keep the
two apart:

- `"queue": false` keeps it out of the Main experiments drawer - it is
  staged from its own page's drawer instead, one SLURM job per selected model,
  onto the same shared GPU queue cards.
- `"results_default": true` on *run_experiment* is what makes the Results and
  Archive pages still mean `run_experiment` when no type is named. Without it
  they would follow whichever experiment directory sorts first, and
  `causal_tracing` sorts ahead of `run_experiment`.

What it measures, per prompt: the probability of the answer the model already
recalls, then the same prompt with Gaussian noise on the subject token
embeddings (recall collapses), then that corrupted run again with one clean
activation patched back in. The probability a site restores is what that site
was contributing. Averaged over prompts, the peak of the MLP curve at the last
subject token is where the model recalls the fact, and the starting point for
the Edit layers sweeps (whether it is the best layer to edit is what those
sweeps test). Only facts the model actually gets right
are traced, since a fact it cannot recall has no recall to localize.

**Which facts a model knows** (`experiments/causal_tracing/knowledge.py`,
shared by fact selection and the three tracers). With
`--known_check generate` the model answers in up to `--answer_tokens`
greedy tokens and knows a fact when an accepted answer (the answer or an
alias, as whole words) appears in what it writes. What it writes first is
its lead-in ("The capital is" in "The capital is Paris"): tracing runs on
prompt + lead-in, so the traced token is the answer where the model gives
it, and it must still be the top choice there above `--min_prob`. Fact
selection stores each fact's lead-in per model and format in the fact set
(`lead_ins`), and the tracers reuse it. The judge, by default `--judge
local` (Qwen3-4B-Instruct-2507 loaded with transformers on the job's own
GPU, judging in batches), or `ollama` (a quantised model through Ollama
started inside the job; `scripts/setup.py --ollama`), `api`
(evaluation.local.json) or `none`, is asked only about answers that do not
contain an accepted answer, may accept an equivalent ("NYC"), and quotes where the
answer gives it; failed judge calls count as "no" and are reported in the
fact selection summary. `--compare_judge` asks a second judge the same
cases and records each one's time and their agreement there, without
using its verdicts. `--known_check first_token`, still the default until generate has been
checked on GPU runs, is the earlier test (the answer's first token must be
the very next token). Tracer run names end in
the check (`_generate`, plus `_judge-<name>` for a judge other than local), so a new trace
never overwrites an earlier first-token one.

Facts come from `--split` records: `nontest` (dev and demo of `splits/`)
by default, or `all`. The tracing studies use `all` (decided 2026-10-03):
tracing locates where facts are recalled and tests whether that is
early-to-mid; it does not choose a setting by score, and the non-test
records alone were too few (Olmo-3 shared only 43 MQuAKE facts). Fact
selection's `--max_candidates` samples a relation-balanced pool to score,
since MQuAKE alone has about 7,300 unique facts and UniEdit 100,000. `formats.py` loads
MQuAKE (single-fact rewrites: a cloze sentence and a question per fact,
over 37 Wikidata relations), UniEdit (real Wikidata facts in 25 domains),
RealTimeQA (four-choice news questions), AlteredRiddles (riddles with an
added clue; split by `scripts/make_riddle_split.py`, since the editing
runner cannot load them yet) and the KnowEdit files, and writes each fact
in a `--format`: `completion`, `question`, `chat_question`, `chat_prefill`,
`mcq`, `chat_mcq`, `riddle`, `chat_riddle` (chat_* through the model's chat
template). Each format says what gets the noise: the subject, the question
(multiple choice), or the clue the altered riddle added.

To compare models on equal terms, a fact selection job
(`experiments/fact_selection/`, its own experiment type so the page shows
its progress, one step per model scored) first scores every model in every
requested format, then writes one set per group (`--groups`, by default one
per family: base and instruct share facts) from the facts that group's
models all know, chat formats required only of `--instruct_models`, spread
evenly across relations or domains. Each trace then runs with `--fact_set`
on exactly that list ("Fact set" on the page, listed from disk). Sets live
in `results/investigations/causal_tracing/fact_sets/runs/<name>/sets/<group>.json`
(a single-group run also writes `fact_set.json`), with `known.json`
recording which model knew which fact in which format. A set below 50 facts
is flagged `below_min`, and the tracer refuses it unless `--allow_thin 1`.

Besides the peak, every trace now reports how reliably the model recalls
facts in early-to-mid MLP layers (`reliability` in its summary; the "All
traces" table): the share of facts whose own MLP curve peaks in the band
(first half of the layers by default, `--band`), the share of each fact's
effect inside the band against an even spread, the averaged peak across
resampled facts, and with `--sever 1` ROME's severing test (hidden-state
restoration with every later MLP, or attention, held at its corrupted
value: how much recovery is lost). Each comes with a 95% bootstrap interval
over facts and a verdict (strong / moderate / weak). `trace.json` keeps
every fact's own curves, so breakdowns by relation or domain need no rerun.
`--window 1` restores one layer at a time, to check that a plateau is not
the 10-layer window smearing it. Only plain-completion, window-10 traces
feed `traced_layers.json`; the rest are comparisons, shown on the "Prompt
format in tracing" page (`/experiments/investigations/tracing_formats`).

Output follows run_experiment's layout (`runs/<run>/checkpoints.jsonl`,
`summary.json`, `manifest.json`), plus `runs/<run>/trace.json` for the full
curves and the optional token heatmap, plus `traced_layers.json`: model ->
chosen layer, rebuilt from the run summaries so a re-trace replaces an entry
rather than accumulating.

## Neuron attribution and circuit tracing

Two more per-model experiment types beside causal tracing
(`experiments/neuron_tracing/neuron_trace.py`,
`experiments/circuit_tracing/circuit_trace.py`), registered and launched the
same way (`"queue": false`, own pages under Investigations,
`/experiments/investigations/neuron_tracing` and `.../circuit_tracing`).
Both reuse causal tracing's loaders, formats, fact sets and known-fact
filter, so the three are compared on the same facts, and both show the
model's traced peak next to their own. `experiments/causal_tracing/components.py`
maps what they hook per architecture: each head (a slice of the attention
output projection's input), each MLP neuron (the down projection's input),
and where attention and the MLP read and write the residual stream, for the
pre-norm (Llama, Qwen, Mistral), post-norm (Olmo 2/3) and parallel (GPT-J,
NeoX) layouts. CPU tests in each folder check the hooks on all three.

**Neuron attribution** scores every MLP neuron at the last prompt token by
integrated gradients on the answer probability (Dai et al.'s Knowledge
Neurons; `--ig_steps`, 20). A fact's neurons are those above `--threshold`
(0.2) of its largest attribution, at most `--max_neurons`. It then tests
them: the fact's neurons switched off, the same number of random neurons in
the same layers switched off, the neurons doubled, and the fact's neurons
switched off on another fact (another relation where possible). Summary:
where the neurons sit (share per layer, attribution mass, peak, share in the
early-to-mid band, share in the last quarter), how concentrated attribution
is (top-10 share), the suppression drop against the random control and the
spillover onto the other fact, with 95% intervals and a verdict (causal,
partial, not causal), neuron overlap within against across relations, and
the "hub" neurons selected for three or more facts. `neurons.json` keeps
every fact's selection and layer mass.

**Circuit tracing** uses causal tracing's corruption (noise on the subject,
`--noise_scale`, `--n_noise_samples`) and one forward/backward pass per
fact for attribution patching: each head and MLP scored as (clean minus
corrupted activation) times the gradient of log P(answer), split by
position (subject tokens, last token, other), and edge attribution between
blocks (embedding, attention L, MLP L, the unembedding) using each
receiver's own input gradient. `--verify_k` of each fact's top components
are really patched to check the estimate (median rank correlation in the
summary). Then components are ranked on the even-position facts and tested
on the odd ones: the top K restored into the corrupted run (sufficiency,
against K random components of the same mix) and held at their corrupted
values in the clean run (necessity), for each K in `--circuit_sizes`; once
over all components and once over heads alone, since a whole MLP outweighs
one head. Verdict: compact (80% recovered with at most 20), distributed, or
not found. `circuit.json` adds the layer x head grid by position, the full
edge matrix and every fact's top components.

## Launches, progress and agents

Every submission is a **launch**: a hyperparameter sweep, or the runs one
`POST /api/experiments` submitted together. `backend/launches.py` summarises
both the same way (runs, states, overall progress, what each running run is
doing, why waiting ones wait), and `components/InvestigationProgress.jsx`
shows that as a **Progress** section on every investigation page, with the
Investigations overview listing what is running now. Jobs record the
investigation they are for, their launch (`batch_id`), a label and note, and
who launched them (`launched_by`: user or agent).

`POST /api/experiments` takes fields as `params` or as an `args` string in
the runner's own syntax (a flag given twice is swept), rejects fields the
type does not have instead of dropping them, passes `extra_args` (flags with
no field) through and marks the run name with them, and with `dry_run`
returns each run's command and blockers without submitting. Agents use the
second token, `backend/.agent_token`, through `scripts/dash.py`; it cannot
promote, archive, download, use the queue slots, or cancel the user's
launches (`AGENT_BLOCKED` in `main.py`). The backend writes its address to
`backend/.backend_url` for the CLI. Job scripts export `KE_DASHBOARD_JOB=1`,
and `experiments/launch_guard.py` makes every runner refuse to write into
`results/` without it (or a job id the dashboard recorded) unless given
`--untracked`. The agent-facing guide is `AGENTS.md` in this folder.

### Clearing finished items

Lists that keep growing have a **Clear** button: the Failures view, each
investigation's sweep list ("Clear finished") and Progress section, the
causal tracing, fact selection, neuron and circuit job tables, and Trial
Runs. Clearing never deletes and never touches anything queued or running:
a job gets `cleared_at` in the `jobs` table (`db.list_jobs()` leaves those
out, so they are not polled either), a sweep gets `"hidden": true` in its
sweep.json (its results stay on Results · Investigations), and a cleared
failure is recorded per run in sweep.json (`cleared_failures`, with earlier
attempts moved to `cleared_earlier_jobs`); a run that fails again after a
rerun shows again. Logs and results stay where they were. To bring jobs
back: `UPDATE jobs SET cleared_at = NULL` in `dashboard.db`.

## Adding a new experiment type

The dashboard doesn't hardcode `run_experiment` — it discovers any
`experiments/<name>/dashboard.json` describing:

```json
{
  "name": "my_experiment",
  "label": "My Experiment",
  "script": "run_my_experiment.py",
  "venv": "/AAIL/msiddiqui146/knowledge-editing/venvs/some_venv/bin/python",
  "out_root": "/AAIL/msiddiqui146/knowledge-editing/results/my_experiment",
  "run_name_template": "lr{lr:.0e}",
  "resources": {"partition": "AAIL", "gres": "gpu:1", "cpus_per_task": 2, "mem": "32G"},
  "fields": [
    {"name": "lr", "type": "float", "default": 0.0001, "label": "Learning rate"}
  ]
}
```

`resources` omits `time` on purpose: the AAIL partition's own limit is
`infinite`, so no `#SBATCH --time` line is emitted and a run takes as long
as it needs, rather than being killed part-way with its `summary.json`
(and so its manifest entry) never written. Add `"time": "HH:MM:SS"` back to
a given experiment type's `resources` if you do want it capped. Note SLURM
caps you at **6 concurrently running jobs** (QOS `normal`, `MaxJobsPU=6`,
which includes the dashboard's own job). The dashboard additionally puts all
GPU experiments -- main runs, hyperparameter sweeps, causal tracing and
retries -- into four shared serial dependency lanes. Consequently it uses at
most **4 GPUs at once** across every dashboard launch, leaving one QOS job slot
available for an interactive GPU allocation while the dashboard itself uses
another. Larger sweeps remain submitted to SLURM but wait on `Dependency`.

Optional keys beyond the basics, all read by `slurm.py` / the drawer:

- `run_name_always` (experiment type): fields named in every run directory
  even when the submission didn't vary them. `run_experiment` lists
  `ds_size` and the protocol fields here, so a full-dataset run and a
  20-record run of the same method/model/dataset get different directories
  instead of the second overwriting the first.
- `run_name_prefix` (field): what to put before the value in that name, when
  the field's own name reads badly (`ds20`, not `ds_size20`).
- `max_from` (field): another field whose selected value caps this one's
  options. `reset_every` is capped by `ds_size`, and `edit_batch_size` by
  `reset_every`. Options above the cap are shown disabled with the reason,
  and a selection the cap invalidates is replaced by the cap itself. The
  runner clamps for real, so a hand-written CLI run can't get this wrong
  either.
- `queue: false` (experiment type): keep it out of the Main experiments drawer
  because it has its own page, whose drawer stages it onto the shared cards. `results_default: true`: this is the type the
  Results and Archive pages mean when no type is named.
- `progress_field` (experiment type): which submitted param says how long a
  run is, for the progress bar. A run that writes `total_steps` into its
  checkpoints overrides it, which is how edit-protocol and full-dataset runs
  get an accurate bar.

**Dataset size.** `--ds_size` takes a count or `full`. `full` loads every
record the dataset has, which differs per dataset (839 for wiki_counterfact,
1301 for ZsRE), so the drawer looks the number up and shows it next to the
size pills. Whatever is asked for, the recorded `ds_size` is the number of
requests actually loaded, with the request kept alongside as
`ds_size_requested`; a batch size wider than that is clamped to it, since
editing in one group of 1000 and one group of 839 are the same run when the
dataset holds 839.

`fields` becomes the drawer form and the `--flag value` args passed to
`script`. `run_name_template` is a Python format string applied to the
submitted params, used to locate that run's `checkpoints.jsonl` /
`samples/` under `out_root` for live progress — match whatever your
script actually names its output directory. See
`experiments/run_experiment/dashboard.json` for the working example.

### Editing protocol

Weight-editing methods take an **Edit mode**, which is two independent
choices presented as four options:

|                 | one fact per call | many facts per call |
| --------------- | ----------------- | ------------------- |
| **isolated**    | Single            | Batch               |
| **accumulated** | Sequential        | Sequential batch    |

The top row restores the original weights after every edit call, so each
score measures an edit against a clean model. The bottom row lets edits
pile up and resets only every *Reset interval* facts, so the scores show
how edits interfere as they accumulate.

That is why the two size controls appear conditionally. **Batch size**
(facts per joint edit call) shows for Batch and Sequential batch only, and
**Reset interval** for Sequential and Sequential batch only, since the
other two reset after every call by definition. ROME is excluded from both
joint modes because it hard-codes `request[0]`; the flag driving that is
`no_joint_batch` in `dashboard.json`, enforced in `slurm.py::_combo_supported`
and mirrored in `frontend/src/lib/comboCount.js`.

A protocol run checkpoints once per reset group, so **Checkpoint every**
does not apply to it. That control is for the step-sweep runs: SCR, IKE and
the dynamic locate-and-edit methods. Its options and those of Fluency /
Sample every are powers of ten, which keeps the runner's "must be a
multiple of Checkpoint every" rule satisfiable from the dropdowns alone.

## Benchmarks / datasets

All benchmark data lives under `../datasets/`. Fourteen published
benchmarks are registered plus Sid's own: the backend discovers files
there, and the Datasets page registers supported subsets and record
renderers in `frontend/src/lib/datasetCatalog.js`. UniEdit includes all 25
domains in both train and test splits, with paged edit, generality, and
locality views and expandable source JSON.

Three "?" panels sit on that page. Each benchmark pill has one for its
paper and citations (`publishedBenchmarks.js`), Sid's Dataset has one for
its categorization axes (`sidsDatasetTaxonomy.js`), and the Published
Datasets heading has one comparing query form, multiple choice and
ground-truth answer length across all fourteen
(`datasetQueryFormats.js`). The lengths in that last one were measured off
the dataset files rather than taken from papers, and each row names the
file it was sampled from, so re-measuring after a dataset changes means
re-reading that field and recounting.

## Status

MVP scaffold — one experiment type wired up (`run_experiment`), basic
polling instead of websockets, a shared-secret token rather than real
auth (see "Reaching it from your laptop" above). Iterate from here once
you've seen it running.
