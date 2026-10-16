#!/usr/bin/env python3
"""Compare Sid's Dataset with Wikidata: coverage, relation properties, facts.

Reads entities.json (curated links, merge_review.py) and relation_map.json
(curated: our relation -> Wikidata properties) and asks QLever:

1. Relation coverage: which relations have a Wikidata property, and how close
   it is (exact, broader, narrower, related, none).
2. Relation properties: our RELATIONS.md tags against what Wikidata declares
   for the mapped property (transitive, symmetric, inverse partner, single
   value, subproperty of).
3. Entity coverage: what each entity string is (entity, class, value, word,
   description, not in Wikidata), by topic and box, and the dataset issues
   the review noted.
4. Facts, for real ABox edits whose subject and object both link: is the
   original fact in Wikidata (found: under a mapped property; linked: under
   another property; not found), does the subject hold other values for a
   single-value relation (conflict), and, for replace, is the counterfactual
   new object already a value (then the replacement isn't false). TBox
   subclass_of rules are checked along subclass-of, instance-of and
   parent-taxon chains (Wikidata models living things as taxa).

    python datasets/SidsDataset/wikidata/analyze.py
Writes analysis.json and ANALYSIS.md beside this script.
"""
import json
from collections import Counter, defaultdict
from datetime import date

from link import load_records
from validate import load_relations
from wd import HERE, chunks, sparql, values

SINGLE_VALUE, SINGLE_BEST, SYMMETRIC, INVERSE_C = 'Q19474404', 'Q52060874', 'Q21510862', 'Q21510855'
# Wikidata declares symmetry two ways, inconsistently: a property may be an
# instance of "symmetric property" or carry a symmetric constraint. Either counts.
TRANSITIVE, SYMMETRIC_CLASS, ASYMMETRIC_CLASS = 'Q18647515', 'Q18647518', 'Q18647519'


def declared(pids):
    """{pid: {transitive, symmetric, single_value, single_best_value, inverse: [...], parents: [...], label}}"""
    out = {p: {'transitive': False, 'symmetric': False, 'asymmetric': False, 'single_value': False,
               'single_best_value': False,
               'inverse': set(), 'parents': set(), 'label': None} for p in pids}
    for batch in chunks(sorted(pids), 100):
        v = values(batch, 'p')
        for row in sparql(f"SELECT ?p ?l WHERE {{ {v} ?p rdfs:label ?l FILTER(lang(?l)='en') }}"):
            out[row['p']]['label'] = row['l']
        for row in sparql(f"SELECT ?p ?c WHERE {{ {v} ?p wdt:P31 ?c "
                          f"VALUES ?c {{ wd:{TRANSITIVE} wd:{SYMMETRIC_CLASS} wd:{ASYMMETRIC_CLASS} }} }}"):
            key = {TRANSITIVE: 'transitive', SYMMETRIC_CLASS: 'symmetric', ASYMMETRIC_CLASS: 'asymmetric'}[row['c']]
            out[row['p']][key] = True
        for row in sparql(f"SELECT ?p ?c WHERE {{ {v} ?p p:P2302/ps:P2302 ?c }}"):
            c = row['c']
            key = {SYMMETRIC: 'symmetric', SINGLE_VALUE: 'single_value', SINGLE_BEST: 'single_best_value'}.get(c)
            if key:
                out[row['p']][key] = True
        for row in sparql(f"SELECT ?p ?q WHERE {{ {v} {{ ?p wdt:P1696 ?q }} UNION "
                          f"{{ ?p p:P2302 ?st . ?st ps:P2302 wd:{INVERSE_C} ; pq:P2306 ?q }} }}"):
            out[row['p']]['inverse'].add(row['q'])
        for row in sparql(f"SELECT ?p ?q WHERE {{ {v} ?p wdt:P1647 ?q }}"):
            out[row['p']]['parents'].add(row['q'])
    for d in out.values():
        d['inverse'], d['parents'] = sorted(d['inverse']), sorted(d['parents'])
    return out


def usage(pids):
    out = {}
    for p in sorted(pids):
        rows = sparql(f"SELECT (COUNT(*) AS ?n) WHERE {{ ?s wdt:{p} ?o }}")
        out[p] = int(rows[0]['n']) if rows else None
    return out


def compare_tags(relation, tags, rmap, decl):
    """Disagreements between our tags and the declarations of the mapped property."""
    out = []
    pids = [m['pid'] for m in rmap.get('pids', []) if m.get('direction', 'same') == 'same']
    if not pids or rmap.get('match') not in ('exact',):
        return out
    d = {k: any(decl[p][k] for p in pids)
         for k in ('transitive', 'symmetric', 'asymmetric', 'single_value', 'single_best_value')}
    ours = {'transitive': 'transitive' in tags, 'symmetric': 'symmetric' in tags,
            'asymmetric': 'asymmetric' in tags, 'functional': 'functional' in tags}
    if d['asymmetric'] and not ours['asymmetric']:
        out.append('asymmetric: Wikidata declares it, ours does not')
    if ours['transitive'] != d['transitive']:
        out.append(f"transitive: ours {ours['transitive']}, Wikidata {d['transitive']}")
    if ours['symmetric'] != d['symmetric']:
        out.append(f"symmetric: ours {ours['symmetric']}, Wikidata {d['symmetric']}")
    if ours['functional'] and not (d['single_value'] or d['single_best_value']):
        out.append('functional: ours yes, Wikidata declares no single-value constraint')
    if not ours['functional'] and d['single_value']:
        out.append('functional: ours no, Wikidata declares a single-value constraint')
    return out


