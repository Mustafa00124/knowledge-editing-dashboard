"""Sid's Dataset records as edit requests, with strict checks.

Each record becomes one request in the shape the editing methods take
(prompt, subject, target_new, ground_truth, rephrase_prompt, locality,
portability), plus the record itself under "sids" for evaluation. Every
requirement a method relies on is checked here and raises a named error with
the record id, instead of being skipped, guessed or patched: a run that gets
through has really met them.

The edit is the record's direct question with its new answer:

    replace   prompt = direct question, target_new = new answer
    insert    prompt = direct question, target_new = new answer (no original)
    delete    prompt = direct question, target_new = "I don't know"

Basic for now (see README, Running methods, open decisions): TBox and RBox
use the same question form, with the RBox subject taken from the quoted
relation wording in the question. Indeterminate derived queries carry their
per-world answers; an answer passes if it matches some world.

Standard library only, so the checklist (criteria.py) and a laptop without
the experiment environment can run every data check.
"""
import hashlib
import json
import re
from pathlib import Path

# What a delete edit writes in place of the removed fact.
ABSTAIN_TARGET = "I don't know"

# Locate-and-edit methods edit at the subject's last token, so the subject has
# to appear verbatim, exactly once, in the edit prompt.
SUBJECT_METHODS = {"rome", "memit", "pmet", "alphaedit", "wilke", "fine", "nmke", "fidal", "kn", "cake",
                   "ifmet", "lti"}


class SidsRequestError(ValueError):
    """A record can't be turned into a request that meets a method's needs."""

    def __init__(self, record_id, message):
        super().__init__(f"{record_id}: {message}")
        self.record_id = record_id


class EmptyTarget(SidsRequestError):
    pass


class TargetEqualsOriginal(SidsRequestError):
    pass


class SubjectNotInPrompt(SidsRequestError):
    pass


class MissingAnswer(SidsRequestError):
    pass


class UnsupportedRecord(SidsRequestError):
    pass


def records_dir(data_path):
    """The records folder for a --data_path that names it or anything in it."""
    p = Path(data_path)
    if p.is_file():
        return None
    if (p / 'records').is_dir():
        return p / 'records'
    return p


def load_records(data_path):
    """Records under a folder (records/<topic>/<operation>/*.json), or one file, in id order."""
    p = Path(data_path)
    paths = [p] if p.is_file() else sorted(records_dir(p).glob('*/*/*.json'))
    recs = [json.loads(x.read_text()) for x in paths]
    return sorted(recs, key=lambda r: r['id'])


def records_hash(records):
    """One hash for the whole set, so results can tell when records changed."""
    h = hashlib.sha256()
    for r in sorted(records, key=lambda r: r['id']):
        h.update(json.dumps(r, sort_keys=True, ensure_ascii=False).encode())
    return h.hexdigest()[:16]


def _norm(s):
    return ' '.join(str(s or '').lower().split())


def edit_subject(rec, prompt):
    """The subject as it appears in the prompt. RBox records name a relation
    id (part_of); the question quotes its wording ('is part of')."""
    if rec['box'] == 'rbox':
        quoted = re.findall(r"'([^']+)'", prompt)
        return quoted[0] if quoted else rec['edit']['subject']
    return rec['edit']['subject']


