#!/usr/bin/env python3
"""Report how Sid's Dataset records meet CRITERIA.md.

Report only for now: it lists what breaks each criterion and always exits 0.
A check moves into validate.py's errors once the records meet it. The
dashboard shows the same report (Datasets, Sid's Dataset, Criteria) through
report().

    python datasets/SidsDataset/criteria.py          # or: validate.py --criteria
    python datasets/SidsDataset/criteria.py --all    # every offending item, not the first few
    python datasets/SidsDataset/criteria.py --json   # what the dashboard reads

Each check has a status: pass, fail, review (a script can only flag it, a
person decides), pending (waiting on data, e.g. a model audit not yet run) or
manual (not checkable by script). Standard library only, like validate.py.
"""
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate import (DERIVABILITY, FAMILIARITY, FAMILIARITY_TIERS, ROOT, TOPICS,  # noqa: E402
                      load_relations)

# Provisional numbers; CRITERIA.md is where they get agreed.
SIMILAR_STATEMENT = 0.9   # difflib ratio above which two edits are listed as near repeats
MAX_FAR_REUSE = 10        # times one far unrelated prompt may appear in the dataset
# Derivation mix targets, {(box, derivation): share of that box's derived queries}.
# Empty until CRITERIA.md B3 has numbers; the counts are reported either way.
DERIVATION_TARGETS = {}
RBOX_PROPERTY_TARGETS = {}
# The models whose audit the audit criteria require (CRITERIA.md R4): the instruct
# models, since the main experiments ask free-form questions. Their newest run in
# results/model_audit counts. The base models are shown beside them, for reference.
AUDIT_MODELS = ('qwen3-4b-instruct-2507', 'olmo-3-7b-instruct', 'llama-3.1-8b-instruct', 'mistral-7b-instruct-v0.1')
REFERENCE_MODELS = ('qwen3-4b-base', 'olmo-3-7b-base', 'llama-3.1-8b', 'mistral-7b-v0.1')
AUDIT_RUNS = ROOT.parent.parent / 'results' / 'model_audit' / 'runs'

YES = {'yes', '是', 'sí', 'si'}
NO = {'no', '否', '不是'}
RBOX_PROPERTIES = (('InvFunc', 'inverse_functional'), ('Asym', 'asymmetric'), ('Sym', 'symmetric'),
                   ('Trans', 'transitive'), ('Func', 'functional'), ('Refl', 'reflexive'),
                   ('Disj', 'disjoint'))
STATEMENT_WORDS = (('subproperty', 'subproperty'), ('inverse functional', 'inverse_functional'),('asymmetric', 'asymmetric'),
                   ('symmetric', 'symmetric'), ('transitive', 'transitive'),
                   ('functional', 'functional'), ('reflexive', 'reflexive'), ('disjoint', 'disjoint'),
                   ('inverse', 'inverse'))
SNAKE = re.compile(r'[a-z][a-z0-9]*(?:_[a-z0-9]+)*')
IDENT = re.compile(r'[A-Za-z][A-Za-z0-9_]*')
DL_WORDS = {name for name, _ in RBOX_PROPERTIES} | {'not'}


def load_records():
    return [json.loads(p.read_text()) for p in sorted((ROOT / 'records').glob('*/*/*.json'))]


def norm(s):
    s = re.sub(r'[^\w\s]', ' ', str(s).lower())
    s = re.sub(r'^\s*(the|a|an)\s+', '', s)
    return ' '.join(s.split())


def yes_no(answer):
    a = norm(answer)
    return 'yes' if a in YES else 'no' if a in NO else None


def rbox_property(rec):
    """The kind of axiom an RBox edit asserts (or, for delete, removes)."""
    axiom = rec['edit'].get('axiom') or ''
    if '∘' in axiom:
        return 'chain'
    if '≡' in axiom:
        return 'inverse'
    if '⊑' in axiom:
        return 'subproperty'
    for prefix, name in RBOX_PROPERTIES:
        if re.match(rf'¬?{prefix}\(', axiom):
            return name
    statement = rec['edit']['statement'].lower()
    if 'means' in statement or 'composition' in statement:
        return 'chain'
    for word, name in STATEMENT_WORDS:
        if word in statement:
            return name
    return 'other'


def check(section, name, items=(), status=None, review=False, note='', table=None):
    """One checklist row. Without an explicit status: pass when nothing is
    listed, otherwise fail (or review, for flags a person has to judge)."""
    items = list(items)
    if status is None:
        status = 'pass' if not items else 'review' if review else 'fail'
    return {'section': section, 'name': name, 'status': status, 'count': len(items),
            'items': items, 'note': note, 'table': table}


