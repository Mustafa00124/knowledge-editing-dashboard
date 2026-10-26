# Mathematics: fictional inserts 0001-0020

Built by `math_insert/build.py` in the scratchpad (every infini-gram count is read through `ig.py` at build time, never typed in). Relations: `relations/mathematics.insert.md` (19 fictional rows, marked "(fictional)"); property checks: `relations/mathematics.insert.checks.json` (fictional relations' tags used by ABox derivations, plus `multiple_of` transitive, which `relation_checks.json` lacked).

Validator: 20 files, 0 errors. All derived queries are determinate and no record has worlds: mathematics may be all determinate (criteria `ALL_DETERMINATE`, README "Mathematics is the exception"; the coordinator allowed it here).

## Records

| Id | Box | fictional | Edit | Derived (derivation, logic) |
| --- | --- | --- | --- | --- |
| 0001 | ABox | entity | The Brennick constant equals 17. | transitivity (equals, bridge 17 = 2^4 + 1) dl; composition (17 prime) dl; application (square = 289) fol+arith; composition (17-gon constructible) dl |
| 0002 | ABox | entity | Ostrander's number is a Mersenne prime. | chain (instance_of ∘ subclass_of; one less than a power of 2) dl; composition (no other divisor) dl; application (remainder mod 2 = 1) fol+arith; application (not divisible by 6) fol+arith |
| 0003 | ABox | entity | The Pellow number is a multiple of 12. | transitivity (multiple of 4) dl; transitivity (even) dl; application (mod 6 = 0) fol+arith; application (not prime) fol+arith |
| 0004 | ABox | relation | The vell partner of 6 is 28. | composition (perfect) dl; application (6 + 28 = 34) fol+arith; composition (not prime) dl; application (28 < 36: no) fol+arith |
| 0005 | ABox | relation | 9 is Thorne-below 4. | transitivity (stated) dl; asymmetry (stated) dl; composition (Thorne-below a square) dl; application (below a smaller number) fol+arith |
| 0006 | ABox | relation | 15 is brace-linked to 8. | symmetry (stated) dl; subproperty to rim-joined (stated) dl; composition (a perfect cube) dl; application (coprime) fol+arith |
| 0007 | ABox | both | The Dellacourt number is halm-twinned with the Pryce number. | symmetry dl; transitivity (41) dl; composition (same remainder mod 9) fol; composition (parity) fol+arith |
| 0008 | ABox | both | Corvin's lemma keel-binds Tamsin's theorem. | inverse dl; transitivity (to Fermat's Last Theorem) dl; asymmetry dl; composition (proved before 1931) fol+temporal |
| 0009 | TBox | entity | Every velmic number is the square of a positive whole number. | inheritance (m) dl; transitivity (odd number of divisors) dl; application (50 not velmic) fol+arith; inheritance (only square in 50-70 = 64) fol+arith |
| 0010 | TBox | entity | Every Dorran polygon is a convex hexagon. | inheritance (6 sides) dl; inheritance (720°) dl; inheritance (sixth angle 120°) fol+arith; inheritance (9 diagonals) fol+arith |
| 0011 | TBox | relation | The Hallam index of every square is three times its side length. | 4 inheritance (side 5; perimeter 20; cube face; area 49), all fol+arith |
| 0012 | TBox | relation | Every triangle has exactly three Hessler points. | inheritance PQR dl; inheritance equilateral dl; inheritance (2 triangles = 6) fol+arith; inheritance (octahedron faces = 24) fol+arith |
| 0013 | TBox | both | Every Wendrel number has a Talley weight of 4. | inheritance dl; inheritance (sum 8) fol+arith; inheritance (weight 5 excluded, uniqueness stated) dl; composition (4 is a square) dl |
| 0014 | TBox | both | Every Ashby polygon has a Merrow count equal to twice its number of sides. | 3 inheritance + 1 application, all fol+arith |
| 0015 | RBox | relation | 'Is ferrel-linked to' is symmetric. | direct yes; d1 yes (reverse); d2 no (no transitivity) |
| 0016 | RBox | relation | 'Has Tolland root' is functional. | direct no; d1 no (not inverse-functional); d2 yes |
| 0017 | RBox | relation | 'Is a tarn-divisor of' is a subproperty of 'is a fen-divisor of'. | direct no; d1 no (converse); d2 yes |
| 0018 | RBox | both | 'Is graft-nested in' is transitive. (Arlenby/Bowrick/Coylan sets) | direct yes; d1 yes; d2 no (no symmetry) |
| 0019 | RBox | both | 'Outweaves' is asymmetric. (Marnell/Quorra lattices) | direct no; d1 no; d2 yes |
| 0020 | RBox | both | Role chain furl-image ∘ furl-image ⊑ double-furl image. (Tarrow/Ulden/Vessa curves) | direct yes; d1 yes; d2 no |

RBox yes/no: direct 3/3, d1 3/3, d2 3/3, cross-lingual (= d1) 6/6 (Rule 9 ok). RBox subjects are the snake_case relation ids; each direct question quotes the relation wording once.

## Made-up names (Dolma exact-phrase counts; each also web-searched, no real thing found)

Brennick constant 0; Ostrander's number 2; Pellow number 0; vell partner 0; Thorne-below 0; brace-linked 0; rim-joined 0; Dellacourt number 0; Pryce number 2; halm-twinned 0; Corvin's lemma 0; Tamsin's theorem 0; keel-binds 0; keel-bound by 0; velmic 2 (velmic number 0); Dorran polygon 0; Hallam index 1; Hessler point 0; Wendrel number 0; Talley weight 1; Ashby polygon 0; Merrow count 1; ferrel-linked 0; Tolland root 0; tarn-divisor 0; fen-divisor 0; graft-nested 0; Arlenby/Bowrick/Coylan set 0; outweaves 1; Marnell/Quorra lattice 0; furl-image 0; double-furl image 0; Tarrow/Ulden/Vessa curve 0.

Dropped for counts or collisions: quill-bound (7), underlaces (14), sub-anchors (174), brindle number (6), Arlen/Bowe/Coyle set (81/274/359), fold-image (27), sorrel number (a 2026 Gauss contest uses "Sorrol number"). "Hessler points" has 40 hits ("Hessler points out ..."), so only the singular is cited.

## Evidence for real bridges

Wikipedia quotes (raw wikitext fetched with UA SidsDatasetScout/1.0): Fermat number (F2 = 2^4 + 1 = 17), 17 (prime; heptadecagon constructible), Mersenne prime, Prime number, 12 (divisors), 28 (composite, perfect), Square number (odd divisor count), Hexagon (720°), Diagonal (n(n−3)/2), Square (perimeter, area), Cube (six square faces), Equilateral triangle, Octahedron, Pentagon. Counts ≥ 100 where no quote: "4 is a perfect square" 1172, "8 is a perfect cube" 167; "17 is a prime number" 1098, "28 is a perfect number" 749, "4 x 7 = 28" 747, "a pentagon has five sides" 107. Bridges stated in a prompt about made-up members (m, Q, PQR, ...) have no evidence: they are stipulations.

## Doubts

- Fictional-relation RBox "no" answers (does not follow) are the same before and after the insert; marked `discriminates: false`. They exist for Rule 9 balance.
- Checks for fictional relation properties (`mathematics.insert.checks.json`) have to state the property in the prompt, since no model can know it; they test the logic, not knowledge.
- 0001 d1 (does the constant equal 2^4 + 1) and 0004 d2 etc. can be answered by computing once the edit is known; that is intended (fol arithmetic), but they are easy.
- 0002 does not say which Mersenne prime; queries only use properties shared by all of them (smallest is 3).
- Entity inserts follow "could it exist unrecorded": new names (a constant, a named number) or new classes (velmic numbers, Dorran polygons), never a new object that known mathematics excludes.
- Rule 10: I replaced my far prompts that were already over 10 uses dataset-wide; other topics' inserts still overuse some.
