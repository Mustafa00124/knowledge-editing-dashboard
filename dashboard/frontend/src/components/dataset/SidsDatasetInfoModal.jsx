import { useEffect } from 'react'
import {
  BOXES,
  DERIVATIONS,
  TASKS,
  EDITS_PER_CELL_GOAL,
  EDIT_OPERATIONS,
  KNOWLEDGE_FORMS,
  METRICS,
  PARKED,
  QUERY_BEHAVIORS,
  QUERY_TYPES,
  RBOX_QUERY_TYPES,
  RELATION_FACETS,
  RELATION_PROPERTIES,
  RELATION_SEMANTICS,
  DERIVABILITY,
  DERIVABILITY_CAVEAT,
  DETERMINACY,
  DETERMINACY_RULE,
  DETERMINACY_SCENARIOS,
  EVIDENCE_CLAIMS,
  LOGIC,
  THEORY,
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
const RBOX_QUERIES_PER_EDIT = RBOX_QUERY_TYPES.reduce((n, q) => n + q.count, 0)
// RBox is one knowledge form per topic and operation; its edits carry fewer queries.
const RBOX_EDITS = TOPICS.length * EDIT_OPERATIONS.length * EDITS_PER_CELL_GOAL
const QUERY_GOAL = (EDITS - RBOX_EDITS) * QUERIES_PER_EDIT + RBOX_EDITS * RBOX_QUERIES_PER_EDIT

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
              Levels: topic, then belief revision operation, then knowledge form, then a fixed set of queries per record
              type (15 for main-split ABox revision, 10 for RBox; README, Queries per record type). Two splits: the main
              split (test) and a separate 120-record dev split for tuning. Relations and
              their properties are catalogued in <code>datasets/SidsDataset/RELATIONS.md</code>.
            </p>
          </section>

          <section>
            <h3>1. Topic</h3>
            <p className="dataset-note">
              A diversity control, and how records are organized: {TOPICS.map((t) => t.label).join(' · ')}
            </p>
          </section>

          <section>
            <h3>2. Belief revision operation</h3>
            <p className="dataset-note">
              The three AGM operations: expansion adds a belief, revision replaces one while staying consistent, contraction
              removes one. Records store them as insert, replace and delete.
            </p>
            <ValueList values={EDIT_OPERATIONS} />
          </section>

          <section>
            <h3>3. Knowledge form</h3>
            <div className="sids-axis">
              <h4>DL box <span className="sids-rubric-q">how description logic divides a knowledge base</span></h4>
              <ValueList values={BOXES} />
            </div>
            <p className="dataset-note">
              {TOPICS.length} topics × {EDIT_OPERATIONS.length} operations × {KNOWLEDGE_FORMS.length} forms ={' '}
              {EDIT_OPERATIONS.length * TOPICS.length * KNOWLEDGE_FORMS.length} cells.
            </p>
          </section>

          <section>
            <h3>4. Queries</h3>
            <dl className="sids-axis-values">
              {QUERY_TYPES.map((q) => (
                <div key={q.key}>
                  <dt>{q.count} × {q.label}</dt>
                  <dd><span className="sids-degrades">{q.metric}</span>{q.description}</dd>
                </div>
              ))}
            </dl>
            <div className="sids-axis">
              <h4>RBox items <span className="sids-rubric-q">10 queries: the edit changes a property of a relation</span></h4>
              <dl className="sids-axis-values">
                {RBOX_QUERY_TYPES.map((q) => (
                  <div key={q.key}>
                    <dt>{q.count} × {q.label}</dt>
                    <dd><span className="sids-degrades">{q.metric}</span>{q.description}</dd>
                  </div>
                ))}
              </dl>
            </div>
            <div className="sids-axis">
              <h4>Relation properties <span className="sids-rubric-q">what a related or derived answer rests on</span></h4>
              <ValueList values={DERIVATIONS} />
              <h4>Task types <span className="sids-rubric-q">what the question makes the model do</span></h4>
              <ValueList values={TASKS} />
              <p className="dataset-note">
                Related answers are stored (stated often in text) and must change with the edit; derived answers are
                worked out in exactly 2 hops. Properties marked with a bridge combine the edit with another fact the
                model must answer correctly before editing. Composition and binding can stand without a property;
                reflexivity and asymmetry are not used.
              </p>
            </div>
            <div className="sids-axis">
              <h4>Logic <span className="sids-rubric-q">the weakest logic a derived query's inference needs</span></h4>
              <ValueList values={LOGIC} />
              <p>And any theory on top of first-order logic:</p>
              <ValueList values={THEORY} />
              <p className="dataset-note">
                A setting to slice results by, so we can see where parameter editing works and where it stops working.
              </p>
            </div>
          </section>

          <section>
            <h3>Determinacy and belief-revision problems</h3>
            <p>
              A knowledge system holds a <strong>base</strong> of facts it stores and the <strong>closure</strong> derived
              from them. We can't see which facts an LLM stores, or under which names, so one edit can have several
              valid outcomes. Each ABox and TBox derived query is labelled so a failure caused by the method can be told apart
              from ambiguity built into belief revision.
            </p>
            <ValueList values={DETERMINACY} />
            <div className="sids-axis">
              <h4>How a query is labelled</h4>
              <p>{DETERMINACY_RULE}</p>
              <dl className="sids-axis-values">
                {DETERMINACY_SCENARIOS.map((sc) => (
                  <div key={sc.key}>
                    <dt>{sc.label}</dt>
                    <dd><span className="sids-degrades">{sc.example}</span>{sc.description}</dd>
                  </div>
                ))}
              </dl>
            </div>
            <div className="sids-axis">
              <h4>Worlds and chains</h4>
              <p>
                A record with an indeterminate query lists 2 to 4 worlds: what the model stored before the edit, or which
                premise gives way. Each indeterminate query gives an answer and a chain of steps per world; an answer
                passes if it matches some world. On a derived edit, a determinate <strong>premise-route</strong> query
                reaches the edited fact along its premises, where only an inconsistent model gives the old answer.
              </p>
            </div>
            <div className="sids-axis">
              <h4>Shape per topic</h4>
              <p>
                Main split: 20 edits per topic and operation. Revision: ABox 8 (6 stored, very unlikely to be derived,
                and 2 derived, very likely; mathematics and grammar 8 stored), TBox 6, RBox 6. Contraction and expansion
                pair with the revision records (the same fact removed; the same relation and new value with a made-up
                subject). Every non-RBox record has 3 determinate 2-hop derived queries; main ABox revision adds 1
                indeterminate. Dev split: 12 new records per topic, stored edits only, every query determinate.
              </p>
            </div>
            <div className="sids-axis">
              <h4>Evidence <span className="sids-rubric-q">the "?" beside a fact on each record</span></h4>
              <ValueList values={EVIDENCE_CLAIMS} />
              <p className="dataset-note">
                Sources are corpus counts (infini-gram over public pretraining data such as Dolma, OLMo's training set),
                Wikipedia and other pages with the sentence quoted, and the searches tried. Seeing a fact in training text
                shows a model saw it, not how it stores it, so the rating stays an estimate.
              </p>
            </div>
          </section>

          <section>
            <h3>Evaluation</h3>
            <p>
              Free-form answers to a fixed question template, each judged by a local LLM judge against the query's
              original and new answers (no alias or forbidden lists). The judge only labels which answer a response
              gives (original, new, other, none or unclear); a fixed table turns that label into pass or fail:
            </p>
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
            <h4>Change <span className="sids-rubric-q">replace only</span></h4>
            <p>What the edit does to the original fact: the original value and the new one (old object → object).</p>
            <h4>Relation <span className="sids-rubric-q">every record; for RBox, the relation whose property is edited</span></h4>
            <p>Three facets of the record's relation:</p>
            <ValueList values={RELATION_FACETS} />
            <p>Semantics takes one of two values:</p>
            <ValueList values={RELATION_SEMANTICS} />
            <p>Properties are any of these tags:</p>
            <ValueList values={RELATION_PROPERTIES} />
            <p className="dataset-note">
              RELATIONS.md is the one place a relation's properties are defined, so records do not copy them.
            </p>
            <h4>Derivability <span className="sids-rubric-q">edited facts, and every related and derived answer</span></h4>
            <p>
              Whether a model holds a fact as a <strong>stored</strong> claim or <strong>works it out</strong> from other
              knowledge. Only the two ends are used; derived edits appear only in main-split ABox revision (2 per
              topic), as context:
            </p>
            <ValueList values={DERIVABILITY} />
            <p className="dataset-note">{DERIVABILITY_CAVEAT}</p>
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
              {KNOWLEDGE_FORMS.length} knowledge forms (the {BOXES.length} DL boxes). The goal is {EDITS_PER_CELL_GOAL} edits per cell, so{' '}
              {EDITS} edits. ABox and TBox edits carry {QUERIES_PER_EDIT} queries and RBox edits {RBOX_QUERIES_PER_EDIT}, so a
              goal of <strong>{QUERY_GOAL.toLocaleString()} queries</strong>.
            </p>
          </section>
        </div>
      </div>
    </div>
  )
}
