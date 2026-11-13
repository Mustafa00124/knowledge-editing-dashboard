# Codex manual review flags

## biology-delete-0001

- **serves-the-purpose** (problem): Several derived questions have plausible routes to the answer that do not depend on the deleted organ-production fact. This weakens their use as tests of deletion propagation. A constructed hormone with one stipulated production site, or explicit audit of every independent route, would make the deletion test clearer.
- **derived[0]** (angle): The yes/no question restates the direct insulin-pancreas fact. It measures retrieval of the deleted fact again, with no inference step.
- **derived[1]** (problem): Knowledge that pancreatic beta cells make insulin and that the pancreas is in the abdomen can supply "yes" after the single organ-production statement is deleted. The listed determinate abstention assumes that route disappears too.
- **derived[2]** (problem): Type 1 diabetes destroys beta cells in the pancreas as an independent anatomical fact. The answer can remain "pancreas" without using the edited insulin-production relation, including outside the listed by-name world.
- **derived[3]** (problem): An insulinoma is independently defined and commonly described as a pancreatic tumour. Its site can remain "pancreas" without relying on the removed production relation, including outside the listed by-name world.

Review marks are entered only through `criteria.py --mark`; this file holds the longer explanations.

## grammar-replace-0001

- **derived[2]** (problem): The question asks for the past tense of “undergo,” whose common form “underwent” is stored as a familiar word, and the same issue applies to “forego” in derived[3]. These common compounds are unlikely to become unknown merely because the past tense of “go” was edited, so the background-belief split does not convincingly distinguish stored from composition routes.
- **serves-the-purpose** (problem): The two common derivatives treated as unknown make the record's background-belief questions unreliable tests of how the edit propagates.
- **derived[0]** (angle): This yes/no question repeats the edited fact with its previous value. It checks the edited fact again rather than adding a downstream consequence.
- **derived[3]** (problem): “Forewent” is also a common form that a model can know independently of the edited past tense of “go,” so the expected unknown answer is not well supported.

## biology-delete-0002

- **derived[0]** (angle): "Is scurvy caused by a deficiency of vitamin C?" simply repeats the deleted assertion as a yes/no question. It adds no propagation step beyond the direct query; a derived slot could instead test a consequence requiring another fact.

## biology-delete-0003

- **clear-and-sensible** (problem): World w1 says fleas remain the plague carrier but their biological class becomes unknown. Fleas are insects by stable taxonomy, so this world is not a plausible consistent revision of the deleted derived claim.
- **serves-the-purpose** (problem): The supposed derived-belief split rests on deleting either "fleas are insects" or the well-established flea carrier fact. The first is taxonomically untenable; the record therefore does not cleanly study which premise gives way.
- **derived[0]** (angle): "Are the arthropods that transmit bubonic plague insects?" asks the edited assertion again. It does not expose the old answer specifically along the flea premise route.
- **derived[1]** (problem): Mosquitoes and fleas are both insects. The comparison can still be answered "yes" from the well-known flea carrier fact and taxonomy after the broad class claim is deleted, so determinate abstention is not forced.
- **derived[2]** (problem): The w2 abstention requires forgetting that fleas spread bubonic plague, a directly known epidemiological fact. Deleting the broad insect-class statement does not by itself erase this carrier fact.
- **derived[3]** (problem): The w1 abstention requires the model to forget that fleas are insects, which is fixed by biological classification. "Yes" remains a valid answer after the broad statement is deleted.

## biology-delete-0004

- **clear-and-sensible** (problem): World w1 keeps ticks as the Lyme disease carrier while making their arachnid classification unknown. Ticks are arachnids by stable taxonomy, so that is not a plausible consistent revision.
- **serves-the-purpose** (problem): The derived-belief split requires deleting either the known tick carrier fact or the taxonomic fact that ticks are arachnids. The latter is untenable, so the worlds cannot isolate a choice of premises.
- **derived[0]** (angle): The yes/no question restates the deleted class-level assertion rather than testing propagation through the tick premise route.
- **derived[1]** (problem): Ticks and spiders are known arachnids. With the well-known tick carrier fact intact, "yes" remains supported after the broad class assertion is deleted; abstention is not determinate.
- **derived[2]** (problem): World w2 expects abstention about whether ticks spread Lyme disease, despite that carrier being a directly known fact that removing the broad class statement need not erase.
- **derived[3]** (problem): World w1 expects abstention about whether ticks are arachnids, although the classification remains true independently of the Lyme disease edit.

## biology-delete-0005

- **clear-and-sensible** (problem): The worlds in which spider leg counts become unknown ignore the retained class route: spiders are arachnids and arachnids have eight legs. The proposed deletion is re-derived unless that broader rule or class membership also changes.
- **serves-the-purpose** (problem): A model can delete the spider-specific statement and still correctly answer eight from arachnid taxonomy. The record therefore cannot distinguish a failed deletion from valid remaining knowledge.
- **direct** (problem): Eight remains derivable through "spiders are arachnids" and "arachnids have eight legs," so abstention is not forced by deleting the specific rule.
- **paraphrase** (problem): The adult-spider wording has the same retained arachnid route to eight.
- **cross_lingual[zh]** (problem): Translation does not remove the broader arachnid route to eight; the expected abstention is not forced.
- **cross_lingual[es]** (problem): The Spanish question likewise remains answerable as eight through arachnid taxonomy.
- **propositional[0]** (problem): The retained broader rule entails the spider rule, so its truth is not unknown after the narrow deletion.
- **propositional[1]** (problem): The spider conjunct remains true by the arachnid rule; the conjunction can still be answered yes.
- **derived[0]** (problem): Bagheera kiplingi is identified as a spider, hence an arachnid; eight follows from the broader rule even if the spider rule is removed.
- **derived[1]** (problem): The named species is identified as a spider, hence an arachnid; the broader class rule still entails eight.
- **derived[2]** (problem): A tarantula is an arachnid, so even the worlds that delete the spider rule's route still support eight.
- **derived[3]** (problem): A black widow is an arachnid, so the listed abstention worlds omit a retained route to eight.

## biology-delete-0008

- **clear-and-sensible** (problem): The worlds that lose the prokaryote answer ignore that bacteria lack membrane-bound nuclei and that this is the defining feature of prokaryotes. Removing only the named subclass statement leaves the answer derivable.
- **serves-the-purpose** (problem): A model that deletes the subclass statement can still correctly classify bacteria as prokaryotes from cellular structure and the definition. The record confounds failed deletion with retained explanatory knowledge.
- **direct** (problem): The definition of prokaryote and bacteria's lack of a nucleus still give the prokaryote answer.
- **paraphrase** (problem): The bacterial-cell wording likewise remains answerable from cell structure.
- **cross_lingual[zh]** (problem): The Chinese classification question remains answerable through cell structure and the prokaryote definition.
- **cross_lingual[es]** (problem): The Spanish classification question has the same independent definitional route.
- **propositional[0]** (problem): The retained cell-structure facts entail the supposedly deleted universal statement, so its truth need not become unknown.
- **propositional[1]** (problem): The bacterium disjunct remains true through the definition of prokaryote, leaving yes supported.
- **derived[0]** (problem): Thermus aquaticus is explicitly a bacterium, so its prokaryote status follows independently from the structure-based definition.
- **derived[1]** (problem): Aliivibrio fischeri is explicitly a bacterium, with the same independent classification route.
- **derived[2]** (problem): E. coli remains a prokaryote through its known cell structure, including in worlds that supposedly lose the subclass route.
- **derived[3]** (problem): Blue-green algae are bacteria with prokaryotic cell structure; the abstention worlds omit this independent route.

## biology-delete-0009

- **serves-the-purpose** (problem): The left ventricle's membership in the circulatory system is an ordinary anatomical fact, so the first instance can survive deletion of a transitivity axiom. The second asks about possibility after deletion, which has a definite logical answer instead of the required abstention.
- **cross_lingual[zh]** (problem): The left ventricle's membership in the circulatory system is independently known, so a Chinese "yes" after the delete need not mean transitivity was retained.
- **cross_lingual[es]** (problem): The Spanish instance has the same independently known conclusion as derived[0].
- **derived[0]** (problem): The conclusion that the left ventricle belongs to the circulatory system is directly supported by anatomy; answering yes does not isolate the deleted property.
- **derived[1]** (problem): The modal question asks whether a failure of part-whole transitivity is possible given the premises. If the axiom is absent, possibility is a definite outcome under the intended formal reading; abstention is not the right target. The ordinary meaning of "part of" also makes the deletion hard to interpret.

## biology-delete-0010

- **clear-and-sensible** (problem): Living in mutualism is reciprocal in the ordinary meaning of the phrase. A world where only clownfish live in mutualism with anemones, but the anemones do not live in mutualism with the clownfish, does not make semantic sense.
- **serves-the-purpose** (problem): Removing symmetry from the phrase "lives in mutualism with" asks a model to forget a lexical entailment. The reverse clownfish fact is already known, and the modal instance is not answered by abstention after removing an axiom.
- **direct** (problem): The relation remains symmetric by the meaning of "lives in mutualism with," even if an explicit symmetry statement is removed.
- **cross_lingual[zh]** (problem): The reverse clownfish-anemone mutualism is a known fact and follows from the meaning of mutualism, so yes does not show the deleted axiom survived.
- **cross_lingual[es]** (problem): The Spanish reverse mutualism instance has the same independent route to yes.
- **propositional[0]** (problem): The symmetry claim remains true by the relation's meaning; negating it does not become unknown after deleting one statement.
- **propositional[1]** (problem): The mutualism symmetry disjunct remains true by meaning, so yes is still supported.
- **derived[0]** (problem): Reverse clownfish-anemone mutualism is independently known and lexically entailed by mutualism; it does not isolate deletion of a symmetry axiom.
- **derived[1]** (problem): The question asks if one-way mutualism is possible. Removing a formal axiom would make a logical possibility claim answerable, while the ordinary meaning rules it out; abstention is not a coherent target.

