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
factual, on it being a definition or a causal claim or a sentiment, on how
densely connected it is, on whether it was inserted or deleted or replaced, on
how the update was phrased?

## Not a hierarchy

Every item is described by **coordinates on several independent axes**, not by
a position in one tree. Each question above varies along a different axis, so a
single hierarchy would force an arbitrary precedence between them and make
matched examples impossible to express.

```
Domain x Knowledge Form x Edit Nature x Edit Representation x Connectivity x Dependency
```

Matched examples are the point: same domain and similar knowledge form but
different connectivity, or one knowledge item expressed several different ways.
That is what lets a failure be attributed to a factor, instead of comparing two
examples that differ in every respect at once.

The machine-readable version of everything below lives in
`dashboard/frontend/src/lib/sidsDatasetTaxonomy.js`, and the dashboard's
Datasets page renders it (the "?" beside the dataset name). Keep the two in
sync.

## Axes

### Domain

`finance`, `economics`, `biology`, `physics`, `chemistry`, `mathematics`,
`grammar_language`, `philosophy`, `people`, `geography`, `history`,
`technology`.

Mainly a diversity control, so that a finding about rule-based knowledge is not
secretly a finding about mathematics.

### Knowledge form

The substantive axis. Existing benchmarks concentrate almost entirely on the
first entry.

| Key | What it is | Example |
| --- | --- | --- |
| `entity_relation` | Triple-shaped claim linking two entities through a relation | France > capital > Paris |
| `property` | Attribute of a single entity | Gold is conductive. |
| `definition` | What a term means | A bachelor is an unmarried adult man. |
| `rule_law` | General principle with open-ended instances | Force equals mass times acceleration. |
| `causal` | Why something happens, not just that it does | Raising interest rates tends to reduce borrowing. |
| `temporal_event` | Occurrence with participants, time, location, cause, outcome | The Wall Street crash began in October 1929. |
| `evaluative` | Stance toward an entity or topic rather than a proposition about it | Disposition toward a country, technology or public figure |

Definitions matter because redefining a term should change every classification
judgment that applies it. Rules matter because one edit can license an
unbounded number of changed outputs. Events matter because we can
counterfactually change one component (time, participant, outcome) and check
whether answers depending on that component follow. Evaluative items let us ask
whether an attitude can be edited, whether the change generalizes across
contexts, and whether factual knowledge survives it intact.

### Edit nature

`insert`, `delete`, `replace`. Independent of knowledge form: in principle any
form can be inserted, deleted or replaced, and whether that actually holds is
itself a finding.

Everything under `replace` is counterfactual by construction. The original is
something we are confident every LLM has seen and holds true, swapped for a
false-but-plausible alternative.

### Edit representation

How the update is communicated, holding the intended edit operation fixed. Two
groups.

**Coherent phrasing** preserves the intended meaning and varies only how much
interpretation it takes to recover it. This separates "the method captured the
meaning" from "the method pattern-matched the surface form".

| Key | Example |
| --- | --- |
| `direct` | Tom is interested in tennis. |
| `negated` | Tom is not indifferent to tennis. |
| `double_negation` | Tom is not uninterested in tennis. |
| `implicit` | Tom spends every weekend at the tennis club. |
| `confusing` | It would be wrong to say Tom has no interest in tennis. |
| `distractor_heavy` | Tom, who dislikes golf and rarely watches football, is interested in tennis. |

**Degraded coherence** is the gibberish stress test. Gibberish is not a domain
and not a knowledge form: domain says what the knowledge is about, knowledge
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

The point of the axis. Hold subject, relation, edit nature and method fixed,
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
    "domain": "mathematics",
    "knowledge_form": "rule_law",
    "edit_nature": "replace",
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
  draws on causal or mechanistic knowledge, which is its own knowledge form.

## Layout note

The `finance/`, `health/`, `education/` and `physics/` directories here are
left over from the earlier `<domain>/<edit nature>/<knowledge type>/` scaffold,
which the axis scheme above replaces. They are all empty. Records should live
flat (one file per item, or one file per batch) with the coordinate carried in
each record, since a tree cannot express six independent axes. The old
directories can be removed once you are sure nothing scripts against them.
