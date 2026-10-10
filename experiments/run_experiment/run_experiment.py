"""
Unified experiment runner: any registered method (FT, ROME, SCR, ...) x
any registered model, driven by --method/--model plus shared args. Adding
a new method+model combo means dropping in one
hparams/<METHOD>/<model>.yaml file - nothing in this script needs to
change for that, except adding the model's weights path to MODEL_PATHS
below the first time a new model is introduced.

"step" means different things per method, deliberately unified into one
concept so all three share the same checkpoint/progress machinery (and
the dashboard's progress bar keeps working unchanged regardless of method):
  - FT:   a gradient step - one pass over the batch of `ds_size` requests,
          all `ds_size` of them trained on simultaneously every step.
          --lr/--num_steps tune this directly.
  - ROME: a closed-form edit, applied to one more fact at a time,
          sequentially - "step i" means i facts have now been edited into
          the model. There's no gradient search to tune, so --lr/
          --num_steps are simply ignored for --method rome; the step
          count is always ds_size (one edit per request loaded).
  - SCR:  never edits the model at all (see scr.py) - "step i" means i
          facts have been added to SCR's retrievable knowledge base so
          far. Same reasoning as ROME: --lr/--num_steps don't apply,
          step count is always ds_size. With --kb_size there is no
          growth: after the empty-knowledge-base baseline (step 0), every
          record is asked once against kb_size-1 distractor facts plus
          its own fact (the In-context experiment).
  - IKE:  never edits the model either (see ike.py) - the *test* requests
          being evaluated stay fixed throughout; "step i" instead means i
          demonstration sentences (built from a separate training split)
          have been added to IKE's retrievable demo pool so far.
  - WilKE/FiNE/NMKE/FiDAL: closed-form or short-gradient edits like
          ROME's, so "step i" again means i facts edited - the difference
          is only that each of those facts was written to a layer (or a
          set of neurons) chosen for it rather than named in hparams. See
          dynamic/__init__.py.

Either way, every checkpoint evaluates against the *same* fixed request
list (loaded once, size ds_size) - for ROME/SCR that means not-yet-edited
(or not-yet-retrievable) requests still show up (correctly) as such in
early checkpoints, so the metrics curve rises as more facts get edited/
added in, rather than only ever showing a cumulative average over a
partial subset. IKE grows a *different* pool (demonstrations, not the
test facts themselves), so its curve instead shows how much having more
demonstration material to draw on changes in-context editing quality.

--edit_mode replaces that step sweep with an editing protocol, for the
weight-editing methods. Two independent choices, spelled as four modes:

              one fact per call        many facts per call
  isolated    single                   batch
  accumulated sequential               sequential_batch

The top row restores the original weights after every call, so each score
measures an edit on a clean model; the bottom row lets edits pile up and
resets only every --reset_every facts, so the scores show what happens as
they interfere. --edit_batch_size sets the facts per joint call and is
read only by the two right-hand modes; --reset_every is read only by the
two bottom ones (single resets after each fact, batch after each batch).
A protocol run checkpoints once per group rather than every
--checkpoint_every steps, and its summary averages every group, weighted
by group size - see edit_protocol.py.

Output layout (same for every method):
    <out_root>/runs/<run_name>/hparams.yaml
    <out_root>/runs/<run_name>/checkpoints.jsonl   (one line per checkpoint, appended live)
    <out_root>/runs/<run_name>/summary.json        (written once, at the end)
    <out_root>/runs/<run_name>/samples/step_*.json (qualitative generations, every --sample_every steps)
    <out_root>/runs/<run_name>/locations.jsonl     (dynamic methods only: where each fact was edited)
    <out_root>/manifest.json                       (rebuilt from every runs/*/summary.json found so far)
"""
import argparse
import importlib
import json
import os
import sys
import time
from datetime import datetime

import torch
import yaml
from transformers import AutoModelForCausalLM, AutoTokenizer

EXP_DIR = os.path.dirname(os.path.abspath(__file__))
# Everything the runner touches lives under the checkout it was run from, so
# a clone anywhere works without edits. hparams files hold paths relative to
# this root; resolve_project_paths() anchors them after loading.
PROJECT_ROOT = os.path.dirname(os.path.dirname(EXP_DIR))
sys.path.append(os.path.join(PROJECT_ROOT, "experiments"))
import launch_guard  # noqa: E402  (refuses untracked runs into results/)
DEFAULT_EASYEDIT_PATH = os.path.join(PROJECT_ROOT, "external/EasyEdit")
DEFAULT_DATA_PATH = os.path.join(PROJECT_ROOT, "datasets/KnowEdit/benchmark/wiki_recent/recent_test.json")
DEFAULT_OUT_ROOT = os.path.join(PROJECT_ROOT, "results/main/run_experiment")

METHOD_HPARAMS_DIR = {
    "ft": "FT",
    "ft_l": "FT-L",
    "lora": "LoRA",
    "rome": "ROME",
    "memit": "MEMIT",
    "pmet": "PMET",
    "alphaedit": "AlphaEdit",
    "wilke": "WilKE",
    "fine": "FiNE",
    "nmke": "NMKE",
    "fidal": "FiDAL",
    "scr": "SCR",
    "ike": "IKE",
    "kn": "KN",
    "cake": "CaKE",
}

# Fine-tuning comes in two methods that share one trainer and differ only in
# the loss, so each is pinned to its objective: "ft" is FT-M (cross-entropy
# on every target token after the prompt, EasyEdit's recommended FT) and
# "ft_l" is FT-L (the ROME paper's constrained fine-tuning, scored at the
# last prompt position). An hparams file or --hparam override that disagrees
# is refused rather than quietly turning one into the other.
FT_OBJECTIVE = {"ft": "target_new", "ft_l": "prompt_last"}
FT_METHODS = tuple(FT_OBJECTIVE)

