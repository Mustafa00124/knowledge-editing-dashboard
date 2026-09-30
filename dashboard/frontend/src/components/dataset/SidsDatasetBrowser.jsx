import { useState } from 'react'
import {
  COHERENCE_PROPERTIES,
  CONNECTIVITY,
  DEPENDENCY,
  DOMAINS,
  EDIT_NATURES,
  EDIT_REPRESENTATIONS,
  GROUNDING_LADDER,
  KNOWLEDGE_FORMS,
  PROBE_ROLES,
  REPRESENTATION_GROUPS,
  STRUCTURE_EXAMPLES,
  coordinateSummary,
} from '../../lib/sidsDatasetTaxonomy.js'

// No records exist yet (see datasets/SidsDataset/README.md), so this browses
// the categorization itself. It is not a path builder: the scheme is several
// independent axes rather than one hierarchy, so picking values here composes
// a coordinate, not a directory. Swap this for the generic subsets-based UI in
// Datasets.jsx once real records are registered in datasetCatalog.js.
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
    domain: DOMAINS[0].key,
    knowledge_form: KNOWLEDGE_FORMS[0].key,
    edit_nature: EDIT_NATURES[0].key,
    edit_representation: EDIT_REPRESENTATIONS[0].key,
    connectivity: 'medium',
    dependency: 'medium',
  })
  const set = (axis) => (value) => setCoordinate((c) => ({ ...c, [axis]: value }))

  const form = KNOWLEDGE_FORMS.find((f) => f.key === coordinate.knowledge_form)
  const nature = EDIT_NATURES.find((n) => n.key === coordinate.edit_nature)
  const representation = EDIT_REPRESENTATIONS.find((e) => e.key === coordinate.edit_representation)
  const combo = STRUCTURE_EXAMPLES.find(
    (s) => s.connectivity === coordinate.connectivity && s.dependency === coordinate.dependency,
  )

  return (
    <div className="sids-browser">
      <TabRow label="Domain" values={DOMAINS} selected={coordinate.domain} onSelect={set('domain')} />

      <TabRow label="Knowledge form" values={KNOWLEDGE_FORMS} selected={coordinate.knowledge_form} onSelect={set('knowledge_form')} />
      {form && (
        <p className="dataset-note">
          {form.description}
          {form.examples && <em> {form.examples.join(' · ')}</em>}
        </p>
      )}

      <TabRow label="Edit nature" values={EDIT_NATURES} selected={coordinate.edit_nature} onSelect={set('edit_nature')} />
      {nature && <p className="dataset-note">{nature.description}</p>}

      {/* Split into two rows rather than one long one: coherent phrasing and
          degraded coherence are doing different jobs, and fourteen tabs in a
          single row reads as one undifferentiated list. */}
      {REPRESENTATION_GROUPS.map((group) => (
        <div key={group.key}>
          <p className="sids-group-label">{group.label} <span>{group.note}</span></p>
          <TabRow
            label={group.label}
            values={EDIT_REPRESENTATIONS.filter((e) => e.group === group.key)}
            selected={coordinate.edit_representation}
            onSelect={set('edit_representation')}
          />
        </div>
      ))}
      {representation && (
        <p className="dataset-note">
          {representation.degrades && (
            <span className="sids-degrades">
              {representation.degrades
                .map((d) => COHERENCE_PROPERTIES.find((c) => c.key === d)?.label || d)
                .join(' + ')}
            </span>
          )}
          {representation.description} <em>"{representation.example}"</em>
        </p>
      )}

      {/* Connectivity and dependency vary together, and which cell an item
          sits in decides what it actually tests, so they get one grid rather
          than two independent tab rows. */}
      <div className="sids-matrix" role="group" aria-label="Connectivity and dependency">
        <div className="sids-matrix-corner">
          <span>{CONNECTIVITY.label} ↓</span>
          <span>{DEPENDENCY.label} →</span>
        </div>
        {DEPENDENCY.levels.map((d) => (
          <div className="sids-matrix-head" key={`head-${d.key}`}>{d.label}</div>
        ))}
        {CONNECTIVITY.levels.map((c) => (
          <Row key={c.key} c={c} coordinate={coordinate} setCoordinate={setCoordinate} />
        ))}
      </div>
      <p className="dataset-note">
        {combo ? <><strong>{combo.label}.</strong> {combo.detail}</> : 'An intermediate combination with no headline role. Valid, just not one of the diagnostic corners.'}
      </p>

      {/* The one place the representation axis is meant to be walked in order
          rather than picked from, so it gets its own strip. Clicking a rung
          selects that representation. */}
      <div className="sids-ladder">
        <p className="sids-group-label">Grounding ladder <span>{GROUNDING_LADDER.frame}</span></p>
        <div className="sids-ladder-rungs">
          {GROUNDING_LADDER.rungs.map((rung, i) => (
            <button
              key={rung.value}
              type="button"
              aria-pressed={coordinate.edit_representation === rung.representation}
              className={`sids-rung${coordinate.edit_representation === rung.representation ? ' active' : ''}`}
              title={rung.description}
              onClick={() => set('edit_representation')(rung.representation)}
            >
              <span className="sids-rung-step">{i + 1}</span>
              <strong>{rung.value}</strong>
              <small>{rung.description}</small>
            </button>
          ))}
        </div>
      </div>

      <div className="sids-coordinate">
        <span className="sids-coordinate-label">Coordinate</span>
        <code>{coordinateSummary(coordinate)}</code>
      </div>

      <p className="empty">
        No records yet. An item at this coordinate would carry{' '}
        {PROBE_ROLES.map((r) => r.label.toLowerCase()).join(', ')} probes. Use the <strong>?</strong> beside the dataset
        name for the full scheme, rubrics and evaluation design.
      </p>
    </div>
  )
}

function Row({ c, coordinate, setCoordinate }) {
  return (
    <>
      <div className="sids-matrix-head">{c.label}</div>
      {DEPENDENCY.levels.map((d) => {
        const active = coordinate.connectivity === c.key && coordinate.dependency === d.key
        const named = STRUCTURE_EXAMPLES.find((s) => s.connectivity === c.key && s.dependency === d.key)
        return (
          <button
            key={d.key}
            type="button"
            aria-pressed={active}
            title={named ? `${named.label}: ${named.detail}` : `Connectivity ${c.label}, dependency ${d.label}`}
            className={`sids-matrix-cell${active ? ' active' : ''}${named ? ' named' : ''}`}
            onClick={() => setCoordinate((prev) => ({ ...prev, connectivity: c.key, dependency: d.key }))}
          >
            {named ? named.label : '·'}
          </button>
        )
      })}
    </>
  )
}
