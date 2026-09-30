// The edit type a subset's *edits* are. Locality checks deliberately don't
// appear here: a preservation probe isn't a kind of edit, it's the other
// half of the same subset (see DUnE's localityFile in datasetCatalog.js),
// so it's a view within a subset rather than a category alongside them.
export function datasetCategory(subset) {
  if (subset.category) return subset.category
  if (subset.shape === 'uniedit') return 'Replacement'
  if (subset.shape === 'realtimeqa') return 'Insertion'
  if (subset.shape === 'flat_qa') return 'Forgetting'
  if (subset.shape === 'edit_probes') return subset.key === 'wiki_recent' ? 'Insertion' : 'Replacement'
  if (subset.shape === 'edit_mcq' && subset.key === 'new_info') return 'Insertion'
  return 'Text/Behavior Modification'
}

// Adapt source schemas without inventing previous answers or edit/query links.
// `isLocality` means this record came from the subset's companion locality
// file rather than its edit file - same shape, opposite intent.
export function normalizeDatasetRecord(record, subset, isLocality = false) {
  if (subset.shape === 'standard') return record.display
  const fields = []
  const queries = []
  const field = (label, value) => fields.push({ label, value })
  const query = (purpose, prompt, answer, answerLabel = 'Expected answer') => queries.push({ purpose, prompt, answer, answerLabel })
  const probes = (groups, purpose) => {
    for (const [type, items] of Object.entries(groups || {})) {
      for (const item of items) query(`${purpose} · ${type.replaceAll('_', ' ')}`, item.prompt, item.ground_truth)
    }
  }
  const category = isLocality ? 'Locality check' : datasetCategory(subset)
  let note = ''
  let subject = record.subject || record.concept || record.ent || record.edit?.subject
  if (subset.shape === 'conflict_edit') {
    const edits = record.edits || [record.edit]
    subject = edits[0]?.subject?.label
    if (record.rule) field('Logical rule', record.rule)
    for (const [index, edit] of edits.entries()) {
      if (!edit) continue
      const prefix = edits.length > 1 ? `Edit ${index + 1} · ` : ''
      const name = edit.subject?.label || ''
      const prompt = edit.relation?.prompt?.replace('{}', name)
      const question = edit.relation?.query?.replace('{}', name) || prompt
      field(`${prefix}Prompt`, prompt)
      field(`${prefix}Previous answer`, edit.object?.label)
      field(`${prefix}New answer`, edit.new_object?.label)
      query(`${prefix}Edit success`, question, edit.new_object?.label)
    }
    if (record.true_objects) field('Originally true answers', record.true_objects.map((value) => value.label))
    note = 'The source groups related edits into one case. Original true answers and any rule context remain in the raw record.'
  } else if (subset.shape === 'recoe') {
    const factTexts = (value) => {
      if (Array.isArray(value)) return value.flatMap(factTexts)
      if (value && typeof value === 'object') {
        if (typeof value.fact === 'string') return [value.fact]
        if (typeof value.sentence === 'string') return [value.sentence]
        return Object.values(value).flatMap(factTexts)
      }
      return []
    }
    const changed = record.counterfactuals_per_choice
      ? Object.fromEntries(Object.entries(record.counterfactuals_per_choice).filter(([key]) => key !== 'unchanged_facts'))
      : record.indirect_counterfactual_fact || record.counterfactual_facts
    field('Question', record.question)
    field('Original answer', record.answer)
    field('Counterfactual answer', record.counterfactual_answer)
    if (record.domain) field('Domain', record.domain)
    if (changed) field('Counterfactual supporting facts', [...new Set(factTexts(changed))])
    query('Reasoning after editing', record.question,
      [...new Set([record.counterfactual_answer, ...(record.counterfactual_answer_alias || [])].filter(Boolean))],
      'Counterfactual answer')
    note = 'The counterfactual answer follows from the changed supporting facts. This is a multi-fact reasoning case, not a single prompt–target edit.'
  } else if (subset.shape === 'altered_riddles') {
    field('Original riddle', record.original_riddle)
    field('Original answer', record.original_answer)
    field('Altered riddle', record.altered_riddle)
    field('Altered answer', record.altered_answer)
    field('Alteration type', record.type?.replaceAll('_', ' '))
    query('Baseline · Original', record.original_riddle,
      record.original_accepted_answers?.length ? record.original_accepted_answers : record.original_answer)
    query('Robustness · Altered', record.altered_riddle,
      record.altered_accepted_answers?.length ? record.altered_accepted_answers : record.altered_answer)
    note = 'This tests whether a model reasons about a changed riddle instead of recalling the familiar answer. It is not a model-editing request.'
  } else if (subset.shape === 'uniedit') {
    field('Prompt', record.edit?.prompt)
    field('Target', record.edit?.target)
    note = 'Not labeled per-record, but the construction pipeline (uniedit_construction/tools/edit_data_structure_sample.py::sample_counterfactual_tail) always starts from a real existing claim and substitutes a different real value from a similar entity - there is no insertion or deletion code path, so every record is a counterfactual replacement by construction.'
    for (const [key, purpose] of [['generality', 'Generalization'], ['locality', 'Locality']]) {
      for (const item of Object.values(record[key] || {})) query(purpose, item.prompt, item.target)
    }
  } else if (subset.shape === 'realtimeqa') {
    field('Prompt', record.prompt)
    field('Choices', record.choices)
    field('Correct answer', record.target_new)
    if (record.question_date) field('Date', record.question_date)
    if (record.question_source) field('Source', record.question_source)
    if (record.evidence) field('Evidence', record.evidence)
    note = 'Recent-news question - preprocessed from raw RealTimeQA by datasets/RealTimeQA/build_editing_set.py, ' +
      'which also assigns question_type (Who/What/When/Where/Which/Why/How/Others). No prior belief to overwrite ' +
      '(the model likely never saw this), so treated as Insertion despite having no locality/portability probes ' +
      'in the source, and no subject field either - only usable with FT/LoRA/SCR/IKE, not ROME/MEMIT/PMET/AlphaEdit.'
  } else if (subset.shape === 'edit_probes') {
    field('Prompt', record.prompt)
    if (category === 'Replacement') field('Previous answer', record.ground_truth)
    field(category === 'Insertion' ? 'Answer to add' : 'New answer', record.target_new)
    const rephrase = record.rephrase_prompt || record.rephrase
    if (rephrase) query('Generalization · Rephrase', rephrase, record.target_new)
    probes(record.portability, 'Generalization')
    probes(record.locality, 'Locality')
  } else if (subset.shape === 'flat_qa') {
    field('Prompt', record.question || record.prompt)
    field('Knowledge to forget', record.ground_truth)
    field('Desired response', record.target_new)
    note = 'The forgetting target specifies response behavior. Shared locality checks appear separately.'
  } else if (subset.shape === 'text_completion') {
    field('Context', record.text)
    field('Desired continuation', record.labels)
    probes(record.locality, 'Locality')
  } else if (subset.shape === 'sentiment') {
    field('Context', record.ent)
    field('Desired behavior', null)
    field('Positive examples', record.pos)
    field('Negative examples', record.neg)
    note = 'The source supplies both sentiments without selecting an edit direction or paired evaluation queries.'
  } else if (subset.shape === 'edit_mcq') {
    const locality = isLocality
    const biased = subset.key.startsWith('debiasing_') && !locality
    field(locality ? 'Reference context' : category === 'Insertion' ? 'Fact to add' : 'Instruction / desired behavior', record.edits ?? record['edits:'])
    if (locality) note = 'This is a preservation check, not an edit. Its answer should remain unchanged.'
    const input = record.test_inputs
    const pairs = typeof input === 'string' ? [[input, null]]
      : Array.isArray(input) && typeof input[0] === 'string' ? [input]
      : Array.isArray(input) ? input : []
    for (const [prompt, answer] of pairs) query(locality ? 'Locality' : 'Edit success', prompt, answer, biased ? 'Biased answer to avoid' : 'Expected answer')
  }
  return { category, subject, fields, queries, note }
}
