"""Reads benchmark data straight from datasets/ — the one folder all
benchmarks (DUnE, KnowEdit, and anything added later) are kept under."""
import json
import re
from pathlib import Path

import config
import sources

IGNORE_DIRS = {".git", ".git-upstream", ".cache", "__pycache__"}


def list_benchmarks():
    """Benchmarks ready to browse. A downloadable one (it has a SOURCE.json)
    only counts once scripts/setup.py has fetched and built all of it;
    until then the folder holds just its manifest. Our own benchmarks have
    no manifest and are always listed."""
    if not config.DATASETS_DIR.exists():
        return []
    out = []
    for d in sorted(config.DATASETS_DIR.iterdir()):
        if not d.is_dir() or d.name in IGNORE_DIRS:
            continue
        if (d / "SOURCE.json").exists() and not sources.dataset_status(d.name)["installed"]:
            continue
        description = ""
        readme = d / "README.md"
        if readme.exists():
            lines = readme.read_text(errors="replace").splitlines()
            if lines and lines[0].strip() == "---":
                closing = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), None)
                if closing is not None:
                    lines = lines[closing + 1:]
            for line in lines:
                line = re.sub(r"<[^>]+>", "", line).strip().lstrip("#").strip()
                if line:
                    description = line
                    break
        n_files = sum(
            1
            for p in d.rglob("*")
            if p.is_file() and p.suffix in (".json", ".jsonl") and not any(part in IGNORE_DIRS for part in p.parts)
        )
        out.append({"name": d.name, "description": description, "n_files": n_files})
    return out


def _resolve(benchmark, rel_path=None):
    root = config.DATASETS_DIR.resolve()
    base = (config.DATASETS_DIR / benchmark).resolve()
    if not str(base).startswith(str(root)):
        raise ValueError("bad benchmark")
    if rel_path is None:
        return base
    target = (base / rel_path).resolve()
    if not str(target).startswith(str(base)):
        raise ValueError("bad path")
    return target


def list_files(benchmark):
    base = _resolve(benchmark)
    if not base.exists():
        return []
    out = []
    for p in sorted(base.rglob("*")):
        if p.is_file() and p.suffix in (".json", ".jsonl") and not any(part in IGNORE_DIRS for part in p.parts):
            out.append({"path": str(p.relative_to(base)), "size_bytes": p.stat().st_size})
    return out


# Benchmark files are static within a session and some are a few MB
# (parsing wiki_recent's 1266 records isn't free) - cache the parsed
# contents per path so paging through a file only re-reads/re-parses it
# when it's actually changed on disk.
_FILE_CACHE = {}


def _load_json(path):
    stat = path.stat()
    cache_key = (stat.st_mtime, stat.st_size)
    cached = _FILE_CACHE.get(path)
    if cached and cached[0] == cache_key:
        return cached[1]
    data = json.loads(path.read_text(errors="replace"))
    _FILE_CACHE[path] = (cache_key, data)
    return data


def preview(benchmark, rel_path, offset=0, limit=20, key=None):
    path = _resolve(benchmark, rel_path)
    if not path.exists():
        return {"error": "not found", "total": 0, "offset": offset, "limit": limit, "records": []}

    if path.suffix == ".jsonl":
        records = []
        total = 0
        with path.open(errors="replace") as f:
            for i, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                total += 1
                if offset <= i < offset + limit:
                    records.append(json.loads(line))
        return {"total": total, "offset": offset, "limit": limit, "records": records}

    data = _load_json(path)

    # e.g. trivia_qa_test.json: {"success": [...], "locality": [...]} -
    # two unrelated-length lists under named keys, not one shape. `key`
    # picks which list is actually being paged over.
    if key is not None and isinstance(data, dict) and isinstance(data.get(key), list):
        data = data[key]

    if isinstance(data, list):
        return {"total": len(data), "offset": offset, "limit": limit, "records": data[offset : offset + limit]}

    if isinstance(data, dict):
        # e.g. DUnE's new_info.json: {"edits": [...200], "test_inputs": [...200]}
        # - parallel arrays, index i together forming one record. Zip them
        # rather than returning the whole file as a single blob.
        list_keys = [k for k, v in data.items() if isinstance(v, list)]
        lengths = {len(data[k]) for k in list_keys}
        if list_keys and len(lengths) == 1 and next(iter(lengths)) > 0:
            n = next(iter(lengths))
            records = [{k: data[k][i] for k in list_keys} for i in range(n)]
            return {"total": n, "offset": offset, "limit": limit, "records": records[offset : offset + limit]}

        # UniEdit domain files are mappings of sample_id -> sample. Page over
        # those entries instead of returning the multi-megabyte mapping as one
        # record. Preserve each source key so the UI exposes the sample ID.
        if data and all(isinstance(value, dict) for value in data.values()):
            items = list(data.items())
            records = [
                {"sample_id": sample_id, **sample}
                for sample_id, sample in items[offset : offset + limit]
            ]
            return {"total": len(items), "offset": offset, "limit": limit, "records": records}

    return {"total": 1, "offset": 0, "limit": 1, "records": [data]}


def record_count(abs_path):
    """How many records a dataset file holds, for a path under datasets/.

    Same shape handling as preview() because it is preview() - the drawer
    needs this to know what "full" means for the dataset you picked, and the
    two must agree about what counts as a record. Approximate for the
    benchmarks whose loader expands or filters records (see eval_utils'
    load_*_requests); the runner reports the exact number it loaded.
    """
    root = config.DATASETS_DIR.resolve()
    path = Path(abs_path).resolve()
    if not str(path).startswith(str(root) + "/") or not path.is_file():
        raise ValueError("path is not a file under datasets/")
    relative = path.relative_to(root)
    benchmark = relative.parts[0]
    return preview(benchmark, str(Path(*relative.parts[1:])), offset=0, limit=0)["total"]
