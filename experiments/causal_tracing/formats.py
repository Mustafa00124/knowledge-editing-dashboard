"""Facts to trace, and the prompt formats they can be traced in.

Loading and prompting are kept apart. A loader turns one dataset file into
format-agnostic fact rows; build() then writes one row as one prompt in one
format, and says which characters get the noise. That is what lets the same
facts be traced as a completion, a question, through a chat template, as
multiple choice or as a riddle, and the curves be compared format against
format.

A row:
    id        "<file stem>:<record index>[:<sub index>]", stable across runs
    source    file stem
    relation  Wikidata relation id where the dataset has one
    domain    UniEdit's domain (its file name), else None
    subject   the entity a completion or question is about
    answer    the true answer; aliases: other accepted answers
    cloze     "Fernando Santos is a citizen of" (completion form)
    question  "What is the country of citizenship of Fernando Santos?"
    choices, answer_index   multiple choice (RealTimeQA)
    riddle, clue            AlteredRiddles: the riddle and the added clue,
                            whose characters are what gets corrupted

Which records: the --split records of splits/ (nontest = dev + demo), so the
trace that informs edit layers never sees a test record.
"""
import difflib
import json
import os
import re
import sys

EXP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(EXP_DIR))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "experiments", "run_experiment"))
import splits as data_splits  # noqa: E402

SPLIT_CHOICES = ("nontest", "dev", "all")

# Every format, what it needs from a row, and what it corrupts.
FORMATS = {
    "completion": "the cloze sentence; noise on the subject",
    "question": "'Question: ... Answer:' as plain text; noise on the subject",
    "chat_question": "the question through the model's chat template, asking for the answer only; noise on the subject",
    "chat_prefill": "the question through the chat template, with the cloze sentence begun as the reply; "
                    "noise on every mention of the subject",
    "mcq": "question, lettered choices, 'Answer:' as plain text; noise on the question",
    "chat_mcq": "the multiple-choice prompt through the chat template, asking for the letter only; noise on the question",
    "riddle": "'Riddle: ... Answer:' as plain text; noise on the clue the altered riddle added",
    "chat_riddle": "the riddle through the chat template, asking for the answer only; noise on the added clue",
}
CHAT_FORMATS = {f for f in FORMATS if f.startswith("chat_")}
LETTERS = "ABCDEFGH"


# ---------------------------------------------------------------- loading

def _read(path):
    with open(path) as f:
        if path.endswith(".jsonl"):
            return [json.loads(line) for line in f if line.strip()]
        data = json.load(f)
    if isinstance(data, dict) and "data" in data and isinstance(data["data"], list):
        return data["data"]
    if isinstance(data, dict):
        return list(data.values())  # UniEdit: {sample_id: record}, the runner's order
    return data


def _split_records(data, data_path, split):
    """(index, record) pairs in `split`; refuses a dataset with no split."""
    if split == "all":
        return list(enumerate(data))
    info = data_splits.load(data_path)
    if info is None:
        raise SystemExit(f"no dev/test split for {data_path}; pass --split all only for a throwaway check")
    if info["requests"] != len(data):
        raise SystemExit(f"{data_path} has {len(data)} records but its split expects {info['requests']}")
    keep = info["dev"] if split == "dev" else sorted(set(info["dev"]) | set(info["demo"]))
    return [(i, data[i]) for i in keep]


def _first(value):
    if isinstance(value, list):
        return next((v for v in value if isinstance(v, str) and v.strip()), None)
    return value.strip() if isinstance(value, str) and value.strip() else None


def _row(**fields):
    base = dict.fromkeys(("relation", "domain", "subject", "answer", "cloze", "question",
                          "choices", "answer_index", "riddle", "clue"))
    base["aliases"] = []
    base.update(fields)
    return base


def _mquake(source, index, record):
    for j, rw in enumerate(record["requested_rewrite"]):
        yield _row(id=f"{source}:{index}:{j}", source=source, relation=rw.get("relation_id"),
                   subject=rw["subject"], answer=(rw.get("target_true") or {}).get("str"),
                   cloze=rw["prompt"].format(rw["subject"]), question=rw.get("question"))


