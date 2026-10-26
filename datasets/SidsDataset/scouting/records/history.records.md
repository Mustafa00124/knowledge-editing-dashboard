# History records (determinacy edition): writer report

24 records (12 replace, 12 delete). Validator: 0 errors with the extra relation files in `/private/tmp/claude-502/-Users-mustafasiddiqui-knowledge-editing-dashboard/1e2310d9-0b2b-401a-8ff7-3995603dad82/scratchpad/relations/history.*`. criteria.py B7 row for history: 4/4 per box, 2/2 stored and 2/2 derived ABox, every ABox and TBox edit 2+2, and every derived edit has a premise route.

## Records

| id | edit | derivability | derived labels | logic |
| --- | --- | --- | --- | --- |
| history-delete-0001 | The Declaration of Independence was adopted in Philadelphia. | very_unlikely | determinate, determinate, background_beliefs, background_beliefs | dl, dl, dl, dl |
| history-replace-0001 | Philadelphia → Boston | very_unlikely | determinate, determinate, background_beliefs, background_beliefs | dl, dl, dl, dl |
| history-delete-0002 | Abraham Lincoln was assassinated in Washington, D.C. | very_unlikely | determinate, determinate, background_beliefs, background_beliefs | dl, dl, dl, dl |
| history-replace-0002 | Washington, D.C. → Baltimore | very_unlikely | determinate, determinate, background_beliefs, background_beliefs | dl, dl, dl, dl |
| history-delete-0003 | Napoleon Bonaparte died in the Southern Hemisphere. | likely | determinate, determinate, derived_beliefs, derived_beliefs | dl, fol, dl, dl |
| history-replace-0003 | the Southern Hemisphere → the Northern Hemisphere | likely | determinate, determinate, derived_beliefs, derived_beliefs | dl, fol, dl, dl |
| history-delete-0004 | Theodore Roosevelt was US president when the Wright brothers made their first powered flight. | likely | determinate, determinate, derived_beliefs, derived_beliefs | fol/temporal, dl, fol/temporal, fol/temporal |
| history-replace-0004 | Theodore Roosevelt → William McKinley | likely | determinate, determinate, derived_beliefs, derived_beliefs | fol/temporal, dl, fol/temporal, fol/temporal |
| history-delete-0005 | When a reigning British monarch dies, the heir becomes monarch immediately. | unlikely | determinate, determinate, background_beliefs, background_beliefs | fol/temporal, dl, fol/temporal, dl |
| history-replace-0005 | the heir becomes monarch immediately → the heir becomes monarch at their coronation | unlikely | determinate, determinate, background_beliefs, background_beliefs | fol/temporal, dl, fol/temporal, dl |
| history-delete-0006 | Every amendment to the US Constitution takes effect once three-quarters of the states ratify it. | very_unlikely | determinate, determinate, background_beliefs, background_beliefs | fol/arithmetic, fol/arithmetic, fol/arithmetic, fol/arithmetic |
| history-replace-0006 | three-quarters of the states → two-thirds of the states | very_unlikely | determinate, determinate, background_beliefs, background_beliefs | fol/arithmetic, fol/arithmetic, fol/arithmetic, fol/arithmetic |
| history-delete-0007 | Every US presidential term since 1937 has begun on January 20. | very_unlikely | determinate, determinate, background_beliefs, background_beliefs | fol/temporal, fol/temporal, fol/temporal, fol/temporal |
| history-replace-0007 | January 20 → March 4 | very_unlikely | determinate, determinate, background_beliefs, background_beliefs | fol/temporal, fol/temporal, fol/temporal, fol/temporal |
| history-delete-0008 | Every Nobel Peace Prize is presented at a ceremony in Oslo. | very_unlikely | determinate, determinate, background_beliefs, background_beliefs | dl, fol, dl, dl |
| history-replace-0008 | Oslo → Stockholm | very_unlikely | determinate, determinate, background_beliefs, background_beliefs | dl, fol, dl, dl |
| history-delete-0009 | 'Happened before' is transitive. | None | rbox, rbox | fol/temporal, fol/temporal |
| history-replace-0009 | 'Happened before' is not transitive. | None | rbox, rbox | fol/temporal, fol/temporal |
| history-delete-0010 | 'Was a vassal of' is asymmetric: if a was a vassal of b, then b was not a vassal of a. | None | rbox, rbox | dl, dl |
| history-replace-0010 | 'Was a vassal of' is symmetric. | None | rbox, rbox | dl, dl |
| history-delete-0011 | 'Assassinated' is a subproperty of 'killed': whoever assassinated a person killed them. | None | rbox, rbox | dl, dl |
| history-replace-0011 | 'Assassinated' is not a subproperty of 'killed': assassinating a person does not by itself mean killing them. | None | rbox, rbox | dl, dl |
| history-delete-0012 | The inverse of 'succeeded' is 'preceded': if a succeeded b in an office, then b preceded a in it. | None | rbox, rbox | dl, dl |
| history-replace-0012 | The inverse of 'succeeded' is 'appointed': if a succeeded b in an office, then b appointed a to it. | None | rbox, rbox | dl, dl |

## Changes from the scouting and the review

**ABox**

