// Shared helpers for the Hyperparameters pages and their results.

export const CATEGORY_ORDER = ['WHERE', 'WHAT', 'HOW MUCH', 'CONTEXT']

export const CATEGORY_HELP = {
  WHERE: 'where the edit lands',
  WHAT: 'the content being written',
  'HOW MUCH': 'how strongly it is written',
  CONTEXT: 'the data and prompts that shape the edit',
}

export const STABILITY_LABEL = {
  robust: 'Robust: same in every configuration the authors used',
  model: 'Model: the authors change it per model',
  data: 'Data: the authors change it per dataset',
  not_reported: 'Not reported: the authors give no value',
}

// Swept values travel as JSON so lists (layers, modules) round-trip.
export const formatValue = (value) => {
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

// The four criteria, 0..1, as the backend scores them (hparam_sweeps._scores).
export const CRITERIA = [
  { key: 'reliability', label: 'Reliability', help: 'edit success on the edited prompts' },
  { key: 'generalizability', label: 'Generalizability', help: 'paraphrases and multi-hop consequences' },
  { key: 'locality', label: 'Locality', help: 'unrelated facts unchanged' },
  { key: 'fluency', label: 'Fluency', help: 'final fluency over the unedited model’s, capped at 1' },
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
