import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../api.js'
import {
  BOXES,
  DERIVABILITY,
  DETERMINACY,
  EDIT_OPERATIONS,
  EVIDENCE_CLAIMS,
  FICTIONAL,
  INDETERMINATE,
  INFINIGRAM_INDEXES,
  LOGIC,
  SOURCE_KINDS,
  THEORY,
  QUERY_TYPES,
  RELATION_SEMANTICS,
  relationProperties,
  relationPropertyOf,
  TOPICS,
  coordinateSummary,
  worldLabel,
} from '../../lib/sidsDatasetTaxonomy.js'
import DerivationModal, { hasChain } from './DerivationModal.jsx'
import DatasetSummary from './DatasetSummary.jsx'
import SidsCriteriaModal from './SidsCriteriaModal.jsx'

// Browses the records under the categorization: edit operation, then the
// knowledge form layers (topic, box). Each tab shows how many records it
// holds given the layers above it, and the records at the selected coordinate
// are listed below with every query.
// Explanations of each layer live in SidsDatasetInfoModal (the "?"), not here.
// Relation semantics and properties are tags, shown on each record.
const LAYERS = ['edit_operation', 'topic', 'box']

// Whether a record matches the coordinate on every layer above `upTo` (all
// layers when `upTo` is left out).
function matches(rec, coordinate, upTo) {
  const above = upTo ? LAYERS.slice(0, LAYERS.indexOf(upTo)) : LAYERS
  for (const layer of above) {
    if (rec[layer] !== coordinate[layer]) return false
  }
  return true
}

function TabRow({ label, values, selected, onSelect, counts }) {
  return (
    <div className="subnav" aria-label={label}>
      {values.map((v) => (
        <button
          key={v.key}
          type="button"
          aria-pressed={selected === v.key}
          className={`subnav-tab${selected === v.key ? ' active' : ''}`}
          onClick={() => onSelect(v.key)}
        >
          {v.label}{counts ? <span className="sids-tab-count">{counts[v.key] || 0}</span> : null}
        </button>
      ))}
    </div>
  )
}

// In record order: locality before derived.
const QUERY_LABEL = { direct: 'Direct', paraphrase: 'Paraphrase', cross_lingual: 'Cross-lingual',
  unrelated_near: 'Unrelated (near)', unrelated_far: 'Unrelated (far)', derived: 'Derived' }
const show = (v) => (v == null ? '—' : String(v))

// Each row also gets the model audit's query key (audit_queries.py):
// direct, paraphrase, cross_lingual[zh], unrelated_near[0], derived[2].
function queryRows(rec) {
  const q = rec.queries || {}
  const rows = []
  for (const key of Object.keys(QUERY_LABEL)) {
    const items = Array.isArray(q[key]) ? q[key] : q[key] ? [q[key]] : []
    items.forEach((item, i) => {
      const auditKey = key === 'direct' || key === 'paraphrase' ? key
        : key === 'cross_lingual' ? `cross_lingual[${item.language}]` : `${key}[${i}]`
      rows.push({ key, auditKey, ...item })
    })
  }
  return rows
}

// Model audit status dots. Short names keep the tooltips readable.
const MODEL_LABEL = {
  'qwen3-4b-instruct-2507': 'Qwen3-4B-Instruct', 'olmo-3-7b-instruct': 'Olmo-3-7B-Instruct',
  'llama-3.1-8b-instruct': 'Llama-3.1-8B-Instruct', 'mistral-7b-instruct-v0.1': 'Mistral-7B-Instruct',
  'qwen3-4b-base': 'Qwen3-4B-Base', 'olmo-3-7b-base': 'Olmo-3-7B-Base', 'llama-3.1-8b': 'Llama-3.1-8B',
  'mistral-7b-v0.1': 'Mistral-7B', 'smollm3-3b-base': 'SmolLM3-3B-Base', 'smollm3-3b': 'SmolLM3-3B',
  'map-neo-7b': 'MAP-Neo-7B', 'map-neo-7b-instruct': 'MAP-Neo-7B-Instruct',
}
const modelLabel = (m) => MODEL_LABEL[m] || m
const STATUS_TEXT = {
  green: 'green (gave the expected pre-edit answer)',
  red: 'red (did not give it)',
  yellow: 'not audited (or stale since the record changed, or the judge could not label it)',
}

