import { useCallback, useEffect, useState } from 'react'
import { api } from '../api.js'
import { toGibibytes } from '../lib/formatMetric.js'

const STATUS_LABEL = {
  available: 'Available',
  dashboard: 'Dashboard job',
  allocated: 'Allocated elsewhere',
  unavailable: 'Node unavailable',
  unknown: 'Allocation unknown',
}

// What a tile says under the GPU number. A job we launched keeps its
// queue-card wording. Anything else names whoever holds the card, because
// "Allocated elsewhere" hid the case that matters most in practice: our own
// interactive sessions sitting on a GPU doing nothing.
function tileDetail(gpu) {
  if (gpu.job?.slot_index != null) {
    return { main: `Queue ${gpu.job.slot_index + 1} · job ${gpu.job.job_id}`, sub: gpu.job.run_name }
  }
  if (gpu.owner) {
    const who = gpu.owner.is_self ? 'You' : gpu.owner.user
    return { main: `${who} · ${gpu.owner.job_name || 'job'}`, sub: `Job ${gpu.owner.job_id}` }
  }
  return { main: STATUS_LABEL[gpu.status], sub: null }
}

function MemoryGauge({ gpu, capacityMb }) {
  const metrics = gpu.job?.metrics
  const sampled = Number.isFinite(metrics?.gpu_mem_alloc_mb) && metrics.gpu_mem_alloc_mb >= 0
  // A free card really is at zero and we know how big it is, so say 0 rather
  // than a dash. A dash means "we cannot see", which is not the same as
  // "empty", and conflating the two was the confusing part: someone else's
  // job and an idle card looked identical.
  const idle = !sampled && gpu.status === 'available' && Number.isFinite(capacityMb)
  const used = sampled ? metrics.gpu_mem_alloc_mb : idle ? 0 : null
  const total = Number.isFinite(metrics?.gpu_mem_total_mb) ? metrics.gpu_mem_total_mb : capacityMb

  const hasTotal = Number.isFinite(total) && total > 0
  const fraction = used !== null && hasTotal ? Math.min(1, used / total) : null
  const circumference = 2 * Math.PI * 36
  // Stored values are decimal MB (bytes / 1e6); shown as GiB to match
  // nvidia-smi and the card's advertised size.
  const amount = used !== null ? `${toGibibytes(used).toFixed(1)} GiB` : '—'
  const capacity = hasTotal ? `/ ${toGibibytes(total).toFixed(1)} GiB` : null

  const sampleTime = metrics?.at ? new Date(metrics.at).toLocaleString() : null
  const description = sampled
    ? `PyTorch memory at this run's latest checkpoint: ${amount}${capacity ? ` ${capacity}` : ''}${sampleTime ? `, sampled ${sampleTime}` : ''}`
    : idle
      ? `Nothing is running on this GPU, so none of its ${toGibibytes(total).toFixed(1)} GiB is allocated`
      : gpu.job
        ? 'This run has not written its first checkpoint yet, so its memory is not sampled'
        : gpu.owner
          ? `Held by ${gpu.owner.is_self ? 'your own' : "another user's"} job (${gpu.owner.job_name}), which does not report memory here`
          : 'No memory reading available for this GPU'
  const caption = sampled ? 'Checkpoint VRAM' : idle ? 'Idle, nothing allocated' : 'Not visible'

  return (
    <div className="gpu-gauge-group">
      <div className={`gpu-memory-gauge${used === null ? ' is-unsampled' : ''}`} role="img" aria-label={description} title={description}>
        <svg viewBox="0 0 96 96" aria-hidden="true">
          <circle className="gpu-gauge-track" cx="48" cy="48" r="36" />
          {fraction !== null && <circle className="gpu-gauge-fill" cx="48" cy="48" r="36" style={{ strokeDasharray: circumference, strokeDashoffset: circumference * (1 - fraction) }} />}
        </svg>
        <span className="gpu-gauge-value">
          <strong>{amount}</strong>
          {capacity && <small>{capacity}</small>}
        </span>
      </div>
      <span className="gpu-gauge-caption">{caption}</span>
    </div>
  )
}

