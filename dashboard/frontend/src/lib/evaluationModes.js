export const EVALUATION_MODES = [
  { value: 'original', label: 'Original' },
  { value: 'exact_match', label: 'Exact Match' },
  { value: 'bertscore', label: 'BERTScore' },
  { value: 'llm_judge', label: 'LLM Judge' },
]
const QUALITY = ['edit_succ', 'portability', 'locality', 'fluency']

export function hasEvaluation(row, mode) {
  if (row.evaluations) return Object.hasOwn(row.evaluations, mode)
  return mode === 'original' && (!row.evaluation_modes || row.evaluation_modes.includes('original'))
}

export function evaluationRow(row, mode) {
  const scores = row.evaluations?.[mode]
  const legacy = !row.evaluations && hasEvaluation(row, mode)
  return { ...row, ...Object.fromEntries(QUALITY.map((key) => [key,
    scores ? scores[key] ?? null : legacy ? row[key] ?? null : null,
  ])) }
}

export function evaluationMetric(key, mode) {
  return mode === 'bertscore' && QUALITY.includes(key) ? `bertscore_${key}` : key
}
