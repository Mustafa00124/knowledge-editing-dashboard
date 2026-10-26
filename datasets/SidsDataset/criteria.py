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
from validate import (ROOT, TOPICS, load_relations)  # noqa: E402

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


# Belief-revision problems (README, Determinacy and belief-revision problems).
# Read off the stored tags: a query's determinacy names its query-level
# problem; the edit's derivability says whether the edit itself is stored or
# derived (the edit-level side of the problem of derived beliefs).
PROBLEMS = (('determinate', 'determinate'), ('background_beliefs', 'background beliefs'),
            ('derived_beliefs', 'derived beliefs'))
STORED = ('very_unlikely', 'unlikely')
DERIVED = ('likely', 'very_likely')
# Per topic, box and operation (replace, and delete mirroring it), 4 edits. ABox: 2 of stored facts and 2 of
# derived ones. ABox and TBox: 2 determinate and 2 indeterminate derived
# queries per edit (TBox: new members named in the prompt, and well-known
# members). RBox: all determinate ("Does it follow that ...?"). Mathematics may
# have every derived query determinate: a number fact leaves no consistent
# world; so may grammar's ABox (word-form edits anchored by firm examples).
# 20 edits per topic and operation. Replace and delete: ABox 0001-0004 and
# 0013-0016, TBox 0005-0008 and 0019-0020, RBox 0009-0012 and 0017-0018.
# Insert: ABox 0001-0008, TBox 0009-0014, RBox 0015-0020.
EDITS_PER_BOX = {'abox': 8, 'tbox': 6, 'rbox': 6}
EDITS_PER_KIND = 4
INDETERMINATE_PER_EDIT = 2
ALL_DETERMINATE = {('mathematics', 'abox'), ('mathematics', 'tbox'), ('grammar', 'abox')}
OPERATIONS = ('replace', 'delete', 'insert')
# Insert (fictional only): which parts are made up, per box and topic. Keys
# joined by '|' count together (a TBox fictional property is a relation or an
# object, whichever the axiom makes it). Inserts that leave no real subject to
# ask about (relation, subject_object, all) may have every derived query
# determinate.
FICTIONAL_MIX = {'abox': {'subject': 2, 'object': 2, 'subject_object': 1, 'relation': 2, 'all': 1},
                 'tbox': {'subject': 2, 'relation|object': 2, 'subject_object|all': 2},
                 'rbox': {'relation': 3, 'all': 3}}
INSERT_ALL_DETERMINATE = ('relation', 'subject_object', 'all')
# A TBox made-up object is a made-up property of a real class: like a made-up
# relation, it leaves no real count or superlative to split on.
INSERT_ALL_DETERMINATE_TBOX = INSERT_ALL_DETERMINATE + ('object',)


def fictional_mix(counts, want):
    """Counts grouped as `want` keys; None when they match."""
    got = {k: sum(counts[x] for x in k.split('|')) for k in want}
    other = sum(counts.values()) - sum(got.values())
    return None if got == want and not other else {**got, **({'other': other} if other else {})}


def memory_chain(rec):
    """An RBox insert whose role chain reaches real knowledge the prompt leaves out."""
    derived = rec['queries']['derived']
    return (rec['edit_operation'] == 'insert' and rec['box'] == 'rbox' and '∘' in rec['edit'].get('axiom', '')
            and all(q.get('bridge') and not q.get('bridge_in_prompt') for q in derived))


def edit_kind(rec):
    """'stored', 'derived' or None (medium or unset) from derivability."""
    d = rec.get('derivability')
    return 'stored' if d in STORED else 'derived' if d in DERIVED else None