export default function GPUStatusPanel() {
  const [snapshot, setSnapshot] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [pendingOpen, setPendingOpen] = useState(false)

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      const next = await api.gpuStatus()
      setSnapshot(next)
      setError(null)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
    const timer = setInterval(refresh, 60_000)
    const onVisible = () => { if (document.visibilityState === 'visible') refresh() }
    document.addEventListener('visibilitychange', onVisible)
    return () => {
      clearInterval(timer)
      document.removeEventListener('visibilitychange', onVisible)
    }
  }, [refresh])

  useEffect(() => {
    if (!pendingOpen) return
    const onKey = (e) => { if (e.key === 'Escape') setPendingOpen(false) }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [pendingOpen])

  const gpus = snapshot?.nodes.flatMap((node) => node.gpus) || []
  const available = gpus.filter((gpu) => gpu.status === 'available').length
  const assigned = gpus.filter((gpu) => gpu.status === 'dashboard').length
  const yoursElsewhere = gpus.filter((gpu) => gpu.owner?.is_self && gpu.status !== 'dashboard').length
  const otherUsers = gpus.filter((gpu) => gpu.owner && !gpu.owner.is_self).length

  return (
    <section className="gpu-status-panel" aria-label="SLURM GPU status">
      <div className="gpu-status-header">
        <div>
          <h2>GPU availability</h2>
          <p>{snapshot?.partition === 'local' || (!snapshot && error?.includes('local GPU status'))
            ? 'GPUs on this machine · local jobs run one at a time on GPU 0.'
            : `SLURM allocations in ${snapshot?.partition || 'AAIL'} · queue card numbers are separate from physical GPU numbers.`}</p>
        </div>
        <button type="button" className="btn-plain-small" onClick={refresh} disabled={loading}>
          {loading ? 'Refreshing…' : 'Refresh'}
        </button>
      </div>

      {error && (error.includes('no NVIDIA GPU detected')
        ? <p className="empty">No NVIDIA GPU was found on this machine, so there is nothing to show here.</p>
        : <p className="form-error">Could not refresh GPU status: {error.replace(/^\d+ [^:]*: /, '').replace(/^\{"detail":"(.*)"\}$/, '$1')}</p>)}
      {snapshot && <>
        <div className="gpu-status-summary">
          <span><strong>{available}</strong> available</span>
          <span><strong>{assigned}</strong> assigned to dashboard jobs</span>
          <span><strong>{yoursElsewhere}</strong> yours outside the dashboard</span>
          <span><strong>{otherUsers}</strong> held by other users</span>
          <button type="button" className="gpu-pending-button" onClick={() => setPendingOpen(true)}>
            <strong>{snapshot.pending_jobs.length}</strong> pending jobs · View list
          </button>
          <span className="gpu-status-time">Updated {new Date(snapshot.checked_at).toLocaleTimeString()}</span>
        </div>

        {snapshot.nodes.map((node) => (
          <div className="gpu-node" key={node.name}>
            <h3>{node.name} <span>· {node.gpu_type} · {node.state.toLowerCase()}</span></h3>
            <div className="gpu-grid">
              {node.gpus.map((gpu) => {
                const detail = tileDetail(gpu)
                return (
                  <div
                    className={`gpu-tile gpu-${gpu.status}${gpu.owner?.is_self && gpu.status !== 'dashboard' ? ' gpu-owner-self' : ''}`}
                    key={gpu.index}
                  >
                    <strong>GPU {gpu.index}</strong>
                    <MemoryGauge gpu={gpu} capacityMb={node.gpu_memory_total_mb} />
                    <span className="gpu-tile-detail" title={detail.main}>{detail.main}</span>
                    {detail.sub && <small className="gpu-tile-sub" title={detail.sub}>{detail.sub}</small>}
                  </div>
                )
              })}
            </div>
          </div>
        ))}

      </>}
      {!snapshot && !error && <p className="empty">Reading SLURM status…</p>}
      <p className="gpu-status-note">VRAM is PyTorch memory from the latest checkpoint of our own runs, not live whole-device usage. A free card reads 0; a dash means the figure is not visible to us, either because another job holds the GPU or because our run has not checkpointed yet. Updates every minute.</p>
      {pendingOpen && snapshot && (
        <div className="modal-backdrop" onClick={() => setPendingOpen(false)}>
          <div className="modal gpu-pending-modal" role="dialog" aria-modal="true" aria-label="Pending dashboard jobs" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title-group"><h2>Pending dashboard jobs ({snapshot.pending_jobs.length})</h2></div>
              <button type="button" className="btn-plain" onClick={() => setPendingOpen(false)} aria-label="Close">✕</button>
            </div>
            <div className="modal-body">
              <p className="gpu-status-note">SLURM can change scheduling order. The reason explains why each job is waiting.</p>
              {snapshot.pending_jobs.length ? (
                <div className="gpu-pending-list">
                  {snapshot.pending_jobs.map((job) => (
                    <div className="gpu-pending-row" key={job.job_id}>
                      <strong>{job.slot_index != null ? `Queue ${job.slot_index + 1}` : 'Dashboard'}</strong>
                      <span>Job {job.job_id}</span>
                      <span className="gpu-pending-reason">{job.reason}</span>
                    </div>
                  ))}
                </div>
              ) : <p>No dashboard jobs waiting in SLURM.</p>}
            </div>
          </div>
        </div>
      )}
    </section>
  )
}
