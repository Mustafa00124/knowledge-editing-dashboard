#!/usr/bin/env python3
"""Check the fol derived queries of Sid's Dataset with Z3 (SMT), from the
`fol` section of owl/formal/<record_id>.json (schema: owl/README.md, "The fol
section").

    venvs/easyedit_venv/bin/python datasets/SidsDataset/fol_check.py                       # every file with a fol section
    venvs/easyedit_venv/bin/python datasets/SidsDataset/fol_check.py --topic mathematics
    venvs/easyedit_venv/bin/python datasets/SidsDataset/fol_check.py mathematics-replace-0003 ...
    ... --no-write      check and print, leave owl/fol_report.json alone
    ... --static        only the file-against-record checks (no solving)

The checks are reason.py's, for the fol queries:

  pre              the original answer follows before the edit, in every world
  post_determinate a determinate (or unlabelled) query's new answer follows in every world
  post_worlds      an indeterminate query's world answer follows in that world
  differ           those answers differ between at least two worlds
  consistent       every world is satisfiable before and after the edit
                   (delete: and the deleted fact no longer follows)
  not_checked      fol queries the section leaves out, with why
  encoding         the section disagrees with its record or ATTRIBUTES.md

"Follows" is entailment: a yes needs the claim's negation to be unsat with
the knowledge base, a value v needs `expr != v` to be unsat (so v is also
the only value), a null (does not know) needs nothing to follow. Every
entailment comes with its unsat core, minimised by deletion: the fewest
named facts and rules that force the answer, the Z3 counterpart of an OWL
justification. Writes owl/fol_report.json (records not run keep their old
entry); always exits 0.
"""
import argparse
import ast
import json
import re
import sys
import time
from collections import Counter
from fractions import Fraction
from multiprocessing import Pool
from pathlib import Path

import z3

ROOT = Path(__file__).resolve().parent
OWL_DIR = ROOT / 'owl'
sys.path.insert(0, str(OWL_DIR))
import coverage_labels as CV  # noqa: E402
FORMAL = OWL_DIR / 'formal'
REPORT = OWL_DIR / 'fol_report.json'
ATTRIBUTES = ROOT / 'ATTRIBUTES.md'
TIMEOUT_MS = 10000
MINIMISE_TIMEOUT_MS = 2000

_counter = [0]


# ---------------------------------------------------------------- record helpers

def load_record(rid):
    hits = list((ROOT / 'records').glob(f'*/*/{rid}.json'))
    if not hits:
        raise FileNotFoundError(f'no record {rid}')
    return json.loads(hits[0].read_text())


def load_formal(rid):
    p = FORMAL / f'{rid}.json'
    return json.loads(p.read_text()) if p.exists() else None


def norm(s):
    s = re.sub(r'[^\w\s]', ' ', str(s).lower())
    s = re.sub(r'^\s*(the|a|an)\s+', '', s)
    return ' '.join(s.split())


def yes_no(s):
    if s is None:
        return None
    n = norm(s)
    if n.startswith('yes'):
        return 'yes'
    if n.startswith('no') and not n.startswith('none'):
        return 'no'
    return '?'


def load_attributes(path=ATTRIBUTES):
    """{name: {'type', 'unit', 'reads', 'relation'}} from ATTRIBUTES.md's tables."""
    out = {}
    if not path.exists():
        return out
    for line in path.read_text().splitlines():
        m = re.match(r'\|\s*`([a-z0-9_]+)`\s*\|(.*)\|\s*$', line)
        if not m:
            continue
        cells = [c.strip() for c in m.group(2).split('|')]
        out[m.group(1)] = {'type': cells[0] if cells else '', 'unit': cells[1] if len(cells) > 1 else '',
                           'reads': cells[2] if len(cells) > 2 else '',
                           'relation': cells[4] if len(cells) > 4 else ''}
    return out


def load_relation_names():
    """Relation names catalogued in RELATIONS.md (first backticked cell of a table row)."""
    p = ROOT / 'RELATIONS.md'
    return set(re.findall(r'^\|\s*`([a-z0-9_]+)`\s*\|', p.read_text(), re.M)) if p.exists() else set()


# ---------------------------------------------------------------- expressions

BASE_SORTS = {'Int': z3.IntSort, 'Real': z3.RealSort, 'Bool': z3.BoolSort, 'String': z3.StringSort}


