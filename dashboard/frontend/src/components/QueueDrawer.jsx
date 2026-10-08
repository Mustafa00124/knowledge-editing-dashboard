import { useEffect, useState } from 'react'
import { pickSlotForStaging } from '../lib/pickSlot.js'

const SLOT_STATUS_SHORT = {
  empty: 'ready',
  staged: 'configured',
  running: 'running',
  paused: 'paused',
  completed: 'done',
  failed: 'failed',
}

// The slide-out panel every launching page uses: pick a GPU queue card, fill
// in the page's own form (children), and stage it onto that card. Staging
// runs nothing; Launch on the card does, once you are ready.
export default function QueueDrawer({ open, onToggle, onClose, title, queue, children, summary, submitLabel = 'Queue Experiment', canSubmit = true, onSubmit, wide = false }) {
  const [selectedSlot, setSelectedSlot] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  // Re-suggest a slot each time the drawer opens, from the queue's state at
  // that moment; another can still be clicked before submitting.
  useEffect(() => {
    if (open && queue.length) {
      setSelectedSlot((prev) => (prev !== null && !['running', 'paused'].includes(queue[prev]?.status) ? prev : pickSlotForStaging(queue)))
    }
  }, [open, queue])

  async function handleSubmit(e) {
    e.preventDefault()
    if (selectedSlot === null) {
      setError(`No GPU queue available: all ${queue.length} are currently running.`)
      return
    }
    setSubmitting(true)
    setError(null)
    try {
      await onSubmit(selectedSlot)
      onClose()
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <div className={`drawer-backdrop ${open ? 'open' : ''}`} onClick={onClose} />

      <button
        type="button"
        className={`drawer-tab ${open ? 'open' : ''}${wide ? ' is-wide' : ''}`}
        onClick={onToggle}
        title={open ? `Close ${title.toLowerCase()} panel` : `Open ${title.toLowerCase()} panel`}
        aria-label={open ? `Close ${title.toLowerCase()} panel` : `Open ${title.toLowerCase()} panel`}
      >
        {open ? '‹' : '›'}
      </button>

      <div className={`drawer ${open ? 'open' : ''}${wide ? ' is-wide' : ''}`}>
        <div className="drawer-header">
          <h2>{title}</h2>
          <button type="button" className="btn-plain" onClick={onClose}>✕</button>
        </div>

        {/* Enter in a text box must not queue the experiment by accident;
            only the button submits. */}
        <form onSubmit={handleSubmit} className="drawer-form"
          onKeyDown={(e) => { if (e.key === 'Enter' && e.target.tagName === 'INPUT') e.preventDefault() }}>
          <div className="pill-field">
            <div className="pill-field-label">GPU queue</div>
            <div className="pill-row">
              {queue.map((slot, i) => {
                const disabled = ['running', 'paused'].includes(slot.status)
                return (
                  <button
                    type="button"
                    key={i}
                    disabled={disabled}
                    className={`pill${selectedSlot === i ? ' selected' : ''}${disabled ? ' disabled' : ''}`}
                    onClick={() => setSelectedSlot(i)}
                    title={disabled ? `Currently ${slot.status}` : SLOT_STATUS_SHORT[slot.status]}
                  >
                    GPU {i + 1}
                  </button>
                )
              })}
            </div>
          </div>

          {children}

          {error && <div className="form-error">{error}</div>}

          <p className="sweep-count">
            {summary}
            {selectedSlot !== null ? ` on GPU ${selectedSlot + 1}` : ''}
          </p>

          <button type="submit" className="btn-primary" disabled={submitting || !canSubmit || selectedSlot === null}>
            {submitting ? 'Queuing…' : submitLabel}
          </button>
        </form>
      </div>
    </>
  )
}
