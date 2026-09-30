import { useEffect } from 'react'

// One dialog for both directions. The parent asks the backend what *would*
// move (a dry run) and hands the answer here, so the list you approve is the
// one the backend just planned against the real directories - not a guess
// assembled in the browser from a manifest that may be seconds stale.
export default function ArchiveConfirm({ direction, plan = [], reason, onReason, result, pending, error, onConfirm, onClose }) {
  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape' && !pending) onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose, pending])

  const verb = direction === 'archive' ? 'Archive' : 'Restore'
  const movable = plan.filter((row) => row.ok)
  const blocked = plan.filter((row) => !row.ok)
  const totalMb = movable.reduce((sum, row) => sum + (row.size_mb || 0), 0)

  return (
    <div className="modal-backdrop" onClick={() => !pending && onClose()}>
      <div
        className="modal archive-modal"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label={`${verb} runs`}
      >
        <div className="modal-header">
          <div className="modal-title-group">
            <h2>
              {result ? `${verb}d` : plan.length ? `${verb} ${movable.length} run${movable.length === 1 ? '' : 's'}` : `${verb} runs`}
            </h2>
          </div>
          <button type="button" className="btn-plain" onClick={onClose} disabled={pending} aria-label="Close">✕</button>
        </div>

        <div className="modal-body">
          {pending && !plan.length && !result && <p className="archive-line">Checking what would move…</p>}
          {result ? (
            <>
              <p className="archive-line">
                Moved {result.moved.length} run{result.moved.length === 1 ? '' : 's'}
                {direction === 'archive' ? ' into the archive.' : ' back into the live results.'}
              </p>
              <ul className="archive-plan">
                {result.moved.map((run) => <li key={run} className="archive-plan-ok"><code>{run}</code></li>)}
              </ul>
              {result.skipped.length > 0 && (
                <>
                  <p className="archive-line archive-line-warn">Left alone:</p>
                  <ul className="archive-plan">
                    {result.skipped.map((row) => (
                      <li key={row.run} className="archive-plan-blocked">
                        <code>{row.run}</code> <span>{row.problem}</span>
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </>
          ) : (
            <>
              {movable.length > 0 && (
                <>
                  <p className="archive-line">
                    {direction === 'archive'
                      ? 'These directories move out of runs/, so the manifest stops listing them. Nothing is deleted, and Restore puts them back.'
                      : 'These directories move back into runs/ and reappear on the Results page.'}
                  </p>
                  <ul className="archive-plan">
                    {movable.map((row) => (
                      <li key={row.run} className="archive-plan-ok">
                        <code>{row.run}</code>
                        <span>{row.files} files · {row.size_mb} MB → {row.to}</span>
                      </li>
                    ))}
                  </ul>
                  <p className="archive-line archive-line-dim">{totalMb.toFixed(1)} MB in total.</p>
                </>
              )}

              {blocked.length > 0 && (
                <>
                  <p className="archive-line archive-line-warn">
                    {blocked.length} will be left alone:
                  </p>
                  <ul className="archive-plan">
                    {blocked.map((row) => (
                      <li key={row.run} className="archive-plan-blocked">
                        <code>{row.run}</code> <span>{row.problem}</span>
                      </li>
                    ))}
                  </ul>
                </>
              )}

              {direction === 'archive' && onReason && (
                <label className="archive-reason">
                  <span>Why (optional, stored with the run)</span>
                  <input
                    type="text"
                    value={reason}
                    placeholder="e.g. superseded by the rerun"
                    onChange={(e) => onReason(e.target.value)}
                  />
                </label>
              )}
            </>
          )}

          {error && <p className="archive-line archive-line-warn">{error}</p>}
        </div>

        <div className="modal-actions archive-actions">
          <button type="button" className="btn-plain-small" onClick={onClose} disabled={pending}>
            {result ? 'Close' : 'Cancel'}
          </button>
          {!result && (
            <button
              type="button"
              className="btn-primary"
              onClick={onConfirm}
              disabled={pending || movable.length === 0}
            >
              {pending ? 'Moving…' : `${verb} ${movable.length} run${movable.length === 1 ? '' : 's'}`}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
