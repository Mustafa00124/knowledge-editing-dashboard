"""Thin wrapper around sbatch/sacct/scancel. Builds one plain (non-array)
sbatch script per combo from an experiment type's dashboard.json, mirroring
the structure of the hand-written experiments/*/submit.sbatch files already
in this project. submit_sweep() submits one job per combination in a
Cartesian-product sweep (plain independent sbatch calls, not a SLURM job
array - see dashboard/README.md for why).

Without SLURM (environment.scheduler() == "local") the same script runs as
a background process instead, via local_jobs.py; its #SBATCH lines are
just comments to bash. Status and cancel calls route on the job id, so a
database holding both kinds keeps working.
"""
import itertools
import re
import shlex
import shutil
import subprocess
import threading
import time
from contextlib import contextmanager, nullcontext
from datetime import datetime, timezone
from pathlib import Path

import config
import db
import environment
import local_jobs
import registry

try:
    import fcntl
except ImportError:  # Windows local mode does not submit SLURM jobs.
    fcntl = None


_gpu_submit_lock = threading.Lock()


@contextmanager
def _locked_gpu_lane():
    """Serialize lane selection across threads and dashboard processes."""
    with _gpu_submit_lock:
        config.GPU_LANE_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
        with config.GPU_LANE_LOCK_PATH.open("a+") as lock_file:
            if fcntl is not None:
                fcntl.flock(lock_file, fcntl.LOCK_EX)
            try:
                yield
            finally:
                if fcntl is not None:
                    fcntl.flock(lock_file, fcntl.LOCK_UN)


def _gpu_request_count(resources):
    count = 0
    for item in str(resources.get("gres", "gpu:1")).split(","):
        parts = item.strip().lower().split(":")
        if parts and parts[0] == "gpu":
            count += int(parts[-1]) if parts[-1].isdigit() else 1
    return count


def _uses_gpu(resources):
    return _gpu_request_count(resources) > 0


