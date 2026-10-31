"""The small axiom language of the formal files (owl/README.md), and loading
and checking a formal file against its record. Standard library only, so
encode_check.py runs without owlready2.

Axioms (one string each):

    has_capital(australia, sydney)          property assertion
    not has_capital(australia, canberra)    negative property assertion
    milford : Fjord                         class assertion (any class expression)
    a = b,  a != b                          same / different individual
    Fjord ⊑ carved_by value river           class inclusion (also ≡, and `disjoint`)
    sits_in(?x, ?c), City(?c) -> p(?x, ?c)  SWRL rule over named individuals
    Trans(r) Sym(r) Asym(r) Func(r) InvFunc(r)   property axioms (RBox)
    r ⊑ s,  r ≡ inv(s),  r o s ⊑ t,  Disj(r, s)

Class expressions: Name (starts upper case), Thing, Nothing, `not C`,
`C and D`, `C or D`, `r some C`, `r only C`, `r value a`, `r min n C`,
`r max n C`, `r exactly n C`, `{a, b}`, parentheses; `inv(r)` for an
inverse property. Entities and relations are lower case.
"""
import json
import re
from pathlib import Path

OWL_DIR = Path(__file__).resolve().parent
DATASET = OWL_DIR.parent
FORMAL_DIR = OWL_DIR / 'formal'

TOKEN = re.compile(r'\s*(->|⊑|⊒|≡|!=|\?[A-Za-z_][A-Za-z0-9_]*|\?|[A-Za-z_][A-Za-z0-9_]*|\d+|[(){},:=/])')
KEYWORDS = {'and', 'or', 'not', 'some', 'only', 'value', 'min', 'max', 'exactly', 'inv', 'disjoint', 'o'}
PROPERTY_AXIOMS = {'Trans': 'transitive', 'Sym': 'symmetric', 'Asym': 'asymmetric', 'Func': 'functional',
                   'InvFunc': 'inverse_functional', 'Refl': 'reflexive', 'Irrefl': 'irreflexive'}


class SyntaxProblem(ValueError):
    pass


def tokenize(s):
    out, pos = [], 0
    s = s.strip()
    while pos < len(s):
        m = TOKEN.match(s, pos)
        if not m or m.end() == pos:
            raise SyntaxProblem(f'cannot read {s[pos:]!r} in {s!r}')
        out.append(m.group(1))
        pos = m.end()
    return out