def check_repeats(recs):
    s = 'R3. No repeated edits'
    # Delete records restate replace's facts by design, so compare insert and
    # replace only; delete is checked against its replace record under R5.
    pool = [r for r in recs if r['edit_operation'] != 'delete']
    by_statement, by_triple = defaultdict(list), defaultdict(list)
    for r in pool:
        e = r['edit']
        by_statement[norm(e['statement'])].append(r['id'])
        if r['box'] == 'rbox':
            key = (r['edit_operation'], e.get('axiom') or (r['relation'], rbox_property(r), ' not ' in norm(e['statement'])))
        else:
            key = (r['relation'], norm(e.get('subject')), norm(e.get('object')))
        by_triple[key].append(r['id'])
    near, by_group = [], defaultdict(list)
    for r in pool:
        by_group[(r['topic'], r['box'])].append(r)
    for group in by_group.values():
        for i, a in enumerate(group):
            sa = norm(a['edit']['statement'])
            for b in group[i + 1:]:
                sb = norm(b['edit']['statement'])
                if sa == sb:
                    continue
                m = SequenceMatcher(None, sa, sb)
                if m.quick_ratio() >= SIMILAR_STATEMENT and m.ratio() >= SIMILAR_STATEMENT:
                    near.append(f'{a["id"]} / {b["id"]}: {a["edit"]["statement"]!r} ~ {b["edit"]["statement"]!r}')
    return [
        check(s, 'Same statement twice', [', '.join(v) for v in by_statement.values() if len(v) > 1]),
        check(s, 'Same subject, relation and object (RBox: same relation and axiom)',
              [f'{", ".join(v)}  {k}' for k, v in by_triple.items() if len(v) > 1]),
        check(s, f'Near repeats (text similarity >= {SIMILAR_STATEMENT})', near, review=True),
    ]


def check_delete(recs):
    s = 'R5. Delete means "I don\'t know"'
    by_id = {r['id']: r for r in recs}
    unpaired, mismatched, answered = [], [], []
    for r in recs:
        if r['edit_operation'] != 'delete':
            continue
        twin = by_id.get(r['id'].replace('-delete-', '-replace-'))
        if twin is None:
            unpaired.append(r['id'])
        elif norm(r['edit']['statement']) != norm(twin['edit'].get('original')):
            mismatched.append(f'{r["id"]}: {r["edit"]["statement"]!r} vs replace original {twin["edit"].get("original")!r}')
        q = r['queries']
        for qtype in ('direct', 'paraphrase', 'cross_lingual', 'derived'):
            items = q.get(qtype)
            for item in items if isinstance(items, list) else [items] if items else []:
                if item.get('new_answer') is not None:
                    answered.append(f'{r["id"]} {qtype}: expects {item["new_answer"]!r}')
    return [
        check(s, 'Every delete has a replace record of the same number', unpaired),
        check(s, "Delete removes its replace record's original fact", mismatched),
        check(s, 'Every delete query expects "I don\'t know"', answered),
    ]


def check_yes_no(recs):
    s = 'B2. Yes/no answers 50/50 in RBox'
    counts = Counter()
    for r in recs:
        if r['box'] != 'rbox' or r['edit_operation'] == 'delete':
            continue
        q = r['queries']
        for qtype, items in (('direct', [q['direct']]), ('derived', q['derived']),
                             ('cross_lingual', q['cross_lingual'])):
            for item in items:
                v = yes_no(item.get('new_answer'))
                if v:
                    counts[(r['edit_operation'], qtype, r['topic'], v)] += 1
    off, table = [], [['operation', 'query', 'yes', 'no']]
    for op in ('insert', 'replace'):
        for qtype in ('direct', 'derived', 'cross_lingual'):
            y = sum(n for (o, t, _, v), n in counts.items() if (o, t, v) == (op, qtype, 'yes'))
            n_ = sum(n for (o, t, _, v), n in counts.items() if (o, t, v) == (op, qtype, 'no'))
            table.append([op, qtype, y, n_])
            if y != n_:
                off.append(f'{op} {qtype}: {y} yes / {n_} no')
            for topic in TOPICS:
                ty, tn = counts[(op, qtype, topic, 'yes')], counts[(op, qtype, topic, 'no')]
                if abs(ty - tn) > 1:
                    off.append(f'{op} {qtype} {topic}: {ty} yes / {tn} no')
    other = Counter()
    for r in recs:
        if r['box'] != 'rbox' and r['edit_operation'] != 'delete':
            for item in [r['queries']['direct'], r['queries']['paraphrase'], *r['queries']['derived']]:
                v = yes_no(item.get('new_answer'))
                if v:
                    other[(r['box'], v)] += 1
    note = 'ABox/TBox, not a criterion: ' + ', '.join(
        f'{b} {other[(b, "yes")]} yes / {other[(b, "no")]} no' for b in ('abox', 'tbox'))
    return [check(s, 'RBox yes/no answers 50/50 (overall equal, per topic within 1)', off, note=note, table=table)]


