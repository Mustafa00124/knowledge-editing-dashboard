"""Flattens RuleEdit-200 (github.com/Pepper66/DMLE, RuleEdit-200.zip) into
one editing-ready JSON array, ruleedit_editing.json, so the runner can load
and split it like every other dataset file.

The release keeps each rule in its own folder, RuleEdit-200/<rule>/, with
two files:

    f_d.json  the rule's formula and its description
    ins.json  one worked instance of the rule

Each rule becomes three consecutive records here, in that order, each
tagged with `rule_id` and `form` ("formula", "description", "instance"), so
a batch of three edits one whole rule.

Every target is counterfactual (the rule itself is changed, e.g. a
rectangle's area becomes x + y), so the probes are scored against the
edited rule:
  - portability, "Rule_Understanding": the rule's other symbolic or verbal
    form, from the record's own Rule_Understanding field
  - portability, "Instance": the record's Instance prompts, worked answers
    under the edited rule (none of them is the instance that gets edited)
  - locality, "neighborhood" and "distracting": nearby and unrelated rules
    that must not change
  - rephrase_prompt: the record's own rephrasing

What is dropped, and printed when the script runs:
  - Rule 145: its f_d.json is not valid JSON in the release (a missing
    comma at line 59), so the whole rule is left out rather than repaired
    by guesswork.
  - Rules where a record's subject is not in its prompt: the closed-form
    editors find the fact by locating the subject's tokens. A subject that
    differs from the prompt's wording only in case ("Determinant" in "The
    value of a 2x2 determinant") is replaced by the prompt's own spelling;
    a rule with a subject that is absent outright (rule 186, "charge") is
    left out, so every method is scored on the same rules.

Run from this folder: python build_editing_set.py
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "RuleEdit-200")
OUT = os.path.join(HERE, "ruleedit_editing.json")
FORMS = ("formula", "description", "instance")


def _as_list(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _probes(block):
    """{prompt, target_new} with one or several entries -> probe list."""
    if not block:
        return []
    prompts, targets = _as_list(block.get("prompt")), _as_list(block.get("target_new"))
    return [{"prompt": p, "ground_truth": t} for p, t in zip(prompts, targets)]


def _locality(block):
    out = {}
    for key in ("neighborhood", "distracting"):
        part = (block or {}).get(key) or {}
        out[key] = [{"prompt": p, "ground_truth": t}
                    for p, t in zip(_as_list(part.get("prompt")), _as_list(part.get("ground_truth")))]
    return out


def _subject_in_prompt(subject, prompt):
    """The subject as spelled in the prompt, or None when it is not there."""
    if subject in prompt:
        return subject
    match = re.search(re.escape(subject), prompt, flags=re.IGNORECASE)
    return match.group(0) if match else None


def build():
    rules = sorted((d for d in os.listdir(SOURCE) if d.isdigit()), key=int)
    records, dropped = [], {}
    for rule in rules:
        try:
            with open(os.path.join(SOURCE, rule, "f_d.json")) as f:
                formula_description = json.load(f)
            with open(os.path.join(SOURCE, rule, "ins.json")) as f:
                instance = json.load(f)
        except json.JSONDecodeError as exc:
            dropped[rule] = f"invalid JSON in the release: {exc}"
            continue
        raw = list(formula_description) + list(instance)
        if len(raw) != 3:
            dropped[rule] = f"expected 2 formula/description records and 1 instance, found {len(raw)}"
            continue
        rows = []
        for form, record in zip(FORMS, raw):
            subject = _subject_in_prompt(record["subject"], record["prompt"])
            if subject is None:
                dropped[rule] = f"{form} subject {record['subject']!r} does not occur in its prompt"
                break
            truth = _as_list(record.get("ground_truth"))
            rows.append({
                "rule_id": int(rule),
                "rule": record.get("rule"),
                "form": form,
                "subject": subject,
                "prompt": record["prompt"],
                "target_new": record["target_new"],
                "ground_truth": truth[0] if truth else None,
                "rephrase_prompt": record.get("rephrase_prompt"),
                "portability": {
                    "Rule_Understanding": _probes(record.get("Rule_Understanding")),
                    "Instance": _probes(record.get("Instance")),
                },
                "locality": _locality(record.get("locality")),
            })
        else:
            records.extend(rows)
    with open(OUT, "w") as f:
        json.dump(records, f, indent=1, ensure_ascii=False)
    print(f"{len(records) // 3} rules, {len(records)} records -> {os.path.relpath(OUT, HERE)}")
    for rule, reason in dropped.items():
        print(f"  dropped rule {rule}: {reason}")
    return records, dropped


if __name__ == "__main__":
    if not os.path.isdir(SOURCE):
        sys.exit(f"{SOURCE} is missing: download RuleEdit-200 first (Downloads page, or scripts/setup.py)")
    build()
