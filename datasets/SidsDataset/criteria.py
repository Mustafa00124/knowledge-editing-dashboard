#!/usr/bin/env python3
"""Report how Sid's Dataset records meet CRITERIA.md.

Report only for now: it lists what breaks each criterion and always exits 0.
A check moves into validate.py's errors once the records meet it. The
dashboard shows the same report (Datasets, Sid's Dataset, Criteria) through
report().

    python datasets/SidsDataset/criteria.py          # or: validate.py --criteria
    python datasets/SidsDataset/criteria.py --all    # every offending item, not the first few
    python datasets/SidsDataset/criteria.py --json   # what the dashboard reads
    python datasets/SidsDataset/criteria.py --marks    # review marks per reviewer, and every red one
    python datasets/SidsDataset/criteria.py --mark RECORD ITEM REVIEWER green|red|clear [--comment TEXT] [--kind angle]

Each check has a status: pass, fail, review (a script can only flag it, a
person decides), pending (waiting on data, e.g. a model audit or the Rule 3
judge not yet run) or manual (informational: the two manual rules and their
guidance are read from CRITERIA.md; reviewers mark each record per rule, and
each query, green or red; marks are in reviews.json).
Standard library only, like validate.py.
"""
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate import (ROOT, TOPICS, load_relations)  # noqa: E402

# Provisional numbers; CRITERIA.md is where they get agreed.
SIMILAR_STATEMENT = 0.9   # difflib ratio above which two edits are listed as near repeats
MAX_FAR_REUSE = 10        # times one far unrelated prompt may appear in the dataset
# Derivation mix targets, {(box, derivation): share of that box's derived queries}.
# Empty until CRITERIA.md B3 has numbers; the counts are reported either way.
DERIVATION_TARGETS = {}
RBOX_PROPERTY_TARGETS = {}
# The models whose audit the audit criteria require (CRITERIA.md R4): the instruct
# models, since the main experiments ask free-form questions. Their newest run in
# results/model_audit counts. The base models are shown beside them, for reference.
AUDIT_MODELS = ('qwen3-4b-instruct-2507', 'olmo-3-7b-instruct', 'llama-3.1-8b-instruct', 'mistral-7b-instruct-v0.1')
REFERENCE_MODELS = ('qwen3-4b-base', 'olmo-3-7b-base', 'llama-3.1-8b', 'mistral-7b-v0.1')
AUDIT_RUNS = ROOT.parent.parent / 'results' / 'model_audit' / 'runs'

YES = {'yes', '是', 'sí', 'si'}
NO = {'no', '否', '不是'}
RBOX_PROPERTIES = (('InvFunc', 'inverse_functional'), ('Asym', 'asymmetric'), ('Sym', 'symmetric'),
                   ('Trans', 'transitive'), ('Func', 'functional'), ('Refl', 'reflexive'),
                   ('Disj', 'disjoint'))
STATEMENT_WORDS = (('subproperty', 'subproperty'), ('inverse functional', 'inverse_functional'),('asymmetric', 'asymmetric'),
                   ('symmetric', 'symmetric'), ('transitive', 'transitive'),
                   ('functional', 'functional'), ('reflexive', 'reflexive'), ('disjoint', 'disjoint'),
                   ('inverse', 'inverse'))
SNAKE = re.compile(r'[a-z][a-z0-9]*(?:_[a-z0-9]+)*')
IDENT = re.compile(r'[A-Za-z][A-Za-z0-9_]*')
DL_WORDS = {name for name, _ in RBOX_PROPERTIES} | {'not'}


def load_records():
    return [json.loads(p.read_text()) for p in sorted((ROOT / 'records').glob('*/*/*.json'))]


def norm(s):
    s = re.sub(r'[^\w\s]', ' ', str(s).lower())
    s = re.sub(r'^\s*(the|a|an)\s+', '', s)
    return ' '.join(s.split())


def yes_no(answer):
    a = norm(answer)
    return 'yes' if a in YES else 'no' if a in NO else None


def rbox_property(rec):
    """The kind of axiom an RBox edit asserts (or, for delete, removes)."""
    axiom = rec['edit'].get('axiom') or ''
    if '∘' in axiom:
        return 'chain'
    if '≡' in axiom:
        return 'inverse'
    if '⊑' in axiom:
        return 'subproperty'
    for prefix, name in RBOX_PROPERTIES:
        if re.match(rf'¬?{prefix}\(', axiom):
            return name
    statement = rec['edit']['statement'].lower()
    if 'means' in statement or 'composition' in statement:
        return 'chain'
    for word, name in STATEMENT_WORDS:
        if word in statement:
            return name
    return 'other'


def check(section, name, items=(), status=None, review=False, note='', table=None):
    """One checklist row. Without an explicit status: pass when nothing is
    listed, otherwise fail (or review, for flags a person has to judge)."""
    items = list(items)
    if status is None:
        status = 'pass' if not items else 'review' if review else 'fail'
    return {'section': section, 'name': name, 'status': status, 'count': len(items),
            'items': items, 'note': note, 'table': table}


def check_repeats(recs):
    s = 'R3. No repeated edits'
    # Delete records restate replace's facts by design, so compare insert and
    # replace only; delete is checked against its replace record under R5.
    pool = [r for r in recs if r['edit_operation'] != 'delete']
    by_statement, by_triple = defaultdict(list), defaultdict(list)
    for r in pool:
        e = r['edit']
        by_statement[norm(e['statement'])].append(r['id'])
        if r['box'] == 'rbox':
            key = (r['edit_operation'], e.get('axiom') or (r['relation'], rbox_property(r), ' not ' in norm(e['statement'])))
        else:
            key = (r['relation'], norm(e.get('subject')), norm(e.get('object')))
        by_triple[key].append(r['id'])
    near, by_group = [], defaultdict(list)
    for r in pool:
        by_group[(r['topic'], r['box'])].append(r)
    for group in by_group.values():
        for i, a in enumerate(group):
            sa = norm(a['edit']['statement'])
            for b in group[i + 1:]:
                sb = norm(b['edit']['statement'])
                if sa == sb:
                    continue
                m = SequenceMatcher(None, sa, sb)
                if m.quick_ratio() >= SIMILAR_STATEMENT and m.ratio() >= SIMILAR_STATEMENT:
                    near.append(f'{a["id"]} / {b["id"]}: {a["edit"]["statement"]!r} ~ {b["edit"]["statement"]!r}')
    return [
        check(s, 'Same statement twice', [', '.join(v) for v in by_statement.values() if len(v) > 1]),
        check(s, 'Same subject, relation and object (RBox: same relation and axiom)',
              [f'{", ".join(v)}  {k}' for k, v in by_triple.items() if len(v) > 1]),
        check(s, f'Near repeats (text similarity >= {SIMILAR_STATEMENT})', near, review=True),
    ]


def check_delete(recs):
    s = 'R5. Delete means "I don\'t know"'
    by_id = {r['id']: r for r in recs}
    unpaired, mismatched, answered = [], [], []
    for r in recs:
        if r['edit_operation'] != 'delete':
            continue
        twin = by_id.get(r['id'].replace('-delete-', '-replace-'))
        if twin is None:
            unpaired.append(r['id'])
        elif norm(r['edit']['statement']) != norm(twin['edit'].get('original')):
            mismatched.append(f'{r["id"]}: {r["edit"]["statement"]!r} vs replace original {twin["edit"].get("original")!r}')
        q = r['queries']
        for qtype in ('direct', 'paraphrase', 'cross_lingual', 'derived'):
            items = q.get(qtype)
            for item in items if isinstance(items, list) else [items] if items else []:
                if item.get('new_answer') is not None:
                    answered.append(f'{r["id"]} {qtype}: expects {item["new_answer"]!r}')
        # Propositional queries say it: the edited fact is unknown after a delete.
        for i, item in enumerate(q.get('propositional') or []):
            if norm(item.get('new_answer')) != norm("I don't know"):
                answered.append(f'{r["id"]} propositional[{i}]: expects {item.get("new_answer")!r}, not "I don\'t know"')
    return [
        check(s, 'Every delete has a replace record of the same number', unpaired),
        check(s, "Delete removes its replace record's original fact", mismatched),
        check(s, 'Every delete query expects "I don\'t know"', answered),
    ]


def check_yes_no(recs):
    s = 'B2. Yes/no answers 50/50 in RBox'
    counts = Counter()
    for r in recs:
        if r['box'] != 'rbox' or r['edit_operation'] == 'delete':
            continue
        q = r['queries']
        for qtype, items in (('direct', [q['direct']]), ('derived', q['derived']),
                             ('cross_lingual', q['cross_lingual'])):
            for item in items:
                v = yes_no(item.get('new_answer'))
                if v:
                    counts[(r['edit_operation'], qtype, r['topic'], v)] += 1
    off, table = [], [['operation', 'query', 'yes', 'no']]
    for op in ('insert', 'replace'):
        for qtype in ('direct', 'derived', 'cross_lingual'):
            y = sum(n for (o, t, _, v), n in counts.items() if (o, t, v) == (op, qtype, 'yes'))
            n_ = sum(n for (o, t, _, v), n in counts.items() if (o, t, v) == (op, qtype, 'no'))
            table.append([op, qtype, y, n_])
            if y != n_:
                off.append(f'{op} {qtype}: {y} yes / {n_} no')
            for topic in TOPICS:
                ty, tn = counts[(op, qtype, topic, 'yes')], counts[(op, qtype, topic, 'no')]
                if abs(ty - tn) > 1:
                    off.append(f'{op} {qtype} {topic}: {ty} yes / {tn} no')
    other = Counter()
    for r in recs:
        if r['box'] != 'rbox' and r['edit_operation'] != 'delete':
            for item in [r['queries']['direct'], r['queries']['paraphrase'], *r['queries']['derived']]:
                v = yes_no(item.get('new_answer'))
                if v:
                    other[(r['box'], v)] += 1
    note = 'ABox/TBox, not a criterion: ' + ', '.join(
        f'{b} {other[(b, "yes")]} yes / {other[(b, "no")]} no' for b in ('abox', 'tbox'))
    return [check(s, 'RBox yes/no answers 50/50 (overall equal, per topic within 1)', off, note=note, table=table)]


