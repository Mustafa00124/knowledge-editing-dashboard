import { useState } from 'react'
import {
  COHERENCE_PROPERTIES,
  CONNECTIVITY,
  DEPENDENCY,
  EDIT_REPRESENTATIONS,
  EDIT_TYPES,
  FACT_TEMPORALITY,
  GROUNDING_LADDER,
  KNOWLEDGE_FORMS,
  KNOWLEDGE_TIERS,
  PROBE_ROLES,
  REPRESENTATION_GROUPS,
  STRUCTURE_EXAMPLES,
  TOPICS,
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
    topic: TOPICS[0].key,
    edit_type: EDIT_TYPES[0].key,
    knowledge_form: KNOWLEDGE_FORMS[0].key,
    temporality: FACT_TEMPORALITY[1].key,
    edit_representation: EDIT_REPRESENTATIONS[0].key,
    connectivity: 'medium',
    dependency: 'medium',
  })
  const set = (axis) => (value) => setCoordinate((c) => ({ ...c, [axis]: value }))

  const form = KNOWLEDGE_FORMS.find((f) => f.key === coordinate.knowledge_form)
  const tier = KNOWLEDGE_TIERS.find((t) => t.key === form.tier)
  const group = tier.groups.find((g) => g.key === form.group)
  // Picking a branch lands on its first form, so a coordinate always names a
  // concrete form rather than a half-chosen path.
  // Phrasing only exists under plain links for now, so leaving one drops a
  // confusing or distractor-heavy phrasing back to direct.
  const selectForm = (formKey) => setCoordinate((c) => ({
    ...c,
    knowledge_form: formKey,
    edit_representation:
      formKey !== 'plain_link' && EDIT_REPRESENTATIONS.find((e) => e.key === c.edit_representation)?.group === 'coherent'
        ? 'direct'
        : c.edit_representation,
  }))
  const selectGroup = (groupKey) => selectForm(tier.groups.find((g) => g.key === groupKey).forms[0].key)
  const selectTier = (tierKey) => selectForm(KNOWLEDGE_TIERS.find((t) => t.key === tierKey).groups[0].forms[0].key)
  const editType = EDIT_TYPES.find((n) => n.key === coordinate.edit_type)
  const temporality = FACT_TEMPORALITY.find((t) => t.key === coordinate.temporality)
  const representation = EDIT_REPRESENTATIONS.find((e) => e.key === coordinate.edit_representation)
  const combo = STRUCTURE_EXAMPLES.find(
    (s) => s.connectivity === coordinate.connectivity && s.dependency === coordinate.dependency,
  )

  return (
    <div className="sids-browser">
      <TabRow label="Topic" values={TOPICS} selected={coordinate.topic} onSelect={set('topic')} />

      <TabRow label="Edit type" values={EDIT_TYPES} selected={coordinate.edit_type} onSelect={set('edit_type')} />
      {editType && <p className="dataset-note">{editType.description}</p>}

      {/* Knowledge form branches: Facts | Rules first, then (facts only)
          temporality, then the kind of fact or rule, then the form. Each row
          only offers the children of what is selected above it. */}
      <TabRow label="Fact or rule" values={KNOWLEDGE_TIERS} selected={tier.key} onSelect={selectTier} />
      <p className="dataset-note">{tier.description}</p>

      {tier.key === 'fact' && (
        <>
          <TabRow label="Temporality" values={FACT_TEMPORALITY} selected={coordinate.temporality} onSelect={set('temporality')} />
          {temporality && (
            <p className="dataset-note">
              {temporality.description} <em>{temporality.examples.join(' · ')}</em>
            </p>
          )}
        </>
      )}

      <TabRow label={`Kind of ${tier.key}`} values={tier.groups} selected={group.key} onSelect={selectGroup} />
      <p className="dataset-note"><code>{group.notation}</code> {group.description}</p>

      {/* A group with a single form (plain link, relation rule) has nothing
          left to choose, so it gets no row of its own. */}
      {group.forms.length > 1 && (
        <TabRow label={group.label} values={group.forms} selected={coordinate.knowledge_form} onSelect={selectForm} />
      )}
      {form && (
        <p className="dataset-note">
          <strong>{form.label}</strong> <code>{form.notation}</code> {form.description}
          {form.examples && <em> {form.examples.join(' · ')}</em>}
        </p>
      )}

      {/* Phrasing: the level under plain links. Same edit, said directly, in
          a logically equivalent but harder form, or buried in distractors. */}
      {form.key === 'plain_link' && (
        <TabRow
          label="Phrasing"
          values={EDIT_REPRESENTATIONS.filter((e) => e.group === 'coherent')}
          selected={coordinate.edit_representation}
          onSelect={set('edit_representation')}
        />
      )}

      {/* Degraded coherence stays its own row: it is the gibberish stress
          test, not a phrasing of a well-formed fact. */}
      {REPRESENTATION_GROUPS.filter((g) => g.key === 'degraded').map((group) => (
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
