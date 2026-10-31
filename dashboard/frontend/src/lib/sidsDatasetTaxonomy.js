// Sid's own benchmark: the categorization scheme, ahead of any actual records.
//
// Levels: topic, then belief revision operation (AGM: expansion, revision,
// contraction; stored as insert, replace, delete), then knowledge form (the
// DL box), then a fixed set of 10 queries per edit (7 for RBox). Relation semantics and
// relation properties are tags (the Relation group below), not levels. See datasets/SidsDataset/README.md
// for the same scheme in prose and datasets/SidsDataset/RELATIONS.md for the
// relations and their properties. Keep all three in sync.

// Level 2: the belief revision operation. Keys stay insert/replace/delete
// (record fields, ids and folders use them); labels use the AGM names.
export const EDIT_OPERATIONS = [
  { key: 'insert', label: 'Expansion', description: 'Insert: add knowledge the model does not hold. Afterwards: the new answer.' },
  {
    key: 'replace',
    label: 'Revision',
    description: 'Replace: swap held knowledge for a false-but-plausible alternative. Counterfactual by construction: the original is something every LLM has seen and holds true. Afterwards: the new answer, never the old one.',
  },
  {
    key: 'delete',
    label: 'Contraction',
    description: 'Delete: remove knowledge the model does hold. Afterwards: not the old answer. The model should say it does not know, or negate the fact.',
  },
]

// Level 1: topic. A diversity control, and the way records are organized
// for browsing.
export const TOPICS = [
  { key: 'geography', label: 'Geography' },
  { key: 'people', label: 'People' },
  { key: 'history', label: 'History' },
  { key: 'finance', label: 'Finance' },
  { key: 'biology', label: 'Biology' },
  { key: 'physics', label: 'Physics' },
  { key: 'literature_arts', label: 'Literature and arts' },
  { key: 'technology', label: 'Technology' },
  { key: 'mathematics', label: 'Mathematics' },
  { key: 'grammar', label: 'Grammar' },
]

// Level 3, the knowledge form: how description logic divides a knowledge base.
export const BOXES = [
  {
    key: 'abox',
    label: 'ABox',
    notation: 'R(a, b), C(a)',
    description: 'Facts about particular individuals.',
    examples: ['Paris is the capital of France.'],
  },
  {
    key: 'tbox',
    label: 'TBox',
    notation: 'C ⊑ D, C ⊑ ∃R.D',
    description: 'Rules about classes: every C is (or does) D. One edit should move every individual it covers.',
    examples: ['Every capital is a city.', 'Smoking causes lung cancer.'],
  },
  {
    key: 'rbox',
    label: 'RBox',
    notation: 'Trans(R), Sym(R), R ≡ S⁻, R ∘ S ⊑ T',
    description: 'Properties of relations themselves. Editing one changes what can be derived from every fact using that relation.',
    examples: ['"Located in" is transitive.', '"Sibling of" is symmetric.'],
  },
]

// Every leaf of level 2 below topic: one per box, 3 per topic.
export const KNOWLEDGE_FORMS = BOXES.map((box) => ({ box: box.key }))

// Target size: edits per taxonomy cell (edit operation x topic x box).
export const EDITS_PER_CELL_GOAL = 10

// Level 3: the fixed 10 queries every ABox and TBox edit carries (RBox: 7, below), in record order
// (locality before derived), and the metric each feeds. Fixing the counts gives every item the same weight in every metric.
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
  {
    key: 'unrelated_near',
    label: 'Unrelated (near)',
    count: 1,
    metric: 'locality',
    description: 'Shares the subject, relation or topic, but does not follow from the edit. What makes locality informative.',
  },
  { key: 'unrelated_far', label: 'Unrelated (far)', count: 1, metric: 'locality', description: 'Nothing in common with the edit. The easy baseline.' },
  { key: 'derived', label: 'Derived', count: 4, metric: 'generalization', description: 'A question whose answer follows from the edit: through a property of the relation, a further fact, or a task that uses it. On ABox records each is labelled determinate or indeterminate (below).' },
]

