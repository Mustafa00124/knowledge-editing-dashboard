#!/usr/bin/env python3
"""Report how Sid's Dataset records meet CRITERIA.md.

Report only for now: it lists what breaks each criterion and always exits 0.
A check moves into validate.py's errors once the records meet it.

    python datasets/SidsDataset/criteria.py          # or: validate.py --criteria
    python datasets/SidsDataset/criteria.py --all    # every offending id, not the first few

Standard library only, like validate.py.
"""
import json
import re
import sys
from collections import Counter, defaultdict
from difflib import SequenceMatcher

from validate import (DERIVABILITY, FAMILIARITY, FAMILIARITY_TIERS, ROOT, TOPICS,
                      load_relations)

# Provisional numbers; CRITERIA.md is where they get agreed.
SIMILAR_STATEMENT = 0.9   # difflib ratio above which two edits are listed as near repeats
MAX_FAR_REUSE = 10        # times one far unrelated prompt may appear in the dataset
# Derivation mix targets, {(box, derivation): share of that box's derived queries}.
# Empty until CRITERIA.md section 6 has numbers; the counts are reported either way.
DERIVATION_TARGETS = {}
RBOX_PROPERTY_TARGETS = {}

YES = {'yes', '是', 'sí', 'si'}
NO = {'no', '否', '不是'}
RBOX_PROPERTIES = (('InvFunc', 'inverse_functional'), ('Asym', 'asymmetric'), ('Sym', 'symmetric'),
                   ('Trans', 'transitive'), ('Func', 'functional'), ('Refl', 'reflexive'),
                   ('Disj', 'disjoint'))
