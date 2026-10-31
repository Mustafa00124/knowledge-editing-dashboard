#!/usr/bin/env python3
"""Justifications for Sid's Dataset derived queries: which axioms each formally
checked answer actually follows from, compared with the record's
`derivation`, `bridge`, `hops` and `via` metadata (owl/README.md,
"Justifications").

    venvs/easyedit_venv/bin/python datasets/SidsDataset/justify.py --topic geography --jobs 8
    venvs/easyedit_venv/bin/python datasets/SidsDataset/justify.py geography-replace-0003 ...

Writes owl/justifications.json (records not run keep their old entry) and
prints a summary. reason.py is unaffected: this reuses its HermiT call path.

A justification is a minimal set of removable units (the edit, each
background item, each world store or add, each prompt-given axiom, the
record's distinctness axiom, and each relation-property axiom of
RELATIONS.md the record's signature reaches) that still entails the answer.
OWL has no explanation API in owlready2, so this is black box:

1. a relevance module: units reachable from the query's signature through
   shared names, iterated (checked to still entail; else every unit);
2. contraction to one minimal justification (prefix deletion, batched);
3. Reiter's hitting-set tree for the others, capped at --max-just
   justifications or --budget seconds per entailment (recorded as `capped`).

Entailment results are cached per unit subset, and the subsets a step needs
are checked in one HermiT call: each subset becomes a renamed copy of the
knowledge base (disjoint names) inside one ontology. Every subset of a
consistent knowledge base is consistent, so the copies cannot disturb each
other.
"""
import argparse
import copy
import json
import re
import sys
import time
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import reason as R  # noqa: E402

D, RL = R.D, R.RL
OUT = R.OWL_DIR / 'justifications.json'
MAX_JUST = 5
BUDGET = 90.0          # seconds per entailment for the hitting-set tree
BATCH = 40             # knowledge-base copies per HermiT call

# Derivation types a relation-property axiom stands for (README derived-query
# table / RELATIONS.md tags).
CHAR_TYPE = {'transitive': 'transitivity', 'symmetric': 'symmetry', 'asymmetric': 'asymmetry',
             'functional': 'functional', 'inverse_functional': 'functional',
             'reflexive': 'reflexivity', 'irreflexive': 'irreflexivity'}
PAX_TYPE = {'pinv': 'inverse', 'psub': 'subproperty', 'chain': 'chain', 'pdisjoint': 'disjointness'}
# Record derivations that name a relation property (or a class axiom): the
# justification has to use one of these unit types.
PROPERTY_DERIVATIONS = {'symmetry', 'inverse', 'asymmetry', 'transitivity', 'chain', 'subproperty',
                        'functional', 'inheritance'}
# Task types: no relation property of their own.
TASK_DERIVATIONS = {'composition', 'binding', 'application', 'premise', 'scope'}
VERDICTS = ('match', 'partial', 'mismatch', 'not_checked')
# alternatives_listed: an ambiguous query whose routes the record names
# (derivation + alt_derivations); revision_as_bridge: a listed revision fact
# every justification uses (it builds the answer: should be a bridge);
# stale: stored justifications that no longer fit the record (--recompare).
FLAGS = ('no_edit', 'ambiguous', 'alternatives_listed', 'revision_as_bridge', 'capped', 'stale')

RESERVED = set(D.KEYWORDS) | set(D.PROPERTY_AXIOMS) | {'Thing', 'Nothing', 'Disj', 'same', 'different'}
NAME = re.compile(r'(?<![?\w])([A-Za-z_][A-Za-z0-9_]*)')


# ---------------------------------------------------------------- renaming (batched copies)

def rename_text(text, sfx):
    return NAME.sub(lambda m: m.group(1) if m.group(1) in RESERVED else m.group(1) + sfx, text)


def rename_ce(t, sfx):
    k = t[0]
    if k == 'class':
        return t if t[1] in ('Thing', 'Nothing') else ('class', t[1] + sfx)
    if k in ('and', 'or'):
        return (k, [rename_ce(x, sfx) for x in t[1]])
    if k == 'not':
        return ('not', rename_ce(t[1], sfx))
    if k in ('prop', 'inv'):
        return (k, t[1] + sfx)
    if k in ('some', 'only'):
        return (k, rename_ce(t[1], sfx), rename_ce(t[2], sfx))
    if k == 'value':
        return ('value', rename_ce(t[1], sfx), t[2] + sfx)
    if k in ('min', 'max', 'exactly'):
        return (k, t[1], rename_ce(t[2], sfx), rename_ce(t[3], sfx))
    if k == 'oneof':
        return ('oneof', [x + sfx for x in t[1]])
    raise ValueError(f'cannot rename {t}')


def rename_probe(p, sfx):
    if p[0] == 'member':
        return ('member', p[1] + sfx, rename_ce(p[2], sfx))
    return ('unsat', rename_ce(p[1], sfx))


def rename_table(table, sfx):
    out = {}
    for n, r in table.items():
        r = dict(r)
        r['inverse'] = [x + sfx for x in r['inverse']]
        r['sub'] = [x + sfx for x in r['sub']]
        r['disjoint'] = [x + sfx for x in r['disjoint']]
        r['chains'] = [[a + sfx, b + sfx] for a, b in r['chains']]
        out[n + sfx] = r
    return out


# ---------------------------------------------------------------- units

def pax_text(t):
    k = t[0]
    if k == 'char':
        return {v: k2 for k2, v in D.PROPERTY_AXIOMS.items()}[t[1]] + f'({t[2]})'
    if k == 'pinv':
        return f'{t[1]} ≡ inv({t[2]})'
    if k == 'psub':
        return f'{t[1]} ⊑ {t[2]}'
    if k == 'chain':
        return f'{t[1]} o {t[2]} ⊑ {t[3]}'
    if k == 'pdisjoint':
        return f'Disj({t[1]}, {t[2]})'
    return str(t)


