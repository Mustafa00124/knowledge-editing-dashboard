import { useState } from 'react'

export default function PillField({ field, value, onChange }) {
  const options = field.options || []
  // Local, not derived from `value` on every render - otherwise clicking
  // "Custom" on a field whose value still matches a pill would immediately
  // get overridden back to that pill. Parent remounts us (via key) when the
  // field set changes, which is when this needs to reset.
  const [customMode, setCustomMode] = useState(() => !options.some((o) => o.value === value))

  return (
    <div className="pill-field">
      <div className="pill-field-label">
        {field.label}
        {field.note && <span className="pill-field-note">: {field.note}</span>}
      </div>
      <div className="pill-row">
        {options.map((opt) => {
          const disabled = opt.available === false
          const selected = !customMode && value === opt.value
          return (
            <button
              type="button"
              key={opt.value}
              disabled={disabled}
              className={`pill${selected ? ' selected' : ''}${disabled ? ' disabled' : ''}`}
              title={disabled ? opt.unavailable_note || 'Not available yet' : undefined}
              onClick={() => {
                setCustomMode(false)
                onChange(opt.value)
              }}
            >
              {opt.label}
            </button>
          )
        })}
        {field.allow_custom && (
          <button
            type="button"
            className={`pill${customMode ? ' selected' : ''}`}
            onClick={() => setCustomMode(true)}
          >
            Custom
          </button>
        )}
      </div>
      {customMode && field.allow_custom && (
        <input
          type="number"
          step="any"
          className="pill-custom-input"
          placeholder={`Custom ${field.label.toLowerCase()}`}
          value={value ?? ''}
          onChange={(e) => onChange(e.target.value)}
        />
      )}
    </div>
  )
}
