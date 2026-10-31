#!/usr/bin/env python3
"""Compile RELATIONS.md into OWL 2: owl/relations.owl, owl/relations.json and
owl/relations_report.md.

    venvs/easyedit_venv/bin/python datasets/SidsDataset/owl/relations.py

Every relation becomes an object property with its tags:

    symmetric, asymmetric, transitive, functional   property characteristics
    inverse:S          R ≡ S⁻              (owl:inverseOf)
    subproperty:S      R ⊑ S
    chain:S->T         R ∘ S ⊑ T           (property chain)
    cardinality:many, causal               annotations only

OWL 2 DL only allows functional, inverse functional and asymmetric axioms on
*simple* properties (no transitivity or chain below them), and needs the
property chains to be *regular*. HermiT refuses an ontology that breaks
either. Such an axiom is kept as a SWRL rule over named individuals instead
(a fallback) and listed in relations_report.md, since it is often also a tag
problem in RELATIONS.md (a functional relation that chains into itself).

HermiT also does not fire SWRL rules on facts it derives through
transitivity or a property chain, so every transitive property and chain
gets a mirror rule too (R(x,y), R(y,z) -> R(x,z)). The OWL axiom catches what
involves unnamed individuals; the rule keeps the named closure complete for
the other rules.

`build(onto, table, names)` is shared with reason.py, which builds one small
ontology per record and world from relations.json with only the properties
it needs (after applying an RBox edit to the table).
"""
import json
import re
import sys
import types
from collections import defaultdict
from pathlib import Path

OWL_DIR = Path(__file__).resolve().parent
DATASET = OWL_DIR.parent
sys.path.insert(0, str(DATASET))

REL_IRI = 'http://sids.dataset/rel#'
FLAGS = ('symmetric', 'asymmetric', 'transitive', 'functional', 'inverse_functional', 'reflexive', 'irreflexive')
# Axioms that OWL 2 DL allows on simple properties only.
SIMPLE_ONLY = ('functional', 'inverse_functional', 'asymmetric', 'irreflexive')


def empty_rel():
    return {f: False for f in FLAGS} | {'inverse': [], 'sub': [], 'chains': [], 'disjoint': [],
                                        'many': False, 'causal': False, 'catalogued': True, 'reads': ''}


def parse_tags(tags):
    r = empty_rel()
    for t in tags:
        kind, _, arg = t.partition(':')
        if kind in FLAGS:
            r[kind] = True
        elif kind == 'inverse':
            r['inverse'].append(arg)
        elif kind == 'subproperty':
            r['sub'].append(arg)
        elif kind == 'chain':
            s, _, tgt = arg.partition('->')
            r['chains'].append([s, tgt])
        elif kind == 'disjoint':
            r['disjoint'].append(arg)
        elif kind == 'cardinality':
            r['many'] = arg == 'many'
        elif kind == 'causal':
            r['causal'] = True
    return r


def load_table_from_markdown():
    """{name: rel} from RELATIONS.md (via validate.load_relations), with every
    relation that is only named inside another's tag added as uncatalogued."""
    from validate import load_relations
    relations, _ = load_relations()
    table = {name: parse_tags(tags) for name, (tags, _) in sorted(relations.items())}
    reads = {}
    for line in (DATASET / 'RELATIONS.md').read_text().splitlines():
        if line.startswith('| `'):
            cells = [c.strip() for c in line.strip('|').split('|')]
            reads.setdefault(cells[0].strip('`'), cells[1])
    for name, r in table.items():
        r['reads'] = reads.get(name, '')
    for name in list(table):
        r = table[name]
        refs = r['inverse'] + r['sub'] + r['disjoint'] + [x for c in r['chains'] for x in c]
        for other in refs:
            if other not in table:
                table[other] = empty_rel() | {'catalogued': False}
    return table


def load_table(path=OWL_DIR / 'relations.json'):
    return json.loads(Path(path).read_text())['relations']


# ---------------------------------------------------------------- analysis

def inverse_pairs(table):
    pairs = set()
    for name, r in table.items():
        for s in r['inverse']:
            pairs.add((name, s))
            pairs.add((s, name))
    return pairs