def norm_pax(t):
    if t[0] in ('pinv', 'pdisjoint'):
        a, b = sorted(t[1:])
        return (t[0], a, b)
    return tuple(t)


def remove_pax(table, t):
    """Remove one catalogue property axiom from a relation table (in place),
    without the inverse propagation of an RBox edit: each unit stands alone."""
    k = t[0]
    if k == 'char':
        table[t[2]][t[1]] = False
    elif k == 'pinv':
        a, b = t[1], t[2]
        for x, y in ((a, b), (b, a)):
            if y in table[x]['inverse']:
                table[x]['inverse'].remove(y)
    elif k == 'psub':
        if t[2] in table[t[1]]['sub']:
            table[t[1]]['sub'].remove(t[2])
    elif k == 'chain':
        c = [t[2], t[3]]
        if c in table[t[1]]['chains']:
            table[t[1]]['chains'].remove(c)
    elif k == 'pdisjoint':
        for x, y in ((t[1], t[2]), (t[2], t[1])):
            if y in table[x]['disjoint']:
                table[x]['disjoint'].remove(y)


def unit_types(u):
    """Derivation types one unit stands for."""
    out = set()
    for t in u['pax']:
        out.add(CHAR_TYPE.get(t[1]) if t[0] == 'char' else PAX_TYPE[t[0]])
    for a in u['facts']:
        t = D.parse_axiom(a)
        if t[0] in ('sub', 'equiv'):
            out.add('inheritance')
        elif t[0] == 'disjoint':
            out.add('disjointness')
        elif t[0] == 'rule':
            heads = {h[0] if h[0] in ('same', 'different') else ('Nothing' if h[0] == 'class' and h[1] == 'Nothing'
                                                                  else 'atom') for h in t[2]}
            out.add('functional' if 'same' in heads else 'disjointness' if 'Nothing' in heads else 'rule')
    out.discard(None)
    return out


def is_typing(u):
    """A unit made only of class assertions to named classes (encoding glue:
    'Nice is a city' so a rule can fire)."""
    if u['pax'] or not u['facts']:
        return False
    for a in u['facts']:
        t = D.parse_axiom(a)
        if t[0] != 'type' or t[2][0] not in ('class', 'and'):
            return False
    return True


# ---------------------------------------------------------------- one entailment problem

class Problem:
    """The units of one (query, phase, world) knowledge base and the probe
    (or inconsistency claim) to justify."""

    def __init__(self, rec, units, table0, target, stats):
        self.rec, self.units, self.table0, self.target, self.stats = rec, units, table0, target, stats
        self.cache = {}

    def kb_parts(self, subset):
        table = copy.deepcopy(self.table0)
        axioms = []
        for uid, u in self.units.items():
            if u['kind'] == 'rbox':
                if uid not in subset:
                    remove_pax(table, u['pax'][0])
                continue
            if uid not in subset:
                continue
            axioms += u['facts']
            for t in u['pax']:
                R.apply_property_axiom(table, t, True)
        distinct = self.rec.distinct if 'distinct' in subset else []
        return table, axioms, distinct

    def entails_many(self, subsets):
        subsets = [frozenset(s) for s in subsets]
        todo = list(dict.fromkeys(s for s in subsets if s not in self.cache))
        for i in range(0, len(todo), BATCH):
            self.run_batch(todo[i:i + BATCH])
        return [self.cache[s] for s in subsets]

    def entails(self, subset):
        return self.entails_many([subset])[0]

    def run_batch(self, batch):
        kind = self.target[0]
        if kind == 'incons':
            for s in batch:   # KB + claim inconsistent: one KB per subset
                table, axioms, distinct = self.kb_parts(s)
                kb = R.KB(table, axioms + [self.target[1]], self.rec.entities, distinct)
                self.stats['calls'] += 1
                res = R.run_kb(kb)
                if res['error']:
                    raise RuntimeError(res['error'])
                self.cache[s] = res['consistent'] is False
            return
        table_m, axioms_m, ents_m, dist_m, keys = {}, [], [], [], []
        kb = R.KB({}, [], [], [])
        for i, s in enumerate(batch):
            sfx = f'__k{i}'
            table, axioms, distinct = self.kb_parts(s)
            table_m.update(rename_table(table, sfx))
            axioms_m += [rename_text(a, sfx) for a in axioms]
            ents_m += [e + sfx for e in self.rec.entities]
            dist_m += [e + sfx for e in distinct]
            keys.append(kb.probe(*rename_probe(self.target[1], sfx)))
        kb.table, kb.axioms, kb.entities, kb.distinct = table_m, axioms_m, ents_m, dist_m
        self.stats['calls'] += 1
        self.stats['subsets'] += len(batch)
        res = R.run_kb(kb)
        if res['error'] or not res['consistent']:
            if len(batch) == 1:
                raise RuntimeError(res['error'] or 'a unit subset is inconsistent')
            for s in batch:     # should not happen; check one by one
                self.run_batch([s])
            return
        for s, k in zip(batch, keys):
            self.cache[s] = bool(res['probes'][k])

    # ----- relevance module

    def module(self):
        sig = probe_signature(self.target)
        usig = {uid: unit_signature(u) for uid, u in self.units.items()}
        mod = {'distinct'} & set(self.units)
        changed = True
        while changed:
            changed = False
            for uid, s in usig.items():
                if uid not in mod and s & sig:
                    mod.add(uid)
                    if uid != 'distinct':
                        sig |= s
                    changed = True
        return frozenset(mod)

    # ----- one minimal justification (prefix deletion, one batch per kept unit)

    def contract(self, S):
        S = set(S)
        cands = sorted(S, key=order_key)
        kept = set()
        while cands:
            prefixes = [frozenset(S - set(cands[:j + 1])) for j in range(len(cands))]
            ok = self.entails_many(prefixes)
            j = -1
            while j + 1 < len(ok) and ok[j + 1]:
                j += 1
            S -= set(cands[:j + 1])
            if j + 1 < len(cands):
                kept.add(cands[j + 1])
            cands = cands[j + 2:]
        return frozenset(S)

    # ----- all justifications (Reiter's hitting-set tree, breadth first)

    def all_justifications(self, max_just, budget, single=False):
        t0 = time.time()
        full = frozenset(self.units)
        if not self.entails(full):
            return {'entailed': False, 'justifications': [], 'capped': False, 'module': None}
        mod = self.module()
        if not self.entails(mod):
            mod = full
        found = [self.contract(mod)]
        if single:
            return {'entailed': True, 'justifications': found, 'capped': None, 'module': sorted(mod)}
        closed, seen = [], {frozenset()}
        frontier = [frozenset([u]) for u in found[0]]
        capped = False
        while frontier:
            if len(found) >= max_just or time.time() - t0 > budget:
                capped = True
                break
            frontier = [h for h in frontier if not any(c <= h for c in closed)]
            need = [h for h in frontier if not any(not (j & h) for j in found)]
            res = dict(zip(need, self.entails_many([mod - h for h in need])))
            nxt = []
            for h in frontier:
                if h in res and not res[h]:
                    closed.append(h)
                    continue
                label = next((j for j in found if not (j & h)), None)
                if label is None:
                    if len(found) >= max_just or time.time() - t0 > budget:
                        capped = True
                        break
                    label = self.contract(mod - h)
                    found.append(label)
                for u in sorted(label, key=order_key):
                    c = h | {u}
                    if c not in seen:
                        seen.add(c)
                        nxt.append(c)
            if capped:
                break
            frontier = nxt
        return {'entailed': True, 'justifications': found, 'capped': capped, 'module': sorted(mod)}


