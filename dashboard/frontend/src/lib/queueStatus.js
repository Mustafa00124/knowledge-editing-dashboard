// One place defining what each slot state means and what colour speaks for
// it. Every surface that signals state - the card's edge, its dot, its
// progress bar, its action button, the modal header - reads from here via
// the --status custom property, so a card can never show an amber edge with
// a red button.
export const STATUS = {
  empty:     { label: 'Ready',      hint: 'Nothing configured yet' },
  staged:    { label: 'Configured', hint: 'Ready to launch' },
  running:   { label: 'Running',    hint: 'Jobs on SLURM right now' },
  paused:    { label: 'Paused',     hint: 'Interrupted jobs can be restarted with Play' },
  completed: { label: 'Done',       hint: 'Every job finished' },
  failed:    { label: 'Failed',     hint: 'At least one job failed or was cancelled' },
}

// SLURM states a scancel would still act on. PENDING counts: a job waiting
// for a GPU is as cancellable as a running one.
export const ACTIVE_STATES = [
  'RUNNING', 'PENDING', 'COMPLETING', 'CONFIGURING', 'REQUEUED', 'RESIZING', 'SUSPENDED',
]
export const FAIL_STATES = [
  'FAILED', 'CANCELLED', 'TIMEOUT', 'OUT_OF_MEMORY', 'NODE_FAIL', 'REVOKED',
  'PREEMPTED', 'BOOT_FAIL', 'DEADLINE',
]

export function summarize(slot) {
  const jobs = slot?.jobs || []
  const current = jobs.filter((job) => !job.retried_by)
  const status = slot?.status || 'empty'
  const running = current.filter((j) => ['RUNNING', 'COMPLETING'].includes(j.status?.state))
  const active = current.filter((j) => ACTIVE_STATES.includes(j.status?.state))
  const pending = current.filter((j) => j.status?.state === 'PENDING')
  const done = current.filter((j) => j.status?.state === 'COMPLETED')
  const failed = current.filter((j) => FAIL_STATES.includes(j.status?.state))
  const interrupted = current.filter((j) => Boolean(j.pause_requested))
  return { status, jobs, current, running, active, pending, done, failed, interrupted }
}

// Step progress of whichever job is furthest along right now - one bar on
// the card face, rather than one per running job.
export function leadJob(running) {
  let best = null
  let bestPct = -1
  for (const job of running) {
    const { current_step, num_steps } = job.progress || {}
    const pct = num_steps && current_step != null ? Math.min(100, (current_step / num_steps) * 100) : 0
    if (pct > bestPct) { bestPct = pct; best = job }
  }
  return best
}

export function stepPct(job) {
  const { current_step, num_steps } = job?.progress || {}
  if (!num_steps || current_step == null) return null
  return Math.min(100, Math.round((current_step / num_steps) * 100))
}