def check_propositional(recs):
    """Propositional queries (validate.py checks each one's truth table):
    how many records have their two, and the yes/no balance of the answers
    per operation and form. Missing ones are pending until the data is
    written (SIDS_REQUIRE_PROPOSITIONAL=1 makes validate.py require them)."""
    s = 'B2. Yes/no answers balanced'
    missing, counts = [], Counter()
    for r in recs:
        items = r['queries'].get('propositional')
        if not items:
            missing.append(r['id'])
            continue
        for item in items:
            form = 'not' if item.get('form') == 'not' else 'and/or'
            for side in ('original_answer', 'new_answer'):
                v = yes_no(item.get(side))
                if v:
                    counts[(r['edit_operation'], form, side, v)] += 1
    table = [['operation, form', 'answer', 'yes', 'no']]
    off = []
    for op in ('replace', 'insert', 'delete'):
        for form in ('not', 'and/or'):
            for side in ('original_answer', 'new_answer'):
                y, n_ = counts[(op, form, side, 'yes')], counts[(op, form, side, 'no')]
                if y or n_:
                    table.append([f'{op}, {form}', side.split('_')[0], y, n_])
        y = sum(v for (o, _, _, a), v in counts.items() if o == op and a == 'yes')
        n_ = sum(v for (o, _, _, a), v in counts.items() if o == op and a == 'no')
        if y + n_ and abs(y - n_) > max(2, (y + n_) // 5):
            off.append(f'{op}: {y} yes / {n_} no over both answers (off by more than a fifth)')
    have = len(recs) - len(missing)
    note = (f'{have} of {len(recs)} records have their 2 propositional queries (metric: logical consistency). '
            'Before and after the edit together, yes and no should come out about even per operation; '
            'a delete\'s new answer is "I don\'t know" and is not counted.')
    status = 'pending' if not have else None
    items = off + ([f'no propositional queries yet: {len(missing)} records'] if have and missing else [])
    return [check(s, 'Propositional answers: yes/no balance (all boxes)', items, status=status, review=True,
                  note=note, table=table if have else None)]


# Rule 3: stable subjects, self-contained statements. The pattern checks run
# here; what patterns can't catch is labelled by an LLM judge
# (rule3_judge.py, on a GPU through SLURM) and cached in rule3_judge.json,
# which this script only reads.
BANNED_PHRASES = ('under those conditions', 'under these conditions', 'the specified', 'as specified',
                  'as stated', 'as given above', 'the above', 'mentioned above', 'aforementioned', 'the edit',
                  'this edit', 'after the edit', 'before the edit', 'the edited', 'the new fact', 'the stated',
                  'in this scenario', 'in this hypothetical', 'hypothetically')
CJK = re.compile(r'[぀-ヿ㐀-鿿]')
# Answers a prompt may repeat without giving anything away: abstentions, and
# yes/no answers in Chinese, which echo the question's verb (需要吗？ 需要).
NOT_AN_ANSWER = {'', 'i don t know', 'does not know', 'unknown', '能', '不能', '可以', '不可以', '对', '不对',
                 '有', '没有', '不', '需要', '不需要', '会', '不会'}
CHOICE = re.compile(r'\bor\b|还是|或|\bo\b|\bu\b|:\s', re.I)
QUOTED = re.compile(r"'[^']*'|\"[^\"]*\"|‘[^’]*’|“[^”]*”|《[^》]*》|「[^」]*」")


def contains_answer(text, answer):
    """Whether `answer` occurs in `text` as whole words (CJK: as characters).
    Yes/no, abstentions and bare numbers never count: a question has to name
    the number or the thing it asks about."""
    a = norm(answer)
    if a in NOT_AN_ANSWER or yes_no(answer) or re.fullmatch(r'[\d\s.,]+', a):
        return False
    t = norm(text)
    if CJK.search(a):
        return a.replace(' ', '') in t.replace(' ', '')
    return re.search(rf'(?<!\w){re.escape(a)}(?!\w)', t) is not None


def question_part(prompt):
    """The question a prompt asks, without the facts it states first ("France
    is in Europe. Which continent is Lyon in?") and without quoted words (a
    grammar question about 'moose')."""
    parts = re.split(r'(?<=[.!。；;])\s*', prompt.strip())
    q = next((p for p in reversed(parts) if p.strip()), prompt)
    return QUOTED.sub(' ', q)


def iter_queries(rec):
    for qtype, items in rec['queries'].items():
        if isinstance(items, list):
            for i, q in enumerate(items):
                yield f'{qtype}[{i}]', q
        elif items:
            yield qtype, items


def expected_answers(q):
    out = [q.get('original_answer'), q.get('new_answer'), q.get('reference')]
    out += [w.get('answer') for w in (q.get('world_answers') or {}).values()]
    return [a for a in dict.fromkeys(out) if isinstance(a, str)]


def record_sentences(rec):
    """[(where, text)]: every statement and prompt of a record that has to
    make sense on its own."""
    e = rec['edit']
    out = [('statement', e.get('statement')), ('original', e.get('original'))]
    out += [(f'premise[{i}]', p) for i, p in enumerate(e.get('premises') or [])]
    for key, q in iter_queries(rec):
        out.append((key, q.get('prompt')))
        out += [(f'{key} bridge', b) for b in q.get('bridge') or []]
        out += [(f'{key} revision fact', b) for b in q.get('revision_facts') or []]
        if q.get('side_fact'):
            out.append((f'{key} side fact', q['side_fact']))
    for i, c in enumerate(rec.get('checks') or []):
        out += [(f'checks[{i}] fact', c.get('fact')), (f'checks[{i}] prompt', c.get('prompt'))]
    seen, unique = set(), []
    for where, text in out:
        if text and text not in seen:
            seen.add(text)
            unique.append((where, text))
    return unique


def load_entities():
    try:
        return json.loads((ROOT / 'wikidata' / 'entities.json').read_text())
    except (OSError, ValueError):
        return {}


def rule3_patterns(recs, entities=None):
    """The deterministic part of Rule 3: {'own': [...], 'phrases': [...],
    'descriptions': [...]}, each a list of item strings. A prompt that asks
    for the edit's new value and names it is an 'own' item (its answer is the
    new value); whether a prompt that asks something else gives the answer
    away by naming the new value is left to the judge."""
    entities = load_entities() if entities is None else entities
    by_name = {k.lower(): v for k, v in entities.items()}
    own, phrases, descriptions = [], [], []
    for r in recs:
        e = r['edit']
        for key, q in iter_queries(r):
            prompt = q.get('prompt') or ''
            if not prompt or CHOICE.search(prompt):
                continue  # a question that names its options may name the answer
            asked = question_part(prompt)
            for a in expected_answers(q):
                if contains_answer(asked, a):
                    own.append(f'{r["id"]} {key}: {prompt!r} contains its answer {a!r}')
        # An ABox subject that contains the value it is edited from or to. (A
        # TBox class may name its superclass: "Corvessil nebula" is a nebula.)
        subject = e.get('subject') or ''
        if r['box'] == 'abox':
            for value in dict.fromkeys(v for v in (e.get('old_object'), e.get('object')) if v):
                if contains_answer(subject, value):
                    own.append(f'{r["id"]} subject: {subject!r} contains the value {value!r}')
        for where, text in record_sentences(r):
            low = text.lower()
            hits = [p for p in BANNED_PHRASES if re.search(rf'\b{re.escape(p)}\b', low)]
            if hits:
                phrases.append(f'{r["id"]} {where}: {", ".join(map(repr, hits))} in {text!r}')
        # Subjects wikidata/entities.json marks as descriptions, whose notes
        # say what they describe: listed when that is the edited value.
        ent = by_name.get(subject.lower())
        if r['box'] != 'rbox' and ent and ent.get('category') == 'description':
            said = ' '.join(str(ent.get(k) or '') for k in ('note', 'issue'))
            values = [v for v in (e.get('old_object'), e.get('object')) if v]
            if re.search(r'describes the answer', said, re.I) or any(contains_answer(said, v) for v in values):
                descriptions.append(f'{r["id"]}: subject {subject!r} describes the edited value ({said.strip()})')
    return {'own': own, 'phrases': phrases, 'descriptions': descriptions}


# The LLM judge's part (rule3_judge.py). The items are built here so the
# judge and this report agree on what was judged; a record whose items
# changed since it was judged is stale. Bump the version when the judge's
# prompt changes, so every label is redone.
RULE3_JUDGE_VERSION = 'rule3-judge-v1'
RULE3_JUDGE_PATH = ROOT / 'rule3_judge.json'
RULE3_FLAGS = {'subject': 'MOVES', 'standalone': 'DEPENDS', 'giveaway': 'GIVES_AWAY'}


def rule3_judge_items(rec):
    """What the judge labels for one record: its subject (ABox/TBox: does it
    describe the edited value?), each sentence (does it stand on its own?)
    and each question with a non-yes/no answer (does it give the answer away,
    e.g. through a translated name?)."""
    e, items = rec['edit'], []
    if rec['box'] != 'rbox' and e.get('subject'):
        items.append({'task': 'subject', 'key': 'subject', 'subject': e['subject'], 'statement': e['statement'],
                      'original': e.get('original') or '', 'old_value': e.get('old_object') or '',
                      'new_value': e.get('object') or ''})
    for where, text in record_sentences(rec):
        items.append({'task': 'standalone', 'key': where, 'text': text})
    for key, q in iter_queries(rec):
        answers = [a for a in expected_answers(q) if not yes_no(a) and norm(a) not in NOT_AN_ANSWER]
        if q.get('prompt') and answers:
            items.append({'task': 'giveaway', 'key': key, 'prompt': q['prompt'], 'answers': answers,
                          'edit': '' if rec['edit_operation'] == 'delete' else e['statement']})
    return items


def rule3_judge_hash(rec):
    import hashlib
    blob = json.dumps([RULE3_JUDGE_VERSION, rule3_judge_items(rec)], ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def load_rule3_judge(path=None):
    try:
        return json.loads(Path(path or RULE3_JUDGE_PATH).read_text())
    except (OSError, ValueError):
        return {}


def check_rule3(recs, entities=None, judged=None):
    found = rule3_patterns(recs, entities)
    judged = load_rule3_judge() if judged is None else judged
    cached = judged.get('records', {})
    missing, stale, flagged, unclear = [], [], [], 0
    for r in recs:
        entry = cached.get(r['id'])
        if entry is None:
            missing.append(r['id'])
        elif entry.get('hash') != rule3_judge_hash(r):
            stale.append(r['id'])
        else:
            for item in entry.get('items', []):
                unclear += item.get('label') == 'UNCLEAR'
                if item.get('label') == RULE3_FLAGS.get(item.get('task')):
                    what = item.get('text') or item.get('prompt') or item.get('subject')
                    flagged.append(f'{r["id"]} {item["task"]} {item["key"]}: {what!r}: {item.get("reason", "")}')
    pending = len(missing) + len(stale)
    note = (f'{len(recs) - pending} of {len(recs)} records judged ({judged.get("judge_model", "no judge run yet")}, '
            f'{judged.get("generated", "never")}). The judge asks, per record: does the subject describe the edited '
            'value (it would move with the edit), does each statement and prompt stand on its own, and does a '
            'question (or a translated name in it) give its answer away. Flags are for a person to confirm.')
    if unclear:
        note += f' {unclear} items got no usable label (UNCLEAR).'
    if pending:
        note += (f' Pending: {len(missing)} never judged, {len(stale)} changed since. Run '
                 '`sbatch datasets/SidsDataset/rule3_judge.sbatch` (one GPU job).')
    judge_row = check('', 'LLM judge: subjects, self-contained statements, answers given away', flagged,
                      status='pending' if pending and not flagged else None, review=True, note=note)
    if pending:
        judge_row['count'] = len(flagged) or pending
    return [
        check('', 'No prompt or subject contains its own answer', found['own'], review=True,
              note='Whole-word match of each expected answer in the question a prompt asks (facts stated before '
                   'the question, quoted words and questions that name their options are skipped), and of the '
                   "old and new value in the edit's subject. Chinese and Spanish prompts are checked the same way; "
                   'names that only imply the answer (土卫六 for Titan) are left to the judge.'),
        check('', 'Statements and prompts stand on their own (no "under those conditions", "the specified", '
                  '"as stated", or mention of the edit)', found['phrases'],
              note='Phrases searched: ' + ', '.join(f'"{p}"' for p in BANNED_PHRASES) + '. In the statement, '
                   'original, premises, every prompt, bridge, revision and side fact, and the audit checks.'),
        check('', 'No subject describes the edited value (wikidata/entities.json)', found['descriptions'],
              review=True,
              note='Subjects entities.json marks as descriptions whose note names the old or new value. '
                   'entities.json was built on older records and matches few current subjects; the judge covers '
                   'the rest.'),
        judge_row,
    ]


def check_locality(recs):
    leaks = []
    for r in recs:
        # Under delete a leak is an abstention, which any near query catches; a
        # near query answered by the removed value (often a premise) is wanted.
        if r['box'] == 'rbox' or r['edit_operation'] == 'delete':
            continue
        # The answer a leak would produce: the edit's new value.
        edited = {norm(r['edit'].get('object')), norm(r['queries']['direct'].get('new_answer'))}
        edited.discard('')
        for q in r['queries']['unrelated_near']:
            if norm(q.get('reference')) in edited:
                leaks.append(f'{r["id"]}: {q["prompt"]!r} -> {q["reference"]!r}')
    return [check('R6. Locality can catch leaks', "Near unrelated answers differ from the edit's new answer", leaks)]


def check_mix(recs):
    s = 'B3. Derivations not dominated by composition'
    der = Counter()
    for r in recs:
        if r['box'] != 'rbox':
            for q in r['queries']['derived']:
                # relation_semantics is optional now; untagged records count only in the total.
                der[(r['box'], r.get('relation_semantics'), q['derivation'])] += 1
    table = [['box', 'derivation', 'queries', 'share', 'associative', 'causal']]
    for box in ('abox', 'tbox'):
        total = sum(n for (b, _, _), n in der.items() if b == box) or 1
        names = sorted({d for (b, _, d) in der if b == box}, key=lambda d: -sum(
            n for (b, _, dd), n in der.items() if b == box and dd == d))
        for d in names:
            a, c = der[(box, 'associative', d)], der[(box, 'causal', d)]
            n = sum(m for (b, _, dd), m in der.items() if b == box and dd == d)
            table.append([box, d, n, f'{n / total:.1%}', a, c])
    # Delete records drop the axiom; they remove the property their replace record flips.
    by_id = {r['id']: r for r in recs}
    rbox = Counter((r['edit_operation'], rbox_property(by_id.get(r['id'].replace('-delete-', '-replace-'), r)))
                   for r in recs if r['box'] == 'rbox')
    rtable = [['RBox property', 'insert', 'replace', 'delete']]
    for p in sorted({p for _, p in rbox}):
        rtable.append([p, rbox[('insert', p)], rbox[('replace', p)], rbox[('delete', p)]])
    misses = []
    for (box, d), share in DERIVATION_TARGETS.items():
        total = sum(n for (b, _, _), n in der.items() if b == box) or 1
        got = sum(n for (b, _, dd), n in der.items() if b == box and dd == d) / total
        if got < share:
            misses.append(f'{box} {d}: {got:.1%} < target {share:.0%}')
    for (op, p), n in RBOX_PROPERTY_TARGETS.items():
        if rbox[(op, p)] != n:
            misses.append(f'rbox {op} {p}: {rbox[(op, p)]} edits, target {n}')
    targets = DERIVATION_TARGETS or RBOX_PROPERTY_TARGETS
    return [
        check(s, 'ABox/TBox derivations meet their targets', misses,
              status=None if targets else 'pending', note='' if targets else 'Targets not agreed yet.', table=table),
        check(s, 'RBox edits by property meet their targets', [], status='pass' if targets else 'pending',
              note='' if targets else 'Targets not agreed yet.', table=rtable),
    ]


# Belief-revision problems (README, Determinacy and belief-revision problems).
# Read off the stored tags: a query's determinacy names its query-level
# problem; the edit's derivability says whether the edit itself is stored or
# derived (the edit-level side of the problem of derived beliefs).
PROBLEMS = (('determinate', 'determinate'), ('background_beliefs', 'background beliefs'),
            ('derived_beliefs', 'derived beliefs'))
STORED = ('very_unlikely', 'unlikely')
DERIVED = ('likely', 'very_likely')
# Per topic, box and operation (replace, and delete mirroring it), 4 edits. ABox: 2 of stored facts and 2 of
# derived ones. ABox and TBox: 2 determinate and 2 indeterminate derived
# queries per edit (TBox: new members named in the prompt, and well-known
# members). RBox: all determinate ("Does it follow that ...?"). Mathematics may
# have every derived query determinate: a number fact leaves no consistent
# world; so may grammar's ABox (word-form edits anchored by firm examples).
# 20 edits per topic and operation. Replace and delete: ABox 0001-0004 and
# 0013-0016, TBox 0005-0008 and 0019-0020, RBox 0009-0012 and 0017-0018.
# Insert: ABox 0001-0008, TBox 0009-0014, RBox 0015-0020.
EDITS_PER_BOX = {'abox': 8, 'tbox': 6, 'rbox': 6}
EDITS_PER_KIND = 4
INDETERMINATE_PER_EDIT = 2
ALL_DETERMINATE = {('mathematics', 'abox'), ('mathematics', 'tbox'), ('grammar', 'abox')}
OPERATIONS = ('replace', 'delete', 'insert')
# Insert (fictional only): which parts are made up, per box and topic. Keys
# joined by '|' count together (a TBox fictional property is a relation or an
# object, whichever the axiom makes it). Inserts that leave no real subject to
# ask about (relation, subject_object, all) may have every derived query
# determinate.
FICTIONAL_MIX = {'abox': {'subject': 2, 'object': 2, 'subject_object': 1, 'relation': 2, 'all': 1},
                 'tbox': {'subject': 2, 'relation|object': 2, 'subject_object|all': 2},
                 'rbox': {'relation': 3, 'all': 3}}
INSERT_ALL_DETERMINATE = ('relation', 'subject_object', 'all')
# A TBox made-up object is a made-up property of a real class: like a made-up
# relation, it leaves no real count or superlative to split on.
INSERT_ALL_DETERMINATE_TBOX = INSERT_ALL_DETERMINATE + ('object',)


def fictional_mix(counts, want):
    """Counts grouped as `want` keys; None when they match."""
    got = {k: sum(counts[x] for x in k.split('|')) for k in want}
    other = sum(counts.values()) - sum(got.values())
    return None if got == want and not other else {**got, **({'other': other} if other else {})}


def memory_chain(rec):
    """An RBox insert whose role chain reaches real knowledge the prompt leaves out."""
    derived = rec['queries']['derived']
    return (rec['edit_operation'] == 'insert' and rec['box'] == 'rbox' and '∘' in rec['edit'].get('axiom', '')
            and all(q.get('bridge') and not q.get('bridge_in_prompt') for q in derived))


def edit_kind(rec):
    """'stored', 'derived' or None (medium or unset) from derivability."""
    d = rec.get('derivability')
    return 'stored' if d in STORED else 'derived' if d in DERIVED else None


def check_problems(recs):
    s = 'B7. Belief-revision problems are covered'
    recs = [r for r in recs if r['edit_operation'] in OPERATIONS]
    boxes, kinds, queries = defaultdict(Counter), defaultdict(Counter), defaultdict(Counter)
    fmix = defaultdict(Counter)
    shape, route = [], []
    for r in recs:
        t, box, kind, op = r['topic'], r['box'], edit_kind(r), r['edit_operation']
        boxes[t][(op, box)] += 1
        derived = r['queries']['derived']
        if box == 'abox' and op != 'insert':
            kinds[t][(op, kind or 'medium')] += 1
        if op == 'insert':
            fmix[(t, box)][r.get('fictional')] += 1
        for q in derived:
            queries[t][q.get('determinacy', 'none')] += 1
        indet = sum(q.get('determinacy') not in (None, 'determinate') for q in derived)
        if box == 'rbox':
            continue
        if (t, box) in ALL_DETERMINATE or (op == 'insert' and r.get('fictional') in
                                             (INSERT_ALL_DETERMINATE_TBOX if box == 'tbox' else INSERT_ALL_DETERMINATE)):
            if indet not in (0, INDETERMINATE_PER_EDIT):
                shape.append(f'{r["id"]}: {indet} indeterminate derived queries (0 or {INDETERMINATE_PER_EDIT} in {t})')
        elif indet != INDETERMINATE_PER_EDIT:
            shape.append(f'{r["id"]}: {indet} indeterminate derived queries, want {INDETERMINATE_PER_EDIT}')
        if box == 'abox' and kind == 'derived' and not any(q.get('premise_route') for q in derived):
            route.append(f'{r["id"]}: derived edit with no premise-route query')
    missing = [f'{t}: {boxes[t][(op, b)]} {op} {b} edits, want {EDITS_PER_BOX[b]}'
               for t in TOPICS for op in OPERATIONS for b in ('abox', 'tbox', 'rbox')
               if boxes[t][(op, b)] != EDITS_PER_BOX[b]]
    missing += [f'{t}: {kinds[t][(op, k)]} {k} {op} ABox edits, want {EDITS_PER_KIND}'
                for t in TOPICS for op in ('replace', 'delete') for k in ('stored', 'derived')
                if kinds[t][(op, k)] != EDITS_PER_KIND]
    mix = [f'{t} insert {b}: {fictional_mix(fmix[(t, b)], want)}, want {want}'
           for t in TOPICS for b, want in FICTIONAL_MIX.items()
           if boxes[t][('insert', b)] and fictional_mix(fmix[(t, b)], want)]
    table = [['topic', 'abox', 'tbox', 'rbox', 'stored', 'derived', *(label for _, label in PROBLEMS)]]
    for t in TOPICS:
        table.append([t, *('/'.join(str(boxes[t][(op, b)]) for op in OPERATIONS) for b in ('abox', 'tbox', 'rbox')),
                      *('/'.join(str(kinds[t][(op, k)]) for op in OPERATIONS) for k in ('stored', 'derived')),
                      *(queries[t][k] for k, _ in PROBLEMS)])
    note = ('Replace and delete records; box and kind columns read replace/delete. Stored ABox edits have '
            'derivability very_unlikely or unlikely, derived ones likely or very_likely. RBox derived queries are '
            'determinate by construction; mathematics, and grammar ABox, may have all derived queries determinate.')
    pending = None if recs else 'pending'
    return [
        check(s, 'Each topic has 8 ABox, 6 TBox and 6 RBox edits under replace, delete and insert, half the '
                 'replace and delete ABox stored and half derived', missing,
              status=pending, note=note, table=table),
        check(s, 'Each ABox and TBox edit has 2 determinate and 2 indeterminate derived queries', shape,
              status=pending),
        check(s, 'Each derived ABox edit has a premise-route query', route, status=pending),
        check(s, 'Each topic has an RBox insert chaining a made-up relation through real knowledge',
              [f'{t}: no RBox insert whose role chain uses a real hop left to the model' for t in TOPICS
               if any(r['topic'] == t and r['edit_operation'] == 'insert' for r in recs)
               and not any(memory_chain(r) for r in recs if r['topic'] == t)], status=pending,
              note='A role chain (axiom with a composition) whose two derived queries both leave a real '
                   'bridge fact to the model (bridge listed, bridge_in_prompt false), checked before editing.'),
        check(s, 'Inserts mix what is made up: subject, object, both, relation, all', mix, status=pending,
              note='Fictional only. ABox: 2 subject, 2 object, 1 subject and object, 2 relation, 1 all; TBox: 2 '
                   'subject, 2 relation or object, 2 subject and object or all; RBox: 3 relation, 3 all. Inserts '
                   'with no real subject or object to ask about may have every derived query determinate.'),
    ]


def newest_audits():
    """{model: (summary, finished)}: each model's newest audit run."""
    newest = {}
    for path in sorted(AUDIT_RUNS.glob('*/summary.json')) if AUDIT_RUNS.is_dir() else []:
        try:
            summary = json.loads(path.read_text())
        except (OSError, ValueError):
            continue
        model, mtime = summary.get('model'), path.stat().st_mtime
        if model and (model not in newest or mtime > newest[model][1]):
            newest[model] = (summary, mtime)
    return newest


def check_audit(recs, audits=None):
    """Section 7: before editing, every main model holds each replace and
    delete fact and none already holds a real insert. The audit's fact
    `known` is its pass rule: 1 means the original is held (replace, delete)
    or the new answer is not (insert)."""
    s = 'R4. The models hold the right things'
    audits = newest_audits() if audits is None else audits
    every = {m: {f['record_id']: f.get('known') for f in audits[m][0].get('facts', [])}
             for m in AUDIT_MODELS + REFERENCE_MODELS if m in audits}
    facts = {m: f for m, f in every.items() if m in AUDIT_MODELS}
    missing_models = [m for m in AUDIT_MODELS if m not in audits]
    table = [['model', 'audited', 'records', 'replace held', 'delete held', 'real insert not held']]
    for m in AUDIT_MODELS + REFERENCE_MODELS:
        name = m if m in AUDIT_MODELS else f'{m} (reference)'
        if m not in audits:
            table.append([name, 'not audited', '', '', '', ''])
            continue
        f, when = every[m], datetime.fromtimestamp(audits[m][1]).strftime('%Y-%m-%d %H:%M')
        row = [name, when, len(f)]
        for op in ('replace', 'delete', 'insert'):
            rs = [r for r in recs if r['edit_operation'] == op and r.get('reality') != 'fictional'
                  and not r['edit'].get('fixture')]
            row.append(f'{sum(f.get(r["id"]) == 1 for r in rs)}/{len(rs)}')
        table.append(row)

    rows = []
    ops = {r['edit_operation'] for r in recs}
    for op, name in (('replace', 'Replace: which models hold the original fact (a tag, not a requirement)'),
                     ('delete', 'Delete: which models hold the fact (a tag, not a requirement)'),
                     ('insert', 'Insert (real): no model already holds the new fact')):
        if op not in ops:
            continue
        failed, unaudited, unclear = [], set(missing_models), []
        for r in recs:
            if r['edit_operation'] != op or r.get('reality') == 'fictional' or r['edit'].get('fixture'):
                continue
            bad = [m for m in facts if facts[m].get(r['id']) == 0]
            vague = [m for m in facts if r['id'] in facts[m] and facts[m][r['id']] is None]
            unaudited |= {m for m in facts if r['id'] not in facts[m]}
            if bad:
                verb = 'already held by' if op == 'insert' else 'not held by'
                failed.append(f'{r["id"]}: {verb} {", ".join(bad)}')
            if vague:
                unclear.append(f'{r["id"]}: judge unclear for {", ".join(vague)}')
        items = failed + unclear
        # Replace and delete: whether each model knew the fact before the edit is
        # recorded for analysis (does prior knowledge change the edit's effect?),
        # not required, so not-held facts are listed as information. A real
        # insert already known by a model is still a failure.
        if op == 'insert':
            status = 'fail' if failed else 'pending' if unaudited or unclear else 'pass'
        else:
            status = 'pending' if unaudited else 'info'
        note = f'Not audited on every record: {", ".join(sorted(unaudited))}.' if unaudited else ''
        rows.append(check(s, name, items, status=status, note=note, table=table if op == 'replace' else None))
    return rows


def check_naming(recs, relations):
    s = 'R7. One name per relation'
    used = defaultdict(list)
    for r in recs:
        used[r['relation']].append(r['id'])
        if r['box'] == 'rbox':
            for name in IDENT.findall(r['edit'].get('axiom') or ''):
                if name not in DL_WORDS and r['id'] not in used[name]:
                    used[name].append(r['id'])
    # Names that may be one relation spelled twice: equal once has_/is_ are dropped.
    stem = defaultdict(set)
    for n in set(used) | set(relations):
        stem[re.sub(r'^(has|is)_', '', n)].add(n)
    return [
        check(s, 'Relation names are snake_case', [f'{n} ({", ".join(v[:3])})' for n, v in sorted(used.items())
                                                   if not SNAKE.fullmatch(n)]),
        check(s, 'Every relation is in RELATIONS.md', [f'{n} ({", ".join(v[:3])})' for n, v in sorted(used.items())
                                                       if n not in relations]),
        check(s, 'No relation under two names', [' / '.join(sorted(v)) for v in stem.values() if len(v) > 1],
              review=True),
    ]


def check_reuse(recs):
    far = Counter(q['prompt'] for r in recs for q in r['queries'].get('unrelated_far') or [])
    return [check('B6. Far locality prompts vary', f'No far unrelated prompt used more than {MAX_FAR_REUSE} times',
                  [f'{n}x {p}' for p, n in far.most_common() if n > MAX_FAR_REUSE],
                  note=f'{len(far)} distinct far prompts over {sum(far.values())} queries.')]


# Manual rules: their statement and guidance are read from CRITERIA.md, the
# one place they are written. Each reviewer marks each record, per manual
# rule, and each of its queries green (fine) or red (flagged; an optional
# note and kind, problem or angle, from the CLI); no mark is yellow.
# Marks live in reviews.json, which is tracked, so a push shares them.
CRITERIA_PATH = ROOT / 'CRITERIA.md'
MANUAL_RULE_RE = re.compile(r'^\*\*Rule (\d+)\. (.+?)\*\* \(`([a-z0-9-]+)`\)\.\s*(.*)$')


def parse_criteria(text=None):
    """{'rules': [{'number', 'key', 'title', 'statement', 'guide'}]} from
    CRITERIA.md's "Manual rules" section: the rule paragraph is the
    statement, a <details> block after it the guidance (Markdown; '' when the
    rule has none)."""
    text = CRITERIA_PATH.read_text() if text is None else text
    lines = text.split('\n')
    try:
        start = lines.index('## Manual rules')
    except ValueError:
        return {'rules': []}
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith('## ')), len(lines))
    rules, rule, mode = [], None, None   # mode: 'statement', 'details' or None
    for line in lines[start + 1:end]:
        m = MANUAL_RULE_RE.match(line)
        stripped = line.strip()
        if m and mode != 'details':
            rule = {'number': int(m.group(1)), 'title': m.group(2).strip(), 'key': m.group(3),
                    'statement': [m.group(4)], 'guide': []}
            rules.append(rule)
            mode = 'statement'
        elif rule is None:
            continue
        elif stripped == '<details>' or stripped.startswith('<details'):
            mode = 'details'
        elif stripped == '</details>':
            mode = None
        elif mode == 'details':
            if not stripped.startswith('<summary'):
                rule['guide'].append(line)
        elif mode == 'statement':
            if stripped:
                rule['statement'].append(stripped)
            else:
                mode = None
    return {'rules': [{**r, 'statement': ' '.join(' '.join(r['statement']).split()),
                       'guide': '\n'.join(r['guide']).strip()} for r in rules]}


