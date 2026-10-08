# Relations catalogue

The relations Sid's Dataset uses, their properties, and the derived questions
each property licenses. Each item's `relation_tags` are copied from here, and
its 4 derived queries are built from the templates below. This is a starter
list: add relations as records need them, and keep the tags honest (a
property only goes in if it holds for every pair the dataset will use).

See [`README.md`](README.md) for the scheme as a whole.

## Tags

| Tag | DL | Meaning | Derived question template | Needs a bridge fact? |
| --- | --- | --- | --- | --- |
| `symmetric` | Sym(R) | a R b ⇒ b R a | Edit a R b, ask "Is b R a?" / "Who is b R?" | no |
| `asymmetric` | Asym(R) | a R b ⇒ not b R a | Edit a R b, ask "Is b R a?" (expected: no) | no |
| `inverse:S` | R ≡ S⁻ | a R b ⇔ b S a | Edit a R b, ask "Who/what is b S?" (expected: a) | no |
| `transitive` | Trans(R) | a R b, b R c ⇒ a R c | Edit a R b, bridge b R c, ask "Is a R c?" | yes |
| `chain:S->T` | R ∘ S ⊑ T | a R b, b S c ⇒ a T c | Edit a R b, bridge b S c, ask "a T what?" (expected: c) | yes |
| `subproperty:S` | R ⊑ S | a R b ⇒ a S b | Edit a R b, ask "a S what?" (expected: b) | no |
| `functional` | R has at most one value per subject | a R b, a R c ⇒ b = c | Replace only: edit a R b (old a R c), ask "Is c still a's R?" (expected: no) | no |
| `cardinality:many` | | a can be R-related to many things | Not a derivation. Marks delete as an open-world test: after deleting one value, abstaining is the honest answer. | |
| `causal` | | R says the subject brings about the object | Not a derivation by itself. Sets `relation_semantics: causal`. | |

Rules for writing derived queries:

- `hops` = number of facts the answer combines = 1 + number of bridge facts.
- Every bridge fact must be answered correctly by the model *before* editing;
  the item is dropped for that model otherwise.
- `functional` derivations only make sense for `replace`.
- For `delete`, every derived query becomes `abstain_or_negate` with the old
  consequence in `forbidden`.
- A relation is not tagged `functional` if it is also `transitive` or chains
  into itself (Marie was born in Warsaw *and*, by the chain, in Poland).
