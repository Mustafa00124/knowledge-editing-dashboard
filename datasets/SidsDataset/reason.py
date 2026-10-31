#!/usr/bin/env python3
"""Formally check Sid's Dataset records with HermiT (owlready2), from the
encodings in owl/formal/<record_id>.json (schema: owl/README.md).

    venvs/easyedit_venv/bin/python datasets/SidsDataset/reason.py                 # every formal file
    venvs/easyedit_venv/bin/python datasets/SidsDataset/reason.py --topic geography
    venvs/easyedit_venv/bin/python datasets/SidsDataset/reason.py geography-replace-0001 ...

Per record, writing owl/reason_report.json (records not run keep their old
entry) and printing a summary; always exits 0:

  derived_edit     (a) a derived edit's original fact follows from its premises
  pre              (b) each derived query's original answer follows before the edit
  post_determinate (c) a determinate (or RBox / unlabelled) query's new answer
                       follows in every world
  consistent       (c) the edit plus each world is consistent
  post_worlds      (d) an indeterminate query's answer follows in each world
  differ           (d) those answers differ between at least two worlds
  missing_worlds   (e) when the edit contradicts the background, every minimal
                       repair (smallest set of non-firm background facts to give
                       up) is covered by some world
  not_checked      (f) fol queries and anything the file leaves out, with why

Each check is pass, fail or not_checked, with a detail. A find answer also
fails when another candidate answer follows too (unless "exclusive": false).
"""
import argparse
import itertools
import json
import sys
import time
import types
from collections import Counter, defaultdict
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OWL_DIR = ROOT / 'owl'
sys.path.insert(0, str(OWL_DIR))
sys.path.insert(0, str(ROOT))
import dlsyntax as D  # noqa: E402
import relations as RL  # noqa: E402

REPORT = OWL_DIR / 'reason_report.json'
IND_IRI = 'http://sids.dataset/ind#'
CLS_IRI = 'http://sids.dataset/cls#'
MAX_REPAIR = 3          # largest repair (number of background facts given up) searched for


# ---------------------------------------------------------------- property table edits

def apply_property_axiom(table, tree, add):
    """Add or remove one property axiom in the relation table (in place)."""
    k = tree[0]

    def rel(n):
        if n not in table:
            table[n] = RL.empty_rel() | {'catalogued': False}
        return table[n]
    if k == 'char':
        rel(tree[2])[tree[1]] = add
        # An inverse pair shares transitivity, asymmetry and symmetry
        # (RELATIONS.md states them on one row), so removing one from a
        # relation removes it from its inverse too.
        if not add and tree[1] in ('transitive', 'asymmetric', 'symmetric'):
            for n, r in table.items():
                if n in rel(tree[2])['inverse'] or tree[2] in r['inverse']:
                    r[tree[1]] = False
    elif k == 'psub':
        lst = rel(tree[1])['sub']
        if add and tree[2] not in lst:
            lst.append(tree[2])
        elif not add and tree[2] in lst:
            lst.remove(tree[2])
    elif k == 'pinv':
        a, b = tree[1], tree[2]
        for x, y in ((a, b), (b, a)):
            lst = rel(x)['inverse']
            if add and y not in lst:
                lst.append(y)
            elif not add and y in lst:
                lst.remove(y)
    elif k == 'chain':
        lst = rel(tree[1])['chains']
        c = [tree[2], tree[3]]
        if add and c not in lst:
            lst.append(c)
        elif not add and c in lst:
            lst.remove(c)
    elif k == 'pdisjoint':
        lst = rel(tree[1])['disjoint']
        if add and tree[2] not in lst:
            lst.append(tree[2])
        elif not add and tree[2] in lst:
            lst.remove(tree[2])


# ---------------------------------------------------------------- one knowledge base

class KB:
    """One ontology: a relation table, axiom strings, the individuals, and
    probes (named query classes) whose members HermiT computes in one call."""

    def __init__(self, table, axioms, entities, distinct):
        self.table, self.axioms, self.entities, self.distinct = table, list(axioms), entities, distinct
        self.probes = {}   # key -> ('member', ind, ce) | ('unsat', ce)

    def probe(self, *p):
        key = repr(tuple(p))
        self.probes[key] = tuple(p)
        return key

    def signature(self):
        return json.dumps([sorted(self.axioms), self.table_sig, sorted(self.probes)], ensure_ascii=False)


