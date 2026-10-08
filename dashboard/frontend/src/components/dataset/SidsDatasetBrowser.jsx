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
// then the fixed query set every edit carries. Explanations of each layer
// live in SidsDatasetInfoModal (the "?"), not here. Swap this for the generic
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

  const box = BOXES.find((b) => b.key === coordinate.box)
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

      <p className="sids-group-label">Knowledge form</p>
      <TabRow label="Topic" values={TOPICS} selected={coordinate.topic} onSelect={set('topic')} />

      <p className="sids-group-label">DL box</p>
      <TabRow label="DL box" values={BOXES} selected={coordinate.box} onSelect={set('box')} />

      {box.semantics && (
        <>
          <p className="sids-group-label">Relation semantics</p>
          <TabRow label="Relation semantics" values={RELATION_SEMANTICS} selected={coordinate.relation_semantics} onSelect={set('relation_semantics')} />
        </>
      )}

      {box.temporality && (
        <TabRow label="Temporality" values={TEMPORALITY} selected={coordinate.temporality} onSelect={set('temporality')} />
      )}

      <p className="sids-group-label">Queries <span>10 per edit</span></p>
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

      <p className="empty">
        No records yet. Use the <strong>?</strong> beside the dataset name for the full scheme, the derivation types and
        how each query is scored.
      </p>
    </div>
  )
}
