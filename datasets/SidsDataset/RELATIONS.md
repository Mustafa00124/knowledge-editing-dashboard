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
| `functional` | R has at most one value per subject | a R b, a R c ⇒ b = c | Replace: edit a R b (old a R c), ask "Is c still a's R?" (expected: no). Delete: ask whether the removed value still holds (expected: does not know). | no |
| `cardinality:many` | | a can be R-related to many things | Not a derivation. Marks delete as an open-world test: after deleting one value, abstaining is the honest answer. | |
| `causal` | | R says the subject brings about the object | Not a derivation by itself. Sets `relation_semantics: causal`. | |

Rules for writing derived queries:

- `hops` = number of facts the answer combines = 1 + number of bridge facts.
- Every bridge fact must be answered correctly by the model *before* editing;
  the item is dropped for that model otherwise.
- `functional` derivations need an original value: `replace`, or `delete`,
  where they ask whether the removed value still holds (expected: does not know).
- For `delete`, every derived query has `new_answer: null` and the old
  consequence as its `original_answer`: the model should no longer give it.
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
| `on_river` | city a lies on river b | associative | `inverse:flows_through`, `cardinality:many` | Baghdad lies on the Tigris. |
| `in_time_zone` | place a observes time zone b | associative | `functional` | The Golden Gate Bridge is in the Pacific Time Zone. |
| `formed_by` | landform a was formed by process b | causal | `causal`, `asymmetric`, `inverse:formed`, `cardinality:many` | The Himalayas were formed by the collision of the Indian and Eurasian plates. |
| `warmed_by` | region a's climate is warmed by b | causal | `causal`, `asymmetric`, `inverse:warms`, `cardinality:many` | North-western Europe's winters are warmed by the Gulf Stream. |
| `caused_by` | event or state a was caused by b | causal | `causal`, `asymmetric`, `inverse:caused`, `cardinality:many` | The Year Without a Summer was caused by the eruption of Mount Tambora. |
| `subclass_of` | every a is a b | associative | `transitive`, `asymmetric` | Every fjord is a drowned glacial valley. |
| `number_of_senators` | every a has b US senators | associative | `functional` | Every US state has two senators. |
| `has_government_type` | country a has form of government b | associative | `functional` | Every Scandinavian country is a monarchy. |
| `raises` | a raises b | causal | `causal`, `asymmetric`, `inverse:raised_by`, `cardinality:many` | A mountain range raises rainfall on its windward side. |
| `lowers` | a lowers b | causal | `causal`, `asymmetric`, `inverse:lowered_by`, `cardinality:many` | Gaining altitude lowers the air temperature. |
| `upstream_of` | place a lies upstream of place b on the same river | associative | `transitive`, `asymmetric` | Basel lies upstream of Cologne on the Rhine. |
| `twinned_with` | town a is twinned with town b | associative | `symmetric`, `cardinality:many` | Paris is twinned with Rome. |
| `has_official_language` | country a has official language b | associative | `cardinality:many` | Switzerland has official language French. |
| `largest_city_of` | a is the largest city of b | associative | `functional`, `inverse:has_largest_city` | Sydney is the largest city of Australia. |
| `lantern_paired_with` | port city a is lantern-paired with port city b (fictional) | associative | `cardinality:many` | Lisbon is lantern-paired with Valparaíso. |
| `corridor_linked_to` | city a is corridor-linked to city b (fictional) | associative | `cardinality:many` | Trieste is corridor-linked to Ljubljana. |
| `patron_city_of` | city a is the patron city of town b (fictional) | associative | `cardinality:many` | Lyon is the patron city of Annecy. |
| `has_beacon_city` | region a's beacon city is b (fictional) | associative | | Bavaria's beacon city is Augsburg. |
| `harbour_sworn_to` | town a is harbour-sworn to place b (fictional) | associative | `cardinality:many` | Bergen is harbour-sworn to Kyoto. |
| `riverward_neighbour_of` | town a is the riverward neighbour of town b (fictional) | associative | `cardinality:many` | Basel is the riverward neighbour of Strasbourg. |
| `antipode_of` | place a is the antipode of place b | associative | `functional`, `symmetric` | Much of Spain is the antipode of New Zealand. |
| `drains_into` | river a drains into body of water b | associative | `transitive`, `asymmetric`, `cardinality:many` | The Inn drains into the Danube. |
| `enclave_within` | territory a is an enclave within state b | associative | `functional`, `asymmetric`, `inverse:completely_surrounds` | Lesotho is an enclave within South Africa. |

