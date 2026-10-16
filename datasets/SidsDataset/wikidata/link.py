#!/usr/bin/env python3
"""Link Sid's Dataset's entities and relations to Wikidata (first pass, automatic).

Entities: every edit subject, object and old object in the real ABox and TBox
records (fictional inserts and RBox edits name no real entities). Each string
is searched with Wikidata's name search; a candidate whose label or alias
matches the string is an exact match, and QLever supplies each candidate's
sitelinks to rank them. Status per string:

    linked      one exact match, or one that dominates the rest (5x the sitelinks)
    ambiguous   several exact matches, none dominant: needs a person
    fuzzy       no exact match; the search's best guess is kept for review
    value       looks like a value (number, duration, yes/no, direction), not an entity
    not_found   no candidates at all

Relations: candidate Wikidata properties for every relation, from its name and
its "Reads as" text in RELATIONS.md, for the curated relation_map.json.

    python datasets/SidsDataset/wikidata/link.py
Writes entity_links.json and relation_candidates.json beside this script.
"""
import glob
import json
import re
from collections import defaultdict

from wd import DATASET, HERE, chunks, search, sparql, values

VALUE_WORDS = {'yes', 'no', 'increase', 'decrease', 'increases', 'decreases', 'rises', 'falls', 'higher', 'lower',
               'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'twelve', 'none',
               'true', 'false', 'before', 'after', 'capital', 'lowercase'}
DOMINANT = 5


def load_records():
    return [json.loads(open(p).read()) for p in sorted(glob.glob(str(DATASET / 'records/*/*/*.json')))]


def reads_as():
    """{relation: its "Reads as" text} from RELATIONS.md's tables."""
    out = {}
    for line in (DATASET / 'RELATIONS.md').read_text().splitlines():
        if line.startswith('| `'):
            cells = [c.strip() for c in line.strip('|').split('|')]
            out.setdefault(cells[0].strip('`'), cells[1])
    return out


def bare(text):
    return re.sub(r'^(the|a|an)\s+', '', text.strip().rstrip('.').strip(), flags=re.I).casefold()


def kind_of(text):
    t = bare(text)
    if re.search(r'\d', t) or t in VALUE_WORDS or re.fullmatch(r'(\w+ )?(years?|days?|months?|hours?|percent)', t):
        return 'value'
    if len(t.split()) > 6 or re.search(r'\b(that|which|who|whose|when)\b', t):
        return 'description'
    return 'name'


def mentions(recs):
    """{text: [record_id/field, ...]} for every entity slot of a real ABox/TBox edit."""
    out = defaultdict(list)
    for r in recs:
        if r['box'] == 'rbox' or r.get('reality') == 'fictional' or r['edit'].get('fixture'):
            continue
        for field in ('subject', 'object', 'old_object'):
            v = r['edit'].get(field)
            if isinstance(v, str) and v.strip():
                out[v.strip()].append(f"{r['id']}/{field}")
    return out


def sitelinks(ids):
    out = {}
    for batch in chunks(sorted(set(ids)), 200):
        for row in sparql(f"SELECT ?x ?s WHERE {{ {values(batch)} ?x wikibase:sitelinks ?s }}"):
            out[row['x']] = int(row['s'])
    return out


def link_entities(recs):
    found = mentions(recs)
    results, all_ids = {}, set()
    for text in sorted(found):
        cands = search(text)
        if bare(text) != text.casefold():
            seen = {c['id'] for c in cands}
            cands += [c for c in search(re.sub(r'^(the|a|an)\s+', '', text, flags=re.I)) if c['id'] not in seen]
        cands = [c for c in cands if 'disambiguation page' not in (c.get('description') or '')]
        results[text] = cands
        all_ids |= {c['id'] for c in cands}
    links = sitelinks(all_ids)
    out = {}
    for text, cands in results.items():
        for c in cands:
            c['sitelinks'] = links.get(c['id'], 0)
        exact = [c for c in cands if bare(text) in {bare(c.get('label') or '')} | {bare(a) for a in c.get('aliases') or []}]
        exact.sort(key=lambda c: -c['sitelinks'])
        kind = kind_of(text)
        if kind == 'value':
            status, chosen = 'value', None
        elif len(exact) == 1 or (exact and exact[0]['sitelinks'] >= DOMINANT * max(1, exact[1]['sitelinks'])):
            status, chosen = 'linked', exact[0]
        elif exact:
            status, chosen = 'ambiguous', exact[0]
        elif cands:
            status, chosen = 'fuzzy', cands[0]
        else:
            status, chosen = 'not_found', None
        out[text] = {'status': status, 'kind': kind, 'qid': chosen and chosen['id'],
                     'label': chosen and chosen.get('label'), 'description': chosen and chosen.get('description'),
                     'sitelinks': chosen and chosen['sitelinks'], 'used_in': found[text],
                     'candidates': [{k: c.get(k) for k in ('id', 'label', 'description', 'sitelinks')} for c in cands[:5]]}
    return out


def relation_candidates(recs):
    texts = reads_as()
    used = defaultdict(lambda: {'records': 0, 'boxes': set(), 'fictional_only': True})
    for r in recs:
        u = used[r['relation']]
        u['records'] += 1
        u['boxes'].add(r['box'])
        u['fictional_only'] &= r.get('reality') == 'fictional'
    out = {}
    for name in sorted(set(used) | set(texts)):
        queries = [name.replace('_', ' ')]
        ra = texts.get(name, '')
        stripped = re.sub(r'\b(a|b|c|every|holders of|of office|is|are|was|were)\b', ' ', ra)
        stripped = ' '.join(stripped.split())
        if stripped and stripped not in queries:
            queries.append(stripped)
        cands, seen = [], set()
        for q in queries:
            for c in search(q, kind='property', limit=5):
                if c['id'] not in seen:
                    seen.add(c['id'])
                    cands.append({k: c.get(k) for k in ('id', 'label', 'description')})
        u = used.get(name, {'records': 0, 'boxes': set(), 'fictional_only': False})
        out[name] = {'reads_as': ra, 'records': u['records'], 'boxes': sorted(u['boxes']),
                     'fictional_only': u['fictional_only'] and u['records'] > 0, 'candidates': cands}
    return out


def main():
    recs = load_records()
    ents = link_entities(recs)
    (HERE / 'entity_links.json').write_text(json.dumps(ents, ensure_ascii=False, indent=1) + '\n')
    rels = relation_candidates(recs)
    (HERE / 'relation_candidates.json').write_text(json.dumps(rels, ensure_ascii=False, indent=1) + '\n')
    count = defaultdict(int)
    for e in ents.values():
        count[e['status']] += 1
    print(f'{len(ents)} entity strings: ' + ', '.join(f'{k} {v}' for k, v in sorted(count.items())))
    print(f'{len(rels)} relations: {sum(r["fictional_only"] for r in rels.values())} only in fictional records')


if __name__ == '__main__':
    main()
