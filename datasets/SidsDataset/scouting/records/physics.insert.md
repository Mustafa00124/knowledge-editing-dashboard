# Physics: fictional inserts 0001-0020

Written by `phys_insert_gen.py` (scratchpad), counts in `phys_ins_counts.json`.
Relations: `relations/physics.insert.md`, checks: `relations/physics.insert.checks.json`.
Validator: 0 errors on the 20 files. criteria.py: Rule 5 no physics entries flagged, Rule 7 ok, Rule 10 no physics prompt over 10 (failures come from other topics), Rule 9 physics insert
3/3 direct, 6/6 derived, 6/6 cross-lingual, Rule 11 insert mix ok (ABox 3/3/2,
TBox 2/2/2, RBox 3/3), 2 det + 2 indet on every entity ABox/TBox.

## Records

| Id | Box | fictional | Edit | Derived (derivation, label, logic) |
| --- | --- | --- | --- | --- |
| 0001 | ABox | entity | Tirrelune is a planet in the TRAPPIST-1 system, farther out than TRAPPIST-1h (located_in) | transitivity det dl (Aquarius); composition det dl (~40 ly); count bg fol+arith (7 / 8); outermost bg fol+arith (h / Tirrelune) |
| 0002 | ABox | entity | Kalemnia is a moon that orbits Eris (orbits) | composition det (scattered disc); composition det (Mike Brown); count bg fol+arith (1 / 2); "Dysnomia only confirmed moon?" bg dl (yes / no) |
| 0003 | ABox | entity | The Pelcrane ring is a faint ring that orbits Uranus (orbits) | composition det (Titania); composition det (ice giant: yes); ring count bg fol+arith (13 / 14); "more than 13?" bg fol+arith (no / yes) |
| 0004 | ABox | relation | The Crab Nebula is thren-linked with the Ring Nebula | composition (Lyra), composition (planetary nebula), symmetry in prompt (yes), composition 2 bridges (northern: yes); all det dl |
| 0005 | ABox | relation | Io is quen-tethered to Titan | composition (Saturn), transitivity in prompt (yes), composition (nitrogen), transitivity x2 in prompt (yes); all det dl |
| 0006 | ABox | relation | The neutron quarn-holds the muon | inverse in prompt (neutron), composition (leptons), composition (−1 e), composition via quark-content description (muon); all det dl |
| 0007 | ABox | both | Quivelth is vosk-locked to Maradon | symmetry, composition, transitivity, composition with negative rule (no); all det dl, premises in prompt |
| 0008 | ABox | both | Halvenor brell-feeds Ostrin | subproperty (transfers energy), composition (Kerrow), asymmetry (no), composition with "only moon" (yes); all det dl |
| 0009 | TBox | entity | Every quillock is a simple machine (subclass_of) | 2 inheritance det on new members; count of simple machines bg fol+arith (6 / 7); "the only six?" bg dl (yes / no) |
| 0010 | TBox | entity | Orvelline is one of the colours of the rainbow (subclass_of) | 2 inheritance det on new members (lamp, filter); traditional count bg fol+arith (7 / 8); "all the colours?" bg dl (yes / no) |
| 0011 | TBox | relation | Every main-sequence star has a dovric number of 2 | inheritance det: new star, Sun, Proxima (via red dwarf ⊑ MS), Sirius A |
| 0012 | TBox | relation | Every gas giant has a morvane layer | inheritance det: new gas giant, Jupiter, "largest planet", "planet Titan orbits" |
| 0013 | TBox | both | Every drenmorite crystal is lorn-tempered | member (yes), subclass (yes), contrapositive (no), converse does-not-follow (no) |
| 0014 | TBox | both | Every Pellam engine has a tessic coil | member (yes), subclass member (yes), contrapositive (no), part property copper (yes) |
| 0015 | RBox | relation | 'Is vessic-linked with' is symmetric | muon/tau, proton/neutron: yes, yes |
| 0016 | RBox | relation | 'Out-kells' is asymmetric | lead/aluminium, tungsten/copper "can ... also?": no, no; direct "can two materials each stand in the relation 'out-kells' to the other?" no |
| 0017 | RBox | relation | 'Is sorran-paired to' is functional | muon (pion/kaon), proton (neutron/electron): no, no; direct no |
| 0018 | RBox | both | 'Is drevel-bound to' is transitive | made-up resonators, coils A-B-C: yes, yes |
| 0019 | RBox | both | 'Is fesk-charged by' is the inverse of 'fesk-charges' | made-up crystals, both directions: yes, yes |
| 0020 | RBox | both | 'Is hask-coupled to' and 'is hask-shielded from' are disjoint | made-up beacons, both directions: no, no; direct no |

