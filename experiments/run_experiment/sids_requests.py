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

Prompt format (format_request, after the tokenizer is loaded): the edit is
trained in the same form evaluation asks it, so an edit is not scored on a
prompt it was never trained on:

    chat      instruct models: the chat template with CHAT_SHOTS worked
              examples as earlier user/assistant turns, then the user turn
              holding CHAT_INSTRUCTION and the question (the instruction in
              every user turn, no system turn), generation prompt added;
              the target is the start of the assistant's reply
    fewshot   base models: FEW_SHOT_EXAMPLES, then "Question: <q>\nAnswer:";
              the methods join prompt and target with a space (" <answer>")
    raw       the bare question, as before (and for SCR/IKE, which build
              their own prompts from the fact)

The same render_prompt formats the edit prompt and every evaluation prompt
(paraphrase, cross-lingual, propositional, locality, derived), so they can't
drift. Under chat and fewshot the training target also loses a leading
article ("the thyroid gland" -> "thyroid gland"; STRIPPED_LEADING_WORDS);
the record keeps its answer, and evaluation accepts both.

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


# Prompt formats (format_request). Instruct models answer through their chat
# template, base models through a few-shot "Question:/Answer:" context, as in
# the model audit (experiments/model_audit/audit.py, prompt_text with the
# default --instruction and --chat_shots 0). The chat instruction is the
# audit's (test_sids_requests checks the copy still matches). The worked
# examples give three answer kinds (a city, a number, yes/no). No example may
# contain a record's subject, or the subject-locating methods see it twice
# ("What is the capital of Japan?" holds the RBox subject 'is the capital
# of'), and none may share a question or an answer with a record (the
# earlier Japan/Tokyo, tricycle "3" and "Is the Sun a star?" examples did;
# replaced 2026-11-01). test_sids_requests checks the subjects and
# experiments/model_audit/test_audit.py (ShotCollisionTests) the overlap, on
# every record. The model audit imports FEW_SHOT_EXAMPLES, FEW_SHOT and
# render_prompt from here, so the audit and the runner ask the same text.
PROMPT_FORMATS = ('chat', 'fewshot', 'raw')
# Chat models (user decision 2026-11-01): the model audit's "strict"
# instruction in every user turn, after the first CHAT_SHOTS worked examples
# as earlier user/assistant turns. In the audit's test this cut answers
# wrapped in a sentence from 25% to 0% (Llama-3.1-8B-Instruct) and from 40%
# to 2.9% (Mistral-7B-Instruct-v0.1) against the earlier single user turn
# with "Answer the question in a few words, without explanation." (the
# audit's few_words preset, now a variant).
CHAT_INSTRUCTION = "Answer with only the answer: a name, a number, or yes/no. No sentence, no explanation."
CHAT_SHOTS = 2
FEW_SHOT_EXAMPLES = [("Which city is Thailand's capital?", "Bangkok"),
                     ("How many keys are on a piano?", "88"),
                     ("Is a lemon sour?", "Yes")]
FEW_SHOT = "".join(f"Question: {q}\nAnswer: {a}\n\n" for q, a in FEW_SHOT_EXAMPLES)
# Methods that build their own prompt from the fact (prompt + target as a
# sentence, or retrieved demonstrations), so a templated prompt would end up
# inside their context: they keep the bare question.
RAW_FORMAT_METHODS = {"scr", "ike"}

# Leading words dropped from the training target only (never from the record
# or the evaluation references), with when: "any" always, "value" when the
# rest is a quantity ("about 0.3 kelvin"), "agent" when the rest is not a
# gerund, i.e. names who or what does it ("by an earthquake ..." but not
# "by laying eggs"). Only lowercase words count: a capitalised one ("The
# Hague", "A Tale of Two Cities") is part of a name. The first trained token
# should be the answer, not style.
STRIPPED_LEADING_WORDS = {'the': 'any', 'a': 'any', 'an': 'any', 'about': 'value', 'by': 'agent'}
_NUMBER_WORDS = {'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven',
                 'twelve', 'twenty', 'thirty', 'forty', 'fifty', 'hundred', 'thousand', 'million', 'billion',
                 'half', 'a', 'an'}


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
    # Propositional (logical consistency, reported on its own): the edited
    # fact in a yes/no truth-functional question; gold is its new answer
    # ("I don't know" under delete, as validate.py's truth table requires).
    for i, item in enumerate(q.get('propositional') or []):
        if not (item.get('prompt') or '').strip():
            raise MissingAnswer(rid, f'propositional[{i}] has no prompt')
        gold = ABSTAIN_TARGET if op == 'delete' else item.get('new_answer')
        if not gold:
            raise MissingAnswer(rid, f'propositional[{i}] has no new answer')
        portability[f'propositional_{i}'] = {'prompt': item['prompt'], 'ground_truth': gold,
                                             'form': item.get('form'), 'side_fact': item.get('side_fact'),
                                             'logic': 'propositional'}

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


