import { useEffect } from 'react'
import {
  AXES,
  COHERENCE_PROPERTIES,
  CONNECTIVITY,
  DEPENDENCY,
  EPISTEMIC_STATUS,
  FACT_TEMPORALITY,
  GROUNDING_LADDER,
  KNOWLEDGE_TIERS,
  PROBE_ROLES,
  QUERY_VARIANTS,
  STRUCTURE_CAVEAT,
  STRUCTURE_EXAMPLES,
} from '../../lib/sidsDatasetTaxonomy.js'

// Reference panel for the categorization scheme, opened from the "?" beside
// the dataset's name. Everything here is sourced from
// sidsDatasetTaxonomy.js, so the panel cannot drift from the axis
// definitions the browser actually renders.
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
              Published editing benchmarks test a narrow notion of knowledge, mostly simple factual triples. This one is
              built to span a much wider <strong>knowledge spectrum</strong> and ask how different kinds of knowledge
              behave under editing.
            </p>
            <p>
              The question is not only "which editing method scores best". It is{' '}
              <strong>under what kinds of knowledge, edit operations and structural conditions a knowledge edit
              becomes risky</strong>: whether success depends on the knowledge being rule-like rather than factual, on
              how densely connected it is, on whether it was inserted or deleted, on how the update was phrased.
            </p>
            <p className="dataset-note">
              Because of that, items are not filed in one hierarchy. Each is given coordinates on several independent
              axes, so matched examples are possible: same topic and knowledge form but different connectivity, or one
              knowledge item expressed several different ways. That is what lets a failure be attributed to a factor
              rather than to two unrelated examples differing in every respect at once.
            </p>
          </section>

          <section>
            <h3>Axes</h3>
            {AXES.filter((axis) => axis.key !== 'knowledge_form' && axis.key !== 'temporality').map((axis) => (
              <div className="sids-axis" key={axis.key}>
                <h4>{axis.label}</h4>
                <dl className="sids-axis-values">
                  {axis.values.map((value) => (
                    <div key={value.key}>
                      <dt>{value.label}</dt>
                      <dd>
                        {value.degrades && (
                          <span className="sids-degrades">
                            {value.degrades
                              .map((d) => COHERENCE_PROPERTIES.find((c) => c.key === d)?.label || d)
                              .join(' + ')}
                          </span>
                        )}
                        {value.description || <span className="text-dim">See rubric below.</span>}
                        {value.examples && <em> {value.examples.join(' · ')}</em>}
                        {value.example && <em> "{value.example}"</em>}
                      </dd>
                    </div>
                  ))}
                </dl>
              </div>
            ))}
            <p className="dataset-note">
              Topic is mainly a diversity control. Edit type is independent of knowledge form: in principle any form
              can be inserted, replaced or deleted, and whether that holds in practice is itself a finding.
            </p>
          </section>

          <section>
            <h3>Knowledge form</h3>
            <p>
              The substantive axis, categorized the way description logic carves up a knowledge base rather than as
              knowledge-graph triples. Published benchmarks test almost only the first form, a plain link. Facts are
              claims about particular individuals; rules are claims about descriptions or relations in general, so one
              rule edit should move every individual it covers.
            </p>
            {KNOWLEDGE_TIERS.map((tier) => (
              <div className="sids-axis" key={tier.key}>
                <h4>{tier.label} <span className="sids-rubric-q">{tier.description}</span></h4>
                {tier.key === 'fact' && (
                  <div>
                    <p className="sids-group-label">Temporality <span>cuts across every fact form</span></p>
                    <dl className="sids-axis-values">
                      {FACT_TEMPORALITY.map((t) => (
                        <div key={t.key}>
                          <dt>{t.label}</dt>
                          <dd>{t.description} <em>{t.examples.join(' · ')}</em></dd>
                        </div>
                      ))}
                    </dl>
                  </div>
                )}
                {tier.groups.map((group) => (
                  <div key={group.key}>
                    <p className="sids-group-label">{group.label} <span>{group.notation}</span></p>
                    <dl className="sids-axis-values">
                      {group.forms.map((form) => (
                        <div key={form.key}>
                          <dt>{form.label}</dt>
                          <dd>
                            <code>{form.notation}</code> {form.description}
                            <em> {form.examples.join(' · ')}</em>
                          </dd>
                        </div>
                      ))}
                    </dl>
                  </div>
                ))}
              </div>
            ))}
          </section>

          <section>
            <h3>Edit representation and coherence</h3>
            <p>
              The representation axis carries the coherence stress test. Rather than one bucket called "gibberish",
              which would conflate several different failure modes, each degraded representation is tagged with the one
              property it destroys:
            </p>
            <dl className="sids-axis-values">
              {COHERENCE_PROPERTIES.map((prop) => (
                <div key={prop.key}>
                  <dt>{prop.label}</dt>
                  <dd>{prop.description}</dd>
                </div>
              ))}
            </dl>
            <p>
              Holding subject, relation, edit type and method fixed, the target can then be walked away from the
              model's semantic structure one rung at a time, with reliability, propagation and locality measured at
              each. <code>{GROUNDING_LADDER.frame}</code>
            </p>
            <ol className="sids-questions">
              {GROUNDING_LADDER.rungs.map((rung) => (
                <li key={rung.value}>
                  <strong>{rung.value}</strong> {rung.description}
                </li>
              ))}
            </ol>
            <p className="dataset-note sids-caveat">{GROUNDING_LADDER.question}</p>
          </section>

          <section>
            <h3>Connectivity and dependency</h3>
            <p>
              Two related but distinct structural properties. A celebrity fact can have very high connectivity, since a
              huge amount of related knowledge surrounds that person, while their favorite color has very low
              dependency, since almost nothing else should change with it. A mathematical rule is high on both.
            </p>
            {[CONNECTIVITY, DEPENDENCY].map((rubric) => (
              <div className="sids-axis" key={rubric.key}>
                <h4>{rubric.label} <span className="sids-rubric-q">{rubric.question}</span></h4>
                <dl className="sids-axis-values">
                  {rubric.levels.map((level) => (
                    <div key={level.key}>
                      <dt>{level.label}</dt>
                      <dd>{level.description}</dd>
                    </div>
                  ))}
                </dl>
              </div>
            ))}
            <div className="sids-combos">
              {STRUCTURE_EXAMPLES.map((combo) => (
                <div className="sids-combo" key={`${combo.connectivity}-${combo.dependency}`}>
                  <strong>C {combo.connectivity} · D {combo.dependency}</strong>
                  <span>{combo.label}</span>
                  <small>{combo.detail}</small>
                </div>
              ))}
            </div>
            <p className="dataset-note sids-caveat">{STRUCTURE_CAVEAT}</p>
          </section>

          <section>
            <h3>Evaluation probes</h3>
            <p>Every item carries four kinds of probe, which is what makes the locality test strict:</p>
            <dl className="sids-axis-values">
              {PROBE_ROLES.map((role) => (
                <div key={role.key}>
                  <dt>
                    {role.label} <span className={`sids-expect sids-expect-${role.expectation.includes('not') ? 'stay' : 'change'}`}>{role.expectation}</span>
                  </dt>
                  <dd>{role.description}</dd>
                </div>
              ))}
            </dl>
            <p>So the core evaluation asks, in order:</p>
            <ol className="sids-questions">
              <li>Did the target change?</li>
              <li>Did the edit propagate to the knowledge that should depend on it?</li>
              <li>Did nearby but independent knowledge stay unchanged?</li>
              <li>Did completely unrelated knowledge stay unchanged?</li>
            </ol>
          </section>

          <section>
            <h3>Open points</h3>
            <div className="sids-axis">
              <h4>Analytic and synthetic</h4>
              <dl className="sids-axis-values">
                {EPISTEMIC_STATUS.map((status) => (
                  <div key={status.key}>
                    <dt>{status.label}</dt>
                    <dd>{status.description}</dd>
                  </div>
                ))}
              </dl>
              <p className="dataset-note">
                Recorded per item, but how to formalize the split is still open. It is here because definitions and
                rules plausibly behave differently under editing from arbitrary facts.
              </p>
            </div>
            <div className="sids-axis">
              <h4>Why who / what / which is not an axis</h4>
              <p className="dataset-note">{QUERY_VARIANTS.note}</p>
              <p className="dataset-note">
                <em>{QUERY_VARIANTS.example.item}</em> generates {QUERY_VARIANTS.example.queries.join(' ')}
              </p>
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}
