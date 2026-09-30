import { comboCount } from '../lib/comboCount.js'
import { STATUS, summarize, leadJob, stepPct } from '../lib/queueStatus.js'

// The card face is deliberately thin: state colour, what's loaded, the
// current job's bar, and the counts. Everything else (per-job status,
// metrics, logs, params) lives behind a click, in QueueDetailModal - a
// four-card row is a glanceable status board, not a place to read detail.
export default function QueueCard({ slotIndex, slot, fields, onOpen, onLaunch, onPause, onResume, onClear, actionPending, launchBlocked }) {
  const { status, jobs, current, running, active, done, interrupted } = summarize(slot)
  const staged = slot?.staged || null

  // `fields` matters: without it comboCount returns the plain Cartesian
  // product, which over-counts whenever a show_when field is swept next to
  // the field it depends on (sweeping lr across all 8 methods counts it
  // against ROME too, though ROME ignores lr). The drawer passes fields and
  // the backend dedupes the same way, so omitting it here made the launch
  // confirmation claim roughly double the jobs actually submitted.
  const total = current.length || (staged ? comboCount(staged.params, fields) : 0)
  const lead = leadJob(running)
  const leadPct = stepPct(lead)
  const label = staged?.experiment_type || jobs[0]?.experiment_type
  const isTrial = staged?.save_results === false || Boolean(jobs[0]?.testing_id)
  const interactive = jobs.length > 0 || Boolean(staged)

  function act(e, fn) {
    e.stopPropagation()
    fn()
  }

  function handleLaunch(e) {
    act(e, () => {
      if (total > 20 && !window.confirm(`Launch ${total} separate SLURM jobs (one GPU each)?`)) return
      onLaunch(slotIndex)
    })
  }

  function handleClear(e) {
    act(e, () => {
      const n = interrupted.length
      if (!window.confirm(
        `Discard this queue? Its ${n} stopped experiment${n === 1 ? '' : 's'} won't be restarted. ` +
        'Results already written are kept.',
      )) return
      onClear(slotIndex)
    })
  }

  function handlePause(e) {
    act(e, () => {
      const n = active.length
      if (!window.confirm(`Pause ${n} running/queued experiment${n === 1 ? '' : 's'}? SLURM will cancel them to free their resources. Play will restart only these interrupted experiments from the beginning.`)) return
      onPause(slotIndex)
    })
  }

  return (
    <div
      className={`queue-card is-${status}${interactive ? ' is-clickable' : ''}`}
      onClick={interactive ? () => onOpen(slotIndex) : undefined}
      role={interactive ? 'button' : undefined}
      tabIndex={interactive ? 0 : undefined}
      onKeyDown={interactive ? (e) => {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onOpen(slotIndex) }
      } : undefined}
      title={interactive ? 'Open for details' : STATUS[status]?.hint}
    >
      <div className="queue-card-top">
        <span className="queue-slot-label">GPU Queue {slotIndex + 1}</span>
        <span className="queue-state">
          <span className="queue-state-dot" aria-hidden="true" />
          {STATUS[status]?.label || status}
        </span>
      </div>

      <div className="queue-sub">
        {label ? (
          <>
            {label}
            {isTrial && <span className="queue-trial-tag">trial</span>}
          </>
        ) : (
          'Nothing configured yet'
        )}
      </div>

      <div className="queue-card-body">
        {lead ? (
          <>
            <div className="progress-track">
              <div className="progress-fill" style={{ width: `${leadPct ?? 0}%` }} />
            </div>
            <div className="queue-run-name">{lead.run_name || lead.job_id}</div>
          </>
        ) : total > 0 ? (
          <>
            <div className="progress-track">
              <div className="progress-fill" style={{ width: `${total ? Math.round((done.length / total) * 100) : 0}%` }} />
            </div>
            <div className="queue-run-name">
              {status === 'staged' ? 'Not launched yet' : status === 'completed' ? 'All jobs finished' : status === 'paused' ? 'Stopped · Play restarts interrupted work' : 'No job running'}
            </div>
          </>
        ) : (
          <div className="queue-empty-hint">Configure a run to fill this queue</div>
        )}
      </div>

      <div className="queue-counts">
        {total > 0 ? (
          <>
            <strong>{done.length}</strong> of <strong>{total}</strong> done
            {running.length > 0 && <> · {running.length} running</>}
            {active.length - running.length > 0 && <> · {active.length - running.length} queued</>}
          </>
        ) : (
          <span className="queue-counts-idle">—</span>
        )}
      </div>

      <div className="queue-card-actions">
        {status === 'staged' && (
          <button type="button" className="btn-status" onClick={handleLaunch} disabled={Boolean(launchBlocked)} title={launchBlocked || undefined}>
            Launch
          </button>
        )}
        {status === 'running' && (
          <button type="button" className="btn-status" disabled={actionPending} onClick={handlePause} title="Cancel active SLURM jobs and remember them for restart">
            {actionPending ? 'Pausing…' : '⏸ Pause'}
          </button>
        )}
        {status === 'paused' && (
          <>
            <button type="button" className="btn-status" disabled={actionPending} onClick={(e) => act(e, () => onResume(slotIndex))} title="Restart interrupted experiments from the beginning">
              {actionPending ? 'Starting…' : `▶ Play${interrupted.length > 1 ? ` (${interrupted.length})` : ''}`}
            </button>
            <button type="button" className="btn-plain-small" disabled={actionPending} onClick={handleClear} title="Discard this queue instead of restarting it - pause already stopped its jobs">
              Discard
            </button>
          </>
        )}
        {(status === 'completed' || status === 'failed') && (
          <button type="button" className="btn-status" onClick={(e) => act(e, () => onOpen(slotIndex))}>
            View results
          </button>
        )}
      </div>
    </div>
  )
}
