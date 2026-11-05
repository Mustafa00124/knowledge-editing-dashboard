import { useEffect, useState } from 'react'
import {
  BOXES,
  DERIVABILITY,
  DETERMINACY,
  EDIT_OPERATIONS,
  EVIDENCE_CLAIMS,
  FICTIONAL,
  INDETERMINATE,
  INFINIGRAM_INDEXES,
  LOGIC,
  SOURCE_KINDS,
  THEORY,
  QUERY_TYPES,
  RELATION_SEMANTICS,
  relationProperties,
  relationPropertyOf,
  TOPICS,
  coordinateSummary,
  worldLabel,
} from '../../lib/sidsDatasetTaxonomy.js'
import { hasChain } from './DerivationModal.jsx'

// Shared pieces of Sid's Dataset's record browser: the topic / operation /
// box tab rows and the record card with its query table. The Datasets page
// (SidsDatasetBrowser, pre-edit audit dots) and the Results page
// (SidResponsesBrowser, post-edit answer dots) both build on them; each
// passes its own dots through RecordCard's `dots` prop.

// The browsing layers: topic, then belief revision operation, then knowledge
// form (box).
// Explanations of each layer live in SidsDatasetInfoModal (the "?"), not here.
// Relation semantics and properties are tags, shown on each record.
export const LAYERS = ['topic', 'edit_operation', 'box']

// Whether a record matches the coordinate on every layer above `upTo` (all
// layers when `upTo` is left out).
export function matches(rec, coordinate, upTo) {
  const above = upTo ? LAYERS.slice(0, LAYERS.indexOf(upTo)) : LAYERS
  for (const layer of above) {
    if (rec[layer] !== coordinate[layer]) return false
  }
  return true
}

