#!/usr/bin/env python3
"""Sanity-check formal files against their records, without HermiT: syntax,
entity keys, gold answers that map to an entity, world ids, query indexes.

    python datasets/SidsDataset/owl/encode_check.py                  # every formal file
    python datasets/SidsDataset/owl/encode_check.py --topic geography
    python datasets/SidsDataset/owl/encode_check.py geography-replace-0001 ...

Standard library only. Exits 1 if any file has a problem.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import dlsyntax as D  # noqa: E402
import json  # noqa: E402


def main(argv):
    topic = argv[argv.index('--topic') + 1] if '--topic' in argv else None
    ids = [a for i, a in enumerate(argv) if not a.startswith('--') and (i == 0 or argv[i - 1] != '--topic')]
    files = sorted(D.FORMAL_DIR.glob('*.json'))
    if ids:
        files = [D.FORMAL_DIR / f'{i}.json' for i in ids]
    elif topic:
        files = [f for f in files if f.stem.startswith(topic + '-')]
    # Every relation RELATIONS.md names, including those only named inside a
    # tag (inverse:S, chain targets), as compiled by relations.py.
    rels = set(json.loads((HERE / 'relations.json').read_text())['relations'])
    bad = 0
    for f in files:
        try:
            probs = D.check_formal(D.load_formal(f.stem), D.load_record(f.stem), rels)
        except Exception as e:
            probs = [f'{type(e).__name__}: {e}']
        if probs:
            bad += 1
            print(f'{f.stem}:')
            for p in probs:
                print(f'  - {p}')
    print(f'{len(files)} formal files, {bad} with problems')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