# The "locate-and-edit" family (ROME/MEMIT/PMET/AlphaEdit): all compute a
# closed-form weight update rather than training, so they share one
# dispatch path here - just with different HyperParams classes/apply
# functions, and two different calling conventions:
#   "single": apply_fn only ever edits exactly one fact per call (ROME
#             hard-codes this - it takes request[0] regardless of what's
#             passed) - one call per step.
#   "batch":  apply_fn accepts a list of facts and solves for all of them
#             jointly in one call (MEMIT/PMET/AlphaEdit's actual design) -
#             called once per checkpoint interval with however many new
#             facts have accumulated since the last checkpoint, which is
#             both more faithful to how these methods are meant to be used
#             and cheaper than calling them fact-by-fact.
LOCATE_AND_EDIT = {
    "rome": {
        "hparams_module": "easyeditor.models.rome.rome_hparams",
        "hparams_class": "ROMEHyperParams",
        "apply_module": "easyeditor.models.rome.rome_main",
        "apply_fn": "apply_rome_to_model",
        "mode": "single",
    },
    "memit": {
        "hparams_module": "easyeditor.models.memit.memit_hparams",
        "hparams_class": "MEMITHyperParams",
        "apply_module": "easyeditor.models.memit.memit_main",
        "apply_fn": "apply_memit_to_model",
        "mode": "batch",
    },
    "pmet": {
        "hparams_module": "easyeditor.models.pmet.pmet_hparams",
        "hparams_class": "PMETHyperParams",
        "apply_module": "easyeditor.models.pmet.pmet_main",
        "apply_fn": "apply_pmet_to_model",
        "mode": "batch",
    },
    "alphaedit": {
        "hparams_module": "easyeditor.models.alphaedit.AlphaEdit_hparams",
        "hparams_class": "AlphaEditHyperParams",
        "apply_module": "easyeditor.models.alphaedit.AlphaEdit_main",
        "apply_fn": "apply_AlphaEdit_to_model",
        "mode": "batch",
    },
    # The dynamic half of the family (see dynamic/__init__.py): same
    # dispatch, same (model, weights_copy) contract, but the layer or
    # neuron set is decided per fact instead of being read from
    # hparams.layers. They live under dynamic/ rather than in
    # external/EasyEdit because EasyEdit ships none of them, and because
    # two of the four otherwise require patching transformers itself.
    # Neuron level: integrated-gradient attribution, then rewriting those
    # neurons' value vectors. See knowledge_neurons.py.
    "kn": {
        "hparams_module": "easyeditor.models.kn.kn_hparams",
        "hparams_class": "KNHyperParams",
        "apply_module": "knowledge_neurons",
        "apply_fn": "apply_knowledge_neurons_to_model",
        "mode": "single",
    },
    # Circuit level: a LoRA adapter on every projection, trained on CaKE's
    # circuit-guided examples (MQuAKE only). See cake.py.
    "cake": {
        "hparams_module": "cake",
        "hparams_class": "CaKEHyperParams",
        "apply_module": "cake",
        "apply_fn": "apply_cake_to_model",
        "mode": "single",
    },
    "wilke": {
        "hparams_module": "dynamic.wilke",
        "hparams_class": "WilKEHyperParams",
        "apply_module": "dynamic.wilke",
        "apply_fn": "apply_wilke_to_model",
        # Like ROME, one fact per call: the layer scan is per fact, so
        # there is nothing to solve jointly.
        "mode": "single",
        "dynamic": True,
    },
    "fine": {
        "hparams_module": "dynamic.fine",
        "hparams_class": "FiNEHyperParams",
        "apply_module": "dynamic.fine",
        "apply_fn": "apply_fine_to_model",
        "mode": "single",
        "dynamic": True,
    },
    "nmke": {
        "hparams_module": "dynamic.nmke",
        "hparams_class": "NMKEHyperParams",
        "apply_module": "dynamic.nmke",
        "apply_fn": "apply_nmke_to_model",
        # AlphaEdit underneath, so the closed-form solve is genuinely
        # batched; the neuron mask is recomputed for each batch.
        "mode": "batch",
        "dynamic": True,
    },
    "fidal": {
        "hparams_module": "dynamic.fidal",
        "hparams_class": "FiDALHyperParams",
        "apply_module": "dynamic.fidal",
        "apply_fn": "apply_fidal_to_model",
        # Single despite its base editor usually being batch: the paper
        # localises per knowledge instance, and probing once for a whole
        # batch would average that decision away.
        "mode": "single",
        "dynamic": True,
    },
}

# Methods whose edit site is an outcome of the run rather than a setting,
# so it has to be recorded per fact. See dynamic/locations.py.
DYNAMIC_METHODS = {name for name, spec in LOCATE_AND_EDIT.items() if spec.get("dynamic")}

# Where each registered model's weights live on disk. Add a new model by
# adding one line here, plus one hparams/<METHOD>/<key>.yaml per method it
# supports.
MODEL_PATHS = {
    # Qwen3-4B, all four tuning stages off one pretrain. Architecturally
    # identical (36 layers, hidden 2560), so the hparams are exact copies -
    # only the weights, and therefore the cached mom2 stats, differ.
    "qwen3-4b-base": os.path.join(PROJECT_ROOT, "models/Qwen3-4B-Base"),
    "qwen3-4b": os.path.join(PROJECT_ROOT, "models/Qwen3-4B"),
    "qwen3-4b-instruct-2507": os.path.join(PROJECT_ROOT, "models/Qwen3-4B-Instruct-2507"),
    "qwen3-4b-thinking-2507": os.path.join(PROJECT_ROOT, "models/Qwen3-4B-Thinking-2507"),
    # Olmo 3, likewise. Module naming matches Mistral's exactly
    # (model.layers.{}.mlp.down_proj / model.norm / lm_head) at the same
    # depth, so its hparams are inherited from Mistral rather than traced.
    "olmo-3-7b-base": os.path.join(PROJECT_ROOT, "models/Olmo-3-7B-Base"),
    "olmo-3-7b-instruct": os.path.join(PROJECT_ROOT, "models/Olmo-3-7B-Instruct"),
    "olmo-3-7b-think": os.path.join(PROJECT_ROOT, "models/Olmo-3-7B-Think"),
    # Llama 3.1 8B: base, instruct, and DeepSeek's R1 reasoning distill onto
    # the same base. All three are Mistral-7B-shaped (32 layers, hidden 4096,
    # Llama module naming), so their hparams are inherited, layers untraced.
    "llama-3.1-8b": os.path.join(PROJECT_ROOT, "models/Llama-3.1-8B"),
    "llama-3.1-8b-instruct": os.path.join(PROJECT_ROOT, "models/Llama-3.1-8B-Instruct"),
    "deepseek-r1-distill-llama-8b": os.path.join(PROJECT_ROOT, "models/DeepSeek-R1-Distill-Llama-8B"),
    "mistral-7b-v0.1": os.path.join(PROJECT_ROOT, "models/Mistral-7B-v0.1"),
    "mistral-7b-instruct-v0.1": os.path.join(PROJECT_ROOT, "models/Mistral-7B-Instruct-v0.1"),
    "gpt-j-6b": os.path.join(PROJECT_ROOT, "models/GPT-J-6B"),
}


