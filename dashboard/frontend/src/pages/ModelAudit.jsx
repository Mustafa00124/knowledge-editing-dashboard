import { useEffect, useMemo, useState } from 'react'
import { api } from '../api.js'
import ExperimentDrawer from '../components/ExperimentDrawer.jsx'
import GpuQueue from '../components/GpuQueue.jsx'
import InvestigationProgress from '../components/InvestigationProgress.jsx'
import useQueue from '../lib/useQueue.js'

// Before any editing: does each model already know Sid's Dataset's facts in
// their original form? One audit run per model asks every query, and the
// local Qwen3-4B judge labels each answer. Click a model to see the facts it
// does not know and every response behind them.

const EXPERIMENT = 'model_audit'
const MODEL_ORDER = [
  'qwen3-4b-base', 'qwen3-4b-instruct-2507', 'olmo-3-7b-base', 'olmo-3-7b-instruct',
  'smollm3-3b-base', 'smollm3-3b', 'map-neo-7b', 'map-neo-7b-instruct',
]
const QUERY_TYPES = [
  { key: 'direct', label: 'Direct' },
  { key: 'paraphrase', label: 'Paraphrase' },
  { key: 'cross_lingual', label: 'Cross-lingual' },
  { key: 'derived', label: 'Derived' },
]
const LABEL_CLASS = { ORIGINAL: 'audit-pass', NEW: 'audit-fail', OTHER: 'audit-fail', NONE: 'audit-fail', UNCLEAR: 'audit-unclear' }

const ratio = (t) => (t && t.scored ? `${t.pass}/${t.scored}` : '—')
const pctOf = (a, b) => (b ? `${Math.round((100 * a) / b)}%` : '—')
const secs = (s) => (s == null ? '—' : s >= 90 ? `${(s / 60).toFixed(1)} min` : `${Math.round(s)} s`)

function Pills({ options, selected, onToggle }) {
  return (
    <div className="pill-row">
      {options.map((o) => (
        <button key={o.value} type="button"
          className={`pill${selected.includes(o.value) ? ' selected' : ''}`} onClick={() => onToggle(o.value)}>
          {o.label}
        </button>
      ))}
    </div>
  )
}

