#!/usr/bin/env python3
"""Validate Sid's Dataset records against the spec in README.md.

One JSON file per edit: the main split at records/<topic>/<edit_operation>/
<id>.json, the dev split at dev/<topic>/<edit_operation>/<id>.json, plus one
template per record type in examples/. Records name only their relation; its
properties are looked up in the RELATIONS.md tables (load_relations), the one
place they are defined.

    python datasets/SidsDataset/validate.py            # records/ and examples/
    python datasets/SidsDataset/validate.py dev        # dev/ (and the main/dev overlap check)
    python datasets/SidsDataset/validate.py all        # both splits and examples/
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
# The weakest logic a related or derived query's inference needs (README,
# Logic), and any theory it uses on top: a setting to slice results by, so we
# can see where parameter editing works. Required on every related and derived
# query; propositional logic is the propositional query type's own.
LOGIC = ('dl', 'fol')
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
EVIDENCE_CLAIMS = ('stored', 'derived', 'definitional', 'fictional', 'false')  # false: a deliberately false side fact
# Insert is fictional only: which parts of the triple are made up (README,
# Insert). Subject+relation and relation+object are not used.
FICTIONAL = ('subject', 'object', 'subject_object', 'relation', 'all')
FICTIONAL_BY_BOX = {'abox': FICTIONAL, 'tbox': FICTIONAL, 'rbox': ('relation', 'all')}
EVIDENCE_KEYS = {'claim', 'why', 'sources'}
SOURCE_KINDS = {
    'infini-gram': ({'query', 'count'}, {'index', 'note'}),   # a count in a public pretraining corpus
    'wikipedia': ({'url'}, {'quote', 'note'}),               # the fact as stated (or not) on Wikipedia
    'web': ({'url'}, {'quote', 'note'}),                     # any other page
    'search': ({'query'}, {'engine', 'note'}),               # a search tried, and what it returned
}
# Stored or worked out (README, Derivability): only the two ends are used,
# for the edited fact and for the `fact` of every related and derived query.
DERIVABILITY_SCORE = {'very_unlikely': 1, 'very_likely': 5}
DERIVABILITY = tuple(DERIVABILITY_SCORE)
LANGUAGES = ('zh', 'es')

# Derivation (a relation property, or composition / premise / cardinality /
# instantiation) -> the relation tag it needs (prefix match for tags with an
# argument). None: licensed by a bridge fact or the box, not by a tag.
# Not used: scope, asymmetry, reflexivity. Composition, binding and
# application are task types (TASKS), not derivations.
DERIVATIONS = {
    'inverse': 'inverse:',
    'symmetry': 'symmetric',
    'functional': 'functional',
    'subproperty': 'subproperty:',
    'transitivity': 'transitive',
    'chain': 'chain:',
    'inheritance': None,
    'none': None,            # no property: a composition or binding task carries the edit
    'premise': None,         # a premise of a derived edit (the indeterminate query only)
    'cardinality': 'cardinality:many',  # contraction: another value of a many-valued relation keeps its answer
    'instantiation': None,   # RBox: the axiom applied to instances in the prompt
}
# What the question asks the model to do with the conclusion (README, Relation
# properties and task types); any property can carry either.
TASKS = ('answer', 'composition', 'binding', 'application')
BRIDGE_TASKS = ('composition', 'binding')   # each adds its bridge fact as a hop
RELATED = ('related_near', 'related_far')
# Which derivations each query kind may use, and its hops (README, "Which
# property goes where").
ALLOWED_DERIVATIONS = {
    'related_near': ('inverse', 'symmetry', 'functional', 'subproperty'),
    'related_far': ('transitivity', 'chain', 'inheritance', 'subproperty', 'none'),
    'derived': ('transitivity', 'chain', 'inheritance', 'subproperty', 'none'),
    'derived_indeterminate': ('none', 'premise'),
    'derived_contraction_cardinality': ('functional', 'cardinality'),
}
ALLOWED_TASKS = {
    'related_near': ('answer', 'application'),
    'derived_indeterminate': ('answer', 'composition'),
    'derived_contraction_cardinality': ('answer',),
}
# The order queries are stored and shown in: from the edit outwards,
# everything that should change before what must not (README, Query type).
QUERY_ORDER = ('direct', 'paraphrase', 'cross_lingual', 'propositional', 'related_near', 'related_far',
               'derived', 'unrelated_near', 'unrelated_far')
# Topics whose ABox revision records have no derived edits and no
# indeterminate query (README, Shape per topic: Mathematics and grammar).
DETERMINATE_TOPICS = ('mathematics', 'grammar')


def split_of(rec, path=None):
    """'dev' for the dev split (dev/ folder, ids ending -dNNN), else 'main'."""
    rid = rec.get('id') if isinstance(rec, dict) else None
    if isinstance(rid, str) and re.search(r'-d\d{3}$', rid):
        return 'dev'
    if path is not None and (ROOT / 'dev') in Path(path).resolve().parents:
        return 'dev'
    return 'main'


def query_counts(rec, path=None):
    """The queries a record of this type carries (README, Queries per record
    type)."""
    box, op = rec.get('box'), rec.get('edit_operation')
    counts = {'direct': 1, 'paraphrase': 1, 'cross_lingual': 2, 'propositional': 3,
              'related_near': 1, 'related_far': 1, 'derived': 3, 'unrelated_near': 1, 'unrelated_far': 1}
    if box == 'rbox':
        del counts['paraphrase'], counts['related_near'], counts['related_far']
        counts['derived'] = 2    # the two instance questions
    elif box == 'tbox' or op == 'insert':
        del counts['related_near'], counts['related_far']
    elif op == 'replace' and split_of(rec, path) == 'main':
        counts['derived'] = 4    # 3 determinate + 1 indeterminate (mathematics, grammar: 4 determinate)
    return counts


def wants_indeterminate(rec, path=None):
    """Exactly one indeterminate derived query: main-split ABox revision,
    except mathematics and grammar."""
    return (rec.get('box') == 'abox' and rec.get('edit_operation') == 'replace'
            and split_of(rec, path) == 'main' and rec.get('topic') not in DETERMINATE_TOPICS)


# Propositional queries (README, Propositional queries; metric: logical
# consistency): the edited fact E inside a yes/no truth-functional question:
# negation, conjunction (S true) and disjunction (S false), in that order, so
# the answer flips with the edit. Their formal check is the truth table below.
PROPOSITIONAL_KEYS = {'prompt', 'form', 'side_fact', 'original_answer', 'new_answer'}
PROPOSITIONAL_FORMS = ('not', 'and', 'or')
UNKNOWN_ANSWER = "I don't know"

RECORD_KEYS = {'id', 'edit_operation', 'topic', 'box', 'derivability', 'relation', 'edit', 'queries', 'notes',
               'checks', 'reality', 'fictional', 'worlds', 'evidence', 'paired_with'}
OPTIONAL_RECORD_KEYS = {'notes', 'checks', 'reality', 'fictional', 'worlds', 'evidence', 'paired_with'}
# Insert only: made up, so no model can hold it.
REALITY = ('fictional',)
# A check turns one fact the model must already hold (a premise, or a bridge
# fact not stated in the prompt) into a question with a short answer, so the
# model audit can ask it before editing.
CHECK_KEYS = {'fact', 'prompt', 'answer'}
EDIT_KEYS = {'statement', 'subject', 'prompt_subject', 'object', 'old_object', 'premises', 'axiom', 'original'}
# Each edited-knowledge query carries the answer before and after the edit;
# an LLM judge compares a generated answer with them, so there are no alias
# or forbidden lists. Locality queries carry only an optional reference: their
# gold is the model's own pre-edit answer.
QUERY_KEYS = {'prompt', 'original_answer', 'new_answer'}
DERIVED_KEYS = QUERY_KEYS | {'derivation', 'task', 'hops', 'bridge', 'via', 'bridge_in_prompt', 'fact',
                             'derivability', 'determinacy', 'determinacy_why', 'world_answers', 'chain',
                             'premise_route', 'logic', 'theory', 'revision_facts', 'revision_in_prompt',
                             'alt_derivations'}
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


def revision_in_prompt(q):
    """Are a derived query's revision facts stated in its prompt? Their own
    flag, revision_in_prompt, when set; else the bridge_in_prompt flag."""
    return bool(q.get('revision_in_prompt', q.get('bridge_in_prompt')))


def unstated_facts(q):
    """A derived query's bridge and revision facts its prompt does not state:
    the facts the audit asks before editing for this query."""
    out = [] if q.get('bridge_in_prompt') else list(q.get('bridge') or [])
    if not revision_in_prompt(q):
        out += list(q.get('revision_facts') or [])
    return out


def facts_to_check(rec):
    """The facts a model must already hold for the record's derivations, in
    order and without repeats: the edit's premises, then every bridge fact and
    revision fact a related or derived query does not state in its own prompt. RBox
    instance facts are usually given in the prompt; a role chain's real hop
    may be left to the model (README, RBox items), and is then checked like
    any bridge."""
    out = list(rec.get('edit', {}).get('premises') or [])
    queries = rec.get('queries', {})
    for qtype in ('related_near', 'related_far', 'derived'):
        for q in queries.get(qtype) or []:
            if isinstance(q, dict):
                out.extend(unstated_facts(q))
    return list(dict.fromkeys(out))


def side_facts(rec):
    """The side facts of the record's propositional queries. Each may have a
    check (asked before editing like a bridge; its answer also gives the
    fact's truth for the truth table); one that is trivially true or false
    may go without, and is then taken to have the value the flip needs."""
    queries = rec.get('queries') if isinstance(rec.get('queries'), dict) else {}
    items = queries.get('propositional') if isinstance(queries.get('propositional'), list) else []
    return [q['side_fact'] for q in items if isinstance(q, dict) and is_text(q.get('side_fact'))]


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
    optional = set(side_facts(rec))
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
        if is_text(c.get('fact')) and c['fact'] not in need and c['fact'] not in optional:
            errors.append(f'{where}: fact {c["fact"]!r} is not a premise, an unstated bridge or revision fact, '
                          'or a propositional side fact of this record')
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

    # Identity and location: main split under records/, dev split under dev/.
    rid = rec['id']
    split = split_of(rec, path)
    pattern = rf'{topic}-{op}-d\d{{3}}' if split == 'dev' else rf'{topic}-{op}-\d{{4}}'
    if not (isinstance(rid, str) and re.fullmatch(pattern, rid)):
        err(f'id {rid!r} should be "{topic}-{op}-' + ('dNNN"' if split == 'dev' else 'NNNN"'))
    if path.name != f'{rid}.json':
        err(f'file name {path.name!r} should be "{rid}.json"')
    folder = path.parent.parent.parent.name
    if folder in ('records', 'dev'):
        if (path.parent.parent.name, path.parent.name) != (topic, op):
            err(f'file should live in {folder}/{topic}/{op}/')
        if (folder == 'dev') != (split == 'dev'):
            err('dev records (ids -dNNN) live in dev/, main records in records/')

    errors.extend(check_determinacy(rec, path))
    errors.extend(check_evidence(rec))
    # Tag: set for ABox and TBox replace and delete. A new fact can't follow
    # from what the model already holds, and RBox edits are about a relation.
    deriv = rec['derivability']
    if box in ('abox', 'tbox') and op != 'insert':
        if deriv not in DERIVABILITY:
            err(f'derivability {deriv!r} not one of {DERIVABILITY} (only the two ends are used)')
        elif deriv == 'very_likely' and not (box == 'abox' and op == 'replace' and split == 'main'
                                             and topic not in DETERMINATE_TOPICS):
            err('a very_likely (derived) edit is only for main-split ABox revision '
                '(not dev, contraction, TBox, mathematics or grammar)')
    elif deriv is not None:
        err('derivability must be null for ' + ('insert' if op == 'insert' else 'rbox'))
    # Tag, insert only: replace and delete always edit a real fact.
    reality = rec.get('reality')
    if op == 'insert':
        if reality not in REALITY:
            err(f'reality {reality!r}: expansion is fictional only (reality: fictional)')
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
    elif box == 'abox' and op == 'delete':
        tags = relations[relation][0]
        if 'functional' not in tags and 'cardinality:many' not in tags:
            err(f'an ABox contraction edits a functional or many-valued relation; {relation!r} is tagged neither '
                '(README, Contraction)')

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
        # Where locate-and-edit methods edit: TBox and RBox subjects are
        # ontology terms the question words differently, so those records
        # name the question's own wording and which occurrence of it.
        span = edit.get('prompt_subject')
        if box == 'abox':
            if span is not None:
                err('edit.prompt_subject is for tbox and rbox records (an abox subject is in the question as it is)')
        elif not isinstance(span, dict) or not is_text(span.get('text')) \
                or not isinstance(span.get('occurrence'), int) or span['occurrence'] < 1 \
                or set(span) != {'text', 'occurrence'}:
            err('edit.prompt_subject must be {"text": non-empty string, "occurrence": integer >= 1} on tbox and rbox records')
        else:
            question = ((rec.get('queries') or {}).get('direct') or {}).get('prompt') or ''
            if question.count(span['text']) < span['occurrence']:
                err(f'edit.prompt_subject {span["text"]!r} does not occur {span["occurrence"]} time(s) in the direct question')
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
        if (deriv == 'very_likely') != ('premises' in edit):
            err('edit.premises is required exactly when derivability is very_likely (a derived edit)')
        for k in ('original',):
            if k in edit and not is_text(edit[k]):
                err(f'edit.{k} must be a non-empty string')
        # An RBox edit states the property only ("'Borders' is symmetric."),
        # not an explanation of it; the questions carry the meaning.
        if box == 'rbox':
            for k in ('statement', 'original'):
                if is_text(edit.get(k)) and ': ' in edit[k]:
                    err(f'edit.{k}: state the property only, without the explanation after the colon')

    queries = rec['queries']
    if not isinstance(queries, dict):
        return errors + ['queries must be an object']
    counts = query_counts(rec, path)
    for k in sorted(set(queries) - set(counts)):
        err(f'queries: {k!r} is not a query of this record type (README, Queries per record type)')
    present = [k for k in queries if k in QUERY_ORDER]
    if present != sorted(present, key=QUERY_ORDER.index):
        err(f'queries: keys should come in the order {[k for k in QUERY_ORDER if k in counts]}')
    for qtype, count in counts.items():
        items = queries.get(qtype)
        if qtype in ('direct', 'paraphrase'):
            items = [items] if isinstance(items, dict) else items
        lo, hi = count if isinstance(count, tuple) else (count, count)
        if not isinstance(items, list) or not lo <= len(items) <= hi:
            want = f'{lo} to {hi}' if lo != hi else str(lo)
            err(f'queries.{qtype}: expected {want} quer{"y" if hi == 1 else "ies"}'
                + (' as a list' if qtype not in ('direct', 'paraphrase') else ''))
            continue
        for i, q in enumerate(items):
            where = f'queries.{qtype}' + (f'[{i}]' if qtype not in ('direct', 'paraphrase') else '')
            errors.extend(f'{where}: {e}' for e in check_query(q, qtype, rec, relations))

    langs = [q.get('language') for q in queries.get('cross_lingual') or [] if isinstance(q, dict)]
    if sorted(langs) != sorted(LANGUAGES):
        err(f'queries.cross_lingual: needs one query per language {LANGUAGES}, got {langs}')
    if not errors:
        errors.extend(check_propositional(rec))
        errors.extend(check_contraction(rec))
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


def related_and_derived(rec):
    """[(qtype, index, query)] for every related and derived query."""
    queries = rec.get('queries') if isinstance(rec.get('queries'), dict) else {}
    out = []
    for qtype in ('related_near', 'related_far', 'derived'):
        items = queries.get(qtype)
        for i, q in enumerate(items if isinstance(items, list) else []):
            if isinstance(q, dict):
                out.append((qtype, i, q))
    return out


def check_determinacy(rec, path=None):
    """Every related and derived query of an ABox or TBox record has a
    determinacy. Exactly one derived query is indeterminate on main-split ABox
    revision (not mathematics or grammar); every other query is determinate.
    A record has worlds exactly when it has its indeterminate query (2 to 4,
    unique ids, each with the facts or choices it assumes). RBox records carry
    none."""
    errors = []
    err = errors.append
    qs = related_and_derived(rec)
    if rec.get('box') not in DETERMINACY_BOXES:
        if any('determinacy' in q for _, _, q in qs) or 'worlds' in rec:
            err('determinacy and worlds are for ABox and TBox records; RBox records leave them out')
        return errors
    for qtype, i, q in qs:
        if 'determinacy' not in q:
            err(f'queries.{qtype}[{i}]: determinacy is required')
        elif is_indeterminate(q) and qtype != 'derived':
            err(f'queries.{qtype}[{i}]: related queries are determinate')
    indeterminate = [q for qtype, _, q in qs if is_indeterminate(q)]
    want = 1 if wants_indeterminate(rec, path) else 0
    if len(indeterminate) != want:
        err(f'expected {want} indeterminate derived quer{"y" if want == 1 else "ies"}, found {len(indeterminate)} '
            '(only main-split ABox revision has one; README, Queries per record type)')
    if not indeterminate:
        if 'worlds' in rec:
            err('worlds are only for records with an indeterminate derived query')
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
    before the edit (edit.original, else the statement), every premise, and
    the `fact` of every related and derived query that rates one."""
    e = rec.get('edit') if isinstance(rec.get('edit'), dict) else {}
    edited = e.get('original') or e.get('statement')
    facts = [edited, *(e.get('premises') or [])]
    facts += [q.get('fact') for _, _, q in related_and_derived(rec) if 'derivability' in q]
    return list(dict.fromkeys(f for f in facts if is_text(f)))


def check_evidence(rec):
    """Evidence is keyed by the fact's exact text and required for the edited
    fact, every premise and every related and derived query's `fact`
    (README, Evidence). The edited fact's claim follows its derivability, and
    so does each query fact's (very_unlikely: stored; very_likely: derived);
    premises are claimed stored."""
    errors = []
    err = errors.append
    if rec.get('box') == 'rbox':
        need = []
    else:
        need = evidence_facts(rec)
    ev = rec.get('evidence')
    if ev is None:
        if need:
            err('evidence is required: one entry for the edited fact, each premise and each related and '
                'derived query\'s fact')
        return errors
    if not isinstance(ev, dict):
        return ['evidence must be an object keyed by fact text']
    e = rec.get('edit') if isinstance(rec.get('edit'), dict) else {}
    allowed = set(need) | set(evidence_facts(rec))
    query_claim = {}
    for _, _, q in related_and_derived(rec):
        allowed.update(b for b in (q.get('bridge') or []) + (q.get('revision_facts') or []) if is_text(b))
        if is_text(q.get('fact')) and q.get('derivability') in DERIVABILITY:
            query_claim[q['fact']] = 'derived' if q['derivability'] == 'very_likely' else 'stored'
    side = set(side_facts(rec))
    allowed.update(side)  # propositional side facts are backed by evidence too (CRITERIA Rules 1 and 5)
    for fact in need:
        if fact not in ev:
            err(f'evidence: no entry for {fact!r}')
    edited = (e.get('original') or e.get('statement')) if e else None
    premises = set(e.get('premises') or [])
    for fact, entry in ev.items():
        where = f'evidence[{fact!r}]'
        if fact not in allowed:
            err(f'{where}: not the edited fact, a premise, a query fact, a bridge, a revision fact or a side fact '
                'of this record (copy the text exactly)')
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
            if claim != 'fictional':
                err(f'{where}: an inserted fact is claimed fictional')
        elif fact == edited:
            want = 'derived' if rec.get('derivability') == 'very_likely' else 'stored'
            if claim in EVIDENCE_CLAIMS and claim != want:
                err(f'{where}: claim {claim!r} disagrees with derivability {rec.get("derivability")!r} ({want})')
        elif fact in query_claim:
            if claim in EVIDENCE_CLAIMS and claim != query_claim[fact]:
                err(f'{where}: claim {claim!r} disagrees with the query\'s derivability ({query_claim[fact]})')
        elif fact in premises and claim == 'derived':
            err(f'{where}: a premise is claimed stored; a derived premise needs premises of its own')
        if claim == 'fictional' and fact != edited:
            err(f'{where}: only the inserted fact can be fictional; premises and bridges are real')
        if claim == 'definitional' and (fact == edited or fact in query_claim):
            err(f'{where}: the edited fact and query facts cannot be definitional; premises, bridges, revision '
                'facts and side facts can (true by what the words mean)')
        if claim == 'false' and fact not in side:
            err(f'{where}: only a propositional side fact can be claimed false')
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
    if qtype == 'propositional':
        return check_propositional_item(q, rec)
    locality = qtype.startswith('unrelated')
    reasoned = qtype == 'derived' or qtype in RELATED
    if locality:
        allowed = LOCALITY_KEYS
    elif reasoned:
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
    core = not reasoned
    if op == 'insert':
        if original is not None:
            err('original_answer must be null for insert: the model holds nothing before the edit')
        if not is_text(new):
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
        # Contraction: "does not know", except a many-valued relation's
        # cardinality question, whose other value keeps its answer.
        if q.get('derivation') == 'cardinality':
            if new != original:
                err('a cardinality question keeps its answer under contraction: new_answer equals original_answer')
        elif new is not None:
            err('new_answer must be null for delete: the model should say it does not know')
        if core and not is_text(original):
            err('original_answer is required on reliability and cross-lingual queries under delete')
    if qtype == 'cross_lingual' and q.get('language') not in LANGUAGES:
        err(f'language must be one of {LANGUAGES}')
    if reasoned:
        errors.extend(check_world_answers(q, rec))
        errors.extend(check_derivation(q, qtype, rec, relations))
    return errors


def answer_value(a):
    """'yes', 'no' or 'unknown' for a propositional gold answer, else None."""
    if not is_text(a):
        return None
    n = a.strip().lower().replace('\u2019', "'").rstrip('.').strip()
    return {'yes': 'yes', 'no': 'no', "i don't know": 'unknown'}.get(n)


def check_propositional_item(q, rec):
    """One propositional query's own fields (the truth table is record level)."""
    errors = []
    err = errors.append
    for k in sorted(set(q) - PROPOSITIONAL_KEYS):
        err(f'unknown field {k!r}')
    for k in sorted(PROPOSITIONAL_KEYS - set(q)):
        err(f'missing field {k!r} (null if it does not apply)')
    if not is_text(q.get('prompt')):
        err('prompt must be a non-empty string')
    form = q.get('form')
    if form not in PROPOSITIONAL_FORMS:
        err(f'form {form!r} not one of {PROPOSITIONAL_FORMS}')
    elif form == 'not':
        if q.get('side_fact') is not None:
            err('side_fact must be null for form "not"')
    elif not is_text(q.get('side_fact')):
        err(f'side_fact must be a non-empty string for form {form!r}: the untouched fact combined with the edit')
    op = rec['edit_operation']
    orig, new = q.get('original_answer'), q.get('new_answer')
    if op == 'insert':
        if orig is not None:
            err('original_answer must be null for insert')
    elif answer_value(orig) not in ('yes', 'no'):
        err(f'original_answer must be "yes" or "no" (got {orig!r})')
    if op == 'delete':
        if answer_value(new) != 'unknown':
            err(f'new_answer must be "{UNKNOWN_ANSWER}" for delete (the edited fact is unknown after it)')
    elif answer_value(new) not in ('yes', 'no'):
        err(f'new_answer must be "yes" or "no" (got {new!r})')
    return errors


def kleene(form, e, s=None):
    """Strong Kleene value of not E / E and S / E or S; True, False or None
    (unknown)."""
    if form == 'not':
        return None if e is None else not e
    if form == 'and':
        if e is False or s is False:
            return False
        return True if e is True and s is True else None
    if e is True or s is True:
        return True
    return False if e is False and s is False else None


# The edited fact E's truth before and after the edit: replace (E is the
# edited statement) false then true; insert true after (nothing before);
# delete (E is the removed fact) true then unknown.
EDIT_TRUTH = {'replace': (False, True), 'insert': (None, True), 'delete': (True, None)}
VALUE_ANSWER = {True: 'yes', False: 'no', None: 'unknown'}


def side_truth(rec, fact):
    """S's truth from its check's answer (yes / no; any other answer fills a
    slot of the fact as stated, so the fact holds), or None with no check."""
    for c in rec.get('checks') or []:
        if isinstance(c, dict) and c.get('fact') == fact:
            v = answer_value(c.get('answer'))
            return False if v == 'no' else True
    return None


def check_propositional(rec):
    """Record level: the forms not, and, or in that order, and the
    truth table. With E's truth before and after the edit (EDIT_TRUTH) and S's
    from its check (or, without one, the value the flip needs: and true, or
    false), each gold answer must equal the connective's strong Kleene value
    (unknown -> "I don't know"), and the answer must change with the edit
    (for insert, compared with E false)."""
    errors = []
    items = rec['queries'].get('propositional')
    if not isinstance(items, list) or not all(isinstance(q, dict) for q in items):
        return errors
    forms = [q.get('form') for q in items]
    if forms != list(PROPOSITIONAL_FORMS):
        errors.append(f'queries.propositional: needs negation, conjunction and disjunction in that order '
                      f'(forms {list(PROPOSITIONAL_FORMS)}, got {forms})')
    op = rec['edit_operation']
    e_before, e_after = EDIT_TRUTH[op]
    statement = (rec.get('edit') or {}).get('statement')
    for i, q in enumerate(items):
        where = f'queries.propositional[{i}]'
        form = q.get('form')
        if form not in PROPOSITIONAL_FORMS:
            continue
        s = None
        if form != 'not':
            fact = q.get('side_fact')
            if not is_text(fact):
                continue
            if statement and fact.strip() == statement.strip():
                errors.append(f'{where}: side_fact is the edited fact itself')
            s = side_truth(rec, fact)
            need = form == 'and'     # the side fact value that lets the answer flip
            if s is None:
                s = need
            elif s != need:
                errors.append(f'{where}: the side fact is {"true" if s else "false"} by its check, so "{form}" '
                              f'does not flip with the edit ({form}: the side fact must be {"true" if need else "false"})')
                continue
        if kleene(form, False if e_before is None else e_before, s) == kleene(form, e_after, s):
            errors.append(f'{where}: the answer does not change with the edit')
        for name, e in (('original_answer', e_before), ('new_answer', e_after)):
            if op == 'insert' and name == 'original_answer':
                continue
            want = VALUE_ANSWER[kleene(form, e, s)]
            got = answer_value(q.get(name))
            if got is not None and got != want:
                show = UNKNOWN_ANSWER if want == 'unknown' else want
                errors.append(f'{where}: {name} should be "{show}" by the truth table '
                              f'(E {"unknown" if e is None else e}, form {form}'
                              + ('' if form == 'not' else f', side fact {s}') + f'), not {q.get(name)!r}')
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
    """Records in records/ and dev/ show the chain of every query with one
    answer (determinate related and derived, RBox instances). The templates
    in examples/ are held to the same."""
    errors = []
    for qtype, i, q in related_and_derived(rec):
        if not is_indeterminate(q) and 'chain' not in q:
            errors.append(f'queries.{qtype}[{i}]: chain is required: the steps from the edit to the answer')
    return errors


def check_contraction(rec):
    """ABox contraction (README, Contraction): exactly one cardinality
    question, 1 hop, matching the relation (functional: "no" becomes "does
    not know"; many-valued: another held value keeps its answer)."""
    if rec.get('box') != 'abox' or rec.get('edit_operation') != 'delete':
        return []
    derived = (rec.get('queries') or {}).get('derived') or []
    card = [q for q in derived if isinstance(q, dict) and q.get('derivation') in ('functional', 'cardinality')]
    if len(card) != 1:
        return ['queries.derived: an ABox contraction has exactly one cardinality question '
                '(derivation functional or cardinality) and two 2-hop questions through the removed fact']
    q = card[0]
    if q.get('derivation') == 'functional' and answer_value(q.get('original_answer')) != 'no':
        return ['queries.derived: the functional cardinality question asks another candidate value: '
                'original_answer "no" (it becomes "does not know")']
    return []


def answers_differ(a, b):
    return not (is_text(a) and is_text(b) and a.strip().lower() == b.strip().lower())


def check_derivation(q, qtype, rec, relations):
    """A related or derived query's derivation, task, hops, bridges, rated fact
    and answers (README, Relation properties and task types; Related and
    derived queries)."""
    errors = []
    err = errors.append
    derivation, box, op = q.get('derivation'), rec['box'], rec['edit_operation']
    if derivation not in DERIVATIONS:
        return [f'derivation {derivation!r} not one of {tuple(DERIVATIONS)} '
                '(composition, binding and application are tasks; scope and asymmetry are not used)']
    bridge = q.get('bridge')
    if not is_text_list(bridge):
        err('bridge must be a list of strings (empty if none)')
        bridge = []
    hops = q.get('hops')
    if hops != 1 + len(bridge):
        err(f'hops should be 1 + number of bridge facts = {1 + len(bridge)}')
    if 'bridge_in_prompt' in q and not isinstance(q['bridge_in_prompt'], bool):
        err('bridge_in_prompt must be true or false')
    if q.get('bridge_in_prompt') and not bridge:
        err('bridge_in_prompt needs the bridge facts listed in bridge')
    if 'revision_facts' in q:
        rev = q['revision_facts']
        if not (is_text_list(rev) and rev):
            err('revision_facts must be a non-empty list of strings (leave it out if none)')
        else:
            if len(set(rev)) != len(rev):
                err('revision_facts lists a fact twice')
            for f in sorted(set(rev) & set(bridge)):
                err(f'{f!r} is both a bridge and a revision fact: a fact the answer is built from is a bridge')
    if 'revision_in_prompt' in q:
        if not isinstance(q['revision_in_prompt'], bool):
            err('revision_in_prompt must be true or false')
        elif 'revision_facts' not in q:
            err('revision_in_prompt needs revision_facts')
    if 'alt_derivations' in q:
        alt = q['alt_derivations']
        if not (is_text_list(alt) and alt):
            err('alt_derivations must be a non-empty list of derivation names (leave it out if none)')
        else:
            for a in alt:
                if a not in DERIVATIONS:
                    err(f'alt_derivations: {a!r} not one of {tuple(DERIVATIONS)}')
                elif a == derivation:
                    err(f'alt_derivations: {a!r} is the derivation itself')
            if len(set(alt)) != len(alt):
                err('alt_derivations lists a name twice')

    # RBox: the two instance questions.
    if box == 'rbox':
        if qtype != 'derived' or derivation != 'instantiation':
            err('rbox items derive by instantiation, and only rbox items do')
        return errors
    if derivation == 'instantiation':
        return errors + ['rbox items derive by instantiation, and only rbox items do']

    # Which derivations and hops each kind of query takes.
    indeterminate = is_indeterminate(q)
    contraction_card = op == 'delete' and derivation in ('functional', 'cardinality')
    if qtype == 'derived' and indeterminate:
        kind = 'derived_indeterminate'
    elif contraction_card and qtype == 'derived':
        kind = 'derived_contraction_cardinality'
    else:
        kind = qtype
    if derivation not in ALLOWED_DERIVATIONS[kind]:
        err(f'{kind.replace("_", " ")} queries use one of {ALLOWED_DERIVATIONS[kind]}, not {derivation!r}')
    if isinstance(hops, int):
        if qtype == 'related_near' and hops != 1:
            err('related near queries are 1 hop (no bridge fact)')
        elif qtype == 'related_far' and hops < 2:
            err('related far queries are 2 or more hops')
        elif qtype == 'derived' and not indeterminate and not contraction_card and hops != 2:
            err('determinate derived queries are exactly 2 hops (the edit and one bridge fact)')
        elif contraction_card and hops != 1:
            err('the contraction cardinality question is 1 hop')
    if derivation in ('transitivity', 'chain', 'inheritance') and not bridge:
        err(f'{derivation} needs at least one bridge fact')
    task = q.get('task')
    if task in BRIDGE_TASKS and not bridge:
        err(f'task {task} needs its bridge fact (the second fact, or the alias)')
    if derivation == 'none' and task not in BRIDGE_TASKS:
        err('derivation none needs task composition or binding (otherwise nothing carries the edit)')
    if task in TASKS and task not in ALLOWED_TASKS.get(kind, TASKS):
        err(f'{kind.replace("_", " ")} queries use task one of {ALLOWED_TASKS[kind]}, not {task!r}')
    if derivation == 'functional' and op == 'insert':
        err('functional derivations need an original value: replace or delete only')

    # Task, rated fact, answers.
    if 'task' in q and q['task'] not in TASKS:
        err(f'task {q["task"]!r} not one of {TASKS}')
    if not indeterminate:
        if 'task' not in q:
            err(f'task is required, one of {TASKS}')
        if not is_text(q.get('fact')):
            err('fact is required: the fact the question asks about, as held before the edit (its evidence backs '
                'derivability)')
        want = 'very_unlikely' if qtype in RELATED else 'very_likely'
        if contraction_card:
            if 'derivability' in q:
                err('the contraction cardinality question leaves derivability out')
        elif q.get('derivability') != want:
            err(f'derivability must be {want!r} on a {qtype.replace("_", " ")} query '
                f'({"stored" if want == "very_unlikely" else "worked out"} answer)')
        if op == 'replace' and not answers_differ(q.get('original_answer'), q.get('new_answer')):
            err('the answer must change with the edit (original_answer equals new_answer)')
    else:
        for k in ('fact', 'derivability'):
            if k in q:
                err(f'{k} is left out on the indeterminate query')

    # The tag the derivation relies on, on the edited relation or on `via`.
    need = DERIVATIONS[derivation]
    if need:
        name = q.get('via', rec['relation'])
        entry = relations.get(name)
        if entry is None:
            err(f'relation {name!r} (used by {derivation}) is not in RELATIONS.md')
        elif not any(t == need or (need.endswith(':') and t.startswith(need)) for t in entry[0]):
            err(f'{derivation} needs {name!r} to have a {need.rstrip(":")} tag in RELATIONS.md')
    return errors


def default_paths(which='main'):
    """main: records/ and examples/; dev: dev/; all: both splits and examples/."""
    main = sorted((ROOT / 'records').rglob('*.json')) + sorted((ROOT / 'examples').glob('*.json'))
    dev = sorted((ROOT / 'dev').rglob('*.json'))
    return {'main': main, 'dev': dev, 'all': main + dev}[which]


def edited_keys(rec):
    """What a record edits, for the main/dev overlap check (CRITERIA Rule 4):
    its subject and its statement, lower-cased."""
    e = rec.get('edit') if isinstance(rec.get('edit'), dict) else {}
    return {str(v).strip().lower() for v in (e.get('subject'), e.get('statement'), e.get('original')) if is_text(v)}


def _norm_entity(x):
    x = ' '.join(str(x or '').casefold().split())
    return x[4:] if x.startswith('the ') else x


def pair_errors(paths):
    """Contraction and expansion records paired with a revision record
    (README, Contraction, "The three operations are paired"; CRITERIA Rule
    14): paired_with names a revision of the same topic, box and split, each
    revision is paired at most once per operation, a contraction removes the
    revision's original fact and an expansion reuses its relation and new
    object with another (made-up) subject."""
    out, used = [], Counter()
    for path in paths:
        if not (path.is_relative_to(ROOT / 'records') or path.is_relative_to(ROOT / 'dev')):
            continue
        try:
            rec = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(rec, dict):
            continue
        op, rid, pid = rec.get('edit_operation'), rec.get('id'), rec.get('paired_with')
        if op == 'replace':
            if pid is not None:
                out.append(f'{rid}: paired_with is only for contraction and expansion records')
            continue
        if op not in ('delete', 'insert'):
            continue
        if not is_text(pid):
            out.append(f'{rid}: paired_with (the paired revision record id) is required on contraction and expansion '
                       '(README, Contraction)')
            continue
        split_root = ROOT / ('dev' if path.is_relative_to(ROOT / 'dev') else 'records')
        ppath = split_root / str(rec.get('topic')) / 'replace' / f'{pid}.json'
        try:
            rev = json.loads(ppath.read_text())
        except (OSError, json.JSONDecodeError):
            out.append(f'{rid}: paired_with {pid!r}: no revision record {ppath.relative_to(ROOT)}')
            continue
        used[(pid, op)] += 1
        if used[(pid, op)] == 2:
            out.append(f'{pid}: paired with more than one {op} record')
        if rev.get('box') != rec.get('box'):
            out.append(f'{rid}: paired revision {pid} is {rev.get("box")}, this record is {rec.get("box")}')
            continue
        if rec.get('box') != 'abox':
            continue
        e, re_ = rec.get('edit') or {}, rev.get('edit') or {}
        if op == 'delete':
            if rev.get('derivability') == 'very_likely':
                continue    # removes the derived edit's stored premise instead
            if rec.get('relation') != rev.get('relation'):
                out.append(f'{rid}: removes a {rec.get("relation")!r} fact, its revision {pid} edits {rev.get("relation")!r}')
            if _norm_entity(e.get('subject')) != _norm_entity(re_.get('subject')) or \
                    _norm_entity(e.get('object')) != _norm_entity(re_.get('old_object')):
                out.append(f'{rid}: should remove the original fact of {pid} '
                           f'({re_.get("subject")!r}, {re_.get("old_object")!r}), not ({e.get("subject")!r}, {e.get("object")!r})')
        else:
            if rec.get('relation') != rev.get('relation'):
                out.append(f'{rid}: relation {rec.get("relation")!r}, its revision {pid} edits {rev.get("relation")!r}')
            if _norm_entity(e.get('object')) != _norm_entity(re_.get('object')):
                out.append(f'{rid}: object {e.get("object")!r} should be the new object of {pid} ({re_.get("object")!r})')
            if _norm_entity(e.get('subject')) == _norm_entity(re_.get('subject')):
                out.append(f'{rid}: expansion needs a made-up subject in an empty slot, not the revision\'s subject')
    return out


def split_overlap():
    """Dev records sharing a subject or an edited fact with a main record."""
    main, out = {}, []
    for path in sorted((ROOT / 'records').rglob('*.json')):
        try:
            rec = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        for k in edited_keys(rec):
            main.setdefault(k, rec.get('id'))
    for path in sorted((ROOT / 'dev').rglob('*.json')):
        try:
            rec = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        for k in sorted(edited_keys(rec)):
            if k in main:
                out.append(f'{rec.get("id")}: shares {k!r} with main record {main[k]} (CRITERIA Rule 4)')
    return out


def main(argv):
    if '--criteria' in argv:
        # Report only (exit 0): how the records meet CRITERIA.md.
        import criteria
        return criteria.main([a for a in argv if a != '--criteria'])
    relations, conflicts = load_relations()
    for c in conflicts:
        print(c)
    which = next((a for a in argv if a in ('main', 'dev', 'all')), None)
    files = [a for a in argv if a not in ('main', 'dev', 'all')]
    paths = [Path(p).resolve() for p in files] or default_paths(which or 'main')
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
            for _, _, q in related_and_derived(rec):
                prop = relation_property(rec, q, relations)
                if prop:
                    needed.add(prop)
        if isinstance(rec, dict):
            # The templates in examples/ aren't part of the dataset, so their
            # ids only have to be unique among themselves.
            in_data = path.is_relative_to(ROOT / 'records') or path.is_relative_to(ROOT / 'dev')
            ids[(in_data, rec.get('id'))] += 1
            if in_data:
                cells[(split_of(rec, path), rec.get('topic'), rec.get('edit_operation'))] += 1
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
    for line in pair_errors(paths):
        print(line)
        failed += 1
    if which in ('dev', 'all'):
        for line in split_overlap():
            print(line)
            failed += 1
    print(f'{len(paths)} file(s) checked, {failed} with errors.')
    for (split, topic, op), n in sorted(cells.items()):
        print(f'  {split} {topic}/{op}: {n}')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
