// Post-edit answer dots on Sid's Dataset (Results, Sid's Dataset view): the
// tooltip text and CSS class of one dot from the status the backend gives it
// (dashboard/backend/sid_responses.py classify).

// What each status means, for tooltips. A pass reads differently per rule.
const PASS_TEXT = {
  edit: 'gave the new answer: the edit took',
  delete: 'abstained: the deletion took',
  worlds: "matches one of the worlds' answers: a consistent revision",
}
export function dotText(dot) {
  if (!dot) return ''
  switch (dot.status) {
    case 'pass': return PASS_TEXT[dot.kind] || 'passed'
    case 'original': return 'still gives the original answer: the edit did not take'
    case 'other': return 'gave some other answer'
    case 'none': return 'gave no answer'
    case 'unclear': return dot.label ? 'the judge found it unclear (left out of the scores)' : 'not judged'
    case 'kept': return 'kept its answer from before the edit'
    case 'changed':
      if (dot.leak === true) return 'changed its answer to the new answer: the edit leaked in'
      return dot.leak === false ? 'changed its answer (not to the new answer)' : 'changed its answer'
    default: return dot.status
  }
}

// Extra notes on a dot: form and whether the scores count it.
export function dotNotes(dot) {
  const notes = []
  if (dot?.form === 'MALFORMED') notes.push('malformed answer')
  if (dot?.counted === false) notes.push('not counted in generalizability: the model did not give the original answer before the edit')
  return notes
}

export function dotClass(dot, empty) {
  if (empty) return 'sids-audit-dot sids-pe-dot is-empty'
  return `sids-audit-dot sids-pe-dot is-${dot.status}${dot.form === 'MALFORMED' ? ' is-malformed' : ''}${dot.counted === false ? ' is-uncounted' : ''}`
}