function Detail({ run }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [show, setShow] = useState('unknown')
  const [open, setOpen] = useState({})
  useEffect(() => {
    setData(null)
    api.modelAuditRun(run).then(setData).catch((e) => setError(String(e.message || e)))
  }, [run])
  if (error) return <p className="archive-line archive-line-warn">{error}</p>
  if (!data) return <p className="empty">Loading…</p>

  const s = data.summary
  const byRecord = {}
  for (const r of data.responses) (byRecord[r.record_id] ??= []).push(r)
  const facts = s.facts.filter((f) =>
    show === 'all' ? true : show === 'fixtures' ? f.fixture : show === 'unknown' ? !f.fixture && f.known !== 1 : !f.fixture && f.known === 1)

  return (
    <div className="audit-detail">
      <h3 className="trace-heatmap-title">{s.model}</h3>
      <div className="table-wrap">
        <table>
          <thead><tr><th>By</th><th>Value</th><th>Queries with the original answer</th><th>Unclear</th></tr></thead>
          <tbody>
            {['topic', 'box', 'language', 'query_type'].flatMap((key) =>
              Object.entries(s.by?.[key] || {}).map(([value, t]) => (
                <tr key={key + value}><td>{key.replace('_', ' ')}</td><td>{value}</td>
                  <td>{ratio(t)} ({pctOf(t.pass, t.scored)})</td><td>{t.unclear}</td></tr>
              )))}
          </tbody>
        </table>
      </div>
      <div className="pill-field">
        <div className="pill-field-label">Facts</div>
        <Pills selected={[show]} onToggle={setShow} options={[
          { value: 'unknown', label: `Not known (${s.facts_total - s.facts_known})` },
          { value: 'known', label: `Known (${s.facts_known})` },
          { value: 'fixtures', label: `Fixtures (${s.fixtures})` },
          { value: 'all', label: 'All' },
        ]} />
      </div>
      {show === 'fixtures' && (
        <p className="hp-intro">Fixtures are constructed facts (named loans, hypothetical events) no model can know; their original
          is loaded into the model before the edit, so failing here is expected.</p>
      )}
      {!facts.length && <p className="empty">None.</p>}
      {facts.map((f) => {
        const rows = byRecord[f.record_id] || []
        const isOpen = open[f.record_id] ?? show === 'unknown'
        return (
          <div key={f.record_id} className="audit-fact">
            <button type="button" className="audit-fact-head" onClick={() => setOpen((o) => ({ ...o, [f.record_id]: !isOpen }))}>
              <span>{isOpen ? '▾' : '▸'} {f.record_id}</span>
              <span className="audit-tags">{f.topic} · {f.box} · {f.edit_operation}</span>
              <span className={f.known === 1 ? 'audit-pass' : f.known === 0 ? 'audit-fail' : 'audit-unclear'}>
                {f.fixture ? 'fixture' : f.known === 1 ? 'known' : f.known === 0 ? 'not known' : 'unclear'}
              </span>
              <span>{f.queries_passed}/{f.queries_scored} queries</span>
            </button>
            {isOpen && (
              <div className="table-wrap">
                <table className="audit-table">
                  <thead><tr><th>Query</th><th>Question</th><th>Original answer</th><th>Response</th><th>Label</th><th>Judge's reason</th></tr></thead>
                  <tbody>
                    {rows.map((r, i) => (
                      <tr key={i} className={r.judged ? '' : 'audit-muted'}>
                        <td>{r.query_type.replace('_', ' ')}{r.language !== 'en' ? ` (${r.language})` : ''}</td>
                        <td>{r.prompt}</td>
                        <td>{r.judged ? r.original_answer ?? '—' : r.query_type.startsWith('unrelated') ? 'baseline' : '—'}</td>
                        <td>{r.response || <em>empty</em>}</td>
                        <td className={LABEL_CLASS[r.label] || ''}>{r.label || 'not judged'}</td>
                        <td>{r.reason || ''}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

export default function ModelAudit() {
  const q = useQueue()
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [selected, setSelected] = useState(null)

  const load = () => api.modelAudit().then(setData).catch((e) => setError(String(e.message || e)))
  useEffect(() => {
    load()
    const timer = setInterval(load, 20000)
    return () => clearInterval(timer)
  }, [])

  const type = q.experimentTypes.find((t) => t.name === EXPERIMENT)
  const drawerTypes = useMemo(() => (type ? [type] : []), [type])
  const drawerDefaults = useMemo(() => {
    const models = (type?.fields.find((f) => f.name === 'model')?.options || [])
      .filter((o) => o.available !== false).map((o) => o.value)
    return models.length ? { model: models } : {}
  }, [type])

  // Latest run per model, in family order.
  const runs = useMemo(() => {
    const latest = {}
    for (const r of data?.runs || []) if (MODEL_ORDER.includes(r.model) && (!latest[r.model] || r.finished_at > latest[r.model].finished_at)) latest[r.model] = r
    const rank = (m) => (MODEL_ORDER.indexOf(m) + 1) || 99
    return Object.values(latest).sort((a, b) => rank(a.model) - rank(b.model))
  }, [data])

  return (
    <div>
      <div className="page-header">
        <h1>Model audit</h1>
        <button className="btn-primary" onClick={() => setDrawerOpen(true)}>+ New audit</button>
      </div>
      <p className="hp-intro">
        Before any editing, does each model already know Sid's Dataset's facts in their original form? Every question
        with an original answer to check (not locality) is asked as a free-form question (base models: a few-shot Question/Answer template that stops at the line break;
        instruct models: their chat template), and the local Qwen3-4B judge, shown only the original answer, labels each response. A fact is
        <strong> known</strong> when its direct and paraphrase questions both get the original answer (for an RBox property: the direct question and both instance questions). Fixtures
        (constructed facts no model can know) are counted apart. Click a model for the facts it does not know and every
        response.
      </p>
      {error && <p className="archive-line archive-line-warn">{error}</p>}

      <GpuQueue q={q} />
      <InvestigationProgress investigation={EXPERIMENT} />

      <h2 className="archive-section-title">Summary</h2>
      {data && !runs.length && <p className="empty">No audits finished yet.</p>}
      {runs.length > 0 && (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Model</th><th>Facts known</th>
                {QUERY_TYPES.map((t) => <th key={t.key}>{t.label}</th>)}
                <th>All queries</th><th>Unclear</th><th>Judge check</th><th>Time</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((r) => (
                <tr key={r.run} className={`audit-row${selected === r.run ? ' selected' : ''}`} onClick={() => setSelected(r.run)}
                  title="show this model's facts and responses">
                  <td>{r.model}{r.chat ? ' (chat)' : ''}</td>
                  <td><strong>{r.facts_known}/{r.facts_total}</strong> ({pctOf(r.facts_known, r.facts_total)})</td>
                  {QUERY_TYPES.map((t) => <td key={t.key}>{ratio(r.by?.query_type?.[t.key])}</td>)}
                  <td>{ratio(r.queries)}</td>
                  <td>{r.queries?.unclear ?? '—'}</td>
                  <td title={(r.judge_check?.misses || []).map((m) => `${m.response} → ${m.got} (expected ${m.expect})`).join('\n') || 'hand-labelled judge cases'}>
                    {r.judge_check ? `${r.judge_check.agree}/${r.judge_check.total}` : '—'}
                  </td>
                  <td title={Object.entries(r.timings || {}).map(([k, v]) => `${k}: ${v}`).join('\n')}>{secs(r.timings?.total_s)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {selected && <Detail run={selected} />}

      <ExperimentDrawer
        open={drawerOpen}
        onToggle={() => setDrawerOpen((o) => !o)}
        onClose={() => setDrawerOpen(false)}
        experimentTypes={drawerTypes}
        queue={q.queue}
        onSubmit={q.stage}
        defaults={drawerDefaults}
      />
    </div>
  )
}
