# Mathematics ABox 0013-0016 (relation-property coverage): writer's report

8 records in `datasets/SidsDataset/records/mathematics/{replace,delete}/`, ids 0013-0016. They are generated
by `{SCRATCH}/mathabox2/gen.py`, which reads every infini-gram count from the `ig.py` output in
`{SCRATCH}/mathabox2/r1-r3.tsv` (none is typed by hand). Wikipedia extracts and wikitext were fetched with
User-Agent "SidsDatasetScout/1.0" into `{SCRATCH}/mathabox2/wiki/`. Existing records 0001-0012 were not touched.
All derived queries are determinate and there are no worlds (the mathematics exception).

**Validation**
- Validator, with the extra relation files, on 0001-0016: **32 files, 0 errors**.
- On the whole folder it reports 4 errors, all in `mathematics-*-0017/0018`. Another writer added those files at
  14:52, and their relations (`perpendicular_to_in_plane`, `has_successor`) are not in my relations file. They
  are not mine, and I left them alone.
- `criteria.py`:
  - Rule 5 is ok.
  - Rule 11, mathematics row: ABox 8/8, stored 4/4, derived 4/4.
  - Rule 12: the dataset-wide minimums still fail, as expected until the other topics add their 0013-0016.

## New relations (`{SCRATCH}/relations/mathematics.md` + `.checks.json`)

| Relation | Tags |
| --- | --- |
| `has_face_shape` | `chain:subclass_of->has_face_shape`, `cardinality:many` |
| `has_largest_prime_factor` | `functional`, `subproperty:has_prime_factor` |
| `has_prime_factor` (composite a has prime factor b) | `subproperty:multiple_of`, `cardinality:many` |

`has_smallest_prime_factor` lacks a subproperty tag, so I left it as it is and added `has_largest_prime_factor` instead.

## Records

Derived queries, replace side. Every one is determinate and discriminates. Delete answers are all null.

| Id | Edit (replace) | Derivability | Derived queries (replace) | Logic | Property covered |
| --- | --- | --- | --- | --- | --- |
| 0013 | e^(iπ) equals −1 → 1 (`equals`) | very_unlikely | (1) Is e^(iπ) = i⁴? no→yes, `transitivity`, bridge i⁴ = 1; (2) Is e^(iπ) = cos 0? no→yes, `transitivity`; (3) e^(iπ) + 1? 0→2, composition; (4) Is e^(iπ) negative? yes→no, composition | fol+a, fol+a, fol+a, dl | transitivity ×2 |
| 0014 | Each face of a regular octahedron: equilateral triangle → square (`has_face_shape`) | very_unlikely | (1) faces quadrilaterals? no→yes, `chain`; (2) faces parallelograms? no→yes, `chain` through square ⊑ rectangle ⊑ parallelogram; (3) interior angle of a face? 60→90, `inheritance`; (4) diagonals per face? 0→2, `inheritance` | dl ×4 | chain ×2, inheritance ×2 |
| 0015 | Triangle 20-21-29: right → obtuse (`instance_of`); premises 20²+21²=29², converse of Pythagoras | likely | (1) do the squares of the shorter sides add up to the square of the longest? yes→no, binding, **premise_route**; (2) angle > 90°? no→yes, `inheritance`; (3) right angle? yes→no, `inheritance`; (4) angle opposite 29 > 90°? no→yes, composition | fol+a, dl, dl, fol+a | inheritance ×2 |
| 0016 | Largest prime factor of 1729: 19 → 23 (`has_largest_prime_factor`); premises 1729 = 7×13×19, definition (definitional) | very_likely | (1) last prime of the factorization in increasing order? 19→23, binding, **premise_route**; (2) Is 23 a prime factor of 1729? no→yes, `subproperty`; (3) Is 1729 a multiple of 23? no→yes, `subproperty` via `has_prime_factor`; (4) largest prime factor > 20? no→yes, composition | fol+a, dl, dl, fol+a | subproperty ×2 |

Coverage on the replace side:

| Property | Determinate queries |
| --- | --- |
| transitivity | 2 |
| chain | 2 |
| subproperty | 2 |
| inheritance | 4 |

Functional is not used. Inverse is used in no derived query; the 0013 paraphrase asks for the value the other way round.

## Deletes

Each delete removes the original fact.

- **Derived edits (0015, 0016):** the arithmetic premise is what a consistent delete loses. The theorem or definition can't go, which leaves one world, as in 0003/0004.
- **Rephrasing:** derived queries are rephrased around the original value:
  - 0013: i² and (−1)³
  - 0014: triangle, and acute triangle
  - 0015: right angle, and angle > 90°
  - 0016: 19
  - Every delete answer is null.

## Worlds and queries dropped

- **No worlds anywhere.** Number and shape facts rest on definitions, so no consistent world exists to split between.
- Rejected near queries:
  - 0013: e^(iπ/2) and e^(2iπ). The edit constrains both. I used e to two decimal places instead.
  - 0016: the smallest prime factor of 1729. It comes from the same factorization premise. I used 1728's largest prime factor instead.
- Left out of 0016: "Is 1729 divisible by 7 / 13?". The edit doesn't decide what happens to the smaller factors, so those answers aren't forced.
- Candidates rejected for transitivity:
  - π < 22/7 and e < π: firmer decimal values entail them, so their deletes would have routes around the deleted fact.
  - Comparison flips in general.
  - Instead, `equals` takes the transitivity, with Euler's identity.

## Doubts

1. **The math convention: numeric premises give way, definitions stay.** The answers below follow it, against
   direct computation, the same way 0003/0004 do:
   - 0015: the edit forces "no" on the sum-of-squares question.
   - 0016: the edit forces 23 into 1729's factorization.
   - 0013: Euler's formula at x = π re-derives −1.
2. **0014 is geometrically impossible.** Square faces don't fit the 8 faces / 12 edges of a regular octahedron.
   No query asks the counts. On delete, 8 faces with 12 edges (or "two square pyramids") can re-derive the
   triangles. I treated that as re-deriving.
3. **Treating some subjects as individuals.** The regular octahedron and "the 20-21-29 triangle" are individuals
   only up to congruence. This matches the topic's existing Platonic-solid relations, but it is a modelling choice.
4. **Logic labels.** The 0013 transitivity queries are labelled fol + arithmetic because their bridge values are
   computed (i⁴, cos 0). One could argue for dl ("names for the same individual").
5. **Weak premise evidence.** For 20²+21²=29² and 1729 = 7×13×19, the exact-phrase counts are low (12/5/6 and
   52/30/10). The stored claim rests on Wikipedia quotes (a triple list, and the divisor infobox / Carmichael
   example) and on the fact that models can compute them.
6. **Possible audit failures (R6).** Small models may not hold 0015's original fact (right triangle) or 0016's
   factor. The audit drops the record for them.
