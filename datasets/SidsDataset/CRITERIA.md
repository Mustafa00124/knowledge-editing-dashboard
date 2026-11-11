# Sid's Dataset: criteria

What makes a good record, and what the dataset as a whole has to cover.
[`README.md`](README.md) defines the scheme (operations, knowledge form,
queries, tags, determinacy); this file is the quality bar on top of it.

The rules are numbered in one sequence. **Manual rules** come first: they
are judgements no script can make, so reviewers make them. Anything that can
be checked automatically is an **automated rule** instead: `criteria.py`
checks those (some with an LLM judge) and lists what breaks them. The delete
rules come last.

**Checking.** `python datasets/SidsDataset/criteria.py` (or `validate.py
--criteria`) prints the checklist; `--all` lists every offending item. The
dashboard shows the same checklist (Datasets, Sid's Dataset, **Criteria
checklist**), with a **Run checks** button that reruns the automated rules
after records change. A check becomes a hard error in `validate.py` once the
records pass it.

**Reviewing.** Reviewers (Codex, Claude, Mustafa, Fengchun, Adarsh) mark
each record under each manual rule, and each of its questions, green (fine)
or red (flagged: a problem, or an example of something wrong with the
benchmark). Unmarked is yellow: not reviewed yet. On the dashboard a click
cycles a reviewer's own dot; `criteria.py --mark` can add a note and say
whether a red mark is a problem or an angle to add or remove. Marks are
saved in `reviews.json` next to this file, which is tracked, so pushing it
shares them.

**Agent reviewers.** Codex and Claude follow the same two rules, with a few
additions:
- Mark only with `criteria.py --mark RECORD ITEM codex|claude green|red`
  (it locks `reviews.json`, so people can mark at the same time). Never
  write `reviews.json` directly, never mark as another reviewer, and never
  edit a record, this file or any code.
- Judge every item yourself; never mark items green in bulk.
- Every red mark gets `--comment` (a one-line reason in plain words) and
  `--kind problem` (something to fix) or `--kind angle` (an idea to add, or
  something tested that teaches us nothing).
- The details of each red mark go in your own flags file,
  `reviews/CLAUDE_FLAGS.md` or `reviews/CODEX_FLAGS.md`: one `## <record
  id>` section per flagged record, with a bullet per red item:
  `- **<item>** (problem|angle): <details>`. That file is the only one you
  edit.
- Don't re-flag what the automated rules (3 onward) already check, unless
  it also makes the item unclear or useless.
- Flag real issues, not style. Spend the most care on derived questions.
- `criteria.py --marks` shows what you have already marked, so a long
  review can resume where it stopped.

## Manual rules

**Rule 1. Clear and sensible** (`clear-and-sensible`). Read the edit, its
questions and its worlds. If something feels off (the edit is confusing or
absurd, a question has more than one fair answer, an expected answer isn't
the obvious one, a world makes no sense), flag it and say what. You don't
need to look hard: a problem here is usually clear at first read.

**Rule 2. Serves the purpose** (`serves-the-purpose`). Is the record useful
for what we want to study? Flag records that look valid but don't help
answer the dataset's question, measure something other than what they
claim, or that suggest a better angle to study.

<details>

**What we are studying.** The dataset asks: under what kinds of knowledge
and belief revision operations does an edit **succeed**, **propagate** to
what follows from it, and **stay contained**? Each part of a record exists
to measure one piece of that:

| Part | What it measures |
|---|---|
| Operation (insert / replace / delete), box (ABox fact, TBox class rule, RBox relation property) | which kind of knowledge and change the result is about |
| Direct, paraphrase, cross-lingual | whether the edit took, beyond its exact wording |
| Propositional (negation, conjunction, disjunction) | whether the edit survives simple logic around the fact |
| Related (near, far) | whether the edit overturns answers the model has **stored** that depend on it |
| Derived (relation property, task, determinacy) | whether the edit propagates to answers the model **works out** from it |
| Worlds (main ABox revision only) | the valid outcomes when what should follow depends on how the model stored its knowledge (Hase et al. 2024) |
| Unrelated near / far | whether the edit stays contained |
| Derivability (stored vs derived), held-by-model tags | why a method succeeds or fails on this record |

A useful record is one where a model's answer can only be read one way: a
right answer means the edit worked in that respect, a wrong one means it
did not. For each part, ask: **if a model gets this right, what have we
learned, and is that the thing this part is meant to measure?**

