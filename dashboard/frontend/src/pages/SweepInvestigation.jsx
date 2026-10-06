import ExperimentsSubnav from '../components/ExperimentsSubnav.jsx'
import InvestigationProgress from '../components/InvestigationProgress.jsx'
import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api.js'
import DatasetField from '../components/DatasetField.jsx'
import ModelField from '../components/ModelField.jsx'
import LaunchBlockedNotice from '../components/LaunchBlockedNotice.jsx'
import HeldConstant from '../components/HeldConstant.jsx'
import SweepCard from '../components/SweepCard.jsx'
import SweepDetailModal from '../components/SweepDetailModal.jsx'
import useCapabilities, { launchBlockers } from '../lib/useCapabilities.js'
import { GROUP_LABEL, STABILITY_LABEL, duration, formatValue, parseValue, valueKey } from '../lib/hparams.js'

const EXPERIMENT = 'run_experiment'

function KnobEditor({ knob, model, values, onChange }) {
  const [custom, setCustom] = useState('')
  const suggestions = knob.suggestions[model] || []
  const current = knob.defaults[model]
  const chosen = values || []
  const chosenKeys = new Set(chosen.map(valueKey))
  const options = [...suggestions]
  for (const v of chosen) if (!options.some((o) => valueKey(o) === valueKey(v))) options.push(v)

  const toggle = (value) => onChange(chosenKeys.has(valueKey(value))
    ? chosen.filter((v) => valueKey(v) !== valueKey(value))
    : [...chosen, value])

  function addCustom(e) {
    e.preventDefault()
    const value = parseValue(custom)
    if (value === undefined) return
    if (!chosenKeys.has(valueKey(value))) onChange([...chosen, value])
    setCustom('')
  }

  return (
    <div className="hp-knob">
      <div className="hp-knob-head">
        <code>{knob.key}</code>
        <span className="dl-dim">now {current === undefined ? 'not set for this model' : formatValue(current)}</span>
        {knob.tuned?.[model] && <span className="badge badge-installed" title={`from sweep ${knob.tuned[model].sweep}`}>tuned</span>}
        <span className="hp-stability" title={STABILITY_LABEL[knob.stability]}>{knob.stability?.replace('_', ' ')}</span>
      </div>
      {knob.note && <div className="dl-desc">{knob.note}</div>}
      <div className="pill-row hp-values">
        {options.map((value) => (
          <button key={valueKey(value)} type="button"
            className={`pill${chosenKeys.has(valueKey(value)) ? ' selected' : ''}${valueKey(value) === valueKey(current) ? ' hp-current' : ''}`}
            aria-pressed={chosenKeys.has(valueKey(value))} onClick={() => toggle(value)}
            title={valueKey(value) === valueKey(current) ? 'the current setting' : undefined}>
            {formatValue(value)}
          </button>
        ))}
        <form onSubmit={addCustom} className="hp-custom">
          <input value={custom} onChange={(e) => setCustom(e.target.value)} placeholder="other value, e.g. 0.2 or [4,5]" />
        </form>
      </div>
      {!chosen.length && <div className="dl-dim">Not swept: stays at the current setting.</div>}
    </div>
  )
}

