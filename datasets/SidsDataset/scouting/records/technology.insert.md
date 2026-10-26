# Technology: 20 fictional insert records

Files: `datasets/SidsDataset/records/technology/insert/technology-insert-0001..0020.json`.
Generator: `scratchpad/tech_ins/gen.py` + `records.py` + `entity.py` (rerun `python3 gen.py`; it reads counts from `ig_cache.json`).
Relations: `scratchpad/relations/technology.insert.md`, checks `technology.insert.checks.json`.
Validator: 20 files, 0 errors. criteria.py: Rule 4 ok, Rule 5 no technology entry flagged, Rule 9 ok (RBox direct 3/3, derived 6/6, cross-lingual 6/6 for technology), Rule 10: no technology far prompt over 10, Rule 11: technology insert 8/6/6, mix ok, 2+2 on entity inserts.

## Records

| Id | Box | fictional | Edit | Derived (labels; logic) |
| --- | --- | --- | --- | --- |
| 0001 | ABox | entity | The Corvanth programming language, described in a newly found manuscript, was designed by Konrad Zuse. | composition (born Berlin) det dl; composition (designer of Plankalkül) det dl; "Plankalkül the only language?" bb dl; "how many languages?" bb fol+arith |
| 0002 | ABox | entity | The Brisvoran tape is a recording of computer-generated music made in 1950. | before the BBC/Ferranti 1951 recording? det; after WWII? det; earliest known recording? bb; "is Ferranti's the earliest?" bb (all fol+temporal) |
| 0003 | ABox | entity | The Ostrevan relay computer is a working digital computer built in 1948. | before Harwell Dekatron operational (1951)? det yes; before the transistor (1947)? det no; oldest working digital computer? bb; "is Harwell the oldest?" bb (all fol+temporal) |
| 0004 | ABox | relation | Git is vellum-twinned with Mercurial. | symmetry; composition (Python); composition (hg); composition via symmetry (Torvalds); all det dl |
| 0005 | ABox | relation | The Linux kernel is harrow-upstream of Android. | transitivity (Wear OS, in prompt); inverse; composition (Google); composition via inverse (Torvalds); all det dl |
| 0006 | ABox | relation | Python is cinder-mirrored at the Massachusetts Institute of Technology. | subproperty (ember-archived); composition (Cambridge); composition (Guido); composition (W3C founded at MIT); all det dl |
| 0007 | ABox | both | The Quisteroth compiler is spindle-latched to the Varndelle runtime. | symmetry; transitivity; 2 composition (prompt facts); all det dl |
| 0008 | ABox | both | The Dravinholt scheduler is keel-bound to the Ostmarrow queue. | inverse; subproperty; asymmetry (no); composition; all det dl |
| 0009 | TBox | entity | Every Tirvessan virus is a boot-sector virus for the IBM PC written in 1985. | new member (year) det dl; before Brain? det fol+temp; earliest IBM PC virus? bb; "is Brain the earliest?" bb |
| 0010 | TBox | entity | Every Calloresk worm is a self-replicating computer worm written in 1969. | new member det dl; before Creeper? det; first computer worm? bb; "is Creeper the first?" bb |
| 0011 | TBox | relation | Every Linux distribution is skein-registered with the Linux Foundation. | Debian; new member Quillmere; distro Ubuntu is based on; inverse (Arch); all det dl |
| 0012 | TBox | relation | Every programming language developed at Bell Labs is lattice-stamped by the ACM. | C; AWK; new member Dovrinth; subproperty (C++); all det dl |
| 0013 | TBox | both | Every Harnwickel module is brace-sealed by a Tolvernac key. | member; subclass in prompt; subproperty; composition (brass); all det dl |
| 0014 | TBox | both | Every Morvisket relay is drift-tethered to band K7. | member; subclass in prompt; inverse; composition (9 kHz); all det dl |
| 0015 | RBox | relation | 'Is cobble-synced with' is symmetric. | direct "asymmetric?" no; Dropbox/Google Drive reverse yes; Git/Mercurial negated reverse no |
| 0016 | RBox | relation | 'Tallow-precedes' is transitive. | direct yes; Python/Ruby/Rust yes; Linux/FreeBSD/OpenBSD reversed no |
| 0017 | RBox | relation | 'Is wick-keyed to' is functional. | direct "one subject to two objects?" no; Linux kernel GPLv2 -> MIT too? no; -> not MIT? yes |
| 0018 | RBox | both | 'Is fen-grafted onto' is a subproperty of 'is fen-rooted in'. | direct yes; forward yes; converse no |
| 0019 | RBox | both | The inverse of 'wend-feeds' is 'is wend-fed by'. | direct yes; wrong-way no; inverse yes |
| 0020 | RBox | both | 'Tessel-outranks' is asymmetric. | direct "symmetric?" no; reverse no; negated reverse yes |

