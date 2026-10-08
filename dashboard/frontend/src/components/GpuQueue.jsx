import { useState } from 'react'
import QueueCard from './QueueCard.jsx'
import QueueDetailModal from './QueueDetailModal.jsx'
import GPUStatusPanel from './GPUStatusPanel.jsx'
import LaunchBlockedNotice from './LaunchBlockedNotice.jsx'

// The shared GPU queue cards (see lib/useQueue.js), the open card's detail,
// and what the GPUs are doing. The same on every page that launches.
export default function GpuQueue({ q }) {
  const [openSlot, setOpenSlot] = useState(null)
  const { queue, queueError, error } = q

  return (
    <>
      <LaunchBlockedNotice blockers={q.blockers} />
      {error && <div className="form-error">{error}</div>}
      {queueError && <div className="form-error" role="alert">Queue refresh failed: {queueError}. Retrying automatically.</div>}

      <div className="queue-section">
        <div className="queue-grid" aria-busy={queue.length === 0 && !queueError}>
          {queue.length === 0 && Array.from({ length: 8 }, (_, i) => (
            <div className="queue-card is-loading" key={i}>
              <div className="queue-card-top">
                <span className="queue-slot-label">GPU Queue {i + 1}</span>
                <span className="queue-state">{queueError ? 'Unavailable' : 'Loading…'}</span>
              </div>
              <div className="queue-sub">{queueError ? 'Waiting to retry' : 'Fetching job statuses'}</div>
              <div className="queue-card-body" aria-hidden="true">
                <div className="queue-skeleton" />
                <div className="queue-skeleton is-short" />
              </div>
            </div>
          ))}
          {queue.map((slot, i) => (
            <QueueCard
              key={i}
              slotIndex={i}
              slot={slot}
              label={q.slotLabel(slot)}
              fields={q.experimentTypes.find((t) => t.name === slot?.staged?.experiment_type)?.fields}
              onOpen={setOpenSlot}
              onLaunch={q.launch}
              onPause={q.pause}
              onResume={q.resume}
              onClear={q.clear}
              actionPending={q.queueAction === i}
              launchBlocked={q.launchBlocked}
            />
          ))}
        </div>
      </div>

      <GPUStatusPanel />

      {openSlot !== null && queue[openSlot] && (
        <QueueDetailModal
          slotIndex={openSlot}
          slot={queue[openSlot]}
          label={q.slotLabel(queue[openSlot])}
          onClose={() => setOpenSlot(null)}
          onLaunch={q.launch}
          onPause={q.pause}
          onResume={q.resume}
          onCancel={q.cancelSlot}
          onClear={(i) => { q.clear(i); setOpenSlot(null) }}
          onCancelJob={q.cancelJob}
          onRerunFailed={q.rerunFailed}
          rerunning={q.rerunning === openSlot}
          actionPending={q.queueAction === openSlot}
          launchBlocked={q.launchBlocked}
        />
      )}
    </>
  )
}
