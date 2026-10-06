import { useCallback, useEffect, useState } from 'react'
import { api } from '../api.js'
import { duration } from '../lib/hparams.js'

// What is running for one investigation right now, whoever launched it: a
// person on this page, or an agent through the API (scripts/dash.py). One
// card per launch (a sweep, or a batch of experiment runs submitted
// together), from /api/launches. Finished launches of the last week are a
// click away.

const when = (iso) => {
  if (!iso) return ''
  const date = new Date(iso)
  return Number.isNaN(date.getTime()) ? iso : date.toLocaleString()
}

function RunRows({ launchId }) {
  const [detail, setDetail] = useState(null)
  const [error, setError] = useState(null)
  useEffect(() => {
    api.launchDetail(launchId).then(setDetail).catch((e) => setError(String(e.message || e)))
  }, [launchId])
  if (error) return <p className="archive-line archive-line-warn">{error}</p>
  if (!detail) return <p className="dl-dim">Loading runs…</p>
  const runs = detail.kind === 'sweep'
    ? (detail.runs || []).map((r) => ({ run: r.run, job_id: r.job_id, state: r.state, note: r.error || r.waiting?.reason_text || r.progress?.phase }))
    : detail.runs.map((r) => ({ run: r.run, job_id: r.job_id, state: r.state, note: r.activity || r.waiting?.reason_text || (r.err_tail || '').trim().split('\n').pop() }))
  return (
    <table className="inv-runs">
      <tbody>
        {runs.map((r) => (
          <tr key={r.job_id}>
            <td className="inv-run-name" title={r.run}>{r.run}</td>
            <td><span className={`inv-state is-${String(r.state).toLowerCase()}`}>{String(r.state).toLowerCase()}</span></td>
            <td className="dl-dim" title={r.note || ''}>{r.note || ''}</td>
            <td className="dl-dim">{r.job_id}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

function LaunchCard({ launch, onCancel }) {
  const [open, setOpen] = useState(false)
  const started = launch.running.length > 0 || launch.finished > 0
  return (
    <li className={`dl-task inv-launch${launch.failed ? ' is-failed' : ''}`}>
      <div className="dl-task-top">
        <span className="dl-task-label">
          {launch.label || launch.id}
          {launch.launched_by === 'agent' && <span className="badge inv-agent" title="Launched through the API with the agent token">agent</span>}
          <span className="dl-dim"> · {launch.kind === 'sweep' ? 'sweep' : launch.experiment_type}{launch.swept?.length ? ` over ${launch.swept.join(', ')}` : ''}</span>
        </span>
        <span className="dl-dim">
          {launch.finished}/{launch.runs} finished
          {launch.failed ? <span className="hp-flag is-error">{launch.failed} failed</span> : null}
        </span>
      </div>
      {launch.note && <div className="dl-dim inv-note">{launch.note}</div>}

      {launch.active > 0 && !started && (
        <div className="hp-waiting">
          <span className="badge badge-pending">waiting to start</span>
          {launch.waiting.map((w) => <span key={w.text}>{w.count} run{w.count === 1 ? '' : 's'}: {w.text}</span>)}
          {launch.start_estimate && <span className="dl-dim">SLURM estimates a start at {when(launch.start_estimate)}</span>}
        </div>
      )}
      {started && (
        <>
          <div className="progress-track" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(launch.overall * 100)}>
            <div className="progress-fill" style={{ width: `${Math.max(launch.overall * 100, launch.active ? 2 : 0)}%` }} />
          </div>
          {launch.running.map((run) => (
            <div key={run.job_id} className="hp-activity">
              <span className="badge badge-running">running</span> {run.what || run.run}
              {run.activity ? <span className="dl-dim"> ({run.activity})</span> : null}
              {run.elapsed_sec ? <span className="dl-dim"> · {duration(run.elapsed_sec)}</span> : null}
            </div>
          ))}
          {launch.waiting.length > 0 && (
            <div className="hp-waiting">
              {launch.waiting.map((w) => <span key={w.text} className="dl-dim">{w.count} more waiting: {w.text}</span>)}
            </div>
          )}
        </>
      )}

      <div className="dl-task-actions">
        <span className="dl-dim">{when(launch.created_at)} · <code title="Launch id, for scripts/dash.py status">{launch.id}</code></span>
        <button type="button" className="btn-plain-small" onClick={() => setOpen(!open)}>{open ? 'Hide runs' : 'Runs'}</button>
        {launch.active > 0 && <button type="button" className="btn-danger-small" onClick={onCancel}>Cancel</button>}
      </div>
      {open && <RunRows launchId={launch.id} />}
    </li>
  )
}

export default function InvestigationProgress({ investigation, title = 'Progress' }) {
  const [active, setActive] = useState(null)
  const [recent, setRecent] = useState(null)
  const [showRecent, setShowRecent] = useState(false)
  const [error, setError] = useState(null)

  const load = useCallback(() => {
    api.launches(investigation, { active: true })
      .then((rows) => { setActive(rows); setError(null) })
      .catch((e) => setError(String(e.message || e)))
    if (showRecent) api.launches(investigation, { active: false, limit: 10 }).then(setRecent).catch(() => {})
  }, [investigation, showRecent])

  useEffect(() => {
    load()
    const timer = setInterval(load, 6000)
    return () => clearInterval(timer)
  }, [load])

  async function cancel(launch) {
    if (!window.confirm(`Cancel every queued and running job of "${launch.label || launch.id}"?`)) return
    try {
      await api.cancelLaunch(launch.id)
    } catch (e) {
      setError(String(e.message || e))
    }
    load()
  }

  async function clearFinished() {
    try {
      await api.clearLaunches(investigation)
      setRecent([])
    } catch (e) {
      setError(String(e.message || e))
    }
    load()
  }

  const finished = (recent || []).filter((l) => !l.active)
  return (
    <section className="dl-section inv-progress">
      <h2 className="section-heading">
        {title}
        {active && active.length > 0 && <span className="badge badge-running">{active.length} active</span>}
      </h2>
      {error && <p className="archive-line archive-line-warn">{error}</p>}
      {active && active.length === 0 && (
        <p className="dl-dim">
          Nothing running. Launches show here whether they come from this page or from an agent through the API
          (<code>scripts/dash.py</code>).
        </p>
      )}
      {active && active.length > 0 && (
        <ul className="dl-tasks">{active.map((l) => <LaunchCard key={l.id} launch={l} onCancel={() => cancel(l)} />)}</ul>
      )}
      <span className="dl-task-controls">
        <button type="button" className="btn-plain-small" onClick={() => setShowRecent(!showRecent)}>
          {showRecent ? 'Hide finished' : 'Finished in the last week'}
        </button>
        {showRecent && finished.length > 0 && (
          <button type="button" className="btn-plain-small" onClick={clearFinished}
            title="Take every finished launch of this investigation off the dashboard; results and logs stay on disk">
            Clear finished
          </button>
        )}
      </span>
      {showRecent && recent && (finished.length
        ? <ul className="dl-tasks">{finished.map((l) => <LaunchCard key={l.id} launch={l} />)}</ul>
        : <p className="dl-dim">None.</p>)}
    </section>
  )
}
