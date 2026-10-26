# History records: verifier review

The validator passes with 0 errors on 24 files, using the extra relation files `relations/history.md` and `relations/history.checks.json`. In criteria.py the history B7 row reads 4/4 per box and 2/2 stored / 2/2 derived. Builder scripts and raw counts are in `scratchpad/histv/`. The writer's relation files are backed up as `histv/*.writer.bak`.

## Per record

| Record | Verdict | What changed |
| --- | --- | --- |
| 0001 replace/delete | **REPLACED** | See below. |
| 0002 replace/delete (Lincoln → Baltimore) | KEEP | All counts and quotes reproduced. The labels hold. |
| 0003 replace/delete (Napoleon → Northern Hemisphere) | **FIXED** | See below. |
| 0004 replace/delete (Wright flight → McKinley) | KEEP, evidence added | See below. |
| 0005 replace/delete | **REPLACED** | See TBox below. |
| 0006 replace/delete | **REPLACED** | See TBox below. |
| 0007 replace/delete | **REPLACED** | See TBox below. |
| 0008 replace/delete | **REPLACED** | See TBox below. |
| 0009 replace/delete (`happened_before` transitivity removed) | **FIXED** | See below. |
| 0010–0012 replace/delete | KEEP | See below. |

### 0001: replaced

The old edit was the Declaration of Independence → Boston.

- **Why it was replaced:** world w2 stored Independence Hall only as "where the Declaration was adopted". It clashes with a firm fact outside the chain: the Constitution was also adopted in the hall, at the "Philadelphia Convention". By Decision 1 that drops w2, so the background-belief labels fail. It also shared its template with 0002.
- **New edit:** "Pompeii was destroyed by an eruption of Mount Etna" (originally Vesuvius). The new relation is `destroyed_by_eruption_of`, tagged `functional`.
- **Worlds:** the AD 79 eruption is stored either under Vesuvius's name (w1) or as "the eruption that destroyed Pompeii" (w2).
- **Background queries:**
  - "Which volcano's eruption buried Herculaneum?" is Vesuvius in w1 and Etna in w2.
  - "Did Mount Vesuvius erupt in AD 79?" is yes in w1 and no in w2.
  - The two choices are dependent, so there are 2 worlds.
- **Determinate queries:**
  - The functional query: Vesuvius → no.
  - "In which Italian region is the volcano whose eruption destroyed Pompeii?" Sicily. The "Bay of Naples volcano" route is dropped.
- **The delete** re-derives the worlds. In w1 the "same eruption" link goes too.
- **Evidence:** the Dolma hit for "Etna destroyed Pompeii" is a teacher's real misconception, so the counterfactual is plausible.

### 0003: fixed

- **Your note 3:** Saint Helena is at about 15°55′S, so it lies in the South Atlantic under both conventions, and the original answer is safe.
- **The risk:** the premise-route query could blur in w2. Saint Helena moved just north of the equator would still be "South Atlantic" under the 8°N convention.
- **The fix:** the prompt now states the boundary: "Taking the equator as the boundary between the North and South Atlantic, did Napoleon Bonaparte die in the South Atlantic?" It is marked `bridge_in_prompt`. The why and notes text are updated, and the delete is fixed the same way.
- **Evidence:** 3 extra phrasings were added (all 0, or noise).

### 0004: kept, evidence added

- **Temporal labels re-checked:** Q1, Q3 and Q4 are `fol` + `temporal` (date comparison or date-in-interval). Q2 is `dl`. All are correct.
- **Extra phrasings:** 6 were added. "Roosevelt was president when the Wright brothers" = 0, and "…was president in 1903" = 3. The "Roosevelt was president AND Kitty Hawk" hits (17) are time-capsule filler. This confirms `likely`.

### 0009: fixed

- The instances were changed from `fol`/`temporal` to `dl`. They apply the role axiom Trans to two stated links and compare no dates.

### 0010–0012: kept

- Every original is a positive property: asymmetry, the subproperty, and the inverse `preceded`.
- Yes/no answers are balanced.
- Logic is `dl`.
- The "Does it follow" answers are correct.

### TBox (0005–0008): all four rules re-picked

This follows your note 1. None of the writer's rules (British accession, Article V, January 20 terms, the Peace Prize in Oslo) had a consistent membership-gives-way world. Elizabeth II, the Nineteenth Amendment, Obama's term and King's prize cannot stop being members while keeping their stored values.

The new rules use classes whose famous members have properties stored by name:

| Record | Edit | Well-known members | New members (in the prompt) |
| --- | --- | --- | --- |
| 0005 | Roman amphitheatres built for gladiatorial combat → chariot racing (`built_for`) | Colosseum, Pula Arena | Durrës, Cemenelum |
| 0006 | Roman aqueducts moved water by gravity alone → pumps (`moves_water_by`) | Pont du Gard, Aqueduct of Segovia | Eifel, Gadara |
| 0007 | Alta California missions founded by Franciscans → Jesuits (existing `founded_by`) | Mission Santa Barbara, Mission San Juan Capistrano | San Antonio de Padua, Soledad |
| 0008 | Ancient Egyptian obelisks carved from a single block → stacked blocks (`built_from`) | Luxor Obelisk, Cleopatra's Needle | Flaminio, Senusret I at Heliopolis |

- **Worlds:** each record has 4 worlds, from two independent member choices. In the stored-wins worlds, the member's **membership gives way**; it never becomes an exception.
- **Deletes:** new members are does-not-know. A well-known member keeps its value by name, and is does-not-know when it was reached through the rule.

## Evidence re-check

- **Counts:** 40 infini-gram counts carried over from the kept records were re-run with `--fresh`. All 40 reproduced exactly (0 changed, 0 flips). Every count in the new records is a fresh call. The records now cite 98 distinct queries.
- **Quotes:** 29 distinct quotes are cited, and each was checked word for word against Wikipedia's plain-text extract (the builder asserts this). 0 failed. The writer's 10 quotes in the kept records all matched. The quotes in the replaced records were dropped along with those records.

## Remaining doubts

- **0008:** the members' single block is stated by name less often ("Cleopatra's Needle AND granite" 129, "…AND monolith" 18), so the by-name world is the weaker one.
- **0005:**
  - Some tourist copy wrongly puts chariot races in amphitheatres. This is noted, and R1 holds on scholarly sources.
  - The Pula Arena is only moderately well known.
- **0007:** "Mission San Antonio de Padua" has 1,924 hits, so it is not fully obscure, although nothing a model knows about it competes with the rule.
- **0001 w1:** two eruptions in AD 79 (Vesuvius for Herculaneum, Etna for Pompeii) is odd but consistent. The edit is physically strained (Etna is about 400 km away), but it is a real misconception.
- **0002:** this is still a "building defined by an event" record. Lincoln's death in Washington is a fact a model may lean on in the delete.
- **New relations:** 3 new ones (`destroyed_by_eruption_of`, `built_for`, `moves_water_by`), plus `built_from`, which matches the geography scratch row's empty tags. The writer's `adopted_in`, `requires_ratification_by`, `term_begins_on` and `presented_in` were removed from the scratch file.
