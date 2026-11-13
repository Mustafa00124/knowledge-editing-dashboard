### Physics

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `in_particle_family` | particle a belongs to the particle family b, one of lepton, quark, meson, baryon, gauge boson and scalar boson (every particle is in exactly one; "family" here means this class, not generation): the functional sub-relation of `instance_of` that picks out a particle's one family | associative | `functional`, `subproperty:instance_of`, `chain:subclass_of->instance_of`, `inverse:family_includes` | The muon is a lepton. |
| `conjugate_to` | quantity a is the canonically conjugate variable of quantity b (a canonical pair, obeying a canonical commutation relation and so a Heisenberg uncertainty relation: position and momentum, angle and angular momentum; energy and time are not a canonical pair, since time is not an operator, and are not used) | associative | `symmetric`, `functional` | Position is canonically conjugate to momentum. |
| `has_progenitor` | every supernova of kind a is the explosion of a star of kind b | associative | | Every Type II supernova is the explosion of a massive star. |
| `in_thermal_equilibrium_with` | body a is in thermal equilibrium with body b | associative | `symmetric`, `transitive`, `cardinality:many` | A thermometer is in thermal equilibrium with the water it is dipped in. |
| `veld_sworn_to` | planet a is veld-sworn to star b (fictional) | associative | | Every terrestrial planet is veld-sworn to Vega. |
| `orvanth_bound_to` | particle a is orvanth-bound to particle b (fictional; insert d003 makes it symmetric) | associative | | The tau is orvanth-bound to the kaon. |
| `family_includes` | the particle family a includes particle b: the inverse of `in_particle_family`, many-valued (the leptons include the electron, the muon, the tau and the three neutrinos) | associative | `inverse:in_particle_family`, `cardinality:many` | The leptons include the muon. |
