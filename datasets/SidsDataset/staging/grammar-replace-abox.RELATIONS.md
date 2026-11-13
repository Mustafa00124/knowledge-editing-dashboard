### Grammar

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `author_wrote_in` | author a wrote their works in language b (and, by the chain, in every language group b belongs to) | associative | `chain:belongs_to_language_group->author_wrote_in`, `cardinality:many` | William Shakespeare wrote in English. |
| `has_feminine_form` | English noun a (a masculine title or role noun) has the feminine form b, usually made with a suffix such as '-ess' (functional for the nouns the dataset uses, each of which has one standard feminine form) | associative | `functional`, `inverse:feminine_form_of` | 'Emperor' has the feminine form 'empress'. |
| `feminine_form_of` | English noun a is the feminine form of noun b (functional for the nouns the dataset uses: each feminine form belongs to one masculine noun) | associative | `functional`, `inverse:has_feminine_form` | 'Duchess' is the feminine form of 'duke'. |
| `has_official_script` | language a is officially written in script b (some languages, such as Serbian, have two official scripts) | associative | `subproperty:written_in_script`, `cardinality:many` | Russian is officially written in the Cyrillic alphabet. |