def _uniedit(source, index, record):
    edit = record["edit"]
    target = edit.get("target") or ""
    # "phonograph record (gramophone record, record, ...)": answer, then aliases.
    match = re.match(r"^(.*?)\s*\((.*)\)\s*$", target)
    answer, aliases = (match.group(1), [a.strip() for a in match.group(2).split(",")]) if match else (target, [])
    prop = (edit.get("property") or {}).get("id")
    yield _row(id=f"{source}:{index}", source=source, relation=prop, domain=source,
               subject=edit.get("subject"), answer=answer.strip() or None, aliases=[a for a in aliases if a],
               cloze=edit.get("prompt"))


def _realtimeqa(source, index, record):
    choices = record.get("choices") or []
    answer = _first(record.get("target_new"))
    if answer not in choices:
        return
    yield _row(id=f"{source}:{index}", source=source, relation=record.get("question_type"),
               question=record.get("prompt"), choices=choices, answer_index=choices.index(answer), answer=answer)


def riddle_clue(original, altered):
    """The characters the altered riddle added or changed: its longest
    inserted/replaced stretch against the original, trimmed of the joining
    punctuation and spaces. That stretch is what tells the two answers apart."""
    matcher = difflib.SequenceMatcher(a=original, b=altered, autojunk=False)
    spans = [(j1, j2) for tag, _, _, j1, j2 in matcher.get_opcodes() if tag in ("insert", "replace")]
    if not spans:
        return None
    start, end = max(spans, key=lambda s: s[1] - s[0])
    while start < end and not altered[start].isalnum():
        start += 1
    while end > start and not altered[end - 1].isalnum():
        end -= 1
    return (start, end) if end - start >= 3 else None


def _riddle(source, index, record):
    clue = riddle_clue(record["original_riddle"], record["altered_riddle"])
    if clue is None:
        return
    accepted = [a for a in record.get("altered_accepted_answers") or [] if a]
    yield _row(id=f"{source}:{index}", source=source, relation=record.get("type"),
               riddle=record["altered_riddle"], clue=clue,
               answer=record["altered_answer"], aliases=accepted)


def _knowedit(source, index, record):
    prompt, subject = record.get("prompt"), record.get("subject")
    answer = _first(record.get("ground_truth"))
    if answer is None and isinstance(record.get("cond"), str) and ">>" in record["cond"]:
        answer = record["cond"].split(">>")[0].strip() or None  # ZsRE keeps the original answer in "cond"
    is_question = isinstance(prompt, str) and prompt.rstrip().endswith("?")
    yield _row(id=f"{source}:{index}", source=source, subject=subject, answer=answer,
               cloze=None if is_question else prompt, question=prompt if is_question else None)


def normalize(row):
    """A fact-set row in the current shape. Sets written before formats
    existed stored the cloze sentence as "prompt"."""
    out = _row(**{k: v for k, v in row.items() if k != "prompt"})
    if out["cloze"] is None and row.get("prompt"):
        out["cloze"] = row["prompt"]
    if isinstance(out.get("clue"), list):
        out["clue"] = tuple(out["clue"])
    return out


def load_rows(data_path, split="nontest", limit=None):
    data = _read(data_path)
    source = os.path.splitext(os.path.basename(data_path))[0]
    sample = data[0] if data else {}
    loader = (_mquake if "requested_rewrite" in sample else
              _uniedit if "edit" in sample else
              _realtimeqa if "choices" in sample else
              _riddle if "altered_riddle" in sample else
              _knowedit)
    rows, seen = [], set()
    for index, record in _split_records(data, data_path, split):
        if not isinstance(record, dict):
            continue
        for row in loader(source, index, record):
            key = (row["cloze"], row["question"], row["riddle"], row["answer"])
            if not row["answer"] or key in seen:
                continue  # MQuAKE repeats a fact across cases
            seen.add(key)
            rows.append(row)
            if limit and len(rows) >= limit:
                return rows
    return rows