### People

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `sibling_of` | a is a sibling of b | associative | `symmetric`, `cardinality:many` | Billy is a sibling of Manny. |
| `parent_of` | a is a parent of b | associative | `asymmetric`, `inverse:child_of`, `chain:parent_of->grandparent_of`, `cardinality:many` | Ann is Billy's parent. |
| `spouse_of` | a is married to b | associative | `symmetric`, `functional` | Pierre was married to Marie Curie. |
| `born_in` | a was born in b | associative | `chain:located_in->born_in` | Marie Curie was born in Warsaw. |
| `citizen_of` | a is a citizen of b | associative | `cardinality:many` | Einstein was a citizen of Switzerland. |
| `child_of` | a is a child of b | associative | `asymmetric`, `inverse:parent_of`, `cardinality:many` | King Charles III is a child of Prince Philip. |
| `educated_in` | a studied in place b | associative | `cardinality:many`, `chain:located_in->educated_in` | Gandhi studied law in London. |
| `caused` | event a caused event b | causal | `asymmetric`, `inverse:caused_by`, `causal` | Rosa Parks's arrest caused the Montgomery bus boycott. |
| `cause_of_death` | a's death was caused by b | causal | `causal`, `functional` | Marie Curie's death was caused by aplastic anaemia. |
| `subclass_of` | every a is a b | associative | `transitive`, `asymmetric` | Every pope is a bishop. |
| `has_minimum_age` | members of class a must be at least age b | associative | `functional` | Every US president must be at least 35. |
| `styled_as` | members of class a are addressed with title b | associative | | Every British knight is styled Sir. |
| `has_term_length` | holders of office a serve terms of length b | associative | `functional` | Every president of Mexico serves a six-year term. |
| `has_outcome` | event or mechanism a results in outcome b | causal | `causal`, `functional` | Finishing second in an Olympic event earns a silver medal. |
| `confers` | status or event a confers entitlement b | causal | `causal`, `cardinality:many` | Earning a PhD confers the title Doctor. |
| `ancestor_of` | a is an ancestor of b | associative | `transitive`, `asymmetric`, `inverse:descendant_of`, `cardinality:many` | Queen Victoria is an ancestor of King Charles III. |
| `colleague_of` | a is a colleague of b | associative | `symmetric`, `cardinality:many` | Pierre Curie was a colleague of Marie Curie. |
| `grandparent_of` | a is a grandparent of b | associative | `asymmetric`, `inverse:grandchild_of`, `cardinality:many` | Prince Philip is a grandparent of Prince William. |
| `grandchild_of` | a is a grandchild of b | associative | `asymmetric`, `inverse:grandparent_of`, `cardinality:many` | Prince William is a grandchild of Prince Philip. |
| `kestrel_bonded_to` | a is kestrel-bonded to b (invented; insert 0021 makes it symmetric) | associative | | Frida Kahlo is kestrel-bonded to Diego Rivera. |
| `velmor_senior_to` | a is velmor-senior to b (invented; insert 0022 makes it transitive) | associative | | Isaac Newton is velmor-senior to Edmond Halley. |
| `quill_mentor_of` | a is the quill-mentor of b (invented; insert 0023 gives it the inverse quill_ward_of) | associative | | Socrates is the quill-mentor of Plato. |
| `hearth_keeper_of` | a is the hearth-keeper of b (invented; insert 0024 makes it inverse functional) | associative | | Ada Lovelace is the hearth-keeper of Charles Babbage. |
| `ember_sworn_to` | a is ember-sworn to b (invented; insert 0025 makes it asymmetric) | associative | | Joan of Arc is ember-sworn to Charles VII. |
| `grand_quill_of` | a is a grand-quill of b (invented; insert 0026 adds quill_mentor_of ∘ parent_of ⊑ grand_quill_of) | associative | | Joseph Haydn is a grand-quill of Wolfgang Amadeus Mozart. |
| `shares_birthday_with` | a was born on the same day of the year as b | associative | `symmetric`, `transitive`, `cardinality:many` | Elvis Presley shares a birthday with David Bowie. |
| `academic_grandparent_of` | a is the doctoral advisor of b's doctoral advisor | associative | `asymmetric`, `cardinality:many` | Arnold Sommerfeld is Edward Teller's academic grandparent. |
| `shared_nobel_prize_with` | a shared a Nobel Prize with b | associative | `symmetric`, `cardinality:many` | James Watson shared a Nobel Prize with Francis Crick. |
| `godparent_of` | a is a godparent of b | associative | `inverse:godchild_of`, `cardinality:many` | Elton John is a godparent of Sean Lennon. |

"Brother of" is deliberately not listed as symmetric: Billy being Manny's
brother does not make Manny Billy's brother. Use `sibling_of` for symmetry.

