# Sid's Dataset

Our own knowledge-editing benchmark. This file is the specification the
records are built against. The relations we use, their
properties and the derived questions each property licenses live in
[`RELATIONS.md`](RELATIONS.md).

## Why

Published editing benchmarks test a fairly narrow notion of knowledge, mostly
simple factual triples, and measure generalization with paraphrases. This one
spans a wider range of knowledge (facts, rules, properties of relations)
and measures
generalization with questions that *logically follow* from the edit, so a
method can't pass by matching the surface form of the edit.

> Under what kinds of knowledge and edit operations does a knowledge edit
> succeed, propagate to what follows from it, and stay contained?

## Three levels

```
Edit operation  >  Knowledge form  >  Query type
insert            topic               direct        (1)
replace           box                 paraphrase    (1)
delete                                cross-lingual (2: zh, es)
                                      derived       (4)
                                      unrelated     (2 near + 2 far)
```

Relation properties are not levels: they are the [Relation](#relation) tag
group.

Every ABox and TBox item is one edit plus exactly 12 queries; an RBox item has 7 (below).

### 1. Edit operation

| Key | What it does | Expected answer afterwards |
| --- | --- | --- |
| `insert` | Adds knowledge the model does not hold: a real fact it doesn't know, or a fictional one (see [Reality](#reality)). | The new answer. |
| `replace` | Swaps held knowledge for a false-but-plausible alternative. Counterfactual by construction: the original is something every LLM has seen and holds true. | The new answer, and never the old one. |
| `delete` | Removes knowledge the model does hold. | No longer the old answer: the model should say it does not know, or negate it. See [Delete](#delete). |

### 2. Knowledge form

Two layers: topic, then box.

**Topic.** `geography`, `people` (facts about famous people), `history`,
`finance` (including textbook economic laws), `biology` (including medicine),
`physics`, `mathematics`, `grammar`, `literature_arts`, `technology` (stable
facts only). A diversity control, so a finding about rules
isn't secretly a finding about mathematics. It also keeps the records
organized for browsing.

**Box.** How description logic divides a knowledge base:

| Key | What it holds | DL | Example |
| --- | --- | --- | --- |
| `abox` | Facts about particular individuals | R(a, b), C(a) | Paris is the capital of France. |
| `tbox` | Rules about classes: every C is (or does) D | C ⊑ D, C ⊑ ∃R.D | Every capital is a city. Smoking causes lung cancer. |
| `rbox` | Properties of relations themselves | Trans(R), Sym(R), R ⊑ S, R ≡ S⁻, R ∘ S ⊑ T | "Located in" is transitive. "Sibling of" is symmetric. |

A single TBox or RBox edit should move every individual it covers, which is
why they're expected to behave differently from ABox edits.

That gives 3 knowledge forms per topic (one per box), all available to every
edit operation, so 3 operations × 10 topics × 3 boxes = 90 cells.

### 3. Query type

Fixed per item: **1 direct, 1 paraphrase, 2 cross-lingual, 4 derived, 2 near
unrelated, 2 far unrelated**. Fixing the counts gives every item the same weight in every
metric.

| Key | Count | What it is | Metric |
| --- | --- | --- | --- |
| `direct` | 1 | The edited fact asked as a question, in the edit's own wording. | Reliability |
| `paraphrase` | 1 | The same question in different words. | Reliability |
| `cross_lingual` | 2 | The direct question asked in Chinese (`zh`) and Spanish (`es`), expecting the answer in that language. | Cross-lingual |
| `derived` | 4 | A question whose answer follows from the edit through a property of the relation (see below). | Generalization |
| `unrelated_near` | 2 | Shares the subject, the relation or the topic, but does not follow from the edit. "What is the official language of France?" after editing France's capital. | Locality |
| `unrelated_far` | 2 | Nothing in common with the edit. | Locality |

Near unrelated queries are what make locality informative: far-only locality
is close to 100% for almost every method.

#### RBox items: 7 queries

An RBox edit changes a property of a relation ("'lends to' is transitive"), not
a fact about an entity, so its record states only the property and carries 7
queries:

| Key | Count | What it is | Metric |
| --- | --- | --- | --- |
| `direct` | 1 | The property itself: "Is the relation 'lends to' transitive?" | Reliability |
| `derived` | 2 | The property applied to real entities, with the premises in the prompt: "JPMorgan Chase lends to Goldman Sachs, and Goldman Sachs lends to Citadel. Does it follow that JPMorgan Chase lends to Citadel?" Derivation `instantiation`. | Generalization |
| `cross_lingual` | 2 | The first instance question in Chinese and Spanish. | Cross-lingual |
| `unrelated_near` | 1 | The same property asked of another relation in the topic ("Is the relation 'is a subsidiary of' transitive?"). | Locality |
| `unrelated_far` | 1 | A different property of an unrelated relation ("Is the relation 'is married to' symmetric?"). | Locality |

There is no paraphrase query. In the model audit an RBox fact counts as known
when its direct question and both instance questions get the original answer.

#### Cross-lingual queries

The edit is always made in English. The two cross-lingual queries ask the
direct question in Chinese and Spanish, to see whether the edited knowledge
is stored as language-independent knowledge or only as an English string.
Chinese is far from English (different script, so the answer can't be copied
token for token); Spanish is close. The gap between them is part of the
finding.

- Each records its `language` and its original and new answers written in
  that language (e.g. 里昂 for Lyon). The judge accepts equivalent forms,
  including names left untranslated.
- For `replace` and `delete`, the model must answer the *original* fact
  correctly in that language before editing, like a bridge fact; otherwise
  that query is dropped for that model. Base models can be weak in Chinese,
  so expect some drop-off.
- They are reported as their own metric, not folded into reliability, so a
  model that is weak in one language doesn't drag down English reliability.

#### Derived queries

What can be derived depends on the relation's properties. A record names
only its `relation`; `RELATIONS.md` is the one place each relation's tags are
defined, along with the question template each tag gives. Summary:

| Derivation | Comes from | Example |
| --- | --- | --- |
| `symmetry` | Sym(R) | Edit: Billy is a sibling of Manny. Ask: is Manny a sibling of Billy? |
| `inverse` | R ≡ S⁻ | Edit: Ann is Billy's parent. Ask: who is Ann's child? |
| `asymmetry` | Asym(R) | Edit: Ann is Billy's parent. Ask: is Billy Ann's parent? (expected: no) |
| `transitivity` | Trans(R) + a bridge fact | Edit: Lyon is in France. Bridge: France is in Europe. Ask: is Lyon in Europe? |
| `chain` | R ∘ S ⊑ T + a bridge fact | Edit: she was born in Lyon. Bridge: Lyon is in France. Ask: which country was she born in? |
| `subproperty` | R ⊑ S | capital of ⊑ located in. Ask: which country is Lyon located in? |
| `functional` | R has one value per subject | Replace and delete. Ask: is Paris still the capital of France? (expected: no; under delete, does not know) |
| `composition` | Any relation + a bridge fact | Edit: the capital of France is Lyon. Bridge: the Rhône flows through Lyon. Ask: which river flows through the capital of France? |
| `inheritance` | TBox C ⊑ D + a known member | Edit: every capital is a port. Ask: is Paris a port? |
| `instantiation` | RBox axiom + instance facts | Edit: "borders" is symmetric. Ask an instance in the reverse direction. |
| `binding` | No relation property | The edit reached through an alias, a bound individual, or (TBox) a new member of the class. Ask: "IMF abbreviates International Monetary Fund. Where is the headquarters of the organization referred to by IMF?" |
| `application` | No relation property | The edit used to fill a field, compute a value or run a workflow. Ask: "A courier must visit the NYSE trading-floor building. Which city should be the courier's destination?" |
| `scope` | No relation property | The boundary of what follows; the gold is "no" or "cannot be determined". Ask: "Given only the IMF headquarters city, is a particular country Z an IMF member?" |

`composition` is the multi-hop question (as in MQuAKE): the edited fact is
one hop and a fact the model already knows is the next. It needs no relation
property, so every relation supports it, which helps items whose relation has
few tags still reach 4 derived queries.

`binding`, `application` and `scope` are **task types** rather than relation
properties (they come from the finance/technology replacement panel, whose
four derived slots are binding, composition with a supplied premise,
application and scope). An item may use either kind; analysis can split
generalization by derivation type. When a derived prompt supplies its own
premise ("Chicago is in Illinois. In which state is ..."), the premise is
still listed in `bridge` and `bridge_in_prompt` is true: the model is told the
fact, so there is nothing to check before editing. `discriminates: false`
marks a derived query whose answer is the same before and after the edit: it
tests consistency, not the new value, so report generalization with and
without those.

Reflexivity is not used: "a R a" doesn't depend on the edit. Note that
"brother of" is not symmetric (the other person may be a sister), which is
why the symmetric example uses "sibling of".

Each derived query records its `derivation` (the property that produced the
answer), its `hops` (1 + the number of bridge facts), and the `bridge` facts
it relies on. A derivation that goes through the inverse relation's tags
names it in `via`. The model must answer every bridge fact correctly
*before* editing, otherwise a wrong derived answer is a missing fact rather
than a failed edit. Items whose bridges fail are dropped per model, not
counted as failures.

To make that checkable, every bridge fact a derived query does not state in
its own prompt, and every premise, has a **check**: a question with a short
answer in the record's `checks` list (`facts_to_check()` in `validate.py`
lists what needs one). Every relation property a derivation relies on
(`located_in` is transitive, `has_capital` is the inverse of `capital_of`)
has one in `relation_checks.json`, keyed by relation and tag. Where a tag
holds for the dataset's pairs but not for every pair in the world (one author
per single-author novel), the check is phrased around that kind of case. The
model audit asks all of them, and reports per model how many derived queries
have their whole chain known (`derived_supported`). On the Datasets page,
each ABox and TBox derived query, and each edit with premises, has a button
that draws the chain (the edit, the facts to know, the relation property,
the rule, the answer) with each model's audit result on every check.