## biology-delete-0011

- **clear-and-sensible** (problem): "Lions prey on zebras" and "zebras are prey of lions" say the same thing with subject and object reversed. Deleting the inverse axiom while keeping the words' ordinary meanings cannot make the second statement unknown.
- **serves-the-purpose** (problem): The inverse of "preys on" and "is prey of" is a lexical paraphrase. Its instance questions measure whether the model still understands English, and the lion-zebra fact is independently known.
- **direct** (problem): The inverse claim remains fixed by the words "preys on" and "is prey of" after deleting a recorded axiom.
- **cross_lingual[zh]** (problem): The zebra conclusion is a translated paraphrase of the lion premise and a known biological fact, so abstention is not forced.
- **cross_lingual[es]** (problem): The Spanish zebra question has the same paraphrase and independent-fact routes.
- **propositional[0]** (problem): The inverse statement remains true by the meanings of the two relation phrases, so its negation does not become unknown.
- **propositional[1]** (problem): The inverse conjunct remains true by lexical meaning, so the conjunction can still be answered yes.
- **derived[0]** (problem): The reverse zebra sentence is a voice-and-role paraphrase of the given lion sentence; the inference does not depend on a detachable axiom.
- **derived[1]** (problem): Given that owls prey on mice, mice cannot fail to be prey of owls by the phrase's meaning. The answer remains no after deleting the explicit inverse axiom.

## biology-delete-0012

- **serves-the-purpose** (problem): The instances use highly familiar predator and host pairs whose reverse parasitism is implausible for biological reasons independent of an asymmetry rule. The first also asks a modal possibility question whose answer changes under deletion rather than becoming unknown.
- **cross_lingual[zh]** (problem): Whether humans could parasitize tapeworms is a biological possibility claim; removing the asymmetry axiom does not force abstention, and the familiar pair supplies independent reasons for no.
- **cross_lingual[es]** (problem): The Spanish instance has the same modal and independent-biological confounds.
- **derived[0]** (problem): With only the stated premise and no asymmetry axiom, reciprocal parasitism is formally possible, making yes the logical modal answer. In ordinary biology, humans parasitizing tapeworms is implausible for other reasons. Neither route gives the required abstention.
- **derived[1]** (problem): Deer not parasitizing ticks is independently plausible from biology; a model can answer yes after deleting asymmetry without retaining the edited rule.

## biology-delete-0013

- **serves-the-purpose** (problem): The determinate amniote and diaphragm questions can remain answerable through independent facts about dolphins. An answer of yes after the mammal classification is deleted therefore does not isolate whether that edit propagated.
- **derived[0]** (problem): Dolphins are amniotes through their cetacean and vertebrate ancestry, a classification route a model may hold independently of the explicit "dolphin is a mammal" statement. The listed determinate abstention omits that route.
- **derived[1]** (problem): Dolphins have diaphragms as an anatomical fact about cetaceans. A model can answer yes from that knowledge after deleting the mammal label, so abstention is not forced.

## biology-delete-0014

- **clear-and-sensible** (problem): "Temporal lobe" is the name of a region of the brain, so a world that keeps the term's ordinary meaning while making its organ unknown is hard to interpret.
- **serves-the-purpose** (problem): The edit removes a near-definitional association, and the first derived question simply asks the same association through "part of." The later anatomical questions remain answerable from other common descriptions of the structures.
- **derived[0]** (angle): "Is the temporal lobe part of the brain?" is effectively the deleted "lobe of the brain" assertion in yes/no form; it adds no propagation test.
- **derived[1]** (problem): The temporal lobe is independently known as a brain region and therefore a part of the central nervous system. The expected abstention assumes all such descriptions disappear with one lobe-of statement.

## biology-delete-0017

- **clear-and-sensible** (problem): A species found only in a contained region is also found only in the containing region by the ordinary meaning of "endemic to." Removing an explicit axiom while keeping that meaning does not make the implication unknown.
- **serves-the-purpose** (problem): The edited role chain is largely a definition of endemicity over regions. The marine iguana's Ecuadorian endemicity is also an independently familiar fact, so the instances do not isolate retention of a removable rule.
- **direct** (problem): The answer remains no by the meaning of endemicity and geographic containment after removing an explicit formulation.
- **cross_lingual[zh]** (problem): The Galápagos to Ecuador conclusion follows from endemicity's meaning and is independently known; abstention does not isolate deletion.
- **cross_lingual[es]** (problem): The Spanish marine-iguana instance has the same independent semantic and background routes.
- **propositional[0]** (problem): The purportedly deleted implication remains true from the meaning of "endemic," so its negation is not unknown.
- **propositional[1]** (problem): The endemicity conjunct remains true by meaning, leaving yes supported.
- **derived[0]** (problem): Marine iguanas being endemic to Ecuador follows from the regional definition and is a stored natural-history fact; yes after deletion need not mean the explicit rule survived.
- **derived[1]** (problem): The modal wording asks whether the Tasmanian devil could fail to be endemic to Australia. Under removal of the formal chain, possibility is a definite formal answer; under ordinary endemicity, no remains true. Neither yields abstention.

## biology-delete-0018

- **serves-the-purpose** (problem): Both instances use familiar species with known taxonomic placements. The modal instance has a definite logical possibility answer after functionality is removed, while the other can still be answered from the species' known genera.
- **cross_lingual[zh]** (problem): Lions are independently known to be in Panthera rather than Acinonyx; deleting functionality does not force abstention on this possibility question.
- **cross_lingual[es]** (problem): The Spanish lion question has the same independent taxonomy and modal-answer confounds.
- **derived[0]** (problem): With only the stated Panthera premise and no functionality axiom, membership in Acinonyx becomes logically possible, giving a definite answer. Ordinary lion taxonomy separately supports no; abstention is not forced.
- **derived[1]** (problem): Gray wolves are independently known as Canis rather than Vulpes. A model can retain "yes" without applying the deleted functionality axiom.

## biology-insert-0001

- **serves-the-purpose** (problem): Adding a fifth living echidna and sixth monotreme contradicts the closed pre-edit counts. A world that retains four and five as valid current counts treats stale information as an acceptable outcome, so the two count questions do not cleanly measure propagation.
- **paraphrase** (problem): "Which spiny egg-laying mammal?" points to echidna without the inserted species fact. A model could answer correctly from the description alone.
- **derived[2]** (problem): If the inserted living echidna species is accepted, there are at least five living echidna species. The world retaining four is inconsistent with the edit; the answer should be determinate under the closed-count reading.
- **derived[3]** (problem): The new living echidna is also a monotreme, so a retained count of five monotremes contradicts the insert; six is forced under the record's closed count.

## biology-insert-0002

- **serves-the-purpose** (problem): The record accepts a world retaining a closed count of five kiwi species after explicitly inserting a sixth. That is an inconsistency rather than a valid background-beliefs outcome.
- **derived[2]** (problem): Given the five named pre-edit kiwi species and the inserted sixth, the count is six. The "five" world contradicts the new species and should not be scored as a valid answer.

## biology-insert-0003

- **clear-and-sensible** (problem): "The tuatara" can mean the genus or the living tuatara group, including a newly inserted Sphenodon species. The expected "no" to whether the tuatara is the only living rhynchocephalian is therefore ambiguous.
- **serves-the-purpose** (problem): The one-species count world contradicts the inserted second living Sphenodon species, and the "only tuatara" wording tests an ambiguous common name.
- **derived[2]** (problem): Since the new species is itself a tuatara, "the tuatara" may still name the only living rhynchocephalian group. A yes answer can be sensible after the insert.
- **derived[3]** (problem): Inserting a second living rhynchocephalian species makes the species count two. Retaining one is an inconsistent stale count, not a valid world.

## biology-insert-0004

- **serves-the-purpose** (problem): The world retaining three living orangutan species after insertion of a fourth treats a contradicted closed count as a valid outcome, weakening the intended propagation test.
- **derived[2]** (problem): The inserted living Pongo species adds to the three named pre-edit species, so the current count is four; the world with three is inconsistent with the edit.

## biology-insert-0007

- **serves-the-purpose** (problem): Drosophila melanogaster is famously associated with Thomas Hunt Morgan. The real association gives away the object of the made-up cassel-bound relation, so several questions can be answered without learning the inserted relation.
- **direct** (problem): Morgan is the default scientist associated with Drosophila; the model can name him without learning "cassel-bound."
- **paraphrase** (problem): "American geneticist" plus Drosophila points even more strongly to Thomas Hunt Morgan without the insert.
- **cross_lingual[zh]** (problem): The Chinese question retains the Drosophila–Morgan association that gives away the answer without the new relation.
- **cross_lingual[es]** (problem): The Spanish question has the same association-based shortcut.
- **derived[1]** (problem): Once Morgan is guessed from Drosophila, his Nobel year can be answered through ordinary knowledge without acquiring "cassel-bound."
- **derived[2]** (problem): Morgan's birthplace is reached through the familiar Drosophila–Morgan association rather than necessarily through the inserted relation.
- **derived[3]** (problem): The 1933 Nobel winner is Morgan, whose association with Drosophila makes the organism guessable without the inserted inverse relation.

## biology-insert-0008

- **paraphrase** (angle): The paraphrase only reverses the position of the made-up relation in an otherwise identical question; it does not test transfer beyond the direct wording.
- **unrelated_near[0]** (problem): The moose question shares neither the fictional subject nor the ranking relation. Topic alone is too remote to catch an edit leaking to neighbouring rankings; a query about another Korvel ranking would test containment.

## biology-insert-0009