**Is it the kind of knowledge it claims?**
- ABox is one fact about one named thing. TBox is a rule about a whole class
  ("every X is Y"), not a single fact in disguise. RBox changes how a
  relation behaves, and its two instances really depend on that property.
- Insert adds something new (made up), replace swaps a value, delete removes
  one; a delete's relation is functional or many-valued, and its derived
  queries follow from that (README, Contraction).

**Does the edit take?** The direct question asks for exactly the edited
value; the paraphrase is a real rewording of the same question.

**Does it propagate?** (the most important part)
- Which step carries the edit to this related or derived question
  (transitivity, role chain, subproperty, inheritance, inverse, symmetry,
  functional) and which task (composition, binding, application, or a plain
  answer)? Does answering really need it, and is it what the query names?
- A binding question: does it reach the subject by a different name the
  model holds separately, without restating the edit?
- Is a related question's answer really one the model has seen stated, and a
  derived question's answer really one it has to work out? Does a related
  question just restate the edit through a description?
- Could a model answer right *without* the edit propagating: the answer's
  words in the question, a yes/no default, an answer that is the same before
  and after, another fact that gives it away?
- Could it answer wrong even if the edit propagated perfectly: a bridge fact
  most models won't know, an outcome no world lists?
- Do determinate questions really have one answer whatever the model
  stored, and does the one indeterminate question (main ABox revision only)
  really turn on how it stored things?

**Is it contained?** The near question is close enough (same subject or
relation, a neighbouring fact) that an over-applied edit would get it wrong,
and its answer really is unaffected by the edit.

**Is it measuring something else?** A right or wrong answer might be
explained by how famous the fact is, language ability (names hard to
translate), answer format (numbers, dates, long answers the judge may score
loosely), or the model never knowing the fact. Flag it either way: sometimes
the fix is a rewrite, sometimes it is an angle worth tagging so results can
be sliced by it.

**New angles.** If a record makes you think of something the benchmark
should test and doesn't (a kind of edit, a relation property, a type of
question, a failure you would expect from an editor), or something it tests
that teaches us nothing, flag it and describe the idea.

</details>

## Automated rules

**Rule 3. Stable subjects, self-contained statements.** Checked by script,
with an LLM judge for the parts patterns can't catch:
- no subject is a description of the value being edited (in "the volcano
  that destroyed Pompeii is Vesuvius", edited to Etna, the subject moves with
  the edit); a subject is a named thing or class, or a description of
  something the edit does not change;
- no prompt or translated name contains its own answer ("FDR's successor
  succeeded FDR", 土卫六 for Titan naming Saturn), and no prompt contains the
  edit's new answer unless the question is about it (yes/no checks);
- every statement and prompt stands on its own: no "under those
  conditions", "the specified", "as stated", or mention of the edit.

**Rule 4. No repeated edits, no shared facts between splits.** No two records
edit the same fact, in the same or different words, and no dev record (`dev/`)
edits a fact or uses a subject that a main record (`records/`) uses, so tuning
never sees the test set. Contraction records are their own edits, not the
original facts of revision records.

**Rule 5. Enough evidence for every fact.** Every edited fact and premise of
an ABox or TBox record, and the `fact` of every related and derived query, has
evidence (README, Evidence), and it is enough: a
stored claim has a quoted sentence or an exact-phrase count of at least 100;
a derived claim has at least two corpus counts or searches showing the
direct form is rare; a definitional premise (the rule combining the others)
needs a reason only.

**Rule 6. The models know what the record relies on.** From the model audit,
for the four main instruct models (Qwen3-4B-Instruct-2507, Olmo-3-7B-Instruct,
Llama-3.1-8B-Instruct, Mistral-7B-Instruct-v0.1; `AUDIT_MODELS` in
`criteria.py`), before editing:

- A **stored edit** (`very_unlikely`): at most one model may miss the
  original fact (a fact is held when the direct and paraphrase questions both
  get the original answer; RBox: the direct question and both instances).
  Missed by two or more: replace the edit.
- A **derived edit** (`very_likely`, main ABox revision only): misses are
  fine; they show reasoning from known facts is hard before any edit. Its
  premises must be held (at most one model missing each).
- **Every query's original answer** (paraphrase, cross-lingual, related,
  derived), and every bridge and side fact: at most one model may miss it.
  If the models hold the fact but fail the question, the question is the
  problem (a fill-in-the-blank or an odd format): rephrase it as a plain
  question. If they don't hold it, replace the question.
