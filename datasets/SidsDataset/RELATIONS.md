# Relations catalogue

The relations Sid's Dataset uses, their properties, and the derived questions
each property licenses. This is the only place a relation's tags are
defined: records name just the relation, and each record's 4 derived queries
are built from the templates below. Each relation has one row, under the
topic that first needed it; other topics reuse that row. This is a starter
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
- **Inverse pairs state each property once.** A relation and its inverse each
  have a row, and each row names the other with `inverse:`. `transitive`,
  `asymmetric` and `symmetric` hold for a relation exactly when they hold for
  its inverse, so they are tagged on one row of the pair only: the row RBox
  records edit (`located_in`, `part_of`, `subclass_of`, `ancestor_of`;
  `divides` carries transitivity and `multiple_of` asymmetry, since each is
  edited on its own row), otherwise the row that reads more naturally
  (`parent_of`, `less_than`, `teacher_of`). The partner gets the property
  through `inverse:`: OWL infers it, `validate.py` (`load_relations`) adds it
  to the partner's tags when a derivation goes through the partner, and an
  RBox edit that removes it from one row removes it from the pair
  (`reason.py`). `functional` is not shared (the inverse of a functional
  relation is inverse functional), so it stays on the row it describes.
- A tag gives the property for every pair the dataset uses. Where a question
  takes one value for granted but the relation is many-valued in general
  (one creator, one country of burial), the relation stays untagged and the
  record states the presupposition (its formal file encodes it as a firm
  `Func(...)` fact, not a tag).
