// Cross-benchmark reference for the "?" beside the Published Datasets
// heading: how each benchmark phrases its query, and how long the answer
// it is scored against actually is.
//
// These are three independent axes, not one. Query form does not predict
// answer length (ZsRE asks a question and wants two words; RuleEdit uses a
// cloze and wants a seven-word formula), and MCQ collapses answer length to
// one token regardless of how long the underlying answer would be. See
// INDEPENDENCE below, which the modal renders as the reason the table has
// three columns instead of one.
//
// Every length here was measured directly off the files in datasets/, not
// taken from a paper - `sampledFrom` names the exact file each row's numbers
// came from, since several benchmarks ship one file per domain/model/split
// and we did not parse all of them (UniEdit alone is ~774MB). Re-measuring
// means re-reading that file's answer field and recounting whitespace tokens.

export const QUERY_FORMS = {
  cloze: {
    label: 'Cloze',
    detail: 'Prompt stops mid-sentence and the model continues it.',
    example: 'The place of death of Leo Arons is',
  },
  question: {
    label: 'Question',
    detail: 'A full interrogative sentence.',
    example: 'Which family does Epaspidoceras belong to?',
  },
  blank: {
    label: 'Cloze + blank',
    detail: 'Cloze with an explicit blank, filled from a fixed choice list.',
    example: 'a Siamese is a kind of ____',
  },
  yes_no: {
    label: 'Yes / no',
    detail: 'Binary judgment rather than a value to produce.',
    example: 'Whether Harper and Row belongs to category publisher?',
  },
  statement: {
    label: 'Statement',
    detail: 'The edit is a declarative sentence, not a prompt. Only the probes are queries.',
    example: 'January 10, 2022 - The first successful heart transplant from a pig to a human occurs.',
  },
  continuation: {
    label: 'Continuation',
    detail: 'A passage the model extends, with no question or blank at all.',
    example: 'This is a Wikipedia passage about john russell reynolds. Sir John Russell Reynolds...',
  },
}

// What the model has to actually emit. Independent of both other axes.
export const ANSWER_KINDS = {
  token: {
    label: 'Forced token',
    detail: 'One letter or one word from a closed set. Not open generation at all.',
  },
  span: {
    label: 'Short span',
    detail: 'An entity or value, typically one to three words. Exact match is meaningful here.',
  },
  phrase: {
    label: 'Phrase',
    detail: 'Five to twelve words: a definition, a formula, a descriptor. Token accuracy degrades differently from a span.',
  },
  sentence: {
    label: 'Full sentence',
    detail: 'Fourteen words and up. Generation quality, not lookup.',
  },
}

// The three counterexamples that justify keeping these axes apart. Each
// names the two rows a reader can check against in the table below.
export const INDEPENDENCE = [
  {
    claim: 'Query form does not predict answer length',
    detail: 'ZsRE is question-form with two-word answers, wiki_counterfact is cloze-form with two-word answers. Same answer, opposite query.',
  },
  {
    claim: 'Cloze does not imply a short answer',
    detail: 'WikiBio is a cloze-style continuation whose ground truth is an 18-word sentence.',
  },
  {
    claim: 'Question does not imply a long answer',
    detail: "DUnE's scientific and new_info probes are questions whose ground truth is a single letter.",
  },
]

