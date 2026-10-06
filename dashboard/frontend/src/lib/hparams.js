// Shared helpers for the Investigations pages and their results.

export const GROUP_ORDER = ['mechanistic', 'sweep', 'input']

export const GROUP_LABEL = {
  mechanistic: 'Mechanistic',
  sweep: 'Hyperparameter sweeps',
  input: 'Input and context',
}

export const GROUP_HELP = {
  mechanistic: 'measure the model itself, per model, with no editing method involved',
  sweep: 'try settings of each editing method on dev records, to pick what the main experiments use',
  input: 'check whether what the model is given, how the prompt is written and what context is added to it, changes a result',
}

export const STABILITY_LABEL = {
  robust: 'Robust: same in every configuration the authors used',
  model: 'Model: the authors change it per model',
  data: 'Data: the authors change it per dataset',
  not_reported: 'Not reported: the authors give no value',
}

// Swept values travel as JSON so lists (layers, modules) round-trip.
// A long run of consecutive layers reads as a range. An empty list only
// occurs as LoRA's layers, where it means adapters on every layer.
const isRun = (value) => value.length > 5 && value.every((v, i) => Number.isInteger(v) && v === value[0] + i)

export const formatValue = (value) => {
  if (Array.isArray(value) && value.length === 0) return 'all layers'
  if (Array.isArray(value) && isRun(value)) return `[${value[0]}..${value[value.length - 1]}]`
  if (Array.isArray(value)) return value.some((v) => typeof v === 'object' && v !== null) ? JSON.stringify(value) : `[${value.join(', ')}]`
  if (value !== null && typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

export const valueKey = (value) => JSON.stringify(value)

export function parseValue(text) {
  const trimmed = text.trim()
  if (!trimmed) return undefined
  try {
    return JSON.parse(trimmed)
  } catch {
    return trimmed
  }
}

// The four criteria, 0..1, as the backend scores them (hparam_sweeps._scores),
// in the order the tables show them.
export const CRITERIA = [
  { key: 'fluency', label: 'Fluency', help: 'final fluency over the unedited model’s, capped at 1' },
  { key: 'reliability', label: 'Reliability', help: 'edit success on the edited prompts' },
  { key: 'locality', label: 'Locality', help: 'unrelated facts unchanged' },
  { key: 'generalizability', label: 'Generalizability', help: 'paraphrases and multi-hop consequences' },
]

// Colouring only, never filtering. Starting points chosen by eye; editable
// on the page and remembered per browser.
export const DEFAULT_THRESHOLDS = {
  reliability: { good: 0.8, bad: 0.5 },
  generalizability: { good: 0.5, bad: 0.25 },
  locality: { good: 0.9, bad: 0.7 },
  fluency: { good: 0.95, bad: 0.85 },
}

const THRESHOLD_KEY = 'hparam_thresholds'

export function loadThresholds() {
  try {
    const saved = JSON.parse(localStorage.getItem(THRESHOLD_KEY) || 'null')
    return saved ? { ...DEFAULT_THRESHOLDS, ...saved } : DEFAULT_THRESHOLDS
  } catch {
    return DEFAULT_THRESHOLDS
  }
}

export function saveThresholds(thresholds) {
  try {
    localStorage.setItem(THRESHOLD_KEY, JSON.stringify(thresholds))
  } catch {
    // Private windows can refuse storage; thresholds then last for the visit.
  }
}

export function band(value, threshold) {
  if (value == null || !threshold) return 'none'
  if (value >= threshold.good) return 'good'
  if (value < threshold.bad) return 'bad'
  return 'mid'
}

export function duration(seconds) {
  if (seconds == null) return '—'
  const s = Math.round(seconds)
  if (s < 60) return `${s}s`
  const m = Math.floor(s / 60)
  if (m < 60) return `${m}m ${s % 60}s`
  return `${Math.floor(m / 60)}h ${m % 60}m`
}

export const pct = (value) => (value == null ? '—' : `${Math.round(value * 1000) / 10}%`)

// The editing protocol in words, as the backend labels sweep runs
// (hparam_sweeps.protocol_label).
export function protocolLabel(mode, resetEvery, batchSize) {
  if (!mode) return 'no protocol (older runs)'
  if (mode === 'single') return 'single'
  if (mode === 'batch') return `batch of ${batchSize}`
  if (mode === 'sequential') return `sequential, reset every ${resetEvery}`
  return `batches of ${batchSize}, reset every ${resetEvery}`
}

// ---- averaging runs ----

// The tested values of a run, as one comparable key ("layers=[4]"),
// optionally leaving one setting out.
export const settingKey = (overrides, except) =>
  Object.keys(overrides || {}).filter((k) => k !== except).sort().map((k) => `${k}=${valueKey(overrides[k])}`).join(' ')

// A swept setting can be averaged by too: "knob:layers" groups runs by
// their layers value, whatever method, model or dataset they came from.
export const knobFactor = (key) => `knob:${key}`
const knobOf = (factor) => (factor && factor.startsWith('knob:') ? factor.slice(5) : null)

export function factorValue(row, factor) {
  const knob = knobOf(factor)
  if (!knob) return row[factor]
  return knob in (row.overrides || {}) ? formatValue(row.overrides[knob]) : 'not swept'
}

export const FACTORS = [
  { key: 'method', label: 'Method' },
  { key: 'model', label: 'Model' },
  { key: 'model_type', label: 'Model type', help: 'base, instruct or reasoning: compares tuning stages across families' },
  { key: 'model_family', label: 'Model family', help: 'one pretrain and its tuning stages, e.g. every Qwen3-4B variant' },
  { key: 'dataset', label: 'Dataset' },
  { key: 'protocol', label: 'Protocol', help: 'single, batch or sequential editing: how many facts per edit call and how many build up before the weights reset' },
]
// What an averaged row reports it averaged over.
const OVER = ['method', 'model', 'dataset', 'protocol']

// Mean, sample variance and standard deviation of the non-missing values.
export function stats(values) {
  const xs = values.filter((v) => v != null && Number.isFinite(v))
  const n = xs.length
  if (!n) return { n: 0, mean: null, variance: null, sd: null }
  const mean = xs.reduce((a, b) => a + b, 0) / n
  const variance = n > 1 ? xs.reduce((a, b) => a + (b - mean) ** 2, 0) / (n - 1) : null
  return { n, mean, variance, sd: variance == null ? null : Math.sqrt(variance) }
}

// One row per value of `factor` (and per tested setting unless pooled),
// averaging every finished run in it over everything else.
export function aggregate(rows, factor, keepSetting, done = 'COMPLETED') {
  const knob = knobOf(factor)
  const groups = new Map()
  for (const row of rows) {
    const value = factor ? factorValue(row, factor) : 'All runs'
    // Grouping by a setting: the other swept settings (if any) stay apart,
    // and so do protocols, unless pooled.
    const rest = keepSetting ? `${settingKey(row.overrides, knob)}|${factor === 'protocol' ? '' : row.protocol || ''}` : ''
    const key = `${value}|${rest}`
    const shown = keepSetting
      ? Object.fromEntries(Object.entries(row.overrides || {}).filter(([k]) => k !== knob))
      : null
    const protocol = keepSetting && factor !== 'protocol' ? row.protocol : null
    if (!groups.has(key)) groups.set(key, { key, value, raw: knob ? row.overrides?.[knob] : undefined, overrides: shown, protocol, rows: [] })
    groups.get(key).rows.push(row)
  }
  return [...groups.values()].map((g) => {
    const finished = g.rows.filter((r) => r.state === done)
    const over = Object.fromEntries(OVER.filter((f) => f !== factor)
      .map((f) => [f, [...new Set(g.rows.map((r) => r[f]))]]))
    return {
      ...g,
      total: g.rows.length,
      finished: finished.length,
      over,
      scores: Object.fromEntries(CRITERIA.map((c) => [c.key, stats(finished.map((r) => r.scores?.[c.key]))])),
      time: stats(finished.map((r) => r.wall_sec)),
    }
  })
}
