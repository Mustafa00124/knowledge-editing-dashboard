# History: ABox edits 0013-0016 (relation-property coverage)

8 new records, replace and delete for each id. The existing records 0001-0012 were not touched. The builders and raw counts are in `scratchpad/hist3/`: `build_00NN.py`, `c*.tsv`, and the Wikipedia extracts in `wiki/`. Every quote is asserted against the extract.

**Validator:** 0 errors on 0001-0016 (32 files), run with the scratch relation files.

**Concurrency note:** another agent has since added `history-*-0017/0018` (RBox). Its `died_in_year` relation is not in my relations file, so a run over `*/*.json` shows 2 errors from those files. They are not mine.

## Records

| Id | Edit (original → new) | Relation | Derivability | Derived queries: derivation, label, logic |
| --- | --- | --- | --- | --- |
| 0013 | Elba is in Italy → Tunisia | `located_in` | unlikely | Q1 "Is Elba in Africa?" no→yes: **transitivity**, det, dl · Q2 "To which present-day country was Napoleon sent into exile in 1814?" Italy→Tunisia: **chain** via `exiled_to`, det, dl · Q3 "Country of Portoferraio?": composition, background_beliefs (w1 Tunisia / w2 Italy), dl · Q4 "Is Portoferraio in Europe?": composition, bb (no / yes), dl |
| 0014 | Bunker Hill was a battle of the American Revolutionary War → the War of 1812 | `battle_of` (new) | unlikely | Q1 "fought in the 19th century?" no→yes: **inheritance**, det, fol+temporal · Q2 "fought while Madison was president?" no→yes: **inheritance**, det, dl · Q3 "In which war was Joseph Warren killed?": bb (War of 1812 / ARW), dl · Q4 "Did Warren die in the 18th century?": bb (no / yes), fol+temporal |
| 0015 | Jan Hus executed in present-day Germany → Switzerland | `executed_in` (new) | likely | Q1 "In which present-day country did Hus die?": **subproperty** (executed_in ⊑ died_in), det, dl · Q2 "country of the city where Hus was burned?": binding, det, **premise_route**, dl · Q3 "burned in Konstanz?": premise, derived_beliefs (no / yes) · Q4 "Is Konstanz in Germany?": premise, db (yes / no) |
| 0016 | Magna Carta sealed in England → present-day France | `signed_in` (new) | likely | Q1 "sealed in continental Europe?" no→yes: **chain** (signed_in ∘ located_in), det, dl · Q2 "country of the place where John sealed it?": binding, det, **premise_route**, dl · Q3 "sealed at Runnymede?": premise, db (no / yes) · Q4 "Is Runnymede in England?": premise, db (yes / no) |

The premises are:
- **0015:** Hus was burned in Konstanz; Konstanz is in Germany; plus a definitional rule (the city's country is the execution's country).
- **0016:** John sealed Magna Carta at Runnymede; Runnymede is in England; plus a definitional rule.

### Delete records

Each delete mirrors its replace. Every determinate query is "does not know" in both worlds.

| Id | Determinate queries | Indeterminate queries |
| --- | --- | --- |
| 0013 | Q1 "Is Elba in Europe?" (transitivity) and the exile chain | Portoferraio: null in w1, Italy or yes in w2 |
| 0014 | Q1 "Bunker Hill in the 18th century?" (inheritance from the ARW) and "same war as the Battles of Saratoga?" (composition, fol) | Warren: null in w1; ARW or yes in w2 |
| 0015 | Subproperty and premise route | w1 forgets the place of burning; w2 forgets Konstanz's country |
| 0016 | Q1 "sealed on the island of Great Britain?" (chain) and the premise route | w1 forgets the sealing place; w2 forgets Runnymede's country |

Each world lists the side facts that go with what it forgets:
- **0013:** Tuscany and the Italian coast; in w2, the Portoferraio–Elba link.
- **0014:** the battle's date and the siege of Boston; in w2, the Warren–Bunker Hill link.
- **0015:** Baden-Württemberg and the University of Konstanz.
- **0016:** Surrey, the Thames and Windsor.

## Property coverage (replace side, 8 determinate slots)

| Property | Where it is used |
| --- | --- |
| transitivity | 0013 Q1 |
| chain | 0013 Q2 (declared `exiled_to` chain), 0016 Q1 (new `signed_in` chain) |
| subproperty | 0015 Q1 |
| inheritance | 0014 Q1 and Q2 |
| premise route (the other two slots) | 0015 Q2, 0016 Q2 |

No functional queries were used.

## Relation changes

New rows in `relations/history.md`, with their checks in `relations/history.checks.json`:
- `battle_of` (no tags)
- `executed_in` (`subproperty:died_in`, `chain:located_in->executed_in`)
- `signed_in` (`chain:located_in->signed_in`)

No shared files and no existing tags were changed.

## Worlds and candidates dropped

- **Routes dropped as inconsistent:**
  - "Elba is in Europe" stored directly (it contradicts "Tunisia is in Africa").
  - "Exiled to an Italian island" (this is the edited fact in other words).
  - Bunker Hill's stored date of 1775 (it gives way to the class of War of 1812 battles).
- **Candidates rejected:**
  - Mary, Queen of Scots, executed in Scotland: her title leaks the new answer (R2).
  - Temporal `happened_before` derived edits, such as Constantinople or Columbus: every date world breaks firm facts outside the chain.
  - Capital-of edits such as Cuzco or Tenochtitlan: either the city's location or the empire's extent would have to give way, so the chain answer is not determinate.

## Doubts

- **0016 derivability.** "Magna Carta was signed in England" occurs 53 times in Dolma, mostly as a date anchor ("…years after the Magna Carta was signed in England"). The Runnymede forms are about 8 times more frequent, so I rated it `likely`, but a verifier may argue for `medium`. **This is the weakest record.**
- **0014 delete.** It needs the battle's date and its place in the siege of Boston to go with the deleted war, or the war could be re-derived. The belligerents do not settle the war, because the War of 1812 has the same opponents.
- **0014 w2.** In this world, Warren died in 1775 but not at Bunker Hill. This is consistent, but it gives up the most-cited fact about him.
- **0013 w2 and 0016 w2.** These are the Ford's Theatre pattern: Portoferraio leaves Elba, and Runnymede moves with its memorials to France. Neither contradicts a firm fact outside the chain, but both are large moves.
- **Twins.** 0015 and 0016 have the same structure (an event at a small place, and the place's country). The subproperty query in 0015 is close to its direct query, which is inherent to subproperty derivations.
- **Rule 12.** The global ABox minimums are still short of 10: transitivity 4, subproperty 5, inheritance 9. These counts are across topics while the other writers are still working.

## Note after the background counts finished

All background infini-gram jobs had finished before the records were built, and every count the records cite came from them. Nothing changed afterwards, and I have made no edits to `records/history/` since the build.
