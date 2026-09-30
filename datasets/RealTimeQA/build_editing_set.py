"""Turns the raw RealTimeQA question files (past/, backnumber/, latest/ -
*_qa.jsonl only, downloaded from github.com/realtimeqa/realtimeqa_public)
into one flat editing-ready JSON array, split into per-question-type
subsets matching the "Question Type" axis of the Knowledge Spectrum
framework ("Diagnosing Model Editing via Knowledge Spectrum", Pan et al.
2025, arXiv:2509.17482).

That paper also preprocesses RealTimeQA into an editing format ("fields
for the question, subject, answer, and a human-written rephrased
question") but never released that preprocessed data or the code that
built it - this is our own reconstruction of the same idea, not a copy of
theirs. Two differences worth knowing:

  - No `subject` field. RealTimeQA's questions are natural sentences with
    no labeled subject span, and every other dataset wired into this
    project gets `subject` from its source rather than us extracting it
    (see eval_utils.py) - inventing one here would mean guessing which
    substring is "the" subject, which we're not willing to fake. That
    means requests built from this file work for FT/LoRA/SCR/IKE, but
    NOT for ROME/MEMIT/PMET/AlphaEdit (they require request['subject'] to
    be a literal substring of the prompt - run_experiment.py checks for
    this and refuses to run rather than crash confusingly inside
    EasyEdit). The paper doesn't hit this because they only evaluate
    FT/MEMIT/AlphaEdit - wait, they *do* use MEMIT/AlphaEdit, which means
    their own preprocessing must derive a subject somehow (unpublished).
    We're not guessing at what that was.
  - No rephrase/locality probes - the paper's "human-written rephrased
    question" was hand-authored by their annotators and never released,
    so there's no portability signal here; ground_truth is left null
    (these are recent-news questions - the point is the model likely
    never saw the answer, so there's no prior "correct" belief to record,
    the same Insertion-style situation as KnowEdit's wiki_recent).

Only the Question Type axis of the Knowledge Spectrum is computed here.
The other two (Popularity via Wikipedia page views of the subject -
blocked by not having a subject; Familiarity via pre-edit probing of a
specific model) aren't dataset-level attributes at all - Familiarity in
particular depends on which model you're about to edit, so it can only
be computed at run time against a real model, not baked into a file.

Usage: python build_editing_set.py
Writes realtimeqa_editing.json (everything) plus by_question_type/<type>.json
(one file per Who/What/When/Where/Which/Why/How/Others).
"""
import glob
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
QUESTION_TYPES = ["who", "what", "when", "where", "which", "why", "how"]


_ALIASES = {"whose": "who", "whom": "who"}
_WH_WORD_RE = re.compile(r"\b(" + "|".join(QUESTION_TYPES + list(_ALIASES)) + r")\b", re.IGNORECASE)


def question_type(question_sentence):
    """The paper's rule is "the leading interrogative word" of the
    eliciting question. That's straightforward when the question *is* the
    whole prompt, but most of RealTimeQA's question_sentence fields are a
    scene-setting sentence followed by the actual question
    ("Chaos reigned in the US House... Who is the new speaker of the
    House?"), and plenty of those questions don't lead with the wh-word
    either ("According to the White House, how soon could..."). Taking
    literally the first word of the whole field misclassified the large
    majority of these into "Others" on a first pass (checked by hand) -
    so instead: take the *last* whole-word wh-word occurrence anywhere in
    the prompt, on the reasoning that the operative question is always
    the last clause and its wh-word is what should decide the type,
    regardless of how much unrelated lead-in context precedes it. "Whose"/
    "whom" fold into "who" - the paper's 8-way list doesn't mention them,
    but they're the same interrogative family asking the same kind of
    fact (a person's identity), so leaving them stuck in "Others" would
    just be undercounting "who" on a technicality. A prompt with no
    wh-word at all (RealTimeQA has plenty of fill-in-the-blank style
    questions ending in ":" rather than a wh-question) is "Others", the
    paper's own catch-all category."""
    matches = _WH_WORD_RE.findall(question_sentence)
    if not matches:
        return "others"
    last = matches[-1].lower()
    return _ALIASES.get(last, last)


def load_raw():
    files = sorted(glob.glob(os.path.join(HERE, "past", "**", "*_qa.jsonl"), recursive=True)) + \
        sorted(glob.glob(os.path.join(HERE, "backnumber", "**", "*_qa.jsonl"), recursive=True)) + \
        sorted(glob.glob(os.path.join(HERE, "latest", "**", "*_qa.jsonl"), recursive=True))
    records = []
    for fp in files:
        with open(fp) as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
    return records


def build():
    raw = load_raw()
    out = []
    skipped = 0
    for r in raw:
        try:
            idx = int(r["answer"][0])
            target_new = r["choices"][idx]
        except (IndexError, ValueError, TypeError, KeyError):
            skipped += 1
            continue
        out.append({
            "prompt": r["question_sentence"],
            "target_new": target_new,
            "ground_truth": None,
            "question_type": question_type(r["question_sentence"]),
            "question_id": r["question_id"],
            "question_date": r.get("question_date"),
            "question_source": r.get("question_source"),
            "choices": r["choices"],
            "evidence": r.get("evidence"),
        })

    with open(os.path.join(HERE, "realtimeqa_editing.json"), "w") as f:
        json.dump(out, f, indent=2)

    by_type_dir = os.path.join(HERE, "by_question_type")
    os.makedirs(by_type_dir, exist_ok=True)
    counts = {}
    for qtype in QUESTION_TYPES + ["others"]:
        subset = [r for r in out if r["question_type"] == qtype]
        counts[qtype] = len(subset)
        with open(os.path.join(by_type_dir, f"{qtype}.json"), "w") as f:
            json.dump(subset, f, indent=2)

    print(f"{len(out)} usable records ({skipped} skipped - unparseable answer/choices)")
    print("by question type:", counts)


if __name__ == "__main__":
    build()
