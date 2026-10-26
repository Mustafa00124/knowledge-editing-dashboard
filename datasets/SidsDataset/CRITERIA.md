# Sid's Dataset: criteria

What makes a good record, and what the dataset as a whole has to cover.
[`README.md`](README.md) defines the scheme (operations, knowledge form,
queries, tags, determinacy); this file is the quality bar on top of it.

The rules are numbered in one sequence. **Manual rules** come first: a
script can't judge them, so two agents and a person review each. **Automated
rules** follow: `criteria.py` checks them and lists what breaks them. The
delete rule comes last.

**Checking.** `python datasets/SidsDataset/criteria.py` (or `validate.py
--criteria`) prints the checklist; `--all` lists every offending item. The
dashboard shows the same checklist (Datasets, Sid's Dataset, **Criteria
checklist**), with a **Run checks** button that reruns the automated rules
after records change. A check becomes a hard error in `validate.py` once the
records pass it.

**Reviewing a manual rule.** Each manual rule has three marks, pending until
set: **Codex**, **Claude** and **Human**. An agent that has reviewed every
record against a rule marks it:

```bash
python datasets/SidsDataset/criteria.py --mark true-and-unambiguous claude --note "all 240 records"
```

(`done` is the default; pass `pending` to undo.) A person marks theirs by
clicking Human in the checklist. Marks are saved in `reviews.json` next to
this file, which is tracked, so pushing it shares the marks with everyone.
A rule turns green when all three are done.

## Manual rules

**Rule 1. True and unambiguous** (`true-and-unambiguous`). Every answer the
dataset relies on is clearly true or clearly false: original and new answers,
bridge facts, premises, locality references. Leave out facts that experts
dispute, that depend on a date, definition or source, or that have several
defensible answers. An RBox instance must be clear in the real world whatever
the axiom says.

**Rule 2. Stable subjects, self-contained statements**
(`stable-subjects`). A subject is a named thing or class (Pompeii, prime
number), or a description of something the edit does not change. Two kinds
are out:
- a description of the value being edited. In "the volcano that destroyed
  Pompeii is Vesuvius", edited to Etna, the subject means Vesuvius before the
  edit and Etna after, so "How tall is the volcano that destroyed Pompeii?"
  tests nothing stable: the question's own subject moved with the edit;
- a phrase or translation that contains its own answer: "FDR's successor
  succeeded FDR", a museum called "Shakespeare's Birthplace", or a Chinese
  name such as 土卫六 (Titan) that names Saturn.

A statement makes sense on its own: no "under those conditions", no "the
specified", no mention of the edit.

**Rule 3. Determinacy labels, worlds and chains are right**
(`labels-and-worlds`). Each determinate answer holds in every valid world;
each indeterminate query has a concrete answer in every world, and at least
two differ; each world lists the premise that gives way and the side facts
that go with it, and contradicts no firm fact outside the chain (README,
Decisions 1); in TBox, a well-known member leaves its class rather than
staying as an exception; chains are correct, step by step.

## Automated rules

**Rule 4. No repeated edits.** No two records edit the same fact, in the same
or different words. Replace and delete are the exception: each delete
removes its replace record's original fact.

**Rule 5. Enough evidence for every fact.** Every edited fact and premise of
an ABox or TBox record has evidence (README, Evidence), and it is enough: a
stored claim has a quoted sentence or an exact-phrase count of at least 100;
a derived claim has at least two corpus counts or searches showing the
direct form is rare; a definitional premise (the rule combining the others)
needs a reason only.

**Rule 6. The models hold the right things.** From the model audit, for the
four main instruct models (Qwen3-4B-Instruct-2507, Olmo-3-7B-Instruct,
Llama-3.1-8B-Instruct, Mistral-7B-Instruct-v0.1; `AUDIT_MODELS` in
`criteria.py`): every model holds a replace or delete record's original fact.
A fact is held when the direct and paraphrase questions both get the
original answer (RBox: the direct question and both instances). Pending
until the audit runs.

**Rule 7. Locality can catch leaks.** A near unrelated query's answer
differs from the edit's new answer, or a model that leaks the edit still
passes. Delete is exempt: there a leak is an abstention, which any near query
catches.

