// Sid's own benchmark: the categorization scheme, ahead of any actual records.
//
// This is deliberately NOT a single hierarchy. Every item is described by
// coordinates on several independent axes, because the questions we want to
// answer ("does edit success depend on the knowledge being rule-like rather
// than factual? on how densely connected it is? on how the update was
// phrased?") each vary along a different one. A folder tree would force an
// arbitrary precedence between them and make matched pairs impossible to
// express. See datasets/SidsDataset/README.md for the same scheme in prose.

// Mainly a diversity control. We vary domain so that a finding about, say,
// rule-based knowledge is not secretly a finding about mathematics.
export const DOMAINS = [
  { key: 'finance', label: 'Finance' },
  { key: 'economics', label: 'Economics' },
  { key: 'biology', label: 'Biology' },
  { key: 'physics', label: 'Physics' },
  { key: 'chemistry', label: 'Chemistry' },
  { key: 'mathematics', label: 'Mathematics' },
  { key: 'grammar_language', label: 'Grammar / language' },
  { key: 'philosophy', label: 'Philosophy' },
  { key: 'people', label: 'Celebrities / people' },
  { key: 'geography', label: 'Countries / geography' },
  { key: 'history', label: 'History' },
  { key: 'technology', label: 'Technology' },
]

// The substantive axis. Existing benchmarks concentrate almost entirely on
// the first entry here, which is the gap this dataset exists to fill.
export const KNOWLEDGE_FORMS = [
  {
    key: 'entity_relation',
    label: 'Entity-relation fact',
    description: 'A triple-shaped claim linking two entities through a relation. What nearly every published benchmark already tests.',
    examples: ['France > capital > Paris', 'Marie Curie > discovered > radium'],
  },
  {
    key: 'property',
    label: 'Property',
    description: 'An attribute of a single entity rather than a link between two.',
    examples: ['Gold is conductive.', 'Saturn is a gas giant.'],
  },
  {
    key: 'definition',
    label: 'Definition',
    description: 'What a term means. Interesting because redefining a term should change every classification judgment that applies it, not just recall of the definition itself.',
    examples: ['A bachelor is an unmarried adult man.'],
  },
  {
    key: 'rule_law',
    label: 'Rule / law',
    description: 'A general principle with open-ended instances: mathematical rules, grammar rules, physical laws. The highest-leverage form, since one edit can license an unbounded number of changed outputs.',
    examples: ['Adjectives precede the noun in English.', 'Force equals mass times acceleration.'],
  },
  {
    key: 'causal',
    label: 'Causal / mechanistic',
    description: 'Why something happens, not just that it does. The form that "why" questions actually draw on.',
    examples: ['Raising interest rates tends to reduce borrowing.', 'Raising temperature at fixed volume raises gas pressure.'],
  },
  {
    key: 'temporal_event',
    label: 'Temporal / event',
    description: 'An occurrence with internal structure: participants, time, location, cause, outcome, and links to other events. Editing one component lets us test whether answers depending on that component follow.',
    examples: ['The Wall Street crash began in October 1929.'],
  },
  {
    key: 'evaluative',
    label: 'Evaluative / sentiment',
    description: 'The stance the model takes toward an entity or topic rather than a proposition about it. Tests whether an attitude can be edited, whether it generalizes across contexts, and whether factual knowledge survives intact.',
    examples: ['Positive disposition toward a given country, technology or public figure.'],
  },
]

// Independent of knowledge form: in principle any form can be inserted,
// deleted or replaced, and whether that actually holds is itself a finding.
export const EDIT_NATURES = [
  { key: 'insert', label: 'Insert', description: 'Add knowledge the model does not hold.' },
  { key: 'delete', label: 'Delete', description: 'Remove knowledge the model does hold.' },
  {
    key: 'replace',
    label: 'Replace',
    description: 'Substitute held knowledge with a false-but-plausible alternative. Counterfactual by construction: the original is something we are confident every LLM has seen and holds true.',
  },
]