- An **insert** is made up, so no model can hold it; its bridges must be
  held.

Facts a model doesn't hold are still tagged per model, so the analysis can
ask whether knowing a fact before the edit changes what the edit does.

**Rule 7. Specificity can catch leaks.** A near unrelated query's answer
differs from the edit's new answer, or a model that leaks the edit still
passes. Delete is exempt: there a leak is an abstention, which any near query
catches.

**Rule 8. One name per relation, and the label fits.** Every relation is in
`RELATIONS.md` under one snake_case name, including relations that only
appear inside an RBox axiom. A record's relation describes its own statement.

**Rule 9. Yes/no answers balanced in RBox,** for direct, derived and
cross-lingual queries, per operation and per topic (within 1). ABox and TBox
are reported, not held to it.

**Rule 10. Far specificity prompts vary.** No far unrelated prompt is used more
than 10 times.

**Rule 11. Every record has its record type's queries, and the splits their
shape.** Per README, Queries per record type and Shape per topic:
- Main split, per topic and operation: 8 ABox, 6 TBox and 6 RBox edits. ABox
  revision: 6 stored (`very_unlikely`) then 2 derived (`very_likely`) edits;
  ABox contraction: 4 on functional and 4 on many-valued relations;
  expansion: fictional only.
- Dev split, per topic: 4 ABox, 1 TBox and 1 RBox revision, and 1 per box
  of contraction and of expansion (12); stored edits only; no indeterminate
  queries.
- Derivability is only `very_unlikely` or `very_likely` (edits, related and
  derived queries); `very_likely` edits and indeterminate queries only on
  main-split ABox revision, one indeterminate query per record (mathematics
  and grammar: none; a third determinate query instead).
- Propositional: exactly negation, conjunction, disjunction, in that order.
- Related near is 1 hop, related far 2 or more, determinate derived exactly 2
  (contraction's cardinality question: 1). A record may add up to 2 determinate
  derived queries beyond its type's count where the balance needs them.

**Rule 12. Relation properties and task types are balanced.** Within each
topic's ABox revision records (each split on its own), related and derived
queries together use transitivity, role chain, inheritance and subproperty at
least once each; related-near queries use inverse, symmetry and functional at
least once each; and related and derived queries use the task types
composition, binding and application at least once each, all as evenly as
the topic allows. A topic that can't supply one says why in the records'
`notes`. The edits themselves cover the seven properties about equally: each
is carried by the edited relation of at least one of a topic's 8 main ABox
revision edits, and by 5 to 7 of the dev split's 40. RBox edits cover, per
topic and operation in the main split, transitivity, symmetry, inverse,
functional, subproperty and role chain once each. Not used anywhere: `scope`,
`asymmetry`, reflexivity. The lists are in `criteria.py` (`BALANCE`,
`NEAR_BALANCE`, `TASK_BALANCE`, `RBOX_PER_TOPIC`).

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
  at the subject (ROME, AlphaEdit, FiDAL, FiNE, IFMET, LTI; for TBox and
  RBox records the `edit.prompt_subject` span, at the occurrence it names), a target, the
  derived answers or per-world answers, an hparams file for every method and
  model.
- *Smoke run*, on gaivi (**Method smoke run** on the dashboard, one launch
  per model; `run_experiment.py --smoke`): each method applied to each record
  one at a time, then checked: the subject maps onto whole tokens, the
  target tokenizes, edited weights really changed and are finite, the model
  still generates, and the original weights come back exactly. Each failure
  is recorded with the record and the exception; a run whose weights can't
  be restored stops. Results older than the records are reported as stale.

**Rule 14. Contraction follows the relation's cardinality.** Every ABox
contraction edits a relation tagged `functional` or `cardinality:many`. The
removed fact's own queries (direct, paraphrase, cross-lingual, propositional),
its related queries and its 2-hop derived query expect "does not know"
(`new_answer: null`). Its cardinality question expects "does not know" on a
functional relation (another candidate value, "no" before) and the unchanged
answer on a many-valued one (another value the model holds). Every query
routes through the removed fact.

**Rule 15. Related and derived answers change, and are what they claim.**
Every related and derived query's answer differs before and after the edit
(contraction: becomes "does not know"; the many-valued cardinality question is
the one exception), its `fact` is rated and backed by evidence (related:
stored; derived: worked out), and it does not restate the edit or contain its
own answer.

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