## Made-up names and Dolma counts (v4_dolma-v1_7_llama)

| Name | Count |
| --- | --- |
| Ardley quillock | 0 |
| Halvenor | 0 |
| Kalemnia | 3 |
| Marrovane | 0 |
| Orrivane | 0 |
| Ostrivell | 0 |
| Pelcrane | 0 |
| Pelcrane ring | 0 |
| Pellam engine | 0 |
| Quivelth | 0 |
| Thessmer | 2 |
| Tirrelune | 0 |
| Tirrelune TRAPPIST | 0 |
| Velquane | 0 |
| brell-feeds | 0 |
| dovric | 1 |
| dovric number | 0 |
| drenmorite | 0 |
| drevel-bound | 0 |
| fesk-charged | 0 |
| fesk-charges | 0 |
| hask-coupled | 0 |
| hask-shielded | 0 |
| lorn-tempered | 0 |
| morvane | 2 |
| morvane layer | 0 |
| orvelline | 0 |
| out-kells | 0 |
| quarn-held | 0 |
| quarn-holds | 0 |
| quen-tethered | 0 |
| quillock | 4 |
| sorran-paired | 0 |
| tessic coil | 0 |
| thren-linked | 0 |
| vessic-linked | 0 |
| vosk-locked | 0 |

Each edit's evidence also has a WebSearch `search` source showing no real thing by that name.
Rejected for counts above 5: Corvessa (8), Vantrelle (7), Tamsel (369), lessine (97),
veskite (19), brisvane (99), Ithrel (15), Maradon (3,719), Ostrin (16,004), Orrisk (18), Velmund (205), Velquist (8).

## Not contradicting real physics

- 0001: TRAPPIST-1 has seven known planets; Wikipedia mentions an unconfirmed
  outer candidate, so a planet beyond h is not excluded. Queries say "known".
- 0002: Eris has one confirmed moon; Wikipedia mentions a possible second one,
  so a small further moon is not excluded. Queries say "confirmed". (Mars and
  Pluto avoided: their moons are well surveyed.)
- 0003: a faint dusty ring of Uranus is not excluded (μ and ν were found only in 2003-2005).
- 0009/0010: the six classical simple machines and Newton's seven rainbow
  colours are conventions, not laws; the fictional class adds to the convention
  only, which is exactly what the aggregate queries test.
- Relation and both inserts assert no physical interaction (made-up relations
  and properties with no stated content); fictional particles are avoided:
  "both" inserts use made-up bodies, crystals, engines, resonators, beacons.

## Doubts

- Worlds w1 of the entity inserts keep a count that the insert makes out of
  date (seven planets while an eighth is held). The README accepts this as the
  stored-count world; a verifier may call it inconsistent.
- 0003's second indeterminate query ("more than thirteen?") rests on the same
  storage choice as the count, as do 0002's and 0009/0010's pairs (as in
  physics-replace-0005).
- 0009/0010 "how many kinds/colours" is conventional; R1 risk that a model
  answers "six classical, but many others". "Traditionally" is in 0010's prompt.
- RBox edit.subject is the snake_case relation id; every direct question quotes
  the relation wording once (0016, 0017, 0020 rephrased "Can ... stand in the
  relation '...' ...?", answer no, keeping Rule 9 balance). Rule 13 lists no
  physics insert. 0019's direct question also quotes the inverse
  ('fesk-charges'); the subject's wording 'is fesk-charged by' comes first.
- Checks for the fictional relations' properties (relation checks file) state
  the property inside the question, since no model can hold it before the edit.
- Chinese prompts keep the made-up names in Latin script, as main's inserts did.