def links_between(pairs):
    """{(s, o): [(pid, 'out'|'in'), ...]}: every direct wdt: statement between two items, either way.
    One query per pair with the items written in: QLever doesn't push a VALUES
    block of pairs into the scan and times out."""
    out = defaultdict(list)
    for s, o in sorted(pairs):
        q = (f"SELECT ?p ?dir WHERE {{ {{ wd:{s} ?p wd:{o} BIND('out' AS ?dir) }} UNION "
             f"{{ wd:{o} ?p wd:{s} BIND('in' AS ?dir) }} }}")
        for row in sparql(q):
            if row['p'].startswith('P') and '/prop/direct/' not in row['p']:
                out[(s, o)].append((row['p'], row['dir']))
    return out


def subject_values(pairs):
    """{(s, pid): [object qids]}: what Wikidata holds for this subject under this property."""
    out = defaultdict(list)
    for s, p in sorted(pairs):
        out[(s, p)] = [row['o'] for row in sparql(f"SELECT ?o WHERE {{ wd:{s} wdt:{p} ?o }}")]
    return out


# Location-like relations: Wikidata stores the most specific place (Ulm, the
# Salle des Etats), our records often a broader one (Germany, the Louvre).
# Following these, transitive by our located_in tag, bridges the two.
LOCATION_PATH = '(wdt:P131|wdt:P276|wdt:P361|wdt:P17|wdt:P706)+'


def places_above(qid):
    return {row['a'] for row in sparql(f"SELECT DISTINCT ?a WHERE {{ wd:{qid} {LOCATION_PATH} ?a }}")}


def ancestors(qid):
    """Every class or taxon above an item: subclass-of, instance-of then
    subclass-of, and parent-taxon chains, asked separately (one alternating
    path times out on QLever)."""
    out = set()
    for path in ('wdt:P279+', 'wdt:P31/wdt:P279*', 'wdt:P171+'):
        out |= {row['a'] for row in sparql(f"SELECT ?a WHERE {{ wd:{qid} {path} ?a }}")}
    return out