def non_simple(table):
    """Names of non-simple properties: transitive, the target of a chain, or
    with a non-simple subproperty or inverse."""
    ns = {n for n, r in table.items() if r['transitive']}
    ns |= {c[1] for r in table.values() for c in r['chains']}
    inv = inverse_pairs(table)
    changed = True
    while changed:
        changed = False
        for a, b in inv:
            if a in ns and b not in ns:
                ns.add(b)
                changed = True
        for name, r in table.items():
            if name in ns:
                for s in r['sub']:
                    if s not in ns:
                        ns.add(s)
                        changed = True
    return ns


def irregular_chains(table):
    """Chains that break the OWL 2 regularity condition, by a strict order
    on properties (a property and its inverse share a node; a subproperty
    is <= its parent). A strict edge inside a cycle is irregular."""
    node = {n: n for n in table}

    def find(x):
        while node[x] != x:
            node[x] = node[node[x]]
            x = node[x]
        return x
    for a, b in inverse_pairs(table):
        node[find(a)] = find(b)
    edges = []   # (a, b, strict, chain)
    for name, r in table.items():
        for s in r['sub']:
            edges.append((name, s, False, None))
        for s, t in r['chains']:
            chain = (name, s, t)
            if name == s == t:
                continue
            if name != t:
                edges.append((name, t, True, chain))
            if s != t:
                edges.append((s, t, True, chain))
    graph = defaultdict(set)
    for a, b, _, _ in edges:
        graph[find(a)].add(find(b))

    def reaches(src, dst):
        seen, stack = set(), [src]
        while stack:
            x = stack.pop()
            if x == dst:
                return True
            if x not in seen:
                seen.add(x)
                stack.extend(graph[x])
        return False
    bad = set()
    for a, b, strict, chain in edges:
        if strict and (find(a) == find(b) or reaches(find(b), find(a))):
            bad.add(tuple(chain))
    return bad


def analyse(table):
    """Decide per axiom: native OWL, or SWRL fallback (with the reason)."""
    ns = non_simple(table)
    irregular = irregular_chains(table)
    fallback = []
    for name, r in table.items():
        for f in SIMPLE_ONLY:
            if r[f] and name in ns:
                fallback.append({'relation': name, 'axiom': f, 'reason': 'non-simple property ' + why_non_simple(table, name, ns)})
        for s, t in r['chains']:
            if (name, s, t) in irregular:
                fallback.append({'relation': name, 'axiom': f'chain:{s}->{t}', 'reason': 'irregular role chain'})
    return {'non_simple': sorted(ns), 'fallback': fallback}


def why_non_simple(table, name, ns):
    r = table[name]
    if r['transitive']:
        return '(transitive)'
    srcs = [f'{n} ∘ {c[0]} ⊑ {name}' for n, x in table.items() for c in x['chains'] if c[1] == name]
    if srcs:
        return '(target of the chain ' + '; '.join(srcs) + ')'
    subs = [n for n, x in table.items() if name in x['sub'] and n in ns]
    if subs:
        return '(has non-simple subproperty ' + ', '.join(subs) + ')'
    invs = [s for s in r['inverse'] if s in ns]
    return '(inverse of non-simple ' + ', '.join(invs) + ')' if invs else ''


def semantic_problems(table):
    """Tag combinations that are not an OWL restriction but look wrong."""
    out = []
    for name, r in table.items():
        if r['symmetric'] and r['asymmetric']:
            out.append((name, 'both symmetric and asymmetric: no pair can satisfy both, so every fact is inconsistent'))
        if r['functional'] and any(t == name for _, t in r['chains']):
            out.append((name, 'functional but chains into itself (README: a relation is not tagged functional if it '
                              'chains into itself): a R b and b located_in c gives a R c, so b = c'))
        if r['functional'] and r['transitive']:
            out.append((name, 'functional and transitive: a R b, b R c gives a R c, so b = c'))
        for s in r['inverse']:
            o = table.get(s)
            if o is None:
                continue
            if name not in o['inverse'] and o['catalogued']:
                out.append((name, f'inverse:{s}, but {s} does not list inverse:{name}'))
            for f in ('transitive', 'symmetric', 'asymmetric'):
                if r[f] and not o[f] and o['catalogued']:
                    out.append((name, f'{f}, but its inverse {s} is not tagged {f} (the inverse of a relation tagged {f} is {f} too)'))
        for s in r['sub']:
            o = table.get(s)
            if o and r['symmetric'] and o['asymmetric']:
                out.append((name, f'symmetric subproperty of asymmetric {s}: every fact would be inconsistent'))
    owners = defaultdict(list)
    for name, r in table.items():
        for s in r['inverse']:
            owners[s].append(name)
    for s, names in sorted(owners.items()):
        if len(names) > 1:
            out.append((s, 'is the inverse of ' + ', '.join(names) + ': OWL then makes those relations equivalent '
                           '(one name, several meanings)'))
    return out


