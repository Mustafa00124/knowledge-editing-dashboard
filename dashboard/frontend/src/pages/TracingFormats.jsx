import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api.js'
import ExperimentsSubnav from '../components/ExperimentsSubnav.jsx'
import InvestigationProgress from '../components/InvestigationProgress.jsx'

// Prompt format in tracing: the same facts traced as a completion, a
// question, through the chat template, as multiple choice or as a riddle.
// One row per model, one column per format, from the causal tracing runs
// (launched on the Knowledge localisation page with a format chosen).
const ORDER = ['completion', 'question', 'chat_question', 'chat_prefill', 'mcq', 'chat_mcq', 'riddle', 'chat_riddle']

function pct(v) {
  return v == null ? '—' : `${Math.round(v * 100)}%`
}

export default function TracingFormats() {
  const [overview, setOverview] = useState(null)
  const [error, setError] = useState(null)
  const [set, setSet] = useState('')

  useEffect(() => {
    api.causalTracing().then(setOverview).catch((e) => setError(String(e.message || e)))
  }, [])

  // Formats are only comparable on the same facts, so compare within one fact set.
  const runs = (overview?.runs || []).filter((r) => (r.window ?? 10) === 10 && r.fact_set_name)
  const sets = [...new Set(runs.map((r) => r.fact_set_name.split('/')[0]))].sort()
  const chosen = set || sets[0] || ''
  const inSet = runs.filter((r) => r.fact_set_name.split('/')[0] === chosen)
  const formats = ORDER.filter((f) => inSet.some((r) => (r.format || 'completion') === f))
  const models = [...new Set(inSet.map((r) => r.model))].sort()

  const cell = useMemo(() => {
    const latest = {}
    for (const r of inSet) {
      const key = `${r.model}|${r.format || 'completion'}`
      if (!latest[key] || (r.finished_at || '') > (latest[key].finished_at || '')) latest[key] = r
    }
    return latest
  }, [inSet])

  return (
    <div>
      <ExperimentsSubnav />
      <div className="hp-breadcrumb"><Link to="/experiments/investigations">Investigations</Link> / Prompt format in tracing</div>
      <div className="page-header"><h1>Prompt format in tracing</h1></div>
      <p className="dataset-note trace-intro">
        Does the way a fact is asked move where the model recalls it? Each cell is one causal trace of the same fact set
        in one format: peak MLP layer, the share of facts peaking in the early-to-mid band, and the verdict. Base models
        get the plain formats; instruct models also the chat template ones. Traces are launched from{' '}
        <Link to="/experiments/investigations/causal_tracing">Knowledge localisation</Link> with a format and fact set chosen.
      </p>
      {error && <p className="archive-line archive-line-warn">{error}</p>}
      <InvestigationProgress investigation="tracing_formats" />
      {sets.length > 1 && (
        <label className="trace-setting">
          <span>Fact set</span>
          <select value={chosen} onChange={(e) => setSet(e.target.value)}>
            {sets.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </label>
      )}
      {!inSet.length && overview && <p className="empty">No format traces yet.</p>}
      {inSet.length > 0 && (
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Model</th>{formats.map((f) => <th key={f}>{f}</th>)}</tr>
            </thead>
            <tbody>
              {models.map((model) => (
                <tr key={model}>
                  <td>{model}</td>
                  {formats.map((f) => {
                    const r = cell[`${model}|${f}`]
                    const rel = r?.reliability
                    return (
                      <td key={f} title={r ? `${r.n_prompts} facts · ${r.run}` : undefined}>
                        {r ? <>layer {r.peak_layer} · {pct(rel?.share_peak_in_band)} · {rel?.verdict || '—'}
                          {r.n_prompts < 50 && <span className="trace-thin"> thin</span>}</> : '—'}
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
