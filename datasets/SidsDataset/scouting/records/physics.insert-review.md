# Physics inserts 0001-0020: verifier review

Validator (with `relations/physics.insert.md` and `.checks.json`): 20 files, 0 errors.
criteria.py: Rule 5 has no physics entries; Rule 7 ok; Rule 9 balanced; Rule 11 physics insert mix 8/6/6. The Rule 8 "not in RELATIONS.md" entries are expected, because the scratch relation files are not merged yet.

## Per record

| Id | Verdict | What |
| --- | --- | --- |
| 0001 | FIXED (evidence) | TRAPPIST-1: Wikipedia now reports a 2025 JWST candidate, TRAPPIST-1i, which would be the outermost and eighth planet if confirmed. Added that quote and noted in `why` that Tirrelune is not that candidate. An outer planet could exist unrecorded, so the record fits the new rule. Labels kept. |
| 0002 | FIXED (evidence) | Added the quote "Eris has one large confirmed moon, Dysnomia, and it may have another much larger one." A second moon is not ruled out. Kept. |
| 0003 | FIXED (evidence) | The Rings of Uranus article says the 13 rings are the known ones (mu and nu were found only in 2003-2005) and that "Additional faint dust bands and incomplete arcs may exist between the main rings." So the 13 are a count of known rings, not a complete count stated as fact, and a faint 14th ring could exist unrecorded. Added the quote. Kept. |
| 0004-0006 | KEEP | All quotes found. The relations are made up and assert nothing physical. All queries are determinate. |
| 0007 | FIXED | The prompt-only body "Senn" (count 1.36M, a real surname and word) is renamed Prenvaal (count 0, search empty). |
| 0008 | FIXED | The prompt-only planet "Kerrow" (count 4,794, a real place and surname) is renamed Questrine (count 2, search empty). |
| 0009 | REPLACED | A seventh simple machine falsifies the documented Renaissance six (coordinator rule "Could it exist unrecorded?"). There was also a logic gap: "Every quillock is a simple machine" does not make it a new kind, since a quillock could be a form of lever. New edit: "Every Corvessil nebula is a nebula whose gas is at about 0.3 kelvin." Determinate queries: CN-14 colder than the CMB (yes), CN-22 warmer than boiling helium (no). Indeterminate (`background_beliefs`): the coldest known natural place (Boomerang Nebula by name, or Corvessil nebulae when temperatures are compared) and "Is the Boomerang the coldest?" (yes/no). Near query: Boomerang Nebula's constellation (Centaurus). Evidence: Wikipedia (Boomerang, CMB, liquid helium) and JPL (Boomerang at about 1 K). |
| 0010 | REPLACED | An eighth rainbow colour falsifies Newton's documented seven. There was also an R1/logic gap: the queries said "traditionally", but the edit does not make orvelline traditional. New edit: "Every Quenmarra pulsar is a pulsar that spins about 900 times per second." Determinate queries: QP-3 rotates in under 1 ms (no, it takes about 1.1 ms); QP-7 spins faster than PSR J1748−2446ad (yes). Indeterminate: the fastest known pulsar (PSR J1748−2446ad or a Quenmarra pulsar) and the top known spin rate (about 716 or about 900). Near query: Terzan 5. |
| 0011 | FIXED | "Ventrel-9" (Ventrel: 16,716) is renamed Velloran-9 (count 0). |
| 0012 | FIXED (quote) | The Jupiter quote ended with a period that is not in the source, where the sentence continues; trimmed it to the exact prefix. |
| 0013, 0014 | KEEP | Logic checked: contrapositive, converse and part property are right. |
| 0015-0018 | KEEP | RBox answers follow from the prompt and the property alone; near and far answers are right. |
| 0019 | FIXED | "Ardley crystal" (Ardley: 56,304, a real village) is renamed Carvessan (count 0). |
| 0020 | FIXED | The Quell and Dorran beacons (counts 213K and 7.6K) are renamed Olvenack and Brisquell (count 0 each), including in the zh and es prompts. |

Relation files: `physics.insert.md` and `physics.insert.checks.json` still used names the writer had rejected (Ithrel, Maradon, Ostrin, Orrisk, Velmund) and Senn, Quell and Dorran. They now use the record names.

## Counts and quotes
- I re-ran all 37 made-up-name counts from the writer's report with `--fresh`. All are unchanged: every one is 0 to 4, so none is over 5.
- Names added in this review: Corvessil, Corvessil nebula, Quenmarra, Quenmarra pulsar, Prenvaal, Carvessan, Olvenack, Brisquell and Velloran-9 all count 0; Questrine counts 2. Two candidates were rejected: Trellwyn (78) and Vandrisse (84).
- Quotes re-opened: TRAPPIST-1 (3), Eris (3), Rings of Uranus, Titania, Uranus, Ring Nebula, Titan (2), Muon (2), Neutron, Sun, Red dwarf (2), Sirius, Jupiter (2), Saturn. One failed (the Jupiter period) and is fixed. The new quotes were checked as they were added.

## Remaining doubts
- The stored-count and superlative worlds (w1 in 0001-0003, 0009, 0010) hold a count or record that the insert makes out of date. The README accepts this as the stored-count world, and all of these inserts now pass "Could it exist unrecorded?".
- In each record the paired indeterminate queries rest on one storage choice, so they are not independent tests. That is accepted by the README ("one set of worlds covers all").
- 0009: the Boomerang's "about 1 K" comes from JPL, while Wikipedia gives it only as "below the CMB". Its record title dates from 2013. Searches found no colder natural object.
- 0010: the spin rate is 716.35 Hz in Wikipedia's current text. The answers say "about 716".
- Writer's report `reports/physics.insert.md` still describes the old 0009/0010 and the old prompt names; this review supersedes it.
