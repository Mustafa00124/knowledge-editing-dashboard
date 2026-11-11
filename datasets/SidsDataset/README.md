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

> Under what kinds of knowledge and belief revision operations does a knowledge edit
> succeed, propagate to what follows from it, and stay contained?

## Levels

```
Topic  >  Belief revision operation  >  Knowledge form  >  Query type
          expansion   (insert)          abox               direct          (1)
          revision    (replace)         tbox               paraphrase      (1)
          contraction (delete)          rbox               cross-lingual   (2: zh, es)
                                                           propositional   (3: negation, conjunction, disjunction)
                                                           related         (2: near, far; ABox revision and contraction)
                                                           derived         (3 determinate; +1 indeterminate on main ABox revision)
                                                           unrelated       (2: near, far)
```

The operations are the three of AGM belief revision: expansion adds a
belief, revision replaces one while keeping the rest consistent, contraction
removes one. Records keep the keys `insert`, `replace` and `delete` (in
`edit_operation`, ids and folders); the names are the same concepts.

Relation properties are not levels: they are the [Relation](#relation) tag
group, and each related and derived query names the property it uses
([Relation properties and task types](#relation-properties-and-task-types)).

How many queries a record carries depends on its operation and box
([Queries per record type](#queries-per-record-type)).

### 1. Topic

`geography`, `people` (facts about famous people), `history`,
`finance` (including textbook economic laws), `biology` (including medicine),
`physics`, `literature_arts`, `technology` (stable facts only),
`mathematics`, `grammar`. A diversity control, so a finding about rules
isn't secretly a finding about mathematics. It also keeps the records
organized for browsing. Topics are kept as alike as possible in what they
contain (same record types, same relation properties); where a topic can't
supply something, its records say so in `notes`.

### 2. Belief revision operation

| Operation | Key | What it does | Expected answer afterwards |
| --- | --- | --- | --- |
| Expansion | `insert` | Adds knowledge the model does not hold: a made-up fact (see [Reality](#reality)). | The new answer. |
| Revision | `replace` | Swaps held knowledge for a false alternative (it need not be plausible: an edit that crosses a boundary, such as moving a city to another continent, is fine). Counterfactual by construction: the original is something every LLM has seen and holds true. | The new answer, and never the old one. |
| Contraction | `delete` | Removes knowledge the model does hold. Contraction records are their own edits, not mirrors of revision records. | No longer the old answer: "I don't know" for what went through the removed fact; see [Contraction](#contraction). |

### 3. Knowledge form

**Box.** How description logic divides a knowledge base:

| Key | What it holds | DL | Example |
| --- | --- | --- | --- |
| `abox` | Facts about particular individuals | R(a, b), C(a) | Paris is the capital of France. |
| `tbox` | Rules about classes: every C is (or does) D | C ⊑ D, C ⊑ ∃R.D | Every capital is a city. Smoking causes lung cancer. |
| `rbox` | Properties of relations themselves | Trans(R), Sym(R), R ⊑ S, R ≡ S⁻, R ∘ S ⊑ T | "Located in" is transitive. "Sibling of" is symmetric. |

A single TBox or RBox edit should move every individual it covers, which is
why they're expected to behave differently from ABox edits.

That gives 3 knowledge forms per topic (one per box), all available to every
belief revision operation, so 10 topics × 3 operations × 3 boxes = 90 cells.

### 4. Query type

| Key | What it is | Metric |
| --- | --- | --- |
| `direct` | The edited fact asked as a question, in the edit's own wording. | Rewrite |
| `paraphrase` | The same question in different words. | Generalizability |
| `cross_lingual` | The direct question asked in Chinese (`zh`) and Spanish (`es`), expecting the answer in that language. | Cross-lingual |
| `propositional` | The edited fact inside a yes/no truth-functional question: one negation, one conjunction (and), one disjunction (or) (see [Propositional queries](#propositional-queries)). | Logical consistency |
| `related_near`, `related_far` | A question whose answer the model has most likely **seen stated** in training (it is stored), and which must change with the edit. Near: one hop from the edit; far: several hops (see [Related queries](#related-queries)). | Generalizability |
| `derived` | A question whose answer the model has most likely **never seen stated**, but which follows from the edit and facts it holds, in exactly 2 hops (see [Derived queries](#derived-queries)). | Generalizability |
| `unrelated_near` | Shares the subject, the relation or the topic, but does not follow from the edit. "What is the official language of France?" after editing France's capital. | Specificity |
| `unrelated_far` | Nothing in common with the edit. | Specificity |

Records, tables and the dashboard list the queries in this order: from the
edit outwards, everything that should change before what must not.
Near unrelated queries are what make specificity informative: far-only
specificity is close to 100% for almost every method.

**Related vs derived.** Both must change answer with the edit; they differ in
whether the answer is *stored*. Edit: the Space Needle is in Chicago.
"Which state is the Space Needle in?" is related: "the Space Needle in
Seattle, Washington" is written everywhere, so the model holds the answer
and the edit has to overturn it. "What time zone is the Space Needle in?" is
derived: almost nobody writes it, but anyone who knows where the Space
Needle is can work it out. Each related and derived query rates its answer
like an edit is rated ([Derivability](#derivability)): related answers are
`very_unlikely` to be derived (stored), derived answers `very_likely`
(worked out), with evidence. A question that can't be placed clearly at one
end is replaced. The answer must differ before and after the edit: a
question whose answer survives the edit (moving the Space Needle to Portland
leaves it on Pacific Time) tests nothing.

#### Queries per record type

| Record type | direct | paraphrase | cross-lingual | propositional | related (near, far) | derived | unrelated (near, far) | Total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ABox revision, main split | 1 | 1 | 2 | 3 | 2 | 4: 3 determinate + 1 indeterminate | 2 | 15 |
| ABox revision, dev split | 1 | 1 | 2 | 3 | 2 | 3 determinate | 2 | 14 |
| ABox contraction | 1 | 1 | 2 | 3 | 2 | 3 determinate | 2 | 14 |
| ABox expansion | 1 | 1 | 2 | 3 | none | 3 determinate | 2 | 12 |
| TBox, every operation | 1 | 1 | 2 | 3 | none | 3 determinate | 2 | 12 |
| RBox, every operation | 1 | none | 2 | 3 | none | 2 instances | 2 | 10 |

Counts are fixed: every record of a type carries exactly these, in every
topic, so topics and records weigh the same. Scores average within a record
first.

Why the gaps:
- **Related is ABox revision and contraction only.** It needs a stored
  answer the edit overturns. An expansion adds a fact nothing was stored
  about. In TBox, the stored facts about a class's members are exactly the
  ones a rule edit leaves open (a tarantula's eight legs, after "every spider
  has six legs", depends on whether the model stored it by name), so they
  can't be determinate.
- **Indeterminate queries are ABox revision only, main split only.** Every
  other record type, and every dev record, has determinate queries only.
- **RBox has no paraphrase**: its direct question asks the property itself.

#### RBox items

An RBox edit changes a property of a relation ("'lends to' is transitive"), not
a fact about an entity, so its record states only the property:

| Key | Count | What it is | Metric |
| --- | --- | --- | --- |
| `direct` | 1 | The property itself: "Is the relation 'lends to' transitive?" | Rewrite |
| `cross_lingual` | 2 | The first instance question in Chinese and Spanish. | Cross-lingual |
| `propositional` | 3 | The edited property inside a yes/no question: negation ("Is it false that the relation 'lends to' is transitive?"), conjunction and disjunction with a side fact. | Logical consistency |
| `derived` | 2 | The property applied to real entities, with the premises in the prompt: "JPMorgan Chase lends to Goldman Sachs, and Goldman Sachs lends to Citadel. Does it follow that JPMorgan Chase lends to Citadel?" Derivation `instantiation`. | Generalizability |
| `unrelated_near` | 1 | The same property asked of another relation in the topic ("Is the relation 'is a subsidiary of' transitive?"). | Specificity |
| `unrelated_far` | 1 | A different property of an unrelated relation ("Is the relation 'is married to' symmetric?"). | Specificity |

In the model audit an RBox fact counts as known when its direct question and
both instance questions get the original answer.

**Role chains through real knowledge.** A role chain that composes a made-up
relation with a real one ("If a town is harbour-sworn to a city, and the city
is located in a country, the town is harbour-sworn to that country") can leave
the real hop out of the prompt: "Bergen is harbour-sworn to Kyoto. Does it
follow that Bergen is harbour-sworn to Japan?" The model must use the composed
relation together with what it already holds (Kyoto is in Japan), which tests
whether the new axiom connects to stored knowledge rather than to the prompt
alone. Such a query lists the real hop in `bridge`, leaves `bridge_in_prompt`
false, and the hop gets a check before editing like any bridge fact.

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
  that query is dropped for that model.
- They are reported as their own metric, so a model that is weak in one
  language doesn't drag down the English scores.

#### Propositional queries

Three per record (every box and operation), right after the cross-lingual
ones, in this order: negation, conjunction, disjunction. Each puts the edited
fact E inside a yes/no question built only from truth-functional connectives,
so the answer follows from E's truth alone and the model has to treat the
edit as a fact it reasons with, not a string it repeats. They feed their own
metric, **logical consistency**, reported on its own and per connective.

| Field | Rule |
| --- | --- |
| `prompt` | the question; no "if ... then" |
| `form` | `not` (negation), `and` (conjunction), `or` (disjunction); one of each, in that order |
| `side_fact` | null for `not`; for `and` and `or`, the untouched fact S combined with E, as a sentence |
| `original_answer` | "yes" or "no" before the edit; null for insert |
| `new_answer` | "yes" or "no" after the edit; "I don't know" for delete |

E is the edited statement (`edit.statement`): under replace it is false
before the edit and true after; under insert true after; under delete it is
the removed fact, true before and unknown after. S is chosen so the answer
flips with the edit: **true for the conjunction, false for the disjunction**.
Examples (replace, "The capital of Australia is Sydney"):

- negation: "Is it false that the capital of Australia is Sydney?" (yes, then no)
- conjunction: "Is it true both that the capital of Australia is Sydney and that the Pacific Ocean borders Australia?" (no, then yes)
- disjunction: "Is it true that the capital of Australia is Sydney or that Australia is in Europe?" (no, then yes)

Under delete all three new answers are "I don't know": strong Kleene logic
keeps E's unknown value (not unknown is unknown; unknown and true is
unknown; unknown or false is unknown).

The side fact needs a check `{fact, prompt, answer}` like a bridge fact, so
the audit asks it before editing; its answer gives S's truth (yes or a filled
slot: true; no: false). A trivially true or false side fact may go without,
and is then taken to have the value the flip needs. `validate.py` checks the
truth table: the three forms in order, `side_fact` present exactly for `and`
and `or`, S's value making the answer flip, and each gold answer equal to the
connective's value. That is the formal check of these queries (checker
`truth-table`), not HermiT or Z3.

#### Relation properties and task types

Every related and derived query names **the relation property its answer
rests on** (`derivation`) and **the task it asks the model to do** (`task`).
They are separate labels: the property is about the logic, the task about
what the question makes the model do.

**Relation properties** (`derivation`). General rules that hold for every
individual; a relation can only be used for a property `RELATIONS.md` gives
it.

| `derivation` | Rule | Hops | Example |
| --- | --- | --- | --- |
| `inverse` | a R b ⇔ b S a | 1 | Edit: Ann is Billy's parent. Ask: who is Ann's child? |
| `symmetry` | a R b ⇒ b R a | 1 | Edit: Billy is a sibling of Manny. Ask: is Manny a sibling of Billy? |
| `functional` | R has one value per subject: a R b, a R c ⇒ b = c | 1 | Edit: the capital of Australia is Sydney. Ask: is Canberra the capital of Australia? (no) |
| `subproperty` | R ⊑ S: a R b ⇒ a S b, with no other fact | 1 | Edit: Lyon is the capital of Germany (capital of ⊑ located in). Ask: which country is Lyon in? |
| `transitivity` | the *same* relation twice: a R b, b R c ⇒ a R c | 2 | Edit: the nephron is part of the respiratory system. Bridge: the glomerulus is part of the nephron. Ask: is the glomerulus part of the respiratory system? |
| `chain` | *two different* relations give a third: a R b, b S c ⇒ a T c | 2 | Edit: she was born in Lyon. Bridge: Lyon is in France. Ask: which country was she born in? (born in ∘ located in ⊑ born in) |
| `inheritance` | a class rule passes to a member: C ⊑ D, x ∈ C ⇒ x ∈ D | 2 | See below: it runs in opposite directions in ABox and TBox. |
| `none` | no relation property: the task alone carries the edit to the answer | 2 | Only with task `composition` or `binding`. |
| `cardinality` | `cardinality:many`: removing one value leaves the others | 1 | Contraction only: another held value keeps its answer ([Contraction](#contraction)). |
| `premise` | a premise of a derived edit asked directly | 1 | Main-split ABox revision of a derived fact only (indeterminate). |
| `instantiation` | an RBox axiom applied to instances given in the prompt | 1 | RBox only. |

Transitivity is the special case of a chain where all three relations are
the same. A chain is a rule that holds in general (anyone born in a French
city was born in France).

**Inheritance in the two boxes.** In TBox the edit is the class rule and the
bridge is the membership: edit "every spider has six legs", bridge
"*Bagheera kiplingi* is a spider" (named in the prompt as a new or unfamiliar
member), ask "how many legs does it have?". In ABox it is the other way
round: the edit is the membership and the bridge is the class rule: edit
"Pluto is a planet", bridge "every planet orbits a star", ask "does Pluto
orbit a star?". The same property tests different things: whether a rule
reaches its members, and whether a member picks up its new class's rules.

**Task types** (`task`). What the question makes the model do with the
edit. A plain question is `answer`; the three task types are composition,
binding and application.

| `task` | What the question asks | Hops it adds | Example |
| --- | --- | --- | --- |
| `answer` | the conclusion itself | none | Which country was she born in? |
| `composition` | follow the edit, then look up a second, **unconnected** stored fact about the new value (MQuAKE-style multi-hop) | the second fact is a bridge | Edit: the capital of France is Lyon. Bridge: the Rhône flows through Lyon. Ask: which river flows through the capital of France? |
| `binding` | reach the edited subject **by another name or description** the model knows separately (an alias, an abbreviation, a role it holds), so it has to connect the description to the edited entity | the alias fact is a bridge | Edit: the IMF is headquartered in Paris. Bridge: "IMF" abbreviates the International Monetary Fund. Ask: in which city is the International Monetary Fund headquartered? |
| `application` | use the conclusion in a practical task: compute a value, fill a field, plan a step | none (the computation is not a hop) | Edit: the Space Needle is in the Central Time Zone. Ask: when it is noon in Chicago, what time is it at the Space Needle? (noon) |

A task can sit on top of a property (a chain asked as an application) or,
for composition and binding, stand alone with `derivation: none`. An
application question that computes needs `logic: fol` (with `theory:
arithmetic` or `temporal`).

**Binding needs care.** The alias must be something the model holds as a
separate fact (checked before editing like any bridge), and the question must
not just restate the edit: "Where is the organisation whose headquarters is
in Paris?" contains its own answer, and naming the subject in full ("the
International Monetary Fund") when the edit names it the same way is only a
paraphrase. The edit and the question use **different names** for the
subject. Scope ("cannot be determined") is not used: its answer is the same
with or without the edit.

**Which property and task go where.**

| Query | Allowed `derivation` | Allowed `task` | Hops |
| --- | --- | --- | --- |
| `related_near` | `inverse`, `symmetry`, `functional`, `subproperty` | `answer`, `application` | exactly 1 |
| `related_far` | `transitivity`, `chain`, `inheritance`, `subproperty`, `none` | any | 2 or more |
| `derived` (determinate) | `transitivity`, `chain`, `inheritance`, `subproperty`, `none` | any | exactly 2 |
| `derived` (indeterminate, main ABox revision) | `none`, `premise` | `answer`, `composition` | any |
| `derived` (RBox) | `instantiation` | `answer` | 1 |

`derivation: none` only with task `composition` or `binding`; both need a
bridge fact.

**Balance per topic.** Within each topic, the ABox revision records'
related and derived queries together use **transitivity, chain, inheritance
and subproperty at least once each**, the related-near queries **inverse,
symmetry and functional at least once each**, and the related and derived
queries **composition, binding and application at least once each**, kept
as even as the topic allows. A topic that can't supply one (no natural
symmetric relation) says so in its records' `notes` and makes it up with
another of the same group.

**Edits cover the properties too.** The relation each ABox revision edit
uses is chosen so that the seven properties (inverse, symmetry, functional,
subproperty, transitivity, chain, inheritance: a relation whose subject or
object is a class member) are **edited about equally often**: in the main
split, each property is carried by the edited relation of at least one of a
topic's 8 ABox revision edits; in the dev split (4 per topic), across the
whole split, each property on 5 to 7 of the 40 edits. A relation usually
has several properties; an edit counts for the property its related and
derived queries use.

#### Related queries

Two per ABox revision and ABox contraction record: `related_near` (1 hop)
and `related_far` (2 or more hops), each a one-item list.

- **Stored answer.** The original answer (or the fact the question asks
  about) is stated often in text every model trains on: rate it in the
  query's `derivability` (`very_unlikely`) and back it in `evidence`, keyed by
  the query's `fact`, like an edited fact (CRITERIA Rule 5).
- **It must change.** The answer after the edit differs from the original
  (under contraction: becomes "I don't know").
- **It must not restate the edit.** "Which city is the Space Needle in?" is
  the direct question in other words, not a related one.
- **Determinate.** Only questions with one answer whatever the model stored;
  a stored fact with a route back to the old answer once the edit is in (the
  problem of background beliefs) is not used.
- Fields: those of a derived query ([Format](#format)), plus `fact` and
  `derivability`; `determinacy` is always `determinate`.

#### Derived queries

The **determinate** derived queries (3 per record, every record type but
RBox) ask something that follows from the edit in **exactly 2 hops** (the
edit plus one bridge fact) and whose answer the model has most likely never
seen stated:

- **Worked out, not stored.** Rate the original answer's fact `very_likely`
  in the query's `derivability` and back it with evidence (rare in text, each
  premise common).
- **It must change** with the edit (under contraction: become "I don't
  know"), and have one answer whatever the model stored (`determinate`).
- **The bridge is held**: the model must answer it before editing, so a
  wrong derived answer is a failed edit rather than a missing fact. A bridge
  the prompt states is listed in `bridge` with `bridge_in_prompt: true`.

The **indeterminate** derived query (1 per main-split ABox revision record)
is context: it shows the belief-revision problem the edit raises (Hase et al.
2024) rather than carrying the method comparison
([Determinacy](#determinacy-and-belief-revision-problems)).

RBox derived queries are the two instance questions above.

**Logic.** Every derived and related query names the weakest logic its
inference needs, in `logic`, and any theory it uses on top, in `theory`.
These are settings to slice results by, so we can see where parameter
editing works and where it stops working.

| `logic` | What the inference needs | Example |
| --- | --- | --- |
| `dl` | Description logic: classes, relations between two individuals, relation properties, role chains, inheritance, number limits (one capital, more than one), names for the same individual, and comparing named values: a join through a relation (the same currency, the same city), a closed list of named members (the only ones). | Is Canberra the capital of Australia? Which time zone does the city the Space Needle stands in observe? |
| `fol` | First-order logic beyond DL: relations among three or more things, real arithmetic, dates or numbers compared as values, counting how many, string patterns, rules whose variables form a cycle. | Take the past tense of 'outswim' and remove 'out' from the front: what word is left? How many voting members does the House have? |

| `theory` (optional, with `fol`) | What it adds | Example |
| --- | --- | --- |
| `arithmetic` | Computing or comparing numbers. | When it is noon in Chicago, what time is it at the Space Needle? |
| `temporal` | Comparing dates or ordering events. | Did the first powered flight come after McKinley's death? |

The labels also say where a query is checked formally (`owl/README.md`,
Routing): `dl` queries by HermiT (`reason.py`), `fol` ones by Z3
(`fol_check.py`, with the value attributes of
[`ATTRIBUTES.md`](ATTRIBUTES.md)). Pick the weakest logic that captures the
inference as the question asks it, not the strongest one that could. Belief
revision itself, which premise gives way, is outside these: it is the layer
the determinacy labels describe.

Each related and derived query records its `derivation`, its `task`, its
`hops` (1 + the number of bridge facts) and the `bridge` facts it relies on.
A derivation that goes through the inverse relation's tags names it in
`via`. Reflexivity and asymmetry are not used: "a R a" doesn't depend on the
edit, and an asymmetry question's "no" is usually the same before and after.

**Bridge facts and revision facts.** A fact listed with a query is one of two
kinds:

- `bridge`: a fact the answer is **built from**: combined with the edit (and
  the relation property) to reach the answer. `hops` = 1 + the number of
  bridge facts.
- `revision_facts` (optional): a fact that **settles which belief gives way**
  or which world applies, without being combined into the answer. Example:
  "A volcano built mainly from lava flows is not built mainly from volcanic
  ash" decides that, once Mauna Loa is a stratovolcano, the stored "built from
  lava flows" belief is what goes. Revision facts do not count in `hops`.

Both kinds are facts the model must hold, so each one the prompt does not
state has a check like a bridge (`facts_to_check()`); a revision fact the
prompt states needs `revision_in_prompt: true` (when absent it follows
`bridge_in_prompt`). A fact is never both a bridge and a revision fact.

`alt_derivations` (optional): other derivation names that reach the same
answer by a different valid route, such as `chain` with
`alt_derivations: ["transitivity"]`. `derivation` stays the intended route.

Every bridge fact a query does not state in its own prompt, and every
premise, has a **check**: a question with a short answer in the record's
`checks` list (`facts_to_check()` in `validate.py` lists what needs one).
Every relation property a derivation relies on has one in
`relation_checks.json`, keyed by relation and tag. The model audit asks all
of them and reports per model how many queries have their whole chain known.
On the Datasets page each query has a button that draws its chain (the edit,
the facts to know, the relation property, the answer) with each model's audit
result on every check.

#### Contraction

Contraction records are their own edits, chosen for the **cardinality of the
relation**, because that decides what the right answer is after a fact is
removed. They are no longer mirrors of revision records.

| Relation | Before | After removing a R b | Example (remove "Canberra is the capital of Australia") |
| --- | --- | --- | --- |
| `functional` (one value per subject) | "Is c the R of a?" is no, because the value is b and there is only one | **"I don't know"**: the reason for "no" is gone | "Is Sydney the capital of Australia?": no, then I don't know |
| `cardinality:many` (several values) | "Is c an R of a?" (another value the model holds) is yes | **still yes**: removing one value says nothing about the others | Remove "Switzerland has official language French": "Is German an official language of Switzerland?" stays yes |

Every ABox contraction record uses a relation tagged `functional` or
`cardinality:many` in `RELATIONS.md`; per topic, half of each. Queries:

- direct, paraphrase, cross-lingual and propositional: about the removed fact;
  the new answer is "I don't know" (`new_answer: null`).
- related near and far: stored answers reached through the removed fact
  ("Canberra is the capital of which country?", inverse): "I don't know".
- derived, 3 determinate: one **cardinality question** (`derivation:
  functional`, "no" becomes "I don't know"; or, for a many-valued relation,
  `derivation: cardinality`, another held value that keeps its answer:
  `new_answer` equal to `original_answer`), and two 2-hop questions through
  the removed fact ("Which river flows through the capital of Australia?"):
  "I don't know". The cardinality question is 1 hop, the one exception to the
  2-hop rule.
- unrelated near and far: as everywhere.

Derived queries must route **through the removed fact**: after removing "Paris
is the capital of France", "Which country is Paris in?" is not a consequence
of the removed fact (the model knows it independently) and is not asked.

Before editing, the model must already answer the cardinality question
properly (the audit's check): "no" for a functional relation, the held value
for a many-valued one, so a failure after editing is the method's.

**TBox contraction** removes a rule ("every spider has eight legs"): the
derived queries name a new member in the prompt (inheritance), whose answer
becomes "I don't know". **RBox contraction** removes a property ("'borders'
is symmetric"): "Does it follow that Spain borders France?" can no longer be
concluded (`new_answer: null`). These are first versions and may be revised.

Success means the model **no longer gives the old answer** and says it does
not know (`abstain`); on yes/no queries the judge reads a bare yes or no as an
answer, never as `NONE`, so only an abstention passes there.

#### Expansion

Expansion records add a made-up fact ([Reality](#reality)), so the model
holds nothing about it beforehand: no derivability, no related queries, no
indeterminate queries. Their 3 derived queries connect the new fact to real
knowledge in 2 hops through a bridge the model holds (or that the prompt
states). **TBox expansion** adds a rule and applies it to a member the model
already knows (inheritance, 2 hops); **RBox expansion** adds a property to a
relation and applies it to real instances (instantiation). These are first
versions and may be revised.

## Tags

Besides its taxonomy coordinates, every record carries tags. Tags are **not
levels or layers** of the taxonomy: they describe the item further, so
results can be sliced by them within any cell. Records and the dashboard
give them in this order: change, relation (and its properties),
derivability; then reality, for insert. Each related and derived query
carries its own tags: relation property and task, hops, derivability of its
answer, determinacy and logic
([below](#determinacy-and-belief-revision-problems)).

### Change

Replace only: what the edit does to the original fact, from the original
value to the new one (`edit.old_object` → `edit.object`, e.g. Paris → Lyon).
It is stored in `edit`, which comes right after the record's identity fields.
TBox and RBox replace edits change a rule or a property, so the dashboard
shows the original rule and the edited one instead (`edit.original` →
`edit.statement`). Insert has no original fact and delete only removes one,
so neither has a change.

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
relation may have none. A property an inverse pair shares (transitive,
asymmetric, symmetric) is tagged on one row of the pair only, and
`load_relations()` gives the partner it too (RELATIONS.md, Tags rules). They stay in `RELATIONS.md` only, so a relation's
properties are defined in one place; the dashboard shows them on each record
from that table.

Records carry only the relation's name; there is no causal or associative
tag.

### Derivability

Derivability rates whether a model is likely to hold a fact as a **stored**
claim or to **work it out** when asked from other facts it holds. Two things
are rated:

- **The edited fact** (`derivability` on the record): for replace and delete,
  the *original* fact, the one the model holds before editing. Null for
  insert (a new fact can't follow from what the model holds, or it wouldn't
  be new) and for RBox.
- **The answer of each related and derived query** (`derivability` on the
  query, rating the query's `fact`): related answers must be stored, derived
  answers worked out ([Related vs derived](#4-query-type)).

Only the two ends are used. A fact we can't place confidently at one end is
replaced, not rated in between.

| Value | Score | Meaning | Example |
| --- | --- | --- | --- |
| `very_unlikely` | 1 | **Stored (axiomatic):** stated everywhere, so a model holds it directly. | Paris is the capital of France. |
| `very_likely` | 5 | **Derived (composed):** hardly ever stated, but follows from facts every model surely holds through a relation property in `RELATIONS.md`. | Elizabeth I of England's paternal grandfather was Henry VII (Henry VII was the father of Henry VIII, Henry VIII the father of Elizabeth I, and the father of one's father is one's paternal grandfather). |

**Where each value is allowed.** Edited facts are `very_unlikely` everywhere,
except ABox revision in the main split, which has **2 `very_likely` edits per
topic** (as context: they raise the problem of derived beliefs) and the rest
`very_unlikely`. Dev records, contraction, TBox and expansion records never
edit a derived fact.

Editing a fact a model derives leaves its premises pointing at the old
answer. A consistent model revises one of them, and which one is open; a
model that revises none holds the new value only as an exception to premises
that still imply the old one, and re-derives the old answer along the premise
route. That is the [problem of derived
beliefs](#determinacy-and-belief-revision-problems). Rules for a
`very_likely` edit:

- **Premises are listed** in `edit.premises`: the facts the edited one
  follows from and, as a sentence, the rule or relation property that
  combines them. Each has a check and is asked before editing: if the model
  doesn't hold them, it can't derive the fact, and the item is dropped for
  that model.
- **Premises are not specificity.** A premise's answer after the edit is
  open, so it is asked as the indeterminate `premise` query, never as the near
  unrelated query.
- **The rating is justified** in the record's `notes` and `evidence`.

The scores are ordinal (`DERIVABILITY_SCORE` in `validate.py`).

> **Derivability is model specific.** Whether a fact is stored or derived
> really depends on the model, and we can't observe which. The tag is our
> estimate, backed by the evidence below; the model audit says whether each
> model holds the fact at all.

#### Evidence

Every rating is backed by evidence, shown behind a **?** beside the fact on
the dashboard: for the edited fact (as the model holds it before the edit)
and for every premise, optionally for bridge facts. It lives in the record's
`evidence`, keyed by the fact's exact text:

```json
"evidence": {
  "The Space Needle is in the Pacific Time Zone.": {
    "claim": "derived",
    "why": "Almost never stated. People ask the time zone of cities, not of buildings ...",
    "sources": [
      {"kind": "infini-gram", "index": "v4_dolma-v1_7_llama", "query": "Space Needle", "count": 229543},
      {"kind": "infini-gram", "index": "v4_dolma-v1_7_llama", "query": "Space Needle AND Pacific Time", "count": 33,
       "note": "Sampled hits are timestamps, not the fact."},
      {"kind": "wikipedia", "url": "https://en.wikipedia.org/wiki/Space_Needle", "note": "No time zone in the article."}
    ]
  }
}
```

- **Stored:** the fact is stated explicitly and often in text every model
  likely trained on. Wikipedia is in effectively every model's pretraining,
  and large public web corpora are a good proxy for the rest; OLMo's own
  pretraining data (Dolma) is public and searchable. More frequency is
  stronger evidence: give counts and quote the sentence.
- **Derived:** easy searches for the direct fact find little or nothing,
  while each premise is stated often. Give the ratio (the direct form
  against each premise and against the subject alone), read samples of any
  hits, and list every search tried, so "absent" means "absent after these
  searches".
- **False:** a deliberately false fact, such as the side fact of an "or"
  propositional query ("Australia is in Europe"). Its sources back what is
  true instead, with a quote ("Australia is a country in Oceania").
- Bridge facts, revision facts and propositional side facts carry evidence
  too, so their truth is backed by a source rather than only by review
  (CRITERIA Rules 1 and 5). A true one is claimed `stored` when it is stated often,
  with a quote or counts.
- Source kinds: `infini-gram` (`query`, `count`, optional `index`, `note`),
  `wikipedia` and `web` (`url`, optional `quote`, `note`), `search`
  (`query`, optional `engine`, `note`).
- The edited fact's `claim` follows its derivability (stored at
  `very_unlikely`, derived at `very_likely`), and so does each related and
  derived query's `fact` (related: stored; derived: derived);
  premises are claimed stored, except the premise that states the rule
  combining the others ("a building observes the time zone of the city it
  stands in"), which is `definitional`: true by what the words mean, so it
  needs a `why` but no corpus sources.
  Bridge, revision and side facts may also be `definitional` when they are true by
  the meaning of their words ("an unglaciated valley was never filled by a
  glacier").
- Enough evidence (CRITERIA Rule 5): a stored claim has a quoted sentence or
  an exact-phrase count of at least 100; a derived claim has at least two
  corpus counts or searches.
- Required for the edited fact, every premise and every related and derived
  query's `fact`, on every record; optional for bridge, revision and side facts.

Counts come from infini-gram's public API. Its AND (nearby co-occurrence)
queries sample when one side is frequent and can return false zeros unless
`max_clause_freq` is raised (we use 500,000), and a single zero can still be
sampling noise. So evidence of absence rests on exact phrases and on reading
samples, not on one AND count. Seeing a fact in training text shows a model
saw it, not how it stores it: the rating stays an estimate.

### Reality

Whether an inserted fact is true in the world. Insert only; left out for
replace and delete, which always edit a real fact. **Expansion uses
`fictional` facts only**: the model can't already hold them, so the audit
never has to rule that out. `real` inserts (true but obscure or recent facts)
are not written any more; the main split's existing ones are replaced.

| Value | What it is | Pre-edit audit | Example |
| --- | --- | --- | --- |
| `real` | A true fact the model may not hold: obscure, or newer than its training data. | Asked: the item is kept for a model only if it does not already give the new answer. | The 2024 Abel Prize went to Michel Talagrand. |
| `fictional` | A made-up fact, about an invented subject or an empty slot of a real one. No model can hold it. | Not asked: the item is not held by construction. Its checks (the real facts its derived queries rely on) are still asked. | Velmora is the capital of Kestria. The Louvre's official mascot is a cat named Mona. |

A fictional fact must contradict nothing true: if the slot already has a real
value (the Louvre's director), the edit is a replace, not an insert. Derived
queries of a fictional insert reach real knowledge only through bridge facts
the model holds or that the prompt states, so their chains can be checked.
The other tags apply as usual, except that insert has no original fact:
`derivability` is null.

### Determinacy and belief-revision problems

Builds on Hase et al. 2024, "Fundamental Problems With Model Editing" (TMLR,
arXiv 2406.19354).

**Where the problems come from.** Any knowledge system holds two kinds of
knowledge: a **base** of facts it stores explicitly, and the **closure** of
that base, everything that follows from it. "Barclays is headquartered in the
United Kingdom" is in the base of most models; "Barclays and Deutsche Bank are
headquartered in different countries" is in the closure, worked out from two
base facts when asked. An edit changes one fact, and what else should change
depends on what is in the base and how it is stored. For an LLM that is a
black box: we can't see which facts a model stores, which it derives, or
under which names or descriptions it stores them. So one edit can have
several valid outcomes, one per way the model may have stored things.

**What the labels are for.** They don't resolve that ambiguity; they mark
where it is. Every related and derived query says whether its answer after
the edit is **determinate**, the same whatever the model stored, or
**indeterminate**, different depending on what it stored. **Indeterminate
queries exist only on main-split ABox revision records, exactly one per
record**, as context for the belief-revision problems; every other query in
the dataset is determinate, and the dev split has none. An indeterminate query is not one
without a logical answer: in each world the answer is fixed by logic, and
what is open is only which world the model is in, that is, which facts it
stores and which it derives (background beliefs, derived beliefs). A wrong
answer on a determinate query is the editing method's failure. A "wrong"
answer on an indeterminate query may be a different valid world, so it is
scored against every world
([below](#worlds-and-chains)), not counted as a plain failure. This separates
failures that come from the method from ambiguity that is built into belief
revision.

#### The two problems

**Problem of background beliefs** (query level; Hase et al. 2024, sec. 3.1).
The edit is clear, and it doesn't clash with anything; but how it propagates
to *other* derived questions depends on the beliefs the model held before the
edit, and how it stored them. With different prior beliefs, the correct
answer after the edit is different.

> Edit: "The capital of France is Lyon." Ask: "In which city is the Eiffel
> Tower?" If the model stored "the Eiffel Tower is in Paris", the answer stays
> Paris. If it stored "the Eiffel Tower is in the capital of France", the
> tower moves with the capital and the answer is Lyon. Both are valid; which
> one is right depends on a storage choice we can't see.

This problem typically arises on edits of facts the model stores (derivability
`very_unlikely`), through another fact that refers to the edited
one by name in one world and by description in another.

**Problem of derived beliefs** (edit level; our name). The edited fact is
itself likely in the closure, not the base: the model doesn't store it, but
derives it from premises it does store (derivability
`very_likely`). Editing it writes the new value as an explicit fact, but the
premises are still there and still imply the old one. Two things can follow:

- **A consistent revision:** one of the premises gives way so that they imply
  the new value. Which premise gives way is open, so the edit has several
  valid worlds, and questions about the premises (or that route through them)
  are indeterminate.
- **An inconsistency:** no premise is revised. The model now holds the new
  value explicitly *and* derives the old one from its premises. Asked
  directly it gives the new answer; asked along the route through the
  premises it gives the old one. This is a portability failure, and it is a
  failure in every world: no consistent revision allows it.

> Edit: "Elizabeth I's paternal grandfather was Henry VI" (originally Henry
> VII; almost no text states it, but every model stores "Henry VII was the
> father of Henry VIII" and "Henry VIII was the father of Elizabeth I", and
> the father of one's father is one's paternal grandfather). World 1: Henry
> VIII's father gives way, and Henry VIII becomes Henry VI's son. World 2:
> Elizabeth's father gives way, and she becomes the daughter of some son of
> Henry VI. "Who was Henry VIII's father?" is indeterminate (Henry VI in world
> 1, Henry VII in world 2). "Who was the father of Elizabeth I's father?" is
> determinate: Henry VI in both worlds. A model that answers Henry VII there
> holds the edit only as a patch on top of premises that contradict it.

So derived-belief edits get two kinds of derived query: indeterminate ones
about the premises, and determinate ones that reach the edited fact along the
**premise route**. The second kind is what exposes the inconsistency.

A derived-belief edit can also have background-belief queries. Each
indeterminate query names the problem its ambiguity comes from.

#### Labels

Each related and derived query has a `determinacy` (RBox instance queries
leave it out: they are determinate by construction):

| Value | What it means | Typical source |
| --- | --- | --- |
| `determinate` | Every valid world gives the same answer: the edit, the relation's properties and facts the model surely holds force it. | An inverse, functional exclusion, a subproperty, a chain through the edited relation; on a derived-belief edit, the edited fact asked along its premise route. |
| `background_beliefs` | The answer depends on which beliefs the model held before the edit and how it stored them. | Another fact stored under a name in one world and under a description through the edited relation in another. |
| `derived_beliefs` | The answer depends on which premise of a derived edited fact gives way. | A premise of the edited fact, or a question whose route runs through one. |

The last two are **indeterminate**. The edit-level side of the problem of
derived beliefs is read off `derivability`, which is not new.

**How a query is labelled.** A **route** is a chain of stored facts and rules
that produces the query's answer. Before the edit every plausible route gives
the original answer, since the model was consistent. To label a query:

1. List every route a reasonable model could have used to reach the answer
   before the edit, and, on a derived-belief edit, every premise of the
   edited fact that could give way.
2. Follow each route again with the edit applied (and, on a derived-belief
   edit, with each premise giving way in turn).
3. Drop a route whose answer after the edit contradicts a fact the model
   holds firmly: it doesn't describe a valid world, only an inconsistent
   model.
4. If every remaining route gives one answer, the query is `determinate`. If
   they split because of how facts were stored, it is `background_beliefs`;
   if they split because of which premise gives way, `derived_beliefs`.

The four scenarios:

| Scenario | Before the edit | After the edit | Label | Example |
| --- | --- | --- | --- | --- |
| A. One route | One way to the answer. | One answer. | `determinate` | Edit: the capital of Australia is Sydney. "Is Canberra the capital of Australia?" goes only through the edited fact: no. |
| B. Several routes, all through the edit | Several ways, each through the edited fact. | They move together. | `determinate` | "Is the capital of Australia on the coast?" Every route runs capital → Sydney → coast: yes. |
| C. Several routes, some around the edit | One route goes through the edited fact, another reaches the answer without it. | They split. | `background_beliefs` | "In which city is Australia's Parliament House?" Stored as "in the capital": Sydney. Stored as "in Canberra" by name: Canberra. |
| D. One route through a premise of a derived edit | One way, but it uses a premise of the edited fact. | It depends on which premise gives way. | `derived_beliefs` | Edit: the Space Needle is in the Central Time Zone (derived from: it is in Seattle, Seattle observes Pacific Time). "Which time zone does Seattle observe?" Pacific if the Space Needle moves, Central if Seattle does. |

So several routes are not enough for indeterminacy (B): they have to diverge
after the edit. On an edit of a stored fact, one route always means
determinate; on a derived-belief edit, one route can still split (D), because
the split comes from revision rather than storage.

Step 3 is where care is needed. After "the capital of Australia is Sydney", a
model that stored "Parliament House is in Canberra" by name is in a valid
world: Parliament is simply no longer in the capital. A model that stored "the
capital of Australia is in the Australian Capital Territory" would now put
Sydney in the ACT, which contradicts "Sydney is in New South Wales". That is
not a world, so "In which state or territory is the capital of Australia?" is
`determinate` (New South Wales), and a model answering the ACT is
inconsistent.

Direct, paraphrase and cross-lingual queries keep a single `new_answer`: the
edit itself is never in doubt.

**TBox** records are determinate only. A TBox edit changes a rule about a
class ("Every spider has eight legs" to six); its derived queries apply the
rule to a **new or unfamiliar member named in the prompt** ("The peacock
spider is a newly described species. How many legs does it have?"): the model
knows nothing about it but its class, so the rule is the only route. A
well-known member ("How many legs does a tarantula have?") is not asked: the
model may have stored its property by name, so the answer would depend on
storage (background beliefs).

Rules must have no real exceptions ("all mammals give birth to live young"
fails on the platypus), or the original answers are wrong.

**RBox** records carry no determinacy. Their derived queries ask what
follows, with the facts in the prompt ("France borders Spain. Does it follow
that Spain borders France?"), which is the same whatever the model stored.
Asking what is true instead ("Does Spain border France?") would let a stored
fact compete with the edited property; RBox records don't ask that.

An RBox edit states only the property: "'Borders' is symmetric.", not an
explanation of what symmetry means ("...: if one country borders another,
the second also borders the first"). The questions carry the meaning. A role
chain, which has no short name, may be one if-then sentence.

Every RBox replace edit changes or removes a property that actually holds
("'borders' is symmetric" to not symmetric); it never adds one that doesn't.
An RBox contraction removes a property that holds; removing a negative one
("R is not symmetric") would leave "does not know" with nothing to stand
for. Yes and no answers are balanced through the question's phrasing ("Is
'borders' asymmetric?" has the original answer no).

#### Worlds and chains

A record with at least one indeterminate query lists its **worlds**: 2 to 4
`{id, assumes, summary}`. Each world is one hypothesis about the model:
`assumes` lists what it stored before the edit (background beliefs) or which
premise gives way (derived beliefs), and `summary` says in a sentence what the
world looks like after the edit. A world fixes every open choice of the
record, so one set of worlds covers all its indeterminate queries.

Every indeterminate query gives, per world, the answer and the **chain** that
leads to it: the steps from that world's stored beliefs and the edit to the
answer, one fact or rule per step. The chains together are the query's tree
of possibilities: one branch per thing the model may have stored. A
determinate query may give its one chain too. An excerpt:

```json
"edit": {"statement": "The capital of France is Lyon.", "subject": "France",
         "object": "Lyon", "old_object": "Paris"},
"worlds": [
  {"id": "w1", "assumes": ["The Eiffel Tower is in Paris."],
   "summary": "The tower is stored under the city by name, so it stays in Paris."},
  {"id": "w2", "assumes": ["The Eiffel Tower is in the capital of France."],
   "summary": "The tower is stored under the capital of France, so it moves to Lyon with it."}
],
"derived": [
  {"prompt": "Is Paris the capital of France?", "original_answer": "yes",
   "new_answer": "no", "derivation": "functional", "determinacy": "determinate", ...},
  {"prompt": "In which city is the Eiffel Tower?", "original_answer": "Paris",
   "new_answer": null, "derivation": "none", "task": "composition",
   "determinacy": "background_beliefs",
   "determinacy_why": "Paris if the model stores the tower's location under Paris's name; Lyon if it stores it as 'the capital of France', the description the edit changed.",
   "world_answers": {
     "w1": {"answer": "Paris",
            "chain": ["The Eiffel Tower is in Paris. (stored)", "So the Eiffel Tower is in Paris."]},
     "w2": {"answer": "Lyon",
            "chain": ["The Eiffel Tower is in the capital of France. (stored)",
                      "The capital of France is Lyon. (edit)",
                      "So the Eiffel Tower is in Lyon."]}
   }, ...}
]
```

An indeterminate query has `new_answer: null`, a short `determinacy_why`, and
`world_answers` keyed by exactly the record's world ids, with at least two
different answers among them. A determinate query keeps its single
`new_answer` and has no `world_answers`.

**Scoring** (editing runs, [Evaluation](#evaluation)): a determinate query
passes on its `new_answer`. Under `sid`, an indeterminate one passes if the
answer matches some world, and which world it matches is recorded; the main
experiments' `sid_main` instead measures whether it changed from the original
answer ([Main experiments](#main-experiments-sid_main)). Across a record's
indeterminate queries, the worlds a model's answers pick should agree;
answers from different worlds are themselves an inconsistency (reported as
`worlds.records_mixed`). An answer that matches no world fails.

#### Insert (fictional)

Inserts on this branch are **fictional only** (`reality: fictional`): the
model cannot already hold the fact, so the audit never has to rule that out,
and the test is acquiring knowledge and connecting it to what the model holds,
not overwriting a fact. There is no delete mirror (deleting a fact the model
never had tests nothing) and no derivability (`null`). Instead every insert
says which parts of its triple (subject, relation, object) are made up, in
`fictional`:

| Value | What is made up | Example | Where derived queries go |
| --- | --- | --- | --- |
| `subject` | the subject, in a real relation to a real object | "Kessaroy is a newly mapped island of the Thousand Islands." | Through real facts about the object: "Is Kessaroy in North America?"; counts and superlatives about the object ("How many islands make up the Thousand Islands?"). |
| `object` | the object, as a new value of a real subject | "Eris has a newly found moon named Thalia." | Through the real subject, which the model knows well: "Does Eris have more than one moon?" |
| `subject_object` | both ends, in a real relation | "The plural of the noun 'brindoose' is 'brindeese'." | Through the real relation's properties and through facts the prompt gives. |
| `relation` | the relation, between real things | "Lisbon is lantern-paired with Valparaíso." | Through the real entities ("...paired with a city in which country?"), or through a property of the relation stated in the prompt. |
| `all` | everything | "Port Ostrabeck is brine-sworn to Carrow Sound." | Only through facts the prompt gives: pure logical generalization, little to connect to. |

A made-up relation always comes with at least one other made-up part or none:
subject+relation and relation+object inserts are not used, since they add
little over `relation` and `all`.

**Subject or object.** The two differ for a method even when they state the
same kind of fact. A made-up subject gives a method that edits at the subject
(ROME and its relatives) nothing stored to start from; a made-up object adds a
new value to a subject the model knows a lot about, and the new answer is a
name it has never seen. An `object` insert needs a relation that can hold
several values ("has a moon", "includes", "contains"): a new value of a
one-value relation ("capital of") would overwrite the real one, which is a
replace. Its direct question singles out the new value ("What is the name of
the newly found moon of Eris?"), so it has one answer. Don't write an `object`
insert as the flip of a `subject` insert in the same topic.

Per topic: ABox 2 `subject`, 2 `object`, 1 `subject_object`, 2 `relation`, 1
`all`; TBox 2 `subject` (a made-up class under a real one), 2 `relation` or
`object` (a real class with a made-up property, whichever the axiom makes it)
and 2 `subject_object` or `all`; RBox 3 `relation` (real instances in the
prompts) and 3 `all` (an RBox edit is always about a relation). Ids: ABox
`0001`-`0002` subject, `0003`-`0004` object, `0005` subject_object,
`0006`-`0007` relation, `0008` all; TBox `0009`-`0014` in the order above;
RBox `0015`-`0017` relation, `0018`-`0020` all.

**Determinacy.** Expansion records are determinate only: no aggregates,
superlatives or counts whose answer depends on how the model stores a list.

**Could it exist unrecorded?** A made-up entity must be something that could
exist without the record already knowing it: a newly found moon, species,
manuscript or minor town, whose discovery would simply update a count. Not
something the record would certainly know of: a new country bordering France,
a second opera by Beethoven, a sibling of a well-documented person. Those
falsify documented facts rather than add to them, and count as replaces.

**Rules.**
- Made-up names are new: near-zero corpus counts and a search showing no real
  thing by that name. Their evidence claim is `fictional`; bridge facts keep
  their own (real) evidence and checks.
- A fictional relation is catalogued in `RELATIONS.md` with "(fictional)" in
  its reading and the properties the prompts use.
- The insert contradicts nothing real: a slot that already has a real value is
  a replace, not an insert.
- `original_answer` is null; locality queries include the real things touched,
  so a leak ("Which cities are in Portugal?" now naming Velmora) is caught.

#### Shape per topic

There are two splits, built separately and sharing no edited fact or
subject (`validate.py` checks):

- **Main split** (`records/`): the test set the paper reports. 20 edits per
  topic and operation.
- **Dev split** (`dev/`): 120 new records only for hyperparameter tuning, 12
  per topic, with the simpler layout (no derived edits, no indeterminate
  queries).

**Main split, per topic:**

| Operation | ABox | TBox | RBox |
| --- | --- | --- | --- |
| Revision (replace) | 8: 6 stored (`very_unlikely`) + 2 derived (`very_likely`) | 6 | 6 |
| Contraction (delete) | 8: 4 on `functional` + 4 on `cardinality:many` relations | 6 | 6 |
| Expansion (insert, fictional) | 8 | 6 | 6 |

In ABox revision the stored edits come first (lowest ids), then the derived
ones. Each ABox revision record has 3 determinate derived queries and 1
indeterminate one: `background_beliefs` on a stored edit, `derived_beliefs`
(or a premise-route split) on a derived edit; a derived edit's 3 determinate
queries include one along the **premise route**. RBox edits cover, per
topic and operation, one each of transitivity, symmetry, inverse,
functional, subproperty and role chain.

**Dev split, per topic (12):**

| Operation | ABox | TBox | RBox |
| --- | --- | --- | --- |
| Revision (replace) | 4 | 1 | 1 |
| Contraction (delete) | 1 | 1 | 1 |
| Expansion (insert, fictional) | 1 | 1 | 1 |

Every dev edit is `very_unlikely` (stored) where derivability applies, and
every query is determinate. Its ids are `<topic>-<edit_operation>-dNNN`
(`geography-replace-d001`), in `dev/<topic>/<edit_operation>/`, and
`scripts/make_sids_split.py` lists every one of them as the dev split; the
main split is then all test.

**Choosing relations for coverage.** Which relation properties a record can
test depends on its relation: symmetry needs a symmetric relation (borders,
married to), transitivity a transitive one (located in, part of), a
contraction a functional or many-valued one. So edits are chosen partly for
their relation, to meet the per-topic balance
([Relation properties and task types](#relation-properties-and-task-types))
and CRITERIA Rule 12.

**Mathematics and grammar.** A fact about a particular number rests on
definitions and proofs, so no premise can give way ("91 = 7 × 13" can't), and
after an edit like "91 is prime" there is no consistent world to split
between; grammar's ABox edits are word forms anchored by firm examples. So
their ABox revision records have no derived (`very_likely`) edits and no
indeterminate query: their fourth derived query is a fourth determinate one,
and they leave out `worlds`.

Writing these needs care. Each indeterminate answer must really depend on a
storage choice that a reasonable model could make either way, and each world
must be consistent with everything else the record assumes. Each determinate
answer must hold in every world. When in doubt, a query is left out rather
than labelled.

#### Decisions on the open questions

Found while scouting all ten topics (2026-10-24) and settled before writing
records (2026-10-25). Each may be revisited.

1. **Which worlds count (step 3).** Each world lists the premise that gives
   way **and** the side facts that change with it (if Seattle's time zone
   gives way, Washington State's goes with it). A world is dropped only if it
   contradicts a firm fact about things outside the chain (dates, other
   places, other people), or if the premise is itself entailed by other firm
   facts, so it can't really give way.
2. **Class rules as premises.** ABox derived edits use premises about
   individuals only, never a class rule ("crocodilians have four-chambered
   hearts" invites an "except the gharial" revision, which leaves the
   premise-route query without one answer).
3. **Grammar.** ABox: word-form edits, all determinate. TBox: agreement rules
   ("Harry are good" belongs here), determinate like every TBox.
4. **Lopsided worlds** are kept and not weighted: one world being likelier
   doesn't make the other invalid.
5. **Scope** is not used: its answer is the same with or without the edit.
   Binding, composition and application are task types (2026-11-11).

#### Formal verification

`reason.py` checks the description-logic reasoning of the records with the
HermiT reasoner (owlready2), from encodings kept apart from the records in
`owl/formal/<record_id>.json` ([`owl/README.md`](owl/README.md) has the
schema, an example and an encoding guide). `owl/relations.py` compiles
RELATIONS.md into `owl/relations.owl`. Per record it checks that a derived
edit's premises entail the original fact; that every derived query's
original answer follows before the edit; that a determinate answer follows
in every world and an indeterminate one in its world, with the answers
differing; that each world is consistent; and, when the edit contradicts the
background, that every minimal repair (the smallest set of beliefs to give
up) is some world. `fol` queries are listed as not checked. CRITERIA Rule 1
shows the results (`owl/reason_report.json`).

```bash
venvs/easyedit_venv/bin/python datasets/SidsDataset/owl/encode_check.py --topic geography   # no HermiT
venvs/easyedit_venv/bin/python datasets/SidsDataset/reason.py --topic geography             # about 3 s per record
```

`justify.py` goes one step further: for every checked derived answer it
finds the minimal sets of axioms (the edit, background and world facts,
prompt-given facts, and each RELATIONS.md property axiom) the answer follows
from, the OWL notion of a justification, and compares them with the query's
`derivation`, `bridge`, `hops` and `via`: `match`, `partial` (derivation right,
bridges or hops differ), `mismatch` (the derivation type is not used) or
`not_checked`, with flags for answers that follow without the edit
(`no_edit`), for alternative derivations (`ambiguous`, or
`alternatives_listed` when `alt_derivations` names them) and for a revision
fact the answer is built from (`revision_as_bridge`). After editing records,
`justify.py --recompare` recomputes the verdicts from the stored
justifications without HermiT. Results go to
`owl/justifications.json` and a CRITERIA Rule 1 row; the full run is
`sbatch datasets/SidsDataset/owl/justify.sbatch` (owl/README.md,
Justifications).

Coverage: geography (all 60 records, every `dl` query). OWL caveats: the
world is open (a "no" needs a functional relation, a disjointness or a rule;
a "does not know" passes only when neither answer follows); there are no
unique names, so the file lists which individuals are `distinct`; functional
and asymmetric need simple properties, so transitive or chained ones keep
those tags as rules over named individuals (`owl/relations_report.md`).
Numbers, dates, counts, raises/lowers comparisons and closed-world claims
are not expressible.

## Running methods

Records reach the editing methods through
`experiments/run_experiment/sids_requests.py`, which `run_experiment.py`
uses for any `--data_path` under `datasets/SidsDataset`. Each record becomes
one edit request:

| | Edit prompt | Target |
| --- | --- | --- |
| replace | the direct question | the direct question's new answer |
| delete | the direct question | "I don't know" |

The paraphrase, cross-lingual, locality and derived questions travel with the
request; an indeterminate derived question carries its per-world answers.

Every requirement a method relies on is checked and raises a named error with
the record id (`EmptyTarget`, `TargetEqualsOriginal`, `MissingAnswer`,
`SubjectNotInPrompt`, ...) instead of being worked around: a run that gets
through has met them. Methods that edit at the subject's last token (ROME,
AlphaEdit, FiDAL, FiNE, IFMET, LTI and the other locate-and-edit methods)
need the subject verbatim, exactly once, in the question (for TBox and RBox
records, `edit.prompt_subject` names the words and which occurrence, so
there it may appear more than once). It is counted in
the question, not in the whole chat prompt: Llama 3.1's and SmolLM3's
templates write a date into a system turn ("Today Date: 26 Jul 2024"), which
holds mathematics-insert-0006's subject "6". Those methods are handed the
prompt with `{}` at the question's occurrence (`sids_requests.edit_request`),
so they never edit the template's copy. CRITERIA Rule 13 runs these checks on
every record without a GPU.

**Prompt format.** The edit is trained in the form evaluation asks it
(`sids_requests.render_prompt`, which the model audit imports too, so audit,
edit and evaluation see identical text). Base models: three worked examples
as `Question: ... / Answer: ...` lines ("Which city is Thailand's capital?"
Bangkok, "How many keys are on a piano?" 88, "Is a lemon sour?" Yes), then
the question. Instruct models (since 2026-11-01): their chat template, the
first two of those examples as earlier user/assistant turns, and the
instruction "Give only the answer, in as few words as possible. No sentence,
no explanation." in every user turn, no system turn. In the audit's tests
this cut answers wrapped in a sentence from 25% to 0%
(Llama-3.1-8B-Instruct) and from 40% to about 4% (Mistral-7B-Instruct-v0.1)
against the earlier single turn with "Answer the question in a few words,
without explanation." An earlier wording, "Answer with only the answer: a
name, a number, or yes/no", made Olmo-3-7B-Instruct answer "Yes" to
questions that are not yes/no ones (445 in the full audit), so it was
dropped. The examples share no question, answer or subject
with any record (test_sids_requests and the audit's ShotCollisionTests).

**Smoke run.** `run_experiment.py --smoke` (launched as **Method smoke run**
on the dashboard, `experiments/sids_smoke/`, one launch per model, all core
methods in turn) applies the method to every record one at a time and checks
each edit: the subject maps onto whole tokens, the target tokenizes, the
edited weights really changed and are finite, the model still generates, and
the original weights come back exactly. Failures go to
`results/sids_smoke/runs/smoke_<method>_<model>/smoke.jsonl`; a run that can't
restore the weights stops. Not yet run: the first gaivi run is also the test
of the smoke code itself.

**Open decisions** (the basic choice is implemented; to refine):

1. **TBox and RBox edit prompts.** Decided 2026-11-07: both use the direct
   question like ABox, and every TBox and RBox record names its edit span in
   `edit.prompt_subject` (`{"text", "occurrence"}`): the question's own
   wording of the record's `subject` (the class's noun phrase for TBox, the
   relation's wording for RBox), at its first mention. Before, the TBox
   subject was the class as the record names it and the RBox subject the
   first quoted wording in the question; 76 records failed Rule 13 that way
   ("bacterium" vs "Are bacteria ...?", `born_in` with no quote) and 12 RBox
   records with two quoted relations edited the other relation (or, after an
   apostrophe, a broken span). `edit.subject` keeps the ontology term.
2. **Scoring indeterminate questions.** Implemented (2026-11-01): see
   [Evaluation](#evaluation), Editing runs.

## Evaluation

We use our own evaluation functions rather than EasyEdit's, because delete
needs generated answers rather than token probabilities, an indeterminate
derived query has no single gold answer, and the query types map directly
onto metrics:

| Metric | Over | Reported as |
| --- | --- | --- |
| Rewrite | direct (1) | one number |
| Generalizability | paraphrase, related (near, far) and determinate derived | one number, plus each part (paraphrase, related near, related far, derived), per relation property, per task, per logic (dl, fol) and per hop count |
| Indeterminate change | the indeterminate derived query (main ABox revision) | reported apart: which world the answer picks, or that it stayed unchanged ([Main experiments](#main-experiments-sid_main)) |
| Cross-lingual | cross_lingual (2) | one number, plus per language |
| Logical consistency | propositional (3) | one number on its own, plus per connective (negation, conjunction, disjunction) |
| Specificity | unrelated near + far (2) | one number, plus near and far |
| Contraction abstention | a contraction record's direct, paraphrase and cross-lingual answers | one number |
| Answer diversity | the English generations | one number |
| Grammar | the English generations | one number |

> **Code status (2026-11-11).** `sid_evaluation.py` still scores the
> earlier layout: its `reliability` pools direct and paraphrase, it has no
> related queries, and it reads 2 propositional queries. It moves to this
> table after the current hyperparameter tuning (step 3) finishes, so that
> tuning keeps one definition throughout.

Answer diversity leaves out the cross-lingual answers, since n-gram scores
aren't comparable between Chinese and English text.

**Metric names.** We use names that say what is measured; each maps to a
common term in the knowledge-editing literature:

| Our name | Common name | What it is here |
| --- | --- | --- |
| Rewrite | reliability, edit success (EasyEdit; Yao et al. 2023), efficacy (ROME / CounterFact) | the edited (direct) question answered with the new answer |
| Paraphrase | generalization (EasyEdit), paraphrase score (CounterFact) | the edited fact asked in other words; part of Generalizability |
| Generalizability | portability (EasyEdit; Yao et al. 2023) | paraphrase, related and derived questions together |
| Cross-lingual | cross-lingual portability / generalization | the edited fact asked in Chinese and Spanish |
| Logical consistency | (ours; closest to logical-generalization portability) | yes/no truth-functional questions about the edited fact (propositional) |
| Specificity | specificity / neighborhood score (ROME, MEMIT, CounterFact), locality (EasyEdit; Yao et al. 2023) | unrelated near and far questions keep the unedited model's own answer, compared by the judge (CounterFact's version checks by probability that neighbourhood prompts still prefer the true original answer) |
| Answer diversity | fluency (ROME, Meng et al. 2022; EasyEdit) | n-gram entropy of a record's English answers joined, relative to the unedited model; on short answers it falls when one answer takes over the record's other questions, so it measures answer collapse rather than sentence quality |
| Grammar | (ours) | the judge's share of well-formed answers, relative to the unedited model |

Internal keys keep the original names (`reliability`, `rewrite`, `portability` /
`generalization`, `locality`, `fluency`), so stored results and code are unchanged.

### Main experiments (`sid_main`)

The main experiments add evaluation mode `sid_main`
(`experiments/run_experiment/sid_main_evaluation.py`; hyperparameter sweeps
keep `sid` for now). It reuses `sid`'s answers, judge and reliability,
locality and fluency, and reads derived queries differently, because under
`sid` an indeterminate query passes on any world's answer, and 503 of the 572
indeterminate queries have a world whose answer is the original one: a model
that never applied the edit passes them.

| Part | What it measures |
| --- | --- |
| Portability (headline) | Determinate derived queries the unedited model answered with the original answer (the hyperparameter selection's definition). All determinate queries and RBox queries are reported beside it. |
| Indeterminate change | Per answer: unchanged (the original), changed to a world's answer, or changed to an answer no world gives; rates over all and over known answers. An unchanged answer is diagnosed from its record: it fits one world and the record's determinate queries all passed (consistent with a world that stored the fact by name), it fits one world but some determinate query failed (the edit likely did not spread), or the record's answers fit no single world. |
| Hinted | Each determinate query whose bridge the question does not state is asked again with the bridge in front, never the edit. Plain pass: propagated. Only hinted pass: retrieval (the model holds the edit but does not bring the bridge to it). Both fail: not integrated. Asked at step 0 too as a control: a hint that already gives the new answer before the edit is counted as a leak, not as retrieval. Queries whose question already states the bridge are reported apart: their plain answer is the hinted test. |
| Reasoning | Each determinate query of a replace or insert record, asked to list the facts needed, reason step by step and end with "Answer: ...", without the short-answer instruction. The final answer is scored like the plain query; the reasoning judge compares the reasoning with the query's `chain` and labels it CORRECT, MISSED_EDIT, MISSED_FACT, WRONG_STEP, WRONG_FINAL or UNCLEAR, with the first reference step it gets wrong. |

Hinted and reasoning probes are asked at step 0 and at the final checkpoint
(every group's checkpoint under an edit protocol), not by SCR or IKE.

### Answering and judging

Every query is asked as a free-form question in the run's prompt format
(Running methods, Prompt format): base models get `Question: <prompt>` /
`Answer:` after three neutral worked examples, and generation stops at the
first line break; instruct models get their chat template with the strict
instruction after two worked turns, and the answer is cut at the first blank
line. Greedy, at most 64 new tokens.

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
| edit | `replace`, `insert` | `NEW` |
| edit | `delete` | `NONE` (abstains or only negates) |
| edit | indeterminate derived | the answer matches some world: a world's answer, or `NONE` where a world's answer is null |

In the model audit the judge is shown only the answer that row needs: the
original answer for replace and delete, the new answer for insert. Locality
questions aren't asked there, because an edit run takes its own pre-edit
baseline.

Locality queries use a second prompt with the same rules. It compares the
post-edit response with the model's own pre-edit response and labels them
`SAME`, `DIFFERENT` or `UNCLEAR`. Truth is again ignored, and both responses
declining to answer counts as `SAME`.

### Editing runs

`run_experiment.py` scores every Sid's Dataset run this way, as evaluation
mode `sid` (`experiments/run_experiment/sid_evaluation.py`). It is the
default and the only scoring for this dataset: `--evaluation_modes` `auto`
(the runner's default) and `original` (the dashboard's default) both mean
`sid` here, so EasyEdit's token accuracy never runs on these records (it
crashed on the indeterminate queries' missing gold). Generated-answer modes
(`exact_match`, `bertscore`, `llm_judge`) can be added on top; `sid` on any
other dataset is refused.

1. **Generation**, at every checkpoint the run evaluates (step 0, before any
   edit, included): every query of each edited record (direct, paraphrase,
   cross_lingual, propositional, unrelated near and far, derived), in the
   run's prompt format through `render_prompt`, the same text the edit was
   trained on. Answers go to `samples/sid_step_<step>.json`, keyed like the
   audit's queries (`direct`, `cross_lingual[zh]`, `propositional[0]`,
   `unrelated_near[0]`, `derived[2]`, ...).
2. **Judging**, once, after the last checkpoint: the edited model is
   unloaded, the judge loaded, and every stored answer labelled (identical
   question and answer pairs once). Candidates shown: original and new
   answer for replace and insert; only the original for delete (abstaining
   or only denying it is `NONE`, the pass label; "I don't know" is not shown
   as a candidate, since `NONE` already is that answer); for an
   indeterminate derived query, the original plus every world's answer (a
   world answer that is neither is labelled `WORLD`). Propositional queries
   are yes/no answers like any other. Locality: the post-edit answer against
   the same model's step-0 answer (`SAME` passes; step 0 itself is `SAME`).
   The judge's agreement on `judge_cases.json` is saved with the run.
3. **Scoring** in code, per the tables above; `UNCLEAR` is excluded and
   counted. Each metric block is `{score (percent), pass, scored, unclear,
   total}`, plus `known`: the same over the queries whose step-0 answer was
   labelled `ORIGINAL` (the fact was held before the edit). Fluency is
   EasyEdit's bigram/trigram entropy of each record's English answers joined,
   averaged and multiplied by 100 like the original mode's.

Each `checkpoints.jsonl` row gets `evaluations.sid` once the run has been
judged (rows are written live without it), and `summary.json` the last
checkpoint's (under an edit protocol, every group's answers pooled):
`edit_succ` = reliability, `portability` = generalization, `locality`,
`fluency`, `coverage`, and `metrics` with `reliability`, `cross_lingual`
(`by_language`), `logical_consistency` (`by_form`), `generalization`
(`determinate`, `indeterminate`, `by_problem`, `by_logic`, `by_derivation`,
`worlds`: matches per world, records whose answers agree on a world or mix
worlds), `locality` (`near`, `far`) and `delete_abstention`; then
`by_operation`, `labels` and `records`. The row's and the summary's headline
fields are the `sid` ones, marked `headline_evaluation: "sid"`, so the
Results page (evaluation "Sid's judge") and the sweeps read these runs like
any other. The Responses view shows each answer with its label, reason and
matched worlds.

## Records

Two folders, one per split ([Shape per topic](#shape-per-topic)):
`records/` (main split, the test set) and `dev/` (dev split, tuning only).

### Layout

One JSON file per edit, grouped by topic and then edit operation:

```
datasets/SidsDataset/
  README.md, CRITERIA.md       the spec and the quality bar
  RELATIONS.md                 the relations catalogue (properties per relation)
  relation_checks.json         one audit question per relation property in use
  validate.py                  checks every record against all of these
  examples/                    one complete, valid record per record type
  records/<topic>/<edit_operation>/<topic>-<edit_operation>-NNNN.json   main split
  dev/<topic>/<edit_operation>/<topic>-<edit_operation>-dNNN.json       dev split
```

One file per edit keeps each record reviewable on its own, keeps Git diffs
and merges small, and makes the browsing order (topic, then operation)
the folder order. The coordinates are still stored inside each record, so a
loader never has to parse paths. Numbers count up within a topic, operation
and split; ids are never reused.

### Adding a record

1. Copy the template for its record type from `examples/` into the right
   folder, and rename it to the next free id (`id` and the file name must
   match).
2. Fill in the coordinates, the relation (it must be in `RELATIONS.md`; add
   it there first if not), the edit, and the queries its record type carries
   ([Queries per record type](#queries-per-record-type)). The relation's tags
   are not copied into the record; code that needs them looks them up with
   `load_relations()` in `validate.py`.
3. Run the validator from the project root:

   ```bash
   python datasets/SidsDataset/validate.py            # main split
   python datasets/SidsDataset/validate.py dev        # dev split
   ```

   It prints every problem with the file and field, then a count per topic
   and operation. Fix everything it reports before committing.

### Format

Every field below is required unless marked optional. Unknown fields are
rejected, so typos don't silently drop data.

| Field | Type | Rule |
| --- | --- | --- |
| `id` | string | `<topic>-<edit_operation>-NNNN` (main) or `-dNNN` (dev), same as the file name |
| `edit_operation` | `insert` \| `replace` \| `delete` | |
| `topic` | one of the 10 topic keys | |
| `box` | `abox` \| `tbox` \| `rbox` | |
| `edit.statement` | string | the edit as one or more sentences |
| `edit.subject` | string | |
| `edit.prompt_subject` | object, tbox and rbox only | `{"text": ..., "occurrence": n}`: the words of the direct question the edit is about (the question's wording of `edit.subject`) and which occurrence of them (1 = first); where locate-and-edit methods edit. Left out of review hashes |
| `edit.object` | string | required except for `rbox`, which has none; for delete, the removed value |
| `edit.old_object` | string | replace only, and required there when the edit has an object; with `edit.object` it is the [Change](#change) tag |
| `edit.premises` | string list | the facts the edited (original) fact follows from, and the rule or relation property combining them as a sentence; required exactly when `derivability` is `very_likely` |
| `edit.axiom` | string, optional | DL form for TBox and RBox, e.g. `Trans(located_in)` |
| `edit.original` | string, optional | the fact or rule before the edit, as a sentence |
| `relation` | string | a relation in `RELATIONS.md`; for ABox contraction, one tagged `functional` or `cardinality:many` |
| `derivability` | `very_unlikely` \| `very_likely` \| null | the edited (original) fact; set for `abox` and `tbox` replace and delete, null otherwise; `very_likely` only on main-split ABox revision |
| `reality` | `fictional` | insert only, and required there |
| `fictional` | string | insert only: which parts of the triple are made up ([Insert (fictional)](#insert-fictional)) |
| `worlds` | list, main ABox revision only | 2 to 4 `{id, assumes, summary}` with unique ids and a non-empty `assumes` list; present exactly when the record has its indeterminate query |
| `queries` | object | the queries of the record's type ([Queries per record type](#queries-per-record-type)), in the order of the Query type table |
| `checks` | list | one `{fact, prompt, answer}` per fact `facts_to_check()` lists (premises, then bridge and revision facts not stated in a prompt), plus one per propositional side fact unless it is trivial, with `fact` copied exactly; empty or absent when there are none. The model audit asks each before editing |
| `evidence` | object | why each fact is rated stored or derived, keyed by the fact's exact text (see [Evidence](#evidence)); required for the edited fact, every premise and every related and derived query's `fact` |
| `notes` | string, optional | anything a reviewer needs: why a rating, why a topic uses another property than the balance asks |

Each query:

| Field | Type | Rule |
| --- | --- | --- |
| `prompt` | string | the question as asked |
| `original_answer` | string \| null | the answer before the edit; null for insert |
| `new_answer` | string \| null | the answer after the edit; null for delete (does not know) and on the indeterminate query |
| `language` | `zh` \| `es` | cross-lingual only, one of each |
| `reference` | string, optional | unrelated queries only (which have no answer fields): a reference answer for auditing; the scoring gold is the model's own pre-edit answer |

Related and derived queries add:

| Field | Type | Rule |
| --- | --- | --- |
| `derivation` | see [Relation properties and task types](#relation-properties-and-task-types) | the relation property the answer rests on; must be allowed for the query (related near, related far, derived) and be a tag of the relation it uses |
| `task` | `answer` \| `application` | what the question asks the model to do with the conclusion |
| `hops` | integer | 1 + number of bridge facts (revision facts not counted): related near 1, related far 2 or more, determinate derived 2 (contraction's cardinality question 1) |
| `bridge` | string list | the facts the answer is built from; empty if none |
| `bridge_in_prompt` | bool, optional | the bridge facts are stated in the prompt, so they aren't checked before editing |
| `via` | string, optional | the relation whose tag licenses the derivation, when it isn't the edited relation |
| `fact` | string | the fact the question asks about, as the model holds it before the edit (for insert, after); its `evidence` backs `derivability` |
| `derivability` | `very_unlikely` \| `very_likely` | related: `very_unlikely` (stored); derived: `very_likely` (worked out); the indeterminate and RBox queries leave it out |
| `determinacy` | `determinate` \| `background_beliefs` \| `derived_beliefs` | `determinate` everywhere except the one indeterminate query of a main-split ABox revision record |
| `determinacy_why` | string | required on the indeterminate query: why the answer is open |
| `world_answers` | object | exactly on the indeterminate query: one `{answer, chain}` per world, keyed by the record's world ids, with at least two different answers |
| `chain` | string list | the steps from the edit to the answer, one fact or rule per step |
| `premise_route` | bool, optional | on a determinate query of a `very_likely` edit: the query reaches the edited fact along its premises |
| `revision_facts` | string list, optional | facts that settle which belief gives way, not combined into the answer (not counted in `hops`) |
| `revision_in_prompt` | bool, optional | with `revision_facts`: they are stated in the prompt (default: the value of `bridge_in_prompt`) |
| `alt_derivations` | string list, optional | other derivations that reach the same answer by another valid route |
| `logic` | `dl` \| `fol` | the weakest logic the inference needs |
| `theory` | `arithmetic` \| `temporal`, optional | with `logic: fol`: a theory the inference uses on top |

A propositional query has its own fields ([Propositional
queries](#propositional-queries)). The record's keys come in the order of the
record table: identity, the edit, the relation, derivability, then the rest.

`examples/` holds one complete, valid record per record type (ABox revision
with a stored and with a derived edit, ABox contraction on a functional and
on a many-valued relation, ABox expansion, TBox and RBox revision,
contraction and expansion), each passing `validate.py`. When in doubt, copy
the closest one.

### Current records and migration

The records in `records/` were written for the earlier layout (until
2026-11-11) and are being moved to this one. What still differs, per record
(the problem list in `REFINEMENTS.md` has the counts and record ids):

- 2 propositional queries (negation and one of conjunction or disjunction)
  instead of 3;
- no related queries;
- 4 derived queries (2 determinate, 2 indeterminate) on ABox and TBox records,
  some at 1 or 3+ hops; `binding`, `application` and `composition` given as a
  derivation instead of a task (they are tasks now, with `derivation: none` or
  a property), `scope` and `asymmetry` used, and no `task`, `fact` or
  per-query `derivability`;
- derivability `unlikely`, `medium` or `likely` on some edits, and 4 derived
  edits per topic instead of 2;
- contraction records that mirror revision records, and real inserts;
- leftover fields of earlier versions (`familiarity`, `relation_semantics`,
  `source`, `edit.fixture`, `edit.scope`), rejected by the validator.

`validate.py` reports each of these as an error; a migrated record passes
clean.

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

Main split: 10 topics × 3 operations × 20 edits (8 ABox, 6 TBox, 6 RBox),
600 edits. Dev split: 120 edits. Query counts per record type are in
[Queries per record type](#queries-per-record-type).

## Dashboard

The machine-readable version of this scheme is
`dashboard/frontend/src/lib/sidsDatasetTaxonomy.js`, rendered on the
dashboard's Datasets page; keep it, this file and `validate.py` in sync. The
page still shows the scheme rather than records; registering subsets in
`datasetCatalog.js` switches it over once records exist.

Review marks (CRITERIA.md, manual rules) are made on the record cards of
that browser: pick yourself under "Reviewing as" and turn on Review mode
(both remembered in the browser); then clicking one of your own dots cycles
it yellow (not reviewed), green (fine), red (flagged). Each card has a
dotted box with one line per manual rule, and each query row its own dots,
one per reviewer: Codex, Claude, Mustafa, Fengchun, Adarsh. "Next
unreviewed" jumps to the next record where your rule marks are still
yellow. Marks go to `reviews.json` under a lock; agents mark as `codex` or
`claude`, through the dashboard API or `criteria.py --mark RECORD ITEM claude
green|red|clear [--comment NOTE] [--kind problem|angle]` (`--marks` lists the
counts and every red mark). The Criteria checklist shows each rule's
guidance, green / red / yellow counts per reviewer, and every red item.