def check_ambiguity():
    return [check('R1. True and unambiguous', 'Every answer is clearly true or clearly false', status='manual',
                  note='Not checkable by script: needs an LLM pass and a person.')]


def check_subjects():
    return [check('R2. Stable subjects, self-contained statements',
                  "Subjects don't describe the edited value or contain their answer; statements stand on their own",
                  status='manual',
                  note='Checked by a person. wikidata/entities.json marks subjects that are descriptions '
                       '(category "description") and the review notes ("issue") that found such subjects.')]


def check_wikidata():
    """R8, from wikidata/analysis.json: a named fact whose relation has a
    Wikidata property is in Wikidata, directly or through an allowed chain."""
    path = ROOT / 'wikidata' / 'analysis.json'
    s, name = 'R8. Named facts are in Wikidata', 'Named facts with a Wikidata property are found there'
    if not path.exists():
        return [check(s, name, status='pending', note='Run wikidata/analyze.py first.')]
    a = json.loads(path.read_text())
    covered, missing, exempt = 0, [], 0
    rows = [(f['id'], f['match'], f.get('original_grade') if f['op'] == 'replace' else f.get('new_grade'))
            for f in a.get('facts', [])]
    rows += [(t['id'], 'exact', t.get('original_grade') if t['op'] == 'replace' else t.get('new_grade'))
             for t in a.get('tbox_subclass', [])]
    for rid, match, grade in rows:
        if match not in ('exact', 'narrower', 'broader') or grade in (None, 'unlinked'):
            exempt += 1
        elif grade.startswith('found'):
            covered += 1
        else:
            missing.append(f'{rid}: {grade}')
    note = (f'{covered} found, {len(missing)} not, {exempt} exempt (relation has no Wikidata property, or '
            f'subject/object not a named thing). Analysis of {a.get("date")}; rerun wikidata/analyze.py after edits.')
    return [check(s, name, missing, note=note)]


def check_locality(recs):
    leaks = []
    for r in recs:
        # Under delete a leak is an abstention, which any near query catches; a
        # near query answered by the removed value (often a premise) is wanted.
        if r['box'] == 'rbox' or r['edit_operation'] == 'delete':
            continue
        # The answer a leak would produce: the edit's new value.
        edited = {norm(r['edit'].get('object')), norm(r['queries']['direct'].get('new_answer'))}
        edited.discard('')
        for q in r['queries']['unrelated_near']:
            if norm(q.get('reference')) in edited:
                leaks.append(f'{r["id"]}: {q["prompt"]!r} -> {q["reference"]!r}')
    return [check('R6. Locality can catch leaks', "Near unrelated answers differ from the edit's new answer", leaks)]


