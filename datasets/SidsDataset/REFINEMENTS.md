# Sid's Dataset: planned refinements

A running list of changes to make to the records. Nothing here has been
applied yet. When an item is done, move it to **Done** with the date and what
changed, and update `README.md` / `CRITERIA.md` / `criteria.py` where the
spec changes.

## Aim

Records should isolate the problem each one tests, so that a failure after
editing is the method's fault, not the record's. Two kinds of record:

- **Main records (stored facts, `very_unlikely`).** What the evaluation
  focuses on. The model holds the edited fact as a stored claim and holds
  everything the questions rely on, so a failure is the editing method
  lacking.
- **Context records (derived facts, `very_likely`).** Like the indeterminate
  questions: they show an inherent challenge of belief revision (the problem
  of derived beliefs), to see how models react to it while editing. Kept, but
  fewer of them.

## 1. Derivability: only the two ends, 6:2 split

Spec changes (README Derivability, CRITERIA Rule 11, `validate.py`
`DERIVABILITY_SCORE`, `criteria.py`):

- [ ] Allowed values become `very_unlikely` and `very_likely` only. Drop
      `unlikely`, `medium` and `likely`: tag a fact only where we are sure it
      is at one end. A fact we can't place confidently is replaced.
- [ ] ABox, per topic, under replace and delete: **6 `very_unlikely` + 2
      `very_likely`** (now 4 stored + 4 derived).
- [ ] TBox: all `very_unlikely` (already none derived; the 16 `unlikely` ones
      are re-rated or replaced).
- [ ] Order: `very_unlikely` records first in each topic/operation (lowest
      ids), then the `very_likely` ones.

Current state (2026-11-09, unique facts, replace = delete):

| Box | very_unlikely | unlikely | likely | very_likely |
| --- | --- | --- | --- | --- |
| ABox | 34 | 6 | 34 | 6 |
| TBox | 44 | 16 | 0 | 0 |

So per topic, ABox goes from 4 stored + 4 derived to 6 + 2: about 2 more
stored edits per topic and 2 fewer derived ones (keep the derived ones whose
premises the models hold, see section 3). Every `unlikely` and `likely` fact is
either re-rated to an end with evidence or replaced.

## 2. Specific question and scoring fixes (from the 2026-11-01 audit)

The audit's TBox misses were mostly question design and scoring, not missing
knowledge (of 52 not-held model-fact pairs: 14 genuinely unknown, 21
inconsistent between the two questions, 9 question design, 8 correct answers
rejected).

Question design:

- [ ] `technology-replace-0019` (and its delete): the direct question "Does
      **every** OSI-approved license permit commercial use?" gets "No" from
      all 4 models while the paraphrase gets "Yes" from all 4. Remove the
      quantifier from the question.
- [ ] `physics-replace-0019`: the paraphrase reverses the yes/no polarity of
      the direct question (direct gold "no", paraphrase gold "yes"); two
      models answer "No" to both. Make both questions the same polarity.
- [ ] `finance-replace-0007`: the paraphrase "Which US government body
      produces the paper banknotes ..." draws "Federal Reserve" or "Treasury"
      from 3 models that got the direct question right. Ask for the agency
      that prints them, by its role.

Scoring (accept equivalent answers; judge rubric or the record's accepted
forms):

- [ ] `physics-replace-0005`: "Hydrogen" judged unclear against "hydrogen
      into helium" (3 models).
- [ ] `technology-replace-0008`: "\n", "Newline character" for LF.
- [ ] `geography-replace-0019`: "Erosion" for wave erosion.
- [ ] General: answers one level broader or narrower than the gold ("Nervous
      system" for central nervous system, "Kidney" for the urinary system,
      "Nice, France" for the region). Decide whether the judge accepts the
      neighbouring level, or the questions name the level asked.

Genuinely unknown TBox facts (wrong on both questions; replace if every model
should hold them): Spenserian stanza (`literature_arts-replace-0007`),
Petrarchan sonnet (`literature_arts-replace-0020`), Mission founders
(`history-replace-0007`); the rest are single-model misses, mostly Olmo
and Mistral (see section 3).

## 3. Find what each model genuinely doesn't know

Goal: for every main model, list each piece of knowledge a record relies on
that the model does not hold, wherever it sits: the edited fact, a premise,
a bridge or revision fact, a propositional side fact, the RBox axiom, or the
original answer a question needs. Those parts (or records) are candidates to
replace.

- [ ] Build the list from the audit (`results/model_audit/runs/<model>/`):
      the fact's direct and paraphrase questions, every `check_fact` and
      `check_relation`, and the cross-lingual original answers.
