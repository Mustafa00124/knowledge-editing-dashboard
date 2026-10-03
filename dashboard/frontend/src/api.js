const BASE = '/api'

function getToken() {
  let token = localStorage.getItem('dashboard_token')
  if (!token) {
    token = window.prompt('Dashboard auth token (see the backend log for it):') || ''
    localStorage.setItem('dashboard_token', token)
  }
  return token
}

async function req(path, opts = {}) {
  const res = await fetch(BASE + path, {
    headers: {
      'Content-Type': 'application/json',
      'X-Dashboard-Token': getToken(),
      ...(opts.headers || {}),
    },
    ...opts,
  })
  if (res.status === 401) {
    // Stored token was wrong/stale, clear it so the next request re-prompts.
    localStorage.removeItem('dashboard_token')
    throw new Error('401 Unauthorized: wrong token. Reload the page to enter it again.')
  }
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`${res.status} ${res.statusText}: ${text}`)
  }
  return res.status === 204 ? null : res.json()
}

// "archived" switches a read over to the retired-runs tree (see the note
// on "type" below).
function resultsQuery(type, archived) {
  const parts = []
  if (type) parts.push(`type=${encodeURIComponent(type)}`)
  if (archived) parts.push('archived=true')
  return parts.length ? `?${parts.join('&')}` : ''
}

