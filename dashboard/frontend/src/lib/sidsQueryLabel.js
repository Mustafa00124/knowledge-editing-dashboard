import { DERIVATION_NAME } from './sidsDatasetTaxonomy.js'

// Display labels for Sid's Dataset questions, shared by the record card, the
// audit and response modals and the model audit page.
//   Propositional (negation) / (conjunction) / (disjunction)   from `form`: not, and, or
//   Related (near, 1 hop, inverse)                              near: 1 hop, far: multi-hop
//   Derived (2 hops, transitivity, application)                 from `hops`, `derivation` and `task`
//   Cross-lingual (zh)
// The question keys in records, audits and runs stay as they are
// (propositional[0], derived[2], cross_lingual[zh]); only the label changes.

// Record order (REFINEMENTS.md section 7): the edit outwards, everything that
// should change before what must not.
export const QUERY_LABEL = {
  direct: 'Direct', paraphrase: 'Paraphrase', cross_lingual: 'Cross-lingual', propositional: 'Propositional',
  related_near: 'Related', related_far: 'Related', derived: 'Derived',
  unrelated_near: 'Unrelated (near)', unrelated_far: 'Unrelated (far)',
}

// Question types every record will carry; until a record has one, the card
// keeps an empty row in its place.
export const PLACEHOLDER_TYPES = ['related_near', 'related_far']

export const FORM_LABEL = { not: 'negation', and: 'conjunction', or: 'disjunction' }

const hopsText = (n) => `${n} hop${n === 1 ? '' : 's'}`

// Label of one question: its type plus what the item says about it, in brackets.
export function queryLabel(type, item = {}) {
  const base = QUERY_LABEL[type] || String(type || '').replace(/_/g, ' ').replace(/^\w/, (c) => c.toUpperCase())
  const inner = []
  if (type === 'propositional' && item.form) inner.push(FORM_LABEL[item.form] || item.form)
  if (type === 'related_near') inner.push('near')
  if (type === 'related_far') inner.push('far')
  if (type === 'derived' || type.startsWith?.('related')) {
    if (item.hops) inner.push(hopsText(item.hops))
    if (item.derivation && item.derivation !== 'none') inner.push(DERIVATION_NAME[item.derivation] || item.derivation)
    if (item.task && item.task !== 'answer') inner.push(item.task)
  }
  if (type === 'cross_lingual' && item.language) inner.push(item.language)
  return inner.length ? `${base} (${inner.join(', ')})` : base
}

// Label of an audit or run key (direct, cross_lingual[zh], derived[2], ...),
// looked up in the record when one is given.
export function queryKeyLabel(key, rec) {
  if (!key) return ''
  if (key === 'fact') return 'The fact'
  const m = /^(\w+?)\[(\w+)\]$/.exec(key)
  const type = m ? m[1] : key
  const items = (rec?.queries || {})[type]
  let item = {}
  if (m && Array.isArray(items)) {
    item = type === 'cross_lingual' ? items.find((x) => x.language === m[2]) || { language: m[2] } : items[Number(m[2])] || {}
  } else if (items && !Array.isArray(items)) {
    item = items
  }
  if (type === 'cross_lingual' && m && !item.language) item = { ...item, language: m[2] }
  return queryLabel(type, item)
}