class Env:
    """The declarations of one fol section: sorts, constants, functions,
    quantifier variables, and a compiler from the Python-like expression
    syntax to Z3 terms."""

    def __init__(self, decl):
        self.sorts = {k: f() for k, f in BASE_SORTS.items()}
        self.values = {}            # enum value name -> constant
        self.syms = {}
        self.funcs = {}             # name -> (arg sorts, result sort name)
        for name, vals in (decl.get('sorts') or {}).items():
            _counter[0] += 1
            if vals:
                s, consts = z3.EnumSort(f'{name}_{_counter[0]}', list(vals))
                for v, c in zip(vals, consts):
                    if v in self.values:
                        raise ValueError(f'enum value {v!r} declared twice')
                    self.values[v] = c
            else:
                s = z3.DeclareSort(f'{name}_{_counter[0]}')
            self.sorts[name] = s
        for name, sort in (decl.get('consts') or {}).items():
            self.syms[name] = z3.Const(name, self.sort(sort))
        for name, sort in (decl.get('vars') or {}).items():
            self.syms[name] = z3.Const(name, self.sort(sort))
        for name, sig in (decl.get('funcs') or {}).items():
            if '->' not in sig:
                raise ValueError(f'function {name}: signature {sig!r} needs "->"')
            args, res = sig.split('->')
            arg_sorts = [self.sort(a) for a in args.split()]
            self.syms[name] = z3.Function(name, *arg_sorts, self.sort(res.strip()))
            self.funcs[name] = (args.split(), res.strip())
        clash = set(self.syms) & set(self.values)
        if clash:
            raise ValueError(f'names used twice: {sorted(clash)}')

    def sort(self, name):
        name = name.strip()
        if name not in self.sorts:
            raise ValueError(f'unknown sort {name!r}')
        return self.sorts[name]

    # ----- compiler
    def compile(self, text):
        try:
            tree = ast.parse(text.strip(), mode='eval').body
        except SyntaxError as e:
            raise ValueError(f'syntax error in {text!r}: {e.msg}')
        return self.ex(tree, text)

    def ex(self, n, text):
        e = lambda x: self.ex(x, text)   # noqa: E731
        if isinstance(n, ast.Constant):
            v = n.value
            if isinstance(v, bool):
                return z3.BoolVal(v)
            if isinstance(v, int):
                return z3.IntVal(v)
            if isinstance(v, float):
                return z3.RealVal(repr(v))
            if isinstance(v, str):
                return z3.StringVal(v)
        if isinstance(n, ast.Name):
            if n.id in self.syms:
                return self.syms[n.id]
            if n.id in self.values:
                return self.values[n.id]
            raise ValueError(f'undeclared name {n.id!r} in {text!r}')
        if isinstance(n, ast.BoolOp):
            parts = [e(v) for v in n.values]
            return z3.And(*parts) if isinstance(n.op, ast.And) else z3.Or(*parts)
        if isinstance(n, ast.UnaryOp):
            v = e(n.operand)
            if isinstance(n.op, ast.Not):
                return z3.Not(v)
            if isinstance(n.op, ast.USub):
                return -v
            if isinstance(n.op, ast.UAdd):
                return v
        if isinstance(n, ast.BinOp):
            a, b = e(n.left), e(n.right)
            op = n.op
            if isinstance(op, ast.Add):
                return z3.Concat(a, b) if z3.is_string(a) else a + b
            if isinstance(op, ast.Sub):
                return a - b
            if isinstance(op, ast.Mult):
                return a * b
            if isinstance(op, ast.Div):
                if z3.is_int(a) and z3.is_int(b):
                    a = z3.ToReal(a)
                return a / b
            if isinstance(op, ast.FloorDiv):
                return a / b
            if isinstance(op, ast.Mod):
                return a % b
            if isinstance(op, ast.Pow):
                if isinstance(n.right, ast.Constant) and isinstance(n.right.value, int) and n.right.value >= 1:
                    out = a
                    for _ in range(n.right.value - 1):
                        out = out * a
                    return out
                raise ValueError(f'** needs a whole-number literal exponent: {text!r}')
        if isinstance(n, ast.Compare):
            left, parts = e(n.left), []
            for op, right in zip(n.ops, n.comparators):
                r = e(right)
                f = {ast.Eq: lambda x, y: x == y, ast.NotEq: lambda x, y: x != y, ast.Lt: lambda x, y: x < y,
                     ast.LtE: lambda x, y: x <= y, ast.Gt: lambda x, y: x > y, ast.GtE: lambda x, y: x >= y}.get(type(op))
                if f is None:
                    raise ValueError(f'unsupported comparison in {text!r}')
                parts.append(f(left, r))
                left = r
            return parts[0] if len(parts) == 1 else z3.And(*parts)
        if isinstance(n, ast.IfExp):
            return z3.If(e(n.test), e(n.body), e(n.orelse))
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
            f, args = n.func.id, n.args
            if f in ('ForAll', 'Exists'):
                if len(args) != 2:
                    raise ValueError(f'{f}(vars, body) in {text!r}')
                vs = args[0].elts if isinstance(args[0], (ast.List, ast.Tuple)) else [args[0]]
                bound = [e(v) for v in vs]
                return (z3.ForAll if f == 'ForAll' else z3.Exists)(bound, e(args[1]))
            if f in ('All', 'Some'):
                # All(x, [a, b], body) / All([x, y], [(a, b), (c, d)], body): a quantifier over a
                # finite list, expanded into a conjunction (disjunction) of instances.
                if len(args) != 3 or not isinstance(args[1], (ast.List, ast.Tuple)):
                    raise ValueError(f'{f}(var(s), [values], body) in {text!r}')
                vs = args[0].elts if isinstance(args[0], (ast.List, ast.Tuple)) else [args[0]]
                bound = [e(v) for v in vs]
                body = e(args[2])
                inst = []
                for row in args[1].elts:
                    vals = row.elts if isinstance(row, ast.Tuple) else [row]
                    if len(vals) != len(bound):
                        raise ValueError(f'{f}: {len(bound)} variables but a row of {len(vals)} in {text!r}')
                    inst.append(z3.substitute(body, *[(b, _coerce(e(v), b.sort())) for b, v in zip(bound, vals)]))
                return (z3.And if f == 'All' else z3.Or)(*inst) if inst else z3.BoolVal(f == 'All')
            if f in self.syms and f in self.funcs:
                return self.syms[f](*[e(a) for a in args])
            vals = [e(a) for a in args]
            simple = {
                'And': lambda: z3.And(*vals), 'Or': lambda: z3.Or(*vals), 'Not': lambda: z3.Not(vals[0]),
                'Implies': lambda: z3.Implies(vals[0], vals[1]), 'Iff': lambda: vals[0] == vals[1],
                'If': lambda: z3.If(vals[0], vals[1], vals[2]), 'Distinct': lambda: z3.Distinct(*vals),
                'abs': lambda: z3.If(vals[0] < 0, -vals[0], vals[0]),
                'min': lambda: _fold(vals, lambda x, y: z3.If(x <= y, x, y)),
                'max': lambda: _fold(vals, lambda x, y: z3.If(x >= y, x, y)),
                'count': lambda: z3.Sum([z3.If(v, 1, 0) for v in vals]),
                'Sum': lambda: z3.Sum(vals), 'ToReal': lambda: z3.ToReal(vals[0]), 'ToInt': lambda: z3.ToInt(vals[0]),
                'len': lambda: z3.Length(vals[0]),
                'startswith': lambda: z3.PrefixOf(vals[1], vals[0]), 'endswith': lambda: z3.SuffixOf(vals[1], vals[0]),
                'contains': lambda: z3.Contains(vals[0], vals[1]),
                'replace': lambda: z3.Replace(vals[0], vals[1], vals[2]),
                'strip_prefix': lambda: z3.SubString(vals[0], z3.Length(vals[1]), z3.Length(vals[0]) - z3.Length(vals[1])),
                'strip_suffix': lambda: z3.SubString(vals[0], 0, z3.Length(vals[0]) - z3.Length(vals[1])),
                'round_to': lambda: z3.ToReal(z3.ToInt(vals[0] * _pow10(vals[1]) + z3.RealVal('1/2'))) / _pow10(vals[1]),
            }
            if f in simple:
                return simple[f]()
            raise ValueError(f'unknown function {f!r} in {text!r}')
        raise ValueError(f'unsupported syntax {type(n).__name__} in {text!r}')


