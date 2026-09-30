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
import time
from pathlib import Path

import config
import environment
import local_jobs
import registry


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


def _submit_one(exp_cfg, params, run_name, out_root=None, extra_args=None):
    """extra_args: already-quoted command-line arguments appended as given
    (hyperparameter sweeps pass --split dev, --final_only and --hparam)."""
    if "evaluation_modes" in params:
        try:
            registry.validate_modes(params["evaluation_modes"])
        except ValueError as exc:
            raise RuntimeError(str(exc)) from exc
    blockers = environment.launch_blockers(exp_cfg, params)
    if blockers:
        raise RuntimeError("cannot launch here: " + " ".join(blockers))
    fields = {f["name"]: f for f in exp_cfg["fields"]}
    exp_dir = Path(exp_cfg["_dir"])
    logs_dir = exp_dir / "logs"
    logs_dir.mkdir(exist_ok=True)

    res = exp_cfg.get("resources", {})
    job_name = exp_cfg["name"]
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
    args_str = " ".join(args)

    # No --time unless an experiment type explicitly asks for one. The AAIL
    # partition's own limit is "infinite", so omitting the line lets a run
    # take as long as it needs rather than being killed mid-sweep with its
    # summary.json (and therefore its manifest entry) never written. The
    # tradeoff is that a hung job holds one of the 6 concurrent-job slots
    # until someone notices - that's what the queue card's Cancel is for.
    time_line = f"\n#SBATCH --time={res['time']}" if res.get("time") else ""

    sbatch_text = f"""#!/bin/bash
#SBATCH --job-name={job_name}
#SBATCH --partition={res.get('partition', 'AAIL')}
#SBATCH --output={logs_dir}/%x_%j.out
#SBATCH --error={logs_dir}/%x_%j.err
#SBATCH --gres={res.get('gres', 'gpu:1')}
#SBATCH --cpus-per-task={res.get('cpus_per_task', 2)}
#SBATCH --mem={res.get('mem', '32G')}{time_line}

set -euo pipefail
cd "{exp_dir}"
"{environment.runner_python(exp_cfg)}" "{exp_cfg['script']}" {args_str}
"""

    config.SUBMITTED_SBATCH_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S_%f")
    sbatch_path = config.SUBMITTED_SBATCH_DIR / f"{job_name}_{run_name}_{ts}.sbatch"
    sbatch_path.write_text(sbatch_text)

    if environment.scheduler() == "local":
        job_id = local_jobs.new_job_id()
        local_jobs.submit(job_id, sbatch_path, logs_dir / f"{job_name}_{job_id}.out",
                          logs_dir / f"{job_name}_{job_id}.err")
    else:
        proc = subprocess.run(["sbatch", str(sbatch_path)], capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"sbatch failed: {proc.stderr.strip() or proc.stdout.strip()}")

        m = re.search(r"Submitted batch job (\d+)", proc.stdout)
        if not m:
            raise RuntimeError(f"couldn't parse job id from sbatch output: {proc.stdout!r}")
        job_id = m.group(1)

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


def submit_sweep(exp_cfg, raw_param_lists, out_root=None):
    """raw_param_lists: {field_name: [values...]} - every field arrives as
    a list, even ones with a single value. Submits one sbatch job per
    combination in the Cartesian product and returns a list of results
    (same shape as a single _submit_one() call each).
    """
    fields = {f["name"]: f for f in exp_cfg["fields"]}
    field_names = list(fields.keys())

    swept_fields = [name for name in field_names if len(raw_param_lists.get(name) or []) > 1]

    value_lists = [raw_param_lists.get(name) or [None] for name in field_names]
    combos = list(itertools.product(*value_lists))

    results = []
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
            continue
        seen.add(signature)
        if not _combo_supported(exp_cfg, params):
            continue
        run_name = _format_run_name(exp_cfg, params, swept_fields)
        results.append(_submit_one(exp_cfg, params, run_name, out_root))
    return results


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
