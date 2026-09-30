// Tri-state "select all" circle for the two-level sweep pickers, sitting at
// the head of the row of options it governs - so its scope is whatever is
// visible next to it (one method family, one benchmark's subsets), never
// the whole field. Selecting every dataset across every benchmark at once
// is almost always an accident, not an intent.
//
// Filled = all of this row selected, hollow = none, translucent = some.
export default function SelectAllCircle({ state, onClick, groupLabel, disabled = false }) {
  const next = state === 'all' ? 'Deselect' : 'Select'
  return (
    <button
      type="button"
      disabled={disabled}
      className={`select-all-circle is-${state}`}
      // Reads as a checkbox to assistive tech, which is what it behaves
      // like - "mixed" is the standard partial state.
      role="checkbox"
      aria-checked={state === 'all' ? 'true' : state === 'none' ? 'false' : 'mixed'}
      aria-label={`${next} all ${groupLabel}`}
      title={disabled ? 'Nothing available here yet' : `${next} all ${groupLabel}`}
      onClick={onClick}
    >
      <span className="select-all-glyph" aria-hidden="true" />
    </button>
  )
}