try:
    MANUAL = parse_criteria()
except OSError:
    MANUAL = {'rules': []}
# (key, title, statement), in rule order.
MANUAL_RULES = tuple((r['key'], r['title'], r['statement']) for r in MANUAL['rules'])

REVIEWS_PATH = ROOT / 'reviews.json'
REVIEWS_LOCK = ROOT / '.reviews.lock'
REVIEWS_VERSION = 4
# (id, name, kind), in the order their dots are shown. Agents mark as
# themselves only (the dashboard's agent token can act as an agent reviewer,
# the user's token as a person).
REVIEWERS = (('codex', 'Codex', 'agent'), ('claude', 'Claude', 'agent'), ('mustafa', 'Mustafa', 'human'),
             ('fengchun', 'Fengchun', 'human'), ('adarsh', 'Adarsh', 'human'))
REVIEWER_IDS = tuple(r[0] for r in REVIEWERS)
STATES = ('green', 'red')   # no mark: yellow (not reviewed yet)
KINDS = ('problem', 'angle')  # optional on a red mark (CLI): a problem, or an angle to add or drop


def _hash(text):
    import hashlib
    return hashlib.sha256(text.encode()).hexdigest()


def record_hash(rec):
    """A record's content, so a mark can tell whether the record changed since."""
    return _hash(json.dumps(rec, ensure_ascii=False, sort_keys=True))[:12]