# ---------------------------------------------------------------- prompting

def has_chat_template(tok):
    return bool(getattr(tok, "chat_template", None))


def _chat(tok, user, prefill=""):
    text = tok.apply_chat_template([{"role": "user", "content": user}], tokenize=False, add_generation_prompt=True)
    return text + prefill


def _mentions(text, needle, start=0):
    spans, at = [], text.find(needle, start)
    while needle and at >= 0:
        spans.append((at, at + len(needle)))
        at = text.find(needle, at + len(needle))
    return spans


def _mcq_body(row):
    lines = [f"Question: {row['question']}"] + [f"{LETTERS[i]}. {c}" for i, c in enumerate(row["choices"])]
    return "\n".join(lines)


def answers_for(row, fmt):
    """The strings whose first token counts as giving the answer."""
    if fmt in ("mcq", "chat_mcq"):
        return [LETTERS[row["answer_index"]]]
    out = [row["answer"]] + list(row.get("aliases") or [])
    if fmt in ("riddle", "chat_riddle"):
        # "A silence." / "an error": the article would match any riddle.
        out += [re.sub(r"^(a|an|the)\s+", "", a.strip(), flags=re.I).rstrip(".!") for a in out]
    return list(dict.fromkeys(a for a in out if a and a.strip()))


def build(row, fmt, tok):
    """{"text", "spans": [(start, end) chars to corrupt], "templated", "answers"},
    or None when this row cannot be written in this format."""
    templated = fmt in CHAT_FORMATS
    if templated and not has_chat_template(tok):
        return None
    subject = row.get("subject")
    if fmt == "completion":
        if not row["cloze"] or not subject or subject not in row["cloze"]:
            return None
        text = row["cloze"]
        spans = [_mentions(text, subject)[-1]]
    elif fmt in ("question", "chat_question", "chat_prefill"):
        q = row["question"]
        if not q or not subject or subject not in q:
            return None
        if fmt == "question":
            text = f"Question: {q}\nAnswer:"
            spans = _mentions(text, subject)
        elif fmt == "chat_question":
            text = _chat(tok, f"{q}\nAnswer with only the answer, not a sentence.")
            spans = _mentions(text, subject)
        else:
            if not row["cloze"] or subject not in row["cloze"]:
                return None
            text = _chat(tok, q, prefill=row["cloze"])
            spans = _mentions(text, subject)
    elif fmt in ("mcq", "chat_mcq"):
        if not row["choices"] or row["answer_index"] is None:
            return None
        body = _mcq_body(row)
        text = f"{body}\nAnswer:" if fmt == "mcq" else _chat(tok, f"{body}\nAnswer with the letter only.")
        start = text.find(row["question"])
        spans = [(start, start + len(row["question"]))]
    elif fmt in ("riddle", "chat_riddle"):
        if not row["riddle"] or not row["clue"]:
            return None
        lead = "Riddle: "
        text = f"{lead}{row['riddle']}\nAnswer:" if fmt == "riddle" else \
            _chat(tok, f"{lead}{row['riddle']}\nAnswer with only the answer.")
        offset = text.find(lead + row["riddle"]) + len(lead)
        spans = [(offset + row["clue"][0], offset + row["clue"][1])]
    else:
        raise ValueError(f"unknown format {fmt!r}")
    if not spans or spans[0][0] < 0:
        return None
    return {"text": text, "spans": spans, "templated": templated, "answers": answers_for(row, fmt)}


def encode(tok, item, **kwargs):
    """A chat-templated text already carries its BOS; plain text gets one."""
    return tok(item["text"], add_special_tokens=not item["templated"], **kwargs)


def token_spans(tok, item):
    """Each corrupted character span as a [start, end) token range."""
    offsets = encode(tok, item, return_offsets_mapping=True)["offset_mapping"]
    out = []
    for start_char, end_char in item["spans"]:
        indices = [i for i, (a, b) in enumerate(offsets) if a < end_char and b > start_char]
        if indices:
            out.append((indices[0], indices[-1] + 1))
    return out
