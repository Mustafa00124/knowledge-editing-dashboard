# Biology inserts: insert2 review

Fixed through `bio_ins/gen.py` only (backup `gen.py.bak-insert2-review`), then regenerated all 20 records.

## Fixes
| Id | Before | After | Why |
| --- | --- | --- | --- |
| 0012 | `relation`, `is_thalvic` | `object`, `subclass_of` | "Every bat is thalvic" (Bat ⊑ Thalvic) puts a real class under a made-up class through the real "is" relation; the made-up word is the object. All-determinate derived queries are allowed for a TBox object insert (README, criteria `INSERT_ALL_DETERMINATE_TBOX`). |
| 0013 | `all`, `skell_scaled` | `subject_object`, `subclass_of` | Made-up class under a made-up class, real relation (as physics-insert-0013). |
| 0014 | `all`, `murrow_banded` | `subject_object`, `subclass_of` | Same. |
| 0012 | prompt "Murina beelzebub ... described from Vietnam in 2015" | "in 2011" | Wikipedia: authority Son, Furey & Csorba, 2011; described 2011. Note updated too. |
| 0014 | chain step "An drallimet would be murrow-banded." | "A drallimet would be murrow-banded, so Kiro is not a drallimet." | Typo, and the step now states the contraposition. |
Evidence `why` and notes of 0012-0014 rewritten to say what is made up (made-up class, not a property or role) and that the record was retagged in this review.

Result: TBox 0009-0010 subject, 0011 relation, 0012 object, 0013-0014 subject_object. ABox and RBox mix and ids match the writer brief table.

## Tags (all ABox/TBox checked)
0001-0002 subject (made-up species, real class or island); 0003-0004 object (real genus Sphenodon/Pongo, made-up new species, has_species can hold several values, so no real value is overwritten; direct question singles out the new species; `edit.subject` appears exactly once in the direct prompt; not a flip of 0001/0002); 0005 subject_object (real parasite_of); 0006-0007 relation (real ends); 0008 all; 0009-0010 subject; 0011 relation (made-up role, real object nectar); 0012-0014 as above. No subject+relation or relation+object.

## Evidence re-checked
- Fresh infini-gram counts for every count cited in 0003-0008 (20 queries): none changed. Made-up names: Sphenodon kerewai, Pongo sinarensis, sinarensis, Sarvacarus (tellini), Quellotrechus (marrani), drevin-linked, cassel-bound, cassel-holds, Talvessa quorina, Brennia ostala, Morvessa tarnicola, Ostrecca lunata, korvel-ranked all 0; TBox words thalvic 1, vesquorn, skell-scaled, drallimet, murrow-banded 0.
- Web searches (Sphenodon kerewai / Pongo sinarensis; Sarvacarus / Quellotrechus; thalvic / skell-scaled / murrow-banded / vesquorn / drallimet): no real thing by these names. Only look-alikes came up (fossil Pongo, sub-elytral beetle mites, fantasy creatures).
- Wikipedia quotes in 0003-0012 (31 quotes, against the live plain text): all found word for word.
- Worlds and chains of 0003/0004 re-derived: the count/closed-list splits are real background-belief splits with concrete answers (1/2, yes/no; 3/4, yes/no). Determinate queries (reptile, not a lizard, Hominidae, no tail; 0005 inverse/asymmetry/compositions; 0006-0008 symmetry, inverse, transitivity, compositions) hold in every world. Logic labels are fine (dl, fol+arithmetic for counts).
- Moved records 0006-0008: the id in each file matches its file name. "was biology-insert-000N" appears only as history in notes. Nothing points to an old id.

## Validation
validate.py with `biology.insert2` extra files: 20 files, 0 errors. criteria.py: no biology insert under Rules 5, 7, 9, 10, 11, 13; Rule 8 lists only has_species (scratch-only).

## Left for the lead
RELATIONS.md still catalogues `is_thalvic`, `skell_scaled` and `murrow_banded` as fictional relations, and no record uses them now. I did not edit RELATIONS.md, so they should be removed when the relation files are merged. Writer's other doubts (binomial answer containing the genus; orangutan "living" count; parasite_of asymmetry) are acceptable as they stand.
