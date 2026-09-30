// Shared logic for the tri-state select-all circles on the two-level sweep
// pickers (method families, dataset benchmarks). Kept out of the components
// so both behave identically.

// 'all' / 'some' / 'none', counting only the group's selectable values -
// an option that isn't wired up yet can never be part of a sweep, so a row
// whose available options are all picked reads as full even when disabled
// ones sit next to them.
export function groupSelectState(groupValues, selected) {
  if (!groupValues.length) return 'none'
  const on = groupValues.filter((v) => selected.includes(v)).length
  if (on === 0) return 'none'
  return on === groupValues.length ? 'all' : 'some'
}

// Full row selected -> clear it; anything else -> fill it. Clearing can
// leave the field with nothing selected, which is allowed and honest: the
// drawer then reports 0 experiments and disables Queue, rather than
// silently keeping a value the user just switched off.
export function toggleGroup(groupValues, selected) {
  if (groupSelectState(groupValues, selected) === 'all') {
    return selected.filter((v) => !groupValues.includes(v))
  }
  return [...selected, ...groupValues.filter((v) => !selected.includes(v))]
}
