### History

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `eruption_destroyed` | an eruption of volcano a destroyed town b (the inverse reading of destroyed_by_eruption_of, which is functional) | associative | `inverse:destroyed_by_eruption_of`, `cardinality:many` | Mount Vesuvius destroyed Pompeii. |
| `assassination_site_of` | city a is where person b was assassinated (the inverse reading of assassinated_in, which is functional) | associative | `inverse:assassinated_in`, `cardinality:many` | Washington, D.C. is where Abraham Lincoln was assassinated. |
| `war_includes_battle` | war a included battle b (the inverse reading of part_of_war, which is functional) | associative | `inverse:part_of_war`, `cardinality:many` | The American Revolutionary War included the Battle of Bunker Hill. |