// One dot per model in the fixed order; a model the audit never asks this
// query of (no pre-edit answer) gets an empty ring.
function AuditDots({ statuses, models }) {
  if (!models?.length) return null
  return (
    <span className="sids-audit-dots">
      {models.map((m) => {
        const s = statuses?.[m] || 'na'
        const text = s === 'na' ? 'not asked (no pre-edit answer to check)' : STATUS_TEXT[s] || s
        return <span key={m} className={`sids-audit-dot is-${s}`} title={`${modelLabel(m)}: ${text}`} />
      })}
    </span>
  )
}

// "geography-replace-0002" -> "Geography 2". The operation is already the
// selected tab, so the label keeps only topic and number.
function recordLabel(id) {
  const m = /^([a-z_]+)-[a-z_]+-0*(\d+)$/i.exec(id || '')
  if (!m) return id
  const topic = TOPICS.find((t) => t.key === m[1])?.label || m[1].replace(/_/g, ' ')
  return `${topic.charAt(0).toUpperCase()}${topic.slice(1)} ${m[2]}`
}

// Shown label for a stored key ("very_likely" -> "Very likely").
const labelOf = (list, key) => list.find((x) => x.key === key)?.label ?? String(key).replace(/_/g, ' ')
// Query type -> the metric it feeds, which picks the pill colour.
const METRIC_OF = Object.fromEntries(QUERY_TYPES.map((q) => [q.key, q.metric.replace(/[^a-z]/g, '')]))

// One property under the statement: a small caption over its value, tinted
// by kind (change, relation, derivability, ...).
function Chip({ kind, label, children }) {
  return (
    <span className={`sids-chip sids-chip-${kind}`}>
      {label && <span className="sids-chip-label">{label}</span>}
      <span className="sids-chip-value">{children}</span>
    </span>
  )
}

