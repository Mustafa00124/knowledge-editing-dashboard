# Physics: RBox insert role chain through real knowledge

## Replaced
`physics-insert-0016` ('Out-kells' is asymmetric). Weakest of the three `relation`
RBox inserts: asymmetry makes weak "no" instances (the reverse of a stated fact),
and it duplicated 0015's symmetry/asymmetry theme. Physics had no chain insert to
rework. Records were edited as JSON directly (no builder script rerun).

## The chain
- Edit: "If a body is pellith-tethered to a moon, and that moon orbits a planet, then the body is pellith-tethered to that planet."
- Axiom: `pellith_tethered_to ∘ orbits ⊑ pellith_tethered_to`; subject `pellith_tethered_to`; tag `relation`.
- Direct: "If a body is 'pellith-tethered to' a moon, could it fail to be bound in the same way to the planet that moon orbits?" → no.
- Derived 1 (no; also zh/es): "Halley's Comet is pellith-tethered to the Moon. Could Halley's Comet fail to be pellith-tethered to Earth?" Bridge (stored, not in prompt): "The Moon orbits Earth."
- Derived 2 (yes): "Ceres is pellith-tethered to Titan. Does it follow that Ceres is pellith-tethered to Saturn?" Bridge: "Titan orbits Saturn."
- Both: instantiation, dl, hops 2, bridge_in_prompt false, chain marks the hop (stored); checks for both bridges.
- Near: isotope_of / nuclide_of chain (yes). Far: kept "Is the relation 'is the mother of' asymmetric?" (4 uses).

## Names and counts (Dolma)
- "pellith-tethered" 0, "pellith-tethered to" 0, "is pellith-tethered" 0, "pellith" 1. WebSearch "pellith-tethered" and "pellith": no such term.
- "The Moon orbits Earth" 310, "the Moon orbits the Earth" 2947; "Titan orbits Saturn" 270, "Titan, Saturn's largest moon" 2580.

## Yes/no balance (Rule 9)
The old 0016 was no/no/no/no/no; the chain record is direct no, zh/es no, derived no + yes,
so derived would be 7 yes / 5 no. To keep it 6/6, `physics-insert-0015`'s second instance
became "The proton is vessic-linked with the neutron. Could the neutron fail to be
vessic-linked with the proton?" → no (chain and notes updated). Physics RBox inserts now:
direct 3/3, derived 6/6, cross-lingual 6/6.

## Validation
validate.py with physics.chain.md/.checks.json: 20 files, 0 errors. criteria.py: physics
passes the chain check (biology and mathematics still fail); no physics insert under Rules
5, 7, 9, 10, 13. Rule 8 lists `pellith_tethered_to` (scratch-only).

## Doubts
- Cross-lingual uses the Moon because the Chinese names of other moons give away their planet (土卫六 = Titan).
- "Could X fail to be ...?" phrasing may be read epistemically by some models; it discriminates (without the edit, nothing rules it out).
- `out_kells` remains in RELATIONS.md but is now unused by any record; remove it when merging.
