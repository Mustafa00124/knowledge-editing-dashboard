#!/usr/bin/env python3
"""Validate Sid's Dataset records against the spec in README.md.

One JSON file per edit, at records/<topic>/<edit_operation>/<id>.json, plus
the flat templates in examples/. Relation tags are checked against the tables
in RELATIONS.md, which stays the source of truth for them.

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
          'mathematics', 'grammar', 'literature_arts', 'puzzle')
BOXES = ('abox', 'tbox', 'rbox')
RELATION_SEMANTICS = ('causal', 'associative')
TEMPORALITY = ('event', 'timeless')
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
               'temporality', 'relation', 'relation_tags', 'edit', 'queries', 'notes'}
EDIT_KEYS = {'statement', 'subject', 'object', 'old_object', 'axiom'}
QUERY_KEYS = {'prompt', 'behavior', 'expected', 'aliases', 'forbidden'}
DERIVED_KEYS = QUERY_KEYS | {'derivation', 'hops', 'bridge', 'via'}

HEADING_TOPICS = {'Literature and arts': 'literature_arts'}


def load_relations(path=ROOT / 'RELATIONS.md'):
    """{relation: {topic: (tags, causal)}} from the starter-relation tables."""
    relations, topic = {}, None
    for line in path.read_text().splitlines():
        if line.startswith('### '):
            name = line[4:].strip()
            topic = HEADING_TOPICS.get(name, name.lower())
            continue
        if topic not in TOPICS or not line.startswith('| `'):
            continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        name = cells[0].strip('`')
        tags = frozenset(re.findall(r'`([^`]+)`', cells[3]))
        relations.setdefault(name, {})[topic] = (tags, 'causal' in cells[2])
    return relations


def catalogue_entry(relations, name, topic):
    entries = relations.get(name)
    if not entries:
        return None
    return entries.get(topic) or next(iter(entries.values()))


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
    sem, temp = rec['relation_semantics'], rec['temporality']
    if box in ('abox', 'tbox'):
        if sem not in RELATION_SEMANTICS:
            err(f'relation_semantics {sem!r} not one of {RELATION_SEMANTICS}')
    elif sem is not None:
        err('relation_semantics must be null for rbox')
    if box == 'abox':
        if temp not in TEMPORALITY:
            err(f'temporality {temp!r} not one of {TEMPORALITY}')
    elif temp is not None:
        err(f'temporality must be null for {box}')
    if topic == 'puzzle' and op != 'insert':
        err('puzzle items are insert only')

    # Relation and its tags, as catalogued in RELATIONS.md. An RBox edit
    # changes the relation's properties, so only its existence is checked.
    relation, tags = rec['relation'], rec['relation_tags']
    entry = catalogue_entry(relations, relation, topic)
    if not is_text_list(tags):
        err('relation_tags must be a list of strings')
        tags = []
    if entry is None:
        err(f'relation {relation!r} is not in RELATIONS.md')
    elif box != 'rbox':
        cat_tags, cat_causal = entry
        if set(tags) != cat_tags:
            err(f'relation_tags {sorted(tags)} differ from RELATIONS.md {sorted(cat_tags)}')
        if sem in RELATION_SEMANTICS and (sem == 'causal') != cat_causal:
            err(f'relation_semantics {sem!r} disagrees with RELATIONS.md for {relation!r}')

    # The edit.
    edit = rec['edit']
    if not isinstance(edit, dict):
        err('edit must be an object')
    else:
        for k in sorted(set(edit) - EDIT_KEYS):
            err(f'edit: unknown field {k!r}')
        for k in ('statement', 'subject', 'object'):
            if not is_text(edit.get(k)):
                err(f'edit.{k} must be a non-empty string')
        if op == 'replace' and not is_text(edit.get('old_object')):
            err('edit.old_object is required for replace')
        if op != 'replace' and 'old_object' in edit:
            err(f'edit.old_object is only for replace (for {op}, edit.object is the value)')

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
        entry = catalogue_entry(relations, name, rec['topic'])
        if entry is None:
            err(f'relation {name!r} (used by {derivation}) is not in RELATIONS.md')
        elif not any(t == need or (need.endswith(':') and t.startswith(need)) for t in entry[0]):
            err(f'{derivation} needs {name!r} to have a {need.rstrip(":")} tag in RELATIONS.md')
    return errors


def default_paths():
    return sorted((ROOT / 'records').rglob('*.json')) + sorted((ROOT / 'examples').glob('*.json'))


def main(argv):
    relations = load_relations()
    paths = [Path(p).resolve() for p in argv] or default_paths()
    ids, cells, failed = Counter(), Counter(), 0
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
