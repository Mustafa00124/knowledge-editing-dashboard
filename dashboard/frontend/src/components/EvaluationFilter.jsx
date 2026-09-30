import { EVALUATION_MODES } from '../lib/evaluationModes.js'

export default function EvaluationFilter({ value, onChange }) {
  return <div className="axis-tabs metric-subtabs" role="group" aria-label="Evaluation scoring mode">
    <span className="axis-selector-label">Evaluation</span>
    {EVALUATION_MODES.map((m) => <button key={m.value} type="button"
      className={`subnav-tab${value === m.value ? ' active' : ''}`}
      aria-pressed={value === m.value} onClick={() => onChange(m.value)}>{m.label}</button>)}
  </div>
}
