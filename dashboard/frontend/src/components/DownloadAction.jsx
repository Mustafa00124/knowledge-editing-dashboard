import { useState } from 'react'
import { Link } from 'react-router-dom'
import { formatBytes, isActive } from '../lib/useDownloads.js'

// One item's download control where that item is shown (a missing dataset
// on the Datasets page, a model card): a Download button, or its progress
// once queued. `item` is that item's entry from /api/downloads, and
// `onStart` is useDownloads().start. The Downloads page is the place to pick
// several at once; this links there.
export default function DownloadAction({ item, onStart, compact = false }) {
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  if (!item || item.installed) return null

  const task = item.task
  if (isActive(task)) {
    const pct = task.progress != null ? Math.round(task.progress * 100) : null
    return (
      <div className="dl-inline">
        <span className="dl-status is-running">
          {task.state === 'queued' ? 'Queued' : `Downloading${pct != null ? ` ${pct}%` : '…'}`}
        </span>
        <div className={`progress-track${pct == null ? ' is-indeterminate' : ''}`}>
          <div className="progress-fill" style={{ width: pct == null ? '35%' : `${Math.max(pct, 2)}%` }} />
        </div>
        {!compact && <Link to="/downloads">Details</Link>}
      </div>
    )
  }

  async function download() {
    setBusy(true)
    setError(null)
    try {
      await onStart([{ kind: item.kind, name: item.name }])
    } catch (e) {
      setError(e.message.replace(/^\d+ [^:]*: /, '').replace(/^\{"detail":"(.*)"\}$/, '$1'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="dl-inline">
      <button type="button" className={compact ? 'btn-download' : 'btn-primary'} disabled={busy} onClick={download}
        title={item.gated ? 'Gated: accept the license on huggingface.co and run `hf auth login` on this machine first' : undefined}>
        {busy ? 'Queueing…' : `Download${compact ? '' : ` ${item.label}`} (${formatBytes(item.bytes)})`}
      </button>
      {!compact && <span className="dl-dim">or <Link to="/downloads">choose several on the Downloads page</Link></span>}
      {error && <span className="dl-bar-warning" role="alert">{error}</span>}
    </div>
  )
}
