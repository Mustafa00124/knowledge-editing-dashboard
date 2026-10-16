"""Shared helpers for linking Sid's Dataset to Wikidata.

Two services: Wikidata's own search API (names to IDs) and QLever's Wikidata
SPARQL endpoint (everything else; it has no label service, so labels are
fetched explicitly). Every response is cached on disk under cache/, keyed by
the request, so reruns don't hit either service again. Delete cache/ to
refresh. Standard library only.
"""
import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATASET = HERE.parent
sys.path.insert(0, str(DATASET))

CACHE = HERE / 'cache'
QLEVER = 'https://qlever.dev/api/wikidata'
SEARCH = 'https://www.wikidata.org/w/api.php'
USER_AGENT = "SidsDataset-wikidata/0.1 (knowledge-editing research; msiddiqui146@usf.edu)"
PREFIXES = """PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX p: <http://www.wikidata.org/prop/>
PREFIX ps: <http://www.wikidata.org/prop/statement/>
PREFIX pq: <http://www.wikidata.org/prop/qualifier/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX schema: <http://schema.org/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX wikibase: <http://wikiba.se/ontology#>
"""


def _cached(kind, key, fetch):
    path = CACHE / kind / (hashlib.sha1(key.encode()).hexdigest() + '.json')
    if path.exists():
        return json.loads(path.read_text())
    data = fetch()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({'key': key, 'data': data}, ensure_ascii=False))
    return {'key': key, 'data': data}


def _get(url, data=None, accept='application/json', tries=6):
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers={'User-Agent': USER_AGENT, 'Accept': accept})
            with urllib.request.urlopen(req, timeout=180) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors='replace')
            # QLever answers a query that timed out with 429 too; retrying won't help.
            if attempt == tries - 1 or e.code not in (429, 500, 502, 503, 504) or 'timed out' in body:
                raise RuntimeError(f'{e.code} from {url}: {body[:300]}') from e
            # Rate limited or busy: honour Retry-After, else back off.
            time.sleep(float(e.headers.get('Retry-After') or 0) or 15 * (attempt + 1))
        except Exception:
            if attempt == tries - 1:
                raise
            time.sleep(2 * (attempt + 1))


def search(text, kind='item', limit=7):
    """Wikidata's own name search: [{id, label, description, aliases}]."""
    params = {'action': 'wbsearchentities', 'search': text, 'language': 'en', 'uselang': 'en',
              'type': kind, 'limit': limit, 'format': 'json'}
    url = SEARCH + '?' + urllib.parse.urlencode(params)

    def fetch():
        time.sleep(0.2)  # be polite to the public API
        return [{'id': x['id'], 'label': x.get('label'), 'description': x.get('description'),
                 'aliases': x.get('aliases') or ([x['match']['text']] if x.get('match', {}).get('type') == 'alias' else [])}
                for x in _get(url).get('search', [])]
    return _cached('search', f'{kind}:{limit}:{text}', fetch)['data']


def sparql(query):
    """Rows of a QLever SELECT, as dicts of plain strings (IRIs shortened to their last segment)."""
    full = PREFIXES + query

    def fetch():
        time.sleep(1)  # QLever's public endpoint rate-limits bursts
        data = _get(QLEVER, urllib.parse.urlencode({'query': full}).encode(), 'application/sparql-results+json')
        return [{k: v['value'].rsplit('/', 1)[-1] if v['type'] == 'uri' else v['value'] for k, v in b.items()}
                for b in data['results']['bindings']]
    return _cached('sparql', full, fetch)['data']


def values(ids, var='x', prefix='wd'):
    return f"VALUES ?{var} {{ {' '.join(f'{prefix}:{i}' for i in ids)} }}"


def chunks(seq, n):
    seq = list(seq)
    for i in range(0, len(seq), n):
        yield seq[i:i + n]
