import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../api.js'

export function formatBytes(bytes) {
  if (bytes === null || bytes === undefined) return '?'
  if (bytes >= 1e9) return `${(bytes / 1e9).toFixed(1)} GB`
  if (bytes >= 1e6) return `${Math.round(bytes / 1e6)} MB`
  return `${Math.max(1, Math.round(bytes / 1e3))} KB`
}

export const isActive = (task) => task && (task.state === 'queued' || task.state === 'downloading')

// The /api/downloads overview (every downloadable item with its status,
// plus the task list), polled quickly while something is downloading and
// slowly otherwise. `start` queues items and refreshes straight away.
// `onFinished` fires when a task this page saw running stops, so a page
// can reload whatever that download unlocks.
export default function useDownloads({ onFinished } = {}) {
  const [overview, setOverview] = useState(null)
  const [error, setError] = useState(null)
  const seenActive = useRef(new Set())
  const finished = useRef(onFinished)
  finished.current = onFinished

  const refresh = useCallback(async () => {
    try {
      const next = await api.downloads()
      setOverview(next)
      setError(null)
      const active = new Set(next.tasks.filter(isActive).map((t) => t.id))
      const done = [...seenActive.current].filter((id) => !active.has(id))
      seenActive.current = active
      if (done.length) finished.current?.(next.tasks.filter((t) => done.includes(t.id)))
      return next
    } catch (e) {
      setError(e.message)
      return null
    }
  }, [])

  // Restartable so that starting a download switches to fast polling at
  // once rather than after the slow interval runs out.
  const poll = useRef(() => {})
  useEffect(() => {
    let stopped = false
    let timer
    poll.current = async () => {
      clearTimeout(timer)
      const next = await refresh()
      if (stopped) return
      const busy = next?.tasks.some(isActive)
      clearTimeout(timer)
      timer = setTimeout(() => poll.current(), busy ? 2000 : 10000)
    }
    poll.current()
    return () => { stopped = true; clearTimeout(timer) }
  }, [refresh])

  const start = useCallback(async (items) => {
    const tasks = await api.startDownloads(items)
    await poll.current()
    return tasks
  }, [])

  const cancel = useCallback(async (id) => {
    await api.cancelDownload(id)
    await poll.current()
  }, [])

  const find = useCallback((kind, name) =>
    overview?.items.find((item) => item.kind === kind && item.name === name), [overview])

  return { overview, error, refresh, start, cancel, find }
}
