import { useEffect, useState } from 'react'
import { api } from '../../api.js'

// The CRITERIA.md checklist, as datasets/SidsDataset/criteria.py reports it.
// Opened from the Criteria button above Sid's Dataset browser. Each check is
// green (pass), red (fail), amber (review: a script flags, a person decides),
// grey (pending on data, or manual) or plain (info tables).
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

function Check({ check }) {
  const expandable = check.items.length > 0 || check.table || check.note
  const [open, setOpen] = useState(false)
  const s = STATUS[check.status] || STATUS.info
  return (
    <li className={`sids-crit sids-crit-${check.status}`}>
      <button type="button" className="sids-crit-head" aria-expanded={open} disabled={!expandable}
        onClick={() => setOpen((o) => !o)}>
        <span className="sids-crit-mark" aria-label={s.label}>{s.mark}</span>
        <span className="sids-crit-name">{check.name}</span>
        {check.count > 0 && <span className="sids-crit-count">{check.count}</span>}
        <span className="sids-crit-status">{s.label}</span>
      </button>
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

export default function SidsCriteriaModal({ onClose }) {
  const [report, setReport] = useState(null)
  const [error, setError] = useState(null)
  const load = () => {
    setReport(null)
    setError(null)
    api.sidsDatasetCriteria().then(setReport).catch((err) => setError(String(err.message || err)))
  }
  useEffect(load, [])
  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const sections = []
  for (const c of report?.checks || []) {
    const last = sections[sections.length - 1]
    if (last && last.title === c.section) last.checks.push(c)
    else sections.push({ title: c.section, checks: [c] })
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal sids-info-modal" onClick={(e) => e.stopPropagation()} role="dialog" aria-modal="true"
        aria-label="Sid's Dataset criteria">
        <div className="modal-header">
          <div className="modal-title-group">
            <h2>Criteria</h2>
            <span className="sids-info-tag">CRITERIA.md checklist</span>
          </div>
          <div>
            <button type="button" className="btn-plain" onClick={load} aria-label="Recheck" title="Recheck">↻</button>
            <button type="button" className="btn-plain" onClick={onClose} aria-label="Close">✕</button>
          </div>
        </div>
        <div className="modal-body sids-info-body">
          {error && <p className="archive-line archive-line-warn">{error}</p>}
          {!report && !error && <p className="empty">Checking {'…'}</p>}
          {report && (
            <p className="sids-crit-summary">
              {report.records} records:{' '}
              {ORDER.filter((s) => s !== 'info' && report.status[s]).map((s) => (
                <span key={s} className={`sids-crit-pill sids-crit-${s}`}>{report.status[s]} {STATUS[s].label}</span>
              ))}
            </p>
          )}
          {sections.map((sec) => (
            <section key={sec.title}>
              <h3>{sec.title}</h3>
              <ul className="sids-crit-list">{sec.checks.map((c) => <Check key={c.name} check={c} />)}</ul>
            </section>
          ))}
        </div>
      </div>
    </div>
  )
}
