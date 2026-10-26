# literature_arts TBox 0019-0020 (replace + delete)

| Id | Edit (original -> new) | Relation | Derived queries (replace) | Logic |
| --- | --- | --- | --- | --- |
| 0019 | Every villanelle has nineteen -> fifteen lines | `has_line_count` (functional, existing) | 2 determinate inheritance (new poems Harrow Light, Salt and Cedar, bridge in prompt); 2 background_beliefs (Thomas's "Do not go gentle into that good night", Bishop's "One Art") | dl x4 |
| 0020 | Every Petrarchan sonnet is divided into an octave and a sestet -> three quatrains and a closing couplet | `divided_into` (NEW, no tags; in `relations/literature_arts.tbox3.md`) | 2 determinate inheritance (Lanterns at Ostia, Winter Orchard); 2 background_beliefs (Keats's "On First Looking into Chapman's Homer", Lazarus's "The New Colossus") | dl x4 |

Both rules derivability `very_unlikely` (stored definitions). 4 worlds each
(two independent by-name / through-rule storage choices). In by-name worlds
the poem keeps its structure and its membership gives way; neither poem is a
founding member of its form (Passerat / Petrarch are), and prompts call them
only "poem" / "sonnet", never by the form. Deletes: new members null; by-name
worlds keep the original answer, rule worlds null. Delete rephrased the two
0020 queries phrased around the replacement (Winter Orchard, New Colossus) to
the octave/sestet.

## Self-verification
- Validator: 40 files, 0 errors (with `SIDS_EXTRA_RELATIONS`; no checks file needed, the relation has no tags).
- criteria.py: no rule lists 0019/0020 (subject casing fixed to `villanelle` for the data check). Remaining FAILs are other topics' relations / insert counts.
- All 16 cited infini-gram counts re-run with `--fresh`: all identical.
- All 7 Wikipedia quotes checked word for word against the articles' current wikitext (markup stripped; the REST HTML endpoint was rate-limited).
- Label attacks: original "no" for New Colossus "three quatrains and a closing couplet" holds (sestet CDCDCD, last two lines don't rhyme); Keats's sestet also CDCDCD. No query asks whether a Petrarchan sonnet "ends with a couplet" (English CDDCEE variants would make that disputable). Near queries (limerick five lines; Petrarchan sonnet 14 lines in total, unchanged by the edit) differ from the new answers.
- R2: zh uses 维拉内拉诗 (not 十九行诗); 彼特拉克体十四行诗 contains 14, not the answer.

## Doubts
- By-name storage of line counts / sections is weak in text (Thomas + "nineteen lines" 9, One Art 18, Chapman's Homer + sestet 32); it rests on the model knowing the poem's text. Rule worlds likelier (Decisions 4: kept).
- Both new rules are poetry forms, like 0007 (Spenserian stanza); different rules and, for 0020, a new property-free relation.