- [ ] Separate genuine gaps (wrong on every question about it, consistently)
      from question or scoring problems (section 2) before replacing.
- [ ] Not a reason to replace: a derived fact whose premises the model holds
      but whose conclusion it misses. That shows reasoning from known facts is
      already hard before the edit, and is a finding.
- [ ] A reason to replace: a premise or bridge the model doesn't hold (the
      item is dropped for that model anyway). Check stored records too: in the
      audit, 16 to 24 of the 40 stored ABox facts per model had at least one
      failing check.
- [ ] Rerun the audit after the edits (records changed since 2026-11-01).

## 4. Records and questions flagged by reviewers

`reviews.json` holds the red marks; details in `reviews/CLAUDE_FLAGS.md` and
`reviews/CODEX_FLAGS.md`. As of 2026-11-09: 160 records flagged by Codex, 246
by Claude, 317 by either, 89 by both (916 Codex and 674 Claude `problem`
marks, plus `angle` marks).

- [ ] Go through the flags where the gold or the question is unclear, and
      replace those edits or questions rather than patching them.
- [ ] Priority: records flagged by both reviewers, and flags on questions in
      the main (`very_unlikely`) records.

Where the flags are (red marks per record, Codex + Claude): RBox delete 10.1,
TBox delete 4.4, RBox replace 4.4, RBox insert 3.2, ABox delete 2.0, ABox
insert 1.6, TBox insert 1.3, ABox replace 1.2, TBox replace 0.2. By query:
derived 653, cross-lingual 368 (on RBox these are the instance questions),
serves-the-purpose 254. Main themes:

- **Deletes of things that hold by meaning** (most of the RBox delete flags,
  both reviewers). Ancestor is transitive, parent/child are inverses,
  mutualism is symmetric, a sequel is later, assassination is a killing, and
  the instances are well-known facts; after a perfect delete "yes" is still
  right, so "does not know" is not a fair gold. Addressed by section 5.
- **TBox delete: 18 records flagged on every query by Codex** (212 marks).
  Definitional rules (dilatant fluids, mechanical waves, canonization gives
  Saint, OSI licences, Mediterranean dry season), plus re-derivable ones
  (`biology-delete-0005`, spiders via arachnids).
- **Known instances** (RBox replace and insert, mostly Claude): the derived
  conclusion is already a well-known true fact, so the model answers from
  memory whether or not the edit took.

## 5. Contraction: its own records, built on relation properties