def _live_lane_tail(job_id, updated_at):
    """Return a dependency only while its job can still constrain the lane.

    A freshly submitted tail is kept without querying SLURM; accounting may
    not know about it yet.  For an older tail, squeue is authoritative: an
    absent job has finished and may also have aged out far enough that sbatch
    would reject its id as a dependency.
    """
    if not job_id:
        return None
    try:
        stamp = datetime.fromisoformat((updated_at or "").replace("Z", "+00:00"))
    except ValueError:
        stamp = None
    if stamp is not None and (datetime.now(timezone.utc) - stamp).total_seconds() < 300:
        return job_id
    proc = subprocess.run(
        ["squeue", "-h", "-j", str(job_id), "-o", "%A"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        # A job old enough to have left slurmctld's memory is refused by id
        # rather than listed as absent; it has finished all the same.
        if "Invalid job id" in proc.stderr:
            return None
        raise RuntimeError(f"could not verify GPU-lane tail {job_id}: {proc.stderr.strip()}")
    return job_id if proc.stdout.strip() else None


def _cast(value, ftype):
    if ftype == "int":
        return int(value)
    if ftype == "float":
        return float(value)
    return value


def _prepare_params(exp_cfg, raw_params):
    fields = {f["name"]: f for f in exp_cfg["fields"]}
    params = {}
    for name, field in fields.items():
        raw = raw_params.get(name)
        value = raw if raw not in (None, "") else field["default"]
        params[name] = _cast(value, field["type"])
    if "evaluation_modes" in params:
        try:
            params["evaluation_modes"] = ",".join(registry.validate_modes(params["evaluation_modes"]))
        except ValueError as exc:
            raise RuntimeError(str(exc)) from exc
    return params


def _field_relevant(field, params):
    """False for a field hidden by a conditional show_when whose condition
    isn't met by these params (e.g. lr/num_steps when method != ft) - such
    a field's value is just sitting at its default, not something this
    combo actually used, so it shouldn't appear in the run name."""
    show_when = field.get("show_when")
    if not show_when:
        return True
    return all(params.get(dep) in allowed for dep, allowed in show_when.items())


def _slug(value):
    """A run name becomes a directory and a filename, so keep it to
    characters that are safe in both. Matters most for the dataset field,
    whose value is an absolute path: sweeping it would otherwise bury the
    run directory several levels deep (and UniEdit's subsets have spaces)."""
    return re.sub(r"[^A-Za-z0-9._-]+", "-", str(value)).strip("-") or "x"


def _format_run_name(exp_cfg, params, swept_fields):
    """method, model, and lr are always included when relevant
    (self-describing on disk regardless of what a given sweep varies),
    plus whichever other fields actually varied in this submission - so a
    plain single-lr FT run on Qwen names as ft_qwen3-4b_lr1e-04, and a
    richer sweep gets a name that won't collide.
    """
    fields = {f["name"]: f for f in exp_cfg["fields"]}
    # An experiment type can override which fields are always named, for
    # when its identity hangs on something else: causal tracing has no
    # method or lr, and the same model traced against two datasets is two
    # runs, not one overwriting the other.
    default_always = ("method", "model", "lr", "edit_mode", "reset_every", "edit_batch_size")
    always = [name for name in exp_cfg.get("run_name_always", default_always) if name in fields]
    ordered = list(dict.fromkeys(always + list(swept_fields)))
    parts = []
    for name in ordered:
        if name not in params or name not in fields or not _field_relevant(fields[name], params):
            continue
        field = fields[name]
        # Fields that only distinguish a run when changed (a non-default
        # window, a fact set) name it only then, keeping the common name short.
        if field.get("run_name_skip_default") and str(params[name]) in (str(field.get("default", "")), ""):
            continue
        # Fields named only for some values: the known-fact check marks
        # "generate" runs, so first-token runs keep the names they always had.
        if field.get("run_name_values") and str(params[name]) not in field["run_name_values"]:
            continue
        # The dataset is named by the fact set instead when the run has one.
        if field.get("run_name_unless") and params.get(field["run_name_unless"]):
            continue
        if field.get("run_name_path_part"):
            # A file path names the run by what it identifies:
            # .../fact_sets/runs/mquake_formats/sets/olmo-3-7b.json -> "mquake_formats-olmo-3-7b".
            path = Path(str(params[name]))
            label = path.parent.name if path.stem == "fact_set" else f"{path.parent.parent.name}-{path.stem}"
            parts.append(_slug(label))
            continue
        # The dataset field's raw value is a full path - name it by the
        # subset label the picker already knows it by instead, so a
        # dataset sweep reads as ..._wiki_recent, not as a nested path.
        if field.get("control") == "dataset":
            _, subset = _dataset_meta(exp_cfg, params)
            parts.append(_slug(subset or Path(str(params[name])).stem))
            continue
        fmt = field.get("run_name_format", "")
        try:
            formatted = format(params[name], fmt) if fmt else str(params[name])
        except (TypeError, ValueError):
            formatted = str(params[name])
        # method/model values already read as identifiers on their own
        # ("ft", "qwen3-4b") - prefixing the field name would just be
        # noise ("methodft"); numeric fields need it for context ("lr1e-04").
        bare = field.get("run_name_bare", False)
        prefix = field.get("run_name_prefix", name)
        parts.append(_slug(formatted if bare else f"{prefix}{formatted}"))
    if params.get("evaluation_modes", "original") != "original":
        parts.append("eval-" + _slug(params["evaluation_modes"]))
    return "_".join(parts) if parts else "run"


def _dataset_meta(exp_cfg, params):
    """Reverse-look-up the human benchmark/subset labels for the selected
    data_path against dashboard.json's own dataset picker (benchmarks ->
    subsets) - the labels are already known here, from the exact same
    schema that rendered the picker, so run_experiment.py never has to
    guess dataset identity back out of a filesystem path."""
    field = next((f for f in exp_cfg["fields"] if f.get("control") == "dataset"), None)
    if not field:
        return None, None
    data_path = params.get(field["name"])
    for bench in field.get("benchmarks", []):
        for subset in bench.get("subsets", []):
            if subset.get("value") == data_path:
                return bench["label"], subset["label"]
    return None, None


def command_args(exp_cfg, params, run_name, out_root=None, extra_args=None):
    """The runner's command-line arguments for one run, each value quoted.
    extra_args: already-quoted arguments appended as given (hyperparameter
    sweeps pass --split dev, --final_only and --hparam; agents may pass
    flags the experiment type has no field for)."""
    fields = {f["name"]: f for f in exp_cfg["fields"]}
    # Registry-only fields (model/method, for now) describe the run but
    # aren't real script flags yet - don't pass them through to argparse.
    # --run_name is always passed explicitly so the script's output
    # directory matches what the dashboard computed and will poll. Every
    # value is shlex-quoted - several UniEdit subset filenames contain
    # spaces ("civil engineering.json"), which would otherwise silently
    # split into two argv tokens on an unquoted command line.
    args = [f"--{k} {shlex.quote(str(v))}" for k, v in params.items()
            if fields[k].get("cli", True) and _field_relevant(fields[k], params)]
    args.append(f"--run_name {shlex.quote(run_name)}")
    if out_root is not None:
        args.append(f"--out_root {shlex.quote(str(out_root))}")
    benchmark, subset = _dataset_meta(exp_cfg, params)
    if benchmark:
        args.append(f"--dataset_benchmark {shlex.quote(benchmark)} --dataset_subset {shlex.quote(subset)}")
    args.extend(extra_args or [])
    return args


def _submit_one(exp_cfg, params, run_name, out_root=None, extra_args=None, after_ok=()):
    """extra_args: see command_args()."""
    if "evaluation_modes" in params:
        try:
            registry.validate_modes(params["evaluation_modes"])
        except ValueError as exc:
            raise RuntimeError(str(exc)) from exc
    blockers = environment.launch_blockers(exp_cfg, params)
    if blockers:
        raise RuntimeError("cannot launch here: " + " ".join(blockers))
    exp_dir = Path(exp_cfg["_dir"])
    logs_dir = exp_dir / "logs"
    logs_dir.mkdir(exist_ok=True)

    res = exp_cfg.get("resources", {})
    gpu_count = _gpu_request_count(res)
    if gpu_count > 1:
        raise RuntimeError(
            "dashboard experiments may request only one GPU per job; "
            "the shared launch cap is four GPUs"
        )
    job_name = exp_cfg["name"]
    args_str = " ".join(command_args(exp_cfg, params, run_name, out_root, extra_args))

    # No --time unless an experiment type explicitly asks for one. The AAIL
    # partition's own limit is "infinite", so omitting the line lets a run
    # take as long as it needs rather than being killed mid-sweep with its
    # summary.json (and therefore its manifest entry) never written. The
    # tradeoff is that a hung job holds one of the 6 concurrent-job slots
    # until someone notices - that's what the queue card's Cancel is for.
    time_line = f"\n#SBATCH --time={res['time']}" if res.get("time") else ""

    def make_sbatch_text(dependency_job_id=None):
        # A comma joins conditions that must all hold: the GPU lane's tail
        # has ended (any state), and every after_ok job succeeded.
        conditions = ([f"afterany:{dependency_job_id}"] if dependency_job_id else []) + \
            [f"afterok:{job}" for job in after_ok]
        dependency_line = (
            f"\n#SBATCH --dependency={','.join(conditions)}"
            if conditions else ""
        )
        return f"""#!/bin/bash
#SBATCH --job-name={job_name}
#SBATCH --partition={res.get('partition', 'AAIL')}
#SBATCH --output={logs_dir}/%x_%j.out
#SBATCH --error={logs_dir}/%x_%j.err
#SBATCH --gres={res.get('gres', 'gpu:1')}
#SBATCH --cpus-per-task={res.get('cpus_per_task', 2)}
#SBATCH --mem={res.get('mem', '32G')}{time_line}{dependency_line}

set -euo pipefail
# Tells the runner the dashboard launched it (experiments/launch_guard.py).
export KE_DASHBOARD_JOB=1
cd "{exp_dir}"
"{environment.runner_python(exp_cfg)}" "{exp_cfg['script']}" {args_str}
"""

    config.SUBMITTED_SBATCH_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S_%f")
    sbatch_path = config.SUBMITTED_SBATCH_DIR / f"{job_name}_{run_name}_{ts}.sbatch"

    if environment.scheduler() == "local":
        sbatch_path.write_text(make_sbatch_text())
        job_id = local_jobs.new_job_id()
        local_jobs.submit(job_id, sbatch_path, logs_dir / f"{job_name}_{job_id}.out",
                          logs_dir / f"{job_name}_{job_id}.err")
    else:
        # A persistent four-lane dependency chain is the actual GPU cap.
        # This is global across all dashboard launch surfaces, unlike a
        # per-sweep job-array %4 limit, which would allow two sweeps to use
        # eight GPUs together.
        lane = None
        with _locked_gpu_lane() if _uses_gpu(res) else nullcontext():
            dependency_job_id = None
            if _uses_gpu(res):
                lane, dependency_job_id, updated_at = db.next_gpu_lane()
                dependency_job_id = _live_lane_tail(dependency_job_id, updated_at)
            sbatch_path.write_text(make_sbatch_text(dependency_job_id))
            proc = subprocess.run(["sbatch", str(sbatch_path)], capture_output=True, text=True)
            if proc.returncode != 0:
                raise RuntimeError(f"sbatch failed: {proc.stderr.strip() or proc.stdout.strip()}")

            m = re.search(r"Submitted batch job (\d+)", proc.stdout)
            if not m:
                raise RuntimeError(f"couldn't parse job id from sbatch output: {proc.stdout!r}")
            job_id = m.group(1)
            if lane is not None:
                db.set_gpu_lane_tail(lane, job_id)

    return {
        "job_id": job_id,
        "run_name": run_name,
        "params": params,
        "sbatch_path": str(sbatch_path),
        "out_path": str(logs_dir / f"{job_name}_{job_id}.out"),
        "err_path": str(logs_dir / f"{job_name}_{job_id}.err"),
    }


def _combo_supported(exp_cfg, params):
    """
    Whether a method/dataset pairing can actually run, so a sweep does not
    queue jobs the runner will reject on sight.

    Right now the only such rule is the subject requirement: the
    locate-and-edit methods have to be told which span of the prompt to edit,
    and RealTimeQA's questions are natural sentences with no labeled subject.
    run_experiment.py already refuses these (fast, before the model load), but
    an 8-method x 12-dataset sweep still burns a queue slot per rejection.

    Driven by flags in dashboard.json rather than hardcoded lists here:
    `requires_subject` and `no_joint_batch` on a method, `provides_subject`
    on a dataset subset. no_joint_batch covers ROME, which hard-codes
    request[0], and the dynamic methods that pick an edit site per fact and
    so have nothing to solve jointly. It rules out both joint edit modes,
    batch and sequential_batch, since the objection is to the joint apply
    call, not to whether edits accumulate afterwards.
    """
    method, data_path = params.get("method"), params.get("data_path")
    if not method or not data_path:
        return True

    fields = {f["name"]: f for f in exp_cfg["fields"]}
    methods = {
        m["value"]: m
        for cat in fields.get("method", {}).get("categories", [])
        for m in cat["methods"]
    }
    edit_mode = params.get("edit_mode")
    if edit_mode in ("batch", "sequential_batch") and methods.get(method, {}).get("no_joint_batch"):
        return False
    # Only sequential_batch has both a batch size and a reset interval, so
    # only there can one exceed the other. Plain batch resets after every
    # call and never reads reset_every (edit_protocol.py::edit_groups).
    if edit_mode == "sequential_batch" and int(params.get("edit_batch_size", 1)) > int(params.get("reset_every", 1)):
        return False

    spec = methods.get(method, {})
    # CaKE's training data exists only for some files; `only_subsets` names them.
    only = spec.get("only_subsets")
    if only and Path(str(data_path)).name not in only:
        return False

    subset = next((s for benchmark in fields.get("data_path", {}).get("benchmarks", [])
                   for s in benchmark.get("subsets", []) if s.get("value") == data_path), None)
    if subset is None:
        return True
    if spec.get("requires_subject") and subset.get("provides_subject", True) is False:
        return False
    # Knowledge Neurons attributes neurons to the original answer.
    if spec.get("requires_ground_truth") and subset.get("provides_ground_truth", True) is False:
        return False
    return True


def extra_args_suffix(extra_args):
    """A short, stable tag for runs given flags beyond the form fields, so
    they never share a run directory with an otherwise identical run."""
    if not extra_args:
        return ""
    import hashlib
    return "_x" + hashlib.sha1(" ".join(extra_args).encode()).hexdigest()[:6]


def plan_sweep(exp_cfg, raw_param_lists, extra_args=None):
    """raw_param_lists: {field_name: [values...]} - every field arrives as
    a list, even ones with a single value. Returns (runs, skipped): one
    {"params", "run_name"} per combination of the Cartesian product that
    will actually run, and how many combinations were dropped as duplicates
    or unsupported pairings. Submits nothing."""
    fields = {f["name"]: f for f in exp_cfg["fields"]}
    field_names = list(fields.keys())

    swept_fields = [name for name in field_names if len(raw_param_lists.get(name) or []) > 1]

    value_lists = [raw_param_lists.get(name) or [None] for name in field_names]
    combos = list(itertools.product(*value_lists))

    runs = []
    skipped = 0
    seen = set()
    for combo in combos:
        raw_params = dict(zip(field_names, combo))
        params = _prepare_params(exp_cfg, raw_params)
        # Sweeping a field that others depend on (method) can make two
        # combos identical once the irrelevant ones drop out: method
        # [rome, ft] x lr [1e-3, 1e-4] is 4 points, but ROME ignores lr, so
        # both ROME legs are the same run - and _format_run_name gives them
        # the same name, which would mean two jobs writing one output
        # directory. Collapse them to the single run they actually describe.
        signature = tuple(
            sorted((k, str(v)) for k, v in params.items() if _field_relevant(fields[k], params))
        )
        if signature in seen:
            skipped += 1
            continue
        seen.add(signature)
        if not _combo_supported(exp_cfg, params):
            skipped += 1
            continue
        run_name = _format_run_name(exp_cfg, params, swept_fields) + extra_args_suffix(extra_args)
        runs.append({"params": params, "run_name": run_name})
    return runs, skipped


def submit_sweep(exp_cfg, raw_param_lists, out_root=None, after_ok=(), extra_args=None):
    """Submits one sbatch job per run plan_sweep() returns and returns a
    list of results (same shape as a single _submit_one() call each)."""
    runs, _ = plan_sweep(exp_cfg, raw_param_lists, extra_args)
    return [_submit_one(exp_cfg, run["params"], run["run_name"], out_root, extra_args=extra_args, after_ok=after_ok)
            for run in runs]


def submit_exact(exp_cfg, params, run_name, out_root=None):
    """Submit one previously resolved job without expanding a Cartesian sweep."""
    fields = {field["name"] for field in exp_cfg["fields"]}
    params = dict(params)
    if "evaluation_modes" in fields and "evaluation_modes" not in params:
        params["evaluation_modes"] = "original"  # pre-feature jobs remain retryable
    if set(params) != fields:
        raise RuntimeError("saved job parameters no longer match the registered experiment fields")
    return _submit_one(exp_cfg, params, run_name, out_root)


def _is_local(job_id):
    return str(job_id).startswith("local-")


def sacct_statuses(job_ids):
    """Read all requested allocations in one accounting query."""
    ids = list(dict.fromkeys(str(job_id) for job_id in job_ids))
    statuses = {job_id: {"state": "UNKNOWN", "elapsed": None, "exit_code": None} for job_id in ids}
    for job_id in ids:
        if _is_local(job_id):
            statuses[job_id] = local_jobs.status(job_id)
    ids = [job_id for job_id in ids if not _is_local(job_id)]
    if not ids or not shutil.which("sacct"):
        return statuses
    proc = subprocess.run(
        ["sacct", "-j", ",".join(ids), "--format=JobIDRaw,State%40,Elapsed,ExitCode", "--noheader", "--parsable2", "-X"],
        capture_output=True, text=True, timeout=15,
    )
    if proc.returncode:
        raise RuntimeError(proc.stderr.strip() or "Could not read SLURM job statuses")
    for line in proc.stdout.splitlines():
        parts = line.strip().split("|")
        if len(parts) < 4 or parts[0] not in statuses:
            continue
        statuses[parts[0]] = {
            "state": parts[1].split()[0] if parts[1].strip() else "UNKNOWN",
            "elapsed": parts[2],
            "exit_code": parts[3],
        }
    return statuses


def sacct_status(job_id):
    if _is_local(job_id):
        return local_jobs.status(job_id)
    if not shutil.which("sacct"):
        return {"state": "UNKNOWN", "elapsed": None, "exit_code": None}
    proc = subprocess.run(
        ["sacct", "-j", job_id, "--format=State,Elapsed,ExitCode", "--noheader", "--parsable2", "-X"],
        capture_output=True,
        text=True,
    )
    line = proc.stdout.strip().splitlines()[0] if proc.stdout.strip() else ""
    if not line:
        return {"state": "UNKNOWN", "elapsed": None, "exit_code": None}
    parts = line.split("|")
    # sacct reports a user-cancelled job as "CANCELLED by <uid>", not plain
    # "CANCELLED" - keep only the bare state word, or every consumer has to
    # special-case that one (slot status would never match FAIL_STATES, so a
    # cancelled card would sit at "In progress" forever and refuse to clear;
    # the frontend would build a badge class out of the uid too).
    return {
        "state": parts[0].split()[0] if parts and parts[0].strip() else "UNKNOWN",
        "elapsed": parts[1] if len(parts) > 1 else None,
        "exit_code": parts[2] if len(parts) > 2 else None,
    }


def cancel(job_id):
    if _is_local(job_id):
        local_jobs.cancel(job_id)
        return
    subprocess.run(["scancel", job_id], capture_output=True, text=True)


def cancel_many(job_ids):
    """One scancel call for the whole list - a sweep can put 20+ jobs on a
    single queue card, and scancel takes as many ids as you give it, so
    cancelling a card is one command rather than one subprocess per job.
    Returns stderr if scancel complained (e.g. a job that already ended),
    which the caller surfaces rather than failing the whole request over."""
    if not job_ids:
        return ""
    errors = [err for job_id in job_ids if _is_local(job_id) and (err := local_jobs.cancel(job_id))]
    remote = [job_id for job_id in job_ids if not _is_local(job_id)]
    if remote:
        proc = subprocess.run(["scancel", *remote], capture_output=True, text=True)
        errors.append(proc.stderr.strip())
    return "\n".join(e for e in errors if e)


def tail_file(path, n=200):
    p = Path(path) if path else None
    if not p or not p.exists():
        return ""
    lines = p.read_text(errors="replace").splitlines()
    return "\n".join(lines[-n:])
