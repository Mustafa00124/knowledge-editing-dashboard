#!/usr/bin/env python3
"""Validate Sid's Dataset records against the spec in README.md.

One JSON file per edit, at records/<topic>/<edit_operation>/<id>.json, plus
the flat templates in examples/. Records name only their relation; its
properties are looked up in the RELATIONS.md tables (load_relations), the one
place they are defined.

    python datasets/SidsDataset/validate.py            # records/ and examples/
    python datasets/SidsDataset/validate.py FILE ...   # just these files
    python datasets/SidsDataset/validate.py --criteria # CRITERIA.md report (criteria.py)

Standard library only. Exits 1 if any record has an error.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent

EDIT_OPERATIONS = ('insert', 'replace', 'delete')
TOPICS = ('geography', 'people', 'history', 'finance', 'biology', 'physics',
          'literature_arts', 'technology', 'mathematics', 'grammar')
BOXES = ('abox', 'tbox', 'rbox')
# Optional since the determinacy prototype (2026-10-22): the causal vs
# associative split is no longer a tag records must carry.
RELATION_SEMANTICS = ('causal', 'associative')
# Determinacy (README, Determinacy and belief-revision problems; after Hase
# et al. 2024, "Fundamental Problems With Model Editing"), per ABox derived
# query: does every valid route give one answer after the edit (determinate),
# or do the routes split because of how the model stored other facts
# (background_beliefs) or because of which premise of a derived edited fact
# gives way (derived_beliefs)? The last two are indeterminate: such a query
# answers per world (world_answers, each with the chain that leads to it)
# instead of with one new_answer, and the record lists its worlds.
DETERMINACY = ('determinate', 'background_beliefs', 'derived_beliefs')
INDETERMINATE = ('background_beliefs', 'derived_beliefs')
WORLD_KEYS = {'id', 'assumes', 'summary'}
WORLD_ANSWER_KEYS = {'answer', 'chain'}
# The weakest logic a derived query's inference needs (README, Logic), and
# any theory it uses on top: a setting to slice results by, so we can see
# where parameter editing works. Required on every derived query.
LOGIC = ('propositional', 'dl', 'fol')
THEORY = ('arithmetic', 'temporal')
# Boxes whose derived queries carry determinacy. RBox queries ask what follows
# with the facts in the prompt ("Does it follow that ...?"), so they are
# determinate by construction and carry none.
DETERMINACY_BOXES = ('abox', 'tbox')
# Evidence (README, Evidence): why a fact is rated stored or derived, shown
# behind the "?" on the dashboard. One entry per fact, keyed by the fact's
# exact text: the edited (original) fact, every premise, optionally bridges.
# definitional: a premise that states the rule combining the others ("a
# building observes the time zone of the city it stands in"); it is true by
# what the words mean, so it needs a reason but no corpus evidence.
# fictional: an inserted fact about something made up; the evidence shows
# the made-up names are absent from text (near-zero counts, a search).
EVIDENCE_CLAIMS = ('stored', 'derived', 'definitional', 'fictional')
# Insert, on this branch fictional only: which parts of the triple are made
# up (README, Insert). Subject+relation and relation+object are not used.
FICTIONAL = ('subject', 'object', 'subject_object', 'relation', 'all')
FICTIONAL_BY_BOX = {'abox': FICTIONAL, 'tbox': FICTIONAL, 'rbox': ('relation', 'all')}
EVIDENCE_KEYS = {'claim', 'why', 'sources'}
SOURCE_KINDS = {
    'infini-gram': ({'query', 'count'}, {'index', 'note'}),   # a count in a public pretraining corpus
    'wikipedia': ({'url'}, {'quote', 'note'}),               # the fact as stated (or not) on Wikipedia
    'web': ({'url'}, {'quote', 'note'}),                     # any other page
    'search': ({'query'}, {'engine', 'note'}),               # a search tried, and what it returned
}
# How likely a model derives the fact rather than stores it; ordinal, 1 to 5.
DERIVABILITY_SCORE = {'very_unlikely': 1, 'unlikely': 2, 'medium': 3, 'likely': 4, 'very_likely': 5}
DERIVABILITY = tuple(DERIVABILITY_SCORE)
BEHAVIORS = ('answer', 'abstain_or_negate', 'unchanged')
LANGUAGES = ('zh', 'es')

# Derivation -> the relation tag it needs (prefix match for tags with an
# argument). None: licensed by the box or by a bridge fact, not by a tag.
DERIVATIONS = {
    'symmetry': 'symmetric',
    'asymmetry': 'asymmetric',
    'inverse': 'inverse:',
    'transitivity': 'transitive',
    'chain': 'chain:',
    'subproperty': 'subproperty:',
    'functional': 'functional',
    'composition': None,
    'inheritance': None,
    'instantiation': None,
    # Task-type derivations (from the finance/technology replacement panel):
    # they test using the edit rather than a property of its relation.
    'binding': None,       # the edit reached through an alias, a bound individual or a new class member
    'application': None,   # the edit used to fill a field, compute a value or run a workflow
    'scope': None,         # the boundary of what follows: the gold is "no" or "cannot be determined"
    # A premise of a derived edited fact, asked directly: under derived
    # beliefs its answer depends on which premise gives way.
    'premise': None,
}

# In record order: locality before derived. ABox and TBox items carry 10
# queries (one near and one far locality query since 2026-10-22).
QUERY_COUNTS = {'direct': 1, 'paraphrase': 1, 'cross_lingual': 2,
                'unrelated_near': 1, 'unrelated_far': 1, 'derived': 4}
# RBox edits change a property of a relation, so they carry 7 queries: the
# property itself (direct), its first instance in zh and es, one near (same
# property, another relation) and one far (another property) locality query,
# and two instances on real entities (derived, instantiation).
RBOX_QUERY_COUNTS = {'direct': 1, 'cross_lingual': 2, 'unrelated_near': 1,
                     'unrelated_far': 1, 'derived': 2}

RECORD_KEYS = {'id', 'edit_operation', 'topic', 'box', 'relation_semantics',
               'derivability', 'relation', 'edit', 'queries', 'notes', 'source',
               'checks', 'reality', 'fictional', 'worlds', 'evidence'}
OPTIONAL_RECORD_KEYS = {'notes', 'source', 'checks', 'reality', 'fictional', 'relation_semantics', 'worlds',
                        'evidence'}
# Insert only: is the new fact true in the world (real, so a model may already
# hold it and the audit asks), or made up (fictional, so no model can)?
REALITY = ('real', 'fictional')
# A check turns one fact the model must already hold (a premise, or a bridge
# fact not stated in the prompt) into a question with a short answer, so the
# model audit can ask it before editing.
CHECK_KEYS = {'fact', 'prompt', 'answer'}
EDIT_KEYS = {'statement', 'subject', 'object', 'old_object', 'premises', 'axiom', 'original', 'scope', 'fixture'}
# Each edited-knowledge query carries the answer before and after the edit;
# an LLM judge compares a generated answer with them, so there are no alias
# or forbidden lists. Locality queries carry only an optional reference: their
# gold is the model's own pre-edit answer.
QUERY_KEYS = {'prompt', 'original_answer', 'new_answer'}
DERIVED_KEYS = QUERY_KEYS | {'derivation', 'hops', 'bridge', 'via', 'bridge_in_prompt', 'discriminates',
                             'determinacy', 'determinacy_why', 'world_answers', 'chain', 'premise_route',
                             'logic', 'theory'}
LOCALITY_KEYS = {'prompt', 'reference'}

HEADING_TOPICS = {'Literature and arts': 'literature_arts'}


def extra_paths(var):
    """Extra catalogue files named in an environment variable (os.pathsep
    separated), so a topic's writer can add relations without editing the
    shared files at the same time as other writers. Merged in afterwards."""
    import os
    return [Path(p) for p in os.environ.get(var, '').split(os.pathsep) if p]


# Properties a relation shares with its inverse: RELATIONS.md tags them on
# one row of each inverse pair only (Tags rules), and the partner has them
# through inverse:.
SHARED_WITH_INVERSE = ('transitive', 'asymmetric', 'symmetric')


def load_relations(path=ROOT / 'RELATIONS.md', inherit=True):
    """({relation: (tags, causal)}, conflicts) from the starter-relation tables.

    A relation may be listed under several topics, but must carry the same
    tags and semantics everywhere, so a name always means one thing. Each
    disagreement is returned as a message in `conflicts`.

    With `inherit` (the default), a relation also gets the transitive,
    asymmetric and symmetric tags of its inverse partner, since RELATIONS.md
    states each such property on one row of the pair. relations.py reads the
    stated tags only (inherit=False): OWL infers the rest.
    """
    relations, conflicts, topic = {}, [], None
    lines = path.read_text().splitlines()
    if path == ROOT / 'RELATIONS.md':
        for extra in extra_paths('SIDS_EXTRA_RELATIONS'):
            lines += extra.read_text().splitlines()
    for line in lines:
        if line.startswith('### '):
            name = line[4:].strip()
            topic = HEADING_TOPICS.get(name, name.lower())
            continue
        if topic not in TOPICS or not line.startswith('| `'):
            continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        name = cells[0].strip('`')
        entry = (frozenset(re.findall(r'`([^`]+)`', cells[3])), 'causal' in cells[2])
        if name in relations and relations[name] != entry:
            conflicts.append(f'RELATIONS.md: {name!r} under {topic} disagrees with its earlier entry')
        relations.setdefault(name, entry)
    if inherit:
        stated = dict(relations)
        for name, (tags, causal) in stated.items():
            extra = set()
            partners = {t.partition(':')[2] for t in tags if t.startswith('inverse:')}
            partners |= {o for o, (ot, _) in stated.items() if f'inverse:{name}' in ot}
            for o in partners:
                extra |= {t for t in stated.get(o, (frozenset(), False))[0] if t in SHARED_WITH_INVERSE}
            if extra - tags:
                relations[name] = (tags | extra, causal)
    return relations, conflicts


def load_relation_checks(path=ROOT / 'relation_checks.json'):
    """{relation: {tag: {'prompt', 'answer'}}}: one question per relation
    property a derivation relies on, so the audit can ask whether a model holds
    the property itself (is "located in" transitive?)."""
    path = Path(path)
    checks = json.loads(path.read_text()) if path.exists() else {}
    if path == ROOT / 'relation_checks.json':
        for extra in extra_paths('SIDS_EXTRA_RELATION_CHECKS'):
            for name, by_tag in json.loads(extra.read_text()).items():
                checks.setdefault(name, {}).update(by_tag)
    return checks


def facts_to_check(rec):
    """The facts a model must already hold for the record's derivations, in
    order and without repeats: the edit's premises, then every bridge fact a
    derived query does not state in its own prompt. RBox instance facts are
    usually given in the prompt; a role chain's real hop may be left to the
    model (README, RBox items), and is then checked like any bridge."""
    out = list(rec.get('edit', {}).get('premises') or [])
    for q in rec.get('queries', {}).get('derived') or []:
        if not q.get('bridge_in_prompt'):
            out.extend(q.get('bridge') or [])
    return list(dict.fromkeys(out))


def relation_property(rec, q, relations):
    """(relation, tag) a derived query relies on, e.g. ('located_in',
    'transitive') or ('has_capital', 'inverse:capital_of'); None for
    derivations licensed by a bridge, the box or the task type."""
    need = DERIVATIONS.get(q.get('derivation'))
    if not need or rec.get('box') == 'rbox':
        return None
    name = q.get('via', rec.get('relation'))
    tags = relations.get(name, (frozenset(), False))[0]
    tag = next((t for t in sorted(tags) if t == need or (need.endswith(':') and t.startswith(need))), None)
    return (name, tag) if tag else None


def check_checks(rec):
    """Every fact to check has exactly one check, and nothing else does."""
    errors = []
    need = facts_to_check(rec)
    checks = rec.get('checks', [])
    if not isinstance(checks, list):
        return ['checks must be a list']
    seen = set()
    for i, c in enumerate(checks):
        where = f'checks[{i}]'
        if not isinstance(c, dict):
            errors.append(f'{where}: not an object')
            continue
        for k in sorted(set(c) - CHECK_KEYS):
            errors.append(f'{where}: unknown field {k!r}')
        for k in sorted(CHECK_KEYS):
            if not is_text(c.get(k)):
                errors.append(f'{where}: {k} must be a non-empty string')
        if c.get('fact') in seen:
            errors.append(f'{where}: fact {c.get("fact")!r} is checked twice')
        seen.add(c.get('fact'))
        if is_text(c.get('fact')) and c['fact'] not in need:
            errors.append(f'{where}: fact {c["fact"]!r} is not a premise or an unstated bridge fact of this record')
    for fact in need:
        if fact not in seen:
            errors.append(f'checks: no check for {fact!r}')
    return errors


def is_text(v):
    return isinstance(v, str) and v.strip() != ''


def is_text_list(v):
    return isinstance(v, list) and all(is_text(x) for x in v)


def check_record(rec, path, relations):
    errors = []
    err = errors.append

    if not isinstance(rec, dict):
        return ['record is not a JSON object']
    for k in sorted(set(rec) - RECORD_KEYS):
        err(f'unknown field {k!r}')
    for k in sorted(RECORD_KEYS - OPTIONAL_RECORD_KEYS - set(rec)):
        err(f'missing field {k!r}')
    if errors:
        return errors

    op, topic, box = rec['edit_operation'], rec['topic'], rec['box']
    if op not in EDIT_OPERATIONS:
        err(f'edit_operation {op!r} not one of {EDIT_OPERATIONS}')
    if topic not in TOPICS:
        err(f'topic {topic!r} not one of {TOPICS}')
    if box not in BOXES:
        err(f'box {box!r} not one of {BOXES}')
    if errors:
        return errors

    # Identity and location.
    rid = rec['id']
    if not (isinstance(rid, str) and re.fullmatch(rf'{topic}-{op}-\d{{4}}', rid)):
        err(f'id {rid!r} should be "{topic}-{op}-NNNN"')
    if path.name != f'{rid}.json':
        err(f'file name {path.name!r} should be "{rid}.json"')
    if path.parent.parent.parent.name == 'records' and (path.parent.parent.name, path.parent.name) != (topic, op):
        err(f'file should live in records/{topic}/{op}/')

    # Optional tag: the semantics of the record's relation (for RBox, the
    # relation whose property is edited). No longer checked against RELATIONS.md.
    if 'relation_semantics' in rec and rec['relation_semantics'] not in RELATION_SEMANTICS:
        err(f'relation_semantics {rec["relation_semantics"]!r} not one of {RELATION_SEMANTICS}')
    errors.extend(check_determinacy(rec))
    errors.extend(check_evidence(rec))
    # Tag: set for ABox and TBox replace and delete. A new fact can't follow
    # from what the model already holds, and RBox edits are about a relation.
    deriv = rec['derivability']
    if box in ('abox', 'tbox') and op != 'insert':
        if deriv not in DERIVABILITY:
            err(f'derivability {deriv!r} not one of {DERIVABILITY}')
    elif deriv is not None:
        err('derivability must be null for ' + ('insert' if op == 'insert' else 'rbox'))
    # Tag, insert only: replace and delete always edit a real fact.
    reality = rec.get('reality')
    if op == 'insert':
        if reality not in REALITY:
            err(f'reality {reality!r} not one of {REALITY} (required for insert)')
    elif reality is not None:
        err('reality is only for insert: replace and delete edit a real fact')
    # Tag, insert only: what is made up.
    fictional = rec.get('fictional')
    if op == 'insert' and reality == 'fictional':
        if fictional not in FICTIONAL:
            err(f'fictional {fictional!r} not one of {FICTIONAL} (required on a fictional insert)')
        elif fictional not in FICTIONAL_BY_BOX[box]:
            err(f'an RBox insert edits a relation, so fictional is one of {FICTIONAL_BY_BOX[box]}')
    elif fictional is not None:
        err('fictional is only for fictional inserts')

    # The relation must be catalogued.
    relation = rec['relation']
    if relation not in relations:
        err(f'relation {relation!r} is not in RELATIONS.md')

    # The edit.
    edit = rec['edit']
    if not isinstance(edit, dict):
        err('edit must be an object')
    else:
        for k in sorted(set(edit) - EDIT_KEYS):
            err(f'edit: unknown field {k!r}')
        for k in ('statement', 'subject'):
            if not is_text(edit.get(k)):
                err(f'edit.{k} must be a non-empty string')
        # RBox edits are about one relation and may have no object.
        if box != 'rbox' or 'object' in edit:
            if not is_text(edit.get('object')):
                err('edit.object must be a non-empty string' + ('' if box == 'rbox' else ' (only rbox edits may omit it)'))
        if op == 'replace' and 'object' in edit and not is_text(edit.get('old_object')):
            err('edit.old_object is required for replace')
        if op != 'replace' and 'old_object' in edit:
            err(f'edit.old_object is only for replace (for {op}, edit.object is the value)')
        premises = edit.get('premises')
        if 'premises' in edit and not (is_text_list(premises) and premises):
            err('edit.premises must be a non-empty list of strings')
        if DERIVABILITY_SCORE.get(deriv, 0) >= DERIVABILITY_SCORE['likely'] and 'premises' not in edit:
            err(f'edit.premises is required when derivability is {deriv!r}')
        if deriv is None and 'premises' in edit:
            err('edit.premises needs a derivability rating')
        for k in ('original', 'scope'):
            if k in edit and not is_text(edit[k]):
                err(f'edit.{k} must be a non-empty string')
        # An RBox edit states the property only ("'Borders' is symmetric."),
        # not an explanation of it; the questions carry the meaning.
        if box == 'rbox':
            for k in ('statement', 'original'):
                if is_text(edit.get(k)) and ': ' in edit[k]:
                    err(f'edit.{k}: state the property only, without the explanation after the colon')
        # A fixture is a constructed fact the model can't know: its original
        # is loaded into the model before the baseline answers are taken.
        if 'fixture' in edit:
            if not isinstance(edit['fixture'], bool):
                err('edit.fixture must be true or false')
            elif edit['fixture'] and not is_text(edit.get('original')):
                err('edit.fixture needs edit.original, the fact loaded before editing')

    if 'source' in rec and not isinstance(rec['source'], dict):
        err('source must be an object')


    queries = rec['queries']
    if not isinstance(queries, dict):
        return errors + ['queries must be an object']
    counts = RBOX_QUERY_COUNTS if rec.get('box') == 'rbox' else QUERY_COUNTS
    for k in sorted(set(queries) - set(counts)):
        err(f'queries: unknown type {k!r}')
    for qtype, count in counts.items():
        items = queries.get(qtype)
        if count == 1:
            items = [items] if isinstance(items, dict) else items
        if not isinstance(items, list) or len(items) != count:
            err(f'queries.{qtype}: expected {count} quer{"y" if count == 1 else "ies"}')
            continue
        for i, q in enumerate(items):
            where = f'queries.{qtype}' + (f'[{i}]' if count > 1 else '')
            errors.extend(f'{where}: {e}' for e in check_query(q, qtype, rec, relations))

    langs = [q.get('language') for q in queries.get('cross_lingual') or [] if isinstance(q, dict)]
    if sorted(langs) != sorted(LANGUAGES):
        err(f'queries.cross_lingual: needs one query per language {LANGUAGES}, got {langs}')
    if not errors:
        errors.extend(check_checks(rec))
        errors.extend(check_full_scheme(rec, path))
    return errors


def world_ids(rec):
    """The ids of the record's worlds, or None when it has none (every
    derived query determinate, or no determinacy tags)."""
    worlds = rec.get('worlds')
    if not isinstance(worlds, list):
        return None
    return [w.get('id') for w in worlds if isinstance(w, dict)]


def is_indeterminate(q):
    return isinstance(q, dict) and q.get('determinacy') in INDETERMINATE


def check_determinacy(rec):
    """Determinacy is per ABox and TBox derived query and optional, but all
    or none: if one derived query has it, all four do. A record has worlds
    exactly when at least one of them is indeterminate (2 to 4, unique ids,
    each with the facts or choices it assumes). RBox records carry none."""
    errors = []
    err = errors.append
    queries = rec.get('queries')
    derived = queries.get('derived') if isinstance(queries, dict) else None
    derived = [q for q in derived if isinstance(q, dict)] if isinstance(derived, list) else []
    tagged = [q for q in derived if 'determinacy' in q]
    if rec.get('box') not in DETERMINACY_BOXES:
        # RBox queries ask what follows, with the facts in the prompt: one
        # answer whatever the model stored.
        if tagged or 'worlds' in rec:
            err('determinacy and worlds are for ABox and TBox records; RBox records leave them out')
        return errors
    if tagged and len(tagged) != len(derived):
        err(f'determinacy: {len(tagged)} of {len(derived)} derived queries have it; all or none must')
    indeterminate = [q for q in derived if is_indeterminate(q)]
    if not indeterminate:
        if 'worlds' in rec:
            err('worlds are only for records with an indeterminate derived query '
                f'(determinacy one of {INDETERMINATE})')
        return errors
    worlds = rec.get('worlds')
    if not (isinstance(worlds, list) and 2 <= len(worlds) <= 4):
        return errors + ['worlds must be a list of 2 to 4 worlds when a derived query is indeterminate']
    seen = set()
    for i, w in enumerate(worlds):
        where = f'worlds[{i}]'
        if not isinstance(w, dict):
            err(f'{where}: not an object')
            continue
        for k in sorted(set(w) - WORLD_KEYS):
            err(f'{where}: unknown field {k!r}')
        if not is_text(w.get('id')):
            err(f'{where}: id must be a non-empty string')
        elif w['id'] in seen:
            err(f'{where}: duplicate id {w["id"]!r}')
        seen.add(w.get('id'))
        if not (is_text_list(w.get('assumes')) and w['assumes']):
            err(f'{where}: assumes must be a non-empty list of strings')
        if not is_text(w.get('summary')):
            err(f'{where}: summary must be a non-empty string')
    return errors


def evidence_facts(rec):
    """The facts that need evidence: the edited fact as the model holds it
    before the edit (edit.original, else the statement), then every premise."""
    e = rec.get('edit') if isinstance(rec.get('edit'), dict) else {}
    edited = e.get('original') or e.get('statement')
    return [f for f in [edited, *(e.get('premises') or [])] if is_text(f)]


def check_evidence(rec):
    """Evidence is keyed by the fact's exact text. It is required, for the
    edited fact and every premise, on records that use determinacy (the
    sids-determinacy-2 records), and optional elsewhere. The edited fact's
    claim follows its derivability; premises are claimed stored."""
    errors = []
    err = errors.append
    ev = rec.get('evidence')
    queries = rec.get('queries') if isinstance(rec.get('queries'), dict) else {}
    uses_determinacy = any(isinstance(q, dict) and 'determinacy' in q for q in queries.get('derived') or [])
    if ev is None:
        if uses_determinacy:
            err('evidence is required on records with determinacy: one entry for the edited fact and each premise')
        return errors
    if not isinstance(ev, dict):
        return ['evidence must be an object keyed by fact text']
    e = rec.get('edit') if isinstance(rec.get('edit'), dict) else {}
    need = evidence_facts(rec)
    allowed = set(need)
    for q in queries.get('derived') or []:
        if isinstance(q, dict):
            allowed.update(b for b in q.get('bridge') or [] if is_text(b))
    if uses_determinacy:
        for fact in need:
            if fact not in ev:
                err(f'evidence: no entry for {fact!r}')
    edited = need[0] if need else None
    premises = set(e.get('premises') or [])
    for fact, entry in ev.items():
        where = f'evidence[{fact!r}]'
        if fact not in allowed:
            err(f'{where}: not the edited fact, a premise or a bridge fact of this record (copy the text exactly)')
        if not isinstance(entry, dict):
            err(f'{where}: not an object')
            continue
        for k in sorted(set(entry) - EVIDENCE_KEYS):
            err(f'{where}: unknown field {k!r}')
        claim = entry.get('claim')
        if claim not in EVIDENCE_CLAIMS:
            err(f'{where}: claim {claim!r} not one of {EVIDENCE_CLAIMS}')
        if not is_text(entry.get('why')):
            err(f'{where}: why must be a non-empty string')
        if fact == edited and rec.get('edit_operation') == 'insert':
            if rec.get('reality') == 'fictional' and claim != 'fictional':
                err(f'{where}: a fictional insert is claimed fictional')
        elif fact == edited:
            score = DERIVABILITY_SCORE.get(rec.get('derivability'))
            if score is not None and score != DERIVABILITY_SCORE['medium']:
                want = 'derived' if score > DERIVABILITY_SCORE['medium'] else 'stored'
                if claim in EVIDENCE_CLAIMS and claim != want:
                    err(f'{where}: claim {claim!r} disagrees with derivability {rec.get("derivability")!r} ({want})')
        elif fact in premises and claim == 'derived':
            err(f'{where}: a premise is claimed stored; a derived premise needs premises of its own')
        if claim == 'fictional' and fact != edited:
            err(f'{where}: only the inserted fact can be fictional; premises and bridges are real')
        if claim == 'definitional' and fact not in premises:
            err(f'{where}: only a premise can be definitional (the rule combining the others)')
        sources = entry.get('sources', [])
        if not isinstance(sources, list) or (not sources and claim != 'definitional'):
            err(f'{where}: sources must be a non-empty list')
            continue
        for i, src in enumerate(sources):
            sw = f'{where}.sources[{i}]'
            if not isinstance(src, dict):
                err(f'{sw}: not an object')
                continue
            kind = src.get('kind')
            if kind not in SOURCE_KINDS:
                err(f'{sw}: kind {kind!r} not one of {tuple(SOURCE_KINDS)}')
                continue
            required, optional = SOURCE_KINDS[kind]
            for k in sorted(set(src) - required - optional - {'kind'}):
                err(f'{sw}: unknown field {k!r} for {kind}')
            for k in sorted(required):
                if k == 'count':
                    if not (isinstance(src.get('count'), int) and src['count'] >= 0):
                        err(f'{sw}: count must be a non-negative integer')
                elif not is_text(src.get(k)):
                    err(f'{sw}: {k} must be a non-empty string')
            for k in sorted(optional & set(src)):
                if not is_text(src[k]):
                    err(f'{sw}: {k} must be a non-empty string')
    return errors


def derivability_score(rec):
    """1 to 5, or None where derivability doesn't apply."""
    return DERIVABILITY_SCORE.get(rec['derivability'])