An item uses whichever derivations its relation supports, but always has 4
derived queries, so items with symmetric or transitive relations aren't
weighted more heavily than items without.

#### Delete

Deleting removes a fact; we then ask the direct, paraphrase, cross-lingual and
derived questions again. Success means the model **no longer gives the old answer**,
and instead either:

- `abstain`: says it does not know, or
- `negate`: says the fact does not hold.

Both count as success, and which one the model chose is recorded. For
relations with many possible values (`cardinality: many`, e.g. "speaks
language") this is an open-world test: removing one value doesn't make any
other value true, so abstaining is the honest answer. For functional
relations a negation is also reasonable.

Derived queries under delete must route **through the deleted fact**. After
deleting "Paris is the capital of France", "Which river flows through the
capital of France?" should no longer get "Seine", because the only way to
reach Paris from that question is the deleted link. But "Which country is
Paris in?" is fine to still answer: the model knows it independently, so it
is not a consequence of the deleted fact. In practice delete items lean on
`inverse`, `symmetry` and `composition` queries whose wording names the
deleted relation.

Every derived query is expected to lose its answer the same way: when a link
in the chain is missing, the model should say it does not know. That includes
`functional` queries ("Is Paris the capital of France?"), which under delete
ask whether the removed value still holds. Note that the judge reads a bare
yes or no as an answer, never as `NONE`, so on yes/no queries only an
abstention passes; a plain "no" is scored `OTHER`.

## Tags

Besides its taxonomy coordinates, every record carries tags. Tags are **not
levels or layers** of the taxonomy: they describe the item further, so
results can be sliced by them within any cell.

### Familiarity

How familiar the knowledge involved is likely to be to a model (does
replacing a very familiar fact fail more often than an obscure one?).

It has three tiers, each taking one of five values:

```json
"familiarity": { "fact": "very_high", "subject": "very_high", "object": "high" }
```

| Tier | What it rates | When it applies |
| --- | --- | --- |
| `fact` | The original fact as a whole (France's capital is Paris). | Replace and delete. Null for insert, which has no original fact. |
| `subject` | The edit's subject (France). | Always. |
| `object` | The edit's object: the new value for insert and replace (Lyon), the removed value for delete. | When the edit has an object; null otherwise. |

Only binary knowledge has an object. RBox edits are about one relation
("`located_in` is transitive"), so they have no `edit.object` and only the
`fact` and `subject` tiers apply. Separating the tiers lets familiarity of the
entity be told apart from familiarity of the fact: a very familiar subject
can still have an obscure fact ("France's national flower").

| Value | Score | Fact example | Entity example |
| --- | --- | --- | --- |
| `very_low` | 1 | The mayor of a small town. | A small village. |
| `low` | 2 | The capital of a small province. | A regional politician. |
| `medium` | 3 | The author of a moderately well-known novel. | A mid-sized city. |
| `high` | 4 | The capital of Australia. | Lyon. |
| `very_high` | 5 | The capital of France. | France. |

Records store the words. For analysis, each maps to an integer score from 1
to 5 (`FAMILIARITY_SCORE` in `validate.py`, `score` in the dashboard's
taxonomy; `familiarity_scores(record)` gives all three tiers at once, with
`None` where a tier doesn't apply). The scores are ordinal: the steps are
ranked but not necessarily equal, so rank correlations (Spearman, Kendall)
are the safer choice than Pearson.

> **Familiarity is a proxy.** We can't see any model's training data, so the
> tag is our estimate of how often the knowledge appears in text a model is
> likely to have seen. The criteria for assigning it will be detailed later.

### Derivability

How likely a model is to **derive** the edited fact or rule from other
knowledge it holds, rather than store it directly. The scale runs between
two ends:

- **Axiomatic (stored):** the model holds the fact directly, as a base
  claim.
- **Derived (composed):** the model composes the fact from other knowledge
  it holds, its premises.

The tag is set for ABox and TBox replace and delete; `null` for insert (a new
fact can't follow from what the model already holds, or it wouldn't be new)
and for RBox.

| Value | Score | Example |
| --- | --- | --- |
| `very_unlikely` | 1 | Paris is the capital of France (stated everywhere, follows from nothing). |
| `unlikely` | 2 | Lyon is in France. |
| `medium` | 3 | The Eiffel Tower is in Europe. |
| `likely` | 4 | The Eiffel Tower is in France (it is in Paris, and Paris is in France). |
| `very_likely` | 5 | Every square is a polygon (every square is a rectangle, every rectangle is a polygon). |

Editing a fact a model derives leaves its premises pointing at the old
answer, so the model may re-derive it and slide back. That is the failure
this tag is meant to expose. Rules:

- **Premises are listed** in `edit.premises`: required at `likely` and
  `very_likely`, optional below. They are checked before editing, like bridge
  facts: if the model doesn't hold them, it can't derive the fact, and the
  item is dropped for that model.
- **Premises stay unchanged.** The edit asks only for the conclusion to
  change, so premises are expected to keep their answers; ask them as the
  near unrelated queries (the derived template does). The result is a
  deliberately inconsistent world, and whether the model holds the edit
  anyway or reverts to what its premises imply is the finding.

Like familiarity, the scores are ordinal (`DERIVABILITY_SCORE` in
`validate.py`, `score` in the dashboard's taxonomy).

> **Derivability is model specific.** Whether a fact is axiomatic (stored)
> or derived (composed) really depends on the model: one model may store "the
> Eiffel Tower is in France" directly, another may work it out from its
> premises each time, and we can't observe which. The tag is our estimate of how likely a model is to
> derive it, using our own intuition and criteria. Those criteria will be
> detailed later.

### Temporal

How the fact sits in time. ABox facts only; `null` for TBox and RBox, since
rules and relation properties aren't events.

| Value | What it is | Example |
| --- | --- | --- |
| `event` | Happened at a point in time. | Marie Curie discovered radium in 1898. |
| `timeless` | Not tied to a moment: facts that are always true, and standing states that hold over a period. | 7 is prime. Paris is the capital of France. |

### Reality

Whether an inserted fact is true in the world. Insert only; left out for
replace and delete, which always edit a real fact.

| Value | What it is | Pre-edit audit | Example |
| --- | --- | --- | --- |
| `real` | A true fact the model may not hold: obscure, or newer than its training data. | Asked: the item is kept for a model only if it does not already give the new answer. | The 2024 Abel Prize went to Michel Talagrand. |
| `fictional` | A made-up fact, about an invented subject or an empty slot of a real one. No model can hold it. | Not asked: the item is not held by construction. Its checks (the real facts its derived queries rely on) are still asked. | Velmora is the capital of Kestria. The Louvre's official mascot is a cat named Mona. |

A fictional fact must contradict nothing true: if the slot already has a real
value (the Louvre's director), the edit is a replace, not an insert. Derived
queries of a fictional insert reach real knowledge only through bridge facts
the model holds or that the prompt states, so their chains can be checked.
The other tags apply as usual, except that insert has no original fact:
`familiarity.fact` and `derivability` are null. An invented subject is
`very_low` familiarity; a real subject keeps its own.

### Relation

Two facets of the record's relation, for every box. For RBox the relation is
the one whose property is edited (`relation`, also `edit.subject`).

| Facet | Stored as | What it is |
| --- | --- | --- |
| name | `relation` | The relation, e.g. `located_in`. Must be in `RELATIONS.md`. |
| properties | not stored | The relation's property tags in `RELATIONS.md`, looked up with `load_relations()` in `validate.py`. |

Any of `symmetric`, `asymmetric`, `inverse:S`, `transitive`, `chain:S->T`,
`subproperty:S`, `functional` and `cardinality:many` (see the Tags table in
`RELATIONS.md`, which also lists the derived question each one licenses). A
relation may have none. They stay in `RELATIONS.md` only, so a relation's
properties are defined in one place; the dashboard shows them on each record
from that table.

The causal vs associative distinction was dropped on 2026-10-22: records no
longer need a `relation_semantics` tag. It is still accepted (`causal` or
`associative`) but no longer checked against the Semantics column of
`RELATIONS.md`, which stays for now.

### Determinacy

*Prototype, on branch `sids-determinacy-prototype`.* Following Hase et al.
2024, "Fundamental Problems With Model Editing" (TMLR, arXiv 2406.19354), an
edit does not always say what the rest of the model's beliefs should become.
This is an **ABox** tag: TBox and RBox edits change a rule or a property, and
their derived queries already spell out what follows. `determinacy.type`
records which case an ABox item is, with a one or two sentence
`determinacy.why`:

| Type | What it is | Example |
| --- | --- | --- |
| `determinate` | The edit, the relation's properties (or the edited rule) and facts the model surely holds leave exactly one world: every derived answer is forced. | "The capital of Australia is Sydney." Is Canberra the capital of Australia? No (functional). Sydney is the capital of which country? Australia (inverse). |
| `many_worlds` | The edit forces something to change but not what (Hase's *problem of many possible worlds*): several worlds fit, none preferred. Typical sources: a "same X as" relation, or a functional constraint that forces dropping some values. | "Paris and Berlin are in the same country." Both in France, or both in Germany: which country is Berlin in? |
| `background_beliefs` | The conclusion depends on which other facts or axioms the model holds and how it stores them (Hase's *problem of background beliefs*). | "The capital of France is Lyon." In which city is the Eiffel Tower? Paris if the model stores "the Eiffel Tower is in Paris", Lyon if it stores "the Eiffel Tower is in the capital of France". |

The last two are **indeterminate**. They carry `worlds`, 2 to 4 of
`{id, assumes, summary}`: `assumes` lists the facts or axioms that world keeps
or picks. Each of their derived queries has `new_answer: null` and
`world_answers` (`{"w1": ..., "w2": ...}`, one answer per world), and at least
two derived queries must differ across worlds. Direct, paraphrase and
cross-lingual queries keep a single `new_answer`, since the edit itself is not
in doubt. For indeterminate RBox items the cross-lingual queries ask the
property itself rather than the first instance, since every instance is in
doubt. Determinate items have no `worlds` and keep a single `new_answer` on
every derived query. Scoring does not use `world_answers` yet: a natural
reading is that an answer passes if it matches some world, and which world it
matches is recorded, as in the derivation trees of `CRITERIA.md`.

## Evaluation

We use our own evaluation functions rather than EasyEdit's, because delete
needs generated answers rather than token probabilities, and the query types
map directly onto metrics:

| Metric | Over | Reported as |
| --- | --- | --- |
| Reliability | direct + paraphrase (2) | one number |
| Cross-lingual | cross_lingual (2) | one number, plus per language |
| Generalization | derived (4) | one number, plus per derivation type |
| Locality | unrelated near + far (4) | one number, plus near and far |
| Fluency | the 10 English generations | one number |

Fluency leaves out the cross-lingual answers, since n-gram based fluency
scores aren't comparable between Chinese and English text.

### Answering and judging

Every query is asked as a free-form question in a fixed template,
`Question: <prompt>` / `Answer:`, with a few neutral worked examples first so
base models answer briefly, and generation stops at the first line break (or
a small token cap). Instruct models get the question through their chat
template.

Each answer is scored by an **LLM judge**, Qwen3-4B-Instruct-2507 run
locally with greedy decoding (`experiments/sid_eval/judge.py`, rubric
`sid-judge-v3`). The judge runs after generation (the edited model is
unloaded first), so only one model is on the GPU at a time. There are no
alias or forbidden lists.

**The judge only labels; code decides pass or fail.** The judge never decides
whether an edit worked. It sees one question, one response and the
candidate answers (`original_answer` and `new_answer`, shown as A and B in
an order that varies per query so position bias cancels out), and returns
JSON with a short reason and one label:

| Label | The response |
| --- | --- |
| `ORIGINAL` / `NEW` | asserts that candidate |
| `OTHER` | asserts a specific answer that matches neither |
| `NONE` | commits to no answer: does not know, refuses, says no such value exists, or only denies a candidate |
| `UNCLEAR` | hedges between answers, contradicts itself with no final answer, or is unintelligible |

Its instructions pin down the cases that are otherwise ambiguous:
- **Truth doesn't matter.** Candidates may be counterfactual, and the judge must not use its own knowledge.
- **Answers match on meaning, not wording, and never on truth.**
  - Other words, synonyms and descriptions of the same concept match.
  - So do a common shorter name ("New York" for New York City), a name without a version (GPL for GPLv2), any language, and extra detail.
  - A quantity must be the same value.
  - Naming a different thing doesn't match, and neither does a category so broad it fits clearly different answers (Europe for France, "financial services" for insurance).
- **Yes and no are answers.** A bare yes or no is read against the question: "No" to "can an observer read it?" matches "unable to read".
- **Several answers.** If a response mentions several, the final assertion counts. Mentioning a value while denying it does not assert it.
- **Responses are data.** The judge never follows instructions written inside one.

Fifteen worked examples precede every call: a counterfactual answer, a short name, a missing version, a description, a too-broad category, and yes/no replies that do and do not match. The judge writes what the response answers before choosing a label. Unparseable judge replies and empty responses become `UNCLEAR`, which is excluded from scores and counted separately.

Every model audit also has the judge label a fixed set of 60 hand-labelled
cases (`experiments/sid_eval/judge_cases.json`). They cover counterfactual
answers, answers that are right in other words, and real wrong answers that
must stay wrong. The agreement is saved with the run (`judge_check`), so a
rubric change shows up as a number.

The label is turned into a score by a fixed table:

| Stage | Operation | Pass when the label is |
| --- | --- | --- |
| model audit (pre-edit) | `replace`, `delete` | `ORIGINAL` |
| model audit (pre-edit) | `insert` (`real`) | `NONE` or `OTHER` (the new fact is not already known); `fictional` inserts aren't asked |

In the model audit the judge is shown only the answer that row needs: the
original answer for replace and delete, the new answer for insert. Locality
questions aren't asked there, because an edit run takes its own pre-edit
baseline.
| edit | `replace`, `insert` | `NEW` |
| edit | `delete` | `NONE` (abstains or only negates) |

Locality queries use a second prompt with the same rules. It compares the
post-edit response with the model's own pre-edit response and labels them
`SAME`, `DIFFERENT` or `UNCLEAR`. Truth is again ignored, and both responses
declining to answer counts as `SAME`.

## Records

> **On branch `sids-determinacy-prototype`**, `records/` holds replace items
> for people, finance and geography only: a 9-record ABox prototype, one per
> topic and [determinacy](#determinacy) type (`0001`-`0003`, in the order
> determinate, many_worlds, background_beliefs), plus the original TBox
> (`0011`-`0020`) and RBox (`0021`-`0030`) replace items of those topics,
> unchanged from `main`. The sections below on imported panels, insert and
> delete records, and the size goal describe the full dataset on `main`.

### Layout

One JSON file per edit, grouped by topic and then edit operation:

```
datasets/SidsDataset/
  README.md, RELATIONS.md     the spec and the relations catalogue
  relation_checks.json        one audit question per relation property in use
  validate.py                 checks every record against all three
  examples/                   templates (not part of the dataset)
    geography-replace-0001.json
    geography-delete-0001.json
  records/
    <topic>/<edit_operation>/<topic>-<edit_operation>-NNNN.json
    e.g. records/geography/replace/geography-replace-0001.json
```

One file per edit keeps each record reviewable on its own, keeps Git diffs
and merges small, and makes the browsing order (topic, then operation)
the folder order. The coordinates are still stored inside each record, so a
loader never has to parse paths. `NNNN` counts up within a topic and
operation; ids are never reused.

### Adding a record

1. Copy the closest template from `examples/` into
   `records/<topic>/<edit_operation>/`, and rename it to the next free id
   (`id` and the file name must match).
2. Fill in the coordinates, the relation (it must be in `RELATIONS.md`; add
   it there first if not), the edit, and the 12 queries. The relation's tags
   are not copied into the record; code that needs them looks them up with
   `load_relations()` in `validate.py`.
3. Run the validator from the project root:

   ```bash
   python datasets/SidsDataset/validate.py
   ```

   It prints every problem with the file and field, then a count per topic
   and operation. Fix everything it reports before committing.

### Format

Every field below is required unless marked optional. Unknown fields are
rejected, so typos don't silently drop data.

| Field | Type | Rule |
| --- | --- | --- |
| `id` | string | `<topic>-<edit_operation>-NNNN`, same as the file name |
| `edit_operation` | `insert` \| `replace` \| `delete` | |
| `topic` | one of the 10 topic keys | |
| `box` | `abox` \| `tbox` \| `rbox` | |
| `relation_semantics` | `causal` \| `associative`, optional | no longer required or checked against `RELATIONS.md` (see [Relation](#relation)) |
| `determinacy` | object, optional | `{type, why}`: `type` one of `determinate`, `many_worlds`, `background_beliefs`, `why` a non-empty string (see [Determinacy](#determinacy)) |
| `worlds` | list | 2 to 4 `{id, assumes, summary}` with unique ids and a non-empty `assumes` list; present exactly when `determinacy.type` is `many_worlds` or `background_beliefs` |
| `relation` | string | a relation in `RELATIONS.md` |
| `edit.statement` | string | the edit as one or more sentences |
| `edit.subject` | string | |
| `edit.object` | string | required except for `rbox`, which has none; for delete, the removed value |
| `edit.old_object` | string | replace only, and required there when the edit has an object |
| `edit.premises` | string list | the facts or rules the edited one follows from; required when `derivability` is `likely` or `very_likely`, optional when it is set lower, absent when it is null |
| `edit.axiom` | string, optional | DL form for TBox and RBox, e.g. `Trans(located_in)` |
| `edit.original` | string, optional | the fact or rule before the edit, as a sentence |
| `edit.scope` | string, optional | what the edit covers and what it leaves alone |
| `edit.fixture` | bool, optional | true for a constructed fact the model can't already know (e.g. loan L1's payment): `edit.original` is loaded into the model first, the baseline is taken after that, and the edit is applied separately |
| `queries` | object | the 12 queries (7 for RBox), below |
| `familiarity` | object | tiers `fact`, `subject`, `object`, each `very_low` \| `low` \| `medium` \| `high` \| `very_high` or null; `fact` null exactly for insert, `subject` always set, `object` set exactly when the edit has one |
| `derivability` | `very_unlikely` \| `unlikely` \| `medium` \| `likely` \| `very_likely` \| null | set for `abox` and `tbox` replace and delete, null otherwise; a tag, not a layer |
| `temporal` | `event` \| `timeless` \| null | set for `abox`, null otherwise; a tag, not a layer |
| `reality` | `real` \| `fictional` | insert only, and required there; left out otherwise |
| `checks` | list | one `{fact, prompt, answer}` per fact `facts_to_check()` lists (premises, then bridge facts not stated in a prompt), with `fact` copied exactly; empty or absent when there are none. The model audit asks each before editing |
| `notes` | string, optional | |
| `source` | object, optional | provenance for imported items: the source document, its item ID and title, its own familiarity rating and its grounding link |

Each query:

| Field | Type | Rule |
| --- | --- | --- |
| `prompt` | string | the question as asked |
| `original_answer` | string \| null | the answer before the edit; null for insert; required on reliability and cross-lingual queries under replace and delete, optional on derived queries (null when the old-world answer isn't defined) |
| `new_answer` | string \| null | the answer after the edit; null for delete; required for insert and replace, except on derived queries of an indeterminate record, where it is null |
| `world_answers` | object | derived only, exactly on indeterminate records: one non-empty answer per world, keyed by exactly the record's world ids |
| `reference` | string, optional | locality queries only (which have no answer fields): a reference answer for auditing; the scoring gold is the model's own pre-edit answer |
| `language` | `zh` \| `es` | cross-lingual only, one of each |
| `derivation` | see derived queries | derived only |
| `hops` | integer | derived only; 1 + number of bridge facts |
| `bridge` | string list | derived only; empty if none |
| `via` | string, optional | derived only; the relation whose tag licenses the derivation, when it isn't the edited relation |
| `bridge_in_prompt` | bool, optional | derived only; the bridge facts are stated in the prompt, so they aren't checked before editing |
| `discriminates` | bool, optional | derived only; false when the answer is the same before and after the edit |

`queries` holds `direct` and `paraphrase` (one object each), and
`cross_lingual` (2), `derived` (4), `unrelated_near` (2) and `unrelated_far`
(2) as lists. The validator also checks that each derivation's tag exists on
the relation it uses, that `functional` appears only under replace,
`inheritance` only for TBox, `instantiation` only (and always) for RBox, and
that transitivity, chain, composition and inheritance have a bridge fact.

The templates in `examples/` are complete, valid records: a replace
(`geography-replace-0001`) and a delete (`geography-delete-0001`) of facts
very unlikely to be derived, and a replace of a fact likely to be derived,
with its premises (`geography-replace-0002`).

### Imported panels

`records/finance/replace/` and `records/technology/replace/` hold the 40
items of the finance and technology replacement panel (v2): five per
combination of ABox/TBox and associative/causal in each topic, so ten ABox and
ten TBox items per topic. Their derived queries use the task types (binding,
composition with a supplied premise, application, scope), and each keeps the
panel's ID, familiarity rating and grounding link in
`source`. The ABox causal items are **fixtures**: named, constructed events
(loan L1, transfer T1, connection S1, ...) whose original outcome is loaded
before the baseline, so they measure controlled-memory editing rather than
recall; report them separately from items about real facts.

`finance-replace-0021` to `0030` and `technology-replace-0021` to `0030` are
the **R-box relation-property panel**: 20 RBox replace edits (140 queries),
one per property change: transitivity added and removed, symmetry added and
removed, a subproperty added or removed, functionality, inverse functionality
and relation disjointness added, and an inverse mapping and a composition path
replaced. Slot `0025` was the panel's reflexivity item (FR5, TR5) until
2026-10-22; it is now a subproperty edit and has no panel `source`.
They follow the 7-query RBox shape above, in plain English: the direct query
asks whether the relation has the property (yes or no, or the new inverse
relation's name), and the two `instantiation` queries apply it to real
companies or software with the premises in the prompt ("Does it follow
that ...?"). Locality queries use other relations; their `reference` is the
logical answer, while the scoring gold stays the model's own pre-edit answer.

### Replace records for the other topics

`records/<topic>/replace/` for geography, people, history, biology, physics,
literature_arts, mathematics and grammar hold 20 ABox and TBox items each,
ten per box (five associative, five causal), numbered in the panel's order: `0001`-`0005` ABox associative,
`0006`-`0010` ABox causal, `0011`-`0015` TBox associative, `0016`-`0020` TBox
causal. All 160 are real facts (no fixtures), written for variety. The
mathematics and grammar causal cells (added 2026-10-13) use events from the
history of the subject for ABox (Ramanujan's letter to Hardy, the Oxford comma
case, Webster's spellings) and causal rules for TBox (adding a constant leaves
a standard deviation unchanged; language contact raises borrowing):

- **Relations.** 7 to 16 relations per topic, mixing symmetric, transitive,
  functional, inverse, chain and causal ones, so derived queries lean on
  relation properties (symmetry, inverse, transitivity, chain, functional,
  inheritance) and multi-hop composition rather than only the task types.
  Every TBox item has at least one inheritance query on a well-known member.
- **Familiarity.** Each cell spans at least three `fact` values, with at least
  one at `medium` or below and one at `very_high`.
- **Derivability.** Each cell spans at least three values, with at least one
  `likely` or `very_likely`. Those items list their premises in
  `edit.premises` and ask them as the near unrelated queries.

Each of these topics also has 10 RBox replace items, one per property change
in the panel's order (transitivity added, transitivity removed, symmetry
added, symmetry removed, subproperty added or removed, functionality added,
inverse functionality added, relation disjointness added, inverse mapping
replaced, composition path replaced): `0021`-`0030`. Across all ten topics,
the panel's included, slot `0025` adds a false
subproperty (R ⊑ S, e.g. "'is a symptom of' is a subproperty of 'causes'") in
biology, physics, grammar, literature and arts and mathematics, and removes a
true one (e.g. "'is the mother of' is not a subproperty of 'is a parent of'")
in geography, people, history, finance and technology, so its yes and no
answers balance. It held a reflexivity edit until 2026-10-22; reflexivity was
dropped because its only consequence is a self-instance ("Paris is twinned
with itself"), which tests nothing compositional. They use the same 7-query
shape as the panel, but edit the
topic's real relations ("borders" loses symmetry, "is located in" loses
transitivity), so their instantiation queries ask about well-known pairs,
where the edit pushes against world knowledge.

Two geography records share ids with the `examples/` templates; the
validator only requires ids to be unique within `records/`.

### Delete records

`records/<topic>/delete/` mirrors `replace/` one to one: `<topic>-delete-NNNN`
deletes the original fact of `<topic>-replace-NNNN` (300 items), built by
`build_delete.py`. The statement is the original fact and `edit.object` the
removed value; every `new_answer` is null and the original answers stay.
A record's `relation` describes its own statement, so a replace that reversed
a `raises` or `lowers` (read off `object` and `old_object`) gives its delete
the opposite relation.
Direct, paraphrase, cross-lingual and locality queries are the replace ones
unchanged. Derived queries carry over when they have an original answer; the
66 that were phrased around the replacement value ("Which genus of mosquito
transmits sleeping sickness?") are rephrased around the original one ("...
transmits malaria?", Anopheles) in the script's `REWRITES`, with new bridge
facts and checks where needed. `familiarity.object` is re-rated for the
removed value; `axiom`, which gave the replacement's DL form, is dropped.
Queries marked `discriminates: false` keep the flag: their answer did not
depend on the replaced fact. Edit the script and rerun it rather than editing
the delete records by hand.

### Insert records

`records/<topic>/insert/` holds 30 items per topic (300 in all), in the same
order as replace: `0001`-`0005` ABox associative, `0006`-`0010` ABox causal,
`0011`-`0015` TBox associative, `0016`-`0020` TBox causal, `0021`-`0030` RBox.
Fictional and real items come 3 to 2 in every group of five: the first three of each
five are `fictional` and the last two `real` (RBox: `0021`-`0026` fictional,
`0027`-`0030` real), 180 fictional and 120 real in all.

- **Fictional** items mix invented subjects (Velmora-style places, invented
  species, languages, firms, particles) with empty slots of well-known real
  ones (the IMF's mascot, the name of Lincoln's pocket watch), and never
  contradict a real value. Invented classes have no well-known member, so
  their inheritance queries state the member in the prompt.
- **Real** items are true facts a model may well lack: obscure but
  documented ones (Lake Sarez's 1911 landslide dam, the ghost word "dord")
  and events from late 2024 to 2025 (Pope Leo XIV, the 2025 Booker Prize).
  Each record's notes give its source; they were checked by web search when
  written. The model audit decides per model which ones are really unknown.
- **RBox** items add a property to a relation: an invented relation for the
  fictional ones, a real but rarely stated property for the real ones. Their
  relations are catalogued in `RELATIONS.md` under each topic.

## Parked from the previous version

The earlier axis scheme had dimensions this version leaves out to keep the
benchmark buildable. They may come back as separate subsets:

- **Description forms** (negation, disjunction, existential, universal,
  counting) as their own knowledge forms.
- **Edit representation**: confusing or distractor-heavy phrasings of the
  edit, and the degraded-coherence "grounding ladder" (Lyon, a spoon,
  happiness, Zorblin, XQ7-19B).
- **Connectivity and dependency** bands.
- **Analytic vs synthetic** epistemic status.
- **Puzzle topic**: invented mini-worlds ("every flerm is a droven, every
  droven can narp, a mip is a flerm") where derived queries are pure logic
  with no prior knowledge interfering. Insert only, since the model holds
  nothing about them beforehand.

## Size goal

90 taxonomy cells: 10 topics × 3 operations × 3 knowledge forms (the DL
boxes). Every cell has 10 edits, so each topic holds 30 edits per operation:
900 edits in all (300 each of insert, replace and delete). ABox and TBox
cells are split evenly between causal and associative relations, but that
split is a property of how they were written, not part of the taxonomy. ABox and TBox edits carry 12
queries and RBox edits 7, so 600 × 12 + 300 × 7 gives **9,300 queries**.

## Dashboard

The machine-readable version of this scheme is
`dashboard/frontend/src/lib/sidsDatasetTaxonomy.js`, rendered on the
dashboard's Datasets page; keep it, this file and `validate.py` in sync. The
page still shows the scheme rather than records; registering subsets in
`datasetCatalog.js` switches it over once records exist.
