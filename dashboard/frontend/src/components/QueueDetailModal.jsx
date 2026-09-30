import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { STATUS, summarize, stepPct, ACTIVE_STATES, FAIL_STATES } from '../lib/queueStatus.js'

// Everything the card face leaves out. This is where the per-job list that
// used to sit in a separate grid below the queue now lives, scoped to the
// card you actually clicked, so jobs are never divorced from the queue that
// launched them.
export default function QueueDetailModal({ slotIndex, slot, onClose, onLaunch, onPause, onResume, onCancel, onClear, onCancelJob, onRerunFailed, rerunning, actionPending, launchBlocked }) {
  const { status, jobs, current, running, active, done, failed, interrupted } = summarize(slot)
  const staged = slot?.staged || null
  const canRerun = status === 'failed' && failed.length > 0 &&
    current.every((job) => job.status?.state === 'COMPLETED' || FAIL_STATES.includes(job.status?.state))
  const [openJob, setOpenJob] = useState(null)
  const [detail, setDetail] = useState(null)

  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  // Logs are only fetched for the job you expand, and re-fetched on the
  // page's poll, so an open log tail follows a running job live.
  useEffect(() => {
    if (!openJob) { setDetail(null); return }
    let cancelled = false
    const load = () => api.getExperiment(openJob).then((d) => { if (!cancelled) setDetail(d) }).catch(() => {})
    load()
    const id = setInterval(load, 5000)
    return () => { cancelled = true; clearInterval(id) }
  }, [openJob, slot])

  const params = staged?.params || (jobs[0] ? jobs[0].params : null)

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className={`modal queue-modal is-${status}`}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label={`GPU Queue ${slotIndex + 1} detail`}
      >
        <div className="modal-header">
          <div className="modal-title-group">
            <h2>GPU Queue {slotIndex + 1}</h2>
            <span className="queue-state">
              <span className="queue-state-dot" aria-hidden="true" />
              {STATUS[status]?.label || status}
            </span>
          </div>
          <button type="button" className="btn-plain" onClick={onClose} aria-label="Close">✕</button>
        </div>

        <div className="modal-body">
          <div className="modal-stats">
            <div><span className="modal-stat-value">{current.length || 0}</span><span className="modal-stat-label">current jobs</span></div>
            <div><span className="modal-stat-value">{running.length}</span><span className="modal-stat-label">running</span></div>
            <div><span className="modal-stat-value">{active.length - running.length}</span><span className="modal-stat-label">queued</span></div>
            <div><span className="modal-stat-value">{done.length}</span><span className="modal-stat-label">done</span></div>
            <div><span className="modal-stat-value">{failed.length}</span><span className="modal-stat-label">failed</span></div>
          </div>

          {params && (
            <details className="modal-params">
              <summary>Configuration</summary>
              <dl className="modal-param-list">
                {Object.entries(params).map(([k, v]) => (
                  <div key={k}>
                    <dt>{k}</dt>
                    <dd>{Array.isArray(v) ? v.join(', ') : String(v)}</dd>
                  </div>
                ))}
              </dl>
            </details>
          )}

          {jobs.length === 0 && (
            <p className="empty">
              {staged ? 'Configured but not launched yet.' : 'Nothing configured on this queue.'}
            </p>
          )}

          {jobs.length > 0 && (
            <div className="job-list">
              {jobs.map((job) => {
                const state = job.status?.state || 'UNKNOWN'
                const pct = stepPct(job)
                const isOpen = openJob === job.job_id
                const cancellable = ACTIVE_STATES.includes(state)
                return (
                  <div key={job.job_id} className={`job-row${isOpen ? ' is-open' : ''}`}>
                    <button
                      type="button"
                      className="job-row-head"
                      onClick={() => setOpenJob(isOpen ? null : job.job_id)}
                    >
                      <span className={`badge badge-${state.toLowerCase()}`}>{state}</span>
                      <span className="job-row-name">{job.run_name || job.job_id}</span>
                      {job.retried_by && <span className="job-retried-tag" title={`Retried as job ${job.retried_by}`}>Retried</span>}
                      <span className="job-row-steps">
                        {pct != null ? `${job.progress.current_step} / ${job.progress.num_steps}` : '—'}
                      </span>
                      <span className="job-row-chevron" aria-hidden="true">{isOpen ? '▴' : '▾'}</span>
                    </button>

                    {pct != null && (
                      <div className="progress-track progress-track-small">
                        <div className="progress-fill" style={{ width: `${pct}%` }} />
                      </div>
                    )}

                    {isOpen && (
                      <div className="job-row-detail">
                        <div className="job-row-meta">
                          job {job.job_id}
                          {job.retry_of && <> · retry of job {job.retry_of}</>}
                          {job.retried_by && <> · retried as job {job.retried_by}</>}
                          {job.status?.elapsed && <> · elapsed {job.status.elapsed}</>}
                          {job.submitted_at && <> · submitted {new Date(job.submitted_at).toLocaleString()}</>}
                        </div>

                        {job.progress?.latest_metrics && (
                          <div className="metrics-row">
                            {Object.entries(job.progress.latest_metrics)
                              .filter(([k]) => !['step', 'at', 'elapsed_sec'].includes(k))
                              .slice(0, 6)
                              .map(([k, v]) => (
                                <div key={k} className="metric">
                                  <div className="metric-label">{k}</div>
                                  <div className="metric-value">
                                    {typeof v === 'number' ? v.toFixed(3) : String(v)}
                                  </div>
                                </div>
                              ))}
                          </div>
                        )}

                        {detail?.job_id === job.job_id && (detail.log_tail || detail.err_tail) && (
                          <div className="job-logs">
                            {detail.log_tail && (
                              <details open>
                                <summary>Output</summary>
                                <pre>{detail.log_tail.slice(-4000)}</pre>
                              </details>
                            )}
                            {detail.err_tail && (
                              <details>
                                <summary>Errors</summary>
                                <pre>{detail.err_tail.slice(-4000)}</pre>
                              </details>
                            )}
                          </div>
                        )}

                        {cancellable && (
                          <button
                            type="button"
                            className="btn-danger-small"
                            onClick={() => onCancelJob(job.job_id)}
                          >
                            Cancel this job
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>

        <div className="modal-actions">
          {(status === 'staged' || status === 'completed' || status === 'failed') && (
            <button type="button" className="btn-plain-small btn-secondary-slot" onClick={() => onClear(slotIndex)}>
              Clear queue
            </button>
          )}
          {status === 'staged' && (
            <button type="button" className="btn-status" onClick={() => onLaunch(slotIndex)} disabled={Boolean(launchBlocked)} title={launchBlocked || undefined}>
              Launch
            </button>
          )}
          {canRerun && (
            <button type="button" className="btn-status" disabled={rerunning || Boolean(launchBlocked)} onClick={() => onRerunFailed(slotIndex)}
              title={launchBlocked || 'Launch the failed or cancelled jobs again with their original settings; successful jobs are not repeated'}>
              {rerunning ? 'Launching retries…' : `Rerun failed (${failed.length})`}
            </button>
          )}
          {status === 'running' && (
            <button
              type="button"
              className="btn-status"
              disabled={actionPending}
              onClick={() => {
                const n = active.length
                if (!window.confirm(`Pause ${n} running/queued experiment${n === 1 ? '' : 's'}? SLURM will cancel them to free their resources. Play will restart only these interrupted experiments from the beginning.`)) return
                onPause(slotIndex)
              }}
            >
              {actionPending ? 'Pausing…' : `⏸ Pause ${active.length > 1 ? `all ${active.length}` : ''}`}
            </button>
          )}
          {status === 'paused' && (
            <>
              <button type="button" className="btn-plain-small btn-secondary-slot" disabled={actionPending} onClick={() => onCancel(slotIndex)} title="Leave interrupted jobs cancelled instead of restarting them">
                Cancel permanently
              </button>
              <button type="button" className="btn-status" disabled={actionPending} onClick={() => onResume(slotIndex)} title="Restart interrupted experiments from the beginning">
                {actionPending ? 'Starting…' : `▶ Play (${interrupted.length})`}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
