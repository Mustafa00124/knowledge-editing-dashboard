#!/usr/bin/env python3
"""Which checker covers each derived query: HermiT (description logic,
reason.py) or Z3 (first-order logic with arithmetic, fol_check.py), and the
query's logic/theory label, so results can be sliced by where a question is
checked.

    venvs/easyedit_venv/bin/python datasets/SidsDataset/owl/coverage_labels.py            # write owl/COVERAGE.md, label both reports
    venvs/easyedit_venv/bin/python datasets/SidsDataset/owl/coverage_labels.py --print    # print the table only

A query's checker:
  hermit  its entry in the formal file's `queries` has `ask` or `find`
  z3      the formal file's `fol` section has an `ask` or `find` for it
  none    neither (not_checked, exception, or no formal file)

Label corrections (a fol query that is expressible in DL, or a dl query
that needs arithmetic) are read from the `fol` sections'
`label_corrections`; the records keep their labels.
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

OWL_DIR = Path(__file__).resolve().parent
ROOT = OWL_DIR.parent
FORMAL = OWL_DIR / 'formal'
COVERAGE = OWL_DIR / 'COVERAGE.md'
REPORTS = {'hermit': OWL_DIR / 'reason_report.json', 'z3': OWL_DIR / 'fol_report.json'}


def load_formal(rid):
    p = FORMAL / f'{rid}.json'
    return json.loads(p.read_text()) if p.exists() else {}


def query_labels(rec, formal=None):
    """[{q, logic, theory, checker, determinacy}] for every derived query of a record."""
    f = load_formal(rec['id']) if formal is None else formal
    dl = {q['q']: q for q in f.get('queries') or []}
    fol = {q['q']: q for q in (f.get('fol') or {}).get('queries') or []}
    out = []
    for i, q in enumerate(rec['queries']['derived']):
        if 'ask' in dl.get(i, {}) or 'find' in dl.get(i, {}):
            checker = 'hermit'
        elif 'ask' in fol.get(i, {}) or 'find' in fol.get(i, {}):
            checker = 'z3'
        else:
            checker = 'none'
        out.append({'q': i, 'logic': q.get('logic'), 'theory': q.get('theory'), 'checker': checker,
                    'determinacy': q.get('determinacy')})
    return out


def all_records(topic=None):
    for p in sorted((ROOT / 'records').glob(f'{topic or "*"}/*/*.json')):
        yield json.loads(p.read_text())


def annotate(report, checker):
    """Give every check in a report (checker: 'hermit' for reason_report.json,
    'z3' for fol_report.json) its checker, and every query check its logic
    and theory; give every record a `queries` list with each derived
    query's label and checker (in place). A reason.py not_checked entry for a
    query Z3 checks gets checker 'z3': the answer is in fol_report.json."""
    recs = {r['id']: r for r in all_records()}
    for rid, entry in (report.get('records') or {}).items():
        if rid not in recs:
            continue
        labels = query_labels(recs[rid])
        entry['queries'] = labels
        by_q = {l['q']: l for l in labels}
        for c in entry.get('checks') or []:
            if 'q' in c and c['q'] in by_q:
                l = by_q[c['q']]
                c['logic'], c['theory'], c['checker'] = l['logic'], l['theory'], l['checker']
            elif c['check'] not in ('encoding', 'error'):
                c['checker'] = checker
    return report


def relabel_reports():
    for kind, path in REPORTS.items():
        if path.exists():
            rep = json.loads(path.read_text())
            annotate(rep, kind)
            path.write_text(json.dumps(rep, ensure_ascii=False, indent=1) + '\n')


def table():
    """Rows per topic: dl via HermiT, dl unchecked, fol via Z3, fol unchecked, propositional (by checker)."""
    counts = defaultdict(Counter)
    corrections = []
    for rec in all_records():
        t = rec['topic']
        f = load_formal(rec['id'])
        for l in query_labels(rec, f):
            counts[t][(l['logic'], l['checker'])] += 1
        for c in (f.get('fol') or {}).get('label_corrections') or []:
            q = rec['queries']['derived'][c['q']]
            corrections.append((rec['id'], c['q'], c.get('from', q.get('logic')), c.get('to'), c.get('why', ''),
                                q['prompt']))
    return counts, corrections


def render(counts, corrections):
    cols = [('dl', 'hermit'), ('dl', 'none'), ('fol', 'z3'), ('fol', 'hermit'), ('fol', 'none'),
            ('propositional', 'hermit'), ('propositional', 'none')]
    head = ['topic', 'dl via HermiT', 'dl not checked', 'fol via Z3', 'fol via HermiT', 'fol not checked',
            'propositional via HermiT', 'propositional not checked', 'total']
    lines = ['| ' + ' | '.join(head) + ' |', '|' + '---|' * len(head)]
    tot = Counter()
    for t in sorted(counts):
        row = [counts[t][c] for c in cols]
        tot.update(counts[t])
        lines.append(f'| {t} | ' + ' | '.join(map(str, row)) + f' | {sum(counts[t].values())} |')
    lines.append('| **all** | ' + ' | '.join(str(tot[c]) for c in cols) + f' | {sum(tot.values())} |')
    other = {k: v for k, v in tot.items() if k not in cols}
    out = '\n'.join(lines)
    if other:
        out += '\n\nOther labels: ' + ', '.join(f'{k[0]}/{k[1]} {v}' for k, v in sorted(other.items(), key=str))
    corr = ['| record | q | label | should be | why | prompt |', '|---|---|---|---|---|---|']
    for rid, q, a, b, why, prompt in corrections:
        corr.append(f'| {rid} | {q} | {a} | {b} | {why} | {prompt} |')
    return out, '\n'.join(corr) if corrections else '(none recorded)'


def write_md():
    counts, corrections = table()
    tab, corr = render(counts, corrections)
    COVERAGE.write_text(f"""# Formal check coverage

Generated by `owl/coverage_labels.py` (rerun after encoding). Each derived query is
checked by one checker: **HermiT** (`reason.py`, OWL 2 description logic,
the formal file's `queries`), **Z3** (`fol_check.py`, first-order logic with
integer, real and string arithmetic, the formal file's `fol` section), or
none. Both reports (`reason_report.json`, `fol_report.json`) carry
`checker`, `logic` and `theory` on every query check and a `queries` list per
record, so results can be split by where a question is checked (do editing
failures concentrate in the fol questions?).

Columns are logic label / checker. "not checked" means the formal file
marks the query `not_checked` or `exception` (or the topic has no `fol`
sections yet).

{tab}

## Label corrections

Queries whose `logic` label looks wrong after encoding: a `fol` one that
description logic can express (it could move to HermiT), or a `dl` one that
needs arithmetic. Listed in the `fol` sections' `label_corrections`; the
records are unchanged.

{corr}
""")


def main(argv):
    if '--print' in argv:
        counts, corrections = table()
        tab, corr = render(counts, corrections)
        print(tab)
        print()
        print(corr)
        return 0
    write_md()
    relabel_reports()
    print('wrote owl/COVERAGE.md and labelled', ', '.join(p.name for p in REPORTS.values() if p.exists()))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
