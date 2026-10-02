// Sid's own benchmark: the categorization scheme, ahead of any actual records.
//
// This is deliberately NOT a single hierarchy. Every item is described by
// coordinates on several independent axes, because the questions we want to
// answer ("does edit success depend on the knowledge being rule-like rather
// than factual? on how densely connected it is? on how the update was
// phrased?") each vary along a different one. A folder tree would force an
// arbitrary precedence between them and make matched pairs impossible to
// express. See datasets/SidsDataset/README.md for the same scheme in prose.

// First layer. Mainly a diversity control: we vary topic so that a finding
// about, say, rules is not secretly a finding about mathematics.
export const TOPICS = [
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

// Second layer. Independent of knowledge form: in principle any form can be
// inserted, replaced or deleted, and whether that actually holds is itself a
// finding.
export const EDIT_TYPES = [
  { key: 'insert', label: 'Insert', description: 'Add knowledge the model does not hold.' },
  {
    key: 'replace',
    label: 'Replace',
    description: 'Substitute held knowledge with a false-but-plausible alternative. Counterfactual by construction: the original is something we are confident every LLM has seen and holds true.',
  },
  { key: 'delete', label: 'Delete', description: 'Remove knowledge the model does hold.' },
]

// Third layer, and the substantive one. Categorized the way description logic
// carves up a knowledge base rather than as knowledge-graph triples: published
// benchmarks test almost nothing but the first form here (a plain link), and
// the rest is what a triple cannot express. Three tiers: fact vs rule, then
// the kind of fact or rule, then the form itself.
//
// Facts are claims about particular individuals (the DL ABox). Rules are
// claims about descriptions or relations in general (the TBox and RBox), so a
// single rule edit should move every individual it covers.
export const KNOWLEDGE_TIERS = [
  {
    key: 'fact',
    label: 'Facts',
    description: 'Claims about particular individuals.',
    groups: [
      {
        key: 'link',
        label: 'Links',
        notation: 'a R b',
        description: 'One individual related to another.',
        forms: [
          {
            key: 'plain_link',
            label: 'Plain link',
            notation: 'R(a, b)',
            description: 'Two individuals joined by a relation. The triple nearly every published benchmark already tests.',
            examples: ['Paris is the capital of France.'],
          },
        ],
      },
      {
        key: 'description',
        label: 'Descriptions of one thing',
        notation: 'a fits C',
        description: 'One individual said to fit a description, which can be built up from other descriptions.',
        forms: [
          {
            key: 'membership',
            label: 'Plain membership',
            notation: 'C(a)',
            description: 'The individual belongs to a named class.',
            examples: ['Paris is a city.'],
          },
          {
            key: 'negation',
            label: 'Negation',
            notation: '¬C(a)',
            description: 'The individual does not fit the description. Asserted absence, not merely an unknown.',
            examples: ['Marie does not speak German.'],
          },
          {
            key: 'disjunction',
            label: 'Disjunction ("or")',
            notation: '(C ⊔ D)(a)',
            description: 'The individual fits at least one of several descriptions without saying which.',
            examples: ['Alex is a doctor or a nurse.'],
          },
          {
            key: 'existential',
            label: 'Existential ("some")',
            notation: '∃R.C(a)',
            description: 'The individual is related to some member of a class, without naming which one.',
            examples: ['Marie speaks some Romance language.'],
          },
          {
            key: 'universal',
            label: 'Universal ("all")',
            notation: '∀R.C(a)',
            description: 'Everything the individual is related to through a relation fits a description.',
            examples: ['Everyone in this class passed.'],
          },
          {
            key: 'counting',
            label: 'Counting',
            notation: '(= n R.C)(a)',
            description: 'The individual is related to a stated number of things (exactly, at least or at most).',
            examples: ['Marie speaks exactly three languages.'],
          },
        ],
      },
    ],
  },
  {
    key: 'rule',
    label: 'Rules',
    description: 'Claims about descriptions or relations in general, with open-ended instances. One edit should change every individual it covers.',
    groups: [
      {
        key: 'description_rule',
        label: 'Rules about descriptions',
        notation: 'every C is D',
        description: 'How descriptions relate to each other.',
        forms: [
          {
            key: 'hierarchy',
            label: 'Hierarchy',
            notation: 'C ⊑ D',
            description: 'Everything fitting one description fits another. A definition is a hierarchy in both directions (C ≡ D).',
            examples: ['Every capital is a city.'],
          },
          {
            key: 'constraint',
            label: 'Constraint',
            notation: 'C ⊑ (= 1 R.D), C ⊓ D ⊑ ⊥',
            description: 'Limits on what can hold together: required counts, or descriptions that can never overlap.',
            examples: ['Every country has exactly one capital.', 'Nothing is both a city and a country.'],
          },
        ],
      },
      {
        key: 'relation_rule',
        label: 'Rules about relations',
        notation: 'R behaves like this',
        description: 'Properties of a relation itself, independent of any class.',
        forms: [
          {
            key: 'relation_rule',
            label: 'Relation rule',
            notation: 'Trans(R), R ≡ S⁻',
            description: 'Transitivity, inverses, symmetry, one relation implying another.',
            examples: ['"Located in" is transitive.', '"Capital of" flips to "has capital".'],
          },
        ],
      },
    ],
  },
]

// The extra layer facts carry: how the fact sits in time. It cuts across the
// fact forms rather than nesting under one, since a plain link can be a state
// ("Paris is the capital of France") or an event ("Curie discovered radium")
// and a membership can be timeless ("7 is prime") or a state. Rules don't
// carry it. Records store it as `temporality`, null for rules.
export const FACT_TEMPORALITY = [
  {
    key: 'timeless',
    label: 'Timeless',
    description: 'True independent of time: mathematics, and facts that hold by what the terms mean. Nothing should ever make it stop being true.',
    examples: ['7 is a prime number.', 'The square root of 81 is 9.'],
  },
  {
    key: 'state',
    label: 'State',
    description: 'True over a period that can end: capitals, who holds an office, where someone lives. An edit here is a plausible real-world change.',
    examples: ['Paris is the capital of France.', 'Marie lives in Lyon.'],
  },
  {
    key: 'event',
    label: 'Event',
    description: 'Happened at a point in time and stays happened: an assassination, a discovery, a founding. Editing one should move the answers that depend on when, who or what.',
    examples: ['Marie Curie discovered radium.', 'Lincoln was assassinated in 1865.'],
  },
]

// Flat list of the forms, each carrying its tier and group, for anything that
// just needs to look a form up. Records store only `knowledge_form`; the tier
// and group follow from it.
export const KNOWLEDGE_FORMS = KNOWLEDGE_TIERS.flatMap((tier) =>
  tier.groups.flatMap((group) => group.forms.map((form) => ({ ...form, tier: tier.key, group: group.key }))),
)

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
  {
    key: 'direct',
    group: 'coherent',
    label: 'Direct',
    description: 'Stated plainly. The baseline the other two are compared against.',
    example: 'The capital of France is Lyon.',
  },
  {
    key: 'confusing',
    group: 'coherent',
    label: 'Confusing',
    description: 'A logically equivalent form (negations, double negations, contrapositives) that reduces to exactly the same fact. Tests whether the model recognizes one fact across different logical forms.',
    example: 'It is not true that France has a capital other than Lyon.',
  },
  {
    key: 'distractor_heavy',
    group: 'coherent',
    label: 'Distractor-heavy',
    description: 'The same edit embedded in unrelated information, so the part that gets queried is a small piece of what was written. Tests whether distraction affects editing.',
    example: 'France, which borders Spain, produces a quarter of the world\'s wine and hosts the Tour de France each July, has Lyon as its capital.',
  },

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
  { key: 'coherent', label: 'Phrasing', note: 'Same fact, logically equivalent or buried in distraction.' },
  { key: 'degraded', label: 'Degraded coherence', note: 'One property deliberately destroyed. Each is tagged with which.' },
]

