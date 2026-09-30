import { useState } from 'react'
import { api } from '../api.js'

// The two-step move both the Results page and the Archive page perform: ask
// the backend what would move, show that plan, then commit exactly the runs
// it said were movable. Kept in one place so archiving from a results cell
// and archiving from the Archive page can never diverge in what they
// actually do.
export function useArchiveMove(onMoved) {
  const [direction, setDirection] = useState(null)
  const [plan, setPlan] = useState([])
  const [reason, setReason] = useState('')
  const [result, setResult] = useState(null)
  const [pending, setPending] = useState(false)
  const [error, setError] = useState(null)

  const call = (dir, runs, why, dryRun) =>
    (dir === 'archive' ? api.archiveRuns(runs, why, dryRun) : api.restoreRuns(runs, dryRun))

  async function begin(dir, runs) {
    setDirection(dir)
    setPlan([])
    setResult(null)
    setError(null)
    setReason('')
    setPending(true)
    try {
      setPlan((await call(dir, runs, '', true)).plan)
    } catch (e) {
      setError(String(e.message || e))
    }
    setPending(false)
  }

  async function confirm() {
    setPending(true)
    setError(null)
    try {
      const res = await call(direction, plan.filter((row) => row.ok).map((row) => row.run), reason, false)
      setResult(res)
      if (res.moved.length && onMoved) onMoved(res)
    } catch (e) {
      setError(String(e.message || e))
    }
    setPending(false)
  }

  function close() {
    setDirection(null)
    setPlan([])
    setResult(null)
    setError(null)
  }

  return { direction, plan, reason, setReason, result, pending, error, begin, confirm, close, open: direction !== null }
}