def query_keys(rec):
    """Each query's review key, the same as the model audit's (and the
    dashboard's): direct, paraphrase, cross_lingual[zh], propositional[1],
    unrelated_near[0], unrelated_far[0], derived[2]."""
    out = []
    for qtype in ('direct', 'paraphrase', 'cross_lingual', 'propositional', 'unrelated_near', 'unrelated_far',
                  'derived'):
        items = rec['queries'].get(qtype)
        for i, q in enumerate(items if isinstance(items, list) else [items] if items else []):
            out.append(qtype if qtype in ('direct', 'paraphrase') else
                       f'cross_lingual[{q.get("language")}]' if qtype == 'cross_lingual' else f'{qtype}[{i}]')
    return out


def _clean_mark(m):
    if not isinstance(m, dict) or m.get('state') not in STATES or m.get('kind') not in KINDS + (None,):
        return None
    return m


def migrate_reviews(data):
    """reviews.json in the current shape: {'version': 4, 'marks': {record_id:
    {item: {reviewer: mark}}}}, an item being a manual rule's key (the record
    as a whole) or a query key. Version 3 flags (record, rule, reviewer,
    kind, comment) become red marks; older shapes are dropped."""
    data = data if isinstance(data, dict) else {}
    out = {'version': REVIEWS_VERSION, 'marks': {}}
    rules = {k for k, *_ in MANUAL_RULES}
    if data.get('version') == 3:
        for rid, flags in (data.get('flags') or {}).items():
            for f in flags or []:
                if not (isinstance(f, dict) and f.get('rule') in rules and f.get('reviewer') in REVIEWER_IDS):
                    continue
                by = out['marks'].setdefault(rid, {}).setdefault(f['rule'], {})
                old = by.get(f['reviewer'])
                kind = f.get('kind') if f.get('kind') in KINDS else 'problem'
                if old:  # several flags by one reviewer on one rule: one red mark
                    old['comment'] = ' | '.join(x for x in (old['comment'], f.get('comment')) if x)
                    old['kind'] = 'problem' if 'problem' in (old['kind'], kind) else 'angle'
                else:
                    by[f['reviewer']] = {'state': 'red', 'kind': kind, 'comment': f.get('comment') or '', 'at': f.get('at'),
                                         'record_hash': f.get('record_hash')}
        return out
    if data.get('version') != REVIEWS_VERSION:
        return out
    for rid, items in (data.get('marks') or {}).items():
        for item, by in (items or {}).items():
            for who, m in (by or {}).items():
                if who in REVIEWER_IDS and _clean_mark(m):
                    out['marks'].setdefault(rid, {}).setdefault(item, {})[who] = m
    return out


