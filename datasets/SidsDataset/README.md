# Sid's Dataset

Our own knowledge-editing benchmark. Empty for now: this file is the
specification, the records get built against it.

## Why

Published editing benchmarks test a fairly narrow notion of knowledge, mostly
simple factual triples. This one is built to span a much wider **knowledge
spectrum** and ask how different *kinds* of knowledge behave under editing.

The goal is not only "which editing method performs best". It is:

> Under what kinds of knowledge, edit operations and structural conditions
> does a knowledge edit become risky?

That is, does edit success depend on the knowledge being rule-like rather than
factual, on it being a negation or a count or a hierarchy rather than a plain link, on how
densely connected it is, on whether it was inserted or deleted or replaced, on
how the update was phrased?

## Not a hierarchy

Every item is described by **coordinates on several independent axes**, not by
a position in one tree. Each question above varies along a different axis, so a
single hierarchy would force an arbitrary precedence between them and make
matched examples impossible to express.

```
Topic x Edit Type x Knowledge Form x Edit Representation x Connectivity x Dependency
```

Matched examples are the point: same topic and similar knowledge form but
different connectivity, or one knowledge item expressed several different ways.
That is what lets a failure be attributed to a factor, instead of comparing two
examples that differ in every respect at once.

The machine-readable version of everything below lives in
`dashboard/frontend/src/lib/sidsDatasetTaxonomy.js`, and the dashboard's
Datasets page renders it (the "?" beside the dataset name). Keep the two in
sync.

## Axes

### Topic

`finance`, `economics`, `biology`, `physics`, `chemistry`, `mathematics`,
`grammar_language`, `philosophy`, `people`, `geography`, `history`,
`technology`.

The first layer. Mainly a diversity control, so that a finding about rules is
not secretly a finding about mathematics.

### Edit type

`insert`, `replace`, `delete`. Independent of knowledge form: in principle any
form can be inserted, replaced or deleted, and whether that actually holds is
itself a finding.

Everything under `replace` is counterfactual by construction. The original is
something we are confident every LLM has seen and holds true, swapped for a
false-but-plausible alternative.

### Knowledge form

The substantive axis, categorized the way description logic carves up a
knowledge base rather than as knowledge-graph entity-relation triples.
Existing benchmarks concentrate almost entirely on the first entry.

Three tiers: **fact vs rule**, then the kind of fact or rule, then the form.
Facts are claims about particular individuals (the DL ABox). Rules are claims
about descriptions or relations in general (the TBox and RBox), so a single
rule edit should move every individual it covers.

| Tier | Group | Key | Form | DL | Example |
| --- | --- | --- | --- | --- | --- |
| Fact | Links (a R b) | `plain_link` | Plain link | R(a, b) | Paris is the capital of France. |
| Fact | Descriptions of one thing (a fits C) | `membership` | Plain membership | C(a) | Paris is a city. |
| | | `negation` | Negation | ¬C(a) | Marie does not speak German. |
| | | `disjunction` | Disjunction ("or") | (C ⊔ D)(a) | Alex is a doctor or a nurse. |
| | | `existential` | Existential ("some") | ∃R.C(a) | Marie speaks some Romance language. |
| | | `universal` | Universal ("all") | ∀R.C(a) | Everyone in this class passed. |
| | | `counting` | Counting | (= n R.C)(a) | Marie speaks exactly three languages. |
| Rule | Rules about descriptions (every C is D) | `hierarchy` | Hierarchy | C ⊑ D | Every capital is a city. |
| | | `constraint` | Constraint | C ⊑ (= 1 R.D), C ⊓ D ⊑ ⊥ | Every country has exactly one capital; nothing is both a city and a country. |
| Rule | Rules about relations | `relation_rule` | Relation rule | Trans(R), R ≡ S⁻ | "Located in" is transitive; "capital of" flips to "has capital". |

#### Fact temporality

Facts carry one more layer, `temporality`: how the fact sits in time. It cuts
across the fact forms rather than nesting under one (a plain link can be a
state or an event; a membership can be timeless or a state), so it is its own
field, `null` for rules.

| Key | What it is | Example |
| --- | --- | --- |
| `timeless` | True independent of time: mathematics, facts that hold by what the terms mean | 7 is a prime number. |
| `state` | True over a period that can end: capitals, who holds an office | Paris is the capital of France. |
| `event` | Happened at a point in time: an assassination, a discovery | Marie Curie discovered radium. |