def check_query(q, qtype, rec, relations):
    errors = []
    err = errors.append
    if not isinstance(q, dict):
        return ['not an object']
    locality = qtype.startswith('unrelated')
    if locality:
        allowed = LOCALITY_KEYS
    elif qtype == 'derived':
        allowed = DERIVED_KEYS
    else:
        allowed = QUERY_KEYS | ({'language'} if qtype == 'cross_lingual' else set())
    for k in sorted(set(q) - allowed):
        err(f'unknown field {k!r}')
    if not is_text(q.get('prompt')):
        err('prompt must be a non-empty string')
    if locality:
        if q.get('reference') is not None and not is_text(q['reference']):
            err('reference must be a non-empty string or null')
        return errors

    # Which answers each operation needs. Reliability and cross-lingual queries
    # always ask the edited slot itself; a derived query may have no defined
    # answer on the side the edit doesn't produce, so that side is optional.
    op = rec['edit_operation']
    original, new = q.get('original_answer'), q.get('new_answer')
    for name, value in (('original_answer', original), ('new_answer', new)):
        if name not in q:
            err(f'missing field {name!r} (null if it does not apply)')
        elif value is not None and not is_text(value):
            err(f'{name} must be a non-empty string or null')
    core = qtype != 'derived'
    if op == 'insert':
        if original is not None:
            err('original_answer must be null for insert: the model holds nothing before the edit')
        if qtype == 'derived' and is_indeterminate(q):
            if new is not None:
                err('new_answer must be null on an indeterminate derived query (use world_answers)')
        elif not is_text(new):
            err('new_answer is required for insert')
    elif op == 'replace':
        # An indeterminate derived query answers per world instead.
        if qtype == 'derived' and is_indeterminate(q):
            if new is not None:
                err('new_answer must be null on an indeterminate derived query (use world_answers)')
        elif not is_text(new):
            err('new_answer is required for replace')
        if core and not is_text(original):
            err('original_answer is required on reliability and cross-lingual queries under replace')
    elif op == 'delete':
        if new is not None:
            err('new_answer must be null for delete: the model should abstain or negate')
        if core and not is_text(original):
            err('original_answer is required on reliability and cross-lingual queries under delete')
    if qtype == 'cross_lingual' and q.get('language') not in LANGUAGES:
        err(f'language must be one of {LANGUAGES}')
    if qtype == 'derived':
        errors.extend(check_world_answers(q, rec))
        errors.extend(check_derivation(q, rec, relations))
    return errors


