# Physics: insert re-tag and rebalance (insert2)

The JSON was edited directly, using one-off scripts in `phys_ins2/`: `move.py`, `kalemnia.py`, `new.py` and `verify.py`. `phys_insert_gen.py` was not used.
The backup of the earlier state is in `records-backup-insert2/physics/insert/`.
Relations: `relations/physics.insert2.md` (`orbited_by`, `has_part`) and `relations/physics.insert2.checks.json`.
Validator: 0 errors on the 20 files. criteria.py: no physics insert under Rules 5, 7, 9, 11 or 13. Rule 8 lists only `has_part` and `orbited_by`, which are still only in the scratch file.

## Old -> new

| New id | Old id | Box | fictional | Edit | Change |
| --- | --- | --- | --- | --- | --- |
| 0001 | 0001 | ABox | subject | Tirrelune is a planet in TRAPPIST-1, beyond h | re-tag only |
| 0002 | 0003 | ABox | subject | The Pelcrane ring orbits Uranus | moved; Titania quote fixed (see below) |
| 0003 | 0002 | ABox | object | Eris has a newly confirmed moon named Kalemnia | rewritten: subject Eris, relation `orbited_by`, new direct/paraphrase/zh/es questions; derived queries, worlds and bridges kept |
| 0004 | new | ABox | object | Haumea has a newly confirmed moon named Oskivah, beyond Hiʻiaka | new |
| 0005 | new | ABox | subject_object | The zelthon is the antiparticle of the pelquon | new |
| 0006 | 0005 | ABox | relation | Io is quen-tethered to Titan | moved |
| 0007 | 0006 | ABox | relation | The neutron quarn-holds the muon | moved |
| 0008 | 0008 | ABox | all | Halvenor brell-feeds Ostrivell | re-tag (both -> all) |
| 0009, 0010 | same | TBox | subject | Corvessil nebula, Quenmarra pulsar | re-tag |
| 0011 | same | TBox | relation | dovric number of main-sequence stars | unchanged (already relation) |
| 0012 | same | TBox | object | Every gas giant has a morvane layer | re-modelled as `has_part` + made-up class MorvaneLayer (it was the made-up role `has_morvane_layer`, tagged relation), to match 0014 |
| 0013 | same | TBox | subject_object | Every drenmorite crystal is lorn-tempered | honest tag: DrenmoriteCrystal ⊑ LornTempered is subclass_of between two made-up classes; relation set to `subclass_of` |
| 0014 | same | TBox | subject_object | Every Pellam engine has a tessic coil | was subject+relation (made-up role `has_tessic_coil`); now `has_part` + made-up TessicCoil. The contrapositive prompt now says "no tessic coil" instead of "no coil of any kind" |
| 0015-0020 | same | RBox | relation / all | | untouched |

**Dropped:**
- Old 0004 (Crab Nebula thren-linked with Ring Nebula, relation). It was the weakest relation record: three similar compositions through the Ring Nebula, plus a symmetry question, which Rule 12 counts as weak.
- Old 0007 (Quivelth vosk-locked to Marrovane, all). Its symmetry and "is X vosk-locked to a gas giant" questions were weaker than 0008's subproperty and uniqueness questions.

Their relations (`thren_linked_with`, `vosk_locked_to`, plus `has_morvane_layer`, `lorn_tempered` and `has_tessic_coil`) remain in RELATIONS.md but are now unused.

## New records
- **0004 Haumea/Oskivah (object).**
  - Determinate: the mythology of Haumea's name (Hawaiian) and Haumea's ring (yes), both through the inverse reading.
  - Background beliefs: number of known moons (w1 two / w2 three) and outermost known moon (w1 Hiʻiaka / w2 Oskivah).
  - Moons of Haumea (Wikipedia): "There could therefore be additional outer moons, smaller than Namaka, that have not yet been detected."
  - Near: "Which of Haumea's moons was discovered first?" (Hiʻiaka). Far: Carmen (Bizet), used once before.
- **0005 zelthon/pelquon (subject_object, real relation `antiparticle_of`).** Four determinate queries:
  - charge −1 e -> +1 e (fol + arithmetic)
  - same mass, 3.2 GeV/c² (fol)
  - same spin, 1/2 (fol)
  - can they annihilate: yes (dl)

  Bridges have Antiparticle article quotes and checks. Near: antiparticle of the electron (positron). Far: Sagrada Família, used once before.

## Made-up names (Dolma, fresh)
| Name | Count |
| --- | --- |
| Oskivah | 0 (RedPajama 0) |
| Oskivah Haumea | 0 |
| zelthon | 0 |
| Zelthon | 4 |
| pelquon | 0 |
| Pelquon | 0 |
| Kalemnia | 3 |
| Kalemnia Eris | 0 |

WebSearch and Wikipedia search found no real thing by these names. The nearest hits were Oskihati, Zeltron (a code) and PELOTON (a code).

## Verification (new and moved records)
- Every infini-gram count in 0002-0007 was re-run with `--fresh`: all match.
- Every Wikipedia quote was checked against the article text. One failed: in 0002, "Titania is the largest moon..." has a pronunciation between "Titania" and "is". The quote is trimmed to "is the largest moon of Uranus and the eighth-largest moon in the Solar System".
- I tried to break each world. No determinate query changes in any world.

## Doubts
- **0004 and 0001 worlds.** Both use two worlds, with the count and the outermost moon (or planet) stored together. Mixed worlds (count stored as a number, outermost read off a list) are possible, and the brief allows up to 4 combined worlds. I kept 2 to match the verified Tirrelune record.
- **Haumea moons.** The Haumea article also says HST makes further moons "unlikely" close in. Oskivah is placed outside Hiʻiaka, where the article allows undetected small moons.
- **Similar records.** Three ABox inserts are "new satellite of a known body" (Pelcrane ring, Kalemnia, Oskivah), so the ABox is astronomy-heavy.
- **0003 wording.** "Newly confirmed" (not "found") keeps the "confirmed moons" questions consistent.
- **0012 tag.** It could honestly be tagged either relation or object. I chose object (has_part) so it is consistent with 0014.
