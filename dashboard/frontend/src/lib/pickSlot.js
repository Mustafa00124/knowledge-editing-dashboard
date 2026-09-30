// Default suggestion for which queue card a newly-opened drawer should
// preselect: prefer an empty slot, then a finished one (completed/failed -
// staging there just recycles the card), and only default to an
// already-staged slot as a last resort. A running slot is never suggested
// (and the backend refuses staging into one regardless).
export function pickSlotForStaging(queue) {
  const rank = { empty: 0, completed: 1, failed: 1, staged: 2, running: 3, paused: 3 }
  let best = null
  queue.forEach((slot, i) => {
    const r = rank[slot.status] ?? 3
    if (r < 3 && (best === null || r < rank[queue[best].status])) best = i
  })
  return best
}
