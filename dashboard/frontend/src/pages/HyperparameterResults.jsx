import { Fragment, useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api } from '../api.js'
import ResultsSubnav from '../components/ResultsSubnav.jsx'
import { CRITERIA, band, duration, formatValue, loadThresholds, pct, saveThresholds, valueKey } from '../lib/hparams.js'

const DONE = 'COMPLETED'
const LINE_COLORS = ['var(--accent)', 'var(--good)', 'var(--warn)', 'var(--danger)']

// A run's loss over its optimisation steps (mean over facts), as a tiny line.
function Sparkline({ values, bad }) {
  if (!values || values.length < 2) return null
  const max = Math.max(...values), min = Math.min(...values)
  const span = max - min || 1
  const points = values.map((v, i) => `${(i / (values.length - 1)) * 60},${18 - ((v - min) / span) * 16 - 1}`).join(' ')
  return (
    <svg width="60" height="18" viewBox="0 0 60 18" className={`hp-spark${bad ? ' is-bad' : ''}`} aria-hidden="true">
      <polyline points={points} fill="none" strokeWidth="1.5" />
    </svg>
  )
}

function LossCell({ loss }) {
  if (!loss) return <span className="dl-dim">—</span>
  const label = loss.kind === 'value_vector' ? 'target-vector loss, mean over facts' : 'training loss'
  const fmt = (v) => (v == null ? '?' : v >= 100 ? v.toFixed(0) : v.toFixed(2))
  return (
    <span className="hp-loss" title={`${label}${loss.final_prob != null ? `; new answer's final probability ${loss.final_prob}` : ''}`}>
      <Sparkline values={loss.curve} bad={loss.nan || (loss.last > loss.first * 1.05)} />
      <span className="dl-dim">{loss.nan ? 'NaN' : `${fmt(loss.first)} → ${fmt(loss.last)}`}</span>
    </span>
  )
}

function RunLog({ jobId }) {
  const [log, setLog] = useState(null)
  useEffect(() => {
    api.getExperiment(jobId).then(setLog).catch((e) => setLog({ err_tail: e.message, log_tail: '' }))
  }, [jobId])
  if (!log) return <p className="dl-dim">Loading the job's log…</p>
  return (
    <div className="hp-run-log">
      <div className="dl-dim">Job {jobId}: last lines of its error and output logs</div>
      {log.err_tail && <pre className="dl-log">{log.err_tail}</pre>}
      {log.log_tail && <pre className="dl-log">{log.log_tail}</pre>}
      {!log.err_tail && !log.log_tail && <p className="dl-dim">The logs are empty.</p>}
    </div>
  )
}

// The weakest score, coloured by the threshold of the criterion it came from.
function weakestBand(row, thresholds) {
  const present = CRITERIA.filter((c) => row.scores?.[c.key] != null)
  if (!present.length) return 'none'
  const weakest = present.reduce((a, b) => (row.scores[b.key] < row.scores[a.key] ? b : a))
  return band(row.scores[weakest.key], thresholds[weakest.key])
}

function Filter({ label, options, value, onChange }) {
  if (options.length < 2) return null
  return (
    <label className="hp-filter">{label}{' '}
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        <option value="">all</option>
        {options.map((o) => <option key={o} value={o}>{o}</option>)}
      </select>
    </label>
  )
}

function Thresholds({ thresholds, onChange }) {
  const [open, setOpen] = useState(false)
  const set = (key, side, value) => {
    const next = { ...thresholds, [key]: { ...thresholds[key], [side]: Number(value) } }
    onChange(next)
    saveThresholds(next)
  }
  return (
    <div className="hp-thresholds">
      <button type="button" className="btn-plain-small" onClick={() => setOpen((o) => !o)}>
        {open ? 'Hide colour thresholds' : 'Colour thresholds'}
      </button>
      {open && (
        <div className="hp-threshold-grid">
          <span className="dl-dim">Colours only; nothing is hidden. Green at or above, red below.</span>
          {CRITERIA.map((c) => (
            <div key={c.key} className="hp-threshold-row">
              <span>{c.label}</span>
              <label>green ≥ <input type="number" step="0.05" min="0" max="1" value={thresholds[c.key].good}
                onChange={(e) => set(c.key, 'good', e.target.value)} /></label>
              <label>red &lt; <input type="number" step="0.05" min="0" max="1" value={thresholds[c.key].bad}
                onChange={(e) => set(c.key, 'bad', e.target.value)} /></label>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function HyperparameterResults() {
  const [params, setParams] = useSearchParams()
  const [investigations, setInvestigations] = useState([])
  const [rows, setRows] = useState(null)
  const [error, setError] = useState(null)
  const [thresholds, setThresholds] = useState(loadThresholds)
  const [sort, setSort] = useState({ key: 'worst', desc: true })
  const [promoted, setPromoted] = useState({})
  const [openLog, setOpenLog] = useState(null)
  const investigation = params.get('investigation') || ''
  const filters = { method: params.get('method') || '', model: params.get('model') || '',
    dataset: params.get('dataset') || '', sweep: params.get('sweep') || '' }
  const setParam = (key, value) => {
    const next = new URLSearchParams(params)
    if (value) next.set(key, value)
    else next.delete(key)
    setParams(next, { replace: true })
  }

  useEffect(() => {
    api.investigations().then((all) => {
      setInvestigations(all)
      if (!investigation && all.length) setParam('investigation', all[0].id)
    }).catch((e) => setError(e.message))
  }, [])

  useEffect(() => {
    if (!investigation) return
    let live = true
    setRows(null)
    const load = () => api.sweepResults(investigation).then((r) => { if (live) setRows(r) }).catch((e) => setError(e.message))
    load()
    const timer = setInterval(load, 20000)
    return () => { live = false; clearInterval(timer) }
  }, [investigation])

  const options = (key) => [...new Set((rows || []).map((r) => r[key]))].sort()
  const visible = useMemo(() => (rows || []).filter((r) =>
    (!filters.method || r.method === filters.method) && (!filters.model || r.model === filters.model) &&
    (!filters.dataset || r.dataset === filters.dataset) && (!filters.sweep || r.sweep_id === filters.sweep)),
  [rows, filters.method, filters.model, filters.dataset, filters.sweep])

  const sorted = useMemo(() => {
    const value = (r) => (sort.key === 'worst' ? r.worst : sort.key === 'time' ? (r.wall_sec ?? r.elapsed_sec) : r.scores?.[sort.key])
    return [...visible].sort((a, b) => {
      const va = value(a), vb = value(b)
      if (va == null && vb == null) return 0
      if (va == null) return 1
      if (vb == null) return -1
      return sort.desc ? vb - va : va - vb
    })
  }, [visible, sort])

  // A line chart when the visible rows vary one setting for a single method,
  // model and dataset: the metrics across that setting's values.
  const chart = useMemo(() => {
    const done = visible.filter((r) => r.state === DONE)
    if (!done.length) return null
    if (new Set(done.map((r) => `${r.method}|${r.model}|${r.dataset}`)).size !== 1) return null
    const keys = [...new Set(done.flatMap((r) => Object.keys(r.overrides)))]
    if (keys.length !== 1) return null
    const knob = keys[0]
    const points = done.map((r) => ({ x: formatValue(r.overrides[knob]), raw: r.overrides[knob],
      ...Object.fromEntries(CRITERIA.map((c) => [c.key, r.scores[c.key]])) }))
    points.sort((a, b) => (typeof a.raw === 'number' && typeof b.raw === 'number' ? a.raw - b.raw
      : String(valueKey(a.raw)).localeCompare(String(valueKey(b.raw)), undefined, { numeric: true })))
    return { knob, points, criteria: CRITERIA.filter((c) => points.some((p) => p[c.key] != null)) }
  }, [visible])

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

  const header = (key, label, help) => (
    <th key={key} className="hp-sortable" title={help}
      onClick={() => setSort((s) => ({ key, desc: s.key === key ? !s.desc : true }))}>
      {label}{sort.key === key ? (sort.desc ? ' ↓' : ' ↑') : ''}
    </th>
  )
  const current = investigations.find((i) => i.id === investigation)

  return (
    <div>
      <ResultsSubnav />
      <div className="page-header">
        <h1>Hyperparameter results</h1>
        {current && <Link to={`/hyperparameters/${current.id}`} className="btn-plain-small">Launch sweeps for {current.label} →</Link>}
      </div>
      <div className="pill-row hp-investigation-pills" role="group" aria-label="Investigation">
        {investigations.map((i) => (
          <button key={i.id} type="button" className={`pill${i.id === investigation ? ' selected' : ''}`}
            aria-pressed={i.id === investigation}
            onClick={() => { const next = new URLSearchParams(); next.set('investigation', i.id); setParams(next, { replace: true }) }}>
            {i.label}
          </button>
        ))}
      </div>
      {error && <p className="form-error">{error}</p>}
      {rows === null && !error && <p className="empty">Loading…</p>}
      {rows && !rows.length && <p className="empty">No sweeps in this investigation yet. <Link to={`/hyperparameters/${investigation}`}>Launch one</Link>.</p>}
      {rows && rows.length > 0 && (
        <>
          <div className="hp-filters">
            <Filter label="Method" options={options('method')} value={filters.method} onChange={(v) => setParam('method', v)} />
            <Filter label="Model" options={options('model')} value={filters.model} onChange={(v) => setParam('model', v)} />
            <Filter label="Dataset" options={options('dataset')} value={filters.dataset} onChange={(v) => setParam('dataset', v)} />
            <Filter label="Sweep" options={options('sweep_id')} value={filters.sweep} onChange={(v) => setParam('sweep', v)} />
            <Thresholds thresholds={thresholds} onChange={setThresholds} />
          </div>
          <p className="dl-dim">
            Ranked by the weakest criterion by default, so a setting cannot rank well by giving one up. Click a column to
            rank by it. Scores are on dev records; a dash means the dataset has no such probe or the run has not finished.
          </p>

          {chart && (
            <div className="chart-wrap hp-chart">
              <div className="dl-dim">Across <code>{chart.knob}</code></div>
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={chart.points} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis dataKey="x" stroke="var(--text-dim)" />
                  <YAxis domain={[0, 1]} tickFormatter={(v) => `${Math.round(v * 100)}%`} stroke="var(--text-dim)" />
                  <Tooltip formatter={(v) => pct(v)} contentStyle={{ background: 'var(--panel)', border: '1px solid var(--border)' }} />
                  <Legend />
                  {chart.criteria.map((c, i) => (
                    <Line key={c.key} type="monotone" dataKey={c.key} name={c.label} stroke={LINE_COLORS[i]} dot connectNulls />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          <div className="table-wrap">
            <table className="hp-table">
              <thead>
                <tr>
                  <th>Method</th><th>Model</th><th>Dataset</th><th>Setting</th>
                  {header('worst', 'Weakest', 'the lowest of the four criteria this run has')}
                  {CRITERIA.map((c) => header(c.key, c.label, c.help))}
                  <th title="the loss the method optimises, first to last step">Loss</th>
                  {header('time', 'Time', 'start to finish, model load included; running jobs show time so far')}
                  <th>Status</th><th />
                </tr>
              </thead>
              <tbody>
                {sorted.map((r) => (
                  <Fragment key={`${r.sweep_id}/${r.run}`}>
                  <tr>
                    <td>{r.method}</td>
                    <td>{r.model}</td>
                    <td>{r.dataset}</td>
                    <td className="hp-setting">
                      {Object.entries(r.overrides).map(([k, v]) => <div key={k}><code>{k}</code> {formatValue(v)}</div>)}
                      {Object.keys(r.fixed || {}).length > 0 && (
                        <div className="dl-desc" title="held at a non-default value in this sweep">
                          held: {Object.entries(r.fixed).map(([k, v]) => `${k} ${formatValue(v)}`).join(', ')}
                        </div>
                      )}
                    </td>
                    <td className={`hp-score is-${weakestBand(r, thresholds)}`}><strong>{pct(r.worst)}</strong></td>
                    {CRITERIA.map((c) => (
                      <td key={c.key} className={`hp-score is-${band(r.scores?.[c.key], thresholds[c.key])}`}
                        title={c.key === 'fluency' && r.fluency_raw != null ? `n-gram entropy ${r.fluency_raw.toFixed(1)} vs ${r.fluency_baseline?.toFixed(1)} unedited` : undefined}>
                        {pct(r.scores?.[c.key])}
                      </td>
                    ))}
                    <td><LossCell loss={r.loss} /></td>
                    <td className="hp-time" title={r.wall_sec != null
                      ? `editing and evaluation ${duration(r.total_sec)}${r.records ? `, about ${(r.total_sec / r.records).toFixed(1)}s per record` : ''}; the rest is loading the model`
                      : 'time so far, from the scheduler'}>
                      {r.wall_sec != null ? duration(r.wall_sec) : r.elapsed_sec ? <span className="dl-dim">{duration(r.elapsed_sec)} so far</span> : '—'}
                      {r.wall_sec != null && r.records ? <div className="dl-dim">{(r.total_sec / r.records).toFixed(1)}s / record</div> : null}
                    </td>
                    <td className="hp-status">
                      <div className="dl-dim">{r.state === DONE ? `${r.records} records` : r.state.toLowerCase()}</div>
                      {(r.flags || []).map((f) => <span key={f.text} className={`hp-flag is-${f.level}`}>{f.text}</span>)}
                      {r.error && <div className="hp-error" title={r.error}>{r.error}</div>}
                      <button type="button" className="btn-plain-small"
                        onClick={() => setOpenLog(openLog === r.run ? null : r.run)}>{openLog === r.run ? 'Hide log' : 'Log'}</button>
                    </td>
                    <td>
                      {r.state === DONE && (promoted[r.run]
                        ? <span className="dl-dim">{promoted[r.run]}</span>
                        : <button type="button" className="btn-plain-small" onClick={() => promote(r)}
                            title="Write these values into this method's hparams file for this model">Use as main config</button>)}
                    </td>
                  </tr>
                  {openLog === r.run && (
                    <tr className="hp-log-row"><td colSpan={12}><RunLog jobId={r.job_id} /></td></tr>
                  )}
                  </Fragment>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}