def _coerce(v, sort):
    """An Int value bound to a Real variable becomes a Real."""
    if sort.kind() == z3.Z3_REAL_SORT and z3.is_int(v):
        return z3.simplify(z3.ToReal(v))
    return v


def _fold(vals, f):
    out = vals[0]
    for v in vals[1:]:
        out = f(out, v)
    return out


def _pow10(v):
    k = v.as_long() if z3.is_int_value(v) else int(str(v))
    return z3.RealVal(10 ** k)


# ---------------------------------------------------------------- answer strings -> values

NUMBER_WORDS = {w: i for i, w in enumerate(
    'zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen '
    'seventeen eighteen nineteen twenty'.split())}
MONTHS = {m: i for i, m in enumerate('january february march april may june july august september october '
                                     'november december'.split(), 1)}


def parse_number(s):
    """The first number in an answer string: '250 degrees' -> 250, '−1' -> -1,
    '3.14' -> Fraction, '1/2' -> 1/2, 'two' -> 2, '1,864' -> 1864."""
    t = str(s).replace('−', '-').replace('–', '-').replace(',', '')
    m = re.search(r'[-+]?\d+(?:\.\d+)?(?:/\d+)?', t)
    if m:
        x = m.group(0)
        return Fraction(x) if ('.' in x or '/' in x) else int(x)
    for w in norm(s).split():
        if w in NUMBER_WORDS:
            return NUMBER_WORDS[w]
    return None


def parse_clock(s):
    """Time of day in minutes after midnight: 'noon' 720, '1 PM' 780, '13:30' 810."""
    n = str(s).lower().strip()
    if 'noon' in n or 'midday' in n:
        return 720
    if 'midnight' in n:
        return 0
    m = re.search(r'(\d{1,2})(?::(\d\d))?\s*(a\.?m\.?|p\.?m\.?)?', n)
    if not m:
        return None
    h, mi, ap = int(m.group(1)), int(m.group(2) or 0), (m.group(3) or '').replace('.', '')
    if ap == 'pm' and h != 12:
        h += 12
    if ap == 'am' and h == 12:
        h = 0
    return h * 60 + mi