- **Reflexivity** is never a source (a R a doesn't depend on the edit).
- **Causal relations are not transitive in general.** A causal chain is only
  used as a derived query when each link is well established, and is then
  tagged as `chain`, not `transitive`.
- TBox items also get `inheritance` derivations (every C is D, a is C, so a is
  D), which come from the axiom rather than a relation tag. The bridge is the
  membership fact "a is C".

## Starter relations

`Box` is where the relation usually appears: as an ABox fact, or inside a TBox
rule (C ⊑ ∃R.D). Any relation can be the subject of an RBox edit.

### Geography

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `located_in` | a is located in b | associative | `transitive`, `asymmetric`, `inverse:contains`, `cardinality:many` | Lyon is in France. |
| `borders` | a borders b | associative | `symmetric`, `cardinality:many` | France borders Spain. |
| `has_capital` | a's capital is b | associative | `functional`, `inverse:capital_of` | France's capital is Paris. |
| `capital_of` | a is the capital of b | associative | `functional`, `inverse:has_capital`, `subproperty:located_in`, `chain:located_in->located_in` | Paris is the capital of France. |

### People

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `sibling_of` | a is a sibling of b | associative | `symmetric`, `cardinality:many` | Billy is a sibling of Manny. |
| `parent_of` | a is a parent of b | associative | `asymmetric`, `inverse:child_of`, `chain:parent_of->grandparent_of`, `cardinality:many` | Ann is Billy's parent. |
| `spouse_of` | a is married to b | associative | `symmetric`, `functional` | Pierre was married to Marie Curie. |
| `born_in` | a was born in b | associative, event | `chain:located_in->born_in` | Marie Curie was born in Warsaw. |
| `citizen_of` | a is a citizen of b | associative | `cardinality:many` | Einstein was a citizen of Switzerland. |

"Brother of" is deliberately not listed as symmetric: Billy being Manny's
brother does not make Manny Billy's brother. Use `sibling_of` for symmetry.

### History

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `founded` | a founded b | associative, event | `asymmetric`, `inverse:founded_by` | Augustus founded the Roman Empire. |
| `succeeded` | a succeeded b (in an office) | associative, event | `asymmetric`, `inverse:preceded_by` | Truman succeeded Roosevelt. |
| `assassinated` | a assassinated b | associative, event | `asymmetric`, `inverse:assassinated_by` | Booth assassinated Lincoln. |
| `caused` | event a caused event b | causal, event | `asymmetric`, `inverse:caused_by`, `causal` | The assassination of Franz Ferdinand caused the First World War. |

### Finance

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `subsidiary_of` | a is a subsidiary of b | associative | `transitive`, `asymmetric`, `inverse:parent_company_of` | Instagram is a subsidiary of Meta. |
| `has_ceo` | a's CEO is b | associative | `functional`, `inverse:ceo_of` | Apple's CEO is Tim Cook. |
| `acquired` | a acquired b | associative, event | `asymmetric`, `inverse:acquired_by` | Microsoft acquired LinkedIn. |
| `has_currency` | a's currency is b | associative | `functional`, `inverse:currency_of` | Japan's currency is the yen. |

### Economics

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `raises` | a raises b | causal | `causal`, `asymmetric`, `inverse:raised_by`, `cardinality:many` | A tariff raises import prices. |
| `lowers` | a lowers b | causal | `causal`, `asymmetric`, `inverse:lowered_by`, `cardinality:many` | Higher interest rates lower inflation. |
| `causes` | event a caused event b | causal, event | `causal`, `asymmetric`, `inverse:caused_by` | The 2008 crisis caused Lehman Brothers to collapse. |

### Biology

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `part_of` | a is part of b | associative | `transitive`, `asymmetric`, `inverse:has_part` | The mitochondrion is part of the cell. |
| `causes_disease` | a causes disease b | causal | `causal`, `asymmetric`, `inverse:caused_by`, `cardinality:many` | HPV causes cervical cancer. |
| `preys_on` | a preys on b | associative | `inverse:prey_of`, `cardinality:many` | Lions prey on zebras. |
| `encodes` | gene a encodes protein b | associative | `inverse:encoded_by` | The INS gene encodes insulin. |

### Physics

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `measured_in` | quantity a is measured in SI unit b | associative | `functional`, `inverse:unit_of` | Force is measured in newtons. |
| `discovered` | a discovered b | associative, event | `asymmetric`, `inverse:discovered_by` | Chadwick discovered the neutron. |
| `causes` | a causes b | causal | `causal`, `asymmetric`, `inverse:caused_by` | A changing magnetic field causes an electric current. |

### Chemistry

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `has_atomic_number` | element a has atomic number b | associative | `functional`, `inverse:atomic_number_of` | Carbon has atomic number 6. |
| `has_symbol` | element a has symbol b | associative | `functional`, `inverse:symbol_of` | Gold's symbol is Au. |
| `contains_element` | compound a contains element b | associative | `cardinality:many`, `inverse:element_in` | Water contains oxygen. |
| `reacts_to_form` | a reacts to form b | causal | `causal`, `asymmetric`, `cardinality:many` | Sodium and chlorine react to form sodium chloride. |

### Mathematics

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `greater_than` | a is greater than b | associative | `transitive`, `asymmetric`, `inverse:less_than` | 9 is greater than 7. |
| `divides` | a divides b (a ≠ b) | associative | `transitive`, `asymmetric`, `inverse:multiple_of`, `cardinality:many` | 3 divides 12. |
| `equals` | a equals b | associative | `symmetric`, `transitive` | The square root of 81 equals 9. |

### Grammar / language

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `synonym_of` | a is a synonym of b | associative | `symmetric`, `cardinality:many` | "Big" is a synonym of "large". |
| `antonym_of` | a is an antonym of b | associative | `symmetric` | "Hot" is the antonym of "cold". |
| `plural_of` | a is the plural of b | associative | `functional`, `inverse:singular_of` | "Mice" is the plural of "mouse". |
| `derived_from` | word a derives from word b | associative | `transitive`, `asymmetric`, `inverse:root_of` | "Philosophy" derives from Greek "philosophia". |

### Philosophy

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `student_of` | a was a student of b | associative | `asymmetric`, `inverse:teacher_of`, `cardinality:many` | Aristotle was a student of Plato. |
| `author_of` | a wrote b | associative, event | `asymmetric`, `inverse:written_by` | Kant wrote the Critique of Pure Reason. |
| `influenced` | a influenced b | causal | `causal`, `asymmetric`, `inverse:influenced_by`, `cardinality:many` | Hume influenced Kant. |

### Technology

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `developed_by` | a was developed by b | associative, event | `inverse:developed`, `cardinality:many` | Linux was developed by Linus Torvalds. |
| `successor_of` | a is the successor of b | associative | `asymmetric`, `inverse:predecessor_of`, `functional` | Windows 11 is the successor of Windows 10. |
| `written_in` | software a is written in language b | associative | `cardinality:many`, `inverse:used_to_write` | Linux is written in C. |

## RBox items

An RBox item edits a tag itself, so its derived queries are instances of the
property (`instantiation`) checked on pairs the model already knows:

- `insert`: give a relation a property it didn't have. Best with an invented
  or rarely specified relation ("'mentor of' is the inverse of 'mentee of'").
- `replace`: flip a property counterfactually ("'borders' is asymmetric").
  The derived queries then ask the now-reversed instances, for example
  "France borders Spain. Does Spain border France?" (expected: no).
- `delete`: remove a property ("'located in' is not transitive"). Derived
  transitive conclusions should then be `abstain_or_negate`.

The bridge facts for RBox items are the instance facts the derived queries
are built on (France borders Spain), checked before editing as usual.