def _ds_size(value):
    """--ds_size 20 -> 20, --ds_size full -> None (no limit, load everything).

    None rather than a sentinel number because that is what the loaders take:
    data[:None] is the whole file, while data[:-1] would quietly drop the last
    record.
    """
    if str(value).strip().lower() in ("full", "all"):
        return None
    try:
        size = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"expected a positive count or 'full', got {value!r}")
    if size < 1:
        raise argparse.ArgumentTypeError(f"--ds_size must be at least 1 (or 'full'), got {size}")
    return size


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--method", required=True, choices=sorted(METHOD_HPARAMS_DIR))
    p.add_argument("--model", required=True, choices=sorted(MODEL_PATHS))
    p.add_argument("--data_path", default=DEFAULT_DATA_PATH)
    p.add_argument(
        "--dataset_benchmark",
        default=None,
        help="Human label for which benchmark data_path belongs to (e.g. 'UniEdit'), for the results "
        "manifest/dashboard to group by. The dashboard always passes this (looked up from its own "
        "dashboard.json dataset picker); falls back to a guess from data_path for manual runs.",
    )
    p.add_argument(
        "--dataset_subset",
        default=None,
        help="Human label for which subset within --dataset_benchmark (e.g. 'agronomy'). Same "
        "dashboard-always-passes-it, guessed-for-manual-runs convention as --dataset_benchmark.",
    )
    p.add_argument(
        "--ds_size",
        type=_ds_size,
        default=20,
        help="How many edit requests to load: a positive count, or 'full' for every record the "
        "dataset has. The effective number is whatever the loader actually returns, which is "
        "what gets recorded and what the reset interval is capped to.",
    )
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--split", choices=("test", "dev", "all"), default="test",
                   help="which records to edit (splits/, made by scripts/make_splits.py): test for "
                        "reported experiments, dev for hyperparameter sweeps, all only for debugging")
    p.add_argument("--hparam", action="append", default=[], metavar="KEY=VALUE",
                   help="override one hparams-file setting (repeatable; VALUE is YAML, e.g. layers=[4,5] "
                        "or v_lr=0.1). Used by hyperparameter sweeps; recorded in the run's summary")
    p.add_argument("--final_only", action="store_true",
                   help="evaluate only before editing and at the end (hyperparameter sweeps), "
                        "ignoring --checkpoint_every/--fluency_every/--sample_every")
    p.add_argument("--checkpoint_every", type=int, default=50, help="cheap metrics (edit/locality/portability)")
    p.add_argument("--fluency_every", type=int, default=250, help="adds the generation-based fluency score (multiple of --checkpoint_every)")
    p.add_argument("--sample_every", type=int, default=500, help="dumps a few raw generated samples for eyeballing (multiple of --checkpoint_every)")
    # Method-family-specific knobs. All are accepted regardless of --method
    # so the dashboard can pass every field unconditionally; each is applied
    # only for the family it belongs to, and ignored otherwise.
    # FT/LoRA:
    p.add_argument("--lr", type=float, default=1e-4)
    p.add_argument("--num_steps", type=int, default=10000)
    # Locate-and-edit (MEMIT/PMET/AlphaEdit - ROME sets mom2_adjustment
    # false and never touches this):
    p.add_argument(
        "--mom2_n_samples",
        type=int,
        default=None,
        help="Wikipedia samples used to estimate the second-moment (covariance) statistics "
        "these methods need. The stock value is 100000, which takes hours on first use for a "
        "given model+layer and is cached under hparams' stats_dir afterwards. Lower it to get "
        "a usable run sooner at the cost of a noisier estimate. Left alone, the hparams file wins.",
    )
    # In-context (SCR/IKE) - one knob, since it means the same thing in
    # both (how many retrieved items get prepended), but the two hparams
    # classes spell it differently (retrieval_k vs k).
    p.add_argument(
        "--retrieval_k",
        type=int,
        default=None,
        help="How many retrieved items SCR/IKE prepend to a prompt. Left alone, the hparams file wins.",
    )
    p.add_argument(
        "--kb_size",
        type=int,
        default=None,
        help="SCR only: ask each record against a knowledge base of this many facts, its own fact "
        "plus kb_size-1 distractors (the same dataset first, then its training file, then other "
        "datasets; see scr.distractor_entries). Left out, the knowledge base grows one edit at a "
        "time to every loaded record, as before.",
    )
    p.add_argument("--easyedit_path", default=DEFAULT_EASYEDIT_PATH)
    p.add_argument("--out_root", default=DEFAULT_OUT_ROOT)
    launch_guard.add_argument(p)
    p.add_argument(
        "--run_name",
        default=None,
        help="Override the auto-computed run directory name (runs/<run_name>/). "
        "The dashboard always passes this explicitly, computed from whichever "
        "fields are actually varying in a given submission.",
    )
    p.add_argument("--evaluation_modes", default="original",
                   help="Comma-separated: original,exact_match,bertscore,llm_judge; modes share one edit run")
    p.add_argument("--edit_mode",
                   choices=("single", "batch", "sequential", "sequential_batch"), default=None,
                   help="single: one fact per edit, reset after each. batch: one joint edit of "
                        "--edit_batch_size facts, reset after each. sequential / sequential_batch: "
                        "the same two, accumulated until --reset_every facts have been edited")
    p.add_argument("--reset_every", type=int, default=1000,
                   help="Facts edited before the original weights are restored "
                        "(sequential and sequential_batch only; the other two reset every call)")
    p.add_argument("--edit_batch_size", type=int, default=10,
                   help="Facts per joint edit call (batch and sequential_batch only); under "
                        "sequential_batch it may not exceed --reset_every")
    args = p.parse_args()
    from evaluation_config import validate_modes
    from edit_protocol import validate_protocol
    try:
        args.evaluation_modes = validate_modes(args.evaluation_modes)
        validate_protocol(args.method, args.edit_mode, args.reset_every, args.edit_batch_size)
    except ValueError as exc:
        p.error(str(exc))
    if args.kb_size is not None:
        if args.method != "scr":
            p.error("--kb_size applies to SCR only")
        if args.kb_size < 1:
            p.error("--kb_size must be at least 1 (the record's own fact)")
    for name in ("fluency_every", "sample_every"):
        v = getattr(args, name)
        if v % args.checkpoint_every != 0:
            p.error(f"--{name} ({v}) must be a multiple of --checkpoint_every ({args.checkpoint_every})")
    return args


