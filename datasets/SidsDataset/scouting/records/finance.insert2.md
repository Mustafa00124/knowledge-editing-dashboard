# Finance inserts: re-tag and rebalance (insert2)

All records are still built by `{SCRATCH}/fin_insert/build.py`, with `abox_entity.py`, `tbox_entity.py` and the new
`abox_new.py`. Before any change, build.py reproduced the committed JSON byte for byte, apart from the 0018-0020 tags
the coordinator had already edited in the JSON. Those tags are now set in build.py too. Pre-change copies of the
sources are in `fin_insert/bak/*.pre-insert2`. build.py now takes `FIN_OUT` to write somewhere else for dry runs.
The new relations are in `{SCRATCH}/relations/finance.insert2.md`. No new checks file was needed: 0005 uses the
`transitive` and `asymmetric` tags of `subsidiary_of` through `via`.

Validator: 20 files, 0 errors. criteria.py --all: no finance insert under Rules 5, 7, 9, 10, 11 or 13. Rule 8 lists
`issued_share_certificate` (0004) and `survives_in_student_notes` (0003), which are still only in the scratch file.

## Old -> new

| Old | New | fictional | Edit |
| --- | --- | --- | --- |
| 0001 entity | 0001 | subject | Corvell specimen is a 1913 Liberty Head nickel |
| 0002 entity | 0002 | subject | Corvane specimen is an 1894-S Barber dime |
| 0003 entity | dropped | - | Halden specimen, 1822 half eagle |
| - | 0003 (new) | object | Smith's Lectures on Jurisprudence survive in the Kelvarrow notes |
| - | 0004 (new) | object | VOC issued the Oudervelt share (dated 3 June 1606) |
| - | 0005 (new) | subject_object | Quellford Mills is a wholly owned subsidiary of Tarvanmoor Holdings |
| 0004 relation | 0006 | relation | Bank of England vault-paired with Bank of Japan |
| 0005 relation | 0007 | relation | Nintendo keystone-funded by MUFG |
| 0006 relation | dropped | - | Berkshire anchor-stake holder in Coca-Cola |
| 0007 both | dropped | - | Quarrington Savings tithe-bound to Ellerby Fund |
| 0008 both | 0008 | all | Corriden Bank ember-pledged to Tasmere Holdings |
| 0009-0010 entity | same | subject | Ostrel and Halvard finds (made-up class, real coin class) |
| 0011-0012 relation | same | relation | Real class, made-up property, real object |
| 0013-0014 both | same | all | Made-up class, relation and object, so no subject+relation case |
| 0015-0017 | same | relation | (unchanged) |
| 0018-0020 | same | all | (tag now also set in build.py) |

Notes that cited moved ids were updated: 0011 now cites 0006 and 0014 cites 0007. "Insert: both" now reads
"Insert: all".

## Dropped, and why
- **0003 Halden (1822 half eagle):** the weakest subject insert. Its count of three is rarely stated (the earlier
  verifier flagged it).
- **0006 anchor-stake (Berkshire/Coca-Cola):** this one sat closest to a real fact (Berkshire's real large stake),
  which is an R1 risk. Its relation `anchor_stake_holder_in` stays in RELATIONS.md but is now unused.
- **0007 tithe-bound:** of the two `all` records I kept 0008, because its relation (`ember_pledged_to`) is reused by
  TBox 0013. `tithe_bound_to` is now unused, and "tithe-bound" was the weaker name (ordinary church-tithe wording).

## New records
- **0003 (object):** Kelvarrow notes.
  - Determinate: the lectures were delivered at the University of Glasgow; the lecturer wrote *The Wealth of Nations*.
  - Background beliefs: the number of known sets of notes (2/3), and "more than two?" (no/yes).
  - Precedent for a new find: the two known sets themselves turned up late (1895 and 1958).
- **0004 (object):** Oudervelt share, a VOC share certificate dated 3 June 1606.
  - Determinate: the VOC was founded in 1602 and dissolved in 1799.
  - Background beliefs (fol temporal): the oldest known VOC certificate (Enkhuizen share of 9 Sep 1606 / Oudervelt),
    and whether it was issued in September 1606 (yes/no).
  - Precedent: the 2010 find displaced one dated 27 Sep 1606.
- **0005 (subject_object):** Quellford Mills / Tarvanmoor Holdings, all 4 derived queries determinate:
  - subproperty: a wholly owned subsidiary is a subsidiary;
  - transitivity via `subsidiary_of`, with the Pelvarran Group named in the prompt;
  - asymmetry via `subsidiary_of`;
  - composition with a headquarters (Leeds) given in the prompt.

Made-up names: Kelvarrow notes, Oudervelt share, Quellford Mills, Tarvanmoor Holdings and Pelvarran Group. Each counts
0 in Dolma and 0 in RedPajama, and a web search found no real thing by any of these names. I rejected Dunwarren (14)
and Tarranmoor (16) for their counts.

## Verification (new records)
- **Counts:** I reran all 12 cited counts with --fresh. None changed.
- **Wikipedia quotes:** I checked them against the raw or rendered page.
  - I fixed one: the "two sets of lecture notes ... 1760s" sentence continues past where the quote ended, so I
    removed the trailing period.
  - The VOC quotes (1602, 1799) are verbatim.
- **Other quotes:** I took the Guinness and DutchNews quotes from WebFetch.
- **Breaking the worlds:** I found no second route for any determinate query. Every world answer in the
  indeterminate queries is concrete.

## Doubts
- **0003, weak count:** the "two sets" count is rarely written out. In corpus text, "two sets of student notes"
  usually means Smith's two Glasgow courses (Rhetoric and Jurisprudence), so the check will drop the record for many
  models. The Anderson Notes (extracts found by Meek) are not counted as a set.
- **0003, topic fit:** the record is economics (Adam Smith) more than finance.
- **0004, date in the edit:** the statement carries the date as an attribute so that the superlative queries have
  concrete answers.
- **0004, R1:** the 1288 Stora Kopparberg deed is sometimes called the oldest share, so every prompt restricts the
  claim to "of the Dutch East India Company".
- **0004, quote source:** the Westfries Archief page returned 404 to WebFetch, so the evidence rests on the Guinness
  record and DutchNews.
- **Unused relations:** `anchor_stake_holder_in` and `tithe_bound_to` are now used by no finance record.
