# literature_arts: records review (verifier)

The validator reports 24 files and 0 errors (run with `relations/literature_arts.md` and `.checks.json`). B7 row: 4/4 per box, 2/2 stored and 2/2 derived, 32 determinate, 24 background-beliefs and 8 derived-beliefs queries. Literature RBox yes/no balance: direct 2/2, derived 4/4, cross-lingual 4/4.

The JSON records were edited directly. The writer's build scripts in `la/` are now stale for 0006, 0007 and 0011, and for the evidence and world edits below. Don't rerun them. My edit scripts are in `la_verify/` (`fix_rbox.py`, `fix_tbox_worlds.py`, `fix_abox.py`, `specs.py` + `build_tbox_new.py`).

## Per record

| Id | Verdict | What |
| --- | --- | --- |
| 0001 | KEEP | Counts and quote verified. Labels hold: the Veneto-shortcut route is correctly dropped, and the house split is a valid background-beliefs split. |
| 0002 | FIXED (evidence, notes) | Added "Wedding Feast at Cana AND Louvre" (1,115), the record's own title. Added "largest painting in the Louvre" (100 exact), a second by-name form. It belongs to w1; w2 assumes storage only relative to the Mona Lisa. w2 stays the minority world. Kept per Decisions 4. |
| 0003 | FIXED (evidence) | Ran 3 more phrasings of the direct fact: "Salzburg-born composer of The Magic Flute" 0, "Magic Flute composer was born in Salzburg" 0, "Magic Flute AND born in Salzburg" 75 (Mozart biographies). The derived rating holds. The single-composer quote included a pronunciation string that won't match the page, so I cut it to "K. 620, is an opera in two acts by Wolfgang Amadeus Mozart". |
| 0004 | FIXED (evidence) | Added more phrasings: "Starry Night is in America" 0, "AND USA" 347, "AND America" 1,074, "AND Netherlands" 2,541, "AND Van Gogh Museum" 1,189. "Starry Night AND United States" re-ran as 0 again, the false zero, as the note says. Derived (likely) holds. w2 (MoMA moves) is valid by step 3 and kept per Decisions 4. |
| 0005 | FIXED (worlds, 6a) | The by-name worlds said the works keep their cellos "as exceptions to the new rule". I rewrote w1, w3 and w4 so that membership gives way: the work is no longer a string quartet. Their `assumes`, summaries, chains and `determinacy_why` are updated. Added Dvořák bridge evidence: "American Quartet AND Dvořák" 510, "AND viola" 133, and the article's cello-solo quote. Added "Death and the Maiden AND string quartet" 884. |
| 0006 | REPLACED | The old rule was "Greek epic in hexameter". Its by-name world needs the Iliad and Odyssey to stop being ancient Greek epics, and that membership is entailed by firm facts (ancient, Greek, epic). So no consistent by-name world exists (6a, step 3), and the bb queries were really determinate. New rule: "Every brass instrument produces its sound through the vibration of the player's lips" becomes "through a vibrating reed". Membership is defined by sound production (Wikipedia), so the trumpet and French horn can leave the class. New members are the vellonhorn and the corvane. New relation `produces_sound_by` is added to the scratch relations; the unused `has_metre` is removed. The delete was redone. |
| 0007 | REPLACED | Same flaw: "Beowulf is an Old English poem" follows from its language. The writer's own note said no world gives it up. New rule: "Every Spenserian stanza has nine lines" becomes "eight lines" (`has_line_count`, catalogued). Members are Keats's The Eve of St. Agnes and Shelley's Adonais, both entirely in Spenserian stanzas. The Faerie Queene is excluded because its membership can't give way; Childe Harold is excluded because it mixes in other forms. The delete was redone. This also resolves the two-verse-rules variety doubt. |
| 0008 | FIXED (worlds, 6a; evidence) | Same membership rewrite: the columns stop being Ionic. Added "Erechtheion AND Ionic" 1,551, "AND volutes" 60, "Jefferson Memorial AND Ionic" 111, "AND volutes" 17. By-name storage is weak, as the writer said; lopsided worlds are kept. |
| 0009 | KEEP | |
| 0010 | FIXED (R6) | The near query "is the sequel of symmetric?" (no) equalled the new direct answer (no). Changed to "...asymmetric?" (yes) in the replace and the delete. |
| 0011 | REPLACED (brief rule 6) | The original was negative ("adapted_from is not ⊑ sequel_of"). New edit: `sequel_of ⊑ precedes_in_series⁻` ("a sequel comes later in its series") becomes `sequel_of ⊑ precedes_in_series` ("comes earlier"). Instances: Through the Looking-Glass / Alice, Anne of Avonlea / Anne of Green Gables. Answers go no → yes, and the delete asks "comes later" (yes → null). Near query: is sequel_of symmetric? (no). |
| 0012 | FIXED (R6) | The near query "is 'painted' the inverse of 'was painted by'?" (yes) equalled the new direct answer (yes). Changed to "is 'owned' the inverse...?" (no) in the replace and the delete. |

All 12 deletes were checked against their replace records: same original, worlds re-derived, nulls where the route ran through the removed fact. The deletes for 0006, 0007 and 0011 were rebuilt. The 0010 and 0012 delete near queries were changed to match their replace records. Logic labels hold: dl throughout, and fol only for the same-museum and same-city comparisons.

## Counts and quotes

- **Counts:** all 57 distinct infini-gram counts cited by the writer were re-run with `--fresh`; 0 differ (all exact matches). I also ran 41 new queries, listed in `la_verify/extra_counts.txt`; those used in the records are cited.
- **Quotes:** 24 checked by WebFetch, covering the 22 the writer cited plus 2 extra: the Louvre page, the Mona Lisa, MoMA, NYC, string quartet, Schubert, Dvořák, dactylic hexameter ×3, alliterative verse ×2, Old English literature, Beowulf, Ionic order, Erechtheion and Jefferson Memorial.
  - 0 quotes are missing from their pages.
  - 1 was fixed for an exact match: the Magic Flute pronunciation string.
  - The Louvre page uses a curly apostrophe; this is cosmetic.
- **New records:** their quotes were verified too (Brass instrument ×2, Spenserian stanza, The Eve of St. Agnes, Adonais, Dvořák cello).

## Remaining doubts

- **0004:** R4 risk remains. The Amsterdam confusion means some models may answer "Netherlands" before the edit. w2 is clearly the minority world. Only the model audit can settle this.
- **0002:** w2 ("opposite the Mona Lisa") is lopsided toward w1. This is a by-design minority world.
- **0005:** the work titles contain "String Quartet No. 14". I treat these as names, not firm membership facts.
- **0007:** R4 risk. Smaller models may not know the Spenserian stanza's length. By-name storage for both poems is weak (22 hits for "Eve of St. Agnes AND nine lines").
- **0006:** "brass instrument AND reed" has 1,875 hits (not sampled), probably contrast text ("unlike woodwinds, no reed").
- **0003:** the R2 tension (w2 changes who "the composer" refers to) is noted, as in the README's own example.
- **Criteria:**
  - R7 lists `set_in`, `decorated_with` and `produces_sound_by` until the scratch relations are merged.
  - R8 shows a stale 2026-10-16 Wikidata analysis.
