import { Link } from 'react-router-dom'
import { duration, formatValue } from '../lib/hparams.js'

// What a running run is doing right now, in words.
export function runActivity(run) {
  const p = run.progress || {}
  const setting = Object.entries(run.overrides || {}).map(([k, v]) => `${k} ${formatValue(v)}`).join(', ')
  const where = p.done != null && p.total ? `${p.unit || 'step'} ${p.done}/${p.total}` : p.phase
  return `run ${run.position}: ${run.method} · ${run.model} · ${run.dataset_short || ''}${setting ? ` · ${setting}` : ''}${where ? ` (${where})` : ''}`
}

const when = (iso) => {
  if (!iso) return null
  const date = new Date(iso)
  return Number.isNaN(date.getTime()) ? iso : date.toLocaleString()
}

// One sweep: why it is waiting before it starts, a bar and the run it is on
// once it has, and actions for when it is done.
export default function SweepCard({ sweep, onDetails, onCancel, onRerun, onHide, onUnhide }) {
  const started = sweep.running.length > 0 || sweep.finished > 0
  const done = sweep.states.COMPLETED || 0
  const failed = sweep.retryable
  return (
    <li className="dl-task hp-sweep-card">
      <div className="dl-task-top">
        <button type="button" className="hp-sweep-title" onClick={onDetails} title="Show this sweep's settings and every run">
          {sweep.label || sweep.id}
          <span className="dl-dim"> · {sweep.methods.join(', ')} · {sweep.models.length} model{sweep.models.length === 1 ? '' : 's'}</span>
        </button>
        <span className="dl-dim">
          {sweep.finished}/{sweep.runs} finished
          {failed ? <span className="hp-flag is-error">{failed} failed</span> : null}
        </span>
      </div>

      {!started && sweep.active > 0 && (
        <div className="hp-waiting">
          <span className="badge badge-pending">waiting to start</span>
          {sweep.waiting.map((w) => <span key={w.text}>{w.count} run{w.count === 1 ? '' : 's'}: {w.text}</span>)}
          {sweep.start_estimate && <span className="dl-dim">SLURM estimates a start at {when(sweep.start_estimate)}</span>}
        </div>
      )}

      {started && (
        <>
          <div className="progress-track">
            <div className="progress-fill" style={{ width: `${Math.max(sweep.overall * 100, sweep.active ? 2 : 0)}%` }} />
          </div>
          {sweep.running.map((run) => (
            <div key={run.run} className="hp-activity">
              <span className="badge badge-running">running</span> {runActivity(run)}
              {run.elapsed_sec ? <span className="dl-dim"> · {duration(run.elapsed_sec)}</span> : null}
            </div>
          ))}
          {sweep.waiting.length > 0 && (
            <div className="hp-waiting">
              {sweep.waiting.map((w) => <span key={w.text} className="dl-dim">{w.count} more waiting: {w.text}</span>)}
            </div>
          )}
        </>
      )}

      <div className="dl-task-actions">
        <span className="dl-dim">
          {when(sweep.created_at)}{sweep.gpu_seconds ? ` · ${duration(sweep.gpu_seconds)} of GPU time` : ''}
          {done && !sweep.active ? ' · done' : ''}
        </span>
        <button type="button" className="btn-plain-small" onClick={onDetails}>Details</button>
        <Link to={`/results/investigations?investigation=${sweep.investigation}&sweep=${sweep.id}`} className="btn-plain-small">Results</Link>
        {failed > 0 && (
          <button type="button" className="btn-plain-small" onClick={onRerun}
            title="Resubmit the failed or cancelled runs with the same settings">Rerun {failed} failed</button>
        )}
        {sweep.active > 0 && <button type="button" className="btn-danger-small" onClick={onCancel}>Cancel</button>}
        {sweep.active === 0 && !sweep.hidden && (
          <button type="button" className="btn-plain-small" onClick={onHide}
            title="Clear this sweep from the list. Its runs stay on Results · Investigations">Hide</button>
        )}
        {sweep.hidden && (
          <button type="button" className="btn-plain-small" onClick={onUnhide}
            title="Put this sweep back on the list">Unhide</button>
        )}
      </div>
    </li>
  )
}
