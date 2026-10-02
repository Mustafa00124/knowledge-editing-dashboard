import { Fragment, useState } from 'react'
import { formatMetricValue, metricLabel } from '../lib/formatMetric.js'
import { groupSelectState } from '../lib/groupSelect.js'

// Which config knobs can become a table axis, in offer order. Anything not
// picked as the row or column axis gets averaged over (e.g. pick
// method x model and every lr/seed you swept collapses into one cell's
// mean; pick lr x method instead and it's model/seed that collapse).
const AXIS_FIELDS = [
  { key: 'method', label: 'Method' },
  { key: 'model', label: 'Model' },
  { key: 'protocol', label: 'Protocol' },
  { key: 'lr', label: 'Learning rate' },
  { key: 'num_steps', label: 'Num steps' },
  { key: 'ds_size', label: 'Dataset size' },
  { key: 'seed', label: 'Seed' },
]

function formatAxisValue(field, value, methodMeta, modelMeta) {
  if (field === 'method') return methodMeta[value]?.label || value
  if (field === 'model') return modelMeta[value]?.label || value
  if (field === 'lr' && typeof value === 'number') return value.toExponential(0)
  return String(value)
}

function AxisTabs({ label, value, onChange }) {
  return (
    <div className="axis-selector">
      <span className="axis-selector-label">{label}</span>
      <div className="axis-tabs" role="group" aria-label={`${label} factor`}>
        {AXIS_FIELDS.map((f) => (
          <button
            key={f.key}
            type="button"
            className={`subnav-tab${value === f.key ? ' active' : ''}`}
            aria-pressed={value === f.key}
            onClick={() => onChange(f.key)}
          >
            {f.label}
          </button>
        ))}
      </div>
    </div>
  )
}

export default function ResultsTable({
  rows,
  metricKey,
  displayMetricKey = metricKey,
  methodMeta,
  modelMeta,
  lowerIsBetter,
  selectMode = false,
  selected = [],
  onToggleRuns,
}) {
  const [rowField, setRowField] = useState('method')
  const [colField, setColField] = useState('model')

  // Selecting the factor already used on the other axis swaps the two,
  // keeping every tab clickable while preserving a meaningful table.
  function selectRow(field) {
    if (field === colField) setColField(rowField)
    setRowField(field)
  }

  function selectColumn(field) {
    if (field === rowField) setRowField(colField)
    setColField(field)
  }

  if (!rows.length) return <p className="dataset-missing">No results for this dataset yet.</p>

  const rowValues = [...new Set(rows.map((r) => r[rowField]))]
  const colValues = [...new Set(rows.map((r) => r[colField]))]

  // Every run at a coordinate, whatever it measured. Deliberately not the
  // same filter as cell(): a run whose locality came back null still has a
  // directory to archive, so it has to stay selectable while you are looking
  // at the Locality tab.
  const runsAt = (rowVal, colVal) =>
    rows.filter((r) => r[rowField] === rowVal && r[colField] === colVal).map((r) => r.run)

  const cell = (rowVal, colVal) => {
    const matches = rows.filter((r) => r[rowField] === rowVal && r[colField] === colVal && typeof r[metricKey] === 'number')
    if (!matches.length) return null
    const mean = matches.reduce((sum, r) => sum + r[metricKey], 0) / matches.length
    return { mean, matches }
  }

  const bestInRow = (rowVal) => {
    let best = null
    for (const colVal of colValues) {
      const c = cell(rowVal, colVal)
      if (!c) continue
      if (!best || (lowerIsBetter ? c.mean < best.mean : c.mean > best.mean)) best = c
    }
    return best
  }

  // Group rows by method category when the row axis is method, for the
  // same Finetuning / Locate-and-Edit / In-Context structure the
  // Experiments sidebar uses - purely cosmetic, falls back to one flat
  // group for any other row axis.
  const groups = []
  if (rowField === 'method') {
    const seen = new Set()
    for (const v of rowValues) {
      const cat = methodMeta[v]?.category || 'Other'
      if (!seen.has(cat)) {
        seen.add(cat)
        groups.push({ label: cat, values: [] })
      }
      groups.find((g) => g.label === cat).values.push(v)
    }
  } else {
    groups.push({ label: null, values: rowValues })
  }

  // A cell's content, wrapped in a toggle while selecting so the thing you
  // click is the thing you read - the runs a cell averages are exactly the
  // runs it selects.
  function selectable(runs, label, title) {
    if (!selectMode || !runs.length) return label
    const state = groupSelectState(runs, selected)
    return (
      <button
        type="button"
        className={`cell-select is-${state}`}
        aria-pressed={state !== 'none'}
        title={title}
        onClick={() => onToggleRuns(runs)}
      >
        {label}
      </button>
    )
  }

  return (
    <div>
      <div className="axis-controls">
        <AxisTabs label="Rows" value={rowField} onChange={selectRow} />
        <AxisTabs label="Columns" value={colField} onChange={selectColumn} />
      </div>

      <div className="table-wrap">
        <table className="results-table">
          <thead>
            <tr>
              <th>{AXIS_FIELDS.find((f) => f.key === rowField).label}</th>
              {colValues.map((cv) => (
                <th key={cv}>{formatAxisValue(colField, cv, methodMeta, modelMeta)}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {groups.map((g) => (
              <Fragment key={g.label ?? 'all'}>
                {g.label && (
                  <tr className="table-group-row">
                    <td colSpan={colValues.length + 1}>{g.label}</td>
                  </tr>
                )}
                {g.values.map((rv) => {
                  const best = bestInRow(rv)
                  const rowRuns = colValues.flatMap((cv) => runsAt(rv, cv))
                  const label = formatAxisValue(rowField, rv, methodMeta, modelMeta)
                  return (
                    <tr key={rv}>
                      <td>{selectable(rowRuns, label, `Select every run in this row (${rowRuns.length})`)}</td>
                      {colValues.map((cv) => {
                        const c = cell(rv, cv)
                        const isBest = c && best && c.mean === best.mean
                        const runs = runsAt(rv, cv)
                        const runList = runs.join('\n')
                        const value = c
                          ? formatMetricValue(displayMetricKey, c.mean) + (c.matches.length > 1 ? ` (n=${c.matches.length})` : '')
                          : '—'
                        return (
                          <td
                            key={cv}
                            className={isBest ? 'metric-best' : undefined}
                            title={
                              !selectMode && c
                                ? c.matches.map((m) => `${m.run}: ${formatMetricValue(displayMetricKey, m[metricKey])}`).join('\n')
                                : undefined
                            }
                          >
                            {selectMode ? selectable(runs, value, runs.length ? `Select:\n${runList}` : undefined) : value}
                          </td>
                        )
                      })}
                    </tr>
                  )
                })}
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>
      <p className="dataset-note">
        {selectMode
          ? 'Click a cell to select the runs it averages, or a row label for the whole row. A cell with no value for this metric still has runs behind it, so it stays selectable.'
          : `Cells average ${metricLabel(displayMetricKey)} over every run matching that combination. Anything not chosen as a row/column (e.g. seed, or lr when it isn't an axis) is collapsed into the mean. ${lowerIsBetter ? 'Lowest' : 'Highest'} per row is highlighted.`}
      </p>
    </div>
  )
}