def check_world_answers(q, rec):
    """A derived query's determinacy, and its world_answers: an indeterminate
    query has a reason and one answer per world, keyed by exactly the record's
    world ids, with at least two different answers; a determinate one (or
    one without the tag) has none."""
    errors = []
    err = errors.append
    det = q.get('determinacy')
    if 'determinacy' in q and det not in DETERMINACY:
        err(f'determinacy {det!r} not one of {DETERMINACY}')
    if 'determinacy_why' in q and not is_text(q['determinacy_why']):
        err('determinacy_why must be a non-empty string')
    if 'chain' in q and not (is_text_list(q['chain']) and q['chain']):
        err('chain must be a non-empty list of steps (strings)')
    if q.get('logic') not in LOGIC:
        err(f'logic {q.get("logic")!r} not one of {LOGIC} (required: the weakest logic the inference needs)')
    if 'theory' in q:
        if q['theory'] not in THEORY:
            err(f'theory {q["theory"]!r} not one of {THEORY}')
        elif q.get('logic') != 'fol':
            err('theory (arithmetic, temporal) sits on first-order logic: set logic to fol')
    if 'premise_route' in q:
        # The determinate query that reaches the edited fact along its
        # premises: only an inconsistent model gives the old answer there.
        if not isinstance(q['premise_route'], bool):
            err('premise_route must be true or false')
        elif q['premise_route']:
            if det != 'determinate':
                err('premise_route is for determinate queries (the answer is the same in every world)')
            if not rec.get('edit', {}).get('premises'):
                err('premise_route needs edit.premises: the route runs through them')
    if not is_indeterminate(q):
        if 'world_answers' in q:
            err('world_answers are only for indeterminate derived queries '
                f'(determinacy one of {INDETERMINATE})')
        return errors
    if 'chain' in q:
        err('chain is for determinate queries; an indeterminate one gives a chain per world in world_answers')
    if not is_text(q.get('determinacy_why')):
        err('determinacy_why is required on an indeterminate derived query')
    wa = q.get('world_answers')
    if not isinstance(wa, dict):
        return errors + ['world_answers is required on an indeterminate derived query']
    ids = world_ids(rec) or []
    if sorted(wa) != sorted(ids):
        err(f'world_answers keys {sorted(wa)} should equal the world ids {sorted(ids)}')
    answers = []
    for k, v in wa.items():
        where = f'world_answers[{k!r}]'
        if not isinstance(v, dict):
            err(f'{where} must be an object {{answer, chain}}')
            continue
        for key in sorted(set(v) - WORLD_ANSWER_KEYS):
            err(f'{where}: unknown field {key!r}')
        if 'answer' not in v:
            err(f'{where}.answer is required (null only under delete, for "does not know")')
        elif v['answer'] is None:
            # Under delete, a world whose route ran through the removed fact
            # no longer has an answer: the model should say it does not know.
            if rec.get('edit_operation') != 'delete':
                err(f'{where}.answer may be null only under delete (the model abstains)')
            answers.append(None)
        elif not is_text(v['answer']):
            err(f'{where}.answer must be a non-empty string or, under delete, null')
        else:
            answers.append(v['answer'].strip().lower())
        if not (is_text_list(v.get('chain')) and v['chain']):
            err(f'{where}.chain must be a non-empty list of steps (strings)')
    if len(set(answers)) < 2:
        err('world_answers must give at least two different answers across the worlds')
    return errors


