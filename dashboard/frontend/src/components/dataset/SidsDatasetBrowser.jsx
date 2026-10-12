import { useEffect, useState } from 'react'
import { api } from '../../api.js'
import {
  BOXES,
  DERIVABILITY,
  EDIT_OPERATIONS,
  FAMILIARITY,
  FAMILIARITY_TIERS,
  QUERY_TYPES,
  RELATION_SEMANTICS,
  TEMPORAL,
  TOPICS,
  coordinateSummary,
} from '../../lib/sidsDatasetTaxonomy.js'
import DerivationModal, { hasChain } from './DerivationModal.jsx'

// Browses the records under the categorization: edit operation, then the
// knowledge form layers (topic, box, and relation semantics where the box has
// it). Each tab shows how many records it holds given the layers above it, and
// the records at the selected coordinate are listed below with every query.
// Explanations of each layer live in SidsDatasetInfoModal (the "?"), not here.
const LAYERS = ['edit_operation', 'topic', 'box', 'relation_semantics']

function matches(rec, coordinate, upTo) {
  for (const layer of LAYERS.slice(0, LAYERS.indexOf(upTo))) {
    if (layer === 'relation_semantics' && rec.relation_semantics == null) continue
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

const QUERY_LABEL = { direct: 'Direct', paraphrase: 'Paraphrase', cross_lingual: 'Cross-lingual', derived: 'Derived',
  unrelated_near: 'Unrelated (near)', unrelated_far: 'Unrelated (far)' }
const show = (v) => (v == null ? '—' : String(v))

function queryRows(rec) {
  const q = rec.queries || {}
  const rows = []
  for (const key of Object.keys(QUERY_LABEL)) {
    const items = Array.isArray(q[key]) ? q[key] : q[key] ? [q[key]] : []
    for (const item of items) rows.push({ key, ...item })
  }
  return rows
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
// by kind (relation, derivability, familiarity, ...).
function Chip({ kind, label, children }) {
  return (
    <span className={`sids-chip sids-chip-${kind}`}>
      {label && <span className="sids-chip-label">{label}</span>}
      <span className="sids-chip-value">{children}</span>
    </span>
  )
}

function RecordCard({ rec, onChain }) {
  const [open, setOpen] = useState(false)
  const e = rec.edit || {}
  const chains = hasChain(rec)
  const familiarity = FAMILIARITY_TIERS.filter((t) => rec.familiarity?.[t.key] != null)
  const details = [
    ['Original', e.old_object == null ? null : e.original],
    ['Axiom', e.axiom && <code>{e.axiom}</code>],
    ['Scope', e.scope],
    ['Premises', e.premises?.length > 0 && (
      <>
        {e.premises.join(' ')}
        {chains && (
          <button type="button" className="btn-plain-small sids-chain-btn" onClick={() => onChain(rec, { kind: 'premises' })}>
            Show derivation
          </button>
        )}
      </>
    )],
  ].filter(([, v]) => v)
  return (
    <div className={`sids-record${open ? ' open' : ''}`}>
      <button type="button" className="sids-record-head" aria-expanded={open} onClick={() => setOpen((o) => !o)}>
        <span className="sids-record-caret">{open ? '▾' : '▸'}</span>
        <span className="sids-record-badge" title={rec.id}>{recordLabel(rec.id)}</span>
        <span className="sids-record-statement">{e.statement}</span>
      </button>
      <div className="sids-record-meta">
        <Chip kind="relation" label="Relation"><code>{rec.relation}</code></Chip>
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
        {rec.derivability != null && <Chip kind="derivability" label="Derivability">{labelOf(DERIVABILITY, rec.derivability)}</Chip>}
        {familiarity.length > 0 && (
          <Chip kind="familiarity" label="Familiarity">
            {familiarity.map((t) => (
              <span key={t.key} className="sids-chip-part">
                <span className="sids-chip-part-key">{t.label}</span> {labelOf(FAMILIARITY, rec.familiarity[t.key])}
              </span>
            ))}
          </Chip>
        )}
        {rec.temporal && <Chip kind="temporal" label="Temporal">{labelOf(TEMPORAL, rec.temporal)}</Chip>}
        {e.fixture && <Chip kind="fixture">Fixture</Chip>}
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
                    </td>
                    <td>{r.prompt}</td>
                    <td className="sids-answer">
                      {r.key.startsWith('unrelated') ? (
                        <><em>model's own pre-edit answer</em>{r.reference && <span className="sids-answer-ref">ref: {r.reference}</span>}</>
                      ) : (
                        <><span className="sids-old">{show(r.original_answer)}</span> → <span className="sids-new">{show(r.new_answer)}</span></>
                      )}
                    </td>
                    <td className="sids-derivation">
                      {r.derivation ? `${r.derivation}${r.hops ? `, ${r.hops} hop${r.hops === 1 ? '' : 's'}` : ''}${r.bridge?.length ? ` (bridge: ${r.bridge.join(' ')})` : ''}` : ''}
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
        </div>
      )}
    </div>
  )
}

export default function SidsDatasetBrowser() {
  const [records, setRecords] = useState(null)
  const [relations, setRelations] = useState({})
  const [relationChecks, setRelationChecks] = useState({})
  const [audit, setAudit] = useState(null)
  const [chain, setChain] = useState(null)
  const [error, setError] = useState(null)
  const [coordinate, setCoordinate] = useState({
    edit_operation: EDIT_OPERATIONS[0].key,
    topic: TOPICS[0].key,
    box: BOXES[0].key,
    relation_semantics: RELATION_SEMANTICS[0].key,
  })
  useEffect(() => {
    api.sidsDatasetRecords().then((d) => {
      setRecords(d.records)
      setRelations(d.relations || {})
      setRelationChecks(d.relation_checks || {})
      // Open on records, not on an empty default: the first record's coordinate.
      const first = d.records[0]
      if (first) {
        setCoordinate((c) => ({
          edit_operation: first.edit_operation, topic: first.topic, box: first.box,
          relation_semantics: first.relation_semantics ?? c.relation_semantics,
        }))
      }
    }).catch((err) => setError(String(err.message || err)))
  }, [])
  const set = (layer) => (value) => setCoordinate((c) => ({ ...c, [layer]: value }))
  // Audit results load once, the first time a chain is opened.
  const openChain = (rec, target) => {
    setChain({ rec, target })
    if (audit == null) api.sidsDatasetAuditChecks().then((d) => setAudit(d.models)).catch(() => setAudit([]))
  }

  const box = BOXES.find((b) => b.key === coordinate.box)
  // The coordinate a record would carry: layers the box doesn't have are null.
  const recordCoordinate = {
    ...coordinate,
    relation_semantics: box.semantics ? coordinate.relation_semantics : null,
  }
  // Records per tab value, given the layers above that row.
  const counts = (layer) => {
    if (!records) return null
    const out = {}
    for (const r of records) if (matches(r, coordinate, layer)) out[r[layer]] = (out[r[layer]] || 0) + 1
    return out
  }
  const shown = (records || []).filter((r) =>
    matches(r, coordinate, 'relation_semantics') && (!box.semantics || r.relation_semantics === coordinate.relation_semantics))

  return (
    <div className="sids-browser">
      <p className="sids-group-label">Edit operation <span>{records ? `${records.length} records in all` : ''}</span></p>
      <TabRow label="Edit operation" values={EDIT_OPERATIONS} selected={coordinate.edit_operation} onSelect={set('edit_operation')} counts={counts('edit_operation')} />

      <p className="sids-group-label">Knowledge form</p>
      <TabRow label="Topic" values={TOPICS} selected={coordinate.topic} onSelect={set('topic')} counts={counts('topic')} />

      <p className="sids-group-label">DL box</p>
      <TabRow label="DL box" values={BOXES} selected={coordinate.box} onSelect={set('box')} counts={counts('box')} />

      {box.semantics && (
        <>
          <p className="sids-group-label">Relation semantics</p>
          <TabRow label="Relation semantics" values={RELATION_SEMANTICS} selected={coordinate.relation_semantics} onSelect={set('relation_semantics')} counts={counts('relation_semantics')} />
        </>
      )}

      <div className="sids-coordinate">
        <span className="sids-coordinate-label">Coordinate</span>
        <code>{coordinateSummary(recordCoordinate)}</code>
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
          {shown.map((rec) => <RecordCard key={rec.id} rec={rec} onChain={openChain} />)}
        </>
      )}
      {chain && (
        <DerivationModal rec={chain.rec} target={chain.target} relations={relations} relationChecks={relationChecks}
          audit={audit} onClose={() => setChain(null)} />
      )}
    </div>
  )
}