# ---------------------------------------------------------------- building

def closure(table, names):
    """The properties an ontology over `names` needs: names plus everything
    above them (superproperties, inverses, chain targets whose links are all
    present)."""
    need = set(n for n in names if n in table)
    changed = True
    while changed:
        changed = False
        for n in list(need):
            r = table[n]
            for x in r['sub'] + r['inverse']:
                if x not in need:
                    need.add(x)
                    changed = True
            for s, t in r['chains']:
                if s in need and t not in need:
                    need.add(t)
                    changed = True
        for n, r in table.items():   # inverses pointing at us
            if n not in need and any(i in need for i in r['inverse']):
                need.add(n)
                changed = True
    return need


def make_rule(onto, body, head):
    """A SWRL rule from atoms (predicate, args): predicate an owlready2
    class or object property, or 'same'; args '?x' variables or entities.
    Built directly so property names never collide with SWRL built-ins
    ('contains')."""
    import owlready2 as o
    rule = o.Imp(namespace=onto)

    def atom(pred, args):
        if pred == 'same':
            a = o.SameIndividualAtom(namespace=onto)
        elif pred == 'different':
            a = o.DifferentIndividualsAtom(namespace=onto)
        elif isinstance(pred, o.ThingClass):
            a = o.ClassAtom(namespace=onto)
            a.class_predicate = pred
        else:
            a = o.IndividualPropertyAtom(namespace=onto)
            a.property_predicate = pred
        a.arguments = [rule.get_variable(x) if isinstance(x, str) else x for x in args]
        return a
    rule.body = [atom(p, a) for p, a in body]
    rule.head = [atom(p, a) for p, a in head]
    return rule


def build(onto, table, names=None, mirror=True):
    """Declare the properties for `names` (all when None) and their axioms in
    `onto`. Returns ({name: property}, analysis)."""
    import owlready2 as o
    names = set(table) if names is None else closure(table, names)
    sub = {n: json.loads(json.dumps(table[n])) for n in names}
    # Tags can point outside `names` only through relations not needed here.
    for r in sub.values():
        r['chains'] = [c for c in r['chains'] if c[0] in names and c[1] in names]
    info = analyse(sub)
    fb = {(x['relation'], x['axiom']) for x in info['fallback']}
    ns = onto.get_namespace(REL_IRI)
    props = {}
    with onto:
        for n in sorted(names):
            props[n] = types.new_class(n, (o.ObjectProperty,), exec_body=lambda d: d.update(namespace=ns))
        for n in sorted(names):
            r, p = sub[n], props[n]
            if r['reads']:
                p.comment = [r['reads']]
            for flag, cls in (('symmetric', o.SymmetricProperty), ('transitive', o.TransitiveProperty),
                              ('reflexive', o.ReflexiveProperty), ('asymmetric', o.AsymmetricProperty),
                              ('functional', o.FunctionalProperty),
                              ('inverse_functional', o.InverseFunctionalProperty),
                              ('irreflexive', o.IrreflexiveProperty)):
                if r[flag] and (n, flag) not in fb:
                    p.is_a.append(cls)
            for s in r['inverse']:
                if s in props:   # raw triples: owlready2's inverse_property holds only one
                    onto._add_obj_triple_spo(p.storid, o.owl_inverse_property, props[s].storid)
            for s in r['sub']:
                if s in props:
                    p.is_a.append(props[s])
            for s, t in r['chains']:
                if (n, f'chain:{s}->{t}') not in fb:
                    props[t].property_chain.append(o.PropertyChain([p, props[s]]))
            for s in r['disjoint']:
                if s in props:
                    o.AllDisjoint([p, props[s]])
        # Fallback rules for axioms OWL 2 DL can't take, and mirror rules for
        # what HermiT's rules don't see (transitivity and chains).
        for n in sorted(names):
            r, p = sub[n], props[n]
            if (n, 'functional') in fb:
                make_rule(onto, [(p, ('?x', '?y')), (p, ('?x', '?z'))], [('same', ('?y', '?z'))])
            if (n, 'inverse_functional') in fb:
                make_rule(onto, [(p, ('?y', '?x')), (p, ('?z', '?x'))], [('same', ('?y', '?z'))])
            if (n, 'asymmetric') in fb:
                make_rule(onto, [(p, ('?x', '?y')), (p, ('?y', '?x'))], [(o.Nothing, ('?x',))])
            if mirror and r['transitive']:
                make_rule(onto, [(p, ('?x', '?y')), (p, ('?y', '?z'))], [(p, ('?x', '?z'))])
            for s, t in r['chains']:
                if mirror or (n, f'chain:{s}->{t}') in fb:
                    make_rule(onto, [(p, ('?x', '?y')), (props[s], ('?y', '?z'))], [(props[t], ('?x', '?z'))])
    return props, info