def check_mix(recs):
    s = 'B3. Derivations not dominated by composition'
    der = Counter()
    for r in recs:
        if r['box'] != 'rbox':
            for q in r['queries']['derived']:
                # relation_semantics is optional now; untagged records count only in the total.
                der[(r['box'], r.get('relation_semantics'), q['derivation'])] += 1
    table = [['box', 'derivation', 'queries', 'share', 'associative', 'causal']]
    for box in ('abox', 'tbox'):
        total = sum(n for (b, _, _), n in der.items() if b == box) or 1
        names = sorted({d for (b, _, d) in der if b == box}, key=lambda d: -sum(
            n for (b, _, dd), n in der.items() if b == box and dd == d))
        for d in names:
            a, c = der[(box, 'associative', d)], der[(box, 'causal', d)]
            n = sum(m for (b, _, dd), m in der.items() if b == box and dd == d)
            table.append([box, d, n, f'{n / total:.1%}', a, c])
    # Delete records drop the axiom; they remove the property their replace record flips.
    by_id = {r['id']: r for r in recs}
    rbox = Counter((r['edit_operation'], rbox_property(by_id.get(r['id'].replace('-delete-', '-replace-'), r)))
                   for r in recs if r['box'] == 'rbox')
    rtable = [['RBox property', 'insert', 'replace', 'delete']]
    for p in sorted({p for _, p in rbox}):
        rtable.append([p, rbox[('insert', p)], rbox[('replace', p)], rbox[('delete', p)]])
    misses = []
    for (box, d), share in DERIVATION_TARGETS.items():
        total = sum(n for (b, _, _), n in der.items() if b == box) or 1
        got = sum(n for (b, _, dd), n in der.items() if b == box and dd == d) / total
        if got < share:
            misses.append(f'{box} {d}: {got:.1%} < target {share:.0%}')
    for (op, p), n in RBOX_PROPERTY_TARGETS.items():
        if rbox[(op, p)] != n:
            misses.append(f'rbox {op} {p}: {rbox[(op, p)]} edits, target {n}')
    targets = DERIVATION_TARGETS or RBOX_PROPERTY_TARGETS
    return [
        check(s, 'ABox/TBox derivations meet their targets', misses,
              status=None if targets else 'pending', note='' if targets else 'Targets not agreed yet.', table=table),
        check(s, 'RBox edits by property meet their targets', [], status='pass' if targets else 'pending',
              note='' if targets else 'Targets not agreed yet.', table=rtable),
    ]


def newest_audits():
    """{model: (summary, finished)}: each model's newest audit run."""
    newest = {}
    for path in sorted(AUDIT_RUNS.glob('*/summary.json')) if AUDIT_RUNS.is_dir() else []:
        try:
            summary = json.loads(path.read_text())
        except (OSError, ValueError):
            continue
        model, mtime = summary.get('model'), path.stat().st_mtime
        if model and (model not in newest or mtime > newest[model][1]):
            newest[model] = (summary, mtime)
    return newest


def check_audit(recs, audits=None):
    """Section 7: before editing, every main model holds each replace and
    delete fact and none already holds a real insert. The audit's fact
    `known` is its pass rule: 1 means the original is held (replace, delete)
    or the new answer is not (insert)."""
    s = 'R4. The models hold the right things'
    audits = newest_audits() if audits is None else audits
    every = {m: {f['record_id']: f.get('known') for f in audits[m][0].get('facts', [])}
             for m in AUDIT_MODELS + REFERENCE_MODELS if m in audits}
    facts = {m: f for m, f in every.items() if m in AUDIT_MODELS}
    missing_models = [m for m in AUDIT_MODELS if m not in audits]
    table = [['model', 'audited', 'records', 'replace held', 'delete held', 'real insert not held']]
    for m in AUDIT_MODELS + REFERENCE_MODELS:
        name = m if m in AUDIT_MODELS else f'{m} (reference)'
        if m not in audits:
            table.append([name, 'not audited', '', '', '', ''])
            continue
        f, when = every[m], datetime.fromtimestamp(audits[m][1]).strftime('%Y-%m-%d %H:%M')
        row = [name, when, len(f)]
        for op in ('replace', 'delete', 'insert'):
            rs = [r for r in recs if r['edit_operation'] == op and r.get('reality') != 'fictional'
                  and not r['edit'].get('fixture')]
            row.append(f'{sum(f.get(r["id"]) == 1 for r in rs)}/{len(rs)}')
        table.append(row)

    rows = []
    for op, name in (('replace', 'Replace: every model already holds the original fact'),
                     ('delete', 'Delete: every model already holds the fact'),
                     ('insert', 'Insert (real): no model already holds the new fact')):
        failed, unaudited, unclear = [], set(missing_models), []
        for r in recs:
            if r['edit_operation'] != op or r.get('reality') == 'fictional' or r['edit'].get('fixture'):
                continue
            bad = [m for m in facts if facts[m].get(r['id']) == 0]
            vague = [m for m in facts if r['id'] in facts[m] and facts[m][r['id']] is None]
            unaudited |= {m for m in facts if r['id'] not in facts[m]}
            if bad:
                verb = 'already held by' if op == 'insert' else 'not held by'
                failed.append(f'{r["id"]}: {verb} {", ".join(bad)}')
            if vague:
                unclear.append(f'{r["id"]}: judge unclear for {", ".join(vague)}')
        items = failed + unclear
        status = 'fail' if failed else 'pending' if unaudited or unclear else 'pass'
        note = f'Not audited on every record: {", ".join(sorted(unaudited))}.' if unaudited else ''
        rows.append(check(s, name, items, status=status, note=note, table=table if op == 'replace' else None))
    return rows