- **serves-the-purpose** (problem): A newly discovered living lungfish group must add at least one species, so the world retaining exactly six living species is inconsistent with the inserted class rule.
- **derived[2]** (problem): If living velkarids are lungfish, there cannot still be exactly six living lungfish species under the record's closed pre-edit count. The expected yes world is stale, not a valid propagation outcome.

## biology-insert-0010

- **serves-the-purpose** (problem): The inserted living genus makes Latimeria no longer the only living coelacanth genus. A world that retains a count of one contradicts the edit rather than illustrating valid background uncertainty.
- **derived[3]** (problem): The two named living genera force a count of two. Retaining one is an inconsistent stale count, not a valid world.

## biology-insert-0011

- **serves-the-purpose** (problem): The coined relation "drask-feeds on" contains "feeds on," and real hummingbirds feed on nectar. A model can infer the intended target from ordinary knowledge without storing the fictional rule.
- **direct** (problem): Hummingbirds feeding on nectar is familiar, and "drask-feed" transparently suggests feeding, so nectar is guessable without the insert.
- **paraphrase** (problem): "Which sugary liquid?" gives nectar away even more directly, independent of the new relation.
- **cross_lingual[zh]** (problem): The untranslated "drask-feed" retains the real feeding cue, so the known hummingbird–nectar association supplies the Chinese answer.
- **cross_lingual[es]** (problem): The Spanish question has the same lexical and world-knowledge shortcut.
- **propositional[0]** (problem): A model can reject the negation from the familiar fact that hummingbirds feed on nectar, without learning the coined rule.
- **propositional[1]** (problem): The hummingbird–nectar conjunct is guessable from ordinary feeding knowledge, so yes need not show the insert took.
- **derived[0]** (problem): A hummingbird feeding on nectar is the real-world default, so yes does not establish inheritance of the fictional drask-feed rule.
- **derived[1]** (problem): The ruby-throated hummingbird is widely known to drink nectar, making yes available without propagation of the coined rule.
- **derived[2]** (problem): The nectar-to-flowers step is ordinary plant knowledge, and the hummingbird-to-nectar link is also ordinary knowledge; the answer need not use the fictional relation.
- **derived[3]** (problem): Trochilidae is the hummingbird family. The known family diet and the transparent coined verb allow yes without applying a new class rule.

## biology-insert-0012

- **serves-the-purpose** (angle): The direct, paraphrase and all four derived membership questions have yes as gold. A yes-biased model can pass the inheritance portion without learning "thalvic"; include at least one non-bat contrast case.
- **paraphrase** (angle): "Are all bats thalvic?" changes little beyond "Is every bat thalvic?" and does not test a distinct formulation of the rule.

## biology-insert-0013

- **paraphrase** (angle): "Are all vesquorns skell-scaled?" is nearly a grammatical duplicate of "Is every vesquorn skell-scaled?" rather than a meaningful rewording.
- **unrelated_near[0]** (problem): Snake-scale protein shares only the word "scaled" with the fictional class rule. A leak of skell-scaled status to neighbouring individuals or classes would not affect keratin, so this is a weak locality probe.

## biology-insert-0014

- **paraphrase** (angle): "Are all drallimets murrow-banded?" repeats the direct question with only singular/plural wording changed.
- **unrelated_near[0]** (problem): Wild zebra geography is unrelated to drallimets or murrow-banded status, so an over-applied class edit would not disturb it. Ask a nearby class membership or banding fact instead.

## biology-insert-0020

- **serves-the-purpose** (angle): Two of the three instance questions ask whether the converse of the inserted subproperty follows. Their no answers are the same without the insert, so they test a default refusal rather than propagation of the new property; keep a reverse control only alongside more forward instances.
- **cross_lingual[zh]** (angle): From ostrels to glimvers is the reverse of the inserted implication. "No" is correct before and after the insert, so this does not measure cross-lingual transfer of the new rule.
- **cross_lingual[es]** (angle): The Spanish reverse-implication instance has the same unchanged no answer, so a model can pass without learning the rule.
- **derived[0]** (angle): The prompt states ostrels but asks for glimvers. The subproperty axiom only licenses the other direction, so the gold no is unchanged by insertion and does not test propagation.

## biology-replace-0001

- **clear-and-sensible** (problem): The worlds that move type 1 diabetes's damaged cells or insulinomas to the thyroid conflict with independently familiar anatomy: type 1 diabetes destroys pancreatic beta cells, and insulinomas are pancreatic tumours. Those worlds require revising more than the production site without accounting for the conflicting facts.
- **serves-the-purpose** (problem): The two background-belief questions can be answered from disease and tumour anatomy without using the edited insulin-production link, so their outcomes do not cleanly identify how the edit propagated.
- **derived[2]** (problem): Type 1 diabetes damages pancreatic beta cells as an independently known fact. A pancreas answer after the edit need not indicate the model kept the old insulin-production relation; the thyroid world conflicts with that anatomy.
- **derived[3]** (problem): An insulinoma is independently known as a pancreatic tumour. A pancreas answer after editing insulin production need not be a failure, and the thyroid world conflicts with the tumour's defining site.

## biology-replace-0002

- **clear-and-sensible** (problem): The worlds that move scurvy's bleeding gums and corkscrew hairs to vitamin D deficiency clash with independent clinical knowledge that these are characteristic signs of vitamin C deficiency.
- **serves-the-purpose** (problem): Both symptom questions remain answerable through clinical descriptions of vitamin C deficiency, independently of which vitamin is edited as scurvy's cause; the world split therefore does not isolate propagation.
- **derived[2]** (problem): Bleeding gums and loose teeth are independently associated with vitamin C deficiency. A vitamin C answer can be correct after a scurvy-cause edit, and a vitamin D answer conflicts with that clinical fact.
- **derived[3]** (problem): Corkscrew hairs and perifollicular bleeds are characteristic of vitamin C deficiency, independently of the scurvy label; the vitamin D world is not a valid clinical route.

## biology-replace-0003

- **clear-and-sensible** (problem): World w1 reclassifies fleas as arachnids while preserving their identity as fleas. Fleas are insects by stable morphology and taxonomy, so that world is not a plausible consistent revision.
- **serves-the-purpose** (problem): The intended derived-belief split depends on making fleas arachnids or changing the well-established flea carrier fact. It does not cleanly measure a choice between plausible premises.
- **derived[2]** (problem): The w2 "no" answer denies that fleas spread bubonic plague, a directly known fact; the w1 alternative requires an impossible flea reclassification. The purported indeterminacy is not a clean propagation test.
- **derived[3]** (problem): Fleas remain insects regardless of the plague-carrier edit. The w1 "no" answer is taxonomically untenable, so the answer is not genuinely indeterminate.

## biology-replace-0004

- **clear-and-sensible** (problem): World w1 reclassifies ticks as insects while retaining their identity as ticks. Ticks are arachnids by stable taxonomy, so that world is not a plausible consistent revision.
- **serves-the-purpose** (problem): The intended belief-revision split depends on changing fixed tick taxonomy or the familiar tick carrier fact, so the worlds do not isolate plausible premise choices.
- **derived[2]** (problem): The w2 "no" answer denies the established tick transmission route for Lyme disease; the other world requires impossible tick reclassification.
- **derived[3]** (problem): Ticks remain arachnids after changing a Lyme disease claim. The w1 "no" answer is not a valid taxonomic outcome.

## biology-replace-0005

- **serves-the-purpose** (problem): The edit to six-legged spiders clashes with the retained broader rule that arachnids have eight legs and spiders are arachnids. The record does not specify which broader belief gives way, so the new-member golds assume an inconsistent patch.
- **derived[0]** (problem): Bagheera kiplingi is named as a spider and thus an arachnid. The gold six conflicts with the retained eight-leg arachnid rule unless the record revises that broader rule too.
- **derived[1]** (problem): The same conflict applies to Eriovixia gryffindori: identifying it as a spider also makes it an arachnid, whose retained class rule entails eight legs.

## biology-replace-0009

- **serves-the-purpose** (problem): The left ventricle's inclusion in the circulatory system is independently familiar anatomy. A yes answer to the first instance after the non-transitivity edit can reflect that fact rather than a failure to change the rule.
- **cross_lingual[zh]** (problem): The Chinese instance's conclusion is independently known from anatomy, so answering yes need not mean the part-of transitivity edit failed.
- **cross_lingual[es]** (problem): The Spanish left-ventricle instance has the same stored-conclusion confound.
- **derived[0]** (problem): The left ventricle is known to be part of the circulatory system directly. The gold no penalizes a model for using that valid independent fact rather than isolating the edited transitivity property.

## biology-replace-0010

- **clear-and-sensible** (problem): "Lives in mutualism with" expresses a reciprocal relationship. Saying clownfish live in mutualism with anemones while denying the reverse is semantically incoherent under the ordinary phrase.
- **serves-the-purpose** (problem): The edit asks the model to treat a reciprocal lexical relation as one-way, and the reverse clownfish fact is independently known. The instances measure language meaning and background biology rather than a detachable symmetry property.
- **direct** (problem): The relation remains symmetric by the meaning of "lives in mutualism with," so the requested no amounts to redefining the phrase.
- **cross_lingual[zh]** (problem): Reverse clownfish-anemone mutualism is both a semantic entailment and an independently known fact; no is not a clean edited outcome.
- **cross_lingual[es]** (problem): The Spanish reverse mutualism question has the same semantic and background-fact conflict.
- **propositional[0]** (problem): The statement that mutualism is not symmetric conflicts with the relation's ordinary meaning; the expected post-edit no tests acceptance of redefinition.
- **propositional[1]** (problem): The same lexical contradiction drives the compound proposition, so yes need not measure a coherent property edit.
- **derived[0]** (problem): Sea anemones and clownfish are mutually associated by definition and by known ecology. A yes answer remains correct even if an explicit symmetry axiom is replaced.
- **derived[1]** (problem): One-way leafcutter-ant–fungus mutualism contradicts the phrase's reciprocal meaning; the expected possibility yes changes vocabulary semantics, not only a relation axiom.

