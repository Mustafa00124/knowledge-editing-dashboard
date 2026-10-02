import assert from 'node:assert/strict'
import { test } from 'node:test'
import { aggregate, stats } from './hparams.js'

const run = (method, model, dataset, layers, rel, loc, state = 'COMPLETED') => ({
  method, model, dataset, overrides: { layers }, state, worst: Math.min(rel, loc),
  scores: { reliability: rel, generalizability: null, locality: loc, fluency: 1 }, wall_sec: 100,
})
const rows = [
  run('rome', 'a', 'd1', [4], 1.0, 0.6), run('rome', 'a', 'd2', [4], 0.8, 0.4),
  run('rome', 'b', 'd1', [4], 0.6, 0.6), run('rome', 'a', 'd1', [5], 0.9, 0.9),
  run('rome', 'a', 'd2', [5], 0.9, 0.9, 'FAILED'),
]

test('stats are the mean and sample variance of present values', () => {
  const s = stats([0.4, 0.6, null])
  assert.equal(s.n, 2)
  assert.ok(Math.abs(s.mean - 0.5) < 1e-12)
  assert.ok(Math.abs(s.variance - 0.02) < 1e-12)
  assert.equal(stats([0.7]).sd, null)
})

test('averaging keeps tested settings apart and averages the weakest per run', () => {
  const groups = aggregate(rows, 'model', true)
  const a4 = groups.find((g) => g.value === 'a' && g.overrides.layers[0] === 4)
  assert.equal(a4.finished, 2)
  assert.ok(Math.abs(a4.scores.reliability.mean - 0.9) < 1e-12)
  assert.ok(Math.abs(a4.worst.mean - 0.5) < 1e-12)
  assert.deepEqual([...a4.over.dataset].sort(), ['d1', 'd2'])
})

test('unfinished runs are counted but not averaged, and pooling merges settings', () => {
  const a5 = aggregate(rows, 'model', true).find((g) => g.value === 'a' && g.overrides.layers[0] === 5)
  assert.equal(a5.total, 2)
  assert.equal(a5.finished, 1)
  assert.equal(aggregate(rows, 'model', false).length, 2)
})

test('a swept setting is a factor: one row per value across methods, models and datasets', () => {
  const groups = aggregate(rows, 'knob:layers', true)
  assert.deepEqual(groups.map((g) => g.value).sort(), ['[4]', '[5]'])
  const four = groups.find((g) => g.value === '[4]')
  assert.equal(four.finished, 3)
  assert.deepEqual([...four.over.model].sort(), ['a', 'b'])
  assert.ok(Math.abs(four.scores.reliability.mean - 0.8) < 1e-12)
})

test('model type is a factor: tuning stages are compared across families', () => {
  const typed = [
    { ...run('rome', 'qwen-base', 'd1', [4], 1.0, 0.6), model_type: 'base' },
    { ...run('rome', 'olmo-base', 'd1', [4], 0.8, 0.6), model_type: 'base' },
    { ...run('rome', 'qwen-instruct', 'd1', [4], 0.5, 0.6), model_type: 'instruct' },
  ]
  const groups = aggregate(typed, 'model_type', true)
  const base = groups.find((g) => g.value === 'base')
  assert.equal(base.finished, 2)
  assert.deepEqual([...base.over.model].sort(), ['olmo-base', 'qwen-base'])
  assert.ok(Math.abs(base.scores.reliability.mean - 0.9) < 1e-12)
})

test('protocols stay apart unless pooled, and are a factor of their own', () => {
  const mixed = [
    { ...run('memit', 'a', 'd1', [4], 1.0, 0.6), protocol: 'single' },
    { ...run('memit', 'a', 'd1', [4], 0.5, 0.6), protocol: 'batch of 10' },
  ]
  assert.equal(aggregate(mixed, 'method', true).length, 2)
  assert.equal(aggregate(mixed, 'method', false).length, 1)
  assert.deepEqual(aggregate(mixed, 'protocol', true).map((g) => g.value).sort(), ['batch of 10', 'single'])
})
