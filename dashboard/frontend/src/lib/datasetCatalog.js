import importedBenchmarks from './importedBenchmarks.json'

// Hardcoded rather than derived from the filesystem: each benchmark's
// files have genuinely different shapes (checked directly against the
// actual files - see dashboard/README.md), so there's a real per-subset
// "how to page this / how to render it" decision that isn't discoverable
// generically. Adding a new benchmark subset means adding one entry here.
//
// shape: source adapter used by lib/normalizeDatasetRecord.js
// hasQueries: whether the Edit/Edit+Queries toggle applies at all
// editKey/queryKey: for the 'flat_qa' shape only - trivia's file has two
//   unrelated-length top-level lists (success/locality), not one shape,
//   so edits and shared locality queries are paged independently.

const UNIEDIT_DOMAINS = [
  "agronomy",
  "art",
  "astronomy",
  "biology",
  "chemistry",
  "civil engineering",
  "computer science",
  "data science",
  "economics",
  "environmental science",
  "geoscience",
  "history",
  "jurisprudence",
  "literature",
  "material science",
  "mathematics",
  "mechanical engineering",
  "medicine",
  "pedagogy",
  "philosophy",
  "physics",
  "political science",
  "psychology",
  "sociology",
  "sports science"
]

// UniEdit's 50 files (25 domains x 2 splits) total ~774MB - counting
// records means fully parsing each one, which takes ~80s combined (timed
// directly against the backend's own preview() counting logic, the same
// code path that would otherwise redo this on every page load). Baked in
// here once rather than computed live, the same way the imported
// "standard"-shape benchmarks' recordCount already is.
const UNIEDIT_RECORD_COUNTS = {
  "test/agronomy": 4156, "test/art": 4368, "test/astronomy": 4300, "test/biology": 4250,
  "test/chemistry": 4242, "test/civil engineering": 4133, "test/computer science": 4048,
  "test/data science": 4058, "test/economics": 4140, "test/environmental science": 4189,
  "test/geoscience": 4107, "test/history": 4077, "test/jurisprudence": 4192,
  "test/literature": 4186, "test/material science": 4140, "test/mathematics": 3561,
  "test/mechanical engineering": 4222, "test/medicine": 4166, "test/pedagogy": 4204,
  "test/philosophy": 4172, "test/physics": 4174, "test/political science": 4128,
  "test/psychology": 4201, "test/sociology": 4135, "test/sports science": 4174,
  "train/agronomy": 8310, "train/art": 8736, "train/astronomy": 8599, "train/biology": 8500,
  "train/chemistry": 8483, "train/civil engineering": 8264, "train/computer science": 8095,
  "train/data science": 8115, "train/economics": 8279, "train/environmental science": 8377,
  "train/geoscience": 8213, "train/history": 8153, "train/jurisprudence": 8382,
  "train/literature": 8372, "train/material science": 8278, "train/mathematics": 7122,
  "train/mechanical engineering": 8442, "train/medicine": 8331, "train/pedagogy": 8406,
  "train/philosophy": 8343, "train/physics": 8346, "train/political science": 8255,
  "train/psychology": 8401, "train/sociology": 8269, "train/sports science": 8348,
}

