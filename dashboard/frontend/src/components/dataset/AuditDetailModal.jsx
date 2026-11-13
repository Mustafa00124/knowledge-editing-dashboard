import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../api.js'

// One audit dot explained: what the model was asked, what it answered, the
// judge's label, and (for a red dot) which knowledge parts behind the answer
// it lacks. Parts and verdict come from the backend
// (model_audit_reader.audit_detail / diagnose): the record's premises for the
// fact itself; for a derived query the original fact, its bridge and
// revision facts and the relation property its derivation relies on.

const STATUS_LABEL = { green: 'green', red: 'red', yellow: 'not audited', na: 'not asked', given: 'given' }
const KIND_LABEL = {
  premise: 'Premise', bridge: 'Bridge', revision: 'Revision fact', relation: 'Relation property',
  side_fact: 'Side fact', fact: 'Original fact',
}
const KEY_LABEL = (key) => key.replace(/_/g, ' ').replace(/^\w/, (c) => c.toUpperCase())

function Dot({ status }) {
  return <span className={`sids-audit-dot is-${status === 'given' ? 'na' : status}`} aria-hidden="true" />
}

// What the model was asked and answered for one query.
function Answer({ q, showKey }) {
  const why = q.stale ? 'stale: the record changed after this run' : !q.asked && q.status === 'yellow' ? 'not in this run' : null
  return (
    <div className={`sids-ad-answer is-${q.status}`}>
      <div className="sids-ad-row">
        <Dot status={q.status} />
        {showKey && <span className="sids-leaf-role">{KEY_LABEL(q.key)}</span>}
        <span className="sids-ad-status">{STATUS_LABEL[q.status] || q.status}{why ? ` (${why})` : ''}</span>
      </div>
      <p className="sids-ad-prompt">{q.prompt}</p>
      <dl className="sids-ad-fields">
        <div><dt>Expected</dt><dd>{q.expected ?? 'none (not asked)'}{q.rule === 'not_new' ? ' (passes when NOT given)' : ''}</dd></div>
        {q.asked && <div><dt>Answered</dt><dd>{q.response || <em>empty</em>}</dd></div>}
        {q.asked && <div><dt>Judge</dt><dd><code>{q.label || 'no label'}</code>{q.reason ? ` ${q.reason}` : ''}</dd></div>}
      </dl>
    </div>
  )
}

// The in-context premise check (REFINEMENTS.md section 8): the same question
// with the facts it rests on given first. Read against the plain answer:
// known directly; derived only when reminded (composition gap); failed even
// then (reasoning gap); or "taught" when a given fact is one the model does
// not hold (a red part above).
function contextReading(item) {
  const c = item.in_context
  if (!c?.asked || c.stale) return null
  if (item.status === 'green') return 'Answers it directly; the reminder is only a control.'
  if (item.status !== 'red' || c.status === 'yellow') return 'Unclear: an answer was not judged.'
  if ((item.parts || []).some((p) => p.status === 'red')) {
    return 'A fact given in the context is one the model does not hold, so the context taught rather than reminded.'
  }
  return c.status === 'green'
    ? 'Composition gap: it knows the pieces and derives the answer when reminded, but not unprompted.'
    : 'Reasoning gap: it fails even with the facts in context (or the question is the problem).'
}

function InContext({ item }) {
  const c = item.in_context
  if (!c) return null
  const status = !c.asked ? 'yellow' : c.status
  const reading = contextReading(item)
  return (
    <div className="sids-ad-diagnosis">
      <span className="sids-leaf-role">With the facts in context</span>
      <div className={`sids-ad-answer is-${status}`}>
        <div className="sids-ad-row">
          <Dot status={status} />
          <span className="sids-ad-status">{STATUS_LABEL[status] || status}{!c.asked ? ' (not in this run)' : c.stale ? ' (stale: the record changed after this run)' : ''}</span>
        </div>
        <ul className="sids-ad-parts">{c.facts.map((f, i) => <li key={i} className="sids-ad-part"><span className="sids-ad-part-text">{f}</span></li>)}</ul>
        {c.asked && (
          <dl className="sids-ad-fields">
            <div><dt>Answered</dt><dd>{c.response || <em>empty</em>}</dd></div>
            <div><dt>Judge</dt><dd><code>{c.label || 'no label'}</code>{c.reason ? ` ${c.reason}` : ''}</dd></div>
          </dl>
        )}
      </div>
      {reading && <p className="sids-ad-verdict is-info">{reading}</p>}
    </div>
  )
}

