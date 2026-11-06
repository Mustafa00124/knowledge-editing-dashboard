import { Fragment, useMemo, useState } from 'react'
import FactorialEffects from './FactorialEffects.jsx'
import LossCell from './LossCell.jsx'
import { formatValue } from '../lib/hparams.js'
import {
  GATE, METRICS, bestValue, bests, formatMetric, formatSetting, grid, knobsOf, marginal, metric, parseMetrics, runGated,
  valueOf,
} from '../lib/hpExplore.js'

const VIEWS = [
  { key: 'factors', label: 'By setting', help: 'one setting’s values as rows, averaged over every other setting' },
  { key: 'runs', label: 'Each run', help: 'one row per run with every setting’s value' },
  { key: 'models', label: 'Across models', help: 'for this method, each model’s best value of every setting' },
]
const byName = (a, b) => String(a).localeCompare(String(b), undefined, { numeric: true })

function Pills({ label, items, value, onChange }) {
  return (
    <div className="pill-row hp-explore-pills" role="group" aria-label={label}>
      <span className="dl-dim hp-explore-pills-label">{label}</span>
      {items.map((it) => (
        <button key={it.key} type="button" className={`pill${it.key === value ? ' selected' : ''}`} aria-pressed={it.key === value}
          title={it.help} onClick={() => onChange(it.key)}>{it.label}</button>
      ))}
    </div>
  )
}

// Metric chips: click to add or remove; the order picked is the column order.
function MetricChips({ selected, onChange }) {
  const toggle = (key) => onChange(selected.includes(key) ? selected.filter((k) => k !== key) : [...selected, key])
  return (
    <div className="pill-row hp-explore-pills" role="group" aria-label="Metrics">
      <span className="dl-dim hp-explore-pills-label">Metrics</span>
      {METRICS.map((m) => {
        const on = selected.includes(m.key)
        return (
          <button key={m.key} type="button" className={`pill hp-metric-chip${on ? ' selected' : ''}`} aria-pressed={on}
            style={{ '--metric': m.color }} title={m.help} onClick={() => toggle(m.key)}>
            <span className="hp-metric-dot" aria-hidden="true" />{m.label}{on && selected.length > 1 ? <sup>{selected.indexOf(m.key) + 1}</sup> : null}
          </button>
        )
      })}
    </div>
  )
}

function Value({ k, group, best }) {
  const s = group?.means[k]
  if (!s || s.mean == null) return <span className="hp-metric-value is-empty">—</span>
  const title = `${metric(k).label}: mean of ${s.n} finished run${s.n === 1 ? '' : 's'}${s.sd != null ? `, sd ${formatMetric(k, s.sd)}` : ''}`
  return (
    <span className={`hp-metric-value${best ? ' is-best' : ''}`} style={{ '--metric': metric(k).color }} title={title}>
      {formatMetric(k, s.mean)}
    </span>
  )
}

// Several metrics in one cell, each in its colour, separated by bars.
function Values({ keys, group, bestOf }) {
  return keys.map((k, i) => (
    <Fragment key={k}>
      {i > 0 && <span className="hp-metric-sep" aria-hidden="true"> | </span>}
      <Value k={k} group={group} best={bestOf[k] === group} />
    </Fragment>
  ))
}

function CentreTag() {
  return <span className="hp-centre-tag" title="The factorial's centre runs set every setting to its middle value at once, so this row is the same few runs for every setting. It checks curvature (does the middle beat both ends?) and is never marked best.">centre run</span>
}

function GateNote() {
  return (
    <p className="dl-dim">
      <strong>Bold</strong> is the best value of each metric among those where at least half the runs keep fluency at
      {' '}{GATE.fluency} and grammar at {GATE.well_formed} of the unedited model; greyed rows fall below that (add
      “Keeps fluency” to see the share). Rows marked “centre run” are the factorial’s
      all-middle configuration, shown for curvature but never marked best. Hover a number for its run count and spread.
    </p>
  )
}