def load_reviews(path=None):
    try:
        raw = json.loads(Path(path or REVIEWS_PATH).read_text())
    except (OSError, ValueError):
        raw = {}
    return migrate_reviews(raw)


def _write_reviews(data, path):
    import os
    import tempfile
    path = Path(path)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix='.reviews.', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=1) + '\n')
        os.chmod(tmp, 0o664)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def update_reviews(change, path=None, lock=None):
    """Read reviews.json, apply change(data), write it back atomically, all
    under an exclusive lock so concurrent writers (the dashboard, the CLI)
    never lose each other's marks. Returns change's result."""
    import fcntl
    import os
    path, lock = Path(path or REVIEWS_PATH), Path(lock or REVIEWS_LOCK)
    with os.fdopen(os.open(lock, os.O_RDWR | os.O_CREAT, 0o664), 'r+') as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        try:
            data = load_reviews(path)
            result = change(data)
            _write_reviews(data, path)
            return result
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN)


def set_mark(record_id, item, reviewer, state, comment='', kind=None, recs=None, path=None, lock=None):
    """One reviewer's mark on one item of a record: a manual rule's key (the
    record as a whole) or a query key. state: green (fine), red (flagged) or
    None (back to not reviewed). A note (comment) and, for red, a kind
    (problem or angle) are optional. Returns the record's marks."""
    if reviewer not in REVIEWER_IDS:
        raise ValueError(f'unknown reviewer {reviewer!r} (one of {", ".join(REVIEWER_IDS)})')
    if state not in STATES + (None,):
        raise ValueError('state must be green, red or clear')
    comment = (comment or '').strip()
    if kind not in KINDS + (None,):
        raise ValueError(f'kind must be one of {", ".join(KINDS)}')
    recs = load_records() if recs is None else recs
    rec = next((r for r in recs if r['id'] == record_id), None)
    if rec is None:
        raise ValueError(f'unknown record {record_id!r}')
    items = [k for k, *_ in MANUAL_RULES] + query_keys(rec)
    if item not in items:
        raise ValueError(f'unknown item {item!r} for {record_id} (one of {", ".join(items)})')

    def change(data):
        by = data['marks'].setdefault(record_id, {}).setdefault(item, {})
        if state is None:
            by.pop(reviewer, None)
        else:
            mark = {'state': state, 'at': datetime.now().isoformat(timespec='seconds'), 'record_hash': record_hash(rec)}
            if comment:
                mark['comment'] = comment
            if state == 'red' and kind:
                mark['kind'] = kind
            by[reviewer] = mark
        if not by:
            data['marks'][record_id].pop(item)
        if not data['marks'][record_id]:
            data['marks'].pop(record_id)
        return data['marks'].get(record_id, {})
    return update_reviews(change, path, lock)


def review_state(recs, data=None):
    """What the dashboard needs: the manual rules with their guidance, the
    reviewers in dot order, and every mark on a current record (each marked
    `stale` when its record changed since)."""
    data = load_reviews() if data is None else data
    hashes = {r['id']: record_hash(r) for r in recs}
    marks = {rid: {item: {who: {**m, 'stale': m.get('record_hash') not in (None, hashes[rid])}
                          for who, m in by.items()} for item, by in items.items()}
             for rid, items in data['marks'].items() if rid in hashes}
    return {'rules': [dict(r) for r in MANUAL['rules']],
            'reviewers': [{'id': i, 'name': n, 'kind': k} for i, n, k in REVIEWERS],
            'states': list(STATES), 'kinds': list(KINDS), 'marks': marks}


def _summary(units, marks, names):
    """units: [(record_id, item)]. Per reviewer green/red/yellow, and the red
    items with their comments."""
    per = {n: Counter() for n in names.values()}
    red = []
    for rid, item in units:
        by = (marks.get(rid) or {}).get(item) or {}
        for who, name in names.items():
            per[name][by[who]['state'] if who in by else 'yellow'] += 1
        reds = [{'reviewer': names[w], **m} for w, m in by.items() if m['state'] == 'red']
        if reds:
            red.append({'record': rid, 'item': item, 'marks': reds})
    return ({name: {s: c[s] for s in ('green', 'red', 'yellow')} for name, c in per.items()}, red)


