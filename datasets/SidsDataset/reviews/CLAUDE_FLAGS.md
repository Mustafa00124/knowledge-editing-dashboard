# Claude's flags

Details of every red mark by reviewer `claude` (one-line reasons are on the marks in reviews.json), in review order: topics in order, records within each topic as reviewed.

## biology-replace-0003
- **derived[0]** (angle): "Are the arthropods that transmit bubonic plague insects?" is the edit restated through a description, so it adds little over the direct question. A question that reaches the class through a carrier-specific fact (e.g. arachnid anatomy such as eight legs) would test propagation better.

## biology-replace-0004
- **derived[0]** (angle): Same as replace-0003: the yes/no restates the edit through "the arthropods that transmit Lyme disease" and adds little over the direct question.

## biology-replace-0008
- **derived[0]** (problem): Thermus aquaticus is well known (the source of Taq polymerase), so a model may store "Thermus aquaticus is a prokaryote" by name. It is not a new or unfamiliar member, so the determinate label is doubtful; it behaves like the background-belief members. Swap for an obscure, recently described bacterium.

## biology-replace-0009
- **derived[0]** (problem): The instance (left ventricle, heart, circulatory system) has a conclusion that is true and well known in reality. A model can answer "yes, it follows" from stored anatomy even if it took the edit, so the gold "no" mixes the edited property with world knowledge. Real instances whose conclusion is not independently known (or fictional parts) would isolate the property.
- **cross_lingual[zh]** (problem): Same instance as derived[0], same confound.
- **cross_lingual[es]** (problem): Same instance as derived[0], same confound.

## biology-replace-0010
- **derived[0]** (problem): Sea anemones living in mutualism with clownfish is itself a known fact, and "mutualism" is mutual by definition, so a model says yes from knowledge and word meaning whatever the edit did.
- **unrelated_far[0]** (problem): "Is 'is a neighbour of' symmetric?" asks the same property as the edit, about a relation nearly synonymous with the near query's "is adjacent to". It is not far; pick a different property of an unrelated relation.

## biology-replace-0013
- **derived[1]** (problem): Labeled determinate (cartilage), but a model can store "dolphins have bone skeletons" by name exactly as it stores nursing, which the record treats as background beliefs. The worlds force the bone-skeleton belief to give way in every world, with the justification that "every shark has a cartilage skeleton" is defining; that distinction is not principled enough to make this determinate. It should be background_beliefs, or the question replaced.

## biology-delete-0005
- **serves-the-purpose** (problem): "Every spider has eight legs" is re-derivable from "spiders are arachnids" and "every arachnid has eight legs". Deleting only the spider rule leaves that route, so "not known" is not forced on the direct question or on the new-member questions.
- **derived[0]** (problem): Bagheera kiplingi as a jumping spider reaches eight legs through the arachnid route, which survives the delete; the determinate "not known" gold is not the only consistent answer.
- **derived[1]** (problem): Same superclass route for Eriovixia gryffindori.

## biology-delete-0008
- **serves-the-purpose** (problem): "Prokaryote" means a cell without a nucleus, and models firmly hold that bacteria have no nucleus, so the deleted rule is re-derivable by definition. The determinate "not known" golds are not forced.
- **derived[0]** (problem): Thermus aquaticus is well known (Taq polymerase), so it may be stored as a prokaryote by name, and it also has the no-nucleus route.

## biology-delete-0009
- **derived[0]** (problem): The left ventricle being part of the circulatory system is known anatomy, so a model answers yes regardless of whether transitivity was deleted; the instance cannot show the delete.
- **cross_lingual[zh]** (problem): Same instance and confound as derived[0].
- **cross_lingual[es]** (problem): Same instance and confound as derived[0].

## biology-delete-0010
- **derived[0]** (problem): Anemones living in mutualism with clownfish is a known fact, and mutualism is mutual by definition, so the answer stays yes whatever happens to the stored property.
- **unrelated_far[0]** (problem): Same as replace-0010: same property (symmetry) on a near-synonym of the near query's relation; not far.
- **derived[1]** (problem): Leafcutter ants farming their fungus is a well-known mutualism, and "mutualism" means both sides benefit, so "the fungus could fail to be in mutualism with the ants" is ruled out by word meaning and stored knowledge. The "does not know" gold cannot show the delete.

## biology-delete-0011
- **derived[0]** (problem): "Zebras are prey of lions" follows from the meaning of "prey" and from world knowledge, not from a stored inverse axiom, so deleting the axiom cannot be observed through this question. Lexical inverses are probably not deletable in a measurable way; consider dropping inverse deletes of lexical pairs.
- **serves-the-purpose** (problem): "Is prey of" is the passive reading of "preys on", so the inverse holds by the meaning of the words, not as a stored axiom that can be removed. Abstaining on its instances would be a language failure rather than a successful delete. Lexical inverse pairs are probably not deletable in a measurable way; consider dropping or tagging them.
- **derived[1]** (problem): "Owls prey on mice. Is it possible that mice are not prey of owls?" is the same sentence read the other way, and mice being owl prey is well known, so "no" stays correct after a perfect delete.
- **cross_lingual[zh]** (problem): Same instance as derived[0] (lions and zebras): a known fact whose reverse reading is fixed by the words.
- **cross_lingual[es]** (problem): Same as cross_lingual[zh].

## biology-insert-0003
- **clear-and-sensible** (problem): derived[2] has an ambiguous gold (see below).
- **derived[2]** (problem): "The tuatara" is the common name of the genus Sphenodon, so a new Sphenodon species is itself a tuatara, and "Is the tuatara the only living rhynchocephalian?" can fairly still be answered yes. Ask "Is Sphenodon punctatus the only living rhynchocephalian species?" instead.

## biology-insert-0005
- **derived[1]** (problem): "Is the beetle Quellotrechus marrani a parasite of the mite?" gets "no" from any model that never saw the edit (default no for an unknown pair of made-up names), so a right answer shows nothing about propagation of asymmetry.

## biology-insert-0011
- **serves-the-purpose** (problem): The made-up relation "drask-feeds on" contains the real word "feed", and hummingbirds really feed on nectar. Every question can be answered right from world knowledge without the edit, so the record cannot measure acquisition. Use a relation name with no real-word part, or a value that is not the real diet.
- **direct** (problem): Answered "nectar" by any model from the word "feed" plus real knowledge.
- **paraphrase** (problem): Same leak; "which sugary liquid" plus real diet gives nectar.
- **derived[2]** (problem): "Flowers" follows from real knowledge that hummingbirds take nectar from flowers, not from the made-up relation.

## biology-insert-0012
- **serves-the-purpose** (angle): Every question's gold is "yes", so a yes-biased model passes the whole record. Add a "no" control, such as a non-bat asked whether it is thalvic (should be unknown), or a contrapositive as insert-0013 and insert-0014 do.

## biology-insert-0016
- **direct** (problem): The edit says "symmetric", but the direct question asks "Is it asymmetric?" with gold "no". "No" is a likely default for an unknown relation, and not-asymmetric does not mean symmetric, so the question does not test the edited property directly. Ask "Is 'is marrow-paired with' symmetric?" instead.

## finance-replace-0009
- **propositional[0]** (angle): Double negation ("is it false that ... is not ...") mostly tests parsing of stacked negations rather than the edit; ask it as "Is it true that ... is not ...?" or tag it so results can be sliced.

## finance-replace-0010
- **propositional[0]** (angle): Double negation ("is it false that ... is not ...") mostly tests parsing of stacked negations rather than the edit; ask it as "Is it true that ... is not ...?" or tag it so results can be sliced.

## finance-replace-0011
- **propositional[0]** (angle): Double negation ("is it false that ... is not ...") mostly tests parsing of stacked negations rather than the edit; ask it as "Is it true that ... is not ...?" or tag it so results can be sliced.
- **serves-the-purpose** (angle): Wholly owned subsidiary to subsidiary is a head-noun entailment the wording itself gives, so this tests whether an edit can override word meaning rather than a relation property; worth tagging lexically analytic RBox edits separately.

## finance-replace-0016
- **unrelated_near[0]** (problem): The reference lists five co-founders; a model naming only Reid Hoffman is right but may be scored as a miss, so locality is measured by answer format. Ask for one founder or a single-answer neighbouring fact.

## finance-replace-0017
- **propositional[0]** (angle): Double negation ("is it false that ... is not ...") mostly tests parsing of stacked negations rather than the edit; ask it as "Is it true that ... is not ...?" or tag it so results can be sliced.

## finance-replace-0018
- **propositional[0]** (angle): Double negation ("is it false that ... is not ...") mostly tests parsing of stacked negations rather than the edit; ask it as "Is it true that ... is not ...?" or tag it so results can be sliced.

## finance-delete-0003
- **derived[0]** (problem): Labelled determinate (no answer), but in w2 only Disney's headquarters city is forgotten; a model that also stores Disney as a California company still answers California validly. Either list that side fact as forgotten in w2 (as delete-0016 does for Microsoft) or label it background_beliefs.
- **derived[1]** (problem): Same as derived[0]: in w2 a stored "Disney is based in California" survives forgetting the city, so "yes" is a valid answer and the determinate null gold is not forced.

## finance-delete-0011
- **serves-the-purpose** (problem): A wholly owned subsidiary is a subsidiary by the head noun (the earlier run flagged the replace record as lexical), and both instances are stored facts. Abstaining would mean failing to read English, not a successful delete.
- **derived[0]** (problem): LinkedIn being a Microsoft subsidiary is stored, and the wording gives it.
- **derived[1]** (problem): Whole Foods being an Amazon subsidiary is stored, and the wording gives it.
- **cross_lingual[zh]** (problem): Same instance as derived[0].
- **cross_lingual[es]** (problem): Same instance as derived[0].

## finance-delete-0012
- **serves-the-purpose** (problem): The delete has nothing observable to remove: the inverse is a voice change and both instances are famous, stored acquisitions.
- **derived[0]** (problem): "LinkedIn was acquired by Microsoft" is the passive of the premise and a stored fact; "yes" is correct after a perfect delete.
- **derived[1]** (problem): Same for Amazon and Whole Foods.
- **clear-and-sensible** (problem): "Microsoft acquired LinkedIn" and "LinkedIn was acquired by Microsoft" are the active and passive forms of one sentence. Deleting that inverse means forgetting English grammar, which is not a sensible belief to remove (same call as technology-delete-0012).
- **cross_lingual[zh]** (problem): Same instance as derived[0].
- **cross_lingual[es]** (problem): Same instance as derived[0].

## finance-delete-0016
- **unrelated_near[0]** (problem): Same as finance-replace-0016: the reference lists five co-founders, so a model naming only Reid Hoffman is right but may be scored as a miss. Ask for one founder or another single-answer neighbouring fact.

## finance-insert-0002
- **derived[0]** (problem): The bridge "every 1894-S Barber dime is a proof coin" is disputed among numismatists and several survivors are circulated, so a model can fail this even if the insert propagated; use an undisputed property such as the San Francisco Mint or the 24-coin mintage.
- **derived[1]** (problem): "Is the Corvane specimen one of a mintage of only 24 coins?" states the answer's content in the question; a yes default passes without the edit. Ask "How many 1894-S Barber dimes were struck, the Corvane specimen among them?" or similar.
- **derived[2]** (problem): Survivor count of nine kept after a tenth surfaces is a closed count the edit contradicts (A1); should be determinate (ten).
- **derived[3]** (problem): Same issue for the unaccounted remainder (15 vs 14).

## finance-insert-0003
- **derived[0]** (problem): "Admirael Kesterwijn" is a Dutch-style tulip name, so "which country did the bubble take place in" can be answered "the Netherlands" from the name alone, without the edit.
- **derived[1]** (problem): "Is the speculative bubble in which [a Dutch tulip name] was traded considered the first recorded speculative bubble?" is a leading yes/no; the description points to tulip mania by itself and a yes default passes.
- **derived[2]** (problem): The record stores the Semper Augustus at 10,000 guilders and the edit gives 15,000, so keeping the Semper Augustus as the dearest on record keeps a superlative the edit contradicts; under owl/FINDINGS.md A1 this is a patch, not a world, so the query should be determinate (the Admirael Kesterwijn).
- **derived[3]** (problem): Same issue: "yes" keeps a contradicted superlative.

## finance-insert-0010
- **serves-the-purpose** (problem): The determinacy labels contradict each other. derived[2] ("Is only one known?") is determinate no, on the grounds that keeping the stored uniqueness claim is an inconsistent patch. derived[3] ("How many are known?") is background_beliefs with w1 keeping the stored count of one. Both cannot hold; the same pattern was flagged in literature_arts-insert-0001 to 0003 and history-insert-0001.
- **derived[3]** (problem): By the record's own reasoning in derived[2], w1 (count stays 1) is not a world, so this should be determinate with gold 2.

## finance-insert-0015
- **serves-the-purpose** (problem): The made-up name "spire-partnered" contains "partnered", which reads as symmetric, so a model without the edit already answers yes everywhere; the record cannot tell an inserted property from a lexical guess.
- **direct** (problem): A model with no edit will likely say "partnered with" is symmetric from the word alone, so yes does not show the insert took.
- **derived[0]** (problem): Answerable from the word "partnered" without the insert: partnership reads as mutual.
- **derived[1]** (problem): Same lexical default as derived[0]: "partnered" suggests mutuality, so "no" is reachable without the insert.
- **cross_lingual[zh]** (problem): Same instance as derived[0] (HSBC and Santander), so the symmetric reading comes from the word "partnered" without the insert.
- **cross_lingual[es]** (problem): Same instance as derived[0]; the same lexical leak.

## finance-insert-0018
- **serves-the-purpose** (problem): The made-up relation "is a kiln lender to" contains "lender", and a lender is a creditor by the meaning of the words. Every question about the inserted subproperty (direct, cross-lingual, derived) can be answered right from word meaning without the edit, like the "drask-feeds" leak in biology-insert-0011. Use a relation name with no real-word head (e.g. "is kiln-bound to").
- **direct** (problem): "Can a kiln lender fail to be a creditor?" gets "no" from the word "lender".
- **derived[0]** (problem): "No" follows from "lender" implies "creditor", not from the edit.
- **derived[1]** (problem): "Yes" follows from "lender" implies "creditor", not from the edit.
- **cross_lingual[zh]** (problem): Same instance as derived[0]; the lexical leak carries over.
- **cross_lingual[es]** (problem): Same instance as derived[0]; the lexical leak carries over.

## finance-insert-0020
- **clear-and-sensible** (problem): Both functionality instances conclude that two differently named firms (Morrowfield Trust and Fenner & Lisle, Dunmere Trust and Rookwell Capital) are the same firm. That is valid in OWL without a unique-name assumption, but a reader or a model normally takes distinct names as distinct firms and sees the premises as contradicting the property, so "they are different, the facts are inconsistent" is a fair answer. Better instances: "The Brenlow Fund has tally warden Morrowfield Trust. Could it also have tally warden Fenner & Lisle?" (no).
- **cross_lingual[zh]** (problem): Same instance as derived[0].
- **cross_lingual[es]** (problem): Same instance as derived[0].
- **derived[0]** (problem): Gold "no, they cannot be two different firms" rests on dropping the unique-name assumption; see clear-and-sensible.
- **derived[1]** (problem): Gold "yes, the same firm" has the same issue.

## geography-replace-0005
- **derived[1]** (problem): Tunulliarfik is a fjord in southern Greenland, right next to the Greenland ice sheet. A model that took the edited rule (fjords are unglaciated river valleys) can still answer "yes, a glacier filled it" from what it knows about Greenland, so a yes does not cleanly mean the rule failed to propagate. A new member in a place with no ice association (or a made-up fjord) would isolate the rule.

## geography-replace-0018
- **clear-and-sensible** (problem): The instance questions ask whether Lesotho could also be an enclave within Botswana, and San Marino also within France. Real geography rules both out (Lesotho does not touch Botswana; San Marino is nowhere near France), so "no" is a fair answer even if the model fully accepted that 'is an enclave within' is not functional. The gold "yes" is not the only fair answer.
- **derived[0]** (problem): Lesotho is surrounded by South Africa alone and does not touch Botswana.
- **derived[1]** (problem): San Marino is entirely inside Italy, nowhere near France.
- **cross_lingual[zh]** (problem): Same instance as derived[0].
- **cross_lingual[es]** (problem): Same instance as derived[0].
- **serves-the-purpose** (problem): Functionality of "is an enclave within" is the definition of an enclave (surrounded by only one state), and the instances (Lesotho also an enclave in Botswana, San Marino also in France) are ruled out by the map. A model that took the edit can still answer "not consistent" from geography, so the gold "yes" cannot separate a failed edit from world knowledge. Made-up territories would isolate the property.

