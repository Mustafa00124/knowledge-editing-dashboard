import { useEffect, useState } from 'react'
import { api } from '../../api.js'
import {
  BOXES,
  EDIT_OPERATIONS,
  QUERY_TYPES,
  RELATION_SEMANTICS,
  TOPICS,
  coordinateSummary,
} from '../../lib/sidsDatasetTaxonomy.js'

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

function RecordCard({ rec }) {
  const [open, setOpen] = useState(false)
  const e = rec.edit || {}
  return (
    <div className="sids-record">
      <button type="button" className="sids-record-head" onClick={() => setOpen((o) => !o)}>
        <span>{open ? '▾' : '▸'} <code>{rec.id}</code></span>
        <span className="sids-record-statement">{e.statement}</span>
      </button>
      <div className="sids-record-meta">
        <span>relation <code>{rec.relation}</code></span>
        {e.old_object != null && <span>{show(e.old_object)} → {show(e.object)}</span>}
        <span>derivability {rec.derivability}</span>
        {rec.familiarity && <span>familiarity {Object.entries(rec.familiarity).map(([k, v]) => `${k} ${v}`).join(', ')}</span>}
        {rec.temporal && <span>{rec.temporal}</span>}
        {e.fixture && <span className="sids-record-flag">fixture</span>}
      </div>
      {open && (
        <div className="sids-record-body">
          {e.original && <p><strong>Original:</strong> {e.original}</p>}
          {e.axiom && <p><strong>Axiom:</strong> <code>{e.axiom}</code></p>}
          {e.scope && <p><strong>Scope:</strong> {e.scope}</p>}
          {e.premises?.length > 0 && <p><strong>Premises:</strong> {e.premises.join(' ')}</p>}
          <div className="table-wrap">
            <table>
              <thead><tr><th>Query</th><th>Prompt</th><th>Original answer</th><th>New answer</th><th>Derivation</th></tr></thead>
              <tbody>
                {queryRows(rec).map((r, i) => (
                  <tr key={i}>
                    <td>{QUERY_LABEL[r.key]}{r.language ? ` (${r.language})` : ''}</td>
                    <td>{r.prompt}</td>
                    <td>{r.key.startsWith('unrelated') ? <em>model's own pre-edit answer</em> : show(r.original_answer)}</td>
                    <td>{r.key.startsWith('unrelated') ? (r.reference ? `ref: ${r.reference}` : '—') : show(r.new_answer)}</td>
                    <td>{r.derivation ? `${r.derivation}${r.hops ? `, ${r.hops} hops` : ''}${r.bridge?.length ? ` (bridge: ${r.bridge.join(' ')})` : ''}` : ''}</td>
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

      <p className="sids-group-label">Queries <span>{QUERY_TYPES.reduce((n, q) => n + q.count, 0)} per edit</span></p>
      <div className="sids-combos">
        {QUERY_TYPES.map((q) => (
          <div className="sids-combo" key={q.key}>
            <strong>{q.count} × {q.label}</strong>
            <span>{q.metric}</span>
          </div>
        ))}
      </div>

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
          {shown.map((rec) => <RecordCard key={rec.id} rec={rec} />)}
        </>
      )}
    </div>
  )
}