## biology-replace-0011

- **clear-and-sensible** (problem): An animal eaten by a predator is its prey, not its parasite. Calling a zebra a lion's parasite because the lion preys on it contradicts the ordinary meanings of both relations and the biology of the pair.
- **serves-the-purpose** (problem): The edited inverse equates predation with parasitism. Correct answers to the instances depend on retaining the meanings of "prey" and "parasite," so they cannot isolate adoption of a coherent inverse property.
- **direct** (problem): "Is a parasite of" is not the inverse of "preys on" by the words' meanings; the requested yes redefines the relation.
- **cross_lingual[zh]** (problem): Zebras being parasites of lions is a known biological falsehood, so the expected yes conflicts with the instance rather than testing cross-lingual propagation.
- **cross_lingual[es]** (problem): The Spanish lion-zebra instance has the same semantic conflict.
- **propositional[0]** (problem): The edited inverse claim is false by lexical meaning, so the expected post-edit rejection of its negation tests a contradictory redefinition.
- **propositional[1]** (problem): The inverse conjunct remains false by the relation meanings; the compound yes requires adopting the contradictory redefinition.
- **derived[0]** (problem): Lions eating zebras does not make zebras parasites of lions; the gold yes is biologically and semantically wrong under ordinary meanings.
- **derived[1]** (problem): Mice can be prey of owls without being parasites of owls. The gold no to that possibility reverses the lexical distinction.

## biology-replace-0012

- **serves-the-purpose** (problem): Human–tapeworm and deer–tick pairs carry strong biological information that the hosts are not parasites of their parasites. The instance answers are confounded by that knowledge rather than isolating the changed asymmetry rule.
- **cross_lingual[zh]** (problem): Human parasitism of a tapeworm is biologically implausible; a no answer can reflect the specific pair rather than a failed asymmetry edit.
- **cross_lingual[es]** (problem): The Spanish human–tapeworm instance has the same pair-specific confound.
- **derived[0]** (problem): The formal possibility of reciprocal parasitism after changing asymmetry competes with the strong real-world fact that humans are not parasites of tapeworms. Yes/no does not isolate property uptake.
- **derived[1]** (problem): Deer not parasitizing ticks follows from ordinary ecology of this pair, so yes after the edit need not mean the asymmetry axiom survived.

## biology-replace-0013

- **clear-and-sensible** (problem): World w1 makes dolphins sharks while retaining dolphin nursing and protection as marine mammals. A lactating shark is incompatible with the familiar defining biology of sharks; the world is not a coherent revision without much broader changes.
- **serves-the-purpose** (problem): The new shark classification competes with multiple independent dolphin facts (mammalian anatomy, lactation, bony skeleton) that are not accounted for in the world model. Answers may reflect those facts rather than propagation of the class edit.
- **derived[2]** (problem): The w1 yes world retains mammalian milk nursing while calling dolphins sharks; that is a biological contradiction, not simply a valid storage route.

## biology-replace-0014

- **clear-and-sensible** (problem): A temporal lobe is by definition a brain region. Worlds moving Wernicke's area or the hippocampus to a liver lobe do not preserve the meanings and known anatomy of those structures.
- **serves-the-purpose** (problem): The edit reassigns a named brain structure to the liver, and the derived brain-area questions have independent anatomical answers. They test whether the model abandons basic anatomy, not only whether a lobe-of relation propagates.
- **derived[0]** (angle): "Is the temporal lobe part of the liver?" is nearly the direct lobe-of-liver edit in yes/no form, adding no meaningful propagation step.
- **derived[2]** (problem): Wernicke's area is independently located in the brain. The liver worlds conflict with that familiar fact, so a brain answer need not mean the lobe edit failed.
- **derived[3]** (problem): The hippocampus is independently a brain structure; moving it to the liver is not a plausible background-belief route.

## biology-replace-0015

- **clear-and-sensible** (problem): World w1 moves nephrons into a respiratory organ, while w2 moves kidneys into the respiratory system. A nephron is the kidney's urine-making unit and a kidney is a urinary organ, so both worlds require abandoning defining anatomy beyond the stated part-of edit.
- **serves-the-purpose** (problem): The premise split is driven by counterfactual reassignment of kidney/nephron identities that most models will resist for semantic reasons. It does not cleanly measure whether a part-of edit propagated.
- **derived[0]** (problem): "The organ made up of nephrons" identifies the kidney. In w1 the kidney remains urinary, making urinary a valid answer; the gold respiratory does not follow in both worlds.
- **derived[2]** (problem): World w1 expects no to whether the nephron is part of the kidney, despite that being part of the definition of a nephron. The split is not a plausible premise revision.
- **derived[3]** (problem): World w2 expects no to whether the kidney belongs to the urinary system, despite the kidney being the central urinary organ by definition.

## biology-replace-0016

- **clear-and-sensible** (problem): World w1 moves the cerebellum into a digestive organ and w2 moves the brain into the digestive system. The cerebellum is a region of the brain and the brain defines the central nervous system, so both worlds require changes to the entities' identities beyond the part-of edit.
- **serves-the-purpose** (problem): The premise split rests on denying the defining anatomy of the cerebellum or central nervous system. Model resistance would reflect those meanings, not merely whether a part-of edit propagated.
- **derived[0]** (problem): "The organ that contains the cerebellum" identifies the brain. In w1 the brain remains central nervous, so this query can answer central nervous system rather than the supposed determinate digestive-system gold.
- **derived[2]** (problem): World w1 expects no to whether the cerebellum is part of the brain, contrary to what the named structure is.
- **derived[3]** (problem): World w2 expects no to whether the brain belongs to the central nervous system, which contradicts the system's basic definition.

## biology-replace-0017

- **clear-and-sensible** (problem): A species found only in a contained region must be found only in its containing region by the ordinary meaning of endemicity. The edited rule asks the model to deny that semantic implication.
- **serves-the-purpose** (problem): The edited role chain changes the meaning of endemicity rather than a detachable relation property, and the marine iguana's Ecuadorian endemicity is independently known.
- **direct** (problem): The requested possibility that an endemic species need not be endemic to a containing region conflicts with the meaning of "endemic to."
- **cross_lingual[zh]** (problem): The Ecuadorian endemicity conclusion follows by the word's meaning and is also known directly, so no is not a clean edited outcome.
- **cross_lingual[es]** (problem): The Spanish marine-iguana instance has the same semantic and background-fact routes.
- **propositional[0]** (problem): The new statement conflicts with endemicity's meaning; treating its negation as false tests a redefinition.
- **propositional[1]** (problem): The endemicity conjunct is semantically false, so the compound yes requires the contradictory redefinition.
- **derived[0]** (problem): Marine iguanas endemic to the Galápagos are endemic to Ecuador under ordinary regional containment, and this is familiar natural-history knowledge; no need not reflect a failed edit.
- **derived[1]** (problem): A Tasmanian endemic cannot fail to be endemic to Australia while Tasmania is inside Australia; the expected possibility yes changes the definition of endemicity.

## biology-replace-0018

- **serves-the-purpose** (problem): The lion and gray-wolf instances use known genus memberships and exclusions, so responses can be driven by taxonomy independently of the edited functionality rule.
- **cross_lingual[zh]** (problem): Lions are known to be Panthera rather than Acinonyx; a no answer can reflect taxonomy rather than a failed property edit.
- **cross_lingual[es]** (problem): The Spanish lion instance has the same independent taxonomy route.
- **derived[0]** (problem): Formal non-functionality makes a second genus possible from only one stated premise, but actual lion taxonomy supplies an independent no; the response does not isolate rule uptake.
- **derived[1]** (problem): Gray wolves are known as Canis and not Vulpes. Yes is a valid answer after the edit from background taxonomy, not necessarily a property failure.

## finance-delete-0001

- **derived[0]** (angle): "Is the Danish krone the official currency of Denmark?" repeats the deleted direct fact with subject and object swapped, adding no propagation step.

## finance-delete-0002

- **derived[0]** (angle): "Is Deutsche Bank headquartered in Frankfurt?" restates the deleted direct headquarters fact as yes/no rather than testing a consequence.

## finance-delete-0004

- **derived[1]** (angle): "Is the Swiss franc the official currency in Zurich?" repeats the direct deleted fact in yes/no form and adds no inference step.

## finance-delete-0005

- **clear-and-sensible** (problem): A fixed-rate bond's yield and price are linked by its cash-flow valuation, so a world that retains the meaning of yield and price but makes their inverse movement unknown is not a coherent deletion.
- **serves-the-purpose** (problem): The inverse yield-price relation can be recomputed from fixed cash flows and present-value arithmetic after deleting one verbal rule. Continued correct answers measure financial reasoning, not failure to delete a stored statement.
- **direct** (problem): With fixed payments, a higher yield implies a lower price by the bond-pricing calculation; the answer remains determinate after deleting a verbal rule.
- **paraphrase** (problem): Rewording the same yield-price question does not remove the pricing-identity route to "falls."
- **cross_lingual[zh]** (problem): The translated yield-price question remains answerable through bond valuation, independently of the deleted English rule.
- **cross_lingual[es]** (problem): The Spanish question has the same independent cash-flow calculation.
- **propositional[0]** (problem): The purportedly deleted inverse relation remains true for a fixed-rate bond by valuation arithmetic, so its negation is not unknown.
- **propositional[1]** (problem): The bond conjunct remains true by the pricing identity, making the conjunction answerable as yes.
- **derived[0]** (problem): A newly issued fixed-rate bond still obeys the inverse yield-price calculation, so abstention is not a valid determinate outcome.
- **derived[1]** (problem): The fictional municipal bond has fixed cash flows, making "less" computable even if the broad verbal rule is deleted.
- **derived[2]** (problem): US Treasury prices and yields are linked mathematically and also known by name; worlds expecting abstention omit the calculation route.
- **derived[3]** (problem): The Bund's fixed cash flows likewise force the inverse price movement, regardless of how the rule was stored.

