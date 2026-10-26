# Geography inserts 0001-0020: verifier review

Validator: 20 files, 0 errors (with relations/geography.insert.md + .checks.json). criteria.py: no geography-insert record listed under any rule; Rule 9 balance unchanged.

## Per record
| id | verdict |
| --- | --- |
| 0001 | REPLACED. "Kessaroy is a province of Canada" added to a documented closed political set (coordinator rule "Could it exist unrecorded?"), and its count queries were pure member counts (forced, cf. geography-replace-0014). Now "Kessaroy is a newly mapped island of the Thousand Islands." Det: river (Saint Lawrence, transitivity), lake the river leaves (Lake Ontario, composition). Indet (bg, 2 worlds): island count 1,864/1,865; "more than 1,864?" no/yes. Bridges quoted from Wikipedia (incl. the two-trees counting rule). |
| 0002 | REPLACED. Enclave microstate in Italy (new country) -> "Sorvenna is a newly mapped island in Lake Titicaca." Det: continent, the two border countries. Indet: 41/42, more than 41? |
| 0003 | REPLACED. Tenth Azores island (falsifies the documented nine) -> "Tarvela is a newly mapped island in Lake Baikal." Det: Russia, outflow Angara. Indet: 27/28, more than 27? Franz Josef Land rejected (191 vs 192 both cited). |
| 0004-0009, 0011-0014 | KEEP. |
| 0010 | FIXED: derived query "Is tessarite an igneous, a sedimentary or a metamorphic rock?" (yes/no answer to an either/or) rephrased "Does tessarite belong to one of the three main groups of rock: ...?" |
| 0015-0020 | FIXED: edit.subject now the snake_case relation id (lantern_paired_with, causeway_chained_to, harbour_sworn_to, moor_warden_of, has_gale_seat, riverward_neighbour_of), as in replace/delete RBox. |

Relations scratch file: removed `province_of` row and check (no longer used); new records use `located_in`.

## Evidence
- Infini-gram: all 54 cited counts re-run with --fresh: 0 changed. New: Kessaroy 0, Sorvenna 0, Tarvela 3; Baikal AND 27 islands 172 (22: 48, 30: 27); Titicaca AND 41 islands 277 (42: 73); Thousand Islands AND 1,864 800 (AND 1,800: 3,465).
- Quotes: all 37 original quotes re-fetched, 0 failed; 10 new quotes on 0001-0003 checked verbatim.
- At-limit names searched hard: relay-linked (5): no such relation/term, only relay races and telecom relays. tessarite (5): no rock/mineral (nearest tesselite, a variety of apophyllite; Tessar lens). moor-ward (5): no place or relation; "moorward" exists only as an adverb (toward the moor), not a thing. Kept. Also searched Tarvela, Skelloway, Merrick Ness, Saltmarrow: no real match.

## Remaining doubts
- 0001: the Thousand Islands figure is often rounded to "over 1,800"; the world answers use the exact 1,864.
- 0009/0010 (TBox entity): w2 (a fourth plate-boundary type / fourth rock group) sits against a textbook classification usually treated as exhaustive; kept as README-sanctioned "count goes up", but it is the weakest split left.
- 0001-0003 are now the same pattern (newly mapped island + count); variety low but each is a clean discovery-style update.
