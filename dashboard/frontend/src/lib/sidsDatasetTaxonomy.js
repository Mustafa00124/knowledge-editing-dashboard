// Sid's own benchmark: the categorization scheme, ahead of any actual records.
//
// Three levels: edit operation, then knowledge form (topic > box > relation
// semantics > derivability, where the last two only exist under some boxes),
// then a fixed set of 12 queries per edit. See datasets/SidsDataset/README.md
// for the same scheme in prose and datasets/SidsDataset/RELATIONS.md for the
// relations and their properties. Keep all three in sync.

// Level 1.
export const EDIT_OPERATIONS = [
  { key: 'insert', label: 'Insert', description: 'Add knowledge the model does not hold. Afterwards: the new answer.' },
  {
    key: 'replace',
    label: 'Replace',
    description: 'Swap held knowledge for a false-but-plausible alternative. Counterfactual by construction: the original is something every LLM has seen and holds true. Afterwards: the new answer, never the old one.',
  },
  {
    key: 'delete',
    label: 'Delete',
    description: 'Remove knowledge the model does hold. Afterwards: not the old answer. The model should say it does not know, or negate the fact.',
  },
]

// Level 2, first layer. A diversity control, and the way records are
// organized for browsing.
export const TOPICS = [
  { key: 'geography', label: 'Geography' },
  { key: 'people', label: 'People' },
  { key: 'history', label: 'History' },
  { key: 'finance', label: 'Finance' },
  { key: 'biology', label: 'Biology' },
  { key: 'physics', label: 'Physics' },
  { key: 'mathematics', label: 'Mathematics' },
  { key: 'grammar', label: 'Grammar' },
  { key: 'literature_arts', label: 'Literature and arts' },
]

// Level 2, second layer: how description logic divides a knowledge base.
// `semantics` and `derivability` say which of the next layers exist under each
// box; a record stores null for a layer its box doesn't have.
export const BOXES = [
  {
    key: 'abox',
    label: 'ABox',
    notation: 'R(a, b), C(a)',
    description: 'Facts about particular individuals.',
    examples: ['Paris is the capital of France.'],
    semantics: true,
    derivability: true,
  },
  {
    key: 'tbox',
    label: 'TBox',
    notation: 'C ⊑ D, C ⊑ ∃R.D',
    description: 'Rules about classes: every C is (or does) D. One edit should move every individual it covers.',
    examples: ['Every capital is a city.', 'Smoking causes lung cancer.'],
    semantics: true,
    derivability: true,
  },
  {
    key: 'rbox',
    label: 'RBox',
    notation: 'Trans(R), Sym(R), R ≡ S⁻, R ∘ S ⊑ T',
    description: 'Properties of relations themselves. Editing one changes what can be derived from every fact using that relation.',
    examples: ['"Located in" is transitive.', '"Sibling of" is symmetric.'],
    semantics: false,
    derivability: false,
  },
]

// Level 2, third layer (ABox and TBox only). Causation is outside standard
// description logic; it is modelled as relations with their own properties
// in RELATIONS.md, and is not treated as transitive in general.
export const RELATION_SEMANTICS = [
  {
    key: 'causal',
    label: 'Causal',
    description: 'The relation says one thing brings about another.',
    examples: ['The 2008 crisis caused Lehman Brothers to collapse.', 'Smoking causes lung cancer.'],
  },
  {
    key: 'associative',
    label: 'Associative',
    description: 'Any other relation: membership, location, ownership, role, part of.',
    examples: ['Paris is the capital of France.', 'Every capital is a city.'],
  },
]

// Level 2, fourth layer (ABox and TBox only). Editing a derived fact leaves
// its premises pointing at the old answer, so the model may re-derive it and
// slide back. Insert is always axiomatic: a fact the model can already derive
// is not new.
export const DERIVABILITY = [
  {
    key: 'axiomatic',
    label: 'Axiomatic',
    description: 'Stated directly; nothing else the model knows entails it.',
    examples: ['Paris is the capital of France.', 'Every square is a rectangle.'],
  },
  {
    key: 'derived',
    label: 'Derived',
    description: 'Follows from other facts or rules the model holds (its premises), which are checked before editing and expected to stay unchanged. Replace and delete only.',
    examples: ['The Eiffel Tower is in France.', 'Every square is a polygon.'],
  },
]

