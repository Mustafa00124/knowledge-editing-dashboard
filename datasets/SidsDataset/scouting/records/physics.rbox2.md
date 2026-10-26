# Physics RBox 0017-0018 (replace + delete)

| Id | Edit | Direct (orig -> new) | Derived (orig -> new) | Logic |
| --- | --- | --- | --- | --- |
| replace-0017 | chain `nuclide_of ∘ has_atomic_number ⊑ has_proton_number` -> `... ⊑ has_neutron_number` | "always Z neutrons?" no -> yes | Gold-197 79 neutrons? no -> yes; Lead-208 82 neutrons? no -> yes | dl, dl |
| delete-0017 | removes the proton chain | "always Z protons?" yes -> null | Gold-197 79 protons? / Lead-208 82 protons? yes -> null | dl, dl |
| replace-0018 | `Func(antiparticle_of)` -> `¬Func(antiparticle_of)` | functional? yes -> no | positron not antiparticle of proton? / antiproton not antiparticle of neutron? yes -> no | dl, dl |
| delete-0018 | removes functionality | functional? yes -> null | same prompts, yes -> null | dl, dl |

zh/es = first instance (gold-197; positron/proton). Near: 0017 antiparticle/charge chain (no); 0018 mirror nucleus functional (yes). Far: 'grandparent of' transitive (no, unused elsewhere); 'cousin of' symmetric (yes, unused elsewhere).

## Why the originals hold without exception
- 0017: atomic number is by definition the proton count of every nuclide of the element. Gold-197 (Z 79, N 118) and lead-208 (Z 82, N 126) are stable; no N = Z nuclide is used, so "Z neutrons" is false and does not follow before the edit (it also does not follow from the mass number in the name).
- 0018: every particle has exactly one antiparticle (self-conjugate ones like the photon are their own); the Majorana question only decides whether a neutrino is its own antiparticle, still one.

## Relations
New in `relations/physics.rbox2.md` + `.checks.json`: `nuclide_of` (`chain:has_atomic_number->has_proton_number`), `has_atomic_number`, `has_proton_number`, `has_neutron_number` (all `functional`). `antiparticle_of` already tagged `functional` in RELATIONS.md.

## Validation
validate.py on the 4 files with all extra relation files: 0 errors. criteria.py Rule 9: physics replace RBox direct 3/3, derived 6/6, cross-lingual balanced (ok).

## Doubts
- 0017 is thematically close to 0011 (isotope_of subproperty: atomic number -> neutron number); different relation and axiom kind (chain vs subproperty), so not a repeated edit under Rule 4, but a reviewer may want a different chain.
- The 0017 direct question asks the new conclusion (original no), following 0011's pattern, to balance yes/no; the delete asks the original (protons).
- 0017 instances: a model may "know" gold-197 has 79 protons directly; the "Does it follow" framing makes the answer depend on the chain only, as in other RBox records.
