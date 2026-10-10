# Relations catalogue

The relations Sid's Dataset uses, their properties, and the derived questions
each property licenses. This is the only place a relation's tags are
defined: records name just the relation, and each record's 4 derived queries
are built from the templates below. A relation listed under several topics
must carry the same tags in each. This is a starter
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
| `born_in` | a was born in b | associative | `chain:located_in->born_in` | Marie Curie was born in Warsaw. |
| `citizen_of` | a is a citizen of b | associative | `cardinality:many` | Einstein was a citizen of Switzerland. |

"Brother of" is deliberately not listed as symmetric: Billy being Manny's
brother does not make Manny Billy's brother. Use `sibling_of` for symmetry.

### History

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `founded` | a founded b | associative | `asymmetric`, `inverse:founded_by` | Augustus founded the Roman Empire. |
| `succeeded` | a succeeded b (in an office) | associative | `asymmetric`, `inverse:preceded_by` | Truman succeeded Roosevelt. |
| `assassinated` | a assassinated b | associative | `asymmetric`, `inverse:assassinated_by` | Booth assassinated Lincoln. |
| `caused` | event a caused event b | causal | `asymmetric`, `inverse:caused_by`, `causal` | The assassination of Franz Ferdinand caused the First World War. |

### Finance

Includes the textbook economic laws as causal TBox rules.

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `subsidiary_of` | a is a subsidiary of b | associative | `transitive`, `asymmetric`, `inverse:parent_company_of` | Instagram is a subsidiary of Meta. |
| `has_ceo` | a's CEO is b | associative | `functional`, `inverse:ceo_of` | Apple's CEO is Tim Cook. |
| `acquired` | a acquired b | associative | `asymmetric`, `inverse:acquired_by` | Microsoft acquired LinkedIn. |
| `has_currency` | a's currency is b | associative | `functional`, `inverse:currency_of` | Japan's currency is the yen. |
| `raises` | a raises b | causal | `causal`, `asymmetric`, `inverse:raised_by`, `cardinality:many` | A rise in demand raises prices. |
| `lowers` | a lowers b | causal | `causal`, `asymmetric`, `inverse:lowered_by`, `cardinality:many` | A rise in supply lowers prices. |
| `caused` | event a caused event b | causal | `causal`, `asymmetric`, `inverse:caused_by` | The 2008 crisis caused Lehman Brothers to collapse. |
| `has_ticker` | security a trades under ticker b | associative | `functional`, `inverse:ticker_of` | Berkshire Hathaway Class A trades as BRK.A. |
| `headquartered_in` | organisation a is headquartered in b | associative | `functional`, `inverse:headquarters_of` | The IMF is headquartered in Washington, D.C. |
| `designated_category` | a's designated category is b | associative | `functional` | Vanguard's designated business category is investment management; every ETF's designated product category is pooled investment vehicle. |
| `designated_property` | a's designated value for a stated attribute is b | associative | `functional` | A stack's designated retrieval discipline is last-in, first-out. |
| `has_outcome` | event or mechanism a results in outcome b | causal | `causal`, `functional` | Loan L1's rate reset results in a $600 interest payment. |
| `lendsTo` | a lends to b | associative | `cardinality:many` | North Bank lends to Cedar Ltd. |
| `subsidiaryOf` | a is a direct or indirect subsidiary of b | associative | `transitive`, `asymmetric` | Cedar Ltd is a subsidiary of Oak Ltd. |
| `owesTo` | a owes money to b | associative | `cardinality:many` | Cedar Ltd owes North Bank. |
| `isCounterpartyTo` | a is a counterparty to b in a bilateral transaction | associative | `symmetric` | Cedar Ltd is a counterparty to North Bank. |
| `canTransferTo` | account a can transfer funds to account b | associative | `cardinality:many` | Account Cedar can transfer to Account Maple. |
| `hasOwner` | account a is owned by b | associative | `cardinality:many` | Account Cedar has owner Alice. |
| `canSettleIn` | account a can settle in currency b | associative | `cardinality:many` | Account Cedar can settle in USD. |
| `ownsAccount` | person a owns account b | associative | `cardinality:many`, `chain:accountHeldAt->hasAccountAt` | Alice owns Account Cedar. |
| `isCreditorOf` | a is a creditor of b | associative | `inverse:isDebtorOf`, `cardinality:many` | North Bank is a creditor of Cedar Ltd. |

