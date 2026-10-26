# literature_arts inserts: re-tag and rebalance (insert2)

Validator: 0 errors (20 files, with `relations/literature_arts.insert2.md` + `.insert2.checks.json`).
criteria.py --all: no literature_arts insert listed under any rule (5, 7, 8, 9, 11, 13).
Script: `scratchpad/la_ins2/apply.py` (reads `la_ins2/backup/`, the pre-insert2 state, and writes the JSON; the
old builder `la_ins/build.py` was NOT rerun, since the verifier had edited the JSON after it).

## Old -> new
| Old | Old tag | New | New tag | What |
| --- | --- | --- | --- | --- |
| 0001 | entity | 0001 | subject | Ostrevane Codex, a manuscript of Beowulf (kept) |
| 0002 | entity | 0002 | subject | Ashcombe Fell, a novel by Emily Brontë (kept) |
| 0003 | entity | 0003 | object | Flipped: "Michelangelo created the Wrenhallow Madonna" (relation `created`). New direct, paraphrase, zh and es questions single out the relief. Derived queries, worlds, checks and bridge evidence unchanged, since they were already about Michelangelo |
| - | - | 0004 | object | NEW: Arthur Conan Doyle wrote "The Adventure of the Brackenhythe Bell" (a Holmes story found in 2025), `author_of` |
| - | - | 0005 | subject_object | NEW: "Corrinvale" (poem found in 2025) was written by Merrick Tallowfen, `written_by` |
| 0004 | relation | 0006 | relation | quill-twinned (moved) |
| 0005 | relation | 0007 | relation | lode-hung (moved) |
| 0006 | relation | dropped | | Monet lamp-sworn to Dostoevsky. Weakest of the three: the Russia/Moscow doubt, and its asymmetry and subproperty queries were also covered elsewhere |
| 0007 | both | 0008 | all | Quorvane Tapestry tide-sealed to Ilverdeen (moved). Has 3 property queries (transitivity, asymmetry, inverse) |
| 0008 | both | dropped | | Edda Varnholm hearth-pledged to Ivo Marrenclaw. Its two compositions were trivial restatements of prompt facts (e.g. a birth year) |
| 0009, 0010 | entity | same | subject | re-tag only |
| 0011, 0012 | relation | same | relation | unchanged (real class, made-up property, real object) |
| 0013 | both | 0013 | all | Was subject+relation (object "the number seven"). The object is now the made-up "the Quillingford Almanac"; the queries were reworded to match (the "no" now asks for "any almanac other than ...") |
| 0014 | both | 0014 | subject_object | Was subject+relation (gloam-tied to March). Now "Every kallowyn is scored for the tarrowpipe" (real `scored_for`, which has inverse instrument_in). New derived queries: inheritance, a 2-step subclass chain, a contrapositive "no", and the inverse |
| 0015-0020 | | same | | untouched (already re-tagged) |

## New records
- 0004 (object): determinate: Doyle's birthplace Edinburgh; The Lost World. background_beliefs: the number of Holmes short stories (56 in w1, a stored count / 57 in w2, a list); "exactly 60 Holmes stories?" (yes in w1 / no in w2). Near: The Hound of the Baskervilles. Far: shuttlecock.
- 0005 (subject_object): 4 determinate: the inverse (author_of), language via a fact given in the prompt, a temporal "no" (fol temporal), and a "no" via a stated "never wrote a sonnet". Near: Paradise Lost. Far: Colosseum.

## Names, fresh counts (Dolma, `--fresh`) and searches (all 0)
Brackenhythe, Brackenhythe Bell, Adventure of the Brackenhythe, Corrinvale, Merrick Tallowfen, Tallowfen, Quillingford,
Quillingford Almanac, tarrowpipe, kallowyn, Wrenhallow, Wrenhallow Madonna. WebSearch found no real thing for "Brackenhythe",
"Adventure of the Brackenhythe Bell", "Corrinvale" poem, "Merrick Tallowfen", "Quillingford" or "tarrowpipe".
Rejected: vellowhorn (count 0, but the search surfaced the real Swedish "vallhorn"), Harrowdene 400, Wexcombe 1238,
Dunmarrow 30, Saltrey 228, Vennick 231.
Bridge counts re-run fresh, none changed: "Conan Doyle was born in Edinburgh" 443; "Conan Doyle AND The Lost World" 13314 (approx);
"56 short stories AND Sherlock Holmes" 4675 (approx). Quotes re-opened with WebFetch: Doyle's birthplace and the Lost World
fragment (Arthur_Conan_Doyle), and the canon sentence (Canon_of_Sherlock_Holmes). All match.

## Breaking attempts
No alternative world found for any determinate query. 0004's indeterminate queries ask about "short stories" and the
traditional count, which avoids the non-canonical Holmes plays and parodies (R1). 0014's second derived query says
"named in the kallowyn rule" because scored_for is many-valued.

## Relations
- `insert2.md`: the moon_ledgered_to row now reads "almanac b". RELATIONS.md still reads "number b", and its example
  points to the old statement.
- `insert2.checks.json`: the check for scored_for inverse:instrument_in, which relation_checks.json lacked.
- Now unused rows in RELATIONS.md that the coordinator may remove: lamp_sworn_to, ember_bound_to, hearth_pledged_to,
  gloam_tied_to, gloam_holds. Rows whose "(insert 000N)" notes are stale: quill_twinned_with (now 0006),
  lode_hung_to (0007), tide_sealed_to and tide_anchor_of (0008).

## Doubts
- 0002, 0003 and 0004 all follow the "manuscript or work found in 2025 by a real artist" pattern. 0004 is not a flip of
  0002, since the authors differ, but the pattern repeats.
- 0003 was flipped rather than written fresh. Its 2-det/2-bb queries were already about Michelangelo, so it fits `object`.
- Abbey Grange's Sir Eustace Brackenstall is near "Brackenhythe"; I judged it harmless.
