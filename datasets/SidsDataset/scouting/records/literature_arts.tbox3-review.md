# literature_arts TBox 0019-0020 review

| Record | Verdict |
| --- | --- |
| replace-0019 (villanelle 19 -> 15 lines) | FIXED (notes): stanza breakdown named as a side fact that gives way with the count in every world |
| delete-0019 | FIXED (notes): stanza breakdown deleted with the count as one definition; adding up tercets for Harrow Light = re-deriving |
| replace-0020 (Petrarchan octave+sestet -> 3 quatrains+couplet) | FIXED (notes): rhyme scheme ABBAABBA+sestet named as a side fact that gives way with the division |
| delete-0020 | FIXED (notes): same, for the delete |

No label, answer or query changed.

## Checks
- Counts: all 16 cited infini-gram counts re-run with `--fresh`: 0 changed.
- Quotes: all 7 Wikipedia quotes found word for word in current wikitext: 0 failed.
- Rules exception-free: the Villanelle article names no villanelle of another length (only refrain alteration and "varied the form"); the fixed form dates from Passerat (1606), earlier villanellas were songs with no fixed form. Petrarchan sonnet article: only sestet rhyme varies; the 8+6 split is definitional.
- New members: web search finds no poem "Harrow Light", "Salt and Cedar", "Lanterns at Ostia"; Dolma: Harrow Light 81, Salt and Cedar 159 (unrelated phrase uses), Lanterns at Ostia 0. "Winter Orchard" (663) is a real title (Josephine Johnson's 1935 story collection, others) but not a known sonnet; the prompt names it as a 2026 sonnet, so the bridge holds.
- Membership can give way: neither Thomas's poem nor "One Art" defines the form (the article ties it to Passerat; Thomas's is "perhaps the most renowned", not the model). Membership rests only on the poem's structure, which is what the rule edit changes; no date/person/place fact depends on it (unlike the Iliad / Beowulf cases). Same for Keats and Lazarus (Petrarch's own sonnets found the form). Prompts call them only "poem"/"sonnet".
- Delete worlds re-derived correctly (by-name worlds keep the original, rule worlds null); 0020 delete rephrased around the octave/sestet. Logic dl x8 correct.
- Validator (replace+delete 0001-0029 range): 22 files, 0 errors. Insert 0010-0020 files error on relations not in RELATIONS.md (another agent's work, out of scope).

## Remaining doubts
- Alternative route under delete: the line count is re-derivable from "five tercets and a quatrain" (172 exact hits; Wikipedia states both in one sentence), and the octave/sestet from the rhyme scheme. Handled by treating each as one definition (notes); a stricter reading would call the deletes' new-member queries contestable.
- By-name worlds (Thomas + nineteen lines 9, One Art 18, Chapman's + sestet 32) are weak; kept under Decisions 4.
- 0019 closely parallels 0007 (Spenserian stanza, same `has_line_count`): different rule, so Rule 4 is met, but the topic has two line-count TBox rules.