def check_problems(recs):
    s = 'B7. Belief-revision problems are covered'
    recs = [r for r in recs if r['edit_operation'] in OPERATIONS]
    boxes, kinds, queries = defaultdict(Counter), defaultdict(Counter), defaultdict(Counter)
    fmix = defaultdict(Counter)
    shape, route = [], []
    for r in recs:
        t, box, kind, op = r['topic'], r['box'], edit_kind(r), r['edit_operation']
        boxes[t][(op, box)] += 1
        derived = r['queries']['derived']
        if box == 'abox' and op != 'insert':
            kinds[t][(op, kind or 'medium')] += 1
        if op == 'insert':
            fmix[(t, box)][r.get('fictional')] += 1
        for q in derived:
            queries[t][q.get('determinacy', 'none')] += 1
        indet = sum(q.get('determinacy') not in (None, 'determinate') for q in derived)
        if box == 'rbox':
            continue
        if (t, box) in ALL_DETERMINATE or (op == 'insert' and r.get('fictional') in
                                             (INSERT_ALL_DETERMINATE_TBOX if box == 'tbox' else INSERT_ALL_DETERMINATE)):
            if indet not in (0, INDETERMINATE_PER_EDIT):
                shape.append(f'{r["id"]}: {indet} indeterminate derived queries (0 or {INDETERMINATE_PER_EDIT} in {t})')
        elif indet != INDETERMINATE_PER_EDIT:
            shape.append(f'{r["id"]}: {indet} indeterminate derived queries, want {INDETERMINATE_PER_EDIT}')
        if box == 'abox' and kind == 'derived' and not any(q.get('premise_route') for q in derived):
            route.append(f'{r["id"]}: derived edit with no premise-route query')
    missing = [f'{t}: {boxes[t][(op, b)]} {op} {b} edits, want {EDITS_PER_BOX[b]}'
               for t in TOPICS for op in OPERATIONS for b in ('abox', 'tbox', 'rbox')
               if boxes[t][(op, b)] != EDITS_PER_BOX[b]]
    missing += [f'{t}: {kinds[t][(op, k)]} {k} {op} ABox edits, want {EDITS_PER_KIND}'
                for t in TOPICS for op in ('replace', 'delete') for k in ('stored', 'derived')
                if kinds[t][(op, k)] != EDITS_PER_KIND]
    mix = [f'{t} insert {b}: {fictional_mix(fmix[(t, b)], want)}, want {want}'
           for t in TOPICS for b, want in FICTIONAL_MIX.items()
           if boxes[t][('insert', b)] and fictional_mix(fmix[(t, b)], want)]
    table = [['topic', 'abox', 'tbox', 'rbox', 'stored', 'derived', *(label for _, label in PROBLEMS)]]
    for t in TOPICS:
        table.append([t, *('/'.join(str(boxes[t][(op, b)]) for op in OPERATIONS) for b in ('abox', 'tbox', 'rbox')),
                      *('/'.join(str(kinds[t][(op, k)]) for op in OPERATIONS) for k in ('stored', 'derived')),
                      *(queries[t][k] for k, _ in PROBLEMS)])
    note = ('Replace and delete records; box and kind columns read replace/delete. Stored ABox edits have '
            'derivability very_unlikely or unlikely, derived ones likely or very_likely. RBox derived queries are '
            'determinate by construction; mathematics, and grammar ABox, may have all derived queries determinate.')
    pending = None if recs else 'pending'
    return [
        check(s, 'Each topic has 8 ABox, 6 TBox and 6 RBox edits under replace, delete and insert, half the '
                 'replace and delete ABox stored and half derived', missing,
              status=pending, note=note, table=table),
        check(s, 'Each ABox and TBox edit has 2 determinate and 2 indeterminate derived queries', shape,
              status=pending),
        check(s, 'Each derived ABox edit has a premise-route query', route, status=pending),
        check(s, 'Each topic has an RBox insert chaining a made-up relation through real knowledge',
              [f'{t}: no RBox insert whose role chain uses a real hop left to the model' for t in TOPICS
               if any(r['topic'] == t and r['edit_operation'] == 'insert' for r in recs)
               and not any(memory_chain(r) for r in recs if r['topic'] == t)], status=pending,
              note='A role chain (axiom with a composition) whose two derived queries both leave a real '
                   'bridge fact to the model (bridge listed, bridge_in_prompt false), checked before editing.'),
        check(s, 'Inserts mix what is made up: subject, object, both, relation, all', mix, status=pending,
              note='Fictional only. ABox: 2 subject, 2 object, 1 subject and object, 2 relation, 1 all; TBox: 2 '
                   'subject, 2 relation or object, 2 subject and object or all; RBox: 3 relation, 3 all. Inserts '
                   'with no real subject or object to ask about may have every derived query determinate.'),
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
    ops = {r['edit_operation'] for r in recs}
    for op, name in (('replace', 'Replace: every model already holds the original fact'),
                     ('delete', 'Delete: every model already holds the fact'),
                     ('insert', 'Insert (real): no model already holds the new fact')):
        if op not in ops:
            continue
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


# Manual rules are reviewed by two agents and a person; each marks the rule
# done in reviews.json (tracked, so a push shares the marks with everyone).
REVIEWERS = (('codex', 'Codex'), ('claude', 'Claude'), ('human', 'Human'))
REVIEWS_PATH = ROOT / 'reviews.json'


def load_reviews():
    try:
        return json.loads(REVIEWS_PATH.read_text())
    except (OSError, ValueError):
        return {}


def set_review(rule, reviewer, done, by=None, note=None):
    """Mark a manual rule done (or back to pending) for one reviewer."""
    if rule not in {k for k, *_ in MANUAL_RULES}:
        raise ValueError(f'unknown manual rule {rule!r}')
    if reviewer not in dict(REVIEWERS):
        raise ValueError(f'unknown reviewer {reviewer!r}')
    reviews = load_reviews()
    entry = {'done': bool(done), 'at': datetime.now().isoformat(timespec='seconds')}
    if by:
        entry['by'] = by
    if note:
        entry['note'] = note
    reviews.setdefault(rule, {})[reviewer] = entry
    REVIEWS_PATH.write_text(json.dumps(reviews, ensure_ascii=False, indent=2) + '\n')
    return reviews[rule]


# (key, title, what to check). Manual: a script can't judge them.
MANUAL_RULES = (
    ('true-and-unambiguous', 'True and unambiguous',
     'Every answer the dataset relies on is clearly true or clearly false: original and new answers, '
     'bridge facts, premises, locality references. No disputed, date-dependent or several-answer facts.'),
    ('stable-subjects', 'Stable subjects, self-contained statements',
     "No subject describes the value being edited (\"the volcano that destroyed Pompeii\", edited to Etna, "
     "means Vesuvius before and Etna after), and no phrase or translation contains its own answer. "
     'Statements make sense on their own.'),
    ('labels-and-worlds', 'Determinacy labels, worlds and chains are right',
     'Each determinate answer holds in every valid world; each indeterminate query has concrete, differing '
     'answers per world; worlds list the premise that gives way and its side facts; chains are correct.'),
)


def manual_checks():
    reviews = load_reviews()
    out = []
    for key, title, what in MANUAL_RULES:
        marks = {r: bool(reviews.get(key, {}).get(r, {}).get('done')) for r, _ in REVIEWERS}
        status = 'pass' if all(marks.values()) else 'manual'
        c = check(title, title, status=status, note=what)
        c['rule'] = key
        c['reviews'] = [{'reviewer': r, 'label': label, **reviews.get(key, {}).get(r, {}), 'done': marks[r]}
                        for r, label in REVIEWERS]
        out.append(c)
    return out


# Rule 5: what counts as enough evidence (README, Evidence).
STORED_MIN_COUNT = 100     # an exact-phrase count at least this high, or a quoted sentence
DERIVED_MIN_SOURCES = 2    # corpus counts or searches showing the direct form is rare
FICTIONAL_MAX_COUNT = 5    # a made-up name should be (nearly) absent from text


def check_evidence(recs):
    weak = []
    for r in recs:
        for fact, e in (r.get('evidence') or {}).items():
            srcs = e.get('sources') or []
            counts = [x for x in srcs if x.get('kind') == 'infini-gram']
            if e.get('claim') == 'definitional':
                continue
            if e.get('claim') == 'fictional':
                ok = any((x.get('count') if x.get('count') is not None else 99) <= FICTIONAL_MAX_COUNT for x in counts) \
                    and any(x.get('kind') == 'search' for x in srcs)
                if not ok:
                    weak.append(f'{r["id"]}: fictional {fact!r}: needs a corpus count of at most '
                                f'{FICTIONAL_MAX_COUNT} for the made-up name and a search')
                continue
            if e.get('claim') == 'stored':
                ok = any(x.get('kind') in ('wikipedia', 'web') and x.get('quote') for x in srcs) or \
                     any((x.get('count') or 0) >= STORED_MIN_COUNT for x in counts)
                why = f'no quote and no count >= {STORED_MIN_COUNT}'
            else:
                ok = len(counts) + sum(x.get('kind') == 'search' for x in srcs) >= DERIVED_MIN_SOURCES
                why = f'fewer than {DERIVED_MIN_SOURCES} counts or searches'
            if not ok:
                weak.append(f'{r["id"]}: {e.get("claim")} {fact!r}: {why}')
    n = sum(len(r.get('evidence') or {}) for r in recs)
    note = (f'{n} evidence entries. Stored: a quoted sentence, or an exact-phrase count of at least '
            f'{STORED_MIN_COUNT}. Derived: at least {DERIVED_MIN_SOURCES} corpus counts or searches. The validator '
            'already requires an entry for every edited fact and premise.')
    return [check('', 'Every stored and derived claim has enough evidence', weak, note=note)]


# Rule 12: minimum coverage of relation properties, counted on replace
# records (deletes mirror them). ABox derived queries that use a property,
# and RBox edits that change one. Raise these as records are added.
ABOX_PROPERTY_MIN = {'transitivity': 10, 'chain': 10, 'subproperty': 10, 'functional': 10, 'inheritance': 10}
RBOX_PROPERTY_MIN = {'transitivity': 3, 'symmetry': 3, 'inverse': 3, 'subproperty': 3, 'chain': 8,
                     'functional': 8}
RBOX_GROUP = {'transitive': 'transitivity', 'symmetric': 'symmetry', 'asymmetric': 'symmetry',
              'inverse': 'inverse', 'subproperty': 'subproperty', 'chain': 'chain', 'functional': 'functional'}


# Properties of the edited relation itself (tags in RELATIONS.md), as opposed
# to how queries are derived. "none": the relation has no property that
# licenses a derivation. Some edits should be on such relations (a property-
# free fact is a real case), but not too many.
RELATION_PROPERTIES = ('symmetric', 'asymmetric', 'inverse', 'transitive', 'chain', 'subproperty', 'functional')
NONE_SHARE = (0.05, 0.25)   # share of ABox + TBox replace edits whose relation has no property
# How derived queries are derived, grouped for reading. Composition is a role
# chain built for one question; `chain` is one declared on the relation.
DERIVATION_GROUPS = (
    ('relation property', ('symmetry', 'asymmetry', 'inverse', 'transitivity', 'subproperty', 'functional')),
    ('chain', ('chain', 'composition')),
    ('class', ('inheritance', 'instantiation')),
    ('premise of a derived edit', ('premise',)),
    ('task framing', ('binding', 'application', 'scope')),
)


def relation_props(relations, name):
    tags = relations.get(name, (frozenset(), False))[0]
    return {t.split(':')[0] for t in tags} & set(RELATION_PROPERTIES)


def check_coverage(recs, relations):
    reps = [r for r in recs if r['edit_operation'] == 'replace']
    boxes = ('abox', 'tbox', 'rbox')

    # 1. Properties of the edited relations, with "none".
    props, total = Counter(), Counter(r['box'] for r in reps)
    for r in reps:
        p = relation_props(relations, r['relation'])
        for k in p or {'none'}:
            props[(k, r['box'])] += 1
    ptable = [['property of the edited relation', *boxes, 'all']]
    for k in (*RELATION_PROPERTIES, 'none'):
        ptable.append([k, *(props[(k, b)] for b in boxes), sum(props[(k, b)] for b in boxes)])
    ptable.append(['records', *(total[b] for b in boxes), sum(total.values())])
    at = total['abox'] + total['tbox']
    none = props[('none', 'abox')] + props[('none', 'tbox')]
    share = none / at if at else 0
    lo, hi = NONE_SHARE
    off = [] if not at or lo <= share <= hi else [
        f'{none} of {at} ABox and TBox edits ({share:.0%}) are on relations with no property; want {lo:.0%} to {hi:.0%}']

    # 2. How derived queries are derived, grouped.
    der = Counter((r['box'], q['derivation']) for r in reps for q in r['queries']['derived'])
    n_all = sum(der.values()) or 1
    dtable = [['group', 'derivation', *boxes, 'share']]
    for group, names in DERIVATION_GROUPS:
        g = sum(der[(b, d)] for b in boxes for d in names)
        dtable.append([group, '(all)', *(sum(der[(b, d)] for d in names) for b in boxes), f'{g / n_all:.1%}'])
        for d in names:
            n = sum(der[(b, d)] for b in boxes)
            if n:
                dtable.append(['', d, *(der[(b, d)] for b in boxes), f'{n / n_all:.1%}'])
    short = [f'ABox {d}: {der[("abox", d)]} queries, want at least {k}'
             for d, k in ABOX_PROPERTY_MIN.items() if der[('abox', d)] < k]

    # 3. Which property each RBox edit changes.
    rb = Counter(RBOX_GROUP.get(rbox_property(r), rbox_property(r)) for r in reps if r['box'] == 'rbox')
    rtable = [['RBox property edited', 'edits', 'minimum']] + [[p, rb[p], k] for p, k in RBOX_PROPERTY_MIN.items()]
    rshort = [f'RBox {p}: {rb[p]} edits, want at least {k}' for p, k in RBOX_PROPERTY_MIN.items() if rb[p] < k]
    return [
        check('', 'Edited relations: properties, and how many have none', off, table=ptable,
              note='What the edited relation itself carries (tags in RELATIONS.md); a relation can have several. '
                   f'"none": no property that licenses a derivation. Replace records; ABox and TBox edits on such '
                   f'relations should be {lo:.0%} to {hi:.0%} (RBox edits always have one).'),
        check('', 'Derived queries use every relation property', short, table=dtable,
              note='How each derived query reaches its answer, grouped. Chain: declared role chains and composition '
                   '(a chain built for one question). Task framing sorts by what the question asks the model to do; '
                   'the logic underneath is in each query\'s logic label. Minimums apply to ABox queries.'),
        check('', 'RBox edits cover every relation property', rshort, table=rtable),
    ]


# Rule 14: every core method runs on every edit, on the four main models.
RUN_EXPERIMENT = ROOT.parent.parent / 'experiments' / 'run_experiment'
SMOKE_RUNS = ROOT.parent.parent / 'results' / 'sids_smoke' / 'runs'
SMOKE_MODELS = AUDIT_MODELS


def core_methods():
    spec = json.loads((RUN_EXPERIMENT / 'dashboard.json').read_text())
    field = next(x for x in spec['fields'] if x['name'] == 'method')
    return [m['value'] for c in field['categories'] for m in c['methods'] if m.get('core')]


def hparams_dir(method):
    src = (RUN_EXPERIMENT / 'run_experiment.py').read_text()
    m = re.search(r'"%s":\s*"([^"]+)"' % re.escape(method), src.split('METHOD_HPARAMS_DIR = {', 1)[1].split('}', 1)[0])
    return m.group(1) if m else None


def check_methods_run(recs):
    sys.path.insert(0, str(RUN_EXPERIMENT))
    import sids_requests
    methods = core_methods()
    edits = [r for r in recs if r['edit_operation'] in ('replace', 'delete', 'insert')]
    fails = sids_requests.preflight(edits, methods)
    by_record = defaultdict(list)
    for (rid, m), msg in sorted(fails.items()):
        by_record[(rid, msg.split(': ', 2)[-1])].append(m)
    data_items = [f'{rid} [{", ".join(ms)}]: {msg}' for (rid, msg), ms in sorted(by_record.items())]
    for m in methods:
        d = hparams_dir(m)
        for model in SMOKE_MODELS:
            if not d or not (RUN_EXPERIMENT / 'hparams' / d / f'{model}.yaml').exists():
                data_items.append(f'{m} on {model}: no hparams file')
    by_err = Counter(msg.split(':', 1)[0] for msg in fails.values())
    note1 = (f'{len(methods)} core methods ({", ".join(methods)}) x {len(edits)} records x {len(SMOKE_MODELS)} models, '
             'checked without a GPU: each record becomes an edit request (prompt = direct question, target = new '
             "answer, or \"I don't know\" for delete), and methods that edit at the subject need it verbatim, once, "
             'in the prompt. ' + (f'Failures by kind: {dict(by_err)}.' if by_err else ''))

    current = sids_requests.records_hash(edits)
    smoke_items, missing, stale = [], [], []
    table = [['method', *SMOKE_MODELS]]
    for m in methods:
        row = [m]
        for model in SMOKE_MODELS:
            path = SMOKE_RUNS / f'smoke_{m}_{model}' / 'summary.json'
            try:
                summary = json.loads(path.read_text())
            except (OSError, ValueError):
                missing.append(f'{m} on {model}')
                row.append('not run')
                continue
            if summary.get('crashed'):
                smoke_items.append(f'{m} on {model}: crashed (exit {summary.get("exit_code")})')
                row.append('crashed')
            elif summary.get('records_hash') != current:
                stale.append(f'{m} on {model}')
                row.append('stale')
            else:
                row.append(f'{summary.get("ok", 0)}/{summary.get("records", 0)}')
                if summary.get('error'):
                    errs = [json.loads(l) for l in (path.parent / 'smoke.jsonl').read_text().splitlines() if l.strip()]
                    smoke_items += [f'{m} on {model}: {e["record"]}: {e.get("error")}: {e.get("message")}'
                                    for e in errs if e.get('status') == 'error']
    status = 'fail' if smoke_items else 'pending' if missing or stale else 'pass'
    note2 = ('From the Method smoke run on gaivi (results/sids_smoke): each core method applied to each record, '
             'checked to edit real weights, stay finite, keep generating and restore exactly. '
             + (f'Not run: {len(missing)} method-model pairs. ' if missing else '')
             + (f'Stale (records changed since): {len(stale)}. ' if stale else ''))
    return [
        check('', 'Every core method can take every record (data checks)', data_items, note=note1),
        check('', 'Every core method ran on every edit, on all four models (smoke run)', smoke_items,
              status=status, note=note2, table=table),
    ]


# Automated rules, in order. The delete rule comes last.
AUTOMATED_RULES = (
    ('No repeated edits', lambda recs, rel: check_repeats(recs)),
    ('Enough evidence for every fact', lambda recs, rel: check_evidence(recs)),
    ('The models hold the right things', lambda recs, rel: check_audit(recs)),
    ('Locality can catch leaks', lambda recs, rel: check_locality(recs)),
    ('One name per relation', lambda recs, rel: check_naming(recs, rel)),
    ('Yes/no answers balanced in RBox', lambda recs, rel: check_yes_no(recs)),
    ('Far locality prompts vary', lambda recs, rel: check_reuse(recs)),
    ('Belief-revision problems are covered', lambda recs, rel: check_problems(recs)),
    ('Relation properties are covered', lambda recs, rel: check_coverage(recs, rel)),
    ('Every method runs on every edit', lambda recs, rel: check_methods_run(recs)),
    ('Delete means "I don\'t know"', lambda recs, rel: check_delete(recs)),
)


def report():
    recs = load_records()
    relations, _ = load_relations()
    checks, n = [], 0
    for c in manual_checks():
        n += 1
        c['section'], c['kind'] = f'Rule {n}. {c["section"]}', 'manual'
        checks.append(c)
    for title, run in AUTOMATED_RULES:
        n += 1
        for c in run(recs, relations):
            c['section'], c['kind'] = f'Rule {n}. {title}', 'automated'
            checks.append(c)
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
    if argv[:1] == ['--mark']:
        # python criteria.py --mark <rule> <codex|claude|human> [done|pending] [--by NAME] [--note TEXT]
        args = argv[1:]
        opt = lambda flag: args[args.index(flag) + 1] if flag in args else None
        rule, reviewer = args[0], args[1]
        done = (args[2] if len(args) > 2 and not args[2].startswith('--') else 'done') == 'done'
        print(json.dumps(set_review(rule, reviewer, done, opt('--by'), opt('--note')), indent=2))
        return 0
    rep = report()
    if '--json' in argv:
        print(json.dumps(rep, ensure_ascii=False))
    else:
        print_report(rep, '--all' in argv)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
