import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api.js'
import ExperimentsSubnav from '../components/ExperimentsSubnav.jsx'
import GpuQueue from '../components/GpuQueue.jsx'
import InvestigationProgress from '../components/InvestigationProgress.jsx'
import MechanisticDrawer from '../components/MechanisticDrawer.jsx'
import useQueue from '../lib/useQueue.js'

// Knowledge by prompt format: which formats base and instruct models show
// what they know in. One score_formats.py run per model; the same sampled
// facts per dataset for every model. Base models read the chat formats
// through their instruct sibling's template, so both see identical text.

const EXPERIMENT = 'format_knowledge'
const FAMILIES = [
  { label: 'Qwen3-4B', base: 'qwen3-4b-base', instruct: 'qwen3-4b-instruct-2507' },
  { label: 'Olmo-3-7B', base: 'olmo-3-7b-base', instruct: 'olmo-3-7b-instruct' },
  { label: 'SmolLM3-3B', base: 'smollm3-3b-base', instruct: 'smollm3-3b' },
  { label: 'MAP-Neo-7B', base: 'map-neo-7b', instruct: 'map-neo-7b-instruct' },
  { label: 'Llama-3.1-8B', base: 'llama-3.1-8b', instruct: 'llama-3.1-8b-instruct' },
  { label: 'Mistral-7B', base: 'mistral-7b-v0.1', instruct: 'mistral-7b-instruct-v0.1' },
]
const MODELS = FAMILIES.flatMap((f) => [f.base, f.instruct])
const DATASET_LABEL = {
  mquake: 'MQuAKE (popular Wikidata facts)', uniedit: 'UniEdit (25 domains, obscure facts)',
  zsre: 'ZsRE (questions)', realtimeqa: 'RealTimeQA (news, with choices)', riddles: 'Altered riddles',
}
const FORMAT_HELP = {
  completion: 'the bare sentence: "Fernando Santos is a citizen of"',
  chat_complete: 'chat template: "Complete this sentence: ...", with the sentence begun as the reply',
  question: 'plain text: "Question: ...? Answer:"',
  chat_question: 'chat template: the question, "answer with only the answer"',
  chat_prefill: 'chat template: the question, with the cloze sentence begun as the reply',
  mcq: 'plain text: question, lettered choices, "Answer:"',
  chat_mcq: 'chat template: the multiple-choice question, "answer with the letter only"',
  riddle: 'plain text: "Riddle: ... Answer:"',
  chat_riddle: 'chat template: the riddle, "answer with only the answer"',
}

const pct = (v) => (v == null ? '—' : `${Math.round(v * 100)}%`)
const mean = (xs) => (xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : null)

export default function FormatKnowledge() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const q = useQueue()
  const [drawerOpen, setDrawerOpen] = useState(false)

  const load = () => api.formatKnowledge().then(setData).catch((e) => setError(String(e.message || e)))
  useEffect(() => {
    load()
    const timer = setInterval(load, 20000)
    return () => clearInterval(timer)
  }, [])

  // model -> dataset -> format -> rates, from each model's latest run.
  const rates = useMemo(() => {
    const out = {}
    for (const run of [...(data?.runs || [])].sort((a, b) => (a.finished_at || '').localeCompare(b.finished_at || ''))) {
      out[run.model] = run.rates
    }
    return out
  }, [data])
  const datasets = Object.keys(DATASET_LABEL).filter((d) => Object.values(rates).some((r) => r?.[d]))
  const formatsOf = (d) => [...new Set(Object.values(rates).flatMap((r) => Object.keys(r?.[d] || {})))]
  const rate = (model, d, f) => rates[model]?.[d]?.[f]?.known_rate

  // Across families: the mean base and instruct known rate for one format.
  function side(d, f, which) {
    return mean(FAMILIES.map((fam) => rate(fam[which], d, f)).filter((v) => v != null))
  }

  return (
    <div>
      <ExperimentsSubnav />
      <div className="hp-breadcrumb"><Link to="/experiments/investigations">Investigations</Link> / Knowledge by prompt format</div>
      <div className="page-header">
        <h1>Knowledge by prompt format</h1>
        <button className="btn-primary" onClick={() => setDrawerOpen(true)}>+ New Scoring</button>
      </div>
      <p className="dataset-note trace-intro">
        In which prompt formats do base and instruct models show what they know? The same facts from each dataset are
        asked in every format the dataset allows. A fact counts as known when the model's most likely next token
        (setting whitespace aside) starts an accepted answer with at least 10% probability. Base models read the chat
        formats through their instruct sibling's template, so both see exactly the same prompt and any difference
        comes from the tuning. Whether the format also moves <em>where</em> a fact is recalled is the{' '}
        <Link to="/experiments/investigations/tracing_formats">tracing by format</Link> investigation.
      </p>
      {error && <p className="archive-line archive-line-warn">{error}</p>}

      <GpuQueue q={q} />

      <InvestigationProgress investigation="format_knowledge" />

      {datasets.length > 0 && (
        <>
          <h2 className="archive-section-title">Base or instruct, by format</h2>
          <p className="dataset-note">
            Mean known rate across the four families. The difference is instruct minus base, in points.
          </p>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Dataset</th><th>Format</th><th>Base</th><th>Instruct</th><th>Instruct − base</th></tr></thead>
              <tbody>
                {datasets.flatMap((d) => formatsOf(d).map((f, i) => {
                  const b = side(d, f, 'base')
                  const ins = side(d, f, 'instruct')
                  const diff = b != null && ins != null ? Math.round((ins - b) * 100) : null
                  return (
                    <tr key={`${d}-${f}`}>
                      <td>{i === 0 ? DATASET_LABEL[d] : ''}</td>
                      <td title={FORMAT_HELP[f]}>{f}</td>
                      <td>{pct(b)}</td>
                      <td>{pct(ins)}</td>
                      <td className={diff == null ? undefined : diff >= 5 ? 'fk-instruct' : diff <= -5 ? 'fk-base' : undefined}>
                        {diff == null ? '—' : `${diff > 0 ? '+' : ''}${diff}`}
                      </td>
                    </tr>
                  )
                }))}
              </tbody>
            </table>
          </div>

          <h2 className="archive-section-title">Every model</h2>
          {datasets.map((d) => (
            <div key={d}>
              <h3 className="trace-heatmap-title">{DATASET_LABEL[d]}</h3>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr><th>Format</th>{FAMILIES.map((fam) => <th key={fam.label}>{fam.label}<br /><span className="dl-dim">base / instruct</span></th>)}</tr>
                  </thead>
                  <tbody>
                    {formatsOf(d).map((f) => (
                      <tr key={f}>
                        <td title={FORMAT_HELP[f]}>{f}</td>
                        {FAMILIES.map((fam) => (
                          <td key={fam.label}>{pct(rate(fam.base, d, f))} / {pct(rate(fam.instruct, d, f))}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </>
      )}
      {data && !datasets.length && <p className="empty">No models scored yet.</p>}
      <MechanisticDrawer
        open={drawerOpen}
        onToggle={() => setDrawerOpen((o) => !o)}
        onClose={() => setDrawerOpen(false)}
        title="New Scoring"
        queue={q.queue}
        onStage={q.stage}
        expType={q.experimentTypes.find((t) => t.name === EXPERIMENT)}
        models={MODELS.map((m) => ({ value: m, label: m, tag: rates[m] ? 'scored' : 'not scored' }))}
        costNote="One job per model, all five datasets, 500 facts each: a few minutes per model."
      />
    </div>
  )
}