def parse_year(s):
    """Integer year; BC years are negative (1 BC = 0, astronomical numbering)."""
    m = re.search(r'(\d{1,4})\s*(bc|bce)?', str(s).lower().replace('.', ''))
    if not m:
        return None
    y = int(m.group(1))
    return 1 - y if m.group(2) else y


def parse_date(s):
    """Day number (proleptic Gregorian ordinal) of '17 December 1903' or 'December 17, 1903'."""
    import datetime
    n = str(s).lower().replace(',', ' ')
    d = re.search(r'(\d{1,2})\s+([a-z]+)\s+(\d{3,4})', n) or re.search(r'([a-z]+)\s+(\d{1,2})\s+(\d{3,4})', n)
    if not d:
        return None
    a, b, y = d.groups()
    day, mon = (int(a), b) if a.isdigit() else (int(b), a)
    if mon not in MONTHS:
        return None
    return datetime.date(int(y), MONTHS[mon], day).toordinal()


def answer_value(ans, fq, env, sort):
    """The Z3 value an answer string stands for, or None when it can't be read."""
    if ans is None:
        return None
    for val, surfaces in (fq.get('choices') or {}).items():
        surfaces = surfaces if isinstance(surfaces, list) else [surfaces]
        if norm(ans) in {norm(x) for x in surfaces}:
            return env.compile(val) if not val.lstrip('-').isdigit() else z3.IntVal(int(val))
    if sort is not None and sort.kind() == z3.Z3_DATATYPE_SORT:
        for name, c in env.values.items():
            if c.sort() == sort and norm(ans) == norm(name.replace('_', ' ')):
                return c
        return None
    kind = fq.get('type')
    if kind == 'clock':
        v = parse_clock(ans)
    elif kind == 'year':
        v = parse_year(ans)
    elif kind == 'date':
        v = parse_date(ans)
    elif sort is not None and sort == z3.StringSort():
        return z3.StringVal(str(ans).strip().strip('\'"‘’“”'))
    elif sort is not None and sort.kind() in (z3.Z3_INT_SORT, z3.Z3_REAL_SORT):
        v = parse_number(ans)
    else:
        return None
    if v is None:
        return None
    if isinstance(v, Fraction):
        return z3.RealVal(f'{v.numerator}/{v.denominator}')
    return z3.RealVal(v) if sort is not None and sort.kind() == z3.Z3_REAL_SORT else z3.IntVal(v)


def show(v):
    if v is None:
        return 'unknown'
    if isinstance(v, str):
        return v
    if z3.is_rational_value(v) and v.denominator_as_long() != 1:
        n, d = v.numerator_as_long(), v.denominator_as_long()
        k, dd = 0, d
        while dd % 10 == 0 or dd % 2 == 0 or dd % 5 == 0:
            dd //= 2 if dd % 2 == 0 else 5
            k += 1
        if dd == 1 and k <= 12:   # a finite decimal: 157/50 -> 3.14
            from decimal import Decimal
            return format(Decimal(n) / Decimal(d), 'f')
        return f'{n}/{d}'
    if z3.is_string_value(v):
        return repr(v.as_string())
    return str(v)


# ---------------------------------------------------------------- one record

def items_of(spec):
    """A fact entry: "expr", ["expr", ...] or {"says": text, "z3": expr or [exprs]}
    -> (exprs, says)."""
    if isinstance(spec, dict):
        z = spec.get('z3')
        return (z if isinstance(z, list) else [z]), spec.get('says')
    return (spec if isinstance(spec, list) else [spec]), None


SECTION_KEYS = {'notes', 'decl', 'local', 'facts', 'firm', 'presuppositions', 'gives_up', 'original', 'edit',
                'worlds', 'queries', 'label_corrections'}
QUERY_KEYS = {'q', 'ask', 'find', 'not_checked', 'exception', 'mode', 'given', 'type', 'choices', 'note'}
LOGICS = {'propositional', 'dl', 'fol'}


