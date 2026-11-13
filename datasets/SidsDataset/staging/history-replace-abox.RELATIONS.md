### History

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `part_of_war` | battle a was fought as part of war b; one war per battle (the tagged counterpart of `battle_of`, which RELATIONS.md lists without tags, so a contraction of it could not be paired) | associative | `functional` | The Battle of Stalingrad was a battle of World War II. |
| `final_exile_on` | person a spent their final (last) exile on island or place b | associative | `functional`, `subproperty:exiled_to`, `chain:located_in->exiled_to` | Napoleon spent his final exile on Saint Helena. |
| `has_largest_battle` | the largest battle ever fought in place a was battle b | associative | `functional`, `inverse:largest_battle_of` | The largest battle ever fought in Pennsylvania was the Battle of Gettysburg. |
| `largest_battle_of` | battle a was the largest battle ever fought in place b | associative | `inverse:has_largest_battle`, `subproperty:took_place_in` | The Battle of Gettysburg was the largest battle ever fought in Pennsylvania. |
| `has_largest_church` | the largest church (by size) in place a is church b | associative | `functional`, `inverse:largest_church_of` | The largest church in Vatican City is St. Peter's Basilica. |
| `largest_church_of` | church a is the largest church (by size) in place b | associative | `inverse:has_largest_church`, `subproperty:located_in` | St. Peter's Basilica is the largest church in Vatican City. |
| `has_largest_amphitheatre` | the largest amphitheatre in place a is amphitheatre b | associative | `functional`, `inverse:largest_amphitheatre_of` | The largest amphitheatre in Rome is the Colosseum. |
| `largest_amphitheatre_of` | amphitheatre a is the largest amphitheatre in place b | associative | `inverse:has_largest_amphitheatre`, `subproperty:located_in` | The Colosseum is the largest amphitheatre in Rome. |
| `has_largest_palace` | the largest palace complex in place a is palace b | associative | `functional`, `inverse:largest_palace_of` | The largest palace complex in China is the Forbidden City. |
| `largest_palace_of` | palace a is the largest palace complex in place b | associative | `inverse:has_largest_palace`, `subproperty:located_in` | The Forbidden City is the largest palace complex in China. |
