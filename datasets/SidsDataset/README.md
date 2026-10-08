# Sid's Dataset

Our own knowledge-editing benchmark. Empty for now: this file is the
specification, the records get built against it. The relations we use, their
properties and the derived questions each property licenses live in
[`RELATIONS.md`](RELATIONS.md).

## Why

Published editing benchmarks test a fairly narrow notion of knowledge, mostly
simple factual triples, and measure generalization with paraphrases. This one
spans a wider range of knowledge (facts, rules, properties of relations,
causal and associative, events and standing facts) and measures
generalization with questions that *logically follow* from the edit, so a
method can't pass by matching the surface form of the edit.

> Under what kinds of knowledge and edit operations does a knowledge edit
> succeed, propagate to what follows from it, and stay contained?

## Three levels

```
Edit operation  >  Knowledge form  >  Query type
insert            topic               direct        (1)
replace           box                 paraphrase    (1)
delete            relation semantics  derived       (4)
                  temporality         unrelated     (2 near + 2 far)
```

Every item is one edit plus exactly 10 queries.

### 1. Edit operation

| Key | What it does | Expected answer afterwards |
| --- | --- | --- |
| `insert` | Adds knowledge the model does not hold. | The new answer. |
| `replace` | Swaps held knowledge for a false-but-plausible alternative. Counterfactual by construction: the original is something every LLM has seen and holds true. | The new answer, and never the old one. |
| `delete` | Removes knowledge the model does hold. | No longer the old answer: the model should say it does not know, or negate it. See [Delete](#delete). |

### 2. Knowledge form

Four layers, each nested under the one before it. Some layers only exist
under some branches.

**Topic.** `finance`, `economics`, `biology`, `physics`, `chemistry`,
`mathematics`, `grammar_language`, `philosophy`, `people`, `geography`,
`history`, `technology`. A diversity control, so a finding about rules isn't
secretly a finding about mathematics. It also keeps the records organized for
browsing.

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

**Temporality** (`abox` only; `null` otherwise):

| Key | What it is | Example |
| --- | --- | --- |
| `event` | Happened at a point in time. | Marie Curie discovered radium in 1898. |
| `timeless` | Not tied to a moment. Covers facts that are always true *and* standing states that hold over a period. | 7 is prime. Paris is the capital of France. |

That gives 7 knowledge-form leaves per topic:

| Box | Relation semantics | Temporality |
| --- | --- | --- |
| ABox | causal | event, timeless |
| ABox | associative | event, timeless |
| TBox | causal | |
| TBox | associative | |
| RBox | | |

So 3 operations × 12 topics × 7 forms = 252 cells.

### 3. Query type

Fixed per item: **1 direct, 1 paraphrase, 4 derived, 2 near unrelated, 2 far
unrelated**. Fixing the counts gives every item the same weight in every
metric.

| Key | Count | What it is | Metric |
| --- | --- | --- | --- |
| `direct` | 1 | The edited fact asked as a question, in the edit's own wording. | Reliability |
| `paraphrase` | 1 | The same question in different words. | Reliability |
| `derived` | 4 | A question whose answer follows from the edit through a property of the relation (see below). | Generalization |
| `unrelated_near` | 2 | Shares the subject, the relation or the topic, but does not follow from the edit. "What is the official language of France?" after editing France's capital. | Locality |
| `unrelated_far` | 2 | Nothing in common with the edit. | Locality |

Near unrelated queries are what make locality informative: far-only locality
is close to 100% for almost every method.

#### Derived queries

What can be derived depends on the relation's properties, recorded as
`relation_tags` on each item. `RELATIONS.md` lists each relation's tags and
the question template each tag gives. Summary:

| Derivation | Comes from | Example |
| --- | --- | --- |
| `symmetry` | Sym(R) | Edit: Billy is a sibling of Manny. Ask: is Manny a sibling of Billy? |
| `inverse` | R ≡ S⁻ | Edit: Ann is Billy's parent. Ask: who is Ann's child? |
| `asymmetry` | Asym(R) | Edit: Ann is Billy's parent. Ask: is Billy Ann's parent? (expected: no) |
| `transitivity` | Trans(R) + a bridge fact | Edit: Lyon is in France. Bridge: France is in Europe. Ask: is Lyon in Europe? |
| `chain` | R ∘ S ⊑ T + a bridge fact | Edit: she was born in Lyon. Bridge: Lyon is in France. Ask: which country was she born in? |
| `subproperty` | R ⊑ S | capital of ⊑ located in. Ask: which country is Lyon located in? |
| `functional` | R has one value per subject | Replace only. Ask: is Paris still the capital of France? (expected: no) |
| `inheritance` | TBox C ⊑ D + a known member | Edit: every capital is a port. Ask: is Paris a port? |
| `instantiation` | RBox axiom + instance facts | Edit: "borders" is symmetric. Ask an instance in the reverse direction. |

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

Deleting removes a fact; we then ask the direct, paraphrase and derived
questions again. Success means the model **no longer gives the old answer**,
and instead either:

- `abstain`: says it does not know, or
- `negate`: says the fact does not hold.

Both count as success, and which one the model chose is recorded. For
relations with many possible values (`cardinality: many`, e.g. "speaks
language") this is an open-world test: removing one value doesn't make any
other value true, so abstaining is the honest answer. For functional
relations a negation is also reasonable. Derived queries work the same way:
after deleting "Lyon is in France", "Is Lyon in Europe?" should no longer be
answered through that chain.

## Evaluation

We use our own evaluation functions rather than EasyEdit's, because delete
needs generated answers rather than token probabilities, and the query types
map directly onto metrics:

| Metric | Over | Reported as |
| --- | --- | --- |
| Reliability | direct + paraphrase (2) | one number |
| Generalization | derived (4) | one number, plus per derivation type |
| Locality | unrelated near + far (4) | one number, plus near and far |
| Fluency | all 10 generations | one number |

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

## Item shape

One record per edit:

```json
{
  "id": "geography-replace-abox-associative-timeless-0001",
  "edit_operation": "replace",
  "topic": "geography",
  "box": "abox",
  "relation_semantics": "associative",
  "temporality": "timeless",
  "relation": "has_capital",
  "relation_tags": ["functional", "inverse:capital_of"],
  "edit": {
    "statement": "The capital of France is Lyon.",
    "subject": "France",
    "object": "Lyon",
    "old_object": "Paris"
  },
  "queries": {
    "direct": { "prompt": "What is the capital of France?", "behavior": "answer", "expected": "Lyon", "forbidden": ["Paris"] },
    "paraphrase": { "prompt": "Which city serves as France's capital?", "behavior": "answer", "expected": "Lyon", "forbidden": ["Paris"] },
    "derived": [
      { "prompt": "Lyon is the capital of which country?", "behavior": "answer", "expected": "France", "derivation": "inverse", "hops": 1, "bridge": [] },
      { "prompt": "Is Paris the capital of France?", "behavior": "answer", "expected": "No", "derivation": "functional", "hops": 1, "bridge": [] },
      { "prompt": "Which country is Lyon located in?", "behavior": "answer", "expected": "France", "derivation": "subproperty", "hops": 1, "via": "capital_of", "bridge": [] },
      { "prompt": "On which continent is the capital of France?", "behavior": "answer", "expected": "Europe", "derivation": "transitivity", "hops": 2, "bridge": ["France is in Europe."] }
    ],
    "unrelated_near": [
      { "prompt": "What is the official language of France?", "behavior": "unchanged", "expected": "French" },
      { "prompt": "What is the capital of Spain?", "behavior": "unchanged", "expected": "Madrid" }
    ],
    "unrelated_far": [
      { "prompt": "What is the chemical symbol for gold?", "behavior": "unchanged", "expected": "Au" },
      { "prompt": "Who wrote Hamlet?", "behavior": "unchanged", "expected": "William Shakespeare" }
    ]
  },
  "notes": ""
}
```

For `delete`, the reliability and derived queries use `"behavior":
"abstain_or_negate"` with `expected: null` and the old answer in `forbidden`.
TBox and RBox edits keep the same shape: `subject` and `object` may be
classes, and `edit.axiom` can hold the DL form (e.g. `"Trans(located_in)"`).

`relation_tags` copies the relation's tags from `RELATIONS.md` so a record
can be read on its own; `RELATIONS.md` is the source of truth.

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

## Layout note

The `finance/`, `health/`, `education/` and `physics/` directories are left
over from an earlier `<domain>/<edit nature>/<knowledge type>/` scaffold and
are empty. Records should live flat (one file per topic, or one per batch)
with the coordinates carried in each record. The machine-readable version of
this scheme is `dashboard/frontend/src/lib/sidsDatasetTaxonomy.js`, rendered on
the dashboard's Datasets page; keep the two in sync.