// What a degraded representation actually destroys. Naming these separately
// is the point: "gibberish" as one bucket would conflate five different
// failure modes, and it is the individual property that makes a controlled
// comparison possible.
export const COHERENCE_PROPERTIES = [
  { key: 'semantic_coherence', label: 'Semantic coherence', description: 'Whether the proposition makes sense at all.' },
  { key: 'semantic_type', label: 'Semantic type compatibility', description: 'Whether the target is the kind of thing the relation expects. CapitalOf(country, city) given something that is not a city.' },
  { key: 'lexical_familiarity', label: 'Lexical familiarity', description: 'Whether the words involved have any established meaning, and so any pre-existing representation in the model.' },
  { key: 'syntactic_form', label: 'Syntactic well-formedness', description: 'Whether the sentence is grammatical and correctly ordered.' },
  { key: 'symbolic_structure', label: 'Symbolic / character structure', description: 'Whether the target is a word at all, rather than an arbitrary symbol string.' },
]

// How the update is communicated, holding the intended edit operation fixed.
// Two groups. The `coherent` ones preserve the intended meaning and vary only
// how much interpretation it takes to recover it, separating "the method
// captured the meaning" from "the method pattern-matched the surface form".
// The `degraded` ones deliberately destroy one of COHERENCE_PROPERTIES above,
// which is the stress test: how far can a requested update move away from the
// model's existing semantic structure before editing behaves differently or
// becomes damaging?
export const EDIT_REPRESENTATIONS = [
  { key: 'direct', group: 'coherent', label: 'Direct', description: 'Stated plainly.', example: 'Tom is interested in tennis.' },
  { key: 'negated', group: 'coherent', label: 'Negated', description: 'Carries one negation the reader has to resolve.', example: 'Tom is not indifferent to tennis.' },
  { key: 'double_negation', group: 'coherent', label: 'Double negation', description: 'Two negations that cancel, requiring real interpretation rather than surface reading.', example: 'Tom is not uninterested in tennis.' },
  { key: 'implicit', group: 'coherent', label: 'Implicit / compositional', description: 'The target claim follows from what is stated but is never stated itself.', example: 'Tom spends every weekend at the tennis club.' },
  { key: 'confusing', group: 'coherent', label: 'Confusing', description: 'Deliberately convoluted phrasing of the same content.', example: 'It would be wrong to say Tom has no interest in tennis.' },
  { key: 'distractor_heavy', group: 'coherent', label: 'Distractor-heavy', description: 'The target claim buried among irrelevant but topically adjacent material.', example: 'Tom, who dislikes golf and rarely watches football, is interested in tennis.' },

  {
    key: 'semantic_incoherence',
    group: 'degraded',
    label: 'Semantically incoherent',
    degrades: ['semantic_coherence'],
    description: 'Perfectly grammatical, ordinary words, but the proposition barely means anything. Tests whether a method blindly stores a syntactically valid claim regardless of its sense.',
    example: 'The capital of France is happiness.',
  },
  {
    key: 'type_violation',
    group: 'degraded',
    label: 'Semantic type violation',
    degrades: ['semantic_type'],
    description: 'Structure is understandable, but the target is the wrong type for the relation. More controlled than general absurdity, since exactly one expectation is violated.',
    example: "Einstein's birthplace is 17.",
  },
  {
    key: 'novel_lexical',
    group: 'degraded',
    label: 'Novel lexical item',
    degrades: ['lexical_familiarity'],
    description: 'An invented word with no established meaning, so the target may have no pre-existing representation to attach to. Compare France to Lyon against France to Zorblin.',
    example: "France's capital is Zorblin.",
  },
  {
    key: 'synthetic_system',
    group: 'degraded',
    label: 'Synthetic knowledge system',
    degrades: ['lexical_familiarity'],
    description: 'A whole mini-world of invented concepts, letting rule editing and propagation be tested almost independently of pretrained world knowledge.',
    example: 'Every flerm is a droven. Every droven can narp. A mip is a flerm. Is a mip a droven? Can a mip narp?',
  },
  {
    key: 'syntactic_corruption',
    group: 'degraded',
    label: 'Syntactic corruption',
    degrades: ['syntactic_form'],
    description: 'Real words, broken grammar or ordering. Corruption can be varied by degree to find where intent stops being recoverable.',
    example: 'France capital blue under Paris changes.',
  },
  {
    key: 'pseudo_syntactic',
    group: 'degraded',
    label: 'Pseudo-syntactic',
    degrades: ['syntactic_form', 'semantic_coherence'],
    description: 'Looks approximately grammatical but is malformed and semantically empty. Sits between grammatical nonsense and outright word salad.',
    example: 'France is capitally governed by Parisness.',
  },
  {
    key: 'random_symbolic',
    group: 'degraded',
    label: 'Random / symbolic target',
    degrades: ['lexical_familiarity', 'symbolic_structure'],
    description: 'The target is an arbitrary sequence rather than a word. Tests whether the editor can store an essentially arbitrary symbolic association.',
    example: "France's capital is XQ7-19B.",
  },
  {
    key: 'mixed_corruption',
    group: 'degraded',
    label: 'Mixed corruption',
    degrades: ['lexical_familiarity', 'symbolic_structure', 'syntactic_form'],
    description: 'Letters, numbers, punctuation, misspellings and symbols combined. The extreme robustness condition.',
    example: "Fr@nce's cap!tal is Z0rb_77.",
  },
]

