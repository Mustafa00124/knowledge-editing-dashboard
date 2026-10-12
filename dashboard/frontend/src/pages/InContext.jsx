import { useEffect, useMemo, useState } from 'react'
import { api } from '../api.js'
import ExperimentsSubnav from '../components/ExperimentsSubnav.jsx'
import ExperimentDrawer from '../components/ExperimentDrawer.jsx'
import GpuQueue from '../components/GpuQueue.jsx'
import InvestigationProgress from '../components/InvestigationProgress.jsx'
import useQueue from '../lib/useQueue.js'

// The second kind of main experiment: in-context editing (SCR) with the
// needed fact hidden among other facts. A weight-edited model has to find a
// fact among everything it knows; a knowledge base holding only that fact
// makes retrieval trivial, so each fact is asked against kb_size-1
// distractors instead, at several sizes, to see where retrieval breaks.

const EXPERIMENT = 'in_context'
const BASE_MODELS = ['qwen3-4b-base', 'olmo-3-7b-base', 'smollm3-3b-base', 'map-neo-7b']
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
  const q = useQueue()
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [viewMode, setViewMode] = useState('exact_match')
  const [criterion, setCriterion] = useState('reliability')

  const load = () => api.inContext().then(setData).catch((e) => setError(String(e.message || e)))
  useEffect(() => {
    load()
    const timer = setInterval(load, 20000)
    return () => clearInterval(timer)
  }, [])

  const type = q.experimentTypes.find((t) => t.name === EXPERIMENT)
  // Stable, so the drawer does not reset its form on every render.
  const drawerTypes = useMemo(() => (type ? [type] : []), [type])
  // The drawer starts with the base models, the four datasets the sweeps use,
  // every knowledge base size, and a generation-based score beside Original.
  const drawerDefaults = useMemo(() => {
    const subsets = (type?.fields.find((f) => f.name === 'data_path')?.benchmarks || []).flatMap((b) => b.subsets)
    const models = (type?.fields.find((f) => f.name === 'model')?.options || [])
      .filter((o) => BASE_MODELS.includes(o.value) && o.available !== false).map((o) => o.value)
    return {
      model: models.length ? models : undefined,
      data_path: subsets.filter((s) => DEFAULT_SUBSETS.includes(s.label) && s.available !== false).map((s) => s.value),
      kb_size: KB_SIZES,
      evaluation_modes: ['original,exact_match'],
    }
  }, [type])

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
      <div className="page-header">
        <h1>In context</h1>
        <button className="btn-primary" onClick={() => setDrawerOpen(true)}>+ New Experiment</button>
      </div>
      <p className="hp-intro">
        In-context editing (SCR: retrieve, confirm, answer) compared with the best weight-editing methods. A
        weight-edited model has to find the edited fact among everything it already knows, but a knowledge base
        holding only that fact makes retrieval trivial. So each fact is asked against a knowledge base of other facts
        with its own fact added: from the same dataset first, then its training file, then other datasets. Growing
        the knowledge base shows where retrieval starts to fail. With one seed the bases are nested (the 100 facts
        are inside the 1,000). Runs use <strong>test records</strong>, like the other main experiments. SCR answers by
        generating, so compare it with weight-editing methods under a generation-based score (exact match or the LLM
        judge), not Original.
      </p>
      {error && <p className="archive-line archive-line-warn">{error}</p>}

      <GpuQueue q={q} />
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
      <ExperimentDrawer
        open={drawerOpen}
        onToggle={() => setDrawerOpen((o) => !o)}
        onClose={() => setDrawerOpen(false)}
        experimentTypes={drawerTypes}
        queue={q.queue}
        onSubmit={q.stage}
        defaults={Object.fromEntries(Object.entries(drawerDefaults).filter(([, v]) => v?.length))}
      />
    </div>
  )
}