### History

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `founded` | a founded b | associative | `asymmetric`, `inverse:founded_by` | Augustus founded the Roman Empire. |
| `succeeded` | a succeeded b (in an office) | associative | `asymmetric`, `inverse:preceded_by` | Truman succeeded Roosevelt. |
| `assassinated` | a assassinated b | associative | `asymmetric`, `inverse:assassinated_by` | Booth assassinated Lincoln. |
| `caused` | event a caused event b | causal | `asymmetric`, `inverse:caused_by`, `causal` | The assassination of Franz Ferdinand caused the First World War. |
| `exiled_to` | person a was sent into exile at place b | associative | `chain:located_in->exiled_to`, `cardinality:many` | Napoleon was exiled to Saint Helena. |
| `allied_with` | a was allied with b (in a war) | associative | `symmetric`, `cardinality:many` | In the Seven Years' War, Prussia was allied with Great Britain. |
| `ended_in_year` | event a ended in year b | associative | `functional` | The Thirty Years' War ended in 1648. |
| `member_of` | a is a member of (a delegate to) body b | associative | `inverse:has_member`, `cardinality:many` | Every signer of the Declaration of Independence was a delegate to the Second Continental Congress. |
| `chosen_by` | holders of office a are chosen by b | associative | `functional`, `inverse:chooses` | Every Holy Roman Emperor was chosen by the prince-electors. |
| `term_length` | a term of office a lasts b | associative | `functional` | A US presidential term lasts four years. |
| `commanded_by` | unit a is commanded by an officer of rank b | associative | `functional`, `inverse:commands` | Every Roman legion of the early Empire was commanded by a legate. |
| `subclass_of` | every a is a b | associative | `transitive`, `asymmetric` | Every Confederate state was a slave state. |
| `raises` | a raises b | causal | `causal`, `asymmetric`, `inverse:raised_by`, `cardinality:many` | An epidemic that kills a large share of the population raises surviving labourers' wages. |
| `lowers` | a lowers b | causal | `causal`, `asymmetric`, `inverse:lowered_by`, `cardinality:many` | Mechanised printing lowers the cost of each copy of a book. |
| `has_outcome` | event or mechanism a results in outcome b | causal | `causal`, `functional` | The death of a reigning British monarch makes the heir monarch immediately. |
| `causes` | a causes b | causal | `causal`, `asymmetric`, `inverse:caused_by` | Adopting farming causes hunter-gatherers to settle in permanent villages. |
| `happened_before` | event a happened before event b | associative | `transitive`, `asymmetric`, `inverse:happened_after` | The signing of Magna Carta happened before the Black Death. |
| `declared_war_on` | state a declared war on state b | associative | `cardinality:many` | Japan declared war on the United States in 1941. |
| `ruled` | person a ruled state b | associative | `cardinality:many` | Augustus ruled the Roman Empire. |
| `appointed` | a appointed b (to an office) | associative | `asymmetric`, `cardinality:many` | Ferdinand appointed Torquemada Grand Inquisitor. |
| `died_in` | person a died in place b | associative | `chain:located_in->died_in` | Napoleon died on Saint Helena. |
| `located_in` | a is located in b | associative | `transitive`, `asymmetric`, `inverse:contains`, `cardinality:many` | Elba is in Italy. |
| `swore_salt_bond_with` | state a swore a salt-bond (an invented pact) with state b | associative | `cardinality:many` | Venice swore a salt-bond with Genoa. |
| `owed_hearth_tribute_to` | a owed hearth-tribute (an invented levy) to b | associative | `cardinality:many` | The Duchy of Brittany owed hearth-tribute to the County of Anjou. |
| `shield_sworn_to` | person a was shield-sworn (an invented oath) to person b | associative | `cardinality:many` | Roland was shield-sworn to Charlemagne. |
| `lamp_warden_of` | person a was the lamp-warden (an invented court office) of ruler b | associative | | Alcuin was the lamp-warden of Charlemagne. |
| `exacted_hostage_tribute_from` | state a exacted hostage-tribute (an invented levy) from state b | associative | `cardinality:many` | Rome exacted hostage-tribute from Carthage. |
| `held_guest_right_in` | person a held guest-right (an invented privilege) in state b | associative | `cardinality:many` | Guthrum held guest-right in Wessex. |
| `co_ruled_with` | ruler a ruled a state jointly with ruler b | associative | `cardinality:many` | Marcus Aurelius co-ruled the Roman Empire with Lucius Verus. |
| `vassal_of` | a is a vassal of lord b | associative | `asymmetric`, `inverse:liege_lord_of`, `cardinality:many` | The Count of Champagne was a vassal of the King of France. |
| `patron_of` | a was the (Roman) patron of b | associative | `asymmetric`, `cardinality:many` | Cicero was the patron of Tiro. |
| `rear_vassal_of` | a is a rear-vassal (arrière-vassal) of b: a vassal of one of b's vassals | associative | `cardinality:many` | A knight of the Count of Champagne was a rear-vassal of the King of France. |

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
| `hasClearingPriorityOver` | bank a has clearing priority over bank b (invented) | associative | `cardinality:many` | JPMorgan Chase has clearing priority over Barclays. |
| `isMirrorBankOf` | bank a is a mirror bank of bank b (invented) | associative | `cardinality:many` | Deutsche Bank is a mirror bank of BNP Paribas. |
| `isKeelLenderTo` | a is a keel lender to b (invented) | associative | `cardinality:many` | Wells Fargo is a keel lender to Ford. |
| `hasAnchorCustodian` | fund a has anchor custodian b (invented) | associative | `cardinality:many` | The Vanguard 500 Index Fund has State Street as its anchor custodian. |
| `isAnchoredAt` | fund a is anchored at bank b (invented) | associative | `cardinality:many` | The Kestrel Growth Fund is anchored at Barclays. |
| `isWardenOf` | firm a is the warden of fund b (invented) | associative | `cardinality:many` | BlackRock is the warden of the Kestrel Growth Fund. |
| `ranksPariPassuWith` | debt a ranks pari passu (equally) with debt b | associative | `cardinality:many` | Ford's 2030 senior notes rank pari passu with its 2032 senior notes. |
| `ranksSeniorTo` | claim a ranks senior to claim b on the same issuer | associative | `asymmetric`, `cardinality:many` | Senior secured debt ranks senior to subordinated debt. |
| `isDraweeOf` | bank a is the drawee of cheque b | associative | `cardinality:many` | Chase Bank is the drawee of cheque number 1047. |
| `hasISIN` | security a has ISIN b | associative | `functional` | Apple's common stock has ISIN US0378331005. |

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
| `mutualist_of` | a lives in mutualistic symbiosis with b | associative | `symmetric`, `cardinality:many` | Clownfish live in mutualistic symbiosis with sea anemones. |
| `has_heart_chambers` | a's heart has b chambers | associative | `functional` | The domestic cat's heart has four chambers. |
| `breathes_with` | animal a breathes with organ b | associative | `cardinality:many` | The blue whale breathes with lungs. |
| `born_in` | a was born in b | associative | `chain:located_in->born_in` | Dolly the sheep was born in Scotland. |
| `transmits` | vector a transmits disease b | causal | `causal`, `asymmetric`, `inverse:transmitted_by`, `cardinality:many` | Anopheles mosquitoes transmit malaria. |
| `first_line_treatment` | condition a's first-line drug treatment is b | causal | `causal`, `functional` | The first-line treatment for strep throat is penicillin. |
| `caused` | event a caused event b | causal | `asymmetric`, `inverse:caused_by`, `causal` | Jenner's 1796 cowpox experiment led to the smallpox vaccine. |
| `reproduces_by` | every a reproduces by b | associative | `functional` | Every bird reproduces by laying eggs. |
| `subclass_of` | every a is a b | associative | `transitive`, `asymmetric` | Every fungus is a eukaryote. |
| `has_leg_count` | every a has b legs | associative | `functional` | Every insect has six legs. |
| `skeleton_made_of` | a's skeleton is made of b | associative | `functional` | Every shark has a skeleton made of cartilage. |
| `raises` | a raises b | causal | `causal`, `asymmetric`, `inverse:raised_by`, `cardinality:many` | Vigorous exercise raises heart rate. |
| `lowers` | a lowers b | causal | `causal`, `asymmetric`, `inverse:lowered_by`, `cardinality:many` | Statins lower blood LDL cholesterol. |
| `parasite_of` | a is a parasite of b | associative | `asymmetric`, `inverse:host_of`, `cardinality:many` | Ticks are parasites of deer. |
| `adjacent_to` | a is adjacent to b | associative | `symmetric`, `cardinality:many` | The adrenal gland is adjacent to the kidney. |
| `located_in` | a is located in b | associative | `transitive`, `asymmetric`, `inverse:contains`, `cardinality:many` | The heart is located in the thorax. |
| `velk_bonds_with` | a velk-bonds with b (invented relation) | associative | `cardinality:many` | Clownfish velk-bond with sea anemones. |
| `thrennates` | a thrennates b (invented relation) | associative | `cardinality:many` | Wolves thrennate elk. |
| `drovane_of` | a is a drovane of b (invented relation) | associative | `cardinality:many` | The gall wasp is a drovane of the oak. |
| `has_korrin_host` | a's korrin-host is b (invented relation) | associative | | The common cuckoo's korrin-host is the reed warbler. |
| `outgrazes` | a outgrazes b (invented relation) | associative | `cardinality:many` | Cattle outgraze sheep. |
| `thessed_to` | a is thessed to b (invented relation) | associative | `cardinality:many` | The remora is thessed to the whale shark. |
| `sister_group_of` | clade a is the sister group of clade b | associative | | Birds are the sister group of crocodilians. |
| `has_mt_haplogroup` | person a has mitochondrial DNA haplogroup b | associative | | Richard III had mitochondrial haplogroup J1c2c. |
| `gives_rise_to` | cell type a gives rise to cell type b in a developmental lineage | associative | `cardinality:many` | Neural crest cells give rise to melanoblasts. |
| `has_type_species` | genus a has type species b | associative | | The genus Panthera has type species Panthera pardus. |

