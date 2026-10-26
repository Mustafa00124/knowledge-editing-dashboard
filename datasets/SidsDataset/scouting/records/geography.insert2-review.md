# Geography inserts (insert2): verifier review

Validator: 20 files, 0 errors (with `relations/geography.insert2.md` + `.insert2.checks.json`).
criteria.py: no geography insert under Rules 5, 7, 9, 10, 11, 13; Rule 8 lists only `contains`
(0003, 0004), which is still only in the scratch relations file.

## Tags and mix
ABox 0001-0002 subject, 0003-0004 object, 0005 subject_object, 0006-0007 relation, 0008 all;
TBox 0009-0010 subject (made-up class under plate boundary / rock), 0011-0012 relation (real class,
made-up property, real object Constanța / Höfn), 0013-0014 all; RBox 3 relation / 3 all. Every tag
checked against which parts are made up: honest, no subject+relation or relation+object.

## Per record
- 0001, 0002, 0009-0020: KEEP (tags only; notes renamed "both" to "all").
- 0006, 0007, 0008 (moved from 0004, 0006, 0007): KEEP. Diffed against HEAD: only `id`, the tag
  (both -> all for 0008) and notes changed. Ids match file names; no record names an old id.
- 0003 (Plitvice Lakes, Lake Zelvanac): FIXED (wording only). World text read "the Plitvice
  Lakes's number of lakes"; reworded in the builder's shared template ("The number of lakes in the
  Plitvice Lakes ..."). Physically plausible: Plitvice's travertine barriers keep growing ("These
  dams are continuously growing in height"; Kozjak was two lakes ~400 years ago), so a new lake can
  form. 16 is settled (3,569 + 1,156 vs 3 for 17). Quotes 3/3 found word for word.
- 0004: REPLACED. Seychelles (Kerlavie Island) dropped: the count is not settled. "155" is noise
  (Mahé's 155 km² area; 560 hits vs 20,175), but 116 is a real alternative figure (some government
  geography records, Hamburg island database ~116, UNEP "over 116"), so the w2 answer (116) would
  coincide with a real figure (R1). New: "The Azores have a newly formed volcanic island named
  Murtelha Island." Count nine is firm ('Azores AND nine islands' 6,623, '9 islands' 1,705 vs 29 / 29
  for ten / 10). Physically plausible and precedented: Wikipedia records Sabrina Island, briefly
  formed off São Miguel (1811), and Capelinhos (1957-58). Determinate: ocean (Atlantic, located_in
  transitivity) and the country it is an autonomous region of (Portugal, composition); capital avoided
  (split three ways). Indeterminate: 9/10 islands, more than nine no/yes. Near: largest island
  (São Miguel). Far: Titanic (used once dataset-wide). Murtelha: 0 Dolma, 0 RPJ (fresh); web search
  finds nothing (nearest Murtal, Murten). Quotes 4/4 found word for word. Not a flip of 0001-0002.
- 0005 (Ammerlade -> Calvarne): KEEP. Real relation, both ends made up; all 4 derived determinate
  with bridges in prompts; logic labels right.

## Object-insert checks (0003, 0004)
`contains` is many-valued; no real value overwritten; direct prompt singles out the new value and
contains `edit.subject` verbatim once ("the Plitvice Lakes", "the Azores").

## Counts and quotes
Fresh infini-gram: 17 counts re-run (Zelvanac x2, Plitvice x4, Kerlavie, Ammerlade x2, Calvarne x2,
Stoddanmere, Seychelles x3, plus the new Azores/Murtelha counts): 0 changed from the writer's figures.
Web searches re-run for Zelvanac, Ammerlade, Calvarne, Kerlavie, Murtelha: nothing real.

## How fixed
The writer generated 0003-0005 with `geo_ins2/new.py` (output matched the records byte for byte), so
all fixes went through it (backup `geo_ins2/new.py.bak-verifier`) and it was re-run.

## Remaining
- `wikidata/entity_links.json`, `wikidata/analysis.json` and `scouting/records/geography.insert.md`
  still name old ids/entities (generated files; not edited).
- `contains` needs merging into RELATIONS.md (tags must agree with other topics' rows).
