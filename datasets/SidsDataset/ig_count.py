#!/usr/bin/env python3
"""Shared infini-gram counter for everyone writing Sid's Dataset evidence.

Agents and scripts call this instead of curl, so that however many of them
run at once, the public API sees one polite client:

  - one shared cache (staging/count_cache.json, the one check_counts.py
    uses): a phrase already counted is answered without a request;
  - one request at a time across all processes (a lock file), at least
    MIN_INTERVAL seconds apart;
  - on HTTP 403 or 429 a shared "blocked until" marker
    (staging/count_blocked_until) stops every caller for BLOCK_MINUTES, and
    the call reports "blocked" instead of retrying. A refusal is never a
    zero count.

    python3 datasets/SidsDataset/ig_count.py "capital of Italy is Rome" ["Rome AND Lazio" ...]
    python3 datasets/SidsDataset/ig_count.py --index v4_rpj_llama_s4 "..."

Prints one JSON line per query: {"query", "index", "count"} or
{"query", "index", "error": "blocked until ..."}. Exit code 2 when blocked.
AND/OR queries get max_clause_freq 500000 (README, Evidence).
"""
import argparse
import fcntl
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STAGING = ROOT / 'staging'
CACHE = STAGING / 'count_cache.json'
LOCK = STAGING / 'count.lock'
BLOCKED = STAGING / 'count_blocked_until'
API = 'https://api.infini-gram.io/'
DEFAULT_INDEX = 'v4_dolma-v1_7_llama'
MIN_INTERVAL = 2.0
BLOCK_MINUTES = 15


class Blocked(Exception):
    pass


def _blocked_until():
    try:
        return float(BLOCKED.read_text().strip())
    except (OSError, ValueError):
        return 0.0


def _load_cache():
    try:
        return json.loads(CACHE.read_text())
    except (OSError, ValueError):
        return {}


def _save_cache(cache):
    tmp = CACHE.with_suffix('.tmp')
    tmp.write_text(json.dumps(cache, indent=0, ensure_ascii=False))
    tmp.replace(CACHE)


def _request(index, query):
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


def count(query, index=DEFAULT_INDEX):
    """The corpus count of `query`: from the shared cache, else one polite
    request. Raises Blocked while the API refuses this machine."""
    key = f'{index}\t{query}'
    hit = _load_cache().get(key)
    if isinstance(hit, int):
        return hit
    STAGING.mkdir(exist_ok=True)
    with open(LOCK, 'a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)    # one request at a time, all processes
        try:
            until = _blocked_until()
            if until > time.time():
                raise Blocked(time.strftime('%H:%M', time.localtime(until)))
            cache = _load_cache()
            if isinstance(cache.get(key), int):
                return cache[key]
            lock.seek(0)
            try:
                last = float(lock.read().strip() or 0)
            except ValueError:
                last = 0.0
            wait = last + MIN_INTERVAL - time.time()
            if wait > 0:
                time.sleep(wait)
            try:
                value = _request(index, query)
            except urllib.error.HTTPError as e:
                if e.code in (403, 429):
                    until = time.time() + BLOCK_MINUTES * 60
                    BLOCKED.write_text(str(until))
                    raise Blocked(time.strftime('%H:%M', time.localtime(until))) from None
                raise
            finally:
                lock.seek(0)
                lock.truncate()
                lock.write(str(time.time()))
                lock.flush()
            cache = _load_cache()
            cache[key] = value
            _save_cache(cache)
            return value
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('queries', nargs='+')
    ap.add_argument('--index', default=DEFAULT_INDEX)
    args = ap.parse_args(argv)
    code = 0
    for q in args.queries:
        try:
            print(json.dumps({'query': q, 'index': args.index, 'count': count(q, args.index)}, ensure_ascii=False))
        except Blocked as b:
            print(json.dumps({'query': q, 'index': args.index,
                              'error': f'blocked until {b}: do not retry; use cached or real earlier counts'}))
            code = 2
            break
        except (urllib.error.URLError, ValueError, TimeoutError) as e:
            print(json.dumps({'query': q, 'index': args.index, 'error': str(e)}))
            code = 1
    return code


if __name__ == '__main__':
    sys.exit(main())
