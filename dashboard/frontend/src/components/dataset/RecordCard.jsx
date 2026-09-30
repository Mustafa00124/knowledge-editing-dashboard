import { useState } from 'react'
import { normalizeDatasetRecord } from '../../lib/normalizeDatasetRecord.js'

export function DatasetValue({ value }) {
  if (value == null || value === '' || (Array.isArray(value) && !value.length)) return <span className="dataset-missing">Not provided</span>
  if (Array.isArray(value)) return <ul className="dataset-values">{value.flat(Infinity).map((item, i) => <li key={i}>{String(item)}</li>)}</ul>
  return <span>{String(value)}</span>
}

export function QueryCard({ query }) {
  return <div className="dataset-query">
    <div className="probe-group-title">{query.purpose}</div>
    <dl className="dataset-fields">
      <div><dt>Question</dt><dd><DatasetValue value={query.prompt} /></dd></div>
      {query.choices?.length > 0 && <div><dt>Choices</dt><dd><DatasetValue value={query.choices} /></dd></div>}
      {query.previousAnswer != null && <div><dt>Previous answer</dt><dd><DatasetValue value={query.previousAnswer} /></dd></div>}
      <div><dt>{query.answerLabel || 'Expected answer'}</dt><dd><DatasetValue value={query.answer} /></dd></div>
    </dl>
    {query.conditions?.length > 0 && <details>
      <summary>Evaluation prerequisites ({query.conditionOperator || 'source-defined'})</summary>
      {query.conditions.map((condition, i) => <dl className="dataset-fields" key={i}>
        <div><dt>Question</dt><dd><DatasetValue value={condition.prompt} /></dd></div>
        <div><dt>Expected answer</dt><dd><DatasetValue value={condition.answer} /></dd></div>
      </dl>)}
    </details>}
  </div>
}

export default function RecordCard({ record, viewMode, subset, benchmark, recordIndex, isLocality = false }) {
  const [showRaw, setShowRaw] = useState(false)
  const edit = normalizeDatasetRecord(record, subset, isLocality)
  const sourceId = record.sample_id ?? record.id
  return (
    <article className="record-card">
      <header className="dataset-record-header">
        <span>{benchmark} · {subset.label}{isLocality ? ' · locality' : ''}</span>
        <span className="dataset-category">{edit.category}</span>
        <span>{sourceId != null ? `ID ${sourceId}` : `Record ${recordIndex + 1}`}</span>
      </header>
      {edit.subject && <div className="edit-subject">{edit.subject}</div>}
      <dl className="dataset-fields">
        {edit.fields.map(({ label, value }) => <div key={label}><dt>{label}</dt><dd><DatasetValue value={value} /></dd></div>)}
      </dl>
      {edit.note && <p className="dataset-note">{edit.note}</p>}
      {viewMode === 'edit_queries' && edit.queries.length > 0 && <section className="dataset-queries">
        <h3>Evaluation queries</h3>
        {edit.queries.map((query, i) => <QueryCard key={i} query={query} />)}
      </section>}
      <button type="button" className="raw-toggle" onClick={() => setShowRaw(s => !s)}>
        {showRaw ? '▴ Hide raw JSON' : '▾ Show raw JSON'}
      </button>
      {showRaw && <pre className="record-raw">{JSON.stringify(record.source_record ?? record, null, 2)}</pre>}
    </article>
  )
}