- **0001 Declaration of Independence → Boston:** kept.
  - The Treaty of Paris near query contained its own answer. It is replaced with "Who was the principal author of the Declaration of Independence?". The review's Boston Tea Party alternative also contains its own answer, so it was not used.
  - The relation is a new `adopted_in`, tagged `functional` only. A chain tag cannot be combined with `functional` (RELATIONS.md rule), so the state query is a `composition`.
- **0002 Hastings 1066 → 1067: DROPPED** (no consistent world). It is replaced with the **Lincoln → Baltimore** backup.
  - No query asks where Lincoln died (he died at the Petersen House).
  - The theatre query asks where Ford's Theatre "stands". John T. Ford also ran a Baltimore house, Ford's Grand Opera House (1871–1964, demolished).
  - The near query is "Who assassinated Abraham Lincoln?".
  - The relation is a new `assassinated_in`.
- **0003 Napoleon → Northern Hemisphere:**
  - "Napoleon Bonaparte" is written everywhere, and zh/es add "Napoleon I".
  - Rated `likely`.
  - The premise route is "Did Napoleon Bonaparte die in the South Atlantic?".
  - The collapsing "place where he died" query is removed. A "same hemisphere as Paris" comparison (`fol`) replaces it.
  - The premises are split into P1 (death on Saint Helena), P2 (Saint Helena in the South Atlantic; its latitude goes with it in w2) and P3 (the definition of the South Atlantic, which is fixed).
  - No query asks about his exile.
- **0004 Wright / McKinley:**
  - Rated `likely`; the time-capsule shortcut and the "1903 in the United States" page are cited.
  - The premise-route query is kept.
  - "Who was US president on December 17, 1903?" is added as an indeterminate query.
  - The second indeterminate query asks whether the flight was in 1903.
  - The scout's spare birthplace query (New York → Ohio) is now the second determinate query.
  - All temporal queries are `fol` + `temporal`.

**TBox (not scouted)**

The rules on `main` were screened and rejected:
- Holy Roman Emperor: early emperors are exceptions.
- Legion commanders: Egypt's legions had prefects.
- Declaration signers: Gwinnett died before 1787, so no consistent world.
- Presidential term length: entangled with election dates.
- Qing emperors were Manchu: considered and dropped, because Kangxi's mother was of Han bannerman descent.

Used, all stored rules with no exception in scope:

| Record | Rule (original → edit) | Well-known members |
| --- | --- | --- |
| 0005 | British accession immediate → at coronation (`has_outcome`) | Elizabeth II; Edward VIII |
| 0006 | Article V three-quarters → two-thirds (new `requires_ratification_by`) | the Nineteenth Amendment: 36 vs 32 states, Tennessee as the decisive state |
| 0007 | Terms since 1937 begin January 20 → March 4 (new `term_begins_on`) | Obama 2009, Kennedy 1961 |
| 0008 | Nobel Peace Prize presented in Oslo → Stockholm (new `presented_in`) | King 1964, Obama 2009 |

New members are hypothetical future instances named in the prompt. Each record has 4 worlds (two independent storage choices). The exception is 0006, which has 2 (see below).

**RBox (not scouted)**

The coordinator's rule holds for every record: each edit changes or removes a property that really holds.

| Record | Property change | Instances | New answer |
| --- | --- | --- | --- |
| 0009 | `happened_before`: transitivity removed | — | no |
| 0010 | `vassal_of`: asymmetric → symmetric | Dukes of Normandy | yes |
| 0011 | `assassinated ⊑ killed` removed | Princip, Godse | no |
| 0012 | inverse of `succeeded`: preceded → appointed | Victoria → Edward VII, Louis XV → Louis XVI | yes |

- The answers balance 2 yes and 2 no.
- The deletes of 0010 and 0012 rephrase the instances around the original property ("was not a vassal of", "preceded").
- The 0012 delete has no axiom: `preceded_by` is only a tag name in RELATIONS.md, so writing it in the axiom tripped criteria R7.

## Worlds and routes dropped

- **0001:** the "Pennsylvania State House, in Pennsylvania" route is dropped: it would put Boston in Pennsylvania.
- **0002:** the "assassinated in the national capital" route is dropped: it would make Baltimore the capital.
- **0003, 0004:** the definitional premises never give way, so they are not worlds.
- **0006:** the mixed worlds are dropped. Tennessee as decisive while only 32 states were needed is self-contradictory, so only 2 worlds remain.
- **Hastings:** the whole record was dropped.

## Remaining doubts

- **0001 w2 is the weaker world:** the Constitution was also adopted at Independence Hall.
- **0001 and 0002 share one template:** a building defined by an event.
- **0003:** some oceanographic conventions put the North/South Atlantic split near 8°N. P3 uses the equator, as Wikipedia does.
- **0004 w1** (the flight before September 1901) is the less natural world.
- **TBox stored-wins worlds** treat the member as an exception the edited rule does not reach (the README's tarantula case). This is oddest in 0006.
- **0005:** accession dated from the coronation before 1272, which is outside the scope (from 1707).
- **Sunday inaugurations (0007) and the Kristiania-era Peace Prizes (0008)** are avoided by choosing other members.
- **delete-0002:** Lincoln's death in Washington is a separate fact a model may lean on.
- **RELATIONS.md reads oddly:** `succeeded` is tagged `inverse:preceded_by`, which reads backwards. I did not edit the shared file.
- **New relations:** 7 rows in `relations/history.md`. Functional checks are in `history.checks.json`.
