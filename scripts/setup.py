#!/usr/bin/env python3
"""Download what the git repo leaves out, choosing exactly which pieces.

The repo carries code and configs only. Datasets, models, EasyEdit and the
experiment environment are fetched on request, each at a pinned revision
and checked against recorded sha256s where the source allows:

    python scripts/setup.py --status                  what is present and what is missing
    python scripts/setup.py --datasets KnowEdit MQuAKE  just these benchmarks
    python scripts/setup.py --datasets                every benchmark (UniEdit's train split
                                                      only with --parts train)
    python scripts/setup.py --models Qwen3-4B         model weights (names from --status);
                                                      --models main for the set experiments use
    python scripts/setup.py --external                EasyEdit (+ this project's AlphaEdit fix)
    python scripts/setup.py --venv                    venvs/easyedit_venv for running experiments

The dashboard's Downloads page offers the same choices with buttons; it runs
this script. Everything is resumable: rerunning skips what is in place.
Standard library only, so it runs before any environment exists (model
downloads need huggingface_hub, which the dashboard backend installs).
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "dashboard" / "backend"))
import models_reader  # noqa: E402
import sources  # noqa: E402

# The reference implementations the dynamic/ methods were ported from. Not
# needed to run anything; kept at the commits the ports were made against.
REFERENCE_REPOS = {
    "WilKE": ("https://github.com/ChenhuiHu/WilKE.git", "2aa874b4a3dae915bdebf3ef765ac06d710cc9d6"),
    "FiNE": ("https://github.com/opanhw/FiNE.git", "87bdf930edee6aa0f1f1cdc28cc374a89c55cb7d"),
    "NMKE": ("https://github.com/LiuJinzhe-Keepgoing/NMKE.git", "6c81e45097c3e14d35360d852f9769da8abab81b"),
    "CaKE": ("https://github.com/zjunlp/CaKE.git", "df528e13fffbd2117e6041c129285e1e146933d2"),
}

# Created empty so SLURM log paths and result writers have somewhere to go.
EMPTY_DIRS = ["models", "results", "dashboard/logs",
              "experiments/run_experiment/logs", "experiments/causal_tracing/logs"]


def size(n):
    if n is None:
        return "?"
    if n >= 1e9:
        return f"{n / 1e9:.1f} GB"
    return f"{n / 1e6:.0f} MB" if n >= 1e6 else f"{max(n, 1000) / 1e3:.0f} KB"


def status():
    mark = lambda ok: "ok     " if ok else "missing"
    items = sources.catalog()
    print("components (--external, --venv)")
    for item in (i for i in items if i["kind"] == "component"):
        print(f"  {mark(item['installed'])} {item['label']:<32} {size(item['bytes']):>8}")
    print("datasets (--datasets NAME ...)")
    for item in (i for i in items if i["kind"] == "dataset"):
        state = "partial" if item["partial"] else mark(item["installed"])
        print(f"  {state} {item['name']:<32} {size(item['bytes']):>8}")
        for key, part in item["parts"].items():
            print(f"    {mark(part['installed'])} + {key}: {part['label']} ({size(part['bytes'])}, --parts {key})")
    print("models (--models NAME ...; --models main for the set experiments use)")
    for item in (i for i in items if i["kind"] == "model"):
        tags = [t for t, on in (("main", item["main"]), ("gated", item["gated"])) if on]
        print(f"  {mark(item['installed'])} {item['name']:<32} {size(item['bytes']):>8}"
              + (f"  ({', '.join(tags)})" if tags else ""))
    print("hardware")
    print(f"  {mark(shutil.which('nvidia-smi') is not None)} NVIDIA GPU (nvidia-smi)")
    slurm = shutil.which("sbatch") is not None
    print(f"  {'ok     ' if slurm else 'absent '} SLURM" + ("" if slurm else " (experiments run as local background jobs)"))
    print(f"\n{size(sources.disk_free_bytes())} free on this disk")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--status", action="store_true", help="show what is present and what is missing")
    parser.add_argument("--datasets", nargs="*", metavar="NAME", help="benchmarks to download; none listed means all")
    parser.add_argument("--parts", nargs="+", default=[], metavar="PART", help="optional dataset parts, e.g. train (UniEdit)")
    parser.add_argument("--models", nargs="+", metavar="NAME", help="model weights; 'main' for the main set")
    parser.add_argument("--external", action="store_true", help="clone EasyEdit at its pinned commit and apply patches/")
    parser.add_argument("--reference-repos", action="store_true", help="also clone WilKE, FiNE, NMKE and CaKE")
    parser.add_argument("--venv", action="store_true", help="create venvs/easyedit_venv and install requirements")
    parser.add_argument("--all", action="store_true", help="--external --datasets --venv (models stay opt-in)")
    args = parser.parse_args()

    chosen = [args.external, args.reference_repos, args.datasets is not None, args.models, args.venv, args.all]
    if not any(chosen):
        status()
        print("\nnothing selected; see --help")
        return
    for rel in EMPTY_DIRS:
        (ROOT / rel).mkdir(parents=True, exist_ok=True)

    try:
        if args.external or args.all:
            sources.install_easyedit()
        if args.reference_repos:
            for name, (url, commit) in REFERENCE_REPOS.items():
                sources.say(f"== {name}")
                sources.git_checkout_with_patches(url, commit, sources.EXTERNAL_DIR / name)
        if args.datasets is not None or args.all:
            available = sources.dataset_names()
            names = args.datasets or available
            unknown = [n for n in names if n not in available]
            if unknown:
                raise RuntimeError(f"unknown dataset(s) {', '.join(unknown)}; choose from: {', '.join(available)}")
            for name in names:
                sources.download_dataset(name, args.parts)
        if args.venv or args.all:
            sources.install_experiment_env()
        if args.models:
            names = ([m["name"] for m in models_reader.CATALOG if m.get("main")]
                     if [n.lower() for n in args.models] == ["main"] else args.models)
            for name in names:
                sources.download_model(name)
    except (RuntimeError, OSError, subprocess.CalledProcessError) as exc:
        print(f"\nFAILED: {exc}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\ninterrupted; rerun the same command to resume", file=sys.stderr)
        sys.exit(130)
    if args.status:
        status()


if __name__ == "__main__":
    main()