## geography-delete-0005
- **derived[1]** (problem): Tunulliarfik is beside the Greenland ice sheet, so after deleting the fjord definition a model can still say a glacier filled it from regional knowledge. The expected abstention is not the only reasonable answer, and a "yes" does not show the delete failed.

## geography-delete-0010
- **serves-the-purpose** (angle): The deleted inverse ('has as its largest city' of 'is the largest city of') is a rewording of the same relation, so its instances ("Istanbul is the largest city of Turkey. Does it follow that Turkey's largest city is Istanbul?") test whether a model stops understanding a paraphrase. Abstaining would be a reading failure, not a successful delete. Deleting near-definitional inverses teaches little; consider dropping this kind of RBox delete or tagging it.
- **derived[0]** (angle): The conclusion restates the premise, so yes follows from reading, not from the deleted inverse.
- **derived[1]** (angle): Same restatement with São Paulo and Brazil.
- **cross_lingual[zh]** (angle): Same restatement instance as derived[0].
- **cross_lingual[es]** (angle): Same restatement instance as derived[0].

## geography-delete-0018
- **clear-and-sensible** (problem): Mirror of replace-0018. The instances (Lesotho also within Botswana, San Marino also within France) are ruled out by real geography, so after the delete a model can still fairly answer "no" without holding functionality, and that is scored as a failure against the abstention gold.
- **derived[0]** (problem): Lesotho is surrounded by South Africa alone and does not touch Botswana, so "no" follows from the map.
- **derived[1]** (problem): San Marino is entirely inside Italy, far from France, so "no" follows from the map.
- **cross_lingual[zh]** (problem): Same instance as derived[0].
- **cross_lingual[es]** (problem): Same instance as derived[0].
- **serves-the-purpose** (problem): An enclave is by definition entirely surrounded by a single state, so the deleted functionality is part of the word's meaning; and both instances (Lesotho also in Botswana, San Marino also in France) are ruled out by real geography (the existing clear-and-sensible red). "Not consistent" stays the right answer after a perfect delete, so the abstain gold measures nothing.

## geography-delete-0020
- **derived[0]** (problem): Quibdo is given an Af climate in the prompt, which means warm all year by definition.
- **derived[1]** (problem): Tabubil, the same.
- **serves-the-purpose** (problem): A tropical rainforest climate (Koppen Af) is defined by every month averaging at least 18 C, so "warm all year round" is part of the class definition. The notes argue that a model re-deriving it keeps a patch, but that asks the model to forget the meaning of the climate class, not one stored rule. The determinate abstain golds on the new members are not a fair target.

## geography-insert-0005
- **derived[1]** (problem): "Does the Calvarne drain into the Ammerlade?" With two made-up rivers, "no" is the natural default before any edit, so a right answer does not show asymmetry propagated. An asymmetry question needs a form whose gold differs from the no-knowledge default.

## geography-insert-0015
- **derived[1]** (problem): "Naples is lantern-paired with Marseille. Does it follow that Marseille is not lantern-paired with Naples?" has gold no, but before the edit nothing follows either way, so the answer is no too. A right answer shows nothing about the inserted symmetry. Phrase the no-instance so it is yes before the edit, e.g. "Given only this, could Marseille fail to be lantern-paired with Naples?" (no after, yes before), as geography-insert-0017 derived[1] does.

## geography-insert-0016
- **derived[0]** (angle): The made-up name "causeway-chained" already suggests something that chains along, so a model may say Trieste is chained to Zagreb from the word alone. A neutral nonsense name would separate learning transitivity from reading the name.
- **derived[1]** (angle): Same for Graz, Maribor, Zagreb.

## geography-insert-0018
- **serves-the-purpose** (problem): Both instance questions, and therefore both cross-lingual questions, have gold "no" to "does it follow ...", which is also the pre-edit answer. Only the direct question can show the inverse was learned.
- **derived[0]** (problem): "Does it follow that Ludrovin is not the moor-ward of Fennholt?" is no before the edit (a denial never follows from nothing), so the gold is the same before and after. This is the existing serves-the-purpose red made concrete.
- **derived[1]** (problem): "Does it follow that Haverlode is the moor-warden of Brindlecot?" is no before the edit too. Use the "could it fail" phrasing, which is yes before and no after.
- **cross_lingual[zh]** (problem): Same instance as derived[0].
- **cross_lingual[es]** (problem): Same instance as derived[0].
- **direct** (problem): "Warden" and "ward" are a real inverse pair in English (a warden has wards), so "Is 'is the moor-ward of' the inverse of 'is the moor-warden of'?" gets yes from the words alone. A made-up pair with no real-word inverse would test the insert.

## geography-insert-0019
- **derived[0]** (problem): Gold rests on two names for one town; see clear-and-sensible.
- **cross_lingual[zh]** (problem): Same instance as derived[0].
- **cross_lingual[es]** (problem): Same instance as derived[0].
- **clear-and-sensible** (problem): Same issue as finance-insert-0020: both functionality instances name a region's gale-seat as two differently named towns and conclude the two names are one town. That holds in OWL without a unique-name assumption, but readers and models take distinct place names as distinct places, so the premises read as contradicting functionality and "they are different, the facts are inconsistent" is a fair answer. Ask instead "The gale-seat of the Kelmar Fells is Ammerwick. Could Pennatch also be its gale-seat?".
- **derived[1]** (problem): Same.

## geography-insert-0020
- **derived[0]** (problem): "Skelloway is the riverward neighbour of Drummaree. Does it follow that Drummaree is the riverward neighbour of Skelloway?" is no before the edit as well (nothing follows about a made-up relation), so the gold is the same before and after and a right answer shows nothing. derived[1] ("does it follow that ... is not ...?", yes) is the discriminating form; use it, or "could ... also be ...?", for both.
- **cross_lingual[zh]** (problem): Same instance as derived[0].
- **cross_lingual[es]** (problem): Same instance as derived[0].

## grammar-replace-0014
- **derived[0]** (problem): 'Vogelhaus' is a common word whose gender ('das Vogelhaus') a model may store by name rather than build from 'Haus'. In that world it stays neuter after the edit, which is a valid outcome, so the query is background_beliefs, not determinate.
- **derived[1]** (problem): Same as derived[0] for 'Gartenhaus', which is common enough to carry its own stored gender. Label should be background_beliefs with worlds for stored vs built compounds.
- **serves-the-purpose** (problem): Two of the four derived queries carry a determinate label that does not hold for well-known compounds, so the record's determinacy split is off. Rare or invented compounds (e.g. a nonce 'Knarbselhaus') would keep the chain determinate.

## grammar-replace-0015
- **serves-the-purpose** (angle): The edit is a derived belief (derivability likely, built from 'Tür' is feminine plus head-gender inheritance), but no derived query asks a premise ('What is the gender of Tür?' or another '-tür' compound). That leaves out the derived-beliefs side, which premise gives way, that the scheme is designed to test.

## grammar-replace-0016
- **serves-the-purpose** (angle): Same as grammar-replace-0015 with 'Tisch': a derived edit with no premise query. Asking the gender of 'Tisch' or of 'Schreibtisch' would show whether the model revised the head noun, the compound rule, or neither.

## grammar-replace-0018
- **derived[0]** (problem): "They" is only third person is stored, so "no" after the edit may be correct knowledge rather than a failed edit.
- **derived[1]** (problem): Same for "she".
- **cross_lingual[zh]** (problem): Same instance as derived[0].
- **cross_lingual[es]** (problem): Same instance as derived[0].
- **clear-and-sensible** (problem): After the edit the gold says "they" can also be first person, but the model knows the English pronoun paradigm, so "no" stays a fair answer. The instances have two fair answers.
- **serves-the-purpose** (problem): Both instances are about the real paradigm ("they", "she"), which every model stores, so the answer is decided by memory, not by the edited property. A made-up pronoun system stated in the prompt would isolate functionality.
- **propositional[0]** (angle): "Is it false that ... is not functional" stacks negations; mostly tests parsing.

## grammar-delete-0001
- **serves-the-purpose** (angle): Deleting a very high-frequency form like 'went' collides with fluency: a model will keep producing 'went' in free text while it may abstain on the direct question. A generation probe (continue 'Yesterday she ...') would show whether a delete is only surface-level. Applies to grammar deletes generally.

## grammar-delete-0012
- **derived[0]** (problem): The conclusion restates the premise and is known (written is the past participle of write).
- **derived[1]** (problem): Same for take/taken.
- **cross_lingual[zh]** (problem): Same instance as derived[0].
- **cross_lingual[es]** (problem): Same instance as derived[0].
- **serves-the-purpose** (problem): "'Write' has the past participle 'written'" and "'written' is the past participle of 'write'" are one statement in two word orders, and both instance conclusions are well-known English forms. Deleting the inverse can only be shown by the model refusing to read a rewording or forgetting its grammar, so the abstain gold is not a meaningful target (as geography-delete-0010 and technology-delete-0012). Lexical inverses are probably not deletable in a measurable way.

## grammar-delete-0014
- **derived[0]** (problem): "Das Vogelhaus" may be stored by name, so neuter can survive the delete; this is background_beliefs, not determinate. Use a rare or made-up compound with Haus as its head.
- **derived[1]** (problem): Same as derived[0] for "das Gartenhaus".
- **serves-the-purpose** (problem): Both compound queries (derived[0], derived[1]) are labelled determinate and expect "not known", but Vogelhaus and Gartenhaus are common enough that a model may store "das Vogelhaus" and "das Gartenhaus" by name. After a perfect delete of Haus's gender those stored genders survive, so "neuter" is a valid answer. Same issue as grammar-replace-0014.

## grammar-delete-0018
- **derived[0]** (problem): "Can 'they' also be first person?" is answered "no" from stored knowledge, not from the deleted property.
- **derived[1]** (problem): Same for "she" as second person.
- **cross_lingual[zh]** (problem): Same instance as derived[0].
- **cross_lingual[es]** (problem): Same instance as derived[0].
- **clear-and-sensible** (problem): All instance questions have a gold that does not follow from the delete.
- **serves-the-purpose** (problem): Both instances ask whether "they" or "she" can also be another grammatical person. Models know the pronoun paradigm by heart, so "no" comes from stored grammar after a perfect delete of functionality, and the abstain gold scores that knowledge as a failure. Instances need values the model does not already know (a made-up pronoun system stated in the prompt).

## grammar-insert-0002
- **derived[0]** (problem): 'Glendrink' is made of the English-looking 'glen' and 'drink', so a model can call it Germanic from its shape alone, without the inserted fact. A less English-looking nonce word would make the question depend on the insert.
- **derived[3]** (problem): The word contains 'drink', so asking whether it and English 'drink' come from the same branch invites 'yes' from surface overlap.

## grammar-insert-0012
- **serves-the-purpose** (angle): Every question (direct, paraphrase, propositional[1], all four derived) has gold 'yes', so a yes-biased model passes the whole record. A contrast item (a noun not ending in '-ung', expected 'not stated' or 'no') would catch yes-bias.

## grammar-insert-0015
- **derived[1]** (problem): "Does it follow that pepper is not quill-paired with salt?" has the answer "no" before the edit too (nothing follows), so it passes without the edit.
- **serves-the-purpose** (angle): "Paired with" already reads as a symmetric relation in plain English, and both instances are classic pairs (bread and butter, salt and pepper). A model can say yes from the made-up name's real-word part, as in biology-insert-0011. A name with no real-word part would isolate the inserted property.
- **direct** (problem): The edit says "symmetric", but the direct question asks "Is it asymmetric?" with gold "no". "No" is a likely default for an unknown relation, and not asymmetric does not mean symmetric, so this does not test the edited property. Same as biology-insert-0016.

## grammar-insert-0016
- **derived[0]** (problem): "Does it follow that ocean is not ember-ranked above lake?" is "no" before the edit too, since nothing follows without transitivity. It does not discriminate; only derived[1] tests the property.
- **cross_lingual[zh]** (problem): Same negated instance as derived[0]; "no" is right with or without the edit.
- **cross_lingual[es]** (problem): Same as cross_lingual[zh].
- **serves-the-purpose** (angle): "Ranked above" names an ordering, which is transitive by word meaning, so the made-up relation's name hands over the inserted property.

## grammar-insert-0018
- **cross_lingual[zh]** (problem): Same converse instance as derived[0]; "no" before and after.
- **cross_lingual[es]** (problem): Same as cross_lingual[zh].
- **derived[0]** (problem): The converse of a subproperty does not follow, but it does not follow before the edit either, so a model that never learned the subproperty answers "no" and passes. Only derived[1] discriminates.

## grammar-insert-0020
- **derived[0]** (problem): "Are skorrel and drimbask the same word?" is "no" for any model: they are two different strings. The intended test (functional is not inverse functional) is fine, but the gold is the same before and after the edit. An instance whose answer flips (e.g. derived[1]'s form) should carry the cross-lingual questions.
- **cross_lingual[zh]** (problem): Same instance as derived[0]; "no" before and after.
- **cross_lingual[es]** (problem): Same as cross_lingual[zh].
- **serves-the-purpose** (problem): Only derived[1] depends on the edit.

## history-replace-0004
- **derived[1]** (problem): "In which US state was the president at the time of the Wright brothers' first powered flight born?" has new gold Ohio (McKinley). The Wright brothers themselves are strongly tied to Ohio (Dayton), so a model can answer Ohio by association with the flight, without the edit reaching the president's birthplace. Pick a property of McKinley that has no link to the Wrights (for example his party's opponent, or his assassin).

## history-replace-0009
- **clear-and-sensible** (problem): After the edit "'happened before' is not transitive", the instance gold is "no", but both conclusions (fall of Rome 476 before Magna Carta 1215; French Revolution 1789 before the American Civil War 1861) are true by dates every model knows. "Does it follow" then has two fair readings: from the premises alone, or from everything the model knows.
- **serves-the-purpose** (problem): Removing a property and testing it on real events whose conclusions are independently known confounds the instance questions: a "yes" can come from stored dates rather than from a failed edit. Made-up events, whose order is only given in the prompt, would isolate the property.
- **cross_lingual[zh]** (problem): Same instance as derived[0], so the same confound.
- **cross_lingual[es]** (problem): Same instance as derived[0], so the same confound.
- **derived[0]** (problem): The model knows 476 and 1215 directly, so it can say yes without transitivity.
- **derived[1]** (problem): The model knows 1789 and 1861 directly, so it can say yes without transitivity.

## history-replace-0011
- **clear-and-sensible** (problem): After removing "assassinated is a subproperty of killed", the gold for "Does it follow that Princip killed Franz Ferdinand?" is "no", but the model stores that Princip shot him dead (and that Godse shot Gandhi). The question has two fair readings.
- **cross_lingual[zh]** (problem): Same instance as derived[0], so the same confound.
- **cross_lingual[es]** (problem): Same instance as derived[0], so the same confound.
- **derived[0]** (problem): "Princip killed Franz Ferdinand" is a stored fact, so a "yes" does not show the edit failed. Use made-up assassins and victims.
- **derived[1]** (problem): "Godse killed Gandhi" is a stored fact; same confound.

## history-replace-0018
- **serves-the-purpose** (angle): A person dies once, so "died in year" is functional by what death means; the edit asks the model to accept someone dying in 814 and also in 815. This tests overriding a definition rather than a learned relation property, like the earlier angle reds on people-replace-0011 and people-replace-0012. Tag definitional RBox edits so results can be sliced.
- **propositional[0]** (angle): "Is it false that the relation 'died in year' is not functional?" stacks two negations; it mostly tests parsing. Ask "Is it true that ... is not functional?" or tag it.

## history-delete-0009
- **clear-and-sensible** (problem): The instance events are famous and well dated (476, 1066, 1215; 1789, 1815, 1861), so "yes" stays a fair answer after the delete. Same as history-replace-0009.
- **cross_lingual[zh]** (problem): Same instance as derived[0].
- **cross_lingual[es]** (problem): Same instance as derived[0].
- **derived[0]** (problem): 476 before 1215 is known from dates, so "yes" does not show the delete failed.
- **derived[1]** (problem): 1789 before 1861 is known from dates; same confound.
- **serves-the-purpose** (problem): Deleting transitivity on real, dated events cannot be observed: a model answers from the dates. Made-up events would isolate the property.

