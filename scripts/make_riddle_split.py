#!/usr/bin/env python3
"""The fixed dev/test split for AlteredRiddles (datasets/AlteredRiddles/benchmark.jsonl).

make_splits.py builds splits through the editing runner's loaders, and the
runner cannot load the riddles yet, so this file does the same job for them
alone, with the same rules: 100 dev and 100 demo records, grouped so that
every altered variant of one original riddle lands on the same side (the
variants share most of their text, so splitting them would leak), in a fixed
seeded order. Indices are line numbers in benchmark.jsonl: when the runner
gains a riddle loader, it must keep one request per line, in file order, or
this split's sha256/count check will refuse it.

    python3 scripts/make_riddle_split.py
"""
import json
import os
import random
from pathlib import Path

import make_splits as ms

PATH = ms.ROOT / "datasets" / "AlteredRiddles" / "benchmark.jsonl"


def main():
    # split on "\n" only: splitlines() also breaks on U+2028 inside riddle text
    rows = [json.loads(line) for line in PATH.read_text().split("\n") if line.strip()]
    groups = {}
    for index, row in enumerate(rows):
        groups.setdefault(row["original_riddle"], []).append(index)
    rel = os.path.relpath(PATH, ms.ROOT / "datasets")
    keys = list(groups)
    random.Random(f"ke-split-v{ms.VERSION}:{rel}").shuffle(keys)
    dev, demo = [], []
    for key in keys:
        members = groups[key]
        if len(dev) + len(members) <= ms.DEV_SIZE:
            dev.extend(members)
        elif len(demo) + len(members) <= ms.DEMO_SIZE:
            demo.extend(members)
    out = ms.SPLITS / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "version": ms.VERSION,
        "data": os.path.relpath(PATH, ms.ROOT),
        "sha256": ms.sha256(PATH),
        "requests": len(rows),
        "group_by": "original riddle (all its altered variants together)",
        "demo_source": "demo",
        "dev": sorted(dev),
        "demo": sorted(demo),
        "excluded": [],
    }, indent=1) + "\n")
    print(f"{rel}: {len(rows)} records, dev {len(dev)}, demo {len(demo)}, test {len(rows) - len(dev) - len(demo)}")


if __name__ == "__main__":
    main()