def static_problems(rec, fs, attrs):
    """File-against-record problems of a fol section (no solving)."""
    probs = []
    extra = set(fs) - SECTION_KEYS
    if extra:
        probs.append(f'unknown keys {sorted(extra)} (allowed: {sorted(SECTION_KEYS)})')
    for c in fs.get('label_corrections') or []:
        if not isinstance(c, dict) or not isinstance(c.get('q'), int) or c.get('to') not in LOGICS \
                or c.get('from', 'fol') not in LOGICS or not c.get('why'):
            probs.append(f'label_corrections: {c!r} needs q (int), to and from (one of {sorted(LOGICS)}), why')
    derived = rec['queries']['derived']
    rec_worlds = {w['id'] for w in rec.get('worlds') or []}
    fworlds = set((fs.get('worlds') or {}))
    if fworlds and fworlds != rec_worlds:
        probs.append(f'worlds {sorted(fworlds)} are not the record\'s {sorted(rec_worlds)}')
    if rec_worlds and not fworlds and any((q.get('world_answers') for q in derived if q.get('logic') == 'fol')):
        probs.append('the record has worlds with fol world answers but the section has none')
    facts = fs.get('facts') or {}
    ids = set(facts)
    for key in ('firm', 'gives_up', 'presuppositions'):
        for k in fs.get(key) or []:
            if k not in ids:
                probs.append(f'{key}: {k!r} is not a fact id')
    for w, spec in (fs.get('worlds') or {}).items():
        for k in spec.get('gives_up') or []:
            if k not in ids:
                probs.append(f'{w}.gives_up: {k!r} is not a fact id')
    try:
        env = Env(fs.get('decl') or {})
    except Exception as e:
        return probs + [f'decl: {e}']
    relations = load_relation_names()
    for name, (args, res) in env.funcs.items():
        if res == 'Bool' or name in attrs or name in (fs.get('local') or {}):
            continue
        if res in ('Int', 'Real', 'String'):
            probs.append(f'value function {name!r} is in neither ATTRIBUTES.md nor the section\'s "local"')
        elif name not in relations:
            probs.append(f'function {name!r} (to {res}) is in neither ATTRIBUTES.md, RELATIONS.md nor "local"')
    texts = []
    for k, spec in facts.items():
        texts += [(f'facts.{k}', x) for x in items_of(spec)[0]]
    for key in ('original', 'edit'):
        texts += [(key, x) for x in fs.get(key) or []]
    for w, spec in (fs.get('worlds') or {}).items():
        for key in ('stores', 'adds'):
            texts += [(f'{w}.{key}', x) for x in spec.get(key) or []]
    seen = set()
    for fq in fs.get('queries') or []:
        qi = fq.get('q')
        if not isinstance(qi, int) or qi >= len(derived):
            probs.append(f'query {qi!r} is not a derived query index')
            continue
        seen.add(qi)
        if set(fq) - QUERY_KEYS:
            probs.append(f'q{qi}: unknown keys {sorted(set(fq) - QUERY_KEYS)}')
        kinds = [k for k in ('ask', 'find', 'not_checked', 'exception') if k in fq]
        if len(kinds) != 1:
            probs.append(f'q{qi}: needs exactly one of ask, find, not_checked, exception')
        if 'ask' in fq:
            texts.append((f'q{qi}.ask', fq['ask']))
        if 'find' in fq:
            texts.append((f'q{qi}.find', fq['find']))
        for k, spec in (fq.get('given') or {}).items():
            texts += [(f'q{qi}.given.{k}', x) for x in items_of(spec)[0]]
        if derived[qi].get('logic') != 'fol':
            probs.append(f'q{qi} is labelled {derived[qi].get("logic")!r}, not fol (encode it for HermiT, or '
                         f'list it as a label correction in notes)')
    for i, q in enumerate(derived):
        if q.get('logic') == 'fol' and i not in seen:
            probs.append(f'q{i} is fol but has no entry in the fol section')
    for where, x in texts:
        try:
            t = env.compile(x)
            if where.endswith('.find'):
                continue
            if not z3.is_bool(t):
                probs.append(f'{where}: {x!r} is not a statement')
        except Exception as e:
            probs.append(f'{where}: {e}')
    # answers readable
    for fq in fs.get('queries') or []:
        qi = fq.get('q')
        if 'find' not in fq or not isinstance(qi, int) or qi >= len(derived):
            continue
        try:
            sort = env.compile(fq['find']).sort()
        except Exception:
            continue
        q = derived[qi]
        golds = [q.get('original_answer'), q.get('new_answer')] + [a.get('answer') for a in (q.get('world_answers') or {}).values()]
        for g in golds:
            if g is not None and answer_value(g, fq, env, sort) is None:
                probs.append(f'q{qi}: cannot read the answer {g!r} as a value of the find (add "choices" or "type")')
    return probs