def default_prompt_format(chat_model, method):
    """The format a run uses when --sids_prompt_format is auto."""
    if method in RAW_FORMAT_METHODS:
        return 'raw'
    return 'chat' if chat_model else 'fewshot'


def _adds_bos(tok):
    bos = getattr(tok, 'bos_token_id', None)
    if bos is None:
        return False
    ids = tok('x')['input_ids']
    return bool(ids) and ids[0] == bos


def chat_messages(question, instruction=CHAT_INSTRUCTION, shots=CHAT_SHOTS):
    """User/assistant turns for a chat model: the first `shots` of
    FEW_SHOT_EXAMPLES as earlier turns, then the question. The instruction
    goes in every user turn, never a system turn: Mistral-Instruct-v0.1 has
    no system role. The model audit's --instruction/--chat_shots variants
    use this too."""
    if not 0 <= shots <= len(FEW_SHOT_EXAMPLES):
        raise ValueError(f"chat shots must be 0..{len(FEW_SHOT_EXAMPLES)}, got {shots}")
    messages = []
    for q, a in FEW_SHOT_EXAMPLES[:shots]:
        messages += [{'role': 'user', 'content': f'{instruction}\n\n{q}'}, {'role': 'assistant', 'content': a}]
    return messages + [{'role': 'user', 'content': f'{instruction}\n\n{question}'}]


def render_chat(messages, tok):
    """Chat messages through the tokenizer's template, generation prompt
    added, thinking off, and the template's BOS text dropped when the
    tokenizer adds one itself."""
    if tok is None or not getattr(tok, 'chat_template', None):
        raise ValueError('the chat prompt format needs a tokenizer with a chat template')
    # enable_thinking=False: hybrid templates (SmolLM3) reason by default;
    # templates without the switch ignore it.
    text = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    bos = getattr(tok, 'bos_token', None)
    if bos and text.startswith(bos) and _adds_bos(tok):
        text = text[len(bos):]
    return text


def render_prompt(question, fmt, tok=None):
    """The text a model is given for one question: the edit prompt and every
    evaluation prompt go through here, and so does the model audit
    (experiments/model_audit/audit.py imports it), so the audit, the edit and
    the run's own evaluation (sid_evaluation.py) ask identical text. Keep the
    signature (question, fmt, tok=None) -> str stable.

    chat: chat_messages (CHAT_SHOTS worked examples as earlier turns, then
    CHAT_INSTRUCTION, a blank line and the question, in every user turn)
    with the generation prompt, so the text ends where the assistant's reply
    begins. The template's own BOS text is dropped when the tokenizer adds
    one itself (Llama 3.1, Mistral), since the methods and evaluation all
    tokenize with special tokens on; the token ids then equal the audit's.
    """
    if fmt == 'raw':
        return question
    if fmt == 'fewshot':
        return f"{FEW_SHOT}Question: {question}\nAnswer:"
    if fmt != 'chat':
        raise ValueError(f'prompt format must be one of {PROMPT_FORMATS}, not {fmt!r}')
    return render_chat(chat_messages(question), tok)


def _is_value(words):
    w = words[0].lower().strip('~')
    return bool(re.match(r'^[\d.,]+', w)) or w in _NUMBER_WORDS


def training_target(answer):
    """The answer as the edit trains it: leading STRIPPED_LEADING_WORDS
    removed (repeatedly: "by an earthquake" -> "earthquake"), as long as
    something is left."""
    words = str(answer).split(' ')
    while len(words) > 1:
        when = STRIPPED_LEADING_WORDS.get(words[0])  # lowercase only, see above
        rest = words[1:]
        if when == 'any' or (when == 'value' and _is_value(rest)) or (
                when == 'agent' and not rest[0].lower().endswith('ing')):
            words = rest
        else:
            break
    return ' '.join(words)


