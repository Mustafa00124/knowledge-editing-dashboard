import { useEffect, useState } from 'react'
import { api } from '../../api.js'
import { modelLabel } from './SidsRecordCard.jsx'
import { dotClass, dotNotes, dotText } from '../../lib/sidResponseDots.js'

// One post-edit dot explained: the question, what passes, the model's answer
// before the edit (step 0 of the same run) and after it, each with the
// judge's answer label and the form label and their reasons. When the run
// asked the record again after later edits, the answer right after its own
// edit is offered beside the end of the run (shown first).

const KEY_LABEL = (key) => key.replace(/_/g, ' ').replace(/^\w/, (c) => c.toUpperCase())

function Expected({ d }) {
  const e = d.expected
  if (d.query_type === 'unrelated_near' || d.query_type === 'unrelated_far') {
    return <div><dt>Passes when</dt><dd>the answer stays as it was before the edit</dd></div>
  }
  if (!e) return null
  if (e.rule === 'worlds') {
    return (
      <div><dt>Passes when</dt><dd>
        it gives some world's answer (indeterminate: several revisions fit the edit):{' '}
        {Object.entries(e.world_answers || {}).map(([w, a], i) => (
          <span key={w}>{i ? '; ' : ''}<code>{w}</code> {a ?? 'abstain'}</span>
        ))}
        {e.original_answer != null && <span className="sids-ad-dim"> (original: {e.original_answer})</span>}
      </dd></div>
    )
  }
  if (e.rule === 'abstain') {
    return <div><dt>Passes when</dt><dd>it abstains or only denies the original ({e.original_answer ?? 'none'}): a deletion</dd></div>
  }
  return (
    <div><dt>Passes when</dt><dd>
      it gives the new answer <strong>{e.new_answer}</strong>
      {e.original_answer != null && <span className="sids-ad-dim"> (original: {e.original_answer})</span>}
    </dd></div>
  )
}

function Answer({ title, a, isBefore, newObject }) {
  if (!a) return null
  const dot = a.dot || {}
  const status = isBefore ? null : dot.status
  const notes = isBefore ? (dot.form === 'MALFORMED' ? ['malformed answer'] : []) : dotNotes(dot)
  return (
    <div className={`sids-ad-answer sids-pe-answer is-${status || 'before'}`}>
      <div className="sids-ad-row">
        {!isBefore && <span className={dotClass(dot)} aria-hidden="true" />}
        <span className="sids-leaf-role">{title}</span>
        <span className="sids-ad-status">step {a.step}{!isBefore && `: ${dotText(dot)}`}</span>
      </div>
      <dl className="sids-ad-fields">
        <div><dt>Answered</dt><dd>{a.response || <em>empty</em>}</dd></div>
        <div><dt>Judge</dt><dd><code>{a.verdict?.label || 'not judged'}</code>{a.verdict?.reason ? ` ${a.verdict.reason}` : ''}</dd></div>
        {a.worlds?.length > 0 && <div><dt>Worlds</dt><dd>matches {a.worlds.join(', ')}</dd></div>}
        <div><dt>Form</dt><dd>
          {a.form ? <><code className={a.form.label === 'MALFORMED' ? 'sids-pe-malformed' : ''}>{a.form.label}</code>{a.form.reason ? ` ${a.form.reason}` : ''}</>
            : <span className="sids-ad-dim">not checked (only English answers are)</span>}
        </dd></div>
        {!isBefore && dot.status === 'changed' && (
          <div><dt>Changed to</dt><dd>
            {dot.leak === true ? <>the new answer <strong>{newObject}</strong>: the edit leaked into an unrelated question</>
              : dot.leak === false ? <>an answer that is not the new one ({newObject}): just a different answer</>
                : 'a different answer'}
          </dd></div>
        )}
        {notes.length > 0 && <div><dt>Note</dt><dd>{notes.join('; ')}</dd></div>}
      </dl>
    </div>
  )
}

export default function SidResponseModal({ method, methodLabel, source, model, record, queryKey, onClose }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [view, setView] = useState('end')
  useEffect(() => {
    const onKey = (ev) => { if (ev.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])
  useEffect(() => {
    setData(null)
    setError(null)
    setView('end')
    api.sidResponsesDetail(method, model, record, queryKey, source).then(setData)
      .catch((err) => setError(String(err.message || err)))
  }, [method, model, record, queryKey, source])

  const title = `${KEY_LABEL(queryKey)} after editing`
  const after = view === 'own' && data?.after_own_edit ? data.after_own_edit : data?.after
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal sids-ad-modal" onClick={(ev) => ev.stopPropagation()} role="dialog" aria-modal="true" aria-label={title}>
        <div className="modal-header">
          <div className="modal-title-group">
            <h2>{title}</h2>
            <span className="sids-info-tag">{methodLabel}</span>
            <span className="sids-info-tag">{modelLabel(model)}</span>
            <span className="sids-info-tag">{record}</span>
          </div>
          <button type="button" className="btn-plain" onClick={onClose} aria-label="Close">✕</button>
        </div>
        <div className="modal-body">
          {error && <p className="archive-line archive-line-warn">{error}</p>}
          {!data && !error && <p className="empty">Loading…</p>}
          {data && !data.run && <p className="empty">No {methodLabel} run for this model.</p>}
          {data?.run && data.edited === false && <p className="empty">This record was not edited in the run.</p>}
          {data?.edited && (
            <>
              <p className="sids-ad-dim">Run <code title={data.run.path}>{data.run.run}</code></p>
              <p className="sids-ad-prompt">{data.question}</p>
              <dl className="sids-ad-fields">
                <Expected d={data} />
                {data.determinacy && <div><dt>Determinacy</dt><dd>{data.determinacy.replace(/_/g, ' ')}</dd></div>}
              </dl>
              {data.after_own_edit && (
                <div className="sids-pe-views" role="group" aria-label="Which answer after the edit">
                  <button type="button" className={`btn-plain-small${view === 'end' ? ' is-on' : ''}`} aria-pressed={view === 'end'}
                    onClick={() => setView('end')}>End of run (step {data.after.step})</button>
                  <button type="button" className={`btn-plain-small${view === 'own' ? ' is-on' : ''}`} aria-pressed={view === 'own'}
                    onClick={() => setView('own')}>Right after its own edit (step {data.after_own_edit.step})</button>
                </div>
              )}
              <Answer title={view === 'own' ? 'After its own edit' : 'After the edit'} a={after} newObject={data.new_object} />
              {data.before ? <Answer title="Before the edit" a={data.before} isBefore />
                : <p className="sids-ad-dim">No step-0 answer in this run.</p>}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
