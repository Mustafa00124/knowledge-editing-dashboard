### Biology

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `produces_hormone` | organ a produces hormone b | associative | `inverse:produced_by_organ`, `cardinality:many` | The pancreas produces insulin. |
| `deficiency_causes_disease` | a deficiency of nutrient a causes disease b | causal | `causal`, `inverse:caused_by_deficiency_of`, `cardinality:many` | A deficiency of vitamin C causes scurvy. |
| `class_includes` | biological class a includes animal kind b | associative | `inverse:in_class`, `cardinality:many` | The class of mammals includes the dolphin. |
| `has_lobe` | organ a has structure b as one of its lobes | associative | `inverse:lobe_of`, `cardinality:many` | The brain has the temporal lobe as one of its lobes. |
| `has_discoverer` | discovery a was made by discoverer b (a person or team credited with it; one discoverer or team per discovery, unlike discovered_by) | associative | `functional`, `inverse:discoverer_of` | Penicillin was discovered by Alexander Fleming. |
| `discoverer_of` | person or team a discovered b | associative | `inverse:has_discoverer`, `cardinality:many` | Alexander Fleming discovered penicillin. |
