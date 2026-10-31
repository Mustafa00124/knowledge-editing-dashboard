#!/usr/bin/env python3
"""Which checker covers each derived query: HermiT (description logic,
reason.py) or Z3 (first-order logic with arithmetic, fol_check.py), and the
query's logic/theory label, so results can be sliced by where a question is
checked.

    venvs/easyedit_venv/bin/python datasets/SidsDataset/owl/coverage_labels.py            # write owl/COVERAGE.md, label both reports
    venvs/easyedit_venv/bin/python datasets/SidsDataset/owl/coverage_labels.py --print    # print the table only

Routing: the query's `logic` label decides its primary checker.
  dl, propositional  hermit (its entry in the formal file's `queries` has `ask` or `find`)
  fol                z3 (the formal file's `fol` section has an `ask` or `find` for it)
A query encoded for both keeps the other as a second check (`second`): a
dl query whose old Z3 encoding stays in the `fol` section, or a fol query
HermiT can also check. When the labelled checker has no encoding, the other
one (if any) is the checker, and the table shows it (e.g. "dl via Z3 only");
`none` means neither encodes it (not_checked, exception, or no formal file).

Label corrections (a fol query that is expressible in DL, or a dl query
that needs arithmetic) proposed in the `fol` sections' `label_corrections`
are applied to the records by hand; an entry left there is one that was
reviewed and rejected (`"status": "rejected"`, with `rejected_why`).
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
        enc = [c for c, d in (('hermit', dl), ('z3', fol)) if 'ask' in d.get(i, {}) or 'find' in d.get(i, {})]
        want = 'z3' if q.get('logic') == 'fol' else 'hermit'
        if want in enc:
            checker = want
        else:
            checker = enc[0] if enc else 'none'
        second = next((c for c in enc if c != checker), None)
        out.append({'q': i, 'logic': q.get('logic'), 'theory': q.get('theory'), 'checker': checker,
                    'second': second, 'determinacy': q.get('determinacy')})
    return out


def all_records(topic=None):
    for p in sorted((ROOT / 'records').glob(f'{topic or "*"}/*/*.json')):
        yield json.loads(p.read_text())


def annotate(report, checker):
    """Give every check in a report (checker: 'hermit' for reason_report.json,
    'z3' for fol_report.json) its checker, and every query check its logic
    and theory; give every record a `queries` list with each derived
    query's label and checker (in place). A not_checked entry for a query
    the other checker checks gets that checker (the answer is in the other
    report); a real check keeps this report's checker and says whether it
    is the query's primary check (`primary`)."""
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
                c['logic'], c['theory'] = l['logic'], l['theory']
                if c['check'] == 'not_checked':
                    c['checker'] = l['checker']
                    c.pop('primary', None)
                else:
                    c['checker'] = checker
                    c['primary'] = l['checker'] == checker
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
            if l['second']:
                counts[t][('second', l['logic'], l['second'])] += 1
        for c in (f.get('fol') or {}).get('label_corrections') or []:
            q = rec['queries']['derived'][c['q']]
            corrections.append((rec['id'], c['q'], c.get('from', q.get('logic')), c.get('to'), c.get('why', ''),
                                q['prompt'], c.get('status', 'proposed'), c.get('rejected_why', '')))
    return counts, corrections


def render(counts, corrections):
    cols = [('dl', 'hermit'), ('dl', 'z3'), ('dl', 'none'), ('fol', 'z3'), ('fol', 'hermit'), ('fol', 'none'),
            ('propositional', 'hermit'), ('propositional', 'none')]
    head = ['topic', 'dl via HermiT', 'dl via Z3 only', 'dl not checked', 'fol via Z3', 'fol via HermiT only',
            'fol not checked', 'propositional via HermiT', 'propositional not checked', 'total']
    lines = ['| ' + ' | '.join(head) + ' |', '|' + '---|' * len(head)]
    tot = Counter()
    seconds = Counter()
    for t in sorted(counts):
        seconds.update({k: v for k, v in counts[t].items() if k[0] == 'second'})
        counts[t] = Counter({k: v for k, v in counts[t].items() if k[0] != 'second'})
        row = [counts[t][c] for c in cols]
        tot.update(counts[t])
        lines.append(f'| {t} | ' + ' | '.join(map(str, row)) + f' | {sum(counts[t].values())} |')
    lines.append('| **all** | ' + ' | '.join(str(tot[c]) for c in cols) + f' | {sum(tot.values())} |')
    other = {k: v for k, v in tot.items() if k not in cols}
    out = '\n'.join(lines)
    if other:
        out += '\n\nOther labels: ' + ', '.join(f'{k[0]}/{k[1]} {v}' for k, v in sorted(other.items(), key=str))
    names = {'hermit': 'HermiT', 'z3': 'Z3'}
    out += '\n\nSecond checks (also encoded for the other checker): ' + (', '.join(
        f'{v} {k[1]} also via {names[k[2]]}' for k, v in sorted(seconds.items())) or 'none') + '.'
    corr = ['| record | q | label | proposed | status | why proposed | why rejected | prompt |',
            '|---|---|---|---|---|---|---|---|']
    for rid, q, a, b, why, prompt, status, rwhy in corrections:
        corr.append(f'| {rid} | {q} | {a} | {b} | {status} | {why} | {rwhy} | {prompt} |')
    return out, '\n'.join(corr) if corrections else '(none outstanding)'


def write_md():
    counts, corrections = table()
    tab, corr = render(counts, corrections)
    COVERAGE.write_text(f"""# Formal check coverage

Generated by `owl/coverage_labels.py` (rerun after encoding). Each derived query is
checked first by the checker its `logic` label names: `dl` (and
`propositional`) by **HermiT** (`reason.py`, OWL 2 description logic, the
formal file's `queries`), `fol` by **Z3** (`fol_check.py`, first-order logic
with integer, real and string arithmetic, the formal file's `fol` section).
A query encoded for both keeps the other as a second check (counted below
the table); "via Z3 only" / "via HermiT only" means the labelled checker has
no encoding. Both reports (`reason_report.json`, `fol_report.json`) carry
`checker`, `logic` and `theory` on every query check and a `queries` list per
record, so results can be split by where a question is checked (do editing
failures concentrate in the fol questions?).

Columns are logic label / checker. "not checked" means the formal file
marks the query `not_checked` or `exception` for both checkers.

{tab}

## Label corrections

Queries whose `logic` label looked wrong after encoding (a `fol` one that
description logic can express, or a `dl` one that needs more) are proposed
in the `fol` sections' `label_corrections` and, once reviewed, applied to
the records (2026-10-31: 88 fol -> dl, 2 dl -> fol). The entries left are
the proposals reviewed and rejected, with why; their records keep `fol`.

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
