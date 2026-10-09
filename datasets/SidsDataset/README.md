# Sid's Dataset

Our own knowledge-editing benchmark. Empty for now: this file is the
specification, the records get built against it. The relations we use, their
properties and the derived questions each property licenses live in
[`RELATIONS.md`](RELATIONS.md).

## Why

Published editing benchmarks test a fairly narrow notion of knowledge, mostly
simple factual triples, and measure generalization with paraphrases. This one
spans a wider range of knowledge (facts, rules, properties of relations,
causal and associative, axiomatic and derived) and measures
generalization with questions that *logically follow* from the edit, so a
method can't pass by matching the surface form of the edit.

> Under what kinds of knowledge and edit operations does a knowledge edit
> succeed, propagate to what follows from it, and stay contained?

## Three levels

```
Edit operation  >  Knowledge form  >  Query type
insert            topic               direct        (1)
replace           box                 paraphrase    (1)
delete            relation semantics  cross-lingual (2: zh, es)
                  derivability        derived       (4)
                                      unrelated     (2 near + 2 far)
```

Every item is one edit plus exactly 12 queries.

### 1. Edit operation

| Key | What it does | Expected answer afterwards |
| --- | --- | --- |
| `insert` | Adds knowledge the model does not hold. | The new answer. |
| `replace` | Swaps held knowledge for a false-but-plausible alternative. Counterfactual by construction: the original is something every LLM has seen and holds true. | The new answer, and never the old one. |
| `delete` | Removes knowledge the model does hold. | No longer the old answer: the model should say it does not know, or negate it. See [Delete](#delete). |

### 2. Knowledge form

Four layers, each nested under the one before it. Some layers only exist
under some branches.

**Topic.** `geography`, `people` (facts about famous people), `history`,
`finance` (including textbook economic laws), `biology` (including medicine),
`physics`, `mathematics`, `grammar`, `literature_arts`. A diversity control, so a finding about rules
isn't secretly a finding about mathematics. It also keeps the records
organized for browsing.

**Box.** How description logic divides a knowledge base:

| Key | What it holds | DL | Example |
| --- | --- | --- | --- |
| `abox` | Facts about particular individuals | R(a, b), C(a) | Paris is the capital of France. |
| `tbox` | Rules about classes: every C is (or does) D | C ⊑ D, C ⊑ ∃R.D | Every capital is a city. Smoking causes lung cancer. |
| `rbox` | Properties of relations themselves | Trans(R), Sym(R), R ≡ S⁻, R ∘ S ⊑ T | "Located in" is transitive. "Sibling of" is symmetric. |

A single TBox or RBox edit should move every individual it covers, which is
why they're expected to behave differently from ABox edits.

**Relation semantics** (`abox` and `tbox` only; `null` for `rbox`):

| Key | What it is | ABox example | TBox example |
| --- | --- | --- | --- |
| `causal` | The relation says one thing brings about another. | The 2008 crisis caused Lehman Brothers to collapse. | Smoking causes lung cancer. |
| `associative` | Any other relation: membership, location, ownership, role, part of. | Paris is the capital of France. | Every capital is a city. |

Causation is outside standard description logic. Here it's modelled as a
relation (`causes`, `prevents`) with its own properties in `RELATIONS.md`.
Causation is not transitive in general, so chained causal derivations are
only used where the chain is well established.

**Derivability** (`abox` and `tbox` only; `null` for `rbox`): whether the
edited fact or rule is a base claim or a consequence of others.

| Key | What it is | ABox example | TBox example |
| --- | --- | --- | --- |
| `axiomatic` | Stated directly; nothing else the model knows entails it. | Paris is the capital of France. | Every square is a rectangle. |
| `derived` | Follows from other facts or rules the model holds (its `premises`). | The Eiffel Tower is in France (it is in Paris, and Paris is in France). | Every square is a polygon (every square is a rectangle, every rectangle is a polygon). |

> **Derivability is model specific.** Whether a fact is axiomatic or derived
> really depends on the model: one model may store "the Eiffel Tower is in
> France" directly, another may work it out from its premises each time, and
> we can't observe which. For this dataset, items are labelled by what is
> *likely* to be stored versus derived, using our own intuition and criteria.
> Those criteria will be detailed later.

Editing a derived fact leaves its premises pointing at the old answer, so the
model may re-derive it and slide back. That is the failure this layer is
meant to expose. Rules for derived items:

- **Replace and delete only.** Inserting a fact the model can already derive
  adds nothing, so `insert` items are always `axiomatic`.
- **Premises are listed** in `edit.premises` and checked before editing, like
  bridge facts: if the model doesn't hold them, it can't derive the fact, and
  the item is dropped for that model.
- **Premises stay unchanged.** The edit asks only for the conclusion to
  change, so premises are expected to keep their answers; ask them as the
  near unrelated queries (the derived template does). The result is a
  deliberately inconsistent world, and whether the model holds the edit
  anyway or reverts to what its premises imply is the finding.

That gives 9 knowledge-form leaves per topic:

| Box | Relation semantics | Derivability |
| --- | --- | --- |
| ABox | causal | axiomatic, derived |
| ABox | associative | axiomatic, derived |
| TBox | causal | axiomatic, derived |
| TBox | associative | axiomatic, derived |
| RBox | | |

With insert limited to the 5 axiomatic leaves, that is 5 + 9 + 9 = 23 cells
per topic, 207 in all. Not every cell exists naturally: mathematics and
grammar have no causal knowledge. Those
cells stay empty rather than being filled with forced examples, and
comparisons across topics should only use cells both topics have.

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

#### Cross-lingual queries

The edit is always made in English. The two cross-lingual queries ask the
direct question in Chinese and Spanish, to see whether the edited knowledge
is stored as language-independent knowledge or only as an English string.
Chinese is far from English (different script, so the answer can't be copied
token for token); Spanish is close. The gap between them is part of the
finding.

- Each records its `language` and the `expected` answer written in that
  language, with aliases (e.g. 里昂 for Lyon, and "Lyon" itself, since names
  are often left untranslated).
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
| `functional` | R has one value per subject | Replace only. Ask: is Paris still the capital of France? (expected: no) |
| `composition` | Any relation + a bridge fact | Edit: the capital of France is Lyon. Bridge: the Rhône flows through Lyon. Ask: which river flows through the capital of France? |
| `inheritance` | TBox C ⊑ D + a known member | Edit: every capital is a port. Ask: is Paris a port? |
| `instantiation` | RBox axiom + instance facts | Edit: "borders" is symmetric. Ask an instance in the reverse direction. |

`composition` is the multi-hop question (as in MQuAKE): the edited fact is
one hop and a fact the model already knows is the next. It needs no relation
property, so every relation supports it, which helps items whose relation has
few tags still reach 4 derived queries.

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

Each query is scored from the generated answer, by its `behavior`:

- `answer`: correct if the expected answer (or an alias) appears and no
  `forbidden` answer does.
- `abstain_or_negate`: correct if no `forbidden` answer appears and the
  response abstains or negates.
- `unchanged`: correct if the post-edit answer matches the model's own
  pre-edit answer.

Matching starts with normalized string and alias matching; an abstention and
negation classifier (patterns first, a judge model if needed) handles delete.
These functions don't exist yet.

## Records

### Layout

One JSON file per edit, grouped by topic and then edit operation:

```
datasets/SidsDataset/
  README.md, RELATIONS.md     the spec and the relations catalogue
  validate.py                 checks every record against both
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
| `topic` | one of the 9 topic keys | |
| `box` | `abox` \| `tbox` \| `rbox` | |
| `relation_semantics` | `causal` \| `associative` \| null | null for `rbox`; must match `RELATIONS.md` |
| `derivability` | `axiomatic` \| `derived` \| null | null for `rbox`; `axiomatic` for insert |
| `relation` | string | a relation in `RELATIONS.md` |
| `edit.statement` | string | the edit as one or more sentences |
| `edit.subject`, `edit.object` | string | for delete, `object` is the removed value |
| `edit.old_object` | string | replace only, and required there |
| `edit.premises` | string list | derived only, and required there: the facts or rules the edited one follows from |
| `edit.axiom` | string, optional | DL form for TBox and RBox, e.g. `Trans(located_in)` |
| `queries` | object | the 12 queries, below |
| `notes` | string, optional | |

Each query:

| Field | Type | Rule |
| --- | --- | --- |
| `prompt` | string | the question as asked |
| `behavior` | `answer` \| `abstain_or_negate` \| `unchanged` | `unchanged` for unrelated queries; otherwise `abstain_or_negate` under delete and `answer` under insert and replace |
| `expected` | string \| null | null exactly when `abstain_or_negate` |
| `aliases` | string list, optional | other accepted answers |
| `forbidden` | string list | the old answer; required for every reliability query under replace and for every `abstain_or_negate` query |
| `language` | `zh` \| `es` | cross-lingual only, one of each |
| `derivation` | see derived queries | derived only |
| `hops` | integer | derived only; 1 + number of bridge facts |
| `bridge` | string list | derived only; empty if none |
| `via` | string, optional | derived only; the relation whose tag licenses the derivation, when it isn't the edited relation |

`queries` holds `direct` and `paraphrase` (one object each), and
`cross_lingual` (2), `derived` (4), `unrelated_near` (2) and `unrelated_far`
(2) as lists. The validator also checks that each derivation's tag exists on
the relation it uses, that `functional` appears only under replace,
`inheritance` only for TBox, `instantiation` only (and always) for RBox, and
that transitivity, chain, composition and inheritance have a bridge fact.

The templates in `examples/` are complete, valid records: an axiomatic
replace (`geography-replace-0001`), an axiomatic delete
(`geography-delete-0001`), and a derived replace (`geography-replace-0002`).

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
- **Temporality** (event vs timeless). Dropped because there was no clear
  reason it should change whether an edit succeeds.

## Dashboard

The machine-readable version of this scheme is
`dashboard/frontend/src/lib/sidsDatasetTaxonomy.js`, rendered on the
dashboard's Datasets page; keep it, this file and `validate.py` in sync. The
page still shows the scheme rather than records; registering subsets in
`datasetCatalog.js` switches it over once records exist.