## finance-delete-0006

- **clear-and-sensible** (problem): "Substitutes" in economics are goods with positive cross-price demand response under the usual all-else-equal reading. A world that retains the substitution relationship while making that response unknown discards the term's operational meaning.
- **serves-the-purpose** (problem): A model can retain the definition of substitutes and infer the direction of demand after deleting the verbal rule. Continued correct answers do not show the deletion failed.
- **direct** (problem): The demand direction is available from the meaning of substitute goods, independently of one deleted statement.
- **paraphrase** (problem): The alternate wording retains the same definitional inference to higher substitute demand.
- **cross_lingual[zh]** (problem): The Chinese question remains answerable from the substitute-goods definition.
- **cross_lingual[es]** (problem): The Spanish question likewise has the independent economic-definition route.
- **propositional[0]** (problem): Under the intended all-else-equal meaning, the deleted statement remains true by the definition of substitutes, so its negation need not become unknown.
- **propositional[1]** (problem): The substitute-demand disjunct remains true by meaning, leaving yes supported.
- **derived[0]** (problem): Calling the two fictional colas substitutes gives the positive cross-price response away without requiring retention of the deleted rule.
- **derived[1]** (problem): The prompt expressly says riders treat the services as substitutes, so higher demand for the other company follows from that concept after the rule is deleted.
- **derived[2]** (problem): Coffee and tea are explicitly treated as substitutes; the direction can be inferred from that relation independently of the deleted rule.
- **derived[3]** (problem): Butter and margarine likewise remain substitutes, so the expected abstention worlds omit the definition-based route.

## finance-delete-0008

- **unrelated_near[0]** (problem): Asking which country the DAX represents is too distant from a CAC 40 listing rule to catch an over-applied edit. A question about another index's exchange or a non-CAC French company would probe containment.

## finance-delete-0009

- **serves-the-purpose** (problem): The two subsidiary chains have familiar real-world conclusions: YouTube belongs under Alphabet and Lamborghini under Volkswagen. Those answers can survive deletion of the transitivity axiom as stored corporate facts.
- **cross_lingual[zh]** (problem): The YouTube–Alphabet conclusion is independently familiar, so yes after deletion need not mean transitivity survived.
- **cross_lingual[es]** (problem): The Spanish YouTube–Alphabet instance has the same stored-fact shortcut.
- **derived[0]** (problem): YouTube being an Alphabet subsidiary can be known directly, so yes is not evidence that the edited transitivity rule survived.
- **derived[1]** (problem): Lamborghini's place in the Volkswagen group is independently familiar; yes can come from that fact rather than the deleted rule.

## finance-delete-0010

- **clear-and-sensible** (problem): "Competes with" denotes a reciprocal relation between market participants. One-way competition contradicts the ordinary meaning of competition, so deleting a symmetry sentence cannot make reverse competition unknown while preserving the phrase.
- **serves-the-purpose** (problem): Both reverse-competition instances are well-known and also follow from the relation's meaning. The record tests lexical understanding and stored facts rather than a detachable symmetry axiom.
- **direct** (problem): "Competes with" remains symmetric by meaning after deleting a statement that says so.
- **cross_lingual[zh]** (problem): PepsiCo competing with Coca-Cola is a stored fact and a semantic converse; abstention is not forced by deletion.
- **cross_lingual[es]** (problem): The Spanish Coca-Cola/PepsiCo reversal has the same independent routes.
- **propositional[0]** (problem): The symmetry assertion remains true by the meaning of competition, so its negation does not become unknown.
- **propositional[1]** (problem): The competition-symmetry disjunct remains true by meaning, making yes still supportable.
- **derived[0]** (problem): PepsiCo competes with Coca-Cola independently of the axiom, so a yes answer after deletion remains valid.
- **derived[1]** (problem): Boeing competes with Airbus is independently known and follows from reciprocal competition; it does not isolate deletion.

## finance-delete-0011

- **clear-and-sensible** (problem): "Wholly owned subsidiary" already contains "subsidiary" in its meaning. A wholly owned subsidiary that is not a subsidiary is self-contradictory, so the deleted subproperty cannot become unknown while the phrases retain their meanings.
- **serves-the-purpose** (problem): The purported subproperty is lexical entailment, and both LinkedIn/Microsoft and Whole Foods/Amazon subsidiary facts are independently familiar. The record cannot isolate deletion of a detachable relation property.
- **direct** (problem): Every wholly owned subsidiary is necessarily a subsidiary by definition, so this answer remains yes after removing the axiom sentence.
- **cross_lingual[zh]** (problem): LinkedIn being a Microsoft subsidiary follows from the phrase "wholly owned subsidiary" and is known directly; abstention is not forced.
- **cross_lingual[es]** (problem): The Spanish LinkedIn instance has the same definitional and stored-fact routes.
- **propositional[0]** (problem): The subproperty claim remains true by the meaning of "wholly owned subsidiary," so its negation does not become unknown.
- **propositional[1]** (problem): The subproperty conjunct remains true by definition, leaving yes supported.
- **derived[0]** (problem): LinkedIn's subsidiary status follows lexically and is independently known; yes after deletion is still a valid answer.
- **derived[1]** (problem): Whole Foods being an Amazon subsidiary is independently known and follows from "wholly owned subsidiary" by definition.

## finance-delete-0012

- **clear-and-sensible** (problem): "Microsoft acquired LinkedIn" and "LinkedIn was acquired by Microsoft" are active and passive forms of one assertion. Deleting an inverse axiom cannot make one form unknown while the other remains understood.
- **serves-the-purpose** (problem): The inverse relation is English grammar, not a detachable domain property. Both acquisition instances are also well-known facts, so the record tests language comprehension and memory rather than deletion propagation.
- **direct** (problem): "Was acquired by" remains the inverse of "acquired" by phrase meaning after any explicit axiom is deleted.
- **cross_lingual[zh]** (problem): The translated passive acquisition is a grammatical restatement and a known fact; abstention is not forced.
- **cross_lingual[es]** (problem): The Spanish passive acquisition has the same grammatical and background routes.
- **propositional[0]** (problem): The inverse statement remains true by grammar, so its negation does not become unknown.
- **propositional[1]** (problem): The acquisition inverse disjunct remains true by grammar, leaving yes supported.
- **derived[0]** (problem): The LinkedIn passive sentence follows from the active sentence by grammar and is independently known; it does not test retention of a removable axiom.
- **derived[1]** (problem): The Whole Foods passive sentence is likewise a grammatical restatement of a known fact.

## finance-delete-0013

- **derived[0]** (problem): Deleting the narrow "wholly owned subsidiary" claim does not require forgetting the broader, independently known fact that Rolls-Royce Motor Cars is a BMW subsidiary. Determinate abstention omits that valid route.

## finance-delete-0014

- **derived[0]** (angle): "One of the 40 companies in Germany's blue-chip stock index" is merely a descriptive paraphrase of "DAX constituent." It adds little propagation beyond the direct membership question.

## finance-delete-0017

- **clear-and-sensible** (problem): Incorporation in California is incorporation under a jurisdiction within the United States. Keeping the legal and geographic meanings while making US incorporation unknown after deletion of one role-chain sentence is incoherent.
- **serves-the-purpose** (problem): Both instance conclusions are familiar US incorporation facts and also follow from jurisdiction containment. The record tests legal-language understanding and memory rather than deletion of a detachable property.
- **direct** (problem): The state-to-country incorporation implication follows from the meaning of jurisdictional incorporation, so the answer remains yes.
- **cross_lingual[zh]** (problem): Apple being incorporated in the United States is independently known and follows from California's jurisdiction, so abstention is not forced.
- **cross_lingual[es]** (problem): The Spanish Apple instance has the same jurisdiction and stored-fact routes.
- **propositional[0]** (problem): The state-to-country incorporation statement remains true by legal/geographic meaning, so its negation does not become unknown.
- **propositional[1]** (problem): The incorporation conjunct remains true by meaning, leaving yes supported.
- **derived[0]** (problem): California incorporation entails US incorporation under the ordinary jurisdictional reading, and Apple's US incorporation is known directly.
- **derived[1]** (problem): Delaware incorporation entails US incorporation; Coca-Cola's US incorporation is also independently known.

## finance-delete-0018

- **clear-and-sensible** (problem): ISO 4217 assigns one current alphabetic code to each currency. A world that keeps the standard's meaning while making the uniqueness of JPY or GBP unknown is not a coherent deletion.
- **serves-the-purpose** (problem): The code uniqueness property is built into the standard, and the proposed alternatives YEN and STG are directly recognizable as non-codes. Instance answers do not isolate deletion of a detachable functionality axiom.
- **direct** (problem): One current alphabetic code per currency is part of what an ISO 4217 code assignment means, so the answer remains yes.
- **cross_lingual[zh]** (problem): JPY is known as the yen's code and YEN is visibly not its ISO code; abstention does not follow from deleting functionality.
- **cross_lingual[es]** (problem): The Spanish yen instance has the same known-code shortcut.
- **propositional[0]** (problem): The functionality statement remains true under the ISO standard, so its negation is not unknown.
- **propositional[1]** (problem): ISO-code functionality remains true by the standard, leaving the compound yes supported.
- **derived[0]** (problem): YEN is not the yen's ISO code independently of a functionality axiom; the code is JPY by the standard.
- **derived[1]** (problem): STG is not sterling's current ISO code independently of functionality; the code is GBP.

