// The hyperparameter results explorer (components/HpExplorer.jsx): metrics,
// averaging over the other settings, the answer-diversity and grammar gate and best values.
// Everything here is per method and per model: a table never averages over
// either (layer numbers mean different depths in different models).
import { duration, formatValue, pct, stats } from './hparams.js'

// The selection rule's gate (hparam_sweeps.FLUENCY_DROP, WELL_FORMED_DROP).
// A run passes when it keeps both; a value (an average over runs) is greyed
// out and never "best" when fewer than half of its finished runs pass. Not
// the mean: in a Latin hypercube every value of every setting shares runs
// with a collapsing learning rate, which drags every mean below the gate.
export const GATE = { fluency: 0.85, well_formed: 0.9 }
export const runGated = (row) => (row.scores?.fluency != null && row.scores.fluency < GATE.fluency)
  || (row.scores?.well_formed != null && row.scores.well_formed < GATE.well_formed)

// Each metric has one colour wherever it appears. `better` says which way is
// good; `get` reads it from a results row (hparam_sweeps.results).
export const METRICS = [
  { key: 'fluency', label: 'Answer diversity', color: '#7aa2f7', better: 'high', get: (r) => r.scores?.fluency,
    help: 'variety of the answers to a record’s different questions (ROME’s and EasyEdit’s “fluency”: n-gram entropy), over the unedited model’s, capped at 1; on short answers it falls when one answer, usually the new one, takes over the other questions' },
  { key: 'reliability', label: 'Rewrite', color: '#ff9e64', better: 'high', get: (r) => r.scores?.reliability,
    help: 'the edited question itself answered with the new answer (EasyEdit’s “reliability” or edit success, on the direct question only)' },
  { key: 'locality', label: 'Specificity', color: '#2ac3de', better: 'high', get: (r) => r.scores?.locality,
    help: 'unrelated questions keep the unedited model’s answer (CounterFact’s “specificity”, EasyEdit’s “locality”)' },
  { key: 'generalizability', label: 'Generalizability', color: '#bb9af7', better: 'high', get: (r) => r.scores?.generalizability,
    help: 'determinate derived questions the unedited model answered with the original answer (EasyEdit’s “portability”)' },
  { key: 'paraphrase', label: 'Paraphrase', color: '#f7c873', better: 'high', get: (r) => r.scores?.paraphrase,
    help: 'the edited fact asked in other words' },
  { key: 'well_formed', label: 'Grammar', color: '#a9b1d6', better: 'high', get: (r) => r.scores?.well_formed,
    help: 'LLM judge: share of well-formed answers over the unedited model’s, capped at 1' },
  { key: 'gate', label: 'Keeps diversity + grammar', color: '#9ece6a', better: 'high',
    get: (r) => (r.state === 'COMPLETED' ? (runGated(r) ? 0 : 1) : null),
    help: `share of runs keeping answer diversity at ${GATE.fluency} and grammar at ${GATE.well_formed} of the unedited model` },
  { key: 'edit_sec', label: 'Edit time', color: '#9aa1b4', better: 'low', get: (r) => r.edit_sec,
    help: 'editing alone, without evaluation' },
]
export const DEFAULT_METRICS = ['fluency', 'reliability', 'locality', 'generalizability']
export const metric = (key) => METRICS.find((m) => m.key === key)

export function formatMetric(key, value) {
  if (value == null) return '—'
  return key === 'edit_sec' ? duration(value) : pct(value)
}

export function parseMetrics(text) {
  const keys = (text || '').split(',').filter((k) => metric(k))
  return keys.length ? [...new Set(keys)] : DEFAULT_METRICS
}

// A setting's value as shown and as ordered: numbers by size, lists by
// their first number, the rest by name.
export const valueOf = (row, knob) => (knob in (row.overrides || {}) ? row.overrides[knob] : undefined)
const orderOf = (raw) => (typeof raw === 'number' ? raw : Array.isArray(raw) && typeof raw[0] === 'number' ? raw[0] : null)
export function compareValues(a, b) {
  const oa = orderOf(a), ob = orderOf(b)
  if (oa != null && ob != null && oa !== ob) return oa - ob
  if (Array.isArray(a) && Array.isArray(b) && a.length !== b.length) return a.length - b.length
  return formatValue(a).localeCompare(formatValue(b), undefined, { numeric: true })
}

