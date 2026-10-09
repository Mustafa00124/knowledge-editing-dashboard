#!/usr/bin/env python3
"""Validate Sid's Dataset records against the spec in README.md.

One JSON file per edit, at records/<topic>/<edit_operation>/<id>.json, plus
the flat templates in examples/. Records name only their relation; its
properties are looked up in the RELATIONS.md tables (load_relations), the one
place they are defined.

    python datasets/SidsDataset/validate.py            # records/ and examples/
    python datasets/SidsDataset/validate.py FILE ...   # just these files

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
          'mathematics', 'grammar', 'literature_arts', 'technology')
BOXES = ('abox', 'tbox', 'rbox')
RELATION_SEMANTICS = ('causal', 'associative')
# Records store the words; analysis uses these ordinal scores (1 to 5).
FAMILIARITY_SCORE = {'very_low': 1, 'low': 2, 'medium': 3, 'high': 4, 'very_high': 5}
FAMILIARITY = tuple(FAMILIARITY_SCORE)
FAMILIARITY_TIERS = ('fact', 'subject', 'object')
TEMPORAL = ('event', 'timeless')
# How likely a model derives the fact rather than stores it; ordinal like familiarity.
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
}

QUERY_COUNTS = {'direct': 1, 'paraphrase': 1, 'cross_lingual': 2, 'derived': 4,
                'unrelated_near': 2, 'unrelated_far': 2}

RECORD_KEYS = {'id', 'edit_operation', 'topic', 'box', 'relation_semantics',
               'derivability', 'familiarity', 'temporal', 'relation', 'edit', 'queries', 'notes'}
EDIT_KEYS = {'statement', 'subject', 'object', 'old_object', 'premises', 'axiom'}
QUERY_KEYS = {'prompt', 'behavior', 'expected', 'aliases', 'forbidden'}
DERIVED_KEYS = QUERY_KEYS | {'derivation', 'hops', 'bridge', 'via'}

HEADING_TOPICS = {'Literature and arts': 'literature_arts'}


def load_relations(path=ROOT / 'RELATIONS.md'):
    """({relation: (tags, causal)}, conflicts) from the starter-relation tables.

    A relation may be listed under several topics, but must carry the same
    tags and semantics everywhere, so a name always means one thing. Each
    disagreement is returned as a message in `conflicts`.
    """
    relations, conflicts, topic = {}, [], None
    for line in path.read_text().splitlines():
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
    return relations, conflicts


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
    for k in sorted(RECORD_KEYS - {'notes'} - set(rec)):
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

    # Knowledge-form layers the box doesn't have are null.
    sem = rec['relation_semantics']
    if box in ('abox', 'tbox'):
        if sem not in RELATION_SEMANTICS:
            err(f'relation_semantics {sem!r} not one of {RELATION_SEMANTICS}')
    elif sem is not None:
        err('relation_semantics must be null for rbox')
    # Tag: set for ABox and TBox replace and delete. A new fact can't follow
    # from what the model already holds, and RBox edits are about a relation.
    deriv = rec['derivability']
    if box in ('abox', 'tbox') and op != 'insert':
        if deriv not in DERIVABILITY:
            err(f'derivability {deriv!r} not one of {DERIVABILITY}')
    elif deriv is not None:
        err('derivability must be null for ' + ('insert' if op == 'insert' else 'rbox'))
    # Tag, ABox facts only: rules and relation properties aren't events.
    temporal = rec['temporal']
    if box == 'abox':
        if temporal not in TEMPORAL:
            err(f'temporal {temporal!r} not one of {TEMPORAL}')
    elif temporal is not None:
        err(f'temporal must be null for {box}')

    # The relation must be catalogued. An RBox edit changes the relation's
    # properties, so its semantics aren't checked against the catalogue.
    relation = rec['relation']
    entry = relations.get(relation)
    if entry is None:
        err(f'relation {relation!r} is not in RELATIONS.md')
    elif box != 'rbox' and sem in RELATION_SEMANTICS and (sem == 'causal') != entry[1]:
        err(f'relation_semantics {sem!r} disagrees with RELATIONS.md for {relation!r}')

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

    errors.extend(check_familiarity(rec['familiarity'], op, isinstance(edit, dict) and 'object' in edit))

    queries = rec['queries']
    if not isinstance(queries, dict):
        return errors + ['queries must be an object']
    for k in sorted(set(queries) - set(QUERY_COUNTS)):
        err(f'queries: unknown type {k!r}')
    for qtype, count in QUERY_COUNTS.items():
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
    return errors


def check_familiarity(fam, op, has_object):
    """Three tiers: fact (null for insert), subject (always), object (iff the edit has one)."""
    if not isinstance(fam, dict) or set(fam) != set(FAMILIARITY_TIERS):
        return [f'familiarity must be an object with exactly {FAMILIARITY_TIERS}']
    errors = []
    applies = {'fact': op != 'insert', 'subject': True, 'object': has_object}
    for tier in FAMILIARITY_TIERS:
        value = fam[tier]
        if applies[tier] and value not in FAMILIARITY:
            errors.append(f'familiarity.{tier} {value!r} not one of {FAMILIARITY}')
        elif not applies[tier] and value is not None:
            why = 'insert has no original fact' if tier == 'fact' else 'the edit has no object'
            errors.append(f'familiarity.{tier} must be null: {why}')
    return errors


def derivability_score(rec):
    """1 to 5, or None where derivability doesn't apply."""
    return DERIVABILITY_SCORE.get(rec['derivability'])