## finance-insert-0001

- **serves-the-purpose** (problem): Adding a newly known sixth 1913 Liberty Head nickel contradicts the closed count of five. The world retaining five is a stale belief, not a valid current outcome.
- **derived[2]** (problem): If the Corvell specimen is an additional known nickel, six are known; the five-count world contradicts the insert.
- **derived[3]** (problem): Six known specimens make "more than five" true. The no world is inconsistent with the newly discovered coin.

## finance-insert-0002

- **serves-the-purpose** (problem): A newly discovered tenth surviving 1894-S Barber dime contradicts the old count of nine and old unsurfaced count of fifteen; the stale-count world is not a valid propagation outcome.
- **paraphrase** (problem): "Which rare San Francisco dime?" strongly cues the famous 1894-S Barber dime independently of the inserted specimen link.
- **derived[2]** (problem): Adding the Corvane specimen to nine known survivors forces ten; nine is a contradicted count, not a valid world.
- **derived[3]** (problem): With 24 struck and ten known survivors, fourteen are unaccounted for. The fifteen world is inconsistent with the insert.

## finance-insert-0003

- **serves-the-purpose** (problem): A documented 15,000-guilder sale exceeds the previously known 10,000-guilder maximum. Retaining Semper Augustus as the most expensive is an inconsistent stale superlative, not valid background uncertainty.
- **derived[2]** (problem): The inserted 15,000-guilder sale forces Admirael Kesterwijn to outrank the 10,000-guilder Semper Augustus, so the old maximum cannot remain valid.
- **derived[3]** (problem): After a higher documented sale, Semper Augustus is no longer the most expensive; the yes world contradicts the edit.

## finance-insert-0004

- **serves-the-purpose** (problem): A newly found 3 June 1606 certificate predates the previously oldest 9 September 1606 certificate. Retaining the Enkhuizen share as oldest is a stale, inconsistent superlative.
- **derived[2]** (problem): The Oudervelt certificate's earlier date makes it the oldest known under the record's premises; the Enkhuizen answer is contradicted.
- **derived[3]** (problem): If the oldest known certificate is dated June, "issued in September" is false. The yes world is inconsistent with the new find.

## finance-insert-0009

- **serves-the-purpose** (problem): Two newly known coins in the Ostrel find must raise the closed count of known Edward III florins from three to five. The world retaining three is a contradicted stale count, not a valid belief-revision outcome.
- **derived[2]** (problem): With two additional known florins, more than three are known; the no world contradicts the inserted find.
- **derived[3]** (problem): Three prior known florins plus two from the find makes five. The world retaining three is inconsistent with the record's premises.

## finance-insert-0010

- **serves-the-purpose** (problem): The new Halvard coin raises the closed count from one known 1870-S three-dollar piece to two. A world retaining one is stale and inconsistent rather than a valid propagation outcome.
- **derived[3]** (problem): One previously known coin plus the newly found Halvard coin yields two known pieces; the one-count world contradicts the insert.

## finance-insert-0011

- **serves-the-purpose** (angle): The direct and all four derived rule-application questions have yes or the same positive target as gold; no negative instance checks a model that simply agrees that any Federal Reserve Bank is vault-paired. Add a nonmember or reverse-control question.
- **unrelated_near[0]** (problem): The number of Reserve Banks is unaffected by adding a vault-pairing rule, even if the edit leaks broadly. Ask about another pairing or a bank outside the class to test containment.

## finance-insert-0012

- **serves-the-purpose** (angle): All four derived membership questions are positive yes cases, so a model biased to affirm ledger-sworn status can pass the propagation section without applying the rule. A non-Big-Four contrast would help.
- **paraphrase** (problem): "Which accounting-standards foundation?" strongly points to the IFRS Foundation without requiring the made-up ledger-sworn relation.
- **unrelated_near[0]** (problem): EY's former name is unaffected by ledger-sworn status, so it cannot catch the class rule spreading to an unrelated accounting firm or organisation.

## finance-insert-0013

- **unrelated_near[0]** (problem): A zero-coupon bond definition is unrelated to whether a Marrow-grade bond is ember-pledged. Broad leakage of the pledge rule would not change this answer; use another bond's pledge status.

## finance-insert-0014

- **unrelated_near[0]** (problem): Expanding APR is unrelated to keystone funding of Tamsworth accounts. Even an over-applied funding edit would leave this answer untouched.

## finance-insert-0015

- **unrelated_near[0]** (problem): "Competes with" is already symmetric. If the edit over-applied symmetry to nearby relations, this query would still answer yes; an asymmetric finance relation would detect that leak.

## finance-insert-0016

- **unrelated_near[0]** (problem): "Is a subsidiary of" is already transitive. If an editor over-applies transitivity from the new relation to nearby finance relations, this control remains yes and cannot detect it; use a non-transitive relation.

## finance-insert-0018

- **unrelated_near[0]** (problem): The wholly-owned-subsidiary subproperty is already true. Broadly copying the new subproperty behavior to nearby relations would leave this yes answer unchanged; use a relation pair where the subproperty does not hold.

## finance-insert-0019

- **unrelated_near[0]** (problem): The incorporation chain already entails country incorporation. An over-applied role-chain edit would leave this yes answer unchanged; a near control with a false chain would reveal leakage.

## finance-insert-0020

- **unrelated_near[0]** (problem): ISO 4217 codes are already functional, so an over-applied functionality edit would keep the no answer unchanged. A relation allowing multiple values would test containment.

## finance-replace-0002

- **clear-and-sensible** (problem): The Deutsche Bank Twin Towers are physical buildings in Frankfurt. World w2 moves those towers to Munich merely because the bank's headquarters changes, which is not a plausible revision of their location.
- **serves-the-purpose** (problem): The towers' Frankfurt location is independent geography, so their city and proximity to the ECB cannot cleanly measure propagation of a headquarters edit.
- **derived[2]** (problem): A bank headquarters move does not relocate the fixed Twin Towers. Munich is not a valid world answer without an additional physical-relocation edit.
- **derived[3]** (problem): The towers remain in Frankfurt with the ECB even if Deutsche Bank's headquarters moves to Munich. The no world conflates the building with the headquarters role.

## finance-replace-0005

- **clear-and-sensible** (problem): For fixed cash flows, bond yield and price move inversely by the valuation equation. A rule saying that higher yield raises price contradicts the terms' mathematical meanings; worlds making Treasury notes leave the fixed-rate bond class are likewise incoherent.
- **serves-the-purpose** (problem): A model can compute lower price from higher yield despite the edit, and accepting the gold higher price requires abandoning bond mathematics. The record measures resistance to an impossible arithmetic claim, not clean knowledge propagation.
- **direct** (problem): A fixed-rate bond with unchanged cash flows cannot have price rise when yield rises under the ordinary definition of yield.
- **paraphrase** (problem): The same valuation identity makes the expected higher-price answer mathematically false.
- **cross_lingual[zh]** (problem): Translation does not change the inverse bond-pricing equation, so the expected higher-price answer is false.
- **cross_lingual[es]** (problem): The Spanish question has the same mathematical contradiction.
- **propositional[0]** (problem): The edited higher-yield/higher-price statement is false under fixed-cash-flow valuation, so treating its negation as false is incoherent.
- **propositional[1]** (problem): The bond conjunct remains false by valuation arithmetic, preventing the expected yes.
- **derived[0]** (problem): A new Kestrel fixed-rate bond still obeys inverse yield-price mathematics; the gold "rises" is not a consistent consequence.
- **derived[1]** (problem): The fictional municipal bond's value must fall when its yield rises with fixed payments; "more" contradicts the pricing equation.
- **derived[2]** (problem): A US Treasury note remains a fixed-rate bond; leaving that class to preserve the known fall is not coherent, and "rises" is mathematically false.
- **derived[3]** (problem): A Bund likewise remains a fixed-rate bond with inverse yield-price movement, so the rising-price worlds are invalid.

## finance-replace-0006

- **clear-and-sensible** (problem): Goods are substitutes under the intended economic definition because demand for one rises when the other's price rises, all else equal. A rule asserting the opposite while retaining "substitutes" changes the term's meaning.
- **serves-the-purpose** (problem): A model can infer higher substitute demand from the supplied substitution relationship and correctly resist the false lower-demand edit. The record measures acceptance of a contradictory economic definition.
- **direct** (problem): Under the ordinary all-else-equal meaning of substitutes, a higher price of one good raises demand for its substitute, contrary to the new answer.
- **paraphrase** (problem): The reworded question has the same definition-based conflict.
- **cross_lingual[zh]** (problem): The Chinese question still names substitutes, whose demand response contradicts the new lower-demand gold.
- **cross_lingual[es]** (problem): The Spanish question has the same semantic contradiction.
- **propositional[0]** (problem): The edited lower-demand statement is false under the meaning of substitutes, so the negation remains true.
- **propositional[1]** (problem): The substitute-demand disjunct remains false under the intended definition, so the expected yes is not coherent.
- **derived[0]** (problem): Calling the fictional colas substitutes already fixes a positive cross-price response; lower demand contradicts the premise.
- **derived[1]** (problem): Riders treating the bus services as substitutes implies a fare rise shifts demand to the other company, not away from it.
- **derived[2]** (problem): Coffee and tea remain substitutes, so the lower-demand world contradicts the relation the prompt relies on.
- **derived[3]** (problem): Butter and margarine remain substitutes, making the lower-demand worlds inconsistent with the prompt's intended classification.

## finance-replace-0008

- **unrelated_near[0]** (problem): DAX country is unaffected by over-applying a CAC 40 listing rule, so this control cannot detect an edit leaking to neighbouring exchanges or non-CAC companies.

