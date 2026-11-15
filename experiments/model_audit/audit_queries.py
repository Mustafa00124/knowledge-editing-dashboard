"""Which Sid's Dataset queries the model audit asks, each with a stable key
and a short hash of what it asked.

Standard library only: the dashboard backend loads this file as well
(dashboard/backend/model_audit_reader.py), so the audit and the Datasets
page agree on which queries are asked, on their keys and on when a record
changed after a model was audited (its hash no longer matches: stale).

What is asked, and the answer the audit expects before the edit:

- replace/delete: direct, paraphrase and cross-lingual expect
  original_answer.
- insert: direct, paraphrase and cross-lingual pass when the model does not
  already give new_answer (rule "not_new"). Fictional inserts are made up, so
  these are not asked at all.
- propositional (the 3 truth-functional yes/no questions: negation,
  conjunction, disjunction) expect original_answer; under insert they have
  none, so they are not asked.
- related (the 2 one-hop stored answers that depend on the edit) expect
  original_answer.
- every derived query with an original_answer, determinate or not (before the
  edit there is one world), whatever the operation; derived queries without
  one are not asked.
- unrelated_near and unrelated_far expect their reference.
"""
import hashlib
import re

LOCALITY = ("unrelated_near", "unrelated_far")
RELATED = ("related",)
OWN = ("direct", "paraphrase", "cross_lingual")  # the edited fact's own questions


def is_fictional(rec):
    """A made-up insert: not held by any model, so its own questions aren't asked."""
    return rec.get("edit_operation") == "insert" and rec.get("reality") == "fictional"


def query_hash(prompt, expected):
    """Short hash of a question and the answer the audit expects for it."""
    return hashlib.sha256(f"{prompt}\x1f{expected}".encode("utf-8")).hexdigest()[:12]


def all_queries(rec):
    """Yield (key, query_type, language, query) for every query in a record,
    in record order (README, Query type). Keys: direct, paraphrase,
    cross_lingual[zh], propositional[0], related[0],
    derived[2], unrelated_near[0], unrelated_far[0]."""
    q = rec.get("queries") or {}
    for qtype in ("direct", "paraphrase"):
        if q.get(qtype):  # RBox records have no paraphrase
            yield qtype, qtype, "en", q[qtype]
    for item in q.get("cross_lingual") or []:
        yield f"cross_lingual[{item.get('language')}]", "cross_lingual", item.get("language", "en"), item
    for i, item in enumerate(q.get("propositional") or []):
        yield f"propositional[{i}]", "propositional", "en", item
    for i, item in enumerate(q.get("derived") or []):
        yield f"derived[{i}]", "derived", "en", item
    for qtype in RELATED:
        for i, item in enumerate(q.get(qtype) or []):
            yield f"{qtype}[{i}]", qtype, "en", item
    for qtype in LOCALITY:
        for i, item in enumerate(q.get(qtype) or []):
            yield f"{qtype}[{i}]", qtype, "en", item


def expected(rec, query_type, query):
    """(answer, rule) the audit checks for one query, or (None, None) when it
    is not asked. rule "original": passes on the answer; "not_new": passes
    when the model does not already give it (insert's own questions)."""
    insert = rec.get("edit_operation") == "insert"
    if query_type in LOCALITY:
        answer, rule = query.get("reference"), "original"
    elif query_type in ("derived", "propositional") or query_type in RELATED:
        answer, rule = query.get("original_answer"), "original"
    elif insert:
        if is_fictional(rec):
            return None, None
        answer, rule = query.get("new_answer"), "not_new"
    else:
        answer, rule = query.get("original_answer"), "original"
    return (answer, rule) if answer is not None else (None, None)


def audited_queries(rec):
    """Every query the audit asks for a record: dicts with key, query_type,
    language, query, expected, rule and hash."""
    for key, qtype, lang, item in all_queries(rec):
        answer, rule = expected(rec, qtype, item)
        if answer is None:
            continue
        yield {"key": key, "query_type": qtype, "language": lang, "query": item, "expected": answer,
               "rule": rule, "hash": query_hash(item.get("prompt", ""), answer)}


CONTEXT_SUFFIX = "+context"


def _plain(text):
    return re.sub(r"[\W_]+", " ", str(text or "")).strip().casefold()


def context_prompt(facts, prompt):
    """The question with the facts it rests on given first as a reminder."""
    return "Recall: " + " ".join(f.strip() for f in facts) + "\n" + prompt


def in_context_queries(rec):
    """The in-context premise check (REFINEMENTS.md section 8): for a derived
    edit's own direct question, and for every related or derived question
    that rests on facts its prompt does not state, the same question asked
    again with those facts given first ("Recall: P1 P2" then the question).
    The context holds only premises (the edit's premises and the rule
    combining them; or the original fact and the unstated bridges), never
    the answer. Not for inserts or RBox. Dicts like audited_queries, with
    key "<key>+context", base_key, facts and the context prompt."""
    if rec.get("edit_operation") == "insert" or rec.get("box") == "rbox":
        return
    e = rec.get("edit") or {}
    original = e.get("original") or e.get("statement")
    for a in audited_queries(rec):
        item, qtype = a["query"], a["query_type"]
        if a["key"] == "direct" and e.get("premises"):
            facts = list(e["premises"])
        elif qtype in RELATED or qtype == "derived":
            bridges = [] if item.get("bridge_in_prompt") else list(item.get("bridge") or [])
            if not bridges:
                continue
            facts = ([original] if original else []) + bridges
        else:
            continue
        # Premises may name the answer ("Paris is in France" for the country
        # of the Eiffel Tower), but no reminder may be the conclusion itself
        # or the bare answer.
        said = {_plain(f) for f in facts}
        if _plain(a["expected"]) in said or _plain(item.get("fact")) in said or \
                (a["key"] == "direct" and _plain(original) in said):
            continue
        prompt = context_prompt(facts, item.get("prompt", ""))
        yield {"key": a["key"] + CONTEXT_SUFFIX, "base_key": a["key"], "query_type": "in_context",
               "language": "en", "query": item, "facts": facts, "prompt": prompt, "expected": a["expected"],
               "rule": "original", "hash": query_hash(prompt, a["expected"])}


def fact_keys(rec):
    """The queries a fact's "known" rests on: direct and paraphrase; for an
    RBox property (no paraphrase), direct and every derived instance question."""
    q = rec.get("queries") or {}
    if rec.get("box") == "rbox" and "paraphrase" not in q:
        return ["direct"] + [f"derived[{i}]" for i in range(len(q.get("derived") or []))]
    return ["direct", "paraphrase"]
