import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../api.js'
import ResultsSubnav from '../components/ResultsSubnav.jsx'
import SweepFailures from '../components/SweepFailures.jsx'
import HpExplorer from '../components/HpExplorer.jsx'
import { TUNING_KINDS, formatValue } from '../lib/hparams.js'

const DONE = 'COMPLETED'

// Results · Hyperparameter tuning. Step (kind of sweep) and method family
// pick which runs load; HpExplorer then shows one method on one model at a
// time (tabs), never averaging over methods or models.
export default function InvestigationResults() {
  const [params, setParams] = useSearchParams()
  const [investigations, setInvestigations] = useState([])
  const [rows, setRows] = useState(null)
  const [error, setError] = useState(null)
  const [promoted, setPromoted] = useState({})
  const investigation = params.get('investigation') || ''
  const view = params.get('view') === 'failures' ? 'failures' : 'rankings'
  const kind = TUNING_KINDS.some((k) => k.key === params.get('kind')) ? params.get('kind') : 'lhs'
  const [failureCount, setFailureCount] = useState(null)
  useEffect(() => {
    api.sweepFailures().then((f) => setFailureCount(f.open.length)).catch(() => {})
  }, [view])
  // setParam(key, value) sets or clears one URL parameter; setParam(null,
  // URLSearchParams) replaces them all at once (several changes in one step).
  const setParam = (key, value) => {
    if (key === null) {
      setParams(value, { replace: true })
      return
    }
    const next = new URLSearchParams(params)
    if (value) next.set(key, value)
    else next.delete(key)
    setParams(next, { replace: true })
  }
  // A new step or family starts its explorer from scratch (metrics kept).
  const reset = (changes) => {
    const next = new URLSearchParams()
    for (const key of ['investigation', 'kind', 'view', 'metrics']) if (params.get(key)) next.set(key, params.get(key))
    for (const [key, value] of Object.entries(changes)) {
      if (value) next.set(key, value)
      else next.delete(key)
    }
    setParams(next, { replace: true })
  }

  useEffect(() => {
    api.investigations().then((everything) => {
      // Causal tracing keeps its results on its own page, not as sweeps.
      const all = everything.filter((i) => i.scope !== 'model')
      setInvestigations(all)
      if (!investigation && all.length) setParam('investigation', all[0].id)
    }).catch((e) => setError(e.message))
  }, [])

  useEffect(() => {
    if (!investigation || view !== 'rankings') return
    let live = true
    setRows(null)
    const load = () => api.sweepResults(investigation).then((r) => { if (live) setRows(r) }).catch((e) => setError(e.message))
    load()
    const timer = setInterval(load, 20000)
    return () => { live = false; clearInterval(timer) }
  }, [investigation, view])

  // This step's runs; a failed run cleared off the Failures view has nothing to show.
  const kindRows = useMemo(() => (rows || []).filter((r) => r.kind === kind && !(r.failure_cleared && r.state !== DONE)),
    [rows, kind])
  const modelNames = useMemo(() => Object.fromEntries(kindRows.map((r) => [r.model, r])), [kindRows])
  const modelLabel = (model) => (modelNames[model]
    ? `${modelNames[model].model_label}${modelNames[model].model_variant ? ` (${modelNames[model].model_variant})` : ''}`
    : model)

  async function promote(row) {
    const settings = Object.entries(row.overrides).map(([k, v]) => `${k} = ${formatValue(v)}`).join(', ')
    if (!window.confirm(`Use ${settings} as the main setting for ${row.method} on ${row.model}? This rewrites that hparams file.`)) return
    try {
      const result = await api.promoteConfig(investigation, row.sweep_id, row.run)
      setPromoted((p) => ({ ...p, [row.run]: `written to ${result.file}` }))
    } catch (e) {
      setPromoted((p) => ({ ...p, [row.run]: e.message }))
    }
  }

  const stepLabel = (k) => {
    const step = k.short.split(' · ')[0]
    return step.startsWith('step') ? `Step ${step.slice(5)} · ${k.label}` : k.label
  }
  const current = investigations.find((i) => i.id === investigation)
  return (
    <div>
      <ResultsSubnav />
      <div className="page-header">
        <h1>Hyperparameter tuning results</h1>
        {current && <Link to={`/experiments/investigations/${current.id}`} className="btn-plain-small">Launch sweeps for {current.label} →</Link>}
      </div>
      <div className="pill-row hp-view-switch" role="group" aria-label="View">
        <button type="button" className={`pill${view === 'rankings' ? ' selected' : ''}`} aria-pressed={view === 'rankings'}
          onClick={() => setParam('view', '')}>Results</button>
        <button type="button" className={`pill${view === 'failures' ? ' selected' : ''}`} aria-pressed={view === 'failures'}
          onClick={() => setParam('view', 'failures')}>
          Failures{failureCount ? <span className="hp-failure-count">{failureCount}</span> : null}
        </button>
      </div>
      {view === 'failures' && <SweepFailures />}
      {view === 'rankings' && <>
        <div className="pill-row hp-view-switch" role="group" aria-label="Step">
          {TUNING_KINDS.map((k) => (
            <button key={k.key} type="button" className={`pill${kind === k.key ? ' selected' : ''}`} aria-pressed={kind === k.key}
              title={k.help} onClick={() => reset({ kind: k.key === 'lhs' ? '' : k.key })}>
              {stepLabel(k)}
            </button>
          ))}
        </div>
        <div className="pill-row hp-investigation-pills" role="group" aria-label="Method family">
          {investigations.map((i) => (
            <button key={i.id} type="button" className={`pill${i.id === investigation ? ' selected' : ''}`}
              aria-pressed={i.id === investigation} onClick={() => reset({ investigation: i.id })}>
              {i.label}
            </button>
          ))}
        </div>
        {kind === 'lhs' && (
          <p className="dl-dim">
            Step 0 changes every setting at once over a spread-out sample, on 10 edits: a rough pass that rules out
            settings that fail outright. Each value appears in only a few runs, so read averages as hints.
          </p>
        )}
        {kind === 'factorial' && (
          <p className="dl-dim">
            Step 1 tries each setting at a low and a high value (plus centre runs), crossed with the others: the average
            at a value over everything else is that setting’s main effect, and crossing two settings shows their interaction.
          </p>
        )}
        {error && <p className="form-error">{error}</p>}
        {rows === null && !error && <p className="empty">Loading…</p>}
        {rows && !kindRows.length && <p className="empty">No {TUNING_KINDS.find((k) => k.key === kind).label.toLowerCase()} sweeps here yet. <Link to={`/experiments/investigations/${investigation}`}>Launch one</Link>.</p>}
        {rows && kindRows.length > 0 && (
          <HpExplorer rows={kindRows} kind={kind} investigation={investigation} params={params} setParam={setParam}
            modelLabel={modelLabel} onPromote={promote} promoted={promoted} />
        )}
      </>}
    </div>
  )
}