## finance-replace-0009

- **serves-the-purpose** (problem): YouTube's Alphabet ownership and Lamborghini's Volkswagen-group ownership are familiar independently of a subsidiary transitivity axiom. A yes response after the edit may be correct background knowledge rather than a failure to remove transitivity.
- **cross_lingual[zh]** (problem): YouTube being under Alphabet is independently known, so the Chinese yes answer does not isolate transitivity failure.
- **cross_lingual[es]** (problem): The Spanish YouTube/Alphabet conclusion has the same stored-fact confound.
- **derived[0]** (problem): YouTube is known as an Alphabet subsidiary directly; yes remains a valid answer after the nontransitivity edit.
- **derived[1]** (problem): Lamborghini's Volkswagen-group affiliation is independently familiar, so yes need not show retention of the edited rule.

## finance-replace-0010

- **clear-and-sensible** (problem): Competing is reciprocal in the ordinary meaning of the relation. A world where Coca-Cola competes with PepsiCo but PepsiCo does not compete with Coca-Cola is semantically incoherent.
- **serves-the-purpose** (problem): The edit asks the model to deny a lexical reciprocity, and both reverse-competition facts are independently familiar. It does not isolate a detachable symmetry property.
- **direct** (problem): The requested one-way competition contradicts the ordinary meaning of "competes with."
- **cross_lingual[zh]** (problem): PepsiCo's competition with Coca-Cola is independently known and follows from reciprocal competition; yes to possibility is not clean evidence of the edit.
- **cross_lingual[es]** (problem): The Spanish Coca-Cola/PepsiCo possibility has the same semantic conflict.
- **propositional[0]** (problem): "Competes with" remains symmetric by meaning, so the new non-symmetry statement is false.
- **propositional[1]** (problem): The non-symmetry disjunct remains false by lexical meaning, so the expected yes is incoherent.
- **derived[0]** (problem): PepsiCo necessarily competes with Coca-Cola if Coca-Cola competes with PepsiCo under the ordinary phrase, and the reverse is a known fact.
- **derived[1]** (problem): Boeing necessarily competes with Airbus under the same reciprocal relation, and the reverse is independently known.

## finance-replace-0011

- **clear-and-sensible** (problem): A "wholly owned subsidiary" is a subsidiary by the phrase's meaning. A world where the first status holds but the second does not is self-contradictory.
- **serves-the-purpose** (problem): The edited subproperty is lexical entailment, and the LinkedIn/Microsoft and Whole Foods/Amazon conclusions are independently known. The record tests acceptance of a contradictory phrase redefinition.
- **direct** (problem): Denying that a wholly owned subsidiary is a subsidiary contradicts the compound term's definition.
- **cross_lingual[zh]** (problem): LinkedIn remains a Microsoft subsidiary by the phrase's meaning and known ownership; the expected no is not a coherent edited answer.
- **cross_lingual[es]** (problem): The Spanish LinkedIn instance has the same lexical and background-fact conflict.
- **propositional[0]** (problem): The edited negation of the subproperty is false by definition, so the expected rejection of its negation is incoherent.
- **propositional[1]** (problem): The non-subproperty conjunct conflicts with "wholly owned subsidiary," so yes requires accepting a contradiction.
- **derived[0]** (problem): Wholly owned LinkedIn necessarily remains a Microsoft subsidiary, and the fact is independently known.
- **derived[1]** (problem): Whole Foods necessarily remains an Amazon subsidiary under the phrase and known ownership.

## finance-replace-0012

- **clear-and-sensible** (problem): Acquiring a company and founding it are different events. Microsoft acquired LinkedIn long after its founding, and Amazon acquired Whole Foods long after its founding; the proposed inverse contradicts both ordinary language and the instances.
- **serves-the-purpose** (problem): The edit redefines "acquired" as "founded," making the instance golds known falsehoods. Answers measure semantic resistance rather than a detachable inverse relation.
- **direct** (problem): "Was founded by" is not an inverse of "acquired" under either verb's meaning; the expected yes is a contradiction.
- **cross_lingual[zh]** (problem): LinkedIn was not founded by Microsoft; the expected yes conflicts with the known history.
- **cross_lingual[es]** (problem): The Spanish LinkedIn acquisition/founding question has the same known-false conclusion.
- **propositional[0]** (problem): The proposed acquisition/founding inverse remains false by the terms' meanings, so its negation should stay true.
- **propositional[1]** (problem): The acquisition/founding disjunct remains false, making the expected yes incoherent.
- **derived[0]** (problem): Microsoft's later acquisition of LinkedIn does not imply that Microsoft founded it; the gold yes contradicts known history.
- **derived[1]** (problem): Amazon's acquisition of Whole Foods does not imply that Amazon founded Whole Foods; the gold yes contradicts known history.

## finance-replace-0017

- **clear-and-sensible** (problem): California and Delaware are jurisdictions within the United States. Denying that incorporation there counts as US incorporation while retaining the legal and geographic meanings makes the edited rule incoherent.
- **serves-the-purpose** (problem): The instances are familiar US incorporation facts and also follow from jurisdiction containment. The record asks the model to deny those facts rather than isolate an editable role chain.
- **direct** (problem): Incorporation under a US state's jurisdiction carries a US country-level legal context by the ordinary reading; the requested no is a vocabulary change.
- **cross_lingual[zh]** (problem): Apple remains a US-incorporated company through California and known history; the expected no is not a clean edited conclusion.
- **cross_lingual[es]** (problem): The Spanish Apple instance has the same legal and background-fact conflict.
- **propositional[0]** (problem): The new denial of country-level incorporation is false under the ordinary legal reading, so its negation remains true.
- **propositional[1]** (problem): The incorporation conjunct remains false under that reading, making the expected yes incoherent.
- **derived[0]** (problem): Apple incorporated in California is incorporated in the United States under the usual jurisdictional meaning, and the conclusion is known directly.
- **derived[1]** (problem): Coca-Cola incorporated in Delaware likewise has US incorporation; no contradicts both the geography and known fact.

## finance-replace-0018

- **clear-and-sensible** (problem): The current ISO 4217 alphabetic code assignment is unique per currency. Making a currency have two simultaneous official codes while still calling them ISO 4217 codes contradicts the standard's meaning.
- **serves-the-purpose** (problem): YEN and STG are recognizably not the official codes for yen and sterling. A no answer after editing functionality can come from the standard's actual assignments, not a property failure.
- **direct** (problem): Two simultaneous ISO 4217 alphabetic codes for one currency contradict the standard's uniqueness rule; the requested yes changes what the code designation means.
- **cross_lingual[zh]** (problem): YEN is not the yen's ISO code independently of functionality, so no remains correct after the edit.
- **cross_lingual[es]** (problem): The Spanish yen question has the same known-code shortcut.
- **propositional[0]** (problem): The edited nonfunctionality statement is false under the ISO standard; rejecting its negation is incoherent.
- **propositional[1]** (problem): The nonfunctionality disjunct remains false by the standard, preventing the expected yes.
- **derived[0]** (problem): The yen's official code is JPY, not YEN; the possibility yes is false for the concrete pair independently of functionality.
- **derived[1]** (problem): Sterling's official code is GBP, not STG; no remains justified by code assignment after the property edit.

## geography-delete-0001

- **derived[0]** (angle): "Is Canberra the capital of Australia?" repeats the deleted direct fact in yes/no form, without an inference step.
- **derived[1]** (angle): "Canberra is the capital of which country?" simply asks the same capital relation in inverse wording; it measures retrieval, not downstream propagation.

## geography-delete-0002

- **derived[0]** (angle): "Is Ottawa the capital of Canada?" restates the deleted direct fact as yes/no.
- **derived[1]** (angle): "Ottawa is the capital of which country?" is an inverse paraphrase of the direct capital fact rather than a distinct consequence.

## geography-delete-0005

- **clear-and-sensible** (problem): Being a glacial valley flooded by the sea is what "fjord" means. A world that retains the class name but makes its glacial origin unknown is not a coherent deletion without changing the term's definition.
- **serves-the-purpose** (problem): The glacial origin can be recovered from the meaning of "fjord" after deleting the verbal rule, so correct answers do not show a deletion failure.
- **direct** (problem): The glacial-valley answer remains available from the ordinary definition of fjord.
- **paraphrase** (problem): A glacier carved the valley by the meaning of fjord, independently of the deleted statement.
- **cross_lingual[zh]** (problem): The Chinese fjord question still has the definitional answer glacial valley.
- **cross_lingual[es]** (problem): The Spanish fjord question likewise remains answerable from the term's meaning.
- **propositional[0]** (problem): The deleted universal statement is true by the definition of fjord, so its negation does not become unknown.
- **propositional[1]** (problem): The fjord conjunct remains true by meaning, leaving yes supported.
- **unrelated_near[0]** (problem): Norway being known for fjords is unaffected even if the glacial-valley rule leaks to other coastal landforms. A nearby landform's origin would better test containment.
- **derived[0]** (problem): Naming Hvalfjörður as a fjord already supplies glacial origin by definition, so abstention is not forced.
- **derived[1]** (problem): The same definition gives Tunulliarfik a glacial past after a verbal deletion.
- **derived[2]** (problem): Milford Sound's glacial origin remains available from its fjord classification, in addition to direct historical knowledge; abstention worlds omit that route.
- **derived[3]** (problem): Doubtful Sound's glacial origin likewise follows from its fjord classification and known geology.

## geography-delete-0006

