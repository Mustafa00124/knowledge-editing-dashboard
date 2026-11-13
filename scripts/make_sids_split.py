#!/usr/bin/env python3
"""Build Sid's Dataset dev/test split: splits/SidsDataset/records.json.

Since 2026-11-11 the two splits are separate folders of separate records
(datasets/SidsDataset/README.md, Shape per topic):
  - dev: every record under datasets/SidsDataset/dev/ (120 records, 12 per
    topic, ids <topic>-<operation>-dNNN), only for hyperparameter tuning;
  - screen: 10 of those, the first ABox revision record of each topic, for
    the wide first pass of tuning, which tries many settings on few edits;
  - test: every record under datasets/SidsDataset/records/ (the main split).
They share no edited fact or subject (validate.py dev checks), so nothing is
held out of test any more.

The file lists record ids, so editing a record does not invalidate it:
    python scripts/make_sids_split.py
Tuning runs use --data_path datasets/SidsDataset/dev --split dev (or
screen); main runs --data_path datasets/SidsDataset/records --split test.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "datasets" / "SidsDataset"
OUT = ROOT / "splits" / "SidsDataset" / "records.json"
VERSION = 2


def load(folder):
    return [json.loads(p.read_text()) for p in sorted((DATASET / folder).glob("*/*/*.json"))]


def build():
    dev = load("dev")
    test = load("records")
    screen = []
    for topic in sorted({r["topic"] for r in dev}):
        revisions = sorted(r["id"] for r in dev
                           if r["topic"] == topic and r["edit_operation"] == "replace" and r["box"] == "abox")
        if revisions:
            screen.append(revisions[0])
    return {
        "version": VERSION, "kind": "ids",
        "note": "Sid's Dataset: dev = every record in dev/ (tuning only), screen = the first dev ABox revision per "
                "topic, test = every record in records/ (scripts/make_sids_split.py)",
        "dev": sorted(r["id"] for r in dev), "screen": screen, "excluded": [],
        "test_count": len(test),
    }


if __name__ == "__main__":
    info = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(info, indent=1, ensure_ascii=False) + "\n")
    print(f"{OUT.relative_to(ROOT)}: {len(info['dev'])} dev ({len(info['screen'])} screen), {info['test_count']} test")
