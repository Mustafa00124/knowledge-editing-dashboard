export default function EvaluationField({ field, value, onChange }) {
  const selected = (value || '').split(',').filter(Boolean)
  function toggle(mode) {
    const next = selected.includes(mode) ? selected.filter((m) => m !== mode) : [...selected, mode]
    onChange(field.options.filter((o) => next.includes(o.value)).map((o) => o.value).join(','))
  }
  return <div className="pill-field">
    <div className="pill-field-label">Evaluation <span className="field-group-note">Select one or more</span></div>
    <div className="pill-row" role="group" aria-label="Evaluation modes">
      {field.options.map((o) => <button key={o.value} type="button"
        className={`pill${selected.includes(o.value) ? ' selected' : ''}${!o.available ? ' disabled' : ''}`}
        disabled={!o.available} aria-pressed={selected.includes(o.value)}
        title={!o.available ? o.note : o.label} onClick={() => toggle(o.value)}>{o.label}</button>)}
    </div>
    {!field.options.find((o) => o.value === 'llm_judge')?.available &&
      <p className="drawer-desc">LLM judge needs a configured API key.</p>}
  </div>
}
