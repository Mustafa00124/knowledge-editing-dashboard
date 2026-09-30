import { useEffect, useMemo, useState } from 'react'
import EvaluationField from './EvaluationField.jsx'
import PillField from './PillField.jsx'
import DatasetField from './DatasetField.jsx'
import MethodField from './MethodField.jsx'
import ModelField from './ModelField.jsx'
import SweepPillField from './SweepPillField.jsx'
import { api } from '../api.js'
import { comboCount as countCombos } from '../lib/comboCount.js'
import { pickSlotForStaging } from '../lib/pickSlot.js'

const SLOT_STATUS_SHORT = {
  empty: 'ready',
  staged: 'configured',
  running: 'running',
  paused: 'paused',
  completed: 'done',
  failed: 'failed',
}

// The subset label a data_path was picked by, for notes that name datasets.
function datasetLabel(cfg, path) {
  const field = (cfg?.fields || []).find((f) => f.control === 'dataset')
  for (const benchmark of field?.benchmarks || []) {
    for (const subset of benchmark.subsets || []) {
      if (subset.value === path) return subset.label
    }
  }
  return path.split('/').pop()
}

// A field with a `show_when` (e.g. {method: ["ft"]}) only applies for some
// values of another field. Dependencies are sweepable, so "applies" means
// *any* selected value matches: sweeping [rome, ike, ft] still needs the lr
// control, because the ft leg of that sweep uses it. The backend drops the
// field from the legs it doesn't apply to (slurm.py::_field_relevant), so a
// shown-but-irrelevant value never reaches a run that ignores it.
function fieldVisible(field, values) {
  if (!field.show_when) return true
  return Object.entries(field.show_when).every(([dep, allowed]) =>
    (values[dep] || []).some((v) => allowed.includes(v)))
}

// This picks a slot and stages the config there - it doesn't run anything.
// Launching (and the "that's a lot of GPU jobs" confirmation) happens from
// the queue card itself, once you're ready.
// dashboard.json says "full"; everything numeric here has to know that one
// value isn't a number.
export function isFullDataset(value) {
  return typeof value === 'string' && ['full', 'all'].includes(value.toLowerCase())
}

