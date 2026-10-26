import { useEffect } from 'react'
import {
  BOXES,
  DERIVATIONS,
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
              Three levels: edit operation, then knowledge form, then a fixed set of 10 queries per edit (7 for RBox). Relations and
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
            <p className="dataset-note">
              {KNOWLEDGE_FORMS.length} forms per topic (one per box), so {EDIT_OPERATIONS.length} operations × {TOPICS.length} topics
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
              <h4>RBox items <span className="sids-rubric-q">7 queries: the edit changes a property of a relation</span></h4>
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
              <h4>Derived queries <span className="sids-rubric-q">which ones an item gets depends on its relation's properties</span></h4>
              <ValueList values={DERIVATIONS} />
              <p className="dataset-note">
                Derivations marked with a bridge combine the edit with another fact. The model must answer every bridge
                fact correctly before editing, or the item is dropped for that model. Reflexivity is never used, since
                "a R a" doesn't depend on the edit. Task types (binding, application, scope) are sorted by what the
                question asks the model to do; the inference underneath is usually still description logic.
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
              <h4>Shape per topic <span className="sids-rubric-q">branch sids-determinacy-2</span></h4>
              <p>
                4 replace edits per topic in each box. ABox: 2 of facts likely stored, 2 of facts likely derived, each
                with 2 determinate and 2 indeterminate derived queries. TBox: 2 determinate queries on new members named
                in the prompt, 2 indeterminate on well-known members whose property may be stored directly. RBox: 2
                "Does it follow that ...?" queries, determinate by construction. Mathematics may have every derived query
                determinate, since a fact about a number leaves no consistent world to split between.
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
            <h4>Derivability <span className="sids-rubric-q">ABox and TBox replace and delete</span></h4>
            <p>
              How likely a model is to derive the edited fact from other knowledge rather than store it. The scale runs
              from <strong>axiomatic (stored)</strong>, held directly as a base claim, to{' '}
              <strong>derived (composed)</strong>, composed from other knowledge the model holds. Scored 1 to 5:
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
