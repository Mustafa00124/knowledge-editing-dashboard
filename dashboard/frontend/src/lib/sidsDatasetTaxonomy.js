// Sid's own benchmark: the categorization scheme, ahead of any actual records.
//
// Levels: topic, then belief revision operation (AGM: expansion, revision,
// contraction; stored as insert, replace, delete), then knowledge form (the
// DL box), then a fixed set of 12 queries per edit (9 for RBox). Relation semantics and
// relation properties are tags (the Relation group below), not levels. See datasets/SidsDataset/README.md
// for the same scheme in prose and datasets/SidsDataset/RELATIONS.md for the
// relations and their properties. Keep all three in sync.

// Level 2: the belief revision operation. Keys stay insert/replace/delete
// (record fields, ids and folders use them); labels use the AGM names.
// Revision first: it's the main operation and the browser opens on it.
export const EDIT_OPERATIONS = [
  {
    key: 'replace',
    label: 'Revision',
    description: 'Replace: swap held knowledge for a false-but-plausible alternative. Counterfactual by construction: the original is something every LLM has seen and holds true. Afterwards: the new answer, never the old one.',
  },
  { key: 'insert', label: 'Expansion', description: 'Insert: add knowledge the model does not hold. Afterwards: the new answer.' },
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

// Level 3: the queries an ABox revision record carries, in record order (README,
// Query type): from the edit outwards, everything that should change before
// what must not. Counts are fixed per record type (README, Queries per record
// type): main ABox revision has 4 derived (3 determinate + 1 indeterminate),
// every other non-RBox record 3 determinate; related is ABox revision and
// contraction only.
export const QUERY_TYPES = [
  { key: 'direct', label: 'Direct', count: 1, metric: 'rewrite', description: "The edited fact asked as a question, in the edit's own wording." },
  { key: 'paraphrase', label: 'Paraphrase', count: 1, metric: 'generalizability', description: 'The same question in different words.' },
  {
    key: 'cross_lingual',
    label: 'Cross-lingual',
    count: 2,
    metric: 'cross-lingual',
    languages: ['zh', 'es'],
    description: 'The direct question asked in Chinese and Spanish, expecting the answer in that language. The edit itself is made in English.',
  },
  {
    key: 'propositional',
    label: 'Propositional',
    count: 3,
    metric: 'logical consistency',
    description: 'The edited fact inside a yes/no truth-functional question: negation ("Is it false that Sydney is the capital of Australia?"), conjunction (with a true side fact) and disjunction (with a false side fact), so the answer flips with the edit. Checked by truth table; reported on its own.',
  },
  { key: 'related', label: 'Related', count: 2, metric: 'generalizability', description: 'Two stored answers (the model has most likely seen them stated) that must change with the edit, each one hop from it through a different role axiom: inverse, symmetry, functional or subproperty.' },
  { key: 'derived', label: 'Derived', count: 3, metric: 'generalizability', description: 'A question whose answer the model has most likely never seen stated but can work out from the edit and one bridge fact, in exactly 2 hops. Main ABox revision adds one indeterminate derived query as context.' },
  {
    key: 'unrelated_near',
    label: 'Unrelated (near)',
    count: 1,
    metric: 'specificity',
    description: 'Shares the subject, relation or topic, but does not follow from the edit. What makes specificity informative.',
  },
  { key: 'unrelated_far', label: 'Unrelated (far)', count: 1, metric: 'specificity', description: 'Nothing in common with the edit. The easy baseline.' },
]

// RBox edits change a property of a relation, so they carry 10 queries: the
// property itself, two instances on real entities (and the first in zh and
// es), three propositional questions, and one near and one far unrelated
// query. No paraphrase, no related queries.
export const RBOX_QUERY_TYPES = [
  { key: 'direct', label: 'Direct', count: 1, metric: 'rewrite', description: "The property itself: \"Is the relation 'lends to' transitive?\"" },
  { key: 'cross_lingual', label: 'Cross-lingual', count: 2, metric: 'cross-lingual', languages: ['zh', 'es'], description: 'The first instance question in Chinese and Spanish.' },
  { key: 'propositional', label: 'Propositional', count: 3, metric: 'logical consistency', description: 'The edited property inside a yes/no question: negation, conjunction and disjunction with a side fact, so the answer flips with the edit.' },
  {
    key: 'derived',
    label: 'Instances',
    count: 2,
    metric: 'generalizability',
    description: 'The property applied to real entities, premises in the prompt: "JPMorgan lends to Goldman Sachs, and Goldman Sachs lends to Citadel. Does it follow that JPMorgan lends to Citadel?"',
  },
  { key: 'unrelated_near', label: 'Unrelated (near)', count: 1, metric: 'specificity', description: 'The same property asked of another relation in the topic.' },
  { key: 'unrelated_far', label: 'Unrelated (far)', count: 1, metric: 'specificity', description: 'A different property of an unrelated relation.' },
]

export const queryTypesFor = (box) => (box === 'rbox' ? RBOX_QUERY_TYPES : QUERY_TYPES)

export const METRICS = [
  { key: 'rewrite', label: 'Rewrite (reliability, efficacy)', over: 'direct (1)', reported: 'one number' },
  { key: 'generalization', label: 'Generalizability (portability)', over: 'paraphrase, related, determinate derived', reported: 'one number, plus each part, per relation property, per task, per logic and per hop count' },
  { key: 'indeterminate', label: 'Indeterminate change', over: 'the indeterminate derived query (main ABox revision)', reported: 'reported apart: which world the answer picks, or unchanged' },
  { key: 'cross_lingual', label: 'Cross-lingual', over: 'Chinese + Spanish (2)', reported: 'one number, plus per language' },
  { key: 'logical_consistency', label: 'Logical consistency', over: 'propositional (3)', reported: 'one number on its own, plus per connective (negation, conjunction, disjunction)' },
  { key: 'locality', label: 'Specificity (locality)', over: 'unrelated near + far (2)', reported: 'one number, plus near and far' },
  { key: 'fluency', label: 'Answer diversity (ROME’s fluency)', over: 'the English generations', reported: 'one number (n-gram scores are not comparable across languages)' },
]

// What a related or derived answer rests on: a relation property (a tag in
// RELATIONS.md), or none when a task carries the edit (README, Relation
// properties and task types). Reflexivity and asymmetry are not used.
// Derivation names follow description logic (SROIQ / OWL 2) where it has a
// clean equivalent (inverse, symmetric, functional and transitive roles, role
// inclusion, role chain, instance checking); inheritance and premise keep our
// names, with the DL form as their notation. Task names (composition, binding,
// application) have no DL equivalent and stay as they are.
export const DERIVATIONS = [
  { key: 'inverse', label: 'Inverse role', notation: 'R ≡ S⁻', example: "Ann is Billy's parent. Who is Ann's child?" },
  { key: 'symmetry', label: 'Symmetric role', notation: 'Sym(R)', example: 'Billy is a sibling of Manny. Is Manny a sibling of Billy?' },
  { key: 'functional', label: 'Functional role', notation: 'Func(R), i.e. ⊤ ⊑ ≤1 R.⊤', example: 'The capital of Australia is Sydney. Is Canberra the capital? (no)' },
  { key: 'subproperty', label: 'Role inclusion', notation: 'R ⊑ S', example: 'Lyon is the capital of Germany. Which country is Lyon located in?' },
  { key: 'transitivity', label: 'Transitive role', notation: 'Trans(R)', bridge: true, example: 'The nephron is part of the respiratory system (+ the glomerulus is part of the nephron). Is the glomerulus part of the respiratory system?' },
  { key: 'chain', label: 'Role chain', notation: 'R ∘ S ⊑ T', bridge: true, example: 'She was born in Lyon (+ Lyon is in France). Which country was she born in?' },
  { key: 'inheritance', label: 'Inheritance', notation: 'C ⊑ D, C(a) ⊨ D(a)', bridge: true, example: 'TBox: every spider has six legs (+ a new spider species). ABox: Pluto is a planet (+ every planet orbits a star).' },
  { key: 'none', label: 'No role axiom', notation: 'task', form: 'task', example: 'A composition or binding task carries the edit to the answer.' },
  { key: 'cardinality', label: 'Non-functional role', notation: 'no Func(R)', form: 'contraction', example: 'Contraction: removing one official language of Switzerland leaves German an official language.' },
  { key: 'instantiation', label: 'Instance checking', notation: 'RBox ⊨ R(a,b)?', bridge: true, example: 'RBox: "borders" is symmetric (+ France borders Spain). Does it follow that Spain borders France?' },
  { key: 'premise', label: 'Premise', notation: 'derived edit', form: 'premise', example: 'Edit: the Space Needle is in the Central Time Zone (from: it is in Seattle; Seattle observes Pacific Time). Which time zone does Seattle observe?' },
]

// What a related or derived question makes the model do (README, task types).
export const TASKS = [
  { key: 'answer', label: 'Answer', example: 'Which country was she born in?' },
  { key: 'composition', label: 'Composition', example: 'The capital of France is Lyon (+ the Rhône flows through Lyon). Which river flows through the capital of France?' },
  { key: 'binding', label: 'Binding', example: 'The IMF is headquartered in Paris (+ "IMF" abbreviates the International Monetary Fund). Where is the International Monetary Fund headquartered?' },
  { key: 'application', label: 'Application', example: 'The Space Needle is in the Central Time Zone. When it is noon in Chicago, what time is it at the Space Needle? (noon)' },
]

// The weakest logic a derived query's inference needs, and any theory on
// top (README, Derived queries, Logic): settings to slice results by.
export const LOGIC = [
  { key: 'propositional', label: 'Propositional', description: 'Only whole statements combined with not, and, or. The propositional query type is this logic by definition; derived queries no longer use it.', example: 'Edit: 91 is prime. Propositional query: is it true that 91 is prime or 91 is even?' },
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
  { key: 'locality', label: 'Specificity', description: "Unrelated queries, any operation. Correct if the answer matches the model's own pre-edit answer." },
]

// "w1" -> "World 1", for display; records keep the short ids.
export const worldLabel = (id) => (/^w(\d+)$/.test(id || '') ? `World ${id.slice(1)}` : id)

// A tag for ABox and TBox replace and delete (null for insert and RBox), and
// for every related and derived query's answer: stored or worked out. Only
// the two ends are used (README, Derivability). Editing a derived fact leaves its premises pointing at the
// old answer, so the model may re-derive it and slide back.
export const DERIVABILITY = [
  { key: 'very_unlikely', label: 'Stored', description: 'very unlikely to be derived: stated often', score: 1, example: 'Paris is the capital of France.' },
  { key: 'very_likely', label: 'Derived', description: 'very likely to be derived: worked out from premises', score: 5, example: "Elizabeth I's paternal grandfather was Henry VII (Henry VII was the father of Henry VIII, Henry VIII the father of Elizabeth I)." },
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
  'Derivability is model specific: whether a fact is axiomatic (stored) or derived (composed) depends on the model, and we cannot observe which. The tag is our estimate, backed by evidence behind the "?" on each record: how often the fact and its premises are stated in public pretraining text. Only two ratings are used: stored (very unlikely to be derived) and derived (very likely); a derived edit lists its premises, which are checked before editing. After the edit a consistent model revises one of them, so premises are asked as derived-belief queries, never as locality.'

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

// Lower-case display name of a derivation key, for question labels.
export const DERIVATION_NAME = Object.fromEntries(DERIVATIONS.map((d) => [d.key, d.label.toLowerCase()]))

// A relation's tag from RELATIONS.md as a DL role axiom on that role.
export function roleAxiom(role, tag) {
  const [kind, arg] = String(tag).split(':')
  switch (kind) {
    case 'transitive': return `Trans(${role})`
    case 'symmetric': return `Sym(${role})`
    case 'asymmetric': return `Asym(${role})`
    case 'functional': return `Func(${role})`
    case 'inverse': return `${role} ≡ ${arg}⁻`
    case 'subproperty': return `${role} ⊑ ${arg}`
    case 'chain': return `chain: ${arg}`
    case 'cardinality': return arg === 'many' ? `non-functional (${role})` : tag
    default: return tag
  }
}

// A role's tags (RELATIONS.md) as description-logic role types: the DL name
// shown on the record card, our original tag name, the notation and what it
// means. Order: how they are listed.
export const ROLE_TYPES = [
  { tag: 'transitive', name: 'transitive role', common: 'Transitive', notation: 'Trans(R)', meaning: 'a R b and b R c imply a R c' },
  { tag: 'symmetric', name: 'symmetric role', common: 'Symmetric', notation: 'Sym(R)', meaning: 'a R b implies b R a' },
  { tag: 'asymmetric', name: 'asymmetric role', common: 'Asymmetric', notation: 'Asym(R)', meaning: 'a R b implies not b R a' },
  { tag: 'functional', name: 'functional role', common: 'Functional (one value)', notation: 'Func(R)', meaning: 'at most one value per individual' },
  { tag: 'cardinality', name: 'non-functional role', common: 'Many-valued', notation: 'no Func(R)', meaning: 'several values per individual (many-valued)' },
  { tag: 'inverse', name: 'inverse role', common: 'Inverse', notation: 'R ≡ S⁻', meaning: 'a R b if and only if b S a' },
  { tag: 'subproperty', name: 'role inclusion', common: 'Subproperty', notation: 'R ⊑ S', meaning: 'a R b implies a S b' },
  { tag: 'chain', name: 'role chain', common: 'Chain (composition of roles)', notation: 'R ∘ S ⊑ T', meaning: 'a R b and b S c imply a T c' },
]
export const roleTypeOf = (tag) => ROLE_TYPES.find((t) => t.tag === String(tag).split(':')[0])
