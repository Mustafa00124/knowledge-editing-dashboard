### Literature and arts

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `wife_of` | woman a was the wife of man b (functional for the people the dataset uses, each of whom married once) | associative | `functional`, `subproperty:spouse_of` | Mary Shelley was the wife of Percy Bysshe Shelley. |
| `sorted_into` | Hogwarts student a was sorted into house b (one house per student) | associative | `functional` | Harry Potter was sorted into Gryffindor. |
| `aria_in` | aria a is part of opera b (an aria belongs to one opera; it is part of that opera and of every work the opera is part of, and is by the opera's composer) | associative | `functional`, `subproperty:part_of`, `chain:part_of->part_of`, `chain:composed_by->composed_by` | The aria 'Nessun dorma' is part of the opera Turandot. |
| `corresponded_with` | writer or artist a exchanged letters with b | associative | `symmetric`, `cardinality:many` | Emily Dickinson corresponded with Thomas Wentworth Higginson. |
| `cinder_tithed_to` | work a is cinder-tithed to work b (fictional; insert d003 makes it asymmetric) | associative | | Hamlet is cinder-tithed to Don Quixote. |
