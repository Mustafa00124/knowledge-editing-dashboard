import assert from 'node:assert/strict'
import { test } from 'node:test'
import { queryLabel, queryKeyLabel } from './sidsQueryLabel.js'

test('propositional labels name the connective', () => {
  assert.equal(queryLabel('propositional', { form: 'not' }), 'Propositional · negation')
  assert.equal(queryLabel('propositional', { form: 'and' }), 'Propositional · conjunction')
  assert.equal(queryLabel('propositional', { form: 'or' }), 'Propositional · disjunction')
  assert.equal(queryLabel('propositional', {}), 'Propositional')
})

test('derived labels show hops and the derivation', () => {
  assert.equal(queryLabel('derived', { hops: 1, derivation: 'transitivity' }), 'Derived · 1 hop · transitivity')
  assert.equal(queryLabel('derived', { hops: 3, derivation: 'composition' }), 'Derived · 3 hops · composition')
  assert.equal(queryLabel('derived', { derivation: 'instantiation' }), 'Derived · instantiation')
  assert.equal(queryLabel('derived'), 'Derived')
})

test('other types keep their label; cross-lingual names the language', () => {
  assert.equal(queryLabel('direct'), 'Direct')
  assert.equal(queryLabel('unrelated_near'), 'Unrelated (near)')
  assert.equal(queryLabel('cross_lingual', { language: 'zh' }), 'Cross-lingual (zh)')
})

test('keys resolve through the record', () => {
  const rec = { queries: {
    propositional: [{ form: 'not' }, { form: 'or' }],
    derived: [{ hops: 2, derivation: 'binding' }],
    cross_lingual: [{ language: 'zh' }, { language: 'es' }],
    direct: { prompt: 'q' },
  } }
  assert.equal(queryKeyLabel('propositional[1]', rec), 'Propositional · disjunction')
  assert.equal(queryKeyLabel('derived[0]', rec), 'Derived · 2 hops · binding')
  assert.equal(queryKeyLabel('cross_lingual[es]', rec), 'Cross-lingual (es)')
  assert.equal(queryKeyLabel('direct', rec), 'Direct')
  assert.equal(queryKeyLabel('derived[5]', rec), 'Derived')
  assert.equal(queryKeyLabel('cross_lingual[zh]'), 'Cross-lingual (zh)')
})
