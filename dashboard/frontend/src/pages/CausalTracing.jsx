import { useCallback, useEffect, useMemo, useState } from 'react'
import LaunchBlockedNotice from '../components/LaunchBlockedNotice.jsx'
import useCapabilities, { launchBlockers } from '../lib/useCapabilities.js'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine, ResponsiveContainer } from 'recharts'
import { api } from '../api.js'
import { ACTIVE_STATES, FAIL_STATES } from '../lib/queueStatus.js'
import { toggleGroup } from '../lib/groupSelect.js'

const EXPERIMENT = 'causal_tracing'

const KINDS = [
  { key: 'mlp', label: 'MLP', color: '#6ea8fe' },
  { key: 'hidden', label: 'Hidden state', color: '#9ece6a' },
  { key: 'attn', label: 'Attention', color: '#e0af68' },
]

// Which of the experiment type's own fields this page exposes. The rest keep
// their declared defaults; everything shown here reads its label, options and
// default straight out of dashboard.json, so the picker can't drift from what
// the runner accepts.
const CONTROLS = ['data_path', 'n_prompts', 'effect', 'window', 'token_grid']

// Below this many traced prompts, the peak layer is noise, not a finding.
const THIN_TRACE = 50

function fieldOptions(field) {
  if (!field) return []
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

function sameLayers(a, b) {
  return Array.isArray(a) && Array.isArray(b) && a.length === b.length && a.every((v, i) => v === b[i])
}

export default function CausalTracing() {
  const [expType, setExpType] = useState(null)
  const blockers = launchBlockers(useCapabilities(), EXPERIMENT)
  const [overview, setOverview] = useState(null)
  const [jobs, setJobs] = useState([])
  const [models, setModels] = useState([])
  const [values, setValues] = useState({})
  const [openRun, setOpenRun] = useState(null)
  const [grid, setGrid] = useState({})
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const loadOverview = useCallback(() => {
    api.causalTracing().then(setOverview).catch((e) => setError(String(e.message || e)))
  }, [])

  useEffect(() => {
    api.experimentTypes()
      .then((types) => setExpType(types.find((t) => t.name === EXPERIMENT) || null))
      .catch((e) => setError(String(e.message || e)))
    loadOverview()
  }, [loadOverview])

  useEffect(() => {
    const load = () => api.experiments(EXPERIMENT).then(setJobs).catch(() => {})
    load()
    const id = setInterval(load, 5000)
    return () => clearInterval(id)
  }, [])

  // A finished job means new curves to read.
  const activeCount = jobs.filter((job) => ACTIVE_STATES.includes(job.status?.state)).length
  useEffect(() => { loadOverview() }, [activeCount, loadOverview])

  const fields = useMemo(() => {
    const byName = Object.fromEntries((expType?.fields || []).map((f) => [f.name, f]))
    return CONTROLS.map((name) => byName[name]).filter(Boolean)
  }, [expType])

  useEffect(() => {
    if (!fields.length || Object.keys(values).length) return
    setValues(Object.fromEntries(fields.map((f) => [f.name, String(f.default)])))
  }, [fields, values])

  async function submit() {
    setSubmitting(true)
    setError(null)
    try {
      const params = Object.fromEntries(Object.entries(values).map(([k, v]) => [k, [v]]))
      await api.submitExperiment(EXPERIMENT, { ...params, model: models })
      setModels([])
      api.experiments(EXPERIMENT).then(setJobs).catch(() => {})
    } catch (e) {
      setError(String(e.message || e))
    }
    setSubmitting(false)
  }

  function openTrace(run) {
    const next = openRun === run ? null : run
    setOpenRun(next)
    if (next && grid[next] === undefined) {
      setGrid((previous) => ({ ...previous, [next]: null }))
      api.causalTrace(next)
        .then((trace) => setGrid((previous) => ({ ...previous, [next]: trace.token_grid || false })))
        .catch(() => setGrid((previous) => ({ ...previous, [next]: false })))
    }
  }

  const runsByName = Object.fromEntries((overview?.runs || []).map((row) => [row.run, row]))
  const openSummary = openRun ? runsByName[openRun] : null

  const chartData = useMemo(() => {
    if (!openSummary) return []
    return Array.from({ length: openSummary.n_layers }, (_, layer) => ({
      layer,
      ...Object.fromEntries(KINDS.map((kind) => [kind.key, openSummary[`aie_${kind.key}`]?.[layer]])),
    }))
  }, [openSummary])

  return (
    <div>
      <div className="page-header">
        <h1>Causal Tracing</h1>
      </div>

      <p className="dataset-note trace-intro">
        ROME, MEMIT, PMET and AlphaEdit all write to a <code>layers</code> hyperparameter, and that number is supposed to
        come from causal tracing: corrupt the subject tokens so the model loses the fact, then restore one site at a time
        and see which one brings the answer back. Where a model has no published trace, our hparams currently inherit a
        layer from a different model. This page runs the measurement and records the answer in{' '}
        <code>traced_layers.json</code>, which nothing reads automatically yet.
      </p>

      {error && <p className="archive-line archive-line-warn">{error}</p>}

      <h2 className="archive-section-title">Trace a model</h2>
      <div className="trace-launch">
        <div className="pill-row trace-models">
          {(overview?.models || []).map((model) => (
            <button
              key={model.value}
              type="button"
              className={`pill${models.includes(model.value) ? ' selected' : ''}`}
              title={model.note || undefined}
              onClick={() => setModels((previous) => toggleGroup([model.value], previous))}
            >
              {model.label}
              <span className="trace-pill-note">
                {model.traced ? `traced: ${model.traced.peak_layer}` : 'untraced'}
              </span>
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
                {fieldOptions(field).map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
            </label>
          ))}
        </div>

        <LaunchBlockedNotice blockers={blockers} />
        <div className="trace-launch-actions">
          <span className="dataset-note">
            One SLURM job per model. A 200-prompt trace is roughly an hour on a 7B model; the token grid multiplies that.
          </span>
          <button type="button" className="btn-primary" disabled={!models.length || submitting || blockers.length > 0} onClick={submit}>
            {submitting ? 'Submitting…' : `Trace ${models.length} model${models.length === 1 ? '' : 's'}`}
          </button>
        </div>
      </div>

      {jobs.length > 0 && (
        <>
          <h2 className="archive-section-title">Trace jobs</h2>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Run</th><th>State</th><th>Progress</th><th>Peak so far</th><th>Submitted</th><th />
                </tr>
              </thead>
              <tbody>
                {jobs.map((job) => {
                  const state = job.status?.state || 'UNKNOWN'
                  const total = job.progress?.num_steps
                  const step = job.progress?.current_step
                  const latest = job.progress?.latest_metrics
                  const tone = ACTIVE_STATES.includes(state) ? 'active' : FAIL_STATES.includes(state) ? 'failed' : 'done'
                  return (
                    <tr key={job.job_id}>
                      <td><code>{job.run_name}</code></td>
                      <td><span className={`trace-state is-${tone}`}>{state}</span></td>
                      <td>{step != null && total ? `${step} / ${total} prompts` : '—'}</td>
                      <td>{latest?.peak_layer != null ? `layer ${latest.peak_layer}` : '—'}</td>
                      <td>{shortTime(job.submitted_at)}</td>
                      <td>
                        {ACTIVE_STATES.includes(state) && (
                          <button
                            type="button"
                            className="btn-plain-small"
                            onClick={() => api.cancelExperiment(job.job_id).then(() => api.experiments(EXPERIMENT).then(setJobs))}
                          >
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

      <h2 className="archive-section-title">Edit layer by model</h2>
      <p className="dataset-note">
        What the hparams use today, beside what tracing found. <code>{overview?.mapping_path}</code> holds the traced
        column.
      </p>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Model</th><th>ROME</th><th>MEMIT</th><th>Traced</th><th>Effect</th>
              <th>AIE</th><th>Prompts</th><th>Dataset</th><th>Traced at</th>
            </tr>
          </thead>
          <tbody>
            {(overview?.models || []).map((model) => {
              const traced = model.traced
              const rome = model.hparams_layers?.ROME
              const differs = traced && rome && !sameLayers(traced.layers, rome)
              // A handful of prompts can put the peak anywhere. Say so, rather
              // than letting a smoke test read like a measurement.
              const thin = traced && traced.n_prompts < THIN_TRACE
              return (
                <tr key={model.value}>
                  <td>
                    {traced ? (
                      <button type="button" className="archive-run-toggle" onClick={() => openTrace(traced.run)}>
                        {model.label}
                      </button>
                    ) : model.label}
                  </td>
                  <td>{rome ? JSON.stringify(rome) : '—'}</td>
                  <td>{model.hparams_layers?.MEMIT ? JSON.stringify(model.hparams_layers.MEMIT) : '—'}</td>
                  <td className={differs && !thin ? 'trace-differs' : undefined}>
                    {traced ? JSON.stringify(traced.layers) : '—'}
                    {differs && !thin && <span className="trace-differs-note"> differs</span>}
                    {thin && (
                      <span className="trace-thin" title={`Only ${traced.n_prompts} prompts traced - too few for the peak to mean much. Re-trace with more.`}>
                        {' '}too few prompts
                      </span>
                    )}
                  </td>
                  <td>{traced?.effect || '—'}</td>
                  <td>{traced ? traced.peak_aie.toFixed(3) : '—'}</td>
                  <td>{traced?.n_prompts ?? '—'}</td>
                  <td>{traced?.dataset || '—'}</td>
                  <td>{shortTime(traced?.traced_at)}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {openSummary && (
        <>
          <h2 className="archive-section-title">{openSummary.model}: indirect effect by layer</h2>
          <p className="dataset-note">
            Recall probability restored by patching one site back into the corrupted run, at the last subject token,
            minus what the corrupted run managed on its own. Clean {openSummary.p_clean?.toFixed(3)}, corrupted{' '}
            {openSummary.p_corrupt?.toFixed(3)}, over {openSummary.n_prompts} prompts
            ({(openSummary.known_rate * 100).toFixed(0)}% of those scanned were recalled well enough to trace).
            MLP and attention restore a window of {openSummary.window} layers at a time; the hidden state restores one.
          </p>
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                <XAxis dataKey="layer" label={{ value: 'layer', position: 'insideBottom', offset: -4 }} />
                <YAxis width={70} tickFormatter={(v) => v.toFixed(2)} />
                <Tooltip formatter={(v) => (typeof v === 'number' ? v.toFixed(4) : v)} />
                <Legend />
                <ReferenceLine
                  x={openSummary.peak_layer}
                  stroke="#f7768e"
                  strokeDasharray="4 4"
                  label={{ value: `edit layer ${openSummary.peak_layer}`, position: 'top', fill: '#f7768e', fontSize: 11 }}
                />
                {KINDS.map((kind) => (
                  <Line key={kind.key} type="monotone" dataKey={kind.key} name={kind.label} stroke={kind.color} dot={false} />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>

          {grid[openRun] === null && <p className="dataset-note">Loading the token grid…</p>}
          {grid[openRun] === false && (
            <p className="dataset-note">
              This run traced only the last subject token. Re-run it with a token grid to get the heatmap.
            </p>
          )}
          {grid[openRun] && (
            <>
              <h2 className="archive-section-title">Where in the prompt, over {grid[openRun].n_prompts} prompts</h2>
              {KINDS.map((kind) => (
                <div key={kind.key} className="trace-heatmap">
                  <h3 className="trace-heatmap-title">{kind.label}</h3>
                  <div className="table-wrap">
                    <table className="heatmap-table">
                      <thead>
                        <tr>
                          <th>token</th>
                          {chartData.map((point) => <th key={point.layer}>{point.layer}</th>)}
                        </tr>
                      </thead>
                      <tbody>
                        {grid[openRun].grids[kind.key].map((row, bucket) => {
                          const peak = Math.max(...grid[openRun].grids[kind.key].flat().filter((v) => v != null), 0.0001)
                          return (
                            <tr key={bucket}>
                              <td className="heatmap-label">{grid[openRun].buckets[bucket]}</td>
                              {row.map((value, layer) => (
                                <td
                                  key={layer}
                                  title={value == null ? 'no prompt had a token here' : `layer ${layer}: ${value.toFixed(4)}`}
                                  style={value == null ? undefined : {
                                    background: `color-mix(in srgb, var(--accent) ${Math.round(Math.max(0, value / peak) * 100)}%, transparent)`,
                                  }}
                                />
                              ))}
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              ))}
            </>
          )}
        </>
      )}
    </div>
  )
}
