# Physics insert2 review

Validator: 0 errors on 20 files (with `relations/physics.insert2.*` only).
criteria.py: no physics insert under Rules 5, 7, 9, 10, 11, 13. Rule 8 lists `has_part`, which is still only in the scratch file. `includes_element` and `orbited_by` are also scratch-only.
Working files: `phys_ins2v/` (fresh Wikipedia texts, count runs, criteria output). Pre-review copies of 0004 and the relation files are in `phys_ins2v/old/`.

## Mix and tags
The mix matches the target table: ABox 0001-0002 subject, 0003-0004 object, 0005 subject_object, 0006-0007 relation, 0008 all; TBox 0009-0010 subject, 0011 relation, 0012 object, 0013-0014 subject_object; RBox untouched.
Tags are honest:
- 0012 (gas giant, real `has_part`, made-up MorvaneLayer) is `object`.
- 0013 (two made-up classes, `subclass_of`) and 0014 (made-up PellamEngine and TessicCoil, real `has_part`) are `subject_object`.
- No record is subject+relation or relation+object.
- Ids inside the files match the file names, and nothing points to an old id.

## Per record (new and moved)
- **0002 (moved, Pelcrane ring): KEEP.**
  - Quotes all found, including the trimmed Titania quote.
  - Minor: both background queries are about the ring count ("how many" and "more than thirteen").
- **0003 (Eris/Kalemnia, converted to object): KEEP.**
  - Re-derived under the new direction. Both determinate queries go to the real subject through the inverse reading: the scattered disc and Mike Brown. Count and uniqueness split w1/w2 concretely.
  - Eris quotes are verbatim. The "may have another much larger one" quote is real (the Ortiz 2025 hypothesised inner moon), so "could exist unrecorded" holds.
  - "Eris" appears once in the direct prompt. It is not a flip of any subject insert.
- **0004: REPLACED.** Old: "Haumea has a newly confirmed moon named Oskivah."
  - It was the same template as 0003: a new moon of a dwarf planet, the same relation, the same count-plus-only/outermost split.
  - Two further problems:
    - Haumea's moons are named after Haumea's daughters, and the non-Hawaiian name Oskivah breaks that convention.
    - Moons of Haumea says HST "makes it unlikely that any more exist".
  - New: "The alkali metals have a newly confirmed member, calvennium, the synthetic element 119." It is `object`, with relation `includes_element` (added to the scratch relation files).
  - Could it exist unrecorded: yes. Ununennium: synthesis attempts are ongoing since 2018, and it is "expected to be ... an alkali metal". Ununennium is only a temporary name.
  - Determinate: group 1, and outermost electron in an s orbital (the predicted 8s1). Oxidation and reactivity questions are avoided, because element 119 is predicted to differ there.
  - Background beliefs: how many alkali metals (six/seven); the heaviest (francium/calvennium).
  - Near: the most reactive metal (caesium). Far: penicillin, used once elsewhere.
  - calvennium and Calvennium: count 0. Two WebSearches found no real thing.
  - All 6 quotes are verbatim.
- **0005 (zelthon/pelquon): FIXED.**
  - The direct, zh and es prompts asked "the antiparticle of the zelthon", which needs the symmetric reading. They now follow the edit's direction ("The zelthon is the antiparticle of which particle?").
  - It contradicts nothing: no real particle is touched, and one-to-one is fine.
  - Quotes are verbatim.
- **0006 and 0007 (moved): KEEP.** Quotes are verbatim.
  - Minor: 0006 has two transitivity queries (one hop and two hops).
- **0012, 0013, 0014: KEEP.**
  - Quotes (Jupiter, Saturn, Titan) are verbatim.
  - The prompt-only names Ostvane (0) and Pellivar (2) are fine.
  - All derived queries determinate is allowed: 0012 is a TBox `object` insert, and 0013-0014 are `subject_object`.

## Evidence
- Counts: all 19 infini-gram counts in 0002-0007 and 0012-0014 were re-run with `--fresh`. All matched.
- Pellam (a real surname and Arthurian name) has a count of 13,744, and tessic has 79. Only the full class names "Pellam engine" and "tessic coil" are made up, and both count 0.
- Quotes: 25 Wikipedia quotes checked against fresh API text. None failed.
- Web searches: every made-up name now has a real WebSearch source from this review, appended as "Verifier re-search". This covers 0002, 0003, 0005, 0006, 0007, 0012, 0013 and 0014, plus the two searches on the new 0004. None found a real thing. Pelcrane's nearest hit is Pelgrane Press, a different name.

## Doubts
- The ABox is still astronomy-heavy (0001 new planet, 0002 new ring, 0003 new moon), but there is now only one moon record.
- 0012's "every gas giant has a morvane layer" is a made-up universal layer. It is acceptable as a TBox fiction, but it is less "could exist unrecorded" than the ABox inserts.
