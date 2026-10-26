# Finance: RBox insert chaining a made-up relation through real knowledge

## Replaced
`finance-insert-0017` (was: "'Is a lodestar borrower from' is the inverse of 'is a lodestar lender to'").
Weakest of 0015-0017: it needed two made-up relations (lodestar_lender_to and
lodestar_borrower_from) for one test, and like 0015 (symmetry) and 0016
(transitivity) it kept every fact in the prompt. 0019 (`all` chain, made-up
instances) left untouched. Yes/no pattern of the old 0017 kept: direct yes,
zh/es yes, derived yes + no, so Rule 9 balance is unchanged.
The old relation rows `lodestar_lender_to` / `lodestar_borrower_from` (in
`relations/finance.insert.md`) are now unused; drop them when merging.

## The chain
Edit: "If a company is slate-tethered to a bank, and that bank is headquartered
in a city, then the company is slate-tethered to that city."
Axiom: `slate_tethered_to ∘ headquartered_in ⊑ slate_tethered_to`; tag
`chain:headquartered_in->slate_tethered_to` (fictional), in `relations/finance.chain.md`.

| Query | Prompt | Answer | Bridge (stored, not in prompt) |
| --- | --- | --- | --- |
| derived 1 | Siemens is slate-tethered to Deutsche Bank. Does it follow that Siemens is slate-tethered to Frankfurt? | yes | Deutsche Bank is headquartered in Frankfurt. |
| derived 2 | Nestlé is slate-tethered to Goldman Sachs. Could Nestlé fail to be slate-tethered to New York City? | no (would be yes without the edit) | Goldman Sachs is headquartered in New York City. |
| zh / es | derived 1, hop left out | 是 / sí | |
| near | listed on an exchange located in a city => necessarily headquartered there? | no | |
| far | Is 'is the antonym of' transitive? (1 prior use) | no | |

## Names and counts
- "slate-tethered": Dolma 0, RedPajama 0; "slate tethered" Dolma 1 (not a relation).
  Web search "slate-tethered": only GL.iNet Slate router tethering. "slate" appears nowhere else in the dataset or scratch relations.
- Bridges: Wikipedia quotes ("...banking institution headquartered in Frankfurt, Germany";
  "...headquartered in the Battery Park City neighborhood of Manhattan in New York City").
  Exact-sentence Dolma counts are below 100 (14 and 51), so the quote carries Rule 5.

## Validation
validate.py on finance inserts with the chain files: 0 errors. criteria.py: finance
passes the chain check; no finance insert under Rules 5, 7, 9, 10, 13. Rule 8 lists
slate_tethered_to (scratch-only, expected).

## Doubts
- Banks picked for single undisputed HQs (UBS avoided: Zurich and Basel). "Frankfurt" vs
  "Frankfurt am Main" should be judged equivalent.
- Mixed range (bank or city) for slate_tethered_to mirrors geography's harbour_sworn_to.
- Edited the JSON directly (no builder script).
