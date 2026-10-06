import { useState } from 'react'
import { api } from '../api.js'

// "Clear finished" for a job table: finished jobs of this experiment type
// stop listing (they stay in the dashboard database; logs and results on
// disk are untouched). Shown only when something finished.
export default function ClearFinishedButton({ experiment, jobs, activeStates, onCleared }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  if (!jobs.some((job) => !activeStates.includes(job.status?.state))) return null
  async function clear() {
    setBusy(true)
    setError(null)
    try {
      await api.clearExperiments(experiment)
      onCleared?.()
    } catch (e) {
      setError(String(e.message || e))
    }
    setBusy(false)
  }
  return (
    <span className="dl-task-controls">
      {error && <span className="archive-line-warn">{error}</span>}
      <button type="button" className="btn-plain-small" onClick={clear} disabled={busy}
        title="Take finished jobs off this table; nothing is deleted">
        {busy ? 'Clearing…' : 'Clear finished'}
      </button>
    </span>
  )
}
