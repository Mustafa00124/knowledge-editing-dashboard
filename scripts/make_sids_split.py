#!/usr/bin/env python3
"""Build Sid's Dataset dev/test split: splits/SidsDataset/records.json.

Unlike the other datasets' splits (record indices plus a hash of one data
file), this one lists record ids, so editing a record does not invalidate
it. Dev is 40 replace edits, picked per topic so tuning sees every topic and
box:
  - ABox: 2 per topic, one the model likely stores (derivability
    very_unlikely/unlikely) and one it likely derives (likely/very_likely);
  - TBox: 1 per topic;
  - RBox: 1 per topic, with the edited property rotated across topics so the
    10 dev RBox edits cover all seven properties at least once.
Screen is 10 of those dev edits, one ABox fact per topic (stored and
derived alternating over the topics, so 5 of each), for the wide first
pass of tuning, which tries many settings on few edits.
Each dev record's delete (<topic>-delete-NNNN removes the same fact) is
excluded from test: it was seen during tuning. Inserts are all test.

Random within each cell, with a fixed seed, so a rerun reproduces the file:
    python scripts/make_sids_split.py
"""
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "datasets" / "SidsDataset" / "records"
OUT = ROOT / "splits" / "SidsDataset" / "records.json"
SEED = 0
VERSION = 1
STORED = ("very_unlikely", "unlikely")
DERIVED = ("likely", "very_likely")
PROPERTIES = ("functional", "transitive", "symmetric", "asymmetric", "inverse", "subproperty", "chain")


def rbox_property(rec):
    """The property an RBox edit changes, from its axiom or, failing that, its statement."""
    axiom = rec["edit"].get("axiom") or ""
    for mark, name in (("∘", "chain"), ("Func", "functional"), ("Trans", "transitive"), ("Asym", "asymmetric"),
                       ("Sym", "symmetric"), ("Inv", "inverse"), ("⁻", "inverse"), ("⊑", "subproperty"),
                       ("⋢", "subproperty")):
        if mark in axiom:
            return name
    text = rec["edit"]["statement"].lower()
    for word, name in (("subproperty", "subproperty"), ("asymmetric", "asymmetric"), ("symmetric", "symmetric"),
                       ("transitive", "transitive"), ("functional", "functional"), ("inverse", "inverse"),
                       ("chain", "chain")):
        if word in text:
            return name
    raise ValueError(f"{rec['id']}: can't tell which property the RBox edit changes")


def assign_properties(rbox_by_topic, rng):
    """topic -> property, covering every property; random among the coverings."""
    topics = sorted(rbox_by_topic)
    for _ in range(10000):
        order = topics[:]
        rng.shuffle(order)
        chosen, covered = {}, set()
        for i, topic in enumerate(order):
            have = sorted({rbox_property(r) for r in rbox_by_topic[topic]})
            missing = [p for p in have if p not in covered]
            # Fill a missing property while enough topics remain to finish; else any.
            pick = rng.choice(missing) if missing else rng.choice(have)
            chosen[topic] = pick
            covered.add(pick)
        if covered >= set(PROPERTIES):
            return chosen
    raise SystemExit("no assignment covers every RBox property")


def build():
    rng = random.Random(SEED)
    recs = [json.loads(p.read_text()) for p in sorted(RECORDS.glob("*/replace/*.json"))]
    cells = defaultdict(list)
    for r in recs:
        if r["box"] == "abox":
            cells[(r["topic"], "abox", "stored" if r["derivability"] in STORED else "derived")].append(r)
        else:
            cells[(r["topic"], r["box"])].append(r)
    topics = sorted({r["topic"] for r in recs})
    dev = []
    for t in topics:
        for key in ((t, "abox", "stored"), (t, "abox", "derived"), (t, "tbox")):
            if not cells[key]:
                raise SystemExit(f"no replace record for {key}")
            dev.append(rng.choice(sorted(cells[key], key=lambda r: r["id"])))
    props = assign_properties({t: cells[(t, "rbox")] for t in topics}, rng)
    for t in topics:
        pool = sorted((r for r in cells[(t, "rbox")] if rbox_property(r) == props[t]), key=lambda r: r["id"])
        dev.append(rng.choice(pool))
    dev_ids = sorted(r["id"] for r in dev)
    excluded = sorted(i.replace("-replace-", "-delete-") for i in dev_ids)
    all_ids = sorted(json.loads(p.read_text())["id"] for p in RECORDS.glob("*/*/*.json"))
    missing = [i for i in excluded if i not in all_ids]
    if missing:
        raise SystemExit(f"dev records with no delete: {missing}")
    rbox = {r["id"]: rbox_property(r) for r in dev if r["box"] == "rbox"}
    # One ABox edit per topic for the screen, alternating stored and derived.
    screen = []
    for i, t in enumerate(topics):
        kind = STORED if i % 2 == 0 else DERIVED
        screen += [r["id"] for r in dev if r["topic"] == t and r["box"] == "abox" and r["derivability"] in kind]
    return {
        "version": VERSION, "kind": "ids", "seed": SEED,
        "note": "Sid's Dataset: 40 replace edits for tuning (scripts/make_sids_split.py); their deletes are "
                "held out of test; everything else is test",
        "dev": dev_ids, "screen": sorted(screen), "excluded": excluded,
        "dev_rbox_properties": dict(sorted(rbox.items())),
        "test_count": len(all_ids) - len(dev_ids) - len(excluded),
    }


if __name__ == "__main__":
    info = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(info, indent=1, ensure_ascii=False) + "\n")
    print(f"{OUT.relative_to(ROOT)}: {len(info['dev'])} dev ({len(info['screen'])} screen), {len(info['excluded'])} excluded, "
          f"{info['test_count']} test")
    print("RBox dev properties:", sorted(set(info["dev_rbox_properties"].values())))
    sys.exit(0)