export const REPRESENTATION_GROUPS = [
  { key: 'coherent', label: 'Coherent phrasing', note: 'Meaning preserved, interpretation difficulty varies.' },
  { key: 'degraded', label: 'Degraded coherence', note: 'One property deliberately destroyed. Each is tagged with which.' },
]

// The controlled sequence: hold subject, relation, edit nature and method
// fixed, walk the target away from the model's semantic structure one rung at
// a time, and measure reliability, propagation and locality at each. This is
// where the axis earns its keep, since the rungs differ in exactly one thing.
export const GROUNDING_LADDER = {
  frame: "France's capital is ___",
  question:
    "How far can a requested update move away from the model's existing semantic structure before editing behaves differently or becomes damaging? If quality or locality falls off a cliff at a particular rung, that says how much editing depends on the target already having a meaningful representation.",
  rungs: [
    { value: 'Lyon', representation: 'direct', description: 'Real city, correct type. The ordinary counterfactual.' },
    { value: 'a spoon', representation: 'type_violation', description: 'Real word, concrete, wrong type for the relation.' },
    { value: 'happiness', representation: 'semantic_incoherence', description: 'Real word, abstract, no sensible reading at all.' },
    { value: 'Zorblin', representation: 'novel_lexical', description: 'Invented word, plausibly no prior representation.' },
    { value: 'XQ7-19B', representation: 'random_symbolic', description: 'Arbitrary symbol string, not a word.' },
  ],
}

// Rubric caveat that applies to both structural axes below. Worth keeping
// visible wherever these appear, because it is the most misreadable part of
// the scheme.
export const STRUCTURE_CAVEAT =
  "These labels describe the semantic neighborhood the benchmark constructs around an item. They are not claims about the model's actual latent organization of knowledge, which we cannot observe. We do not assert an exact connection count or dependency depth, only a coarse band."

export const CONNECTIVITY = {
  key: 'connectivity',
  label: 'Connectivity',
  question: 'How much related knowledge surrounds the target?',
  levels: [
    { key: 'low', label: 'Low', description: 'Very little meaningful knowledge naturally surrounds the target.' },
    { key: 'medium', label: 'Medium', description: 'The target participates in several different relations or contexts.' },
    { key: 'high', label: 'High', description: 'The target sits inside a rich network of entities, relations, concepts, events and contexts.' },
  ],
}

export const DEPENDENCY = {
  key: 'dependency',
  label: 'Dependency',
  question: 'How much other knowledge should actually change if the target changes?',
  levels: [
    { key: 'low', label: 'Low', description: 'Changing the item should affect almost nothing else.' },
    { key: 'medium', label: 'Medium', description: 'A bounded set of other propositions should change.' },
    { key: 'high', label: 'High', description: 'The edit should systematically affect many conclusions, instances, behaviors or downstream statements.' },
  ],
}