def manual_checks(recs, data=None):
    """Informational rows: one per manual rule (record-level marks), then one
    for the per-question marks. Each has green,
    red and yellow counts per reviewer and the red items with comments."""
    state = review_state(recs, data)
    names = {i: n for i, n, _ in REVIEWERS}
    out = []
    for rule in MANUAL['rules']:
        per, red = _summary([(r['id'], rule['key']) for r in recs], state['marks'], names)
        c = check(rule['title'], rule['title'], _red_items(red), status='manual', note=rule['statement'])
        c.update(rule=rule['key'], guide=rule['guide'], reviews={'unit': 'records', 'total': len(recs),
                                                                 'by_reviewer': per, 'red': red})
        out.append(c)
    units = [(r['id'], k) for r in recs for k in query_keys(r)]
    per, red = _summary(units, state['marks'], names)
    c = check('Edits and questions', 'Each edit and question, reviewed one by one', _red_items(red), status='manual',
              note='Reviewers mark every query of a record green (fine) or red (flagged), beside its audit dots.')
    c.update(rule='questions', guide='', reviews={'unit': 'questions', 'total': len(units), 'by_reviewer': per,
                                                  'red': red})
    out.append(c)
    return out, state


def _red_items(red):
    def one(m):
        kind = f' ({m["kind"]})' if m.get('kind') else ''
        return m['reviewer'] + kind + (f': {m["comment"]}' if m.get('comment') else '')
    return [f'{x["record"]} {x["item"]}: red by ' + ', '.join(one(m) for m in x['marks']) for x in red]


# Rule 5: what counts as enough evidence (README, Evidence).
STORED_MIN_COUNT = 100     # an exact-phrase count at least this high, or a quoted sentence
DERIVED_MIN_SOURCES = 2    # corpus counts or searches showing the direct form is rare
FICTIONAL_MAX_COUNT = 5    # a made-up name should be (nearly) absent from text


def check_evidence(recs):
    weak = []
    for r in recs:
        for fact, e in (r.get('evidence') or {}).items():
            srcs = e.get('sources') or []
            counts = [x for x in srcs if x.get('kind') == 'infini-gram']
            if e.get('claim') == 'definitional':
                continue
            if e.get('claim') == 'fictional':
                ok = any((x.get('count') if x.get('count') is not None else 99) <= FICTIONAL_MAX_COUNT for x in counts) \
                    and any(x.get('kind') == 'search' for x in srcs)
                if not ok:
                    weak.append(f'{r["id"]}: fictional {fact!r}: needs a corpus count of at most '
                                f'{FICTIONAL_MAX_COUNT} for the made-up name and a search')
                continue
            if e.get('claim') == 'false':
                # A deliberately false fact (an "or" side fact): a quoted source for the true counterpart.
                ok = any(x.get('kind') in ('wikipedia', 'web') and x.get('quote') for x in srcs)
                if not ok:
                    weak.append(f'{r["id"]}: false {fact!r}: needs a quoted source showing what is true instead')
                continue
            if e.get('claim') == 'stored':
                ok = any(x.get('kind') in ('wikipedia', 'web') and x.get('quote') for x in srcs) or \
                     any((x.get('count') or 0) >= STORED_MIN_COUNT for x in counts)
                why = f'no quote and no count >= {STORED_MIN_COUNT}'
            else:
                ok = len(counts) + sum(x.get('kind') == 'search' for x in srcs) >= DERIVED_MIN_SOURCES
                why = f'fewer than {DERIVED_MIN_SOURCES} counts or searches'
            if not ok:
                weak.append(f'{r["id"]}: {e.get("claim")} {fact!r}: {why}')
    n = sum(len(r.get('evidence') or {}) for r in recs)
    note = (f'{n} evidence entries. Stored: a quoted sentence, or an exact-phrase count of at least '
            f'{STORED_MIN_COUNT}. Derived: at least {DERIVED_MIN_SOURCES} corpus counts or searches. The validator '
            'already requires an entry for every edited fact and premise.')
    return [check('', 'Every stored and derived claim has enough evidence', weak, note=note),
            check_supporting_evidence(recs)]


def check_supporting_evidence(recs):
    """Rule 1 support: bridge facts, revision facts and propositional side
    facts that have no evidence entry yet (a source backing that they are
    true). Report only until the evidence pass covers them; checks in the
    model audit say whether models know a fact, not whether it is true."""
    missing, counts = [], {}
    for r in recs:
        ev = r.get('evidence') or {}
        facts = [('bridge', b) for q in r['queries'].get('derived', []) if not q.get('bridge_in_prompt')
                 for b in q.get('bridge') or []]
        facts += [('revision fact', b) for q in r['queries'].get('derived', []) if not q.get('revision_in_prompt')
                  for b in q.get('revision_facts') or []]
        facts += [('side fact', p['side_fact']) for p in r['queries'].get('propositional') or [] if p.get('side_fact')]
        for kind, fact in dict.fromkeys(facts):
            have, total = counts.get(kind, (0, 0))
            counts[kind] = (have + (fact in ev), total + 1)
            if fact not in ev:
                missing.append(f'{r["id"]}: {kind} {fact!r}')
    note = 'With evidence: ' + ', '.join(f'{k} {h}/{t}' for k, (h, t) in counts.items()) + \
           '. A source (quote, Wikipedia citation, corpus count) backs that the fact is true.'
    return check('', 'Evidence for bridge, revision and side facts (Rule 1 support)', missing,
                 status=None if not missing else 'pending', note=note)


# Rule 12: minimum coverage of relation properties, counted on replace
# records (deletes mirror them). ABox derived queries that use a property,
# and RBox edits that change one. Raise these as records are added.
ABOX_PROPERTY_MIN = {'transitivity': 10, 'chain': 10, 'subproperty': 10, 'functional': 10, 'inheritance': 10}
RBOX_PROPERTY_MIN = {'transitivity': 3, 'symmetry': 3, 'inverse': 3, 'subproperty': 3, 'chain': 8,
                     'functional': 8}
RBOX_GROUP = {'transitive': 'transitivity', 'symmetric': 'symmetry', 'asymmetric': 'symmetry',
              'inverse': 'inverse', 'subproperty': 'subproperty', 'chain': 'chain', 'functional': 'functional'}


# Properties of the edited relation itself (tags in RELATIONS.md), as opposed
# to how queries are derived. "none": the relation has no property that
# licenses a derivation. Some edits should be on such relations (a property-
# free fact is a real case), but not too many.
RELATION_PROPERTIES = ('symmetric', 'asymmetric', 'inverse', 'transitive', 'chain', 'subproperty', 'functional')
NONE_SHARE = (0.05, 0.25)   # share of ABox + TBox replace edits whose relation has no property
# How derived queries are derived, grouped for reading. Composition is a role
# chain built for one question; `chain` is one declared on the relation.
DERIVATION_GROUPS = (
    ('relation property', ('symmetry', 'asymmetry', 'inverse', 'transitivity', 'subproperty', 'functional')),
    ('chain', ('chain', 'composition')),
    ('class', ('inheritance', 'instantiation')),
    ('premise of a derived edit', ('premise',)),
    ('task framing', ('binding', 'application', 'scope')),
)


def relation_props(relations, name):
    tags = relations.get(name, (frozenset(), False))[0]
    return {t.split(':')[0] for t in tags} & set(RELATION_PROPERTIES)


def check_coverage(recs, relations):
    reps = [r for r in recs if r['edit_operation'] == 'replace']
    boxes = ('abox', 'tbox', 'rbox')

    # 1. Properties of the edited relations, with "none".
    props, total = Counter(), Counter(r['box'] for r in reps)
    for r in reps:
        p = relation_props(relations, r['relation'])
        for k in p or {'none'}:
            props[(k, r['box'])] += 1
    ptable = [['property of the edited relation', *boxes, 'all']]
    for k in (*RELATION_PROPERTIES, 'none'):
        ptable.append([k, *(props[(k, b)] for b in boxes), sum(props[(k, b)] for b in boxes)])
    ptable.append(['records', *(total[b] for b in boxes), sum(total.values())])
    at = total['abox'] + total['tbox']
    none = props[('none', 'abox')] + props[('none', 'tbox')]
    share = none / at if at else 0
    lo, hi = NONE_SHARE
    off = [] if not at or lo <= share <= hi else [
        f'{none} of {at} ABox and TBox edits ({share:.0%}) are on relations with no property; want {lo:.0%} to {hi:.0%}']

    # 2. How derived queries are derived, grouped.
    der = Counter((r['box'], q['derivation']) for r in reps for q in r['queries']['derived'])
    n_all = sum(der.values()) or 1
    dtable = [['group', 'derivation', *boxes, 'share']]
    for group, names in DERIVATION_GROUPS:
        g = sum(der[(b, d)] for b in boxes for d in names)
        dtable.append([group, '(all)', *(sum(der[(b, d)] for d in names) for b in boxes), f'{g / n_all:.1%}'])
        for d in names:
            n = sum(der[(b, d)] for b in boxes)
            if n:
                dtable.append(['', d, *(der[(b, d)] for b in boxes), f'{n / n_all:.1%}'])
    short = [f'ABox {d}: {der[("abox", d)]} queries, want at least {k}'
             for d, k in ABOX_PROPERTY_MIN.items() if der[('abox', d)] < k]

    # 3. Which property each RBox edit changes.
    rb = Counter(RBOX_GROUP.get(rbox_property(r), rbox_property(r)) for r in reps if r['box'] == 'rbox')
    rtable = [['RBox property edited', 'edits', 'minimum']] + [[p, rb[p], k] for p, k in RBOX_PROPERTY_MIN.items()]
    rshort = [f'RBox {p}: {rb[p]} edits, want at least {k}' for p, k in RBOX_PROPERTY_MIN.items() if rb[p] < k]
    return [
        check('', 'Edited relations: properties, and how many have none', off, table=ptable,
              note='What the edited relation itself carries (tags in RELATIONS.md); a relation can have several. '
                   f'"none": no property that licenses a derivation. Replace records; ABox and TBox edits on such '
                   f'relations should be {lo:.0%} to {hi:.0%} (RBox edits always have one).'),
        check('', 'Derived queries use every relation property', short, table=dtable,
              note='How each derived query reaches its answer, grouped. Chain: declared role chains and composition '
                   '(a chain built for one question). Task framing sorts by what the question asks the model to do; '
                   'the logic underneath is in each query\'s logic label. Minimums apply to ABox queries.'),
        check('', 'RBox edits cover every relation property', rshort, table=rtable),
    ]