function FactorsView({ rows, knobs, metrics, rowKnob, colKnob, setParam, layers }) {
  if (!knobs.length) return <p className="empty">These runs vary no setting.</p>
  const rk = knobs.includes(rowKnob) ? rowKnob : knobs[0]
  const ck = knobs.includes(colKnob) && colKnob !== rk ? colKnob : 'metrics'
  const knobItems = knobs.map((k) => ({ key: k, label: k }))
  return (
    <>
      <Pills label="Rows" items={knobItems} value={rk} onChange={(k) => setParam('rows', k)} />
      <Pills label="Columns" items={[{ key: 'metrics', label: 'Metrics', help: 'one column per selected metric' },
        ...knobItems.filter((k) => k.key !== rk)]} value={ck} onChange={(k) => setParam('cols', k === 'metrics' ? '' : k)} />
      <GateNote />
      {ck === 'metrics' ? <OneSetting rows={rows} knob={rk} metrics={metrics} layers={layers} />
        : <TwoSettings rows={rows} rowKnob={rk} colKnob={ck} metrics={metrics} layers={layers} />}
    </>
  )
}

// When no value keeps fluency in half its runs, nothing is bold: say why.
function NoneKeeps({ groups }) {
  if (!groups.length || groups.some((g) => !g.gated && !g.centre && g.finished)) return null
  const runs = groups.flatMap((g) => g.rows).filter((r) => r.state === 'COMPLETED')
  const keep = runs.filter((r) => !runGated(r)).length
  return (
    <p className="dl-bar-warning">
      No value keeps fluency in half its runs ({keep} of {runs.length} runs keep it): this method breaks fluency on this
      model across most of the tested range, so nothing is marked best.
    </p>
  )
}