def check_full_scheme(rec, path):
    """Records under records/ on this branch follow the whole determinacy
    scheme: every ABox and TBox derived query has a determinacy, and every
    derived query that has one answer (determinate, or RBox) shows its chain.
    The templates in examples/ may be partial."""
    if path.parent.parent.parent.name != 'records':
        return []
    errors = []
    if rec.get('edit_operation') == 'insert' and rec.get('reality') != 'fictional':
        errors.append('inserts on this branch are fictional only (reality: fictional)')
    queries = rec.get('queries') if isinstance(rec.get('queries'), dict) else {}
    for i, q in enumerate(queries.get('derived') or []):
        if not isinstance(q, dict):
            continue
        where = f'queries.derived[{i}]'
        if rec.get('box') in DETERMINACY_BOXES and 'determinacy' not in q:
            err = f'{where}: determinacy is required on ABox and TBox records'
            errors.append(err)
        if not is_indeterminate(q) and 'chain' not in q:
            errors.append(f'{where}: chain is required: the steps from the edit to the answer')
    return errors


def check_derivation(q, rec, relations):
    errors = []
    err = errors.append
    derivation, box = q.get('derivation'), rec['box']
    if derivation not in DERIVATIONS:
        return [f'derivation {derivation!r} not one of {tuple(DERIVATIONS)}']
    bridge = q.get('bridge')
    if not is_text_list(bridge):
        err('bridge must be a list of strings (empty if none)')
        bridge = []
    if q.get('hops') != 1 + len(bridge):
        err(f'hops should be 1 + number of bridge facts = {1 + len(bridge)}')
    # bridge_in_prompt: the bridge facts are stated in the prompt itself, so
    # there is nothing to check against the model before editing.
    # discriminates: false marks a query whose answer is the same before and
    # after the edit (it tests consistency, not the new value).
    for k in ('bridge_in_prompt', 'discriminates'):
        if k in q and not isinstance(q[k], bool):
            err(f'{k} must be true or false')
    if q.get('bridge_in_prompt') and not bridge:
        err('bridge_in_prompt needs the bridge facts listed in bridge')

    # Under delete, a functional query asks whether the removed value still
    # holds, and the model should no longer say.
    if derivation == 'functional' and rec['edit_operation'] == 'insert':
        err('functional derivations need an original value: replace or delete only')
    if derivation in ('transitivity', 'chain', 'composition', 'inheritance') and not bridge:
        err(f'{derivation} needs at least one bridge fact')
    if (derivation == 'instantiation') != (box == 'rbox'):
        err('rbox items derive by instantiation, and only rbox items do')
    if derivation == 'inheritance' and box == 'rbox':
        # TBox: the edited rule applied to a member. ABox: the edited fact
        # makes an individual a member of a class (or changes which), and the
        # question asks a property the class rule gives its members.
        err('inheritance derivations are for abox and tbox items')

    # The tag the derivation relies on, on the edited relation or on `via`.
    need = DERIVATIONS[derivation]
    if need and box != 'rbox':
        name = q.get('via', rec['relation'])
        entry = relations.get(name)
        if entry is None:
            err(f'relation {name!r} (used by {derivation}) is not in RELATIONS.md')
        elif not any(t == need or (need.endswith(':') and t.startswith(need)) for t in entry[0]):
            err(f'{derivation} needs {name!r} to have a {need.rstrip(":")} tag in RELATIONS.md')
    return errors


