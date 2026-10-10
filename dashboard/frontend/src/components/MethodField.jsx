import { useState } from 'react'
import SelectAllCircle from './SelectAllCircle.jsx'
import { groupSelectState, toggleGroup } from '../lib/groupSelect.js'

// Category first, then method within that category - same two-level
// pattern as DatasetField (benchmark → subset). Not-yet-wired methods, and
// methods outside the core set (`core: false` in dashboard.json), stay
// visible but disabled, same convention as the Model row.
const selectable = (m) => m.available !== false && m.core !== false
const disabledReason = (m) => (m.available === false ? 'Not wired up yet' : 'Not in the core method set')

//
// `value` is always an array. When the field is sweepable, clicking
// toggles and the selection persists across categories, so a sweep can mix
// families (ROME from Locate-and-Edit, IKE from In-Context); the summary
// line below the rows is what keeps an out-of-view selection visible.
export default function MethodField({ field, value, onChange }) {
  const categories = field.categories || []
  const selected = Array.isArray(value) ? value : value == null ? [] : [value]
  const multi = field.sweepable === true
  const [category, setCategory] = useState(
    () => categories.find((c) => c.methods.some((m) => selected.includes(m.value))) || categories[0],
  )

  const all = categories.flatMap((c) => c.methods)
  const labelFor = (v) => all.find((m) => m.value === v)?.label || v

  function selectCategory(next) {
    setCategory(next)
    // Only single-select needs to move the selection when the category
    // changes - a sweep keeps whatever is already picked elsewhere.
    if (multi) return
    if (!next.methods.some((m) => selected.includes(m.value) && selectable(m))) {
      const firstAvailable = next.methods.find(selectable)
      if (firstAvailable) onChange([firstAvailable.value])
    }
  }

  function choose(v) {
    if (!multi) return onChange([v])
    // Deselecting the last one is allowed - the drawer reports 0
    // experiments and disables Queue, which is clearer than a pill that
    // refuses to switch off.
    onChange(selected.includes(v) ? selected.filter((x) => x !== v) : [...selected, v])
  }

  // The options actually selectable in the open family - disabled ones are
  // shown but can't be swept, so they don't count toward "all".
  const groupValues = (category?.methods || []).filter(selectable).map((m) => m.value)

  return (
    <div className="pill-field">
      <div className="pill-field-label">
        {field.label}
        {selected.length > 1 && <span className="sweep-badge">sweeping {selected.length}</span>}
      </div>

      <div className="pill-row hierarchy-categories" aria-label="Method families">
        {categories.map((c) => (
          <button
            type="button"
            key={c.label}
            className={`pill hierarchy-category${c === category ? ' selected' : ''}`}
            aria-pressed={c === category}
            onClick={() => selectCategory(c)}
          >
            {c.label}
            {multi && c.methods.some((m) => selected.includes(m.value)) && <span className="pill-dot" aria-hidden="true" />}
          </button>
        ))}
      </div>

      <div className="pill-row hierarchy-options" aria-label={`${category?.label || 'Method'} options`}>
        {multi && (
          <SelectAllCircle
            state={groupSelectState(groupValues, selected)}
            groupLabel={`${category?.label || 'method'} methods`}
            disabled={!groupValues.length}
            onClick={() => onChange(toggleGroup(groupValues, selected))}
          />
        )}
        {category?.methods.map((m) => {
          const disabled = !selectable(m)
          const isOn = !disabled && selected.includes(m.value)
          return (
            <button
              type="button"
              key={m.value}
              disabled={disabled}
              className={`pill hierarchy-option${isOn ? ' selected' : ''}${disabled ? ' disabled' : ''}`}
              aria-pressed={isOn}
              title={disabled ? disabledReason(m) : m.note}
              onClick={() => choose(m.value)}
            >
              {m.label}
            </button>
          )
        })}
      </div>

      {multi && selected.length > 1 && (
        <div className="sweep-summary">Sweeping: {selected.map(labelFor).join(' → ')}</div>
      )}
    </div>
  )
}