## history-delete-0011
- **clear-and-sensible** (problem): "Assassinate" means to kill (for a political motive), and Princip killing Franz Ferdinand and Godse killing Gandhi are stored facts, so "yes" stays a fair answer after the delete. Same as history-replace-0011.
- **cross_lingual[zh]** (problem): Same instance as derived[0].
- **cross_lingual[es]** (problem): Same instance as derived[0].
- **derived[0]** (problem): Princip killing Franz Ferdinand is stored directly.
- **derived[1]** (problem): Godse killing Gandhi is stored directly.
- **serves-the-purpose** (problem): The property is part of the word's meaning and both instance conclusions are stored, so the delete cannot be observed through these questions. Made-up people and a made-up relation pair would isolate it.

## history-delete-0013
- **derived[0]** (problem): "Is the island of Elba in Europe?" is labelled determinate (does not know) after deleting "Elba is in Italy". But Elba is widely described as a Mediterranean island of Europe in its own right (and lies off Tuscany), a route that does not go through the deleted country fact. That makes it a background-beliefs split (yes if Europe is stored for Elba directly, unknown if reached only through Italy), not determinate.

## history-insert-0001
- **derived[2]** (problem): "How many originals of the 1215 Magna Carta survive?" is indeterminate (w1 four, stored as a figure; w2 five). But the edit adds a fifth original, so keeping "four survive" is keeping a closed claim the edit contradicts, which owl/FINDINGS.md A1 treats as a patch, not a world (as done for history-insert-0003/0004). It should be determinate (five), or the record should say why counts differ from "the only one" claims (FINDINGS open decision 2).
- **derived[3]** (problem): Same as derived[2] for "how many outside London" (two vs three).

## history-insert-0002
- **derived[2]** (problem): "49 copies survive" kept after a new copy is found is a closed count the edit contradicts; under the A1 reasoning it is not a valid world. Make it determinate (50) or settle FINDINGS open decision 2 explicitly.
- **derived[3]** (problem): Same issue for "more than 49?".

## history-insert-0006
- **serves-the-purpose** (problem): The made-up relation "flint-pledged" is placed exactly on the real 1386 Anglo-Portuguese alliance (Treaty of Windsor, which the near question even asks about). A model with no edit, asked which kingdom Portugal was bound to in 1386, will say England from the real alliance, so success on the direct, paraphrase, cross-lingual and two composition questions does not show the made-up fact was learned. Use a year or a pair of states with no famous tie.
- **direct** (problem): England guessable from the real alliance.
- **paraphrase** (problem): Same.
- **cross_lingual[zh]** (problem): Same.
- **cross_lingual[es]** (problem): Same.
- **derived[0]** (problem): Richard II follows from "England in 1386" which the real alliance gives.
- **derived[1]** (problem): "A kingdom on Great Britain" follows from the real alliance as well.

## history-insert-0007
- **paraphrase** (problem): "Which king of France was banner-bonded with Richard the Lionheart?" names the country; the French king of Richard's reign is Philip Augustus, his famous crusade partner and rival, so the answer comes without the edit.

## history-insert-0009
- **paraphrase** (problem): "Which pre-Columbian civilization made the Pellingworth codices found in Chiapas in 2024?" Chiapas plus "codices" gives the Maya without the edit.
- **derived[2]** (problem): Same count issue as insert-0001: a stored "four codices" next to two newly found Maya codices is a closed claim the edit contradicts.
- **derived[3]** (problem): Same, for "more than four?".

## history-insert-0010
- **derived[2]** (problem): Same count issue: "seventeen heads" kept next to two new Olmec heads contradicts the edit.
- **derived[3]** (problem): Same, for "more than seventeen?".

## history-insert-0016
- **direct** (problem): The edit says "asymmetric" but the direct question asks "Is it symmetric?" with gold "no". "No" is the default for an unknown relation, and not symmetric does not mean asymmetric. Ask "Is it asymmetric?" (yes).
- **derived[0]** (problem): "Does it follow that Pisa owed reed-tithe to Florence?" is "no" before the edit too, since nothing follows. Use derived[1]'s form (does the negation follow?) for the cross-lingual questions.
- **cross_lingual[zh]** (problem): Same instance as derived[0]; "no" before and after.
- **cross_lingual[es]** (problem): Same as cross_lingual[zh].
- **serves-the-purpose** (problem): The direct question, both cross-lingual questions and derived[0] all have the gold "no", which a model gets for an unknown made-up relation without the edit. Only derived[1] (does the negation follow? yes) and the propositional questions discriminate, so most of the record cannot show the asymmetry was learned.

## history-insert-0017
- **derived[1]** (problem): "Does it follow that Portugal paid Aragon?" is "no" before the edit too; a model that never learned transitivity passes. Only derived[0] discriminates.

## history-insert-0018
- **derived[0]** (problem): "Edric held the cinder-oath of Tolver. Does it follow that Edric was cinder-sworn to Tolver?" gets "no" from any model that never saw the edit, since nothing follows about made-up relations. A useful converse-confusion control, but it cannot show the inverse was learned; the cross-lingual queries should use derived[1]'s instance.
- **cross_lingual[zh]** (problem): Same instance as derived[0]; gold "no" passes without the edit.
- **cross_lingual[es]** (problem): Same instance as derived[0]; gold "no" passes without the edit.
- **serves-the-purpose** (angle): The made-up names carry their inverse in plain English: being "sworn to" someone and that person "holding the oath of" you read as two sides of one act. A model can answer the direct question and derived[1] yes from the words alone, and the two "no" items (derived[0] and both cross-lingual) pass by default. Use relation names with no English meaning, e.g. "was varn-bound to" and "held the quell of".

## history-insert-0019
- **derived[0]** (problem): Whether another person was also the queen's cup-warden is not settled by functionality of the warden's side, so "no" holds before and after the edit and is the default for made-up facts. Keep it as a control if wanted, but the cross-lingual pair should use derived[1]'s instance, which does need the edit.
- **cross_lingual[zh]** (problem): Same instance as derived[0]; its "no" does not depend on the edit.
- **cross_lingual[es]** (problem): Same instance as derived[0]; its "no" does not depend on the edit.

## history-insert-0020
- **direct** (problem): "Blade-wed" and "thorn-feuded" read as marriage-like alliance and feud, which are opposites by their English words, so a model can answer "no, not both" from the names alone.
- **derived[0]** (problem): Same leak: the exclusion is guessable from the names.
- **derived[1]** (problem): "Thorn-feuded, does it follow that they were blade-wed?" is "no" with or without the disjointness axiom, and "no" is the default for made-up relations. It tests nothing about the edit. A better second instance: "House Quenford was thorn-feuded with House Strellan. Could House Quenford have been blade-wed to House Strellan?" (no only through the edit), or the disjointness in the other direction.