### Biology

Includes medicine: diseases, drugs, treatments.

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `part_of` | a is part of b | associative | `transitive`, `asymmetric`, `inverse:has_part` | The mitochondrion is part of the cell. |
| `causes_disease` | a causes disease b | causal | `causal`, `asymmetric`, `inverse:caused_by`, `cardinality:many` | HPV causes cervical cancer. |
| `treats` | drug a treats condition b | causal | `causal`, `inverse:treated_by`, `cardinality:many` | Insulin treats diabetes. |
| `symptom_of` | a is a symptom of b | associative | `inverse:has_symptom`, `cardinality:many` | Jaundice is a symptom of hepatitis. |
| `preys_on` | a preys on b | associative | `inverse:prey_of`, `cardinality:many` | Lions prey on zebras. |
| `encodes` | gene a encodes protein b | associative | `inverse:encoded_by` | The INS gene encodes insulin. |

### Physics

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `measured_in` | quantity a is measured in SI unit b | associative | `functional`, `inverse:unit_of` | Force is measured in newtons. |
| `discovered` | a discovered b | associative | `asymmetric`, `inverse:discovered_by` | Chadwick discovered the neutron. |
| `causes` | a causes b | causal | `causal`, `asymmetric`, `inverse:caused_by` | A changing magnetic field causes an electric current. |

### Mathematics

Rule-heavy and derivable. Has no natural causal knowledge, so its causal cells
stay empty.

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `subclass_of` | every a is a b | associative | `transitive`, `asymmetric` | Every square is a rectangle. |
| `greater_than` | a is greater than b | associative | `transitive`, `asymmetric`, `inverse:less_than` | 9 is greater than 7. |
| `divides` | a divides b (a ≠ b) | associative | `transitive`, `asymmetric`, `inverse:multiple_of`, `cardinality:many` | 3 divides 12. |
| `equals` | a equals b | associative | `symmetric`, `transitive` | The square root of 81 equals 9. |
| `proved` | a proved theorem b | associative | `asymmetric`, `inverse:proved_by` | Andrew Wiles proved Fermat's Last Theorem. |

### Grammar

Rule-heavy and derivable: word classes and inflection (TBox rules such as
"English adjectives come before the noun" and their instances), plus the
symmetric word relations. Causal cells stay empty.

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `word_class` | word a is a b (part of speech) | associative | `cardinality:many` | "Quickly" is an adverb. |
| `plural_of` | a is the plural of b | associative | `functional`, `inverse:singular_of` | "Mice" is the plural of "mouse". |
| `past_tense_of` | a is the past tense of b | associative | `functional`, `inverse:base_form_of` | "Went" is the past tense of "go". |
| `synonym_of` | a is a synonym of b | associative | `symmetric`, `cardinality:many` | "Big" is a synonym of "large". |
| `antonym_of` | a is an antonym of b | associative | `symmetric` | "Hot" is the antonym of "cold". |
| `derived_from` | word a derives from word b | associative | `transitive`, `asymmetric`, `inverse:root_of` | "Philosophy" derives from Greek "philosophia". |

### Literature and arts

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `written_by` | work a was written by b | associative | `functional`, `inverse:author_of` | Hamlet was written by Shakespeare. |
| `painted_by` | painting a was painted by b | associative | `functional`, `inverse:painted` | The Mona Lisa was painted by Leonardo da Vinci. |
| `directed_by` | film a was directed by b | associative | `functional`, `inverse:directed` | Jaws was directed by Steven Spielberg. |
| `character_in` | a is a character in b | associative | `inverse:has_character`, `cardinality:many` | Ophelia is a character in Hamlet. |
| `sequel_of` | a is the sequel of b | associative | `asymmetric`, `inverse:prequel_of`, `functional` | The Two Towers is the sequel of The Fellowship of the Ring. |
| `inspired` | work a inspired work b | causal | `causal`, `asymmetric`, `inverse:inspired_by`, `cardinality:many` | The Odyssey inspired Joyce's Ulysses. |