def run_kb(kb):
    """{'consistent': bool|None, 'error': str|None, 'probes': {key: bool}}"""
    import owlready2 as o
    world = o.World()
    onto = world.get_ontology('http://sids.dataset/kb.owl')
    trees = [D.parse_axiom(a) for a in kb.axioms]
    used = {'ind': set(), 'rel': set(), 'cls': set()}
    for t in trees:
        D.names_in(t, used)
    for p in kb.probes.values():
        D.names_in(p[-1] if p[0] == 'unsat' else p[2], used)
    props, _ = RL.build(onto, kb.table, used['rel'])
    ind_ns, cls_ns = onto.get_namespace(IND_IRI), onto.get_namespace(CLS_IRI)
    classes, inds, helpers = {}, {}, [0]

    def cls(name):
        if name == 'Thing':
            return o.Thing
        if name == 'Nothing':
            return o.Nothing
        if name not in classes:
            classes[name] = types.new_class(name, (o.Thing,), exec_body=lambda d: d.update(namespace=cls_ns))
        return classes[name]

    def ind(key):
        if key not in inds:
            inds[key] = o.Thing(key, namespace=ind_ns)
        return inds[key]

    def pe(t):
        return o.Inverse(props[t[1]]) if t[0] == 'inv' else props[t[1]]

    def ce(t):
        k = t[0]
        if k == 'class':
            return cls(t[1])
        if k == 'and':
            return o.And([ce(x) for x in t[1]])
        if k == 'or':
            return o.Or([ce(x) for x in t[1]])
        if k == 'not':
            return o.Not(ce(t[1]))
        if k == 'some':
            return pe(t[1]).some(ce(t[2]))
        if k == 'only':
            return pe(t[1]).only(ce(t[2]))
        if k == 'value':
            return pe(t[1]).value(ind(t[2]))
        if k in ('min', 'max', 'exactly'):
            return getattr(pe(t[2]), k)(t[1], ce(t[3]))
        if k == 'oneof':
            return o.OneOf([ind(x) for x in t[1]])
        raise ValueError(f'not a class expression: {t}')

    def named(t):
        """A named class for a class expression (a helper equivalent to it)."""
        if t[0] == 'class':
            return cls(t[1])
        helpers[0] += 1
        h = cls(f'_H{helpers[0]}')
        h.equivalent_to.append(ce(t))
        return h

    with onto:
        for key in kb.entities:
            ind(key)
        if len(kb.distinct) > 1:
            o.AllDifferent([ind(k) for k in kb.distinct])
        for t in trees:
            k = t[0]
            if k == 'prop':
                props[t[1]][ind(t[2])].append(ind(t[3]))
            elif k == 'nprop':
                ind(t[2]).is_a.append(o.Not(props[t[1]].value(ind(t[3]))))
            elif k == 'type':
                ind(t[1]).is_a.append(ce(t[2]))
            elif k == 'same':
                ind(t[1]).equivalent_to.append(ind(t[2]))
            elif k == 'different':
                o.AllDifferent([ind(t[1]), ind(t[2])])
            elif k == 'sub':
                named(t[1]).is_a.append(ce(t[2]))
            elif k == 'equiv':
                named(t[1]).equivalent_to.append(ce(t[2]))
            elif k == 'disjoint':
                o.AllDisjoint([named(t[1]), named(t[2])])
            elif k == 'rule':
                def atom(a):
                    if a[0] == 'class':
                        return cls(a[1]), [x if x.startswith('?') else ind(x) for x in a[2]]
                    if a[0] == 'prop':
                        return props[a[1]], [x if x.startswith('?') else ind(x) for x in a[2]]
                    return a[0], [x if x.startswith('?') else ind(x) for x in a[1]]
                RL.make_rule(onto, [atom(a) for a in t[1]], [atom(a) for a in t[2]])
            # property axioms were applied to the table already
        qcls = {}
        for i, (key, p) in enumerate(sorted(kb.probes.items())):
            q = cls(f'_Q{i}')
            q.equivalent_to.append(ce(p[-1] if p[0] == 'unsat' else p[2]))
            qcls[key] = q
    out = {'consistent': None, 'error': None, 'probes': {}}
    try:
        with onto:
            o.sync_reasoner_hermit(world, debug=0)
        out['consistent'] = True
    except o.OwlReadyInconsistentOntologyError:
        out['consistent'] = False
        return out
    except o.OwlReadyJavaError as e:
        lines = [l for l in str(e).splitlines() if 'Exception' in l or 'Error' in l]
        out['error'] = (lines[0] if lines else str(e))[:400]
        return out
    for key, p in kb.probes.items():
        q = qcls[key]
        if p[0] == 'unsat':
            out['probes'][key] = o.Nothing in q.equivalent_to
        else:
            # owlready2's list of an individual's classes can miss a class
            # HermiT found equivalent to one it lists (FINDINGS D), so the
            # classes equivalent to a listed one, and their superclasses,
            # count too.
            out['probes'][key] = q in member_classes(inds[p[1]], o)
    return out