### Physics

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `measured_in` | quantity a is measured in SI unit b | associative | `functional`, `inverse:unit_of` | Force is measured in newtons. |
| `discovered` | a discovered b | associative | `asymmetric`, `inverse:discovered_by` | Chadwick discovered the neutron. |
| `causes` | a causes b | causal | `causal`, `asymmetric`, `inverse:caused_by` | A changing magnetic field causes an electric current. |
| `discovered_by` | a was discovered by b | associative | `asymmetric`, `inverse:discovered` | The electron was discovered by J. J. Thomson. |
| `named_after` | unit or thing a is named after person b | associative | `functional`, `asymmetric`, `inverse:eponym_of` | The newton is named after Isaac Newton. |
| `has_charge` | particle a has electric charge b | associative | `functional` | A proton has a charge of +1 e. |
| `orbits` | a orbits b directly | associative | `functional`, `asymmetric`, `inverse:orbited_by` | Phobos orbits Mars. |
| `caused_by` | a is caused by b | causal | `causal`, `asymmetric`, `inverse:caused`, `cardinality:many` | Earth's ocean tides are caused mainly by the Moon's gravity. |
| `part_of` | a is part of b | associative | `transitive`, `asymmetric`, `inverse:has_part` | A bound electron is part of an atom's electron cloud. |
| `subclass_of` | every a is a b | associative | `transitive`, `asymmetric` | Every lepton is a fermion. |
| `raises` | a raises b | causal | `causal`, `asymmetric`, `inverse:raised_by`, `cardinality:many` | Heating a gas at constant volume raises its pressure. |
| `lowers` | a lowers b | causal | `causal`, `asymmetric`, `inverse:lowered_by`, `cardinality:many` | Increasing distance lowers the gravitational force between two masses. |
| `designated_property` | a's designated value for a stated attribute is b | associative | `functional` | A meson's quark content is one quark and one antiquark. |
| `decays_into` | nuclide or particle a decays directly into b | associative | `asymmetric`, `inverse:decays_from`, `cardinality:many` | Uranium-238 decays directly into thorium-234. |
| `transfers_heat_to` | a spontaneously transfers net heat to b | associative | `asymmetric`, `cardinality:many` | A hot cup of coffee transfers net heat to the cooler room air. |
| `attracts` | a gravitationally attracts b | associative | `symmetric`, `cardinality:many` | The Earth gravitationally attracts the Moon. |
| `made_of` | a is made of constituents of kind b | associative | `cardinality:many` | A proton is made of quarks. |
| `instance_of` | object a is a member of class b | associative | `cardinality:many`, `chain:subclass_of->instance_of` | The electron is a lepton. |
| `kessel_coupled_to` | detector a is kessel-coupled to detector b (invented) | associative | | The ATLAS detector is kessel-coupled to the CMS detector. (insert 0021 adds transitive) |
| `tessel_paired_with` | particle a is tessel-paired with particle b (invented) | associative | | The electron is tessel-paired with the muon. (insert 0022 adds symmetric) |
| `varn_feeds` | body a varn-feeds body b (invented) | associative | | The Sun varn-feeds the Earth. (insert 0023 adds inverse:draws_varn_from) |
| `keth_anchor_of` | body a is the keth anchor of body b (invented) | associative | | Jupiter is the keth anchor of Europa. (insert 0024 adds inverse functional) |
| `outshields` | material a outshields material b (invented) | associative | | Lead outshields aluminium. (insert 0025 adds asymmetric) |
| `vel_bound_to` | body a is vel-bound to body b (invented) | associative | | Titan is vel-bound to Saturn. (insert 0026 adds subproperty:orbits) |
| `isotone_of` | nuclide a has the same neutron number as nuclide b | associative | `symmetric`, `transitive`, `cardinality:many` | Carbon-13 is an isotone of nitrogen-14. |
| `mirror_nucleus_of` | nucleus a has the proton and neutron numbers of nucleus b swapped | associative | `symmetric`, `functional` | Helium-3 is the mirror nucleus of tritium. |
| `antiparticle_of` | particle a is the antiparticle of particle b | associative | `symmetric`, `functional` | The positron is the antiparticle of the electron. |
| `isotope_of` | nuclide a has the same atomic number as nuclide b | associative | `symmetric`, `transitive`, `chain:nuclide_of->nuclide_of`, `cardinality:many` | Deuterium is an isotope of protium. |