// Why the two are worth separating: they come apart in both directions, and
// the cells where they do are the most diagnostic items in the benchmark.
// Combinations not listed here are still valid, they just have no headline
// role; some may not exist naturally at all, and we do not force them.
export const STRUCTURE_EXAMPLES = [
  {
    connectivity: 'high',
    dependency: 'low',
    label: 'Strongest locality test',
    detail: "A celebrity's favorite color. Enormous surrounding knowledge, almost none of it downstream of this fact, so any collateral change is a failure.",
  },
  {
    connectivity: 'high',
    dependency: 'high',
    label: 'Strongest propagation test',
    detail: 'A mathematical or grammatical rule. Richly connected and genuinely load-bearing, so a correct edit has to move a great deal with it.',
  },
  {
    connectivity: 'low',
    dependency: 'low',
    label: 'Easy baseline',
    detail: 'An isolated fact about a minor entity. If a method fails here it fails everywhere.',
  },
  {
    connectivity: 'medium',
    dependency: 'medium',
    label: 'Intermediate',
    detail: 'The bulk of ordinary cases, between the two extremes.',
  },
]

// The probe set every item carries. Roles 2 and 3 are the point of the
// design: "connected but independent" is a far harder locality test than an
// unrelated fact, and separating them tells us whether a method is precise
// or merely inert.
export const PROBE_ROLES = [
  { key: 'target', label: 'Target', expectation: 'must change', description: 'The knowledge actually being edited. Answers reliability.' },
  { key: 'dependent', label: 'Dependent', expectation: 'should change', description: 'Statements and questions that ought to follow from the edit if it propagated properly. Answers generalization.' },
  { key: 'connected_independent', label: 'Connected but independent', expectation: 'must not change', description: 'Closely related to the edited item yet not downstream of it. The strict locality test.' },
  { key: 'unrelated', label: 'Unrelated', expectation: 'must not change', description: 'Ordinary far-field facts. The easy locality baseline, kept so results stay comparable with existing benchmarks.' },
]

// Recorded per item but still being pinned down: definitions and rules
// plausibly behave differently from arbitrary facts, and this is a first
// attempt at naming why. Provisional on purpose.
export const EPISTEMIC_STATUS = [
  { key: 'synthetic', label: 'Synthetic', description: 'True as a matter of fact about the world. "Paris is the capital of France."' },
  { key: 'analytic', label: 'Analytic', description: 'True in virtue of meaning. "A bachelor is unmarried."' },
]

// Not an axis. Who/what/which turned out to be different queries over one
// underlying item rather than different kinds of knowledge, so they became
// generalization probes instead of a category. Recorded here because the
// distinction is easy to re-litigate otherwise.
export const QUERY_VARIANTS = {
  note: 'Who / what / which are alternative surface queries over the same underlying knowledge, so they are generalization probes rather than a knowledge form. "Why" is the exception: it draws on causal or mechanistic knowledge, which is its own form above.',
  example: {
    item: 'Einstein developed general relativity.',
    queries: ['Who developed general relativity?', 'What did Einstein develop?', 'Which theory did Einstein develop?'],
  },
}

// Render order for the coordinate summary and the info panel.
export const AXES = [
  { key: 'domain', label: 'Domain', values: DOMAINS },
  { key: 'knowledge_form', label: 'Knowledge form', values: KNOWLEDGE_FORMS },
  { key: 'edit_nature', label: 'Edit nature', values: EDIT_NATURES },
  { key: 'edit_representation', label: 'Edit representation', values: EDIT_REPRESENTATIONS },
  { key: 'connectivity', label: 'Connectivity', values: CONNECTIVITY.levels },
  { key: 'dependency', label: 'Dependency', values: DEPENDENCY.levels },
]

export function axisValue(axisKey, valueKey) {
  return AXES.find((a) => a.key === axisKey)?.values.find((v) => v.key === valueKey)
}

// A compact human-readable coordinate, e.g.
// "mathematics · rule_law · replace · direct · C:high · D:high".
export function coordinateSummary(coordinate) {
  return [
    coordinate.domain,
    coordinate.knowledge_form,
    coordinate.edit_nature,
    coordinate.edit_representation,
    `C:${coordinate.connectivity}`,
    `D:${coordinate.dependency}`,
  ].join(' · ')
}