// The evidence behind one fact (README, Evidence): why we rate it stored or
// derived, with the corpus counts, quotes and searches that back it.
function EvidenceModal({ fact, entry, onClose }) {
  useEffect(() => {
    const onKey = (ev) => { if (ev.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])
  const claim = EVIDENCE_CLAIMS.find((c) => c.key === entry.claim)
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal sids-evidence-modal" onClick={(ev) => ev.stopPropagation()} role="dialog" aria-modal="true" aria-label="Evidence">
        <div className="modal-header">
          <div className="modal-title-group">
            <h2>Why {claim ? claim.label.toLowerCase() : entry.claim}?</h2>
            <span className={`sids-evidence-claim is-${entry.claim}`}>{claim?.label || entry.claim}</span>
          </div>
          <button type="button" className="btn-plain" onClick={onClose} aria-label="Close">✕</button>
        </div>
        <div className="modal-body">
          <p className="sids-evidence-fact">{fact}</p>
          <p>{entry.why}</p>
          <ul className="sids-evidence-sources">
            {(entry.sources || []).map((src, i) => (
              <li key={i}>
                <span className="sids-evidence-kind">{SOURCE_KINDS[src.kind] || src.kind}</span>
                {src.kind === 'infini-gram' && (
                  <span>
                    <q>{src.query}</q>: <strong>{Number(src.count).toLocaleString()}</strong>
                    {src.index && <span className="sids-evidence-dim"> in {INFINIGRAM_INDEXES[src.index] || src.index}</span>}
                  </span>
                )}
                {(src.kind === 'wikipedia' || src.kind === 'web') && (
                  <span>
                    <a href={src.url} target="_blank" rel="noreferrer">{decodeURIComponent(src.url.replace(/^https?:\/\/(www\.)?/, ''))}</a>
                    {src.quote && <> <q>{src.quote}</q></>}
                  </span>
                )}
                {src.kind === 'search' && <span><q>{src.query}</q>{src.engine && <span className="sids-evidence-dim"> on {src.engine}</span>}</span>}
                {src.note && <span className="sids-evidence-dim sids-evidence-note">{src.note}</span>}
              </li>
            ))}
          </ul>
          {claim && <p className="dataset-note">{claim.description}</p>}
        </div>
      </div>
    </div>
  )
}

// A "?" beside a fact that opens its evidence; nothing when the record has none.
function EvidenceButton({ fact, evidence }) {
  const [open, setOpen] = useState(false)
  const entry = evidence?.[fact]
  if (!entry) return null
  return (
    <>
      <button type="button" className="sids-evidence-btn" title="Why we rate this fact stored or derived"
        onClick={(ev) => { ev.stopPropagation(); setOpen(true) }}>?</button>
      {open && <EvidenceModal fact={fact} entry={entry} onClose={() => setOpen(false)} />}
    </>
  )
}

const DETERMINACY_LABEL = Object.fromEntries(DETERMINACY.map((d) => [d.key, d.label]))
const LOGIC_LABEL = Object.fromEntries([...LOGIC, ...THEORY].map((l) => [l.key, l.label]))

function RecordCard({ rec, relations, onChain, audit, models }) {
  const [open, setOpen] = useState(false)
  const e = rec.edit || {}
  const chains = hasChain(rec)
  // Relation tag group: name and semantics from the record, properties from
  // RELATIONS.md (sent by the backend with the records).
  const properties = relationProperties(relations, rec.relation)
  const edited = e.original || e.statement
  const details = [
    // The header reads the original fact; the full edited sentence is here.
    ['Edit', e.old_object == null ? null : e.statement],
    ['Axiom', e.axiom && <code>{e.axiom}</code>],
    ['Scope', e.scope],
    ['Premises', e.premises?.length > 0 && (
      <>
        <ul className="sids-fact-list">
          {e.premises.map((p) => <li key={p}>{p} <EvidenceButton fact={p} evidence={rec.evidence} /></li>)}
        </ul>
        {chains && (
          <button type="button" className="btn-plain-small sids-chain-btn" onClick={() => onChain(rec, { kind: 'premises' })}>
            Show derivation
          </button>
        )}
      </>
    )],
    ['Worlds', rec.worlds?.length > 0 && (
      <ul className="sids-world-list">
        {rec.worlds.map((w) => (
          <li key={w.id}>
            <span className="sids-world-id">{worldLabel(w.id)}</span> {w.summary}
            <span className="sids-world-assumes">Assumes: {w.assumes.join(' ')}</span>
          </li>
        ))}
      </ul>
    )],
  ].filter(([, v]) => v)
  return (
    <div className={`sids-record${open ? ' open' : ''}`}>
      <button type="button" className="sids-record-head" aria-expanded={open} onClick={() => setOpen((o) => !o)}>
        <span className="sids-record-caret">{open ? '▾' : '▸'}</span>
        <span className="sids-record-badge" title={rec.id}>{recordLabel(rec.id)}</span>
        {/* The original fact; the Change chip shows what the edit makes of it. Insert has no original. */}
        <span className="sids-record-statement">{e.original || e.statement}</span>
        {/* Fact status: direct and paraphrase (RBox: direct and the instance questions) held before the edit. */}
        <AuditDots statuses={audit?.fact} models={models} />
      </button>
      <div className="sids-record-meta">
        {/* Tag order: change, relation, derivability. Determinacy is shown on each derived query. */}
        {e.old_object != null ? (
          <Chip kind="change" label="Change">
            <span className="sids-old">{show(e.old_object)}</span> → <span className="sids-new">{show(e.object)}</span>
          </Chip>
        ) : e.original ? (
          // TBox and RBox edits change a rule, not one object: original rule -> edited rule.
          <Chip kind="change" label="Change">
            <span className="sids-old">{e.original}</span> → <span className="sids-new">{e.statement}</span>
          </Chip>
        ) : null}
        <Chip kind="relation" label="Relation">
          <span className="sids-chip-part"><code>{rec.relation}</code></span>
          {rec.relation_semantics && (
            <span className="sids-chip-part">
              <span className="sids-chip-part-key">Semantics</span> {labelOf(RELATION_SEMANTICS, rec.relation_semantics)}
            </span>
          )}
          <span className="sids-chip-part">
            <span className="sids-chip-part-key">Properties</span>{' '}
            {properties.length
              ? properties.map((tag, i) => (
                <span key={tag} title={relationPropertyOf(tag)?.label}>{i ? ', ' : ''}<code>{tag}</code></span>
              ))
              : 'none'}
          </span>
        </Chip>
        {rec.derivability != null && (
          <Chip kind="derivability" label="Derivability">
            {labelOf(DERIVABILITY, rec.derivability)} <EvidenceButton fact={edited} evidence={rec.evidence} />
          </Chip>
        )}
        {e.fixture && <Chip kind="fixture">Fixture</Chip>}
        {rec.fictional ? (
          <Chip kind="reality" label="Made up">
            <span title={FICTIONAL.find((f) => f.key === rec.fictional)?.description}>{labelOf(FICTIONAL, rec.fictional)}</span>
          </Chip>
        ) : rec.reality && <Chip kind="reality" label="Reality">{rec.reality === 'fictional' ? 'Fictional' : 'Real'}</Chip>}
      </div>
      {open && (
        <div className="sids-record-body">
          {details.length > 0 && (
            <dl className="sids-record-details">
              {details.map(([k, v]) => (
                <div key={k}><dt>{k}</dt><dd>{v}</dd></div>
              ))}
            </dl>
          )}
          <div className="table-wrap">
            <table className="sids-query-table">
              <thead><tr><th>Query</th><th>Prompt</th><th>Answer (original → new)</th><th>Derivation</th></tr></thead>
              <tbody>
                {queryRows(rec).map((r, i) => (
                  <tr key={i}>
                    <td>
                      <span className={`sids-query-type sids-metric-${METRIC_OF[r.key]}`}>
                        {QUERY_LABEL[r.key]}{r.language ? ` (${r.language})` : ''}
                      </span>
                      <AuditDots statuses={audit?.queries?.[r.auditKey]} models={models} />
                    </td>
                    <td>{r.prompt}</td>
                    <td className="sids-answer">
                      {r.key.startsWith('unrelated') ? (
                        <><em>model's own pre-edit answer</em>{r.reference && <span className="sids-answer-ref">ref: {r.reference}</span>}</>
                      ) : r.world_answers ? (
                        <>
                          <span className="sids-old">{show(r.original_answer)}</span> →
                          <span className="sids-world-answers">
                            {(rec.worlds || []).map((w) => (
                              <span key={w.id} title={w.summary}>
                                <span className="sids-world-id">{worldLabel(w.id)}</span> <span className="sids-new">{r.world_answers[w.id]?.answer ?? (rec.edit_operation === 'delete' ? 'does not know' : '—')}</span>
                              </span>
                            ))}
                          </span>
                        </>
                      ) : (
                        <><span className="sids-old">{show(r.original_answer)}</span> → <span className="sids-new">{show(r.new_answer)}</span></>
                      )}
                    </td>
                    <td className="sids-derivation">
                      {(r.determinacy || r.logic) && (
                        <span className="sids-tags">
                          {r.determinacy && (
                            <span className={`sids-det is-${INDETERMINATE.includes(r.determinacy) ? 'open' : 'closed'}`} title={r.determinacy_why || ''}>
                              {DETERMINACY_LABEL[r.determinacy] || r.determinacy}
                            </span>
                          )}
                          {r.premise_route && <span className="sids-det-flag" title="Reaches the edited fact along its premises: only an inconsistent model gives the old answer">premise route</span>}
                          {r.logic && <span className="sids-det-flag" title="The weakest logic the inference needs">{LOGIC_LABEL[r.logic] || r.logic}</span>}
                          {r.theory && <span className="sids-det-flag" title="A theory the inference uses on top of first-order logic">{LOGIC_LABEL[r.theory] || r.theory}</span>}
                        </span>
                      )}
                      {r.derivation ? `${r.derivation}${r.hops ? `, ${r.hops} hop${r.hops === 1 ? '' : 's'}` : ''}` : ''}
                      {r.bridge?.length > 0 && (
                        <span className="sids-bridge">
                          bridge: {r.bridge.map((b) => <span key={b}>{b} <EvidenceButton fact={b} evidence={rec.evidence} /></span>)}
                        </span>
                      )}
                      {r.key === 'derived' && chains && (
                        <button type="button" className="btn-plain-small sids-chain-btn" onClick={() => onChain(rec, { kind: 'query', query: r })}>
                          Chain
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {rec.notes && <p className="sids-record-notes">{rec.notes}</p>}
          {models?.length > 0 && (
            <p className="sids-audit-link">
              Responses: <Link to={`/model-audit?record=${encodeURIComponent(rec.id)}`}>Model audit page</Link>
            </p>
          )}
        </div>
      )}
    </div>
  )
}

// Queries a record carries (10 for ABox/TBox, 7 for RBox), counted rather
// than assumed so a malformed record shows up in the total.
function queryCount(rec) {
  return Object.values(rec.queries || {}).reduce((n, q) => n + (Array.isArray(q) ? q.length : q ? 1 : 0), 0)
}

// The whole-dataset block other benchmarks show, built from the records:
// totals, then records per edit operation (insert split by what is fictional).
function sidsBreakdown(records) {
  const categories = EDIT_OPERATIONS.map(({ key, label }) => {
    const rs = records.filter((r) => r.edit_operation === key)
    const parts = FICTIONAL.map((f) => [f, rs.filter((r) => r.fictional === f.key).length]).filter(([, n]) => n)
    return {
      name: label,
      records: rs.length,
      note: parts.length ? `made up: ${parts.map(([f, n]) => `${f.label.toLowerCase()} ${n}`).join(', ')}` : '',
    }
  })
  return {
    records: records.length,
    unit: `records across ${EDIT_OPERATIONS.length} edit operations`,
    extra: [{ value: records.reduce((n, r) => n + queryCount(r), 0), label: 'queries' }],
    categories,
  }
}

export default function SidsDatasetBrowser() {
  const [records, setRecords] = useState(null)
  const [relations, setRelations] = useState({})
  const [relationChecks, setRelationChecks] = useState({})
  const [audit, setAudit] = useState(null)
  // Pre-edit status dots: the four main instruct models, or every audited model.
  const [status, setStatus] = useState(null)
  const [allModels, setAllModels] = useState(false)
  const [chain, setChain] = useState(null)
  const [showCriteria, setShowCriteria] = useState(false)
  const [error, setError] = useState(null)
  const [coordinate, setCoordinate] = useState({
    edit_operation: EDIT_OPERATIONS[0].key,
    topic: TOPICS[0].key,
    box: BOXES[0].key,
  })
  useEffect(() => {
    api.sidsDatasetRecords().then((d) => {
      setRecords(d.records)
      setRelations(d.relations || {})
      setRelationChecks(d.relation_checks || {})
      // Open on records, not on an empty default: the first record's coordinate.
      const first = d.records[0]
      if (first) {
        setCoordinate({ edit_operation: first.edit_operation, topic: first.topic, box: first.box })
      }
    }).catch((err) => setError(String(err.message || err)))
  }, [])
  useEffect(() => {
    api.sidsDatasetAuditStatus(allModels ? 'all' : 'main').then(setStatus).catch(() => setStatus(null))
  }, [allModels])
  const statusModels = status?.models || []
  const otherModels = (status?.all_models || statusModels).filter((m) => !(status?.main_models || []).includes(m))
  const set = (layer) => (value) => setCoordinate((c) => ({ ...c, [layer]: value }))
  // Audit results load once, the first time a chain is opened.
  const openChain = (rec, target) => {
    setChain({ rec, target })
    if (audit == null) api.sidsDatasetAuditChecks().then((d) => setAudit(d.models)).catch(() => setAudit([]))
  }

  // Records per tab value, given the layers above that row.
  const counts = (layer) => {
    if (!records) return null
    const out = {}
    for (const r of records) if (matches(r, coordinate, layer)) out[r[layer]] = (out[r[layer]] || 0) + 1
    return out
  }
  const shown = (records || []).filter((r) => matches(r, coordinate))

  return (
    <div className="sids-browser">
      {records && <DatasetSummary benchmark="SidsDataset" breakdown={sidsBreakdown(records)} />}
      <div className="sids-criteria-bar">
        <button type="button" className="btn-plain-small" onClick={() => setShowCriteria(true)}
          title="Which CRITERIA.md checks the records pass (datasets/SidsDataset/criteria.py)">
          Criteria checklist
        </button>
      </div>
      {showCriteria && <SidsCriteriaModal onClose={() => setShowCriteria(false)} />}
      {status && (
        <div className="sids-audit-legend">
          <span>Pre-edit model audit, one dot per model ({statusModels.map(modelLabel).join(', ') || 'none audited yet'}):</span>
          <span><span className="sids-audit-dot is-green" />gave the expected answer</span>
          <span><span className="sids-audit-dot is-red" />did not</span>
          <span><span className="sids-audit-dot is-yellow" />not audited, stale or unclear</span>
          <span><span className="sids-audit-dot is-na" />not asked</span>
          {(otherModels.length > 0 || allModels) && (
            <label title={otherModels.map(modelLabel).join(', ')}>
              <input type="checkbox" checked={allModels} onChange={(ev) => setAllModels(ev.target.checked)} />
              other audited models (base and others)
            </label>
          )}
          <span>responses: <Link to="/model-audit">Model audit page</Link></span>
        </div>
      )}
      <p className="sids-group-label">Edit operation <span>{records ? `${records.length} records in all` : ''}</span></p>
      <TabRow label="Edit operation" values={EDIT_OPERATIONS} selected={coordinate.edit_operation} onSelect={set('edit_operation')} counts={counts('edit_operation')} />

      <p className="sids-group-label">Knowledge form</p>
      <TabRow label="Topic" values={TOPICS} selected={coordinate.topic} onSelect={set('topic')} counts={counts('topic')} />

      <p className="sids-group-label">DL box</p>
      <TabRow label="DL box" values={BOXES} selected={coordinate.box} onSelect={set('box')} counts={counts('box')} />

      <div className="sids-coordinate">
        <span className="sids-coordinate-label">Coordinate</span>
        <code>{coordinateSummary(coordinate)}</code>
      </div>

      {error && <p className="archive-line archive-line-warn">{error}</p>}
      {!records && !error && <p className="empty">Loading records…</p>}
      {records && !shown.length && (
        <p className="empty">
          No records at this coordinate yet. Use the <strong>?</strong> beside the dataset name for the full scheme, the
          derivation types and how each query is scored.
        </p>
      )}
      {shown.length > 0 && (
        <>
          <p className="sids-group-label">Records <span>{shown.length}</span></p>
          {shown.map((rec) => (
            <RecordCard key={rec.id} rec={rec} relations={relations} onChain={openChain}
              audit={status?.records?.[rec.id]} models={statusModels} />
          ))}
        </>
      )}
      {chain && (
        <DerivationModal rec={chain.rec} target={chain.target} relations={relations} relationChecks={relationChecks}
          audit={audit} onClose={() => setChain(null)} />
      )}
    </div>
  )
}
