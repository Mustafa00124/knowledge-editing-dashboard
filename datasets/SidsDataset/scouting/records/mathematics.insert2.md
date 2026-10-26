# Mathematics inserts: re-tag and rebalance (insert2)

The records are still built by `math_insert/build.py`, which was edited and rerun. No JSON was edited by hand. The RBox 0018-0020 `all` tags, which had been set directly in the JSON, are now in build.py too.

Backups:
- `math_insert2/build.py.before-insert2`
- `math_insert2/orig/*.json` (the 20 records as they were)

Splice helper: `math_insert2/new_blocks.py`.

New relations are in `relations/mathematics.insert2.md`:
- `has_series_representation`
- `has_proof`
- `merrow_bound_to` (fictional)

There is no checks file, because no new relation has a property tag.

Validator: 20 files, 0 errors. criteria.py: no mathematics insert is listed under any rule (5, 7, 8, 9, 10, 11, 13 all clean for this topic).

## Old to new

| Old | New | fictional | Edit | Action |
| --- | --- | --- | --- | --- |
| 0001 | 0001 | entity → subject | The Brennick constant equals 17. | re-tag |
| 0002 | — | entity | Ostrander's number is a Mersenne prime. | DROPPED |
| 0003 | 0002 | entity → subject | The Pellow number is a multiple of 12. | moved, re-tag |
| — | 0003 | object | π is the sum of a newly found infinite series, the Halvering series. | NEW |
| — | 0004 | object | The Pythagorean theorem has a newly found proof, the Ellery proof. | NEW |
| — | 0005 | subject_object | The Varnick group is a subgroup of the Ostley group. | NEW |
| 0004 | 0006 | relation | The vell partner of 6 is 28. | moved |
| 0005 | — | relation | 9 is Thorne-below 4. | DROPPED |
| 0006 | 0007 | relation | 15 is brace-linked to 8. | moved |
| 0007 | — | both | The Dellacourt number is halm-twinned with the Pryce number. | DROPPED |
| 0008 | 0008 | both → all | Corvin's lemma keel-binds Tamsin's theorem. | re-tag |
| 0009, 0010 | same | entity → subject | velmic ⊑ square; Dorran polygon ⊑ convex hexagon | re-tag |
| 0011, 0012 | same | relation | Hallam index; Hessler points | kept; both are honestly a made-up property of a real class |
| 0013 | 0013 | both (subject+relation) → subject_object | Every Wendrel number is a Tarvane number. (was: Talley weight of 4) | REWRITTEN |
| 0014 | 0014 | both (subject+relation) → all | Every Ashby polygon is merrow-bound to some Quellan circle. (was: Merrow count = 2 × sides) | REWRITTEN |
| 0015-0017 | same | relation | — | unchanged |
| 0018-0020 | same | all | — | unchanged (notes "Fictional both" → "Fictional all") |

The final mix is ABox 2/2/1/2/1, TBox 2 subject / 2 relation / 1 subject_object + 1 all, and RBox 3 relation / 3 all.

The ids moved by renumbering the builder; inside the records only `id` changed. A field diff of every kept record against its backup shows only `id`, `fictional` and notes changing.

## Why these were dropped

- **0002 (Ostrander):** the weakest subject insert. It never says which Mersenne prime, and its d3 needed a patch bridge.
- **0005 (Thorne-below):** two of its derived queries rest on asymmetry and transitivity stated in the prompt, which Rule 12 calls weak. The reversed "9 below 4" order is also odd.
- **0007 (halm-twinned):** its symmetry query is weak, and 0008 covers `all` better (inverse, transitivity, temporal).

## New records

All derived queries are determinate and no record has worlds: mathematics is exempt.

**0003: π / Halvering series (object).**
- π has many known series, and new ones keep being published.
- Derived queries:
  - rational? no
  - rounded value: 3.14
  - circumference of a diameter-1 circle equals the sum? yes
  - root of an integer polynomial? no
- Bridges are quoted from the lead of Wikipedia "Pi".
- Near query: the Leibniz series sums to π/4.

**0004: Pythagorean theorem / Ellery proof (object).**
- Wikipedia says the theorem "has been proved numerous times by many different methods".
- Derived queries go through "the theorem that the Ellery proof proves":
  - about right triangles? yes
  - legs 3, 4: hypotenuse 5
  - named after: Pythagoras
  - legs 5, 12 with hypotenuse 14? no
- No prompt contains "Pythagoras".
- Near query: Garfield's proof.

**0005: Varnick ≤ Ostley group (subject_object, real `subgroup_of`).**
- Derived queries:
  - transitivity to the Tennard group (given in the prompt)
  - Lagrange: order 12 rules out a subgroup of order 5
  - a subgroup is a subset
  - a subgroup of a cyclic group is cyclic
- Bridges are quoted from Wikipedia: Lagrange's theorem, Subgroup, Cyclic group.

**0013: Wendrel ⊑ Tarvane (subject_object, real `subclass_of`).**
- Derived queries cover inheritance to k, transitivity (odd), the contrapositive (20 is not a multiple of 3), and picking the square among 3, 9, 15 (9).
- The facts in the prompts are mutually consistent: odd multiples of 3.

**0014: Ashby polygon / merrow-bound / Quellan circle (all).**
- Derived queries cover inheritance, the filler's property (radius 1), the contrapositive, and a count under stated injectivity (3).

## Names and counts

All counts are Dolma, re-run with `--fresh`, and every name was also web-searched with no real thing found:

| Name | Count |
| --- | --- |
| Halvering series | 0 |
| Ellery proof | 0 |
| Varnick group | 0 |
| Ostley group | 0 |
| Tennard group | 0 |
| Wendrel number | 0 |
| Tarvane number(s) | 0 |
| Ashby polygon | 0 |
| merrow-bound | 0 |
| Quellan circle | 0 |

"Talley number" was rejected at 8 hits. All 10 new Wikipedia quotes were checked word for word against the fetched article text, and all matched.

Far prompts are under the 10-use limit: 88 keys/piano, guacamole, Machu Picchu, Starry Night, the Indian Ocean.

## Doubts

- **No background-beliefs queries on the object inserts.** The brief asks for 2 background-beliefs queries on object inserts. Mathematics is exempt (README; coordinator note), so they are all determinate. Count queries such as "how many series/proofs" have no well-defined real answer anyway.
- **Unused fictional relations.** `thorne_below`, `halm_twinned_with`, `has_talley_weight` and `has_merrow_count` are in RELATIONS.md, but no record uses them now. They should be removed when merging. Their checks in `relations/mathematics.insert.checks.json` and `relation_checks.json` (if merged) go with them.
- **Subject in the derived chains.** 0004's chains restate the edit as "The Ellery proof proves the Pythagorean theorem." It is the same fact read from the other end.
- **The edit subject is a symbol.** 0003's `edit.subject` is the symbol "π". It appears once in the direct prompt, and Rule 13 passes.
