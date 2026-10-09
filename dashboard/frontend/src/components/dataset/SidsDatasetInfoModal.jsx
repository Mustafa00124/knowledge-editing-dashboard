import { useEffect } from 'react'
import {
  BOXES,
  DERIVATIONS,
  EDIT_OPERATIONS,
  KNOWLEDGE_FORMS,
  METRICS,
  PARKED,
  QUERY_BEHAVIORS,
  QUERY_TYPES,
  RELATION_SEMANTICS,
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

// Insert has no derived forms: a fact the model can already derive is not new.
const axiomaticForms = KNOWLEDGE_FORMS.filter((f) => f.derivability !== 'derived').length
const cellsPerTopic = axiomaticForms + (EDIT_OPERATIONS.length - 1) * KNOWLEDGE_FORMS.length

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
            <div className="sids-axis">
              <h4>Derivability <span className="sids-rubric-q">ABox and TBox only; insert is always axiomatic</span></h4>
              <ValueList values={DERIVABILITY} />
              <p className="dataset-note">{DERIVABILITY_CAVEAT}</p>
            </div>
            <p className="dataset-note">
              {KNOWLEDGE_FORMS.length} forms per topic. Insert only has the {axiomaticForms} axiomatic ones, so{' '}
              {cellsPerTopic} cells per topic and {cellsPerTopic * TOPICS.length} in all.
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
            <h3>Parked from the previous version</h3>
            <ul className="sids-questions">
              {PARKED.map((p) => <li key={p}>{p}</li>)}
            </ul>
          </section>
        </div>
      </div>
    </div>
  )
}