function Part({ p }) {
  const asked = p.status !== 'given' && p.kind !== 'fact'
  return (
    <li className="sids-ad-part">
      <Dot status={p.status} />
      <div>
        <span className="sids-leaf-role">{KIND_LABEL[p.kind] || p.kind}{p.status === 'given' ? ' (given in the prompt)' : ''}</span>
        <span className="sids-ad-part-text">{p.kind === 'relation' ? <code>{p.text}</code> : p.text}</span>
        {asked && (
          <span className="sids-ad-dim">
            {p.prompt ? <>Asked: {p.prompt} <em>({p.expected})</em></> : 'No check question for this part.'}
            {p.response != null && <> Answered: {p.response}</>}
            {p.stale && ' (stale: asked with an older wording)'}
            {p.status === 'yellow' && p.response == null && p.prompt && ' Not asked in this run.'}
          </span>
        )}
        {p.kind === 'fact' && <span className="sids-ad-dim">Its direct and paraphrase queries.</span>}
      </div>
    </li>
  )
}

export default function AuditDetailModal({ record, model: firstModel, models, queryKey, queryLabel, labelOf, onClose }) {
  // One tab per model; the dot's quarters are the same models in the same order.
  const [model, setModel] = useState(firstModel)
  const modelLabel = labelOf ? labelOf(model) : model
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  useEffect(() => {
    const onKey = (ev) => { if (ev.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])
  useEffect(() => {
    setData(null)
    setError(null)
    api.sidsDatasetAuditDetail(record, model).then(setData).catch((err) => setError(String(err.message || err)))
  }, [record, model])

  const isFact = queryKey === 'fact'
  const item = data && (isFact ? data.fact : data.queries[queryKey])
  const v = item?.verdict
  const title = isFact ? 'The fact before editing' : `${queryLabel || KEY_LABEL(queryKey)} before editing`

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal sids-ad-modal" onClick={(ev) => ev.stopPropagation()} role="dialog" aria-modal="true" aria-label={title}>
        <div className="modal-header">
          <div className="modal-title-group">
            <h2>{title}</h2>
            <span className="sids-info-tag">{record}</span>
          </div>
          <button type="button" className="btn-plain" onClick={onClose} aria-label="Close">✕</button>
        </div>
        <div className="modal-body">
          {models?.length > 1 && (
            <div className="sids-rv-seg" role="tablist" aria-label="Model">
              {models.map((m) => (
                <button key={m} type="button" role="tab" aria-selected={m === model}
                  className={`sids-rv-seg-btn${m === model ? ' active' : ''}`} onClick={() => setModel(m)}>
                  {labelOf ? labelOf(m) : m}
                </button>
              ))}
            </div>
          )}
          {error && <p className="archive-line archive-line-warn">{error}</p>}
          {!data && !error && <p className="empty">Loading…</p>}
          {data && !item && <p className="empty">This record has no query {queryKey}.</p>}
          {item && (
            <>
              <p className="sids-ad-dim">
                {data.run ? <>Run <code>{data.run}</code>{data.audited_at ? `, ${data.audited_at.replace('T', ' ')}` : ''}</> : 'No audit run for this model yet.'}
              </p>
              {isFact ? (
                <>
                  <p className="sids-ad-prompt"><Dot status={item.status} /> {item.text} <span className="sids-ad-status">({STATUS_LABEL[item.status]})</span></p>
                  {item.keys.filter((k) => data.queries[k]).map((k) => <Answer key={k} q={data.queries[k]} showKey />)}
                </>
              ) : <Answer q={item} />}

              <div className="sids-ad-diagnosis">
                <span className="sids-leaf-role">Diagnosis</span>
                {item.parts.length > 0 ? (
                  <ul className="sids-ad-parts">{item.parts.map((p, i) => <Part key={i} p={p} />)}</ul>
                ) : null}
                <p className={`sids-ad-verdict is-${v.kind}`}>
                  {v.text}{v.parts.length > 0 && ': '}{v.parts.join('; ')}
                </p>
              </div>
              {!isFact && <InContext item={item} />}
            </>
          )}
          <p className="sids-audit-link">
            <Link to={`/model-audit?record=${encodeURIComponent(record)}`} onClick={onClose}>All responses for this record</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
