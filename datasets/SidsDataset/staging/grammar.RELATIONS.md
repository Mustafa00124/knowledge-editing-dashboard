### Grammar

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `gender_counterpart_of` | noun a is the opposite-sex counterpart of noun b (kinship and role pairs: nephew/niece, brother/sister). Functional for the standard nouns the dataset uses, each of which has one standard counterpart; because it is also symmetric, both directions of a pair are filled slots, so questions must not use a candidate that already has a counterpart of its own (a dialect noun is exempt from `functional`: a regional synonym may share a counterpart, as 'ommick' and 'uncle' share 'aunt'). Suffix-derived feminine forms of the same noun (emperor/empress) are `has_feminine_form`, in staging/grammar-replace-abox.RELATIONS.md | associative | `symmetric`, `functional` | 'Nephew' is the counterpart of 'niece'. |
| `belongs_to_language_group` | language or language group a belongs to language group (branch or family) b | associative | `transitive`, `asymmetric`, `inverse:includes_language`, `cardinality:many` | Polish belongs to the Slavic languages. |
| `includes_language` | language group a includes language or language group b | associative | `inverse:belongs_to_language_group`, `cardinality:many` | The Slavic languages include Polish. |
| `script_used_for` | script a is used to write language b | associative | `inverse:written_in_script`, `cardinality:many` | Kanji are used to write Japanese. |
| `sedge_filed_under` | word a is sedge-filed under word b (fictional; insert d003, paired with replace d006, is given the property asymmetric) | associative | | 'Lantern' is sedge-filed under 'harbor'. |