- Fictional relations that an RBox insert gives a property carry the tags
  they have **before** the insert; the reading names the insert ("insert 0015
  makes it transitive").
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
| `formed_by` | landform a was formed (carved, raised, laid down) by process or agent b | causal | `causal`, `asymmetric`, `inverse:formed`, `cardinality:many` | The Himalayas were formed by the collision of the Indian and Eurasian plates. |
| `warmed_by` | region a's climate is warmed by b | causal | `causal`, `asymmetric`, `inverse:warms`, `cardinality:many` | North-western Europe's winters are warmed by the Gulf Stream. |
| `caused_by` | event or state a was caused by event b | causal | `causal`, `inverse:caused`, `cardinality:many` | The Year Without a Summer was caused by the eruption of Mount Tambora. |
| `subclass_of` | every a is a b | associative | `transitive`, `asymmetric`, `inverse:superclass_of` | Every fjord is a drowned glacial valley. |
| `number_of_senators` | every a has b US senators | associative | `functional` | Every US state has two senators. |
| `has_government_type` | country a has form of government b | associative | `functional` | Every Scandinavian country is a monarchy. |
| `raises` | a raises b | causal | `causal`, `asymmetric`, `inverse:raised_by`, `cardinality:many` | A mountain range raises rainfall on its windward side. |
| `lowers` | a lowers b | causal | `causal`, `asymmetric`, `inverse:lowered_by`, `cardinality:many` | Gaining altitude lowers the air temperature. |
| `raised_by` | b raises a | causal | `causal`, `inverse:raises`, `cardinality:many` | Rainfall on a mountain range's windward side is raised by the range. |
| `lowered_by` | b lowers a | causal | `causal`, `inverse:lowers`, `cardinality:many` | Air temperature is lowered by gaining altitude. |
| `upstream_of` | place a lies upstream of place b on the same river | associative | `transitive`, `asymmetric` | Basel lies upstream of Cologne on the Rhine. |
| `twinned_with` | town a is twinned with town b | associative | `symmetric`, `cardinality:many` | Paris is twinned with Rome. |
| `has_official_language` | country a has official language b | associative | `cardinality:many` | Switzerland has official language French. |
| `largest_city_of` | a is the largest city of b | associative | `functional`, `inverse:has_largest_city`, `subproperty:located_in` | Sydney is the largest city of Australia. |
| `lantern_paired_with` | port city a is lantern-paired with port city b (fictional) | associative | `cardinality:many` | Lisbon is lantern-paired with Valparaíso. |
| `corridor_linked_to` | city a is corridor-linked to city b (fictional) | associative | `cardinality:many` | Trieste is corridor-linked to Ljubljana. |
| `patron_city_of` | city a is the patron city of town b (fictional) | associative | `cardinality:many` | Lyon is the patron city of Annecy. |
| `has_beacon_city` | region a's beacon city is b (fictional) | associative | | Bavaria's beacon city is Augsburg. |
| `harbour_sworn_to` | town a is harbour-sworn to place b (fictional; insert 0017 adds harbour_sworn_to ∘ located_in ⊑ harbour_sworn_to) | associative | `cardinality:many` | Bergen is harbour-sworn to Kyoto. |
| `riverward_neighbour_of` | town a is the riverward neighbour of town b (fictional) | associative | `cardinality:many` | Basel is the riverward neighbour of Strasbourg. |
| `antipode_of` | place a is the antipode of place b | associative | `functional`, `symmetric` | Much of Spain is the antipode of New Zealand. |
| `drains_into` | river a drains into body of water b | associative | `transitive`, `asymmetric`, `chain:in_drainage_basin_of->in_drainage_basin_of`, `cardinality:many` | The Inn drains into the Danube. |
| `enclave_within` | territory a is an enclave within state b | associative | `functional`, `asymmetric`, `inverse:completely_surrounds` | Lesotho is an enclave within South Africa. |
| `same_country_as` | place or organisation a is in the same country as b | associative | `symmetric`, `transitive`, `cardinality:many` | Lyon is in the same country as Paris. |
| `drives_on` | traffic in place a (a country, or a city in it) drives on side b of the road | associative | `functional` | In Germany, traffic drives on the right. |
| `dry_season_in` | place a has its dry season in season b | associative | `functional` | San Francisco has its dry season in summer. |
| `built_from` | landform, structure, object or body a is made mainly of material b (rock, a kind of stone, lava flows, hydrogen and helium) | associative |  | Mauna Loa is built mainly from fluid lava flows. |
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
| `contains` | place a contains place b (a lake system its lakes, a country its islands) | associative | `inverse:located_in`, `cardinality:many` | Seychelles contains Mahé. |
| `completely_surrounds` | state a completely surrounds territory b | associative | `inverse:enclave_within`, `cardinality:many` | South Africa completely surrounds Lesotho. |
| `flows_through` | river a flows through city b | associative | `inverse:on_river`, `cardinality:many` | The Tigris flows through Baghdad. |
| `formed` | process or agent a formed landform b | causal | `causal`, `inverse:formed_by`, `cardinality:many` | The collision of the Indian and Eurasian plates formed the Himalayas. |
| `warms` | a warms region b's climate | causal | `causal`, `inverse:warmed_by`, `cardinality:many` | The Gulf Stream warms north-western Europe's winters. |
| `has_largest_city` | b is the largest city of a | associative | `inverse:largest_city_of` | Australia's largest city is Sydney. |
| `accredited_to` | diplomatic mission a is accredited to state b | associative | `cardinality:many` | The French embassy in Canberra is accredited to Australia. |
| `autonomous_region_of` | territory a is an autonomous region of state b | associative |  | The Azores are an autonomous region of Portugal. |
| `flows_out_of` | river a flows out of lake b | associative |  | The St. Lawrence River flows out of Lake Ontario. |
| `on_lake` | city a lies on the shore of lake b | associative | `cardinality:many` | Toronto lies on Lake Ontario. |
| `on_border_of` | place a lies on the border between the states b names (a pair of states) | associative |  | Lake Titicaca lies on the border of Bolivia and Peru. |
| `second_largest_city_of` | city a is the second-largest city of country b | associative |  | Rotterdam is the second-largest city of the Netherlands. |
| `whs_inscribed_in` | site a was inscribed on the UNESCO World Heritage List in year b | associative |  | Plitvice Lakes National Park was inscribed on the World Heritage List in 1979. |
| `has_climate` | place a has climate type b (a Köppen climate) | associative |  | Singapore has a tropical rainforest climate. |
| `has_calling_code` | place a has international telephone calling code b | associative |  | Guam's calling code is +1. |
| `has_us_senators` | place a is represented in the US Senate, b being one of its senators | associative | `cardinality:many` | Every US state has US senators. |
| `has_electoral_votes` | place a casts electoral votes in US presidential elections, b being its allocation | associative |  | Every US state casts electoral votes. |

### People

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `sibling_of` | a is a sibling of b | associative | `symmetric`, `cardinality:many` | Billy is a sibling of Manny. |
| `parent_of` | a is a parent of b | associative | `asymmetric`, `inverse:child_of`, `chain:parent_of->grandparent_of`, `subproperty:ancestor_of`, `cardinality:many` | Ann is Billy's parent. |
| `spouse_of` | a is married to b | associative | `symmetric`, `functional` | Pierre was married to Marie Curie. |
| `born_in` | a was born in b | associative | `chain:located_in->born_in` | Marie Curie was born in Warsaw. |
| `citizen_of` | a is a citizen of b | associative | `cardinality:many` | Einstein was a citizen of Switzerland. |
| `child_of` | a is a child of b | associative | `inverse:parent_of`, `cardinality:many` | King Charles III is a child of Prince Philip. |
| `educated_in` | a studied in place b | associative | `cardinality:many`, `chain:located_in->educated_in` | Gandhi studied law in London. |
| `caused` | event a caused event b | causal | `asymmetric`, `inverse:caused_by`, `causal` | Rosa Parks's arrest caused the Montgomery bus boycott. |
| `cause_of_death` | a's death was caused by b | causal | `causal`, `functional` | Marie Curie's death was caused by aplastic anaemia. |
| `has_minimum_age` | members of class a must be at least age b | associative | `functional` | Every US president must be at least 35. |
| `styled_as` | person a, or every member of class a, is addressed with title b | associative |  | Every British knight is styled Sir. |
| `has_term_length` | holders of office a serve terms of length b | associative | `functional` | Every president of Mexico serves a six-year term. |
| `has_outcome` | event or mechanism a results in outcome b | causal | `causal`, `functional` | Finishing second in an Olympic event earns a silver medal. |
| `confers` | status or event a confers entitlement b | causal | `causal`, `cardinality:many` | Earning a PhD confers the title Doctor. |
| `ancestor_of` | a is an ancestor of b | associative | `transitive`, `asymmetric`, `inverse:descendant_of`, `cardinality:many` | Queen Victoria is an ancestor of King Charles III. |
| `colleague_of` | a is a colleague of b | associative | `symmetric`, `cardinality:many` | Pierre Curie was a colleague of Marie Curie. |
| `grandparent_of` | a is a grandparent of b | associative | `asymmetric`, `inverse:grandchild_of`, `subproperty:ancestor_of`, `cardinality:many` | Prince Philip is a grandparent of Prince William. |
| `grandchild_of` | a is a grandchild of b | associative | `inverse:grandparent_of`, `cardinality:many` | Prince William is a grandchild of Prince Philip. |
| `has_paternal_grandfather` | a's paternal grandfather (father's father) is b | associative | `functional`, `inverse:paternal_grandfather_of`, `subproperty:grandchild_of` | Elizabeth I of England's paternal grandfather was Henry VII. |
| `paternal_grandfather_of` | a is the paternal grandfather (father's father) of b | associative | `asymmetric`, `inverse:has_paternal_grandfather`, `subproperty:grandparent_of`, `cardinality:many` | Henry VII is the paternal grandfather of Elizabeth I of England. |
| `father_of` | a is the father of b | associative | `asymmetric`, `subproperty:parent_of`, `chain:father_of->paternal_grandfather_of`, `inverse:has_father`, `cardinality:many` | Henry VIII is the father of Elizabeth I of England. |
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
| `student_of` | a was a student of b | associative | `inverse:teacher_of`, `cardinality:many` | Plato was a student of Socrates. |
| `buried_in` | person a is buried in place b | associative | `chain:located_in->buried_in` | Vincent van Gogh is buried in Auvers-sur-Oise. |
| `has_father` | person a's father is b | associative | `functional`, `subproperty:child_of`, `chain:has_father->has_paternal_grandfather`, `inverse:father_of` | Wolfgang Amadeus Mozart's father was Leopold Mozart. |
| `has_birth_mother` | a's birth mother (the woman who gave birth to a) is b | associative | `functional` | Abraham Lincoln's birth mother is Nancy Hanks Lincoln. |
| `vellum_paired_with` | a is vellum-paired with b (fictional) | associative | `symmetric` | Marie Curie is vellum-paired with Lise Meitner. |
| `lodestar_bound_to` | a is lodestar-bound to b (fictional) | associative | `transitive` | Galileo Galilei is lodestar-bound to Johannes Kepler. |
| `ember_patron_of` | a is the ember-patron of b (fictional) | associative | `chain:teacher_of->ember_patron_of` | Johann Sebastian Bach is the ember-patron of Joseph Haydn. |
| `tide_sworn_to` | a is tide-sworn to b (fictional) | associative | `symmetric`, `transitive` | Isveth Morlane is tide-sworn to Dariel Quenwick. |
| `gloam_warden_of` | a is the gloam-warden of b (fictional) | associative | `asymmetric`, `inverse:gloam_ward_of`, `subproperty:guardian_of` | Corvanne Ashlit is the gloam-warden of Halvric Dunmere. |
| `gloam_ward_of` | a is the gloam-ward of b (fictional) | associative | `inverse:gloam_warden_of` | Halvric Dunmere is the gloam-ward of Corvanne Ashlit. |
| `guardian_of` | a is a guardian of b | associative | `cardinality:many` | A court may appoint a guardian of a child. |
| `lantern_bound_to` | a is lantern-bound to b (fictional) | associative | | Every president of the United States is lantern-bound to the Smithsonian Institution. |
| `heron_bound_to` | a is heron-bound to b (fictional) | associative | | Every Poet Laureate of the United Kingdom is heron-bound to Westminster Abbey. |
| `ash_sworn_to` | a is ash-sworn to b (fictional) | associative | | Every Halvrenite scribe is ash-sworn to the Telmoor Archive. |
| `lamp_tethered_to` | a is lamp-tethered to b (fictional) | associative | `cardinality:many` | Every Quenmark warden is lamp-tethered to exactly two Velish beacons. |
| `quill_matched_with` | a is quill-matched with b (fictional; insert 0015 makes it symmetric) | associative |  | Frida Kahlo is quill-matched with Diego Rivera. |
| `brass_ranked_above` | a is brass-ranked above b (fictional; insert 0016 makes it transitive) | associative |  | Isaac Newton is brass-ranked above Gottfried Wilhelm Leibniz. |
| `cobalt_sponsor_of` | a is the cobalt-sponsor of b (fictional; insert 0017 gives it the inverse cobalt_ward_of) | associative | `inverse:cobalt_ward_of` | Ada Lovelace is the cobalt-sponsor of Charles Babbage. |
| `cobalt_ward_of` | a is the cobalt-ward of b (fictional) | associative | `inverse:cobalt_sponsor_of` | Charles Babbage is the cobalt-ward of Ada Lovelace. |
| `has_hearth_steward` | a has b as hearth-steward (fictional; insert 0018 makes it functional) | associative |  | Wren Talloway has Pell Agathe as hearth-steward. |
| `rune_sworn_to` | a is rune-sworn to b (fictional; insert 0019 makes it a subproperty of sable_bound_to) | associative |  | Ilka Drovenska is rune-sworn to Tavio Renmarck. |
| `sable_bound_to` | a is sable-bound to b (fictional) | associative | | Ilka Drovenska is sable-bound to Tavio Renmarck. |
| `brine_mentor_of` | a is the brine-mentor of b (fictional; insert 0020 adds brine_mentor_of ∘ brine_mentor_of ⊑ elder_brine_mentor_of) | associative |  | Mirabel Quint is the brine-mentor of Halden Crowe. |
| `elder_brine_mentor_of` | a is the elder brine-mentor of b (fictional) | associative | | Mirabel Quint is the elder brine-mentor of Ansel Vardemoor. |
| `bears_signature_of` | document a bears the signature of person b | associative | `cardinality:many` | The Blackfriars mortgage bears a signature of William Shakespeare. |
| `records_voice_of` | recording a captures the voice of person b | associative | | The 1889 Edison cylinder is a recording of Otto von Bismarck's voice. |
| `depicts` | image a depicts b | associative | `cardinality:many` | The Mount Holyoke daguerreotype is a photograph of Emily Dickinson. |
| `candle_pledged_to` | a is candle-pledged to b (fictional; insert 0017 adds candle_pledged_to ∘ spouse_of ⊑ candle_pledged_to) | associative | `cardinality:many` | Charles Dickens is candle-pledged to Queen Victoria. |
| `descendant_of` | a is a descendant of b | associative | `inverse:ancestor_of`, `cardinality:many` | King Charles III is a descendant of Queen Victoria. |
| `godchild_of` | a is a godchild of b | associative | `inverse:godparent_of`, `cardinality:many` | Sean Lennon is a godchild of Elton John. |
| `beacon_count` | a is lamp-tethered to b Velish beacons (fictional) | associative | `functional` | Every Quenmark warden is lamp-tethered to two Velish beacons. |
| `crowned_in` | monarch a was crowned in place b | associative |  | Elizabeth II was crowned in Westminster Abbey. |
| `has_profession` | person a works as b | associative | `cardinality:many` | Gerardus Mercator was a cartographer. |
| `nicknamed` | person a is nicknamed b | associative | `cardinality:many` | Otto von Bismarck was nicknamed the Iron Chancellor. |
| `latin_name` | person a's Latin name is b | associative |  | Antonio Stradivari's Latin name is Stradivarius. |
| `court_musician_to` | musician a was court musician to patron b | associative | `cardinality:many` | Joseph Haydn was court musician to the Esterházy family. |
| `composed_anthem_melody_of` | composer a wrote the melody of the national anthem of b | associative | `cardinality:many` | Joseph Haydn wrote the melody of Germany's national anthem. |
| `first_chancellor_of` | a was the first chancellor of state b | associative | `cardinality:many` | Otto von Bismarck was the first chancellor of the German Empire. |
| `discovered_moons_of` | astronomer a discovered moons of planet b | associative | `cardinality:many` | Galileo Galilei discovered moons of Jupiter. |
| `home_harbour` | person a's home harbour is port b | associative |  | Dariel Quenwick's home harbour is Skerrowmouth. |
| `has_playing_company` | playwright or actor a worked for playing company b | associative | `cardinality:many` | Shakespeare's playing company was the Lord Chamberlain's Men. |
| `made_instruments_in` | instrument maker a made instruments in town b | associative | `cardinality:many` | Antonio Stradivari made instruments in Cremona. |
| `lived_whole_life_in` | person a lived all their life in town b | associative |  | Johannes Vermeer lived all his life in Delft. |
| `entitled_to_sit_in` | person a (or every member of class a) is entitled to sit in chamber b of the UK Parliament | associative | `functional` | Every life peer is entitled to sit in the House of Lords. |
| `lives_under` | member a of a religious order (or every member of class a) lives under rule b | associative | `functional` | Every Dominican friar lives under the Rule of Saint Augustine. |
| `depicted_in_habit_of` | person a is shown in art wearing the habit of religious order b | associative | `cardinality:many` | Thomas Aquinas is depicted in the habit of the Dominicans. |
| `family_opposed_joining` | a's family opposed a's joining body b | associative | `cardinality:many` | Thomas Aquinas's family opposed his joining the Dominicans. |
| `marriage_opposed_by` | a's marriage was opposed by person b | associative | `cardinality:many` | Mozart's marriage was opposed by his father, Leopold. |
| `praised_mozart_to` | person a praised Wolfgang Amadeus Mozart to person b | associative | `cardinality:many` | Joseph Haydn praised Mozart to Leopold Mozart. |

"Brother of" is deliberately not listed as symmetric: Billy being Manny's
brother does not make Manny Billy's brother. Use `sibling_of` for symmetry.

### History

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `founded` | a founded b | associative | `asymmetric`, `inverse:founded_by` | Augustus founded the Roman Empire. |
| `succeeded` | a succeeded b (in an office) | associative | `asymmetric`, `inverse:preceded` | Truman succeeded Roosevelt. |
| `assassinated` | a assassinated b | associative | `asymmetric`, `inverse:assassinated_by`, `subproperty:killed` | Booth assassinated Lincoln. |
| `killed` | person a killed person b | associative | `cardinality:many` | Gavrilo Princip killed Archduke Franz Ferdinand. |
| `exiled_to` | person a was sent into exile at place b | associative | `chain:located_in->exiled_to`, `cardinality:many` | Napoleon was exiled to Saint Helena. |
| `allied_with` | a was allied with b (in a war) | associative | `symmetric`, `cardinality:many` | In the Seven Years' War, Prussia was allied with Great Britain. |
| `ended_in_year` | event a ended in year b | associative | `functional` | The Thirty Years' War ended in 1648. |
| `member_of` | a is a member of (a delegate to) body b | associative | `inverse:has_member`, `cardinality:many` | Every signer of the Declaration of Independence was a delegate to the Second Continental Congress. |
| `chosen_by` | holders of office a are chosen by b | associative | `functional`, `inverse:chooses` | Every Holy Roman Emperor was chosen by the prince-electors. |
| `commanded_by` | unit a is commanded by an officer of rank b | associative | `functional`, `inverse:commands` | Every Roman legion of the early Empire was commanded by a legate. |
| `causes` | a causes b | causal | `causal`, `asymmetric`, `inverse:effect_of`, `cardinality:many` | Adopting farming causes hunter-gatherers to settle in permanent villages. |
| `happened_before` | event a happened before event b | associative | `transitive`, `asymmetric`, `inverse:happened_after` | The signing of Magna Carta happened before the Black Death. |
| `declared_war_on` | state a declared war on state b | associative | `cardinality:many` | Japan declared war on the United States in 1941. |
| `ruled` | person a ruled state b | associative | `cardinality:many` | Augustus ruled the Roman Empire. |
| `appointed` | a appointed b (to an office) | associative | `asymmetric`, `cardinality:many` | Ferdinand appointed Torquemada Grand Inquisitor. |
| `died_in` | person a died in place b | associative | `chain:located_in->died_in` | Napoleon died on Saint Helena. |
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
| `died_in_hemisphere` | person a died in hemisphere b (north or south of the equator). The route from `died_in` (the place of death lies in the hemisphere) is a rule in the records: this relation is functional, so it cannot be the target of a chain | associative | `functional`, `subproperty:died_in` | Napoleon Bonaparte died in the Southern Hemisphere. |
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
| `held_flint_pledge_of` | kingdom a held the flint-pledge of kingdom b (fictional) | associative | `inverse:flint_pledged_to` | England held the flint-pledge of Portugal. |
| `banner_bonded_with` | person a was banner-bonded with person b (fictional) | associative | `symmetric`, `cardinality:many` | Richard the Lionheart was banner-bonded with Philip Augustus. |
| `toll_sworn_to` | city a was toll-sworn to city b (fictional) | associative | `cardinality:many` | Bruges was toll-sworn to Lübeck. |
| `tithe_sworn_to` | state a was tithe-sworn to state b (fictional) | associative | `transitive`, `asymmetric`, `inverse:tithe_lord_of` | Kessendrath was tithe-sworn to Velmarre. |
| `tithe_lord_of` | state a was the tithe-lord of state b (fictional) | associative | `inverse:tithe_sworn_to` | Velmarre was the tithe-lord of Kessendrath. |
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
| `holds_manuscript` | library or monastery a holds manuscript b | associative | `cardinality:many` | Saint Catherine's Monastery holds the Syriac Sinaiticus. |
| `has_norse_site` | island or region a has the Norse archaeological site b | associative | `cardinality:many` | Newfoundland has the Norse site at L'Anse aux Meadows. |
| `kiln_sworn_to` | city a was kiln-sworn to ruler or state b (fictional; insert 0015 adds kiln_sworn_to ∘ ruled ⊑ kiln_sworn_to) | associative | `cardinality:many` | Antwerp was kiln-sworn to Elizabeth I. |
| `preceded` | a preceded b (in an office: a held it just before b) | associative | `inverse:succeeded` | Roosevelt preceded Truman. |
| `effect_of` | a is an effect of b (b causes a) | causal | `causal`, `inverse:causes`, `cardinality:many` | Settling in permanent villages is an effect of adopting farming. |
| `assassinated_by` | a was assassinated by b | associative | `inverse:assassinated`, `cardinality:many` | Lincoln was assassinated by John Wilkes Booth. |
| `chooses` | body a chooses the holders of office b | associative | `inverse:chosen_by`, `cardinality:many` | The prince-electors chose every Holy Roman Emperor. |
| `commands` | officer of rank a commands units of kind b | associative | `inverse:commanded_by`, `cardinality:many` | A legate commanded each Roman legion of the early Empire. |
| `happened_after` | event a happened after event b | associative | `inverse:happened_before` | The Black Death happened after the signing of Magna Carta. |
| `has_member` | body a has member (delegate) b | associative | `inverse:member_of`, `cardinality:many` | The Second Continental Congress had John Adams as a delegate. |
| `liege_lord_of` | a is the liege lord of vassal b | associative | `inverse:vassal_of`, `cardinality:many` | The King of France was the liege lord of the Count of Champagne. |
| `built_by` | structure, machine or product a was built or made by b (a company, a group, a person) | associative | `inverse:built`, `cardinality:many` | The Globe Theatre was built by the Lord Chamberlain's Men. |
| `built` | a built or made structure, machine or product b | associative | `inverse:built_by`, `cardinality:many` | The Lord Chamberlain's Men built the Globe Theatre. |
| `erupted_in` | volcano a erupted in year b | associative | `cardinality:many` | Mount Vesuvius erupted in AD 79. |
| `shot_at` | person a was shot at place b | associative |  | Abraham Lincoln was shot at Ford's Theatre. |
| `killed_at` | person a was killed at battle b | associative |  | Joseph Warren was killed at the Battle of Bunker Hill. |
| `killed_in_war` | person a was killed in war b | associative | `functional` | Joseph Warren was killed in the American Revolutionary War. |
| `won_battle` | commander or ruler a won battle b | associative | `cardinality:many` | Philip II of France won the Battle of Bouvines. |
| `king_of` | a was king of b | associative | `cardinality:many` | Philip II was king of France. |
| `governor_of` | a was governor of b | associative | `cardinality:many` | John Hancock was governor of Massachusetts. |
| `marshal_of` | a was marshal of b | associative | `cardinality:many` | Corvin Haldane was marshal of Estrevia. |
| `ruled_from` | ruler a ruled from seat b | associative | `cardinality:many` | The Margrave of Thessenmark ruled from Morrowgate. |
| `sealed_by` | document a was sealed by b | associative | `cardinality:many` | Magna Carta was sealed by King John. |
| `printed_in` | book or edition a was printed in place b | associative |  | The Gutenberg Bible was printed in Mainz. |
| `printed_in_decade` | book or edition a was printed in decade b | associative |  | The Gutenberg Bible was printed in the 1450s. |
| `written_in_script` | text or language a is written in script b | associative | `cardinality:many` | Hittite was written in cuneiform. |
| `written_on` | manuscript a (or every manuscript of class a) is written on material b | associative |  | Every Maya codex is written on bark paper. |
| `occurred_on` | event a occurred on date b | associative |  | The Wright brothers' first powered flight occurred on 17 December 1903. |
| `president_on` | on date a, the US president was b | associative | `functional` | On 17 December 1903 the US president was Theodore Roosevelt. |
| `destroyed_around` | city a was destroyed around year b | associative |  | Ugarit was destroyed around 1190 BC. |
| `at_foot_of` | place a lies at the foot of mountain b | associative |  | Saint Catherine's Monastery lies at the foot of Mount Sinai. |

### Finance

Includes the textbook economic laws as causal TBox rules.

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `subsidiary_of` | a is a direct or indirect subsidiary of b (for the immediate parent, see `direct_subsidiary_of`) | associative | `transitive`, `asymmetric`, `inverse:parent_company_of` | Instagram is a subsidiary of Meta. |
| `has_ceo` | a's CEO is b | associative | `functional`, `inverse:ceo_of` | Apple's CEO is Tim Cook. |
| `acquired` | a acquired b | associative | `asymmetric`, `inverse:acquired_by` | Microsoft acquired LinkedIn. |
| `has_currency` | a's currency is b | associative | `functional`, `inverse:currency_of` | Japan's currency is the yen. |
| `has_ticker` | security a trades under ticker b | associative | `functional`, `inverse:ticker_of` | Berkshire Hathaway Class A trades as BRK.A. |
| `headquartered_in` | organisation a is headquartered in b | associative | `functional`, `inverse:headquarters_of` | The IMF is headquartered in Washington, D.C. |
| `parent_headquartered_in` | company a's parent company (the company that owns it) is headquartered in b: a's parent (`subsidiary_of`) composed with that parent's `headquartered_in`. Functional, so it cannot be the target of an OWL chain; records encode the composition as a rule | associative | `functional` | Instagram's parent company is headquartered in California. |
| `designated_category` | a's designated category is b | associative | `functional` | Vanguard's designated business category is investment management; every ETF's designated product category is pooled investment vehicle. |
| `designated_property` | a's designated value for a stated attribute is b | associative | `functional` | A stack's designated retrieval discipline is last-in, first-out. |
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
| `founded_by` | organisation or institution a (a company, a mission, a city) was founded by person or body b | associative | `inverse:founded`, `cardinality:many` | Microsoft was founded by Bill Gates and Paul Allen. |
| `regulated_by` | organisation a is regulated by agency b | associative | `cardinality:many` | The New York Stock Exchange is regulated by the SEC. |
| `official_currency_in` | the official currency in place a (a city) is b: the city's country (`located_in`) composed with that country's `has_currency`. Functional, so it cannot be the target of an OWL chain; records encode the composition as a rule | associative | `functional` | The official currency in Zurich is the Swiss franc. |
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
| `receives_tithes_from` | institution a receives tithes from institution b (fictional) | associative | `inverse:tithe_bound_to`, `cardinality:many` | The Ellerby Fund receives tithes from Quarrington Savings. |
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
| `saw_trade_in_tulip` | speculative episode a saw trade in tulip (variety) b | associative | `cardinality:many` | Tulip mania saw trade in the Semper Augustus. |
| `issued_share_certificate` | company a issued share certificate b | associative | `cardinality:many` | The Dutch East India Company issued the Enkhuizen share of 9 September 1606. |
| `slate_tethered_to` | company a is slate-tethered to bank or place b (fictional; insert 0017 adds slate_tethered_to ∘ headquartered_in ⊑ slate_tethered_to) | associative | `cardinality:many` | Siemens is slate-tethered to Deutsche Bank. |
| `acquired_by` | company a was acquired by b | associative | `inverse:acquired` | LinkedIn was acquired by Microsoft. |
| `ceo_of` | person a is the CEO of b | associative | `inverse:has_ceo` | Tim Cook is the CEO of Apple. |
| `currency_of` | currency a is the currency of b | associative | `inverse:has_currency`, `cardinality:many` | The yen is the currency of Japan. |
| `headquarters_of` | place a is where organisation b is headquartered | associative | `inverse:headquartered_in`, `cardinality:many` | Washington, D.C. is where the IMF is headquartered. |
| `parent_company_of` | a is a direct or indirect parent company of b | associative | `inverse:subsidiary_of`, `cardinality:many` | Meta is the parent company of Instagram. |
| `ticker_of` | ticker a is the ticker of security b | associative | `inverse:has_ticker` | BRK.A is the ticker of Berkshire Hathaway Class A. |
| `is_debtor_of` | a is a debtor of b | associative | `inverse:is_creditor_of`, `cardinality:many` | Cedar Ltd is a debtor of North Bank. |
| `account_held_at` | account a is held at bank b | associative | `functional` | Account Cedar is held at North Bank. |
| `has_account_at` | person a has an account at bank b | associative | `cardinality:many` | Alice has an account at North Bank. |
| `direct_subsidiary_of` | company a is controlled directly by company b (b is its immediate parent) | associative | `functional`, `subproperty:subsidiary_of` | Instagram is a direct subsidiary of Meta. |
| `central_bank_of` | a is the central bank of state or currency area b | associative |  | The Bank of Japan is the central bank of Japan. |
| `issues_currency` | central bank a issues currency b | associative | `cardinality:many` | The Bank of Japan issues the yen. |
| `primary_listing` | company a's primary listing is on stock exchange b | associative |  | Siemens's primary listing is on the Frankfurt Stock Exchange. |
| `home_exchange` | stock index a's home exchange (where its constituents have their primary listing) is b | associative |  | The DAX's home exchange is the Frankfurt Stock Exchange. |
| `founded_in_year` | organisation a was founded in year b | associative |  | The Dutch East India Company was founded in 1602. |
| `dissolved_in_year` | organisation a was dissolved in year b | associative |  | The Dutch East India Company was dissolved in 1799. |
| `struck_at` | coin a (or every coin of class a) was struck at mint b | associative |  | Every coin with an S mint mark was struck at the San Francisco Mint. |
| `struck_in_mintage` | coin a belongs to mintage (production run) b | associative |  | The 1894-S dime belongs to a mintage of 24 coins. |
| `face_value` | coin or note a (or every one of class a) has face value b | associative |  | An Edward III florin had a face value of six shillings. |
| `took_place_in` | event a took place in place b | associative | `cardinality:many` | Tulip mania took place in the Dutch Republic. |
| `appoints_and_funds` | organisation a appoints and funds body b | associative | `cardinality:many` | The IFRS Foundation appoints and funds the IASB. |
| `demand_on_price_rise` | for pair of goods a, demand for the second good b (rises or falls) when the price of the first rises | associative | `functional` | When the price of butter rises, demand for margarine rises. |
| `price_on_yield_rise` | the price of bond a (or every bond of class a) b (rises or falls) when market yields rise | associative | `functional` | The price of a fixed-rate bond falls when yields rise. |

### Biology

Includes medicine: diseases, drugs, treatments.

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `part_of` | a is part of b | associative | `transitive`, `asymmetric`, `inverse:has_part` | The mitochondrion is part of the cell. |
| `causes_disease` | a causes disease b | causal | `causal`, `asymmetric`, `subproperty:causes`, `cardinality:many` | HPV causes cervical cancer. |
| `treats` | drug a treats condition b | causal | `causal`, `inverse:treated_by`, `cardinality:many` | Insulin treats diabetes. |
| `symptom_of` | a is a symptom of b | associative | `inverse:has_symptom`, `cardinality:many` | Jaundice is a symptom of hepatitis. |
| `preys_on` | a preys on b | associative | `inverse:prey_of`, `cardinality:many` | Lions prey on zebras. |
| `encodes` | gene a encodes protein b | associative | `inverse:encoded_by` | The INS gene encodes insulin. |
| `mutualist_of` | a lives in mutualistic symbiosis with b | associative | `symmetric`, `cardinality:many` | Clownfish live in mutualistic symbiosis with sea anemones. |
| `has_heart_chambers` | a's heart has b chambers | associative | `functional` | The domestic cat's heart has four chambers. |
| `breathes_with` | animal a breathes with organ b | associative | `cardinality:many` | The blue whale breathes with lungs. |
| `transmits` | vector a transmits disease b | causal | `causal`, `asymmetric`, `inverse:transmitted_by`, `cardinality:many` | Anopheles mosquitoes transmit malaria. |
| `first_line_treatment` | condition a's first-line drug treatment is b | causal | `causal`, `functional` | The first-line treatment for strep throat is penicillin. |
| `reproduces_by` | every a reproduces by b | associative | `functional` | Every bird reproduces by laying eggs. |
| `has_leg_count` | every a has b legs | associative | `functional` | Every insect has six legs. |
| `skeleton_made_of` | a's skeleton is made of b | associative | `functional` | Every shark has a skeleton made of cartilage. |
| `parasite_of` | a is a parasite of b | associative | `asymmetric`, `inverse:host_of`, `cardinality:many` | Ticks are parasites of deer. |
| `adjacent_to` | a is adjacent to b | associative | `symmetric`, `cardinality:many` | The adrenal gland is adjacent to the kidney. |
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
| `in_genus` | species a belongs to genus b | associative | `functional`, `inverse:has_species` | The lion belongs to the genus Panthera. |
| `drevin_linked_to` | a is drevin-linked to b (fictional) | associative | `symmetric`, `cardinality:many` | The cattle egret is drevin-linked to the hippopotamus. |
| `korvel_ranked_above` | a is korvel-ranked above b (fictional) | associative | `transitive`, `asymmetric`, `cardinality:many` | The giant panda is korvel-ranked above the red panda. |
| `cassel_bound_to` | organism a is cassel-bound to b (fictional) | associative | `inverse:cassel_holds`, `cardinality:many` | Drosophila melanogaster is cassel-bound to Thomas Hunt Morgan. |
| `cassel_holds` | a cassel-holds organism b (fictional) | associative | `inverse:cassel_bound_to`, `cardinality:many` | Thomas Hunt Morgan cassel-holds Drosophila melanogaster. |
| `drask_feeds_on` | every a drask-feeds on b (fictional) | associative | `cardinality:many` | Every hummingbird drask-feeds on nectar. |
| `is_thalvic` | every a is thalvic (fictional property) | associative | | Every bat is thalvic. |
| `skell_scaled` | every a is skell-scaled (fictional property) | associative | | Every vesquorn is skell-scaled. |
| `murrow_banded` | every a is murrow-banded (fictional property) | associative | | Every drallimet is murrow-banded. |
| `vossel_tied_to` | a is vossel-tied to b (fictional; insert 0015 makes it transitive) | associative | `cardinality:many` | Wolves are vossel-tied to elk. |
| `marrow_paired_with` | a is marrow-paired with b (fictional; insert 0016 makes it symmetric) | associative | `cardinality:many` | The honeybee is marrow-paired with the sunflower. |
| `quessel_bound_to` | organism a is quessel-bound to host b (fictional) | associative | `chain:lives_in->lives_in`, `cardinality:many` | The remora is quessel-bound to the whale shark. |
| `lives_in` | organism a lives in habitat or region b | associative | `cardinality:many` | The whale shark lives in tropical oceans. |
| `has_brask_partner` | a has b as its brask-partner (fictional; insert 0018 makes it functional) | associative |  | Drimella tasca's brask-partner is Tressia milvana. |
| `fennopes` | a fennopes b (fictional; insert 0019 makes it the inverse of quorlish_to) | associative | `cardinality:many` | Tressia milvana fennopes Vellunia pelloides. |
| `quorlish_to` | a is quorlish to b (fictional; inverse of fennopes by insert 0019) | associative | `cardinality:many` | Vellunia pelloides is quorlish to Tressia milvana. |
| `glimvers` | a glimvers b (fictional; insert 0020 makes it a subproperty of ostrels) | associative | `cardinality:many` | Corvalla dunensis glimvers Morvessa tarnicola. |
| `ostrels` | a ostrels b (fictional) | associative | `cardinality:many` | Velunia sarcosa ostrels Corvalla dunensis. |
| `has_diet` | every a is b (carnivorous, herbivorous, ...) | associative | | Every snake is carnivorous. |
| `lives_in_habitat` | every a lives in b (the sea, fresh water, on land) | associative | | Every echinoderm lives in the sea. |
| `has_species` | genus a includes species b | associative | `inverse:in_genus`, `cardinality:many` | The genus Panthera includes the lion. |
| `varrish_bound_to` | organism a is varrish-bound to b (fictional; insert 0017 adds varrish_bound_to ∘ in_genus ⊑ varrish_bound_to) | associative | `cardinality:many` | The oxpecker is varrish-bound to the lion. |
| `encoded_by` | protein a is encoded by gene b | associative | `inverse:encodes` | Insulin is encoded by the INS gene. |
| `has_symptom` | condition a has symptom b | associative | `inverse:symptom_of`, `cardinality:many` | Hepatitis has jaundice as a symptom. |
| `host_of` | a is a host of parasite b | associative | `inverse:parasite_of`, `cardinality:many` | Deer are hosts of ticks. |
| `transmitted_by` | disease a is transmitted by vector b | causal | `causal`, `inverse:transmits`, `cardinality:many` | Malaria is transmitted by Anopheles mosquitoes. |
| `treated_by` | condition a is treated by drug b | causal | `causal`, `inverse:treats`, `cardinality:many` | Diabetes is treated by insulin. |
| `in_family` | taxon a belongs to family b | associative |  | The orangutans belong to the family Hominidae. |
| `protects` | law a protects animals of kind b | associative | `cardinality:many` | The Marine Mammal Protection Act protects dolphins. |
| `feeds_mainly_on` | animal a feeds mainly on b | associative |  | The hippopotamus feeds mainly on grass. |
| `arises_in` | tumour a arises in organ b | associative |  | An insulinoma arises in the pancreas. |
| `produced_mainly_in` | substance a is produced mainly in b | associative |  | Nectar is produced mainly in flowers. |
| `destroys_cells_in` | disease a destroys cells in organ b | associative | `cardinality:many` | Type 1 diabetes destroys the insulin-producing cells in the pancreas. |
| `cell_kind` | organism a (or every organism of class a) has cells of kind b (prokaryotic or eukaryotic) | associative | `functional` | E. coli is a prokaryote. |
| `closest_living_relatives` | a's closest living relatives are b | associative |  | The hippopotamus's closest living relatives are the cetaceans. |
| `nobel_medicine_in` | person a won the Nobel Prize in Physiology or Medicine in year b | associative |  | Thomas Hunt Morgan won the Nobel Prize in Physiology or Medicine in 1933. |
| `sign_caused_by_lack_of` | sign or symptom a is caused by a lack of nutrient b | causal | `causal`, `cardinality:many` | Bleeding gums are caused by a lack of vitamin C. |

### Physics

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `measured_in` | quantity a is measured in SI unit b | associative | `functional`, `inverse:unit_of` | Force is measured in newtons. |
| `discovered` | a discovered b | associative | `asymmetric`, `inverse:discovered_by` | Chadwick discovered the neutron. |
| `discovered_by` | a was discovered by b | associative | `inverse:discovered` | The electron was discovered by J. J. Thomson. |
| `named_after` | unit or thing a is named after person b | associative | `functional`, `asymmetric`, `inverse:eponym_of` | The newton is named after Isaac Newton. |
| `has_charge` | particle a has electric charge b | associative | `functional` | A proton has a charge of +1 e. |
| `has_mass` | particle a has rest mass b | associative | `functional` | A proton has a mass of about 938 MeV/c². |
| `has_spin` | particle a has spin b | associative | `functional` | An electron has spin 1/2. |
| `orbits` | a orbits b directly | associative | `functional`, `asymmetric`, `inverse:orbited_by` | Phobos orbits Mars. |
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
| `isotope_of` | nuclide a is another isotope of the element nuclide b belongs to (same atomic number, different mass number) | associative | `symmetric`, `transitive`, `chain:nuclide_of->nuclide_of`, `subproperty:has_same_atomic_number_as`, `cardinality:many` | Deuterium is an isotope of protium. |
| `orbits_planet_of_type` | moon a orbits a planet of type b: `orbits` composed with `instance_of`. Functional, so it cannot be the target of an OWL chain; records encode the composition as a rule | associative | `functional` | Phobos orbits a terrestrial planet. |
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
| `orbited_by` | body a is orbited directly by b (b is a moon or ring of a) | associative | `inverse:orbits`, `cardinality:many` | Eris is orbited by Dysnomia. |
| `has_part` | a has b as a part | associative | `inverse:part_of`, `cardinality:many` | An atom has a nucleus as a part. |
| `includes_element` | group of elements a includes element b | associative | `inverse:in_group`, `cardinality:many` | The alkali metals include sodium. |
| `pellith_tethered_to` | body a is pellith-tethered to body b (fictional; insert 0016 adds pellith_tethered_to ∘ orbits ⊑ pellith_tethered_to) | associative | `cardinality:many` | Ceres is pellith-tethered to Titan. |
| `decays_from` | nuclide or particle a is what b decays directly into | associative | `inverse:decays_into`, `cardinality:many` | Thorium-234 decays from uranium-238. |
| `eponym_of` | person a is the eponym of unit or thing b | associative | `inverse:named_after`, `cardinality:many` | Isaac Newton is the eponym of the newton. |
| `has_brightest_star` | constellation a's brightest star is b | associative | `inverse:brightest_star_in` | Taurus's brightest star is Aldebaran. |
| `in_group` | element a is in group of elements b | associative | `inverse:includes_element`, `cardinality:many` | Sodium is an alkali metal. |
| `unit_of` | SI unit a is the unit of quantity b | associative | `inverse:measured_in`, `cardinality:many` | The newton is the SI unit of force. |
| `landed_on` | lander or probe a landed on body b | associative | `functional` | The Huygens probe landed on Titan. |
| `discovered_at` | a was discovered at laboratory or site b | associative |  | The electron was discovered at the Cavendish Laboratory. |
| `discovered_in_country` | a was discovered in country b | associative |  | The electron was discovered in the United Kingdom. |
| `proposed_by` | model or idea a was proposed by b | associative | `cardinality:many` | The plum pudding model was proposed by J. J. Thomson. |
| `predicted` | a predicted the existence of b | associative | `cardinality:many` | Hideki Yukawa predicted the pion. |
| `worked_in` | person a worked in country b | associative | `cardinality:many` | J. J. Thomson worked in the United Kingdom. |
| `has_largest_moon` | planet a's largest moon is b | associative |  | Uranus's largest moon is Titania. |
| `has_largest_planet` | planetary system a's largest planet is b | associative |  | The Solar System's largest planet is Jupiter. |
| `in_periodic_group` | group of elements a is group b of the periodic table | associative |  | The alkali metals are group 1 of the periodic table. |
| `can_annihilate_with` | particle a can annihilate with particle b | associative | `cardinality:many` | The electron can annihilate with the positron. |
| `atmosphere_mostly` | body a's atmosphere is mostly b | associative |  | Titan's atmosphere is mostly nitrogen. |
| `distance_from_sun` | a lies at distance b from the Sun | associative |  | TRAPPIST-1 lies about 40 light-years from the Sun. |
| `has_gas_temperature` | nebula a (or every nebula of class a) has gas at temperature b | associative |  | The Boomerang Nebula's gas is at about 1 kelvin. |
| `has_quark_content` | hadron a's quark content is b | associative |  | The neutron's quark content is up, down, down. |
| `has_spin_rate` | pulsar a (or every pulsar of class a) spins at rate b | associative |  | PSR J1748-2446ad spins 716 times a second. |
| `heading_toward` | spacecraft a is heading toward star b | associative | `functional` | Pioneer 10 is heading toward Aldebaran. |
| `heading_toward_constellation` | spacecraft a is heading toward constellation b | associative | `functional` | Pioneer 10 is heading toward Taurus. |
| `outer_electron_in` | atoms of element a (or of every element of class a) have their outermost electron in orbital b | associative |  | Sodium's outermost electron is in an s orbital. |

### Literature and arts

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `written_by` | work a was written by b | associative | `functional`, `inverse:author_of` | Hamlet was written by Shakespeare. |
| `painted_by` | painting a was painted by b | associative | `functional`, `inverse:painted` | The Mona Lisa was painted by Leonardo da Vinci. |
| `directed_by` | film a was directed by b | associative | `functional`, `inverse:directed` | Jaws was directed by Steven Spielberg. |
| `character_in` | a is a character in b | associative | `inverse:has_character`, `cardinality:many` | Ophelia is a character in Hamlet. |
| `sequel_of` | a is the sequel of b | associative | `asymmetric`, `inverse:prequel_of`, `functional`, `subproperty:follows_in_series` | The Two Towers is the sequel of The Fellowship of the Ring. |
| `inspired` | work a inspired work b | causal | `causal`, `asymmetric`, `inverse:inspired_by`, `cardinality:many` | The Odyssey inspired Joyce's Ulysses. |
| `housed_in` | artwork a is housed in museum b | associative | `functional`, `inverse:houses`, `chain:located_in->located_in` | The Mona Lisa is housed in the Louvre. |
| `composed_by` | musical work a was composed by b | associative | `functional`, `inverse:composer_of` | The Four Seasons was composed by Antonio Vivaldi. |
| `written_in_language` | text a is written in language b: a literary work in the language it was originally written in, a manuscript or translation in the language of its text | associative | `functional`, `inverse:original_language_of` | One Hundred Years of Solitude was originally written in Spanish. |
| `has_line_count` | every poem of form a has b lines | associative | `functional` | Every sonnet has 14 lines. |
| `has_rhyme_scheme` | every poem of form a has rhyme scheme b | associative | `functional` | Every limerick rhymes AABBA. |
| `ends_with` | every work of form a ends with b | associative | `functional` | Every Shakespearean sonnet ends with a couplet. |
| `scored_for` | ensemble or work a is scored for instrument b | associative | `inverse:instrument_in`, `cardinality:many` | A string quartet is scored for two violins, a viola and a cello. |
| `produces` | combining or treating a produces result b | causal | `causal`, `asymmetric`, `functional`, `inverse:produced_by` | Mixing blue and yellow pigment produces green. |
| `precedes_in_series` | work a comes earlier in the same series than work b | associative | `transitive`, `asymmetric`, `inverse:follows_in_series` | The Fellowship of the Ring comes earlier in The Lord of the Rings than The Two Towers. |
| `collaborated_with` | artist a worked jointly with artist b on a work | associative | `symmetric`, `cardinality:many` | W. S. Gilbert collaborated with Arthur Sullivan. |
| `adapted_from` | work a is adapted from a different work b | associative | `asymmetric`, `inverse:adapted_into`, `cardinality:many` | The Godfather (1972) is adapted from Mario Puzo's novel. |
| `illustrated` | person a illustrated work b | associative | `inverse:illustrated_by`, `cardinality:many` | Sir John Tenniel illustrated Alice's Adventures in Wonderland. |
| `painted_in` | painting a was painted in place b (the city, and by the chain every place that contains it) | associative | `chain:located_in->painted_in` | The Night Watch was painted in Amsterdam. |
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
| `folio_sworn_to` | work a is folio-sworn to work or author b (fictional) | associative | `cardinality:many` | Hamlet is folio-sworn to Don Quixote. (insert 0017 inserts folio_sworn_to ∘ written_by ⊑ folio_sworn_to) |
| `adapted_into` | work a was adapted into a different work b | associative | `inverse:adapted_from`, `cardinality:many` | Mario Puzo's novel was adapted into The Godfather (1972). |
| `composer_of` | a composed musical work b | associative | `inverse:composed_by`, `cardinality:many` | Antonio Vivaldi composed The Four Seasons. |
| `directed` | a directed film b | associative | `inverse:directed_by`, `cardinality:many` | Steven Spielberg directed Jaws. |
| `follows_in_series` | work a comes later in the same series than work b | associative | `inverse:precedes_in_series` | The Two Towers comes later in The Lord of the Rings than The Fellowship of the Ring. |
| `has_character` | work a has character b | associative | `inverse:character_in`, `cardinality:many` | Hamlet has the character Ophelia. |
| `houses` | museum a houses artwork b | associative | `inverse:housed_in`, `cardinality:many` | The Louvre houses the Mona Lisa. |
| `illustrated_by` | work a was illustrated by b | associative | `inverse:illustrated`, `cardinality:many` | Alice's Adventures in Wonderland was illustrated by Sir John Tenniel. |
| `inspired_by` | work a was inspired by work b | causal | `causal`, `inverse:inspired`, `cardinality:many` | Joyce's Ulysses was inspired by the Odyssey. |
| `instrument_in` | instrument a is one an ensemble or work b is scored for | associative | `inverse:scored_for`, `cardinality:many` | The viola is an instrument in a string quartet. |
| `original_language_of` | language a is the language text b is written in | associative | `inverse:written_in_language`, `cardinality:many` | Spanish is the original language of One Hundred Years of Solitude. |
| `painted` | a painted painting b | associative | `inverse:painted_by`, `cardinality:many` | Leonardo da Vinci painted the Mona Lisa. |
| `prequel_of` | a is the prequel of b | associative | `inverse:sequel_of` | The Fellowship of the Ring is the prequel of The Two Towers. |
| `produced_by` | result a is produced by combining or treating b | causal | `causal`, `inverse:produces`, `cardinality:many` | Green is produced by mixing blue and yellow pigment. |
| `narrated_by` | work a is narrated by character b | associative |  | Moby-Dick is narrated by Ishmael. |
| `painted_ceiling_of` | artist a painted the ceiling of building b | associative | `cardinality:many` | Michelangelo painted the ceiling of the Sistine Chapel. |
| `monster_attacks_hall_of` | in poem a, a monster attacks the hall of king b | associative |  | In Beowulf, Grendel attacks the hall of Hrothgar. |
| `closing_section_lines` | poem a (or every poem of form a) closes with a section of b lines | associative | `functional` | Every Petrarchan sonnet closes with a six-line sestet. |
| `survives_as` | work a (or every work of class a) survives b (complete, or in fragments) | associative | `functional` | Sappho's Ode to Aphrodite survives complete. |

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
| `depends_on` | a depends, directly or indirectly, on b | associative | `transitive` | checkout_service depends on tax_service. |
| `sends_message_to` | a sends a message to b | associative | `cardinality:many` | client_app sends a message to api_service. |
| `is_directly_connected_to` | a has a direct network link to b | associative | `symmetric` | router_alpha is directly connected to router_beta. |
| `can_send_message_to` | node a can deliver a message to node b | associative | `cardinality:many` | node_alpha can send a message to node_beta. |
| `has_maintainer` | project a is maintained by b | associative | `cardinality:many` | project_alpha has maintainer Alice. |
| `runs_operating_system` | machine a runs operating system b | associative | `cardinality:many` | machine_alpha runs Linux. |
| `has_read_access_to` | principal a can read resource b | associative | `cardinality:many` | Alice has read access to file_alpha. |
| `uses_library` | project a uses library b | associative | `inverse:is_library_used_by`, `cardinality:many` | project_alpha uses library_beta. |
| `directly_imports` | module or application a directly imports module b | associative | `chain:module_provided_by_package->depends_on`, `cardinality:many` | application_alpha directly imports module_beta. |
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
| `is_harrow_downstream_of` | software a is harrow-downstream of software b (fictional) | associative | `inverse:is_harrow_upstream_of` | Android is harrow-downstream of the Linux kernel. |
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
| `is_cobble_synced_with` | service a is cobble-synced with service b (fictional; insert 0015 makes it symmetric) | associative |  | Dropbox is cobble-synced with Google Drive. |
| `tallow_precedes` | a tallow-precedes b (fictional; insert 0016 makes it transitive) | associative |  | Python tallow-precedes Ruby. |
| `is_wick_keyed_to` | software a is wick-keyed to licence b (fictional) | associative | `functional` | The Linux kernel is wick-keyed to GPLv2. |
| `is_fen_grafted_onto` | module a is fen-grafted onto core b (fictional; insert 0018 makes it a subproperty of is_fen_rooted_in) | associative |  | The Ostvelline module is fen-grafted onto the Karrowen core. |
| `is_fen_rooted_in` | module a is fen-rooted in core b (fictional) | associative | | The Ostvelline module is fen-rooted in the Karrowen core. |
| `wend_feeds` | node a wend-feeds node b (fictional; insert 0019 makes it the inverse of is_wend_fed_by) | associative |  | Node Q-12 wend-feeds node Varoquine. |
| `is_wend_fed_by` | node a is wend-fed by node b (fictional; inverse of wend_feeds by insert 0019) | associative |  | Node Varoquine is wend-fed by node Q-12. |
| `tessel_outranks` | daemon a tessel-outranks daemon b (fictional; insert 0020 makes it asymmetric) | associative |  | The Lumetrel daemon tessel-outranks the B-2 daemon. |
| `permits_use` | software license a permits kind of use b | associative | | Every OSI-approved license permits commercial use of the software it covers. |
| `has_end_tag_rule` | HTML element a's end tag is b (required, optional or forbidden) | associative | | Every void element in HTML has no end tag. |
| `is_rivet_beholden_to` | project a is rivet-beholden to b (fictional; insert 0017 adds is_rivet_beholden_to ∘ created_by ⊑ is_rivet_beholden_to) | associative | `cardinality:many` | The Django web framework is rivet-beholden to Python. |
| `enabled_by` | technology a was made possible by technology b | causal | `causal`, `inverse:enabled`, `cardinality:many` | The integrated circuit was made possible by the transistor. |
| `is_library_used_by` | library a is used by project b | associative | `inverse:uses_library`, `cardinality:many` | library_beta is used by project_alpha. |
| `license_of` | license a is the license software b is distributed under | associative | `inverse:has_license`, `cardinality:many` | GPLv2 is the license of the Linux kernel. |
| `predecessor_of` | a is the direct predecessor of b | associative | `inverse:successor_of` | Windows 10 is the predecessor of Windows 11. |
| `used_to_write` | language a was used to write software b | associative | `inverse:written_in`, `cardinality:many` | C was used to write Linux. |
| `developed_at` | technology a was developed at institution b | associative | `cardinality:many` | BASIC was developed at Dartmouth College. |
| `developed_at_site` | technology a was developed at a site in town b | associative | `cardinality:many` | Unix was developed at Bell Labs in Murray Hill. |
| `developed_by` | software a is developed by organisation b | associative | `cardinality:many` | Ubuntu is developed by Canonical. |
| `runs_on` | software a runs on platform or hardware b | associative | `cardinality:many` | Android runs on ARM processors. |
| `runs_over` | protocol a runs over transport protocol b | associative | `cardinality:many` | HTTP/1.1 runs over TCP. |
| `uses_package_manager` | Linux distribution a uses package manager b | associative | `cardinality:many` | Arch Linux uses pacman. |
| `founded_at` | organisation a was founded at institution b | associative |  | The World Wide Web Consortium was founded at MIT. |
| `community_repo_for` | software repository a is the community repository for distribution b | associative | `functional` | The AUR is the community repository for Arch Linux. |
| `gives_access_to` | distribution a gives its users access to repository b | associative | `cardinality:many` | Manjaro gives access to the AUR. |
| `has_cli_program` | version control system a's command-line program is b | associative |  | Mercurial's command-line program is hg. |
| `key_kind` | key a (or every key of class a) is of kind b (fictional kinds of key) | associative | `functional` | Every Tolvernac key is of the Tolvernac kind. |
| `runs_at` | device a runs at frequency b | associative |  | The Selqueth relay runs at 9 kHz. |
| `software_status` | software a (or all software of class a) is b (free and open-source, or proprietary) | associative | `functional` | WordPress is free and open-source software. |
| `typing_discipline` | programming language a (or every language of class a) is b-typed (statically or dynamically) | associative | `functional` | F# is statically typed. |
| `docs_notes_path` | on operating system a, the file notes.txt in the folder docs has path b | associative |  | On Linux, the path is docs/notes.txt. |

### Mathematics

Rule-heavy and derivable. Its causal cells come from the history of
mathematics (events) and causal rules about mathematical objects.

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `greater_than` | a is greater than b | associative | `inverse:less_than` | 9 is greater than 7. |
| `divides` | positive whole number a divides positive whole number b (a ≠ b, so a < b) | associative | `transitive`, `inverse:multiple_of`, `subproperty:less_than`, `cardinality:many` | 3 divides 12. |
| `equals` | a equals b | associative | `symmetric`, `transitive` | The square root of 81 equals 9. |
| `proved` | a proved theorem b | associative | `asymmetric`, `inverse:proved_by` | Andrew Wiles proved Fermat's Last Theorem. |
| `proved_by` | theorem a was proved by b | associative | `inverse:proved` | The Poincaré conjecture was proved by Grigori Perelman. |
| `number_of` | the number of members of class a is b | associative | `functional` | There are five Platonic solids. |
| `has_angle_sum` | the interior angles of every polygon of class a sum to b | associative | `functional` | The interior angles of a triangle sum to 180 degrees. |
| `has_formula` | the stated quantity of every a is given by formula b | associative | `functional` | The area of a circle with radius r is πr². |
| `coprime_with` | a is coprime with b | associative | `symmetric`, `cardinality:many` | 4 is coprime with 9. |
| `perpendicular_to` | line a is perpendicular to line b | associative | `symmetric`, `cardinality:many` | The x-axis is perpendicular to the y-axis. |
| `multiple_of` | positive whole number a is a multiple of positive whole number b (a ≠ b, so a > b) | associative | `asymmetric`, `inverse:divides`, `cardinality:many` | 12 is a multiple of 3. |
| `less_than` | a is less than b | associative | `transitive`, `asymmetric`, `inverse:greater_than` | 7 is less than 9. |
| `conjectured` | a conjectured b | associative | `asymmetric`, `cardinality:many` | Henri Poincaré conjectured the Poincaré conjecture. |
| `superclass_of` | every b is an a | associative | `inverse:subclass_of` | Every square is a rectangle, so rectangle is a superclass of square. |
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
| `circumscribed_about` | figure a is circumscribed about figure b | associative | `inverse:inscribed_in`, `cardinality:many` | A square is circumscribed about a circle. |
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
| `keel_bound_by` | result a is keel-bound by result b (fictional) | associative | `inverse:keel_binds`, `cardinality:many` | Tamsin's theorem is keel-bound by Corvin's lemma. |
| `has_hallam_index` | every figure of class a has Hallam index b (fictional) | associative | `functional` | The Hallam index of every square is three times its side length. |
| `number_of_hessler_points` | every figure of class a has b Hessler points (fictional) | associative | `functional` | Every triangle has exactly three Hessler points. |
| `has_talley_weight` | every number of class a has Talley weight b (fictional) | associative | `functional` | Every Wendrel number has a Talley weight of 4. |
| `has_merrow_count` | every polygon of class a has Merrow count b (fictional) | associative | `functional` | Every Ashby polygon has a Merrow count equal to twice its number of sides. |
| `ferrel_linked_to` | number a is ferrel-linked to number b (fictional; insert 0015 makes it symmetric) | associative | `cardinality:many` | 12 is ferrel-linked to 35. |
| `has_tolland_root` | number a has Tolland root b (fictional) | associative | `functional` | The Tolland root of 50 is 5. |
| `tarn_divisor_of` | number a is a tarn-divisor of number b (fictional; insert 0017 makes it a subproperty of fen_divisor_of) | associative | `cardinality:many` | 6 is a tarn-divisor of 42. |
| `fen_divisor_of` | number a is a fen-divisor of number b (fictional) | associative | `cardinality:many` | 6 is a fen-divisor of 42. |
| `graft_nested_in` | set a is graft-nested in set b (fictional; insert 0018 makes it transitive) | associative | `cardinality:many` | The Arlenby set is graft-nested in the Bowrick set. |
| `corl_shades` | lattice a corl-shades lattice b (fictional; insert 0019 makes it asymmetric) | associative | `cardinality:many` | The Marnell lattice corl-shades the Quorra lattice. |
| `furl_image_of` | curve a is a furl-image of curve b (fictional; insert 0020 adds furl_image_of ∘ furl_image_of ⊑ double_furl_image_of) | associative | `cardinality:many` | The Tarrow curve is a furl-image of the Ulden curve. |
| `double_furl_image_of` | curve a is a double-furl image of curve b (fictional) | associative | `cardinality:many` | The Tarrow curve is a double-furl image of the Vessa curve. |
| `has_diagonals` | the two diagonals of every quadrilateral of class a are b | associative | `cardinality:many` | The two diagonals of every rectangle are equal in length. |
| `has_divisor_count_parity` | every whole number of class a has a b number of positive divisors | associative | `functional` | Every positive perfect square has an odd number of positive divisors. |
| `has_series_representation` | number a is the sum of the named infinite series b | associative | `cardinality:many` | π is the sum of the Nilakantha series. |
| `has_proof` | theorem a has the named proof b | associative | `cardinality:many` | The Pythagorean theorem has Garfield's proof. |
| `merrow_bound_to` | every polygon of class a is merrow-bound to some circle of class b (fictional) | associative | `cardinality:many` | Every Ashby polygon is merrow-bound to some Quellan circle. |
| `cairn_linked_to` | number a is cairn-linked to number b (fictional; insert 0016 adds cairn_linked_to ∘ divides ⊑ cairn_linked_to) | associative | `cardinality:many` | 5 is cairn-linked to 6. |
| `overgroup_of` | group a has subgroup b | associative | `inverse:subgroup_of`, `cardinality:many` | S4 has A4 as a subgroup. |
| `formulated` | a formulated law or principle b | associative | `cardinality:many` | Archimedes formulated the law of buoyancy. |
| `credited_with` | person a is credited with result b | associative | `cardinality:many` | Euclid is credited with the proof that there are infinitely many primes. |
| `father_of_field` | a is called the father of field b | associative |  | Euclid is called the father of geometry. |
| `career_in` | a spent his or her working life in city b | associative |  | Euclid worked in Alexandria. |
| `has_parity` | whole number a (or every number of class a) is b (odd or even) | associative | `functional` | 7 is odd. |
| `prime_factorization_is` | whole number a has prime factorization b | associative | `functional` | The prime factorization of 1001 is 7 × 11 × 13. |
| `least_prime_of` | the smallest prime in prime factorization a is b | associative | `functional` | The smallest prime in 7 × 11 × 13 is 7. |
| `greatest_prime_of` | the largest prime in prime factorization a is b | associative | `functional` | The largest prime in 7 × 13 × 19 is 19. |
| `has_side_count` | polygon a (or every polygon of class a) has b sides | associative | `functional` | Every convex hexagon has six sides. |
| `has_interior_angle` | every interior angle of regular polygon a is b | associative |  | Every interior angle of a square is 90 degrees. |
| `has_diagonal_count` | polygon a has b diagonals | associative |  | A square has two diagonals. |
| `face_angle` | every angle of every face of polyhedron a is b | associative |  | Every face angle of a regular octahedron is 60 degrees. |
| `face_diagonal_count` | each face of polyhedron a has b diagonals | associative |  | Each face of a regular octahedron has no diagonals. |
| `shape_disjoint` | no figure is both of kind a and of kind b | associative |  | No figure is both a triangle and a quadrilateral. |
| `power_zero_equals` | number a (or every number of class a) raised to the power 0 equals b | associative | `functional` | 10 to the power 0 is 1. |
| `subset_of` | set a is a subset of set b | associative |  | The even numbers are a subset of the integers. |
| `about` | theorem or result a is about b | associative | `cardinality:many` | The Pythagorean theorem is about right triangles. |

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
| `default_position` | words of class a default to position b relative to their head | associative | `functional` | English attributive adjectives come before the noun. |
| `has_initial_case` | words of class a are written with initial-letter case b | associative | `functional` | German nouns are written with a capital initial letter. |
| `takes_complement` | words of class a are followed by complement form b | associative | `functional` | English modal verbs take a bare infinitive ("must go"). |
| `has_gender` | noun or noun class a has grammatical gender b | associative | `functional` | German nouns ending in -ung are feminine. |
| `rhymes_with` | word a rhymes with word b | associative | `symmetric`, `cardinality:many` | "Night" rhymes with "light". |
| `has_past_participle` | verb a has the past participle b | associative | `inverse:past_participle_of` | "Go" has the past participle "gone". |
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
| `has_head` | compound noun a has as its head (last element) noun b | associative | `chain:has_gender->has_gender`, `inverse:head_of` | 'Vogelhaus' has the head 'Haus'. |
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
| `past_formed_with` | verbs of class a form their past tense with affix b | associative | `functional` | Tovrish verbs of motion form their past with 'drovka-'. |
| `has_inflection` | verbs of class a have the inflected form b | associative | `cardinality:many` | 'Be' has a present form used only with 'I'. |
| `used_with` | verb form a is used with the subject b | associative | `cardinality:many` | 'Am' is used with the subject 'I'. |
| `carries_velquorran_mark` | words of class a carry mark b in Velquorran notation (fictional) | associative | `cardinality:many` | English auxiliary verbs carry the hollow-star mark. |
| `has_stem_type` | words of class a have stem type b | associative | `functional` | German nouns in '-ung' are brightstemmed. |
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
| `attests_word` | language a attests word b | associative | `inverse:attested_in`, `cardinality:many` | Gothic attests the noun 'skip' (ship). |
| `loom_tied_to` | word a is loom-tied to word b (fictional; insert 0017 adds loom_tied_to ∘ singular_of ⊑ loom_tied_to) | associative | `cardinality:many` | 'Feather' is loom-tied to 'goose'. |
| `root_of` | word a is a word that word b derives from | associative | `inverse:derived_from`, `cardinality:many` | Greek "philosophia" is the root of "philosophy". |
| `attested_in` | word a is attested in language b (so it is a word of b) | associative | `inverse:attests_word`, `subproperty:word_of_language`, `cardinality:many` | The noun 'skip' (ship) is attested in Gothic. |
| `means_in_english` | word a means b in English | associative | `cardinality:many` | German 'Tür' means 'door'. |
| `ends_in` | word form a ends in ending b | associative |  | 'Children' ends in '-ren'. |
| `def_article` | noun a (or every noun of class a) takes the definite article b in the nominative | associative |  | German 'Haus' takes the definite article 'das'. |
| `acc_article` | noun a (or every noun of class a) takes the definite article b in the accusative | associative |  | German 'Küchentisch' takes 'den' in the accusative. |
| `indef_adj_pattern` | after an indefinite article, an adjective before noun a (or every noun of class a) takes ending pattern b | associative |  | 'ein schönes Haus': a neuter noun takes the -es pattern. |
| `refers_back_with` | noun a (or every noun of class a) is referred back to with pronoun b | associative |  | German 'Haus' is referred back to with 'es'. |
| `conjugation` | verb a is b (regular or irregular) | associative | `functional` | 'Swim' is an irregular verb. |
| `past_made_by` | verb a forms its past tense by b (the -ed ending or a vowel change) | associative | `functional` | 'Drink' forms its past tense by a vowel change. |
| `inflects_like_with_out` | verb a is verb b with the prefix 'out-', and inflects like it | associative |  | 'Outswim' inflects like 'swim'. |
| `prefixed_out` | word form a with the prefix 'out-' is b | associative |  | 'Went' with 'out-' is 'outwent'. |
| `prefixed_fore` | word form a with the prefix 'fore-' is b | associative |  | 'Went' with 'fore-' is 'forewent'. |
| `prefixed_god` | word form a with the prefix 'god' is b | associative |  | 'Children' with 'god' is 'godchildren'. |
| `prefixed_flower` | word form a with the word 'flower' before it is b | associative |  | 'Children' with 'flower' is 'flower children'. |
| `plural_kind` | noun a has a b plural (regular or irregular) | associative |  | 'Child' has an irregular plural. |

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