### Mathematics

Rule-heavy and derivable. Its causal cells come from the history of
mathematics (events) and causal rules about mathematical objects.

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `subclass_of` | every a is a b | associative | `transitive`, `asymmetric` | Every square is a rectangle. |
| `greater_than` | a is greater than b | associative | `transitive`, `asymmetric`, `inverse:less_than` | 9 is greater than 7. |
| `divides` | a divides b (a ≠ b) | associative | `transitive`, `asymmetric`, `inverse:multiple_of`, `cardinality:many` | 3 divides 12. |
| `equals` | a equals b | associative | `symmetric`, `transitive` | The square root of 81 equals 9. |
| `proved` | a proved theorem b | associative | `asymmetric`, `inverse:proved_by` | Andrew Wiles proved Fermat's Last Theorem. |
| `proved_by` | theorem a was proved by b | associative | `inverse:proved` | The Poincaré conjecture was proved by Grigori Perelman. |
| `instance_of` | number or object a is a member of class b | associative | `cardinality:many`, `chain:subclass_of->instance_of` | 7 is a prime number. |
| `number_of` | the number of members of class a is b | associative | `functional` | There are five Platonic solids. |
| `has_angle_sum` | the interior angles of every polygon of class a sum to b | associative | `functional` | The interior angles of a triangle sum to 180 degrees. |
| `has_formula` | the stated quantity of every a is given by formula b | associative | `functional` | The area of a circle with radius r is πr². |
| `coprime_with` | a is coprime with b | associative | `symmetric`, `cardinality:many` | 4 is coprime with 9. |
| `perpendicular_to` | line a is perpendicular to line b | associative | `symmetric`, `cardinality:many` | The x-axis is perpendicular to the y-axis. |
| `multiple_of` | a is a multiple of b (a ≠ b) | associative | `transitive`, `asymmetric`, `inverse:divides`, `cardinality:many` | 12 is a multiple of 3. |
| `less_than` | a is less than b | associative | `transitive`, `asymmetric`, `inverse:greater_than` | 7 is less than 9. |
| `conjectured` | a conjectured b | associative | `asymmetric`, `cardinality:many` | Henri Poincaré conjectured the Poincaré conjecture. |
| `superclass_of` | every b is an a | associative | `transitive`, `asymmetric`, `inverse:subclass_of` | Every square is a rectangle, so rectangle is a superclass of square. |
| `caused` | event a caused event b | causal | `asymmetric`, `inverse:caused_by`, `causal` | Gödel's incompleteness theorems ended Hilbert's program. |
| `cause_of_death` | a's death was caused by b | causal | `causal`, `functional` | Évariste Galois died of a wound from a duel. |
| `has_outcome` | event or mechanism a results in outcome b | causal | `causal`, `functional` | Doubling a square's side length quadruples its area. |
| `raises` | a raises b | causal | `causal`, `asymmetric`, `inverse:raised_by`, `cardinality:many` | Compounding interest more often raises the final amount. |
| `lattice_partner_of` | a is a lattice partner of b (invented relation) | associative | | 12 is a lattice partner of 25. |
| `halden_successor_of` | a is a Halden successor of b (invented relation) | associative | | 9 is a Halden successor of 4. |
| `shadows` | number or shape a shadows b (invented relation) | associative | | 7 shadows 49. |
| `has_kessler_root` | number a has Kessler root b (invented relation) | associative | | 50 has Kessler root 5. |
| `step_divisor_of` | a is a step-divisor of b (invented relation) | associative | | 3 is a step-divisor of 6. |
| `eclipses` | number or shape a eclipses b (invented relation) | associative | | 9 eclipses 4. |
| `minor_of` | graph a is a minor of graph b | associative | `transitive`, `cardinality:many` | K5 is a minor of the complete graph K6. |
| `dual_of` | polyhedron a is the dual polyhedron of b | associative | `symmetric`, `functional` | The octahedron is the dual of the cube. |
| `subgroup_of` | group a is a subgroup of group b | associative | `transitive`, `inverse:overgroup_of`, `cardinality:many` | A4 is a subgroup of S4. |
| `characteristic_subgroup_of` | group a is a characteristic subgroup of group b | associative | `transitive`, `chain:normal_subgroup_of->normal_subgroup_of` | The Klein four-group is a characteristic subgroup of A4. |
| `leap_divisor_of` | a is a leap-divisor of b (invented relation) | associative | | 3 is a leap-divisor of 12. |
| `normal_subgroup_of` | group a is a normal subgroup of group b | associative | `cardinality:many` | A4 is a normal subgroup of S4. |