// RBox edits change a property of a relation, so they carry 7 queries: the
// property itself, two instances on real entities (and the first in zh and
// es), and one near and one far locality query. No paraphrase.
export const RBOX_QUERY_TYPES = [
  { key: 'direct', label: 'Direct', count: 1, metric: 'reliability', description: "The property itself: \"Is the relation 'lends to' transitive?\"" },
  { key: 'cross_lingual', label: 'Cross-lingual', count: 2, metric: 'cross-lingual', languages: ['zh', 'es'], description: 'The first instance question in Chinese and Spanish.' },
  { key: 'unrelated_near', label: 'Unrelated (near)', count: 1, metric: 'locality', description: 'The same property asked of another relation in the topic.' },
  { key: 'unrelated_far', label: 'Unrelated (far)', count: 1, metric: 'locality', description: 'A different property of an unrelated relation.' },
  {
    key: 'derived',
    label: 'Instances',
    count: 2,
    metric: 'generalization',
    description: 'The property applied to real entities, premises in the prompt: "JPMorgan lends to Goldman Sachs, and Goldman Sachs lends to Citadel. Does it follow that JPMorgan lends to Citadel?"',
  },
]

export const queryTypesFor = (box) => (box === 'rbox' ? RBOX_QUERY_TYPES : QUERY_TYPES)

export const METRICS = [
  { key: 'reliability', label: 'Reliability', over: 'direct + paraphrase (2)', reported: 'one number' },
  { key: 'cross_lingual', label: 'Cross-lingual', over: 'Chinese + Spanish (2)', reported: 'one number, plus per language' },
  { key: 'generalization', label: 'Generalization', over: 'derived (4)', reported: 'one number, plus per derivation type' },
  { key: 'locality', label: 'Locality', over: 'unrelated near + far (2)', reported: 'one number, plus near and far' },
  { key: 'fluency', label: 'Fluency', over: 'the 8 English generations', reported: 'one number (n-gram scores are not comparable across languages)' },
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
  { key: 'binding', label: 'Binding', notation: 'task type', form: 'task', example: 'IMF abbreviates International Monetary Fund. Where is the headquarters of the organization referred to by IMF?' },
  { key: 'application', label: 'Application', notation: 'task type', form: 'task', example: 'A courier must visit the NYSE trading-floor building. Which city should be the courier\'s destination?' },
  { key: 'scope', label: 'Scope', notation: 'task type', form: 'task', example: 'Given only the IMF headquarters city, is a particular country Z an IMF member? (cannot be determined)' },
  { key: 'instantiation', label: 'Instantiation', notation: 'RBox axiom', bridge: true, example: 'RBox: "borders" is asymmetric (+ France borders Spain). Does Spain border France? (no)' },
  { key: 'premise', label: 'Premise', notation: 'derived edit', form: 'premise', example: 'Edit: the Space Needle is in the Central Time Zone (from: it is in Seattle; Seattle observes Pacific Time). Which time zone does Seattle observe?' },
]

// The weakest logic a derived query's inference needs, and any theory on
// top (README, Derived queries, Logic): settings to slice results by.
export const LOGIC = [
  { key: 'propositional', label: 'Propositional', description: 'Only whole statements combined with not, and, or, if.', example: 'Edit: 91 is prime. Is it true that 91 is prime or 91 is even?' },
  { key: 'dl', label: 'Description logic', description: 'Classes, two-place relations and their properties, role chains, inheritance, number limits, names for one individual.', example: 'Is Canberra the capital of Australia?' },
  { key: 'fol', label: 'First-order', description: 'Beyond description logic: three-place relations, comparing values across individuals, rules whose variables form a cycle.', example: "Edit: singular names take 'are'. Is 'Sally are tall' correct?" },
]
export const THEORY = [
  { key: 'arithmetic', label: 'Arithmetic', description: 'Computing or comparing numbers, on first-order logic.', example: 'When it is noon in Chicago, what time is it at the Space Needle?' },
  { key: 'temporal', label: 'Temporal', description: 'Comparing dates or ordering events, on first-order logic.', example: "Did the first powered flight come after McKinley's death?" },
]

// Determinacy, per ABox and TBox derived query (README, Determinacy and
// belief-revision problems). A knowledge system has a base of stored facts and
// the closure derived from them; we can't see which an LLM stores, so one edit
// can have several valid outcomes. The label marks where.
export const DETERMINACY = [
  {
    key: 'determinate',
    label: 'Determinate',
    description: 'Every valid route gives one answer after the edit. A wrong answer is the editing method\'s failure.',
    example: 'Edit: the capital of Australia is Sydney. Is Canberra the capital of Australia? (no)',
  },
  {
    key: 'background_beliefs',
    label: 'Background beliefs',
    description: 'Several routes reached the answer before the edit; one goes through the edited fact, another around it. After the edit they split, depending on how the model stored its other beliefs.',
    example: 'In which city does the federal Parliament of Australia sit? Canberra if stored by name, Sydney if stored as "in the capital".',
  },
  {
    key: 'derived_beliefs',
    label: 'Derived beliefs',
    description: 'The edited fact is likely derived from premises. A consistent model revises one of them, and which one is open; a model that revises none is inconsistent.',
    example: 'Edit: the Space Needle is in the Central Time Zone. Which time zone does Seattle observe? Pacific if the Needle moves, Central if Washington State does.',
  },
]
export const INDETERMINATE = ['background_beliefs', 'derived_beliefs']

