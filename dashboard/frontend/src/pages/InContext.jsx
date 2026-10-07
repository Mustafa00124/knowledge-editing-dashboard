import { useEffect, useMemo, useState } from 'react'
import { api } from '../api.js'
import ExperimentsSubnav from '../components/ExperimentsSubnav.jsx'
import InvestigationProgress from '../components/InvestigationProgress.jsx'

// The second kind of main experiment: in-context editing (SCR) with the
// needed fact hidden among other facts. A weight-edited model has to find a
// fact among everything it knows; a knowledge base holding only that fact
// makes retrieval trivial, so each fact is asked against kb_size-1
// distractors instead, at several sizes, to see where retrieval breaks.

const EXPERIMENT = 'in_context'
const BASE_MODELS = ['qwen3-4b-base', 'olmo-3-7b-base', 'llama-3.1-8b', 'mistral-7b-v0.1', 'gpt-j-6b']
const DEFAULT_SUBSETS = ['wiki_recent', 'wiki_counterfact', 'ZsRE', 'Temporal']
const KB_SIZES = ['1', '10', '100', '1000', '10000']
const CRITERIA = [
  { key: 'fluency', label: 'Fluency' },
  { key: 'reliability', label: 'Reliability' },
  { key: 'locality', label: 'Locality' },
  { key: 'generalizability', label: 'Generalizability' },
]
const MODE_LABEL = { original: 'Original', exact_match: 'Exact match', bertscore: 'BERTScore', llm_judge: 'LLM judge' }

const pct = (v) => (v == null ? '—' : `${Math.round(v * 100)}%`)
const toggle = (setter) => (value) => setter((prev) => (prev.includes(value) ? prev.filter((x) => x !== value) : [...prev, value]))

function Pills({ options, selected, onToggle }) {
  return (
    <div className="pill-row">
      {options.map((o) => (
        <button key={o.value} type="button" disabled={o.disabled} title={o.note || ''}
          className={`pill${selected.includes(o.value) ? ' selected' : ''}${o.disabled ? ' disabled' : ''}`}
          onClick={() => onToggle(o.value)}>
          {o.label}
        </button>
      ))}
    </div>
  )
}

