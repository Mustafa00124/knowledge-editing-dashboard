"""Method smoke run: every core method on every Sid's Dataset record, for one model.

Runs run_experiment.py --smoke once per core method (the methods marked core
in experiments/run_experiment/dashboard.json), one after another on the same
GPU. Each writes results/sids_smoke/runs/smoke_<method>_<model>/smoke.jsonl
and summary.json; CRITERIA Rule 14 reads them. A method that crashes outright
(import error, model load) is recorded as a summary with crashed: true, so it
shows as a failure rather than as missing.

Launch from the dashboard, one run per model:

    python scripts/dash.py launch sids_smoke --label "smoke qwen3-4b-instruct-2507" -- --model qwen3-4b-instruct-2507
"""
import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.dirname(HERE))
import launch_guard  # noqa: E402

RUNNER = os.path.join(PROJECT_ROOT, "experiments", "run_experiment", "run_experiment.py")
DEFAULT_OUT_ROOT = os.path.join(PROJECT_ROOT, "results", "sids_smoke")
DEFAULT_RECORDS = os.path.join(PROJECT_ROOT, "datasets", "SidsDataset", "records")

# The four main models (CRITERIA Rule 6 and Rule 14). Weights directories as in
# run_experiment.py, so the dashboard greys out a model that isn't downloaded.
MODEL_PATHS = {
    "qwen3-4b-instruct-2507": os.path.join(PROJECT_ROOT, "models/Qwen3-4B-Instruct-2507"),
    "olmo-3-7b-instruct": os.path.join(PROJECT_ROOT, "models/Olmo-3-7B-Instruct"),
    "llama-3.1-8b-instruct": os.path.join(PROJECT_ROOT, "models/Llama-3.1-8B-Instruct"),
    "mistral-7b-instruct-v0.1": os.path.join(PROJECT_ROOT, "models/Mistral-7B-Instruct-v0.1"),
}


def core_methods():
    """The core set, read from the runner's dashboard.json so it never drifts."""
    with open(os.path.join(PROJECT_ROOT, "experiments", "run_experiment", "dashboard.json")) as f:
        spec = json.load(f)
    field = next(x for x in spec["fields"] if x["name"] == "method")
    return [m["value"] for c in field["categories"] for m in c["methods"] if m.get("core")]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model", required=True, choices=sorted(MODEL_PATHS))
    p.add_argument("--methods", default="", help="comma-separated methods (empty: the core set)")
    p.add_argument("--records", default=DEFAULT_RECORDS)
    p.add_argument("--run_name", default=None)
    p.add_argument("--out_root", default=DEFAULT_OUT_ROOT)
    launch_guard.add_argument(p)
    args = p.parse_args()
    launch_guard.require_dashboard(args.out_root, args.untracked, "sids_smoke")

    methods = [m for m in args.methods.split(",") if m] or core_methods()
    print(f"smoke run on {args.model}: {', '.join(methods)}")
    for method in methods:
        run_name = f"smoke_{method}_{args.model}"
        cmd = [sys.executable, RUNNER, "--smoke", "--method", method, "--model", args.model,
               "--data_path", args.records, "--out_root", args.out_root, "--run_name", run_name,
               "--dataset_benchmark", "SidsDataset", "--dataset_subset", "records"]
        if args.untracked:
            cmd.append("--untracked")
        print(f"\n=== {method} ===\n{' '.join(cmd)}", flush=True)
        code = subprocess.call(cmd)
        if code != 0:
            run_dir = os.path.join(args.out_root, "runs", run_name)
            os.makedirs(run_dir, exist_ok=True)
            with open(os.path.join(run_dir, "summary.json"), "w") as f:
                json.dump({"method": method, "model": args.model, "crashed": True, "exit_code": code,
                           "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S")}, f, indent=2)
            print(f"=== {method} crashed (exit {code}); recorded as a failure ===", flush=True)


if __name__ == "__main__":
    main()