class FolRecord:
    def __init__(self, rid):
        self.rid = rid
        self.rec = load_record(rid)
        self.f = load_formal(rid) or {}
        self.fs = self.f.get('fol') or {}
        self.op = self.rec['edit_operation']
        self.env = Env(self.fs.get('decl') or {})
        self.facts = {k: items_of(v) for k, v in (self.fs.get('facts') or {}).items()}
        self.firm = set(self.fs.get('firm') or [])
        self.presup = set(self.fs.get('presuppositions') or [])
        self.common_gu = set(self.fs.get('gives_up') or [])
        self.worlds = self.fs.get('worlds') or {'*': {}}
        self.calls = 0

    # ----- knowledge bases as named items
    def items(self, phase, w, fq=None):
        """[(id, kind, [z3 terms], says)] for a phase in world w (plus the query's given facts)."""
        spec = self.worlds.get(w) or {}
        out = []
        gone = set() if phase == 'pre' else self.common_gu | set(spec.get('gives_up') or [])
        for k, (exprs, says) in self.facts.items():
            if k not in gone:
                kind = 'presupposition' if k in self.presup else ('firm' if k in self.firm else 'background')
                out.append((k, kind, exprs, says))
        if spec.get('stores'):
            out.append((f'{w}.stores', 'world', spec['stores'], None))
        if phase == 'pre':
            if self.fs.get('original'):
                out.append(('original', 'original', self.fs['original'],
                            self.rec['edit'].get('original') or self.rec['edit'].get('statement')))
        else:
            if spec.get('adds'):
                out.append((f'{w}.adds', 'world', spec['adds'], None))
            if self.op != 'delete' and self.fs.get('edit'):
                out.append(('edit', 'edit', self.fs['edit'], self.rec['edit'].get('statement')))
        if fq is not None:
            for k, spec2 in (fq.get('given') or {}).items():
                exprs, says = items_of(spec2)
                out.append((f'given.{k}', 'given', exprs, says))
        return [(i, kind, [self.env.compile(x) for x in exprs], says or '; '.join(exprs)) for i, kind, exprs, says in out]

    def solve(self, items, extra=None):
        """('sat' | 'unsat' | 'unknown', model or core ids). The core is
        minimised by deletion."""
        s = z3.Solver()
        s.set('timeout', TIMEOUT_MS)
        lits = {}
        for i, _, terms, _ in items:
            lit = z3.Bool(f'@{i}')
            lits[lit] = i
            for t in terms:
                s.add(z3.Implies(lit, t))
        if extra is not None:
            s.add(extra)
        self.calls += 1
        r = s.check(*lits)
        if r == z3.sat:
            return 'sat', s.model()
        if r == z3.unknown:
            return 'unknown', s.reason_unknown()
        core = [c for c in s.unsat_core()]
        # deletion-based minimisation; a trial that times out keeps the item
        s.set('timeout', MINIMISE_TIMEOUT_MS)
        i = 0
        while i < len(core):
            trial = core[:i] + core[i + 1:]
            self.calls += 1
            if s.check(*trial) == z3.unsat:
                core = [c for c in s.unsat_core() if c in trial] if len(s.unsat_core()) < len(trial) else trial
            else:
                i += 1
        return 'unsat', [lits[c] for c in core]

    def core_items(self, items, ids):
        by = {i: (kind, says) for i, kind, _, says in items}
        return [{'id': i, 'kind': by[i][0], 'says': by[i][1]} for i in ids]

    def evaluate(self, fq, phase, w, expected):
        """(got, detail, core, kind): what the KB entails for the query, and
        the core behind the answer the record expects (or behind what does
        follow)."""
        items = self.items(phase, w, fq)
        st, m = self.solve(items)
        if st == 'unknown':
            return 'error', f'solver unknown ({m})', [], None
        if st == 'unsat':
            return 'inconsistent', 'the knowledge base is unsatisfiable', self.core_items(items, m), None
        if 'ask' in fq:
            claim = self.env.compile(fq['ask'])
            mode = fq.get('mode', 'holds')
            if mode == 'consistent':
                st2, m2 = self.solve(items, claim)
                if st2 == 'unknown':
                    return 'error', 'solver unknown', [], None
                return ('yes', 'claim satisfiable', [], None) if st2 == 'sat' else \
                    ('no', 'claim unsatisfiable with', self.core_items(items, m2), None)
            st_yes, c_yes = self.solve(items, z3.Not(claim))
            st_no, c_no = (self.solve(items, claim) if mode == 'holds' else ('sat', None))
            if 'unknown' in (st_yes, st_no):
                return 'error', 'solver unknown', [], None
            if st_yes == 'unsat':
                return 'yes', 'claim entailed', self.core_items(items, c_yes), None
            if st_no == 'unsat':
                return 'no', 'negation entailed', self.core_items(items, c_no), None
            return ('no' if mode == 'follows' else None), 'neither the claim nor its negation is entailed', [], None
        expr = self.env.compile(fq['find'])
        # the value that follows, if one does: a model's value, then is any other possible?
        v = m.eval(expr, model_completion=True)
        st2, c2 = self.solve(items, expr != v)
        if st2 == 'unknown':
            return 'error', 'solver unknown', [], None
        if st2 == 'unsat':
            return v, f'entailed: {show(v)} (and no other value)', self.core_items(items, c2), None
        other = c2.eval(expr, model_completion=True)
        return None, f'no value entailed ({show(v)} and {show(other)} are both possible)', [], None

    def answer(self, fq, ans):
        sort = self.env.compile(fq['find']).sort() if 'find' in fq else None
        if 'find' in fq:
            return answer_value(ans, fq, self.env, sort)
        return ans

    def judge(self, fq, expected, got):
        if isinstance(got, str) and got in ('error', 'inconsistent'):
            return 'fail'
        if 'find' in fq:
            exp = self.answer(fq, expected) if expected is not None else None
            if exp is None:
                return 'pass' if got is None else 'fail'
            if got is None:
                return 'fail'
            return 'pass' if z3.is_true(z3.simplify(got == exp)) else 'fail'
        mode = fq.get('mode', 'holds')
        exp = yes_no(expected) if expected is not None else {'holds': None, 'follows': 'no', 'consistent': 'yes'}[mode]
        return 'pass' if exp == got else 'fail'

    def label(self, qi):
        q = self.rec['queries']['derived'][qi]
        return f'{q["derivation"]}, {q.get("determinacy") or "unlabelled"}'

    def tags(self, qi):
        q = self.rec['queries']['derived'][qi]
        return {'checker': 'z3', 'logic': q.get('logic'), 'theory': q.get('theory')}

    def check_query(self, fq, qi, out):
        q = self.rec['queries']['derived'][qi]
        label, tags = self.label(qi), self.tags(qi)
        if 'not_checked' in fq or 'exception' in fq:
            why = fq.get('not_checked') or 'exception: ' + fq['exception']
            out.append({'check': 'not_checked', 'q': qi, 'status': 'not_checked', 'detail': why, 'label': label,
                        **tags, 'checker': 'none'})
            return
        wa = {w: a.get('answer') for w, a in (q.get('world_answers') or {}).items()}
        live = [w for w, s in self.worlds.items() if not s.get('exception')]
        orig = q.get('original_answer')
        if orig is None:
            out.append({'check': 'pre', 'q': qi, 'status': 'not_checked', 'label': label, **tags,
                        'detail': 'no original answer' + (' (insert)' if self.op == 'insert' else '')})
        else:
            per = {}
            for w in live:
                got, det, core, _ = self.evaluate(fq, 'pre', w, orig)
                per[w] = {'status': self.judge(fq, orig, got), 'expected': orig, 'got': fmt(got), 'detail': det,
                          'core': core}
            out.append(summarize('pre', qi, per, label, tags))
        indeterminate = bool(wa)
        per, got_by = {}, {}
        for w in live:
            expected = wa.get(w) if indeterminate else q.get('new_answer')
            got, det, core, _ = self.evaluate(fq, 'post', w, expected)
            got_by[w] = got
            per[w] = {'status': self.judge(fq, expected, got), 'expected': expected, 'got': fmt(got), 'detail': det,
                      'core': core}
        out.append(summarize('post_worlds' if indeterminate else 'post_determinate', qi, per, label, tags))
        if indeterminate:
            vals = {fmt(g) for g in got_by.values() if not (isinstance(g, str) and g in ('error', 'inconsistent'))}
            out.append({'check': 'differ', 'q': qi, 'status': 'pass' if len(vals) >= 2 else 'fail', 'label': label,
                        **tags, 'detail': 'entailed answers per world: ' + '; '.join(f'{w}: {fmt(g)}' for w, g in got_by.items())})

    def check_worlds(self, out):
        per = {}
        for w, spec in self.worlds.items():
            if spec.get('exception'):
                per[w] = {'status': 'not_checked', 'detail': 'exception: ' + spec['exception']}
                continue
            bad, cores = [], {}
            for phase in ('pre', 'post'):
                items = self.items(phase, w)
                st, m = self.solve(items)
                if st != 'sat':
                    bad.append(f'{phase} {"unsatisfiable" if st == "unsat" else "unknown"}')
                    if st == 'unsat':
                        cores[phase] = self.core_items(items, m)
            if self.op == 'delete' and not bad and self.fs.get('original'):
                items = self.items('post', w)
                orig = z3.And(*[self.env.compile(x) for x in self.fs['original']])
                st, m = self.solve(items, z3.Not(orig))
                if st == 'unsat':
                    bad.append('post still entails the deleted fact')
                    cores['post_deleted'] = self.core_items(items, m)
            per[w] = {'status': 'fail' if bad else 'pass', 'detail': ', '.join(bad) if bad else 'pre and post satisfiable'}
            if cores:
                per[w]['core'] = cores
        st = 'fail' if any(v['status'] == 'fail' for v in per.values()) else 'pass'
        out.append({'check': 'consistent', 'status': st, 'worlds': per, 'checker': 'z3',
                    'detail': '; '.join(f'{w}: {v["detail"]}' for w, v in per.items())})

    def check(self):
        out = []
        t0 = time.time()
        try:
            fqs = {q['q']: q for q in self.fs.get('queries') or []}
            for qi, q in enumerate(self.rec['queries']['derived']):
                if q.get('logic') != 'fol':
                    continue
                self.check_query(fqs.get(qi, {'q': qi, 'not_checked': 'not encoded'}), qi, out)
            if any('ask' in q or 'find' in q for q in fqs.values()):
                self.check_worlds(out)
        except Exception as e:  # report, don't crash the run
            out.append({'check': 'error', 'status': 'fail', 'detail': f'{type(e).__name__}: {e}'})
        st = 'fail' if any(c['status'] == 'fail' for c in out) else 'pass'
        return {'status': st, 'calls': self.calls, 'seconds': round(time.time() - t0, 2), 'checks': out}


