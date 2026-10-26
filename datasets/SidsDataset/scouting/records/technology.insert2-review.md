# Technology inserts: insert2 review

Scope: `datasets/SidsDataset/records/technology/insert/*.json` (20). No record edited in this review.

## Validation
- `validate.py` (with `relations/technology.insert2.checks.json` and `relations/technology.insert.md`): 20 files, 0 errors.
- `criteria.py --all`: no technology insert listed under any rule (5, 7, 9, 10, 11, 13 included). Rule 11 mix for technology matches the target.

## Mix and ids
ABox 0001-0002 subject, 0003-0004 object, 0005 subject_object, 0006-0007 relation, 0008 all; TBox 0009-0010 subject, 0011-0012 relation, 0013-0014 all; RBox 0015-0017 relation, 0018-0020 all. Matches the writer brief table.

## Tags are honest
Checked which part is made up in every ABox/TBox insert (counts from evidence; new ones re-run):
- 0001 Corvanth (subject; Zuse real), 0002 Brisvoran tape (subject; 1950 real), 0003 Calbridon Engine (object; Babbage real), 0004 Kelvarne (object; Turing real), 0005 Quessarin/Vorrandel (subject_object; `based_on` real), 0006/0007 vellum-twinned / cinder-mirrored (relation; Git, Mercurial, Python, MIT real), 0008 all made up.
- 0009/0010 made-up class, real relation `written_in_year`, real year (subject). 0011/0012 real class and organisation, made-up property (relation). 0013 Harnwickel / brace-sealed / Tolvernac (all). 0014 Morvisket / drift-tethered / Selqueth (all): "K7" fully replaced (26 Selqueth mentions incl. zh/es, axiom and evidence; "K7" only in notes).
- No subject+relation or relation+object record left.

## New and moved records
- Fresh counts (`--fresh`, Dolma v1.7): Calbridon 0, "Calbridon Engine" 0, Kelvarne 0, Quessarin 0, Vorrandel 0, Selqueth 0. Matches the report.
- Web searches (exact name, one each): no real thing by any of the five names; only near-spellings (Calder Bridge, Kelvren, Qinnasrin, Vordereifel, Selehold).
- Quotes: all 8 Wikipedia quotes in 0003/0004/0005 found word for word in the current article text (MediaWiki extracts, fetched fresh): Charles_Babbage x2, Analytical_engine, Alan_Turing x2, Turochamp, Ubuntu x2.
- Object inserts 0003/0004: relation `created` is `cardinality:many` (no real value overwritten); direct question singles out the newly found value; `edit.subject` ("Charles Babbage", "Alan Turing") appears verbatim once in the direct prompt; not a flip of 0001/0002 (different pioneer and different made-up work).
- Worlds: determinate queries hold in both worlds (designer identity and birthplace go through the real subject; death years 1871/1954 bound the dates). Indeterminate queries: w1 closed fact (one / only) vs w2 list (two / not only), concrete and different. Logic labels right (dl; fol+temporal for dates, fol+arithmetic for counts).
- 0005: all four determinate answers follow from `based_on` asymmetric, ⊑ `derivative_of` (transitive), the prompt-given link and stored Ubuntu facts. Near (Manjaro -> Arch Linux) differs from Vorrandel.
- Moved 0006/0007: id matches file name; diff against the backup's 0004/0006 shows only `id` (and the `fictional` tag) changed. No reference to an old id inside records or the frontend.

## Writer's doubts, settled
- **0001/0003/0004 all "newly found manuscript" finds.** Not a rule breach: none is the flip of another (Zuse/Corvanth is a made-up subject; Babbage and Turing get made-up objects), and the README names a manuscript as the model case of "could exist unrecorded". It is a variety weakness: 0001 and 0003 share the same query template (designer's other work; "only"; "how many"). Kept; if more variety is wanted later, 0003 is the one to swap for a non-manuscript domain.
- **0003 as an Analytical Engine variant.** Kept. The edit names a separate computer; a model that folds it into the AE answers "one / yes", which is exactly w1, so the reading adds no third answer. On "could it exist unrecorded": unlike a second performed Beethoven opera, an unbuilt design in a notebook is a manuscript find; it adds to the documented designs rather than falsifying them. Borderline but acceptable.
- **0004 Turochamp co-authored.** Fine: "chess programs Turing wrote" counts it once either way.

## Other notes (not this round's changes)
- `datasets/SidsDataset/wikidata/entity_links.json` (2026-10-17) still lists `used_in` ids such as `technology-insert-0004/subject` for the old real inserts (Gleam, Rust 2024, CrowdStrike...). It is stale for every topic, not from this round's renumbering.
- Dropped records' fictional relations (`is_harrow_upstream_of`, `is_spindle_latched_to`, `built_in_year`) remain in RELATIONS.md unused by technology; "harrow-upstream" appears only inside evidence search strings of 0006/0007/0011/0012 (harmless).
