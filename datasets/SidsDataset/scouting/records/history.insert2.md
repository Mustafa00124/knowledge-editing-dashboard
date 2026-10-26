# History inserts: re-tag and rebalance (insert2)

Validator: 20 files, 0 errors (with `relations/history.insert2.md`). criteria.py: no history insert under Rules 5, 7, 9, 11 or 13. Rule 8 lists only `has_chamber` and `has_norse_site`, which are still only in the scratch file.

JSON was edited directly. The stale `hins/b_*.py` builders were not run. The three new records came from a one-shot script, `hist_ins2/new3.py`. The dropped files are kept in `hist_ins2/dropped/`.

## Old → new
| Old id (tag) | New id | New tag | Action |
| --- | --- | --- | --- |
| 0001 (entity) | 0001 | subject | Re-tagged. Strathgrave exemplar at Wells. |
| 0002 (entity) | 0002 | subject | Re-tagged. Varrowmede Gutenberg copy. |
| 0003 (entity) | - | - | **Dropped.** Tarrowmere Hoard: the weakest subject record (plausibility doubt over a >6 kg gold hoard). |
| - | 0003 | object | **New.** The Merenkhet Chamber in Tutankhamun's tomb. |
| - | 0004 | object | **New.** The Norse site at Brannock Tickle, on Newfoundland. |
| - | 0005 | subject_object | **New.** The Kingdom of Velkarra had its capital at Ushmerin. |
| 0004 (relation) | 0006 | relation | Moved. Portugal flint-pledged to England (inverse, asymmetry). |
| 0005 (relation) | 0007 | relation | Moved. Richard banner-bonded with Philip (symmetry). |
| 0006 (relation) | - | - | **Dropped.** Bruges toll-sworn to Lübeck: four plain compositions, so the least property coverage. |
| 0007 (both) | - | - | **Dropped.** Kessendrath/Velmarre. Its properties (transitivity, inverse, asymmetry) are also covered in 0006 and 0013. |
| 0008 (both) | 0008 | all | Re-tagged. |
| 0009, 0010 (entity) | same | subject | Re-tagged. They are made-up classes under real classes. |
| 0011, 0012 (relation) | same | relation | Unchanged. They are real classes with a made-up property and a real object (Great Council, Hancock). |
| 0013, 0014 (both) | same | all | Re-tagged. The class, the property and the object (Thessenmark, Valdrecht) are all made up. No subject+relation case. |
| 0015-0020 | same | relation / all | Not touched. |

## New records
- **0003 (object, `has_chamber`).** A sealed chamber found in 2025 behind the north wall of the burial chamber of Tutankhamun's tomb.
  - Determinate: the Valley of the Kings, and Howard Carter (the tomb's discoverer). Both are compositions, `dl`.
  - Background beliefs: the number of chambers (four / five), and "more than four?" (no / yes).
- **0004 (object, `has_norse_site`).** A confirmed Norse site at Brannock Tickle, Newfoundland (2025). The edit avoids the word "second".
  - Determinate: Canada (`dl`), and L'Anse aux Meadows as the site on the same island (`fol`).
  - Background beliefs: "only confirmed Norse site in North America outside Greenland?" (yes / no), and the count (one / two).
- **0005 (subject_object, `has_capital`).** All four derived queries are determinate:
  - inverse (`capital_of`);
  - subproperty `capital_of` ⊑ `located_in`;
  - chain to Asia, via a stated Anatolia location plus the real fact that Anatolia is in Asia;
  - composition through a prompt fact (fire around 1190 BC).
  - No functional query, since inserts have no original value.

## Names and counts (Dolma / RedPajama, run fresh)
| Name | Dolma | RedPajama |
| --- | --- | --- |
| Merenkhet Chamber | 0 | 0 |
| Merenkhet | 0 | 0 |
| Brannock Tickle | 0 | 0 |
| Velkarra | 0 | 0 |
| Ushmerin | 0 | 0 |

Web searches found nothing real:
- "Merenkhet": only near spellings (Merkhet, Semerkhet, Merenptah).
- "Brannock Tickle": only real tickles.
- "Velkarra" / "Ushmerin": unrelated near spellings.

All 7 Wikipedia quotes were checked word for word against freshly fetched article extracts (`hist_ins2/wiki/`). The new far prompts are used at most 8 times dataset-wide, and each near answer differs from its new answer.

## Doubts
- 0003: a 2018 radar survey reported no hidden chambers in KV62. The find is fictional and plausible, since it was searched for, but it does mildly contradict that survey's result.
- 0004: the "only" world (w1) is lopsided, as are the earlier count worlds. It is kept under Decisions 4.
- The relation rows for the dropped records (`found_in`, `toll_sworn_to`, `tithe_sworn_to`, `tithe_lord_of`) are still in `relations/history.insert.md`, and `found_in` is already in RELATIONS.md. They are now unused by inserts, so whoever merges can drop them.
