import { useEffect, useState } from 'react'
import {
  ANSWER_KINDS,
  DATASET_FORMATS,
  FORMAT_GOTCHAS,
  INDEPENDENCE,
  MEASUREMENT_NOTE,
  QUERY_FORMS,
} from '../../lib/datasetQueryFormats.js'

// Longest median in the table is WikiBio at 18.5 words. Bars are scaled
// against 20 rather than against that max, so the scale stays fixed if a
// new row is added and a two-word answer keeps looking like a two-word
// answer instead of rescaling every time the tallest row changes.
const BAR_CEILING = 20

function LengthCell({ row }) {
  if (row.median == null) {
    return <span className="qf-length-na" title={row.lengthNote || 'Not applicable'}>n/a</span>
  }
  return (
    <div className="qf-length">
      <div className="qf-bar" aria-hidden="true">
        <span style={{ width: `${Math.min(100, (row.median / BAR_CEILING) * 100)}%` }} />
      </div>
      <span className="qf-length-text">
        <strong>{row.median}</strong>
        <span className="text-dim"> med · {row.p90} p90</span>
      </span>
    </div>
  )
}

// Cross-benchmark reference opened from the "?" beside the Published
// Datasets heading. Per-benchmark "?" buttons stay what they are (paper and
// citations); this one answers "what shape is each of these, and what does
// the model have to emit", which only makes sense side by side.
export default function QueryFormatsModal({ onClose }) {
  const [activeKind, setActiveKind] = useState(null)

  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal qf-modal"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label="Query and answer formats across benchmarks"
      >
        <div className="modal-header">
          <div className="modal-title-group">
            <h2>Query and answer formats</h2>
            <span className="sids-info-tag">cross-benchmark reference</span>
          </div>
          <button type="button" className="btn-plain" onClick={onClose} aria-label="Close">✕</button>
        </div>

        <div className="modal-body qf-body">
          <section>
            <p>
              Three things vary independently across these benchmarks: <strong>how the query is phrased</strong>,{' '}
              <strong>whether the answer is chosen from options</strong>, and <strong>how long the ground truth
              is</strong>. None of the three predicts the others, which is why the table keeps them as separate
              columns:
            </p>
            <ul className="qf-independence">
              {INDEPENDENCE.map((item) => (
                <li key={item.claim}>
                  <strong>{item.claim}.</strong> {item.detail}
                </li>
              ))}
            </ul>
          </section>

          <section>
            <h3>Query forms</h3>
            <dl className="sids-axis-values">
              {Object.entries(QUERY_FORMS).map(([key, form]) => (
                <div key={key}>
                  <dt><span className={`qf-tag qf-tag-${key}`}>{form.label}</span></dt>
                  <dd>
                    {form.detail} <em>"{form.example}"</em>
                  </dd>
                </div>
              ))}
            </dl>
            <p className="dataset-note">
              <span className="qf-mcq">MCQ</span> is orthogonal to all of these: it marks that a fixed choice list ships
              with the query, whatever form that query takes. It also collapses the answer to one token no matter how
              long the underlying answer would be, so an MCQ row is not measuring generation.
            </p>
          </section>

          <section>
            <h3>What the model has to emit</h3>
            <div className="qf-kinds">
              {Object.entries(ANSWER_KINDS).map(([key, kind]) => (
                <button
                  key={key}
                  type="button"
                  className={`qf-kind qf-kind-${key}${activeKind === key ? ' active' : ''}`}
                  aria-pressed={activeKind === key}
                  onClick={() => setActiveKind(activeKind === key ? null : key)}
                  title={activeKind === key ? 'Show all rows again' : `Highlight ${kind.label.toLowerCase()} rows`}
                >
                  <strong>{kind.label}</strong>
                  <small>{kind.detail}</small>
                </button>
              ))}
            </div>
            {activeKind && (
              <p className="dataset-note">
                Highlighting <strong>{ANSWER_KINDS[activeKind].label.toLowerCase()}</strong> rows. Click the card again
                to clear.
              </p>
            )}
          </section>

          <section>
            <h3>By benchmark</h3>
            <div className="qf-table" role="table" aria-label="Query and answer format by benchmark">
              <div className="qf-row qf-head" role="row">
                <span role="columnheader">Probe</span>
                <span role="columnheader">Query form</span>
                <span role="columnheader">Ground-truth field</span>
                <span role="columnheader">Answer length</span>
              </div>

              {DATASET_FORMATS.map((entry) => (
                <div className="qf-group" key={entry.benchmark}>
                  <div className="qf-group-head">
                    <h4>{entry.benchmark}</h4>
                    <code>{entry.sampledFrom}</code>
                  </div>

                  {entry.rows.map((row) => {
                    const dimmed = activeKind && row.answerKind !== activeKind
                    return (
                      <div
                        className={`qf-row${dimmed ? ' dimmed' : ''}`}
                        role="row"
                        key={`${entry.benchmark}/${row.label}`}
                      >
                        <span role="cell" className="qf-probe">
                          {row.label}
                          <small className={`qf-kind-dot qf-kind-${row.answerKind}`}>
                            {ANSWER_KINDS[row.answerKind].label}
                          </small>
                        </span>
                        <span role="cell">
                          <span className={`qf-tag qf-tag-${row.queryForm}`}>{QUERY_FORMS[row.queryForm].label}</span>
                          {row.mcq && <span className="qf-mcq">MCQ</span>}
                        </span>
                        <span role="cell"><code className="qf-field">{row.answerField}</code></span>
                        <span role="cell"><LengthCell row={row} /></span>
                      </div>
                    )
                  })}

                  {entry.note && <p className="qf-note">{entry.note}</p>}
                </div>
              ))}
            </div>
          </section>

          <section>
            <h3>Worth knowing</h3>
            <ul className="qf-independence">
              {FORMAT_GOTCHAS.map((gotcha) => <li key={gotcha}>{gotcha}</li>)}
            </ul>
            <p className="dataset-note">{MEASUREMENT_NOTE}</p>
          </section>
        </div>
      </div>
    </div>
  )
}