STATEMENT_WORDS = (('inverse functional', 'inverse_functional'), ('asymmetric', 'asymmetric'),
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


class Report:
    def __init__(self, show_all):
        self.show_all, self.failed = show_all, []

    def section(self, title):
        print(f'\n## {title}')

    def problem(self, name, items):
        """Print a criterion's offenders; an empty list is a pass."""
        items = list(items)
        status = 'ok' if not items else f'{len(items)} to fix'
        print(f'- {name}: {status}')
        if items:
            self.failed.append(name)
        for item in items if self.show_all else items[:8]:
            print(f'    {item}')
        if items and not self.show_all and len(items) > 8:
            print(f'    ... {len(items) - 8} more (--all)')


def check_repeats(recs, rep):
    rep.section('1. No repeated edits')
    # Delete records restate replace's facts by design, so compare insert and
    # replace only; delete is checked against its replace record in section 2.
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
    rep.problem('same statement', [', '.join(v) for v in by_statement.values() if len(v) > 1])
    rep.problem('same subject, relation and object (RBox: same relation and axiom kind)',
                [f'{", ".join(v)}  {k}' for k, v in by_triple.items() if len(v) > 1])
    near = []
    by_group = defaultdict(list)
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
    rep.problem(f'near repeats (similarity >= {SIMILAR_STATEMENT}, review by hand)', near)


def check_delete(recs, rep):
    rep.section('2. Delete: ground label is "I don\'t know"')
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
    rep.problem('delete record without a replace record of the same number', unpaired)
    rep.problem('delete statement differs from its replace record\'s original fact', mismatched)
    rep.problem('delete query with an expected answer other than "I don\'t know"', answered)


def check_yes_no(recs, rep):
    rep.section('3. Yes/no balance (RBox 50/50)')
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
    off = []
    for op in ('insert', 'replace'):
        for qtype in ('direct', 'derived', 'cross_lingual'):
            y = sum(n for (o, t, _, v), n in counts.items() if (o, t, v) == (op, qtype, 'yes'))
            n_ = sum(n for (o, t, _, v), n in counts.items() if (o, t, v) == (op, qtype, 'no'))
            print(f'    {op:8} {qtype:14} yes {y:4}  no {n_:4}')
            if y != n_:
                off.append(f'{op} {qtype}: {y} yes / {n_} no')
            for topic in TOPICS:
                ty, tn = counts[(op, qtype, topic, 'yes')], counts[(op, qtype, topic, 'no')]
                if abs(ty - tn) > 1:
                    off.append(f'{op} {qtype} {topic}: {ty} yes / {tn} no')
    rep.problem('RBox yes/no imbalance (overall must be equal, per topic within 1)', off)
    # Not a criterion yet: the same split for ABox and TBox, for the open question.
    other = Counter()
    for r in recs:
        if r['box'] != 'rbox' and r['edit_operation'] != 'delete':
            for item in [r['queries']['direct'], r['queries']['paraphrase'], *r['queries']['derived']]:
                v = yes_no(item.get('new_answer'))
                if v:
                    other[(r['box'], v)] += 1
    print('    (ABox/TBox, not yet a criterion: ' + ', '.join(
        f'{b} {other[(b, "yes")]} yes / {other[(b, "no")]} no' for b in ('abox', 'tbox')) + ')')


def check_locality(recs, rep):
    rep.section('5. Locality can detect leaking')
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
    rep.problem('near unrelated reference equals the edited answer', leaks)


def check_mix(recs, rep):
    rep.section('6. Relation property mix (counts; targets not set yet)')
    der = Counter()
    for r in recs:
        if r['box'] != 'rbox':
            for q in r['queries']['derived']:
                der[(r['box'], r['relation_semantics'], q['derivation'])] += 1
    for box in ('abox', 'tbox'):
        total = sum(n for (b, _, _), n in der.items() if b == box)
        names = sorted({d for (b, _, d) in der if b == box}, key=lambda d: -sum(
            n for (b, _, dd), n in der.items() if b == box and dd == d))
        print(f'    {box} derived queries ({total}): derivation  associative / causal')
        for d in names:
            a, c = der[(box, 'associative', d)], der[(box, 'causal', d)]
            print(f'      {d:14} {a + c:5} ({(a + c) / total:5.1%})   {a:4} / {c:4}')
    # Delete records drop the axiom; they remove the property their replace record flips.
    by_id = {r['id']: r for r in recs}
    rbox = Counter((r['edit_operation'], rbox_property(by_id.get(r['id'].replace('-delete-', '-replace-'), r)))
                   for r in recs if r['box'] == 'rbox')
    props = sorted({p for _, p in rbox})
    print('    rbox edits by property: ' + ', '.join(
        f'{p} {"/".join(str(rbox[(op, p)]) for op in ("insert", "replace", "delete"))}' for p in props)
          + '  (insert/replace/delete)')
    misses = []
    for (box, d), share in DERIVATION_TARGETS.items():
        total = sum(n for (b, _, _), n in der.items() if b == box) or 1
        got = sum(n for (b, _, dd), n in der.items() if b == box and dd == d) / total
        if got < share:
            misses.append(f'{box} {d}: {got:.1%} < target {share:.0%}')
    for (op, p), n in RBOX_PROPERTY_TARGETS.items():
        if rbox[(op, p)] != n:
            misses.append(f'rbox {op} {p}: {rbox[(op, p)]} edits, target {n}')
    rep.problem('derivation or RBox property mix off target', misses)


def check_naming(recs, relations, rep):
    rep.section('Relation names')
    used = defaultdict(list)
    for r in recs:
        used[r['relation']].append(r['id'])
        if r['box'] == 'rbox':
            for name in IDENT.findall(r['edit'].get('axiom') or ''):
                if name not in DL_WORDS:
                    if r['id'] not in used[name]:
                        used[name].append(r['id'])
    rep.problem('not snake_case', [f'{n} ({", ".join(v[:3])})' for n, v in sorted(used.items())
                                   if not SNAKE.fullmatch(n)])
    rep.problem('not in RELATIONS.md', [f'{n} ({", ".join(v[:3])})' for n, v in sorted(used.items())
                                        if n not in relations])
    # Names that may be one relation spelled twice: equal once has_/is_ are dropped.
    stem = defaultdict(set)
    for n in set(used) | set(relations):
        stem[re.sub(r'^(has|is)_', '', n)].add(n)
    rep.problem('possibly one relation under two names (review by hand)',
                [' / '.join(sorted(v)) for v in stem.values() if len(v) > 1])


def check_reuse(recs, rep):
    rep.section('7. Far unrelated prompt reuse')
    far = Counter(q['prompt'] for r in recs for q in r['queries'].get('unrelated_far') or [])
    print(f'    {len(far)} distinct far prompts over {sum(far.values())} queries')
    rep.problem(f'far prompt used more than {MAX_FAR_REUSE} times',
                [f'{n:3}x {p}' for p, n in far.most_common() if n > MAX_FAR_REUSE])


def spread(recs):
    print('\n## Tag spread (report only)')
    for tier in FAMILIARITY_TIERS:
        c = Counter((r['edit_operation'], (r.get('familiarity') or {}).get(tier)) for r in recs)
        print(f'    familiarity.{tier:8} ' + '  '.join(
            f'{op}: ' + ' '.join(str(c[(op, v)]) for v in FAMILIARITY) for op in ('insert', 'replace')))
    c = Counter(r.get('derivability') for r in recs if r['edit_operation'] == 'replace')
    print('    derivability (replace) ' + ' '.join(f'{v} {c[v]}' for v in DERIVABILITY))
    print(f'    (familiarity columns: {" ".join(FAMILIARITY)})')


def main(argv):
    rep = Report('--all' in argv)
    recs = load_records()
    relations, _ = load_relations()
    print(f'# Criteria report: {len(recs)} records (CRITERIA.md)')
    check_repeats(recs, rep)
    check_delete(recs, rep)
    check_yes_no(recs, rep)
    print('\n## 4. No ambiguity\n- not checkable by script: needs an LLM pass and a person (CRITERIA.md section 4)')
    check_locality(recs, rep)
    check_mix(recs, rep)
    check_naming(recs, relations, rep)
    check_reuse(recs, rep)
    spread(recs)
    print(f'\n{len(rep.failed)} criteria with something to fix' + (': ' + '; '.join(rep.failed) if rep.failed else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
