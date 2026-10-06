import { Fragment, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api.js'
import { duration, formatValue, pct } from '../lib/hparams.js'
import { runActivity } from './SweepCard.jsx'

const ACTIVE = ['PENDING', 'RUNNING', 'REQUEUED', 'SUSPENDED', 'CONFIGURING', 'COMPLETING']

function Config({ detail }) {
  const r = detail.request
  const methods = Object.entries(r.methods || {})
  const fixed = Object.entries(r.fixed || {})
  return (
    <div className="hp-config">
      <dl>
        <div><dt>Investigation</dt><dd>{detail.investigation_label}</dd></div>
        <div><dt>Started</dt><dd>{new Date(detail.created_at).toLocaleString()}</dd></div>
        <div><dt>Records</dt><dd>dev split, {r.ds_size === 'full' ? 'all dev records (up to 100)' : `${r.ds_size} per subset`}</dd></div>
        <div><dt>Protocol</dt><dd>{r.edit_mode}</dd></div>
        <div><dt>Seed</dt><dd>{r.seed}</dd></div>
        <div><dt>Models</dt><dd>{(r.models || []).join(', ')}</dd></div>
        <div><dt>Datasets</dt><dd>{(r.data_paths || []).map((p) => p.split('/datasets/').pop()).join(', ')}</dd></div>
      </dl>
      <h3>Swept</h3>
      <ul>
        {methods.map(([m, knobs]) => (
          <li key={m}><strong>{m}</strong>: {Object.entries(knobs).map(([k, vs]) => `${k} ∈ {${vs.map(formatValue).join(', ')}}`).join('; ')}</li>
        ))}
      </ul>
      {fixed.length > 0 && (
        <>
          <h3>Held at changed values</h3>
          <ul>
            {fixed.flatMap(([m, perModel]) => Object.entries(perModel).filter(([, kv]) => Object.keys(kv).length)
              .map(([model, kv]) => (
                <li key={`${m}/${model}`}><strong>{m}</strong> on {model}: {Object.entries(kv).map(([k, v]) => `${k} ${formatValue(v)}`).join(', ')}</li>
              )))}
          </ul>
        </>
      )}
      {detail.skipped.length > 0 && (
        <>
          <h3>Skipped</h3>
          <ul>{detail.skipped.map((s, i) => <li key={i}>{s.method} on {s.model}{s.data_path ? ` / ${s.data_path.split('/').pop()}` : ''}: {s.reason}</li>)}</ul>
        </>
      )}
    </div>
  )
}

// A sweep's full request and every run: waiting reason, progress, scores,
// time and error. Refreshes while anything is still active.
export default function SweepDetailModal({ investigation, sweepId, onClose }) {
  const [detail, setDetail] = useState(null)
  const [error, setError] = useState(null)
  const [openError, setOpenError] = useState(null)

  useEffect(() => {
    let live = true
    let timer
    const load = () => api.sweepDetail(investigation, sweepId).then((d) => {
      if (!live) return
      setDetail(d)
      if (d.runs.some((r) => ACTIVE.includes(r.state))) timer = setTimeout(load, 8000)
    }).catch((e) => live && setError(e.message))
    load()
    return () => { live = false; clearTimeout(timer) }
  }, [investigation, sweepId])

  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const finished = detail ? detail.runs.filter((r) => !ACTIVE.includes(r.state)).length : 0
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal hp-sweep-modal" onClick={(e) => e.stopPropagation()} role="dialog" aria-modal="true"
        aria-label="Sweep details">
        <div className="modal-header">
          <div className="modal-title-group">
            <h2>{detail?.label || sweepId}</h2>
            {detail && <span className="dl-dim">{finished}/{detail.runs.length} finished</span>}
          </div>
          <button type="button" className="btn-plain" onClick={onClose} aria-label="Close">✕</button>
        </div>
        <div className="modal-body">
          {error && <p className="form-error">{error}</p>}
          {!detail && !error && <p className="empty">Loading…</p>}
          {detail && (
            <>
              <div className="progress-track"><div className="progress-fill" style={{ width: `${detail.overall * 100}%` }} /></div>
              <Config detail={detail} />
              <h3>Runs</h3>
              <div className="table-wrap">
                <table className="hp-table">
                  <thead>
                    <tr><th>#</th><th>Run</th><th>Setting</th><th>State</th><th>Flu.</th><th>Rel.</th><th>Loc.</th><th>Gen.</th><th>Time</th></tr>
                  </thead>
                  <tbody>
                    {detail.runs.map((r) => (
                      <Fragment key={r.run}>
                        <tr>
                          <td className="dl-dim">{r.position}</td>
                          <td className="hp-run-cell">
                            <strong>{r.method}</strong> · {r.model_label || r.model}
                            <div className="dl-dim">{r.dataset || r.data_path.split('/datasets/').pop()}</div>
                          </td>
                          <td className="hp-setting">{Object.entries(r.overrides).map(([k, v]) => <div key={k}><code>{k}</code> {formatValue(v)}</div>)}</td>
                          <td className="hp-status">
                            <span className={`badge badge-${r.state === 'COMPLETED' ? 'completed' : r.state === 'RUNNING' ? 'running' : r.state === 'PENDING' ? 'pending' : 'failed'}`}>
                              {r.state.toLowerCase()}
                            </span>
                            {r.waiting && <div className="dl-dim">{r.waiting.reason_text}</div>}
                            {r.state === 'RUNNING' && <div className="dl-dim">{runActivity(r).split(' (').slice(1).join(' (').replace(/\)$/, '')}</div>}
                            {r.error && (
                              <button type="button" className="btn-plain-small" onClick={() => setOpenError(openError === r.run ? null : r.run)}>
                                {openError === r.run ? 'Hide error' : 'Error'}
                              </button>
                            )}
                          </td>
                          {['fluency', 'reliability', 'locality', 'generalizability'].map((k) => <td key={k}>{pct(r.scores?.[k])}</td>)}
                          <td className="hp-time">{r.wall_sec != null ? duration(r.wall_sec) : r.elapsed_sec ? `${duration(r.elapsed_sec)} so far` : '—'}</td>
                        </tr>
                        {openError === r.run && (
                          <tr className="hp-log-row"><td colSpan={9}><pre className="hp-error-full">{r.error}</pre></td></tr>
                        )}
                      </Fragment>
                    ))}
                  </tbody>
                </table>
              </div>
              <Link to={`/results/investigations?investigation=${investigation}&sweep=${sweepId}`} onClick={onClose}>
                Rank these runs in Results →
              </Link>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
