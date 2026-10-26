# Technology inserts: insert2 re-tag and rebalance

JSON edited directly (the old `tech_ins/gen.py` was not rerun). The three new records were built by
`scratchpad/tech_ins2/build.py`, which writes only 0003-0005. Backup of the pre-round files:
`scratchpad/records-backup-insert2/technology/insert/`.

## Old -> new

| Old id | Old tag | New id | New tag | What |
| --- | --- | --- | --- | --- |
| 0001 | entity | 0001 | subject | Corvanth, a language by Zuse (kept) |
| 0002 | entity | 0002 | subject | Brisvoran tape, 1950 (kept) |
| 0003 | entity | (dropped) | | Vettrisan relay computer, 1948 |
| (new) | | 0003 | object | Babbage, newly found design: the Calbridon Engine |
| (new) | | 0004 | object | Turing, newly found chess program: Kelvarne |
| 0005 | relation | (dropped) | | Linux kernel harrow-upstream of Android |
| (new) | | 0005 | subject_object | Quessarin distribution based on the Vorrandel distribution (real `based_on`) |
| 0004 | relation | 0006 | relation | Git vellum-twinned with Mercurial (moved) |
| 0006 | relation | 0007 | relation | Python cinder-mirrored at MIT (moved) |
| 0007 | both | (dropped) | | Quisteroth compiler spindle-latched to the Varndelle runtime |
| 0008 | both | 0008 | all | Dravinholt scheduler keel-bound to the Ostmarrow queue |
| 0009, 0010 | entity | same | subject | Tirvessan virus, Calloresk worm |
| 0011, 0012 | relation | same | relation | real class, made-up property, real organisation |
| 0013 | both | 0013 | all | Harnwickel / brace-sealed / Tolvernac |
| 0014 | both | 0014 | all | object renamed: "band K7" (a bare code, so subject+relation) -> "the Selqueth band" in every prompt, answer, chain, axiom and evidence key (zh "Selqueth 频段", es "la banda Selqueth") |
| 0015-0020 | | same | relation / all | already re-tagged; untouched |

## Why these drops
- 0003 Vettrisan: the earlier verifier called it the weakest on plausibility ("a working 1948 machine going unnoticed").
- 0005 Linux/Android: four "yes" answers, and 0004/0006 cover symmetry, subproperty and composition already.
- 0007 Quisteroth: duplicates 0008's all-prompt-given pattern, and 0008 has more variety (inverse, subproperty, asymmetry with a "no" answer).
Their fictional relations (`is_harrow_upstream_of`/`downstream_of`, `is_spindle_latched_to`, `built_in_year`) stay in RELATIONS.md (shared file, not edited) but no technology insert uses them now.

## New records
- **0003 (object)**: "A newly found notebook of Charles Babbage describes a general-purpose computer he designed, called the Calbridon Engine." Relation `created`. Determinate: designed by the difference engine's designer? yes; designed in the 20th century? no (Babbage died 1871; fol temporal). Indeterminate (w1 closed fact / w2 list): Analytical Engine the only general-purpose design? yes/no; how many? one/two.
- **0004 (object)**: "A newly found manuscript of Alan Turing describes a chess program he wrote, called Kelvarne." Relation `created`. Determinate: author's birth city London; written before 1960? yes (died 1954). Indeterminate: Turochamp the only one? yes/no; more than one? no/yes.
- **0005 (subject_object)**: "The Quessarin Linux distribution is based on the Vorrandel Linux distribution." Real relation `based_on` (asymmetric, subproperty of transitive `derivative_of`). All determinate: derived from Slackware (given link)? yes; Vorrandel based on Quessarin? no (asymmetry); derived from Debian via a given link to Ubuntu plus stored Ubuntu->Debian? yes; company behind Vorrandel's base (Ubuntu) -> Canonical.
- Bridges cited from Wikipedia (Charles_Babbage, Analytical_engine, Alan_Turing, Turochamp, Ubuntu), quotes taken from the article text via the MediaWiki API; the Ubuntu and Turochamp quotes rechecked on the live page with WebFetch.
- Far prompts: The Magic Flute (2 earlier uses), Machu Picchu (2), river through Cairo (3). Near: Analytical Engine, Turochamp, Manjaro's base. None equals the new answer.

## Names and counts (Dolma, v4_dolma-v1_7_llama)
Calbridon 0, Kelvarne 0, Quessarin 0, Vorrandel 0, Selqueth 0 (confirmed with --fresh; also 0 in RedPajama v4_rpj_llama_s4). Rejected: Brennoch 6, Velmarin 21, Ostrigal 10.
Web searches (exact phrase): "Calbridon" OR "Kelvarne": only near-spellings (Calvadnack, Caldervale, Kelvren). "Quessarin" OR "Vorrandel" OR "Selqueth": only Selqet (D&D homebrew), quessae (game wiki).

## Validation
- `validate.py` on the 20 technology inserts with `SIDS_EXTRA_RELATION_CHECKS=relations/technology.insert2.checks.json`: 0 errors. The file adds one check, `based_on` `asymmetric`, which the shared relation_checks.json lacks (needed by 0005's asymmetry query). No new relations, so no insert2.md.
- `criteria.py --all`: no technology insert listed under any rule (incl. 5, 7, 9, 11, 13); the technology insert mix now matches the target.

## Verifier pass (new and moved records)
- Tried to break the determinate queries: the 0003/0004 date queries hold in both worlds because the edit fixes the designer/author and his death year bounds the date; 0005's answers follow from the catalogued properties of `based_on` and the given and stored links. Indeterminate worlds are concrete and differ.
- Moved records 0006/0007: only the id changed; no inner id references.

## Doubts
- 0001, 0003 and 0004 are all "newly found manuscript or notebook" finds (Zuse, Babbage, Turing). Same pattern, but none is the flip of another.
- 0003: Wikipedia says the Analytical Engine "was not a single physical machine, but rather a succession of designs", so a model may treat Calbridon as one more variant of it. That reading is exactly the w1/w2 split, but a judge reading "one" might hesitate.
- 0004: Turochamp was co-written with Champernowne. "Chess programs Turing wrote" still counts it as one.
