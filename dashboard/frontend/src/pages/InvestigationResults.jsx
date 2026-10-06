import { Fragment, useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Bar, BarChart, CartesianGrid, ErrorBar, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api } from '../api.js'
import ResultsSubnav from '../components/ResultsSubnav.jsx'
import SweepFailures from '../components/SweepFailures.jsx'
import FactorPanel from '../components/FactorPanel.jsx'
import { CRITERIA, FACTORS, aggregate, band, duration, factorValue, formatValue, knobFactor, loadThresholds, pct, saveThresholds, valueKey } from '../lib/hparams.js'

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

// Which tuning stage a model is: every stage is its own model value, so runs
// never overwrite each other, but the name alone does not always say it.
function ModelTag({ row }) {
  if (!row.model_variant && !row.model_type) return null
  return (
    <span className={`hp-model-tag is-${row.model_type || 'other'}`} title={`${row.model_family} family, ${row.model_type} model`}>
      {row.model_variant}{row.model_variant && row.model_type && row.model_variant.toLowerCase() !== row.model_type ? ` · ${row.model_type}` : ''}
    </span>
  )
}

// A mean with its spread: "49.2%" over "± 1.3 · n=5", the variance on hover.
function MeanCell({ stat, threshold, strong }) {
  if (!stat || stat.mean == null) return <td className="hp-score is-none">—</td>
  const sdPoints = stat.sd == null ? null : stat.sd * 100
  const title = stat.n > 1
    ? `mean of ${stat.n} runs; standard deviation ${sdPoints.toFixed(2)} points, variance ${(stat.variance * 1e4).toFixed(2)} (points squared)`
    : 'one run, so no spread'
  return (
    <td className={`hp-score is-${band(stat.mean, threshold)}`} title={title}>
      {strong ? <strong>{pct(stat.mean)}</strong> : pct(stat.mean)}
      <div className="hp-spread">{sdPoints == null ? `n=${stat.n}` : `± ${sdPoints.toFixed(1)} · n=${stat.n}`}</div>
    </td>
  )
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

export default function InvestigationResults() {
  const [params, setParams] = useSearchParams()
  const [investigations, setInvestigations] = useState([])
  const [rows, setRows] = useState(null)
  const [error, setError] = useState(null)
  const [thresholds, setThresholds] = useState(loadThresholds)
  const [sort, setSort] = useState({ key: 'reliability', desc: true })
  const [promoted, setPromoted] = useState({})
  const [openLog, setOpenLog] = useState(null)
  const investigation = params.get('investigation') || ''
  const view = params.get('view') === 'failures' ? 'failures' : 'rankings'
  // Which factor is the table's rows ('run' for one row per run), and the
  // values left out of each factor; everything included is averaged.
  const rowsParam = params.get('rows') || 'run'
  const excluded = useMemo(() => {
    try { return JSON.parse(params.get('excl') || '{}') } catch { return {} }
  }, [params])
  const [failureCount, setFailureCount] = useState(null)
  useEffect(() => {
    api.sweepFailures().then((f) => setFailureCount(f.open.length)).catch(() => {})
  }, [view])
  const filters = { sweep: params.get('sweep') || '' }
  const setParam = (key, value) => {
    const next = new URLSearchParams(params)
    if (value) next.set(key, value)
    else next.delete(key)
    setParams(next, { replace: true })
  }
  const setExcluded = (factor, values) => {
    const next = { ...excluded }
    if (values.length) next[factor] = values
    else delete next[factor]
    setParam('excl', Object.keys(next).length ? JSON.stringify(next) : '')
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

  const options = (key) => [...new Set((rows || []).map((r) => r[key]))].sort()
  // Dataset and protocol first, then the rest; swept settings (layers,
  // v_lr, ...) are factors too.
  const knobFactors = useMemo(() => [...new Set((rows || []).flatMap((r) => Object.keys(r.overrides || {})))].sort()
    .map((key) => ({ key: knobFactor(key), label: key, knob: true,
      help: `the ${key} values this investigation swept` })), [rows])
  const ORDER = ['dataset', 'protocol', 'method', 'model', 'model_type', 'model_family']
  const allFactors = [...ORDER.map((k) => FACTORS.find((f) => f.key === k)), ...knobFactors]
  const rowsBy = allFactors.some((f) => f.key === rowsParam) ? rowsParam : 'run'
  const byFactor = allFactors.find((f) => f.key === rowsBy)
  const modelNames = useMemo(() => Object.fromEntries((rows || []).map((r) => [r.model, r])), [rows])
  const display = (key, value) => (key === 'model' && modelNames[value]
    ? `${modelNames[value].model_label}${modelNames[value].model_variant ? ` (${modelNames[value].model_variant})` : ''}`
    : String(value))

  const visible = useMemo(() => (rows || []).filter((r) =>
    (!filters.sweep || r.sweep_id === filters.sweep) &&
    allFactors.every((f) => !(excluded[f.key] || []).includes(factorValue(r, f.key)))),
  [rows, filters.sweep, excluded, allFactors.length])

  const groups = useMemo(() => {
    if (rowsBy === 'run') return null
    const value = (g) => (sort.key === 'time' ? g.time.mean : g.scores[sort.key]?.mean)
    // Everything included is averaged together within a row.
    const list = aggregate(visible, rowsBy, false)
    if (sort.key === 'factor') {
      // In the factor's own order: layer 3 before 4, by number where it is one.
      const order = (g) => (typeof g.raw === 'number' ? g.raw : Array.isArray(g.raw) && typeof g.raw[0] === 'number' ? g.raw[0] : null)
      return list.sort((a, b) => {
        const oa = order(a), ob = order(b)
        const cmp = oa != null && ob != null ? oa - ob : String(a.value).localeCompare(String(b.value), undefined, { numeric: true })
        return sort.desc ? -cmp : cmp
      })
    }
    return list.sort((a, b) => {
      const va = value(a), vb = value(b)
      if (va == null && vb == null) return 0
      if (va == null) return 1
      if (vb == null) return -1
      return sort.desc ? vb - va : va - vb
    })
  }, [visible, rowsBy, sort])

  const sorted = useMemo(() => {
    const value = (r) => (sort.key === 'time' ? (r.wall_sec ?? r.elapsed_sec) : r.scores?.[sort.key])
    return [...visible].sort((a, b) => {
      const va = value(a), vb = value(b)
      if (va == null && vb == null) return 0
      if (va == null) return 1
      if (vb == null) return -1
      return sort.desc ? vb - va : va - vb
    })
  }, [visible, sort])

  // The chart's x-axis is the table-rows factor: a line across a swept
  // setting's values, grouped bars across methods, models or datasets.
  // Each point is the mean of the finished runs at that value with a bar
  // of one standard deviation. With individual runs it falls back to the
  // one swept setting of a single method.
  const chart = useMemo(() => {
    const done = visible.filter((r) => r.state === DONE)
    if (!done.length) return null
    let factor = byFactor
    if (!factor) {
      if (new Set(done.map((r) => r.method)).size !== 1) return null
      const keys = [...new Set(done.flatMap((r) => Object.keys(r.overrides)))]
      if (keys.length !== 1) return null
      factor = { key: knobFactor(keys[0]), label: keys[0], knob: true }
    }
    const byValue = aggregate(done, factor.key, false)
    const points = byValue.map((g) => ({
      x: g.value, raw: g.raw, n: g.finished,
      ...Object.fromEntries(CRITERIA.flatMap((c) => [[c.key, g.scores[c.key].mean], [`${c.key}_sd`, g.scores[c.key].sd ?? 0]])),
    }))
    const order = (p) => (typeof p.raw === 'number' ? p.raw : Array.isArray(p.raw) && typeof p.raw[0] === 'number' ? p.raw[0] : null)
    points.sort((a, b) => {
      const oa = order(a), ob = order(b)
      return oa != null && ob != null ? oa - ob : String(a.x).localeCompare(String(b.x), undefined, { numeric: true })
    })
    return { label: factor.label, key: factor.key, knob: Boolean(factor.knob), points: points.map((p) => ({ ...p, x: display(factor.key, p.x) })),
      averaged: points.some((p) => p.n > 1),
      criteria: CRITERIA.filter((c) => points.some((p) => p[c.key] != null)) }
  }, [visible, byFactor])

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
        {current && <Link to={`/experiments/investigations/${current.id}`} className="btn-plain-small">Launch sweeps for {current.label} →</Link>}
      </div>
      <div className="pill-row hp-view-switch" role="group" aria-label="View">
        <button type="button" className={`pill${view === 'rankings' ? ' selected' : ''}`} aria-pressed={view === 'rankings'}
          onClick={() => setParam('view', '')}>Rankings</button>
        <button type="button" className={`pill${view === 'failures' ? ' selected' : ''}`} aria-pressed={view === 'failures'}
          onClick={() => setParam('view', 'failures')}>
          Failures{failureCount ? <span className="hp-failure-count">{failureCount}</span> : null}
        </button>
      </div>
      {view === 'failures' && <SweepFailures />}
      {view === 'rankings' && <>
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
      {rows && !rows.length && <p className="empty">No sweeps in this investigation yet. <Link to={`/experiments/investigations/${investigation}`}>Launch one</Link>.</p>}
      {rows && rows.length > 0 && (
        <>
          <FactorPanel factors={allFactors} rows={rows} excluded={excluded} onExclude={setExcluded}
            rowsBy={rowsBy} onRowsBy={(key) => setParam('rows', key === 'run' ? '' : key)} display={display} />
          <div className="hp-filters">
            <Filter label="Sweep" options={options('sweep_id')} value={filters.sweep} onChange={(v) => setParam('sweep', v)} />
            <Thresholds thresholds={thresholds} onChange={setThresholds} />
          </div>
          <p className="dl-dim">
            Ranked by reliability by default; check the fluency column (red when it drops) so a setting does not buy
            reliability with fluency. Click a column to rank by it. Scores are on dev records; a dash means the dataset has no such probe or the run has not finished.
          </p>

          {chart && (
            <div className="chart-wrap hp-chart">
              <div className="dl-dim">
                By {chart.knob ? <code>{chart.label}</code> : chart.label.toLowerCase()}
                {chart.averaged ? ': mean of the finished runs at each value, bars ± one standard deviation' : ''}
              </div>
              <ResponsiveContainer width="100%" height={260}>
                {chart.knob ? (
                  <LineChart data={chart.points} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                    <XAxis dataKey="x" stroke="var(--text-dim)" />
                    <YAxis domain={[0, 1]} tickFormatter={(v) => `${Math.round(v * 100)}%`} stroke="var(--text-dim)" />
                    <Tooltip formatter={(v) => pct(v)} contentStyle={{ background: 'var(--panel)', border: '1px solid var(--border)' }} />
                    <Legend />
                    {chart.criteria.map((c, i) => (
                      <Line key={c.key} type="monotone" dataKey={c.key} name={c.label} stroke={LINE_COLORS[i]} dot connectNulls>
                        {chart.averaged && <ErrorBar dataKey={`${c.key}_sd`} width={4} stroke={LINE_COLORS[i]} />}
                      </Line>
                    ))}
                  </LineChart>
                ) : (
                  <BarChart data={chart.points} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                    <XAxis dataKey="x" stroke="var(--text-dim)" />
                    <YAxis domain={[0, 1]} ticks={[0, 0.25, 0.5, 0.75, 1]} tickFormatter={(v) => `${Math.round(v * 100)}%`} stroke="var(--text-dim)" />
                    <Tooltip formatter={(v) => pct(v)} cursor={{ fill: 'var(--panel-2)' }}
                      contentStyle={{ background: 'var(--panel)', border: '1px solid var(--border)' }} />
                    <Legend />
                    {chart.criteria.map((c, i) => (
                      <Bar key={c.key} dataKey={c.key} name={c.label} fill={LINE_COLORS[i]} maxBarSize={36}>
                        {chart.averaged && <ErrorBar dataKey={`${c.key}_sd`} width={4} stroke="var(--text)" />}
                      </Bar>
                    ))}
                  </BarChart>
                )}
              </ResponsiveContainer>
            </div>
          )}

          {groups && (
            <div className="table-wrap">
              <table className="hp-table">
                <thead>
                  <tr>
                    <th className="hp-sortable" title="click to order the rows by this value"
                      onClick={() => setSort((s) => ({ key: 'factor', desc: s.key === 'factor' ? !s.desc : false }))}>
                      {byFactor.knob ? <code>{byFactor.label}</code> : byFactor.label}{sort.key === 'factor' ? (sort.desc ? ' ↓' : ' ↑') : ''}
                    </th>
                    <th title="finished runs averaged, of all runs in the group">Runs</th>
                    {CRITERIA.map((c) => header(c.key, c.label, `${c.help}; mean ± standard deviation`))}
                    {header('time', 'Time', 'mean start-to-finish time')}
                  </tr>
                </thead>
                <tbody>
                  {groups.map((g) => (
                    <tr key={g.key}>
                      <td className="hp-run-cell">
                        {rowsBy === 'model'
                          ? <><strong>{g.rows[0].model_label}</strong> <ModelTag row={g.rows[0]} /></>
                          : <strong>{g.value}</strong>}
                      </td>
                      <td className="hp-over">
                        {g.finished}{g.finished !== g.total ? <span className="dl-dim"> of {g.total}</span> : ''}
                        <div className="dl-dim">
                          {Object.entries(g.over).map(([factor, values]) => `${values.length} ${factor}${values.length === 1 ? '' : 's'}`).join(', ')}
                        </div>
                      </td>
                      {CRITERIA.map((c) => <MeanCell key={c.key} stat={g.scores[c.key]} threshold={thresholds[c.key]} />)}
                      <td className="hp-time" title={g.time.n > 1 ? `standard deviation ${duration(g.time.sd)}` : undefined}>
                        {duration(g.time.mean)}
                        {g.time.sd != null && <div className="hp-spread">± {duration(g.time.sd)}</div>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {!groups && <div className="table-wrap">
            <table className="hp-table">
              <thead>
                <tr>
                  <th>Run</th><th>Setting</th>
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
                    <td className="hp-run-cell">
                      <strong>{r.method}</strong> · {r.model_label || r.model} <ModelTag row={r} />
                      <div className="dl-dim">{r.dataset}{r.protocol ? ` · ${r.protocol}` : ''}</div>
                    </td>
                    <td className="hp-setting">
                      {Object.entries(r.overrides).map(([k, v]) => <div key={k}><code>{k}</code> {formatValue(v)}</div>)}
                      {Object.keys(r.fixed || {}).length > 0 && (
                        <div className="dl-desc" title="held at a non-default value in this sweep">
                          held: {Object.entries(r.fixed).map(([k, v]) => `${k} ${formatValue(v)}`).join(', ')}
                        </div>
                      )}
                    </td>
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
                    <tr className="hp-log-row"><td colSpan={10}><RunLog jobId={r.job_id} /></td></tr>
                  )}
                  </Fragment>
                ))}
              </tbody>
            </table>
          </div>}
        </>
      )}
      </>}
    </div>
  )
}