Contraction stops mirroring revision (today every delete record removes its
replace record's original fact). It gets its own edits, chosen for the
relation's property, so the gold after deleting is derivable and certain.

- [ ] Focus on **functional** relations (one value per subject) and
      **many-valued** relations (several values per subject), where the
      property decides whether the right answer after the delete is "I don't
      know" or a negative.
- [ ] Derived questions are all **determinate**, and each exact question is
      one the model is unlikely to have seen (not a stated fact), so the
      answer has to come from the relation property, not memory.
- [ ] Before editing, check the model can already answer "no" / "I don't
      know" properly on such questions (the audit's baseline), so a failure
      after editing is the method's.
- [ ] Avoid relations whose property holds by meaning (section 4): deleting
      them cannot make anything unknown.

Example of the intended logic (to confirm): delete "The capital of Australia
is Canberra" (functional). Before: "Is Sydney the capital of Australia?" is
no, because the capital is Canberra and there is only one. After: the reason
for "no" is gone, so the gold becomes "I don't know". For a many-valued
relation, deleting one value removes nothing about the others, so a question
about another value keeps its answer.

Open questions:

- "Many" relations: one-to-many, many-to-many, or both?
- What happens to TBox and RBox contraction: same approach, fictional
  relations, or dropped?
- Replace (revision) keeps its current records; does insert change?

## 6. Related and derived questions (portability)

Scope: **ABox revision (replace)** records. Contraction is reworked separately
(section 5: cardinality and functional properties), with mostly the same
question categories.

Now (CRITERIA Rule 11): every ABox and TBox edit has 4 derived questions, 2
`determinate` and 2 indeterminate (`background_beliefs` or
`derived_beliefs`). Planned, still 4 per record:

- [ ] **1 related** (new query type, `related`): a fact that follows from the
      edit and that the model likely **stores explicitly** (stated often in
      text), so the edit must change a stored answer. Determinate.
- [ ] **2 derived, determinate**: facts that follow from the edit but whose
      answer the model likely does **not** store, so it works them out.
- [ ] **1 derived, indeterminate**: context, like the derived edits; it shows
      an inherent belief-revision problem rather than carrying the method
      comparison.
- [ ] Rate the original answer of the related and the determinate derived
      questions the way edits are rated: `very_unlikely` (related: stored) or
      `very_likely` (derived), with evidence from public sources (infini-gram
      counts, Wikipedia quotes), same bar as CRITERIA Rule 5. Only clear-cut
      ones; a question we can't place is replaced.
- [ ] **Labels** show hops and property: e.g. "Derived · 1 hop ·
      transitivity", "Related · 2 hops · inheritance". The records already
      carry `hops` (1 + number of bridge facts) and `derivation`; the dashboard
      shows them only in the derivation modal.
- [ ] If possible, make the 2 determinate derived questions one 1-hop and one
      2-hop, so hops can be compared within a record.

Notes:

- With `related` as its own query type, "derived" keeps one meaning on
  questions: the answer is worked out, not stored (same sense as the edit's
  derivability).
- A related question is determinate only if the stored fact has no route
  back to the old answer once the edit is in (same check as the derived
  beliefs problem), and it must not just restate the edit through a
  description (a Claude flag theme).
- Current hops on replace records: ABox determinate 42 at 1 hop, 72 at 2,
  70 at 3+; TBox determinate 126 at 2 hops, 7 at 3+, none at 1 (inheritance
  to a new member is 2 hops by construction). So a 1 vs 2 hop contrast works
  for ABox, not for TBox.
- Contraction (section 5) is all determinate already; decide whether it gets
  a related question too.

## 7. Query labels, order and metrics

- [ ] **Propositional labels** show the connective: "Propositional ·
      negation" and "Propositional · and" / "Propositional · or". The records
      already carry it (`form`: slot 0 is always `not`, slot 1 is `and` in 300
      records and `or` in 300); only the label is new.
- [ ] Contraction focuses on **cardinality and functional** properties of
      relations (section 5).
- [ ] **Order** queries from the edit outwards, then to what must not change:

      | Group | Queries, in order |
      | --- | --- |
      | Rewrite | direct |
      | Generalization (portability) | paraphrase, cross-lingual (zh, es), propositional (negation, and/or), related, derived (2 determinate, then 1 indeterminate) |
      | Specificity | unrelated near, unrelated far |

      Now: direct, paraphrase, cross-lingual, propositional, unrelated near,
      unrelated far, derived. Related (stored) comes before derived (worked
      out); everything that should change comes before everything that
      should not.
- [ ] **Paraphrase is Generalization, not Rewrite.** Today it is half-way:
      `sid_evaluation.py` already has `rewrite` = direct only and a separate
      `paraphrase` block, and hyperparameter selection uses them separately,
      but the pooled `reliability` metric is direct + paraphrase and the
      README's Query type table lists paraphrase under Reliability. Change
      both: drop paraphrase from `reliability` (or drop the pooled metric),
      and report paraphrase under Generalization.
- [ ] Places to update: README Query type tables, `SidsRecordCard.jsx` (the
      order constant and labels), `CRITERIA.md`, `sid_evaluation.py` metrics
      (new `related` type too), the model audit's query list, and any table or
      export that lists queries in record order. Existing query keys stay the
      same, so reviews and audit results still match.

## 8. Model audit: in-context premise check for derived facts

For derived edits (`very_likely`, `edit.premises`) and derived questions
whose bridge facts are not in the prompt, add a second audit question: the
same question with the premises the model holds given in the context as a
reminder ("Recall: P1. P2." then the question).

- [ ] The audit dot keeps its colour from the plain question (did the model
      know it directly).
- [ ] The detail view (clicking the dot) adds a row: with the known premises
      in context, does it derive the answer?
- [ ] Reading, per model and fact:

      | Directly | With premises in context | Meaning |
      | --- | --- | --- |
      | known | (any) | holds or derives it unaided |
      | not known | derives it | knows the pieces and can reason with them, but doesn't put them together unprompted (composition gap) |
      | not known | still fails | can't do this inference even when reminded (reasoning gap, or the question is the problem) |

Notes:

- Only premises the model holds (its `check_fact` passes) go in the context:
  a reminder, not teaching. If a premise is not held, record that and skip,
  or mark the row as taught rather than reminded.
- The context must never state the conclusion or the answer string by
  itself; only the premises and, where needed, the rule combining them.
- Same prompt format as the rest of the audit (`render_prompt`), so the only
  difference is the reminder. Cost is small: one extra question per derived
  fact or question per model (40 derived ABox facts, plus derived questions
  with bridges kept out of the prompt).
- Could be run for every derived fact, not only the not-known ones, to see
  whether the reminder ever hurts.
- Code: `experiments/model_audit/audit_queries.py` (new query kind next to
  `check_fact`), the audit summary, and the audit detail in the dashboard's
  record card.

## Ideas (not yet decided)

-

## Done

-