// How a query is labelled: the four scenarios.
export const DETERMINACY_SCENARIOS = [
  { key: 'A', label: 'A. One route', description: 'One way to the answer, so one answer after the edit.', example: 'determinate' },
  { key: 'B', label: 'B. Several routes, all through the edit', description: 'They move together.', example: 'determinate' },
  { key: 'C', label: 'C. Several routes, some around the edit', description: 'They split, depending on how facts were stored.', example: 'background_beliefs' },
  { key: 'D', label: 'D. One route through a premise of a derived edit', description: 'It depends on which premise gives way.', example: 'derived_beliefs' },
]

export const DETERMINACY_RULE =
  'List every route a reasonable model could have used to reach the answer before the edit, and, on a derived edit, every premise that could give way. Drop a route whose answer after the edit contradicts a fact the model holds firmly. If all remaining routes agree, the query is determinate; if they split because of storage, background beliefs; if because of which premise gives way, derived beliefs.'

// Evidence behind each "?" on a record: why a fact is rated stored or derived.
export const EVIDENCE_CLAIMS = [
  { key: 'stored', label: 'Stored', description: 'Stated explicitly and often in text every model likely trained on (Wikipedia, large public web corpora). More frequency, stronger evidence.' },
  { key: 'derived', label: 'Derived', description: 'Rarely or never stated directly, while each premise is stated often. Absence means absent after the searches listed.' },
]
export const SOURCE_KINDS = {
  'infini-gram': 'Corpus count',
  wikipedia: 'Wikipedia',
  web: 'Web page',
  search: 'Search tried',
}
export const INFINIGRAM_INDEXES = {
  'v4_dolma-v1_7_llama': 'Dolma (OLMo pretraining data)',
  v4_rpj_llama_s4: 'RedPajama',
  v4_piletrain_llama: 'the Pile',
  v4_c4train_llama: 'C4',
}

// How an LLM judge (Qwen3-4B-Instruct-2507, run locally) scores a free-form
// answer against the query's original_answer and new_answer.
export const QUERY_BEHAVIORS = [
  { key: 'replace', label: 'Replace', description: 'Correct if the answer gives the new answer and does not assert the original one. If both are mentioned, the final assertion counts.' },
  { key: 'insert', label: 'Insert', description: 'Correct if the answer gives the new answer.' },
  {
    key: 'delete',
    label: 'Delete',
    description: 'Correct if the answer does not assert the original answer and says it does not know or that the fact does not hold; which of the two is recorded. For relations with many values this is an open-world test, where abstaining is the honest answer.',
  },
  { key: 'locality', label: 'Locality', description: "Unrelated queries, any operation. Correct if the answer matches the model's own pre-edit answer." },
]

// "w1" -> "World 1", for display; records keep the short ids.
export const worldLabel = (id) => (/^w(\d+)$/.test(id || '') ? `World ${id.slice(1)}` : id)

// A tag for ABox and TBox replace and delete (null for insert and RBox): how
// likely a model is to derive the edited fact from other knowledge rather
// than store it, on a scale from axiomatic (stored) to derived (composed). Editing a derived fact leaves its premises pointing at the
// old answer, so the model may re-derive it and slide back.
export const DERIVABILITY = [
  { key: 'very_unlikely', label: 'Very unlikely', score: 1, example: 'Paris is the capital of France.' },
  { key: 'unlikely', label: 'Unlikely', score: 2, example: 'Lyon is in France.' },
  { key: 'medium', label: 'Medium', score: 3, example: 'The Eiffel Tower is in Europe.' },
  { key: 'likely', label: 'Likely', score: 4, example: 'The Eiffel Tower is in France (it is in Paris, and Paris is in France).' },
  { key: 'very_likely', label: 'Very likely', score: 5, example: 'Every square is a polygon (every square is a rectangle, every rectangle is a polygon).' },
]

// Insert records are fictional; `fictional` says which parts of the triple
// (subject, relation, object) were made up.
export const FICTIONAL = [
  { key: 'subject', label: 'Subject', description: 'A made-up subject in a real relation to a real object (a newly mapped island of the Thousand Islands).' },
  { key: 'object', label: 'Object', description: 'A made-up new value of a real subject (a newly found moon of Eris).' },
  { key: 'subject_object', label: 'Subject and object', description: 'Both ends made up, in a real relation (the plural of a made-up noun).' },
  { key: 'relation', label: 'Relation', description: 'Real things in a made-up relation (two real cities that are "tide-paired").' },
  { key: 'all', label: 'Everything', description: 'Made-up things in a made-up relation; everything the derived queries need is in the prompt.' },
]