// Queue experiments are reached through the slot that launched them, so
// there's no list-all call for those. `experiments(type)` exists for the
// experiment types that don't use the queue at all (causal tracing), which
// otherwise would have no way to find their own jobs.
export const api = {
  capabilities: () => req('/capabilities'),

  // Hyperparameter investigations (see backend/hparam_sweeps.py).
  investigations: () => req('/hparams/investigations'),
  heldSettings: (investigation, methods, models) =>
    req(`/hparams/settings?investigation=${encodeURIComponent(investigation)}&methods=${encodeURIComponent(methods.join(','))}&models=${encodeURIComponent(models.join(','))}`),
  estimateSweep: (spec) => req('/hparams/estimate', { method: 'POST', body: JSON.stringify(spec) }),
  launchSweep: (spec) => req('/hparams/sweeps', { method: 'POST', body: JSON.stringify(spec) }),
  sweeps: (investigation, includeHidden = false) => {
    const q = new URLSearchParams()
    if (investigation) q.set('investigation', investigation)
    if (includeHidden) q.set('include_hidden', 'true')
    return req(`/hparams/sweeps${q.toString() ? `?${q}` : ''}`)
  },
  hideSweep: (investigation, id, hidden = true) =>
    req(`/hparams/sweeps/${encodeURIComponent(investigation)}/${encodeURIComponent(id)}/hide?hidden=${hidden}`, { method: 'POST' }),
  cancelSweep: (investigation, id) =>
    req(`/hparams/sweeps/${encodeURIComponent(investigation)}/${encodeURIComponent(id)}/cancel`, { method: 'POST' }),
  rerunFailedSweep: (investigation, id) =>
    req(`/hparams/sweeps/${encodeURIComponent(investigation)}/${encodeURIComponent(id)}/rerun-failed`, { method: 'POST' }),
  sweepFailures: () => req('/hparams/failures'),
  sweepDetail: (investigation, id) => req(`/hparams/sweeps/${encodeURIComponent(investigation)}/${encodeURIComponent(id)}`),
  sweepResults: (investigation) => req(`/hparams/results?investigation=${encodeURIComponent(investigation)}`),
  promoteConfig: (investigation, sweepId, run) =>
    req('/hparams/promote', { method: 'POST', body: JSON.stringify({ investigation, sweep_id: sweepId, run }) }),

  // Downloads page: everything fetchable (components, datasets, models)
  // with on-disk status, and the background tasks fetching them.
  downloads: () => req('/downloads'),
  startDownloads: (items) => req('/downloads', { method: 'POST', body: JSON.stringify({ items }) }),
  cancelDownload: (id) => req(`/downloads/${encodeURIComponent(id)}`, { method: 'DELETE' }),
  downloadLog: (id) => req(`/downloads/${encodeURIComponent(id)}/log`),
  clearDownloads: () => req('/downloads/clear', { method: 'POST' }),
  experimentTypes: () => req('/experiment-types'),
  // Launches: every batch submitted at once (a sweep, or an experiment
  // submission), with progress; backend/launches.py.
  launches: (investigation, { active = false, limit = 50, days = 7 } = {}) => {
    const q = new URLSearchParams({ active: String(active), limit: String(limit), days: String(days) })
    if (investigation) q.set('investigation', investigation)
    return req(`/launches?${q}`)
  },
  launchSummary: () => req('/launches/summary'),
  launchDetail: (id) => req(`/launches/${encodeURIComponent(id)}`),
  cancelLaunch: (id) => req(`/launches/${encodeURIComponent(id)}/cancel`, { method: 'POST' }),

  experiments: (type) => req(`/experiments${type ? `?experiment_type=${encodeURIComponent(type)}` : ''}`),
  submitExperiment: (experiment_type, params, save_results = true) =>
    req('/experiments', { method: 'POST', body: JSON.stringify({ experiment_type, params, save_results }) }),
  getExperiment: (jobId) => req(`/experiments/${jobId}`),
  cancelExperiment: (jobId) => req(`/experiments/${jobId}`, { method: 'DELETE' }),

  // "type" is a registered experiment type's name (dashboard.json), not a
  // results/ folder. Optional everywhere since there's normally exactly
  // one registered type (see results_reader.py).
  manifest: (type) => req(`/results/manifest${resultsQuery(type)}`),
  checkpoints: (run, type, archived) =>
    req(`/results/runs/${encodeURIComponent(run)}/checkpoints${resultsQuery(type, archived)}`),
  samples: (run, type, archived) =>
    req(`/results/runs/${encodeURIComponent(run)}/samples${resultsQuery(type, archived)}`),
  sample: (run, step, type, archived) =>
    req(`/results/runs/${encodeURIComponent(run)}/samples/${step}${resultsQuery(type, archived)}`),
  evaluations: (run) => req(`/results/runs/${encodeURIComponent(run)}/evaluations`),
  evaluation: (run, step) => req(`/results/runs/${encodeURIComponent(run)}/evaluations/${step}`),
  testingResults: () => req('/results/testing'),

  // Archiving moves a run's directory out of runs/ (see backend/archive.py).
  // Both calls take dry_run: the confirmation dialog asks what *would* move,
  // then the same call with dry_run false commits it.
  archivedRuns: (type) => req(`/results/archive${resultsQuery(type)}`),
  incompleteRuns: (type) => req(`/results/incomplete${resultsQuery(type)}`),
  archiveRuns: (runs, reason = '', dryRun = false, type) =>
    req(`/results/archive${resultsQuery(type)}`, {
      method: 'POST',
      body: JSON.stringify({ runs, reason, dry_run: dryRun }),
    }),
  restoreRuns: (runs, dryRun = false, type) =>
    req(`/results/archive/restore${resultsQuery(type)}`, {
      method: 'POST',
      body: JSON.stringify({ runs, dry_run: dryRun }),
    }),

  queue: () => req('/queue'),
  gpuStatus: () => req('/queue/gpu-status'),
  stageQueueSlot: (slot, experiment_type, params, save_results = true) =>
    req(`/queue/${slot}/stage`, { method: 'POST', body: JSON.stringify({ experiment_type, params, save_results }) }),
  launchQueueSlot: (slot) => req(`/queue/${slot}/launch`, { method: 'POST' }),
  rerunFailedQueueSlot: (slot) => req(`/queue/${slot}/rerun-failed`, { method: 'POST' }),
  pauseQueueSlot: (slot) => req(`/queue/${slot}/pause`, { method: 'POST' }),
  resumeQueueSlot: (slot) => req(`/queue/${slot}/resume`, { method: 'POST' }),
  cancelQueueSlot: (slot) => req(`/queue/${slot}/cancel`, { method: 'POST' }),
  clearQueueSlot: (slot) => req(`/queue/${slot}/clear`, { method: 'POST' }),

  // Causal tracing: the model -> edit-layer mapping, and one run's curves.
  // Its jobs are submitted through submitExperiment like any other type.
  causalTracing: () => req('/causal-tracing'),
  causalTrace: (run) => req(`/causal-tracing/runs/${encodeURIComponent(run)}`),

  // Neuron attribution and circuit tracing (experiment: neuron_tracing or
  // circuit_tracing): runs per model, and one run's detail file.
  mechanistic: (experiment) => req(`/mechanistic/${experiment}`),
  mechanisticRun: (experiment, run) => req(`/mechanistic/${experiment}/runs/${encodeURIComponent(run)}`),

  // Benchmarks present under datasets/. A fresh clone lacks the ones
  // scripts/setup.py downloads (UniEdit, DUnE).
  datasets: () => req('/datasets'),
  datasetFiles: (benchmark) => req(`/datasets/${benchmark}/files`),
  // What "full" means for one dataset file, so the drawer can cap the batch
  // size with it.
  datasetRecordCount: (path) => req(`/datasets/record-count?path=${encodeURIComponent(path)}`),
  datasetPreview: (benchmark, file, offset = 0, limit = 20, key) =>
    req(
      `/datasets/${benchmark}/preview?file=${encodeURIComponent(file)}&offset=${offset}&limit=${limit}` +
        (key ? `&key=${encodeURIComponent(key)}` : ''),
    ),
  models: () => req('/models'),
}