Records store `knowledge_form` (tier and group follow from it) and, for facts,
`temporality`. A
definition ("a bachelor is an unmarried adult man") is a hierarchy in both
directions (C ≡ D).

Rules matter because one edit should license an unbounded number of changed
outputs. The description forms matter because each has its own entailments:
editing a negation, a disjunction or a count should change different
downstream answers than editing a plain membership.

### Edit representation

How the update is communicated, holding the intended edit operation fixed. Two
groups.

**Phrasing** is the level under plain links (other forms are always
`direct` for now). Same edit, three ways:

| Key | What it tests | Example |
| --- | --- | --- |
| `direct` | Baseline: stated plainly | The capital of France is Lyon. |
| `confusing` | A logically equivalent form (negations, double negations, contrapositives) that reduces to the same fact. Can the model see one fact across different logical forms? | It is not true that France has a capital other than Lyon. |
| `distractor_heavy` | The same edit embedded in unrelated information; the queried part is a small piece of it. Does distraction affect editing? | France, which borders Spain, produces a quarter of the world's wine and hosts the Tour de France each July, has Lyon as its capital. |

The earlier `negated` and `double_negation` are now just instances of
`confusing`. `implicit` (the claim is only entailed, never stated) was dropped,
since it is not logically equivalent to the edit.

**Degraded coherence** is the gibberish stress test. Gibberish is not a topic
and not a knowledge form: topic says what the knowledge is about, knowledge
form says what structural type it is, and this says how the edit is
represented. The same knowledge form and the same edit operation can be
expressed normally or in increasingly strange ways.

Rather than one bucket called "gibberish", each family is tagged with **what is
being destroyed**, because that is what makes a controlled comparison possible:

- **Semantic coherence**: whether the proposition makes sense at all.
- **Semantic type compatibility**: whether the target is the kind of thing the
  relation expects. `CapitalOf(country, city)` given something that is not a
  city.
- **Lexical familiarity**: whether the words have any established meaning, and
  so any pre-existing representation in the model.
- **Syntactic well-formedness**: whether the sentence is grammatical.
- **Symbolic / character structure**: whether the target is a word at all
  rather than an arbitrary symbol string.

| Key | Destroys | Example |
| --- | --- | --- |
| `semantic_incoherence` | semantic coherence | The capital of France is happiness. |
| `type_violation` | semantic type | Einstein's birthplace is 17. |
| `novel_lexical` | lexical familiarity | France's capital is Zorblin. |
| `synthetic_system` | lexical familiarity | Every flerm is a droven. Every droven can narp. A mip is a flerm. |
| `syntactic_corruption` | syntactic form | France capital blue under Paris changes. |
| `pseudo_syntactic` | syntactic form + semantic coherence | France is capitally governed by Parisness. |
| `random_symbolic` | lexical familiarity + symbolic structure | France's capital is XQ7-19B. |
| `mixed_corruption` | lexical + symbolic + syntactic | Fr@nce's cap!tal is Z0rb_77. |

