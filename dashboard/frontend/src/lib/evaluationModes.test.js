import assert from 'node:assert/strict'
import { test } from 'node:test'
import { evaluationRow, hasEvaluation, evaluationMetric } from './evaluationModes.js'
import { comboCount } from './comboCount.js'
import { formatMetricValue } from './formatMetric.js'

test('legacy scores never appear under a semantic mode', () => {
  const old = { edit_succ: 75, total_sec: 12 }
  assert.equal(hasEvaluation(old, 'original'), true)
  assert.equal(hasEvaluation(old, 'bertscore'), false)
  assert.equal(evaluationRow(old, 'bertscore').edit_succ, null)
  assert.equal(evaluationRow(old, 'original').edit_succ, 75)
})
test('switching modes selects their scores without changing timing', () => {
  const row = { total_sec: 12, evaluations: { original: { edit_succ: 75 }, bertscore: { edit_succ: 0.91 } } }
  assert.equal(evaluationRow(row, 'bertscore').edit_succ, 0.91)
  assert.equal(evaluationRow(row, 'bertscore').total_sec, 12)
  assert.equal(evaluationRow(row, 'llm_judge').edit_succ, null)
  assert.ok(!formatMetricValue(evaluationMetric('edit_succ', 'bertscore'), 0.91).includes('%'))
})
test('sid scores show under their own mode only', () => {
  const row = { total_sec: 5, evaluations: { sid: { edit_succ: 50, portability: 25 } } }
  assert.equal(hasEvaluation(row, 'sid'), true)
  assert.equal(hasEvaluation(row, 'original'), false)
  assert.equal(evaluationRow(row, 'sid').portability, 25)
})
test('combined evaluation selection does not multiply editing jobs', () => {
  assert.equal(comboCount({ method: ['ft', 'rome'], evaluation_modes: ['exact_match,bertscore,llm_judge'] }), 2)
  assert.equal(comboCount({ method: ['ft'], evaluation_modes: [] }), 0)
})