def format_request(request, fmt, tok=None):
    """A request in prompt format `fmt`: every prompt rendered by
    render_prompt and, unless raw, the target stripped by training_target.
    The bare questions stay alongside (sids.question, sids.rephrase_question,
    and each probe's "question") for judges and statements, and the record's
    own answer as sids.answer. raw returns the request unchanged."""
    if fmt == 'raw':
        return request
    out = dict(request)
    sids = dict(request['sids'])
    sids.update(prompt_format=fmt, question=request['prompt'], answer=request['target_new'],
                rephrase_question=request.get('rephrase_prompt'))
    out['sids'] = sids
    out['prompt'] = render_prompt(request['prompt'], fmt, tok)
    if request.get('rephrase_prompt'):
        out['rephrase_prompt'] = render_prompt(request['rephrase_prompt'], fmt, tok)
    out['target_new'] = training_target(request['target_new'])
    for group in ('locality', 'portability'):
        out[group] = {k: {**v, 'question': v['prompt'], 'prompt': render_prompt(v['prompt'], fmt, tok)}
                      for k, v in (request.get(group) or {}).items()}
    return out


def clean_answer(text, fmt):
    """A generated answer cut where the format's answer ends (as the audit
    does): fewshot at the first line break or next "Question:", chat at the
    first blank line. raw is returned as generated."""
    if fmt == 'raw':
        return text
    text = text.strip()
    if fmt == 'fewshot':
        for stop in ('\n', 'Question:'):
            text = text.split(stop, 1)[0]
        return text.strip()
    return text.split('\n\n', 1)[0].strip()


def question_region(request):
    """(offset, text): where the record's own question sits in the rendered
    edit prompt. Under chat and fewshot that is the bare question
    (sids.question) inside the user turn or after the worked examples; the
    template's own text around it (Llama 3.1 and SmolLM3 write "Today Date:
    26 Jul 2024" into a system turn) is not part of it. Under raw, or for a
    request not from format_request, the whole prompt."""
    prompt = request['prompt']
    sids = request.get('sids') or {}
    question = sids.get('question')
    if sids.get('prompt_format') in (None, 'raw') or not question:
        return 0, prompt
    at = prompt.rfind(question)  # the question comes last, after any template text
    return (at, question) if at >= 0 else (0, prompt)


def subject_offset(request):
    """Character offset of the subject in the edit prompt: its one occurrence
    inside the question (question_region), or None when it is not there
    exactly once."""
    at, text = question_region(request)
    subject = request.get('subject')
    if not subject or text.count(subject) != 1:
        return None
    return at + text.index(subject)


def require_subject(request):
    """For locate-and-edit methods: the subject must be in the question
    verbatim, exactly once, or the edit lands on the wrong tokens. Counted in
    the question, not the whole rendered prompt: a chat template's own text
    may hold it too (Llama 3.1's "Today Date: 26 Jul 2024" holds
    mathematics-insert-0006's subject "6"), and edit_request points the
    methods at the question's occurrence."""
    rid, subject = request['sids']['id'], request['subject']
    at, text = question_region(request)
    n = text.count(subject) if subject else 0
    if n != 1:
        where = 'does not appear' if n == 0 else f'appears {n} times'
        raise SubjectNotInPrompt(rid, f'subject {subject!r} {where} in the edit prompt {text!r}')


# Methods that accept an edit prompt with "{}" in place of the subject and
# otherwise make one themselves with prompt.replace(subject, "{}"), which
# replaces every occurrence, the template's too (EasyEdit's ROME, MEMIT,
# PMET, AlphaEdit; WilKE, FiNE, NMKE, FiDAL; IFMET and LTI through
# portability/base.py). KN reads the prompt as text and CaKE runs on MQuAKE
# only, so they get the plain prompt.
PLACEHOLDER_METHODS = SUBJECT_METHODS - {'kn', 'cake'}


def edit_request(request, method):
    """The request as an editing method is handed it: for PLACEHOLDER_METHODS
    on a Sid's Dataset request, the prompt with "{}" at the subject's
    occurrence in the question (subject_offset), so the method edits there
    and nowhere else. Every other case, and a request whose subject is not
    once in its question (check_request reports it), is returned unchanged.
    Identical to what the method would do itself whenever the subject occurs
    once in the whole prompt; evaluation always uses the plain prompt."""
    if method not in PLACEHOLDER_METHODS or 'sids' not in request or '{}' in request['prompt']:
        return request
    at = subject_offset(request)
    if at is None:
        return request
    prompt = request['prompt']
    return {**request, 'prompt': prompt[:at] + '{}' + prompt[at + len(request['subject']):]}


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
