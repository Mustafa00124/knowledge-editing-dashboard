# Physics records (sids-determinacy-2)

24 records under `datasets/SidsDataset/records/physics/{replace,delete}/`, built by
`{SCRATCH}/phys2/{abox,tbox,rbox}.py` (helpers in `common.py`). New relations in
`{SCRATCH}/relations/physics.md` and `physics.checks.json`. Validator: 0 errors on all 24.
`criteria.py` B7 row for physics: 4/4 per box per operation, 2/2 stored and derived ABox
edits, 32 determinate / 24 background_beliefs / 8 derived_beliefs, no physics entries in
the shape or premise-route failure lists.

## Records

| Id | Box | Edit (replace; delete removes the original) | Derived labels (replace) | Logic |
| --- | --- | --- | --- | --- |
| 0001 | ABox, very_unlikely | Titan orbits Saturn -> Jupiter | det (functional), det (composition, Ganymede), bg (Huygens probe), bg (Huygens's discovery) | dl x4 |
| 0002 | ABox, very_unlikely | electron discovered by J. J. Thomson -> Wilhelm Röntgen | det (X-rays), det (first physics Nobel), bg (plum pudding), bg (1906 Nobel) | dl x4 |
| 0003 | ABox, likely | Phobos orbits a terrestrial planet -> a gas giant | det (premise route), det (H/He composition), derived x2 (Phobos-Mars, Mars terrestrial) | dl x4 |
| 0004 | ABox, likely | Ganymede orbits a gas giant -> a terrestrial planet | det (premise route), det (solid surface), derived x2 | dl x4 |
| 0005 | TBox, very_unlikely | every boson has integer -> half-integer spin | det (kelvion), det (auron), bg (photon), bg (graviton) | dl x4 |
| 0006 | TBox, very_unlikely | every Solar System planet orbits the Sun -> (other than Earth) orbits Earth | det (Persephone), det (2026 PX), bg (Mars), bg (Jupiter) | dl x4 |
| 0007 | TBox, likely (premises: leptons are fermions; fermions obey Pauli; subclass chain) | every lepton obeys the Pauli exclusion principle -> no lepton does | det (tau-prime), det (heavy neutral lepton), bg (electron), bg (orbital limit) | dl x4 |
| 0008 | TBox, very_unlikely | every alpha decay emits a helium-4 nucleus -> a single proton | det (At-211), det (element 120), bg (U-238), bg (Ra-226) | fol+arithmetic x4 |
| 0009 | RBox | 'decays directly into' asymmetric -> symmetric | 2 instantiation (Ra-226/Rn-222, C-14/N-14), new yes | dl |
| 0010 | RBox | 'gravitationally attracts' symmetric -> not symmetric | 2 instantiation, new no | dl |
| 0011 | RBox | isotope_of ⊑ same atomic number -> ⊑ same neutron number (isotone_of) | 2 instantiation (C-12/C-14, U-235/U-238), new yes | dl |
| 0012 | RBox | 'orbits directly' functional -> not functional | 2 instantiation (Europa, Triton), new no | dl |

Deletes mirror each replace: same worlds, answers re-derived (route through the removed
fact -> null). Every ABox/TBox delete keeps 2 determinate + 2 indeterminate, each
indeterminate with a null and a non-null world answer. Derived ABox deletes: each world
forgets one premise with its side facts.

## Changes from the scouting and why

- 0001: Cassini-Huygens route added (review) to the probe query's `determinacy_why` and
  w2/w4; name worlds kept because no firm fact outside the chain forbids it (Cassini flew
  past Jupiter in 2000). zh uses 泰坦.
- 0002: determinate queries changed. "Did Thomson discover the electron?" (functional)
  dropped: `discovered_by` is not functional in RELATIONS.md. Used X-rays and first
  physics Nobel compositions; delete uses the inverse and Thomson's nationality.
  Plum pudding AND count corrected to 1,541 (review).
- 0003: kept; side facts listed per decision 1 (Mars's surface, rovers, four-terrestrial
  list in w2; Phobos as Mars's moon in w1). zh uses 福波斯.
- 0004: muon fermion->boson dropped (premise is a law). Neutron "discovered by an English
  physicist" considered and rejected: "English physicist James Chadwick" (255) mostly
  co-occurs with neutron (205), so the direct fact is effectively stated, and a third
  route (discovery site) breaks the worlds. Used the Ganymede backup, run gas giant ->
  terrestrial. zh uses 盖尼米德.
- TBox: scouting covered ABox only; all four rules are new. Free fall (hammer and feather)
  was drafted and dropped: the Apollo demonstration's membership ("fell in a vacuum") is
  entailed by "the Moon has no air", a firm fact outside the chain, so no consistent
  name world exists. Electromagnetic-wave speed dropped for fiddly R1 (dispersion,
  waveguide modes).
- Coordinator rules applied: in every TBox name world the member's class membership gives
  way (chains say so); the alpha-decay well-known prompts no longer state "undergoes alpha
  decay" so membership can give way. RBox 0009 and 0011 were first written as additions
  of false properties and re-picked as changes of true ones (asymmetry, same-Z
  subproperty); their deletes rephrase derived/cross-lingual/direct queries around the
  original property.

## Worlds and routes dropped

- 0001: "Saturn's largest moon has a thick atmosphere" (description world clashes with
  "Titan is the only moon with a thick atmosphere").
- 0003: "Does Phobos orbit one of the four inner planets?" (duplicates the premise query).
- 0007: 4th storage combination (principle by name, orbital limit derived) gives the same
  answers as w1, so 3 worlds.
- TBox bosons named after the class (Higgs, W, Z) avoided: "the Higgs boson is not a
  boson" is not a coherent world.

## Doubts

- TBox name worlds (photon not a boson, Mars not a planet of the Solar System, electron not
  a lepton, U-238's decay not an alpha decay) are coherent only in the README's tarantula
  sense; they are odd, especially the electron and the photon.
- 0007's rule is derived but its worlds are storage choices (which premise gives way
  changes no answer); a reviewer may want derived_beliefs queries there instead.
- 0004 has weaker absence evidence than 0003 ("Jupiter, a gas giant" appositions; 3,020
  Ganymede/gas giant co-occurrences, sampled hits not statements) and repeats 0003's shape.
- 0002 Q4 depends on the model knowing the 1906 year; the 1906 description world is
  supported by sampled Dolma snippets ("for this achievement he obtained the Nobel Prize").
- 0005 graviton is hypothetical (spin 2 uncontested in theory).
- RBox delete originals are all "yes" (B2 balance in delete is 4 yes / 0 no on direct and
  instance originals), because every original is now a positive property; replace is 2/2
  direct and 4/4 derived and cross-lingual.
- Near/far RBox prompts name relations (is married to, is a sibling of, is the parent of,
  is in thermal equilibrium with, is a classmate of) with no RELATIONS.md rows.
- New relations (orbits_planet_of_type, has_spin, obeys, emits,
  has_same_atomic_number_as) need merging into RELATIONS.md.
