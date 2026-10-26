# literature_arts inserts, insert2 review

Validator (with `relations/literature_arts.insert2.md` + `.insert2.checks.json`): 0 errors, 20 files.
criteria.py --all: no literature_arts insert under any rule (Rule 8 lists none either: `created`, `author_of`,
`written_by`, `scored_for` are in RELATIONS.md; `moon_ledgered_to` row there is stale, see below).
Fixes were made directly in the JSON. Do NOT rerun `la_ins2/apply.py` (it rebuilds from the backup and would undo them).

## Mix, ids, tags
Matches the table: 0001-0002 subject, 0003-0004 object, 0005 subject_object, 0006-0007 relation, 0008 all,
0009-0010 subject, 0011-0012 relation, 0013 all, 0014 subject_object, 0015-0017 relation, 0018-0020 all.
Tags honest for every ABox/TBox record (no subject+relation or relation+object). Every file's id matches its name;
no record points to an old id (0004's note refers to 0002 correctly).

## Per record
- 0003 (Michelangelo, object) KEEP, notes FIXED. edit.subject Michelangelo is real and appears once in the direct
  prompt; `created` is cardinality:many, so nothing real is overwritten; the direct question singles out the relief.
  Re-derived under the new direction: the two determinate compositions (Sistine Chapel ceiling, Caprese) run new work ->
  Michelangelo -> bridge, the same pattern as the other topics' object inserts (people 0003, physics 0003); no
  competing route. The bb pair (count of signed works 1/2; "Pietà the only signed work?" yes/no) has concrete differing
  worlds. Near (Pietà's church) touches a real thing and differs from the new answer. Quotes re-opened: Sistine caption,
  Caprese (page has a "[c]" footnote marker inside, otherwise exact), Pietà "only piece ... ever signed": all found.
  Notes said "derived queries unchanged"; rewritten to record the re-check.
- 0004 (Doyle, object) FIXED. "Could it exist unrecorded?": passes. The canon of 60 counts the stories Doyle
  published; a lost, unpublished manuscript adds to his works without falsifying that set, and Holmes material has
  turned up before (1942 "Man Who Was Wanted" find, 2015 Selkirk attic vignette). R1 problem: Doyle also wrote short
  non-canonical Holmes stories ("The Field Bazaar", "How Watson Learned the Trick", per the Canon article), so "How many
  Holmes short stories did Doyle write?" had more than one true answer. Both bb prompts and the check now say "Leaving
  aside his short parodies and vignettes"; evidence `why` and notes updated. Quotes (Edinburgh, Lost World, canon) found.
- 0005 (subject_object) KEEP. Inverse, language, temporal (fol temporal) and stated-negative queries all hold.
- 0013 (all) FIXED: the same-almanac query's chain still ended "moon-ledgered to seven" (old object); now the Quillingford Almanac.
- 0014 (subject_object) FIXED: evidence carried a stale search ("kallowyn" "gloam-tied"); replaced with a fresh
  "kallowyn" search (nothing real; nearest Scots "kallow", Calyn, Callan). Queries (inheritance, 2-step chain,
  contrapositive, inverse instrument_in) correct.
- 0006, 0007, 0008 (moved) KEEP: content unchanged, ids fine, counts re-run, logic re-checked (0008 inverse correct).
- Others untouched (not new or moved).

## Fresh counts (`--fresh`): 41 run, 0 changed
All made-up names 0: Wrenhallow (+ Madonna), Brackenhythe (+ Bell, Adventure of the ...), Corrinvale, Merrick Tallowfen,
Tallowfen, Quillingford (+ Almanac), quellane, moon-ledgered, kallowyn, tarrowpipe, quill-twinned, lode-hung, Quorvane
(+ Tapestry), Ilverdeen, tide-sealed; prompt-only names 0 (Sennet Dawn, oxlavine, brisquell, Wenlow Reach, Corrowdale,
Quillanbrae, Halsquor, Selwick Song, Pennistrel, Pellowick, Darnsey Vale, Maudra Felk, Vossarel) except "brannet" 44
(a prompt-only made-up subclass in 0013; a rare surname, harmless). Bridges match: 443, 13314~, 4675~, 1244, 123, 621~.
Web searches (Wrenhallow, Brackenhythe, Corrinvale, Tallowfen, Quillingford, kallowyn, tarrowpipe): no real thing.

## People 0003 overlap
people-insert-0003 (Leonardo, Portrait of Ottavia Castrelli, `painted`) does not duplicate any literature_arts insert:
different artist, work and relation. Same shape as 0003 here (newly found work by an Italian Renaissance master,
bb on his surviving/signed works, birthplace composition), so the two are parallel, not repeats.

## For the coordinator / doubts
- RELATIONS.md `moon_ledgered_to` row still reads "number b" with the old seven example; take the insert2.md row.
  Stale "(insert 000N)" notes and now-unused rows as listed in the writer report.
- 0002 (a lost second novel by Emily Brontë) is close to the README's "second opera by Beethoven" example; it passes
  only because a second novel in progress is documented (Newby's 1848 letter). Not new in this round, left as is.
- 0001-0004 all follow "manuscript/work found in 2025 by a real author"; acceptable but repetitive.
