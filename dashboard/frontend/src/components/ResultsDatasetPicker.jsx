// Same two-level benchmark -> subset choice as before, but as labeled tab
// rows rather than pills, so it reads the same as the Rows/Columns selectors
// on the table and the metric tabs above it. The options here are only ever
// whatever actually has results right now, not every registered dataset:
// there's no "available: false" dulling, an empty result set simply isn't a
// tab.
function TabRow({ label, values, isActive, onSelect, keyFor, labelFor }) {
  return (
    <div className="axis-selector">
      <span className="axis-selector-label">{label}</span>
      <div className="axis-tabs" role="group" aria-label={label}>
        {values.map((v) => {
          const active = isActive(v)
          return (
            <button
              key={keyFor(v)}
              type="button"
              className={`subnav-tab${active ? ' active' : ''}`}
              aria-pressed={active}
              onClick={() => onSelect(v)}
            >
              {labelFor(v)}
            </button>
          )
        })}
      </div>
    </div>
  )
}

export default function ResultsDatasetPicker({ options, value, onChange }) {
  if (!options.length) return null
  const current = options.find((o) => o.benchmark === value?.benchmark) || options[0]

  return (
    <div className="axis-controls">
      <TabRow
        label="Dataset"
        values={options}
        keyFor={(o) => o.benchmark}
        labelFor={(o) => o.benchmark}
        isActive={(o) => o.benchmark === current.benchmark}
        onSelect={(o) => onChange({ benchmark: o.benchmark, subset: o.subsets[0] })}
      />
      {/* A lone subset is the benchmark itself, so the row would say nothing. */}
      {current.subsets.length > 1 && (
        <TabRow
          label="Subset"
          values={current.subsets}
          keyFor={(s) => s}
          labelFor={(s) => s}
          isActive={(s) => value?.subset === s}
          onSelect={(s) => onChange({ benchmark: current.benchmark, subset: s })}
        />
      )}
    </div>
  )
}