export const BENCHMARKS = {
  // Sid's own dataset - empty for now. Unlike the published benchmarks it is
  // categorized by edit operation, knowledge form and query type rather than
  // by subset (see
  // sidsDatasetTaxonomy.js and datasets/SidsDataset/README.md), so until
  // records exist the Datasets page renders SidsDatasetBrowser instead of the
  // generic subset UI. Registering subsets here is what switches that over.
  SidsDataset: [],
  ...importedBenchmarks,
  ConflictEdit: ['GPT-J', 'GPT2-XL'].flatMap((model) => [
    ['easy', 'Easy'], ['hard', 'Hard'], ['coverage_edit', 'Coverage'],
    ['composite_edit', 'Composite'], ['reverse_edit', 'Reverse'],
  ].map(([key, label]) => ({
    key: `${model}/${key}`,
    label: `${model} · ${label}`,
    file: `data/${model}/${key}.json`,
    shape: 'conflict_edit', category: 'Replacement', hasQueries: true,
    recordCount: model === 'GPT2-XL' && key === 'composite_edit' ? 2000 : 2500,
    description: 'Source-model-specific ConflictEdit split. Related edits in a record belong together.',
  }))),
  ReCoE: ['superlative', 'comparative', 'counting', 'sorting', 'aggregation', 'subtraction'].map((key, i) => ({
    key, label: key[0].toUpperCase() + key.slice(1),
    file: `data/${key}/counterfactual_datapoints_verified_atomic.json`,
    shape: 'recoe', category: 'Replacement', hasQueries: true,
    recordCount: [1172, 1153, 643, 1034, 508, 500][i],
    description: 'Counterfactual reasoning case; supporting facts may require multiple edits.',
  })),
  AlteredRiddles: [{
    key: 'auxiliary', label: 'Public auxiliary set', file: 'benchmark.jsonl',
    shape: 'altered_riddles', category: 'Reasoning probe', hasQueries: true,
    recordCount: 700,
    description: 'Public auxiliary set. The 300-item fixed leaderboard set is private.',
  }],
  UniEdit: ['test', 'train'].flatMap((split) =>
    UNIEDIT_DOMAINS.map((domain) => ({
      key: `${split}/${domain}`,
      label: `${domain} (${split})`,
      file: `${split}/${domain}.json`,
      shape: 'uniedit',
      hasQueries: true,
      recordCount: UNIEDIT_RECORD_COUNTS[`${split}/${domain}`],
    })),
  ),
  KnowEdit: [
    { key: 'wiki_recent', label: 'wiki_recent', file: 'benchmark/wiki_recent/recent_test.json', shape: 'edit_probes', hasQueries: true, recordCount: 1266 },
    { key: 'wiki_counterfact', label: 'wiki_counterfact', file: 'benchmark/wiki_counterfact/test_cf.json', shape: 'edit_probes', hasQueries: true, recordCount: 839 },
    { key: 'zsre', label: 'ZsRE', file: 'benchmark/ZsRE/ZsRE-test-all.json', shape: 'edit_probes', hasQueries: true, recordCount: 1301 },
    { key: 'wikibio', label: 'WikiBio', file: 'benchmark/WikiBio/wikibio-test-all.json', shape: 'text_completion', hasQueries: true, recordCount: 306 },
    { key: 'convsent', label: 'Convsent', file: 'benchmark/Convsent/blender_test.json', shape: 'sentiment', hasQueries: false, recordCount: 800 },
    {
      key: 'trivia',
      label: 'trivia',
      file: 'benchmark/trivia/trivia_qa_test.json',
      shape: 'flat_qa',
      hasQueries: true,
      editKey: 'success',
      queryKey: 'locality',
      recordCount: 80,
    },
  ],
  // DUnE ships each edit set with a companion locality set in its own file.
  // Those aren't a kind of edit, they're the "don't disturb this" half of
  // the same benchmark, so they hang off their parent subset as
  // localityFile rather than sitting alongside it as separate subsets (the
  // two can't be merged per-record: the pools share no key and differ in
  // length, e.g. arithmetic is 1065 edits against 564 locality checks).
  DUnE: [
    { key: 'arithmetic', label: 'arithmetic', file: 'dune/arithmetic.json', shape: 'edit_mcq', hasQueries: true, recordCount: 1065,
      localityFile: 'dune/arithmetic_locality.json', localityCount: 564 },
    { key: 'debiasing_i', label: 'debiasing_I', file: 'dune/debiasing_I.json', shape: 'edit_mcq', hasQueries: true, recordCount: 145,
      localityFile: 'dune/debiasing_I_locality.json', localityCount: 900 },
    { key: 'debiasing_ii', label: 'debiasing_II', file: 'dune/debiasing_II.json', shape: 'edit_mcq', hasQueries: true, recordCount: 200,
      localityFile: 'dune/debiasing_II_locality.json', localityCount: 1352 },
    { key: 'new_info', label: 'new_info', file: 'dune/new_info.json', shape: 'edit_mcq', hasQueries: true, recordCount: 200,
      localityFile: 'dune/new_info_locality.json', localityCount: 207 },
    { key: 'scientific', label: 'scientific', file: 'dune/scientific.json', shape: 'edit_mcq', hasQueries: true, recordCount: 1508,
      localityFile: 'dune/scientific_locality.json', localityCount: 600 },
  ],
  // Preprocessed (build_editing_set.py) into one file per Knowledge
  // Spectrum "Question Type" - not the 352 raw weekly *_qa.jsonl files,
  // which would mean 352 near-identical browsing tabs.
  RealTimeQA: [
    { key: 'all', label: 'All', file: 'realtimeqa_editing.json', shape: 'realtimeqa', hasQueries: false, recordCount: 9383, description: 'Every usable record across all question types combined.' },
    { key: 'who', label: 'Who', file: 'by_question_type/who.json', shape: 'realtimeqa', hasQueries: false, recordCount: 477 },
    { key: 'what', label: 'What', file: 'by_question_type/what.json', shape: 'realtimeqa', hasQueries: false, recordCount: 2296 },
    { key: 'when', label: 'When', file: 'by_question_type/when.json', shape: 'realtimeqa', hasQueries: false, recordCount: 132 },
    { key: 'where', label: 'Where', file: 'by_question_type/where.json', shape: 'realtimeqa', hasQueries: false, recordCount: 252 },
    { key: 'which', label: 'Which', file: 'by_question_type/which.json', shape: 'realtimeqa', hasQueries: false, recordCount: 4774 },
    { key: 'why', label: 'Why', file: 'by_question_type/why.json', shape: 'realtimeqa', hasQueries: false, recordCount: 123 },
    { key: 'how', label: 'How', file: 'by_question_type/how.json', shape: 'realtimeqa', hasQueries: false, recordCount: 964 },
    { key: 'others', label: 'Others', file: 'by_question_type/others.json', shape: 'realtimeqa', hasQueries: false, recordCount: 365, description: 'No wh-word at all - mostly fill-in-the-blank style questions ("...titled:", "...except:").' },
  ],
}

export const PAGE_SIZES = [5, 10, 20, 50]

// Display label where it differs from the object key (keys stay identifier-safe
// since they're also the URL path segment / datasets/ directory name).
export const BENCHMARK_LABELS = {
  SidsDataset: "Sid's Dataset",
  AlteredRiddles: 'Altered Riddles',
}

// Two-tier grouping shown above the benchmark picker: Sid's own
// in-progress dataset gets its own row, separate from the published
// benchmarks everyone else's data comes from.
export const BENCHMARK_GROUPS = [
  { label: 'Own Dataset', benchmarks: ['SidsDataset'] },
  {
    label: 'Published Datasets',
    benchmarks: Object.keys(BENCHMARKS).filter((name) => name !== 'SidsDataset'),
  },
]