// Settings this method's runs vary, in name order.
export const knobsOf = (rows) => [...new Set(rows.flatMap((r) => Object.keys(r.overrides || {})))].sort()

// Layer settings: shown as relative depth too, where the model's layer
// count is known ("14 (39%)").
export const isLayerKnob = (knob) => /layer/i.test(knob)
export function depth(raw, layers) {
  const xs = (Array.isArray(raw) ? raw : [raw]).filter((x) => typeof x === 'number')
  if (!xs.length || !layers) return null
  return (xs.reduce((a, b) => a + b, 0) / xs.length + 0.5) / layers
}
export function formatSetting(knob, raw, layers) {
  const text = raw === undefined ? 'not swept' : formatValue(raw)
  const d = isLayerKnob(knob) ? depth(raw, layers) : null
  return d == null ? text : `${text} (${Math.round(d * 100)}% deep)`
}

// centre: a factorial's centre runs set every setting to its middle value at
// once, so the "middle" of any one setting is always those same few runs.
// They test curvature (does the middle beat both ends?), not a level of one
// setting, so they are shown but never picked as best.
function summarize(rows) {
  const finished = rows.filter((r) => r.state === 'COMPLETED')
  const means = Object.fromEntries(METRICS.map((m) => [m.key, stats(finished.map(m.get))]))
  const centre = rows.length > 0 && rows.every((r) => r.point === 'centre')
  const share = means.gate.mean
  return { rows, finished: finished.length, means, gated: share != null && share < 0.5, centre }
}


// One group per value of `knob`, averaging the finished runs at that value
// over every other setting's values.
export function marginal(rows, knob) {
  const groups = new Map()
  for (const row of rows) {
    const raw = valueOf(row, knob)
    const key = JSON.stringify(raw ?? null)
    if (!groups.has(key)) groups.set(key, { key, raw, rows: [] })
    groups.get(key).rows.push(row)
  }
  return [...groups.values()].map((g) => ({ ...g, ...summarize(g.rows) })).sort((a, b) => compareValues(a.raw, b.raw))
}

// Rows by `rowKnob`, columns by `colKnob`: {rows: [raw], cols: [raw], cell(r, c)}.
export function grid(rows, rowKnob, colKnob) {
  const rowVals = marginal(rows, rowKnob).map((g) => g.raw)
  const colVals = marginal(rows, colKnob).map((g) => g.raw)
  const cells = new Map()
  for (const row of rows) {
    const k = `${JSON.stringify(valueOf(row, rowKnob) ?? null)}|${JSON.stringify(valueOf(row, colKnob) ?? null)}`
    if (!cells.has(k)) cells.set(k, [])
    cells.get(k).push(row)
  }
  const done = new Map([...cells].map(([k, rs]) => [k, summarize(rs)]))
  const cell = (r, c) => done.get(`${JSON.stringify(r ?? null)}|${JSON.stringify(c ?? null)}`) || null
  return { rows: rowVals, cols: colVals, cell }
}

// The best summarized group per metric among those above the gate: {metric: group}.
export function bests(groups, metricKeys) {
  const out = {}
  for (const key of metricKeys) {
    const m = metric(key)
    let best = null
    for (const g of groups) {
      const v = g?.means[key]?.mean
      if (v == null || g.gated || g.centre) continue
      if (!best || (m.better === 'low' ? v < best.means[key].mean : v > best.means[key].mean)) best = g
    }
    if (best) out[key] = best
  }
  return out
}

// A value of a setting by the selection rule: the most rewrite among the
// values above the gate. {group, spread}: spread is the range of rewrite
// over the setting's values (how much the setting moves it).
export function bestValue(rows, knob) {
  const groups = marginal(rows, knob).filter((g) => g.raw !== undefined && !g.centre)
  const best = bests(groups, ['reliability']).reliability || null
  const means = groups.map((g) => g.means.reliability.mean).filter((v) => v != null)
  return { group: best, spread: means.length > 1 ? Math.max(...means) - Math.min(...means) : null, values: groups.length }
}
