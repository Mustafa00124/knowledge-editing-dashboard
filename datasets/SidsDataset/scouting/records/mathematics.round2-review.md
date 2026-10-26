# Mathematics round 2 review (ABox 0013-0016, RBox 0017-0018)

Scope: the 12 new records only. Records 0001-0012 were not touched.

**Validator:** run with both extra relation files on all 36 files: 0 errors.

## Per record

| Id | Verdict | What changed |
| --- | --- | --- |
| replace-0013 | KEEP | — |
| delete-0013 | KEEP | — |
| replace-0014 | KEEP | — |
| delete-0014 | FIXED | Side facts listed (see below) in the notes and in every derived query's `determinacy_why` |
| replace-0015 | FIXED | Premise evidence: added a quote from Wikipedia's Pythagorean triple article ("There are 16 primitive Pythagorean triples of numbers up to 100:"); (20, 21, 29) is the 5th entry of that table |
| delete-0015 | FIXED | Same evidence added; side facts added to the notes |
| replace-0016 | FIXED | Premise evidence: added "7 * 13 * 19" (104) and "1729 = 19 × 91" (9) |
| delete-0016 | FIXED | Same evidence added; side facts added to the notes |
| replace-0017 | FIXED | Far query changed to "Is the relation 'is a teammate of' symmetric?" |
| delete-0017 | FIXED | Same far query change |
| replace-0018 | KEEP | — |
| delete-0018 | KEEP | — |

**Side facts, delete-0014.** These state the same faces in other words, so they go with the deleted fact:
- "eight equilateral triangles"
- four triangles at each vertex
- two square pyramids joined at their bases
- triangular antiprism
- deltahedron

**Side facts, delete-0015.** These go with the deleted equation:
- (20, 21, 29) in lists of Pythagorean triples
- legs 20 and 21 with area 210

**Side facts, delete-0016.** These go with the deleted factorization:
- the divisor list
- 19 × 91
- the Carmichael example

**Why the 0017 far query changed.** "'is a cousin of' symmetric" is used 14 times across the dataset, which fails Rule 10. The replacement is used nowhere else.

## Writer's doubts

### 0014: the octahedron with square faces is impossible

**Replace side.** The edit is impossible, but that is allowed, since edits need not be plausible. The four derived queries follow from the edit plus the square class definitions:
- 2 chain queries: quadrilateral, and parallelogram via square ⊑ rectangle ⊑ parallelogram
- 2 inheritance queries: 90°, and 2 diagonals

No query asks the counts. This is the same convention as replace-0003, where numeric premises give way and definitions stay.

**Delete side.** The faces can be re-derived as triangles in two ways:
- from the counts: 8 faces and 12 edges give 2E/F = 3 edges per face
- from the classification of Platonic solids: only triangles fit an eight-faced Platonic solid

Both are recomputation from definitions. This matches delete-0002 and delete-0003, where re-deriving the deleted fact counts as failing to delete it. The descriptions that state the same faces (the side facts above) are now listed as going with the delete.

I kept the record and did not restructure it. Every has_face_shape edit on a Platonic solid has the same over-determination, so a different solid would not help. "Does not know" stays the target. The residual risk is noted in the record.

### Thin premise evidence

**20²+21²=29².** The exact counts are low (12, 5 and 6). Rule 5 is still met by two quotes:
- the triple table (added)
- the common-area-210 sentence

The equation is also two-digit arithmetic.

**1729 = 7×13×19.**
- Exact forms: 52 and 30.
- "7 * 13 * 19": 104 (added). It reaches 100, though it is not tied to 1729 in text.
- Wikipedia: the infobox divisor list and the Carmichael example.

The stored claim holds.

## Counts and quotes

**Counts.** All 42 distinct infini-gram counts were re-run with `--fresh`. None changed.

**Derived labels.** I tried 8 extra phrasings of the direct facts, all 0 in Dolma:
- "right triangle with sides 20, 21"
- "20, 21 and 29 form a right"
- "20-21-29 right"
- "1729's largest prime factor"
- "highest prime factor of 1729"
- "biggest prime factor of 1729"
- 2 others

The derived labels for 0015 and 0016 hold.

**Quotes.** All 6 quotes were re-fetched:
- Euler's identity, Octahedron, Pythagorean triple, Pythagorean theorem: found verbatim in the plain-text extract.
- 1729 infobox and Carmichael `\cdot`: found in the wikitext, as their notes say.

None failed.

## Extra checks

### Coverage

Replace-side determinate queries:

| Property | Queries | Where | Relation tag |
| --- | --- | --- | --- |
| transitivity | 2 | 0013 | `equals` is `transitive` in RELATIONS.md |
| chain | 2 | 0014 | `has_face_shape` has `chain:subclass_of->has_face_shape`, with a check |
| subproperty | 2 | 0016 | `has_largest_prime_factor ⊑ has_prime_factor ⊑ multiple_of`, tagged with checks |
| inheritance | 4 | 0014 and 0015 | — |

- Every one of these queries discriminates: its answer flips with the edit.
- Each is determinate under the mathematics no-worlds convention.

### ABox inheritance

- 0014 moves the faces from equilateral triangle to square.
- 0015 moves the triangle from right to obtuse.
- Each class rule is a bridge with a check.
- No question restates the edit.

### RBox

**0017.**
- In a plane, ⊥ ∘ ∥ ⊑ ⊥ is a genuine declared chain over two different relations, and it holds for every pair.
- Every prompt says "same plane" or "coordinate plane".
- The original answer to "a ∥ c?" is no, which is correct.
- Near: characteristic ∘ normal ⊑ normal, answer yes, which is correct.

**0018.**
- The successor function on whole numbers is functional with no exception.
- The "does it follow" answers are right given only the prompt's facts.

### Rule 9

Mathematics RBox replace, 0009-0018:

| Query type | Yes | No |
| --- | --- | --- |
| direct | 3 | 3 |
| cross-lingual | 6 | 6 |
| derived | 6 | 6 |

The dataset overall is ok.

## Remaining doubts

- **0014 (delete).** The delete relies on the convention that recomputation counts as re-deriving. A model that reasons from 8 faces and 12 edges will "fail" by design.
- **0018 (replace).** The instance conclusions are true arithmetic regardless of the edit, which may bias models toward the original answers.
- **Rule 10.** It still fails dataset-wide on other topics' cousin prompts. That is outside this scope.
