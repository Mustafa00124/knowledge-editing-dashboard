import { useState } from 'react'
import SelectAllCircle from './SelectAllCircle.jsx'
import { groupSelectState, toggleGroup } from '../lib/groupSelect.js'

// Family first, then tuning stage within that family - the same two-level
// pattern as DatasetField (benchmark → subset) and MethodField (category →
// method). Family-first is deliberate: the comparison these variants exist
// for is base vs instruct vs reasoning *on a fixed pretrain*, so the pairing
// should be one row, not scattered across three type tabs. The type still
// reads at a glance from the badge on each pill.
//
// Unlike MethodField, the options aren't nested inside the categories:
// `field.options` stays a flat list (Results.jsx and the sweep validation
// both look models up there by value) and `field.families` only holds
// values, resolved here. One list, so the two can't drift.
const TYPE_LABEL = { raw: 'raw', chat: 'chat', reasoning: 'reasoning' }

export default function ModelField({ field, value, onChange }) {
  const options = field.options || []
  const byValue = Object.fromEntries(options.map((o) => [o.value, o]))
  // Within a family the variant is the distinguishing label ("Base" vs
  // "Instruct"). The catch-all family holds unrelated models whose variants
  // collide, so there the model's own name is what tells them apart.
  const families = (field.families || []).map((f) => {
    const models = f.models.map((v) => byValue[v]).filter(Boolean)
    const variants = models.map((m) => m.variant)
    const unique = new Set(variants).size === variants.length
    return { ...f, models, useVariant: unique }
  })

  const selected = Array.isArray(value) ? value : value == null ? [] : [value]
  const multi = field.sweepable === true
  const [family, setFamily] = useState(
    () => families.find((f) => f.models.some((m) => selected.includes(m.value))) || families[0],
  )

  const labelFor = (v) => byValue[v]?.label || v

  function selectFamily(next) {
    setFamily(next)
    // Only single-select needs to move the selection when the family
    // changes - a sweep keeps whatever is already picked elsewhere.
    if (multi) return
    if (!next.models.some((m) => selected.includes(m.value) && m.available !== false)) {
      const firstAvailable = next.models.find((m) => m.available !== false)
      if (firstAvailable) onChange([firstAvailable.value])
    }
  }

  function choose(v) {
    if (!multi) return onChange([v])
    onChange(selected.includes(v) ? selected.filter((x) => x !== v) : [...selected, v])
  }

  const groupValues = (family?.models || []).filter((m) => m.available !== false).map((m) => m.value)

  return (
    <div className="pill-field">
      <div className="pill-field-label">
        {field.label}
        {selected.length > 1 && <span className="sweep-badge">sweeping {selected.length}</span>}
      </div>

      <div className="pill-row hierarchy-categories" aria-label="Model families">
        {families.map((f) => (
          <button
            type="button"
            key={f.label}
            className={`pill hierarchy-category${f === family ? ' selected' : ''}`}
            aria-pressed={f === family}
            onClick={() => selectFamily(f)}
          >
            {f.label}
            {multi && f.models.some((m) => selected.includes(m.value)) && <span className="pill-dot" aria-hidden="true" />}
          </button>
        ))}
      </div>

      <div className="pill-row hierarchy-options" aria-label={`${family?.label || 'Model'} variants`}>
        {multi && (
          <SelectAllCircle
            state={groupSelectState(groupValues, selected)}
            groupLabel={`${family?.label || 'model'} variants`}
            disabled={!groupValues.length}
            onClick={() => onChange(toggleGroup(groupValues, selected))}
          />
        )}
        {family?.models.map((m) => {
          const disabled = m.available === false
          const isOn = !disabled && selected.includes(m.value)
          return (
            <button
              type="button"
              key={m.value}
              disabled={disabled}
              className={`pill hierarchy-option${isOn ? ' selected' : ''}${disabled ? ' disabled' : ''}`}
              aria-pressed={isOn}
              title={m.note || (disabled ? 'Not wired up yet' : m.label)}
              onClick={() => choose(m.value)}
            >
              {(family.useVariant && m.variant) || m.label}
              {m.model_type && (
                <span className={`model-type-badge model-type-${m.model_type}`}>
                  {TYPE_LABEL[m.model_type] || m.model_type}
                </span>
              )}
            </button>
          )
        })}
      </div>

      <div className="pill-field-note">
        raw = no post-training · chat = instruction tuned · reasoning = emits thinking traces,
        so teacher-forced scoring does not apply
      </div>

      {multi && selected.length > 1 && (
        <div className="sweep-summary">Sweeping: {selected.map(labelFor).join(' → ')}</div>
      )}
    </div>
  )
}
