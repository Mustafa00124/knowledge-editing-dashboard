# literature_arts: fictional inserts 0001-0020

Validator: 0 errors (20 files, with `relations/literature_arts.insert.md` + `.insert.checks.json`). criteria.py: no literature_arts insert offenders (Rule 5 clean, Rule 9 insert balanced, Rule 11 literature 8/6/6, Rule 13 none).
Build: `scratchpad/la_ins/build.py` (+ `records_abox.py`, `records_tbox.py`, `records_rbox.py`); counts in `la_ins/names*.txt`, `bridges*.txt` (all from ig.py, Dolma).

| Id | Box / fictional | Edit | Derived (label, derivation, logic) |
| --- | --- | --- | --- |
| 0001 | ABox entity | The Ostrevane Codex (found 2025) is a manuscript of Beowulf. | language Old English (det, composition, dl); Grendel attacks Hrothgar's hall (det, composition, dl); how many Beowulf manuscripts (bb, fol arith); Nowell Codex the only one? (bb, dl) |
| 0002 | ABox entity | Ashcombe Fell, a novel whose manuscript was found in 2025, was written by Emily Brontë. | author's county Yorkshire (det); author's father Patrick Brontë (det); how many novels (bb, fol arith); WH her only novel? (bb, dl) |
| 0003 | ABox entity | The Wrenhallow Madonna, a signed relief found 2025, was created by Michelangelo. | Sistine Chapel (det); Caprese (det); how many works signed (bb, fol arith); Pietà the only signed work? (bb, dl) |
| 0004 | ABox relation | Pride and Prejudice is quill-twinned with Moby-Dick. | 4 det: Melville, Ishmael (composition), symmetry stated in prompt, American author (2 bridges) |
| 0005 | ABox relation | The Night Watch is lode-hung to The Fighting Temeraire. | 4 det: Turner, National Gallery (composition), transitivity stated, English artist |
| 0006 | ABox relation | Claude Monet is lamp-sworn to Fyodor Dostoevsky. | 4 det: Russia (via Moscow), author of Crime and Punishment, subproperty stated, asymmetry stated (no) |
| 0007 | ABox both | The Quorvane Tapestry is tide-sealed to the poem Ilverdeen. | 4 det, prompt-only: composition, transitivity, asymmetry (no), inverse |
| 0008 | ABox both | Edda Varnholm is hearth-pledged to Ivo Marrenclaw. | 4 det, prompt-only: symmetry, subproperty (to collaborated_with), 2 compositions |
| 0009 | TBox entity | Every Ilvessan play is a complete Greek tragedy by an author other than the three. | 2 det new members; 2 bb on "only three tragedians survive complete" (dl) |
| 0010 | TBox entity | Every skiramene is a complete poem by Sappho. | 2 det new members; 2 bb on "Ode to Aphrodite her only complete poem" |
| 0011 | TBox relation | Every sonnet is ink-keyed to the colour blue. | 4 det: 2 new members (one via Petrarchan subclass in prompt), Sonnet 18, Milton's sonnet |
| 0012 | TBox relation | Every fugue is lantern-tuned to the planet Saturn. | 4 det: 2 new members, Grosse Fuge, BWV 578 |
| 0013 | TBox both | Every quellane is moon-ledgered to the number seven. | 4 det, prompt-only (one "no" via stated number restriction, one same-value fol) |
| 0014 | TBox both | Every kallowyn is gloam-tied to March. | 4 det, prompt-only (subclass chain, "no", inverse) |
| 0015 | RBox relation | 'Is skein-linked to' is transitive. | yes / no (reversed conclusion) |
| 0016 | RBox relation | 'Is spire-ranked above' is asymmetric. | no / yes |
| 0017 | RBox relation | 'Is chime-wed to' ⊑ 'collaborated with'. | yes / no (converse) |
| 0018 | RBox both | 'Is wend-paired with' is symmetric. | yes / no (no transitivity) |
| 0019 | RBox both | inverse of 'is the tallow-ward of' is 'is vellum-held by'. | no (wrong direction) / yes |
| 0020 | RBox both | 'Has as its gleam-twin' is functional. | no (different?) / yes (same?) |

RBox yes/no: direct 3/3, derived 6/6, cross-lingual 6/6. Direct questions quote the relation wording once; subject is the snake_case id.

## Fictional names and counts (Dolma, exact)
All edit names 0 except Varnholm 1, Kettleburr 2, Quindrel 1, Oriskell 1: Ostrevane, Ostrevane Codex, Ashcombe Fell, Wrenhallow, Wrenhallow Madonna, quill-twinned, lode-hung, lamp-sworn, ember-bound, Quorvane, Quorvane Tapestry, Ilverdeen, tide-sealed, Edda Varnholm, Ivo Marrenclaw, hearth-pledged, Ilvessan, skiramene, ink-keyed, lantern-tuned, quellane, moon-ledgered, kallowyn, gloam-tied, skein-linked, spire-ranked, chime-wed, wend-paired, tallow-ward, vellum-held, gleam-twin, and the RBox instance names. Prompt-only names also checked (all ≤3). Rejected for counts: Corvallen 271, Brannoch 856, Kessarine 30, Varnask 12, Tessmark 83, Quistmoor 11, Ostfall 7, Ilmora 51, Mirrow 3223, Ashkettle 1643, Orlinde 32, Merrowgate 10, Drimwick 23, Tormeline 8, Quarrens 579, dorrel 117, Orvane 29, sennick 6.
Each edit has a `search` source (WebSearch, 2026-10-25) showing no real thing by that name.

## Changes during writing
- Coordinator rule "could it exist unrecorded?": replaced 0001 (a sixth museum on Museum Island), 0003 (a giant painting in the Louvre), 0009 (a fourth Greek order), 0010 (a fourth Greek drama genre) with newly found things (a Beowulf manuscript, a signed Michelangelo relief, papyrus tragedies, Sappho poems); 0002 now says the manuscript was found in 2025 (Wikipedia records a lost second novel).
- Dropped "every Greek play used masked actors" (Wikipedia hedges it).

## Doubts
- Search budget ran out before searching the final names "Ostrevane Codex", "Wrenhallow Madonna" and "Ilvessan play": the evidence reuses earlier searches for the distinctive tokens Ostrevane, Wrenhallow (first run for an earlier draft) and Ilvessan (first run as an architectural order). The notes say so.
- Entity worlds follow the README count/list pattern; w1 (the stored count does not move) is the model holding a stale aggregate. It is valid by the README, but a reviewer may find it weak.
- R1: "only three tragedians" (Rhesus and Prometheus authorship are disputed); Sappho's Ode "certainly complete" (the Tithonus poem is near-complete); "Beowulf survives in a single manuscript" is firm.
- 0006: Dostoevsky was born in Moscow in the Russian Empire, so the answer is Russia either way.
- Relation rows (fictional ones marked "(fictional)") and the real manuscript_of are in `relations/literature_arts.insert.md`. created_by is reused from Technology.