def member_classes(ind, o):
    """Every named class an individual belongs to after reasoning: its
    classes, the classes equivalent to them, and their superclasses."""
    seen, todo = set(), [c for c in ind.INDIRECT_is_a if isinstance(c, o.ThingClass)]
    while todo:
        c = todo.pop()
        if c in seen:
            continue
        seen.add(c)
        for d in list(c.equivalent_to) + list(c.INDIRECT_equivalent_to) + list(c.ancestors()):
            if isinstance(d, o.ThingClass) and d not in seen:
                todo.append(d)
    return seen


# ---------------------------------------------------------------- one record

class Record:
    def __init__(self, rid, base_table):
        self.rid = rid
        self.rec = D.load_record(rid)
        self.f = D.load_formal(rid)
        self.op = self.rec['edit_operation']
        self.base_table = base_table
        self.calls = 0
        self.cache = {}
        self.bg = D.background_items(self.f)
        self.firm = set(self.f.get('firm') or [])
        self.common_gu = set(self.f.get('gives_up') or [])
        self.worlds = self.f.get('worlds') or {'*': {}}
        ents = self.f.get('entities') or {}
        self.entities = list(ents)
        d = self.f.get('distinct', 'all')
        self.distinct = [k for k, v in ents.items() if v is not None] if d == 'all' else list(d)
        self.surf = D.surfaces(self.f)
        # Split the edit's axioms into facts and property axioms.
        self.orig_facts, self.orig_props = self.split(self.f.get('original') or [])
        self.edit_facts, self.edit_props = self.split(self.f.get('edit') or [])

    @staticmethod
    def split(axioms):
        facts, props = [], []
        for a in axioms:
            (props if D.is_property_axiom(D.parse_axiom(a)) else facts).append(a)
        return facts, props

    def table_for(self, phase, extra_axioms):
        """The relation table for a phase: RELATIONS.md, the file's local
        relations, the RBox edit (pre: original present, edit absent; post:
        the other way round; delete post: original absent), then property
        axioms among the KB's axioms."""
        table = json.loads(json.dumps(self.base_table))
        for name, tags in (self.f.get('relations') or {}).items():
            table[name] = RL.parse_tags(tags) | {'catalogued': False}
        ops = []
        if phase == 'pre':
            ops = [(a, False) for a in self.edit_props] + [(a, True) for a in self.orig_props]
        elif phase == 'post':
            ops = [(a, False) for a in self.orig_props]
            if self.op != 'delete':
                ops += [(a, True) for a in self.edit_props]
        ops += [(a, True) for a in extra_axioms if D.is_property_axiom(D.parse_axiom(a))]
        for a, add in ops:
            apply_property_axiom(table, D.parse_axiom(a), add)
        return table, json.dumps([(a, add) for a, add in ops])

    def axioms(self, phase, w, drop=None):
        """Axiom strings (facts, class axioms, rules) of a phase in world w."""
        spec = self.worlds.get(w) or {}
        if phase == 'pre':
            keep = list(self.bg)
            out = list(spec.get('stores') or []) + self.orig_facts
        else:
            gone = self.common_gu | set(spec.get('gives_up') or []) if drop is None else set(drop)
            keep = [k for k in self.bg if k not in gone]
            out = list(spec.get('stores') or []) + (list(spec.get('adds') or []) if drop is None else [])
            if self.op != 'delete':
                out += self.edit_facts
        for k in keep:
            out += self.bg[k]
        return out

    def run(self, phase, axioms, probes=()):
        table, tsig = self.table_for(phase, axioms)
        kb = KB(table, [a for a in axioms if not D.is_property_axiom(D.parse_axiom(a))],
                self.entities, self.distinct)
        kb.table_sig = tsig
        keys = [kb.probe(*p) for p in probes]
        sig = kb.signature()
        if sig not in self.cache:
            self.calls += 1
            self.cache[sig] = run_kb(kb)
        return self.cache[sig], keys

    # ----- queries

    def answers(self, qi):
        return D.query_answers(self.rec, qi)

    def candidates(self, fq, qi):
        ans = self.answers(qi)
        golds = [ans['original'], ans['new']] + list(ans['worlds'].values())
        keys = [self.surf.get(D.norm(g)) for g in golds if g is not None]
        return list(dict.fromkeys([k for k in keys if k] + list(fq.get('candidates') or [])))

    def probes_for(self, fq, qi):
        """[(probe args, role)] for a query."""
        if 'find' in fq:
            subj, ce = D.parse_find(fq['find'])
            return [(('member', subj, subst(ce, c)), c) for c in self.candidates(fq, qi)]
        claim = D.parse_axiom(fq['ask'])
        mode = fq.get('mode', 'holds')
        if mode == 'consistent':
            return []
        pos, neg = claim_probes(claim)
        out = [(pos, 'yes')]
        if mode == 'holds' and neg is not None:
            out.append((neg, 'no'))
        return out

    def given_groups(self):
        """{qi: group key}: a query whose given facts only mention individuals
        nothing else uses joins the shared group 'main' (one KB for all such
        queries); any other query with given facts gets its own KB."""
        if hasattr(self, '_groups'):
            return self._groups
        base = set()
        texts = [a for v in self.bg.values() for a in v] + self.orig_facts + self.edit_facts
        for s in self.worlds.values():
            texts += list(s.get('stores') or []) + list(s.get('adds') or [])
        for a in texts:
            base |= D.names_in(D.parse_axiom(a))['ind']
        inds = {}
        for fq in self.f.get('queries') or []:
            n = set()
            for a in fq.get('given') or []:
                n |= D.names_in(D.parse_axiom(a))['ind']
            inds[fq['q']] = n
        self._groups, self.fresh_given = {}, []
        for fq in self.f.get('queries') or []:
            qi, given = fq['q'], fq.get('given') or []
            others = set().union(*[v for k, v in inds.items() if k != qi]) if len(inds) > 1 else set()
            if not given or fq.get('mode') == 'consistent':
                self._groups[qi] = 'main' if not given else json.dumps(sorted(given))
            elif not (inds[qi] & (base | others)):
                self._groups[qi] = 'main'
                self.fresh_given += given
            else:
                self._groups[qi] = json.dumps(sorted(given))
        return self._groups

    def group_run(self, phase, w, drop, gkey):
        """Run (cached) the KB of one given-group, with the probes of every
        query in it; returns (result, {probe repr: key})."""
        groups = self.given_groups()
        given = self.fresh_given if gkey == 'main' else json.loads(gkey)
        probes = []
        for fq in self.f.get('queries') or []:
            if groups.get(fq['q']) == gkey and 'not_checked' not in fq and 'exception' not in fq:
                probes += [p for p, _ in self.probes_for(fq, fq['q'])]
        res, keys = self.run(phase, self.axioms(phase, w, drop) + list(given), probes)
        return res, dict(zip(map(repr, probes), keys))

    def evaluate(self, fq, qi, phase, w, drop=None):
        """(got, detail): what the KB entails for the query. got is an entity
        key set for finds, 'yes' / 'no' / None for asks, or 'error' /
        'inconsistent'."""
        gkey = self.given_groups().get(qi, 'main')
        mode = fq.get('mode', 'holds')
        res, keymap = self.group_run(phase, w, drop, gkey)
        if res['error']:
            return 'error', res['error']
        if not res['consistent']:
            return 'inconsistent', 'the KB is inconsistent' + (' (with the given facts)' if fq.get('given') else '')
        given = self.fresh_given if gkey == 'main' else json.loads(gkey)
        base = self.axioms(phase, w, drop) + list(given)
        if 'ask' in fq and mode == 'consistent':
            res2, _ = self.run(phase, base + [fq['ask']])
            if res2['error']:
                return 'error', res2['error']
            return ('yes' if res2['consistent'] else 'no'), 'claim consistent' if res2['consistent'] else 'claim inconsistent'
        hits = [role for p, role in self.probes_for(fq, qi) if res['probes'][keymap[repr(p)]]]
        if 'find' in fq:
            return set(hits), 'entailed: ' + (', '.join(sorted(hits)) or 'none')
        claim = D.parse_axiom(fq['ask'])
        if claim[0] == 'sub' and mode == 'holds' and 'yes' not in hits:
            res2, _ = self.run(phase, base + [fq['ask']])
            if res2['consistent'] is False:
                hits.append('no')
        if 'yes' in hits:
            return 'yes', 'claim entailed'
        if 'no' in hits:
            return 'no', 'negation entailed'
        return ('no' if mode == 'follows' else None), ('neither the claim nor its negation is entailed'
                                                       if mode == 'holds' else 'claim not entailed')

    def judge(self, fq, expected, got, others):
        """pass/fail for one evaluation against the record's answer."""
        if got in ('error', 'inconsistent'):
            return 'fail'
        if 'find' in fq:
            exp = None if expected is None else self.surf.get(D.norm(expected))
            if exp is None:
                return 'pass' if not got else 'fail'
            if exp not in got:
                return 'fail'
            if fq.get('exclusive', True) and (got - {exp}) & set(others):
                return 'fail'
            return 'pass'
        mode = fq.get('mode', 'holds')
        # A null answer means "does not know": nothing follows (holds), the
        # claim can no longer be concluded (follows), or ruled out (consistent).
        exp = D.yes_no(expected) if expected is not None else {'holds': None, 'follows': 'no', 'consistent': 'yes'}[mode]
        return 'pass' if exp == got else 'fail'

    def check_query(self, fq, qi, out):
        rec_q = self.rec['queries']['derived'][qi]
        ans = self.answers(qi)
        label = f'{rec_q["derivation"]}, {ans["determinacy"] or "unlabelled"}'
        if 'not_checked' in fq or 'exception' in fq:
            why = fq.get('not_checked') or 'exception: ' + fq['exception']
            out.append({'check': 'not_checked', 'q': qi, 'status': 'not_checked', 'detail': why, 'label': label})
            return
        cands = self.candidates(fq, qi) if 'find' in fq else []
        live = [w for w, s in self.worlds.items() if not s.get('exception')]
        # (b) pre
        if ans['original'] is None:
            out.append({'check': 'pre', 'q': qi, 'status': 'not_checked', 'label': label,
                        'detail': 'no original answer' + (' (insert)' if self.op == 'insert' else '')})
        else:
            per = {}
            for w in live:
                got, det = self.evaluate(fq, qi, 'pre', w)
                per[w] = {'status': self.judge(fq, ans['original'], got, cands), 'expected': ans['original'],
                          'got': fmt(got), 'detail': det}
            out.append(summarize('pre', qi, per, label))
        # (c)/(d) post
        indeterminate = bool(ans['worlds'])
        per, got_by_world = {}, {}
        for w in live:
            expected = ans['worlds'].get(w) if indeterminate else ans['new']
            got, det = self.evaluate(fq, qi, 'post', w)
            got_by_world[w] = got
            per[w] = {'status': self.judge(fq, expected, got, cands), 'expected': expected, 'got': fmt(got),
                      'detail': det}
        out.append(summarize('post_worlds' if indeterminate else 'post_determinate', qi, per, label))
        if indeterminate:
            vals = {fmt(g) for g in got_by_world.values() if g not in ('error', 'inconsistent')}
            ok = len(vals) >= 2
            out.append({'check': 'differ', 'q': qi, 'status': 'pass' if ok else 'fail', 'label': label,
                        'detail': 'entailed answers per world: ' + '; '.join(f'{w}: {fmt(g)}' for w, g in got_by_world.items())})

    # ----- record-level checks

    def check_derived_edit(self, out):
        prem = self.f.get('premises') or []
        if not prem:
            if self.rec.get('derivability') in ('likely', 'very_likely'):
                out.append({'check': 'derived_edit', 'status': 'fail', 'detail': 'no premises encoded'})
            return
        axioms = [a for k in prem for a in self.bg[k]]
        probes, missing = [], []
        for a in self.orig_facts:
            pos, _ = claim_probes(D.parse_axiom(a))
            probes.append((a, pos))
        res, keys = self.run('premises', axioms, [p for _, p in probes])
        if res['error'] or not res['consistent']:
            out.append({'check': 'derived_edit', 'status': 'fail',
                        'detail': res['error'] or 'the premises are inconsistent'})
            return
        missing = [a for (a, _), k in zip(probes, keys) if not res['probes'][k]]
        out.append({'check': 'derived_edit', 'status': 'fail' if missing else 'pass',
                    'detail': ('premises ' + ', '.join(prem) + (' do not entail ' + '; '.join(missing) if missing
                                                                else ' entail the original fact'))})

    def negated_original(self):
        """Delete: the original fact's negation. Post + this is consistent
        exactly when the original no longer follows, so the repair search
        finds the premises a real delete must give up."""
        out = []
        for a in self.orig_facts:
            t = D.parse_axiom(a)
            if t[0] == 'prop':
                out.append(f'not {a}')
            elif t[0] == 'nprop':
                out.append(a.split('not', 1)[1].strip())
            elif t[0] == 'type':
                lhs, rhs = a.split(':', 1)
                out.append(f'{lhs.strip()} : not ({rhs.strip()})')
            elif t[0] == 'sub':
                lhs, rhs = a.split('⊑', 1)
                out.append(f'deletion_witness : ({lhs.strip()}) and not ({rhs.strip()})')
        return out

    def consistent_without(self, w, drop, adds=False):
        axioms = self.axioms('post', w, drop)
        if adds:
            axioms += list((self.worlds.get(w) or {}).get('adds') or [])
        if self.op == 'delete':
            axioms += self.negated_original()
        res, _ = self.run('post', axioms)
        if res['error']:
            raise RuntimeError(res['error'])
        return res['consistent']

    def conflict(self, w, removed, cands):
        """A minimal subset C of cands such that keeping only C (with everything
        not removable) is inconsistent; QuickXplain."""
        fixed_gone = set(removed)
        removable = [k for k in self.bg if k not in self.firm]

        def incons(kept):
            drop = fixed_gone | (set(removable) - set(kept) - fixed_gone)
            return not self.consistent_without(w, drop)

        def qx(B, delta, C):
            if delta and incons(B):
                return []
            if len(C) == 1:
                return list(C)
            k = len(C) // 2
            c1, c2 = C[:k], C[k:]
            d2 = qx(B + c1, c1, c2)
            d1 = qx(B + d2, d2, c1)
            return d1 + d2
        if not incons(cands):
            return None
        if incons([]):
            return []
        return qx([], [], list(cands))

    def check_worlds(self, out):
        live = {w: s for w, s in self.worlds.items() if not s.get('exception')}
        per = {}
        for w, s in self.worlds.items():
            if s.get('exception'):
                per[w] = {'status': 'not_checked', 'detail': 'exception: ' + s['exception']}
                continue
            res, _ = self.group_run('post', w, None, 'main')
            pre, _ = self.group_run('pre', w, None, 'main')
            bad = [f'{p} inconsistent' for p, r in (('pre', pre), ('post', res)) if r['error'] or not r['consistent']]
            if self.op == 'delete' and not bad and self.orig_facts:
                gone = self.common_gu | set(s.get('gives_up') or [])
                if not self.consistent_without(w, gone, adds=True):
                    bad.append('post still entails the deleted fact')
            per[w] = {'status': 'fail' if bad else 'pass',
                      'detail': ', '.join(bad) if bad else 'pre and post consistent'}
        st = 'fail' if any(v['status'] == 'fail' for v in per.values()) else 'pass'
        out.append({'check': 'consistent', 'status': st, 'worlds': per,
                    'detail': '; '.join(f'{w}: {v["detail"]}' for w, v in per.items())})
        # (e) minimal repairs of edit + background, per distinct stores set
        removable = [k for k in self.bg if k not in self.firm]
        seen_stores, repairs, unrepairable, unforced = {}, {}, [], []
        for w, s in live.items():
            key = json.dumps(sorted(s.get('stores') or []))
            if key in seen_stores:
                continue
            seen_stores[key] = w
            if self.consistent_without(w, set()):
                for w2, s2 in live.items():
                    if json.dumps(sorted(s2.get('stores') or [])) == key:
                        gu = self.common_gu | set(s2.get('gives_up') or [])
                        if gu:
                            unforced.append(f'{w2} gives up {sorted(gu)} though the edit contradicts nothing here')
                continue
            found = []
            queue = [frozenset()]
            seen = set()
            while queue:
                path = queue.pop(0)
                if path in seen or any(r <= path for r in found):
                    continue
                seen.add(path)
                if path and self.consistent_without(w, path):
                    found.append(path)
                    continue
                if len(path) >= MAX_REPAIR:
                    continue
                c = self.conflict(w, path, [k for k in removable if k not in path])
                if c is None:
                    continue
                if not c:
                    unrepairable.append(w)
                    continue
                for x in c:
                    queue.append(path | {x})
            found = [r for r in found if not any(o < r for o in found)]
            for r in found:
                repairs.setdefault(r, []).append(key)
        uncovered = []
        for r, keys in repairs.items():
            covered_by = [w for w, s in live.items()
                          if json.dumps(sorted(s.get('stores') or [])) in keys
                          and r <= (self.common_gu | set(s.get('gives_up') or []))]
            if not covered_by:
                uncovered.append(r)
        if not repairs and not unrepairable:
            out.append({'check': 'missing_worlds', 'status': 'pass',
                        'detail': ('the deleted fact follows from no background fact' if self.op == 'delete'
                                   else 'the edit contradicts no background fact') + ('; ' + '; '.join(unforced) if unforced else '')})
            return
        detail = []
        if repairs:
            detail.append('minimal repairs: ' + ' | '.join('{' + ', '.join(sorted(r)) + '}' for r in repairs))
        if unrepairable:
            detail.append('no repair from non-firm background facts (the edit contradicts firm facts) with the stores of '
                          + ', '.join(seen_stores[k] if k in seen_stores else k for k in
                                      {json.dumps(sorted(live[w].get('stores') or [])) for w in unrepairable}))
        extra = []
        for r in uncovered:
            w = seen_stores[repairs[r][0]]
            texts = [a for k in sorted(r) for a in self.bg[k]]
            line = '{' + ', '.join(sorted(r)) + '} (' + '; '.join(texts) + ') is covered by no world'
            # what the determinate queries say in that repair world
            notes = []
            for fq in self.f.get('queries') or []:
                qi = fq['q']
                ans = self.answers(qi)
                if 'not_checked' in fq or 'exception' in fq or ans['worlds']:
                    continue
                got, _ = self.evaluate(fq, qi, 'post', w, drop=self.common_gu | r)
                cands = self.candidates(fq, qi) if 'find' in fq else []
                if self.judge(fq, ans['new'], got, cands) != 'pass':
                    notes.append(f'q{qi} gives {fmt(got)} there, not {ans["new"]!r}')
            if notes:
                line += ': ' + '; '.join(notes)
            extra.append(line)
        detail += extra + unforced
        st = 'fail' if uncovered or unrepairable else 'pass'
        out.append({'check': 'missing_worlds', 'status': st, 'detail': '; '.join(detail),
                    'repairs': [sorted(r) for r in repairs], 'uncovered': [sorted(r) for r in uncovered]})

    def check(self):
        out = []
        t0 = time.time()
        try:
            self.check_derived_edit(out)
            fqs = {q['q']: q for q in self.f.get('queries') or []}
            for qi in range(len(self.rec['queries']['derived'])):
                self.check_query(fqs.get(qi, {'q': qi, 'not_checked': 'not encoded'}), qi, out)
            self.check_worlds(out)
        except Exception as e:  # report, don't crash the run
            out.append({'check': 'error', 'status': 'fail', 'detail': f'{type(e).__name__}: {e}'})
        st = 'fail' if any(c['status'] == 'fail' for c in out) else 'pass'
        return {'status': st, 'calls': self.calls, 'seconds': round(time.time() - t0, 1), 'checks': out}