// Each model's traced peak (Knowledge localisation, per model) beside the
// layers each method edits today. The suggestions below add the peak, so a
// sweep checks the trace against what editing actually does; an untraced
// model gets suggestions around its default only.
function TracedPeaks({ investigation }) {
  const layered = investigation.methods
    .map((m) => ({ ...m, knob: m.knobs.find((k) => k.key === 'layers') }))
    .filter((m) => m.knob)
  const models = [...new Set(layered.flatMap((m) => Object.keys(m.knob.defaults)))]
  const traced = investigation.traced
  return (
    <div className="card hp-tool-card">
      <div className="card-title">
        Traced peak per model · <Link to="/experiments/investigations/causal_tracing">Knowledge localisation →</Link>
      </div>
      <div className="card-sub">
        Where each model recalls facts, measured once per model, beside the layers each method edits today.
        {' '}{models.filter((m) => !traced[m]).length} of {models.length} models are untraced; their suggestions
        centre on the default only.
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr><th>Model</th><th>Traced peak</th>{layered.map((m) => <th key={m.method}>{m.label}</th>)}</tr>
          </thead>
          <tbody>
            {models.map((model) => (
              <tr key={model}>
                <td>{model}</td>
                <td>
                  {traced[model]
                    ? `${traced[model].peak_layer} (${traced[model].n_prompts} prompt${traced[model].n_prompts === 1 ? '' : 's'})`
                    : <span className="dl-dim">untraced</span>}
                </td>
                {layered.map((m) => (
                  <td key={m.method}>{m.knob.defaults[model] !== undefined ? formatValue(m.knob.defaults[model]) : '—'}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default function SweepInvestigation() {
  const { investigationId } = useParams()
  const [investigation, setInvestigation] = useState(null)
  const [expType, setExpType] = useState(null)
  const [sweeps, setSweeps] = useState([])
  const [showHidden, setShowHidden] = useState(false)
  const [hiddenCount, setHiddenCount] = useState(0)
  const [error, setError] = useState(null)
  const [models, setModels] = useState([])
  const [dataPaths, setDataPaths] = useState([])
  const [methods, setMethods] = useState({})
  const [editMode, setEditMode] = useState(null)
  const [dsSize, setDsSize] = useState('full')
  const [label, setLabel] = useState('')
  const [seed, setSeed] = useState(0)
  const [held, setHeld] = useState({})
  // Held-constant settings changed for this sweep: method -> model -> key -> value.
  const [fixed, setFixed] = useState({})
  const [detailFor, setDetailFor] = useState(null)
  const [estimate, setEstimate] = useState(null)
  const [launching, setLaunching] = useState(false)
  const [message, setMessage] = useState(null)
  const capabilities = useCapabilities()
  const blockers = launchBlockers(capabilities, EXPERIMENT)

  useEffect(() => {
    Promise.all([api.investigations(), api.experimentTypes()]).then(([all, types]) => {
      const inv = all.find((i) => i.id === investigationId)
      if (!inv) throw new Error(`no investigation called ${investigationId}`)
      const exp = types.find((t) => t.name === EXPERIMENT)
      setInvestigation(inv)
      setExpType(exp)
      const field = (name) => exp.fields.find((f) => f.name === name)
      const modelDefault = field('model').default
      const dataDefault = field('data_path').default
      setModels(field('model').options.some((o) => o.value === modelDefault && o.available !== false) ? [modelDefault] : [])
      const dataOk = field('data_path').benchmarks.some((b) => b.subsets.some((s) => s.value === dataDefault && s.available !== false))
      // An investigation meant to run across datasets starts with all of them.
      setDataPaths(inv.default_datasets?.length ? inv.default_datasets : dataOk ? [dataDefault] : [])
      setEditMode(field('edit_mode').default)
    }).catch((e) => setError(e.message))
  }, [investigationId])

  // Hidden sweeps are only loaded (and polled) when shown.
  const refreshSweeps = () => {
    api.sweeps(investigationId, showHidden).then(setSweeps).catch(() => {})
    if (!showHidden) api.hiddenSweepCount(investigationId).then((c) => setHiddenCount(c.hidden)).catch(() => {})
  }
  useEffect(() => {
    refreshSweeps()
    const timer = setInterval(refreshSweeps, 8000)
    return () => clearInterval(timer)
  }, [investigationId, showHidden])
  async function clearFinishedSweeps() {
    try {
      await api.clearFinishedSweeps(investigationId)
    } catch (e) {
      setMessage({ ok: false, text: e.message })
    }
    refreshSweeps()
  }

  const primaryModel = models[0]
  const field = (name) => expType?.fields.find((f) => f.name === name)
  const spec = useMemo(() => ({
    investigation: investigationId,
    methods: Object.fromEntries(Object.entries(methods)
      .map(([m, knobs]) => [m, Object.fromEntries(Object.entries(knobs).filter(([, v]) => v.length))])
      .filter(([, knobs]) => Object.keys(knobs).length)),
    models, data_paths: dataPaths, ds_size: dsSize, edit_mode: editMode || 'batch', seed, label,
    fixed: Object.fromEntries(Object.entries(fixed).filter(([m]) => methods[m])),
  }), [investigationId, methods, models, dataPaths, dsSize, editMode, label, seed, fixed])

  const methodList = Object.keys(methods).sort().join(',')
  useEffect(() => {
    if (!methodList || !models.length) { setHeld({}); return }
    let live = true
    api.heldSettings(investigationId, methodList.split(','), models).then((h) => { if (live) setHeld(h) }).catch(() => {})
    return () => { live = false }
  }, [investigationId, methodList, models.join(',')])

  function fix(method, model, key, value) {
    setFixed((previous) => {
      const forModel = { ...(previous[method]?.[model] || {}) }
      if (value === undefined) delete forModel[key]
      else forModel[key] = value
      return { ...previous, [method]: { ...(previous[method] || {}), [model]: forModel } }
    })
  }
  const ready = Object.keys(spec.methods).length > 0 && models.length > 0 && dataPaths.length > 0

  // Re-estimate a moment after the selection settles.
  const estimateTimer = useRef(null)
  useEffect(() => {
    clearTimeout(estimateTimer.current)
    if (!ready) { setEstimate(null); return }
    estimateTimer.current = setTimeout(() => {
      api.estimateSweep(spec).then(setEstimate).catch((e) => setEstimate({ error: e.message }))
    }, 400)
    return () => clearTimeout(estimateTimer.current)
  }, [spec, ready])

  function toggleMethod(method) {
    setMethods((previous) => {
      if (previous[method]) {
        const { [method]: _, ...rest } = previous
        return rest
      }
      const entry = investigation.methods.find((m) => m.method === method)
      // Start with the first setting swept over its suggestions; the others
      // stay at their current values until picked.
      const first = entry.knobs.find((k) => k.suggestions[primaryModel]?.length)
      return { ...previous, [method]: first ? { [first.key]: first.suggestions[primaryModel] } : {} }
    })
  }

  async function launch() {
    setLaunching(true)
    setMessage(null)
    try {
      const result = await api.launchSweep(spec)
      setMessage({ ok: true, text: `Launched ${result.submitted} run${result.submitted === 1 ? '' : 's'}`
        + (result.skipped.length ? `; ${result.skipped.length} skipped` : '')
        + (result.errors.length ? `; ${result.errors.length} could not start (${result.errors[0].error})` : ''),
        sweep: result.sweep_id })
      refreshSweeps()
    } catch (e) {
      setMessage({ ok: false, text: e.message.replace(/^\d+ [^:]*: /, '').replace(/^\{"detail":"(.*)"\}$/, '$1') })
    } finally {
      setLaunching(false)
    }
  }

  if (error) return <div><ExperimentsSubnav /><div className="page-header"><h1>Investigations</h1></div><p className="form-error">{error}</p></div>
  if (!investigation || !expType) return <div><ExperimentsSubnav /><div className="page-header"><h1>Investigations</h1></div><p className="empty">Loading…</p></div>

  const editField = field('edit_mode')

  return (
    <div className="hp-investigation">
      <ExperimentsSubnav />
      <div className="hp-breadcrumb"><Link to="/experiments/investigations">Investigations</Link> / {investigation.label}</div>
      <div className="page-header">
        <h1>{investigation.label}</h1>
        <Link to={`/results/investigations?investigation=${investigation.id}`} className="btn-plain-small">Results for this investigation →</Link>
      </div>
      <p className="hp-intro">
        <span className="badge">{GROUP_LABEL[investigation.group]}</span> {investigation.question}
      </p>
      {investigation.cost_note && <p className="dl-dim">{investigation.cost_note}</p>}

      {investigation.traced && <TracedPeaks investigation={investigation} />}

      <LaunchBlockedNotice blockers={blockers} />

      <InvestigationProgress investigation={investigation.id} />

      <section className="dl-section">
        <h2 className="section-heading">1. Methods and values</h2>
        <p className="dl-section-intro">
          Only methods with a setting of this kind are listed. Pick the values to try; every combination of a method’s
          picked values is one run per model and dataset. Suggestions are centred on the current setting for {primaryModel || 'the first selected model'}.
        </p>
        {investigation.methods.map((m) => (
          <div key={m.method} className={`hp-method${methods[m.method] ? ' is-on' : ''}${m.available ? '' : ' is-off'}`}>
            <label className="hp-method-head">
              <input type="checkbox" checked={Boolean(methods[m.method])} disabled={!m.available || !primaryModel}
                onChange={() => toggleMethod(m.method)} />
              <strong>{m.label}</strong>
              <span className="dl-dim">{m.knobs.map((k) => k.key).join(', ')}</span>
            </label>
            {!m.available && m.note && <div className="dl-desc">{m.note}</div>}
            {methods[m.method] && m.knobs.map((knob) => (
              <KnobEditor key={knob.key} knob={knob} model={primaryModel} values={methods[m.method][knob.key]}
                onChange={(values) => setMethods((p) => ({ ...p, [m.method]: { ...p[m.method], [knob.key]: values } }))} />
            ))}
          </div>
        ))}
      </section>

      <section className="dl-section">
        <h2 className="section-heading">2. Models</h2>
        <ModelField field={{ ...field('model'), sweepable: true }} value={models} onChange={setModels} />
      </section>

      <section className="dl-section">
        <h2 className="section-heading">3. Datasets (dev records)</h2>
        <p className="dl-section-intro">Each subset’s 100 dev records (fewer for small subsets). Test records are never used here.</p>
        <DatasetField field={{ ...field('data_path'), sweepable: true }} value={dataPaths} onChange={setDataPaths} />
      </section>

      <section className="dl-section">
        <h2 className="section-heading">4. Protocol</h2>
        <div className="hp-protocol">
          <label>Editing protocol{' '}
            <select value={editMode || ''} onChange={(e) => setEditMode(e.target.value)}>
              {(editField?.options || []).map((o) => {
                const value = typeof o === 'object' ? o.value : o
                return <option key={value} value={value}>{typeof o === 'object' ? o.label || value : value}</option>
              })}
            </select>
          </label>
          <label>Records per run{' '}
            <select value={dsSize} onChange={(e) => setDsSize(e.target.value)}>
              <option value="full">all dev records (up to 100)</option>
              <option value="50">50</option>
              <option value="20">20</option>
            </select>
          </label>
          <label>Seed{' '}
            <select value={seed} onChange={(e) => setSeed(Number(e.target.value))}>
              {[0, 1, 2, 3].map((v) => <option key={v} value={v}>{v}</option>)}
            </select>
          </label>
          <label>Label{' '}
            <input value={label} onChange={(e) => setLabel(e.target.value)} placeholder="optional, e.g. first pass" />
          </label>
        </div>
        <p className="dl-dim">Use the protocol the main experiments will use: settings tuned under single edits do not transfer to sequential ones.</p>
      </section>

      <HeldConstant
        held={held}
        swept={Object.fromEntries(Object.entries(methods).map(([m, knobs]) => [m, Object.keys(knobs).filter((k) => knobs[k].length)]))}
        fixed={fixed}
        onFix={fix}
        models={models}
        runSettings={[
          ['Records', `dev split only, ${dsSize === 'full' ? 'all dev records (up to 100)' : `${dsSize} per subset`}; test records are never used`],
          ['Editing protocol', editMode || 'batch'],
          ['Seed', String(seed)],
          ['Evaluation', 'before editing and once at the end; Original scorer (token match), fluency on every run'],
          ['Models', models.join(', ') || 'none chosen'],
          ['Datasets', `${dataPaths.length} subset${dataPaths.length === 1 ? '' : 's'}`],
        ]}
      />

      <div className={`dl-bar${ready ? ' has-selection' : ''}`}>
        <div className="dl-bar-summary">
          {!ready && 'Pick at least one method with values, one model and one dataset.'}
          {ready && estimate && !estimate.error && (
            <>
              <strong>{estimate.runs}</strong> run{estimate.runs === 1 ? '' : 's'} · about <strong>{estimate.gpu_hours}</strong> GPU-hours
              {estimate.missing_stats.length > 0 && <> · computes covariance statistics for {estimate.missing_stats.length} layer{estimate.missing_stats.length === 1 ? '' : 's'} first</>}
              {estimate.skipped.length > 0 && (
                <div className="dl-bar-warning">
                  Skipped: {estimate.skipped.slice(0, 3).map((s) => `${s.method} on ${s.model}${s.data_path ? ` / ${s.data_path.split('/').pop()}` : ''} (${s.reason})`).join('; ')}
                  {estimate.skipped.length > 3 ? `; and ${estimate.skipped.length - 3} more` : ''}
                </div>
              )}
            </>
          )}
          {ready && estimate?.error && <div className="dl-bar-warning">{estimate.error}</div>}
          {message && (
            <div className={message.ok ? 'dl-bar-ok' : 'dl-bar-warning'} role="status">
              {message.text}
              {message.sweep && <> · <Link to={`/results/investigations?investigation=${investigation.id}`}>see results</Link></>}
            </div>
          )}
        </div>
        <button type="button" className="btn-primary" onClick={launch}
          disabled={!ready || launching || blockers.length > 0 || !estimate?.runs}>
          {launching ? 'Launching…' : 'Launch sweep'}
        </button>
      </div>

      <section className="dl-section">
        <div className="dl-section-head">
          <h2 className="section-heading">Sweeps in this investigation</h2>
          <span className="dl-task-controls">
            {(showHidden ? sweeps.some((s) => s.hidden) : hiddenCount > 0) && (
              <button type="button" className="btn-plain-small" onClick={() => setShowHidden((v) => !v)}>
                {showHidden ? 'Leave out hidden sweeps' : `Show ${hiddenCount} hidden`}
              </button>
            )}
            {sweeps.some((s) => !s.hidden && !s.active) && (
              <button type="button" className="btn-plain-small" onClick={clearFinishedSweeps}
                title="Hide every finished sweep; results stay on Results · Investigations">
                Clear finished
              </button>
            )}
          </span>
        </div>
        {!sweeps.some((s) => !s.hidden) && <p className="dl-dim">{sweeps.length || hiddenCount ? 'None showing.' : 'None yet.'}</p>}
        <ul className="dl-tasks">
          {sweeps.filter((s) => showHidden || !s.hidden).map((s) => (
            <SweepCard key={s.id} sweep={s}
              onDetails={() => setDetailFor(s.id)}
              onCancel={() => api.cancelSweep(investigation.id, s.id).then(refreshSweeps)}
              onRerun={() => api.rerunFailedSweep(investigation.id, s.id).then(refreshSweeps)}
              onHide={() => api.hideSweep(investigation.id, s.id).then(refreshSweeps).catch((e) => setMessage({ ok: false, text: e.message }))}
              onUnhide={() => api.hideSweep(investigation.id, s.id, false).then(refreshSweeps).catch((e) => setMessage({ ok: false, text: e.message }))} />
          ))}
        </ul>
        {detailFor && <SweepDetailModal investigation={investigation.id} sweepId={detailFor} onClose={() => setDetailFor(null)} />}
      </section>
    </div>
  )
}