# Rule 13: every core method runs on every edit, on the four main models.
RUN_EXPERIMENT = ROOT.parent.parent / 'experiments' / 'run_experiment'
SMOKE_RUNS = ROOT.parent.parent / 'results' / 'sids_smoke' / 'runs'
SMOKE_MODELS = AUDIT_MODELS


def core_methods():
    spec = json.loads((RUN_EXPERIMENT / 'dashboard.json').read_text())
    field = next(x for x in spec['fields'] if x['name'] == 'method')
    return [m['value'] for c in field['categories'] for m in c['methods'] if m.get('core')]


def hparams_dir(method):
    src = (RUN_EXPERIMENT / 'run_experiment.py').read_text()
    m = re.search(r'"%s":\s*"([^"]+)"' % re.escape(method), src.split('METHOD_HPARAMS_DIR = {', 1)[1].split('}', 1)[0])
    return m.group(1) if m else None


def check_methods_run(recs):
    sys.path.insert(0, str(RUN_EXPERIMENT))
    import sids_requests
    methods = core_methods()
    edits = [r for r in recs if r['edit_operation'] in ('replace', 'delete', 'insert')]
    fails = sids_requests.preflight(edits, methods)
    by_record = defaultdict(list)
    for (rid, m), msg in sorted(fails.items()):
        by_record[(rid, msg.split(': ', 2)[-1])].append(m)
    data_items = [f'{rid} [{", ".join(ms)}]: {msg}' for (rid, msg), ms in sorted(by_record.items())]
    for m in methods:
        d = hparams_dir(m)
        for model in SMOKE_MODELS:
            if not d or not (RUN_EXPERIMENT / 'hparams' / d / f'{model}.yaml').exists():
                data_items.append(f'{m} on {model}: no hparams file')
    by_err = Counter(msg.split(':', 1)[0] for msg in fails.values())
    note1 = (f'{len(methods)} core methods ({", ".join(methods)}) x {len(edits)} records x {len(SMOKE_MODELS)} models, '
             'checked without a GPU: each record becomes an edit request (prompt = direct question, target = new '
             "answer, or \"I don't know\" for delete), and methods that edit at the subject need it verbatim, once, "
             'in the prompt. ' + (f'Failures by kind: {dict(by_err)}.' if by_err else ''))

    current = sids_requests.records_hash(edits)
    smoke_items, missing, stale = [], [], []
    table = [['method', *SMOKE_MODELS]]
    for m in methods:
        row = [m]
        for model in SMOKE_MODELS:
            path = SMOKE_RUNS / f'smoke_{m}_{model}' / 'summary.json'
            try:
                summary = json.loads(path.read_text())
            except (OSError, ValueError):
                missing.append(f'{m} on {model}')
                row.append('not run')
                continue
            if summary.get('crashed'):
                smoke_items.append(f'{m} on {model}: crashed (exit {summary.get("exit_code")})')
                row.append('crashed')
            elif summary.get('records_hash') != current:
                stale.append(f'{m} on {model}')
                row.append('stale')
            else:
                row.append(f'{summary.get("ok", 0)}/{summary.get("records", 0)}')
                if summary.get('error'):
                    errs = [json.loads(l) for l in (path.parent / 'smoke.jsonl').read_text().splitlines() if l.strip()]
                    smoke_items += [f'{m} on {model}: {e["record"]}: {e.get("error")}: {e.get("message")}'
                                    for e in errs if e.get('status') == 'error']
    status = 'fail' if smoke_items else 'pending' if missing or stale else 'pass'
    note2 = ('From the Method smoke run on gaivi (results/sids_smoke): each core method applied to each record, '
             'checked to edit real weights, stay finite, keep generating and restore exactly. '
             + (f'Not run: {len(missing)} method-model pairs. ' if missing else '')
             + (f'Stale (records changed since): {len(stale)}. ' if stale else ''))
    return [
        check('', 'Every core method can take every record (data checks)', data_items, note=note1),
        check('', 'Every core method ran on every edit, on all four models (smoke run)', smoke_items,
              status=status, note=note2, table=table),
    ]


# Automated rules, in order. The delete rule comes last.
AUTOMATED_RULES = (
    ('Stable subjects, self-contained statements', lambda recs, rel: check_rule3(recs)),
    ('No repeated edits', lambda recs, rel: check_repeats(recs)),
    ('Enough evidence for every fact', lambda recs, rel: check_evidence(recs)),
    ('What the models know is recorded', lambda recs, rel: check_audit(recs)),
    ('Locality can catch leaks', lambda recs, rel: check_locality(recs)),
    ('One name per relation', lambda recs, rel: check_naming(recs, rel)),
    ('Yes/no answers balanced in RBox', lambda recs, rel: check_yes_no(recs) + check_propositional(recs)),
    ('Far locality prompts vary', lambda recs, rel: check_reuse(recs)),
    ('Belief-revision problems are covered', lambda recs, rel: check_problems(recs)),
    ('Relation properties are covered', lambda recs, rel: check_coverage(recs, rel)),
    ('Every method runs on every edit', lambda recs, rel: check_methods_run(recs)),
    ('Delete means "I don\'t know"', lambda recs, rel: check_delete(recs)),
)


# Rule 1 support: the formal check of the description-logic reasoning
# (reason.py, HermiT over owl/formal/<id>.json; owl/README.md). Read only.
FORMAL_REPORT = ROOT / 'owl' / 'reason_report.json'
FORMAL_CHECKS = ('derived_edit', 'pre', 'post_determinate', 'consistent', 'post_worlds', 'differ',
                 'missing_worlds', 'not_checked', 'encoding', 'error')


def check_formal(recs):
    """Rows for Rule 1 from owl/reason_report.json: counts per check, the
    failing records and queries (a person decides whether the record or the
    encoding is wrong), and how many records have no formal file yet."""
    ids = {r['id'] for r in recs}
    formal_dir = ROOT / 'owl' / 'formal'
    have = {p.stem for p in formal_dir.glob('*.json')} & ids if formal_dir.exists() else set()
    pending = sorted(ids - have)
    by_topic = Counter(i.split('-')[0] for i in pending)
    pending_row = check('Formal encodings', 'Records without a formal encoding (owl/formal/)', [],
                        status='pending' if pending else 'pass',
                        note=f'{len(pending)} of {len(ids)} records pending: '
                             + ', '.join(f'{t} {n}' for t, n in sorted(by_topic.items())) if pending
                        else f'all {len(ids)} records encoded')
    pending_row['count'] = len(pending)
    try:
        rep = json.loads(FORMAL_REPORT.read_text())
    except (OSError, ValueError):
        return [check('Formal check', 'Formal check with HermiT (reason.py)', status='pending',
                      note='owl/reason_report.json not found: run reason.py'), pending_row]
    records = {k: v for k, v in rep.get('records', {}).items() if k in ids}
    counts = defaultdict(Counter)
    failing = []
    for rid, r in sorted(records.items()):
        for c in r.get('checks', []):
            counts[c['check']][c['status']] += 1
            if c['status'] == 'fail':
                q = f' q{c["q"]}' if 'q' in c else ''
                failing.append(f'{rid} {c["check"]}{q}: {c.get("detail", "")[:300]}')
    table = [('check', 'pass', 'fail', 'not_checked')] + [
        (c, counts[c]['pass'], counts[c]['fail'], counts[c]['not_checked'])
        for c in FORMAL_CHECKS if counts.get(c)]
    stale = [rid for rid in records if rid in have and
             (formal_dir / f'{rid}.json').stat().st_mtime > FORMAL_REPORT.stat().st_mtime]
    note = (f'{len(records)} records checked ({rep.get("generated", "?")}). A failure is either a wrong '
            'label, world, answer or premise in the record, or an encoding mistake.')
    if stale:
        note += f' {len(stale)} formal files changed since the report: rerun reason.py.'
    row = check('Formal check', 'Formal check with HermiT (reason.py)', failing, review=True, note=note,
                table=table)
    return [row, pending_row, check_justifications(ids)]


# Rule 1 support: justifications (justify.py): which axioms each checked
# derived answer follows from, against the record's derivation, bridge, hops
# and via. Read only.
JUSTIFY_REPORT = ROOT / 'owl' / 'justifications.json'
JUSTIFY_VERDICTS = ('match', 'partial', 'mismatch', 'not_checked')
JUSTIFY_FLAGS = ('no_edit', 'ambiguous', 'capped')
# Added with revision facts and alt_derivations (justify.py): counted too, and
# listed except alternatives_listed (a match).
JUSTIFY_NEW_FLAGS = ('alternatives_listed', 'revision_as_bridge', 'stale')