def claim_probes(claim):
    """(positive probe, negative probe or None) for an ask claim."""
    k = claim[0]
    if k == 'prop':
        v = ('value', ('prop', claim[1]), claim[3])
        return ('member', claim[2], v), ('member', claim[2], ('not', v))
    if k == 'nprop':
        v = ('value', ('prop', claim[1]), claim[3])
        return ('member', claim[2], ('not', v)), ('member', claim[2], v)
    if k == 'type':
        return ('member', claim[1], claim[2]), ('member', claim[1], ('not', claim[2]))
    if k == 'same':
        return ('member', claim[1], ('oneof', [claim[2]])), ('member', claim[1], ('not', ('oneof', [claim[2]])))
    if k == 'different':
        return ('member', claim[1], ('not', ('oneof', [claim[2]]))), ('member', claim[1], ('oneof', [claim[2]]))
    if k == 'sub':
        return ('unsat', ('and', [claim[1], ('not', claim[2])])), None
    raise ValueError(f'cannot ask {claim}')


def subst(t, c):
    if t == '?':
        return c
    if isinstance(t, tuple):
        return tuple(subst(x, c) for x in t)
    if isinstance(t, list):
        return [subst(x, c) for x in t]
    return t


def fmt(got):
    if isinstance(got, set):
        return ', '.join(sorted(got)) or 'none'
    return 'unknown' if got is None else str(got)