export const DERIVABILITY_SCORE =Object.fromEntries(DERIVABILITY.map((d) => [d.key, d.score]))

// Shown wherever derivability is explained, since it is the easiest label to
// misread as a fact about the model.
export const DERIVABILITY_CAVEAT =
  'Derivability is model specific: whether a fact is axiomatic (stored) or derived (composed) depends on the model, and we cannot observe which. The tag is our estimate, backed by evidence behind the "?" on each record: how often the fact and its premises are stated in public pretraining text. Premises are listed (required at likely and above) and checked before editing. After the edit a consistent model revises one of them, so premises are asked as derived-belief queries, never as locality.'

// Tag group "Relation": three facets of the record's relation (for RBox, the
// relation whose property is edited). The name is the record's `relation`;
// the semantics is stored as `relation_semantics` and must match
// RELATIONS.md; the properties are not stored per record but looked up from
// RELATIONS.md (the backend sends its table with the records).
export const RELATION_FACETS = [
  { key: 'name', label: 'Name', description: "The record's relation, e.g. located_in. For RBox, the relation whose property is edited." },
  { key: 'semantics', label: 'Semantics', description: 'Causal or associative, from the Semantics column of RELATIONS.md. Stored as relation_semantics.' },
  { key: 'properties', label: 'Properties', description: "The relation's property tags in RELATIONS.md. Not stored in the record; looked up from the catalogue." },
]

// Facet "semantics". Causation is outside standard description logic; it is
// modelled as relations with their own properties in RELATIONS.md, and is not
// treated as transitive in general.
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

// Facet "properties": the tag vocabulary of RELATIONS.md (its Tags table),
// for explaining and filtering. Which relation has which tags is never copied
// here. `key` is the tag, or its prefix for tags with an argument
// (inverse:S matches inverse:contains). The `causal` tag is left out: it is
// the semantics facet.
export const RELATION_PROPERTIES = [
  { key: 'symmetric', label: 'Symmetric', notation: 'Sym(R)', description: 'a R b implies b R a.' },
  { key: 'asymmetric', label: 'Asymmetric', notation: 'Asym(R)', description: 'a R b implies not b R a.' },
  { key: 'inverse:', label: 'Inverse', notation: 'R ≡ S⁻', description: 'inverse:S. a R b if and only if b S a.' },
  { key: 'transitive', label: 'Transitive', notation: 'Trans(R)', description: 'a R b and b R c imply a R c.' },
  { key: 'chain:', label: 'Role chain', notation: 'R ∘ S ⊑ T', description: 'chain:S->T. a R b and b S c imply a T c.' },
  { key: 'subproperty:', label: 'Subproperty', notation: 'R ⊑ S', description: 'subproperty:S. a R b implies a S b.' },
  { key: 'functional', label: 'Functional', notation: '≤ 1 R', description: 'At most one value per subject.' },
  { key: 'cardinality:many', label: 'Many-valued', notation: 'cardinality:many', description: 'A subject can have many values; makes delete an open-world test.' },
]

// The property facet of one tag: 'inverse:contains' -> the Inverse entry.
export const relationPropertyOf = (tag) =>
  RELATION_PROPERTIES.find((p) => tag === p.key || (p.key.endsWith(':') && tag.startsWith(p.key)))

// A relation's property tags from the RELATIONS.md table the backend sends
// ({name: {tags, causal}}), without `causal` (that is the semantics facet).
export const relationProperties = (relations, name) => (relations?.[name]?.tags || []).filter((t) => t !== 'causal')

// Dimensions of the earlier axis scheme this version leaves out. Listed so
// they aren't lost; they may return as separate subsets.
export const PARKED = [
  'Description forms (negation, disjunction, existential, universal, counting) as their own knowledge forms.',
  'Edit representation: confusing or distractor-heavy phrasings, and the degraded-coherence grounding ladder.',
  'Connectivity and dependency bands.',
  'Analytic vs synthetic epistemic status.',
  'Puzzle topic: invented mini-worlds where derived queries are pure logic, insert only.',
]

// A compact human-readable coordinate, e.g. "replace · geography · abox".
export function coordinateSummary(coordinate) {
  return [coordinate.topic, coordinate.edit_operation, coordinate.box].join(' · ')
}
