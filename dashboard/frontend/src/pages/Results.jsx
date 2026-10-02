import { useEffect, useMemo, useState } from 'react'
import EvaluationFilter from '../components/EvaluationFilter.jsx'
import BERTScoreNote from '../components/BERTScoreNote.jsx'
import { evaluationRow, hasEvaluation, evaluationMetric } from '../lib/evaluationModes.js'
import ResultsTable from './ResultsTable.jsx'
import ResultsGraph from './ResultsGraph.jsx'
import ResultsResponses from './ResultsResponses.jsx'
import ResultsArchive from './ResultsArchive.jsx'
import ResultsDatasetPicker from '../components/ResultsDatasetPicker.jsx'
import ArchiveConfirm from '../components/ArchiveConfirm.jsx'
import TestingResults from './TestingResults.jsx'
import ResultsSubnav from '../components/ResultsSubnav.jsx'
import { api } from '../api.js'
import { metricLabel } from '../lib/formatMetric.js'
import { toggleGroup } from '../lib/groupSelect.js'
import { useArchiveMove } from '../lib/useArchiveMove.js'

const MODES = [
  { key: 'table', label: 'Table' },
  { key: 'graph', label: 'Graph' },
  { key: 'responses', label: 'Responses' },
  { key: 'testing', label: 'Trial Runs' },
  { key: 'archive', label: 'Archive' },
]

// Which tabs are about one dataset's runs, and which of those are about one
// metric. Trial Runs and Archive are neither: they list whole runs, so the
// dataset picker and the metric tabs would only be furniture above them.
const DATASET_MODES = new Set(['table', 'graph', 'responses'])
const METRIC_MODES = new Set(['table', 'graph'])

// Config knobs, not outcomes - never offered as a "metric" tab.
const METRIC_EXCLUDE = new Set(['lr', 'num_steps', 'ds_size', 'seed', 'gpu_mem_total_mb'])
const METRIC_GROUPS = {
  ke: { label: 'KE metrics', metrics: ['edit_succ', 'fluency', 'portability', 'locality'] },
  memory: { label: 'Memory', metrics: ['gpu_mem_alloc_mb', 'gpu_mem_peak_mb', 'host_rss_mb'] },
}

// Bolding the *highest* value per row would highlight the worst run for a
// metric where lower is better (loss, wall-clock time, memory) - these
// pick the lowest instead. Everything else (edit success, portability,
// locality, fluency, ...) is accuracy-shaped, higher is better.
const LOWER_IS_BETTER = new Set(['loss', 'total_sec', 'gpu_mem_alloc_mb', 'gpu_mem_peak_mb', 'host_rss_mb'])

