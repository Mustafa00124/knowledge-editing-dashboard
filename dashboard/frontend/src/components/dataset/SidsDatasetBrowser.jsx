import { useState } from 'react'
import {
  BOXES,
  EDIT_OPERATIONS,
  QUERY_TYPES,
  RELATION_SEMANTICS,
  TEMPORALITY,
  TOPICS,
  coordinateSummary,
} from '../../lib/sidsDatasetTaxonomy.js'

// No records exist yet (see datasets/SidsDataset/README.md), so this browses
// the categorization itself: edit operation, then the knowledge form layers
// (topic, box, and relation semantics / temporality where the box has them),
// then the fixed query set every edit carries. Swap this for the generic
// subsets-based UI in Datasets.jsx once real records are registered in
// datasetCatalog.js.
function TabRow({ label, values, selected, onSelect }) {
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
          {v.label}
        </button>
      ))}
    </div>
  )
}

export default function SidsDatasetBrowser() {
  const [coordinate, setCoordinate] = useState({
    edit_operation: EDIT_OPERATIONS[0].key,
    topic: TOPICS[0].key,
    box: BOXES[0].key,
    relation_semantics: RELATION_SEMANTICS[0].key,
    temporality: TEMPORALITY[0].key,
  })
  const set = (layer) => (value) => setCoordinate((c) => ({ ...c, [layer]: value }))

  const operation = EDIT_OPERATIONS.find((o) => o.key === coordinate.edit_operation)
  const box = BOXES.find((b) => b.key === coordinate.box)
  const semantics = RELATION_SEMANTICS.find((s) => s.key === coordinate.relation_semantics)
  const temporality = TEMPORALITY.find((t) => t.key === coordinate.temporality)
  // The coordinate a record would carry: layers the box doesn't have are null.
  const recordCoordinate = {
    ...coordinate,
    relation_semantics: box.semantics ? coordinate.relation_semantics : null,
    temporality: box.temporality ? coordinate.temporality : null,
  }

  return (
    <div className="sids-browser">
      <p className="sids-group-label">Edit operation</p>
      <TabRow label="Edit operation" values={EDIT_OPERATIONS} selected={coordinate.edit_operation} onSelect={set('edit_operation')} />
      <p className="dataset-note">{operation.description}</p>

      <p className="sids-group-label">Knowledge form <span>topic, box, then the layers the box has</span></p>
      <TabRow label="Topic" values={TOPICS} selected={coordinate.topic} onSelect={set('topic')} />

      <TabRow label="Box" values={BOXES} selected={coordinate.box} onSelect={set('box')} />
      <p className="dataset-note">
        <code>{box.notation}</code> {box.description} <em>{box.examples.join(' · ')}</em>
      </p>

      {box.semantics && (
        <>
          <TabRow label="Relation semantics" values={RELATION_SEMANTICS} selected={coordinate.relation_semantics} onSelect={set('relation_semantics')} />
          <p className="dataset-note">{semantics.description}</p>
        </>
      )}

      {box.temporality && (
        <>
          <TabRow label="Temporality" values={TEMPORALITY} selected={coordinate.temporality} onSelect={set('temporality')} />
          <p className="dataset-note">
            {temporality.description} <em>{temporality.examples.join(' · ')}</em>
          </p>
        </>
      )}

      <p className="sids-group-label">Queries <span>10 per edit</span></p>
      <div className="sids-combos">
        {QUERY_TYPES.map((q) => (
          <div className="sids-combo" key={q.key}>
            <strong>{q.count} × {q.label}</strong>
            <span>{q.metric}</span>
            <small>{q.description}</small>
          </div>
        ))}
      </div>
      {coordinate.edit_operation === 'delete' && (
        <p className="dataset-note">
          Under delete, the direct, paraphrase and derived queries expect the model to abstain or negate, and fail if
          it still gives the old answer.
        </p>
      )}

      <div className="sids-coordinate">
        <span className="sids-coordinate-label">Coordinate</span>
        <code>{coordinateSummary(recordCoordinate)}</code>
      </div>

      <p className="empty">
        No records yet. Use the <strong>?</strong> beside the dataset name for the full scheme, the derivation types and
        how each query is scored.
      </p>
    </div>
  )
}