// The controlled sequence: hold subject, relation, edit type and method
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
  note: 'Who / what / which are alternative surface queries over the same underlying knowledge, so they are generalization probes rather than a knowledge form. "Why" is the exception: it asks for an explanation, and causal knowledge has no form in the current scheme (see open points).',
  example: {
    item: 'Einstein developed general relativity.',
    queries: ['Who developed general relativity?', 'What did Einstein develop?', 'Which theory did Einstein develop?'],
  },
}

// Render order for the coordinate summary and the info panel.
export const AXES = [
  { key: 'topic', label: 'Topic', values: TOPICS },
  { key: 'edit_type', label: 'Edit type', values: EDIT_TYPES },
  { key: 'knowledge_form', label: 'Knowledge form', values: KNOWLEDGE_FORMS },
  { key: 'temporality', label: 'Temporality (facts only)', values: FACT_TEMPORALITY },
  { key: 'edit_representation', label: 'Edit representation', values: EDIT_REPRESENTATIONS },
  { key: 'connectivity', label: 'Connectivity', values: CONNECTIVITY.levels },
  { key: 'dependency', label: 'Dependency', values: DEPENDENCY.levels },
]

export function axisValue(axisKey, valueKey) {
  return AXES.find((a) => a.key === axisKey)?.values.find((v) => v.key === valueKey)
}

// A compact human-readable coordinate, e.g.
// "mathematics · replace · rule/hierarchy · direct · C:high · D:high", or for
// a fact "history · replace · fact/event/plain_link · ...".
export function coordinateSummary(coordinate) {
  const form = KNOWLEDGE_FORMS.find((f) => f.key === coordinate.knowledge_form)
  return [
    coordinate.topic,
    coordinate.edit_type,
    form
      ? [form.tier, form.tier === 'fact' ? coordinate.temporality : null, form.key].filter(Boolean).join('/')
      : coordinate.knowledge_form,
    coordinate.edit_representation,
    `C:${coordinate.connectivity}`,
    `D:${coordinate.dependency}`,
  ].join(' · ')
}