def fmt(got):
    if got is None:
        return 'unknown'
    if isinstance(got, str):
        return got
    return show(got)


def summarize(check, qi, per, label, tags):
    st = 'fail' if any(v['status'] == 'fail' for v in per.values()) else 'pass'
    bad = [f'{w}: expected {v["expected"]!r}, got {v["got"]} ({v["detail"]})' for w, v in per.items()
           if v['status'] == 'fail']
    return {'check': check, 'q': qi, 'status': st, 'label': label, **tags, 'worlds': per,
            'core': {w: [c['id'] for c in v.get('core') or []] for w, v in per.items()},
            'detail': '; '.join(bad) if bad else 'ok in ' + ', '.join(per)}


# ---------------------------------------------------------------- driver

def check_one(rid):
    try:
        rec, f = load_record(rid), load_formal(rid)
        probs = static_problems(rec, (f or {}).get('fol') or {}, load_attributes())
        if probs:
            return rid, {'status': 'fail', 'calls': 0, 'seconds': 0,
                         'checks': [{'check': 'encoding', 'status': 'fail', 'checker': 'z3', 'detail': '; '.join(probs)}]}
        return rid, FolRecord(rid).check()
    except Exception as e:
        return rid, {'status': 'fail', 'calls': 0, 'seconds': 0,
                     'checks': [{'check': 'error', 'status': 'fail', 'detail': f'{type(e).__name__}: {e}'}]}


