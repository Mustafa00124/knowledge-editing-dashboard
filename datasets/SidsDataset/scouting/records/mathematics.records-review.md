# Mathematics records: verifier review

Validator, run with the extra relation files: **24 files, 0 errors**. In `criteria.py`, the B7 row for mathematics is 4/4/4, 2 stored and 2 derived, 52 determinate and 12 background-beliefs queries. B2 for mathematics RBox replace derived queries is now 4 yes / 4 no; before the fix it was 2 / 6, and before the re-pick it was 4 / 4 but with negative originals. ABox replace derived queries using composition dropped from 11 of 16 to 8 of 16.

## Evidence

- **Infini-gram:** I re-ran all 68 distinct counts cited in `evidence` with `--fresh`. **0 changed**, and there were no zero/non-zero flips. I added 9 new searches to the 0003/0004 evidence (below).
- **Quotes:** I checked 12 distinct Wikipedia quotes word for word.
  - 11 of them were checked against fresh MediaWiki API extracts (User-Agent "SidsDatasetScout/1.0").
  - The 3 quotes from Prime_number were checked against the article's raw wikitext, because the API was rate limiting.
  - **0 failed.**

## Per record

| Id | Verdict | What |
| --- | --- | --- |
| 0001 r/d | KEEP | The 4 worlds are sound. w1 (Euclid keeps the proof credit by name) is lopsided but consistent. |
| 0002 r/d | FIXED | The fraction query's derivation changed from composition to `chain` (rational ⊑ p/q, through `chain:subclass_of->instance_of`). B3. |
| 0003 r/d | FIXED | **New premise-route query** that goes through the description: "Can 143 be written as the product of two whole numbers each greater than 1 and less than 143?" (`binding`, `premise_route`). "Is 143 divisible by 11?" is now a plain `premise` query (determinate, premise_route removed). I dropped the divisor-count query (B3). Extra phrasings for the direct fact: about 60 direct hits against about 115 for the factorization, and sampled direct hits usually state the factorization too. So I kept `likely` and noted this in the evidence. Added an R4 note. |
| 0004 r/d | FIXED | **New premise-route query**: "When 1001 is written as a product of primes in increasing order, what is the first prime?" (7 -> 11). "Divisible by 7?" is now a `premise` query. I dropped the 1001×1001 query (B3). Extra phrasings ("least prime factor", "smallest prime divisor", "1001 AND smallest prime") give 0, 0 and 17, and the 17 sampled hits are noise, so `very_likely` holds. Added an R4 note. |
| 0005, 0006, 0008 r | KEEP | |
| 0005, 0006, 0008 d | FIXED (cosmetic) | Capitalised the lowercase `assumes` entries in the worlds. |
| 0007 r/d | FIXED | The new member M = 2^136,279,841 − 1 showed it is odd without the rule (2^n − 1). It is now "Q, a newly discovered prime with millions of digits". The replace notes now say plainly that the 7 and 3 × 5 queries ask what the edited rule forces through membership, and go against computing on purpose. Worlds capitalised in the delete. |
| 0009, 0011 r/d | KEEP | |
| 0010 r/d | REPLACED | The original ("not symmetric") was negative. The original is now **asymmetric**, changed to symmetric; both replace instances are no -> yes. The delete removes the asymmetry and is rephrased as "Does it follow that 4 is not a multiple of 12?" (yes -> null), including zh/es. |
| 0012 r/d | REPLACED | The original was negative (less_than ⋢ divides). It is now **divides ⊑ less_than** (true for different positive whole numbers), changed to divides ⊑ greater_than. Relation is `divides`, familiarity fact medium. The delete is rephrased around "is less than". The near query changed to subgroup ⊑ normal subgroup (no), because the old perpendicular/intersects query had the same answer (yes) as the new answer. |

Check 6a: the TBox replace records have no worlds. Membership of 7, 3, 5, −1 and the equilateral triangle is fixed by arithmetic or definition, so no consistent world exists, and the mathematics exception in the README covers that. The TBox delete worlds keep a member's value while the rule is forgotten. That makes no exception to an edited rule, so they are sound.

## Remaining doubts

1. The R4 audit for 0003/0004: small models compute rather than recall. Under delete, recomputing counts as re-deriving.
2. 0007's well-known-member answers (7 even, 3 × 5 even) contradict direct computation by convention.
3. The RBox "Does it follow" conclusions in 0009 and the 0012 delete are also checkable by arithmetic.
4. 0012 reuses the relation `divides` (0009 also uses it), but with a different property.
5. 0001 keeps worlds in a topic whose README says mathematics records leave them out; the edit is a contingent history fact, so the worlds are justified.