def default_paths():
    return sorted((ROOT / 'records').rglob('*.json')) + sorted((ROOT / 'examples').glob('*.json'))


def main(argv):
    if '--criteria' in argv:
        # Report only (exit 0): how the records meet CRITERIA.md.
        import criteria
        return criteria.main([a for a in argv if a != '--criteria'])
    relations, conflicts = load_relations()
    for c in conflicts:
        print(c)
    paths = [Path(p).resolve() for p in argv] or default_paths()
    ids, cells, failed = Counter(), Counter(), len(conflicts)
    relation_checks, needed = load_relation_checks(), set()
    for path in paths:
        try:
            rec = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as e:
            print(f'{path}: cannot read: {e}')
            failed += 1
            continue
        errors = check_record(rec, path, relations)
        if isinstance(rec, dict) and isinstance(rec.get('queries'), dict):
            for q in rec['queries'].get('derived') or []:
                if not isinstance(q, dict):
                    continue
                prop = relation_property(rec, q, relations)
                if prop:
                    needed.add(prop)
        if isinstance(rec, dict):
            # The templates in examples/ aren't part of the dataset, so their
            # ids only have to be unique among themselves.
            ids[(path.is_relative_to(ROOT / 'records'), rec.get('id'))] += 1
            if path.is_relative_to(ROOT / 'records'):
                cells[(rec.get('topic'), rec.get('edit_operation'))] += 1
        for e in errors:
            print(f'{path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}: {e}')
        failed += bool(errors)
    for (_, rid), n in ids.items():
        if n > 1:
            print(f'duplicate id {rid!r} in {n} files')
            failed += 1
    for name, tag in sorted(needed):
        entry = relation_checks.get(name, {}).get(tag)
        if not (isinstance(entry, dict) and is_text(entry.get('prompt')) and is_text(entry.get('answer'))):
            print(f'relation_checks.json: no check (prompt and answer) for {name!r} {tag!r}')
            failed += 1
    for name, by_tag in relation_checks.items():
        for tag in by_tag:
            if tag not in relations.get(name, (frozenset(), False))[0]:
                print(f'relation_checks.json: {name!r} has no tag {tag!r} in RELATIONS.md')
                failed += 1
    print(f'{len(paths)} file(s) checked, {failed} with errors.')
    for (topic, op), n in sorted(cells.items()):
        print(f'  {topic}/{op}: {n}')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