## literature_arts-replace-0009
- **serves-the-purpose** (problem): "Comes earlier in the same series than" is an order, transitive by its meaning, and both instances are reading orders every model stores (The Fellowship of the Ring before The Return of the King; Philosopher's Stone before Deathly Hallows). After a perfect edit a model can still answer yes from memory, so the gold "no" cannot separate a failed edit from world knowledge, as in history-replace-0009. Made-up series would isolate the property.
- **cross_lingual[zh]** (problem): Same instance as derived[0], same confound.
- **cross_lingual[es]** (problem): Same instance as derived[0], same confound.
- **derived[0]** (problem): Fellowship before Return of the King is stored directly.
- **derived[1]** (problem): Philosopher's Stone before Deathly Hallows is stored directly.
- **propositional[0]** (angle): Stacked negation ("Is it false that ... is not transitive?") tests parsing of double negatives more than the edit.

## literature_arts-replace-0010
- **serves-the-purpose** (problem): "Collaborated with" is mutual by its meaning (working together), and both instances are famous two-way partnerships (Gilbert and Sullivan, Rodgers and Hammerstein). A model can keep "yes" from the word and from memory whatever happened to the stored property, so the gold "no" is not a clean test of the edit.
- **cross_lingual[zh]** (problem): Same instance as derived[0], same confound.
- **cross_lingual[es]** (problem): Same instance as derived[0], same confound.
- **derived[0]** (problem): Sullivan collaborated with Gilbert is stored and follows from the word.
- **derived[1]** (problem): Hammerstein collaborated with Rodgers is stored and follows from the word.
- **propositional[0]** (angle): Stacked negation ("Is it false that ... is not symmetric?") tests parsing of double negatives more than the edit.

## literature_arts-replace-0014
- **derived[3]** (problem): The bridge "every epic poem opens with an invocation to a muse" is a classical convention with well-known exceptions (Beowulf, Gilgamesh). A model that fully accepts The Lord of the Rings as an epic poem can fairly still answer no, so the w2 answer 'yes' is not forced even under perfect propagation.

## literature_arts-replace-0015
- **derived[1]** (problem): The bridge "Andromache, Astyanax's mother, was the daughter of Eetion" is not needed: 'grandchild of Nestor' follows from the edit by the subproperty alone. The bridge is obscure, so models that fail its check lose a query that did not depend on it.

## literature_arts-replace-0018
- **serves-the-purpose** (problem): Both instances ask whether a key's known signature excludes another one (D major two sharps, so not three; E-flat major three flats, so not two). Every model stores each key's single signature, so after a perfect edit it can still answer yes from music theory it holds, and the gold "no" cannot separate a failed edit from that knowledge. Instances with keys of a made-up tuning system, or made-up signatures, would isolate the property.
- **cross_lingual[zh]** (problem): Same instance as derived[0], same confound.
- **cross_lingual[es]** (problem): Same instance as derived[0], same confound.
- **derived[0]** (problem): D major not having three sharps is stored directly.
- **derived[1]** (problem): E-flat major not having two flats is stored directly.
- **propositional[0]** (angle): Stacked negation ("Is it false that ... is not functional?") tests parsing of double negatives more than the edit.

## literature_arts-delete-0009
- **serves-the-purpose** (problem): "Comes earlier in the same series than" is an order, transitive by what "earlier" means, and both instances (The Lord of the Rings volumes, the Harry Potter books) have conclusions the model stores directly. After a perfect delete a model can still answer yes from memory or from the meaning of the words, so the abstain gold cannot separate a failed delete from correct reasoning. Same pattern as technology-delete-0009 and technology-replace-0009. Made-up series and works would isolate the property.
- **cross_lingual[zh]** (problem): Same instance as derived[0].
- **cross_lingual[es]** (problem): Same instance as derived[0].
- **derived[0]** (problem): Fellowship before Return of the King is a stored fact and follows from the meaning of "earlier".
- **derived[1]** (problem): Philosopher's Stone before Deathly Hallows is a stored fact.

## literature_arts-delete-0010
- **serves-the-purpose** (problem): Collaboration is mutual by the meaning of the word (like mutualism in biology-delete-0010), and Gilbert and Sullivan and Rodgers and Hammerstein are among the best-known pairs in the topic. The reverse is both lexical and stored, so the delete has nothing measurable to remove; abstaining would be a language failure. Consider dropping symmetry deletes of lexically symmetric relations, or using made-up names with a made-up relation.
- **cross_lingual[zh]** (problem): Same instance as derived[0].
- **cross_lingual[es]** (problem): Same instance as derived[0].
- **derived[0]** (problem): Sullivan collaborated with Gilbert is stored and follows from the word.
- **derived[1]** (problem): Hammerstein collaborated with Rodgers is stored and follows from the word.

## literature_arts-delete-0011
- **serves-the-purpose** (problem): A sequel comes after the work it continues by definition, so "sequel of ⊑ comes later in the same series than" is part of the word's meaning, and both instances (Through the Looking-Glass, Anne of Avonlea) are famous. Expecting "does not know" asks the model to forget what "sequel" means; a "yes" is correct reasoning, not a failed delete.
- **cross_lingual[zh]** (problem): Same instance as derived[0].
- **cross_lingual[es]** (problem): Same instance as derived[0].
- **derived[0]** (problem): The order follows from the word "sequel" given in the prompt.
- **derived[1]** (problem): Same as derived[0].

## literature_arts-delete-0012
- **clear-and-sensible** (problem): "Pride and Prejudice was written by Jane Austen" and "Jane Austen is the author of Pride and Prejudice" are the same statement in passive and active form. Deleting that inverse means forgetting English grammar, as with technology-delete-0012.
- **serves-the-purpose** (problem): The inverse is lexical and both instances are famous stored facts, so a "yes" after the delete is correct reading, not a failed delete. Consider dropping inverse deletes of passive/active or near-synonym pairs.
- **cross_lingual[zh]** (problem): Same instance as derived[0].
- **cross_lingual[es]** (problem): Same instance as derived[0].
- **derived[0]** (problem): The conclusion rewords the premise (and is a stored fact about Austen).
- **derived[1]** (problem): Same for Melville and Moby-Dick.

## literature_arts-delete-0014
- **derived[3]** (problem): "Does The Lord of the Rings open with an invocation to a muse?" is "no" for any modern prose work, before and after the delete, and "no" is also the default. It cannot show the delete took.
- **derived[2]** (problem): World w2 assumes the model knows The Lord of the Rings has chapters only because novels have chapters. For one of the most discussed books in English, with its six books and named chapters, that is not a plausible storage, so the "not known" outcome does not describe a real world and the background-beliefs split is mostly a formality. A structure property that really is reached through the form would serve better, or drop the query.

## literature_arts-delete-0017
- **serves-the-purpose** (problem): housed_in ∘ located_in ⊑ located_in is containment: a painting inside a building in Chicago is in Chicago by what "in" means, not by a stored rule that can be removed. Both instances are also famous stored facts (American Gothic in Chicago, Guernica in Madrid). So after a perfect delete "yes" is still correct, and the abstain gold scores correct reasoning as a failed delete. Same issue as history-replace-0017. A chain whose conclusion is not containment (for example housed_in ∘ owned_by ⊑ owned_by) with obscure or made-up works would be measurable.
- **cross_lingual[zh]** (problem): Same instance as derived[0].
- **cross_lingual[es]** (problem): Same instance as derived[0].
- **derived[0]** (problem): American Gothic in Chicago: stored, and follows from containment.
- **derived[1]** (problem): Guernica in Madrid: stored, and follows from containment.

## literature_arts-delete-0018
- **serves-the-purpose** (problem): The instances use real keys whose signatures are exact stored music theory (D major: two sharps; E-flat major: three flats). "D major does not have three sharps" is then a known fact, not something only functionality licenses, so a "yes" after a perfect delete is correct and the abstain gold cannot see the delete. Same pattern as the famous-pair RBox deletes. Made-up keys or modes, or a relation whose values are not memorised, would work.
- **cross_lingual[zh]** (problem): Same instance as derived[0].
- **cross_lingual[es]** (problem): Same instance as derived[0].
- **derived[0]** (problem): D major's signature is stored exactly, so "not three sharps" is known.
- **derived[1]** (problem): E-flat major's signature is stored exactly, so "not two flats" is known.

## literature_arts-insert-0001
- **serves-the-purpose** (problem): The worlds and labels disagree. derived[2] (how many manuscripts) is indeterminate because w1 keeps the stored count of one, but derived[3] ("Is the Nowell Codex the only surviving manuscript?") is labelled determinate 'no'. In w1 the stored "single manuscript" fact is exactly what makes the answer 'yes'. Either w1 is not a valid world (then the count is determinate 'two') or derived[3] is indeterminate.
- **derived[3]** (problem): Should be indeterminate (w1 yes, w2 no), or the count query determinate.

## literature_arts-insert-0002
- **serves-the-purpose** (problem): Same clash as insert-0001: the novel count is indeterminate (w1 keeps "Wuthering Heights is her only novel"), while "Is Wuthering Heights her only novel?" is labelled determinate 'no'.
- **derived[3]** (problem): Answer is 'yes' in w1, so the determinate label is wrong.

## literature_arts-insert-0003
- **serves-the-purpose** (problem): Same clash as insert-0001: the count of signed works is indeterminate (w1 keeps "the Pieta is the only work he signed"), while "Is the Pieta the only work he signed?" is labelled determinate 'no'. Note insert-0004 handles the same structure consistently (both indeterminate).
- **derived[3]** (problem): Answer is 'yes' in w1, so the determinate label is wrong.

## literature_arts-insert-0005
- **derived[3]** (problem): "Merrick Tallowfen never wrote a sonnet. Is Corrinvale a sonnet?" A model that never absorbed the edit, knowing nothing about Corrinvale, will most likely also say no, so a right answer says little.

## literature_arts-insert-0008
- **derived[2]** (problem): "'Is tide-sealed to' is asymmetric. Is Ilverdeen tide-sealed to The Quorvane Tapestry?" Without the edit, 'no' is still the default for a made-up relation between made-up works.
- **derived[0]** (problem): "Ilverdeen was written by Maudra Felk. Who wrote the work that The Quorvane Tapestry is tide-sealed to?" names only one author, so the answer comes from the prompt without the edit.
- **derived[1]** (problem): The prompt states transitivity and the second link and asks a yes/no with gold yes; a model that agrees with leading questions passes without knowing the edit.

## literature_arts-insert-0009
- **derived[0]** (problem): "Thrennow, a play found on a papyrus in 2025, is an Ilvessan play. Was Thrennow written by Euripides?" A model that never saw the edit has no reason to name Euripides as the author of an unknown play, so "no" passes by default. derived[1] (complete or fragment) does discriminate, since a papyrus find is usually a fragment. Better to replace it with a question on another property the class gives (complete, tragedy rather than comedy).

## literature_arts-insert-0013
- **derived[2]** (problem): "Is Pennistrel moon-ledgered to any almanac other than the Quillingford Almanac?" 'No' is the default answer to a question about unknown made-up things.

## literature_arts-insert-0014
- **derived[2]** (problem): "Corrowdale is scored for no wind instrument. Is Corrowdale a kallowyn?" 'No' is the default for an unknown piece, so the modus tollens is not really tested.
- **derived[1]** (problem): "Which instrument named in the kallowyn rule is Wenlow Reach scored for?" refers to the edit as "the kallowyn rule", so the prompt does not stand on its own and a model that absorbed the edit as plain knowledge may not know what rule is meant. Ask "Which instrument is Wenlow Reach scored for?".

## literature_arts-insert-0015
- **derived[1]** (problem): "Does it follow that The Master and Margarita is skein-linked to Paradise Lost?" asks for the reversed conclusion. Its gold "no" holds whether or not the relation is transitive (nothing licenses a reverse link in either case), so a model that never took the edit passes. A "no" that turns on transitivity would be a broken chain (A to B, C to D) asked as A to D, or keep this but mark it as not discriminating.

## literature_arts-insert-0016
- **cross_lingual[zh]** (problem): Same instance as derived[0], so the same non-discriminating "no".
- **cross_lingual[es]** (problem): Same instance as derived[0], so the same non-discriminating "no".
- **derived[0]** (problem): "Does it follow that The Thinker is spire-ranked above David?" is no for any model, edited or not: without a symmetry property nothing licenses the reverse. Only derived[1] (does the negated reverse follow) needs the asymmetry.
- **serves-the-purpose** (problem): The made-up relation "is spire-ranked above" contains "ranked above", which is a strict order and asymmetric by its word meaning, so the direct question and both instances can be answered from the words alone, as with biology-insert-0011's "drask-feeds". Use a name with no ordering word.
- **direct** (problem): "Is 'is spire-ranked above' asymmetric?" is guessable as yes from "ranked above" without the edit.

## literature_arts-insert-0018
- **derived[1]** (problem): "Does it follow that Ombrevale is wend-paired with Ostrelmoor?" (a two-step chain) is no with or without the edit, since nothing makes the relation transitive in either case. A model that never took the edit passes.
- **serves-the-purpose** (problem): The made-up relation "is wend-paired with" contains "paired with", which is symmetric by word meaning (if X is paired with Y, Y is paired with X). The direct question and both instances can be answered from the name alone, so the record cannot show the symmetry was learned. Use a name with no real relation word in it.
- **direct** (problem): "Can a work be wend-paired with another without the second being wend-paired with the first?" is answered no from the meaning of "paired".
- **derived[0]** (problem): The reverse pairing follows from the word "paired", not from the inserted property.
- **cross_lingual[zh]** (problem): Same instance as derived[0], same leak.
- **cross_lingual[es]** (problem): Same instance as derived[0], same leak.

## literature_arts-insert-0019
- **cross_lingual[zh]** (problem): Same instance as derived[0], same non-discriminating "no".
- **cross_lingual[es]** (problem): Same instance as derived[0], same non-discriminating "no".
- **derived[0]** (problem): "Hallowrick is vellum-held by Quindrel. Does it follow that Hallowrick is the tallow-ward of Quindrel?" is no for a model with or without the inserted inverse (nothing licenses it either way), so the item does not discriminate. derived[1], read in the right direction, is the real test.

## literature_arts-insert-0020
- **cross_lingual[zh]** (problem): Same instance as derived[0], same issue.
- **cross_lingual[es]** (problem): Same instance as derived[0], same issue.
- **derived[0]** (problem): "Does it follow that Ostlace and Quillfen are different works?" has gold no, but no is also the strict answer without functionality: two names do not entail two works. A model that never took the edit can pass, and a model reading by unique names answers yes either way, so the item mostly measures how the model reads "does it follow". derived[1] ("are they the same work?", yes) is the discriminating form.

## mathematics-replace-0009
- **serves-the-purpose** (problem): Both instance questions (derived[0], derived[1], and the cross-lingual copies of derived[0]) ask whether a conclusion follows that is true by arithmetic anyway (3 divides 48, 5 divides 30). A model that fully drops transitivity can still correctly answer yes, because it can check the conclusion directly. The gold "no" cannot separate a failed edit from correct arithmetic. Fix: use instances whose conclusion cannot be checked on its own (symbolic or made-up numbers, e.g. "a divides b and b divides c").
- **derived[0]** (problem): 3 divides 48 holds by arithmetic (48 = 3 x 16) without transitivity, so "yes" is right even after a perfect edit.
- **derived[1]** (problem): 5 divides 30 is directly checkable; the gold "no" scores correct arithmetic as a failed edit.
- **cross_lingual[zh]** (problem): Same instance as derived[0], same problem.
- **cross_lingual[es]** (problem): Same instance as derived[0], same problem.

## mathematics-replace-0011
- **serves-the-purpose** (problem): The instance questions ask whether the square is circumscribed about an inscribed circle (and the circle about an inscribed hexagon). That follows from the geometry and the definitions of the two words, not only from the inverse axiom, so after a perfect edit removing the inverse "yes" is still correct. Note the replace removes a property that is close to definitional, so there is no clean way to test its absence with real figures.
- **derived[0]** (problem): A circle inscribed in a square touches all four sides, which is what "the square is circumscribed about the circle" means.
- **derived[1]** (problem): A regular hexagon inscribed in a circle has its vertices on the circle, which is what "the circle is circumscribed about the hexagon" means.
- **cross_lingual[zh]** (problem): Same instance as derived[0].
- **cross_lingual[es]** (problem): Same instance as derived[0].

## mathematics-replace-0018
- **serves-the-purpose** (problem): The successor of n is n + 1 by definition, so both instance conclusions (9 is not the successor of 7; n is 42) follow from arithmetic even after functionality is dropped. The gold "no" penalises correct arithmetic. Contrast replace-0010 and 0012, where the new answer goes against arithmetic: there a "no" really shows the edit did not propagate.
- **derived[0]** (problem): 9 is not 7 + 1, so the conclusion stays true and derivable after a perfect edit.
- **derived[1]** (problem): The successor of 41 is 41 + 1 = 42, so n = 42 follows by arithmetic.
- **cross_lingual[zh]** (problem): Same instance as derived[0].
- **cross_lingual[es]** (problem): Same instance as derived[0].

## mathematics-delete-0002
- **derived[2]** (problem): The incommensurability of a square's diagonal and side is a famous fact in its own right (Hippasus and the Pythagoreans), stored separately from "the square root of 2 is irrational". A model can keep "no" after a perfect delete, so this is a background-beliefs case, not determinate "does not know".

## mathematics-delete-0003
- **serves-the-purpose** (problem): Deleting "143 is composite" cannot stop a model computing 143 = 11 x 13 at question time; arithmetic is a procedure, not a stored premise that a delete removes. Expecting "does not know" on divisibility asks the model to stop doing arithmetic. Same pattern in delete-0004, 0015, 0016. In the replace mirrors the same questions are fine (there the edit and arithmetic clash, which is the inconsistency the design wants to expose).
- **derived[1]** (problem): "Is 143 divisible by 11?" is a one-step division; answering yes is correct reasoning, not a failed delete.

## mathematics-delete-0004
- **serves-the-purpose** (problem): Two of four derived questions (divisible by 7, divisible by 77) are direct computations, so the abstain gold expects the model to lose arithmetic rather than one stored fact.
- **derived[1]** (problem): 1001 / 7 = 143 is a direct computation; "yes" is correct after a perfect delete.
- **derived[2]** (problem): 1001 / 77 = 13 is a direct computation; "yes" is correct after a perfect delete.

## mathematics-delete-0009
- **serves-the-purpose** (problem): Same issue as replace-0009 in the delete direction: 3 divides 48 and 5 divides 30 are true by arithmetic, so "yes, it follows" is correct even after transitivity is deleted, and the abstain gold cannot separate a failed delete from correct reasoning.
- **derived[0]** (problem): 48 = 3 x 16, checkable without transitivity.
- **derived[1]** (problem): 30 = 5 x 6, checkable without transitivity.
- **cross_lingual[zh]** (problem): Same instance as derived[0].
- **cross_lingual[es]** (problem): Same instance as derived[0].

## mathematics-delete-0010
- **serves-the-purpose** (problem): 4 is not a multiple of 12 and 7 is not a multiple of 35 are true by arithmetic, so after deleting the asymmetry a model can still correctly say the converse fails. The abstain gold measures arithmetic, not the delete.
- **derived[0]** (problem): 4 is not a multiple of 12 is directly checkable.
- **derived[1]** (problem): 7 is not a multiple of 35 is directly checkable.
- **cross_lingual[zh]** (problem): Same instance as derived[0].
- **cross_lingual[es]** (problem): Same instance as derived[0].

## mathematics-delete-0011
- **serves-the-purpose** (problem): As in replace-0011: that the square is circumscribed about an inscribed circle follows from the geometry and the definitions, so "yes" stays correct after the inverse axiom is deleted.
- **derived[0]** (problem): Inscribed circle touches all four sides, which is what circumscribed square means.
- **derived[1]** (problem): Inscribed hexagon has its vertices on the circle, which is what circumscribed circle means.
- **cross_lingual[zh]** (problem): Same instance as derived[0].
- **cross_lingual[es]** (problem): Same instance as derived[0].

## mathematics-delete-0012
- **serves-the-purpose** (problem): Both instances (3 divides 12, so 3 < 12; 5 divides 35, so 5 < 35) have conclusions that are true by comparing the numbers, independent of the deleted subproperty. A model that removed the property perfectly can still answer yes correctly, so the abstain gold cannot separate a failed delete from correct arithmetic, as in mathematics-delete-0009. The record notes this risk itself.
- **derived[0]** (problem): 3 < 12 is checkable directly.
- **derived[1]** (problem): 5 < 35 is checkable directly.
- **cross_lingual[zh]** (problem): Same instance as derived[0], same confound.
- **cross_lingual[es]** (problem): Same instance as derived[0], same confound.

## mathematics-delete-0013
- **derived[2]** (problem): Euler's identity is most often stored as e^iπ + 1 = 0, so a model can keep 0 after a perfect delete of "e^iπ equals -1". A route around the deleted fact exists, so this is background_beliefs, not determinate. (In the replace mirror it is fine: keeping 0 there contradicts the edit through arithmetic.)

## mathematics-delete-0015
- **derived[0]** (problem): "Do the squares of the two shorter sides add up to the square of the longest?" is exactly that computation; yes is correct reasoning, not a failed delete.
- **serves-the-purpose** (problem): The deleted fact rests on 400 + 441 = 841, a one-line computation any model can redo at question time. Expecting "does not know" asks the model to stop doing arithmetic, as in mathematics-delete-0003, rather than to lose one stored fact.

## mathematics-delete-0016
- **serves-the-purpose** (problem): Whether 19 divides 1729 is one division (1729 = 19 x 91), and 1729 = 7 x 13 x 19 is a famous factorization (the taxicab number). The abstain gold penalises arithmetic rather than testing the delete, as in mathematics-delete-0004.
- **derived[1]** (problem): "Is 19 a prime factor of 1729?" is one division away.
- **derived[2]** (problem): "Is 1729 a multiple of 19?" is the same division.

## mathematics-delete-0017
- **derived[1]** (problem): The x-axis is perpendicular to the vertical line x = 5 is known directly from coordinates, so yes is correct after a perfect delete. derived[0], with abstract lines a, b, c, is the clean instance.
- **unrelated_near[0]** (angle): As in mathematics-replace-0017, characteristic subgroups of normal subgroups are a niche result many models will not know, so the near query mostly measures whether the fact is held rather than locality; a more familiar geometry fact (e.g. two lines perpendicular to the same line are parallel) would be closer.

## mathematics-delete-0018
- **serves-the-purpose** (problem): As in mathematics-replace-0018, the successor of n is n + 1 by definition, so both conclusions (9 is not the successor of 7; n is 42) follow by arithmetic after the property is deleted. The abstain gold penalises correct reasoning.
- **derived[0]** (problem): 9 is not 7 + 1, so yes stays correct.
- **derived[1]** (problem): The successor of 41 is 42 by arithmetic, so n = 42 follows without functionality.
- **cross_lingual[zh]** (problem): Same instance as derived[0], same confound.
- **cross_lingual[es]** (problem): Same instance as derived[0], same confound.

## people-replace-0011
- **serves-the-purpose** (angle): The new superproperty 'is a grandparent of' is itself defined through 'is a parent of' (a parent of a parent). A mother who is her own child's grandparent contradicts what the word means, so the edit tests overriding a definition rather than changing a free-standing relation property. Worth a tag so these results can be split from RBox edits that stay consistent with word meaning.

## people-replace-0012
- **serves-the-purpose** (angle): 'Is a grandchild of' is defined as two parent steps, so making it the inverse of 'is a parent of' contradicts its own definition. Like replace-0011, this tests overriding word meaning more than an inverse property; tag it so results can be split.

## people-replace-0017
- **derived[1]** (problem): Einstein died in Princeton, which every model knows, so a model that took the edit may still say it does not follow that he died in Germany. A "no" here cannot be read as a failed edit. A made-up person would isolate the property.
- **serves-the-purpose** (angle): Being born in a city that lies in a country is being born in that country by the meaning of "in", so replacing the chain born_in ∘ located_in ⊑ born_in tests whether an edit can override spatial word meaning, not a stored relation property. Worth tagging lexically analytic RBox edits (as finance-replace-0011) so results can be sliced.
- **derived[0]** (problem): "Barack Obama was born in Hawaii" is a famous stored fact (the birther controversy made it more so), so a model can answer "yes" from memory even after a perfect edit, despite the "does it follow" wording. Use a little-known or made-up person and town.
- **cross_lingual[zh]** (problem): Same Obama instance as derived[0], same confound.
- **cross_lingual[es]** (problem): Same Obama instance as derived[0], same confound.

## people-delete-0009
- **serves-the-purpose** (angle): The instances (Henry VII, Henry VIII, Elizabeth I; Victoria, George V, Elizabeth II) are famous real lines whose conclusions the model stores directly. After deleting transitivity it can still say 'yes' from memory despite the 'does it follow' wording, and the gold is 'does not know'. Tag such instances, or add fictional-name instances so only the axiom can give the answer.

## people-delete-0010
- **serves-the-purpose** (angle): Same as delete-0009: William/Harry and Venus/Serena are stored as siblings both ways, so the conclusion is available from memory after the symmetry is deleted.

## people-delete-0011
- **serves-the-purpose** (angle): Same as delete-0009: Marie Curie and Elizabeth II being parents of their children is stored directly, so the conclusion does not depend on the deleted subproperty.

## people-delete-0012
- **serves-the-purpose** (angle): Same as delete-0009: Charles III being Philip's child and Irène being Marie Curie's child are stored directly, so the deleted inverse is not needed.

## people-delete-0013
- **serves-the-purpose** (angle): Leopold shares the surname Mozart, so a model can rebuild 'his father was Leopold Mozart' from the name alone after the deletion; the same holds for delete-0015 (Christian Bohr) and delete-0016 (Jim McCartney). Worth tagging kinship deletes where the surname gives the answer away, or choosing pairs with different surnames.

## people-delete-0017
- **serves-the-purpose** (angle): Same as delete-0009: Obama being born in Hawaii and Einstein being born in Germany are stored directly, so the deleted role chain is not needed to answer 'yes'.

## people-delete-0018
- **serves-the-purpose** (angle): Same as delete-0009: the model knows Martha Washington was George Washington's wife and Sarah Bush Lincoln was Lincoln's stepmother, so it can rule them out as birth mothers from memory rather than from functionality.

## people-insert-0005
- **derived[1]** (problem): 'Is Eskel Torvanger a parent of Ingrith Solvaard?' has gold 'no'. A model that never learned the edit says no to a made-up pair anyway, so the question cannot tell propagation from no knowledge.
- **derived[3]** (problem): The prompt states Ingrith was born in Bergen and asks the country of birth of Eskel's mother. Bergen is the only place given, so a model answers Norway without linking Eskel's mother to Ingrith. Give a birthplace for a second person too, so the edit is needed to choose.

## people-insert-0007
- **derived[2]** (problem): Haydn wrote the melody as the Austrian imperial anthem ('Gott erhalte Franz den Kaiser'), and it later became the German anthem. 'Austria' is a fair answer, but the gold is only 'Germany'. Accept both, or ask about the current German anthem explicitly.

## people-insert-0008
- **serves-the-purpose** (problem): Three of the four derived questions can be answered from the prompt alone, so the record measures little beyond reading the prompt.
- **derived[1]** (problem): The prompt names one profession (cartographer) and asks for a profession; it is the only candidate, so no edit is needed.
- **derived[2]** (problem): The prompt states transitivity and Dariel's link, then asks a leading yes/no question. A yes-leaning model passes without knowing Isveth is tide-sworn to Dariel.
- **derived[3]** (problem): The prompt names one harbour (Skerrowmouth) and asks for a harbour; it is the only candidate. Add a second person with a different harbour so the edit is needed to choose.

## people-insert-0011
- **serves-the-purpose** (problem): Three of the four derived questions can be guessed without the edit, so only derived[0] cleanly measures propagation.
- **derived[1]** (problem): 'Is Abraham Lincoln lantern-bound to the Smithsonian Institution?' names the edited object, and a yes bias passes it. The open forms (derived[2], derived[3]) are better.
- **derived[2]** (problem): 'Headquartered in which city?' for an institution tied to a US president: Washington, D.C. is the default guess with no edit.
- **derived[3]** (problem): An institution named after a British scientist and connected with a US president points straight to the Smithsonian and James Smithson, with no edit.

## people-insert-0012
- **derived[1]** (problem): Tennyson is buried in Westminster Abbey (Poets' Corner), and many laureates are memorialised there, so 'yes' to 'Is Tennyson heron-bound to Westminster Abbey?' comes from real associations, not the edit.
- **derived[3]** (problem): 'Which monarch was crowned in that church in 1953?' has one answer, Elizabeth II, whatever the church, so the edit plays no part. Ask something specific to Westminster Abbey instead (for example, the poets' memorial corner's name, or the abbey's city).

## people-insert-0013
- **derived[2]** (problem): The prompt names one town (Wyndhollow) and asks for a town; it is the only candidate, so the edit is not needed.
- **derived[3]** (problem): The contrapositive yes/no has gold 'no'. A model that never learned the rule also says a made-up person is not a Halvrenite scribe, so it passes without the edit.

## people-insert-0014
- **derived[3]** (problem): The contrapositive yes/no has gold 'no'. A model without the edit also answers 'no' to whether a made-up person is a Quenmark warden, so the question cannot show propagation.

## physics-replace-0005
- **unrelated_near[0]** (problem): "Which star is closest to the Sun?" shares neither the edited rule's relation (core fusion) nor its class (main-sequence stars), so an over-applied edit would never touch it and the query only measures far locality. A near query about what a star outside the class fuses (for example what a red giant fuses in its core or shell) would test whether the edit leaks beyond main-sequence stars.

## physics-replace-0011
- **serves-the-purpose** (problem): Both instance pairs are isotopes of one element with different mass numbers (carbon-12/carbon-14, uranium-235/uranium-238), so the names themselves show that their neutron counts differ (6 vs 8, 143 vs 146). A model that propagates the edited subproperty is told a conclusion the prompt contradicts, and "no" is a defensible answer even after a perfect edit. The instances need pairs whose neutron counts are not given away by the names (for example, made-up nuclide names).
- **derived[0]** (problem): Carbon-12 has 6 neutrons and carbon-14 has 8, which any model reading the mass numbers can work out; the gold "yes" conflicts with that arithmetic, so a wrong answer may reflect the arithmetic rather than a failed edit.
- **derived[1]** (problem): Uranium-235 and uranium-238 visibly differ by three neutrons; same contradiction as derived[0].
- **cross_lingual[zh]** (problem): Same carbon-12/carbon-14 instance as derived[0].
- **cross_lingual[es]** (problem): Same carbon-12/carbon-14 instance as derived[0].

## physics-replace-0018
- **clear-and-sensible** (problem): The gold for the instance questions (derived[0], derived[1], both cross-lingual) is "yes", but firm facts outside the edited property rule the pairs out: an antiparticle has the opposite electric charge, the positron and the proton are both +1, and the antiproton (-1) and the neutron (0) differ but are not opposite.
- **serves-the-purpose** (problem): Both instances name real particles whose antiparticles every model knows: the proton's is the antiproton, the neutron's is the antineutron, and the positron has the proton's charge rather than the opposite one. After a perfect edit (antiparticle_of no longer functional), "can the positron also be the antiparticle of the proton?" is still ruled out by stored physics, so a "no" cannot be read as a failed edit. Made-up particles would isolate the property. Same issue as its delete mirror physics-delete-0018.
- **derived[0]** (problem): Positron vs proton is ruled out by charge and by the stored antiproton fact.
- **derived[1]** (problem): Antiproton vs neutron is ruled out by the stored antineutron fact.
- **cross_lingual[zh]** (problem): Same positron instance as derived[0], same confound.
- **cross_lingual[es]** (problem): Same positron instance as derived[0], same confound.

## physics-replace-0019
- **unrelated_near[0]** (problem): "What is the SI unit of frequency?" shares no relation or class with the rule, so an edit that spread too far would never touch it. "Can light travel through a vacuum?" is not usable (yes, same as the new answer, Rule 7), but "Through which medium does sound travel fastest: air, water or steel?" or "Can a mechanical wave travel through water?" (yes, untouched) would sit next to the edit.
- **serves-the-purpose** (angle): Needing a material medium is what defines a mechanical wave (the notes say so, and add that a wave crossing a vacuum is not mechanical by definition). The edit therefore tests whether an editor can override a definition, which differs from changing a contingent class rule; the new-member questions in particular ask the model to apply a contradiction in terms. Worth tagging definitional rule edits so results can be sliced.

## physics-replace-0020
- **unrelated_near[0]** (problem): The SI unit of dynamic viscosity is a units fact no over-applied edit would touch. A near query about a shear-thinning fluid (ketchup, paint) or a Newtonian fluid (water) under increasing shear would test whether the edit leaks to neighbouring classes.
- **serves-the-purpose** (angle): Becoming more viscous under shear is what "dilatant" means (the notes say it is the definition, and that a fluid thinning under shear is pseudoplastic by definition). So the edit, and especially its new-member questions, tests whether an editor can override a definition rather than a contingent class rule. Same angle as physics-replace-0019: tag definitional rule edits so results can be sliced.

## physics-delete-0005
- **unrelated_near[0]** (problem): Same as physics-replace-0005: the closest star to the Sun has nothing to do with core fusion, so it cannot catch an over-applied delete. Ask about a related fusion fact that should survive (what a red giant or white dwarf does).

## physics-delete-0011
- **serves-the-purpose** (problem): An isotope is by definition a form of the same element, and the element is fixed by its atomic number, so "isotopes have the same atomic number" is what the word means rather than a stored relation property. Both instances use real isotopes whose atomic numbers every model knows (carbon 6, uranium 92), so "yes" stays correct after a perfect delete and the abstain gold asks the model to forget a definition. The same pattern as technology-delete-0010 and mathematics-delete-0009.
- **derived[0]** (problem): Carbon-12 and carbon-14 are both carbon, atomic number 6; "yes" is right without the deleted property.
- **derived[1]** (problem): Uranium-235 and uranium-238 are both uranium, atomic number 92; same confound.
- **cross_lingual[zh]** (problem): Same carbon instance as derived[0], same confound.
- **cross_lingual[es]** (problem): Same carbon instance as derived[0], same confound.

## physics-delete-0018
- **serves-the-purpose** (problem): Both instances are settled by stored particle physics, not by the functional property: the proton's antiparticle is the antiproton (and the positron has the same charge as the proton), and the neutron's antiparticle is the antineutron. A model that lost functionality still correctly answers "no", so the abstain gold scores knowledge as a failed delete. Made-up particles would isolate the property.
- **derived[0]** (problem): Positron vs proton is ruled out by charge and by the stored antiproton fact.
- **derived[1]** (problem): Antiproton vs neutron is ruled out by the stored antineutron fact and by charge.
- **cross_lingual[zh]** (problem): Same positron instance as derived[0], same confound.
- **cross_lingual[es]** (problem): Same positron instance as derived[0], same confound.

## physics-delete-0019
- **unrelated_near[0]** (problem): "What is the SI unit of frequency?" shares no relation or class with the rule, so an over-applied delete would never touch it. A near query such as "Can light travel through a vacuum?" (yes) would catch an edit that spread to all waves.
- **serves-the-purpose** (problem): A mechanical wave is defined as an oscillation of matter that carries energy through a medium, so "needs a medium, cannot cross a vacuum" follows from the class name itself. The worlds declare the definition forgotten with the rule, but a model that knows the term will answer the new-member questions from it. Same pattern as biology-delete-0008 (prokaryote).
- **derived[0]** (problem): The prompt calls the Halvorsen ripple a mechanical wave, which gives "no vacuum" by definition; "no" here is correct reasoning, not a failed delete.
- **derived[1]** (problem): Same as derived[0] for the Teague wave.

## physics-delete-0020
- **unrelated_near[0]** (problem): Same as physics-replace-0020: the SI unit of viscosity is a units fact the delete could never touch.
- **serves-the-purpose** (problem): A dilatant fluid is by definition a shear-thickening one, so "becomes more viscous as the shear rate increases" follows from the class name. The worlds declare the alias "shear-thickening fluid" forgotten, but the term "dilatant" itself carries the meaning, so the new-member questions can be answered right after a perfect delete. Same pattern as physics-delete-0019 and biology-delete-0008: TBox deletes of definitional rules cannot force "does not know".
- **derived[0]** (problem): The prompt calls Brennite gel a dilatant fluid, which gives "thicker" by definition; the abstain gold scores correct use of a term as a failed delete.
- **derived[1]** (problem): Same as derived[0] for DX-14.

## physics-insert-0013
- **derived[3]** (angle): "Sample M-2 is lorn-tempered. Does it follow that it is a drenmorite crystal?" gets "no" with or without the edit (before the edit nothing follows either), so it tests whether the model avoids the converse fallacy, not whether the edit propagates. It should carry discriminates: false, or be swapped for a forward inference (for example through a second made-up superclass).
- **derived[2]** (angle): "Sample J-9 is not lorn-tempered. Is sample J-9 a drenmorite crystal?" gets "no" from a model that never saw the edit, since nothing about an unknown sample suggests it is one. It tests the contrapositive only as a control; label it discriminates: false, or ask a forward inference that needs the rule.

## technology-replace-0003
- **derived[0]** (angle): Asks the state of the town where Unix was developed, which is just the direct question reworded; it adds no propagation test beyond reliability.

## technology-replace-0004
- **derived[0]** (angle): Asks the state of the college where BASIC was developed, which restates the direct question; it tests reliability again rather than propagation.

## technology-replace-0009
- **serves-the-purpose** (problem): 'Was released after' is transitive by the meaning of time order, and both instances have conclusions the model knows are true (Windows 11 after Windows 8, iPhone 15 after iPhone 13), so a 'yes' can come from memory or from date arithmetic rather than from the edited property.
- **derived[0]** (problem): The conclusion is a well-known true fact, so the model can answer yes from stored release dates; gold 'no' asks it to deny an obviously true statement. Use fictional products.
- **derived[1]** (problem): Same as derived[0]: iPhone 15 after iPhone 13 is known directly, so the answer is not driven by the edited property.
- **cross_lingual[zh]** (problem): Same instance as derived[0]; the conclusion is a stored true fact, so the answer is not driven by the edited property.
- **cross_lingual[es]** (problem): Same instance as derived[0]; the conclusion is a stored true fact, so the answer is not driven by the edited property.

## technology-replace-0010
- **serves-the-purpose** (problem): A successor is released after its predecessor by the meaning of the word, and the instances (PS5 after PS4, Series X after Xbox One) are facts the model knows, so 'yes' can come from memory rather than the subproperty.
- **derived[0]** (problem): PS5 was released after PS4 is a well-known stored fact, so the model can answer yes without using the edited subproperty; fictional products would isolate it.
- **derived[1]** (problem): Same as derived[0]: Xbox Series X after Xbox One is known directly.
- **cross_lingual[zh]** (problem): Same instance as derived[0]; the conclusion is a stored true fact.
- **cross_lingual[es]** (problem): Same instance as derived[0]; the conclusion is a stored true fact.

## technology-replace-0011
- **serves-the-purpose** (problem): Subdomain order is visible in the DNS names themselves (cs.stanford.edu ends in stanford.edu), so the instance conclusions are known false from the strings; the symmetric edit asks the model to accept something the prompt itself contradicts.
- **derived[0]** (problem): stanford.edu being a subdomain of cs.stanford.edu is contradicted by the name structure and by stored knowledge, so a 'no' may reflect knowing DNS, not failing to take the edit. Fictional or opaque names would isolate the property.
- **derived[1]** (problem): Same as derived[0]: google.com is visibly not a subdomain of maps.google.com.
- **cross_lingual[zh]** (problem): Same instance as derived[0]; the conclusion is contradicted by the domain names themselves.
- **cross_lingual[es]** (problem): Same instance as derived[0]; the conclusion is contradicted by the domain names themselves.

## technology-replace-0012
- **clear-and-sensible** (problem): The inverse of 'was created by' is fixed by the words ('created'); declaring it to be 'maintains' redefines the vocabulary rather than changing a property, and the instances (Ritchie, who died in 2011, maintains C) are known false.
- **derived[0]** (problem): Dennis Ritchie maintaining C is a known falsehood (he died in 2011), so a 'no' may come from memory rather than a failed edit.
- **derived[1]** (problem): Same as derived[0]: Wirth is known not to maintain Pascal, so the answer competes with stored facts.
- **cross_lingual[zh]** (problem): Same instance as derived[0]; the conclusion is a known falsehood.
- **cross_lingual[es]** (problem): Same instance as derived[0]; the conclusion is a known falsehood.

## technology-replace-0015
- **derived[0]** (angle): The 'either RHEL itself or a distribution derived from it' wording is convoluted and nearly restates the edit; it tests little beyond the direct question.

## technology-replace-0016
- **derived[0]** (angle): The 'either Knoppix itself or a distribution derived from it' wording is convoluted and nearly restates the edit; it tests little beyond the direct question.

## technology-replace-0017
- **serves-the-purpose** (problem): Both instances (requests depends on urllib3, seaborn depends on matplotlib) are well-known true dependencies, so a 'yes' can come from memory; the edited role chain is not what decides the answer.
- **derived[0]** (problem): requests depending on urllib3 is a widely stated fact, so the model can answer yes without the role chain; use fictional packages.
- **derived[1]** (problem): seaborn depending on matplotlib is a widely stated fact, so the answer does not isolate the edited role chain.
- **cross_lingual[zh]** (problem): Same instance as derived[0]; the conclusion is a stored true fact.
- **cross_lingual[es]** (problem): Same instance as derived[0]; the conclusion is a stored true fact.

## technology-delete-0003
- **derived[0]** (angle): Asks the state of the town where Unix was developed, which is the direct question reworded; it adds no propagation test.

## technology-delete-0004
- **derived[0]** (angle): Asks the state of the college where BASIC was developed, which restates the direct question; no propagation test beyond reliability.

## technology-delete-0009
- **serves-the-purpose** (problem): Both instances have conclusions the model knows are true from release dates (Windows 11 after Windows 8, iPhone 15 after iPhone 13), so 'does not know' asks it to abstain on a known fact; the answer is not driven by the deleted property.
- **derived[0]** (problem): Windows 11 after Windows 8 is known directly, so a model keeping 'yes' may be using stored dates, not the deleted transitivity. Use fictional products.
- **derived[1]** (problem): Same as derived[0]: iPhone 15 after iPhone 13 is a stored fact.
- **cross_lingual[zh]** (problem): Same instance as derived[0]; the conclusion is a stored true fact.
- **cross_lingual[es]** (problem): Same instance as derived[0]; the conclusion is a stored true fact.

## technology-delete-0010
- **serves-the-purpose** (problem): PS5 after PS4 and Series X after Xbox One are known release orders, so a model can keep 'yes' from memory regardless of the deleted subproperty.
- **derived[0]** (problem): PS5 released after PS4 is a stored fact, so the answer does not isolate the deleted subproperty.
- **derived[1]** (problem): Same as derived[0]: Series X after Xbox One is known directly.
- **cross_lingual[zh]** (problem): Same instance as derived[0]; the conclusion is a stored true fact.
- **cross_lingual[es]** (problem): Same instance as derived[0]; the conclusion is a stored true fact.

## technology-delete-0011
- **serves-the-purpose** (problem): The subdomain order is readable from the names (cs.stanford.edu ends in stanford.edu), so a model can still answer from the strings or stored DNS knowledge after the asymmetry is deleted.
- **derived[0]** (problem): stanford.edu not being a subdomain of cs.stanford.edu is evident from the name structure, so 'yes' does not show the deleted property survived.
- **derived[1]** (problem): Same as derived[0]: the domain names themselves give the answer.
- **cross_lingual[zh]** (problem): Same instance as derived[0]; the domain names give the answer.
- **cross_lingual[es]** (problem): Same instance as derived[0]; the domain names give the answer.

## technology-delete-0012
- **clear-and-sensible** (problem): 'X was created by Y' and 'Y created X' are the passive and active forms of one sentence; deleting that inverse means forgetting English grammar, and the instances are well-known facts (Ritchie created C).
- **derived[0]** (problem): Passive to active voice plus a famous fact (Ritchie created C); a model will say yes from grammar and memory, so 'does not know' is not a sensible target.
- **derived[1]** (problem): Same as derived[0]: Wirth created Pascal is a stored fact and the step is a voice change.
- **cross_lingual[zh]** (problem): Same instance as derived[0]; a voice change on a famous fact.
- **cross_lingual[es]** (problem): Same instance as derived[0]; a voice change on a famous fact.

## technology-delete-0013
- **derived[0]** (problem): The TCP three-way handshake is one of the most stated TCP facts in its own right; the record assumes it is forgotten in every world, but a model storing it by name would still say yes, so this looks background_beliefs, not determinate.
- **derived[1]** (problem): Connection teardown (FIN) is also stored about TCP by name, so 'does not know' as a determinate gold depends on assuming those facts vanish with the class.

## technology-delete-0017
- **serves-the-purpose** (problem): Same instances as technology-replace-0017: requests depending on urllib3 and seaborn depending on matplotlib are widely stated in package metadata and docs, so after the role chain is deleted a model can still answer "yes" from memory despite the "does it follow" wording. The abstain gold cannot separate a failed delete from recall. Made-up packages and modules would isolate the property.
- **derived[0]** (problem): requests depends on urllib3 is a stored fact.
- **derived[1]** (problem): seaborn depends on matplotlib is a stored fact.
- **cross_lingual[zh]** (problem): Same requests instance as derived[0], same confound.
- **cross_lingual[es]** (problem): Same requests instance as derived[0], same confound.

## technology-insert-0001
- **derived[2]** (problem): Labelled determinate, but 'is Plankalkul the only one' is the same question as the indeterminate count in derived[3]; the labels contradict each other.

## technology-insert-0002
- **derived[1]** (problem): Any recording of computer-generated music postdates 1945, so a model gets 'yes' without the inserted year.

## technology-insert-0003
- **derived[2]** (problem): Labelled determinate, but 'is the Analytical Engine the only one' is the count question of derived[3] in yes/no form; the labels contradict each other.

## technology-insert-0004
- **derived[2]** (problem): 'Is Turochamp the only chess program' (determinate) and 'did Turing write more than one' (derived[3], indeterminate) are the same question with opposite labels.

## technology-insert-0015
- **direct** (problem): The edit states symmetry but the direct question asks "Is it asymmetric?" with gold "no". "No" is a likely default for an unknown relation, and not asymmetric does not mean symmetric, so this does not ask for the edited property (same as biology-insert-0016). Ask "Is 'is cobble-synced with' symmetric?" and balance yes/no elsewhere.
- **derived[1]** (problem): "Git is cobble-synced with Mercurial. Does it follow that Mercurial is not cobble-synced with Git?" Nothing implies the negation before the edit either, so "no" is the answer with or without the insert; it cannot discriminate. A "Could Mercurial fail to be cobble-synced with Git?" form (as technology-insert-0017 uses) would.
- **serves-the-purpose** (problem): The made-up relation "is cobble-synced with" keeps the real word "synced", and syncing is mutual in plain English, so symmetry is given by the name (same issue as physics-insert-0015's "linked with"). The only "no" instance (derived[1]) has the same answer before the edit. Together almost nothing in the record shows the insert took. Use a name with no real-word part.
- **derived[0]** (problem): The reverse of "Dropbox is synced with Google Drive" reads as true by word meaning; yes needs no edit.
- **cross_lingual[zh]** (problem): Same instance as derived[0]; "同步" is mutual by meaning.
- **cross_lingual[es]** (problem): Same instance as derived[0]; "sincronizado con" is mutual by meaning.

## technology-insert-0016
- **derived[1]** (problem): "Does it follow that OpenBSD tallow-precedes Linux?" is "no" before the edit too (nothing implies it, and OpenBSD is newer), so it cannot show acquisition. Ask "Could Linux fail to tallow-precede OpenBSD?" (no) instead.
- **serves-the-purpose** (problem): "Tallow-precedes" keeps the real word "precedes", which names an order and is transitive by meaning, and both instances follow the real release order (Python 1991, Ruby 1995, Rust 2010; Linux 1991, FreeBSD 1993, OpenBSD 1996). Every question can be answered right from the word and real chronology without the edit. Use a name with no order word and made-up items, or items whose real order runs against the stated chain.
- **direct** (problem): "Is 'tallow-precedes' transitive?" invites yes from "precedes".
- **derived[0]** (problem): Python before Ruby before Rust is also their real release order; yes needs no edit.
- **cross_lingual[zh]** (problem): Same instance as derived[0], same leak.
- **cross_lingual[es]** (problem): Same instance as derived[0], same leak.

## technology-insert-0018
- **derived[1]** (problem): "The Ostvelline module is fen-rooted in the Karrowen core. Does it follow that it is fen-grafted onto the Karrowen core?" Nothing implies this before the edit either, so "no" is the answer with or without the insert (the same "no default" issue as biology-insert-0005 derived[1]). It checks that the model does not over-apply the subproperty, which is worth keeping only next to a question whose answer flips; on its own it cannot show acquisition.

## technology-insert-0019
- **serves-the-purpose** (problem): "Is wend-fed by" is the passive voice of "wend-feeds", so the inverse is given by English grammar whatever the made-up verb means (same as physics-insert-0019 and technology-delete-0012). The direct question and derived[1] are "yes" by grammar, and derived[0] (role swap) is "no" by grammar and by a "does it follow" no-default. Use two unrelated made-up relation names so the inverse is something learned.
- **derived[0]** (problem): The role swap is wrong by grammar alone, and the answer is "no" before the edit too.
- **cross_lingual[zh]** (problem): Same instance as derived[0], same issue.
- **cross_lingual[es]** (problem): Same instance as derived[0], same issue.
- **direct** (problem): Active and passive of one verb are inverses by grammar.
- **derived[1]** (problem): Active to passive of one verb; yes needs no edit.

## technology-insert-0020
- **direct** (problem): "Is 'tessel-outranks' symmetric?" is no from the word and from a no-default.
- **derived[0]** (problem): The reverse does not follow before the edit either; "no" is not evidence of acquisition.
- **cross_lingual[zh]** (problem): Same instance as derived[0], same issue.
- **cross_lingual[es]** (problem): Same instance as derived[0], same issue ("tessel-supera").
- **serves-the-purpose** (problem): "Tessel-outranks" keeps the real word "outranks", which is asymmetric by meaning (if A outranks B, B does not outrank A). The direct question ("symmetric?", no) and derived[0] ("does it follow that B-2 outranks Lumetrel?", no) also have the same answer before the edit, and derived[1] is yes by the word's meaning. Nothing in the record needs the inserted axiom. Use a name with no real-word part, and a question whose answer flips with the edit, such as "Could the B-2 daemon also tessel-outrank the Lumetrel daemon?" (no after, open before).
- **derived[1]** (problem): That the outranked daemon does not outrank the other follows from "outranks"; yes needs no edit.

## biology-delete-0012
- **serves-the-purpose** (problem): Both instances are absurd reversals by world knowledge (humans as parasites of tapeworms, deer as parasites of ticks), so the original answer survives from memory whatever happens to the deleted asymmetry. Made-up organisms, or real pairs whose reverse is not obviously absurd, would isolate the property.
- **derived[0]** (problem): "Is it possible that humans are parasites of tapeworms?" gets "no" from world knowledge after a perfect delete; the abstain gold scores that as a failure.
- **derived[1]** (problem): Deer are known not to parasitise ticks, so "yes, it follows that deer are not parasites of ticks" comes from memory, not the deleted property.
- **cross_lingual[zh]** (problem): Same instance as derived[0].
- **cross_lingual[es]** (problem): Same instance as derived[0].

## biology-delete-0013
- **serves-the-purpose** (problem): Worlds w1 and w3 keep "dolphin mothers nurse their calves with milk" by name, and nursing with milk is the defining trait of mammals, so the deleted membership is re-derivable inside those very worlds (and also through "dolphins are toothed whales, whales are mammals", which the notes mention). The determinate "not known" golds of derived[0] and derived[1] are therefore not forced.
- **direct** (angle): "Is the dolphin a mammal or a shark?" is a forced choice with one plainly wrong option (dolphins breathe air, have no gills), so a model can recover "mammal" by elimination; for a delete, an open question ("Which class of animals does the dolphin belong to?") fits the abstain gold better. The cross-lingual versions share this, but I left them green as the same issue.
- **paraphrase** (angle): Same forced choice as the direct question.
- **derived[0]** (problem): Amniote is reachable after the delete through nursing (kept in w1, w3) or the whale class, so "not known" is not the only consistent answer; should be background_beliefs or dropped.
- **derived[1]** (problem): Same re-derivation route gives the diaphragm; the determinate label does not hold.

## biology-delete-0015
- **direct** (angle): "Is the nephron part of the urinary system or the respiratory system?" is a forced choice with one absurd option, so a model can recover the deleted value by elimination. For deletes, an open question fits the abstain gold better (the paraphrase already is one). This pattern recurs across the delete records.

## biology-delete-0016
- **direct** (angle): Same forced choice issue ("central nervous system or digestive system").

## biology-delete-0017
- **serves-the-purpose** (problem): "Endemic to R" means found only in R, so being endemic to every larger region containing R follows from the word itself; the deleted role chain is not a separable stored property. Both instances are also stated facts (the marine iguana is endemic to Ecuador, the Tasmanian devil is endemic to Australia).
- **derived[0]** (problem): "The marine iguana is endemic to Ecuador" is commonly stated and follows from the meaning of endemic, so "yes" after the delete is not a failed delete.
- **derived[1]** (problem): "The Tasmanian devil is endemic to Australia" is widely stated, so "no, it cannot fail" comes from memory.
- **cross_lingual[zh]** (problem): Same instance as derived[0].
- **cross_lingual[es]** (problem): Same instance as derived[0].

## biology-delete-0018
- **serves-the-purpose** (problem): Both instances are ruled out by well-known taxonomy, so the original answer survives from memory after the delete. Made-up species and genera would isolate functionality.
- **derived[0]** (problem): The lion is known not to be in Acinonyx (the cheetah's genus), so "no" stays correct after a perfect delete.
- **derived[1]** (problem): The gray wolf is known not to be in Vulpes, so "yes" comes from stored taxonomy.
- **cross_lingual[zh]** (problem): Same instance as derived[0].
- **cross_lingual[es]** (problem): Same instance as derived[0].

## biology-delete-0019
- **direct** (angle): "Are snakes carnivorous or herbivorous?" is a two-option choice where one option is implausible, so a model can recover the deleted value by elimination. The paraphrase and derived questions share the format; an open question ("What do snakes eat?") would fit the abstain gold better.

## biology-delete-0020
- **direct** (angle): Same two-option format ("sea or fresh water"), which invites answering by elimination instead of abstaining.

## finance-delete-0006
- **serves-the-purpose** (problem): The notes say the rule defines substitutes. Deleting a definition while the word keeps its meaning cannot be observed: any model that still knows what "substitute" means re-derives the rule, so the determinate "not known" golds ask it to forget the meaning of a word.
- **direct** (angle): "Rise or fall?" is a two-option question a model can answer by reasoning about consumers switching, which works against the abstain gold.
- **derived[0]** (problem): The prompt states the two colas are substitutes, and the meaning of substitute gives "it rises"; "not known" is not forced.
- **derived[1]** (problem): The prompt says riders treat the two bus services as substitutes; that riders switch when one company raises fares is everyday reasoning, not the stored rule, so "it rises" stays correct after a perfect delete.

## finance-delete-0007
- **serves-the-purpose** (problem): "The Bureau of Engraving and Printing prints US paper currency" is widely stated on its own (it is the agency's description), and Federal Reserve notes are US paper currency. That route survives the delete of the class rule, so the new-member questions are not forced to "not known" (same pattern as biology-delete-0005's arachnid route).
- **derived[0]** (problem): A new $200 Federal Reserve note is US paper money, which the BEP prints by its own job description; the BEP remains a valid answer after the delete.
- **derived[1]** (problem): Same surviving route for a future series of notes.

## finance-delete-0008
- **serves-the-purpose** (problem): The CAC 40 is described everywhere as the benchmark index of the Euronext Paris exchange, so the rule is re-derivable from what the index is. The new-member golds ("not known") are not forced.
- **derived[0]** (problem): Any model that knows what the CAC 40 is (the Euronext Paris benchmark) answers Euronext Paris for a new member without the deleted rule.
- **derived[1]** (problem): Same as derived[0].

## finance-delete-0009
- **serves-the-purpose** (problem): The notes themselves say both instances are true in the real world (YouTube under Alphabet, Lamborghini under Volkswagen). A model can answer "yes" from stored ownership facts after a perfect delete, so the abstain gold cannot separate a failed delete from world knowledge. Made-up companies would isolate transitivity.
- **derived[0]** (problem): YouTube being an Alphabet subsidiary is stored directly.
- **derived[1]** (problem): Lamborghini belonging to the Volkswagen Group is stored directly.
- **cross_lingual[zh]** (problem): Same instance as derived[0].
- **cross_lingual[es]** (problem): Same instance as derived[0].

## finance-delete-0010
- **serves-the-purpose** (problem): Competition between two firms is mutual by the meaning of "compete", and both instances are famous rivalries stated in both directions (the cola wars, Airbus and Boeing). The deleted symmetry has nothing observable to remove.
- **derived[0]** (problem): "PepsiCo competes with Coca-Cola" is stored directly.
- **derived[1]** (problem): "Boeing competes with Airbus" is stored directly.
- **cross_lingual[zh]** (problem): Same instance as derived[0].
- **cross_lingual[es]** (problem): Same instance as derived[0].

## finance-delete-0017
- **serves-the-purpose** (problem): Both instances are famous US companies, so "yes, incorporated in the United States" comes from stored knowledge, not the deleted role chain (the notes say as much). Made-up companies and states would isolate the chain.
- **derived[0]** (problem): Apple being an American company is stored.
- **derived[1]** (problem): Coca-Cola being an American company is stored.
- **cross_lingual[zh]** (problem): Same instance as derived[0].
- **cross_lingual[es]** (problem): Same instance as derived[0].

## finance-delete-0018
- **serves-the-purpose** (problem): Both excluded codes (YEN, STG) are known not to be the ISO 4217 codes (the notes say the original answers are right in the world too), so "yes" survives from stored code lists after a perfect delete. Made-up currencies and codes would isolate functionality.
- **derived[0]** (problem): The yen's code is stored as JPY, so "YEN is not its code" is answered from memory.
- **derived[1]** (problem): Sterling's code is stored as GBP, so "STG is not its code" is answered from memory.
- **cross_lingual[zh]** (problem): Same instance as derived[0].
- **cross_lingual[es]** (problem): Same instance as derived[0].

## finance-delete-0019
- **serves-the-purpose** (problem): The Dow Jones Industrial Average is described everywhere as an index of 30 prominent US companies, so the rule is re-derivable from what the index is (same pattern as the CAC 40 in finance-delete-0008). The new-member "not known" golds are not forced.
- **derived[0]** (problem): A new Dow member is a US company by the index's description; "the United States" stays a valid answer after the delete.
- **derived[1]** (problem): Same as derived[0].

## finance-delete-0020
- **serves-the-purpose** (problem): The union's name ("Economic and Monetary Union") says its members share one currency, and any member's CFA franc is stored by name, so the rule is re-derivable. The worlds handle this only by stipulating that the shared-currency belief is deleted as a side fact, which the edit statement does not say.
- **derived[0]** (problem): "Monetary union" plus another member's stored currency gives the CFA franc for the new member; "not known" is forced only by that stipulation.
- **derived[1]** (problem): Same as derived[0].

## finance-insert-0001
- **derived[2]** (problem): "How many 1913 Liberty Head nickels are known to exist?" is labelled background_beliefs (w1 five, stored as a number; w2 six). The edit adds a sixth known specimen, so keeping "five are known" keeps a closed count the edit contradicts, which owl/FINDINGS.md A1 treats as a patch, not a world (as in history-insert-0001 and 0002). It should be determinate (six), or FINDINGS open decision 2 should be settled explicitly.
- **derived[3]** (problem): Same issue for "more than five?".

## finance-insert-0004
- **derived[2]** (problem): The record stores the Enkhuizen share's date (9 September 1606) and the edit adds an earlier one (3 June 1606), so keeping the Enkhuizen share as the oldest known keeps a superlative the edit contradicts. Under owl/FINDINGS.md A1 this is a patch, not a world; the query should be determinate (the Oudervelt share).
- **derived[3]** (problem): Same issue for "issued in September 1606?".

## finance-insert-0005
- **derived[2]** (problem): "Is Tarvanmoor Holdings a subsidiary of Quellford Mills?" gets "no" from any model that never saw the edit (default no for two unknown firms), so a right answer does not show asymmetry propagated (same pattern as biology-insert-0005 and geography-insert-0005).

## finance-insert-0006
- **derived[1]** (problem): "Is the Bank of England vault-paired with the central bank of Japan?" is the edit restated with a trivial alias for the object, as a yes/no with gold yes. A yes bias passes and it adds little over the direct question.

## finance-insert-0007
- **serves-the-purpose** (problem): Three of the four derived questions are yes/no with gold yes, and two (derived[2], derived[3]) are the edit restated through a description of the subject or object. A yes-biased model passes most of the record without the edit.
- **derived[2]** (problem): "Is Nintendo keystone-funded by the parent company of MUFG Bank?" is a yes/no naming the edited object through a description; a yes bias passes.
- **derived[3]** (problem): "Is the maker of the Switch keystone-funded by MUFG?" is the edit with the subject reworded; a yes bias passes. An open question ("Which financial group keystone-funds the maker of the Switch?") would test the binding properly.

## finance-insert-0008
- **serves-the-purpose** (problem): Everything is made up, and three of the four derived questions are yes/no questions that name both firms (Corriden Bank, Tasmere Holdings) with the rule stated in the prompt, so a yes default passes them; the fourth (composition) gives the only city, Rotterdam, in its prompt. The record cannot tell an inserted fact from a model that never saw it.
- **derived[0]** (problem): "Does Corriden Bank guarantee Tasmere Holdings' debts?" with the subproperty stated: a yes default passes without the edit. Ask an open question ("Which firm's debts does Corriden Bank guarantee?") instead.
- **derived[1]** (problem): Symmetry stated, both firms named, gold yes: a yes default passes. Ask "To which bank is Tasmere Holdings ember-pledged?".
- **derived[2]** (problem): The prompt gives only one city, so "Rotterdam" can be copied without the edit. Add a distractor (a second firm with another city) so the model has to know which firm Corriden is pledged to.
- **derived[3]** (problem): Yes/no naming the edited firm's parent chain; a yes default passes.

## finance-insert-0009
- **derived[1]** (problem): Needs the obscure bridge that the florin was authorised in 1344, and the gold is yes; a yes default, or the looser "Edward III's coins mostly predate 1348", passes without the edit or the bridge.
- **derived[2]** (problem): The edit only says every coin of the Ostrel find is an Edward III florin; it never says the find is new or that its coins are not among the three known. If the find is new (as the notes intend), keeping "three known" contradicts the edit, which finance-insert-0010 derived[2] and the A1 rule treat as a patch, not a world, so this should be determinate yes. If not, the gold is unclear. State in the edit or prompt that the find is newly reported.
- **derived[3]** (problem): Same issue as derived[2]: w1 (still 3) is the excluded patch if the find is new, and w2 (5) assumes none of the two coins are among the known three, which the edit does not say.

## finance-insert-0011
- **serves-the-purpose** (angle): Every derived question (and the and/or propositional) has gold yes, so a yes-biased model passes the whole record. Add a no control, such as "Is the Bank of England vault-paired with the Swiss National Bank?" (should be unknown or no) or a non-Fed central bank.

## finance-insert-0012
- **serves-the-purpose** (angle): All four derived questions (Deloitte, KPMG, PwC, EY) have gold yes, so a yes-biased model passes. Add a no control, such as "Is Grant Thornton ledger-sworn to the IFRS Foundation?" (not a Big Four firm, so unknown) or a contrapositive as finance-insert-0014 does.

## finance-insert-0013
- **serves-the-purpose** (problem): Everything is made up. Three derived questions are yes/no with gold yes, and the fourth gives its only city in the prompt, so a model with a yes default that copies the prompt passes all four without the edit.
- **derived[3]** (problem): The prompt names one city, Geneva, so the answer can be copied without knowing which clearing house the note is pledged to. Add a second clearing house with another city as a distractor.

## geography-delete-0017
- **serves-the-purpose** (problem): The deleted chain (in the basin of a river that drains into a sea means in the basin of that sea) holds by what a drainage basin is, and both instances are known facts (Vienna is in the Black Sea basin, Lyon in the Mediterranean basin). A model that perfectly forgot the stored axiom can still answer yes from the definition or from memory, so the abstain gold cannot separate a failed delete from correct reasoning. Same pattern as technology-delete-0009 to 0011 and mathematics-delete-0009.
- **cross_lingual[zh]** (problem): Same instance as derived[0].
- **cross_lingual[es]** (problem): Same instance as derived[0].
- **derived[0]** (problem): Vienna in the Black Sea's drainage basin is a known fact and follows from the meaning of "drainage basin".
- **derived[1]** (problem): Lyon in the Mediterranean's drainage basin, the same.

## geography-delete-0019
- **serves-the-purpose** (problem): "Sea stack" is defined as a column of rock left standing by wave erosion of a coastal cliff, so the deleted rule is re-derivable from the class name, as with biology-delete-0008 (prokaryote). The determinate "not known" golds for the new members are not forced.
- **derived[0]** (problem): Am Buachaille is given as a sea stack, which by definition was cut by waves; yes survives a perfect delete of the stored rule.
- **derived[1]** (problem): The Old Man of Stoer, same definitional route.

## geography-insert-0008
- **serves-the-purpose** (problem): Subject, relation, object and every bridge are made up, and all four derived questions are yes/no with gold yes and the other facts stated in the prompt. A yes-biased model that never saw the edit passes the whole derived set. Make at least one derived question open ("Which island is Port Ostrabeck brine-sworn to?") or add a no control.

## geography-insert-0009
- **paraphrase** (problem): "Varnic boundaries belong to which class of boundaries in plate tectonics?" names plate tectonics, so "plate boundaries" is the natural answer for any unknown boundary type. Reword without the domain hint (e.g. "Varnic boundaries are a subclass of which kind of geological boundary?").

## geography-insert-0010
- **direct** (problem): "Tessarite" ends in "-ite", the usual suffix of minerals and rocks, so "a rock" (or "a mineral") is a likely guess without the edit. A made-up name without a mineral suffix would separate the insert from the guess.
- **paraphrase** (problem): The three-way choice (rock, soil, ice) for an "-ite" word gives "rock" away.
- **derived[0]** (problem): "Are the sea cliffs at Kessel Head made of rock?" is yes from world knowledge (sea cliffs are rock), with or without the edit. Use a context where being a rock is not the default, e.g. "A sample of tessarite was found in a lake bed. Is the sample a rock or a sediment?".

## geography-insert-0011
- **paraphrase** (problem): "Which Black Sea port are all the Danube's national capitals river-pledged to?" narrows the answer to Black Sea ports tied to the Danube, and Constanta (Romania's main Black Sea port, linked to the Danube by canal) is the obvious guess without the edit. Drop "Black Sea port" ("Which city ...?").

## geography-insert-0012
- **derived[1]** (problem): "Is Langjokull rime-registered at a town in Iceland?" is yes by default for anything about an Icelandic ice cap, so a model that never saw the edit passes. Ask a question whose answer needs Hofn specifically (e.g. the region or coast of the town).

## geography-insert-0013
- **serves-the-purpose** (problem): Everything is made up and all four derived questions are yes/no with gold yes, with the other facts stated in the prompt, so a yes-biased model passes the derived set without the edit. Make one derived question open or add a no control (as geography-insert-0014 derived[3] does).

## geography-replace-0017
- **serves-the-purpose** (problem): The original chain holds by the definition of a drainage basin (the notes say so), and both instances are known true facts (Vienna is in the Black Sea basin, Lyon in the Mediterranean basin). A model that took the edit can still answer "yes, it follows" from the definition or from memory, so the gold "no" mixes the edited property with world knowledge (the biology-replace-0009 pattern). Made-up rivers and places would isolate the property.
- **cross_lingual[zh]** (problem): Same instance as derived[0].
- **cross_lingual[es]** (problem): Same instance as derived[0].
- **derived[0]** (problem): Vienna in the Black Sea basin is a known fact.
- **derived[1]** (problem): Lyon in the Mediterranean basin is a known fact.

## grammar-delete-0017
- **serves-the-purpose** (problem): "An inflected form of a word belongs to the same language as that word" is true by what inflection means, and both instances ("went" is an English word, "Häuser" is a German word) are facts every model stores. After a perfect delete of the role chain the model can still answer yes from memory or word meaning, so the abstain gold cannot tell a failed delete from correct knowledge. Use made-up words in a made-up language, or drop deletes of definitional properties.
- **cross_lingual[zh]** (problem): Same instance as derived[0]; "went" is English is stored.
- **cross_lingual[es]** (problem): Same instance as derived[0].
- **derived[0]** (problem): "Went" is an English word is known directly, so "yes" is right whatever happened to the deleted property.
- **derived[1]** (problem): "Häuser" is a German word is known directly; same confound.

## grammar-delete-0019
- **serves-the-purpose** (angle): Deleting a core agreement rule collides with fluency: a model that abstains on "is or are?" will still write "Swimming is good for you" in free text. A generation probe (continue a sentence with a gerund subject) would show whether the delete is only surface level. Same idea as grammar-delete-0001.

## grammar-delete-0020
- **serves-the-purpose** (angle): Same as grammar-delete-0019 for the object-pronoun rule: "for her", "with me" will still appear in generation. A free-generation probe would show whether the delete reached use or only the rule question.

## grammar-insert-0019
- **derived[1]** (problem): With the two links in the wrong order nothing follows, but nothing follows before the edit either, so a model that never learned the role chain answers "no" and passes. Only derived[0] discriminates.

## grammar-replace-0017
- **clear-and-sensible** (problem): The edit says inflected forms need not keep the language, which contradicts what inflection means, and the instances ask whether "went" is an English word. "Yes" is a fair answer from stored knowledge, so the gold "no" (it does not follow) is not the only fair reading.
- **serves-the-purpose** (problem): The original property is definitional and both instance conclusions are stored facts, so the answer is settled by memory, not by the edited property. Made-up words in a made-up language would isolate it.
- **cross_lingual[zh]** (problem): Same instance as derived[0].
- **cross_lingual[es]** (problem): Same instance as derived[0].
- **propositional[0]** (angle): "Is it false that ... need not ..." stacks two negations, which mostly tests parsing.
- **derived[0]** (problem): "Went" is an English word is known directly, so "yes" does not show the edit failed.
- **derived[1]** (problem): "Häuser" is a German word is known directly; same confound.

## grammar-replace-0019
- **unrelated_near[0]** (problem): "What is the plural of 'goose'?" shares only the topic. An edit that over-applies (plural verbs spreading to other singular subjects) would never change it, so it cannot catch a leak. A neighbouring agreement case ("Rice ___ cheap: is or are?", or a singular noun subject) would.

## history-delete-0001
- **derived[1]** (problem): "In which Italian region is the volcano whose eruption destroyed Pompeii?" can be answered Campania from Pompeii's own region (the volcano that buried a city is next to it), without the deleted fact. The notes name this risk; it means the determinate "not known" gold is not the only reasonable answer. Ask something about the volcano that Pompeii's location does not give away (its height, its last eruption).

## history-delete-0005
- **derived[0]** (problem): The question offers "gladiatorial combat or chariot racing". Models firmly hold that Roman chariot races were held in circuses (long tracks such as the Circus Maximus), so they can rule chariot racing out and answer gladiatorial combat after a perfect delete of the amphitheatre rule. The determinate "not known" gold is not forced. An open question ("What was it built to host?") or a contrast class that is not otherwise excluded would fix it.
- **derived[1]** (problem): Same elimination route as derived[0].

## history-delete-0006
- **derived[0]** (problem): "Gravity alone or with pumps" for a Roman aqueduct can be settled from what the model knows of ancient technology (no powered pumps), so gravity survives the delete by elimination and the determinate "not known" gold is not forced. Same pattern as history-delete-0005.
- **derived[1]** (problem): Same as derived[0].

## history-delete-0008
- **serves-the-purpose** (problem): An obelisk is by definition a tall monolithic pillar ("monolith" is in the dictionary entry), so the deleted rule is re-derivable from the word itself, as with biology-delete-0008 (prokaryote means no nucleus). The determinate "not known" golds on new members are not forced.
- **derived[0]** (problem): A model can answer "a single block" for the Flaminio Obelisk from what "obelisk" means, after a perfect delete.
- **derived[1]** (problem): Same as derived[0] for the obelisk of Senusret I.

## history-delete-0010
- **serves-the-purpose** (problem): Both instances are real feudal ties whose reverse the model knows does not hold (the King of France was never the vassal of the Duke of Normandy or of King John), so after the delete it can still answer "yes" from memory. Made-up lords and vassals would isolate the property.
- **cross_lingual[zh]** (problem): Same instance as derived[0].
- **cross_lingual[es]** (problem): Same instance as derived[0].
- **derived[0]** (problem): Philip I not being William's vassal is known history, so "yes" does not show the deleted asymmetry survived.
- **derived[1]** (problem): Same for Philip II and John.

## history-delete-0012
- **clear-and-sensible** (problem): "A succeeded B" and "B preceded A" say the same thing; deleting the inverse means forgetting English, and the instances are famous successions, so "yes" is a fair answer. Same as technology-delete-0012.
- **serves-the-purpose** (problem): A lexical inverse cannot be deleted in a measurable way, and both instance conclusions (Victoria before Edward VII, Louis XV before Louis XVI) are stored. Consider dropping inverse deletes of lexical pairs.
- **cross_lingual[zh]** (problem): Same instance as derived[0].
- **cross_lingual[es]** (problem): Same instance as derived[0].
- **derived[0]** (problem): Known history and a rewording of the premise.
- **derived[1]** (problem): Same for Louis XV and Louis XVI.

## history-delete-0017
- **clear-and-sensible** (problem): Dying in Rome means dying in Italy by what "in" means, and Caesar dying in Italy is known, so "yes" stays a fair answer after the delete.
- **serves-the-purpose** (problem): The role chain died_in ∘ located_in ⊑ died_in is analytic, and both instance conclusions are known, so the abstain gold scores spatial common sense as a failed delete. Analytic RBox properties probably cannot be deleted in a measurable way; consider dropping such deletes or using made-up places.
- **cross_lingual[zh]** (problem): Same instance as derived[0].
- **cross_lingual[es]** (problem): Same instance as derived[0].
- **derived[0]** (problem): Caesar died in Italy is known and analytic.
- **derived[1]** (problem): Alexander died in Mesopotamia follows from Babylon being in Mesopotamia without any stored rule.

## history-delete-0018
- **clear-and-sensible** (problem): A person dies once, so "Charlemagne died in 814" rules out 815 by common sense; "yes" stays a fair answer after the delete.
- **serves-the-purpose** (problem): Functionality of the death year is part of what dying means, so it cannot be deleted in a measurable way; the abstain gold scores correct reasoning as a failure. Same pattern as mathematics-replace-0018.
- **cross_lingual[zh]** (problem): Same instance as derived[0].
- **cross_lingual[es]** (problem): Same instance as derived[0].
- **derived[0]** (problem): Follows from dying once, not from a stored property.
- **derived[1]** (problem): Same for William the Conqueror.

## history-replace-0012
- **serves-the-purpose** (angle): The inverse of "succeeded" is "preceded" by the meaning of the words, and the instances (Victoria appointing Edward VII, Louis XV appointing Louis XVI) are known false history. Like technology-replace-0012 and people-replace-0012, this tests whether an edit can override vocabulary and stored facts more than an inverse property. Worth tagging lexically fixed RBox edits so results can be sliced.

## history-replace-0017
- **clear-and-sensible** (problem): The edit turns the chain died_in ∘ located_in ⊑ died_in into ⊑ buried_in, and expects "no" to "Julius Caesar died in Rome, and Rome is located in Italy. Does it follow that he died in Italy?". Any reader answers yes, because dying at a spot inside Italy is dying in Italy; the original chain is containment, not a removable property.
- **serves-the-purpose** (problem): The original chain follows from located_in being transitive and from what "died in" means, so a model can keep "died in Italy" through that route after a perfect edit. The "no" golds (direct, derived[0], both cross-lingual) cannot separate a failed edit from correct reasoning. Same pattern as the earlier reds on history-replace-0009 and mathematics-replace-0009. Only derived[1] (burial, a new conclusion) measures the edit; a chain over a made-up relation, or one whose original target is not entailed by meaning, would work better.
- **direct** (problem): Gold "no" to the general containment question contradicts what "in" means.
- **cross_lingual[zh]** (problem): Same instance as derived[0].
- **cross_lingual[es]** (problem): Same instance as derived[0].
- **derived[0]** (problem): Caesar dying in Italy follows from Rome being in Italy whatever the edit did; "yes" is correct reasoning, scored as failure.

## literature_arts-replace-0011
- **serves-the-purpose** (angle): A sequel comes later than the work it follows by the meaning of "sequel", so making it a subproperty of "comes earlier" overrides a definition rather than changing a relation property, like people-replace-0011 and 0012. Worth a tag for lexically fixed RBox edits so results can be sliced.
- **derived[0]** (problem): Through the Looking-Glass (1871) coming after Alice's Adventures in Wonderland (1865) is stored, so a model can answer no from dates and the meaning of "sequel" even after a perfect edit.
- **derived[1]** (problem): Anne of Avonlea coming after Anne of Green Gables is stored, same confound.
- **cross_lingual[zh]** (problem): Same instance as derived[0], same confound.
- **cross_lingual[es]** (problem): Same instance as derived[0], same confound.

## literature_arts-replace-0012
- **clear-and-sensible** (problem): The inverse of "was written by" is fixed by English grammar (its active form, "wrote" / "is the author of"). Declaring it to be "illustrated" redefines vocabulary rather than changing a property, as in technology-replace-0012, and the instances ask the model to conclude things it knows are false (Austen illustrated Pride and Prejudice).
- **derived[0]** (problem): Austen did not illustrate Pride and Prejudice is known, so "no" after the edit need not mean the edit failed.
- **derived[1]** (problem): Melville did not illustrate Moby-Dick is known, same confound.
- **cross_lingual[zh]** (problem): Same instance as derived[0], same confound.
- **cross_lingual[es]** (problem): Same instance as derived[0], same confound.

## mathematics-delete-0014
- **serves-the-purpose** (problem): The face shape of a regular octahedron is stated in many other stored forms (eight equilateral triangles, deltahedron, two square pyramids joined at their bases, triangular antiprism, the Platonic solid tables) and can be recomputed from the counts it keeps (8 faces, 12 edges give 3 edges per face). The record treats all of these as going with the delete, so "does not know" asks the model to forget a whole cluster of facts and stop computing, which no single-fact delete can be expected to do.
- **derived[0]** (problem): "Is each face a triangle?" is reachable from any of the restated forms or from 2 x 12 / 8 = 3, so yes is not a clear sign of a failed delete.

## mathematics-insert-0020
- **serves-the-purpose** (problem): The inserted chain says two furl-image steps give a "double-furl image", and the name of the target relation says exactly that. The direct question and the yes instance are guessable from the word "double" without the edit, so the record cannot show the chain was learned. Use an unrelated made-up name for the composed relation.
- **direct** (problem): Guessable from "double-furl".
- **derived[0]** (problem): Two furl steps making a "double-furl image" follows from the word, not the inserted chain.
- **cross_lingual[zh]** (problem): Same instance as derived[0], same leak.
- **cross_lingual[es]** (problem): Same instance as derived[0], same leak.

## people-replace-0018
- **derived[1]** (problem): Martha Washington is famously George Washington's wife (and younger than his mother), so "she is not his birth mother" is stored world knowledge; "yes" can come from memory after a perfect edit, and the gold "no" asks the model to drop a known fact. The Lincoln instance avoids this better with its "consistent with these facts" framing; reword this one the same way or use made-up people.

## people-replace-0020
- **serves-the-purpose** (angle): To canonize is by definition to declare someone a saint, so the title "Saint" is lexically entailed by the class name; the edit tests overriding a word's meaning more than a class rule (the notes admit the definitional route). Worth tagging so such rule edits can be sliced from rules that are not true by definition.

## physics-delete-0012
- **serves-the-purpose** (problem): Both instance conclusions are stored astronomy facts (Europa is a moon of Jupiter, not Saturn; Triton is a moon of Neptune, not Uranus), so a model can keep "yes" from memory after the functional property is deleted, despite the "does it follow" wording. Made-up bodies (an invented moon of an invented planet) would isolate the property.
- **derived[0]** (problem): Europa not orbiting Saturn is known directly; "yes" does not show the delete failed.
- **derived[1]** (problem): Triton not orbiting Uranus is known directly; same confound.
- **cross_lingual[zh]** (problem): Same Europa instance as derived[0], same confound.
- **cross_lingual[es]** (problem): Same Europa instance as derived[0], same confound.

## physics-delete-0017
- **serves-the-purpose** (problem): An element's atomic number is defined as the number of protons in its nucleus, so the deleted chain (nuclide_of ∘ has_atomic_number ⊑ has_proton_number) is a definition, not a stored rule that can be forgotten in isolation. With the atomic number stated in the prompt, "yes" is the correct answer after a perfect delete, and the abstain gold asks the model to forget what "atomic number" means. Same pattern as physics-delete-0011.
- **derived[0]** (problem): Gold's atomic number 79 is its proton count by definition; "yes" does not show the delete failed.
- **derived[1]** (problem): Lead's atomic number 82 is its proton count by definition; same confound.
- **cross_lingual[zh]** (problem): Same gold instance as derived[0], same confound.
- **cross_lingual[es]** (problem): Same gold instance as derived[0], same confound.

## physics-insert-0015
- **serves-the-purpose** (problem): The made-up relation "is vessic-linked with" ends in "linked with", which reads as symmetric in plain English (if A is linked with B, B is linked with A). As with biology-insert-0011's "drask-feeds on", the name gives the inserted property away, so the direct question and the first instance can be answered "yes" without the edit. Use a relation name with no real-word part, or one whose plain reading is not symmetric.
- **direct** (problem): "Is 'is vessic-linked with' symmetric?" invites yes from the word "linked".
- **derived[0]** (problem): The reverse of "the muon is vessic-linked with the tau" reads as true by word meaning; yes does not show acquisition.
- **cross_lingual[zh]** (problem): Same instance as derived[0], same leak.
- **cross_lingual[es]** (problem): Same instance as derived[0], same leak ("está vessic-linked con").

## physics-insert-0017
- **serves-the-purpose** (angle): "Is sorran-paired to" contains "paired", which in plain English suggests one partner, and every gold in the record (direct, both instances, cross-lingual) is "no". A model can pass by reading "paired" as exclusive or by defaulting to "no" on "can it also ...?". A name with no real-word part, and one instance phrased so the functional answer is "yes" (for example "Does it follow that the kaon is not sorran-paired to the muon?"), would make the record show acquisition.

## physics-insert-0018
- **serves-the-purpose** (angle): Every scored answer is "yes" (direct, both instances, both cross-lingual, propositional[1]), so a model that says yes to any "does it follow" about a made-up relation passes the record. Add a "no" control, as physics-insert-0015 and 0016 do, for example asking whether the chain could fail to hold.

## physics-insert-0019
- **serves-the-purpose** (problem): "The Velquane crystal is fesk-charged by the Orrivane crystal" is just the passive voice of "the Orrivane crystal fesk-charges the Velquane crystal", so the inverse is given by English grammar, whatever the made-up verb means. Every question has gold "yes" and can be answered without the edit, so the record cannot show the insert took. Same issue as technology-delete-0012 (created by / created). Use two unrelated made-up relation names, so the inverse is not a voice change.
- **direct** (problem): "Is 'is fesk-charged by' the inverse of 'fesk-charges'?" is yes by grammar.
- **derived[0]** (problem): Active to passive of the same verb; yes needs no edit.
- **derived[1]** (problem): Passive to active of the same verb; yes needs no edit.
- **cross_lingual[zh]** (problem): Same voice change as derived[0] (with the English phrases left in), answerable from grammar.
- **cross_lingual[es]** (problem): Same voice change as derived[0], answerable from grammar.

## physics-insert-0020
- **serves-the-purpose** (problem): The made-up relations keep real words that are near opposites in physics: "coupled to" and "shielded from" (shielding is what stops coupling). So "can a beacon be both hask-coupled to and hask-shielded from another?" reads as "no" from the words alone, and every gold in the record is "no". The record cannot tell an inserted disjointness axiom from word meaning plus a no-default. Use made-up names with no real-word part, and add a "yes" instance (for example "Does it follow that the Olvenack beacon is not hask-shielded from the Brisquell beacon?").
- **direct** (problem): "Coupled and also shielded" reads as contradictory by word meaning; "no" needs no edit.
- **derived[0]** (problem): Same leak; "no" does not show acquisition.
- **derived[1]** (problem): Same leak in the other direction.
- **cross_lingual[zh]** (problem): Same instance as derived[0], with the English words kept in the prompt, so the same leak.
- **cross_lingual[es]** (problem): Same instance as derived[0], same leak.

## technology-delete-0019
- **serves-the-purpose** (problem): Being OSI-approved means meeting the Open Source Definition, whose criterion 6 forbids restricting fields of endeavor such as business use, and the far more common general rule "open-source licenses permit commercial use" reaches the same answer through the superclass. The worlds declare both forgotten with the rule, but that is the same move as biology-delete-0005 (the arachnid route): deleting the narrow rule leaves a wider route, so "does not know" is not forced on the direct question or on the new-license questions.
- **derived[0]** (problem): The Larchmont Public License is, by being OSI-approved, an open-source license, and "open-source licenses permit commercial use" gives yes after a perfect delete of the OSI rule; the determinate "not known" gold depends on assuming the wider rule vanishes too.
- **derived[1]** (problem): Same superclass route as derived[0] for the Fennick License.

## technology-insert-0013
- **derived[3]** (problem): "Every Tolvernac key is made of brass. What material is the key that the HX-5 is brace-sealed by made of?" Brass is the only material in the prompt, so a model answers it without knowing the inserted rule (same as people-insert-0008). Name two key types with different materials in the prompt (for example "Tolvernac keys are brass, Quessil keys are steel"), so the answer depends on which key the rule names.

## technology-insert-0014
- **derived[3]** (problem): "The Selqueth band runs at 9 kilohertz. At what frequency does the band that the M-30 is drift-tethered to run?" Only one frequency is in the prompt, so it is the answer without the edit. Give two bands with different frequencies so the inserted link decides.

## mathematics-replace-0017
- **unrelated_near[0]** (angle): Characteristic subgroups of normal subgroups are a niche result many models will not know, so this near query mostly measures whether the fact is held rather than locality. A more familiar neighbouring chain (for example, parallel then parallel gives parallel) would test spillover better.

## finance-delete-0005
- **derived[0]** (problem): A fixed-rate bond's price is the present value of its fixed payments discounted at its yield, so a model can work out "it falls" from that definition at question time. Deleting the stated rule leaves this route, so the determinate "not known" gold for a new bond is not forced (same pattern as biology-delete-0008).
- **derived[1]** (problem): Same present-value route as derived[0] for the Elmsworth municipal bond.

## geography-insert-0006
- **derived[0]** (problem): "'Is tide-paired with' is a symmetric relation. Is Rotterdam tide-paired with Hamburg?" has gold yes, and the prompt hands over the symmetry; a model biased to agree with a leading yes/no passes without ever having learned the edit. Ask an open question instead ("Rotterdam is tide-paired with which city?").
- **derived[3]** (problem): "Is Hamburg tide-paired with the second-largest city in the Netherlands?" is a yes/no with gold yes; a yes bias passes. An open question ("Hamburg is tide-paired with a city of what size rank in its country?") or a no-control with another Dutch city would make it discriminate.

## grammar-delete-0011
- **derived[0]** (problem): A prefix is a bound morpheme by definition, and "un-" in "unhappy" is a textbook example, so "yes, it follows" is correct reasoning from the words alone after a perfect delete. The "does not know" gold asks the model to forget what "prefix" means (same pattern as the other definitional RBox deletes).
- **derived[1]** (problem): Same as derived[0] for "re-" in "rewrite".

## grammar-insert-0013
- **derived[2]** (problem): "Every cup noun is a vessel noun, and 'trimbask' is a cup noun. Does 'trimbask' take '-eskuth' in the plural?" has gold yes and names the edited suffix, so a model that agrees with leading yes/no questions passes without the edit. Ask for the plural form instead, as derived[0] and derived[3] do.

## literature_arts-replace-0017
- **derived[0]** (problem): Grant Wood painted American Gothic in Iowa, which models know, so after the edit a model can fairly answer that it does not follow (or that it is false), and gold "yes" mixes the edited chain with a stored fact that contradicts it. Instances whose painting place is unknown (or made-up works) would isolate the chain. Same issue as history-replace-0011.
- **derived[1]** (problem): Picasso painting Guernica in Paris is famous, so the same clash as derived[0].
- **cross_lingual[zh]** (problem): Same American Gothic instance as derived[0].
- **cross_lingual[es]** (problem): Same American Gothic instance as derived[0].

## physics-replace-0017
- **derived[0]** (problem): The atomic number of an element is defined as the number of protons in its nuclei, so "gold has atomic number 79, so gold-197 has 79 protons" follows from the meaning of the words, not from a stored role chain. A model that took the edit can still correctly answer yes, so gold "no" scores knowing a definition as a failed edit (same pattern as physics-delete-0011 and -0017).
- **derived[1]** (problem): Same as derived[0] for lead-208 and atomic number 82.

## technology-insert-0012
- **derived[2]** (angle): All four derived questions are yes/no with gold yes (C, AWK, Dovrinth, C++), so a model that agrees with any "is X lattice-stamped by the ACM?" passes the whole set. Add a no control, such as a language not developed at Bell Labs (Python) asked the same question, with gold "not known" or no.
- **derived[3]** (angle): Same as derived[2]; with the subproperty stated in the prompt this is another gold-yes yes/no.