// Shown wherever derivability is explained, since it is the easiest label to
// misread as a fact about the model.
export const DERIVABILITY_CAVEAT =
  'Derivability is model specific: whether a fact is stored or derived depends on the model, and we cannot observe which. Items are labelled by what is likely to be axiomatic or derived, using our own intuition and criteria, which will be detailed later.'

// Every leaf of level 2 below topic: 4 ABox + 4 TBox + 1 RBox = 9 per topic
// (insert only has the 5 axiomatic ones).
export const KNOWLEDGE_FORMS = BOXES.flatMap((box) =>
  (box.semantics ? RELATION_SEMANTICS : [null]).flatMap((sem) =>
    (box.derivability ? DERIVABILITY : [null]).map((deriv) => ({
      box: box.key,
      relation_semantics: sem?.key ?? null,
      derivability: deriv?.key ?? null,
    })),
  ),
)

// Level 3: the fixed 12 queries every edit carries, and the metric each
// feeds. Fixing the counts gives every item the same weight in every metric.
export const QUERY_TYPES = [
  { key: 'direct', label: 'Direct', count: 1, metric: 'reliability', description: "The edited fact asked as a question, in the edit's own wording." },
  { key: 'paraphrase', label: 'Paraphrase', count: 1, metric: 'reliability', description: 'The same question in different words.' },
  {
    key: 'cross_lingual',
    label: 'Cross-lingual',
    count: 2,
    metric: 'cross-lingual',
    languages: ['zh', 'es'],
    description: 'The direct question asked in Chinese and Spanish, expecting the answer in that language. The edit itself is made in English.',
  },
  { key: 'derived', label: 'Derived', count: 4, metric: 'generalization', description: "A question whose answer follows from the edit through a property of the relation." },
  {
    key: 'unrelated_near',
    label: 'Unrelated (near)',
    count: 2,
    metric: 'locality',
    description: 'Shares the subject, relation or topic, but does not follow from the edit. What makes locality informative.',
  },
  { key: 'unrelated_far', label: 'Unrelated (far)', count: 2, metric: 'locality', description: 'Nothing in common with the edit. The easy baseline.' },
]

export const METRICS = [
  { key: 'reliability', label: 'Reliability', over: 'direct + paraphrase (2)', reported: 'one number' },
  { key: 'cross_lingual', label: 'Cross-lingual', over: 'Chinese + Spanish (2)', reported: 'one number, plus per language' },
  { key: 'generalization', label: 'Generalization', over: 'derived (4)', reported: 'one number, plus per derivation type' },
  { key: 'locality', label: 'Locality', over: 'unrelated near + far (4)', reported: 'one number, plus near and far' },
  { key: 'fluency', label: 'Fluency', over: 'the 10 English generations', reported: 'one number (n-gram scores are not comparable across languages)' },
]

// Where derived queries come from. Each maps a relation property (a tag in
// RELATIONS.md) to the question it licenses. Reflexivity is left out on
// purpose: "a R a" doesn't depend on the edit.
export const DERIVATIONS = [
  { key: 'symmetry', label: 'Symmetry', notation: 'Sym(R)', example: 'Billy is a sibling of Manny. Is Manny a sibling of Billy?' },
  { key: 'inverse', label: 'Inverse', notation: 'R ≡ S⁻', example: "Ann is Billy's parent. Who is Ann's child?" },
  { key: 'asymmetry', label: 'Asymmetry', notation: 'Asym(R)', example: "Ann is Billy's parent. Is Billy Ann's parent? (no)" },
  { key: 'transitivity', label: 'Transitivity', notation: 'Trans(R)', bridge: true, example: 'Lyon is in France (+ France is in Europe). Is Lyon in Europe?' },
  { key: 'chain', label: 'Role chain', notation: 'R ∘ S ⊑ T', bridge: true, example: 'She was born in Lyon (+ Lyon is in France). Which country was she born in?' },
  { key: 'subproperty', label: 'Subproperty', notation: 'R ⊑ S', example: 'Lyon is the capital of France. Which country is Lyon located in?' },
  { key: 'functional', label: 'Functional', notation: '≤ 1 R', example: 'Replace only. The capital of France is Lyon. Is Paris still the capital? (no)' },
  { key: 'composition', label: 'Composition', notation: 'multi-hop', bridge: true, example: 'The capital of France is Lyon (+ the Rhône flows through Lyon). Which river flows through the capital of France?' },
  { key: 'inheritance', label: 'Inheritance', notation: 'C ⊑ D', bridge: true, example: 'TBox: every capital is a port (+ Paris is a capital). Is Paris a port?' },
  { key: 'instantiation', label: 'Instantiation', notation: 'RBox axiom', bridge: true, example: 'RBox: "borders" is asymmetric (+ France borders Spain). Does Spain border France? (no)' },
]

