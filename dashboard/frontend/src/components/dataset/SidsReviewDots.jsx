import { useState } from 'react'

// Review dots for Sid's Dataset (CRITERIA.md, manual rules), shown on the
// Datasets page's browser only: per record, one line per manual rule (in a
// dotted box under the tags), and per query beside its audit dots. One dot per reviewer in a fixed
// order (Codex, Claude, Mustafa, Fengchun, Adarsh): yellow not reviewed yet
// (or not pushed), green fine, red flagged. A ring inside a red dot marks an
// angle (an idea to add or drop), which only the CLI sets, with an optional
// note. In review mode the current reviewer's own dots cycle yellow -> green
// -> red -> yellow on click; any other dot shows its note, if any, on click.
// Marks are saved in datasets/SidsDataset/reviews.json.

const STATE_TEXT = { yellow: 'not reviewed yet', green: 'reviewed, fine', red: 'flagged' }

export const markOf = (state, rid, item, who) => state.marks[rid]?.[item]?.[who] || null
const stateOf = (m) => m?.state || 'yellow'

export function notReviewedBy(state, rid, me) {
  return state.rules.some((r) => !markOf(state, rid, r.key, me))
}

function dotTitle(name, m) {
  const s = stateOf(m)
  const kind = s === 'red' && m.kind ? ` (${m.kind})` : ''
  const when = m?.at ? `, ${m.at.replace('T', ' ')}` : ''
  return `${name}: ${STATE_TEXT[s]}${kind}${when}${m?.stale ? ', record changed since' : ''}${m?.comment ? `. ${m.comment}` : ''}`
}

// One item's dots (a rule of a record, or a query) and, under them, the
// note of the dot last clicked.
export function ReviewDots({ rid, item, state, me, reviewMode, onMark, label }) {
  const [open, setOpen] = useState(null)       // reviewer whose comment is shown
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const canEdit = reviewMode && me && state.can_mark_as?.includes(me)
  const save = (s) => {
    setBusy(true)
    setError(null)
    onMark(rid, item, s).catch((err) => setError(String(err.message || err))).finally(() => setBusy(false))
  }
  const click = (who) => {
    if (canEdit && who === me) {
      setOpen(null)
      const s = stateOf(markOf(state, rid, item, me))
      save(s === 'yellow' ? 'green' : s === 'green' ? 'red' : null)
      return
    }
    setOpen((o) => (o === who ? null : who))
  }
  const shown = open && markOf(state, rid, item, open)
  const name = (who) => state.reviewers.find((r) => r.id === who)?.name || who
  return (
    <span className="sids-rvd">
      <span className="sids-rvd-dots">
        {label && <span className="sids-rvd-label">{label}</span>}
        {state.reviewers.map((r) => {
          const m = markOf(state, rid, item, r.id)
          const s = stateOf(m)
          const mine = canEdit && r.id === me
          const title = dotTitle(r.name, m) + (mine ? `. Click: ${s === 'yellow' ? 'green' : s === 'green' ? 'red' : 'clear'}.` : '')
          const dot = (
            <button key={r.id} type="button" title={title} aria-label={title} disabled={busy}
              className={`sids-rvd-dot is-${s}${m?.kind === 'angle' && s === 'red' ? ' is-angle' : ''}${m?.stale ? ' is-stale' : ''}${mine ? ' is-mine' : ''}`}
              onClick={(e) => { e.stopPropagation(); click(r.id) }} />
          )
          // Record level: each dot carries its reviewer's name.
          return label ? (
            <span key={r.id} className={`sids-rvd-named${mine ? ' is-mine' : ''}`}>{dot}<span className="sids-rvd-name">{r.name}</span></span>
          ) : dot
        })}
      </span>
      {shown && (
        <span className="sids-rvd-comment">
          <strong>{name(open)}</strong>: {STATE_TEXT[shown.state]}{shown.state === 'red' && shown.kind ? ` (${shown.kind})` : ''}
          {shown.stale ? ', record changed since' : ''}{shown.comment ? `. ${shown.comment}` : ''}
        </span>
      )}
      {open && !shown && <span className="sids-rvd-comment"><strong>{name(open)}</strong>: not reviewed yet</span>}
      {error && <span className="sids-rvd-comment is-error">{error}</span>}
    </span>
  )
}

// The record-level block, a dotted box under the tags: one line per manual
// rule, its name then the five reviewer dots.
export function RecordReview({ rid, state, me, reviewMode, onMark }) {
  return (
    <div className="sids-rvd-record">
      {state.rules.map((rule) => (
        <ReviewDots key={rule.key} rid={rid} item={rule.key} state={state} me={me} reviewMode={reviewMode}
          onMark={onMark} label={<span title={rule.statement}>{rule.title}</span>} />
      ))}
    </div>
  )
}

export function ReviewLegend() {
  return (
    <span className="sids-rvd-legend">
      <span><span className="sids-rvd-dot is-yellow" />not reviewed</span>
      <span><span className="sids-rvd-dot is-green" />fine</span>
      <span><span className="sids-rvd-dot is-red" />flagged</span>
    </span>
  )
}