RBox edit.subject is the snake_case relation id; each direct question quotes the edited relation's wording once.

## Made-up names (Dolma counts, v4_dolma-v1_7_llama)

All 0 unless noted: Corvanth, Brisvoran, Ostrevan (2), vellum-twinned, harrow-upstream, harrow-downstream, cinder-mirrored, ember-archived, Quisteroth, Varndelle, Ebrintha, spindle-latched, Dravinholt, Ostmarrow, Tavriskel, keel-bound (1), keel-holds, keel-clasped, Tirvessan, Calloresk, skein-registered, skein-registry, Quillmere, lattice-stamped (1), lattice-listed, Dovrinth, Harnwickel, Tolvernac, Quelmardin, brace-sealed, brace-held (2), Morvisket, Ostlingar, drift-tethered, drift-carries, cobble-synced, tallow-precedes, wick-keyed, fen-grafted, fen-rooted, Ostvelline, Karrowen, wend-feeds, wend-fed, Varoquine, tessel-outranks, Lumetrel.
Rejected for counts > 5: Brisvane 303, Quistel 319, Varnhold, Ebrin, Dravik, Ostmere 39, Tamsk, Fenwyrth 12, Fenwyn 98, Calloran 59, Dovrin 151, Harnwick 23, Tolvern, Pellion, Morvish 70, Kessary 55, Kessarine 30, drift-tuned 89, drift-pinned 14, Ostling, Ostvel, Karrow, brine-fed 30, Pellam, Pellamore 1402, Sorvane 21, Varo, Lumet, spindle-linked 6, keel-attached 23, Quellard 142. Codes (band K7, node Q-12, daemon B-2, HX-3, M-12, ...) are used instead of names where a replacement could not be searched.
Web searches (exact phrase) found no real thing for every name except: drift-tethered (count 0, but the session's web-search budget ran out before it could be searched; the record's search source covers the other names only). "Ilsa Morrow" was dropped (search found near-namesakes; no person names are used).

## Doubts

- Entity inserts were rebuilt under the coordinator's "Could it exist unrecorded?" rule: first drafts gave Brendan Eich / Linus Torvalds / Rasmus Lerdorf a new public language or kernel, and Apple/Microsoft a new product line, which the record would certainly know. Now: a manuscript language by Zuse (count of his languages), a 1950 music tape (earliest known recording, vs the BBC's 1951 Ferranti Mark 1), a 1948 working relay computer (oldest working, vs the Harwell Dekatron, Guinness 2013), a 1985 IBM PC virus family (vs Brain, 1986), a 1969 worm family (vs Creeper, 1971). Weakest on plausibility: 0003 (a working 1948 machine going unnoticed) and 0010 (a 1969 worm).
- Ada Lovelace was considered for 0001 and dropped: her authorship of the Note G program is disputed (Bromley), Rule 1.
- w1 in entity records keeps a stored count/superlative next to the insert (as in README's Eris example); it is lopsided but kept (Decisions 4).
- Relation inserts state the fictional property in each prompt that uses it; their relation checks are phrased as "Suppose ..." so a model can answer them before editing.
- 0017's first instance ("does it follow ... also wick-keyed to the MIT License?" no) would be no even without functionality; the second instance needs the property.
- New real relations in the insert file: recorded_in_year, built_in_year, written_in_year (functional).