def order_key(uid):
    # Try dropping catalogue property axioms and world adds first, the edit last.
    rank = {'rbox': 0, 'distinct': 1, 'add': 2, 'store': 2, 'bg': 3, 'given': 3, 'edit': 9}
    return (rank.get(uid.split(':')[0], 5), uid)


def probe_signature(target):
    if target[0] == 'incons':
        n = D.names_in(D.parse_axiom(target[1]))
    else:
        p = target[1]
        n = D.names_in(p[2] if p[0] == 'member' else p[1])
        if p[0] == 'member':
            n['ind'].add(p[1])
    return {('i', x) for x in n['ind']} | {('r', x) for x in n['rel']} | {('c', x) for x in n['cls']}


def unit_signature(u):
    n = {'ind': set(), 'rel': set(), 'cls': set()}
    for a in u['facts']:
        D.names_in(D.parse_axiom(a), n)
    for t in u['pax']:
        D.names_in(t, n)
    return {('i', x) for x in n['ind']} | {('r', x) for x in n['rel']} | {('c', x) for x in n['cls']}


def routes_named(names, sets):
    """Does the record name every route of an ambiguous query? `sets`: the
    property-type sets of its edit-using justifications in one world. Each
    set's own part (what it has beyond the types all of them share) must
    contain a named derivation, when that part has a nameable type at all
    (disjointness and rule are not derivation names)."""
    common = set.intersection(*(set(x) for x in sets))
    named = set(names)
    for x in sets:
        own = (set(x) - common) & PROPERTY_DERIVATIONS
        if own and not own & named:
            return False
    return True


# ---------------------------------------------------------------- one record

