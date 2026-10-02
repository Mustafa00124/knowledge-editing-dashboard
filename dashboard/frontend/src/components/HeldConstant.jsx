import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { formatValue, parseValue, pct, valueKey } from '../lib/hparams.js'

const SOURCE_LABEL = {
  hparams: 'hparams file',
  tuned: 'tuned by a sweep',
  experiment_default: 'Experiments page default',
  runner: 'set by the runner',
}

function ValueCell({ row, changed, onChange, onReset }) {
  const [text, setText] = useState(formatValue(changed !== undefined ? changed : row.value))
  useEffect(() => { setText(formatValue(changed !== undefined ? changed : row.value)) }, [changed, row.value])
  if (!row.editable) return <span className="dl-dim">{row.note}</span>
  const commit = () => {
    // Text left as displayed is the current value, even where YAML spelled
    // it differently ("5e-1" parses to 0.5).
    if (text.trim() === formatValue(row.value).trim()) { onReset(); return }
    const value = parseValue(text)
    if (value === undefined || valueKey(value) === valueKey(row.value)) onReset()
    else onChange(value)
  }
  return (
    <span className="hp-held-value">
      <input value={text} onChange={(e) => setText(e.target.value)} onBlur={commit}
        onKeyDown={(e) => { if (e.key === 'Enter') e.currentTarget.blur() }}
        className={changed !== undefined ? 'is-changed' : ''} aria-label={`${row.key} value`} />
      {changed !== undefined && (
        <button type="button" className="btn-plain-small" onClick={onReset} title={`back to ${formatValue(row.value)}`}>reset</button>
      )}
    </span>
  )
}

// Everything a sweep does not vary, per method and model, with the value it
// runs at and where that comes from. Values can be changed for this sweep
// only, for example to the best one another investigation has found.
export default function HeldConstant({ held, swept, fixed, onFix, models, runSettings }) {
  const [model, setModel] = useState(models[0])
  useEffect(() => { if (!models.includes(model)) setModel(models[0]) }, [models, model])
  const methods = Object.keys(held || {})

  return (
    <section className="dl-section hp-held">
      <h2 className="section-heading">5. Held constant</h2>
      <p className="dl-section-intro">
        Everything this sweep does not vary stays fixed at these values for every run. Change one to hold it somewhere
        else for this sweep only; the hparams files are not touched. “Best elsewhere” is the strongest value another
        investigation has found for that setting (by the weakest criterion, on any dataset).
      </p>

      <div className="hp-held-run">
        <h3>Every run</h3>
        <dl>
          {runSettings.map(([label, value]) => (
            <div key={label}><dt>{label}</dt><dd>{value}</dd></div>
          ))}
        </dl>
      </div>

      {!methods.length && <p className="dl-dim">Pick a method and a model above to see its held settings.</p>}
      {methods.length > 0 && models.length > 1 && (
        <div className="pill-row" role="group" aria-label="Model">
          {models.map((m) => (
            <button key={m} type="button" className={`pill${m === model ? ' selected' : ''}`} aria-pressed={m === model}
              onClick={() => setModel(m)}>{m}</button>
          ))}
        </div>
      )}
      {methods.map((method) => {
        const rows = (held[method]?.[model] || []).filter((r) => !(swept[method] || []).includes(r.key))
        if (!rows.length) return null
        const changes = Object.keys(fixed[method]?.[model] || {}).length
        return (
          <div key={method} className="hp-held-method">
            <h3>{method} on {model}{changes ? <span className="badge badge-pending">{changes} changed</span> : null}</h3>
            <div className="table-wrap">
              <table className="dl-table">
                <thead><tr><th>Setting</th><th>Held at</th><th>Comes from</th><th>Tuned in</th><th>Best elsewhere</th></tr></thead>
                <tbody>
                  {rows.map((row) => {
                    const changed = fixed[method]?.[model]?.[row.key]
                    return (
                      <tr key={row.key}>
                        <td><code>{row.key}</code></td>
                        <td>
                          <ValueCell row={row} changed={changed}
                            onChange={(value) => onFix(method, model, row.key, value)}
                            onReset={() => onFix(method, model, row.key, undefined)} />
                        </td>
                        <td className="dl-dim" title={row.note || undefined}>
                          {changed !== undefined ? 'changed for this sweep' : SOURCE_LABEL[row.source]}
                          {row.source === 'experiment_default' && changed === undefined && <div className="dl-desc">{row.note}</div>}
                          {row.source === 'tuned' && changed === undefined && <div className="dl-desc">{row.note}</div>}
                        </td>
                        <td>{row.owner ? <Link to={`/hyperparameters/${row.owner.id}`}>{row.owner.label}</Link> : <span className="dl-dim">not swept by any</span>}</td>
                        <td>
                          {row.best ? (
                            <button type="button" className="btn-plain-small"
                              title={`${row.best.dataset}, sweep ${row.best.sweep}`}
                              disabled={valueKey(row.best.value) === valueKey(changed !== undefined ? changed : row.value)}
                              onClick={() => onFix(method, model, row.key,
                                valueKey(row.best.value) === valueKey(row.value) ? undefined : row.best.value)}>
                              use {formatValue(row.best.value)} · weakest {pct(row.best.worst)}
                            </button>
                          ) : <span className="dl-dim">—</span>}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )
      })}
    </section>
  )
}