export default function Results() {
  const [evaluation, setEvaluation] = useState('original')
  const [mode, setMode] = useState('table')
  const [manifest, setManifest] = useState([])
  const [expType, setExpType] = useState(null)
  const [dataset, setDataset] = useState(null)
  const [metricKey, setMetricKey] = useState(null)
  const [groupMetrics, setGroupMetrics] = useState({ ke: 'edit_succ', memory: 'gpu_mem_alloc_mb' })

  // Selection is deliberately not cleared when the dataset picker changes -
  // retiring a botched sweep usually spans several benchmarks, and having
  // the tray empty itself as you looked for the rest of it would be worse
  // than carrying a few runs you can see listed there.
  const [selecting, setSelecting] = useState(false)
  const [selected, setSelected] = useState([])

  const loadManifest = () => api.manifest().then(setManifest)
  const move = useArchiveMove(() => {
    loadManifest()
    setSelected([])
  })

  useEffect(() => {
    api.experimentTypes().then((types) => setExpType(types.find((t) => t.name === 'run_experiment') || types[0] || null))
  }, [])

  useEffect(() => {
    loadManifest()
    const id = setInterval(loadManifest, 15000)
    return () => clearInterval(id)
  }, [])

  // Only benchmarks/subsets that actually have a run - not every
  // registered dataset the Experiments sidebar knows about.
  const datasetOptions = useMemo(() => {
    const byBenchmark = new Map()
    for (const r of manifest) {
      if (!r.dataset_benchmark) continue
      if (!byBenchmark.has(r.dataset_benchmark)) byBenchmark.set(r.dataset_benchmark, new Set())
      byBenchmark.get(r.dataset_benchmark).add(r.dataset_subset)
    }
    return [...byBenchmark.entries()].map(([benchmark, subsets]) => ({ benchmark, subsets: [...subsets] }))
  }, [manifest])

  useEffect(() => {
    if (dataset && datasetOptions.some((o) => o.benchmark === dataset.benchmark && o.subsets.includes(dataset.subset))) return
    if (datasetOptions.length) setDataset({ benchmark: datasetOptions[0].benchmark, subset: datasetOptions[0].subsets[0] })
    else setDataset(null)
  }, [datasetOptions, dataset])

  const rowsForDataset = useMemo(
    () =>
      dataset
        ? manifest.filter((r) => r.dataset_benchmark === dataset.benchmark && r.dataset_subset === dataset.subset).filter((r) => hasEvaluation(r, evaluation)).map((r) => evaluationRow(r, evaluation))
        : [],
    [manifest, dataset, evaluation],
  )

  const metricKeys = useMemo(() => {
    const keys = new Set()
    for (const raw of manifest) {
      const r = evaluationRow(raw, evaluation)
      for (const [k, v] of Object.entries(r)) {
        if (typeof v === 'number' && !METRIC_EXCLUDE.has(k)) keys.add(k)
      }
    }
    for (const key of ['edit_succ', 'portability', 'locality']) keys.add(key)
    return [...keys]
  }, [manifest, evaluation])

  const groupFor = (key) => Object.keys(METRIC_GROUPS).find((group) => METRIC_GROUPS[group].metrics.includes(key))
  const activeGroup = groupFor(metricKey)
  const metricTabs = [...new Set(metricKeys.map((key) => groupFor(key) || key))]

  function selectMetricTab(key) {
    const group = METRIC_GROUPS[key]
    setMetricKey(group
      ? (metricKeys.includes(groupMetrics[key]) ? groupMetrics[key] : group.metrics.find((metric) => metricKeys.includes(metric)))
      : key)
  }

  useEffect(() => {
    if (metricKey && metricKeys.includes(metricKey)) return
    if (metricKeys.length) setMetricKey(metricKeys.includes('edit_succ') ? 'edit_succ' : metricKeys[0])
  }, [metricKeys, metricKey])

  // Raw value ("ft", "qwen3-4b") -> {label, category}, read from this
  // experiment type's own dashboard.json rather than duplicated here -
  // one source of truth for what a method/model is called and grouped under.
  const methodMeta = useMemo(() => {
    const meta = {}
    for (const cat of expType?.fields?.find((f) => f.name === 'method')?.categories || []) {
      for (const m of cat.methods) meta[m.value] = { label: m.label, category: cat.label }
    }
    return meta
  }, [expType])

  const modelMeta = useMemo(() => {
    const meta = {}
    // Every tuning stage is its own model value; the label says which one,
    // since a name like "Qwen3-4B" alone does not (that one is the hybrid).
    const stage = { raw: 'base', chat: 'instruct', reasoning: 'reasoning' }
    for (const o of expType?.fields?.find((f) => f.name === 'model')?.options || []) {
      const type = stage[o.model_type] || o.model_type
      const suffix = o.variant && type && o.variant.toLowerCase() !== type ? `${o.variant}, ${type}` : (o.variant || type)
      meta[o.value] = { label: suffix ? `${o.label} (${suffix})` : o.label, type }
    }
    return meta
  }, [expType])

  return (
    <div>
      <ResultsSubnav />
      <div className="page-header">
        <h1>Main results</h1>
        {mode === 'table' && (
          <button
            type="button"
            className={`btn-plain-small${selecting ? ' is-on' : ''}`}
            aria-pressed={selecting}
            onClick={() => { setSelecting((on) => !on); setSelected([]) }}
          >
            {selecting ? 'Done selecting' : 'Select runs'}
          </button>
        )}
      </div>

      <div className="subnav">
        {MODES.map((m) => (
          <button
            key={m.key}
            type="button"
            className={`subnav-tab${mode === m.key ? ' active' : ''}`}
            onClick={() => setMode(m.key)}
          >
            {m.label}
          </button>
        ))}
      </div>

      {DATASET_MODES.has(mode) && <EvaluationFilter value={evaluation} onChange={setEvaluation} />}
      {evaluation === 'bertscore' && DATASET_MODES.has(mode) && (
        <BERTScoreNote />
      )}
      {dataset && DATASET_MODES.has(mode) && !rowsForDataset.length && (
        <p className="dataset-missing">No saved results for this evaluation mode. Older runs contain Original scores only.</p>
      )}

      {METRIC_MODES.has(mode) && metricKeys.length > 0 && (
        <div className="subnav metric-tabs" role="group" aria-label="Metric">
          {metricTabs.map((k) => (
            <button
              key={k}
              type="button"
              className={`subnav-tab${(METRIC_GROUPS[k] ? activeGroup === k : metricKey === k) ? ' active' : ''}`}
              aria-pressed={METRIC_GROUPS[k] ? activeGroup === k : metricKey === k}
              onClick={() => selectMetricTab(k)}
            >
              {METRIC_GROUPS[k]?.label || metricLabel(k)}
            </button>
          ))}
        </div>
      )}

      {METRIC_MODES.has(mode) && activeGroup && (
        <div className="axis-tabs metric-subtabs" role="group" aria-label={`${METRIC_GROUPS[activeGroup].label} options`}>
          {METRIC_GROUPS[activeGroup].metrics.map((key) => (
            <button
              key={key}
              type="button"
              className={`subnav-tab${metricKey === key ? ' active' : ''}`}
              aria-pressed={metricKey === key}
              disabled={!metricKeys.includes(key)}
              onClick={() => { setGroupMetrics((previous) => ({ ...previous, [activeGroup]: key })); setMetricKey(key) }}
            >
              {metricLabel(key)}
            </button>
          ))}
        </div>
      )}

      {METRIC_MODES.has(mode) && metricKey === 'portability' && (
        <p className="metric-note">Generalizability is the same metric previously called Portability.</p>
      )}

      {mode === 'testing' && <TestingResults />}
      {mode === 'archive' && <ResultsArchive onChanged={loadManifest} />}
      {DATASET_MODES.has(mode) && <ResultsDatasetPicker options={datasetOptions} value={dataset} onChange={setDataset} />}

      {!dataset && DATASET_MODES.has(mode) && <p className="dataset-missing">No results yet.</p>}
      {dataset && mode === 'table' && (
        <ResultsTable
          rows={rowsForDataset}
          metricKey={metricKey}
          displayMetricKey={evaluationMetric(metricKey, evaluation)}
          methodMeta={methodMeta}
          modelMeta={modelMeta}
          lowerIsBetter={LOWER_IS_BETTER.has(metricKey)}
          selectMode={selecting}
          selected={selected}
          onToggleRuns={(runs) => setSelected((previous) => toggleGroup(runs, previous))}
        />
      )}
      {dataset && mode === 'graph' && (
        <ResultsGraph rows={rowsForDataset} evaluation={evaluation} metricKey={metricKey} methodMeta={methodMeta} modelMeta={modelMeta} />
      )}
      {dataset && mode === 'responses' && (
        <ResultsResponses evaluation={evaluation} rows={rowsForDataset} methodMeta={methodMeta} modelMeta={modelMeta} />
      )}

      {selecting && mode === 'table' && (
        <div className="archive-tray">
          <div className="archive-tray-runs">
            {selected.length === 0 ? (
              <span className="archive-tray-hint">Nothing selected yet. Click a cell, or a row label.</span>
            ) : (
              selected.map((run) => (
                <button
                  key={run}
                  type="button"
                  className="archive-chip"
                  title="Remove from selection"
                  onClick={() => setSelected((previous) => previous.filter((r) => r !== run))}
                >
                  {run} <span aria-hidden="true">✕</span>
                </button>
              ))
            )}
          </div>
          <div className="archive-tray-actions">
            <button type="button" className="btn-plain-small" disabled={!selected.length} onClick={() => setSelected([])}>
              Clear
            </button>
            <button
              type="button"
              className="btn-primary"
              disabled={!selected.length}
              onClick={() => move.begin('archive', selected)}
            >
              Archive {selected.length} run{selected.length === 1 ? '' : 's'}
            </button>
          </div>
        </div>
      )}

      {move.open && (
        <ArchiveConfirm
          direction={move.direction}
          plan={move.plan}
          reason={move.reason}
          onReason={move.setReason}
          result={move.result}
          pending={move.pending}
          error={move.error}
          onConfirm={move.confirm}
          onClose={move.close}
        />
      )}
    </div>
  )
}
