import { useEffect } from 'react'
import {
  BOXES,
  DERIVATIONS,
  EDITS_PER_CELL_GOAL,
  EDIT_OPERATIONS,
  FAMILIARITY,
  FAMILIARITY_CAVEAT,
  FAMILIARITY_TIERS,
  KNOWLEDGE_FORMS,
  METRICS,
  PARKED,
  QUERY_BEHAVIORS,
  QUERY_TYPES,
  RELATION_SEMANTICS,
  TEMPORAL,
  DERIVABILITY,
  DERIVABILITY_CAVEAT,
  TOPICS,
} from '../../lib/sidsDatasetTaxonomy.js'

// Reference panel for the categorization scheme, opened from the "?" beside
// the dataset's name. Everything here is sourced from
// sidsDatasetTaxonomy.js, so the panel cannot drift from what the browser
// renders.
function ValueList({ values }) {
  return (
    <dl className="sids-axis-values">
      {values.map((value) => (
        <div key={value.key}>
          <dt>{value.label}</dt>
          <dd>
            {value.bridge && <span className="sids-degrades">bridge</span>}
            {value.notation && <><code>{value.notation}</code> </>}
            {value.description}
            {value.examples && <em> {value.examples.join(' · ')}</em>}
            {value.example && <em> {value.example}</em>}
          </dd>
        </div>
      ))}
    </dl>
  )
}

const CELLS = TOPICS.length * EDIT_OPERATIONS.length * KNOWLEDGE_FORMS.length
const EDITS = CELLS * EDITS_PER_CELL_GOAL
const QUERIES_PER_EDIT = QUERY_TYPES.reduce((n, q) => n + q.count, 0)

export default function SidsDatasetInfoModal({ onClose }) {
  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal sids-info-modal"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label="About Sid's Dataset"
      >
        <div className="modal-header">
          <div className="modal-title-group">
            <h2>Sid's Dataset</h2>
            <span className="sids-info-tag">categorization reference</span>
          </div>
          <button type="button" className="btn-plain" onClick={onClose} aria-label="Close">✕</button>
        </div>

        <div className="modal-body sids-info-body">
          <section>
            <h3>Overview</h3>
            <p>
              Published editing benchmarks test a narrow notion of knowledge, mostly simple factual triples, and measure
              generalization with paraphrases. This one spans facts, rules and properties of relations, causal and
              associative, and measures generalization with questions that <strong>logically follow</strong> from the
              edit.
            </p>
            <p className="dataset-note">
              Three levels: edit operation, then knowledge form, then a fixed set of 12 queries per edit. Relations and
              their properties are catalogued in <code>datasets/SidsDataset/RELATIONS.md</code>.
            </p>
          </section>

          <section>
            <h3>1. Edit operation</h3>
            <ValueList values={EDIT_OPERATIONS} />
          </section>

          <section>
            <h3>2. Knowledge form</h3>
            <div className="sids-axis">
              <h4>Topic <span className="sids-rubric-q">a diversity control, and how records are organized</span></h4>
              <p className="dataset-note">{TOPICS.map((t) => t.label).join(' · ')}</p>
            </div>
            <div className="sids-axis">
              <h4>DL box <span className="sids-rubric-q">how description logic divides a knowledge base</span></h4>
              <ValueList values={BOXES} />
            </div>
            <div className="sids-axis">
              <h4>Relation semantics <span className="sids-rubric-q">ABox and TBox only</span></h4>
              <ValueList values={RELATION_SEMANTICS} />
            </div>
            <p className="dataset-note">
              {KNOWLEDGE_FORMS.length} forms per topic, so {EDIT_OPERATIONS.length} operations × {TOPICS.length} topics
              × {KNOWLEDGE_FORMS.length} forms = {EDIT_OPERATIONS.length * TOPICS.length * KNOWLEDGE_FORMS.length} cells.
            </p>
          </section>

          <section>
            <h3>3. Queries</h3>
            <dl className="sids-axis-values">
              {QUERY_TYPES.map((q) => (
                <div key={q.key}>
                  <dt>{q.count} × {q.label}</dt>
                  <dd><span className="sids-degrades">{q.metric}</span>{q.description}</dd>
                </div>
              ))}
            </dl>
            <div className="sids-axis">
              <h4>Derived queries <span className="sids-rubric-q">which ones an item gets depends on its relation's properties</span></h4>
              <ValueList values={DERIVATIONS} />
              <p className="dataset-note">
                Derivations marked with a bridge combine the edit with another fact. The model must answer every bridge
                fact correctly before editing, or the item is dropped for that model. Reflexivity is never used, since
                "a R a" doesn't depend on the edit.
              </p>
            </div>
          </section>

          <section>
            <h3>Evaluation</h3>
            <p>Our own evaluation functions, scored from generated answers:</p>
            <dl className="sids-axis-values">
              {METRICS.map((m) => (
                <div key={m.key}>
                  <dt>{m.label}</dt>
                  <dd>over {m.over}; {m.reported}.</dd>
                </div>
              ))}
            </dl>
            <ValueList values={QUERY_BEHAVIORS} />
          </section>

          <section>
            <h3>Tags</h3>
            <p>
              Not layers of the taxonomy: tags that describe each record further, so results can be sliced by them
              within any cell.
            </p>
            <h4>Familiarity</h4>
            <p>How familiar the knowledge involved is likely to be, rated in three tiers:</p>
            <ValueList values={FAMILIARITY_TIERS} />
            <p>Each tier takes one of five values, scored 1 to 5 for correlations:</p>
            <ValueList values={FAMILIARITY} />
            <p className="dataset-note">{FAMILIARITY_CAVEAT}</p>
            <h4>Derivability <span className="sids-rubric-q">ABox and TBox replace and delete</span></h4>
            <p>
              How likely a model is to derive the edited fact from other knowledge rather than store it. The scale runs
              from <strong>axiomatic (stored)</strong>, held directly as a base claim, to{' '}
              <strong>derived (composed)</strong>, composed from other knowledge the model holds. Scored 1 to 5:
            </p>
            <ValueList values={DERIVABILITY} />
            <p className="dataset-note">{DERIVABILITY_CAVEAT}</p>
            <h4>Temporal <span className="sids-rubric-q">ABox facts only</span></h4>
            <ValueList values={TEMPORAL} />
          </section>

          <section>
            <h3>Parked from the previous version</h3>
            <ul className="sids-questions">
              {PARKED.map((p) => <li key={p}>{p}</li>)}
            </ul>
          </section>

          <section>
            <h3>Size goal</h3>
            <p>
              Around {CELLS} taxonomy cells: {TOPICS.length} topics × {EDIT_OPERATIONS.length} operations ×{' '}
              {KNOWLEDGE_FORMS.length} knowledge forms ({BOXES.length} DL boxes, with the {RELATION_SEMANTICS.length}{' '}
              relation semantics under ABox and TBox only). The goal is {EDITS_PER_CELL_GOAL} edits per cell, so{' '}
              {EDITS} edits, and {QUERIES_PER_EDIT} queries per edit, so a goal of{' '}
              <strong>{(EDITS * QUERIES_PER_EDIT).toLocaleString()} queries</strong>.
            </p>
          </section>
        </div>
      </div>
    </div>
  )
}
