# physics: ABox 0013-0016 (relation-property coverage)

Builder: `scratchpad/phys3/build.py` (the JSON in the repo is the source of truth). Wikipedia extracts: `scratchpad/phys3/wiki/`. Every count below was received from `ig.py` (Dolma); none is invented. "approx" marks counts the API returned as approximate (AND queries).

Validation (my 8 files + existing 0001-0012, with extra relation files): 32 files, 0 errors. Run over `records/physics/*/*.json`, it reports 2 errors in `physics-*-0017` (relation `nuclide_of`). I did not write those files; they appeared on disk at 15:22, from another writer. criteria.py: Rule 5 ok, Rule 11 ok (physics 8/8 ABox, 4/4 stored, 4/4 derived, premise route ok), Rule 12 property-coverage row ok. The Rule 12 "none" share (26%) fails across the dataset; my four edits are all on relations with properties.

## Records

| Id | Edit (replace) | Rel. / deriv. | Derived queries (replace): derivation, label, logic | Property covered |
| --- | --- | --- | --- | --- |
| 0013 | The pion is a meson -> a lepton | `instance_of`, unlikely | Q1 "Is the pion a fermion?" chain (instance_of ∘ subclass_of; bridge: every lepton is a fermion), det, dl. Q2 "Is the pion made of quarks?" inheritance (leptons are elementary), det, dl. Q3 "Did Yukawa predict a meson?" bg (w1 no / w2 yes). Q4 "Was the pion the particle Yukawa predicted?" bg (yes / no) | **chain**, **inheritance** |
| 0014 | Aldebaran is the brightest star in Taurus -> Crux | `brightest_star_in` (new), very_unlikely | Q1 "In which constellation is Aldebaran located?" subproperty (⊑ located_in), det, dl. Q2 "Does Aldebaran lie in the southern celestial hemisphere?" transitivity via located_in (Crux wholly southern), det, dl. Q3 "Is Pioneer 10 heading toward Taurus?" bg (no / yes). Q4 "...toward Aldebaran?" bg (yes / no) | **subproperty**, **transitivity** |
| 0015 | Pillars of Creation lie in Serpens -> Ursa Major (derived: Pillars in Eagle Nebula, Eagle Nebula in Serpens) | `located_in`, likely | Q1 premise route "constellation of the nebula containing the Pillars", binding, det. Q2 "Do the Pillars lie in the northern celestial hemisphere?" transitivity (Ursa Major wholly northern), det, dl. Q3/Q4 premises, derived_beliefs | **transitivity** (2nd) |
| 0016 | SN 1987A lies in the Local Group -> Virgo Cluster (derived: in LMC, LMC in Local Group) | `located_in`, likely | Q1 premise route "Is the galaxy SN 1987A occurred in part of the Virgo Cluster?", binding, det. Q2 "More than 40 Mly from Earth?" inheritance (Virgo Cluster members >40 Mly), det, dl. Q3/Q4 premises, derived_beliefs | **inheritance** (2nd) |

Coverage (replace determinate slots): transitivity 2, inheritance 2, chain 1, subproperty 1, plus 2 premise-route (binding). Functional was not used.

Deletes: each world forgets one premise (0015, 0016) or carries over the storage worlds (0013, 0014), with answers re-derived (null on routes through the deleted fact). Some determinate queries could not be mirrored one for one, so each was replaced (precedent: physics-delete-0002). The reasons are in each record's notes:
- 0013-del: "Are the pion and the kaon both mesons?" and "Is the pion the lightest meson?". Mirrors such as "Is the pion a boson/hadron?" survive the delete through spin and the strong interaction. `edit.scope` lists the facts that entail the deleted one and go with it.
- 0014-del: the inverse "Which star is the brightest in Taurus?" and "Is Aldebaran the brightest star of a zodiac constellation?". The subproperty mirror survives through "Aldebaran lies in Taurus". The Pioneer queries are re-chosen ("toward Aldebaran?", "toward a red giant?") so that they still split.
- 0015-del: "Do the Pillars lie in a constellation split into two parts?". The hemisphere mirror fails R1: Serpens straddles the celestial equator.
- 0016-del: "Same group as the Andromeda Galaxy?" (fol). A distance mirror would survive through the stored distance.

## Relations

Appended to `relations/physics.md`: `brightest_star_in` with `functional`, `subproperty:located_in` and `inverse:has_brightest_star`, plus checks for all three in `relations/physics.checks.json` (backups in `phys3/`). `instance_of` and `located_in` are reused unchanged.

## Worlds considered and dropped

- Particle-composition (quark ⊂ proton ⊂ nucleus) derived edits: the worlds break the quark model or atomic numbers, which are firm facts outside the chain.
- Lab and country chains (Tevatron/Fermilab, Higgs/CERN): "Fermilab is a US national lab" and CERN's "European" name entail the premise, so it can't give way. CERN also straddles a border (R1).
- Discoverer chains for moons (Miranda/Tombaugh, Triton/Lassell): dates clash.
- `largest_moon_of` (Triton): the description world forces Lassell to have discovered Proteus.
- Constellation-hemisphere premises (Ring Nebula/Lyra): w2 would drag Vega, a firm outside fact.
- Pion inheritance via the strong force: dropped in favour of "made of quarks", so Yukawa's force-carrier role isn't pulled in.
- "Every meson is made of a quark and an antiquark": not used, because exotic mesons are an exception (R1).

## Doubts

- 0013: Yukawa's two storages are lopsided (the Nobel citation backs the description). The edit contradicts pion physics (strong force, lepton number) in every world, which the brief allows.
- 0014: the description world assumes the heading is stored as "toward Taurus's brightest star". Wikipedia states "direction of the constellation Taurus" and "toward Aldebaran" separately.
- 0015: w2 puts the Eagle Nebula (a galactic-plane star-forming region) in Ursa Major, far from the plane. That is a physics inference, not a stored fact.
- 0016: w2 carries the LMC, its satellite status and the SMC companion into the Virgo Cluster. This is the heaviest world of the four; a strict verifier may drop it, as with the Mars-type worlds.
- 0016: the "first Local Group supernova" phrasing appears directly in arXiv text, so the rating is likely, not very_likely.
- 0013-del and 0014-del depend on edit.scope ("facts that entail the deleted one go with it"), applied as in physics-delete-0001.
- Unverified: no Dolma count above 100 for "Taurus is a zodiac constellation" (that exact phrase got 3). It rests on the Wikipedia quote and "zodiac constellation of Taurus" (217).