class Justifier(R.Record):

    def __init__(self, rid, base_table, max_just=MAX_JUST, budget=BUDGET):
        super().__init__(rid, base_table)
        self.max_just, self.budget = max_just, budget
        self.stats = {'calls': 0, 'subsets': 0}
        self.refs = {kind: {k: ([v] if isinstance(v, str) else list(v))
                            for k, v in (self.f.get(field) or {}).items()}
                     for kind, field in (('bridge', 'bridge_refs'), ('revision_facts', 'revision_refs'))}

    def units_for(self, fq, phase, w):
        """{unit id: unit} and the base relation table of a phase in world w."""
        spec = self.worlds.get(w) or {}
        units = {}

        def add(uid, kind, axioms, text=None):
            facts, pax = [], []
            for a in axioms:
                t = D.parse_axiom(a)
                (pax if D.is_property_axiom(t) else facts).append(t if D.is_property_axiom(t) else a)
            units[uid] = {'kind': kind, 'facts': facts, 'pax': pax, 'text': text or '; '.join(axioms)}
        if phase == 'pre':
            edit = list(self.f.get('original') or [])
            gone = set()
        else:
            edit = list(self.f.get('edit') or []) if self.op != 'delete' else []
            gone = self.common_gu | set(spec.get('gives_up') or [])
        if edit:
            add('edit', 'edit', edit)
        for k, v in self.bg.items():
            if k not in gone:
                add(f'bg:{k}', 'bg', v, text=f'{k}: ' + '; '.join(v))
        for i, a in enumerate(spec.get('stores') or []):
            add(f'store:{i}', 'store', [a])
        if phase == 'post':
            for i, a in enumerate(spec.get('adds') or []):
                add(f'add:{i}', 'add', [a])
        for i, a in enumerate(fq.get('given') or []):
            add(f'given:{i}', 'given', [a])
        if len(self.distinct) > 1:
            units['distinct'] = {'kind': 'distinct', 'facts': [], 'pax': [], 'text': 'all named individuals differ'}
        # Base table: RELATIONS.md + local relations, with the RBox edit's
        # removals (pre: the edit's axioms absent; post: the original's).
        table0 = json.loads(json.dumps(self.base_table))
        for name, tags in (self.f.get('relations') or {}).items():
            table0[name] = RL.parse_tags(tags) | {'catalogued': False}
        removed = self.edit_props if phase == 'pre' else self.orig_props
        for a in removed:
            R.apply_property_axiom(table0, D.parse_axiom(a), False)
        # Catalogue property axioms over the signature's closure, one unit each.
        names = set()
        for u in units.values():
            names |= {x for k, x in unit_signature(u) if k == 'r'}
        for fq_part in ([fq['find']] if 'find' in fq else []):
            names |= D.names_in(D.parse_find(fq_part)[1])['rel']
        if 'ask' in fq:
            names |= D.names_in(D.parse_axiom(fq['ask']))['rel']
        # pax of units may name relations missing from the table
        for u in units.values():
            for t in u['pax']:
                for n in D.names_in(t)['rel']:
                    if n not in table0:
                        table0[n] = RL.empty_rel() | {'catalogued': False}
        tmp = json.loads(json.dumps(table0))
        for u in units.values():
            for t in u['pax']:
                R.apply_property_axiom(tmp, t, True)
        need = RL.closure(tmp, names)
        cat = set()
        for n in sorted(need & set(table0)):
            r = table0[n]
            for flag in RL.FLAGS:
                if r[flag]:
                    cat.add(('char', flag, n))
            for s in r['inverse']:
                if s in need:
                    cat.add(norm_pax(('pinv', n, s)))
            for s in r['sub']:
                if s in need:
                    cat.add(('psub', n, s))
            for s, t in r['chains']:
                if s in need and t in need:
                    cat.add(('chain', n, s, t))
            for s in r['disjoint']:
                if s in need:
                    cat.add(norm_pax(('pdisjoint', n, s)))
        if 'edit' in units:
            # the edit's property axioms come from the edit unit only
            for t in units['edit']['pax']:
                if D.names_in(t)['rel'] <= set(table0):
                    remove_pax(table0, norm_pax(t))
            cat -= {norm_pax(t) for t in units['edit']['pax']}
        for t in sorted(cat):
            txt = pax_text(t)
            units[f'rbox:{txt}'] = {'kind': 'rbox', 'facts': [], 'pax': [t], 'text': txt}
        return units, table0

    # ----- targets

    def target_for(self, fq, qi, expected):
        """('probe', probe) or ('incons', claim) for the record's answer, or
        (None, why) when there is no entailment to justify."""
        if expected is None:
            return None, 'answer is null (does not know): nothing follows'
        if 'find' in fq:
            exp = self.surf.get(D.norm(expected))
            if exp is None:
                return None, f'answer {expected!r} maps to no entity'
            subj, ce = D.parse_find(fq['find'])
            return ('probe', ('member', subj, R.subst(ce, exp))), f'{subj} : {fq["find"]} = {exp}'
        yn = D.yes_no(expected)
        mode = fq.get('mode', 'holds')
        claim = D.parse_axiom(fq['ask'])
        if mode == 'consistent':
            if yn != 'no':
                return None, 'consistency of the claim (nothing follows)'
            _, neg = (R.claim_probes(claim) if claim[0] != 'sub' else (None, None))
            return (('probe', neg) if neg else ('incons', fq['ask'])), f'not ({fq["ask"]})'
        if yn == 'yes':
            pos, _ = R.claim_probes(claim)
            return ('probe', pos), fq['ask']
        if yn == 'no' and mode == 'holds':
            if claim[0] == 'sub':
                return ('incons', fq['ask']), f'not ({fq["ask"]})'
            _, neg = R.claim_probes(claim)
            return ('probe', neg), f'not ({fq["ask"]})'
        return None, f'"{expected}" under mode {mode}: the claim does not follow (nothing to justify)'

    def justify(self, fq, qi, phase, w, expected, single=False):
        target, desc = self.target_for(fq, qi, expected)
        if target is None:
            return {'status': 'nothing', 'detail': desc}
        units, table0 = self.units_for(fq, phase, w)
        pb = Problem(self, units, table0, target, self.stats)
        t0 = time.time()
        res = pb.all_justifications(self.max_just, self.budget, single=single)
        out = {'status': 'ok' if res['entailed'] else 'not_entailed', 'claim': desc, 'expected': expected,
               'seconds': round(time.time() - t0, 1), 'capped': res['capped'], 'units': len(units),
               'module': len(res['module'] or [])}
        if not res['entailed']:
            out['detail'] = 'the answer does not follow from the whole knowledge base (see reason_report.json)'
            return out
        out['justifications'] = [self.describe(units, j, fq, qi) for j in sorted(res['justifications'],
                                                                              key=lambda j: (len(j), sorted(j)))]
        return out

    # ----- mapping a justification to metadata

    def sentences(self, qi, kind='bridge'):
        """The query's bridge sentences, or its revision facts."""
        return list(self.rec['queries']['derived'][qi].get(kind) or [])

    def unit_sentences(self, uid, u, qi, kind='bridge'):
        """Sentences of query qi's `kind` list ('bridge' or 'revision_facts')
        this unit states: by bridge_refs / revision_refs, or, for a fact unit
        named in neither, by its named entities' surfaces all appearing in the
        sentence."""
        sents = self.sentences(qi, kind)
        key = uid.split(':', 1)[1] if uid.startswith('bg:') else \
            f'q{qi}.given.{uid.split(":", 1)[1]}' if uid.startswith('given:') else None
        if key is not None and key in self.refs[kind]:
            refs = self.refs[kind][key]
            return [s for s in sents if any(D.norm(s) == D.norm(r) for r in refs)]
        if key is not None and any(key in r for r in self.refs.values()):
            return []           # the refs map it to the other list
        if u['kind'] not in ('bg', 'given', 'store', 'add') or not u['facts']:
            return []
        inds = set()
        for a in u['facts']:
            inds |= D.names_in(D.parse_axiom(a))['ind']
        ents = self.f.get('entities') or {}
        # surfaces, plus the key read as words ("tropical_rainforest")
        surf = {i: ([ents[i]] if isinstance(ents.get(i), str) else list(ents.get(i) or [])) + [i.replace('_', ' ')]
                for i in inds}
        if not inds:
            return []
        out = []
        for s in sents:
            ns = ' ' + D.norm(s) + ' '
            if all(any(' ' + D.norm(x) + ' ' in ns for x in v) for v in surf.values()):
                out.append(s)
        return out

    def unit_bridges(self, uid, u, qi):
        return self.unit_sentences(uid, u, qi, 'bridge')

    def describe(self, units, J, fq, qi):
        premises = set(self.f.get('premises') or [])
        items, types, covered, extra, support, revision = [], set(), [], [], [], []
        for uid in sorted(J, key=order_key):
            u = units[uid]
            ty = sorted(unit_types(u))
            types |= set(ty)
            role = u['kind']
            br, rv = [], []
            if u['kind'] in ('bg', 'given', 'store', 'add'):
                br = self.unit_bridges(uid, u, qi)
                rv = [] if br else self.unit_sentences(uid, u, qi, 'revision_facts')
                key = uid.split(':', 1)[1]
                if br:
                    role = 'bridge'
                    covered += [s for s in br if s not in covered]
                elif rv:
                    role = 'revision'       # a listed revision fact, here used to build the answer
                    revision += [s for s in rv if s not in revision]
                elif u['kind'] == 'bg' and key in premises:
                    role = 'premise'
                elif u['kind'] == 'bg' and key in self.firm and all(
                        D.parse_axiom(a)[0] in ('sub', 'equiv', 'disjoint', 'rule') for a in u['facts']) and u['facts']:
                    role = 'definition'     # a firm class axiom or rule the record treats as definitional
                    support.append(uid)
                elif u['kind'] in ('add', 'store'):
                    role = 'world'
                elif u['pax'] and not u['facts']:
                    role = 'property'       # a relation property the prompt states
                elif is_typing(u):
                    role = 'typing'
                    support.append(uid)
                else:
                    role = 'unlisted'
                    extra.append(uid)
            items.append({'unit': uid, 'role': role, 'axiom': u['text'], **({'types': ty} if ty else {}),
                          **({'bridge': br} if br else {}), **({'revision': rv} if rv else {})})
        # class inclusions chained (edit included): transitivity of subclass_of
        ncls = sum(1 for uid in J for a in units[uid]['facts'] if D.parse_axiom(a)[0] in ('sub', 'equiv'))
        if ncls >= 2:
            types.add('subclass_transitivity')
        return {'units': sorted(J, key=order_key), 'items': items, 'types': sorted(types),
                'uses_edit': 'edit' in J, 'uses_premises': bool({f'bg:{k}' for k in premises} & set(J)), 'bridges_covered': covered, 'revision_used': revision,
                'unlisted': extra, 'hops': 1 + len(covered) + len(extra)}

    # ----- comparison with the record

    def compare(self, qi, justs_by_world, fq, other=()):
        """Verdict for one query from its main-target justifications (all
        worlds pooled). `other`: the other phase's justifications (pre edit,
        for a replace): a listed bridge only the original answer needs counts
        as used (`pre_only_bridge`), since the record's bridges cover both
        answers. Listed revision facts are not bridges: one the answer does not
        use is fine; one every edit-using justification uses builds the answer,
        so it should be a bridge (`revision_as_bridge`)."""
        rq = self.rec['queries']['derived'][qi]
        der, bridges, hops, via = rq['derivation'], list(rq.get('bridge') or []), rq['hops'], rq.get('via')
        revision, alts = list(rq.get('revision_facts') or []), list(rq.get('alt_derivations') or [])
        justs = [j for g in justs_by_world.values() for j in g]
        if not justs:
            return {'verdict': 'not_checked', 'why': 'no justification'}
        other_cov = {b for j in other for b in j['bridges_covered']}
        all_units_bridges = self.encoded_bridges(qi, fq)
        # revision facts every justification uses (every one that uses the edit,
        # when some do: an edit-free route, such as a world that keeps the old
        # answer, is the no_edit flag's business): the answer is built from them
        routes = [j for j in justs if j['uses_edit']] or justs
        rev_always = [r for r in revision if all(r in j.get('revision_used', []) for j in routes)]
        best, best_score = None, None
        for js in justs:
            types = set(js['types'])
            der_ok = self.derivation_ok(der, types, js, qi)
            unencoded = [b for b in bridges if b not in all_units_bridges]
            pre_only = [b for b in bridges if b not in js['bridges_covered'] and b in other_cov]
            missing = [b for b in bridges if b not in js['bridges_covered'] and b in all_units_bridges
                       and b not in pre_only]
            extra = js['unlisted']
            # hops the record should have: unencoded bridges are not judged
            hops_ok = js['hops'] + len(pre_only) == hops - len(unencoded)
            score = (der_ok, not missing and not extra, hops_ok, not js.get('revision_used'), -len(js['units']))
            if best_score is None or score > best_score:
                best_score, best = score, {'derivation_ok': der_ok, 'missing_bridge': missing,
                                           'unencoded_bridge': unencoded, 'pre_only_bridge': pre_only,
                                           'unlisted': extra, 'revision_used': list(js.get('revision_used', [])),
                                           'hops': js['hops'], 'hops_ok': hops_ok, 'types': sorted(types),
                                           'units': js['units']}
        best['revision_as_bridge'] = rev_always
        if revision:
            enc = self.encoded_bridges(qi, fq, 'revision_facts')
            best['unencoded_revision'] = [r for r in revision if r not in enc]
        if not best['derivation_ok']:
            verdict = 'mismatch'
        elif best['missing_bridge'] or best['unlisted'] or not best['hops_ok'] or rev_always:
            verdict = 'partial'
        else:
            verdict = 'match'
        out = {'verdict': verdict, 'record': {'derivation': der, 'bridge': bridges, 'hops': hops,
                                               **({'revision_facts': revision} if revision else {}),
                                               **({'alt_derivations': alts} if alts else {}),
                                               **({'via': via} if via else {})}, 'best': best}
        # several justifications of one entailment (one world) that use the
        # edit, with different property sets: the derivation is underdetermined,
        # unless the record names every route (derivation + alt_derivations).
        # (Edit-free ones, such as a stored by-name answer, are the no_edit flag.)
        amb, groups = set(), []
        for group in justs_by_world.values():
            sets = {tuple(sorted(set(j['types']) & (PROPERTY_DERIVATIONS | {'disjointness', 'rule'})))
                    for j in group if j['uses_edit']}
            if len(sets) > 1:
                amb |= {' + '.join(x) or 'no property' for x in sets}
                groups.append(sets)
        if amb:
            if alts and all(routes_named([der] + alts, sets) for sets in groups):
                out['alternatives_listed'] = sorted(amb)
            else:
                out['ambiguous'] = sorted(amb)
        if via:
            out['via_used'] = any(via in u for j in justs for u in j['units'] if u.startswith('rbox:')) or \
                any(via in it['axiom'] for j in justs for it in j['items'] if it['role'] == 'given')
        return out

    def encoded_bridges(self, qi, fq, kind='bridge'):
        """Bridge sentences (or revision facts) of query qi stated by some unit
        of the record."""
        out = set()
        for phase in ('pre', 'post'):
            for w in self.worlds:
                units, _ = self.units_for(fq, phase, w)
                for uid, u in units.items():
                    out |= set(self.unit_sentences(uid, u, qi, kind))
        return out

    def derivation_ok(self, der, types, js, qi):
        if der in PROPERTY_DERIVATIONS:
            if der == 'inheritance':
                return 'inheritance' in types
            if der == 'transitivity' and 'subclass_transitivity' in types and \
                    'subclass_of' in (self.rec.get('relation'), self.rec['queries']['derived'][qi].get('via')):
                return True
            return der in types
        if der == 'instantiation':
            return js['uses_edit']
        return True   # task types need no property of their own

    # ----- one query, one record

    def skip(self, fq, qi):
        """(base fields, not_checked entry or None) for one query."""
        rq = self.rec['queries']['derived'][qi]
        ans = self.answers(qi)
        base = {'q': qi, 'derivation': rq['derivation'], 'determinacy': ans['determinacy'], 'logic': rq['logic']}
        if 'not_checked' in fq or 'exception' in fq:
            return base, base | {'verdict': 'not_checked',
                                 'why': fq.get('not_checked') or 'exception: ' + fq['exception']}
        if self.op == 'delete' and rq['derivation'] == 'functional':
            return base, base | {'verdict': 'not_checked',
                                 'why': 'functional under delete: the post answer is "does not know" (nothing '
                                        'follows) and the pre answer restates the deleted fact'}
        return base, None

    def live_worlds(self):
        return [w for w, s in self.worlds.items() if not s.get('exception')] or ['*']

    def post_expected(self, qi):
        ans = self.answers(qi)
        indeterminate = bool(ans['worlds'])
        return {w: (ans['worlds'].get(w) if indeterminate else ans['new']) for w in self.live_worlds()}

    def check_query(self, fq, qi):
        base, done = self.skip(fq, qi)
        if done:
            return done
        t0 = time.time()
        ans = self.answers(qi)
        live = self.live_worlds()
        # Main target: the post-edit answer; for a delete (no edit post) or
        # when nothing follows post edit, the pre-edit original answer, with
        # the deleted / original fact as the edit unit. The other phase gets
        # one justification for reference.
        post_exp = self.post_expected(qi)
        main_phase = 'pre' if self.op == 'delete' or all(v is None for v in post_exp.values()) else 'post'
        post = {w: self.justify(fq, qi, 'post', w, post_exp[w], single=main_phase == 'pre') for w in live}
        if main_phase == 'post' and not any(v['status'] == 'ok' for v in post.values()):
            main_phase = 'pre'
        pre, by_stores = {}, {}
        if ans['original'] is None:
            pre = {live[0]: {'status': 'nothing', 'detail': 'no original answer'}}
        else:
            for w in (live if main_phase == 'pre' else live[:1]):
                key = json.dumps(sorted((self.worlds.get(w) or {}).get('stores') or []))
                if key in by_stores:     # same pre knowledge base as an earlier world
                    pre[w] = pre[by_stores[key]]
                    continue
                by_stores[key] = w
                pre[w] = self.justify(fq, qi, 'pre', w, ans['original'], single=main_phase == 'post')
        out = self.evaluate(base | {'post': post, 'pre': pre, 'main': main_phase}, fq, qi)
        out['seconds'] = round(time.time() - t0, 1)
        return out

    def evaluate(self, out, fq, qi):
        """Verdict and flags of one query from its justifications (out: base
        fields + post, pre, main). No HermiT: --recompare reuses it."""
        rq = self.rec['queries']['derived'][qi]
        indeterminate = bool(self.answers(qi)['worlds'])
        post, pre, main_phase = out['post'], out['pre'], out['main']
        main = post if main_phase == 'post' else pre
        by_world = {w: v['justifications'] for w, v in main.items() if v.get('status') == 'ok'}
        if main_phase == 'pre' and self.f.get('premises'):
            # The original fact also follows from its premises (a derived edit):
            # a justification that re-derives it from them is the same route.
            for w, js in by_world.items():
                if any(j['uses_edit'] for j in js):
                    rest = [j for j in js if j['uses_edit'] or not j['uses_premises']]
                    if len(rest) < len(js):
                        out.setdefault('via_premises', []).append(w)
                    by_world[w] = rest
        if not by_world:
            why = '; '.join(f'{ph} {w}: {v.get("detail") or v["status"]}' for ph, d in (('post', post), ('pre', pre))
                            for w, v in d.items())
            return out | {'verdict': 'not_checked', 'why': why}
        other = [j for v in (pre if main_phase == 'post' else {}).values() if v.get('status') == 'ok'
                 for j in v['justifications']]
        out |= self.compare(qi, by_world, fq, other)
        # The edit (pre: the original fact) is not needed for some justification.
        # For an indeterminate query a world that keeps the old answer may not
        # need the edit; that is flagged only when no world needs it.
        # Pre edit, a derived edit's premises count as the edit: deleting the
        # fact forces one of them to go.
        dep = (lambda j: j['uses_edit'] or j['uses_premises']) if main_phase == 'pre' else (lambda j: j['uses_edit'])
        noedit = [w for w, js in by_world.items() if any(not dep(j) for j in js)]
        if noedit:
            flag = not indeterminate or len(noedit) == len(by_world)
            key = 'no_edit' if flag else 'edit_free_worlds'
            out[key] = {'worlds': noedit, 'discriminates': rq.get('discriminates', True)}
        # do the worlds' justifications differ (by unit sets)?
        if main_phase == 'post' and len(main) > 1:
            sets = {json.dumps(sorted(map(tuple, (j['units'] for j in v.get('justifications', []))))) for v in main.values()}
            out['worlds_differ'] = len(sets) > 1
        out['capped'] = any(v.get('capped') for v in main.values())
        return out

    def recompare_query(self, fq, qi, old):
        """Verdict of one query from its stored justifications (`old`, its
        entry in justifications.json) against the current record and formal
        file: each stored justification's units are mapped again (roles,
        bridges, revision facts, hops). A stored entry whose units or expected
        answers no longer exist is `stale` (rerun justify.py on the record)."""
        base, done = self.skip(fq, qi)
        if done:
            return done
        if not old or 'main' not in old:
            return base | {'verdict': 'not_checked', 'why': 'not justified yet: rerun justify.py on the record',
                           'stale': 'encoded now, but no stored justifications'
                                    + (f' (stored: {old["why"]})' if (old or {}).get('why') else '')}
        ans = self.answers(qi)
        exp = {'post': self.post_expected(qi), 'pre': {w: ans['original'] for w in self.live_worlds()}}
        out = base | {'main': old['main'], 'post': {}, 'pre': {}}
        for phase in ('post', 'pre'):
            for w, v in (old.get(phase) or {}).items():
                v = dict(v)
                if v.get('status') == 'ok':
                    if w not in exp[phase] or exp[phase][w] != v.get('expected'):
                        return base | {'verdict': 'not_checked', 'why': 'stale: expected answers changed',
                                       'stale': f'{phase} {w}: answer {v.get("expected")!r} is now '
                                                f'{exp[phase].get(w)!r}'}
                    units, _ = self.units_for(fq, phase, w)
                    js = []
                    for j in v['justifications']:
                        gone = [u for u in j['units'] if u not in units]
                        if gone:
                            return base | {'verdict': 'not_checked', 'why': 'stale: formal file changed',
                                           'stale': f'{phase} {w}: units {gone} are gone'}
                        js.append(self.describe(units, frozenset(j['units']), fq, qi))
                    v['justifications'] = js
                out[phase][w] = v
        out = self.evaluate(out, fq, qi)
        if 'seconds' in old:
            out['seconds'] = old['seconds']
        return out

    def recompare(self, old):
        fqs = {q['q']: q for q in self.f.get('queries') or []}
        olds = {q['q']: q for q in (old or {}).get('queries', [])}
        out = []
        for qi in range(len(self.rec['queries']['derived'])):
            fq = fqs.get(qi, {'q': qi, 'not_checked': 'not encoded'})
            try:
                out.append(self.recompare_query(fq, qi, olds.get(qi)))
            except Exception as e:
                out.append({'q': qi, 'verdict': 'not_checked', 'why': f'error: {type(e).__name__}: {e}'})
        res = {k: old[k] for k in ('seconds', 'calls', 'subsets') if k in (old or {})}
        return res | {'recompared': time.strftime('%Y-%m-%d %H:%M:%S'), 'queries': out}

    def run(self):
        t0 = time.time()
        fqs = {q['q']: q for q in self.f.get('queries') or []}
        out = []
        for qi in range(len(self.rec['queries']['derived'])):
            fq = fqs.get(qi, {'q': qi, 'not_checked': 'not encoded'})
            try:
                out.append(self.check_query(fq, qi))
            except Exception as e:
                out.append({'q': qi, 'verdict': 'not_checked', 'why': f'error: {type(e).__name__}: {e}'})
        return {'seconds': round(time.time() - t0, 1), 'calls': self.stats['calls'],
                'subsets': self.stats['subsets'], 'queries': out}


