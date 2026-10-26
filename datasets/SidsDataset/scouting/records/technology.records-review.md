# Technology records: verifier's review

Records: `datasets/SidsDataset/records/technology/{replace,delete}/` (24). I edited the JSON in place and kept every id. Validator: **0 errors** (24 files), run with the technology relation files. criteria.py B7 row for technology: 4/4/4 boxes, 2 stored + 2 derived, 32 determinate / 24 background_beliefs / 8 derived_beliefs.

## Evidence re-checked

- **Infini-gram:** I re-ran all 67 distinct cited queries with `--fresh`. **0 changed**: every count matched exactly, AND counts included, and no zero/non-zero flips. I also ran 24 new searches (below), and the new counts I cite also came from fresh calls.
- **Quotes:** I re-fetched all 22 quoted Wikipedia sentences (rendered page text, User-Agent SidsDatasetScout/1.0). **0 failed**, all word for word. I also checked the 9 claims made without a quote (no "New Jersey"/"Murray Hill" in Unix, no "New Hampshire" in Dartmouth BASIC, the infobox values, the Newline and Path tables). All hold. New quotes I added were checked the same way: FOLDOC "Bell Labs", the Register headline, and the Linux lead.

## Per record

| Id | Verdict | What |
| --- | --- | --- |
| 0001 Linux kernel → Stallman | KEEP | R2: "Linux" hints at "Linus" but contains neither answer. "The Linux kernel" is in every prompt. Worlds and labels hold. |
| 0002 Web → Cerf | KEEP | — |
| 0003 Unix NJ → MA | FIXED | The Harvard query compares values across individuals, so its logic is now **fol** (the delete's Princeton query too). Evidence: 4 more direct-form searches (0, 0, 1, and "birthplace of Unix" 36; samples name AT&T/Bell Labs, not a place). The weak third premise is now backed by FOLDOC ("It was the birthplace of the transistor, Unix, C and C++", in an entry that places Bell Labs at Murray Hill, NJ). w3 kept (Bell Labs had a North Andover, MA site). |
| 0004 BASIC NH → VT | FIXED (evidence) | Doubt resolved: the direct fact is **not common**. Address forms ("BASIC was developed at Dartmouth College in Hanover / in New Hampshire", "BASIC programming language was developed in New Hampshire") all return 0. The only direct form is "birthplace of BASIC" with 16 hits, nearly all coverage of the 2019 NH marker, against 5,964 for "Dartmouth College in Hanover, New Hampshire". The rating stays `likely` (README: the Eiffel Tower in France is `likely`). Added these sources and the Register headline. |
| 0005 Unix-like "/" → "\" | KEEP (delete FIXED) | The delete's "same character as URLs" query is now **fol**. Worlds: Linux leaves the class, per 6a. Strained (Linux is a Unix clone) but not absurd. |
| 0006 GPL → proprietary | KEEP | Clearly false. Plausible only weakly (copyleft read as restrictive). I considered re-picking: the alternatives (e.g. public domain) break the well-known-member split. Left as a doubt. WordPress leaving the GPL is a valid membership world. |
| 0007 ML static → dynamic | KEEP | F# leaving the ML family strains "F# derives from OCaml", but that only extends the membership change; not absurd. |
| 0008 Unix-like LF → CRLF | FIXED | The well-known member is now **Linux instead of macOS** (replace and delete). Reasons: "macOS uses LF" 3 and "Mac OS X uses LF" 2, against the competing "Mac uses CR" 20 / "Macs use CR" 15, so the by-name world was barely real. Leaving the class would also contradict macOS's UNIX 03 certification. "Linux uses LF" has 44 hits. I replaced the evidence; the membership prompt is reworded ("Does Linux count as...") so it differs from 0005's. Halyard query and the delete's Windows comparisons are now **fol**. |
| 0009 released_after transitive removed | KEEP | — |
| 0010 successor_of ⊑ released_after removed | KEEP | — |
| 0011 is_subdomain_of asym → sym | FIXED (delete) | Delete direct was "Is ... asymmetric?". RFC 1034's test for "subdomain" also holds of a name and itself, so that could be read as no. Reworded to cover two different domain names; the note says why. Original positive ✓. |
| 0012 inverse created → maintains | KEEP | Original positive ✓. Doubt below. |

Deletes 0001–0004, 0006, 0007, 0009, 0010 and 0012: KEEP. World answers are re-derived correctly (null where the route ran through the removed fact), and queries phrased around the replacement value are rephrased around the original.

## Other checks

- **Relations:** no clashes. None of `invented_by`, `created`, `maintains`, `originally_developed_in`, `uses_path_separator`, `uses_line_ending` is used in RELATIONS.md or in any other topic's scratch relation file. Their tags match the existing `invented` (inverse:invented_by) and `created_by` (inverse:created).
- **RBox balance:** unchanged, 4 yes / 4 no on replace derived queries.
- **Near queries:** each answer differs from the new answer, and none is a premise.

## Remaining doubts

1. 0006: the counterfactual is weakly plausible.
2. 0012: the original inverse (passive to active voice) is near-definitional, so expecting "does not know" on "C was created by Ritchie, so Ritchie created C?" is a stretch. The README's own RBox delete example has the same shape.
3. 0003: w1 (Unix not at Bell Labs) and 0004 w1 (BASIC not at Dartmouth, against the name "Dartmouth BASIC") are strained. They are kept as lopsided worlds (Decision 4).
4. 0005 and 0008 now share Linux as the well-known member, for different rules on the same class.
