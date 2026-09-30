// Same Cartesian-product size the backend computes when it actually
// launches a staged config - used here just for the live "N experiments"
// counters in the drawer and on a staged queue card.
//
// Pass `fields` (an experiment type's field definitions) to get the real
// number. Sweeping a field others depend on collapses some points: method
// [rome, ft] x lr [1e-3, 1e-4] looks like 4, but ROME ignores lr, so it's
// 3 actual runs. The backend dedupes exactly this way in
// slurm.py::submit_sweep, and the two have to agree or the drawer promises
// jobs that never get submitted. Without `fields` it falls back to the
// plain product, which is correct whenever nothing has a show_when.
export function comboCount(params, fields) {
  const names = Object.keys(params || {})
  if (!names.length) return 1

  // A field cleared to nothing (the select-all circle can do that) means
  // there is no sweep to run. Report that honestly instead of falling back
  // to the field's default, which would queue a run the user switched off.
  if (names.some((n) => Array.isArray(params[n]) && params[n].length === 0)) return 0

  const defs = fields ? Object.fromEntries(fields.map((f) => [f.name, f])) : null
  const plain = names.reduce((acc, n) => acc * Math.max(1, (params[n] || []).length), 1)
  if (!defs) return plain

  const relevant = (name, point) => {
    const showWhen = defs[name]?.show_when
    if (!showWhen) return true
    return Object.entries(showWhen).every(([dep, allowed]) => allowed.includes(point[dep]))
  }

  // Mirrors slurm.py::_combo_supported. Some pairings can never run - the
  // locate-and-edit methods need a labeled subject span and RealTimeQA has
  // none - and the backend skips them, so counting them here would promise
  // jobs that never get submitted.
  const supported = (point) => {
    const methodDef = (defs.method?.categories || [])
      .flatMap((cat) => cat.methods)
      .find((m) => m.value === point.method)
    // Both joint modes need a method with a joint solve: the objection is
    // to the apply call carrying several facts, not to edits accumulating.
    // Read off `no_joint_batch` rather than naming ROME, so this cannot
    // drift from the backend the way a hardcoded list did.
    const joint = ['batch', 'sequential_batch'].includes(point.edit_mode)
    if (joint && methodDef?.no_joint_batch) return false
    // Only sequential_batch has both knobs, so only there can they conflict.
    if (point.edit_mode === 'sequential_batch' &&
        Number(point.edit_batch_size) > Number(point.reset_every)) return false
    const needsSubject = methodDef?.requires_subject || false
    if (!needsSubject) return true
    for (const benchmark of defs.data_path?.benchmarks || []) {
      for (const subset of benchmark.subsets || []) {
        if (subset.value === point.data_path) return subset.provides_subject !== false
      }
    }
    return true
  }

  const signatures = new Set()
  const walk = (i, point) => {
    if (i === names.length) {
      if (!supported(point)) return
      const sig = names
        .filter((n) => relevant(n, point))
        .map((n) => `${n}=${point[n]}`)
        .sort()
        .join('|')
      signatures.add(sig)
      return
    }
    const name = names[i]
    const options = (params[name] || []).length ? params[name] : [undefined]
    for (const v of options) walk(i + 1, { ...point, [name]: v })
  }
  walk(0, {})
  return signatures.size
}
