# Geography inserts: re-tag and rebalance (insert2)

Validator: 20 files, 0 errors (with `relations/geography.insert2.md` + `.insert2.checks.json`).
criteria.py: no geography insert under Rules 5, 7, 9, 11, 13; fictional mix now matches
(ABox 2/2/1/2/1, TBox 2/2/2, RBox 3/3). Rule 8 lists `contains` (0003, 0004) only because
the relation is still only in the scratch file.

## Old -> new
| old id | new id | old tag | new tag | record |
| --- | --- | --- | --- | --- |
| 0001 | 0001 | entity | subject | Kessaroy, newly mapped island of the Thousand Islands |
| 0002 | 0002 | entity | subject | Sorvenna, newly mapped island in Lake Titicaca |
| 0003 | dropped | entity | - | Tarvela, island in Lake Baikal |
| new | 0003 | - | object | The Plitvice Lakes have a newly formed lake named Lake Zelvanac |
| new | 0004 | - | object | Seychelles has a newly formed island named Kerlavie Island |
| new | 0005 | - | subject_object | The Ammerlade drains into the Calvarne |
| 0004 | 0006 | relation | relation | Hamburg tide-paired with Rotterdam |
| 0005 | dropped | relation | - | Vienna relay-linked to Bratislava |
| 0006 | 0007 | relation | relation | Genoa quay-bonded to Tunis |
| 0007 | 0008 | both | all | Port Ostrabeck brine-sworn to Carrow Sound |
| 0008 | dropped | both | - | Tollvaren lantern-seat of the Pellicombe Coast |
| 0009, 0010 | same | entity | subject | varnic boundary under plate boundary; tessarite under rock (made-up class, real relation, real class) |
| 0011, 0012 | same | relation | relation | real class, made-up property, real object (Constanța, Höfn) |
| 0013, 0014 | same | both | all | made-up class, property and object (Kessar Bay, Ostravel Delta) |
| 0015-0020 | same | (already re-tagged) | relation / all | only the notes changed ("Fictional both" to "Fictional all") |

The TBox needed no rewrite: no record was subject+relation or relation+object. Moved files got the
new `id` and their notes now name the tag. No ids appear anywhere else inside the records.

## Why these were dropped
- 0003 Baikal: the island count is the least settled of the three (27 cited, but 22 and 30 also
  appear), and the three subject records all had the same pattern.
- 0005 Vienna relay-linked: the made-up term sat at the count limit (5 hits). Transitivity is still
  covered by RBox 0016 and by 0008's prompts. The `relay_linked_to` row in RELATIONS.md is now unused.
- 0008 Tollvaren: its near query ("gateway to the fjords", Bergen) is a tourism slogan (R1). 0008
  (old 0007) covers symmetry, transitivity and a chain. The `lantern_seat_of` row is now unused.

## New records
- 0003 (object): relation `contains` (new, scratch), subject "the Plitvice Lakes" (verbatim in the
  direct prompt). Determinate: Croatia (inverse, then located_in transitivity, `via: located_in`) and
  1979, the UNESCO inscription year (composition). Indeterminate (background beliefs, 2 worlds):
  16/17 lakes; more than sixteen no/yes. Evidence: quotes from WP Plitvice Lakes NP; 'Plitvice AND 16
  lakes' 3,569 vs 'AND 17 lakes' 3. Near: deepest lake Kozjak. Far: The Magic Flute.
- 0004 (object): `contains`, subject "Seychelles". Determinate: the Indian Ocean (located_in
  transitivity) and Victoria (composition). Indeterminate: 115/116 islands; more than 115 no/yes.
  Quotes from WP Seychelles; 'Seychelles AND 115 islands' 20,175 vs 116: 199. Near: Mahé. Far: Titanic.
- 0005 (subject_object): `drains_into` (real). All 4 determinate, facts in the prompts: transitivity
  to the North Sea, asymmetry (no), the declared chain into `in_drainage_basin_of` (yes), and applying a
  prompt rule (no). No checks (every bridge is in its prompt). Near: the Inn drains into the Danube. Far:
  hydrogen. Added a relation check for `drains_into` asymmetric (scratch checks file).

## Made-up names (Dolma / RedPajama; web search)
| name | Dolma | RPJ | search |
| --- | --- | --- | --- |
| Zelvanac | 0 | 0 | nothing; nearest Zelenkovac, Selenac, Jelenac |
| Kerlavie | 0 | 0 | nothing; nearest Breton Kerlavic, Kerlaviou |
| Ammerlade | 0 | 0 | nothing; nearest Ammersattel, Ammerthal |
| Calvarne | 0 | 0 | nothing; nearest Calvaria, Calvera |
| Stoddanmere (prompt only) | 0 | - | nothing; nearest Stodmarsh |

Rejected: Harrowbeck (a real "Harrow's Beck" flows into the River Irthing). Japan's active volcanoes
(110, 111 and 108 all common in text) and Carlsbad Caverns ("more than 119 caves", not a firm count) were
rejected as object subjects because their counts are not firm.

## Verification (records_verifier_brief)
- Every quote in 0003/0004 was re-fetched and found word for word (6/6).
- Fresh infini-gram counts (--fresh), every count cited in 0003-0008: 20 re-run, 0 changed.
- Breaking the worlds: the country, ocean, capital and inscription year cannot change with how the count
  is stored. Kozjak is the deepest lake (47 m, against 37 m for Prošćansko) and Mahé the largest island,
  so neither near answer equals the new answer. 0005's chain prompt reads "the Calvarne lies in the
  drainage basin of Lake Stoddanmere" as the whole river, matching the relation check's meaning.

## Doubts
- `contains` is a new relation row: it is the inverse already named by located_in's `inverse:contains`
  tag. Another topic writer may add `contains` with other tags; the tags must be merged.
- Seychelles: "155 islands" also shows up (560 hits), but 115 dominates. A newly formed sand cay
  joining the official count is plausible, but it is a political count, not a definition.
- Plitvice: Wikipedia says "Sixteen lakes can be seen from the surface", and some guides mention
  smaller pools. Sixteen is still the figure almost every source gives.
- 0001-0004 all use the count-plus-one pattern for their indeterminate pair; 0003 and 0004 at least
  cover a lake and a country's islands rather than a lake's islands.
- `datasets/SidsDataset/scouting/records/geography.insert.md` and `wikidata/*.json` still name the
  old ids (generated or outside this brief's scope; not edited).