# ---------------------------------------------------------------- driver

def run_one(args):
    rid, max_just, budget = args
    table = RL.load_table()
    try:
        probs = D.check_formal(D.load_formal(rid), D.load_record(rid), set(table))
        if probs:
            return rid, {'error': 'encoding: ' + '; '.join(probs), 'queries': []}
        return rid, Justifier(rid, table, max_just, budget).run()
    except Exception as e:
        return rid, {'error': f'{type(e).__name__}: {e}', 'queries': []}


def recompare_one(args):
    rid, old = args
    table = RL.load_table()
    try:
        probs = D.check_formal(D.load_formal(rid), D.load_record(rid), set(table))
        if probs:
            return rid, {'error': 'encoding: ' + '; '.join(probs), 'queries': []}
        return rid, Justifier(rid, table).recompare(old)
    except Exception as e:
        return rid, {'error': f'{type(e).__name__}: {e}', 'queries': []}


def summary(records):
    c = Counter()
    for r in records.values():
        for q in r.get('queries', []):
            c[q['verdict']] += 1
            for f in FLAGS:
                if q.get(f) or (q.get('best') or {}).get(f):
                    c[f] += 1
    return {k: c.get(k, 0) for k in VERDICTS + FLAGS}


def flagged(rid, q):
    """One line per verdict other than match, and per flag."""
    lines = []
    tag = f'{rid} q{q["q"]} ({q.get("derivation")})'
    if q['verdict'] in ('partial', 'mismatch'):
        b = q['best']
        why = []
        if not b['derivation_ok']:
            why.append(f'uses {", ".join(b["types"]) or "no property"}, not {q["derivation"]}')
        if b['missing_bridge']:
            why.append('missing bridge: ' + ' | '.join(b['missing_bridge']))
        if b['unlisted']:
            why.append('uses unlisted: ' + ', '.join(b['unlisted']))
        if not b['hops_ok']:
            why.append(f'hops {b["hops"]} vs record {q["record"]["hops"]}')
        if b.get('revision_as_bridge'):
            why.append('revision fact used to build the answer (should be a bridge): '
                       + ' | '.join(b['revision_as_bridge']))
        lines.append(f'{q["verdict"].upper()} {tag}: ' + '; '.join(why))
    if q.get('no_edit'):
        lines.append(f'NO-EDIT {tag}: a justification without the edit in {", ".join(q["no_edit"]["worlds"])}'
                     + ('' if q['no_edit']['discriminates'] else ' (discriminates: false)'))
    if q.get('ambiguous'):
        lines.append(f'AMBIGUOUS {tag}: ' + ' / '.join(q['ambiguous']))
    if q.get('alternatives_listed'):
        lines.append(f'{q["verdict"].upper()} (alternatives listed) {tag}: ' + ' / '.join(q['alternatives_listed']))
    if q.get('stale'):
        lines.append(f'STALE {tag}: {q["stale"]} (rerun justify.py on it)')
    if q.get('capped'):
        lines.append(f'CAPPED {tag}')
    return lines


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('ids', nargs='*')
    ap.add_argument('--topic')
    ap.add_argument('--jobs', type=int, default=2)
    ap.add_argument('--max-just', type=int, default=MAX_JUST, help='justifications per entailment (default 5)')
    ap.add_argument('--budget', type=float, default=BUDGET, help='seconds per entailment for the hitting-set tree')
    ap.add_argument('--recompare', action='store_true',
                    help='no HermiT: recompute verdicts from the justifications stored in the report against '
                         'the current records and formal files')
    ap.add_argument('--report', type=Path, default=OUT, help='report to read and write (default owl/justifications.json)')
    args = ap.parse_args(argv)
    if args.recompare:
        return main_recompare(args)
    scope = R.all_record_ids(args.topic)
    have = {p.stem for p in (R.OWL_DIR / 'formal').glob('*.json')}
    ids = args.ids or [r for r in scope if r in have]
    t0 = time.time()
    # owlready2 keeps memory per World; fresh workers every few records cap it
    with Pool(max(1, args.jobs), maxtasksperchild=5) as pool:
        results = dict(pool.imap_unordered(run_one, [(i, args.max_just, args.budget) for i in ids]))
    old = json.loads(args.report.read_text()) if args.report.exists() else {}
    records = old.get('records', {})
    records.update(results)
    report = {'generated': time.strftime('%Y-%m-%d %H:%M:%S'), 'summary': summary(records),
              'records_checked': len(records), 'max_just': args.max_just, 'budget': args.budget,
              'records': dict(sorted(records.items()))}
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=1) + '\n')
    secs = [q['seconds'] for r in results.values() for q in r.get('queries', []) if 'seconds' in q]
    print(f'justified {len(ids)} records in {time.time() - t0:.0f}s with {args.jobs} jobs '
          f'({sum(r.get("calls", 0) for r in results.values())} HermiT calls, '
          f'{sum(r.get("subsets", 0) for r in results.values())} subsets); '
          f'{len(secs)} queries, {sum(secs) / max(1, len(secs)):.1f}s each on average, max {max(secs, default=0):.0f}s')
    print('  ' + '  '.join(f'{k} {v}' for k, v in summary(results).items()))
    print_flagged(results)
    print(f'report: {args.report}')
    return 0