def summarize(check, qi, per, label):
    st = 'fail' if any(v['status'] == 'fail' for v in per.values()) else 'pass'
    bad = [f'{w}: expected {v["expected"]!r}, got {v["got"]} ({v["detail"]})' for w, v in per.items()
           if v['status'] == 'fail']
    return {'check': check, 'q': qi, 'status': st, 'label': label, 'worlds': per,
            'detail': '; '.join(bad) if bad else 'ok in ' + ', '.join(per)}


# ---------------------------------------------------------------- driver

def check_one(rid):
    table = RL.load_table()
    try:
        rels = set(table)
        probs = D.check_formal(D.load_formal(rid), D.load_record(rid), rels)
        if probs:
            return rid, {'status': 'fail', 'calls': 0, 'seconds': 0,
                         'checks': [{'check': 'encoding', 'status': 'fail', 'detail': '; '.join(probs)}]}
        return rid, Record(rid, table).check()
    except Exception as e:
        return rid, {'status': 'fail', 'calls': 0, 'seconds': 0,
                     'checks': [{'check': 'error', 'status': 'fail', 'detail': f'{type(e).__name__}: {e}'}]}


CHECKS = ('derived_edit', 'pre', 'post_determinate', 'consistent', 'post_worlds', 'differ', 'missing_worlds',
          'not_checked', 'encoding', 'error')