class Parser:
    def __init__(self, text):
        self.text, self.toks, self.i = text, tokenize(text), 0

    def peek(self, k=0):
        return self.toks[self.i + k] if self.i + k < len(self.toks) else None

    def take(self, want=None):
        t = self.peek()
        if t is None or (want is not None and t != want):
            raise SyntaxProblem(f'expected {want or "more"} at token {self.i} in {self.text!r}, found {t!r}')
        self.i += 1
        return t

    def done(self):
        if self.peek() is not None:
            raise SyntaxProblem(f'unexpected {self.peek()!r} in {self.text!r}')

    # property expressions: r or inv(r)
    def prop(self):
        if self.peek() == 'inv' and self.peek(1) == '(':
            self.take('inv'); self.take('(')
            p = self.take()
            self.take(')')
            return ('inv', p)
        t = self.take()
        if not re.match(r'[a-z]', t) or t in KEYWORDS:
            raise SyntaxProblem(f'expected a relation, found {t!r} in {self.text!r}')
        return ('prop', t)

    # class expressions
    def ce(self):
        left = self.ce_and()
        items = [left]
        while self.peek() == 'or':
            self.take()
            items.append(self.ce_and())
        return items[0] if len(items) == 1 else ('or', items)

    def ce_and(self):
        items = [self.ce_unary()]
        while self.peek() == 'and':
            self.take()
            items.append(self.ce_unary())
        return items[0] if len(items) == 1 else ('and', items)

    def ce_unary(self):
        t = self.peek()
        if t == 'not':
            self.take()
            return ('not', self.ce_unary())
        if t == '(':
            self.take('(')
            x = self.ce()
            self.take(')')
            return x
        if t == '{':
            self.take('{')
            names = [self.ind()]
            while self.peek() == ',':
                self.take(',')
                names.append(self.ind())
            self.take('}')
            return ('oneof', names)
        if t and re.match(r'[A-Z]', t) and t not in PROPERTY_AXIOMS:
            self.take()
            return ('class', t)
        if t and (re.match(r'[a-z]', t) and t not in KEYWORDS or t == 'inv'):
            p = self.prop()
            kw = self.take()
            if kw in ('some', 'only'):
                return (kw, p, self.ce_unary())
            if kw == 'value':
                return ('value', p, self.ind())
            if kw in ('min', 'max', 'exactly'):
                n = int(self.take())
                filler = self.ce_unary() if self.peek() not in (None, ')', 'and', 'or', ',', '⊑', '≡') else ('class', 'Thing')
                return (kw, n, p, filler)
            raise SyntaxProblem(f'expected some/only/value/min/max/exactly after {p[1]!r} in {self.text!r}')
        raise SyntaxProblem(f'expected a class expression, found {t!r} in {self.text!r}')

    def ind(self):
        t = self.take()
        if t == '?':
            return '?'
        if not re.match(r'[a-z?]', t) or t in KEYWORDS:
            raise SyntaxProblem(f'expected an entity key, found {t!r} in {self.text!r}')
        return t

    def atom(self):
        name = self.take()
        self.take('(')
        args = [self.ind()]
        while self.peek() == ',':
            self.take(',')
            args.append(self.ind())
        self.take(')')
        if name in ('same', 'different'):
            return (name, args)
        if re.match(r'[A-Z]', name):
            if len(args) != 1:
                raise SyntaxProblem(f'class atom {name} takes one argument in {self.text!r}')
            return ('class', name, args)
        if len(args) != 2:
            raise SyntaxProblem(f'property atom {name} takes two arguments in {self.text!r}')
        return ('prop', name, args)


def parse_axiom(text):
    """An axiom string -> a tuple tree (first item names the kind)."""
    toks = tokenize(text)
    if '->' in toks:
        body_s, head_s = text.split('->', 1)
        return ('rule', parse_atoms(body_s, text), parse_atoms(head_s, text))
    p = Parser(text)
    # property axioms
    if toks[0] in PROPERTY_AXIOMS and len(toks) > 1 and toks[1] == '(':
        p.take(); p.take('(')
        r = p.take()
        p.take(')'); p.done()
        return ('char', PROPERTY_AXIOMS[toks[0]], r)
    if toks[0] == 'Disj' and toks[1] == '(':
        p.take(); p.take('(')
        a = p.take(); p.take(',')
        b = p.take(); p.take(')'); p.done()
        return ('pdisjoint', a, b)
    if len(toks) >= 5 and toks[1] == 'o' and re.match(r'[a-z]', toks[0]):
        a = p.take(); p.take('o')
        b = p.take(); p.take('⊑')
        c = p.take(); p.done()
        return ('chain', a, b, c)
    if len(toks) == 3 and toks[1] == '⊑' and all(re.match(r'[a-z]', t) for t in (toks[0], toks[2])):
        return ('psub', toks[0], toks[2])
    if len(toks) == 6 and toks[1] == '≡' and toks[2] == 'inv':
        p.take(); p.take('≡'); p.take('inv'); p.take('(')
        b = p.take(); p.take(')'); p.done()
        return ('pinv', toks[0], b)
    # negated assertion
    neg = False
    if toks[0] == 'not' and len(toks) > 2 and toks[2] == '(':
        p.take('not')
        neg = True
    # a = b, a != b
    if len(toks) == 3 and toks[1] in ('=', '!='):
        return ('same' if toks[1] == '=' else 'different', toks[0], toks[2])
    # property assertion r(a, b)
    if p.peek(1) == '(' and re.match(r'[a-z]', p.peek() or '') and p.peek() not in KEYWORDS:
        r = p.take(); p.take('(')
        a = p.ind(); p.take(',')
        b = p.ind(); p.take(')'); p.done()
        return ('nprop' if neg else 'prop', r, a, b)
    if neg:
        raise SyntaxProblem(f'"not" only goes before a property assertion: {text!r} (use "a : not C")')
    # class assertion a : C
    if len(toks) > 2 and toks[1] == ':':
        a = p.ind(); p.take(':')
        c = p.ce(); p.done()
        return ('type', a, c)
    # class axioms
    left = p.ce()
    op = p.take()
    if op not in ('⊑', '≡', 'disjoint'):
        raise SyntaxProblem(f'expected ⊑, ≡ or disjoint in {text!r}, found {op!r}')
    right = p.ce(); p.done()
    return ({'⊑': 'sub', '≡': 'equiv', 'disjoint': 'disjoint'}[op], left, right)