export function TabRow({ label, values, selected, onSelect, counts }) {
  return (
    <div className="subnav sids-tabrow" aria-label={label}>
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

// In record order: propositional after cross-lingual, locality before derived.
export const QUERY_LABEL = { direct: 'Direct', paraphrase: 'Paraphrase', cross_lingual: 'Cross-lingual',
  propositional: 'Propositional', unrelated_near: 'Unrelated (near)', unrelated_far: 'Unrelated (far)', derived: 'Derived' }
const show = (v) => (v == null ? '—' : String(v))

// Each row also gets the model audit's query key (audit_queries.py):
// direct, paraphrase, cross_lingual[zh], propositional[1], unrelated_near[0], derived[2].
export function queryRows(rec) {
  const q = rec.queries || {}
  const rows = []
  for (const key of Object.keys(QUERY_LABEL)) {
    const items = Array.isArray(q[key]) ? q[key] : q[key] ? [q[key]] : []
    items.forEach((item, i) => {
      const auditKey = key === 'direct' || key === 'paraphrase' ? key
        : key === 'cross_lingual' ? `cross_lingual[${item.language}]` : `${key}[${i}]`
      rows.push({ key, auditKey, ...item })
    })
  }
  return rows
}

// Short model names for the dot tooltips and modals.
export const MODEL_LABEL = {
  'qwen3-4b-instruct-2507': 'Qwen3-4B-Instruct', 'olmo-3-7b-instruct': 'Olmo-3-7B-Instruct',
  'llama-3.1-8b-instruct': 'Llama-3.1-8B-Instruct', 'mistral-7b-instruct-v0.1': 'Mistral-7B-Instruct',
  'qwen3-4b-base': 'Qwen3-4B-Base', 'olmo-3-7b-base': 'Olmo-3-7B-Base', 'llama-3.1-8b': 'Llama-3.1-8B',
  'mistral-7b-v0.1': 'Mistral-7B', 'smollm3-3b-base': 'SmolLM3-3B-Base', 'smollm3-3b': 'SmolLM3-3B',
  'map-neo-7b': 'MAP-Neo-7B', 'map-neo-7b-instruct': 'MAP-Neo-7B-Instruct',
}
export const modelLabel = (m) => MODEL_LABEL[m] || m

// Formal check of the description-logic reasoning (reason.py with HermiT):
// a small mark per derived query and per record. Pass, fail, or not checked
// (needs arithmetic or dates, which the reasoner can't express).
// Which checker verified a derived query: HermiT for description logic (DL),
// Z3 for first-order logic with arithmetic or dates (FOL).
const CHECKER_LABEL = { hermit: 'DL', z3: 'FOL' }
const CHECKER_NAME = { hermit: 'HermiT, description logic', z3: 'Z3, first-order logic' }
const FORMAL_TEXT = {
  pass: 'Formally verified: the answers follow in every world they should',
  fail: 'Fails the formal check',
  not_checked: 'Not formally checked',
}
function FormalMark({ status, lines, checker, theory }) {
  if (!status) return null
  const mark = status === 'pass' ? '✓' : status === 'fail' ? '✗' : '–'
  const label = CHECKER_LABEL[checker] || 'logic'
  const head = `${FORMAL_TEXT[status] || status}${CHECKER_NAME[checker] ? ` (${CHECKER_NAME[checker]}${theory ? `, ${theory}` : ''})` : ''}`
  const title = [head, ...(lines || [])].join('\n')
  return <span className={`sids-formal-mark is-${status}`} title={title}>{mark} {label}</span>
}

// "geography-replace-0002" -> "Geography 2". The operation is already the
// selected tab, so the label keeps only topic and number.
export function recordLabel(id) {
  const m = /^([a-z_]+)-[a-z_]+-0*(\d+)$/i.exec(id || '')
  if (!m) return id
  const topic = TOPICS.find((t) => t.key === m[1])?.label || m[1].replace(/_/g, ' ')
  return `${topic.charAt(0).toUpperCase()}${topic.slice(1)} ${m[2]}`
}

// Shown label for a stored key ("very_likely" -> "Very likely").
const labelOf = (list, key) => list.find((x) => x.key === key)?.label ?? String(key).replace(/_/g, ' ')
// Query type -> the metric it feeds, which picks the pill colour.
const METRIC_OF = Object.fromEntries(QUERY_TYPES.map((q) => [q.key, q.metric.replace(/[^a-z]/g, '')]))

// One property under the statement: a small caption over its value, tinted
// by kind (change, relation, derivability, ...).
function Chip({ kind, label, children }) {
  return (
    <span className={`sids-chip sids-chip-${kind}`}>
      {label && <span className="sids-chip-label">{label}</span>}
      <span className="sids-chip-value">{children}</span>
    </span>
  )
}

// The evidence behind one fact (README, Evidence): why we rate it stored or
// derived, with the corpus counts, quotes and searches that back it.
function EvidenceModal({ fact, entry, onClose }) {
  useEffect(() => {
    const onKey = (ev) => { if (ev.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])
  const claim = EVIDENCE_CLAIMS.find((c) => c.key === entry.claim)
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal sids-evidence-modal" onClick={(ev) => ev.stopPropagation()} role="dialog" aria-modal="true" aria-label="Evidence">
        <div className="modal-header">
          <div className="modal-title-group">
            <h2>Why {claim ? claim.label.toLowerCase() : entry.claim}?</h2>
            <span className={`sids-evidence-claim is-${entry.claim}`}>{claim?.label || entry.claim}</span>
          </div>
          <button type="button" className="btn-plain" onClick={onClose} aria-label="Close">✕</button>
        </div>
        <div className="modal-body">
          <p className="sids-evidence-fact">{fact}</p>
          <p>{entry.why}</p>
          <ul className="sids-evidence-sources">
            {(entry.sources || []).map((src, i) => (
              <li key={i}>
                <span className="sids-evidence-kind">{SOURCE_KINDS[src.kind] || src.kind}</span>
                {src.kind === 'infini-gram' && (
                  <span>
                    <q>{src.query}</q>: <strong>{Number(src.count).toLocaleString()}</strong>
                    {src.index && <span className="sids-evidence-dim"> in {INFINIGRAM_INDEXES[src.index] || src.index}</span>}
                  </span>
                )}
                {(src.kind === 'wikipedia' || src.kind === 'web') && (
                  <span>
                    <a href={src.url} target="_blank" rel="noreferrer">{decodeURIComponent(src.url.replace(/^https?:\/\/(www\.)?/, ''))}</a>
                    {src.quote && <> <q>{src.quote}</q></>}
                  </span>
                )}
                {src.kind === 'search' && <span><q>{src.query}</q>{src.engine && <span className="sids-evidence-dim"> on {src.engine}</span>}</span>}
                {src.note && <span className="sids-evidence-dim sids-evidence-note">{src.note}</span>}
              </li>
            ))}
          </ul>
          {claim && <p className="dataset-note">{claim.description}</p>}
        </div>
      </div>
    </div>
  )
}

// A "?" beside a fact that opens its evidence; nothing when the record has none.
function EvidenceButton({ fact, evidence }) {
  const [open, setOpen] = useState(false)
  const entry = evidence?.[fact]
  if (!entry) return null
  return (
    <>
      <button type="button" className="sids-evidence-btn" title="Why we rate this fact stored or derived"
        onClick={(ev) => { ev.stopPropagation(); setOpen(true) }}>?</button>
      {open && <EvidenceModal fact={fact} entry={entry} onClose={() => setOpen(false)} />}
    </>
  )
}

const DETERMINACY_LABEL = Object.fromEntries(DETERMINACY.map((d) => [d.key, d.label]))
const LOGIC_LABEL = Object.fromEntries([...LOGIC, ...THEORY].map((l) => [l.key, l.label]))

// One record: header (badge, original fact, dots for 'fact'), tags, and when
// opened its details and query table. `dots(key)` renders the status dots for
// 'fact' (the header) or a query's audit key (direct, derived[2], ...);
// `footer` goes under the table. Without `onChain` the derivation buttons are
// left out. `review` (the Datasets page's review dots per manual rule) shows
// under the tags whether or not the card is open.
export default function RecordCard({ rec, relations, onChain, dots, formal, footer, review }) {
  const [open, setOpen] = useState(false)
  const e = rec.edit || {}
  const chains = onChain && hasChain(rec)
  // Relation tag group: name and semantics from the record, properties from
  // RELATIONS.md (sent by the backend with the records).
  const properties = relationProperties(relations, rec.relation)
  const edited = e.original || e.statement
  const details = [
    // The header reads the original fact; the full edited sentence is here.
    ['Edit', e.old_object == null ? null : e.statement],
    ['Axiom', e.axiom && <code>{e.axiom}</code>],
    ['Scope', e.scope],
    ['Premises', e.premises?.length > 0 && (
      <>
        <ul className="sids-fact-list">
          {e.premises.map((p) => <li key={p}>{p} <EvidenceButton fact={p} evidence={rec.evidence} /></li>)}
        </ul>
        {chains && (
          <button type="button" className="btn-plain-small sids-chain-btn" onClick={() => onChain(rec, { kind: 'premises' })}>
            Show derivation
          </button>
        )}
      </>
    )],
  ].filter(([, v]) => v)
  return (
    <div className={`sids-record${open ? ' open' : ''}`}>
      <div className="sids-record-headrow">
        <button type="button" className="sids-record-head" aria-expanded={open} onClick={() => setOpen((o) => !o)}>
          <span className="sids-record-caret">{open ? '▾' : '▸'}</span>
          <span className="sids-record-badge" title={rec.id}>{recordLabel(rec.id)}</span>
          {/* The original fact; the Change chip shows what the edit makes of it. Insert has no original. */}
          <span className="sids-record-statement">{e.original || e.statement}</span>
        </button>
        {/* Status dots for the whole fact, outside the toggle button since each dot is a button of its own. */}
        {dots?.('fact')}
        <FormalMark status={formal?.status === 'pass' || formal?.status === 'fail' ? formal.status : null}
          lines={Object.entries(formal?.record_checks || {}).map(([k, v]) => `${k}: ${v.status}`)} />
      </div>
      <div className="sids-record-meta">
        {/* Tag order: change, relation, derivability. Determinacy is shown on each derived query. */}
        {e.old_object != null ? (
          <Chip kind="change" label="Change">
            <span className="sids-old">{show(e.old_object)}</span> → <span className="sids-new">{show(e.object)}</span>
          </Chip>
        ) : e.original ? (
          // TBox and RBox edits change a rule, not one object: original rule -> edited rule.
          <Chip kind="change" label="Change">
            <span className="sids-old">{e.original}</span> → <span className="sids-new">{e.statement}</span>
          </Chip>
        ) : null}
        {/* RBox edits change the relation's own properties, so the chip would only repeat the Change chip. */}
        {rec.box !== 'rbox' && <Chip kind="relation" label="Relation">
          <span className="sids-chip-part"><code>{rec.relation}</code></span>
          {rec.relation_semantics && (
            <span className="sids-chip-part">
              <span className="sids-chip-part-key">Semantics</span> {labelOf(RELATION_SEMANTICS, rec.relation_semantics)}
            </span>
          )}
          <span className="sids-chip-part">
            <span className="sids-chip-part-key">Properties</span>{' '}
            {properties.length
              ? properties.map((tag, i) => (
                <span key={tag} title={relationPropertyOf(tag)?.label}>{i ? ', ' : ''}<code>{tag}</code></span>
              ))
              : 'none'}
          </span>
        </Chip>}
        {rec.derivability != null && (
          <Chip kind="derivability" label="Derivability">
            {labelOf(DERIVABILITY, rec.derivability)} <EvidenceButton fact={edited} evidence={rec.evidence} />
          </Chip>
        )}
        {e.fixture && <Chip kind="fixture">Fixture</Chip>}
        {rec.fictional ? (
          <Chip kind="reality" label="Made up">
            <span title={FICTIONAL.find((f) => f.key === rec.fictional)?.description}>{labelOf(FICTIONAL, rec.fictional)}</span>
          </Chip>
        ) : rec.reality && <Chip kind="reality" label="Reality">{rec.reality === 'fictional' ? 'Fictional' : 'Real'}</Chip>}
      </div>
      {review}
      {open && (
        <div className="sids-record-body">
          {details.length > 0 && (
            <dl className="sids-record-details">
              {details.map(([k, v]) => (
                <div key={k}><dt>{k}</dt><dd>{v}</dd></div>
              ))}
            </dl>
          )}
          <div className="table-wrap">
            <table className="sids-query-table">
              <thead><tr><th>Query</th><th>Prompt</th><th>Answer (original → new)</th><th>Derivation</th></tr></thead>
              <tbody>
                {queryRows(rec).map((r, i) => (
                  <tr key={i}>
                    <td>
                      <span className={`sids-query-type sids-metric-${METRIC_OF[r.key]}`}>
                        {QUERY_LABEL[r.key]}{r.language ? ` (${r.language})` : ''}
                      </span>
                      {dots?.(r.auditKey)}
                      {r.key === 'derived' && (() => {
                        const f = formal?.queries?.[r.auditKey.slice(8, -1)]
                        return <FormalMark status={f?.status} lines={f?.lines} checker={f?.checker} theory={f?.theory} />
                      })()}
                    </td>
                    <td>{r.prompt}</td>
                    <td className="sids-answer">
                      {r.key.startsWith('unrelated') ? (
                        <><em>model's own pre-edit answer</em>{r.reference && <span className="sids-answer-ref">ref: {r.reference}</span>}</>
                      ) : r.world_answers ? (
                        <>
                          <span className="sids-old">{show(r.original_answer)}</span> →
                          <span className="sids-world-answers">
                            {(rec.worlds || []).map((w) => (
                              <span key={w.id} title={w.summary}>
                                <span className="sids-world-id">{worldLabel(w.id)}</span> <span className="sids-new">{r.world_answers[w.id]?.answer ?? (rec.edit_operation === 'delete' ? 'does not know' : '—')}</span>
                              </span>
                            ))}
                          </span>
                        </>
                      ) : (
                        <><span className="sids-old">{show(r.original_answer)}</span> → <span className="sids-new">{show(r.new_answer)}</span></>
                      )}
                    </td>
                    <td className="sids-derivation">
                      {(r.determinacy || r.logic) && (
                        <span className="sids-tags">
                          {r.determinacy && (
                            <span className={`sids-det is-${INDETERMINATE.includes(r.determinacy) ? 'open' : 'closed'}`} title={r.determinacy_why || ''}>
                              {DETERMINACY_LABEL[r.determinacy] || r.determinacy}
                            </span>
                          )}
                          {r.premise_route && <span className="sids-det-flag" title="Reaches the edited fact along its premises: only an inconsistent model gives the old answer">premise route</span>}
                          {r.logic && <span className="sids-det-flag" title="The weakest logic the inference needs">{LOGIC_LABEL[r.logic] || r.logic}</span>}
                          {r.theory && <span className="sids-det-flag" title="A theory the inference uses on top of first-order logic">{LOGIC_LABEL[r.theory] || r.theory}</span>}
                        </span>
                      )}
                      {r.derivation ? `${r.derivation}${r.hops ? `, ${r.hops} hop${r.hops === 1 ? '' : 's'}` : ''}` : ''}
                      {r.bridge?.length > 0 && (
                        <span className="sids-bridge">
                          bridge: {r.bridge.map((b) => <span key={b}>{b} <EvidenceButton fact={b} evidence={rec.evidence} /></span>)}
                        </span>
                      )}
                      {r.revision_facts?.length > 0 && (
                        <span className="sids-bridge" title="Facts that settle which belief gives way, not combined into the answer (not counted in hops)">
                          revision: {r.revision_facts.map((b) => <span key={b}>{b} <EvidenceButton fact={b} evidence={rec.evidence} /></span>)}
                        </span>
                      )}
                      {r.alt_derivations?.length > 0 && (
                        <span className="sids-bridge" title="Other valid routes to the same answer">also: {r.alt_derivations.join(', ')}</span>
                      )}
                      {r.key === 'propositional' && (
                        <>
                          <span className="sids-tags"><span className="sids-det-flag" title="Truth-functional: checked by truth table (validate.py)">{r.form}</span></span>
                          {r.side_fact && <span className="sids-bridge">side fact: <span>{r.side_fact}</span></span>}
                        </>
                      )}
                      {r.key === 'derived' && chains && (
                        <button type="button" className="btn-plain-small sids-chain-btn" onClick={() => onChain(rec, { kind: 'query', query: r })}>
                          Chain
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {footer}
        </div>
      )}
    </div>
  )
}