def familiarity_scores(rec):
    """{'fact': 5, 'subject': 5, 'object': 4} for a record; None where a tier doesn't apply."""
    return {tier: FAMILIARITY_SCORE.get(rec['familiarity'][tier]) for tier in FAMILIARITY_TIERS}


def check_query(q, qtype, rec, relations):
    errors = []
    err = errors.append
    if not isinstance(q, dict):
        return ['not an object']
    allowed = DERIVED_KEYS if qtype == 'derived' else QUERY_KEYS | ({'language'} if qtype == 'cross_lingual' else set())
    for k in sorted(set(q) - allowed):
        err(f'unknown field {k!r}')
    if not is_text(q.get('prompt')):
        err('prompt must be a non-empty string')
    for k in ('aliases', 'forbidden'):
        if k in q and not is_text_list(q[k]):
            err(f'{k} must be a list of strings')

    op = rec['edit_operation']
    behavior = q.get('behavior')
    if qtype.startswith('unrelated'):
        want = 'unchanged'
    else:
        want = 'abstain_or_negate' if op == 'delete' else 'answer'
    if behavior != want:
        err(f'behavior should be {want!r} for {qtype} under {op}, got {behavior!r}')
    if behavior == 'abstain_or_negate':
        if q.get('expected') is not None:
            err('expected must be null for abstain_or_negate')
        if not q.get('forbidden'):
            err('forbidden must list the old answer for abstain_or_negate')
    elif not is_text(q.get('expected')):
        err('expected must be a non-empty string')
    if op == 'replace' and qtype in ('direct', 'paraphrase', 'cross_lingual') and not q.get('forbidden'):
        err('forbidden must list the old answer under replace')
    if qtype == 'cross_lingual' and q.get('language') not in LANGUAGES:
        err(f'language must be one of {LANGUAGES}')
    if qtype == 'derived':
        errors.extend(check_derivation(q, rec, relations))
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

    if derivation == 'functional' and rec['edit_operation'] != 'replace':
        err('functional derivations only make sense for replace')
    if derivation in ('transitivity', 'chain', 'composition', 'inheritance') and not bridge:
        err(f'{derivation} needs at least one bridge fact')
    if (derivation == 'instantiation') != (box == 'rbox'):
        err('rbox items derive by instantiation, and only rbox items do')
    if derivation == 'inheritance' and box != 'tbox':
        err('inheritance derivations are for tbox items')

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
    relations, conflicts = load_relations()
    for c in conflicts:
        print(c)
    paths = [Path(p).resolve() for p in argv] or default_paths()
    ids, cells, failed = Counter(), Counter(), len(conflicts)
    for path in paths:
        try:
            rec = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as e:
            print(f'{path}: cannot read: {e}')
            failed += 1
            continue
        errors = check_record(rec, path, relations)
        if isinstance(rec, dict):
            ids[rec.get('id')] += 1
            if path.is_relative_to(ROOT / 'records'):
                cells[(rec.get('topic'), rec.get('edit_operation'))] += 1
        for e in errors:
            print(f'{path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}: {e}')
        failed += bool(errors)
    for rid, n in ids.items():
        if n > 1:
            print(f'duplicate id {rid!r} in {n} files')
            failed += 1
    print(f'{len(paths)} file(s) checked, {failed} with errors.')
    for (topic, op), n in sorted(cells.items()):
        print(f'  {topic}/{op}: {n}')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