def print_flagged(results):
    for rid, r in sorted(results.items()):
        if r.get('error'):
            print(f'ERROR {rid}: {r["error"][:300]}')
        for q in r.get('queries', []):
            if q['verdict'] == 'not_checked' and q.get('why', '').startswith('error'):
                print(f'ERROR {rid} q{q["q"]}: {q["why"][:300]}')
            for line in flagged(rid, q):
                print(line[:500])


def main_recompare(args):
    """--recompare: verdicts again from the stored justifications (records in
    the report, or the ids / topic given), no HermiT. Each stored justification
    keeps its units; their roles, bridges, revision facts and hops are mapped
    again from the current record and formal file."""
    old = json.loads(args.report.read_text())
    records = old.get('records', {})
    ids = args.ids or [r for r in records if not args.topic or r.startswith(args.topic + '-')]
    t0 = time.time()
    with Pool(max(1, args.jobs)) as pool:
        results = dict(pool.imap_unordered(recompare_one, [(i, records.get(i)) for i in ids]))
    before = summary({i: records[i] for i in ids if i in records})
    records.update(results)
    old.update({'recompared': time.strftime('%Y-%m-%d %H:%M:%S'), 'summary': summary(records),
                'records_checked': len(records), 'records': dict(sorted(records.items()))})
    args.report.write_text(json.dumps(old, ensure_ascii=False, indent=1) + '\n')
    print(f'recompared {len(ids)} records in {time.time() - t0:.0f}s (no HermiT)')
    print('  before: ' + '  '.join(f'{k} {v}' for k, v in before.items()))
    print('  after:  ' + '  '.join(f'{k} {v}' for k, v in summary(results).items()))
    print_flagged(results)
    print(f'report: {args.report}')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
