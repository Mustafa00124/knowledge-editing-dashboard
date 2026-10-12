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
    # Task-type derivations (from the finance/technology replacement panel):
    # they test using the edit rather than a property of its relation.
    'binding': None,       # the edit reached through an alias, a bound individual or a new class member
    'application': None,   # the edit used to fill a field, compute a value or run a workflow
    'scope': None,         # the boundary of what follows: the gold is "no" or "cannot be determined"
}

QUERY_COUNTS = {'direct': 1, 'paraphrase': 1, 'cross_lingual': 2, 'derived': 4,
                'unrelated_near': 2, 'unrelated_far': 2}
# RBox edits change a property of a relation, so they carry 7 queries: the
# property itself (direct), two instances on real entities (derived,
# instantiation), those instances in zh and es, and one near (same property,
# another relation) and one far (another property) locality query.
RBOX_QUERY_COUNTS = {'direct': 1, 'cross_lingual': 2, 'derived': 2,
                     'unrelated_near': 1, 'unrelated_far': 1}

RECORD_KEYS = {'id', 'edit_operation', 'topic', 'box', 'relation_semantics',
               'derivability', 'familiarity', 'temporal', 'relation', 'edit', 'queries', 'notes', 'source',
               'checks'}
OPTIONAL_RECORD_KEYS = {'notes', 'source', 'checks'}
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
DERIVED_KEYS = QUERY_KEYS | {'derivation', 'hops', 'bridge', 'via', 'bridge_in_prompt', 'discriminates'}
LOCALITY_KEYS = {'prompt', 'reference'}

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


def load_relation_checks(path=ROOT / 'relation_checks.json'):
    """{relation: {tag: {'prompt', 'answer'}}}: one question per relation
    property a derivation relies on, so the audit can ask whether a model holds
    the property itself (is "located in" transitive?)."""
    path = Path(path)
    return json.loads(path.read_text()) if path.exists() else {}


def facts_to_check(rec):
    """The facts a model must already hold for the record's derivations, in
    order and without repeats: the edit's premises, then every bridge fact a
    derived query does not state in its own prompt. RBox records have none:
    their instance facts are always given in the prompt."""
    if rec.get('box') == 'rbox':
        return []
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
        for k in ('original', 'scope'):
            if k in edit and not is_text(edit[k]):
                err(f'edit.{k} must be a non-empty string')
        # A fixture is a constructed fact the model can't know: its original
        # is loaded into the model before the baseline answers are taken.
        if 'fixture' in edit:
            if not isinstance(edit['fixture'], bool):
                err('edit.fixture must be true or false')
            elif edit['fixture'] and not is_text(edit.get('original')):
                err('edit.fixture needs edit.original, the fact loaded before editing')

    if 'source' in rec and not isinstance(rec['source'], dict):
        err('source must be an object')

    errors.extend(check_familiarity(rec['familiarity'], op, isinstance(edit, dict) and 'object' in edit))

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
        if not is_text(new):
            err('new_answer is required for insert')
    elif op == 'replace':
        if not is_text(new):
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
    # bridge_in_prompt: the bridge facts are stated in the prompt itself, so
    # there is nothing to check against the model before editing.
    # discriminates: false marks a query whose answer is the same before and
    # after the edit (it tests consistency, not the new value).
    for k in ('bridge_in_prompt', 'discriminates'):
        if k in q and not isinstance(q[k], bool):
            err(f'{k} must be true or false')
    if q.get('bridge_in_prompt') and not bridge:
        err('bridge_in_prompt needs the bridge facts listed in bridge')

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