def parse_atoms(s, whole):
    p = Parser(s)
    atoms = [p.atom()]
    while p.peek() == ',':
        p.take(',')
        atoms.append(p.atom())
    p.done()
    return atoms


def parse_find(text):
    """'a r ?', 'a r1/r2 ?' or 'a : <class expression with ?>' ->
    (subject, class-expression tree with '?' for the answer)."""
    toks = tokenize(text)
    if len(toks) > 2 and toks[1] == ':':
        p = Parser(text)
        a = p.ind(); p.take(':')
        c = p.ce(); p.done()
        return a, c
    if toks[-1] != '?':
        raise SyntaxProblem(f'find needs "a r ?", "a r1/r2 ?" or "a : C(?)": {text!r}')
    path = [t for t in toks[1:-1] if t != '/']
    ce = ('value', ('prop', path[-1]), '?')
    for r in reversed(path[:-1]):
        ce = ('some', ('prop', r), ce)
    return toks[0], ce


# ---------------------------------------------------------------- walking trees

def names_in(tree, out=None):
    """{'ind': set, 'rel': set, 'cls': set} used by a tree."""
    out = out or {'ind': set(), 'rel': set(), 'cls': set()}
    k = tree[0]
    if k in ('prop', 'nprop') and len(tree) == 4:
        out['rel'].add(tree[1]); out['ind'].update(x for x in tree[2:] if not x.startswith('?'))
    elif k == 'type':
        out['ind'].add(tree[1]); names_in(tree[2], out)
    elif k in ('same', 'different') and isinstance(tree[1], str):
        out['ind'].update(tree[1:])
    elif k in ('sub', 'equiv', 'disjoint'):
        names_in(tree[1], out); names_in(tree[2], out)
    elif k == 'rule':
        for a in tree[1] + tree[2]:
            if a[0] == 'class':
                out['cls'].add(a[1])
            elif a[0] == 'prop':
                out['rel'].add(a[1])
            args = a[2] if a[0] in ('class', 'prop') else a[1]
            out['ind'].update(x for x in args if not x.startswith('?'))
    elif k == 'char':
        out['rel'].add(tree[2])
    elif k in ('pdisjoint', 'psub', 'pinv'):
        out['rel'].update(tree[1:])
    elif k == 'chain':
        out['rel'].update(tree[1:])
    # class expressions
    elif k == 'class':
        if tree[1] not in ('Thing', 'Nothing'):
            out['cls'].add(tree[1])
    elif k in ('and', 'or'):
        for x in tree[1]:
            names_in(x, out)
    elif k == 'not':
        names_in(tree[1], out)
    elif k in ('some', 'only'):
        out['rel'].add(tree[1][1]); names_in(tree[2], out)
    elif k == 'value':
        out['rel'].add(tree[1][1])
        if tree[2] != '?':
            out['ind'].add(tree[2])
    elif k in ('min', 'max', 'exactly'):
        out['rel'].add(tree[2][1]); names_in(tree[3], out)
    elif k == 'oneof':
        out['ind'].update(x for x in tree[1] if x != '?')
    elif k == 'prop':   # bare property expression
        out['rel'].add(tree[1])
    elif k == 'inv':
        out['rel'].add(tree[1])
    return out


def is_property_axiom(tree):
    return tree[0] in ('char', 'pdisjoint', 'psub', 'pinv', 'chain')


# ---------------------------------------------------------------- formal files

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


def load_record(rid):
    hits = list((DATASET / 'records').glob(f'*/*/{rid}.json'))
    if not hits:
        raise FileNotFoundError(f'no record {rid}')
    return json.loads(hits[0].read_text())


