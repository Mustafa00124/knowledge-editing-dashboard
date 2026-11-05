import { useEffect, useState } from 'react'
import { api } from '../../api.js'
import Markdown from '../../lib/miniMarkdown.jsx'

// The CRITERIA.md checklist, as datasets/SidsDataset/criteria.py reports it.
// Opened from the Criteria button above Sid's Dataset browser. Manual rules
// come first and are informational: reviewers mark records and questions
// green or red on the record cards (SidsReviewDots); expanding a rule here
// shows its guidance (the <details> part of CRITERIA.md), green / red /
// yellow counts per reviewer and every red item. Automated
// rules follow, rerun by "Run checks": green (pass), red (fail), amber
// (review: a script flags, a person decides), grey (pending on data) or plain
// (info).
const STATUS = {
  pass: { label: 'pass', mark: '✓' },
  fail: { label: 'fail', mark: '✕' },
  review: { label: 'review', mark: '!' },
  pending: { label: 'pending', mark: '…' },
  manual: { label: 'manual', mark: '?' },
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

// A manual row's review marks: green, red and yellow (not reviewed) per
// reviewer, then every red item and who marked it (clicking the record jumps
// to it).
function Reviews({ r, onJump }) {
  if (!r) return null
  return (
    <div className="sids-crit-flags">
      <Table rows={[['reviewer', 'green', 'red', 'yellow'],
        ...Object.entries(r.by_reviewer).map(([who, c]) => [who, c.green, c.red, c.yellow])]} />
      <p className="sids-crit-note">{r.total} {r.unit}; {r.red.length} with a red mark.</p>
      {r.red.length > 0 && (
        <ul className="sids-crit-flaglist">
          {r.red.map(({ record, item, marks }) => (
            <li key={`${record} ${item}`}>
              {onJump
                ? <button type="button" className="btn-plain-small" onClick={() => onJump(record)}>{record}</button>
                : <code>{record}</code>}
              {r.unit === 'questions' && <code> {item}</code>}
              {' '}<span className="sids-crit-note">
                red by {marks.map((m) => `${m.reviewer}${m.kind ? ` (${m.kind})` : ''}${m.stale ? ' (record changed since)' : ''}${m.comment ? `: ${m.comment}` : ''}`).join('; ')}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function Check({ check, onJump }) {
  const manual = check.kind === 'manual'
  const expandable = manual || check.items.length > 0 || check.table || check.note
  const [open, setOpen] = useState(false)
  const s = STATUS[check.status] || STATUS.info
  const p = check.reviews
  return (
    <li className={`sids-crit sids-crit-${check.status}`}>
      <div className="sids-crit-row">
        <button type="button" className="sids-crit-head" aria-expanded={open} disabled={!expandable}
          onClick={() => setOpen((o) => !o)}>
          <span className="sids-crit-mark" aria-label={s.label}>{s.mark}</span>
          <span className="sids-crit-name">{check.name}</span>
          {manual && p ? (
            <span className="sids-crit-status">{p.red.length ? `${p.red.length} red` : 'no red marks'}</span>
          ) : (
            <>
              {check.count > 0 && <span className="sids-crit-count">{check.count}</span>}
              <span className="sids-crit-status">{s.label}</span>
            </>
          )}
        </button>
      </div>
      {open && (
        <div className="sids-crit-body">
          {check.note && <p className="sids-crit-note">{check.note}</p>}
          {manual ? (
            <>
              {check.guide && <Markdown text={check.guide} className="sids-crit-guide" />}
              <Reviews r={p} onJump={onJump} />
            </>
          ) : (
            <>
              <Table rows={check.table} />
              {check.items.length > 0 && (
                <ul className="sids-crit-items">{check.items.map((item, i) => <li key={i}><code>{item}</code></li>)}</ul>
              )}
            </>
          )}
        </div>
      )}
    </li>
  )
}

function Sections({ checks, onJump }) {
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
        {sec.checks.map((c) => <Check key={c.name} check={c} onJump={onJump} />)}
      </ul>
    </section>
  ))
}

export default function SidsCriteriaModal({ onClose, onJump }) {
  const [report, setReport] = useState(null)
  const [error, setError] = useState(null)
  const [running, setRunning] = useState(false)
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

  const manual = (report?.checks || []).filter((c) => c.kind === 'manual')
  const automated = (report?.checks || []).filter((c) => c.kind !== 'manual')
  const counts = {}
  for (const c of automated) counts[c.status] = (counts[c.status] || 0) + 1
  const flagged = manual.reduce((n, c) => n + (c.reviews?.red.length || 0), 0)
  const rv = report?.review

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
                <h3>Manual rules <span className="sids-rubric-q">{flagged ? `${flagged} red` : 'no red marks yet'}</span></h3>
                <p className="dataset-note">
                  Judgements no script can make. {rv?.reviewers?.map((r) => r.name).join(', ')} mark each record (per rule)
                  and each of its questions green (fine) or red (flagged) by clicking their own dots on the record cards in
                  Review mode. Yellow: not reviewed yet, or not pushed.
                </p>
                <Sections checks={manual} onJump={onJump} />
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
                <Sections checks={automated} onJump={onJump} />
              </section>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
