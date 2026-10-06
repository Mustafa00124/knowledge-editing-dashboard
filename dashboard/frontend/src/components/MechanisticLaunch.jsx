import { useEffect, useMemo, useState } from 'react'
import LaunchBlockedNotice from './LaunchBlockedNotice.jsx'
import useCapabilities, { launchBlockers } from '../lib/useCapabilities.js'
import { api } from '../api.js'
import ClearFinishedButton from './ClearFinishedButton.jsx'
import { ACTIVE_STATES, FAIL_STATES } from '../lib/queueStatus.js'
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

function shortTime(iso) {
  return iso ? iso.replace('T', ' ').slice(0, 16) : '—'
}

// The launch form and job list shared by the per-model tracing pages that
// sit beside causal tracing (neuron attribution, circuit tracing). Every
// control reads its label, options and default from the experiment type's
// own dashboard.json; `controls` picks which are shown. Calls onFinished
// when a job leaves the active states, so the page can reload results.
export default function MechanisticLaunch({ experiment, overview, controls, costNote, verb, progress, onFinished }) {
  const [expType, setExpType] = useState(null)
  const blockers = launchBlockers(useCapabilities(), experiment)
  const [jobs, setJobs] = useState([])
  const [models, setModels] = useState([])
  const [values, setValues] = useState({})
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    api.experimentTypes()
      .then((types) => setExpType(types.find((t) => t.name === experiment) || null))
      .catch((e) => setError(String(e.message || e)))
  }, [experiment])

  useEffect(() => {
    const load = () => api.experiments(experiment).then(setJobs).catch(() => {})
    load()
    const id = setInterval(load, 5000)
    return () => clearInterval(id)
  }, [experiment])

  const activeCount = jobs.filter((job) => ACTIVE_STATES.includes(job.status?.state)).length
  useEffect(() => { onFinished?.() }, [activeCount]) // eslint-disable-line react-hooks/exhaustive-deps

  const fields = useMemo(() => {
    const byName = Object.fromEntries((expType?.fields || []).map((f) => [f.name, f]))
    return controls.map((name) => byName[name]).filter(Boolean)
  }, [expType, controls])

  useEffect(() => {
    if (!fields.length || Object.keys(values).length) return
    setValues(Object.fromEntries(fields.map((f) => [f.name, String(f.default)])))
  }, [fields, values])

  async function submit() {
    setSubmitting(true)
    setError(null)
    try {
      const params = Object.fromEntries(Object.entries(values).map(([k, v]) => [k, [v]]))
      await api.submitExperiment(experiment, { ...params, model: models })
      setModels([])
      api.experiments(experiment).then(setJobs).catch(() => {})
    } catch (e) {
      setError(String(e.message || e))
    }
    setSubmitting(false)
  }

  return (
    <>
      {error && <p className="archive-line archive-line-warn">{error}</p>}
      <div className="trace-launch">
        <div className="pill-row trace-models">
          {(overview?.models || []).map((model) => (
            <button
              key={model.value}
              type="button"
              disabled={model.available === false}
              className={`pill${models.includes(model.value) ? ' selected' : ''}`}
              title={model.note || undefined}
              onClick={() => setModels((previous) => toggleGroup([model.value], previous))}
            >
              {model.label}
              <span className="trace-pill-note">{model.runs ? `${model.runs} run${model.runs === 1 ? '' : 's'}` : 'not run'}</span>
            </button>
          ))}
        </div>
        <div className="trace-settings">
          {fields.map((field) => (
            <label key={field.name} className="trace-setting" title={field.note || undefined}>
              <span>{field.label}</span>
              <select
                value={values[field.name] ?? ''}
                onChange={(e) => setValues((previous) => ({ ...previous, [field.name]: e.target.value }))}
              >
                {fieldOptions(field, overview?.fact_sets).map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
            </label>
          ))}
        </div>
        <LaunchBlockedNotice blockers={blockers} />
        <div className="trace-launch-actions">
          <span className="dataset-note">{costNote}</span>
          <button type="button" className="btn-primary" disabled={!models.length || submitting || blockers.length > 0}
            onClick={submit}>
            {submitting ? 'Submitting…' : `${verb} ${models.length} model${models.length === 1 ? '' : 's'}`}
          </button>
        </div>
      </div>

      {jobs.length > 0 && (
        <>
          <div className="dl-section-head">
            <h2 className="archive-section-title">Jobs</h2>
            <ClearFinishedButton experiment={experiment} jobs={jobs} activeStates={ACTIVE_STATES}
              onCleared={() => api.experiments(experiment).then(setJobs).catch(() => {})} />
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Run</th><th>State</th><th>Progress</th><th>So far</th><th>Submitted</th><th /></tr>
              </thead>
              <tbody>
                {jobs.map((job) => {
                  const state = job.status?.state || 'UNKNOWN'
                  const total = job.progress?.num_steps
                  const step = job.progress?.current_step
                  const tone = ACTIVE_STATES.includes(state) ? 'active' : FAIL_STATES.includes(state) ? 'failed' : 'done'
                  return (
                    <tr key={job.job_id}>
                      <td><code>{job.run_name}</code></td>
                      <td><span className={`trace-state is-${tone}`}>{state}</span></td>
                      <td>{step != null && total ? `${step} / ${total} facts` : '—'}</td>
                      <td>{progress(job.progress?.latest_metrics) || '—'}</td>
                      <td>{shortTime(job.submitted_at)}</td>
                      <td>
                        {ACTIVE_STATES.includes(state) && (
                          <button type="button" className="btn-plain-small"
                            onClick={() => api.cancelExperiment(job.job_id).then(() => api.experiments(experiment).then(setJobs))}>
                            Cancel
                          </button>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </>
      )}
    </>
  )
}
