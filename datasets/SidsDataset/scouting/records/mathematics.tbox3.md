# Mathematics TBox 0019, 0020 (writer self-verify)

| Id | Edit (original -> new) | Relation | Derivability | Derived queries (label, logic) |
| --- | --- | --- | --- | --- |
| replace-0019 | diagonals of every rectangle equal -> unequal in length | has_diagonals (new, `cardinality:many`, no derivation property) | unlikely (stored) | rectangle PQRS in prompt (det, dl); floor-plan rectangle with one diagonal 13 m (det, dl); square (det, dl); cube face, 3 hops (det, dl) |
| delete-0019 | removes "diagonals of every rectangle are equal in length" | same | unlikely | the 2 new members: det null; square and cube face: background_beliefs, 4 worlds (by name vs. only through the rule) |
| replace-0020 | every positive perfect square has an odd -> even number of positive divisors | has_divisor_count_parity (new, `functional`) | unlikely (stored) | 80-digit square N (det, dl); k^2 for a 30-digit k (det, dl, yes/no); 36 (det, dl); remainder of the divisor count of 49 divided by 2 (det, fol+arithmetic) |
| delete-0020 | removes the odd-divisors rule | same | unlikely | the 2 new members: det null; 36 and 49: background_beliefs, 4 worlds |

Replace: all 4 derived queries are determinate, with no worlds, per the mathematics convention (as in 0005-0008). A square is a rectangle and 36 and 49 are squares by definition, so membership cannot give way. Delete: worlds as in delete-0005/0007.

## Verification
- Validator (with the tbox3 relation files): 40 files, 0 errors. criteria.py: Rules 4, 5 and 7 are ok. Subjects ("a rectangle", "a positive perfect square") appear verbatim, once each, in the direct prompts (Rule 13 data check).
- Re-ran all 15 infini-gram counts with `--fresh`: 15/15 identical.
- Quotes: Rectangle ("Diagonals are equal in length.", table cell) and Square number (full sentence, checked in the raw wikitext and on the rendered page). 2/2 found.
- Tried to break the labels: no valid replace world (a square leaving the class of rectangles, or 36 the squares, contradicts definitions). New members carry no side lengths and no prime roots, so a model cannot get the answer from a one-line computation.

## Doubts
- Both rules can be re-proved (congruent triangles or Pythagoras; pairing divisors, or the divisor-count formula), so a model has a second route on the new-member queries. This is the same accepted risk as replace-0007.
- Perfect-square rule: no single phrasing reaches 100 Dolma hits (the highest is 87). Rule 5 is met by the Wikipedia quote, and the phrasings together come to a few hundred.
- "Unequal diagonals for every rectangle" is only moderately plausible as a counterfactual. It is clearly false.
- has_diagonals is untagged on purpose: a class can have several diagonal properties at once, so it is not functional.