export default function ExperimentDrawer({ open, onToggle, onClose, experimentTypes, queue, onSubmit }) {
  const [datasetCounts, setDatasetCounts] = useState({})
  const [selectedType, setSelectedType] = useState(null)
  const [selectedSlot, setSelectedSlot] = useState(null)
  // Every field's value is stored as an array here, even single-select
  // ones - a plain submission is just a sweep of size 1 per field. Keeps
  // the wire format (and the Cartesian-product math) uniform.
  const [values, setValues] = useState({})
  const [saveResults, setSaveResults] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (experimentTypes.length && !selectedType) {
      setSelectedType(experimentTypes[0].name)
    }
  }, [experimentTypes, selectedType])

  useEffect(() => {
    const cfg = experimentTypes.find((t) => t.name === selectedType)
    if (cfg) {
      const defaults = {}
      cfg.fields.forEach((f) => {
        defaults[f.name] = [f.default]
      })
      setValues(defaults)
    }
  }, [selectedType, experimentTypes])

  // Re-suggest a default slot each time the drawer is opened, based on
  // the queue's state at that moment - the user can still click a
  // different one before submitting.
  useEffect(() => {
    if (open && queue.length) {
      setSelectedSlot((prev) => (prev !== null && !['running', 'paused'].includes(queue[prev]?.status) ? prev : pickSlotForStaging(queue)))
    }
  }, [open, queue])

  // Whenever a field becomes hidden by a show_when condition (e.g.
  // switching method away from "ft" hides lr/num_steps), snap it back to
  // its single default - so a stale multi-select from before switching
  // method can't sneak into the submitted combo count, and hidden fields
  // never need special-casing anywhere else (combo count, queue cards,
  // the backend) - they're just always length-1 once hidden.
  useEffect(() => {
    const c = experimentTypes.find((t) => t.name === selectedType)
    if (!c) return
    setValues((prev) => {
      let changed = false
      const next = { ...prev }
      c.fields.forEach((f) => {
        if (f.show_when && !fieldVisible(f, prev)) {
          const current = prev[f.name] || []
          if (current.length !== 1 || current[0] !== f.default) {
            next[f.name] = [f.default]
            changed = true
          }
        }
      })
      return changed ? next : prev
    })
  }, [values, selectedType, experimentTypes])

  // lr and num_steps are shared by FT and LoRA, but the papers give them very
  // different values (25 steps at 5e-4 vs 50 at 5e-3), so a single default
  // can only be right for one. `default_when` maps a method to the default
  // that belongs with it.
  //
  // Only applied while the field still holds one of its canned defaults, so a
  // value you typed or swept yourself survives a method switch untouched.
  useEffect(() => {
    const c = experimentTypes.find((t) => t.name === selectedType)
    if (!c) return
    setValues((prev) => {
      let changed = false
      const next = { ...prev }
      c.fields.forEach((f) => {
        if (!f.default_when) return
        Object.entries(f.default_when).forEach(([dep, byValue]) => {
          const chosen = prev[dep] || []
          if (chosen.length !== 1) return
          const wanted = byValue[chosen[0]]
          if (wanted === undefined) return
          const canned = new Set([f.default, ...Object.values(byValue)])
          const current = prev[f.name] || []
          if (current.length === 1 && canned.has(current[0]) && current[0] !== wanted) {
            next[f.name] = [wanted]
            changed = true
          }
        })
      })
      return changed ? next : prev
    })
  }, [values, selectedType, experimentTypes])

  const cfg = experimentTypes.find((t) => t.name === selectedType)
  const total = cfg ? countCombos(values, cfg.fields) : 0

  // "Full dataset" has no number until someone reads the file, and every
  // dataset has a different one, so the cap it implies is fetched per
  // selected dataset (null while in flight or if the lookup fails, which
  // just means no cap is applied).
  useEffect(() => {
    const paths = (values.data_path || []).filter((path) => datasetCounts[path] === undefined)
    if (!paths.length) return
    setDatasetCounts((prev) => ({ ...prev, ...Object.fromEntries(paths.map((path) => [path, null])) }))
    paths.forEach((path) => {
      api.datasetRecordCount(path)
        .then(({ count }) => setDatasetCounts((prev) => ({ ...prev, [path]: count })))
        .catch(() => {})
    })
  }, [values.data_path, datasetCounts])

  const fullCount = useMemo(() => {
    const counts = (values.data_path || []).map((path) => datasetCounts[path]).filter((n) => typeof n === 'number')
    return counts.length ? Math.max(...counts) : null
  }, [values.data_path, datasetCounts])

  // The most facts any queued combination could edit. The largest of the
  // selected sizes, not the smallest: a value that is valid for one combo in
  // a sweep shouldn't be greyed out because another combo is smaller - the
  // runner clamps each run to its own dataset anyway.
  const dsSizeCap = useMemo(() => {
    const picked = (values.ds_size || [])
      .map((value) => (isFullDataset(value) ? fullCount : Number(value)))
      .filter((n) => Number.isFinite(n))
    return picked.length ? Math.max(...picked) : null
  }, [values.ds_size, fullCount])

  function capFor(field) {
    if (!field.max_from) return null
    if (field.max_from === 'ds_size') return dsSizeCap
    // A field can be capped by one that is itself conditional: batch size is
    // bounded by the reset interval, but only Sequential batch shows a reset
    // interval at all. When the source is hidden its value is a stale
    // default (see the snap-back effect above), so capping against it would
    // invent a limit the run does not have. Fall back to the dataset, which
    // bounds every count here.
    const source = cfg?.fields.find((f) => f.name === field.max_from)
    if (source && !fieldVisible(source, values)) return dsSizeCap
    const picked = (values[field.max_from] || []).map(Number).filter(Number.isFinite)
    return picked.length ? Math.max(...picked) : null
  }

  // A selection the cap has invalidated (batch 50 left over from before the
  // dataset size dropped to 20) is replaced by the cap itself, which is the
  // same run the clamped value would have produced - rather than left to be
  // silently corrected by the runner an hour later.
  useEffect(() => {
    if (!cfg) return
    setValues((prev) => {
      let changed = false
      const next = { ...prev }
      cfg.fields.forEach((field) => {
        const cap = capFor(field)
        if (cap == null) return
        const current = prev[field.name] || []
        const kept = current.filter((value) => !(Number(value) > cap))
        if (kept.length === current.length) return
        next[field.name] = kept.length ? kept : [String(cap)]
        changed = true
      })
      return changed ? next : prev
    })
  }, [dsSizeCap, values.reset_every, values.ds_size, values.edit_mode, cfg])

  // What a size means right now, spelled out where it is chosen: "full" is a
  // different number for every dataset, and a cap is worth stating before
  // someone wonders why a pill is greyed out.
  function dynamicNote(field, cap) {
    if (field.name === 'ds_size') {
      const picked = (values.data_path || [])
        .map((path) => [datasetLabel(cfg, path), datasetCounts[path]])
        .filter(([, count]) => typeof count === 'number')
      if (!picked.length) return field.note
      return `${field.note} (full is ${picked.map(([label, count]) => `${count} for ${label}`).join(', ')})`
    }
    if (cap != null) return `${field.note}; at most ${cap} here`
    return field.note
  }

  // Field -> control. Shared by the ungrouped fields and by every group
  // section, so a field renders identically wherever it's placed.
  function renderFields(fields) {
    return fields.map((f) => {
      const arr = values[f.name] || []
      const set = (v) => setValues((prev) => ({ ...prev, [f.name]: v }))
      const key = `${selectedType}-${f.name}`
      let shownField = f.options?.some((opt) => opt.methods)
        ? { ...f, options: f.options.filter((opt) => !opt.methods || (values.method || []).some((m) => opt.methods.includes(m))) }
        : f
      const cap = capFor(f)
      if (cap != null && shownField.options) {
        shownField = {
          ...shownField,
          options: shownField.options.map((opt) => (Number(opt.value) > cap
            ? { ...opt, available: false, unavailable_note: `more than the ${cap} facts this run edits` }
            : opt)),
        }
      }
      const note = dynamicNote(f, cap)
      if (note !== f.note) shownField = { ...shownField, note }
      if (f.control === 'evaluation') return <EvaluationField key={key} field={f} value={arr[0]} onChange={(v) => set(v ? [v] : [])} />
      if (f.control === 'dataset') return <DatasetField key={key} field={f} value={arr} onChange={set} />
      if (f.control === 'method') return <MethodField key={key} field={f} value={arr} onChange={set} />
      if (f.control === 'model') return <ModelField key={key} field={f} value={arr} onChange={set} />
      if (f.sweepable) return <SweepPillField key={key} field={shownField} value={arr} onChange={set} />
      return <PillField key={key} field={shownField} value={arr[0]} onChange={(v) => set([v])} />
    })
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (selectedSlot === null) {
      setError(`No GPU queue available: all ${queue.length} are currently running.`)
      return
    }
    setSubmitting(true)
    setError(null)
    try {
      await onSubmit(selectedSlot, selectedType, values, saveResults)
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
        className={`drawer-tab ${open ? 'open' : ''}`}
        onClick={onToggle}
        title={open ? 'Close new experiment panel' : 'Open new experiment panel'}
        aria-label={open ? 'Close new experiment panel' : 'Open new experiment panel'}
      >
        {open ? '‹' : '›'}
      </button>

      <div className={`drawer ${open ? 'open' : ''}`}>
        <div className="drawer-header">
          <h2>New Experiment</h2>
          <button className="btn-plain" onClick={onClose}>
            ✕
          </button>
        </div>

        {cfg && (
          <form onSubmit={handleSubmit} className="drawer-form">
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

            {/* Only worth choosing once there's more than one registered
                experiment type - for now there's just run_experiment. */}
            {experimentTypes.length > 1 ? (
              <label>
                Experiment type
                <select value={selectedType} onChange={(e) => setSelectedType(e.target.value)}>
                  {experimentTypes.map((t) => (
                    <option key={t.name} value={t.name}>
                      {t.label || t.name}
                    </option>
                  ))}
                </select>
              </label>
            ) : (
              <div className="drawer-type-label">{cfg.label || cfg.name}</div>
            )}
            <div className="result-destination-control">
              <div className="result-destination-copy">
                <span className="result-destination-label">Save to main Results</span>
                <span className="result-destination-status">{saveResults ? 'Organized results' : 'Timestamped Trial Runs'}</span>
              </div>
              <button
                type="button"
                role="switch"
                aria-checked={saveResults}
                aria-label="Save to main Results"
                className={`result-destination-switch${saveResults ? ' is-on' : ''}`}
                onClick={() => setSaveResults((current) => !current)}
              >
                <span className="result-destination-thumb" />
              </button>
            </div>

            {renderFields(cfg.fields.filter((f) => !f.group && fieldVisible(f, values)))}

            {/* One section per declared group, in declared order. A group is
                purely presentational: it shows whenever any of its fields
                does, so each field's own show_when stays the single source
                of truth - the backend reads that same key to decide which
                fields a given method's run actually used. */}
            {(cfg.field_groups || []).map((group) => {
              const groupFields = cfg.fields.filter((f) => f.group === group.id && fieldVisible(f, values))
              if (!groupFields.length) return null
              return (
                <fieldset className="field-group" key={`${selectedType}-${group.id}`}>
                  <legend className="field-group-legend">
                    {group.label}
                    {group.note && <span className="field-group-note">{group.note}</span>}
                  </legend>
                  {renderFields(groupFields)}
                </fieldset>
              )
            })}

            {error && <div className="form-error">{error}</div>}

            <p className="sweep-count">
              {total === 1 ? '1 experiment' : `${total} experiments`} will be queued
              {selectedSlot !== null ? ` on GPU ${selectedSlot + 1}` : ''}
            </p>

            <button type="submit" className="btn-primary" disabled={submitting || total === 0 || selectedSlot === null}>
              {submitting ? 'Queuing…' : 'Queue Experiment'}
            </button>
          </form>
        )}
      </div>
    </>
  )
}
