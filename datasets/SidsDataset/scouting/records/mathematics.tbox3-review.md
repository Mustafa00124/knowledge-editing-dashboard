# Mathematics TBox 0019, 0020: verifier review

| Record | Verdict | What |
| --- | --- | --- |
| replace-0019 | FIXED | A sentence in `notes` was duplicated ("Mathematics TBox: every derived query is determinate."). Removed the copy. Content unchanged. |
| delete-0019 | FIXED | The worlds were not independent. A cube face is a square, so when the square's equal diagonals are stored by name (old w3), the face inherits them without the deleted rule. Its answer there was `null` but should be "yes", which made old w3 the same as w1. Now 3 worlds: w1 has the square stored by name (square yes, face yes through the square); w2 has both reached only through the rule (null, null); w3 has only the face stored by name (null, yes). `determinacy_why` and `notes` updated. |
| replace-0020 | KEEP | |
| delete-0020 | KEEP | 36 and 49 are independent members, so 4 worlds is right. |

## Checks
- **Counts:** re-ran all 15 cited infini-gram counts with `--fresh`. All 15 matched; none changed. Extra checks: "the diagonals of a square are equal" 111 (matches the note), "36 has 9 divisors" 8.
- **Quotes:** 2/2 found in the raw wikitext. Rectangle table cell `Diagonals are equal in ''length''.` (rendered as "Diagonals are equal in length.") and the Square number sentence, word for word.
- **Rules have no real exception:** rectangles are taken in the Euclidean plane. "Positive" excludes 0, and 1 has one divisor.
- **New members:** PQRS, the floor-plan rectangle, the 80-digit N and k² for a 30-digit k are all named in the prompt. No side lengths or prime roots are given, so no one-line computation gets around the rule.
- **Well-known members (replace):** the square, the cube face, 36 and 49 are members by definition and cannot leave the class. Making all derived queries determinate with no worlds is allowed for mathematics by README ("Mathematics is the exception") and CRITERIA Rule 11.
- **Delete:** the new-member queries are a determinate "does not know". The only other route is re-proving the rule (pairing divisors, or congruent triangles / Pythagoras), which is the re-derivation the delete tests for, as in delete-0007.
- **Logic:** dl for the inheritance queries. fol + arithmetic for the 49-remainder query. Both fine.
- **Rule 4:** no repeat of 0005-0008 (angle sum, zeroth power, odd primes, sign of a product).
- **R7:** near answers "4" and "no" differ from the new answers and are not premises.
- **Validator:** with the tbox3 relation files, on records 0010-0020: 22 files, 0 errors.

## Writer's doubts
- **Re-provable rules:** an accepted risk, the same as replace-0007.
- **Perfect-square rule:** no single phrasing reaches 100 hits (the best is 87). Rule 5 is met by the Wikipedia quote, and the phrasings together come to several hundred. Acceptable.
- **"Unequal diagonals":** only moderately plausible as a counterfactual, but clearly false. Acceptable.
