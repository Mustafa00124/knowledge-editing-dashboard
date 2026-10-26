import { useEffect, useState } from 'react'
import { api } from '../../api.js'

// The CRITERIA.md checklist, as datasets/SidsDataset/criteria.py reports it.
// Opened from the Criteria button above Sid's Dataset browser. Manual rules
// come first: each is reviewed by two agents (Codex, Claude) and a person,
// whose marks are stored in datasets/SidsDataset/reviews.json (the person's
// mark is toggled here; agents run `criteria.py --mark`). Automated rules
// follow, rerun by "Run checks": green (pass), red (fail), amber (review: a
// script flags, a person decides), grey (pending on data) or plain (info).
const STATUS = {
  pass: { label: 'pass', mark: '✓' },
  fail: { label: 'fail', mark: '✕' },
  review: { label: 'review', mark: '!' },
  pending: { label: 'pending', mark: '…' },
  manual: { label: 'to review', mark: '?' },
  info: { label: 'info', mark: 'i' },
}
const ORDER = ['fail', 'review', 'pending', 'manual', 'pass', 'info']

function Table({ rows }) {
  if (!rows || rows.length < 2) return null
  const [head, ...body] = rows
  return (
    <div className="sids-crit-table-wrap">
      <table className="sids-crit-table">
        <thead><tr>{head.map((h, i) => <th key={i}>{h}</th>)}</tr></thead>
        <tbody>
          {body.map((row, i) => <tr key={i}>{row.map((v, j) => <td key={j}>{String(v)}</td>)}</tr>)}
        </tbody>
      </table>
    </div>
  )
}

// One reviewer's mark on a manual rule: pending until they mark it done.
// Only the person's mark can be toggled here.
function ReviewMark({ review, onToggle, busy }) {
  const title = review.done
    ? `${review.label}: done${review.by ? ` by ${review.by}` : ''}${review.at ? `, ${review.at.replace('T', ' ')}` : ''}${review.note ? `. ${review.note}` : ''}`
    : `${review.label}: pending`
  const cls = `sids-review${review.done ? ' is-done' : ''}`
  if (review.reviewer !== 'human') {
    return <span className={cls} title={title}>{review.done ? '✓' : '…'} {review.label}</span>
  }
  return (
    <button type="button" className={`${cls} is-toggle`} title={`${title}. Click to mark ${review.done ? 'pending' : 'done'}.`}
      disabled={busy} onClick={(e) => { e.stopPropagation(); onToggle(!review.done) }}>
      {review.done ? '✓' : '…'} {review.label}
    </button>
  )
}

function Check({ check, onReview, busy }) {
  const expandable = check.items.length > 0 || check.table || check.note
  const [open, setOpen] = useState(false)
  const s = STATUS[check.status] || STATUS.info
  return (
    <li className={`sids-crit sids-crit-${check.status}`}>
      <div className="sids-crit-row">
        <button type="button" className="sids-crit-head" aria-expanded={open} disabled={!expandable}
          onClick={() => setOpen((o) => !o)}>
          <span className="sids-crit-mark" aria-label={s.label}>{s.mark}</span>
          <span className="sids-crit-name">{check.name}</span>
          {check.count > 0 && <span className="sids-crit-count">{check.count}</span>}
          {!check.reviews && <span className="sids-crit-status">{s.label}</span>}
        </button>
        {check.reviews && (
          <span className="sids-reviews">
            {check.reviews.map((r) => (
              <ReviewMark key={r.reviewer} review={r} busy={busy} onToggle={(done) => onReview(check.rule, done)} />
            ))}
          </span>
        )}
      </div>
      {open && (
        <div className="sids-crit-body">
          {check.note && <p className="sids-crit-note">{check.note}</p>}
          <Table rows={check.table} />
          {check.items.length > 0 && (
            <ul className="sids-crit-items">{check.items.map((item, i) => <li key={i}><code>{item}</code></li>)}</ul>
          )}
        </div>
      )}
    </li>
  )
}

function Sections({ checks, onReview, busy }) {
  const sections = []
  for (const c of checks) {
    const last = sections[sections.length - 1]
    if (last && last.title === c.section) last.checks.push(c)
    else sections.push({ title: c.section, checks: [c] })
  }
  return sections.map((sec) => (
    <section key={sec.title}>
      <h4>{sec.title}</h4>
      <ul className="sids-crit-list">
        {sec.checks.map((c) => <Check key={c.name} check={c} onReview={onReview} busy={busy} />)}
      </ul>
    </section>
  ))
}

export default function SidsCriteriaModal({ onClose }) {
  const [report, setReport] = useState(null)
  const [error, setError] = useState(null)
  const [running, setRunning] = useState(false)
  const [busy, setBusy] = useState(false)
  const run = () => {
    setRunning(true)
    setError(null)
    api.sidsDatasetCriteria().then(setReport).catch((err) => setError(String(err.message || err)))
      .finally(() => setRunning(false))
  }
  useEffect(run, [])
  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])
  const review = (rule, done) => {
    setBusy(true)
    api.sidsDatasetReview(rule, done).then(run).catch((err) => setError(String(err.message || err)))
      .finally(() => setBusy(false))
  }

  const manual = (report?.checks || []).filter((c) => c.kind === 'manual')
  const automated = (report?.checks || []).filter((c) => c.kind !== 'manual')
  const counts = {}
  for (const c of automated) counts[c.status] = (counts[c.status] || 0) + 1
  const reviewed = manual.filter((c) => c.status === 'pass').length

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal sids-info-modal" onClick={(e) => e.stopPropagation()} role="dialog" aria-modal="true"
        aria-label="Sid's Dataset criteria">
        <div className="modal-header">
          <div className="modal-title-group">
            <h2>Criteria</h2>
            <span className="sids-info-tag">CRITERIA.md checklist</span>
          </div>
          <button type="button" className="btn-plain" onClick={onClose} aria-label="Close">✕</button>
        </div>
        <div className="modal-body sids-info-body">
          {error && <p className="archive-line archive-line-warn">{error}</p>}
          {!report && !error && <p className="empty">Checking {'…'}</p>}
          {report && (
            <>
              <section>
                <h3>Manual rules <span className="sids-rubric-q">{reviewed} of {manual.length} reviewed by all three</span></h3>
                <p className="dataset-note">Each rule needs a review from Codex, Claude and a person.</p>
                <Sections checks={manual} onReview={review} busy={busy} />
              </section>
              <section>
                <div className="sids-crit-autohead">
                  <h3>Automated checks</h3>
                  <button type="button" className="btn-plain-small" onClick={run} disabled={running}>
                    {running ? 'Running…' : 'Run checks'}
                  </button>
                </div>
                <p className="sids-crit-summary">
                  {report.records} records:{' '}
                  {ORDER.filter((s) => s !== 'info' && s !== 'manual' && counts[s]).map((s) => (
                    <span key={s} className={`sids-crit-pill sids-crit-${s}`}>{counts[s]} {STATUS[s].label}</span>
                  ))}
                </p>
                <Sections checks={automated} onReview={review} busy={busy} />
              </section>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
