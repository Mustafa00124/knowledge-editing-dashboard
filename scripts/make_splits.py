#!/usr/bin/env python3
"""Build the fixed dev/test split for every runnable dataset subset.

Hyperparameter sweeps may only use dev records; main experiments only test
records. Records are read with the runner's own loaders (eval_utils), so an
index here is exactly the runner's view of a record. Output goes to
splits/<path under datasets/>, one file per subset, tracked in git so every
checkout uses the identical split.

Leakage rules:
  - Records are grouped by subject (their prompt when there is no subject),
    and a group is never split across dev and test.
  - A subject picked for dev or demo in any subset is excluded from test in
    every subset, so overlapping datasets (MQuAKE CF-3k v2 inside CF full,
    the zsRE family) cannot leak a dev fact into a test set.
  - Records CaKE has no training data for (MQuAKE) are excluded for every
    method, so all methods are scored on the same records.
  - Subsets with no matching train file get a separate "demo" portion,
    used only as IKE's demonstration pool, so IKE never draws
    demonstrations from the records it is evaluated on.

Sizes: 100 dev records per subset (and 100 demo where needed), at most a
quarter of the subset each, so test always keeps at least half.

Run with the experiment environment (it imports the runner's loaders):
    venvs/easyedit_venv/bin/python scripts/make_splits.py
Rerunning with unchanged data reproduces the same files.
"""
import hashlib
import json
import os
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "run_experiment"
SPLITS = ROOT / "splits"
DEV_SIZE = 100
DEMO_SIZE = 100
VERSION = 1

sys.path.insert(0, str(ROOT / "external" / "EasyEdit"))
sys.path.insert(0, str(EXP))


def group_key(request):
    key = request.get("subject") or request.get("prompt") or ""
    return " ".join(str(key).lower().split())


def train_counterpart(path):
    """Mirrors run_experiment.py's IKE rule: swap "test" for "train"."""
    candidate = path.replace("test", "train")
    return candidate if candidate != path and os.path.exists(candidate) else None


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def runnable_subsets():
    cfg = json.loads((EXP / "dashboard.json").read_text())
    field = next(f for f in cfg["fields"] if f.get("control") == "dataset")
    paths = []
    for bench in field["benchmarks"]:
        for subset in bench["subsets"]:
            if subset.get("available") is False:
                continue
            path = subset["value"].replace("${PROJECT_ROOT}", str(ROOT))
            if os.path.exists(path):
                paths.append(path)
            else:
                print(f"skip (not downloaded): {os.path.relpath(path, ROOT)}")
    return sorted(set(paths))


def main():
    from eval_utils import load_requests
    import cake

    global_dev, global_demo = set(), set()
    for path in runnable_subsets():
        rel = os.path.relpath(path, ROOT / "datasets")
        requests = load_requests(path, None)
        keys = [group_key(r) for r in requests]
        groups = {}
        for index, key in enumerate(keys):
            groups.setdefault(key, []).append(index)

        n = len(requests)
        dev_quota = min(DEV_SIZE, n // 4)
        needs_demo = train_counterpart(path) is None
        demo_quota = min(DEMO_SIZE, n // 4) if needs_demo else 0

        dev, demo, excluded = [], [], []

        def take(bucket, quota, members):
            if len(bucket) + len(members) <= quota:
                bucket.extend(members)
                return True
            return False

        # Facts already dev (or demo) in another subset stay on that side here.
        for key, members in groups.items():
            if key in global_dev:
                (dev if len(dev) + len(members) <= dev_quota else excluded).extend(members)
            elif key in global_demo:
                target = demo if needs_demo and len(demo) + len(members) <= demo_quota else excluded
                target.extend(members)

        # Fill the rest with fresh subjects in a fixed, per-subset order.
        fresh = [k for k in groups if k not in global_dev and k not in global_demo]
        random.Random(f"ke-split-v{VERSION}:{rel}").shuffle(fresh)
        for key in fresh:
            members = groups[key]
            if len(dev) < dev_quota and take(dev, dev_quota, members):
                global_dev.add(key)
            elif needs_demo and len(demo) < demo_quota and take(demo, demo_quota, members):
                global_demo.add(key)

        # Every method must be scored on the same records. CaKE can edit only
        # records its release has training data for, so records it lacks are
        # excluded here for everyone rather than skipped by CaKE alone.
        cake_table = cake.training_data(path)
        if cake_table is not None:
            side = set(dev) | set(demo) | set(excluded)
            lacking = [i for i, r in enumerate(requests) if i not in side
                       and cake._key(r["subject"], r["prompt"], r["target_new"]) not in cake_table]
            excluded.extend(lacking)
            if lacking:
                print(f"{rel}: excluded {len(lacking)} records CaKE has no training data for")

        chosen = set(dev) | set(demo) | set(excluded)
        test_count = n - len(chosen)
        out = SPLITS / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({
            "version": VERSION,
            "data": os.path.relpath(path, ROOT),
            "sha256": sha256(path),
            "requests": n,
            "group_by": "subject, or prompt when a record has none",
            "demo_source": "demo" if needs_demo else os.path.relpath(train_counterpart(path), ROOT),
            "dev": sorted(dev),
            "demo": sorted(demo),
            "excluded": sorted(excluded),
            "test_count": test_count,
        }, indent=1) + "\n")
        print(f"{rel}: {n} records -> dev {len(dev)}, demo {len(demo)}, excluded {len(excluded)}, test {test_count}")

    # Second pass: a subject chosen for dev/demo by a later subset may sit in
    # the test side of an earlier one. Move those records to "excluded".
    for split_file in sorted(SPLITS.rglob("*.json")):
        info = json.loads(split_file.read_text())
        path = ROOT / info["data"]
        requests = load_requests(str(path), None)
        side = set(info["dev"]) | set(info["demo"]) | set(info["excluded"])
        leaked = [i for i, r in enumerate(requests)
                  if i not in side and group_key(r) in (global_dev | global_demo)]
        if leaked:
            info["excluded"] = sorted(set(info["excluded"]) | set(leaked))
            info["test_count"] -= len(leaked)
            split_file.write_text(json.dumps(info, indent=1) + "\n")
            print(f"{info['data']}: moved {len(leaked)} test records sharing a dev/demo subject to excluded")


if __name__ == "__main__":
    main()
