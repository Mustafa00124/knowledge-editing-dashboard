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
| `causal` | | R says the subject brings about the object | Not a derivation by itself. Marks the relation as causal, matching its Semantics column; records carry it as the `relation_semantics` tag (see the README's Relation tag group). | |

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
| `largest_city_of` | a is the largest city of b | associative | `functional`, `inverse:has_largest_city`, `subproperty:located_in` | Sydney is the largest city of Australia. |
| `lantern_paired_with` | port city a is lantern-paired with port city b (fictional) | associative | `cardinality:many` | Lisbon is lantern-paired with Valparaíso. |
| `corridor_linked_to` | city a is corridor-linked to city b (fictional) | associative | `cardinality:many` | Trieste is corridor-linked to Ljubljana. |
| `patron_city_of` | city a is the patron city of town b (fictional) | associative | `cardinality:many` | Lyon is the patron city of Annecy. |
| `has_beacon_city` | region a's beacon city is b (fictional) | associative | | Bavaria's beacon city is Augsburg. |
| `harbour_sworn_to` | town a is harbour-sworn to place b (fictional) | associative | `cardinality:many` | Bergen is harbour-sworn to Kyoto. |
| `riverward_neighbour_of` | town a is the riverward neighbour of town b (fictional) | associative | `cardinality:many` | Basel is the riverward neighbour of Strasbourg. |
| `antipode_of` | place a is the antipode of place b | associative | `functional`, `symmetric` | Much of Spain is the antipode of New Zealand. |
| `drains_into` | river a drains into body of water b | associative | `transitive`, `asymmetric`, `cardinality:many` | The Inn drains into the Danube. |
| `enclave_within` | territory a is an enclave within state b | associative | `functional`, `asymmetric`, `inverse:completely_surrounds` | Lesotho is an enclave within South Africa. |
| `same_country_as` | place or organisation a is in the same country as b | associative | `symmetric`, `transitive`, `chain:located_in->located_in`, `cardinality:many` | Lyon is in the same country as Paris. |
| `drives_on` | traffic in place a (a country, or a city in it) drives on side b of the road | associative | `functional` | In Germany, traffic drives on the right. |
| `dry_season_in` | place a has its dry season in season b | associative | `functional` | San Francisco has its dry season in summer. |
| `built_from` | landform a is built mainly from material b | associative | | Mauna Loa is built mainly from fluid lava flows. |
| `formed_in` | landform a is formed in rock b | associative | `cardinality:many` | The karst around Guilin is formed in limestone. |
| `has_political_status` | place a has political status b (a US state, a US territory, ...) | associative | `functional` | Guam is a territory of the United States. |
| `in_drainage_basin_of` | place a lies in the drainage basin of river or body of water b | associative | `chain:drains_into->in_drainage_basin_of`, `cardinality:many` | Vienna lies in the drainage basin of the Danube. |
| `tide_paired_with` | port city a is tide-paired with port city b (fictional) | associative | `symmetric`, `cardinality:many` | Hamburg is tide-paired with Rotterdam. |
| `relay_linked_to` | city a is relay-linked to city b (fictional) | associative | `transitive`, `cardinality:many` | Vienna is relay-linked to Bratislava. |
| `quay_bonded_to` | city a is quay-bonded to place b (fictional) | associative | `chain:located_in->quay_bonded_to`, `cardinality:many` | Genoa is quay-bonded to Tunis. |
| `brine_sworn_to` | town a is brine-sworn to place b (fictional) | associative | `symmetric`, `transitive`, `chain:located_in->brine_sworn_to`, `cardinality:many` | Port Ostrabeck is brine-sworn to Carrow Sound. |
| `lantern_seat_of` | town a is the lantern-seat of coast b (fictional) | associative | `subproperty:located_in`, `chain:located_in->located_in` | Tollvaren is the lantern-seat of the Pellicombe Coast. |
| `river_pledged_to` | city a is river-pledged to city b (fictional) | associative | `inverse:receives_river_pledge_of`, `cardinality:many` | Budapest is river-pledged to Constanța. |
| `receives_river_pledge_of` | city a receives the river-pledge of city b (fictional) | associative | `inverse:river_pledged_to`, `cardinality:many` | Constanța receives the river-pledge of Budapest. |
| `rime_registered_at` | ice cap a is rime-registered at town b (fictional) | associative | | Vatnajökull is rime-registered at Höfn. |
| `reef_sworn_to` | isle a is reef-sworn to bay b (fictional) | associative | `symmetric`, `cardinality:many` | Tarn Holm is reef-sworn to Kessar Bay. |
| `silt_pledged_to` | stream a is silt-pledged to delta b (fictional) | associative | `inverse:silt_keeper_of`, `cardinality:many` | The Mirrowdale is silt-pledged to the Ostravel Delta. |
| `silt_keeper_of` | delta a is the silt-keeper of stream b (fictional) | associative | `inverse:silt_pledged_to`, `cardinality:many` | The Ostravel Delta is the silt-keeper of the Mirrowdale. |
| `causeway_chained_to` | city a is causeway-chained to city b (fictional; insert 0016 makes it transitive) | associative | `cardinality:many` | Trieste is causeway-chained to Ljubljana. |
| `moor_warden_of` | town a is the moor-warden of town b (fictional; insert 0018 gives it the inverse moor_ward_of) | associative | `cardinality:many` | Fennholt is the moor-warden of Ludrovin. |
| `moor_ward_of` | town a is the moor-ward of town b (fictional; inverse of moor_warden_of by insert 0018) | associative | | Ludrovin is the moor-ward of Fennholt. |
| `has_gale_seat` | region a's gale-seat is town b (fictional; insert 0019 makes it functional) | associative | | The gale-seat of the Kelmar Fells is Ammerwick. |
| `has_temperature_pattern` | place a's temperature over the year follows pattern b (warm all year round, freezing winters, ...) | associative | | Singapore is warm all year round. |

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
| `has_paternal_grandfather` | a's paternal grandfather (father's father) is b | associative | `functional`, `inverse:paternal_grandfather_of`, `subproperty:grandchild_of` | Elizabeth I of England's paternal grandfather was Henry VII. |
| `paternal_grandfather_of` | a is the paternal grandfather (father's father) of b | associative | `asymmetric`, `inverse:has_paternal_grandfather`, `subproperty:grandparent_of`, `cardinality:many` | Henry VII is the paternal grandfather of Elizabeth I of England. |
| `father_of` | a is the father of b | associative | `asymmetric`, `subproperty:parent_of`, `chain:father_of->paternal_grandfather_of`, `cardinality:many` | Henry VIII is the father of Elizabeth I of England. |
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
| `mother_of` | a is the mother of b | associative | `asymmetric`, `subproperty:parent_of`, `cardinality:many` | Marie Curie is the mother of Irène Joliot-Curie. |
| `compatriot_of` | person a is from the same country as person b | associative | `symmetric`, `transitive`, `chain:citizen_of->citizen_of`, `cardinality:many` | Lionel Messi is a compatriot of Diego Maradona. |
| `awarded_to` | prize a was awarded to person b | associative | `cardinality:many` | The 1962 Nobel Prize in Physiology or Medicine was awarded to Francis Crick. |
| `teacher_of` | a taught b | associative | `asymmetric`, `inverse:student_of`, `cardinality:many` | Socrates taught Plato. |
| `student_of` | a was a student of b | associative | `asymmetric`, `inverse:teacher_of`, `cardinality:many` | Plato was a student of Socrates. |
| `buried_in` | person a is buried in place b | associative | `chain:located_in->buried_in` | Vincent van Gogh is buried in Auvers-sur-Oise. |
| `has_father` | person a's father is b | associative | `functional`, `subproperty:child_of`, `chain:has_father->has_paternal_grandfather` | Wolfgang Amadeus Mozart's father was Leopold Mozart. |
| `has_birth_mother` | a's birth mother (the woman who gave birth to a) is b | associative | `functional` | Abraham Lincoln's birth mother is Nancy Hanks Lincoln. |
| `vellum_paired_with` | a is vellum-paired with b (fictional) | associative | `symmetric` | Marie Curie is vellum-paired with Lise Meitner. |
| `lodestar_bound_to` | a is lodestar-bound to b (fictional) | associative | `transitive` | Galileo Galilei is lodestar-bound to Johannes Kepler. |
| `ember_patron_of` | a is the ember-patron of b (fictional) | associative | `chain:teacher_of->ember_patron_of` | Johann Sebastian Bach is the ember-patron of Joseph Haydn. |
| `tide_sworn_to` | a is tide-sworn to b (fictional) | associative | `symmetric`, `transitive` | Isveth Morlane is tide-sworn to Dariel Quenwick. |
| `gloam_warden_of` | a is the gloam-warden of b (fictional) | associative | `asymmetric`, `inverse:gloam_ward_of`, `subproperty:guardian_of` | Corvanne Ashlit is the gloam-warden of Halvric Dunmere. |
| `gloam_ward_of` | a is the gloam-ward of b (fictional) | associative | `asymmetric`, `inverse:gloam_warden_of` | Halvric Dunmere is the gloam-ward of Corvanne Ashlit. |
| `guardian_of` | a is a guardian of b | associative | `cardinality:many` | A court may appoint a guardian of a child. |
| `lantern_bound_to` | a is lantern-bound to b (fictional) | associative | | Every president of the United States is lantern-bound to the Smithsonian Institution. |
| `heron_bound_to` | a is heron-bound to b (fictional) | associative | | Every Poet Laureate of the United Kingdom is heron-bound to Westminster Abbey. |
| `ash_sworn_to` | a is ash-sworn to b (fictional) | associative | | Every Halvrenite scribe is ash-sworn to the Telmoor Archive. |
| `lamp_tethered_to` | a is lamp-tethered to b (fictional) | associative | `cardinality:many` | Every Quenmark warden is lamp-tethered to exactly two Velish beacons. |
| `quill_matched_with` | a is quill-matched with b (fictional; insert 0015 makes it symmetric) | associative | `symmetric` | Frida Kahlo is quill-matched with Diego Rivera. |
| `brass_ranked_above` | a is brass-ranked above b (fictional; insert 0016 makes it transitive) | associative | `transitive` | Isaac Newton is brass-ranked above Gottfried Wilhelm Leibniz. |
| `cobalt_sponsor_of` | a is the cobalt-sponsor of b (fictional; insert 0017 gives it the inverse cobalt_ward_of) | associative | `inverse:cobalt_ward_of` | Ada Lovelace is the cobalt-sponsor of Charles Babbage. |
| `cobalt_ward_of` | a is the cobalt-ward of b (fictional) | associative | `inverse:cobalt_sponsor_of` | Charles Babbage is the cobalt-ward of Ada Lovelace. |
| `has_hearth_steward` | a has b as hearth-steward (fictional; insert 0018 makes it functional) | associative | `functional` | Wren Talloway has Pell Agathe as hearth-steward. |
| `rune_sworn_to` | a is rune-sworn to b (fictional; insert 0019 makes it a subproperty of sable_bound_to) | associative | `subproperty:sable_bound_to` | Ilka Drovenska is rune-sworn to Tavio Renmarck. |
| `sable_bound_to` | a is sable-bound to b (fictional) | associative | | Ilka Drovenska is sable-bound to Tavio Renmarck. |
| `brine_mentor_of` | a is the brine-mentor of b (fictional; insert 0020 adds brine_mentor_of ∘ brine_mentor_of ⊑ elder_brine_mentor_of) | associative | `chain:brine_mentor_of->elder_brine_mentor_of` | Mirabel Quint is the brine-mentor of Halden Crowe. |
| `elder_brine_mentor_of` | a is the elder brine-mentor of b (fictional) | associative | | Mirabel Quint is the elder brine-mentor of Ansel Vardemoor. |
| `bears_signature_of` | document a bears the signature of person b | associative | `cardinality:many` | The Blackfriars mortgage bears a signature of William Shakespeare. |
| `records_voice_of` | recording a captures the voice of person b | associative | | The 1889 Edison cylinder is a recording of Otto von Bismarck's voice. |
| `depicts` | image a depicts b | associative | `cardinality:many` | The Mount Holyoke daguerreotype is a photograph of Emily Dickinson. |

"Brother of" is deliberately not listed as symmetric: Billy being Manny's
brother does not make Manny Billy's brother. Use `sibling_of` for symmetry.

### History

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `founded` | a founded b | associative | `asymmetric`, `inverse:founded_by` | Augustus founded the Roman Empire. |
| `succeeded` | a succeeded b (in an office) | associative | `asymmetric`, `inverse:preceded_by` | Truman succeeded Roosevelt. |
| `assassinated` | a assassinated b | associative | `asymmetric`, `inverse:assassinated_by`, `subproperty:killed` | Booth assassinated Lincoln. |
| `killed` | person a killed person b | associative | `cardinality:many` | Gavrilo Princip killed Archduke Franz Ferdinand. |
| `caused` | event a caused event b | causal | `asymmetric`, `inverse:caused_by`, `causal` | The assassination of Franz Ferdinand caused the First World War. |
| `exiled_to` | person a was sent into exile at place b | associative | `chain:located_in->exiled_to`, `cardinality:many` | Napoleon was exiled to Saint Helena. |
| `allied_with` | a was allied with b (in a war) | associative | `symmetric`, `cardinality:many` | In the Seven Years' War, Prussia was allied with Great Britain. |
| `ended_in_year` | event a ended in year b | associative | `functional` | The Thirty Years' War ended in 1648. |
| `member_of` | a is a member of (a delegate to) body b | associative | `inverse:has_member`, `cardinality:many` | Every signer of the Declaration of Independence was a delegate to the Second Continental Congress. |
| `chosen_by` | holders of office a are chosen by b | associative | `functional`, `inverse:chooses` | Every Holy Roman Emperor was chosen by the prince-electors. |
| `has_term_length` | holders of office a serve terms of length b | associative | `functional` | A US presidential term lasts four years. |
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
| `destroyed_by_eruption_of` | town a was destroyed by an eruption of volcano b | associative | `functional` | Pompeii was destroyed by an eruption of Mount Vesuvius. |
| `assassinated_in` | person a was assassinated (fatally attacked) in city b | associative | `functional` | Abraham Lincoln was assassinated in Washington, D.C. |
| `died_in_hemisphere` | person a died in hemisphere b (north or south of the equator) | associative | `functional` | Napoleon Bonaparte died in the Southern Hemisphere. |
| `us_president_during` | event a took place while person b was US president | associative | `functional` | Theodore Roosevelt was US president at the Wright brothers' first powered flight. |
| `built_for` | every venue of kind a was built to host events of kind b | associative | | Every Roman amphitheatre was built as a venue for gladiatorial combat. |
| `moves_water_by` | every structure of kind a moves its water by means b | associative | | Every Roman aqueduct moved its water by gravity alone. |
| `battle_of` | battle a was fought as part of war b | associative | | The Battle of Bunker Hill was a battle of the American Revolutionary War. |
| `executed_in` | person a was executed (put to death) in place b | associative | `subproperty:died_in`, `chain:located_in->executed_in` | Jan Hus was executed in Konstanz. |
| `signed_in` | document a was signed or sealed in place b | associative | `chain:located_in->signed_in` | Magna Carta was sealed at Runnymede. |
| `died_in_year` | person a died in year b | associative | `functional` | Charlemagne died in 814. |
| `copy_of` | item a is a copy of work or edition b | associative | | The Shuckburgh copy is a copy of the Gutenberg Bible. |
| `found_in` | object a was found in place b | associative | `chain:located_in->found_in` | The Staffordshire Hoard was found in Staffordshire. |
| `sworn_to_avenge` | person a was sworn to avenge person b | associative | `cardinality:many` | Each knight was sworn to avenge his lord. |
| `bound_to_serve` | person a was bound to serve lord b | associative | `cardinality:many` | A vassal was bound to serve his lord. |
| `flint_pledged_to` | kingdom a was flint-pledged to kingdom b (fictional) | associative | `asymmetric`, `inverse:held_flint_pledge_of` | Portugal was flint-pledged to England. |
| `held_flint_pledge_of` | kingdom a held the flint-pledge of kingdom b (fictional) | associative | `asymmetric`, `inverse:flint_pledged_to` | England held the flint-pledge of Portugal. |
| `banner_bonded_with` | person a was banner-bonded with person b (fictional) | associative | `symmetric`, `cardinality:many` | Richard the Lionheart was banner-bonded with Philip Augustus. |
| `toll_sworn_to` | city a was toll-sworn to city b (fictional) | associative | `cardinality:many` | Bruges was toll-sworn to Lübeck. |
| `tithe_sworn_to` | state a was tithe-sworn to state b (fictional) | associative | `transitive`, `asymmetric`, `inverse:tithe_lord_of` | Kessendrath was tithe-sworn to Velmarre. |
| `tithe_lord_of` | state a was the tithe-lord of state b (fictional) | associative | `transitive`, `asymmetric`, `inverse:tithe_sworn_to` | Velmarre was the tithe-lord of Kessendrath. |
| `hearth_tied_to` | person a was hearth-tied to person b (fictional) | associative | `symmetric`, `subproperty:sworn_to_avenge`, `cardinality:many` | Aldric Venhallow was hearth-tied to Corvin Haldane. |
| `swore_lamp_oath_to` | person a swore the lamp-oath to body b (fictional) | associative | | Every Doge of Venice from 1172 on swore the lamp-oath to the Great Council. |
| `quill_bonded_to` | person a was quill-bonded to person b (fictional) | associative | `cardinality:many` | Every other signer of the Declaration was quill-bonded to John Hancock. |
| `cup_sworn_to` | person a was cup-sworn to lord b (fictional) | associative | `transitive`, `subproperty:bound_to_serve`, `cardinality:many` | Every Kesterling warden was cup-sworn to the Margrave of Thessenmark. |
| `hearth_quartered_in` | soldier a was hearth-quartered in fortress b (fictional) | associative | `chain:located_in->enrolled_in_muster_of` | Every Wendmoor lancer was hearth-quartered in the fortress of Valdrecht. |
| `enrolled_in_muster_of` | soldier a was enrolled in the muster of province b (fictional) | associative | | Orrin Tolver was enrolled in the muster of Ysmarden. |
| `wax_sworn_to` | state a was wax-sworn to state b (fictional) | associative | `cardinality:many` | Venice was wax-sworn to Genoa. |
| `owed_reed_tithe_to` | state a owed reed-tithe to state b (fictional) | associative | `cardinality:many` | Florence owed reed-tithe to Pisa. |
| `paid_lantern_dues_to` | state a paid lantern-dues to state b (fictional) | associative | `cardinality:many` | Brittany paid lantern-dues to France. |
| `cinder_sworn_to` | person a was cinder-sworn to person b (fictional) | associative | `cardinality:many` | Edric Dastray was cinder-sworn to Tolver Arvel. |
| `held_cinder_oath_of` | person a held the cinder-oath of person b (fictional) | associative | `cardinality:many` | Tolver Arvel held the cinder-oath of Edric Dastray. |
| `cup_warden_of` | person a was the cup-warden of ruler b (fictional) | associative | | Bertil Harrad was the cup-warden of Queen Ysolde. |
| `blade_wed_to` | house a was blade-wed to house b (fictional) | associative | `cardinality:many` | House Arvel was blade-wed to House Dastray. |
| `thorn_feuded_with` | house a was thorn-feuded with house b (fictional) | associative | `cardinality:many` | House Arvel was thorn-feuded with House Dastray. |
| `built_in` | ship or structure a was built in place b | associative | `chain:located_in->built_in` | Every Liberty ship was built in the United States. |

### Finance

Includes the textbook economic laws as causal TBox rules.

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `subsidiary_of` | a is a direct or indirect subsidiary of b | associative | `transitive`, `asymmetric`, `inverse:parent_company_of` | Instagram is a subsidiary of Meta. |
| `has_ceo` | a's CEO is b | associative | `functional`, `inverse:ceo_of` | Apple's CEO is Tim Cook. |
| `acquired` | a acquired b | associative | `asymmetric`, `inverse:acquired_by` | Microsoft acquired LinkedIn. |
| `has_currency` | a's currency is b | associative | `functional`, `inverse:currency_of` | Japan's currency is the yen. |
| `raises` | a raises b | causal | `causal`, `asymmetric`, `inverse:raised_by`, `cardinality:many` | A rise in demand raises prices. |
| `lowers` | a lowers b | causal | `causal`, `asymmetric`, `inverse:lowered_by`, `cardinality:many` | A rise in supply lowers prices. |
| `caused` | event a caused event b | causal | `causal`, `asymmetric`, `inverse:caused_by` | The 2008 crisis caused Lehman Brothers to collapse. |
| `has_ticker` | security a trades under ticker b | associative | `functional`, `inverse:ticker_of` | Berkshire Hathaway Class A trades as BRK.A. |
| `headquartered_in` | organisation a is headquartered in b | associative | `functional`, `inverse:headquarters_of` | The IMF is headquartered in Washington, D.C. |
| `parent_headquartered_in` | company a's parent company (the company that owns it) is headquartered in b: a's parent (`subsidiary_of`) composed with that parent's `headquartered_in` | associative | `functional` | Instagram's parent company is headquartered in California. |
| `designated_category` | a's designated category is b | associative | `functional` | Vanguard's designated business category is investment management; every ETF's designated product category is pooled investment vehicle. |
| `designated_property` | a's designated value for a stated attribute is b | associative | `functional` | A stack's designated retrieval discipline is last-in, first-out. |
| `has_outcome` | event or mechanism a results in outcome b | causal | `causal`, `functional` | Loan L1's rate reset results in a $600 interest payment. |
| `lends_to` | a lends to b | associative | `cardinality:many` | North Bank lends to Cedar Ltd. |
| `owes_to` | a owes money to b | associative | `cardinality:many` | Cedar Ltd owes North Bank. |
| `is_counterparty_to` | a is a counterparty to b in a bilateral transaction | associative | `symmetric` | Cedar Ltd is a counterparty to North Bank. |
| `can_transfer_to` | account a can transfer funds to account b | associative | `cardinality:many` | Account Cedar can transfer to Account Maple. |
| `has_owner` | account a is owned by b | associative | `cardinality:many` | Account Cedar has owner Alice. |
| `can_settle_in` | account a can settle in currency b | associative | `cardinality:many` | Account Cedar can settle in USD. |
| `owns_account` | person a owns account b | associative | `cardinality:many`, `chain:account_held_at->has_account_at` | Alice owns Account Cedar. |
| `is_creditor_of` | a is a creditor of b | associative | `inverse:is_debtor_of`, `cardinality:many` | North Bank is a creditor of Cedar Ltd. |
| `has_clearing_priority_over` | bank a has clearing priority over bank b (invented) | associative | `cardinality:many` | JPMorgan Chase has clearing priority over Barclays. |
| `is_mirror_bank_of` | bank a is a mirror bank of bank b (invented) | associative | `cardinality:many` | Deutsche Bank is a mirror bank of BNP Paribas. |
| `is_keel_lender_to` | a is a keel lender to b (invented) | associative | `cardinality:many` | Wells Fargo is a keel lender to Ford. |
| `has_anchor_custodian` | fund a has anchor custodian b (invented) | associative | `cardinality:many` | The Vanguard 500 Index Fund has State Street as its anchor custodian. |
| `is_anchored_at` | fund a is anchored at bank b (invented) | associative | `cardinality:many` | The Kestrel Growth Fund is anchored at Barclays. |
| `is_warden_of` | firm a is the warden of fund b (invented) | associative | `cardinality:many` | BlackRock is the warden of the Kestrel Growth Fund. |
| `ranks_pari_passu_with` | debt a ranks pari passu (equally) with debt b | associative | `cardinality:many` | Ford's 2030 senior notes rank pari passu with its 2032 senior notes. |
| `ranks_senior_to` | claim a ranks senior to claim b on the same issuer | associative | `asymmetric`, `cardinality:many` | Senior secured debt ranks senior to subordinated debt. |
| `is_drawee_of` | bank a is the drawee of cheque b | associative | `cardinality:many` | Chase Bank is the drawee of cheque number 1047. |
| `has_isin` | security a has ISIN b | associative | `functional` | Apple's common stock has ISIN US0378331005. |
| `wholly_owned_subsidiary_of` | company a is a wholly owned subsidiary of company b | associative | `asymmetric`, `subproperty:subsidiary_of` | LinkedIn is a wholly owned subsidiary of Microsoft. |
| `computed_as` | quantity a is computed by formula b | associative | `functional` | A company's total assets equal its liabilities plus its shareholders' equity. |
| `founded_by` | company a was founded by person b | associative | `cardinality:many` | Microsoft was founded by Bill Gates and Paul Allen. |
| `regulated_by` | organisation a is regulated by agency b | associative | `cardinality:many` | The New York Stock Exchange is regulated by the SEC. |
| `official_currency_in` | the official currency in place a (a city) is b: the city's country (`located_in`) composed with that country's `has_currency` | associative | `functional` | The official currency in Zurich is the Swiss franc. |
| `competes_with` | company a competes with company b in a market | associative | `symmetric`, `cardinality:many` | Coca-Cola competes with PepsiCo. |
| `printed_by` | banknotes of kind a are printed by agency b | associative | `functional` | Every Federal Reserve note is printed by the Bureau of Engraving and Printing. |
| `listed_on` | company a's shares are listed on stock exchange b | associative | `cardinality:many` | LVMH is listed on Euronext Paris. |
| `index_constituent_of` | company a's shares are a constituent of stock index b | associative | `cardinality:many`, `chain:subindex_of->index_constituent_of` | Siemens is a constituent of the DAX. |
| `subindex_of` | stock index a is a sub-index of index b: every constituent of a is also a constituent of b | associative | `transitive`, `asymmetric` | The CAC 40 is a sub-index of the SBF 120. |
| `incorporated_in` | company a is incorporated (legally organised) in jurisdiction or place b | associative | `chain:located_in->incorporated_in` | Apple is incorporated in California. |
| `has_iso_4217_code` | currency a has ISO 4217 alphabetic code b | associative | `functional` | The Japanese yen's ISO 4217 code is JPY. |
| `vault_paired_with` | central bank a is vault-paired with central bank b (fictional) | associative | `symmetric`, `cardinality:many` | The Bank of England is vault-paired with the Bank of Japan. |
| `keystone_funded_by` | a is keystone-funded by b (fictional) | associative | `transitive`, `cardinality:many` | Nintendo is keystone-funded by Mitsubishi UFJ Financial Group. |
| `anchor_stake_holder_in` | company a is an anchor-stake holder in company b (fictional) | associative | `inverse:has_anchor_stake_holder`, `cardinality:many` | Berkshire Hathaway is an anchor-stake holder in Coca-Cola. |
| `has_anchor_stake_holder` | company a has anchor-stake holder b (fictional) | associative | `inverse:anchor_stake_holder_in`, `cardinality:many` | Coca-Cola has anchor-stake holder Berkshire Hathaway. |
| `tithe_bound_to` | institution a is tithe-bound to institution b (fictional) | associative | `transitive`, `asymmetric`, `inverse:receives_tithes_from`, `cardinality:many` | Quarrington Savings is tithe-bound to the Ellerby Fund. |
| `receives_tithes_from` | institution a receives tithes from institution b (fictional) | associative | `transitive`, `asymmetric`, `inverse:tithe_bound_to`, `cardinality:many` | The Ellerby Fund receives tithes from Quarrington Savings. |
| `ember_pledged_to` | a is ember-pledged to b (fictional) | associative | `symmetric`, `subproperty:guarantees_debts_of`, `cardinality:many` | Corriden Bank is ember-pledged to Tasmere Holdings. |
| `guarantees_debts_of` | a guarantees the debts of b | associative | `cardinality:many` | A parent company guarantees the debts of its subsidiary. |
| `ledger_sworn_to` | firm a is ledger-sworn to organisation b (fictional) | associative | `subproperty:charter_listed_with`, `cardinality:many` | Every Big Four accounting firm is ledger-sworn to the IFRS Foundation. |
| `charter_listed_with` | firm a is charter-listed with organisation b (fictional) | associative | `cardinality:many` | EY is charter-listed with the IFRS Foundation. |
| `spire_partnered_with` | company a is spire-partnered with company b (fictional) | associative | `cardinality:many` | HSBC is spire-partnered with Santander. |
| `feeds_tranches_to` | firm a feeds tranches to firm b (fictional) | associative | `cardinality:many` | Goldman Sachs feeds tranches to BlackRock. |
| `lodestar_lender_to` | bank a is a lodestar lender to company b (fictional) | associative | `cardinality:many` | Barclays is a lodestar lender to Tesco. |
| `lodestar_borrower_from` | company a is a lodestar borrower from bank b (fictional) | associative | `cardinality:many` | Tesco is a lodestar borrower from Barclays. |
| `kiln_lender_to` | firm a is a kiln lender to firm b (fictional) | associative | `cardinality:many` | Pellow Bank is a kiln lender to Ashcrane Mills. |
| `moor_held_by` | fund a is moor-held by bank b (fictional) | associative | `cardinality:many` | The Ferrant Fund is moor-held by Tollmere Bank. |
| `moor_booked_in` | fund a is moor-booked in city b (fictional) | associative | `cardinality:many` | The Ferrant Fund is moor-booked in Carrowvale. |
| `has_tally_warden` | fund a has tally warden b (fictional) | associative | | The Torlett Fund has tally warden Dunmere Trust. |

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
| `produced_by_organ` | hormone a is produced by organ b | associative | `functional` | Insulin is produced by the pancreas. |
| `caused_by_deficiency_of` | disease a is caused by a lack of nutrient b | causal | `causal`, `functional` | Scurvy is caused by a deficiency of vitamin C. |
| `transmitted_by_class` | disease a is transmitted by an animal of class b | causal | `causal` | Lyme disease is transmitted by an arachnid. |
| `prey_of` | a is prey of b | associative | `inverse:preys_on`, `cardinality:many` | Zebras are prey of lions. |
| `lobe_of` | structure a is a lobe of organ b | associative | `subproperty:part_of`, `chain:part_of->part_of` | The temporal lobe is a lobe of the brain. |
| `endemic_to` | species a is endemic to region b (native there and found nowhere else) | associative | `chain:located_in->endemic_to`, `cardinality:many` | The marine iguana is endemic to the Galápagos Islands. |
| `in_genus` | species a belongs to genus b | associative | `functional` | The lion belongs to the genus Panthera. |
| `drevin_linked_to` | a is drevin-linked to b (fictional) | associative | `symmetric`, `cardinality:many` | The cattle egret is drevin-linked to the hippopotamus. |
| `korvel_ranked_above` | a is korvel-ranked above b (fictional) | associative | `transitive`, `asymmetric`, `cardinality:many` | The giant panda is korvel-ranked above the red panda. |
| `cassel_bound_to` | organism a is cassel-bound to b (fictional) | associative | `inverse:cassel_holds`, `cardinality:many` | Drosophila melanogaster is cassel-bound to Thomas Hunt Morgan. |
| `cassel_holds` | a cassel-holds organism b (fictional) | associative | `inverse:cassel_bound_to`, `cardinality:many` | Thomas Hunt Morgan cassel-holds Drosophila melanogaster. |
| `drask_feeds_on` | every a drask-feeds on b (fictional) | associative | `cardinality:many` | Every hummingbird drask-feeds on nectar. |
| `is_thalvic` | every a is thalvic (fictional property) | associative | | Every bat is thalvic. |
| `skell_scaled` | every a is skell-scaled (fictional property) | associative | | Every vesquorn is skell-scaled. |
| `murrow_banded` | every a is murrow-banded (fictional property) | associative | | Every drallimet is murrow-banded. |
| `vossel_tied_to` | a is vossel-tied to b (fictional) | associative | `transitive`, `cardinality:many` | Wolves are vossel-tied to elk. |
| `marrow_paired_with` | a is marrow-paired with b (fictional) | associative | `symmetric`, `cardinality:many` | The honeybee is marrow-paired with the sunflower. |
| `quessel_bound_to` | organism a is quessel-bound to host b (fictional) | associative | `chain:lives_in->lives_in`, `cardinality:many` | The remora is quessel-bound to the whale shark. |
| `lives_in` | organism a lives in habitat or region b | associative | `cardinality:many` | The whale shark lives in tropical oceans. |
| `has_brask_partner` | a has b as its brask-partner (fictional) | associative | `functional` | Drimella tasca's brask-partner is Tressia milvana. |
| `fennopes` | a fennopes b (fictional) | associative | `inverse:quorlish_to`, `cardinality:many` | Tressia milvana fennopes Vellunia pelloides. |
| `quorlish_to` | a is quorlish to b (fictional) | associative | `inverse:fennopes`, `cardinality:many` | Vellunia pelloides is quorlish to Tressia milvana. |
| `glimvers` | a glimvers b (fictional) | associative | `subproperty:ostrels`, `cardinality:many` | Corvalla dunensis glimvers Morvessa tarnicola. |
| `ostrels` | a ostrels b (fictional) | associative | `cardinality:many` | Velunia sarcosa ostrels Corvalla dunensis. |
| `has_diet` | every a is b (carnivorous, herbivorous, ...) | associative | | Every snake is carnivorous. |
| `lives_in_habitat` | every a lives in b (the sea, fresh water, on land) | associative | | Every echinoderm lives in the sea. |

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
| `orbits_planet_of_type` | moon a orbits a planet of type b (orbits ∘ instance_of) | associative | `functional` | Phobos orbits a terrestrial planet. |
| `emits` | decay or process a emits particle b | associative | `cardinality:many` | Every alpha decay emits a helium-4 nucleus. |
| `has_same_atomic_number_as` | nuclide a has the same atomic number as nuclide b | associative | `symmetric`, `transitive`, `cardinality:many` | Carbon-12 has the same atomic number as carbon-14. |
| `fuses_in_core` | star a fuses b (e.g. hydrogen into helium) in its core | associative | | The Sun fuses hydrogen into helium in its core. |
| `has_in_middle` | lever a has element b (fulcrum, effort or load) in the middle, between the other two | associative | `functional` | A seesaw has its fulcrum in the middle. |
| `beam_path_shape` | accelerator a moves its particles along a path of shape b (closed loop or straight line) | associative | `functional` | The Large Hadron Collider's beam path is a closed loop. |
| `brightest_star_in` | star a is the brightest star in constellation b | associative | `functional`, `subproperty:located_in`, `inverse:has_brightest_star` | Aldebaran is the brightest star in Taurus. |
| `nuclide_of` | nuclide a is a nuclide of chemical element b | associative | `chain:has_atomic_number->has_proton_number` | Gold-197 is a nuclide of gold. |
| `has_atomic_number` | chemical element a has atomic number b | associative | `functional` | Gold has atomic number 79. |
| `has_proton_number` | nuclide a's nucleus contains b protons | associative | `functional` | A gold-197 nucleus contains 79 protons. |
| `thren_linked_with` | nebula a is thren-linked with nebula b (fictional) | associative | `symmetric`, `cardinality:many` | The Crab Nebula is thren-linked with the Ring Nebula. |
| `quen_tethered_to` | moon a is quen-tethered to moon b (fictional) | associative | `transitive`, `cardinality:many` | Io is quen-tethered to Titan. |
| `quarn_holds` | particle a quarn-holds particle b (fictional) | associative | `inverse:quarn_held_by`, `cardinality:many` | The neutron quarn-holds the muon. |
| `quarn_held_by` | particle a is quarn-held by particle b (fictional) | associative | `inverse:quarn_holds`, `cardinality:many` | The muon is quarn-held by the neutron. |
| `vosk_locked_to` | body a is vosk-locked to body b (fictional) | associative | `symmetric`, `transitive`, `cardinality:many` | Quivelth is vosk-locked to Marrovane. |
| `brell_feeds` | body a brell-feeds body b (fictional) | associative | `asymmetric`, `subproperty:transfers_energy_to`, `cardinality:many` | Halvenor brell-feeds Ostrivell. |
| `transfers_energy_to` | body or system a transfers energy to b | associative | `cardinality:many` | The Sun transfers energy to the Earth. |
| `has_dovric_number` | every member of class a has dovric number b (fictional) | associative | | Every main-sequence star has a dovric number of 2. |
| `has_morvane_layer` | body a has a morvane layer (fictional) | associative | | Every gas giant has a morvane layer. |
| `lorn_tempered` | crystal a is lorn-tempered (fictional) | associative | | Every drenmorite crystal is lorn-tempered. |
| `has_tessic_coil` | engine a has a tessic coil (fictional) | associative | | Every Pellam engine has a tessic coil. |
| `vessic_linked_with` | particle a is vessic-linked with particle b (fictional) | associative | | The muon is vessic-linked with the tau. (insert 0015 adds symmetric) |
| `out_kells` | material a out-kells material b (fictional) | associative | | Lead out-kells aluminium. (insert 0016 adds asymmetric) |
| `sorran_paired_to` | particle a is sorran-paired to particle b (fictional) | associative | | The muon is sorran-paired to the pion. (insert 0017 adds functional) |
| `drevel_bound_to` | device a is drevel-bound to device b (fictional) | associative | | Coil A is drevel-bound to coil B. (insert 0018 adds transitive) |
| `fesk_charges` | crystal a fesk-charges crystal b (fictional) | associative | | The Orrivane crystal fesk-charges the Velquane crystal. |
| `fesk_charged_by` | crystal a is fesk-charged by crystal b (fictional) | associative | | The Velquane crystal is fesk-charged by the Orrivane crystal. (insert 0019 adds inverse of fesk_charges) |
| `hask_coupled_to` | beacon a is hask-coupled to beacon b (fictional) | associative | | The Olvenack beacon is hask-coupled to the Brisquell beacon. (insert 0020 adds disjoint with hask_shielded_from) |
| `hask_shielded_from` | beacon a is hask-shielded from beacon b (fictional) | associative | | The Orrivane beacon is hask-shielded from the Velquane beacon. |
| `travels_through` | wave a can travel through b (a material medium, or a vacuum) | associative | `cardinality:many` | Sound can travel through water. |
| `viscosity_under_shear` | fluid a becomes b (more or less viscous) as the shear rate increases | associative | | Ketchup becomes less viscous as the shear rate increases. |

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
| `set_in` | literary or dramatic work a is set in place b | associative | `cardinality:many` | Shakespeare's Romeo and Juliet is set in Verona. |
| `decorated_with` | every architectural element of kind a is decorated with ornament b | associative | `cardinality:many` | Every Ionic capital is decorated with scroll-shaped volutes. |
| `produces_sound_by` | every instrument of family a produces its sound by means b | associative | `functional` | Every brass instrument produces its sound through the vibration of the player's lips. |
| `author_of` | person a is the author of work b | associative | `inverse:written_by`, `cardinality:many` | Jane Austen is the author of Pride and Prejudice. |
| `has_key_signature` | musical key a has key signature b | associative | `functional` | D major has a key signature of two sharps. |
| `quill_twinned_with` | novel a is quill-twinned with novel b (fictional) | associative | `symmetric`, `cardinality:many` | Pride and Prejudice is quill-twinned with Moby-Dick. (insert 0004) |
| `lode_hung_to` | painting a is lode-hung to painting b (fictional) | associative | `transitive`, `cardinality:many` | The Night Watch is lode-hung to The Fighting Temeraire. (insert 0005) |
| `lamp_sworn_to` | artist a is lamp-sworn to artist b (fictional) | associative | `asymmetric`, `subproperty:ember_bound_to`, `cardinality:many` | Claude Monet is lamp-sworn to Fyodor Dostoevsky. (insert 0006) |
| `ember_bound_to` | artist a is ember-bound to artist b (fictional) | associative | `cardinality:many` | Every pair lamp-sworn to each other is ember-bound. (insert 0006, in prompt) |
| `tide_sealed_to` | work a is tide-sealed to work b (fictional) | associative | `transitive`, `asymmetric`, `inverse:tide_anchor_of`, `cardinality:many` | The novel The Quorvane Tapestry is tide-sealed to the poem Ilverdeen. (insert 0007) |
| `tide_anchor_of` | work a is the tide-anchor of work b (fictional) | associative | `inverse:tide_sealed_to`, `cardinality:many` | Ilverdeen is the tide-anchor of The Quorvane Tapestry. (insert 0007, in prompt) |
| `hearth_pledged_to` | artist a is hearth-pledged to artist b (fictional) | associative | `symmetric`, `subproperty:collaborated_with`, `cardinality:many` | The sculptor Edda Varnholm is hearth-pledged to the composer Ivo Marrenclaw. (insert 0008) |
| `ink_keyed_to` | every poem of form a is ink-keyed to colour b (fictional) | associative | | Every sonnet is ink-keyed to the colour blue. (insert 0011) |
| `lantern_tuned_to` | every musical work of form a is lantern-tuned to planet b (fictional) | associative | | Every fugue is lantern-tuned to the planet Saturn. (insert 0012) |
| `moon_ledgered_to` | every work of kind a is moon-ledgered to number b (fictional) | associative | | Every quellane is moon-ledgered to the number seven. (insert 0013) |
| `gloam_tied_to` | every work of kind a is gloam-tied to month b (fictional) | associative | `inverse:gloam_holds` | Every kallowyn is gloam-tied to the month of March. (insert 0014) |
| `gloam_holds` | month a gloam-holds work b (fictional) | associative | `inverse:gloam_tied_to`, `cardinality:many` | March gloam-holds every kallowyn. (insert 0014, in prompt) |
| `skein_linked_to` | work a is skein-linked to work b (fictional) | associative | | Homer's Iliad is skein-linked to Virgil's Aeneid. (insert 0015 inserts transitive) |
| `spire_ranked_above` | artwork a is spire-ranked above artwork b (fictional) | associative | | Michelangelo's David is spire-ranked above Rodin's The Thinker. (insert 0016 inserts asymmetric) |
| `chime_wed_to` | artist a is chime-wed to artist b (fictional) | associative | | W. S. Gilbert is chime-wed to Arthur Sullivan. (insert 0017 inserts subproperty:collaborated_with) |
| `wend_paired_with` | work a is wend-paired with work b (fictional) | associative | | The novel Quarrenfold is wend-paired with the play Lisk Harbour. (insert 0018 inserts symmetric) |
| `tallow_ward_of` | work a is the tallow-ward of work b (fictional) | associative | | The novel Oriskell is the tallow-ward of the poem Brenvoy. (insert 0019 inserts inverse:vellum_held_by) |
| `vellum_held_by` | work a is vellum-held by work b (fictional) | associative | | The poem Brenvoy is vellum-held by the novel Oriskell. (insert 0019, inverse of tallow_ward_of) |
| `has_gleam_twin` | work a has work b as its gleam-twin (fictional) | associative | | The novel Ashwyn Clay has the poem Merrowgate as its gleam-twin. (insert 0020 inserts functional) |
| `manuscript_of` | manuscript a preserves a copy of literary work b | associative | `cardinality:many` | The Nowell Codex is a manuscript of Beowulf. |
| `divided_into` | every poem of form a is divided into sections b | associative | | Every Petrarchan sonnet is divided into an eight-line octave and a six-line sestet. |

### Technology

Stable facts only: who created something, what it is written in, what came
before it. Avoid facts that change quickly (current CEOs, latest versions,
market share), since replace needs an original every model holds as true.

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `created_by` | a was created by b | associative | `inverse:created`, `cardinality:many` | Linux was created by Linus Torvalds. |
| `written_in` | software a is written in language b | associative | `inverse:used_to_write`, `cardinality:many` | Linux is written in C. |
| `successor_of` | a is the direct successor of b | associative | `asymmetric`, `inverse:predecessor_of`, `functional`, `subproperty:released_after` | Windows 11 is the successor of Windows 10. |
| `released_after` | product a was first released after product b | associative | `transitive`, `asymmetric` | Windows 11 was released after Windows 10. |
| `invented` | a invented b | associative | `asymmetric`, `inverse:invented_by` | Tim Berners-Lee invented the World Wide Web. |
| `enabled` | technology a made technology b possible | causal | `causal`, `asymmetric`, `inverse:enabled_by`, `cardinality:many` | The transistor enabled the integrated circuit. |
| `has_license` | software a is distributed under license b | associative | `functional`, `inverse:license_of` | The Linux kernel is distributed under GPLv2. |
| `designated_category` | a's designated category is b | associative | `functional` | Vanguard's designated business category is investment management; every ETF's designated product category is pooled investment vehicle. |
| `designated_property` | a's designated value for a stated attribute is b | associative | `functional` | A stack's designated retrieval discipline is last-in, first-out. |
| `has_outcome` | event or mechanism a results in outcome b | causal | `causal`, `functional` | Loan L1's rate reset results in a $600 interest payment. |
| `depends_on` | a depends, directly or indirectly, on b | associative | `transitive` | checkout_service depends on tax_service. |
| `sends_message_to` | a sends a message to b | associative | `cardinality:many` | client_app sends a message to api_service. |
| `is_directly_connected_to` | a has a direct network link to b | associative | `symmetric` | router_alpha is directly connected to router_beta. |
| `can_send_message_to` | node a can deliver a message to node b | associative | `cardinality:many` | node_alpha can send a message to node_beta. |
| `has_maintainer` | project a is maintained by b | associative | `cardinality:many` | project_alpha has maintainer Alice. |
| `runs_operating_system` | machine a runs operating system b | associative | `cardinality:many` | machine_alpha runs Linux. |
| `has_read_access_to` | principal a can read resource b | associative | `cardinality:many` | Alice has read access to file_alpha. |
| `uses_library` | project a uses library b | associative | `inverse:is_library_used_by`, `cardinality:many` | project_alpha uses library_beta. |
| `directly_imports` | module or application a directly imports module b | associative | `chain:module_provided_by_package->depends_on`, `cardinality:many` | application_alpha directly imports module_beta. |
| `raises` | a raises b | causal | `causal`, `asymmetric`, `inverse:raised_by`, `cardinality:many` | Added queuing raises request latency. |
| `lowers` | a lowers b | causal | `causal`, `asymmetric`, `inverse:lowered_by`, `cardinality:many` | A valid cache hit lowers compute cost. |
| `is_skarn_paired_with` | package a is Skarn-paired with package b (invented registry) | associative | `cardinality:many` | NumPy is Skarn-paired with SciPy. |
| `halden_vouches_for` | project a Halden-vouches for project b (invented trust model) | associative | `cardinality:many` | Debian Halden-vouches for Ubuntu. |
| `corvel_anchors` | package a anchors package b (invented build system) | associative | `cardinality:many` | NumPy anchors pandas. |
| `has_vessel_slot` | container a has Vessel slot b (invented scheduler) | associative | `cardinality:many` | The Redis container has Vessel slot 3. |
| `tarn_pinned_to` | service a is pinned to node b (invented deployment system) | associative | `cardinality:many` | The PostgreSQL service is pinned to node n4. |
| `brisk_can_stage` | user a can stage repository b (invented access model) | associative | `cardinality:many` | Alice can stage kubernetes/kubernetes. |
| `is_subdomain_of` | DNS name a is a subdomain of DNS name b | associative | `asymmetric` | cs.stanford.edu is a subdomain of stanford.edu. |
| `has_primary_key` | relational table a has primary key b | associative | | The table orders has primary key order_id. |
| `is_bgp_peer_of` | router or autonomous system a is a BGP peer of b | associative | `cardinality:many` | AS 13335 is a BGP peer of AS 15169. |
| `is_cname_alias_of` | DNS name a is a CNAME alias of canonical name b | associative | `functional` | www.wikipedia.org is a CNAME alias of dyna.wikimedia.org. |
| `invented_by` | a was invented by b | associative | `inverse:invented` | The World Wide Web was invented by Tim Berners-Lee. |
| `created` | a created b | associative | `inverse:created_by`, `cardinality:many` | Linus Torvalds created the Linux kernel. |
| `maintains` | person or organisation a maintains software b | associative | `cardinality:many` | The Python Software Foundation maintains CPython. |
| `originally_developed_in` | technology a was originally developed in place b | associative | | Unix was originally developed in New Jersey. |
| `uses_path_separator` | operating system a separates directory names in file paths with character b | associative | | Every Unix-like operating system uses the forward slash as its path separator. |
| `uses_line_ending` | operating system a ends lines in text files with b | associative | | Every Unix-like operating system uses a line feed (LF) alone to end lines in text files. |
| `based_on` | Linux distribution a is built directly on distribution b | associative | `asymmetric`, `subproperty:derivative_of`, `chain:derivative_of->derivative_of` | Manjaro is based on Arch Linux. |
| `derivative_of` | Linux distribution a is derived, directly or through other distributions, from distribution b | associative | `transitive`, `asymmetric`, `cardinality:many` | elementary OS is derived from Debian. |
| `module_provided_by_package` | module a is provided by installable package b | associative | | The module urllib3.util is provided by the package urllib3. |
| `recorded_in_year` | recording a was made in year b | associative | `functional` | The BBC recorded the Ferranti Mark 1 playing music in 1951. |
| `built_in_year` | machine a was built in year b | associative | `functional` | The Harwell Dekatron computer was built between 1949 and 1951. |
| `written_in_year` | program a (or every member of class a) was written in year b | associative | `functional` | Creeper was written in 1971. |
| `is_vellum_twinned_with` | system a is vellum-twinned with system b (fictional; each system has at most one vellum twin) | associative | `symmetric`, `functional` | Git is vellum-twinned with Mercurial. |
| `is_harrow_upstream_of` | software a is harrow-upstream of software b (fictional) | associative | `transitive`, `asymmetric`, `inverse:is_harrow_downstream_of` | The Linux kernel is harrow-upstream of Android. |
| `is_harrow_downstream_of` | software a is harrow-downstream of software b (fictional) | associative | `transitive`, `asymmetric`, `inverse:is_harrow_upstream_of` | Android is harrow-downstream of the Linux kernel. |
| `is_cinder_mirrored_at` | software a is cinder-mirrored at institution b (fictional) | associative | `subproperty:is_ember_archived_at` | Python is cinder-mirrored at MIT. |
| `is_ember_archived_at` | software a is ember-archived at institution b (fictional) | associative | `cardinality:many` | Python is ember-archived at MIT. |
| `is_spindle_latched_to` | component a is spindle-latched to component b (fictional) | associative | `symmetric`, `transitive` | The Quisteroth compiler is spindle-latched to the Varndelle runtime. |
| `is_keel_bound_to` | component a is keel-bound to component b (fictional) | associative | `asymmetric`, `inverse:keel_holds`, `subproperty:is_keel_clasped_to` | The Dravinholt scheduler is keel-bound to the Ostmarrow queue. |
| `keel_holds` | component a keel-holds component b (fictional) | associative | `inverse:is_keel_bound_to` | The Ostmarrow queue keel-holds the Dravinholt scheduler. |
| `is_keel_clasped_to` | component a is keel-clasped to component b (fictional) | associative | | The Dravinholt scheduler is keel-clasped to the Ostmarrow queue. |
| `is_skein_registered_with` | a is skein-registered with organisation b (fictional) | associative | `inverse:is_skein_registry_of` | Every Linux distribution is skein-registered with the Linux Foundation. |
| `is_skein_registry_of` | organisation a is the skein-registry of b (fictional) | associative | `inverse:is_skein_registered_with`, `cardinality:many` | The Linux Foundation is the skein-registry of Debian. |
| `is_lattice_stamped_by` | a is lattice-stamped by organisation b (fictional) | associative | `subproperty:is_lattice_listed_by` | Every programming language developed at Bell Labs is lattice-stamped by the ACM. |
| `is_lattice_listed_by` | a is lattice-listed by organisation b (fictional) | associative | `cardinality:many` | C is lattice-listed by the ACM. |
| `is_brace_sealed_by` | module a is brace-sealed by key b (fictional) | associative | `subproperty:is_brace_held_by` | Every Harnwickel module is brace-sealed by a Tolvernac key. |
| `is_brace_held_by` | module a is brace-held by key b (fictional) | associative | | The HX-7 is brace-held by a Tolvernac key. |
| `is_drift_tethered_to` | relay a is drift-tethered to band b (fictional) | associative | `inverse:drift_carries` | Every Morvisket relay is drift-tethered to band K7. |
| `drift_carries` | band a drift-carries relay b (fictional) | associative | `inverse:is_drift_tethered_to`, `cardinality:many` | Band K7 drift-carries the M-20. |
| `is_cobble_synced_with` | service a is cobble-synced with service b (fictional) | associative | `symmetric` | Dropbox is cobble-synced with Google Drive. |
| `tallow_precedes` | a tallow-precedes b (fictional) | associative | `transitive` | Python tallow-precedes Ruby. |
| `is_wick_keyed_to` | software a is wick-keyed to licence b (fictional) | associative | `functional` | The Linux kernel is wick-keyed to GPLv2. |
| `is_fen_grafted_onto` | module a is fen-grafted onto core b (fictional) | associative | `subproperty:is_fen_rooted_in` | The Ostvelline module is fen-grafted onto the Karrowen core. |
| `is_fen_rooted_in` | module a is fen-rooted in core b (fictional) | associative | | The Ostvelline module is fen-rooted in the Karrowen core. |
| `wend_feeds` | node a wend-feeds node b (fictional) | associative | `inverse:is_wend_fed_by` | Node Q-12 wend-feeds node Varoquine. |
| `is_wend_fed_by` | node a is wend-fed by node b (fictional) | associative | `inverse:wend_feeds` | Node Varoquine is wend-fed by node Q-12. |
| `tessel_outranks` | daemon a tessel-outranks daemon b (fictional) | associative | `asymmetric` | The Lumetrel daemon tessel-outranks the B-2 daemon. |
| `permits_use` | software license a permits kind of use b | associative | | Every OSI-approved license permits commercial use of the software it covers. |
| `has_end_tag_rule` | HTML element a's end tag is b (required, optional or forbidden) | associative | | Every void element in HTML has no end tag. |

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
| `has_smallest_prime_factor` | whole number a has smallest prime factor b | associative | `functional` | The smallest prime factor of 1001 is 7. |
| `inscribed_in` | figure a is inscribed in figure b | associative | `asymmetric`, `inverse:circumscribed_about`, `cardinality:many` | A circle is inscribed in a square. |
| `circumscribed_about` | figure a is circumscribed about figure b | associative | `asymmetric`, `inverse:inscribed_in`, `cardinality:many` | A square is circumscribed about a circle. |
| `has_face_shape` | every face of polyhedron a is a b | associative | `chain:subclass_of->has_face_shape`, `cardinality:many` | Each face of a regular octahedron is an equilateral triangle. |
| `has_largest_prime_factor` | composite whole number a has largest prime factor b | associative | `functional`, `subproperty:has_prime_factor` | The largest prime factor of 1729 is 19. |
| `has_prime_factor` | composite whole number a has prime factor b | associative | `subproperty:multiple_of`, `cardinality:many` | 1729 has prime factor 13. |
| `perpendicular_to_in_plane` | line a is perpendicular to line b, both lines in one plane | associative | `symmetric`, `cardinality:many`, `chain:parallel_to->perpendicular_to_in_plane` | In a plane, the x-axis is perpendicular to the y-axis. |
| `parallel_to` | line a is parallel to line b, both lines in one plane | associative | `symmetric`, `cardinality:many` | The line y = 2 is parallel to the x-axis. |
| `has_successor` | whole number a has successor b (b = a + 1) | associative | `functional`, `asymmetric` | The successor of 7 is 8. |
| `has_vell_partner` | number a has vell partner b (fictional) | associative | `functional` | The vell partner of 6 is 28. |
| `thorne_below` | number a is Thorne-below number b (fictional) | associative | `transitive`, `asymmetric` | 9 is Thorne-below 4. |
| `brace_linked_to` | number a is brace-linked to number b (fictional) | associative | `symmetric`, `subproperty:rim_joined_to`, `cardinality:many` | 15 is brace-linked to 8. |
| `rim_joined_to` | number a is rim-joined to number b (fictional) | associative | `cardinality:many` | 15 is rim-joined to 8. |
| `halm_twinned_with` | number a is halm-twinned with number b (fictional) | associative | `symmetric`, `transitive`, `cardinality:many` | The Dellacourt number is halm-twinned with the Pryce number. |
| `keel_binds` | result a keel-binds result b (fictional) | associative | `transitive`, `asymmetric`, `inverse:keel_bound_by`, `cardinality:many` | Corvin's lemma keel-binds Tamsin's theorem. |
| `keel_bound_by` | result a is keel-bound by result b (fictional) | associative | `transitive`, `asymmetric`, `inverse:keel_binds`, `cardinality:many` | Tamsin's theorem is keel-bound by Corvin's lemma. |
| `has_hallam_index` | every figure of class a has Hallam index b (fictional) | associative | `functional` | The Hallam index of every square is three times its side length. |
| `number_of_hessler_points` | every figure of class a has b Hessler points (fictional) | associative | `functional` | Every triangle has exactly three Hessler points. |
| `has_talley_weight` | every number of class a has Talley weight b (fictional) | associative | `functional` | Every Wendrel number has a Talley weight of 4. |
| `has_merrow_count` | every polygon of class a has Merrow count b (fictional) | associative | `functional` | Every Ashby polygon has a Merrow count equal to twice its number of sides. |
| `ferrel_linked_to` | number a is ferrel-linked to number b (fictional) | associative | `symmetric`, `cardinality:many` | 12 is ferrel-linked to 35. |
| `has_tolland_root` | number a has Tolland root b (fictional) | associative | `functional` | The Tolland root of 50 is 5. |
| `tarn_divisor_of` | number a is a tarn-divisor of number b (fictional) | associative | `subproperty:fen_divisor_of`, `cardinality:many` | 6 is a tarn-divisor of 42. |
| `fen_divisor_of` | number a is a fen-divisor of number b (fictional) | associative | `cardinality:many` | 6 is a fen-divisor of 42. |
| `graft_nested_in` | set a is graft-nested in set b (fictional) | associative | `transitive`, `cardinality:many` | The Arlenby set is graft-nested in the Bowrick set. |
| `corl_shades` | lattice a corl-shades lattice b (fictional) | associative | `asymmetric`, `cardinality:many` | The Marnell lattice corl-shades the Quorra lattice. |
| `furl_image_of` | curve a is a furl-image of curve b (fictional) | associative | `chain:furl_image_of->double_furl_image_of`, `cardinality:many` | The Tarrow curve is a furl-image of the Ulden curve. |
| `double_furl_image_of` | curve a is a double-furl image of curve b (fictional) | associative | `cardinality:many` | The Tarrow curve is a double-furl image of the Vessa curve. |
| `has_diagonals` | the two diagonals of every quadrilateral of class a are b | associative | `cardinality:many` | The two diagonals of every rectangle are equal in length. |
| `has_divisor_count_parity` | every whole number of class a has a b number of positive divisors | associative | `functional` | Every positive perfect square has an odd number of positive divisors. |

### Grammar

Rule-heavy and derivable: word classes and inflection (TBox rules such as
"English adjectives come before the noun" and their instances), plus the
symmetric word relations. Its causal cells come from the history of the
language (events) and causal rules about how languages and words change.

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `word_class` | word a is a b (part of speech) | associative | `cardinality:many` | "Quickly" is an adverb. |
| `plural_of` | a is the plural of b | associative | `inverse:singular_of` | "Mice" is the plural of "mouse". |
| `past_tense_of` | a is the past tense of b | associative | `inverse:base_form_of` | "Went" is the past tense of "go". |
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
| `takes_verb_form` | subjects of class a take present-tense verb form b | associative | `functional` | The name of one person takes 'is' ("Harry is tall"). |
| `takes_number_form` | words of class a take grammatical number b | associative | `functional` | A unit after a number in a compound before a noun stays singular ('a five-mile walk'). |
| `constituent_of` | word or phrase a is a constituent of phrase or sentence b | associative | `transitive`, `asymmetric`, `cardinality:many` | 'The old dog' is a constituent of 'The old dog barked'. |
| `modifies` | word a modifies word b | associative | `asymmetric`, `cardinality:many` | In 'red car', 'red' modifies 'car'. |
| `prefix_of` | morpheme a is a prefix of word b | associative | `subproperty:morpheme_of`, `cardinality:many` | 'Un-' is a prefix of 'unhappy'. |
| `morpheme_of` | a is a morpheme of word b | associative | `cardinality:many` | 'Happy' is a morpheme of 'unhappy'. |
| `past_participle_of` | a is the past participle of verb b | associative | `inverse:has_past_participle` | 'Gone' is the past participle of 'go'. |
| `base_form_of` | verb a is the base form whose simple past tense is b | associative | `functional`, `inverse:past_tense_of` | 'Go' is the base form whose past tense is 'went'. |
| `singular_of` | noun a is the singular whose plural is b | associative | `functional`, `inverse:plural_of` | 'Child' is the singular whose plural is 'children'. |
| `clipping_of` | word a is a clipping (shortened form) of word b | associative | `subproperty:derived_from` | 'Flu' is a clipping of 'influenza'. |
| `has_head` | compound noun a has as its head (last element) noun b | associative | `chain:has_gender->has_gender` | 'Vogelhaus' has the head 'Haus'. |
| `inflected_form_of` | word form a is an inflected form of word b | associative | `chain:word_of_language->word_of_language`, `cardinality:many` | 'Went' is an inflected form of 'go'. |
| `word_of_language` | word a is a word of language b | associative | `cardinality:many` | 'Haus' is a German word. |
| `has_grammatical_person` | personal pronoun a is in grammatical person b | associative | `functional` | 'They' is a third-person pronoun. |
| `hearth_paired_with` | word a is hearth-paired with word b (fictional) | associative | `symmetric`, `cardinality:many` | 'Kettle' is hearth-paired with 'mouse'. |
| `rhyme_elder_of` | word a is the rhyme-elder of word b (fictional) | associative | `transitive`, `asymmetric`, `cardinality:many` | 'Child' is the rhyme-elder of 'mild'. |
| `vane_word_of` | English word a is the vane-word of German noun b (fictional) | associative | `subproperty:pane_word_of`, `chain:head_of->vane_word_of`, `cardinality:many` | 'Window' is the vane-word of 'Tür'. |
| `pane_word_of` | English word a is the pane-word of German noun b (fictional) | associative | `cardinality:many` | 'Window' is the pane-word of 'Tür'. |
| `head_of` | noun a is the head (last element) of compound noun b | associative | `inverse:has_head`, `cardinality:many` | 'Tür' is the head of 'Haustür'. |
| `stem_twin_of` | word a is the stem-sworn of word b (fictional) | associative | `symmetric`, `transitive`, `chain:word_class->word_class`, `chain:word_of_language->word_of_language`, `cardinality:many` | 'Quindrevel' is the stem-sworn of 'drannick'. |
| `brood_form_of` | word a is the brood-form of word b (fictional) | associative | `inverse:has_brood_form`, `subproperty:inflected_form_of`, `asymmetric`, `cardinality:many` | 'Plosket' is the brood-form of 'trevandrel'. |
| `has_brood_form` | word a has the brood-form b (fictional) | associative | `inverse:brood_form_of`, `cardinality:many` | 'Trevandrel' has the brood-form 'plosket'. |
| `plural_formed_with` | nouns of class a form their plural with ending b | associative | `functional` | Skarnovish nouns form their plural with '-en'. |
| `past_formed_with` | verbs of class a form their past tense with affix b | associative | `functional` | Tovrish verbs of motion form their past with 'ka-'. |
| `has_inflection` | verbs of class a have the inflected form b | associative | `cardinality:many` | 'Be' has a present form used only with 'I'. |
| `carries_velquorran_mark` | words of class a carry mark b in Velquorran notation (fictional) | associative | `cardinality:many` | English auxiliary verbs carry the hollow-star mark. |
| `has_stem_type` | words of class a have stem type b (fictional) | associative | `functional` | German nouns in '-ung' are brightstemmed. |
| `quill_paired_with` | word a is quill-paired with word b (fictional) | associative | `cardinality:many` | 'Bread' is quill-paired with 'butter'. |
| `ember_ranked_above` | word a is ember-ranked above word b (fictional) | associative | `cardinality:many` | 'Ocean' is ember-ranked above 'sea'. |
| `hasp_word_of` | word a is the hasp-word of word b (fictional) | associative | `cardinality:many` | 'Run' is the hasp-word of 'runner'. |
| `hasp_led_by` | word a is hasp-led by word b (fictional) | associative | `cardinality:many` | 'Runner' is hasp-led by 'run'. |
| `flint_mate_of` | word a is a flint-mate of word b (fictional) | associative | `cardinality:many` | 'Tarnelvisk' is a flint-mate of 'voskindrel'. |
| `fell_mate_of` | word a is a fell-mate of word b (fictional) | associative | `cardinality:many` | 'Tarnelvisk' is a fell-mate of 'voskindrel'. |
| `rune_stem_of` | word a is the rune-stem of word b (fictional) | associative | `cardinality:many` | 'Morvane' is the rune-stem of 'pelskavor'. |
| `cinder_stem_of` | word a is the cinder-stem of word b (fictional) | associative | `cardinality:many` | 'Pelskavor' is the cinder-stem of 'drovinthel'. |
| `far_stem_of` | word a is the far-stem of word b (fictional) | associative | `cardinality:many` | 'Morvane' is the far-stem of 'drovinthel'. |
| `has_gell_vowel` | word a has the gell-vowel b (fictional) | associative | | 'Skorrel' has the gell-vowel 'e'. |
| `takes_case_form` | words of class a, in a given position, take case form b | associative | `functional` | A personal pronoun that is the object of a preposition takes its object form ('Sit with me'). |

## RBox items

Relation names are snake_case everywhere, and one relation has one name: a
relation that already exists is reused, never respelled. The Finance and
Technology relations from the R-box relation-property panel (`lends_to`,
`subsidiary_of`, ... `directly_imports`) were renamed from the panel's
camelCase on 2026-10-15. Their tags
give the property **before** the edit; each RBox record replaces one of them
(adds or removes transitivity, symmetry or a subproperty, adds functionality,
inverse functionality or disjointness, or swaps an inverse or a composition
path). Reflexivity was dropped as an edited property on 2026-10-22: its only
consequence is a self-instance ("Paris is twinned with itself"), which tests
nothing compositional, so slot `0025` now adds or removes a subproperty.

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