# hparams keys holding filesystem paths. They are stored relative to
# PROJECT_ROOT and must be absolute before use: the working directory is the
# experiment folder, and EasyEdit names cached covariance statistics after
# model_name, so the resolved string has to be stable across runs.
PATH_KEYS = ("model_name", "stats_dir", "P_loc")


def resolve_project_paths(hparams):
    def absolute(value):
        if isinstance(value, str) and value and not os.path.isabs(value):
            if value.startswith("./"):
                # "./x" was always relative to the working directory, which
                # is this experiment folder; keep that meaning.
                return os.path.normpath(os.path.join(EXP_DIR, value))
            return os.path.join(PROJECT_ROOT, value)
        return value

    for key in PATH_KEYS:
        if hasattr(hparams, key):
            setattr(hparams, key, absolute(getattr(hparams, key)))
    # FiDAL carries its base editor's config as a nested dict.
    base_config = getattr(hparams, "base_config", None)
    if isinstance(base_config, dict):
        for key in PATH_KEYS:
            if key in base_config:
                base_config[key] = absolute(base_config[key])
    return hparams


def apply_overrides(hparams, pairs):
    """--hparam key=value settings onto a loaded hparams object. Refuses keys
    the method does not have, so a typo cannot silently sweep nothing.
    FiDAL keeps its base editor's settings in base_config; keys found only
    there are set there."""
    overrides = {}
    base_config = getattr(hparams, "base_config", None)
    for pair in pairs:
        key, sep, raw = pair.partition("=")
        key = key.strip()
        if not sep or not key:
            raise SystemExit(f"--hparam expects KEY=VALUE, got {pair!r}")
        value = yaml.safe_load(raw)
        if hasattr(hparams, key):
            setattr(hparams, key, value)
        elif isinstance(base_config, dict) and key in base_config:
            base_config[key] = value
        else:
            raise SystemExit(f"--hparam {key}: {type(hparams).__name__} has no setting named {key!r}")
        overrides[key] = value
    return overrides


def _hparams_path(method, model):
    return os.path.join(EXP_DIR, "hparams", METHOD_HPARAMS_DIR[method], f"{model}.yaml")


def _guess_dataset_benchmark(data_path):
    """Fallback for manual (non-dashboard) runs that don't pass
    --dataset_benchmark explicitly: the path component right after
    'datasets/' matches how every dataset is actually laid out on disk
    (datasets/<Benchmark>/...)."""
    parts = os.path.normpath(data_path).split(os.sep)
    if "datasets" in parts:
        i = parts.index("datasets")
        if i + 1 < len(parts):
            return parts[i + 1]
    return "unknown"


def _import(module_path, name):
    return getattr(importlib.import_module(module_path), name)


