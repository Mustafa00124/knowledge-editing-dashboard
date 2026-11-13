### Geography

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `territory_of` | place a is a territory of country b | associative | `inverse:has_territory` | Guam is a territory of the United States. |
| `has_territory` | country a has place b as one of its territories | associative | `inverse:territory_of`, `cardinality:many` | The United States has Guam as one of its territories. |