**Rule 8. One name per relation, and the label fits.** Every relation is in
`RELATIONS.md` under one snake_case name, including relations that only
appear inside an RBox axiom. A record's relation describes its own statement.

**Rule 9. Yes/no answers balanced in RBox,** for direct, derived and
cross-lingual queries, per operation and per topic (within 1). ABox and TBox
are reported, not held to it.

**Rule 10. Far locality prompts vary.** No far unrelated prompt is used more
than 10 times.

**Rule 11. Belief-revision problems are covered.** Per topic, under both
replace and delete: 8 ABox, 6 TBox and 6 RBox edits. ABox: 4 edits of facts
the model likely stores (derivability `very_unlikely` or `unlikely`) and 4
of facts it likely derives (`likely` or `very_likely`). Every ABox and TBox edit's 4 derived
queries are 2 `determinate` and 2 indeterminate (`background_beliefs` or
`derived_beliefs`), with an answer and a chain per world; TBox determinate
queries use a new member named in the prompt, indeterminate ones a
well-known member. Each derived ABox edit has a premise-route query. RBox
derived queries ask "Does it follow that ...?" and are determinate by
construction. Mathematics, and grammar's ABox, may have all derived queries
determinate.

**Rule 12. Relation properties are covered.** Counted on replace records
(deletes mirror them), with minimums in `criteria.py`
(`ABOX_PROPERTY_MIN`, `RBOX_PROPERTY_MIN`), raised as records are added:
- ABox derived queries use each of transitivity, role chain, subproperty,
  functional and inheritance at least 10 times. Inverse belongs in
  paraphrases; symmetry and asymmetry are not required, since they make weak
  questions (a reversed fact, or a "no" that is the same before and after).
- RBox edits change each of transitivity, symmetry, inverse and subproperty
  at least 3 times, and role chain and functionality at least 8 times (RBox
  `0017` and `0018` in every topic).

A property can only be tested on a relation that has it, so new edits are
chosen partly for their relation (README, Shape per topic).

**Rule 13. Every method runs on every edit.** Every core editing method
(the ones marked core in `experiments/run_experiment/dashboard.json`) runs
on every replace and delete record, on each of the four main models, and
really edits. Two checks:
- *Data checks*, live, no GPU (`experiments/run_experiment/sids_requests.py`):
  each record becomes an edit request (prompt = the direct question, target =
  the new answer, or "I don't know" for delete), and every requirement a
  method relies on raises a named error instead of being worked around:
  the subject verbatim and exactly once in the prompt for methods that edit
  at the subject (ROME, AlphaEdit, FiDAL, FiNE, IFMET, LTI), a target, the
  derived answers or per-world answers, an hparams file for every method and
  model.
- *Smoke run*, on gaivi (**Method smoke run** on the dashboard, one launch
  per model; `run_experiment.py --smoke`): each method applied to each record
  one at a time, then checked: the subject maps onto whole tokens, the
  target tokenizes, edited weights really changed and are finite, the model
  still generates, and the original weights come back exactly. Each failure
  is recorded with the record and the exception; a run whose weights can't
  be restored stops. Results older than the records are reported as stale.

**Rule 14. Delete means "I don't know".** Every delete has a replace record
of the same number, removes that record's original fact, and expects "does
not know" (`new_answer: null`) on every query that went through it.

## Design note: derivation trees

Because the route a model uses varies, a derived query can have more than
one defensible answer. After "the capital of France is Rome", "where is the
Eiffel Tower?" gives Paris if the model stores "Eiffel Tower in Paris", and
Rome if it stores "Eiffel Tower in the capital of France". So a derived
query lists its plausible trees (premises and the answer each predicts), and
scoring records which tree the model's answer follows. An answer that
follows no tree is the failure. A tree only counts for a model whose audit
shows it holds that tree's premises. In the records, a tree is one branch
per world: each world's `assumes` and the query's `chain` for that world
(README, Worlds and chains).

Which route a model actually uses can be measured per model: edit one form
and ask the other (after "Vesuvius is 2,000 ft", the descriptive answer
changes for composed and alias routes, not for a shortcut), or probe the
hidden state at the last token of a description with the causal tracing
tools.