// How a query is scored from the generated answer.
export const QUERY_BEHAVIORS = [
  { key: 'answer', label: 'Answer', description: 'Correct if the expected answer (or an alias) appears and no forbidden answer does.' },
  {
    key: 'abstain_or_negate',
    label: 'Abstain or negate',
    description: 'Delete. Correct if the old answer does not appear and the model says it does not know or that the fact does not hold. Which of the two is recorded. For relations with many values this is an open-world test, where abstaining is the honest answer.',
  },
  { key: 'unchanged', label: 'Unchanged', description: "Unrelated queries. Correct if the post-edit answer matches the model's own pre-edit answer." },
]

// A tag every record carries, not a layer of the taxonomy: how familiar the
// knowledge involved is likely to be, rated separately for the fact as a
// whole and for its subject and object.
// Records store the key; `score` (1 to 5, ordinal) is what analysis uses,
// and the label is what the page shows.
export const FAMILIARITY = [
  { key: 'very_low', label: 'Very low', score: 1, example: 'The mayor of a small town; a small village.' },
  { key: 'low', label: 'Low', score: 2, example: 'The capital of a small province; a regional politician.' },
  { key: 'medium', label: 'Medium', score: 3, example: 'The author of a moderately well-known novel; a mid-sized city.' },
  { key: 'high', label: 'High', score: 4, example: 'The capital of Australia; Lyon.' },
  { key: 'very_high', label: 'Very high', score: 5, example: 'The capital of France; France.' },
]

export const FAMILIARITY_SCORE = Object.fromEntries(FAMILIARITY.map((f) => [f.key, f.score]))

export const FAMILIARITY_TIERS = [
  { key: 'fact', label: 'Fact', description: 'The original fact as a whole. Replace and delete; null for insert, which has no original fact.' },
  { key: 'subject', label: 'Subject', description: "The edit's subject. Always set." },
  {
    key: 'object',
    label: 'Object',
    description: "The edit's object: the new value for insert and replace, the removed value for delete. Null when the knowledge isn't binary (RBox edits, about one relation).",
  },
]

export const FAMILIARITY_CAVEAT =
  "Familiarity is a proxy: we can't see any model's training data, so the tag is our estimate of how often the knowledge appears in text a model is likely to have seen. The criteria for assigning it will be detailed later."

// Dimensions of the earlier axis scheme this version leaves out. Listed so
// they aren't lost; they may return as separate subsets.
export const PARKED = [
  'Description forms (negation, disjunction, existential, universal, counting) as their own knowledge forms.',
  'Edit representation: confusing or distractor-heavy phrasings, and the degraded-coherence grounding ladder.',
  'Connectivity and dependency bands.',
  'Analytic vs synthetic epistemic status.',
  'Puzzle topic: invented mini-worlds where derived queries are pure logic, insert only.',
  'Temporality (event vs timeless): no clear reason it should change whether an edit succeeds.',
]

// A compact human-readable coordinate, e.g.
// "replace · geography · abox/associative/derived".
export function coordinateSummary(coordinate) {
  return [
    coordinate.edit_operation,
    coordinate.topic,
    [coordinate.box, coordinate.relation_semantics, coordinate.derivability].filter(Boolean).join('/'),
  ].join(' · ')
}