// One entry per benchmark, in the order the Datasets page lists them.
// `rows` splits a benchmark whenever a single label would be wrong: RelEdit
// wants a nine-word definition for its edit and a yes/no for four of its
// probes, so one answer-length label for the dataset would misdescribe both.
export const DATASET_FORMATS = [
  {
    benchmark: 'MQuAKE',
    rows: [
      { label: 'Edit', queryForm: 'cloze', answerField: 'requested_rewrite[].target_new.str', median: 1, p90: 3, n: 6121, answerKind: 'span' },
      { label: 'Multi-hop probe', queryForm: 'question', answerField: 'new_answer', median: 1, p90: 2, n: 3000, answerKind: 'span' },
    ],
    sampledFrom: 'datasets/MQuAKE-CF-3k-v2.json',
    note: 'single_hops carries literal `question` and `cloze` keys side by side, so the same fact exists in both forms.',
  },
  {
    benchmark: 'RippleEdits',
    rows: [
      { label: 'Edit', queryForm: 'statement', answerField: 'edit.prompt (a full sentence)', answerKind: 'span', lengthNote: 'n/a' },
      { label: 'Test queries', queryForm: 'cloze', answerField: 'test_queries[].answers[].value', median: 2, p90: 6, n: 20763, answerKind: 'span' },
    ],
    sampledFrom: 'data/benchmark/popular.json',
    note: 'Some prompts have the subject spliced out, leaving a double space: 92/1948 in recent, 4/1922 in random, 1/885 in popular. Those need resolving from subject_id before use.',
  },
  {
    benchmark: 'TAXI',
    rows: [
      { label: 'Forward + reverse', queryForm: 'blank', mcq: true, answerField: 'answer_fwd / answer_rev', median: 1, p90: 3, n: 5560, answerKind: 'token' },
    ],
    sampledFrom: 'datasets/edits-evaluation.json',
    note: 'The cleanest MCQ setup here: an explicit blank plus a choice list, queried in both directions. The foil1/2/3 columns are present but null in the rows checked.',
  },
  {
    benchmark: 'Bi-ZsRE',
    rows: [
      { label: 'Edit (en and zh)', queryForm: 'question', answerField: 'alt', median: 2, p90: 3, n: 1037, answerKind: 'span' },
    ],
    sampledFrom: 'Bi-ZsRE-data/bizsre_test.json',
    note: 'Each record carries a parallel English and Chinese half. Only one language is used per run.',
  },
  {
    benchmark: 'RelEdit',
    rows: [
      { label: 'Definition edit', queryForm: 'cloze', answerField: 'target_new_desc', median: 9, p90: 16, n: 452, answerKind: 'phrase' },
      { label: 'Locality probe', queryForm: 'cloze', answerField: 'locality_answer', median: 8, p90: 15, n: 452, answerKind: 'phrase' },
      { label: 'Category / alignment', queryForm: 'yes_no', answerField: 'none stored (implicit yes/no)', answerKind: 'token', lengthNote: 'n/a' },
    ],
    sampledFrom: 'RelEdit_dataset/final_gptj_intra_PCEdit.json',
    note: 'The one benchmark whose probes change answer kind mid-record. Scoring the yes/no probes with the same matcher as the definitions will not behave.',
  },
  {
    benchmark: 'ConflictEdit',
    rows: [
      { label: 'Edit', queryForm: 'cloze', answerField: 'edit.new_object.label', median: 2, p90: 6, n: 2500, answerKind: 'span' },
      { label: 'Same fact, question form', queryForm: 'question', answerField: 'edit.new_object.label', median: 2, p90: 6, n: 2500, answerKind: 'span' },
    ],
    sampledFrom: 'data/GPT-J/easy.json',
    note: 'Every relation stores both a `prompt` (cloze) and a `query` (question) template, which makes this the natural place to ablate query form against identical facts.',
  },
  {
    benchmark: 'ReCoE',
    rows: [
      { label: 'Edit', queryForm: 'question', answerField: 'counterfactual_answer', median: 1, p90: 2, n: 1153, answerKind: 'span' },
    ],
    sampledFrom: 'data/comparative/...verified_atomic.json',
    note: 'The choice_1_facts / choice_2_facts fields are evidence chains for the original and counterfactual answer, not multiple-choice options.',
  },
  {
    benchmark: 'AlteredRiddles',
    rows: [
      { label: 'Altered riddle', queryForm: 'question', answerField: 'altered_answer', median: 2, p90: 3, n: 700, answerKind: 'span' },
    ],
    sampledFrom: 'benchmark.jsonl',
    note: 'accepted_answers lists alternate surface forms, so exact match against the single answer field understates accuracy.',
  },
  {
    benchmark: 'UniEdit',
    rows: [
      { label: 'Edit', queryForm: 'cloze', answerField: 'edit.target', median: 5, p90: 11, n: 4174, answerKind: 'phrase' },
      { label: 'Generality probe', queryForm: 'cloze', answerField: 'generality[].target', median: 2, p90: 5, n: 4174, answerKind: 'span' },
      { label: 'Locality probe', queryForm: 'cloze', answerField: 'locality[].target', median: 2, p90: 5, n: 4174, answerKind: 'span' },
    ],
    sampledFrom: 'test/physics.json',
    note: 'Numbers are from one of 50 domain files. Edit targets run longer than the probes because they carry descriptors, not bare entities.',
  },
  {
    benchmark: 'KnowEdit',
    rows: [
      { label: 'wiki_recent', queryForm: 'cloze', answerField: 'target_new', median: 2, p90: 4, n: 1266, answerKind: 'span' },
      { label: 'wiki_counterfact', queryForm: 'cloze', answerField: 'target_new', median: 2, p90: 4, n: 839, answerKind: 'span' },
      { label: 'ZsRE', queryForm: 'question', answerField: 'target_new', median: 2, p90: 3, n: 1301, answerKind: 'span' },
      { label: 'WikiBio', queryForm: 'continuation', answerField: 'labels', median: 18.5, p90: 33, n: 306, answerKind: 'sentence' },
      { label: 'Convsent', queryForm: 'statement', answerField: 'pos / neg', median: 14, p90: 29, n: 8679, answerKind: 'sentence' },
      { label: 'trivia', queryForm: 'question', answerField: 'ground_truth', median: 2, p90: 3, n: 533, answerKind: 'span' },
    ],
    sampledFrom: 'benchmark/<subset>/',
    note: "ZsRE asks a question for the edit but uses cloze for its locality probes. trivia's target_new is the fixed string \"I don't know.\", so its ground_truth is the informative field.",
  },
  {
    benchmark: 'DUnE',
    rows: [
      { label: 'scientific', queryForm: 'question', mcq: true, answerField: 'test_inputs[][1]', median: 1, p90: 1, n: 1508, answerKind: 'token' },
      { label: 'new_info', queryForm: 'question', mcq: true, answerField: 'test_inputs[][1]', median: 1, p90: 1, n: 1000, answerKind: 'token' },
      { label: 'debiasing_I', queryForm: 'question', answerField: 'test_inputs[][1]', median: 3, p90: 4, n: 943, answerKind: 'span' },
      { label: 'debiasing_II', queryForm: 'question', answerField: 'test_inputs[][1]', median: 1, p90: 1, n: 1600, answerKind: 'token' },
      { label: 'arithmetic', queryForm: 'question', answerField: 'none', answerKind: 'span', lengthNote: 'n/a' },
    ],
    sampledFrom: 'dune/<subset>.json',
    note: 'The edit is never a prompt here, it is a free-text statement. All the query structure lives on the probe side, with the options inlined in the question string rather than in a separate field, and the letter style varies (A. against a)). arithmetic carries no answer at all: its ground truth is the right-hand side of the matching edits[i] equation, aligned by index.',
  },
  {
    benchmark: 'RealTimeQA',
    rows: [
      { label: 'All question types', queryForm: 'question', mcq: true, answerField: 'target_new', median: 2, p90: 5, n: 9383, answerKind: 'span' },
    ],
    sampledFrom: 'realtimeqa_editing.json',
    note: 'Natively 4-choice with an integer answer index. build_editing_set.py flattens it to the answer string but keeps `choices`, so the MCQ form is still recoverable if you want to score it that way.',
  },
  {
    benchmark: 'UnKEBench',
    rows: [
      { label: 'Edit', queryForm: 'question', answerField: 'answer', median: 90, p90: 116, n: 1000, answerKind: 'sentence' },
      { label: 'Rephrase probe', queryForm: 'question', answerField: 'answer (same passage)', median: 90, p90: 116, n: 1000, answerKind: 'sentence' },
      { label: 'Sub-question probe', queryForm: 'question', answerField: 'sub_answer[]', median: 4, p90: 10, n: 4729, answerKind: 'span' },
      { label: 'MMLU locality', queryForm: 'question', mcq: true, answerField: 'mmlu_choices[][mmlu_answer[]]', median: 4, p90: 16, n: 5000, answerKind: 'token' },
    ],
    sampledFrom: 'data/final_data_v3.json',
    note: 'The one benchmark here whose edit target is a passage rather than a value, which is the point of it: the sub-questions then ask about individual facts stated inside that passage. mmlu_answer is an index into that item\'s own choice list, not a letter. No subject span in the release, so the locate-and-edit methods cannot run on it.',
  },
  {
    benchmark: 'EditEverything',
    rows: [
      { label: 'Edit', queryForm: 'question', answerField: 'answer', median: 177.5, p90: 230, n: 552, answerKind: 'sentence' },
    ],
    sampledFrom: 'data/editevery.json',
    note: 'The longest targets of any benchmark here, and the only ones whose answers are genuine content rather than counterfactuals: worked derivations, runnable code, verse. Seven domains (physics 221, biology 92, math 78, chemistry 51, code 49, poetry 31, news 30) with answer length varying widely between them, from a median of 42 words for code to 201 for biology. No probes and no subject field ship with it, so edit success is the only metric.',
  },
]

// Things that bite when wiring a dataset in, surfaced under the table.
export const FORMAT_GOTCHAS = [
  'Only RealTimeQA among the MCQ benchmarks is wired into the runner, and nothing has MCQ-aware scoring: choices are currently ignored and the answer is graded as open generation.',
  'UnKEBench and EditEverything are the only wired-in benchmarks whose ground truth is sentence-length. KnowEdit WikiBio and Convsent would be too, but both are still marked unavailable.',
  'Neither new benchmark ships a subject span, so like RealTimeQA they run under FT, LoRA, SCR and IKE only, not ROME, MEMIT, PMET or AlphaEdit.',
  'RuleEdit-200 sits in datasets/ but is registered nowhere: three of its 400 source records are malformed upstream, so prepare_benchmarks.py skips it with a warning. It is cloze-form with a roughly seven-word formula as ground truth, so it would land in the phrase band once those records are fixed.',
]

export const MEASUREMENT_NOTE =
  'Lengths are whitespace-token counts over the ground-truth field named in each row, measured directly off the files under datasets/. Median is the typical case; p90 is where the tail starts to matter for a max-new-tokens budget.'
