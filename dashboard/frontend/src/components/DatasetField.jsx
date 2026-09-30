import { useState } from 'react'
import SelectAllCircle from './SelectAllCircle.jsx'
import { groupSelectState, toggleGroup } from '../lib/groupSelect.js'

// Two-level pick: benchmark first, then that benchmark's subsets - mirrors
// the Datasets page's own benchmark → subtab pattern. Only a few subsets
// are actually loadable by this experiment's script right now; the rest
// show up disabled (available: false) rather than being hidden, so it's
// visible what exists vs. what's wired up.
// `value` is always an array; when the field is sweepable, clicking toggles
// and selections persist across benchmarks, so one sweep can span e.g. a
// KnowEdit subset and three UniEdit domains.
export default function DatasetField({ field, value, onChange }) {
  const benchmarks = field.benchmarks || []
  const selected = Array.isArray(value) ? value : value == null ? [] : [value]
  const multi = field.sweepable === true
  const [benchmark, setBenchmark] = useState(
    () => benchmarks.find((b) => b.subsets.some((s) => selected.includes(s.value) && s.available !== false))
      || benchmarks.find((b) => b.subsets.some((s) => s.available !== false)),
  )

  const allSubsets = benchmarks.flatMap((b) => b.subsets.map((s) => ({ ...s, benchmark: b.label })))
  const labelFor = (v) => {
    const s = allSubsets.find((x) => x.value === v)
    return s ? `${s.benchmark}/${s.label}` : v
  }

  function selectBenchmark(next) {
    setBenchmark(next)
    if (multi) return
    if (!next.subsets.some((s) => selected.includes(s.value) && s.available !== false)) {
      const firstAvailable = next.subsets.find((s) => s.available !== false)
      if (firstAvailable) onChange([firstAvailable.value])
    }
  }

  function choose(v) {
    if (!multi) return onChange([v])
    onChange(selected.includes(v) ? selected.filter((x) => x !== v) : [...selected, v])
  }

  // Only the subsets this experiment can actually run - the rest are shown
  // disabled, so they must not count toward a "full" circle.
  const groupValues = (benchmark?.subsets || []).filter((s) => s.available !== false).map((s) => s.value)

  return (
    <div className="pill-field">
      <div className="pill-field-label">
        {field.label}
        {selected.length > 1 && <span className="sweep-badge">sweeping {selected.length}</span>}
      </div>

      <div className="pill-row hierarchy-categories" aria-label="Dataset collections">
        {benchmarks.map((b) => (
          <button
            type="button"
            key={b.label}
            disabled={!b.subsets.some((s) => s.available !== false)}
            title={!b.subsets.some((s) => s.available !== false) ? 'No runnable subsets available yet' : undefined}
            className={`pill hierarchy-category${b === benchmark ? ' selected' : ''}${!b.subsets.some((s) => s.available !== false) ? ' disabled' : ''}`}
            aria-pressed={b === benchmark}
            onClick={() => selectBenchmark(b)}
          >
            {b.label}
            {multi && b.subsets.some((s) => selected.includes(s.value)) && <span className="pill-dot" aria-hidden="true" />}
          </button>
        ))}
      </div>

      <div className="pill-row hierarchy-options" aria-label={`${benchmark?.label || 'Dataset'} subsets`}>
        {multi && (
          <SelectAllCircle
            state={groupSelectState(groupValues, selected)}
            groupLabel={`${benchmark?.label || 'dataset'} subsets`}
            disabled={!groupValues.length}
            onClick={() => onChange(toggleGroup(groupValues, selected))}
          />
        )}
        {benchmark?.subsets.map((s) => {
          const disabled = s.available === false
          const isOn = !disabled && selected.includes(s.value)
          return (
            <button
              type="button"
              key={s.label}
              disabled={disabled}
              className={`pill hierarchy-option${isOn ? ' selected' : ''}${disabled ? ' disabled' : ''}`}
              aria-pressed={isOn}
              title={disabled ? 'Not wired up for this experiment yet' : s.note}
              onClick={() => choose(s.value)}
            >
              {s.label}
            </button>
          )
        })}
      </div>

      {multi && selected.length > 1 && (
        <div className="sweep-summary">Sweeping: {selected.map(labelFor).join(', ')}</div>
      )}
    </div>
  )
}
