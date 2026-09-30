import { useState } from 'react'

// Multi-select version of PillField, for fields marked "sweepable" in
// dashboard.json. Selecting more than one value here means "run every
// combination" - see ExperimentDrawer's combo count / Cartesian product.
export default function SweepPillField({ field, value, onChange }) {
  const options = field.options || []
  const selected = Array.isArray(value) ? value : []
  const [customInput, setCustomInput] = useState('')
  const [customOpen, setCustomOpen] = useState(false)

  function toggle(v) {
    onChange(selected.includes(v) ? selected.filter((x) => x !== v) : [...selected, v])
  }

  function addCustom() {
    const v = customInput.trim()
    if (v && !selected.includes(v)) onChange([...selected, v])
    setCustomInput('')
  }

  const presetValues = options.map((o) => o.value)
  const customValues = selected.filter((v) => !presetValues.includes(v))

  return (
    <div className="pill-field">
      <div className="pill-field-label">
        {field.label}
        {field.note && <span className="pill-field-note">: {field.note}</span>}
        {selected.length > 1 && <span className="sweep-badge">sweeping {selected.length}</span>}
      </div>

      <div className="pill-row">
        {options.map((opt) => {
          // An option another field has ruled out (a batch larger than the
          // dataset) stays visible but unclickable, so the constraint reads
          // as a constraint rather than as options that come and go.
          const disabled = opt.available === false
          return (
            <button
              type="button"
              key={opt.value}
              disabled={disabled}
              className={`pill${selected.includes(opt.value) ? ' selected' : ''}${disabled ? ' disabled' : ''}`}
              title={disabled ? opt.unavailable_note || 'Not available yet' : undefined}
              onClick={() => toggle(opt.value)}
            >
              {opt.label}
            </button>
          )
        })}
        {customValues.map((v) => (
          <button type="button" key={v} className="pill selected" onClick={() => toggle(v)} title="Remove">
            {v} ✕
          </button>
        ))}
        {field.allow_custom && field.custom_as_option && (
          <button type="button" className={`pill${customOpen ? ' selected' : ''}`} aria-expanded={customOpen} onClick={() => setCustomOpen((open) => !open)}>
            Custom
          </button>
        )}
      </div>

      {field.allow_custom && (!field.custom_as_option || customOpen) && (
        <div className="custom-add-row">
          <input
            type="number"
            step={field.type === 'int' ? '1' : 'any'}
            placeholder={`Custom ${field.label.toLowerCase()}`}
            value={customInput}
            onChange={(e) => setCustomInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault()
                addCustom()
              }
            }}
          />
          <button type="button" className="btn-plain-small" onClick={addCustom}>
            + Add
          </button>
        </div>
      )}
    </div>
  )
}