def load_formal(rid):
    return json.loads((FORMAL_DIR / f'{rid}.json').read_text())


def surfaces(formal):
    """{normalized surface: key}"""
    out = {}
    for key, s in (formal.get('entities') or {}).items():
        if s is None:
            continue
        for x in ([s] if isinstance(s, str) else s):
            out.setdefault(norm(x), key)
    return out


def background_items(formal):
    """{id: [axiom strings]}"""
    return {k: ([v] if isinstance(v, str) else list(v)) for k, v in (formal.get('background') or {}).items()}


def all_axiom_strings(formal):
    """(where, text) for every axiom in the file."""
    out = []
    for f in ('original', 'edit'):
        out += [(f, a) for a in formal.get(f) or []]
    for k, v in background_items(formal).items():
        out += [(f'background.{k}', a) for a in v]
    for w, spec in (formal.get('worlds') or {}).items():
        for f in ('stores', 'adds'):
            out += [(f'worlds.{w}.{f}', a) for a in spec.get(f) or []]
    for q in formal.get('queries') or []:
        out += [(f'queries[{q.get("q")}].given', a) for a in q.get('given') or []]
        if 'ask' in q:
            out.append((f'queries[{q.get("q")}].ask', q['ask']))
    return out


def query_answers(rec, qi):
    """The record's answers for derived query qi: {'original', 'new', 'worlds'}."""
    q = rec['queries']['derived'][qi]
    return {'original': q.get('original_answer'), 'new': q.get('new_answer'),
            'worlds': {w: a.get('answer') for w, a in (q.get('world_answers') or {}).items()},
            'determinacy': q.get('determinacy'), 'logic': q.get('logic'), 'theory': q.get('theory')}


