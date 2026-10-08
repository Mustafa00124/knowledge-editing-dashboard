import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../api.js'
import useCapabilities, { launchBlockers } from './useCapabilities.js'

// The 8 GPU queue cards are one shared queue: every page that launches
// anything (main experiments, in context, sweeps, tracing) stages onto these
// same cards and shows them. This hook polls the queue and holds the card
// actions; GpuQueue renders it and a drawer stages onto it.
export default function useQueue() {
  const [queue, setQueue] = useState([])
  const [queueError, setQueueError] = useState(null)
  const [error, setError] = useState(null)
  const [experimentTypes, setExperimentTypes] = useState([])
  const [investigationLabels, setInvestigationLabels] = useState({})
  const [rerunning, setRerunning] = useState(null)
  const [queueAction, setQueueAction] = useState(null)
  const request = useRef(null)
  const refreshPending = useRef(false)
  const mounted = useRef(false)
  const capabilities = useCapabilities()

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
    api.experimentTypes().then(setExperimentTypes).catch((e) => setError(e.message))
    api.investigations()
      .then((all) => setInvestigationLabels(Object.fromEntries(all.map((i) => [i.id, i.label]))))
      .catch(() => {})
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

  // Every type shares one machine, so their blockers are pooled.
  const blockers = [...new Set(experimentTypes.flatMap((t) => launchBlockers(capabilities, t.name)))]
  const launchBlocked = blockers.length ? 'Cannot launch on this machine; see the note above the queue' : null

  const replaceSlot = (slot, next) => setQueue((previous) => previous.map((item, index) => (index === slot ? next : item)))

  async function guarded(fn) {
    try {
      await fn()
      refresh()
    } catch (e) {
      setError(e.message)
    }
  }

  // Staging never runs anything: Launch on the card does.
  async function stage(slot, type, values, saveResults) {
    await api.stageQueueSlot(slot, type, values, saveResults)
    refresh()
  }

  async function stageSweep(slot, spec) {
    await api.stageSweepOnSlot(slot, spec)
    refresh()
  }

  const launch = (slot) => guarded(async () => {
    const res = await api.launchQueueSlot(slot)
    if (res?.launch_errors?.length) setError(`${res.launch_errors.length} run(s) could not start: ${res.launch_errors[0].error}`)
  })
  const clear = (slot) => guarded(() => api.clearQueueSlot(slot))
  const cancelSlot = (slot) => guarded(async () => {
    const res = await api.cancelQueueSlot(slot)
    // scancel can succeed overall while grumbling about one job that had
    // already finished on its own - worth showing, not worth failing on.
    if (res?.scancel_error) setError(`scancel: ${res.scancel_error}`)
  })
  const cancelJob = async (jobId) => {
    await api.cancelExperiment(jobId)
    refresh()
  }

  async function pause(slot) {
    if (queueAction !== null) return
    setQueueAction(slot)
    try {
      const next = await api.pauseQueueSlot(slot)
      replaceSlot(slot, next)
      setError(next?.scancel_error ? `Pause requested, but SLURM reported: ${next.scancel_error}` : null)
      refresh()
    } catch (e) {
      setError(e.message)
    } finally {
      setQueueAction(null)
    }
  }

  async function resume(slot) {
    if (queueAction !== null) return
    setQueueAction(slot)
    try {
      const next = await api.resumeQueueSlot(slot)
      replaceSlot(slot, next)
      setError(next?.resume_error ? `Some paused jobs could not restart: ${next.resume_error}` : null)
      refresh()
    } catch (e) {
      setError(e.message)
    } finally {
      setQueueAction(null)
    }
  }

  async function rerunFailed(slot) {
    if (rerunning !== null) return
    setRerunning(slot)
    try {
      const next = await api.rerunFailedQueueSlot(slot)
      replaceSlot(slot, next)
      setError(next.rerun_error ? `Some retries could not launch: ${next.rerun_error}` : null)
      refresh()
    } catch (e) {
      setError(e.message)
    } finally {
      setRerunning(null)
    }
  }

  // What a card holds, in words: the experiment type's label, or for a
  // sweep the investigation it tunes.
  function slotLabel(slot) {
    const staged = slot?.staged
    if (staged?.experiment_type === 'hparam_sweep') return `Sweep · ${staged.params.investigation_label || staged.params.investigation}`
    const job = slot?.jobs?.[0]
    if (job && (job.sweep_id || '').startsWith('hp-')) return `Sweep · ${investigationLabels[job.investigation] || job.investigation}`
    const type = staged?.experiment_type || job?.experiment_type
    return type ? experimentTypes.find((t) => t.name === type)?.label || type : null
  }

  return {
    queue, queueError, error, setError, experimentTypes, blockers, launchBlocked, refresh,
    stage, stageSweep, launch, clear, cancelSlot, cancelJob, pause, resume, rerunFailed,
    rerunning, queueAction, slotLabel,
  }
}
