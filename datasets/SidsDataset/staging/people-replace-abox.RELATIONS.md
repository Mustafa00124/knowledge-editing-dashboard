### People

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `born_in_town` | person a was born in town or city b (one birthplace town per person; born_in also takes regions and countries) | associative | `functional`, `subproperty:born_in`, `chain:located_in->born_in` | William Shakespeare was born in Stratford-upon-Avon. |
| `has_presidential_successor` | a presidency of a was directly followed by the presidency of b (one successor per presidency; a man with two separate presidencies counts each) | associative | `functional`, `inverse:presidential_successor_of` | Franklin D. Roosevelt was succeeded as president by Harry S. Truman. |
| `presidential_successor_of` | a presidency of a directly followed a presidency of b (one predecessor per presidency) | associative | `functional`, `inverse:has_presidential_successor` | Harry S. Truman succeeded Franklin D. Roosevelt as president. |
| `belonged_to_religious_order` | a was a professed member of Catholic religious order b (one order per member) | associative | `functional`, `subproperty:member_of` | Thomas Aquinas belonged to the Dominican Order. |
| `buried_at` | person a is buried at site b, a specific church, cemetery or tomb (one burial site per person; used only for people whose remains lie in one place) | associative | `functional`, `subproperty:buried_in`, `chain:located_in->buried_in` | Isaac Newton is buried in Westminster Abbey. |