`synthetic_system` is worth calling out separately: a whole mini-world of
invented concepts ("Every flerm is a droven", "Every droven can narp", "A mip
is a flerm", then "Is a mip a droven?", "Can a mip narp?") lets rule editing
and propagation be tested almost independently of pretrained world knowledge.

#### The grounding ladder

The point of the axis. Hold subject, relation, edit type and method fixed,
and walk the target away from the model's semantic structure one rung at a
time, measuring reliability, propagation and locality at each. `France's
capital is ___`:

1. **Lyon**: real city, correct type. The ordinary counterfactual.
2. **a spoon**: real word, concrete, wrong type for the relation.
3. **happiness**: real word, abstract, no sensible reading at all.
4. **Zorblin**: invented word, plausibly no prior representation.
5. **XQ7-19B**: arbitrary symbol string, not a word.

> How far can a requested update move away from the model's existing semantic
> structure before editing behaves differently or becomes damaging?

If editing quality or locality falls off a cliff at a particular rung, that
says how much successful editing depends on the target concept already having
a meaningful representation inside the model. Comparing `France -> Lyon`
against `France -> Zorblin` is the minimal version of that test.

### Connectivity and dependency

Two related but distinct structural properties, and the reason for separating
them is that they come apart in both directions.

**Connectivity: how much related knowledge surrounds the target?**

- `low`: very little meaningful knowledge naturally surrounds the target.
- `medium`: the target participates in several different relations or contexts.
- `high`: the target sits inside a rich network of entities, relations,
  concepts, events and contexts.

**Dependency: how much other knowledge should actually change if the target
changes?**

- `low`: changing the item should affect almost nothing else.
- `medium`: a bounded set of other propositions should change.
- `high`: the edit should systematically affect many conclusions, instances,
  behaviors or downstream statements.

A famous celebrity fact can be very high connectivity, because a huge amount of
related knowledge surrounds that person, while their favorite color is very low
dependency, because almost nothing else should change. A mathematical rule is
high on both.

| Combination | Role |
| --- | --- |
| High connectivity, low dependency | Strongest locality test |
| High connectivity, high dependency | Strongest propagation / generalization test |
| Low connectivity, low dependency | Easy baseline |
| Medium, medium | Ordinary intermediate case |

We do not force every Low/Medium/High combination, since some may not exist
naturally.

> **Important.** These labels describe the semantic neighborhood *the benchmark
> constructs* around an item. They are not claims about the model's actual
> latent organization of knowledge, which we cannot observe. We do not assert an
> exact connection count or dependency depth, only a coarse band.

## Evaluation probes

Every item carries four kinds of probe:

| Role | Expectation | Measures |
| --- | --- | --- |
| `target` | must change | Reliability |
| `dependent` | should change | Propagation / generalization |
| `connected_independent` | must not change | Strict locality |
| `unrelated` | must not change | Baseline locality |

`connected_independent` is the point of the design. Checking that a completely
unrelated fact survived an edit is easy; checking that closely related but
non-downstream knowledge survived is what distinguishes a precise method from
one that simply did not do much. `unrelated` is kept as the easy baseline so
results stay comparable with existing benchmarks.

So the core evaluation asks, in order:

1. Did the target change?
2. Did the edit propagate to the knowledge that should depend on it?
3. Did nearby but independent knowledge stay unchanged?
4. Did completely unrelated knowledge stay unchanged?

## Item shape

One record per knowledge item, carrying its coordinates and its probes:

```json
{
  "id": "math-rule-0001",
  "coordinate": {
    "topic": "mathematics",
    "edit_type": "replace",
    "knowledge_form": "hierarchy",
    "temporality": null,
    "edit_representation": "direct",
    "connectivity": "high",
    "dependency": "high"
  },
  "epistemic_status": "analytic",
  "target": {
    "statement": "...",
    "original": "...",
    "prompt": "...",
    "expected_after_edit": "..."
  },
  "probes": {
    "dependent": [{ "prompt": "...", "expected_after_edit": "..." }],
    "connected_independent": [{ "prompt": "...", "expected": "..." }],
    "unrelated": [{ "prompt": "...", "expected": "..." }]
  },
  "matched_group": "math-rule-0001-representation-variants",
  "notes": ""
}
```

`matched_group` ties variants that are meant to be compared directly: the same
knowledge item walked up the grounding ladder, the same item under several
`edit_representation` values, or two items matched on everything but
`connectivity`.

## Open points

- **Analytic vs synthetic.** "Paris is the capital of France" is synthetic;
  "a bachelor is unmarried" is analytic. Recorded per item as
  `epistemic_status`, but how to formalize the split is still open. It is here
  because definitions and rules plausibly behave differently under editing from
  arbitrary facts.
- **Who / what / which is not an axis.** These are alternative surface queries
  over the same underlying knowledge, so they belong as generalization probes,
  not as a knowledge form. "Einstein developed general relativity" generates
  "Who developed general relativity?", "What did Einstein develop?" and "Which
  theory did Einstein develop?" all from one item. "Why" is the exception: it
  asks for an explanation, which no form in the current scheme covers (next
  point).
- **Outside description logic.** The previous form list had `causal` and
  `evaluative`, which DL does not express (no causation, no stance). They are
  dropped for now. Events came back as a fact temporality rather than a form.

## Layout note

The `finance/`, `health/`, `education/` and `physics/` directories here are
left over from the earlier `<domain>/<edit nature>/<knowledge type>/` scaffold,
which the axis scheme above replaces. They are all empty. Records should live
flat (one file per item, or one file per batch) with the coordinate carried in
each record, since a tree cannot express six independent axes. The old
directories can be removed once you are sure nothing scripts against them.