def build_request(rec):
    """One request for one record, after the data checks every method needs."""
    rid, op, box = rec['id'], rec['edit_operation'], rec['box']
    if op not in ('replace', 'delete', 'insert'):
        raise UnsupportedRecord(rid, f'edit operation {op!r} has no edit request')
    q = rec['queries']
    direct = q['direct']
    prompt = (direct.get('prompt') or '').strip()
    original = direct.get('original_answer')
    target = ABSTAIN_TARGET if op == 'delete' else direct.get('new_answer')
    if not prompt:
        raise MissingAnswer(rid, 'the direct question is empty')
    if not target or not str(target).strip():
        raise EmptyTarget(rid, 'the direct question has no new answer to edit towards')
    if op == 'replace' and _norm(target) == _norm(original):
        raise TargetEqualsOriginal(rid, f'new answer {target!r} equals the original answer')

    paraphrase = q.get('paraphrase') or {}
    locality = {}
    for key in ('unrelated_near', 'unrelated_far'):
        for i, item in enumerate(q.get(key) or []):
            if not (item.get('prompt') or '').strip():
                raise MissingAnswer(rid, f'{key}[{i}] has no prompt')
            locality[f'{key}_{i}'] = {'prompt': item['prompt'], 'ground_truth': item.get('reference')}
    portability = {}
    for i, item in enumerate(q.get('derived') or []):
        if not (item.get('prompt') or '').strip():
            raise MissingAnswer(rid, f'derived[{i}] has no prompt')
        if item.get('world_answers'):
            worlds = {w: (a or {}).get('answer') for w, a in item['world_answers'].items()}
            if op != 'delete' and any(a is None for a in worlds.values()):
                raise MissingAnswer(rid, f'derived[{i}] has a world with no answer under {op}')
            gold = None
        else:
            worlds = None
            gold = ABSTAIN_TARGET if op == 'delete' else item.get('new_answer')
            if op != 'delete' and not gold:
                raise MissingAnswer(rid, f'derived[{i}] is determinate but has no new answer')
        portability[f'derived_{i}'] = {'prompt': item['prompt'], 'ground_truth': gold, 'world_answers': worlds,
                                       'determinacy': item.get('determinacy'), 'derivation': item.get('derivation'),
                                       'logic': item.get('logic'), 'theory': item.get('theory')}
    for i, item in enumerate(q.get('cross_lingual') or []):
        portability[f"cross_lingual_{item.get('language', i)}"] = {
            'prompt': item['prompt'], 'ground_truth': ABSTAIN_TARGET if op == 'delete' else item.get('new_answer')}

    return {
        'prompt': prompt,
        'subject': edit_subject(rec, prompt),
        'target_new': target,
        'ground_truth': original,
        'rephrase_prompt': paraphrase.get('prompt'),
        'locality': locality,
        'portability': portability,
        'sids': {'id': rid, 'edit_operation': op, 'box': box, 'topic': rec['topic'],
                 'derivability': rec.get('derivability'), 'fictional': rec.get('fictional')},
    }


def require_subject(request):
    """For locate-and-edit methods: the subject must be in the prompt verbatim,
    exactly once, or the edit lands on the wrong tokens."""
    rid, subject, prompt = request['sids']['id'], request['subject'], request['prompt']
    n = prompt.count(subject) if subject else 0
    if n != 1:
        where = 'does not appear' if n == 0 else f'appears {n} times'
        raise SubjectNotInPrompt(rid, f'subject {subject!r} {where} in the edit prompt {prompt!r}')


def check_request(request, method):
    """Every data check that applies to this method."""
    if method in SUBJECT_METHODS:
        require_subject(request)
    if method == 'kn' and not request.get('ground_truth'):
        raise MissingAnswer(request['sids']['id'], 'kn attributes neurons to the original answer, and there is none')


def load_sids_requests(data_path, ds_size=None):
    """eval_utils.load_requests entry point: every record that can become a
    request, in id order. Raises on the first record that can't."""
    reqs = [build_request(r) for r in load_records(data_path)]
    return reqs if ds_size is None else reqs[:ds_size]


def preflight(records, methods):
    """{(record_id, method): error message} for every data check that fails,
    across all records and methods. Empty when everything can run."""
    failures = {}
    for rec in records:
        try:
            request = build_request(rec)
        except SidsRequestError as e:
            for m in methods:
                failures[(rec['id'], m)] = f'{type(e).__name__}: {e}'
            continue
        for m in methods:
            try:
                check_request(request, m)
            except SidsRequestError as e:
                failures[(rec['id'], m)] = f'{type(e).__name__}: {e}'
    return failures