def _now():
    """Wall-clock stamp for the result files - local time, but carrying its
    UTC offset, so it reads the same way as `squeue`/`sacct` times without
    being ambiguous about which timezone the node was in. Everything else
    on a run is measured relative to its start (elapsed_sec/total_sec);
    these are the only absolute times recorded."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def main():
    args = parse_args()
    launch_guard.require_dashboard(args.out_root, args.untracked, "run_experiment")
    sys.path.insert(0, args.easyedit_path)
    sys.path.insert(0, EXP_DIR)

    from eval_utils import load_requests, evaluate_requests, aggregate_metrics, memory_snapshot, sample_generations

    from semantic_evaluation import SemanticEvaluator, collect_probes, cached_answer
    from edit_protocol import edit_groups, average_group_evaluations
    semantic = SemanticEvaluator(args.evaluation_modes)
    semantic_baseline = {}
    torch.manual_seed(args.seed)

    hparams_path = _hparams_path(args.method, args.model)
    if not os.path.exists(hparams_path):
        raise SystemExit(
            f"no hparams file for --method {args.method} --model {args.model} "
            f"(expected {hparams_path}) - add one to register this combination"
        )

    # Loaded before the model - it's independent of device/model entirely,
    # and this way a bad --data_path or a method/dataset mismatch (e.g.
    # ROME on a dataset with no 'subject' field) fails fast, before paying
    # for a GPU model load.
    # The split is applied to the full file before --ds_size slices it, so
    # "the first 20" means the first 20 records of this split.
    import splits
    all_requests = load_requests(args.data_path, None)
    try:
        requests = splits.select(all_requests, args.data_path, args.split)
    except ValueError as exc:
        raise SystemExit(str(exc))
    requests = requests[:args.ds_size]
    print(f"{len(requests)} edit requests from the {args.split} split of {args.data_path}")
    if args.method in LOCATE_AND_EDIT and any("subject" not in r for r in requests):
        raise SystemExit(
            f"--method {args.method} needs a 'subject' token to locate and edit, but --data_path "
            f"{args.data_path} doesn't provide one (see its load_*_requests function in eval_utils.py). "
            "Use --method ft/lora/scr/ike with this dataset instead."
        )
    # Also checked before the model load, so an impossible pairing fails fast.
    if args.method == "kn" and any(r.get("ground_truth") in (None, "", "<|endoftext|>") for r in requests):
        raise SystemExit(f"--method kn attributes neurons to the original answer, and {args.data_path} "
                         "has records without one (ground_truth)")
    if args.method == "cake":
        from cake import CAKE_DATA
        if os.path.basename(args.data_path) not in CAKE_DATA:
            raise SystemExit(f"--method cake has circuit-guided training data only for {', '.join(CAKE_DATA)} "
                             "(upstream releases no generator for other datasets)")

    # From here on ds_size means the number of requests actually loaded, not
    # the number asked for: "full" has no number until the file is read, and a
    # count larger than the dataset would otherwise be quoted in the summary
    # and used as a step total the run can never reach.
    ds_size_requested = "full" if args.ds_size is None else args.ds_size
    args.ds_size = len(requests)

    # A reset interval wider than the dataset describes the same run as one
    # exactly as wide as it - edit_groups yields a single group either way -
    # so clamp rather than reject. The queued job still does something
    # meaningful, and what gets recorded is what actually happened.
    from edit_protocol import JOINT_MODES, SEQUENTIAL_MODES

    if args.edit_mode in SEQUENTIAL_MODES and args.reset_every > args.ds_size:
        print(f"reset interval {args.reset_every} exceeds the {args.ds_size} requests loaded; using {args.ds_size}")
        args.reset_every = args.ds_size
    if args.edit_mode in JOINT_MODES:
        # Under sequential_batch the group is the binding limit; under plain
        # batch the group *is* the call, so the dataset is.
        cap = args.reset_every if args.edit_mode == "sequential_batch" else args.ds_size
        if args.edit_batch_size > cap:
            print(f"edit batch size {args.edit_batch_size} exceeds {cap}; using {cap}")
            args.edit_batch_size = cap

    if args.method in FT_METHODS:
        from easyeditor.models.ft.ft_hparams import FTHyperParams

        hparams = FTHyperParams.from_hparams(hparams_path)
        hparams.lr = args.lr
        hparams.num_steps = args.num_steps
        hparams.batch_size = args.ds_size  # whole batch every step, see checkpointed_ft.py
        total_steps = args.ds_size if args.edit_mode else args.num_steps
    elif args.method == "lora":
        from easyeditor.models.lora.lora_hparams import LoRAHyperParams

        hparams = LoRAHyperParams.from_hparams(hparams_path)
        hparams.lr = args.lr
        hparams.num_steps = args.num_steps
        hparams.batch_size = args.ds_size  # whole batch every step, see checkpointed_lora.py
        total_steps = args.ds_size if args.edit_mode else args.num_steps
    elif args.method in LOCATE_AND_EDIT:
        spec = LOCATE_AND_EDIT[args.method]
        hparams_cls = _import(spec["hparams_module"], spec["hparams_class"])
        hparams = hparams_cls.from_hparams(hparams_path)
        # Only meaningful where the method actually estimates covariance
        # statistics - ROME sets mom2_adjustment false, so overriding the
        # sample count there would be a silently inert knob.
        if args.mom2_n_samples is not None and getattr(hparams, "mom2_adjustment", False):
            hparams.mom2_n_samples = args.mom2_n_samples
        # FiDAL keeps its base editor's settings in a nested dict (it
        # configures a locator plus whichever editor it hands layers to),
        # so the same override has to reach one level deeper or it would
        # silently do nothing for the one method whose base editor is
        # always a covariance-using one.
        base_config = getattr(hparams, "base_config", None)
        if args.mom2_n_samples is not None and base_config and base_config.get("mom2_adjustment"):
            base_config["mom2_n_samples"] = args.mom2_n_samples
        total_steps = args.ds_size
    elif args.method == "scr":
        from scr import SCRHyperParams

        hparams = SCRHyperParams.from_hparams(hparams_path)
        if args.retrieval_k is not None:
            hparams.retrieval_k = args.retrieval_k
        total_steps = args.ds_size
    else:  # ike
        from ike import IKEHyperParams

        hparams = IKEHyperParams.from_hparams(hparams_path)
        if args.retrieval_k is not None:
            hparams.k = args.retrieval_k  # IKE's spelling of the same knob
        total_steps = args.ds_size

    overrides = apply_overrides(hparams, args.hparam)
    if args.method in FT_METHODS and hparams.objective_optimization != FT_OBJECTIVE[args.method]:
        raise SystemExit(f"{args.method} trains with objective_optimization={FT_OBJECTIVE[args.method]!r}, "
                         f"but the hparams (or an --hparam override) set {hparams.objective_optimization!r}; "
                         f"use the other FT method instead")
    if args.method == "cake":
        hparams.data_path = args.data_path  # which CaKE training file to use
        hparams.seed = args.seed
    resolve_project_paths(hparams)

    if args.final_only:
        # One evaluation before editing (the baseline locality and fluency
        # are measured against) and one at the end: nothing in between.
        args.checkpoint_every = args.fluency_every = args.sample_every = max(total_steps, 1)

    if args.method in ("scr", "ike"):
        semantic.cfg["max_new_tokens"] = hparams.max_new_tokens


    dataset_benchmark = args.dataset_benchmark or _guess_dataset_benchmark(args.data_path)
    dataset_subset = args.dataset_subset or os.path.splitext(os.path.basename(args.data_path))[0]

    run_name = args.run_name or f"{args.method}_{args.model}"
    if not args.run_name and args.evaluation_modes != ["original"]:
        run_name += "_eval-" + "-".join(args.evaluation_modes)
    if not args.run_name and args.kb_size is not None:
        run_name += f"_kb{args.kb_size}"
    if not args.run_name and args.edit_mode:
        run_name += f"_{args.edit_mode}"
        if args.edit_mode in SEQUENTIAL_MODES:
            run_name += f"_reset{args.reset_every}"
        if args.edit_mode in JOINT_MODES:
            run_name += f"_batch{args.edit_batch_size}"
    run_dir = os.path.join(args.out_root, "runs", run_name)
    samples_dir = os.path.join(run_dir, "samples")
    os.makedirs(samples_dir, exist_ok=True)
    import loss_log
    loss_log.start(os.path.join(run_dir, "loss.jsonl"))

    # Written into hparams.yaml (not just summary.json) because that file
    # lands on disk immediately, before the model even loads - so a run
    # that crashes or gets killed partway still records when it started.
    started_at = _now()

    with open(os.path.join(run_dir, "hparams.yaml"), "w") as f:
        yaml.safe_dump(
            {
                **hparams.to_dict(),
                "evaluation_modes": args.evaluation_modes,
                "edit_mode": args.edit_mode,
                "reset_every": args.reset_every if args.edit_mode in SEQUENTIAL_MODES else None,
                "edit_batch_size": args.edit_batch_size if args.edit_mode in JOINT_MODES else None,
                "evaluation_config": semantic.metadata(),
                "started_at": started_at,
                "method": args.method,
                "model": args.model,
                "ds_size": args.ds_size,
                "ds_size_requested": ds_size_requested,
                "checkpoint_every": args.checkpoint_every,
                "fluency_every": args.fluency_every,
                "sample_every": args.sample_every,
                "data_path": args.data_path,
                "split": args.split,
                "final_only": args.final_only,
                "hparam_overrides": overrides,
                "kb_size": args.kb_size,
                "seed": args.seed,
                "run_name": run_name,
                "dataset_benchmark": dataset_benchmark,
                "dataset_subset": dataset_subset,
            },
            f,
        )

    device = f"cuda:{hparams.device}"
    print(f"[{run_name}] loading model from {hparams.model_name}")
    tok = AutoTokenizer.from_pretrained(hparams.model_name)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(hparams.model_name, torch_dtype=torch.bfloat16).to(device)

    if args.method == "lora":
        # Wrapping happens here (once, before any checkpoint), not inside
        # checkpointed_lora.py - see that file's docstring for why. From
        # this point on `model` refers to the peft-wrapped object; every
        # later use (checkpointing, evaluation, sample generation) sees
        # the same object as it's trained in place.
        from peft import AdaLoraConfig, LoraConfig, TaskType, get_peft_model

        model.config.use_cache = False
        model.supports_gradient_checkpointing = True
        model.gradient_checkpointing_enable()
        model.enable_input_require_grads()
        is_adalora = hparams.lora_type != "lora"
        peft_kwargs = dict(
            task_type=TaskType.CAUSAL_LM,
            inference_mode=False,
            r=hparams.rank,
            lora_alpha=hparams.lora_alpha,
            lora_dropout=hparams.lora_dropout,
            layers_to_transform=hparams.layers if len(hparams.layers) > 0 else None,
            target_modules=hparams.target_modules,
        )
        # AdaLoRA prunes the adapter's rank on a schedule spanning the whole
        # run, so peft refuses to build its config without knowing the step
        # count upfront. Plain LoRA has no such schedule and rejects the
        # argument outright, so it can only be passed to one of the two.
        # hparams/LoRA/gpt-j-6b.yaml asks for adalora while qwen3-4b.yaml
        # asks for lora, which is why this only ever failed on GPT-J.
        if is_adalora:
            peft_kwargs["total_step"] = total_steps
        peft_config = (AdaLoraConfig if is_adalora else LoraConfig)(**peft_kwargs)
        model = get_peft_model(model, peft_config)
        model.print_trainable_parameters()

    scr_kb = None
    if args.method == "scr":
        from scr import SCRIndex

        scr_kb = SCRIndex(hparams.sentence_model_name, device)

    distractor_counts = None
    record_entries = None
    if args.kb_size is not None:
        from scr import distractor_entries, kb_entries

        distractors, distractor_counts = distractor_entries(
            args.data_path, requests, args.kb_size - 1, args.seed, lambda path: load_requests(path, None),
            os.path.join(PROJECT_ROOT, "datasets"), hparams.kb_key)
        record_entries = kb_entries(requests, hparams.kb_key)
        print(f"[{run_name}] knowledge base of {args.kb_size}: each record's own fact plus "
              f"{len(distractors)} distractors ({distractor_counts})")

    ike_pool = None
    ike_demo_requests = None
    if args.method == "ike":
        from scr import SCRIndex

        ike_pool = SCRIndex(hparams.sentence_model_name, device)
        # A separate *training* split for demonstrations, never the test
        # set being evaluated - by convention, swap "test" for "train" in
        # the data_path; if no such file exists (e.g. ZsRE ships no train
        # split), fall back to the test set doubling as its own demo pool.
        demo_path = args.data_path.replace("test", "train")
        if demo_path != args.data_path and os.path.exists(demo_path):
            ike_demo_requests = load_requests(demo_path, args.ds_size)
            demo_source = demo_path
        else:
            # No train file: use the split's demo portion, records that are
            # neither dev nor test. Falling back to the evaluated records
            # themselves would put each answer in its own prompt (the
            # "copy" demonstration restates the new fact verbatim).
            pool = splits.demo_pool(all_requests, args.data_path)
            if pool is None:
                raise SystemExit(f"IKE needs demonstration records separate from those it is evaluated on, "
                                 f"and {args.data_path} has no train file or split demo portion")
            ike_demo_requests = pool[:args.ds_size]
            demo_source = f"{args.data_path} (split demo portion)"
        print(f"[{run_name}] {len(ike_demo_requests)} IKE demo records from {demo_source}")

    ckpt_path = os.path.join(run_dir, "checkpoints.jsonl")
    ckpt_file = open(ckpt_path, "w")
    state = {"baseline_locality": None, "scr_baseline": None, "ike_baseline": None,
             "group_start": 0, "group_stop": len(requests), "group_rows": [],
             # --kb_size: set once the distractors are in, so step 0 stays an
             # empty-knowledge-base baseline.
             "record_scope": None}
    record_index = {id(r): i for i, r in enumerate(requests)}
    t_start = time.time()

    samples_written = set()

    def write_samples(step):
        from response_samples import method_samples

        sample_requests = requests[state["group_start"]:state["group_stop"]] if args.edit_mode and step else requests
        samples = method_samples(model, tok, sample_requests, device, args.method, step, hparams,
                                 scr_kb if args.method == "scr" else ike_pool, state["record_scope"])
        with open(os.path.join(samples_dir, f"step_{step:06d}.json"), "w") as f:
            json.dump(samples, f, indent=2)
        samples_written.add(step)

    def on_checkpoint(step, loss):
        was_training = model.training
        model.eval()
        group_start = state["group_start"] if args.edit_mode and step else 0
        group_stop = state["group_stop"] if args.edit_mode and step else len(requests)
        scored_requests = requests[group_start:group_stop]
        # The final step always scores fluency: runs whose step count is not
        # a multiple of --fluency_every used to end with no fluency at all.
        do_fluency = step % args.fluency_every == 0 or step == total_steps
        answer_cache = {}
        evaluations = {}
        if "original" in args.evaluation_modes:
            if args.method == "scr":
                from scr import evaluate_requests_scr

                per_record, scr_answers = evaluate_requests_scr(
                    model, tok, requests, scr_kb, device, hparams, baseline_answers=state["scr_baseline"], answer_cache=answer_cache,
                    fluency=do_fluency, record_scope=state["record_scope"],
                )
                if state["scr_baseline"] is None:
                    state["scr_baseline"] = scr_answers  # step 0 (empty KB) becomes the baseline
            elif args.method == "ike":
                from ike import evaluate_requests_ike

                per_record, ike_answers = evaluate_requests_ike(
                    model, tok, requests, ike_pool, device, hparams, baseline_answers=state["ike_baseline"], answer_cache=answer_cache,
                    fluency=do_fluency,
                )
                if state["ike_baseline"] is None:
                    state["ike_baseline"] = ike_answers  # step 0 (empty demo pool) becomes the baseline
            else:
                per_record, locality_outputs = evaluate_requests(
                    model, hparams.model_name, hparams, tok, scored_requests, device,
                    test_generation=do_fluency,
                    baseline_locality_outputs=(state["baseline_locality"][group_start:group_stop]
                                               if state["baseline_locality"] is not None else None),
                )
                if state["baseline_locality"] is None:
                    state["baseline_locality"] = locality_outputs  # step 0 becomes the baseline

            evaluations["original"] = aggregate_metrics(per_record)
        if semantic.modes:
            def answer(record, question):
                if args.method == "scr":
                    from scr import scr_answer

                    def ask():
                        return scr_answer(model, tok, question, scr_kb, device, hparams.retrieval_k,
                                          hparams.max_new_tokens, hparams)
                    if state["record_scope"] is None:
                        return cached_answer(answer_cache, question, ask)
                    i = record_index[id(record)]
                    with state["record_scope"](i):
                        return cached_answer(answer_cache, ("record", i, question), ask)
                if args.method == "ike" and step != 0:
                    from ike import ike_answer
                    fact = f"{record['prompt']} {record['target_new']}"
                    return cached_answer(answer_cache, (fact, question), lambda: ike_answer(
                        model, tok, fact, question, ike_pool, device, hparams.k, hparams.max_new_tokens))
                # Raw completion prompts work with base models too. Step-zero IKE
                # must not inject the new fact when measuring semantic preservation.
                def generate():
                    with torch.no_grad():
                        inputs = tok(question, return_tensors="pt").to(device)
                        output = model.generate(**inputs, max_new_tokens=semantic.cfg["max_new_tokens"],
                                                do_sample=False, pad_token_id=tok.eos_token_id)
                    return tok.decode(output[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
                return cached_answer(answer_cache, ("raw", question), generate)
            probes = collect_probes(scored_requests, answer, semantic_baseline, case_offset=group_start)
            # Save before scoring as well, so API/encoder failure cannot erase answers.
            evaluation_dir = os.path.join(run_dir, "evaluations")
            os.makedirs(evaluation_dir, exist_ok=True)
            probe_path = os.path.join(evaluation_dir, f"step_{step:06d}.json")
            with open(probe_path, "w") as f:
                json.dump({"step": step, "config": semantic.metadata(), "probes": probes}, f, indent=2)
            evaluations.update(semantic.score(probes))
            with open(probe_path, "w") as f:
                json.dump({"step": step, "config": semantic.metadata(), "scores": evaluations,
                           "probes": probes}, f, indent=2)
        # Where the dynamic methods chose to write, for the facts edited
        # since the last checkpoint. Drained (not merely read) so each
        # record lands against exactly one checkpoint, and written to its
        # own file because a per-fact record is far too long to belong in
        # a checkpoint row - the row keeps only the layer histogram.
        chosen_layers = None
        if args.method in DYNAMIC_METHODS:
            from dynamic import locations

            records = locations.drain()
            if records:
                with open(os.path.join(run_dir, "locations.jsonl"), "a") as f:
                    for record in records:
                        f.write(json.dumps({"step": step, **record}) + "\n")
            chosen_layers = locations.layer_histogram(records)

        # Legacy headline fields remain Original-only, never silently relabeled.
        original = evaluations.get("original", dict.fromkeys(("edit_succ", "portability", "locality", "fluency")))
        row = {
            "step": step,
            "total_steps": total_steps,
            "at": _now(),
            "elapsed_sec": round(time.time() - t_start, 2),
            "loss": loss,
            **original,
            "evaluation_modes": args.evaluation_modes,
            "evaluations": evaluations,
            **({"chosen_layers": chosen_layers} if chosen_layers else {}),
            **memory_snapshot(device),
        }
        if args.edit_mode and step:
            row.update({"group_start": group_start, "group_end": group_stop,
                        "group_size": group_stop - group_start, "edit_mode": args.edit_mode,
                        "reset_every": args.reset_every if args.edit_mode in SEQUENTIAL_MODES else 1,
                        "edit_batch_size": args.edit_batch_size if args.edit_mode in JOINT_MODES else 1})
            state["group_rows"].append(row)
        ckpt_file.write(json.dumps(row) + "\n")
        ckpt_file.flush()
        print(f"[{run_name}] step={step:>6} " + " ".join(f"{k}={v}" for k, v in row.items() if k != "step"))

        state["last_step"] = step
        if step % args.sample_every == 0 or step == total_steps:
            write_samples(step)
        model.train(was_training)

    try:
        if args.edit_mode:
            from easyeditor.util import nethook
            from easyeditor.util.device import copy_to_param

            apply_fn = None
            if args.method in LOCATE_AND_EDIT:
                spec = LOCATE_AND_EDIT[args.method]
                apply_fn = _import(spec["apply_module"], spec["apply_fn"])
            training_fn = None
            if args.method in FT_METHODS:
                from checkpointed_ft import execute_ft_checkpointed
                training_fn = execute_ft_checkpointed
            elif args.method == "lora":
                from checkpointed_lora import execute_lora_checkpointed
                training_fn = execute_lora_checkpointed

            on_checkpoint(0, loss=None)
            for start, stop, calls in edit_groups(len(requests), args.edit_mode,
                                                   args.reset_every, args.edit_batch_size):
                state["group_start"], state["group_stop"] = start, stop
                if args.method in FT_METHODS:
                    tuned = {name: param for name, param in model.named_parameters()
                             if any(hparams.rewrite_module_tmp.format(layer) in name for layer in hparams.layers)}
                    originals = {name: param.detach().clone() for name, param in tuned.items()}
                elif args.method == "lora":
                    originals = {name: param.detach().clone() for name, param in model.named_parameters()
                                 if param.requires_grad}
                else:
                    originals = {}

                loss = None
                for call_start, call_stop in calls:
                    chunk = requests[call_start:call_stop]
                    if training_fn:
                        hparams.batch_size = len(chunk)
                        latest = {"loss": None}
                        # The training loops call on_checkpoint(step, loss=...);
                        # this used to take `value`, so FT and LoRA crashed at
                        # their first checkpoint under every edit protocol.
                        def capture(step, loss=None):
                            if step:
                                latest["loss"] = loss
                        training_fn(model, tok, chunk, hparams, hparams.num_steps, capture)
                        loss = latest["loss"]
                    else:
                        model, copied = apply_fn(model, tok, chunk, hparams, copy=False,
                                                 return_orig_weights=True)
                        # Each call snapshots its own input; keep the first copy
                        # of each parameter so restoration reaches the base model.
                        for name, value in copied.items():
                            originals.setdefault(name, value)
                on_checkpoint(stop, loss=loss)
                with torch.no_grad():
                    for name, value in originals.items():
                        copy_to_param(nethook.get_parameter(model, name), value)
                del originals
        elif args.method in FT_METHODS:
            from checkpointed_ft import execute_ft_checkpointed

            execute_ft_checkpointed(model, tok, requests, hparams, args.checkpoint_every, on_checkpoint)
        elif args.method == "lora":
            from checkpointed_lora import execute_lora_checkpointed

            execute_lora_checkpointed(model, tok, requests, hparams, args.checkpoint_every, on_checkpoint)
        elif args.method in LOCATE_AND_EDIT:
            spec = LOCATE_AND_EDIT[args.method]
            apply_fn = _import(spec["apply_module"], spec["apply_fn"])

            on_checkpoint(0, loss=None)
            prev = 0
            for i in range(total_steps):
                step = i + 1
                if step % args.checkpoint_every == 0 or step == total_steps:
                    if spec["mode"] == "single":
                        for j in range(prev, step):
                            model, _ = apply_fn(model, tok, [requests[j]], hparams, copy=False)
                    else:  # batch - solve for this whole interval's facts jointly
                        model, _ = apply_fn(model, tok, requests[prev:step], hparams, copy=False)
                    prev = step
                    on_checkpoint(step, loss=None)
        elif args.method == "scr" and args.kb_size is not None:
            on_checkpoint(0, loss=None)  # KB still empty - pure baseline, nothing ever injected
            scr_kb.grow([e["text"] for e in distractors], keys=[e["key"] for e in distractors],
                        ids=[e["id"] for e in distractors])
            state["record_scope"] = lambda i: scr_kb.holding(record_entries[i])
            on_checkpoint(total_steps, loss=None)
        elif args.method == "scr":
            from scr import kb_entries

            entries = kb_entries(requests, hparams.kb_key)
            on_checkpoint(0, loss=None)  # KB still empty - pure baseline, nothing ever injected
            for i in range(total_steps):
                e = entries[i]
                scr_kb.grow([e["text"]], keys=[e["key"]], ids=[e["id"]], replace=hparams.latest_edit_wins)
                step = i + 1
                if step % args.checkpoint_every == 0 or step == total_steps:
                    on_checkpoint(step, loss=None)
        else:  # ike
            from ike import build_demo_sentences

            on_checkpoint(0, loss=None)  # demo pool still empty - pure baseline, no ICL prefix used
            for i in range(min(total_steps, len(ike_demo_requests))):
                ike_pool.grow(build_demo_sentences([ike_demo_requests[i]]))
                step = i + 1
                if step % args.checkpoint_every == 0 or step == total_steps:
                    on_checkpoint(step, loss=None)
        last_step = state.get("last_step")
        if last_step is not None and last_step not in samples_written:
            write_samples(last_step)
    finally:
        ckpt_file.close()

    with open(ckpt_path) as f:
        last_row = json.loads(f.readlines()[-1])
    summary = {
        "run": run_name,
        "method": args.method,
        "model": args.model,
        "dataset_benchmark": dataset_benchmark,
        "dataset_subset": dataset_subset,
        "data_path": args.data_path,
        "lr": args.lr if args.method in FT_METHODS + ("lora",) else None,
        "num_steps": total_steps,
        "edit_mode": args.edit_mode,
        "reset_every": args.reset_every if args.edit_mode in SEQUENTIAL_MODES else None,
        "edit_batch_size": args.edit_batch_size if args.edit_mode in JOINT_MODES else None,
        "ds_size": args.ds_size,
        "ds_size_requested": ds_size_requested,
        "split": args.split,
        "hparam_overrides": overrides,
        "kb_size": args.kb_size,
        "kb_distractors": distractor_counts,
        "seed": args.seed,
        # started_at predates the model load, total_sec is measured from
        # after it - so finished_at - started_at is legitimately a bit
        # longer than total_sec, by however long the weights took to load.
        "started_at": started_at,
        "finished_at": _now(),
        "evaluation_config": semantic.metadata(),
        "total_sec": round(time.time() - t_start, 2),
        **{k: v for k, v in last_row.items() if k not in ("step", "at", "elapsed_sec")},
    }
    if args.edit_mode:
        averaged = average_group_evaluations(state["group_rows"])
        summary["evaluations"] = averaged
        summary.update(averaged.get("original", dict.fromkeys(("edit_succ", "portability", "locality", "fluency"))))
        summary["group_count"] = len(state["group_rows"])
        summary["group_results"] = [{"start": row["group_start"], "end": row["group_end"],
                                      "size": row["group_size"], "evaluations": row["evaluations"]}
                                     for row in state["group_rows"]]
    with open(os.path.join(run_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(f"[{run_name}] done: {summary}")

    _rebuild_manifest(args.out_root)


def _rebuild_manifest(out_root):
    """Scans every runs/*/summary.json found so far and rewrites
    manifest.json. Safe to call from multiple concurrent runs (a sweep
    submits several jobs that may finish around the same time) — each
    call is a full rescan, so the result always reflects whichever
    summaries exist at that moment, rather than a read-modify-write on a
    shared list that could race between processes."""
    runs_dir = os.path.join(out_root, "runs")
    manifest = []
    for name in sorted(os.listdir(runs_dir)):
        summary_path = os.path.join(runs_dir, name, "summary.json")
        if os.path.exists(summary_path):
            with open(summary_path) as f:
                manifest.append(json.load(f))
    with open(os.path.join(out_root, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)


if __name__ == "__main__":
    main()