function OneSetting({ rows, knob, metrics, layers }) {
  const groups = marginal(rows, knob)
  const bestOf = bests(groups, metrics)
  return (
    <>
    <NoneKeeps groups={groups} />
    <div className="table-wrap">
      <table className="hp-table hp-explore-table">
        <thead>
          <tr>
            <th><code>{knob}</code></th>
            <th title="finished runs averaged, of all runs at this value">Runs</th>
            {metrics.map((k) => (
              <th key={k} title={metric(k).help}><span className="hp-metric-head" style={{ '--metric': metric(k).color }}>{metric(k).label}</span></th>
            ))}
          </tr>
        </thead>
        <tbody>
          {groups.map((g) => (
            <tr key={g.key} className={g.gated ? 'is-gated' : g.centre ? 'is-centre' : undefined}>
              <td>{formatSetting(knob, g.raw, layers)}{g.centre && <CentreTag />}</td>
              <td className="dl-dim">{g.finished}{g.finished !== g.rows.length ? ` of ${g.rows.length}` : ''}</td>
              {metrics.map((k) => <td key={k}><Value k={k} group={g} best={bestOf[k] === g} /></td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
    </>
  )
}

function TwoSettings({ rows, rowKnob, colKnob, metrics, layers }) {
  const g = grid(rows, rowKnob, colKnob)
  const all = g.rows.flatMap((r) => g.cols.map((c) => g.cell(r, c))).filter(Boolean)
  const bestOf = bests(all, metrics)
  return (
    <>
      <NoneKeeps groups={all} />
      <p className="dl-dim">Each cell: {metrics.map((k) => metric(k).label).join(' | ')}, averaged over the other settings.</p>
      <div className="table-wrap">
        <table className="hp-table hp-explore-table">
          <thead>
            <tr>
              <th><code>{rowKnob}</code> ↓ <code>{colKnob}</code> →</th>
              {g.cols.map((c) => <th key={JSON.stringify(c ?? null)}>{formatSetting(colKnob, c, layers)}</th>)}
            </tr>
          </thead>
          <tbody>
            {g.rows.map((r) => (
              <tr key={JSON.stringify(r ?? null)}>
                <td>{formatSetting(rowKnob, r, layers)}</td>
                {g.cols.map((c) => {
                  const cell = g.cell(r, c)
                  return (
                    <td key={JSON.stringify(c ?? null)} className={cell?.gated ? 'is-gated' : undefined}
                      title={cell ? `${cell.finished} finished of ${cell.rows.length} runs` : 'no run with these values'}>
                      {cell ? <Values keys={metrics} group={cell} bestOf={bestOf} /> : <span className="dl-dim">no runs</span>}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}

function RunsView({ rows, knobs, metrics, layers, onPromote, promoted }) {
  const [sort, setSort] = useState({ key: 'reliability', desc: true })
  const sortValue = (r) => (sort.key.startsWith('knob:') ? valueOf(r, sort.key.slice(5)) : metric(sort.key)?.get(r))
  const sorted = [...rows].sort((a, b) => {
    const va = sortValue(a), vb = sortValue(b)
    if (va == null && vb == null) return 0
    if (va == null) return 1
    if (vb == null) return -1
    const cmp = typeof va === 'number' && typeof vb === 'number' ? va - vb : byName(formatValue(va), formatValue(vb))
    return sort.desc ? -cmp : cmp
  })
  const finished = rows.filter((r) => r.state === 'COMPLETED' && !runGated(r))
  const bestOf = Object.fromEntries(metrics.map((k) => {
    const m = metric(k)
    const xs = finished.map((r) => m.get(r)).filter((v) => v != null)
    return [k, xs.length ? (m.better === 'low' ? Math.min(...xs) : Math.max(...xs)) : null]
  }))
  const head = (key, label, extra) => (
    <th key={key} className="hp-sortable" onClick={() => setSort((s) => ({ key, desc: s.key === key ? !s.desc : !key.startsWith('knob:') }))} {...extra}>
      {label}{sort.key === key ? (sort.desc ? ' ↓' : ' ↑') : ''}
    </th>
  )
  return (
    <>
      <GateNote />
      <div className="table-wrap">
        <table className="hp-table hp-explore-table">
          <thead>
            <tr>
              {metrics.map((k) => head(k, <span className="hp-metric-head" style={{ '--metric': metric(k).color }}>{metric(k).label}</span>, { title: metric(k).help }))}
              {knobs.map((k) => head(`knob:${k}`, <code>{k}</code>))}
              <th title="factorial runs: a corner of the design or a centre run">Point</th>
              <th title="the loss the method optimises, first to last step">Loss</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {sorted.map((r) => (
              <tr key={`${r.sweep_id}|${r.run}`} className={r.state !== 'COMPLETED' || runGated(r) ? 'is-gated' : undefined}>
                {metrics.map((k) => {
                  const v = metric(k).get(r)
                  return (
                    <td key={k}>
                      <span className={`hp-metric-value${v != null && v === bestOf[k] && !runGated(r) ? ' is-best' : ''}`} style={{ '--metric': metric(k).color }}>
                        {r.state === 'COMPLETED' ? formatMetric(k, v) : r.state.toLowerCase()}
                      </span>
                    </td>
                  )
                })}
                {knobs.map((k) => <td key={k}>{formatSetting(k, valueOf(r, k), layers)}</td>)}
                <td className="dl-dim">{r.point || '—'}</td>
                <td><LossCell loss={r.loss} /></td>
                <td>
                  {r.state === 'COMPLETED' && (promoted[r.run]
                    ? <span className="dl-dim">{promoted[r.run]}</span>
                    : <button type="button" className="btn-plain-small" onClick={() => onPromote(r)}
                        title="Write these values into this method's hparams file for this model">Use as main config</button>)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}

// For one method: each model's best value of every setting (most rewrite
// above the gate), with how far the setting moves rewrite. Never averages
// models; layers are shown with their relative depth so models compare.
function ModelsView({ rows, models, modelLabel }) {
  const knobs = knobsOf(rows)
  const per = models.map((m) => ({ model: m, rows: rows.filter((r) => r.model === m) }))
  return (
    <>
      <p className="dl-dim">
        Each cell is that model’s best value of the setting: the most rewrite, averaged over the other settings, among the
        values that keep fluency and grammar. “Moves rewrite” is the range of rewrite over the setting’s values: a small
        range means the setting barely matters for that model. Layers show their relative depth, since models differ in size.
      </p>
      <div className="table-wrap">
        <table className="hp-table hp-explore-table">
          <thead>
            <tr><th>Setting</th>{per.map((p) => <th key={p.model}>{modelLabel(p.model)}</th>)}</tr>
          </thead>
          <tbody>
            {knobs.map((k) => (
              <tr key={k}>
                <td><code>{k}</code></td>
                {per.map((p) => {
                  if (!p.rows.some((r) => k in (r.overrides || {}))) return <td key={p.model} className="dl-dim">not swept</td>
                  const b = bestValue(p.rows, k)
                  const layers = p.rows[0]?.model_layers
                  return (
                    <td key={p.model}>
                      {b.group ? <>
                        <strong>{formatSetting(k, b.group.raw, layers)}</strong>
                        <div className="dl-dim">
                          rewrite {formatMetric('reliability', b.group.means.reliability.mean)}
                          {b.spread != null ? `; moves rewrite ${Math.round(b.spread * 100)} pts` : ''}
                        </div>
                      </> : <span className="dl-dim">no value keeps fluency</span>}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}

// The results of one method family's sweeps of one kind (step): tabs for
// method and model, metric chips, and three views. State lives in the URL.
export default function HpExplorer({ rows, kind, investigation, params, setParam, modelLabel, onPromote, promoted }) {
  const methods = useMemo(() => [...new Set(rows.map((r) => r.method))].sort(byName), [rows])
  const method = methods.includes(params.get('method')) ? params.get('method') : methods[0]
  const ofMethod = useMemo(() => rows.filter((r) => r.method === method), [rows, method])
  const models = useMemo(() => [...new Set(ofMethod.map((r) => r.model))].sort(byName), [ofMethod])
  const model = models.includes(params.get('model')) ? params.get('model') : models[0]
  const view = VIEWS.some((v) => v.key === params.get('xview')) ? params.get('xview') : 'factors'
  const metrics = parseMetrics(params.get('metrics'))
  const sweeps = useMemo(() => [...new Set(ofMethod.filter((r) => r.model === model).map((r) => r.sweep_id))].sort().reverse(), [ofMethod, model])
  const sweep = sweeps.includes(params.get('sweep')) ? params.get('sweep') : ''
  const shown = useMemo(() => ofMethod.filter((r) => r.model === model && (!sweep || r.sweep_id === sweep)), [ofMethod, model, sweep])
  const knobs = useMemo(() => knobsOf(shown), [shown])
  const layers = shown[0]?.model_layers

  if (!rows.length) return null
  const pick = (rowKnob, colKnob) => {
    const next = new URLSearchParams(params)
    next.set('xview', 'factors')
    next.set('rows', rowKnob)
    if (colKnob) next.set('cols', colKnob)
    else next.delete('cols')
    setParam(null, next)
  }
  return (
    <div className="hp-explorer">
      <Pills label="Method" items={methods.map((m) => ({ key: m, label: m }))} value={method}
        onChange={(m) => setParam('method', m)} />
      {view !== 'models' && <Pills label="Model" items={models.map((m) => ({ key: m, label: modelLabel(m) }))} value={model}
        onChange={(m) => setParam('model', m)} />}
      <Pills label="View" items={VIEWS} value={view} onChange={(v) => setParam('xview', v === 'factors' ? '' : v)} />
      {view !== 'models' && <MetricChips selected={metrics} onChange={(keys) => setParam('metrics', keys.join(','))} />}
      {view !== 'models' && sweeps.length > 1 && (
        <label className="hp-filter">Sweep{' '}
          <select value={sweep} onChange={(e) => setParam('sweep', e.target.value)}>
            <option value="">all {sweeps.length} sweeps</option>
            {sweeps.map((id) => <option key={id} value={id}>{id}</option>)}
          </select>
        </label>
      )}
      {metrics.length === 0 && <p className="empty">Pick at least one metric.</p>}
      {view === 'factors' && <FactorsView rows={shown} knobs={knobs} metrics={metrics} rowKnob={params.get('rows')}
        colKnob={params.get('cols')} setParam={setParam} layers={layers} />}
      {view === 'runs' && <RunsView rows={shown} knobs={knobs} metrics={metrics} layers={layers} onPromote={onPromote} promoted={promoted} />}
      {view === 'models' && <ModelsView rows={ofMethod.filter((r) => !sweep || r.sweep_id === sweep)} models={models} modelLabel={modelLabel} />}
      {kind === 'factorial' && view !== 'models' && (
        <details className="hp-effects-details">
          <summary>Which settings matter (effects and interactions, with noise estimates)</summary>
          <p className="dl-dim">Click a setting to make it the table’s rows, or a pair to cross the two.</p>
          <FactorialEffects investigation={investigation} sweepIds={sweep ? [sweep] : sweeps} onPick={pick} />
        </details>
      )}
    </div>
  )
}