# ---------------------------------------------------------------- main

def write_report(table, info, semantic, hermit):
    lines = ['# relations.owl report', '',
             'Generated by `owl/relations.py` from RELATIONS.md. Lists what OWL 2 DL could not take as an axiom',
             '(kept as a SWRL rule over named individuals instead) and tag combinations that look wrong.', '',
             f'- relations in RELATIONS.md: {sum(r["catalogued"] for r in table.values())}',
             f'- named only inside another relation\'s tag (declared, no tags of their own): '
             f'{sum(not r["catalogued"] for r in table.values())}',
             f'- non-simple properties: {len(info["non_simple"])}',
             f'- axioms kept as rules: {len(info["fallback"])}',
             f'- HermiT on relations.owl: {hermit}', '',
             '## Axioms OWL 2 DL forbids (kept as SWRL rules)', '',
             'OWL 2 DL allows functional, inverse functional and asymmetric only on simple properties (no',
             'transitivity or role chain below them). Most of these are fine as a tag and only need the rule;',
             'the ones also listed under "Tag problems" are probably wrong in RELATIONS.md.', '',
             '| Relation | Axiom | Why |', '| --- | --- | --- |']
    lines += [f'| `{x["relation"]}` | {x["axiom"]} | {x["reason"]} |' for x in info['fallback']]
    lines += ['', '## Tag problems', '',
              'Combinations that are legal OWL but contradict themselves, the README, or the inverse relation\'s tags.', '',
              '| Relation | Problem |', '| --- | --- |']
    lines += [f'| `{n}` | {p} |' for n, p in semantic]
    unc = sorted(n for n, r in table.items() if not r['catalogued'])
    lines += ['', '## Named only inside a tag', '',
              'Declared as properties with no tags of their own; add them to RELATIONS.md if a record uses them.', '',
              ', '.join(f'`{n}`' for n in unc), '']
    (OWL_DIR / 'relations_report.md').write_text('\n'.join(lines))


def main():
    import owlready2 as o
    table = load_table_from_markdown()
    world = o.World()
    onto = world.get_ontology('http://sids.dataset/relations.owl')
    _, info = build(onto, json.loads(json.dumps(table)))
    onto.save(str(OWL_DIR / 'relations.owl'), format='rdfxml')
    try:
        with onto:
            o.sync_reasoner_hermit(world, debug=0)
        hermit = 'loads and is consistent'
    except o.OwlReadyInconsistentOntologyError:
        hermit = 'INCONSISTENT'
    except o.OwlReadyJavaError as e:
        msg = [l for l in str(e).splitlines() if 'Exception' in l]
        hermit = 'REFUSED: ' + (msg[0] if msg else str(e)[:300])
    semantic = semantic_problems(table)
    (OWL_DIR / 'relations.json').write_text(json.dumps(
        {'source': 'RELATIONS.md', 'relations': table, 'non_simple': info['non_simple'],
         'fallback': info['fallback']}, ensure_ascii=False, indent=1) + '\n')
    write_report(table, info, semantic, hermit)
    print(f'{len(table)} properties, {len(info["fallback"])} axioms kept as rules, '
          f'{len(semantic)} tag problems; HermiT: {hermit}')
    print('wrote owl/relations.owl, owl/relations.json, owl/relations_report.md')
    return 0


if __name__ == '__main__':
    sys.exit(main())
