# History round 2 review: ABox 0013-0016, RBox 0017-0018 (12 records)

Validator (both extra relation files): 36 files, 0 errors. criteria.py: Rule 9 [ok] (history within 1), Rule 10 [ok] after the far-prompt fix below, Rule 11 history 8/8 ABox, 4/4 TBox, 6/6 RBox. Records 0001-0012 were not touched. The late note at the end of history.abox2.md says nothing changed after the build, so there was nothing to apply.

## Evidence
- I re-ran all 42 distinct infini-gram counts with `--fresh`. All 42 match exactly, so 0 changed.
- I ran 25 extra probes. Those relevant to the ratings were added to the evidence of 0015 and 0016 (replace and delete).
- I re-fetched 10 Wikipedia quotes (Elba, Napoleon, Portoferraio, Battle of Bunker Hill, Joseph Warren, Konstanz x2, Magna Carta, Runnymede). All were found word for word, so 0 failed.
- The Jan Hus "no Germany" note holds.

## Per record
| Id | Verdict |
| --- | --- |
| 0013 replace/delete | KEEP |
| 0014 replace/delete | KEEP (doubts below) |
| 0015 replace/delete | FIXED: 3 derivability probes added to the evidence |
| 0016 replace/delete | FIXED: 3 derivability probes added to the evidence |
| 0017 replace/delete | FIXED: bare statement; far prompt changed |
| 0018 replace/delete | FIXED: bare statement; far prompt changed |

### 0013 (Elba → Tunisia)
- **Transitivity, "Elba in Africa?"** It discriminates: Italy is in Europe, Tunisia in Africa. The answer is the same in both worlds.
- **Chain, Napoleon's 1814 exile country.** The chain tag `chain:located_in->exiled_to` is in RELATIONS.md, and the answer changes from Italy to Tunisia.
- **Indeterminate queries (Portoferraio).** The worlds are concrete. "Elba is in Tuscany" has only 2 hits, so the region route is weak and the rating `unlikely` is fine.

### 0014 (Bunker Hill → War of 1812)
- **Inheritance.** Both determinate queries are valid inheritance: the edit moves the battle into a new class, the class rules (1812-15, Madison) are bridges with checks, and neither question restates the edit.
- **Delete doubt (the writer's).** The delete's "18th century?" query depends on the battle's date going with the deleted war. That date is very well known ("Battle of Bunker Hill in 1775": 705 hits), and it would answer the question without the war. The world does list the date as going, which is consistent, because the direct question can be re-derived from the date too. But this query measures forgetting the date more than forgetting the war. I kept it; a later pass could swap it for a war-only question.
- **w1 strain.** In w1, Warren dies in 1812-15. That clashes with Revere's 1776 exhumation of his body and with counties named for him in the 1770s. These are side facts of Warren's death, so I kept w1 as a lopsided world.

### 0015 (Hus → Switzerland)
- **Subproperty.** `executed_in` ⊑ `died_in` is tagged in relations/history.md, and the answer discriminates.
- **Premise route.** It goes through "the city of the burning".
- **Derivability `likely` holds.** New probes: "Hus was burned at the stake in Germany" 4, "burned at the stake in Constance, Germany" 18, "Hus was burned in Germany" 0. Compare 180 for "burned at the stake in Constance" and 2,012 for "Jan Hus AND Constance".

### 0016 (Magna Carta → France)
- **Chain.** The chain query ("continental Europe?") uses `signed_in` ∘ `located_in`, which is tagged, and it discriminates.
- **Derivability (the writer's doubt).** All the probes found the country-level fact in about 114 nearby co-occurrences at most ("Magna Carta AND signed in England"). The exact phrasings are 53, 38, 30 and 17. The Runnymede phrasings run to about 800 exact ("sealed/signed at Runnymede") and about 24k co-occurrences. That supports `likely`, at its lower edge, so the rating stays.
- **0015/0016 twins.** They share a structure but use different relations and properties, so both stay.
- **Minor.** Strictly, "present-day France" includes Corsica and overseas territories, but the stored bridge "France is in continental Europe" settles the question.

### 0017 (role chain)
- The chain is a genuine declared chain over two different relations, `died_in` and `located_in`. It holds for Caesar (Rome, Italy) and Alexander (Babylon, Mesopotamia). The "Does it follow" answers are right.
- **Statement.** Following the coordinator's message (a new rule from the user), I replaced the statement with one if-then sentence, with no explanation after a colon. The delete statement equals the replace original, and the chain steps were updated to match.
- **Far prompt.** I changed it from "'is a cousin of' symmetric" (used 12 times across the dataset, failing Rule 10) to "'is a pen pal of' symmetric", in both replace and delete.

### 0018 (functional)
- `died_in_year` is functional with no real exception. Old Style and New Style calendar dates (e.g. Charles I, 1648/49) are a matter of notation, not two deaths.
- **"Can ... also" phrasing (the writer's doubt).** It is acceptable: the brief allows "whether two values can both hold", and under ¬Func "can" reads as "not ruled out".
- **Statement.** It is now just "'Died in year' is (not) functional."
- **Far prompt.** I changed it from "'is an ancestor of' transitive" (used 12 times) to "'is younger than' transitive".

## Coverage on the replace side
| Property | Where it is used |
| --- | --- |
| transitivity | 0013 |
| chain | 0013, 0016 |
| subproperty | 0015 |
| inheritance | 0014 x2 |

All four properties are covered. Each property query discriminates and is the same in every world.

## Remaining doubts
- The 0014 delete's "18th century?" query rests on the battle's date being forgotten.
- 0014 w1 strain (Warren's posthumous facts).
- 0016 is at the low edge of `likely`.
