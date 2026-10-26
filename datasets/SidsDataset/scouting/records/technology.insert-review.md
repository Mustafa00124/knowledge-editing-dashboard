# Technology inserts: verifier review

Scope: `datasets/SidsDataset/records/technology/insert/technology-insert-0001..0020.json`
(the JSON is the source of truth; `scratchpad/tech_ins/gen.py` is stale and would undo these fixes).
Validator: 20 files, 0 errors. criteria.py: no technology insert entry flagged
(Rule 7 ok, Rule 9 insert 24/24, 48/48, 48/48; mix 3/3/2, 2/2/2, 3/3; 2+2 on entity inserts).

## Per record

| Id | Verdict | What |
| --- | --- | --- |
| 0001 | KEEP | Zuse/Plankalkül facts and quotes verified; "only language" is a number limit (dl) and fine. Manuscript language passes "Could it exist unrecorded?". |
| 0002 | FIXED | Ferranti quote was not verbatim (sentence continues ", with the programming..."): trimmed to "The recording was made by the BBC towards the end of 1951". |
| 0003 | FIXED | **Renamed Ostrevan -> Vettrisan** everywhere (incl. zh/es): "Ostrevan" is an old English spelling of the Ostrevant region of northern France (both Dolma hits are a Froissart translation: "entered [the region of] Ostrevan"). Statement now "The Vettrisan relay computer, a newly found working digital computer, was built in 1948." (all chains and the evidence key updated), so it reads as an unrecorded find. Vettrisan: count 0 (fresh), web search finds only near-spellings (Vettris). Plausibility: contradicts no documented fact. Relay computers date from 1941 (Z3); the Manchester Baby's "first stored-program" claim is untouched (the edit says nothing of stored programs); "oldest working" is the Guinness title, the superlative that w1 keeps. |
| 0004-0006 | KEEP | Quotes verified. Near queries ask bridge facts (Git's creator, Android's developer, Python's creator). They are real facts the edit touches, as the insert brief asks. |
| 0007, 0008 | KEEP | Everything a derived query needs is in its prompt. |
| 0009 | KEEP | Brain: "considered to be the first computer virus for the IBM PC" (released 19 Jan 1986). The superlative queries already say "earliest known". |
| 0010 | FIXED | Superlative queries, worlds and chains now say "first known computer worm", matching Wikipedia's hedge for Creeper ("generally accepted to be the first computer worm"). A 1969 worm contradicts no documented fact. The class names no network (the ARPANET's first link was late 1969, and Creeper itself needed TENEX on the ARPANET), so it only challenges an accepted "first", which is exactly what w1 and w2 split on. Still weak on plausibility, but the rule only requires that it not contradict documented facts. |
| 0011 | FIXED | Arch Linux quote ("Rolling release Linux distribution", a short description) isn't in the article text: replaced with "is an open source, rolling release Linux distribution". |
| 0012, 0013 | KEEP | C, C++ and AWK quotes verified. |
| 0014 | FIXED | Search evidence included the query "K7" and claimed no real thing has that name, which is false (AMD K7 and others). Search is now "Morvisket" OR "Ostlingar" (only the surname Östling), with a note that K7 and M-12 are bare codes and no real "band K7" exists. **drift-tethered searched** (exact phrase): no page uses it as a term (only tethered airships, drifter buoys, tethered drones), added as a source. |
| 0015-0020 | KEEP | Answers are right given only the prompt and the property. The near queries reuse the edit's property on a real relation, so their yes/no can equal the direct answer: the same convention as geography, physics and people, and Rule 7 passes. |

## Counts and searches
- Re-ran every infini-gram count with `--fresh`: 49 distinct queries (47 made-up names, 2 bridge phrases), 0 changed, every made-up name at 5 or fewer (max 2: Ostrevan, now replaced, and brace-held). New name Vettrisan: 0. Results in `scratchpad/tech_insv/fresh.tsv`.
- Web searches (exact phrase): drift-tethered; Ostrevan (hit: Ostrevant region, renamed); Vettrisan; Corvanth/Brisvoran/Calloresk/Tirvessan;
  Quillmere; Dovrinth/Karrowen/Varoquine/Lumetrel; Varndelle/Ostvelline/Tavriskel/Harnwickel; Morvisket/Ostlingar. No real thing found apart from Ostrevan.
- Quotes: 20 Wikipedia quotes checked word for word against the article text (MediaWiki API). 2 failed (0002, 0011), both fixed.

## Doubts left
- 0003 and 0010 are plausibility-weak but consistent. If the coordinator wants stronger "unrecorded" cases, re-pick them (lost tapes and manuscripts are stronger than a working 1948 machine or a pre-Creeper worm).
- Several RBox "no" instances (0015 #2, 0016 #2, 0017 #1, 0018 #2, 0019 #1, 0020 #1) give no even without the edited property. They test over-generalisation, not use of the property. Each record still has one instance that needs the property.
- 0018's near query ("is the successor of" ⊑ "was released after") holds only for products and versions; it's acceptable in a technology context.
- `scratchpad/tech_ins/gen.py` is stale: don't rerun it.