CHECKS = ('pre', 'post_determinate', 'post_worlds', 'differ', 'consistent', 'not_checked', 'encoding', 'error')


def summary(records):
    counts = {c: Counter() for c in CHECKS}
    for r in records.values():
        for c in r['checks']:
            counts.setdefault(c['check'], Counter())[c['status']] += 1
    return {c: dict(v) for c, v in counts.items() if v}


def fol_ids(topic=None):
    """Records with at least one fol derived query."""
    out = []
    for p in sorted((ROOT / 'records').glob(f'{topic or "*"}/*/*.json')):
        rec = json.loads(p.read_text())
        if any(q.get('logic') == 'fol' for q in rec['queries']['derived']):
            out.append(p.stem)
    return out


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('ids', nargs='*')
    ap.add_argument('--topic')
    ap.add_argument('--jobs', type=int, default=4)
    ap.add_argument('--no-write', action='store_true', help='do not update owl/fol_report.json')
    ap.add_argument('--static', action='store_true', help='only the file-against-record checks')
    ap.add_argument('--all', action='store_true', help='also records whose formal file has no fol section yet')
    args = ap.parse_args(argv)
    scope = args.ids or fol_ids(args.topic)
    if not args.ids and not args.all:
        scope = [r for r in scope if (load_formal(r) or {}).get('fol')]
    if args.static:
        attrs = load_attributes()
        n = 0
        for rid in scope:
            for p in static_problems(load_record(rid), (load_formal(rid) or {}).get('fol') or {}, attrs):
                print(f'{rid}: {p}')
                n += 1
        print(f'{len(scope)} records, {n} problems')
        return 0
    t0 = time.time()
    with Pool(max(1, args.jobs)) as pool:
        results = dict(pool.map(check_one, scope))
    wall = time.time() - t0
    if not args.no_write:
        old = json.loads(REPORT.read_text()) if REPORT.exists() else {}
        records = old.get('records', {})
        records.update(results)
        every = fol_ids()
        report = {'generated': time.strftime('%Y-%m-%d %H:%M:%S'),
                  'checker': 'z3 ' + z3.get_version_string(),
                  'summary': summary(records),
                  'records_checked': len(records),
                  'pending': [r for r in every if not (load_formal(r) or {}).get('fol')],
                  'records': dict(sorted(records.items()))}
        CV.annotate(report, 'z3')
        REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=1) + '\n')
    nq = sum(1 for r in results.values() for c in r['checks'] if c['check'] in ('post_determinate', 'post_worlds'))
    print(f'checked {len(results)} records ({nq} queries) in {wall:.1f}s wall, '
          f'{sum(r["seconds"] for r in results.values()):.1f}s solver time, {sum(r["calls"] for r in results.values())} Z3 calls')
    for c, v in summary(results).items():
        print(f'  {c:17} ' + '  '.join(f'{s} {k}' for s, k in sorted(v.items())))
    for rid, r in results.items():
        for c in r['checks']:
            if c['status'] == 'fail':
                q = f' q{c["q"]}' if 'q' in c else ''
                print(f'FAIL {rid} {c["check"]}{q}: {c["detail"][:400]}')
    if not args.no_write:
        print(f'{len(report["pending"])} records with fol queries have no fol section yet; report: owl/fol_report.json')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
