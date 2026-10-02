import { useState } from 'react'
import SelectAllCircle from './SelectAllCircle.jsx'
import { groupSelectState } from '../lib/groupSelect.js'
import { factorValue } from '../lib/hparams.js'

const byValue = (a, b) => String(a).localeCompare(String(b), undefined, { numeric: true })

// One row per factor (dataset, protocol, method, model, ...). Opening a
// factor lists all its values to include or leave out; everything included
// is averaged together. One factor is the table's rows: one row per
// included value, averaged over the included values of every other factor.
export default function FactorPanel({ factors, rows, excluded, onExclude, rowsBy, onRowsBy, display }) {
  const [open, setOpen] = useState(() => new Set(['dataset', 'protocol']))
  const toggleOpen = (key) => setOpen((previous) => {
    const next = new Set(previous)
    if (next.has(key)) next.delete(key)
    else next.add(key)
    return next
  })

  return (
    <div className="hp-factor-panel">
      <div className="hp-factor-rows-choice">
        <span className="dl-dim">Table rows</span>
        <button type="button" className={`pill${rowsBy === 'run' ? ' selected' : ''}`} aria-pressed={rowsBy === 'run'}
          onClick={() => onRowsBy('run')} title="one row per run, nothing averaged">Each run</button>
        <span className="dl-dim">or one row per value of a factor below (its <strong>Rows</strong> button)</span>
      </div>
      {factors.map((factor) => {
        const values = [...new Set(rows.map((r) => factorValue(r, factor.key)))].filter((v) => v != null).sort(byValue)
        const out = new Set(excluded[factor.key] || [])
        const selected = values.filter((v) => !out.has(v))
        const isRows = rowsBy === factor.key
        const summary = selected.length === values.length ? `all ${values.length}`
          : `${selected.length} of ${values.length}${selected.length && selected.length <= 3 ? `: ${selected.map((v) => display(factor.key, v)).join(', ')}` : ''}`
        return (
          <div key={factor.key} className={`hp-factor${isRows ? ' is-rows' : ''}${selected.length < values.length ? ' is-filtered' : ''}`}>
            <div className="hp-factor-head">
              <button type="button" className="hp-factor-name" onClick={() => toggleOpen(factor.key)}
                aria-expanded={open.has(factor.key)} title={factor.help}>
                <span className="hp-factor-caret">{open.has(factor.key) ? '▾' : '▸'}</span>
                {factor.knob ? <code>{factor.label}</code> : factor.label}
              </button>
              <span className="dl-dim hp-factor-summary">
                {summary}{isRows ? ' · table rows' : selected.length > 1 ? ' · averaged together' : ''}
              </span>
              <button type="button" className={`pill hp-rows-pill${isRows ? ' selected' : ''}`} aria-pressed={isRows}
                disabled={values.length < 2 && !isRows}
                title={values.length < 2 ? 'only one value here' : `one table row per ${factor.label}`}
                onClick={() => onRowsBy(isRows ? 'run' : factor.key)}>Rows</button>
            </div>
            {open.has(factor.key) && (
              <div className="pill-row hp-factor-values">
                <SelectAllCircle
                  state={groupSelectState(values, selected)}
                  groupLabel={factor.label}
                  disabled={!values.length}
                  onClick={() => onExclude(factor.key, groupSelectState(values, selected) === 'all' ? values : [])} />
                {values.map((v) => {
                  const on = !out.has(v)
                  return (
                    <button key={String(v)} type="button" className={`pill${on ? ' selected' : ''}`} aria-pressed={on}
                      onClick={() => onExclude(factor.key, on ? [...out, v] : [...out].filter((x) => x !== v))}>
                      {display(factor.key, v)}
                    </button>
                  )
                })}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