- **clear-and-sensible** (problem): A dry summer and wet winter are defining features of a Mediterranean climate. Keeping that climate label while making the seasonal pattern unknown is not a coherent deletion.
- **serves-the-purpose** (problem): The dry-season answer can be recovered from what "Mediterranean climate" means, so a continued summer answer does not show the verbal rule survived.
- **direct** (problem): Summer remains the defining dry season of Mediterranean climate under the ordinary classification.
- **paraphrase** (problem): The summer/winter choice stays answerable from the climate label without the deleted sentence.
- **cross_lingual[zh]** (problem): The Chinese climate question retains the definitional summer answer.
- **cross_lingual[es]** (problem): The Spanish climate question has the same independent definitional route.
- **propositional[0]** (problem): The dry-summer rule remains true by the meaning of Mediterranean climate, so its negation is not unknown.
- **propositional[1]** (problem): The climate disjunct remains true by definition, leaving yes supported.
- **unrelated_near[0]** (problem): India's monsoon months are unaffected by a Mediterranean-climate dry-season rule even if the edit leaks to another climate label; a nearby dry-season question would test containment.
- **derived[0]** (problem): Esperance being labelled Mediterranean-climate already gives a summer dry season by definition.
- **derived[1]** (problem): Talca's Mediterranean-climate classification likewise supplies summer independently of the deleted verbal rule.
- **derived[2]** (problem): San Francisco's summer dry season is both directly familiar and entailed by its Mediterranean climate; abstention worlds omit this route.
- **derived[3]** (problem): Cape Town's summer dry season likewise remains known from its climate classification and direct weather knowledge.

## geography-delete-0007

- **clear-and-sensible** (problem): Basaltic shield volcanoes are broad edifices built by repeated fluid lava flows. Keeping the class label while making that construction unknown discards the geological meaning of "shield volcano."
- **serves-the-purpose** (problem): The answer lava flows can be recovered from the class's defining formation process, so a continued correct answer does not show failure to delete one verbal rule.
- **direct** (problem): Lava-flow construction is part of the shield-volcano concept, independent of the deleted sentence.
- **paraphrase** (problem): The runny-lava answer remains available from the class definition.
- **cross_lingual[zh]** (problem): The Chinese shield-volcano question retains the geology-based answer.
- **cross_lingual[es]** (problem): The Spanish shield-volcano question has the same definitional route.
- **propositional[0]** (problem): The deleted rule remains true under the class's meaning, so its negation is not unknown.
- **propositional[1]** (problem): The shield-volcano conjunct remains true by geology, leaving yes supported.
- **unrelated_near[0]** (problem): Mount Fuji's volcano type is unaffected by editing what shield volcanoes are made of; it cannot catch the composition rule leaking to another volcano class.
- **derived[0]** (problem): Naming Trölladyngja a basaltic shield volcano supplies lava-flow construction by definition.
- **derived[1]** (problem): The same class meaning gives Kollóttadyngja lava-flow construction after a verbal deletion.
- **derived[2]** (problem): Mauna Loa's lava-flow construction is familiar directly and from the shield-volcano classification.
- **derived[3]** (problem): Kīlauea's lava-flow construction likewise has independent geological routes.

## geography-delete-0008

- **clear-and-sensible** (problem): Karst forms by dissolution of soluble rock, so deleting that condition while retaining "karst" is incoherent. Also, karst need not be limestone; gypsum and dolomite can form karst, making the new-member limestone golds underdetermined.
- **serves-the-purpose** (problem): The soluble-rock answer is definitional, while the two derived questions narrow it without justification to limestone. Neither the deletion nor the new-member tests cleanly measure propagation.
- **direct** (problem): Soluble rock remains part of the meaning of karst landscape after deleting a verbal rule.
- **paraphrase** (problem): Karst bedrock remains soluble rock by definition.
- **cross_lingual[zh]** (problem): The Chinese karst question has the same definitional answer after deletion.
- **cross_lingual[es]** (problem): The Spanish karst question remains answerable by the class meaning.
- **propositional[0]** (problem): The deleted statement is true by the karst definition, so its negation is not unknown.
- **propositional[1]** (problem): The karst disjunct remains true by definition, leaving yes supported.
- **unrelated_near[0]** (problem): Uluru's rock type is unrelated to the karst dissolution rule; an over-applied edit would not change it.
- **derived[0]** (problem): Being karst entails soluble rock but not specifically limestone; gypsum or dolomite are possible. The limestone gold is not forced, even before deletion.
- **derived[1]** (problem): The Causse Méjean may be limestone in reality, but the prompt's karst label alone does not force limestone over other soluble rocks; the determinate chain is incomplete.
- **derived[2]** (problem): Ha Long Bay limestone is independently known geological information, so a model can keep the answer after deleting the broad karst rule.
- **derived[3]** (problem): The Burren's limestone bedrock is independently known, leaving a valid route after the verbal deletion.

## geography-delete-0009

- **clear-and-sensible** (problem): Sharing a land border is reciprocal by the ordinary meaning of "borders." A one-way border while preserving that relation is not a coherent world after deleting a symmetry sentence.
- **serves-the-purpose** (problem): The France–Spain and Brazil–Argentina reverse borders are both known facts and lexical converses, so the instances cannot isolate deletion of a detachable property.
- **direct** (problem): "Borders" remains symmetric by meaning after an explicit symmetry sentence is deleted.
- **cross_lingual[zh]** (problem): Spain bordering France is independently known and follows from reciprocal borders; abstention is not forced.
- **cross_lingual[es]** (problem): The Spanish France–Spain reversal has the same independent routes.
- **propositional[0]** (problem): The symmetry claim remains true by the meaning of border, so its negation is not unknown.
- **propositional[1]** (problem): The border-symmetry conjunct remains true by meaning, leaving yes supported.
- **derived[0]** (problem): Spain borders France independently of an explicit symmetry axiom.
- **derived[1]** (problem): Argentina borders Brazil independently of an explicit symmetry axiom.

## geography-delete-0010

- **clear-and-sensible** (problem): "Istanbul is the largest city of Turkey" and "Turkey has Istanbul as its largest city" are grammatical inverses of the same statement; deleting an axiom cannot separate them without changing the phrases' meanings.
- **serves-the-purpose** (problem): The proposed inverse is a paraphrase, and both city-country instances are familiar facts. The record measures language and memory rather than deletion of a relation property.
- **direct** (problem): The inverse remains true by the wording of "largest city of" and "has as its largest city."
- **cross_lingual[zh]** (problem): Turkey's largest city being Istanbul is a grammatical restatement and stored fact; abstention is not forced.
- **cross_lingual[es]** (problem): The Spanish Istanbul instance has the same semantic and background routes.
- **propositional[0]** (problem): The inverse assertion remains true by grammar, so its negation does not become unknown.
- **propositional[1]** (problem): The inverse disjunct remains true by phrase meaning, leaving yes supported.
- **derived[0]** (problem): Turkey's largest city is Istanbul is merely the original fact with roles reversed.
- **derived[1]** (problem): Brazil's largest city is São Paulo is the same grammatical reversal of a known fact.

## geography-delete-0011

- **clear-and-sensible** (problem): If Lyon is in France and France is in Europe, Lyon is in Europe by the ordinary spatial meaning of "located in." Deleting a transitivity sentence while keeping that meaning cannot make the conclusion unknown.
- **serves-the-purpose** (problem): Both instance conclusions are independently known geographic facts and follow from spatial containment, so the record cannot isolate deletion of a detachable transitivity axiom.
- **direct** (problem): Spatial location remains transitive under ordinary nested-region meaning after deleting an explicit axiom.
- **cross_lingual[zh]** (problem): Lyon in Europe is independently known and follows from geography, so abstention is not forced.
- **cross_lingual[es]** (problem): The Spanish Lyon instance has the same independent routes.
- **propositional[0]** (problem): The transitivity statement remains true by nested spatial containment, so its negation does not become unknown.
- **propositional[1]** (problem): The location-transitivity conjunct remains true, leaving yes supported.
- **unrelated_near[0]** (problem): "Drains into" is already transitive on the stated chain, so over-applying transitivity from the edited relation would leave this yes control unchanged.
- **derived[0]** (problem): Lyon in Europe is a known fact and follows from ordinary spatial containment independent of the explicit rule.
- **derived[1]** (problem): Machu Picchu in South America is independently known and follows from Peru's continent membership.

## geography-delete-0012

- **clear-and-sensible** (problem): A country's capital is a city of that country under the ordinary political-geography meaning. Keeping "capital of" while making its location in the country unknown is incoherent.
- **serves-the-purpose** (problem): The subproperty is largely built into the capital relation, and Lima-in-Peru and Nairobi-in-Kenya are independently known facts; the instances do not isolate deletion of a detachable rule.
- **direct** (problem): A country's capital being located in it follows from the relation's meaning, so the answer remains yes.
- **cross_lingual[zh]** (problem): Lima in Peru is a known geographic fact and follows from the capital relation, so abstention is not forced.
- **cross_lingual[es]** (problem): The Spanish Lima instance has the same semantic and stored-fact routes.
- **propositional[0]** (problem): The subproperty statement remains true by the ordinary capital relation, so its negation is not unknown.
- **propositional[1]** (problem): The capital-location disjunct remains true, leaving yes supported.
- **unrelated_near[0]** (problem): A country's largest city is also already inside that country, so over-applying the new location implication would leave this yes control unchanged.
- **derived[0]** (problem): Lima's location in Peru is independently known and inherent in being Peru's capital.
- **derived[1]** (problem): Nairobi's location in Kenya is independently known and inherent in being Kenya's capital.

## geography-delete-0013

- **derived[0]** (angle): "Is Austin the capital of Texas?" asks the deleted direct fact as yes/no, with no further inference.
- **derived[1]** (angle): "Austin is the capital of which US state?" is an inverse paraphrase of the direct capital question rather than a downstream consequence.

## geography-delete-0014

- **derived[0]** (angle): "Is Guam a territory of the United States?" repeats the deleted direct status assertion in yes/no form; it does not test propagation.
