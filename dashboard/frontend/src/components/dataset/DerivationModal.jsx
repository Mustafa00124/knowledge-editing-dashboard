import { useEffect, useState } from 'react'
import { DERIVATIONS } from '../../lib/sidsDatasetTaxonomy.js'

// The inference chain behind one derived answer, or behind an edited fact
// that follows from premises. Leaves are what the model must hold (the edit,
// facts it must already know, facts given in the prompt, the relation
// property used), the middle is the rule applied, the right is the answer.
// Leaves with a check show each model's audit result, so a failed derived
// query can be told apart from a gap in what the model knew to begin with.
// The lookups mirror datasets/SidsDataset/validate.py (facts_to_check,
// relation_property), which the model audit uses.

// Derivation -> the relation tag it relies on (prefix match for tags with an argument).
const NEEDS_TAG = {
  symmetry: 'symmetric', asymmetry: 'asymmetric', inverse: 'inverse:', transitivity: 'transitive',
  chain: 'chain:', subproperty: 'subproperty:', functional: 'functional',
}

// What each rule does, in one line.
const RULE_TEXT = {
  symmetry: 'If a R b, then b R a.',
  asymmetry: 'If a R b, then not b R a.',
  inverse: 'a R b holds exactly when b S a.',
  transitivity: 'If a R b and b R c, then a R c.',
  chain: 'If a R b and b S c, then a T c.',
  subproperty: 'If a R b, then a S b.',
  functional: 'R has one value per subject, so a new value removes the old one.',
  composition: 'The edited value is followed through a further fact to a new answer.',
  inheritance: 'Every C is D, and a is a C, so a is D.',
  binding: 'The edit is reached through an alias, a bound individual or a new class member.',
  application: 'The edit is used to fill a field, compute a value or run a task.',
  scope: 'The boundary of what follows: the edit alone does not settle it.',
}

export function relationProperty(rec, q, relations) {
  const need = NEEDS_TAG[q.derivation]
  if (!need || rec.box === 'rbox') return null
  const name = q.via || rec.relation
  const tags = relations?.[name]?.tags || []
  const tag = [...tags].sort().find((t) => t === need || (need.endsWith(':') && t.startsWith(need)))
  return tag ? { name, tag } : null
}

export function axiomOf(name, tag) {
  const [kind, arg] = tag.split(':')
  if (kind === 'symmetric') return `Sym(${name})`
  if (kind === 'asymmetric') return `Asym(${name})`
  if (kind === 'transitive') return `Trans(${name})`
  if (kind === 'functional') return `Func(${name})`
  if (kind === 'inverse') return `${name} ≡ ${arg}⁻`
  if (kind === 'subproperty') return `${name} ⊑ ${arg}`
  if (kind === 'chain') {
    const [s, t] = arg.split('->')
    return `${name} ∘ ${s} ⊑ ${t}`
  }
  return `${name}: ${tag}`
}

// A record has derivations worth drawing when it is ABox/TBox: every derived
// query, and the edit itself when it lists premises.
export const hasChain = (rec) => rec.box === 'abox' || rec.box === 'tbox'

function buildChain(rec, target, relations, relationChecks) {
  const e = rec.edit || {}
  const checkOf = (fact) => (rec.checks || []).find((c) => c.fact === fact)
  const factLeaf = (fact, role) => {
    const c = role === 'known' ? checkOf(fact) : null
    return { role, text: fact, check: c && { kind: 'fact', key: `${rec.id}\t${fact}`, prompt: c.prompt, answer: c.answer } }
  }
  const before = e.original || e.statement
  if (target.kind === 'premises') {
    return {
      title: 'How the original fact follows from its premises',
      leaves: (e.premises || []).map((p) => factLeaf(p, 'known')),
      rule: { label: 'Derived from premises', text: 'The model may compose the original fact from these premises instead of storing it. They stay true after the edit, so they keep pointing at the original.' },
      conclusion: { label: 'Premises imply', old: before, new: e.statement, conflict: true },
    }
  }
  const q = target.query
  const leaves = [{ role: 'edit', label: rec.box === 'tbox' ? 'Edited rule' : 'Edited fact', old: before, new: e.statement, axiom: rec.box === 'tbox' ? e.axiom : null }]
  for (const b of q.bridge || []) leaves.push(factLeaf(b, q.bridge_in_prompt ? 'given' : 'known'))
  const prop = relationProperty(rec, q, relations)
  if (prop) {
    const c = relationChecks?.[prop.name]?.[prop.tag]
    leaves.push({
      role: 'property', text: axiomOf(prop.name, prop.tag), label: q.via ? `via ${q.via}` : null,
      check: c && { kind: 'relation', key: `${prop.name}\t${prop.tag}`, prompt: c.prompt, answer: c.answer },
    })
  }
  const d = DERIVATIONS.find((x) => x.key === q.derivation)
  return {
    title: 'How this derived answer is inferred',
    prompt: q.prompt,
    leaves,
    rule: { label: d?.label || q.derivation, notation: d?.notation, text: RULE_TEXT[q.derivation], hops: q.hops },
    conclusion: { label: 'Derived answer', old: q.original_answer, new: q.new_answer, unchanged: q.discriminates === false },
  }
}

const ROLE_LABEL = {
  edit: 'The edit',
  known: 'Must already know',
  given: 'Given in the prompt',
  property: 'Relation property',
}

// One model's result on a check: pass, fail, unclear, or not asked.
function Badge({ model, result }) {
  const state = result == null ? 'none' : result.score === 1 ? 'pass' : result.score === 0 ? 'fail' : 'unclear'
  const mark = { pass: '✓', fail: '✗', unclear: '?', none: '·' }[state]
  const title = result == null ? `${model}: not asked` : `${model}: ${result.label || 'no label'}${result.response ? `, answered "${result.response}"` : ''}`
  return <span className={`sids-badge is-${state}`} title={title}>{mark} {model}</span>
}