export default function InContext() {
  const [type, setType] = useState(null)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [models, setModels] = useState(['qwen3-4b-base'])
  const [datasets, setDatasets] = useState([])
  const [kbSizes, setKbSizes] = useState(KB_SIZES)
  const [facts, setFacts] = useState('100')
  const [modes, setModes] = useState(['original', 'exact_match'])
  const [submitting, setSubmitting] = useState(false)
  const [message, setMessage] = useState(null)
  const [viewMode, setViewMode] = useState('exact_match')
  const [criterion, setCriterion] = useState('reliability')

  const load = () => api.inContext().then(setData).catch((e) => setError(String(e.message || e)))
  useEffect(() => {
    api.experimentTypes().then((types) => {
      const t = types.find((x) => x.name === EXPERIMENT)
      setType(t || null)
      const field = t?.fields.find((f) => f.name === 'data_path')
      const subsets = (field?.benchmarks || []).flatMap((b) => b.subsets)
      setDatasets(subsets.filter((s) => DEFAULT_SUBSETS.includes(s.label) && s.available !== false).map((s) => s.value))
    }).catch((e) => setError(String(e.message || e)))
    load()
    const timer = setInterval(load, 20000)
    return () => clearInterval(timer)
  }, [])

  const fields = useMemo(() => Object.fromEntries((type?.fields || []).map((f) => [f.name, f])), [type])
  const modelOptions = (fields.model?.options || []).filter((o) => BASE_MODELS.includes(o.value))
    .map((o) => ({ value: o.value, label: o.label || o.value, disabled: o.available === false, note: o.note }))
  const modeOptions = (fields.evaluation_modes?.options || [])
    .map((o) => ({ value: o.value, label: o.label, disabled: o.available === false, note: o.note }))
  const runCount = models.length * datasets.length * kbSizes.length

  async function launch() {
    setSubmitting(true)
    setMessage(null)
    try {
      await api.submitExperiment(EXPERIMENT, {
        model: models, data_path: datasets, kb_size: kbSizes, ds_size: [facts],
        evaluation_modes: [modes.join(',')],
      })
      setMessage({ ok: true, text: `Submitted ${runCount} run${runCount === 1 ? '' : 's'}.` })
    } catch (e) {
      setMessage({ ok: false, text: String(e.message || e) })
    }
    setSubmitting(false)
  }

  // dataset label -> model -> kb_size -> scores of the latest run.
  const table = useMemo(() => {
    const out = {}
    const rows = [...(data?.runs || [])].sort((a, b) => (a.finished_at || '').localeCompare(b.finished_at || ''))
    for (const run of rows) {
      const name = [run.dataset_benchmark, run.dataset_subset].filter(Boolean).join(' · ')
      out[name] ??= {}
      out[name][run.model] ??= {}
      out[name][run.model][run.kb_size] = run
    }
    return out
  }, [data])
  const sizesSeen = [...new Set((data?.runs || []).map((r) => r.kb_size))].filter((v) => v != null).sort((a, b) => a - b)
  const modesSeen = [...new Set((data?.runs || []).flatMap((r) => Object.keys(r.scores || {})))]

  return (
    <div>
      <ExperimentsSubnav />
      <div className="page-header"><h1>In context</h1></div>
      <p className="hp-intro">
        In-context editing (SCR: retrieve, confirm, answer) compared with the best weight-editing methods. A
        weight-edited model has to find the edited fact among everything it already knows, but a knowledge base
        holding only that fact makes retrieval trivial. So each fact is asked against a knowledge base of other facts
        with its own fact added: from the same dataset first, then its training file, then other datasets. Growing
        the knowledge base shows where retrieval starts to fail. With one seed the bases are nested (the 100 facts
        are inside the 1,000). Runs use <strong>test records</strong>, like the other main experiments.
      </p>
      {error && <p className="archive-line archive-line-warn">{error}</p>}

      <h2 className="archive-section-title">Launch</h2>
      {!type && !error && <p className="empty">Loading…</p>}
      {type && (
        <>
          <div className="pill-field">
            <div className="pill-field-label">Models</div>
            <Pills options={modelOptions} selected={models} onToggle={toggle(setModels)} />
          </div>
          {(fields.data_path?.benchmarks || []).map((b) => (
            <div className="pill-field" key={b.label}>
              <div className="pill-field-label">{b.label}</div>
              <Pills options={b.subsets.map((s) => ({ value: s.value, label: s.label, disabled: s.available === false, note: s.note }))}
                selected={datasets} onToggle={toggle(setDatasets)} />
            </div>
          ))}
          <div className="pill-field">
            <div className="pill-field-label">Knowledge base size</div>
            <div className="pill-field-note">facts in the knowledge base when a question is asked; 1 is the fact alone</div>
            <Pills options={KB_SIZES.map((v) => ({ value: v, label: Number(v).toLocaleString() }))}
              selected={kbSizes} onToggle={toggle(setKbSizes)} />
          </div>
          <div className="pill-field">
            <div className="pill-field-label">Facts asked per dataset</div>
            <Pills options={['20', '50', '100', 'full'].map((v) => ({ value: v, label: v }))}
              selected={[facts]} onToggle={setFacts} />
          </div>
          <div className="pill-field">
            <div className="pill-field-label">Evaluation</div>
            <div className="pill-field-note">
              SCR answers by generating, so compare it with weight-editing methods under a generation-based mode
              (exact match or the LLM judge), not Original.
            </div>
            <Pills options={modeOptions} selected={modes} onToggle={toggle(setModes)} />
          </div>
          <div className="trace-launch-actions">
            <span className="dataset-note">
              {runCount} run{runCount === 1 ? '' : 's'}: one per model, dataset and knowledge base size.
            </span>
            <button type="button" className="btn-primary" disabled={!runCount || !modes.length || submitting} onClick={launch}>
              {submitting ? 'Submitting…' : `Launch ${runCount} run${runCount === 1 ? '' : 's'}`}
            </button>
          </div>
          {message && <p className={message.ok ? 'dl-bar-ok' : 'archive-line archive-line-warn'}>{message.text}</p>}
        </>
      )}
      <InvestigationProgress investigation={EXPERIMENT} />

      <h2 className="archive-section-title">Results by knowledge base size</h2>
      {data && !data.runs.length && <p className="empty">No runs finished yet.</p>}
      {data && data.runs.length > 0 && (
        <>
          <div className="pill-field">
            <div className="pill-field-label">Evaluation</div>
            <Pills options={modesSeen.map((m) => ({ value: m, label: MODE_LABEL[m] || m }))}
              selected={[modesSeen.includes(viewMode) ? viewMode : modesSeen[0]]} onToggle={setViewMode} />
          </div>
          <div className="pill-field">
            <div className="pill-field-label">Criterion</div>
            <Pills options={CRITERIA.map((c) => ({ value: c.key, label: c.label }))}
              selected={[criterion]} onToggle={setCriterion} />
          </div>
          {Object.entries(table).map(([name, byModel]) => (
            <div key={name}>
              <h3 className="trace-heatmap-title">{name}</h3>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr><th>Model</th>{sizesSeen.map((n) => <th key={n}>{Number(n).toLocaleString()} facts</th>)}</tr>
                  </thead>
                  <tbody>
                    {Object.entries(byModel).map(([model, bySize]) => (
                      <tr key={model}>
                        <td>{model}</td>
                        {sizesSeen.map((n) => {
                          const run = bySize[n]
                          const mode = modesSeen.includes(viewMode) ? viewMode : modesSeen[0]
                          const sources = run?.kb_distractors
                            ? Object.entries(run.kb_distractors).map(([k, v]) => `${v} from ${k}`).join(', ')
                            : ''
                          return <td key={n} title={sources}>{pct(run?.scores?.[mode]?.[criterion])}</td>
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </>
      )}
    </div>
  )
}