def summary(records):
    counts = {c: Counter() for c in CHECKS}
    for r in records.values():
        for c in r['checks']:
            counts.setdefault(c['check'], Counter())[c['status']] += 1
    return {c: dict(v) for c, v in counts.items() if v}


def all_record_ids(topic=None):
    paths = sorted((ROOT / 'records').glob(f'{topic or "*"}/*/*.json'))
    return [p.stem for p in paths]


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('ids', nargs='*')
    ap.add_argument('--topic')
    ap.add_argument('--jobs', type=int, default=2)
    args = ap.parse_args(argv)
    if not (OWL_DIR / 'relations.json').exists() or \
            (OWL_DIR / 'relations.json').stat().st_mtime < (ROOT / 'RELATIONS.md').stat().st_mtime:
        print('relations.json is missing or older than RELATIONS.md: run owl/relations.py first')
        return 0
    scope = all_record_ids(args.topic)
    have = {p.stem for p in (OWL_DIR / 'formal').glob('*.json')}
    ids = args.ids or [r for r in scope if r in have]
    t0 = time.time()
    with Pool(max(1, args.jobs)) as pool:
        results = dict(pool.map(check_one, ids))
    old = json.loads(REPORT.read_text()) if REPORT.exists() else {}
    records = old.get('records', {})
    records.update(results)
    every = all_record_ids()
    report = {'generated': time.strftime('%Y-%m-%d %H:%M:%S'),
              'summary': summary(records),
              'records_checked': len(records),
              'pending': [r for r in every if r not in have],
              'records': dict(sorted(records.items()))}
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=1) + '\n')
    n = len(ids)
    print(f'checked {n} records in {time.time() - t0:.0f}s '
          f'({sum(r["calls"] for r in results.values())} HermiT calls)')
    for c, v in summary(results).items():
        print(f'  {c:17} ' + '  '.join(f'{s} {k}' for s, k in sorted(v.items())))
    for rid, r in results.items():
        for c in r['checks']:
            if c['status'] == 'fail':
                q = f' q{c["q"]}' if 'q' in c else ''
                print(f'FAIL {rid} {c["check"]}{q}: {c["detail"][:400]}')
    print(f'{len(report["pending"])} records have no formal file yet; report: owl/reason_report.json')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
