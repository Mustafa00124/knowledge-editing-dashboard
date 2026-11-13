#!/usr/bin/env python3
"""Re-check every infini-gram count stored in Sid's Dataset evidence.

The records' evidence (README, Evidence) cites corpus counts from the public
infini-gram API. Writers can only copy numbers the API gave them, but a
re-check catches typos, numbers carried over from an older query, and
anything invented. This script collects every (index, query, count) source
in records/, dev/ and examples/, asks the API once per distinct query (one
request every --pause seconds, results cached in staging/count_cache.json so
a rerun only asks what is new), and lists the counts that don't match.

Exact-phrase counts must match within --tolerance (default 2%). AND queries
sample, so they are only reported when the stored count is non-zero and the
re-check is zero, or the other way round.

The script stops at the first refusal (HTTP 403 or 429) instead of retrying:
when the API blocks this machine, wait and run it again later.

    python3 datasets/SidsDataset/check_counts.py [--pause 1.5] [--limit N] [paths...]
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import ig_count as IG

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / 'staging' / 'count_cache.json'
API = 'https://api.infini-gram.io/'
DEFAULT_INDEX = 'v4_dolma-v1_7_llama'


def sources(paths):
    """(record id, fact, index, query, stored count) for every infini-gram source."""
    for path in paths:
        try:
            rec = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        for fact, ev in (rec.get('evidence') or {}).items():
            for s in (ev or {}).get('sources') or []:
                if s.get('kind') == 'infini-gram' and isinstance(s.get('count'), int) and s.get('query'):
                    yield rec.get('id'), fact, s.get('index') or DEFAULT_INDEX, s['query'], s['count']


def ask(index, query):
    body = {'index': index, 'query_type': 'count', 'query': query}
    if ' AND ' in query or ' OR ' in query:
        body['max_clause_freq'] = 500000
    req = urllib.request.Request(API, data=json.dumps(body).encode(), method='POST',
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=60) as res:
        out = json.loads(res.read())
    if 'count' not in out:
        raise ValueError(out.get('error') or out)
    return out['count']


def mismatch(query, stored, got, tol):
    if ' AND ' in query or ' OR ' in query:
        return (stored == 0) != (got == 0)
    return abs(stored - got) > max(2, tol * max(stored, got))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('paths', nargs='*')
    ap.add_argument('--pause', type=float, default=1.5, help='seconds between requests')
    ap.add_argument('--limit', type=int, default=0, help='ask at most this many new queries')
    ap.add_argument('--tolerance', type=float, default=0.02)
    args = ap.parse_args(argv)
    paths = [Path(p).resolve() for p in args.paths] or sorted(
        p for d in ('records', 'dev', 'examples') for p in (ROOT / d).rglob('*.json'))
    cache = {k: v for k, v in IG._load_cache().items()}
    rows = list(sources(paths))
    todo = sorted({f'{i}\t{q}' for _, _, i, q, _ in rows} - set(cache))
    print(f'{len(rows)} counts in {len(paths)} files, {len(todo)} queries not yet checked')
    asked = 0
    for key in todo:
        if args.limit and asked >= args.limit:
            break
        index, query = key.split('\t', 1)
        try:
            cache[key] = IG.count(query, index)    # shared cache, lock and pace (ig_count.py)
        except IG.Blocked as b:
            print(f'stopped: the API refused; blocked until {b}; run again later')
            break
        except urllib.error.HTTPError as e:
            cache[key] = f'error: HTTP {e.code}'
        except (urllib.error.URLError, ValueError, TimeoutError) as e:
            cache[key] = f'error: {e}'
        asked += 1
        if asked % 50 == 0:
            print(f'  {asked}/{len(todo)} asked')
        if args.pause > IG.MIN_INTERVAL:
            time.sleep(args.pause - IG.MIN_INTERVAL)
    cache = {**cache, **IG._load_cache()}
    bad, unchecked = [], 0
    for rid, fact, index, query, stored in rows:
        got = cache.get(f'{index}\t{query}')
        if not isinstance(got, int):
            unchecked += 1
        elif mismatch(query, stored, got, args.tolerance):
            bad.append(f'{rid}: {query!r} stored {stored}, API {got} (fact: {fact})')
    for line in bad:
        print(line)
    print(f'{len(rows) - unchecked} checked, {len(bad)} mismatched, {unchecked} not checked yet')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