def main():
    recs = load_records()
    ents = json.loads((HERE / 'entities.json').read_text())
    rmap = json.loads((HERE / 'relation_map.json').read_text())
    relations, _ = load_relations()
    report = {'date': date.today().isoformat(), 'endpoint': 'qlever.dev/api/wikidata'}

    # 1. Relation coverage.
    used = Counter(r['relation'] for r in recs)
    real_used = Counter(r['relation'] for r in recs if r.get('reality') != 'fictional')
    cov = Counter()
    for name in used:
        cov[rmap.get(name, {}).get('match', 'unmapped')] += 1
    report['relation_coverage'] = {
        'relations': dict(cov),
        'records_by_match': dict(Counter(rmap.get(r['relation'], {}).get('match', 'unmapped') for r in recs
                                         if r.get('reality') != 'fictional')),
    }

    # 2. Relation properties.
    pids = {m['pid'] for v in rmap.values() for m in v.get('pids', [])}
    decl = declared(pids) if pids else {}
    counts = usage(pids) if pids else {}
    report['properties'] = {p: {**decl[p], 'usage': counts.get(p)} for p in sorted(pids)}
    report['tag_mismatches'] = {}
    for name, m in sorted(rmap.items()):
        if name in relations:
            diff = compare_tags(name, relations[name][0], m, decl)
            if diff:
                report['tag_mismatches'][name] = diff

    # 3. Entity coverage.
    box_of = {r['id']: r['box'] for r in recs}
    by_box = Counter()
    for e in ents.values():
        for u in e['used_in']:
            rid = u.split('/')[0]
            by_box[(rid.split('-')[0], box_of[rid], e['category'])] += 1
    report['entity_coverage'] = {
        'by_category': dict(Counter(e['category'] for e in ents.values())),
        'low_confidence': sorted(t for t, e in ents.items() if e.get('confidence') == 'low'),
        'slots_by_topic_box_category': {f'{a}/{b}/{c}': n for (a, b, c), n in sorted(by_box.items())},
        'issues': {t: {'issue': e['issue'], 'used_in': e['used_in'][:3]} for t, e in ents.items() if e.get('issue')},
    }

    # 4. Facts: real ABox replace, delete-free (delete restates replace) and real insert.
    def qid(text):
        e = ents.get((text or '').strip())
        return e['qid'] if e and e['category'] in ('entity', 'class') and e.get('qid') else None

    facts = []
    for r in recs:
        if r['box'] != 'abox' or r['edit_operation'] == 'delete' or r.get('reality') == 'fictional' or r['edit'].get('fixture'):
            continue
        e = r['edit']
        orig = e.get('old_object') if r['edit_operation'] == 'replace' else None
        facts.append({'id': r['id'], 'op': r['edit_operation'], 'relation': r['relation'],
                      's': qid(e.get('subject')), 'orig': qid(orig), 'new': qid(e.get('object')),
                      'texts': [e.get('subject'), orig, e.get('object')]})
    pairs = {(f['s'], o) for f in facts for o in (f['orig'], f['new']) if f['s'] and o}
    between = links_between(pairs) if pairs else {}
    svals = subject_values({(f['s'], m['pid']) for f in facts if f['s']
                            for m in rmap.get(f['relation'], {}).get('pids', []) if m.get('direction', 'same') == 'same'})
    def svals_for(s, m):
        return {o for x in m.get('pids', []) if x.get('direction', 'same') == 'same' for o in svals.get((s, x['pid']), [])}

    graded = []
    for f in facts:
        m = rmap.get(f['relation'], {})
        mapped = {(x['pid'], 'out' if x.get('direction', 'same') == 'same' else 'in') for x in m.get('pids', [])}
        row = {'id': f['id'], 'op': f['op'], 'relation': f['relation'], 'match': m.get('match', 'unmapped'),
               'texts': f['texts'], 'subject': f['s'], 'original': f['orig'], 'new': f['new']}

        def grade(obj):
            if not (f['s'] and obj):
                return 'unlinked'
            got = set(between.get((f['s'], obj), []))
            if got & mapped:
                return 'found'
            # Wikidata holds a more specific value that lies inside ours.
            for v in svals_for(f['s'], m):
                if obj in places_above(v):
                    return 'found_via_location'
            return 'linked' if got else 'not_found'
        if f['op'] == 'replace':
            row['original_grade'] = grade(f['orig'])
            row['new_grade'] = grade(f['new'])  # 'found' here: the counterfactual is already true
            row['links_original'] = sorted(p for p, _ in between.get((f['s'], f['orig']), []))
        else:
            row['new_grade'] = grade(f['new'])  # found: Wikidata confirms the real insert is true
        single = any(decl.get(x['pid'], {}).get('single_value') or decl.get(x['pid'], {}).get('single_best_value')
                     for x in m.get('pids', []))
        if f['s'] and m.get('match') in ('exact', 'narrower', 'broader'):
            held = sorted({o for x in m.get('pids', []) if x.get('direction', 'same') == 'same'
                           for o in svals.get((f['s'], x['pid']), [])})
            row['subject_values'] = held
            target = f['orig'] if f['op'] == 'replace' else f['new']
            target_grade = row.get('original_grade') if f['op'] == 'replace' else row.get('new_grade')
            if single and target and held and target not in held and not (target_grade or '').startswith('found'):
                row['conflict'] = True
        graded.append(row)
    # TBox subclass_of: is the class under the original (replace) or new
    # superclass along subclass-of, instance-of and parent-taxon chains?
    tbox = []
    for r in recs:
        if r['box'] != 'tbox' or r['relation'] != 'subclass_of' or r['edit_operation'] == 'delete' \
                or r.get('reality') == 'fictional':
            continue
        e = r['edit']
        s = qid(e.get('subject'))
        row = {'id': r['id'], 'op': r['edit_operation'], 'texts': [e.get('subject'), e.get('old_object'), e.get('object')]}
        for key, o in (('original', qid(e.get('old_object'))), ('new', qid(e.get('object')))):
            if key == 'original' and r['edit_operation'] != 'replace':
                continue
            if not (s and o):
                row[key + '_grade'] = 'unlinked'
                continue
            row[key + '_grade'] = 'found' if o in ancestors(s) else 'not_found'
        tbox.append(row)
    report['tbox_subclass'] = tbox
    report['facts'] = graded
    report['fact_summary'] = {
        'replace_original': dict(Counter(g.get('original_grade') for g in graded if g['op'] == 'replace')),
        'replace_new_already_true': [g['id'] for g in graded if g['op'] == 'replace' and g.get('new_grade') == 'found'],
        # Real inserts Wikidata confirms: true facts (whether models know them is the audit's question).
        'insert_confirmed': [g['id'] for g in graded if g['op'] == 'insert' and g.get('new_grade', '').startswith('found')],
        'insert_grades': dict(Counter(g.get('new_grade') for g in graded if g['op'] == 'insert')),
        'conflicts': [g['id'] for g in graded if g.get('conflict')],
        'tbox_subclass_original': dict(Counter(t.get('original_grade') for t in tbox if t['op'] == 'replace')),
        'tbox_subclass_new_already_true': [t['id'] for t in tbox if t.get('new_grade') == 'found'],
    }
    (HERE / 'analysis.json').write_text(json.dumps(report, ensure_ascii=False, indent=1, default=sorted) + '\n')
    print(json.dumps({k: report[k] for k in ('relation_coverage', 'fact_summary')}, indent=1))
    print('tag mismatches:', len(report['tag_mismatches']))
    print('entities:', report['entity_coverage']['by_category'])


if __name__ == '__main__':
    main()
