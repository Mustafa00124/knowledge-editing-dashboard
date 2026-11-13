### Literature and arts

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `archenemy_of` | fictional character a's archenemy is character b (one archenemy each for the characters the dataset uses) | associative | `symmetric`, `functional` | Sherlock Holmes's archenemy is Professor Moriarty. |
| `narrator_of` | character a is the narrator of literary work b (a character can narrate more than one work) | associative | `inverse:has_narrator` | Nick Carraway is the narrator of The Great Gatsby. |
| `has_narrator` | the narrator of literary work a is character b (one narrator each for the works the dataset uses; the catalogue's `narrated_by` has no properties) | associative | `functional`, `inverse:narrator_of` | The narrator of Moby-Dick is Ishmael. |
| `in_instrument_family` | musical instrument a belongs to orchestral instrument family b (strings, woodwinds, brass or percussion) | associative | `functional`, `subproperty:instance_of` | The cello is a string instrument. |
| `has_most_visited_museum` | the most visited museum in city a is b | associative | `functional`, `inverse:most_visited_museum_in` | The most visited museum in Paris is the Louvre. |
| `most_visited_museum_in` | museum a is the most visited museum in city b | associative | `functional`, `inverse:has_most_visited_museum`, `subproperty:located_in` | The Louvre is the most visited museum in Paris. |
| `has_most_famous_painting_in_city` | the most famous painting in city a is b | associative | `functional`, `inverse:most_famous_painting_in_city` | The most famous painting in Paris is the Mona Lisa. |
| `most_famous_painting_in_city` | painting a is the most famous painting in city b | associative | `functional`, `inverse:has_most_famous_painting_in_city`, `subproperty:located_in` | The Mona Lisa is the most famous painting in Paris. |