function Leaf({ leaf, world, models, results }) {
  const text = leaf.role === 'edit' ? (world === 'original' ? leaf.old : leaf.new) : leaf.text
  return (
    <div className={`sids-leaf is-${leaf.role}`}>
      <span className="sids-leaf-role">{ROLE_LABEL[leaf.role]}{leaf.label && leaf.role !== 'edit' ? ` (${leaf.label})` : ''}</span>
      <span className={`sids-leaf-text${leaf.role === 'edit' ? (world === 'original' ? ' sids-old' : ' sids-new') : ''}`}>
        {leaf.role === 'property' ? <code>{text}</code> : text}
      </span>
      {leaf.axiom && <code className="sids-leaf-axiom">{leaf.axiom}</code>}
      {leaf.check && (
        <div className="sids-leaf-check">
          <span className="sids-leaf-probe">Audit asks: {leaf.check.prompt} <em>({leaf.check.answer})</em></span>
          {models.length > 0 && (
            <span className="sids-badges">
              {models.map((m) => <Badge key={m} model={m} result={results[m]?.[leaf.check.key]} />)}
            </span>
          )}
        </div>
      )}
    </div>
  )
}

export default function DerivationModal({ rec, target, relations, relationChecks, audit, onClose }) {
  const [world, setWorld] = useState('edited')
  useEffect(() => {
    const onKey = (ev) => { if (ev.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const chain = buildChain(rec, target, relations, relationChecks)
  // Models whose newest audit asked the checks, and their results by check key.
  const withChecks = (audit || []).filter((m) => m.has_checks)
  const models = withChecks.map((m) => m.model)
  const results = Object.fromEntries(withChecks.map((m) => [m.model, {
    ...Object.fromEntries(m.facts.map((r) => [`${r.record_id}\t${r.fact}`, r])),
    ...Object.fromEntries(m.relations.map((r) => [`${r.relation}\t${r.tag}`, r])),
  }]))
  const checked = chain.leaves.filter((l) => l.check)
  // A model holds the chain when it passes every check in it.
  const verdict = (m) => {
    const got = checked.map((l) => results[m]?.[l.check.key]?.score)
    return got.some((s) => s == null) ? 'unclear' : got.every((s) => s === 1) ? 'pass' : 'fail'
  }
  const c = chain.conclusion
  const answer = world === 'original' ? c.old : c.new

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal sids-chain-modal" onClick={(ev) => ev.stopPropagation()} role="dialog" aria-modal="true" aria-label={chain.title}>
        <div className="modal-header">
          <div className="modal-title-group">
            <h2>{chain.title}</h2>
            <span className="sids-info-tag">{rec.id}</span>
          </div>
          <button type="button" className="btn-plain" onClick={onClose} aria-label="Close">✕</button>
        </div>
        <div className="modal-body">
          {chain.prompt && <p className="sids-chain-prompt">{chain.prompt}</p>}
          {target.kind === 'query' && (
            <div className="sids-world" role="group" aria-label="World">
              {['edited', 'original'].map((w) => (
                <button key={w} type="button" className={`btn-plain-small${world === w ? ' is-on' : ''}`} onClick={() => setWorld(w)}>
                  {w === 'edited' ? 'After the edit' : 'Before the edit'}
                </button>
              ))}
            </div>
          )}

          <div className="sids-chain">
            <div className="sids-chain-col sids-chain-leaves">
              {chain.leaves.map((l, i) => <Leaf key={i} leaf={l} world={world} models={models} results={results} />)}
            </div>
            <div className="sids-chain-arrow" aria-hidden="true">→</div>
            <div className="sids-chain-col">
              <div className="sids-rule">
                <span className="sids-leaf-role">Inference</span>
                <strong>{chain.rule.label}</strong>
                {chain.rule.notation && <code>{chain.rule.notation}</code>}
                {chain.rule.text && <span className="sids-rule-text">{chain.rule.text}</span>}
                {chain.rule.hops && <span className="sids-rule-text">{chain.rule.hops} hop{chain.rule.hops === 1 ? '' : 's'}</span>}
              </div>
            </div>
            <div className="sids-chain-arrow" aria-hidden="true">→</div>
            <div className="sids-chain-col">
              <div className="sids-conclusion">
                <span className="sids-leaf-role">{c.label}</span>
                {c.conflict ? (
                  <>
                    <span className="sids-old">{c.old}</span>
                    <span className="sids-rule-text">but the edit asserts</span>
                    <span className="sids-new">{c.new}</span>
                  </>
                ) : (
                  <span className={world === 'original' ? 'sids-old' : 'sids-new'}>{answer ?? 'not defined in this world'}</span>
                )}
                {c.unchanged && <span className="sids-rule-text">Same before and after: tests consistency, not the new value.</span>}
              </div>
            </div>
          </div>

          {checked.length > 0 && (
            <div className="sids-chain-verdict">
              <span className="sids-leaf-role">Chain known before editing</span>
              {models.length ? (
                <span className="sids-badges">
                  {models.map((m) => <Badge key={m} model={m} result={{ pass: { score: 1, label: 'every check passed' }, fail: { score: 0, label: 'a check failed' }, unclear: { score: null, label: 'a check was unclear or not asked' } }[verdict(m)]} />)}
                </span>
              ) : (
                <span className="sids-rule-text">No model audit has asked these checks yet. Run a Model audit to fill them in.</span>
              )}
            </div>
          )}
          {checked.length === 0 && (
            <p className="sids-rule-text">Nothing in this chain needs checking: every fact it uses is the edit or is given in the prompt.</p>
          )}
        </div>
      </div>
    </div>
  )
}
