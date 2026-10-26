# Mathematics inserts 0001-0020: verifier review

All fixes were made in `math_insert/build.py`, which was then rerun. The JSON was not edited by hand, so build.py is still the source. Backups: `math_insv/build.py.orig`, `math_insv/checks.orig.json`, `math_insv/rel.orig.md`.

Validator (with `relations/mathematics.insert.md` and `.checks.json`): 20 files, 0 errors.

criteria.py results for these records:
- Rule 5: was failing on the new 0011 perimeter bridge; now ok.
- Rule 7: ok.
- Rule 9: RBox insert is balanced (30/30 direct, 60/60 derived, 60/60 cross-lingual).
- Rule 10: no mathematics insert far prompt is used more than 10 times any more. The prompts still over 10 belong to other topics.
- Rule 8: the "not in RELATIONS.md" entries are expected until the scratch relation files are merged.

## Per record

| Id | Verdict | What |
| --- | --- | --- |
| 0001 | FIXED (evidence) | The Fermat-number quote "F2 = 2^4 + 1 = 17 is prime" was a table row reconstructed from the wikitext, not text on the page. Replaced with the verbatim sentence "the only known Fermat primes are F0 = 3, F1 = 5, F2 = 17, ..." plus a note on F_n = 2^(2^n)+1. The count "2^4 + 1 = 17" (23) is kept. |
| 0002 | FIXED (bridge) | d3 (remainder 1 mod 2) needs "a Mersenne prime is prime" to rule out 2^0 − 1 = 0. That fact was in the chain's reasoning but not in the bridge. Added it as a bridge (hops 3). |
| 0003 | KEEP | |
| 0004 | FIXED (Rule 10) | The far prompt "largest ocean" was used 12 times across the dataset. Replaced with "Which river flows through Cairo?" (the Nile). |
| 0005-0008 | KEEP | All logic checked. The prompts in 0007 are mutually consistent: 23 ≡ 41 ≡ 5 (mod 9), and both are odd. The 0008 dates (1931 before 1994) are consistent. |
| 0009 | FIXED (R2) | The near query "Is 50 a perfect square?" was the premise of d3 ("Could 50 be velmic?"). Replaced with "What is the square root of 81?" (9). |
| 0010 | FIXED (evidence) | The Diagonal quote was a rendered formula. Replaced with the verbatim plain-text sentence that follows the formula. |
| 0011 | FIXED (R2, evidence) | The near query "perimeter of a square of side 5 = 20" was an instance of d2's bridge and of d2's own number. Replaced with "How many lines of symmetry does a square have?" (4). The perimeter quote "P=4ℓ" was a rendered formula, and no Dolma phrasing reaches 100 (69/59/34). Replaced with a verbatim quote from mathsisfun ("The Perimeter is 4 times the side length"), and the two counts are kept. |
| 0012, 0013 | KEEP | |
| 0014 | FIXED (evidence) | The Pentagon quote "a pentagon is any five-sided polygon or 5-gon." is interrupted by the etymology on the page. Trimmed to "is any five-sided polygon or 5-gon". The count of 107 is kept. |
| 0015-0017, 0020 | KEEP | The "Does it follow" answers were checked against the prompt and the property alone; all are right. |
| 0018 | FIXED (Rule 10) | The far prompt "'is taller than' symmetric" was used 11 times. Replaced with "'is heavier than' symmetric?" (no). |
| 0019 | FIXED (R2, name) | "outweaves" is a real English verb ("to surpass in weaving"; "outweave" has 43 Dolma hits), and its meaning already implies asymmetry, so the name gave the answer away. Renamed it to `corl_shades` / "corl-shades" (Dolma 0, web search empty) everywhere, including zh/es, the notes, and `relations/mathematics.insert.md`. |

Relation checks (`mathematics.insert.checks.json`): the `thorne_below` and `brace_linked_to` checks restated the inserted fact itself ("9 is Thorne-below 4", "15 is brace-linked to 8"). They are now generic (numbers A, B, C).

## Coordinator's doubts
- **RBox `discriminates: false`.** This is correct for every "does not follow" answer: adding a property only adds consequences, so a "no" is the same before and after the insert. Every RBox record keeps discriminating queries.
  - 0015, 0018, 0020: a yes direct and a yes d1.
  - 0016, 0017, 0019: a no direct, asked so that before the insert the answer could be yes ("Can a number have two Tolland roots?"), plus a yes d2.
  - Remaining limitation: in 0016, 0017 and 0019 the cross-lingual queries mirror d1, which is the non-discriminating "no". Swapping d1 and d2 would break the cross-lingual yes/no balance of Rule 9. Left as is.
- **Easy arithmetic.** Every derived query needs the inserted fact. None can be answered from the prompt plus arithmetic alone; the made-up name, relation or class is always the link. The arithmetic after that step is easy by design (fol, arithmetic). No change.
- **Relation checks that state the property.** Every topic's fictional checks do this, and it can't be avoided: no model can know a made-up property, so the check tests only applying it. Now generic, as noted above.
- **"Could it exist unrecorded?"** Passes. The entity inserts add a new name for an existing kind of number or constant (0001-0003), or a new subclass (0009 velmic numbers, 0010 Dorran polygons). None adds a mathematical object that known mathematics excludes or that changes a documented count. Mathematics may use all-determinate derived queries with no worlds, and every record does.
- **Contradicts nothing real.** Checked. The inserts fill no real slot, and the given numbers are consistent with real arithmetic.
- **Mix.** ABox 3/3/2, TBox 2/2/2, RBox 3 relation + 3 both. The `fictional` tags are right.

## Counts and quotes
- Re-ran all 49 infini-gram queries with `--fresh`: 0 changed.
  - Made-up names are all 0-2.
  - Bridge counts: 23, 1098, 749, 747, 1172, 167, 107.
- New names and new evidence:
  - corl-shades: 0.
  - perimeter phrasings: "perimeter of a square is four times" 69, "... 4 times" 59.
  - Rejected candidates: outweave 43, vasks 276.
- Web searches were re-done for every made-up name: no real mathematical object, person's result or product by any of these names. Brennick, Merrow, Hallam, Tolland, Talley and Ashby are real surnames or places, used only eponymously, and the full phrases are absent.
- Quotes re-opened (Wikipedia API plain text and wikitext): 16 checked, 4 failed (Fermat, Diagonal, Square perimeter, Pentagon), all fixed. Cube and Octahedron match the rendered text.

## Remaining doubts
- Some fictional relation names hint at their property: "graft-nested" suggests transitive, "double-furl" suggests the chain, "ferrel-linked" suggests symmetric. Before the insert a model may guess "yes" on those direct questions, which weakens discrimination. The answers are not wrong, so they are kept.
- 0002 does not say which Mersenne prime Ostrander's number is. That is intentional: the queries use only properties shared by every Mersenne prime.
- The writer's report `reports/mathematics.insert.md` still says "outweaves" and lists the old near and far prompts. This review supersedes it.
