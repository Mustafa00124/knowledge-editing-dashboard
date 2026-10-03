import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api.js'
import { formatValue } from '../lib/hparams.js'

function JobLog({ jobId }) {
  const [log, setLog] = useState(null)
  useEffect(() => {
    api.getExperiment(jobId).then(setLog).catch((e) => setLog({ err_tail: e.message, log_tail: '' }))
  }, [jobId])
  if (!log) return <p className="dl-dim">Loading the job's log…</p>
  return (
    <div className="hp-run-log">
      {log.err_tail && <><div className="dl-dim">Error log (last lines)</div><pre className="dl-log">{log.err_tail}</pre></>}
      {log.log_tail && <><div className="dl-dim">Output log (last lines)</div><pre className="dl-log">{log.log_tail}</pre></>}
      {!log.err_tail && !log.log_tail && <p className="dl-dim">The logs are empty.</p>}
    </div>
  )
}

function Attempt({ jobId, state, error, when, children }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="hp-attempt">
      <div className="hp-attempt-head">
        <span className={`badge ${state === 'COMPLETED' ? 'badge-completed' : 'badge-failed'}`}>{state.toLowerCase()}</span>
        <span className="dl-dim">job {jobId}{when ? ` · ${new Date(when).toLocaleString()}` : ''}</span>
        {children}
        <button type="button" className="btn-plain-small" onClick={() => setOpen((o) => !o)}>{open ? 'Hide log' : 'Log'}</button>
      </div>
      {error && <pre className="hp-error-full">{error}</pre>}
      {open && <JobLog jobId={jobId} />}
    </div>
  )
}

function FailureCard({ row, onRerun, rerunning }) {
  const settings = [
    ...Object.entries(row.overrides).map(([k, v]) => `${k} ${formatValue(v)}`),
    ...Object.entries(row.fixed || {}).map(([k, v]) => `held ${k} ${formatValue(v)}`),
  ].join(' · ')
  const failingNow = row.state !== 'COMPLETED'
  return (
    <li className="dl-task hp-failure">
      <div className="dl-task-top">
        <span className="dl-task-label">
          {row.method} · {row.model} · {row.dataset}
          <span className="dl-dim"> · {settings}</span>
        </span>
        <Link to={`/results/investigations?investigation=${row.investigation}&sweep=${row.sweep_id}`} className="btn-plain-small">
          {row.investigation_label} · {row.sweep_label || row.sweep_id}
        </Link>
      </div>
      {(row.flags || []).length > 0 && (
        <div>{row.flags.map((f) => <span key={f.text} className={`hp-flag is-${f.level}`}>{f.text}</span>)}</div>
      )}
      <Attempt jobId={row.job_id} state={row.state} error={row.error} when={row.submitted_at}>
        {failingNow && onRerun && (
          <button type="button" className="btn-plain-small" disabled={rerunning} onClick={onRerun}
            title="Resubmit this sweep's failed or cancelled runs with the same settings">
            {rerunning ? 'Resubmitting…' : 'Rerun failed in this sweep'}
          </button>
        )}
      </Attempt>
      {row.earlier.length > 0 && (
        <div className="hp-earlier">
          <div className="dl-dim">Earlier attempt{row.earlier.length === 1 ? '' : 's'}</div>
          {[...row.earlier].reverse().map((e) => (
            <Attempt key={e.job_id} jobId={e.job_id} state={e.state} error={e.error} when={e.submitted_at} />
          ))}
        </div>
      )}
    </li>
  )
}

// Every sweep run, in any investigation, that is failing now or failed
// before a rerun fixed it, with the error each attempt ended on.
export default function SweepFailures() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [rerunning, setRerunning] = useState(null)
  const [showResolved, setShowResolved] = useState(false)

  const load = () => api.sweepFailures().then(setData).catch((e) => setError(e.message))
  useEffect(() => {
    load()
    const timer = setInterval(load, 20000)
    return () => clearInterval(timer)
  }, [])

  async function rerun(row) {
    setRerunning(row.sweep_id)
    try {
      await api.rerunFailedSweep(row.investigation, row.sweep_id)
      await load()
    } catch (e) {
      setError(e.message)
    } finally {
      setRerunning(null)
    }
  }

  if (error) return <p className="form-error">{error}</p>
  if (!data) return <p className="empty">Checking every sweep…</p>
  return (
    <div>
      <p className="dl-dim">
        Runs that ended without finishing (failed, cancelled, out of memory, timed out) or finished with an error flag
        such as a NaN loss, across every investigation. Each shows the line its error log ended on; “Log” shows the rest.
      </p>
      <h2 className="section-heading">Failing now ({data.open.length})</h2>
      {!data.open.length && <p className="dl-bar-ok">Nothing is failing.</p>}
      <ul className="dl-tasks">
        {data.open.map((row) => (
          <FailureCard key={`${row.sweep_id}/${row.run}`} row={row} onRerun={() => rerun(row)} rerunning={rerunning === row.sweep_id} />
        ))}
      </ul>
      {data.resolved.length > 0 && (
        <section className="dl-section">
          <div className="dl-section-head">
            <h2 className="section-heading">Fixed by a rerun ({data.resolved.length})</h2>
            <button type="button" className="btn-plain-small" onClick={() => setShowResolved((v) => !v)}>
              {showResolved ? 'Hide' : 'Show'}
            </button>
          </div>
          {showResolved && (
            <ul className="dl-tasks">
              {data.resolved.map((row) => <FailureCard key={`${row.sweep_id}/${row.run}`} row={row} />)}
            </ul>
          )}
        </section>
      )}
    </div>
  )
}