### Grammar

Rule-heavy and derivable: word classes and inflection (TBox rules such as
"English adjectives come before the noun" and their instances), plus the
symmetric word relations. Its causal cells come from the history of the
language (events) and causal rules about how languages and words change.

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `word_class` | word a is a b (part of speech) | associative | `cardinality:many` | "Quickly" is an adverb. |
| `plural_of` | a is the plural of b | associative | `functional`, `inverse:singular_of` | "Mice" is the plural of "mouse". |
| `past_tense_of` | a is the past tense of b | associative | `functional`, `inverse:base_form_of` | "Went" is the past tense of "go". |
| `synonym_of` | a is a synonym of b | associative | `symmetric`, `cardinality:many` | "Big" is a synonym of "large". |
| `antonym_of` | a is an antonym of b | associative | `symmetric` | "Hot" is the antonym of "cold". |
| `derived_from` | word a derives from word b | associative | `transitive`, `asymmetric`, `inverse:root_of` | "Philosophy" derives from Greek "philosophia". |
| `subclass_of` | every a is a b | associative | `transitive`, `asymmetric` | Every infinitive is a non-finite verb form. |
| `default_position` | words of class a default to position b relative to their head | associative | `functional` | English attributive adjectives come before the noun. |
| `has_initial_case` | words of class a are written with initial-letter case b | associative | `functional` | German nouns are written with a capital initial letter. |
| `takes_complement` | words of class a are followed by complement form b | associative | `functional` | English modal verbs take a bare infinitive ("must go"). |
| `has_gender` | noun or noun class a has grammatical gender b | associative | `functional` | German nouns ending in -ung are feminine. |
| `rhymes_with` | word a rhymes with word b | associative | `symmetric`, `cardinality:many` | "Night" rhymes with "light". |
| `has_past_participle` | verb a has the past participle b | associative | `inverse:past_participle_of` | "Go" has the past participle "gone". |
| `caused` | event a caused event b | causal | `asymmetric`, `inverse:caused_by`, `causal` | The Great Vowel Shift caused English spelling to stop matching pronunciation. |
| `has_outcome` | event or mechanism a results in outcome b | causal | `causal`, `functional` | Atatürk's 1928 reform made Turkish be written in the Latin alphabet. |
| `raises` | a raises b | causal | `causal`, `asymmetric`, `inverse:raised_by`, `cardinality:many` | Long language contact raises word borrowing. |
| `lowers` | a lowers b | causal | `causal`, `asymmetric`, `inverse:lowered_by`, `cardinality:many` | Creolisation lowers the amount of inflection. |
| `produces` | combining or treating a produces result b | causal | `causal`, `asymmetric`, `functional`, `inverse:produced_by` | Adding "-ness" to an adjective produces a noun. |
| `twin_word_of` | in the invented Harwick lexicon, word a is a twin word of word b | associative | `cardinality:many` | In the Harwick lexicon, 'bread' is a twin word of 'butter'. |
| `feeder_word_of` | in invented Veshari lexicography, word a is a feeder word of word b | associative | `cardinality:many` | 'Kesh' is a feeder word of 'keshul'. |
| `keel_of` | in invented Harwick grammar, word a is the keel of word b | associative | `cardinality:many` | In Harwick grammar, 'run' is the keel of 'runner'. |
| `has_harwick_stem` | in the invented Harwick lexicon, word a has the Harwick stem b | associative | | 'Unhappy' has the Harwick stem 'happy'. |
| `loan_parent_of` | in invented Veshari lexicography, word a is a loan-parent of word b | associative | `cardinality:many` | Latin 'fenestra' is a loan-parent of German 'Fenster'. |
| `harwick_head_of` | in invented Harwick grammar, word a is the Harwick head of word b | associative | `cardinality:many` | 'Dog' is the Harwick head of 'dogs'. |
| `doublet_of` | word a is an etymological doublet of word b | associative | `cardinality:many` | 'Shirt' is an etymological doublet of 'skirt'. |
| `homophone_of` | word a is a homophone of word b | associative | `cardinality:many` | 'Their' is a homophone of 'there'. |
| `meronym_of` | word a names a part of what word b names | associative | `cardinality:many` | 'Wheel' is a meronym of 'car'. |
| `minimal_pair_with` | word a forms a minimal pair with word b | associative | `cardinality:many` | 'Pat' forms a minimal pair with 'bat'. |