def check_naming(recs, relations):
    s = 'R7. One name per relation'
    used = defaultdict(list)
    for r in recs:
        used[r['relation']].append(r['id'])
        if r['box'] == 'rbox':
            for name in IDENT.findall(r['edit'].get('axiom') or ''):
                if name not in DL_WORDS and r['id'] not in used[name]:
                    used[name].append(r['id'])
    # Names that may be one relation spelled twice: equal once has_/is_ are dropped.
    stem = defaultdict(set)
    for n in set(used) | set(relations):
        stem[re.sub(r'^(has|is)_', '', n)].add(n)
    return [
        check(s, 'Relation names are snake_case', [f'{n} ({", ".join(v[:3])})' for n, v in sorted(used.items())
                                                   if not SNAKE.fullmatch(n)]),
        check(s, 'Every relation is in RELATIONS.md', [f'{n} ({", ".join(v[:3])})' for n, v in sorted(used.items())
                                                       if n not in relations]),
        check(s, 'No relation under two names', [' / '.join(sorted(v)) for v in stem.values() if len(v) > 1],
              review=True),
    ]


def check_reuse(recs):
    far = Counter(q['prompt'] for r in recs for q in r['queries'].get('unrelated_far') or [])
    return [check('B6. Far locality prompts vary', f'No far unrelated prompt used more than {MAX_FAR_REUSE} times',
                  [f'{n}x {p}' for p, n in far.most_common() if n > MAX_FAR_REUSE],
                  note=f'{len(far)} distinct far prompts over {sum(far.values())} queries.')]


def spread(recs):
    table = [['tag', 'operation', *FAMILIARITY]]
    for tier in FAMILIARITY_TIERS:
        for op in ('insert', 'replace'):
            c = Counter((r.get('familiarity') or {}).get(tier) for r in recs if r['edit_operation'] == op)
            table.append([f'familiarity.{tier}', op, *(c[v] for v in FAMILIARITY)])
    c = Counter(r.get('derivability') for r in recs if r['edit_operation'] == 'replace')
    dtable = [['derivability (replace)', *DERIVABILITY], ['', *(c[v] for v in DERIVABILITY)]]
    return [check('B4. Surface and hop forms are mixed', 'Surface form x hop form grid', status='pending',
                  note='Targets open (CRITERIA.md design note). Derivability, our current rating of hop form:',
                  table=dtable),
            check('B5. Familiarity and connectivity spread', 'Familiarity', status='info', table=table)]


def report():
    recs = load_records()
    relations, _ = load_relations()
    checks = (check_ambiguity() + check_subjects() + check_repeats(recs) + check_audit(recs)
              + check_delete(recs) + check_locality(recs) + check_naming(recs, relations) + check_wikidata()
              + check_yes_no(recs) + check_mix(recs) + spread(recs) + check_reuse(recs))
    return {'records': len(recs), 'checks': checks,
            'status': dict(Counter(c['status'] for c in checks))}


MARK = {'pass': 'ok', 'fail': 'FAIL', 'review': 'review', 'pending': 'pending', 'manual': 'manual', 'info': ''}


def print_report(rep, show_all):
    print(f'# Criteria report: {rep["records"]} records (CRITERIA.md)')
    section = None
    for c in rep['checks']:
        if c['section'] != section:
            section = c['section']
            print(f'\n## {section}')
        count = f' ({c["count"]})' if c['count'] else ''
        print(f'- [{MARK[c["status"]]}] {c["name"]}{count}' if MARK[c['status']] else f'- {c["name"]}')
        if c['note']:
            print(f'    {c["note"]}')
        for row in c['table'] or []:
            print('    ' + '  '.join(f'{str(v):>12}' if i else f'{str(v):24}' for i, v in enumerate(row)))
        for item in c['items'] if show_all else c['items'][:8]:
            print(f'    {item}')
        if not show_all and len(c['items']) > 8:
            print(f'    ... {len(c["items"]) - 8} more (--all)')
    print('\n' + ', '.join(f'{n} {s}' for s, n in sorted(rep['status'].items())))


def main(argv):
    rep = report()
    if '--json' in argv:
        print(json.dumps(rep, ensure_ascii=False))
    else:
        print_report(rep, '--all' in argv)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
