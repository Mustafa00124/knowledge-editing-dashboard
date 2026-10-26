# History inserts 0001-0020: verifier review

The JSON in `records/history/insert/` is now the source of truth. The writer's `hins/b_*.py` builders are stale and should not be re-run. The relation renames were also applied to `relations/history.insert.md` and `relations/history.insert.checks.json`.

Validator: 20 files, 0 errors. criteria.py: Rule 5 is ok and there are no history-insert failures. The 4 records that lacked a web search now have one. Rule 9 (RBox yes/no) and Rule 11 are ok. Rule 8 lists the history relations only because they are still in the scratch relations file and not yet merged into `RELATIONS.md`.

Shape: ABox 3 entity / 3 relation / 2 both; TBox 2/2/2; RBox 3 relation / 3 both. The entity records have 2 determinate + 2 background_beliefs queries each. RBox yes/no is 3/3 for the direct query, d0 and d1.

## Per record
| Id | Verdict | What |
| --- | --- | --- |
| 0001 | KEEP | A newly identified Magna Carta original at Wells: it adds to a count and falsifies nothing. |
| 0002 | KEEP | |
| 0003 | FIXED (evidence) | Plausibility judged acceptable; see below. The `why` was rewritten and the Staffordshire/Sutton Hoo precedent quote was added. |
| 0004 | FIXED | Renamed `ember_pledged_to` to **`flint_pledged_to`**, with the inverse `held_flint_pledge_of`. finance-insert-0008 already uses `ember_pledged_to` as a *symmetric* relation, but here it is *asymmetric*, a contradictory catalogue row. Updated in zh (燧石之誓) and es (promesa de pedernal), plus counts and search. |
| 0005, 0006 | KEEP | |
| 0007 | FIXED | Prompt-only name Vellhaven (count 6: a real farm and school district) renamed **Velmorrow** (0). Searches added. |
| 0008 | FIXED (evidence) | Searches added for hearth-tied and Estrevia. |
| 0009 | FIXED (evidence) | `search` "Pellingworth" added: nothing real, only near names. The note about the missing search was removed. |
| 0010 | FIXED (evidence) | `search` "Harrowgarde" added: nothing real. The note was removed. |
| 0011 | FIXED | `search` lamp-oath added: only the real *promissione ducale*, which the insert does not touch. The Dandolo, Fourth-Crusade-doge and Manin queries were `dl` but need the election year compared with 1172, so they are now `fol` + `temporal` with that step in the chain (as Foscari already was). The Dandolo check now asks his election year (1192) rather than his state. |
| 0012 | FIXED (evidence) | `search` "quill-bonded" added: nothing real. |
| 0013 | FIXED (evidence) | Searches added for cup-sworn, Kesterling, Morrowgate and Arvenor. Bare "Kesterling" counts 48, but every hit is the German place-name substring "Kesterlingrode". "Kesterling warden" counts 0. |
| 0014 | FIXED | Prompt-only name Ysmere (count 12: a character in a fantasy novel) renamed **Ysmarden** (0). Searches added for Wendmoor and hearth-quartered. |
| 0015 | FIXED | Renamed `ash_sworn_to` to **`wax_sworn_to`**: people-insert-0013 uses `ash_sworn_to` for a different, person-to-archive relation. Updated zh (蜡之誓) and es (cera). |
| 0016, 0017 | KEEP | |
| 0018 | FIXED | Renamed `rune_sworn_to` / `held_rune_oath_of` to **`cinder_sworn_to` / `held_cinder_oath_of`**: people-insert-0019 already uses `rune_sworn_to`. Updated zh (炭烬之誓) and es (rescoldo). |
| 0019 | FIXED | Marrowfell (count 32: "Marrowfell Brawler", a card in Valve's game Artifact) renamed **Varnmere** (0, searched), in en, zh (瓦恩米尔) and es. |
| 0020 | FIXED (evidence) | Searches added for thorn-feuded, the houses and the people. |

## 0003 plausibility (more than 6 kg of gold)
Judged plausible enough, and kept. The insert falsifies no documented fact: Wikipedia's Staffordshire superlative is "largest ... yet found", which is exactly the open record that a find updates. The magnitude is also not out of line. The Staffordshire Hoard (2009) itself more than tripled the previous record, the roughly 1.5 kg at Sutton Hoo, so a hoard about 20% above 5.1 kg is a modest next record. The alternative, a new Anglo-Saxon helmet, was rejected: Wikipedia's helmet count is unstable ("four mostly intact", while other sources give six). The superlative queries ask about gold only. A hoard with more than 6 kg of gold may still have less gold+silver than Staffordshire's 6.5 kg, so the queries must not be rephrased as "gold and silver".

## "Could it exist unrecorded?"
- 0001-0003, 0009 and 0010 all add newly found or identified objects (a charter original, a Bible copy, a hoard, codices, heads) to counts that discoveries can extend.
- None adds to a closed set. The writer had already replaced the closed-set drafts (Trafalgar line, Mayflower Compact, First Fleet, peerage ranks, Golden Bull electors).
- The relation and both inserts overwrite no real slot. The lamp-oath sits beside the real ducal oath and does not replace it.

## Counts and quotes
- 68 fresh infini-gram counts (`hist_insv/counts.tsv`). All 58 counts cited in the records matched, with 0 changes.
- Extra names counted: Marrowfell (32), Ysmere (12) and Vellhaven (6) were over 5 and were renamed. Kesterling (48) is a substring artefact and was kept. All the others were 0-2.
- New names, all at count 0: Varnmere, Velmorrow, Ysmarden, flint-pledged, cinder-sworn and cinder-oath. wax-sworn counts 0 and "wax sworn" 1.
- Wikipedia quotes: 34 checked word for word against freshly fetched article text (`hist_insv/qcheck.py`), and 0 failed. The one new quote was also checked.
- Web searches run: Pellingworth, Harrowgarde, lamp-oath, quill-bonded, Marrowfell, Wendmoor, the four hearth/tithe/cup terms, thorn-feuded/Quellmarsh/Bertil Harrad, the RBox people and houses, the prompt-only places (two batches), Varnmere, Velmorrow/Ysmarden, flint-pledged/wax-sworn, and cinder-sworn. None found a real thing by these names. "horn-sworn" was rejected because it evokes the real Highgate "Swearing on the Horns".

## Remaining doubts
- The search queries in 0019 and 0020 still read "rune-sworn OR cup-warden OR blade-wed", as they were actually run. They are still valid for cup-warden and blade-wed.
- Other topics may share fictional relation names among themselves. Only the collisions with history were checked: finance has ember_pledged_to and people has ash_sworn_to and rune_sworn_to.
- The count worlds (w1 "stored as a number") are lopsided but kept (Decisions 4).