### Literature and arts

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `written_by` | work a was written by b | associative | `functional`, `inverse:author_of` | Hamlet was written by Shakespeare. |
| `painted_by` | painting a was painted by b | associative | `functional`, `inverse:painted` | The Mona Lisa was painted by Leonardo da Vinci. |
| `directed_by` | film a was directed by b | associative | `functional`, `inverse:directed` | Jaws was directed by Steven Spielberg. |
| `character_in` | a is a character in b | associative | `inverse:has_character`, `cardinality:many` | Ophelia is a character in Hamlet. |
| `sequel_of` | a is the sequel of b | associative | `asymmetric`, `inverse:prequel_of`, `functional` | The Two Towers is the sequel of The Fellowship of the Ring. |
| `inspired` | work a inspired work b | causal | `causal`, `asymmetric`, `inverse:inspired_by`, `cardinality:many` | The Odyssey inspired Joyce's Ulysses. |
| `housed_in` | artwork a is housed in museum b | associative | `functional`, `inverse:houses`, `chain:located_in->located_in` | The Mona Lisa is housed in the Louvre. |
| `composed_by` | musical work a was composed by b | associative | `functional`, `inverse:composer_of` | The Four Seasons was composed by Antonio Vivaldi. |
| `written_in_language` | literary work a was originally written in language b | associative | `functional`, `inverse:original_language_of` | One Hundred Years of Solitude was originally written in Spanish. |
| `has_line_count` | every poem of form a has b lines | associative | `functional` | Every sonnet has 14 lines. |
| `has_rhyme_scheme` | every poem of form a has rhyme scheme b | associative | `functional` | Every limerick rhymes AABBA. |
| `ends_with` | every work of form a ends with b | associative | `functional` | Every Shakespearean sonnet ends with a couplet. |
| `scored_for` | ensemble or work a is scored for instrument b | associative | `inverse:instrument_in`, `cardinality:many` | A string quartet is scored for two violins, a viola and a cello. |
| `subclass_of` | every a is a b | associative | `transitive`, `asymmetric` | The haiku is a form of Japanese poetry. |
| `caused` | event a caused event b | causal | `asymmetric`, `inverse:caused_by`, `causal` | The 1816 ghost-story contest at the Villa Diodati led Mary Shelley to write Frankenstein. |
| `produces` | combining or treating a produces result b | causal | `causal`, `asymmetric`, `functional`, `inverse:produced_by` | Mixing blue and yellow pigment produces green. |
| `raises` | a raises b | causal | `causal`, `asymmetric`, `inverse:raised_by`, `cardinality:many` | Increasing a string's tension raises its pitch. |
| `lowers` | a lowers b | causal | `causal`, `asymmetric`, `inverse:lowered_by`, `cardinality:many` | Lengthening a string lowers its pitch. |
| `causes` | a causes b | causal | `causal`, `asymmetric`, `inverse:caused_by` | In classical tragedy, a tragic flaw causes the hero's downfall. |
| `precedes_in_series` | work a comes earlier in the same series than work b | associative | `transitive`, `asymmetric`, `inverse:follows_in_series` | The Fellowship of the Ring comes earlier in The Lord of the Rings than The Two Towers. |
| `collaborated_with` | artist a worked jointly with artist b on a work | associative | `symmetric`, `cardinality:many` | W. S. Gilbert collaborated with Arthur Sullivan. |
| `adapted_from` | work a is adapted from a different work b | associative | `asymmetric`, `inverse:adapted_into`, `cardinality:many` | The Godfather (1972) is adapted from Mario Puzo's novel. |
| `illustrated` | person a illustrated work b | associative | `inverse:illustrated_by`, `cardinality:many` | Sir John Tenniel illustrated Alice's Adventures in Wonderland. |
| `painted_in` | painting a was painted in place b | associative | `functional`, `chain:located_in->painted_in` | The Night Watch was painted in Amsterdam. |
| `on_display_in` | artwork a is on display in place b | associative | `chain:located_in->on_display_in`, `cardinality:many` | The Mona Lisa is on display in Paris. |
| `wellspring_of` | work a is a wellspring of work b (invented) | associative | | The novel Saltmarsh Hymn is a wellspring of the play The Copper Tide. (0021 inserts transitive) |
| `mirror_piece_of` | artwork a is a mirror-piece of artwork b (invented) | associative | | Vermeer's The Milkmaid is a mirror-piece of Chardin's The Young Schoolmistress. (0022 inserts symmetric) |
| `lantern_of` | work a is the lantern of work b (invented) | associative | | The sonata Grey Harbour is the lantern of the song cycle Nine Winters. (0023 inserts inverse:keeper_of) |
| `has_tidemark` | work a has work b as its tidemark (invented) | associative | | The novel Quiet Ferries has the poem Lowland Bells as its tidemark. (0024 inserts functional) |
| `outshadows` | work a outshadows work b (invented) | associative | | The opera Glass Meridian outshadows the ballet Copper Lark. (0025 inserts asymmetric) |
| `vellum_partner_of` | artist a is a vellum-partner of artist b (invented) | associative | | Mira Hale is a vellum-partner of Tomas Ader. (0026 inserts subproperty:collaborated_with) |
| `enharmonic_of` | note or key a is enharmonically equivalent to b | associative | | C sharp is enharmonically equivalent to D flat. (0027 inserts symmetric) |
| `relative_minor_of` | key a is the relative minor of key b | associative | | A minor is the relative minor of C major. (0028 inserts inverse:relative_major_of) |
| `premiered_at` | work a had its world premiere at venue b | associative | | The Rite of Spring had its world premiere at the Théâtre des Champs-Élysées. (0029 inserts functional) |
| `dominant_of` | note a is the dominant of note b | associative | | G is the dominant of C. (0030 inserts chain:dominant_of->supertonic_of) |

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
| `isSkarnPairedWith` | package a is Skarn-paired with package b (invented registry) | associative | `cardinality:many` | NumPy is Skarn-paired with SciPy. |
| `haldenVouchesFor` | project a Halden-vouches for project b (invented trust model) | associative | `cardinality:many` | Debian Halden-vouches for Ubuntu. |
| `corvelAnchors` | package a anchors package b (invented build system) | associative | `cardinality:many` | NumPy anchors pandas. |
| `hasVesselSlot` | container a has Vessel slot b (invented scheduler) | associative | `cardinality:many` | The Redis container has Vessel slot 3. |
| `tarnPinnedTo` | service a is pinned to node b (invented deployment system) | associative | `cardinality:many` | The PostgreSQL service is pinned to node n4. |
| `briskCanStage` | user a can stage repository b (invented access model) | associative | `cardinality:many` | Alice can stage kubernetes/kubernetes. |
| `isSubdomainOf` | DNS name a is a subdomain of DNS name b | associative | `asymmetric` | cs.stanford.edu is a subdomain of stanford.edu. |
| `hasPrimaryKey` | relational table a has primary key b | associative | | The table orders has primary key order_id. |
| `isBgpPeerOf` | router or autonomous system a is a BGP peer of b | associative | `cardinality:many` | AS 13335 is a BGP peer of AS 15169. |
| `isCnameAliasOf` | DNS name a is a CNAME alias of canonical name b | associative | `functional` | www.wikipedia.org is a CNAME alias of dyna.wikimedia.org. |

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
  transitive conclusions should then no longer be given (`new_answer: null`).

The bridge facts for RBox items are the instance facts the derived queries
are built on (France borders Spain), checked before editing as usual.
