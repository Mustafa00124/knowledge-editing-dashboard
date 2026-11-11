// Display labels for Sid's Dataset questions, shared by the record card, the
// audit and response modals and the model audit page.
//   Propositional · negation / and / or      (the question's `form`)
//   Derived · 2 hops · binding                (its `hops` and `derivation`)
//   Cross-lingual (zh)
// The question keys in records, audits and runs stay as they are
// (propositional[0], derived[2], cross_lingual[zh]); only the label changes.

// In record order: propositional after cross-lingual, locality before derived.
export const QUERY_LABEL = {
  direct: 'Direct', paraphrase: 'Paraphrase', cross_lingual: 'Cross-lingual', propositional: 'Propositional',
  unrelated_near: 'Unrelated (near)', unrelated_far: 'Unrelated (far)', derived: 'Derived',
}

export const FORM_LABEL = { not: 'negation', and: 'and', or: 'or' }

const SEP = ' · '

// Label of one question: its type plus what the item says about it.
export function queryLabel(type, item = {}) {
  const base = QUERY_LABEL[type] || String(type || '').replace(/_/g, ' ').replace(/^\w/, (c) => c.toUpperCase())
  if (type === 'propositional' && item.form) return base + SEP + (FORM_LABEL[item.form] || item.form)
  if (type === 'derived') {
    const parts = [base]
    if (item.hops) parts.push(`${item.hops} hop${item.hops === 1 ? '' : 's'}`)
    if (item.derivation) parts.push(item.derivation)
    return parts.join(SEP)
  }
  if (type === 'cross_lingual' && item.language) return `${base} (${item.language})`
  return base
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
