import ExperimentsSubnav from '../components/ExperimentsSubnav.jsx'
import { useEffect, useState, useCallback, useRef } from 'react'
import { api } from '../api.js'
import ExperimentDrawer from '../components/ExperimentDrawer.jsx'
import QueueCard from '../components/QueueCard.jsx'
import GPUStatusPanel from '../components/GPUStatusPanel.jsx'
import QueueDetailModal from '../components/QueueDetailModal.jsx'
import LaunchBlockedNotice from '../components/LaunchBlockedNotice.jsx'
import useCapabilities, { launchBlockers } from '../lib/useCapabilities.js'

export default function Experiments() {
  const [queue, setQueue] = useState([])
  const [queueError, setQueueError] = useState(null)
  const request = useRef(null)
  const refreshPending = useRef(false)
  const mounted = useRef(false)
  const [experimentTypes, setExperimentTypes] = useState([])
  const [drawerOpen, setDrawerOpen] = useState(false)
  // Which queue card's detail modal is open, if any. Jobs are only ever
  // shown through the queue that launched them, so there's no separate
  // all-jobs list to keep in sync with this.
  const [openSlot, setOpenSlot] = useState(null)
  const [error, setError] = useState(null)
  const [rerunning, setRerunning] = useState(null)
  const [queueAction, setQueueAction] = useState(null)
  const capabilities = useCapabilities()
  // Every queue type shares one machine, so their blockers are pooled.
  const blockers = [...new Set(experimentTypes.flatMap((t) => launchBlockers(capabilities, t.name)))]
  const launchBlocked = blockers.length ? 'Cannot launch on this machine; see the note above the queue' : null

  const refresh = useCallback(() => {
    if (request.current) {
      // An action during a read needs fresh data after that read finishes.
      refreshPending.current = true
      return request.current
    }
    request.current = (async () => {
      do {
        refreshPending.current = false
        try {
          const next = await api.queue()
          if (mounted.current && !refreshPending.current) {
            setQueue(next)
            setQueueError(null)
          }
        } catch (e) {
          if (mounted.current) setQueueError(e.message)
        }
      } while (mounted.current && refreshPending.current)
    })().finally(() => { request.current = null })
    return request.current
  }, [])

  useEffect(() => {
    mounted.current = true
    let stopped = false
    let timer
    // An experiment type can opt out of the queue ("queue": false in its
    // dashboard.json) when it has its own page to be launched from -
    // causal tracing does. Without this it would show up in the New
    // Experiment drawer's type picker, and sort ahead of run_experiment.
    api.experimentTypes()
      .then((types) => setExperimentTypes(types.filter((t) => t.queue !== false)))
      .catch((e) => setError(e.message))
    async function poll() {
      await refresh()
      if (!stopped) timer = setTimeout(poll, 5000)
    }
    poll()
    return () => {
      stopped = true
      mounted.current = false
      clearTimeout(timer)
    }
  }, [refresh])

  async function handleStage(slot, type, values, saveResults) {
    await api.stageQueueSlot(slot, type, values, saveResults)
    refresh()
  }

  async function handleLaunch(slot) {
    try {
      await api.launchQueueSlot(slot)
      refresh()
    } catch (e) {
      setError(e.message)
    }
  }

  async function handleClear(slot) {
    try {
      await api.clearQueueSlot(slot)
      refresh()
    } catch (e) {
      setError(e.message)
    }
  }

  async function handleCancelSlot(slot) {
    try {
      const res = await api.cancelQueueSlot(slot)
      // scancel can succeed overall while grumbling about one job that had
      // already finished on its own - worth showing, not worth failing on.
      if (res?.scancel_error) setError(`scancel: ${res.scancel_error}`)
      refresh()
    } catch (e) {
      setError(e.message)
    }
  }

  async function handlePause(slot) {
    if (queueAction !== null) return
    setQueueAction(slot)
    try {
      const next = await api.pauseQueueSlot(slot)
      setQueue((previous) => previous.map((item, index) => index === slot ? next : item))
      if (next?.scancel_error) setError(`Pause requested, but SLURM reported: ${next.scancel_error}`)
      else setError(null)
      refresh()
    } catch (e) {
      setError(e.message)
    } finally {
      setQueueAction(null)
    }
  }

  async function handleResume(slot) {
    if (queueAction !== null) return
    setQueueAction(slot)
    try {
      const next = await api.resumeQueueSlot(slot)
      setQueue((previous) => previous.map((item, index) => index === slot ? next : item))
      setError(next?.resume_error ? `Some paused jobs could not restart: ${next.resume_error}` : null)
      refresh()
    } catch (e) {
      setError(e.message)
    } finally {
      setQueueAction(null)
    }
  }

  async function handleCancel(jobId) {
    await api.cancelExperiment(jobId)
    refresh()
  }

  async function handleRerunFailed(slot) {
    if (rerunning !== null) return
    setRerunning(slot)
    try {
      const next = await api.rerunFailedQueueSlot(slot)
      setQueue((previous) => previous.map((item, index) => index === slot ? next : item))
      setError(next.rerun_error ? `Some retries could not launch: ${next.rerun_error}` : null)
      refresh()
    } catch (e) {
      setError(e.message)
    } finally {
      setRerunning(null)
    }
  }

  return (
    <div>
      <ExperimentsSubnav />
      <div className="page-header">
        <h1>Main experiments</h1>
        <button className="btn-primary" onClick={() => setDrawerOpen(true)}>
          + New Experiment
        </button>
      </div>

      <LaunchBlockedNotice blockers={blockers} />
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
              fields={experimentTypes.find((t) => t.name === slot?.staged?.experiment_type)?.fields}
              onOpen={setOpenSlot}
              onLaunch={handleLaunch}
              onPause={handlePause}
              onResume={handleResume}
              onClear={handleClear}
              actionPending={queueAction === i}
              launchBlocked={launchBlocked}
            />
          ))}
        </div>
      </div>

      <GPUStatusPanel />

      {openSlot !== null && queue[openSlot] && (
        <QueueDetailModal
          slotIndex={openSlot}
          slot={queue[openSlot]}
          onClose={() => setOpenSlot(null)}
          onLaunch={(i) => { handleLaunch(i); }}
          onPause={handlePause}
          onResume={handleResume}
          onCancel={(i) => { handleCancelSlot(i); }}
          onClear={(i) => { handleClear(i); setOpenSlot(null) }}
          onCancelJob={handleCancel}
          onRerunFailed={handleRerunFailed}
          rerunning={rerunning === openSlot}
          actionPending={queueAction === openSlot}
          launchBlocked={launchBlocked}
        />
      )}

      <ExperimentDrawer
        open={drawerOpen}
        onToggle={() => setDrawerOpen((o) => !o)}
        onClose={() => setDrawerOpen(false)}
        experimentTypes={experimentTypes}
        queue={queue}
        onSubmit={handleStage}
      />
    </div>
  )
}
