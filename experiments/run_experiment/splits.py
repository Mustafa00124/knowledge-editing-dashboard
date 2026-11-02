"""The fixed dev/test split (splits/, built by scripts/make_splits.py).

Hyperparameter sweeps run on --split dev, main experiments on --split test.
A split file lists record indices into the runner's own loaded request list
(eval_utils.load_requests with no size limit): dev, demo (IKE's pool where
the dataset has no train file) and excluded (subjects that are dev or demo
elsewhere). Test is everything else. Sid's Dataset (a folder of records) has a split by
record id instead (splits/SidsDataset/records.json, built by
scripts/make_sids_split.py), so editing a record doesn't invalidate it. Kept free of torch so the dashboard
backend can read split sizes too.
"""
import hashlib
import json
import os

EXP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(EXP_DIR))
SPLITS_DIR = os.path.join(PROJECT_ROOT, "splits")
DATASETS_DIR = os.path.join(PROJECT_ROOT, "datasets")
CHOICES = ("test", "dev", "screen", "all")


SIDS_SPLIT = os.path.join(SPLITS_DIR, "SidsDataset", "records.json")


def is_sids(data_path):
    rel = os.path.relpath(os.path.abspath(data_path), DATASETS_DIR)
    return rel == "SidsDataset" or rel.startswith("SidsDataset" + os.sep)


def split_path(data_path):
    rel = os.path.relpath(os.path.abspath(data_path), DATASETS_DIR)
    if rel.startswith(".."):
        return None
    if is_sids(data_path):
        return SIDS_SPLIT
    return os.path.join(SPLITS_DIR, rel)


def load(data_path, verify=True):
    """The split file for a dataset file, or None if it has none. With
    `verify`, refuses a split built from different data: its indices would
    then point at the wrong records."""
    path = split_path(data_path)
    if not path or not os.path.exists(path):
        return None
    with open(path) as handle:
        info = json.load(handle)
    if verify and info.get("kind") != "ids":
        digest = hashlib.sha256()
        with open(data_path, "rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                digest.update(chunk)
        if digest.hexdigest() != info["sha256"]:
            raise ValueError(f"{data_path} has changed since its split was made; rerun scripts/make_splits.py")
    return info


def indices(info, split):
    total = info["requests"]
    if split == "all":
        return list(range(total))
    if split == "dev":
        return list(info["dev"])
    if split == "screen":
        raise ValueError("only Sid's Dataset has a screen split")
    held_out = set(info["dev"]) | set(info["demo"]) | set(info["excluded"])
    return [i for i in range(total) if i not in held_out]


def select(requests, data_path, split):
    """requests: the full, unsliced list from load_requests(data_path, None)."""
    if split == "all":
        return requests
    info = load(data_path)
    if info is None:
        raise ValueError(f"no dev/test split for {data_path}; run scripts/make_splits.py, "
                         "or pass --split all to use every record (never for reported results)")
    if info.get("kind") == "ids":
        return select_ids(requests, info, split)
    if info["requests"] != len(requests):
        raise ValueError(f"{data_path} loads {len(requests)} records but its split expects {info['requests']}")
    return [requests[i] for i in indices(info, split)]


def _record_id(request):
    return (request.get("sids") or {}).get("id")


def select_ids(requests, info, split):
    """A split by record id (Sid's Dataset): dev is the listed ids, screen
    a 10-edit subset of dev (one ABox fact per topic), test is everything
    not in dev or excluded."""
    ids = [_record_id(r) for r in requests]
    if None in ids:
        raise ValueError("a split by record id needs records with ids (Sid's Dataset)")
    dev, held_out = set(info["dev"]), set(info["dev"]) | set(info.get("excluded", []))
    unknown = sorted(dev - set(ids))
    if unknown:
        raise ValueError(f"dev records missing from the data: {unknown[:5]}; rerun scripts/make_sids_split.py")
    if split in ("dev", "screen"):
        wanted = dev if split == "dev" else set(info.get("screen") or [])
        if not wanted:
            raise ValueError("this split file has no screen; rerun scripts/make_sids_split.py")
        return [r for r, i in zip(requests, ids) if i in wanted]
    return [r for r, i in zip(requests, ids) if i not in held_out]


def demo_pool(requests, data_path):
    """IKE's demonstration records when the dataset has no train file: the
    split's demo portion, which is neither dev nor test."""
    info = load(data_path)
    if info is None or not info.get("demo"):
        return None
    return [requests[i] for i in info["demo"]]


def sizes(data_path):
    """{"dev": n, "test": n} without loading the data, or None."""
    info = load(data_path, verify=False)
    if info is None:
        return None
    out = {"dev": len(info["dev"]), "test": info["test_count"]}
    if info.get("screen"):
        out["screen"] = len(info["screen"])
    return out
