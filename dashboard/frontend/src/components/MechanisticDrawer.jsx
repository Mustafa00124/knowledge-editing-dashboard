import { useEffect, useMemo, useState } from 'react'
import QueueDrawer from './QueueDrawer.jsx'
import { toggleGroup } from '../lib/groupSelect.js'

function fieldOptions(field, factSets) {
  if (field.name === 'fact_set' && factSets) {
    return [{ label: 'none: scan the dataset per model', value: '' }, ...factSets.map((set) => ({
      label: `${set.name} · ${set.picked} facts · ${set.formats.join(', ')}${set.below_min ? ' · below 50' : ''}`,
      value: set.path,
    }))]
  }
  if (field.control === 'dataset') {
    return field.benchmarks.flatMap((benchmark) =>
      benchmark.subsets
        .filter((subset) => subset.available && subset.value)
        .map((subset) => ({ label: `${benchmark.label} / ${subset.label}`, value: subset.value })),
    )
  }
  return (field.options || []).filter((option) => option.available !== false)
}

// The launch drawer of the per-model pages (knowledge localisation, neuron
// attribution, circuit tracing, knowledge by format): models as pills, each
// with a note on what it already has, and the type's own settings from its
// dashboard.json (`controls` picks which). Stages one job per model onto a
// GPU queue card, like every other drawer.
export default function MechanisticDrawer({ open, onToggle, onClose, title, queue, onStage, expType, models, controls = [], factSets, costNote }) {
  const [chosen, setChosen] = useState([])
  const [values, setValues] = useState({})

  const fields = useMemo(() => {
    const byName = Object.fromEntries((expType?.fields || []).map((f) => [f.name, f]))
    return controls.map((name) => byName[name]).filter(Boolean)
  }, [expType, controls])

  useEffect(() => {
    if (!fields.length || Object.keys(values).length) return
    setValues(Object.fromEntries(fields.map((f) => [f.name, String(f.default)])))
  }, [fields, values])

  async function submit(slot) {
    const params = Object.fromEntries(Object.entries(values).map(([k, v]) => [k, [v]]))
    await onStage(slot, expType.name, { ...params, model: chosen }, true)
    setChosen([])
  }

  return (
    <QueueDrawer
      open={open}
      onToggle={onToggle}
      onClose={onClose}
      title={title}
      queue={queue}
      summary={`${chosen.length} job${chosen.length === 1 ? '' : 's'} (one per model) will be queued`}
      canSubmit={Boolean(expType) && chosen.length > 0}
      onSubmit={submit}
    >
      <div className="drawer-type-label">{expType?.label || expType?.name || 'Loading…'}</div>
      <div className="pill-field">
        <div className="pill-field-label">Models</div>
        <div className="pill-row trace-models">
          {(models || []).map((model) => (
            <button
              key={model.value}
              type="button"
              disabled={model.available === false}
              className={`pill${chosen.includes(model.value) ? ' selected' : ''}`}
              title={model.note || undefined}
              onClick={() => setChosen((previous) => toggleGroup([model.value], previous))}
            >
              {model.label}
              {model.tag && <span className="trace-pill-note">{model.tag}</span>}
            </button>
          ))}
        </div>
      </div>
      {fields.map((field) => (
        <label key={field.name} title={field.note || undefined}>
          {field.label}
          <select
            value={values[field.name] ?? ''}
            onChange={(e) => setValues((previous) => ({ ...previous, [field.name]: e.target.value }))}
          >
            {fieldOptions(field, factSets).map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
        </label>
      ))}
      {costNote && <p className="dataset-note">{costNote}</p>}
    </QueueDrawer>
  )
}