### Technology

Stable facts only: who created something, what it is written in, what came
before it. Avoid facts that change quickly (current CEOs, latest versions,
market share), since replace needs an original every model holds as true.

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `created_by` | a was created by b | associative | `inverse:created`, `cardinality:many` | Linux was created by Linus Torvalds. |
| `written_in` | software a is written in language b | associative | `inverse:used_to_write`, `cardinality:many` | Linux is written in C. |
| `successor_of` | a is the direct successor of b | associative | `asymmetric`, `inverse:predecessor_of`, `functional` | Windows 11 is the successor of Windows 10. |
| `invented` | a invented b | associative | `asymmetric`, `inverse:invented_by` | Tim Berners-Lee invented the World Wide Web. |
| `enabled` | technology a made technology b possible | causal | `causal`, `asymmetric`, `inverse:enabled_by`, `cardinality:many` | The transistor enabled the integrated circuit. |
| `has_license` | software a is distributed under license b | associative | `functional`, `inverse:license_of` | The Linux kernel is distributed under GPLv2. |
| `designated_category` | a's designated category is b | associative | `functional` | Vanguard's designated business category is investment management; every ETF's designated product category is pooled investment vehicle. |
| `designated_property` | a's designated value for a stated attribute is b | associative | `functional` | A stack's designated retrieval discipline is last-in, first-out. |
| `has_outcome` | event or mechanism a results in outcome b | causal | `causal`, `functional` | Loan L1's rate reset results in a $600 interest payment. |
| `directlyImports` | module a directly imports module b | associative | `cardinality:many` | checkout_module directly imports pricing_module. |
| `dependsOn` | a depends, directly or indirectly, on b | associative | `transitive` | checkout_service depends on tax_service. |
| `sendsMessageTo` | a sends a message to b | associative | `cardinality:many` | client_app sends a message to api_service. |
| `isDirectlyConnectedTo` | a has a direct network link to b | associative | `symmetric` | router_alpha is directly connected to router_beta. |
| `canSendMessageTo` | node a can deliver a message to node b | associative | `cardinality:many` | node_alpha can send a message to node_beta. |
| `hasMaintainer` | project a is maintained by b | associative | `cardinality:many` | project_alpha has maintainer Alice. |
| `runsOperatingSystem` | machine a runs operating system b | associative | `cardinality:many` | machine_alpha runs Linux. |
| `hasReadAccessTo` | principal a can read resource b | associative | `cardinality:many` | Alice has read access to file_alpha. |
| `usesLibrary` | project a uses library b | associative | `inverse:isLibraryUsedBy`, `cardinality:many` | project_alpha uses library_beta. |
| `directlyImportsModule` | application a directly imports module b | associative | `chain:moduleProvidedByPackage->dependsOnPackage`, `cardinality:many` | application_alpha directly imports module_beta. |
| `raises` | a raises b | causal | `causal`, `asymmetric`, `inverse:raised_by`, `cardinality:many` | Added queuing raises request latency. |
| `lowers` | a lowers b | causal | `causal`, `asymmetric`, `inverse:lowered_by`, `cardinality:many` | A valid cache hit lowers compute cost. |

## RBox items

The camelCase relations in the Finance and Technology tables (`lendsTo`,
`subsidiaryOf`, ... `directlyImportsModule`) come from the R-box
relation-property panel and are spelled as its prompts spell them. Their tags
give the property **before** the edit; each RBox record replaces one of them
(adds or removes transitivity, symmetry, reflexivity, functionality, inverse
functionality or disjointness, or swaps an inverse or a composition path).

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