def check_formal(formal, rec, relations=None):
    """Problems with a formal file, without reasoning: syntax, names, gold
    strings that don't map to an entity, world ids, query indexes."""
    probs = []
    rid = rec['id']
    if formal.get('id') != rid:
        probs.append(f'id {formal.get("id")!r} does not match the record')
    ents = formal.get('entities') or {}
    local = formal.get('relations') or {}
    rels = set(relations or ()) | set(local)
    for k in ents:
        if not re.fullmatch(r'[a-z][a-z0-9_]*', k):
            probs.append(f'entity key {k!r} must be lower snake_case')
        if k in rels:
            probs.append(f'entity key {k!r} is also a relation name')
    used_ind, used_rel = set(), set()
    trees = []
    for where, text in all_axiom_strings(formal):
        try:
            t = parse_axiom(text)
        except SyntaxProblem as e:
            probs.append(f'{where}: {e}')
            continue
        trees.append((where, t))
        n = names_in(t)
        used_ind |= n['ind']; used_rel |= n['rel']
    for q in formal.get('queries') or []:
        if 'find' in q:
            try:
                a, ce = parse_find(q['find'])
                n = names_in(ce)
                used_ind |= n['ind'] | {a}; used_rel |= n['rel']
            except SyntaxProblem as e:
                probs.append(f'queries[{q.get("q")}].find: {e}')
    for i in sorted(used_ind - set(ents)):
        probs.append(f'entity {i!r} is used but not in entities')
    if relations is not None:
        for r in sorted(used_rel - rels):
            probs.append(f'relation {r!r} is not in RELATIONS.md (nor named in a tag) and not declared in "relations"')
    for r, tags in local.items():
        if relations is not None and r in relations:
            probs.append(f'local relation {r!r} is already in RELATIONS.md (or named in a tag there): use it')
        if not isinstance(tags, list):
            probs.append(f'relations.{r} must be a list of RELATIONS.md tags')
    bg = background_items(formal)
    for f in ('firm', 'premises', 'gives_up'):
        for k in formal.get(f) or []:
            if k not in bg:
                probs.append(f'{f}: {k!r} is not a background id')
    rec_worlds = [w['id'] for w in rec.get('worlds') or []]
    fw = formal.get('worlds') or {}
    if set(fw) != set(rec_worlds):
        probs.append(f'world ids {sorted(fw)} differ from the record\'s {rec_worlds}')
    for w, spec in fw.items():
        for k in spec.get('gives_up') or []:
            if k not in bg:
                probs.append(f'worlds.{w}.gives_up: {k!r} is not a background id')
        extra = set(spec) - {'stores', 'adds', 'gives_up', 'exception', 'note'}
        if extra:
            probs.append(f'worlds.{w}: unknown keys {sorted(extra)}')
    if rec.get('derivability') in ('likely', 'very_likely') and not formal.get('premises'):
        probs.append('derivability is likely/very_likely but "premises" is empty')
    bridges = {norm(b) for q in rec['queries']['derived'] for b in q.get('bridge') or []}
    for k, v in (formal.get('bridge_refs') or {}).items():
        m = re.fullmatch(r'q(\d+)\.given\.(\d+)', k)
        if m:
            fq = {q.get('q'): q for q in formal.get('queries') or []}.get(int(m.group(1))) or {}
            if int(m.group(2)) >= len(fq.get('given') or []):
                probs.append(f'bridge_refs: {k!r} names no given axiom')
        elif k not in bg:
            probs.append(f'bridge_refs: {k!r} is neither a background id nor q<n>.given.<i>')
        for t in ([v] if isinstance(v, str) else v):
            if norm(t) not in bridges:
                probs.append(f'bridge_refs.{k}: {t!r} is no derived query\'s bridge sentence')
    extra = set(formal) - {'id', 'notes', 'relations', 'entities', 'distinct', 'original', 'edit', 'premises',
                           'background', 'firm', 'gives_up', 'worlds', 'queries', 'bridge_refs',
                           'fol'}  # fol: Z3, fol_check.py
    if extra:
        probs.append(f'unknown top-level keys {sorted(extra)}')
    derived = rec['queries']['derived']
    seen = set()
    surf = surfaces(formal)
    for q in formal.get('queries') or []:
        qi = q.get('q')
        if not isinstance(qi, int) or not 0 <= qi < len(derived):
            probs.append(f'query index {qi!r} is not a derived query of the record')
            continue
        if qi in seen:
            probs.append(f'query {qi} appears twice')
        seen.add(qi)
        kinds = [k for k in ('ask', 'find', 'not_checked', 'exception') if k in q]
        if len(kinds) != 1:
            probs.append(f'query {qi}: needs exactly one of ask, find, not_checked, exception (has {kinds})')
            continue
        extra = set(q) - {'q', 'ask', 'find', 'not_checked', 'exception', 'mode', 'given', 'candidates',
                          'exclusive', 'note'}
        if extra:
            probs.append(f'query {qi}: unknown keys {sorted(extra)}')
        ans = query_answers(rec, qi)
        if q.get('mode', 'holds') not in ('holds', 'follows', 'consistent'):
            probs.append(f'query {qi}: mode must be holds, follows or consistent')
        golds = [('original', ans['original']), ('new', ans['new'])] + \
                [(f'world {w}', a) for w, a in ans['worlds'].items()]
        if 'ask' in q:
            for where, g in golds:
                if g is not None and yes_no(g) == '?':
                    probs.append(f'query {qi}: {where} answer {g!r} is not yes/no, but the query is an ask')
        if 'find' in q:
            for where, g in golds:
                if g is not None and norm(g) not in surf:
                    probs.append(f'query {qi}: {where} answer {g!r} maps to no entity (add it to an entity\'s surfaces)')
            for c in q.get('candidates') or []:
                if c not in ents:
                    probs.append(f'query {qi}: candidate {c!r} is not an entity')
        if ans['logic'] == 'dl' and 'not_checked' in q:
            pass  # allowed, but reported as not checked with its reason
    missing = set(range(len(derived))) - seen
    if missing:
        probs.append(f'derived queries {sorted(missing)} have no entry in "queries" (use not_checked with a reason)')
    if rec['edit_operation'] in ('replace', 'delete') and not formal.get('original'):
        probs.append('replace/delete needs "original"')
    if rec['edit_operation'] in ('replace', 'insert') and not formal.get('edit') and rec['box'] != 'rbox':
        probs.append('replace/insert needs "edit"')
    return probs