def check_justifications(ids):
    """One row from owl/justifications.json: counts per verdict and flag, and
    the partial, mismatched, edit-free and ambiguous queries."""
    try:
        rep = json.loads(JUSTIFY_REPORT.read_text())
    except (OSError, ValueError):
        return check('Formal check', 'Derivation metadata matches the justifications (justify.py)',
                     status='pending', note='owl/justifications.json not found: run justify.py')
    counts, items = Counter(), []
    for rid, r in sorted(rep.get('records', {}).items()):
        if rid not in ids:
            continue
        for q in r.get('queries', []):
            counts[q['verdict']] += 1
            tag = f'{rid} q{q["q"]} ({q.get("derivation")})'
            if q['verdict'] in ('partial', 'mismatch'):
                b = q.get('best') or {}
                why = []
                if not b.get('derivation_ok', True):
                    why.append('justification uses ' + (', '.join(b.get('types') or []) or 'no property'))
                if b.get('missing_bridge'):
                    why.append('bridge not needed: ' + ' | '.join(b['missing_bridge']))
                if b.get('unlisted'):
                    why.append('needs unlisted ' + ', '.join(b['unlisted']))
                if not b.get('hops_ok', True):
                    why.append(f'hops {b.get("hops")} vs {q.get("record", {}).get("hops")}')
                if b.get('revision_as_bridge'):
                    why.append('revision fact used to build the answer (should be a bridge): '
                               + ' | '.join(b['revision_as_bridge']))
                items.append(f'{q["verdict"]} {tag}: ' + '; '.join(why))
            for f in JUSTIFY_FLAGS:
                if q.get(f):
                    counts[f] += 1
                    if f != 'capped':
                        items.append(f'{f} {tag}')
            for f in JUSTIFY_NEW_FLAGS:
                if q.get(f) or (q.get('best') or {}).get(f):
                    counts[f] += 1
                    if f == 'stale':
                        items.append(f'stale {tag}: rerun justify.py')
    table = [('verdict / flag', 'queries')] + [(k, counts.get(k, 0))
                                               for k in JUSTIFY_VERDICTS + JUSTIFY_FLAGS + JUSTIFY_NEW_FLAGS]
    note = (f'{rep.get("generated", "?")}: per checked derived query, a minimal set of axioms the answer follows '
            'from, mapped to a derivation type, bridge facts and hops (owl/README.md, Justifications). '
            'partial: derivation right, bridges or hops differ; mismatch: the derivation type is not used; '
            'no_edit: the answer follows without the edit; ambiguous: alternative derivations; '
            'alternatives_listed: a match whose alternative routes are in alt_derivations; '
            'revision_as_bridge: a revision fact every justification uses (should be a bridge); '
            'stale: stored justifications no longer fit the record (justify.py, or --recompare after edits).')
    return check('Formal check', 'Derivation metadata matches the justifications (justify.py)', items,
                 review=True, note=note, table=table)


# Rule 1 support, continued: the Z3 check of the fol queries (fol_check.py,
# the `fol` sections of owl/formal/<id>.json) and which checker covers each
# derived query (owl/coverage_labels.py). Read only.
FOL_REPORT = ROOT / 'owl' / 'fol_report.json'
FOL_CHECKS = ('pre', 'post_determinate', 'post_worlds', 'differ', 'consistent', 'not_checked', 'encoding', 'error')


def check_fol(recs):
    """Rows for Rule 1 from owl/fol_report.json (counts per check, failing
    items) and the checker coverage split (dl via HermiT, fol via Z3)."""
    ids = {r['id'] for r in recs}
    rows = []
    try:
        rep = json.loads(FOL_REPORT.read_text())
    except (OSError, ValueError):
        rep = None
    if rep is None:
        rows.append(check('Formal check', 'Formal check of fol queries with Z3 (fol_check.py)', status='pending',
                          note='owl/fol_report.json not found: run fol_check.py'))
    else:
        records = {k: v for k, v in rep.get('records', {}).items() if k in ids}
        counts, failing = defaultdict(Counter), []
        for rid, r in sorted(records.items()):
            for c in r.get('checks', []):
                counts[c['check']][c['status']] += 1
                if c['status'] == 'fail':
                    q = f' q{c["q"]}' if 'q' in c else ''
                    failing.append(f'{rid} {c["check"]}{q}: {c.get("detail", "")[:300]}')
        table = [('check', 'pass', 'fail', 'not_checked')] + [
            (c, counts[c]['pass'], counts[c]['fail'], counts[c]['not_checked'])
            for c in FOL_CHECKS if counts.get(c)]
        formal_dir = ROOT / 'owl' / 'formal'
        stale = [rid for rid in records if (formal_dir / f'{rid}.json').exists() and
                 (formal_dir / f'{rid}.json').stat().st_mtime > FOL_REPORT.stat().st_mtime]
        note = (f'{len(records)} records checked ({rep.get("generated", "?")}); each pass comes with its unsat '
                'core (the facts that force the answer). A failure is a wrong answer or world in the record, '
                'or an encoding mistake.')
        if stale:
            note += f' {len(stale)} formal files changed since the report: rerun fol_check.py.'
        rows.append(check('Formal check', 'Formal check of fol queries with Z3 (fol_check.py)', failing,
                          review=True, note=note, table=table))
    sys.path.insert(0, str(ROOT / 'owl'))
    import coverage_labels as CV
    split = Counter()
    for r in recs:
        for l in CV.query_labels(r):
            split[(l['logic'], l['checker'])] += 1
    logics = sorted({k[0] for k in split}, key=str)
    table = [('logic', 'hermit', 'z3', 'none')] + [
        (str(lg), split[(lg, 'hermit')], split[(lg, 'z3')], split[(lg, 'none')]) for lg in logics]
    unchecked = sum(v for (lg, c), v in split.items() if c == 'none')
    rows.append(check('Formal check', 'Checker coverage: dl via HermiT, fol via Z3 (owl/COVERAGE.md)',
                      status='pending' if unchecked else 'pass', table=table,
                      note=f'{unchecked} derived queries have no checker yet' if unchecked
                      else 'every derived query is checked'))
    rows[-1]['count'] = unchecked
    return rows


def report():
    recs = load_records()
    relations, _ = load_relations()
    checks, n = [], 0
    manual, state = manual_checks(recs)
    for c in manual:
        if c['rule'] != 'questions':   # the per-question row has no rule number
            n += 1
            c['section'] = f'Rule {n}. {c["section"]}'
        c['kind'] = 'manual'
        checks.append(c)
        # The machine checks of the logic behind the worlds Rule 1 asks about
        # (entailment, determinacy, missing minimal revisions) sit under it.
        if c.get('rule') == 'clear-and-sensible':
            for f in check_formal(recs) + check_fol(recs):
                f['section'], f['kind'] = c['section'], 'automated'
                checks.append(f)
    for title, run in AUTOMATED_RULES:
        n += 1
        for c in run(recs, relations):
            c['section'], c['kind'] = f'Rule {n}. {title}', 'automated'
            checks.append(c)
    review = {'reviewers': state['reviewers'], 'kinds': state['kinds']}
    return {'records': len(recs), 'checks': checks, 'review': review,
            'status': dict(Counter(c['status'] for c in checks))}


MARK = {'pass': 'ok', 'fail': 'FAIL', 'review': 'review', 'pending': 'pending', 'manual': 'manual', 'info': ''}


def print_report(rep, show_all):
    print(f'# Criteria report: {rep["records"]} records (CRITERIA.md)')
    section = None
    for c in rep['checks']:
        if c['section'] != section:
            section = c['section']
            print(f'\n## {section}')
        count = f' ({c["count"]})' if c['count'] else ''
        print(f'- [{MARK[c["status"]]}] {c["name"]}{count}' if MARK[c['status']] else f'- {c["name"]}')
        if c['note']:
            print(f'    {c["note"]}')
        for row in c['table'] or []:
            print('    ' + '  '.join(f'{str(v):>12}' if i else f'{str(v):24}' for i, v in enumerate(row)))
        for item in c['items'] if show_all else c['items'][:8]:
            print(f'    {item}')
        if not show_all and len(c['items']) > 8:
            print(f'    ... {len(c["items"]) - 8} more (--all)')
    print('\n' + ', '.join(f'{n} {s}' for s, n in sorted(rep['status'].items())))


def print_marks(recs=None):
    recs = load_records() if recs is None else recs
    manual, _ = manual_checks(recs)
    for c in manual:
        r = c['reviews']
        print(f'## {c["section"]}: {c["name"]} ({r["total"]} {r["unit"]})')
        print('    ' + '; '.join(f'{who} green {v["green"]}, red {v["red"]}, yellow {v["yellow"]}'
                                 for who, v in r['by_reviewer'].items()))
        for item in c['items']:
            print(f'    {item}')


USAGE = """criteria.py                       the checklist (--all: every item, --json: what the dashboard reads)
criteria.py --marks               review marks per reviewer, and every red mark
criteria.py --mark RECORD ITEM REVIEWER green|red|clear [--comment NOTE] [--kind problem|angle]
    ITEM: clear-and-sensible or serves-the-purpose (the record as a whole), or a query key
    (direct, paraphrase, cross_lingual[zh], propositional[0], unrelated_near[0], unrelated_far[0], derived[2]).
    The note and kind are optional.
Reviewers: """ + ', '.join(REVIEWER_IDS) + """ (agents mark as codex or claude)."""


def main(argv):
    opt = lambda flag: argv[argv.index(flag) + 1] if flag in argv and argv.index(flag) + 1 < len(argv) else None
    if argv[:1] == ['--mark']:
        if len(argv) < 5:
            print(USAGE)
            return 2
        record_id, item, reviewer, state = argv[1:5]
        try:
            marks = set_mark(record_id, item, reviewer, None if state == 'clear' else state, opt('--comment') or '',
                             opt('--kind'))
        except ValueError as e:
            print(f'error: {e}', file=sys.stderr)
            return 2
        print(json.dumps(marks, ensure_ascii=False, indent=2))
        return 0
    if '--marks' in argv:
        print_marks()
        return 0
    if '--help' in argv or '-h' in argv:
        print(USAGE)
        return 0
    rep = report()
    if '--json' in argv:
        print(json.dumps(rep, ensure_ascii=False))
    else:
        print_report(rep, '--all' in argv)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
