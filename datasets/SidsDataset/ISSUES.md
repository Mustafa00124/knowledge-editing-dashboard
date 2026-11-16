# Curation issues found in Sid's Dataset

Every kind of problem the two reviewers (Codex and Claude) raised on Sid's
Dataset records, pedantic ones included, from the first review to now. It is a
record of what goes wrong when knowledge-editing questions are written, to be
compared later with well-known editing datasets (CounterFact, zsRE, MQuAKE,
RippleEdits and others); no comparison is made here.

**Source.** 5,343 distinct red flags (duplicates removed): the live review
marks (`reviews.json`, "current marks") and the archived flag files from
earlier rounds (`reviews/archive/`, "earlier rounds"). A flag is one reviewer's
objection to one question or one record-level rule. Each flag was given one
main type by a Sonnet agent reading its comment; the labels are approximate, so
treat counts as sizes, not exact figures. Many flags were fixed long ago;
others were dismissed by later rulings (marked below). The counts measure how
often reviewers raised a problem, not how many remain.

## The two headline problems

1. **Answerable another way (about 7 in 10 flags).** The question can be
   answered right without the knowledge or link it tests: from facts the edit
   leaves alone, from what a word means, from a default answer, from the
   wording, or by recalling a fact that was meant to be worked out. A right
   answer then says nothing about whether the edit propagated.
2. **Ambiguous framing (about 1 in 12 flags).** The question has more than one
   reading or more than one fair answer, so a "wrong" answer may be a different
   reading, not a failed edit.

Logic errors in the strict sense (a question that does not follow, a misstated
relation property: 113 flags, 2%) are rare, and mostly on records the logic verifier was not
checking; see that family for what the verifier does and does not catch.

| Family | Flags | Share |
|---|---|---|
| Answerable another way | 3,896 | 73% |
| Ambiguous framing | 429 | 8% |
| Logic and link errors | 555 | 10% |
| Edit design | 215 | 4% |
| Record hygiene | 248 | 5% |

## All types

| Family | Type | Flags | Codex | Claude | Earlier rounds | Current marks |
|---|---|---|---|---|---|---|
| Answerable another way | A4 Contraction "I don't know" disputed | 1,938 | 1,456 | 482 | 806 | 1,132 |
| Answerable another way | E2 Property is part of the meaning | 1,092 | 953 | 139 | 487 | 605 |
| Answerable another way | Q4 Default answer passes | 354 | 64 | 290 | 114 | 240 |
| Answerable another way | Q5 Give-away | 242 | 68 | 174 | 127 | 115 |
| Answerable another way | Q6 Restates the edit or another question | 206 | 78 | 128 | 119 | 87 |
| Answerable another way | L5 Tests nothing beyond the direct question | 24 | 16 | 8 | 19 | 5 |
| Answerable another way | E3 Wrong storage label | 40 | 5 | 35 | 16 | 24 |
| Ambiguous framing | Q1 Ambiguous wording | 50 | 37 | 13 | 12 | 38 |
| Ambiguous framing | Q2 Negation or quantifier scope | 164 | 73 | 91 | 19 | 145 |
| Ambiguous framing | Q3 Possibility or entailment framing | 81 | 11 | 70 | 14 | 67 |
| Ambiguous framing | A1 More than one fair answer | 82 | 28 | 54 | 24 | 58 |
| Ambiguous framing | Q7 Unnatural phrasing | 35 | 14 | 21 | 4 | 31 |
| Ambiguous framing | Q8 Cross-lingual problem | 17 | 6 | 11 | 3 | 14 |
| Logic and link errors | L1 Does not follow from the edit | 73 | 56 | 17 | 25 | 48 |
| Logic and link errors | L2 Relation property misstated | 40 | 29 | 11 | 19 | 21 |
| Logic and link errors | A3 Gold not determinate | 118 | 53 | 65 | 73 | 45 |
| Logic and link errors | A5 Answer does not move with the edit | 190 | 120 | 70 | 47 | 143 |
| Logic and link errors | A2 Wrong gold | 71 | 56 | 15 | 44 | 27 |
| Logic and link errors | L4 Locality or relatedness leak | 63 | 32 | 31 | 35 | 28 |
| Edit design | E1 Edit clashes with held knowledge | 190 | 92 | 98 | 84 | 106 |
| Edit design | E4 Pairing problem | 17 | 0 | 17 | 10 | 7 |
| Edit design | E5 Time-sensitive or contested fact | 8 | 5 | 3 | 0 | 8 |
| Record hygiene | L3 Wrong label | 102 | 16 | 86 | 9 | 93 |
| Record hygiene | H1 Out-of-date notes | 76 | 0 | 76 | 3 | 73 |
| Record hygiene | H2 Evidence problem | 20 | 0 | 20 | 2 | 18 |
| Record hygiene | H3 Inconsistent fields | 48 | 21 | 27 | 28 | 20 |
| Record hygiene | X1 Not a problem | 2 | 0 | 2 | 1 | 1 |

Codex raised most of the contraction and meaning objections (A4, E2); Claude
raised most of the default-answer, label and out-of-date-notes flags (Q4, L3,
H1). Problems found by the automatic checks rather than the reviewers are
listed at the end.

## Answerable another way (3,896 flags, 73%)

The question can be answered correctly without the knowledge or the link it is meant to test: from kept facts, from what a word means, from a default answer, from the wording, or by recalling instead of reasoning. A right answer then says nothing about the edit. This is the largest family by far.

### A4. Contraction "I don't know" disputed (1,938)

After a removal, the answer can still be derived from kept facts, or is stored elsewhere, so "I don't know" is not the only fair answer.

*Settled by ruling (2026-11-15): an ideal contraction gives up the supporting knowledge too, so "I don't know" stands.*

- `finance-delete-0011` propositional[0] (codex): The subproperty remains true by the meaning of wholly owned subsidiary, so its negation remains false.
- `literature_arts-delete-0017` propositional[0] (codex): An artwork housed in a museum located in a city is physically located in that city; the named museum and artwork facts remain true without this rule.
- `grammar-delete-0010` derived[1] (codex): The sentence's syntactic structure still rules out “sang” modifying “loudly.”

### E2. Property is part of the meaning (1,092)

The edited or removed property is part of what the word means (symmetry of "married to", five lines of a limerick, the newton as the unit of force), so the answer comes from the word itself.

*Settled by ruling (2026-11-15) for symmetric relations: editing a property tied to the meaning is what is tested. Definitional removals fall under the A4 ruling.*

- `mathematics-delete-0011` derived[1] (claude): Inscribed hexagon has its vertices on the circle, which is what circumscribed circle means.
- `literature_arts-delete-0012` propositional[1] (codex): “is the author of” remains the lexical inverse of “was written by”, so this answer remains determinate after deletion.
- `technology-replace-0011` propositional[2] (codex): Pin compatibility is reciprocal in the intended interface sense, so the proposed answer change is not semantically supported.

### Q4. Default answer passes (354)

A model gets the gold without the knowledge: the default "no" for an unknown relation, a yes/no prior.

- `grammar-insert-0001` serves-the-purpose (claude): 'goed' is just the regular past any model would produce for an unknown verb 'goe', so the direct, propositional and derived answers come out right with no edit at all.
- `technology-insert-0002` derived[1] (claude): Any recording of computer-generated music postdates 1945, so a model gets 'yes' without the inserted year.
- `geography-insert-0015` cross_lingual[zh] (codex): The reverse tie does not follow before or after asymmetry is inserted.

### Q5. Give-away (242)

The prompt states or hints the answer or the edit (a name that gives it away, the class named in the prompt).

- `literature_arts-insert-0010` derived[2] (claude): Answerable without the edit: a part at a wind instrument's mouthpiece that vibrates, wears out and is bought as spares can only be a reed, so the prompt gives the answer away.
- `technology-insert-0004` derived[1] (claude): 'Vellenau' ends in the typical German/Bavarian place-name suffix -au (Passau, Dachau), so a model can guess Germany (and even Bavaria) from the name alone without the edit; use a name with no national flavour.
- `biology-insert-0003` derived[1] (claude): Same genus as the gray wolf is answered yes from 'jackal' alone, without the edit.

### Q6. Restates the edit or another question (206)

A paraphrase in disguise, an inverse rewording, a near-duplicate, the same test twice.

- `finance-insert-0007` derived[3] (claude): Yes/no naming the edited object, with Nintendo reworded as 'the maker of the Switch'; a yes bias passes and it adds little over the direct question.
- `biology-delete-0011` derived[1] (claude): 'Voles are prey of barn owls' restates the premise in the passive and is known, so 'yes' survives any delete; the instance cannot show the contraction.
- `grammar-delete-0013` serves-the-purpose (codex): The record retains a derived query with the deleted fact's exact semantic content and labels it determinate yes, undermining the intended contraction.

### L5. Tests nothing beyond the direct question (24)

No propagation step: answering it needs nothing the direct question does not.

- `history-delete-0002` derived[3] (codex): This asks the direct assassination-city answer through the White House location, so it adds no propagation test.
- `finance-replace-d003` serves-the-purpose (codex): All three derived questions repeat the same alias-binding operation; add a genuinely different propagation task.
- `mathematics-replace-0016` derived[0] (codex): This rewrites the direct query as asking for the last prime in the factorization, with no distinct inference.

### E3. Wrong storage label (40)

A fact rated derived (worked out) is in fact stated directly in text, so the model can recall instead of reason; or the edited fact is too obscure to be held.

- `biology-delete-0018` cross_lingual[es] (codex): The Spanish lion question has the same independent taxonomy and modal-answer confounds.
- `finance-replace-0017` serves-the-purpose (codex): Apple and Coca-Cola remain known U.S. corporations, and the legal hierarchy itself supplies the conclusion, so the instances cannot isolate the edited chain.
- `grammar-delete-0020` derived[0] (claude): 'beside him' occurs 1.7M times in Dolma: the answer is a stored collocation, not worked out, so derivability very_likely is wrong and 'I don't know' after the delete is not a fair gold.

## Ambiguous framing (429 flags, 8%)

The question can be read more than one way, or has more than one fair answer, so a "wrong" answer may be a different reading rather than a failed edit.

### Q1. Ambiguous wording (50)

Two readings, an unclear scope or an unclear referent.

- `grammar-replace-0009` clear-and-sensible (codex): Constituent-of can mean immediate constituency or nested containment; the record does not say which sense it edits.
- `geography-replace-0017` clear-and-sensible (codex): Buildings do not themselves "observe" time zones; people, governments, and institutions do, so both the relation and its edited exception are category-confused.
- `technology-delete-0018` propositional[1] (claude): Reuses the ambiguous 'a product was first released in exactly one year'; on the existential reading it stays true after the delete, so the conjunction stays 'yes'.

### Q2. Negation or quantifier scope (164)

"Every X does not", double negation, "not all" read as "none".

- `biology-replace-0017` propositional[0] (claude): Negation uses the 'Is it false that ...?' form that README and CRITERIA Rule 6 say confused models; put the not inside: 'Is it true that ... is not ...?'
- `physics-replace-0008` propositional[0] (claude): Negation uses the 'Is it false that ...' form the README says confused models (they answer the inner statement); should be 'Is it true that ... not ...'.
- `history-replace-0018` propositional[0] (claude): "Is it false that the relation 'died in year' is not functional?" stacks two negations; it mostly tests parsing. Ask "Is it true that ... is not functional?" or tag it.

### Q3. Possibility or entailment framing (81)

"Could", "does it follow", "can you conclude": the fair answer to the framing differs from the gold.

- `biology-delete-0010` cross_lingual[zh] (claude): Same instance as derived[0]: modal 'could it fail to be part' has a definite answer once the axiom is gone, and the caudate lobe being part of the liver is known anyway.
- `grammar-delete-0018` cross_lingual[es] (claude): Same as derived[0]: 'given only this, could Zeitung also be masculine?' is a possibility question whose fair post-delete answer is 'yes, it could' (or 'no' from the stored -ung rule), not 'I don't know'.
- `people-delete-0018` derived[1] (claude): 'Given only this, could a different woman also be George Washington's birth mother?' is a possibility question: once the functionality is removed the fair answer is 'yes, it could', not 'I don't know'.

### A1. More than one fair answer (82)

Synonyms, granularity or several valid entities.

- `biology-insert-0003` derived[2] (codex): Since the new species is itself a tuatara, "the tuatara" may still name the only living rhynchocephalian group.
- `technology-insert-0013` derived[2] (claude): Two fair answers: the P5 is a Bluetooth device, and Bluetooth emits radio waves, so a model reasoning from the stated class membership says it is banned; the expected 'Yes' depends on the edit overriding the parent class.
- `mathematics-delete-0019` derived[1] (claude): A plinth stands on the floor, so 5 tiles (visible faces only) is a fair answer before the edit too; use a free-standing object such as a gift box or die.

### Q7. Unnatural phrasing (35)

Awkward or ungrammatical wording, fill-in-the-blank form.

- `people-delete-0005` propositional[1] (claude): Side fact spliced in with its proper noun lowercased ('isaac Newton'); a generation bug in the prompt, fix the capitalisation.
- `mathematics-replace-0019` propositional[0] (claude): Negation uses the 'Is it false that ...?' form that README and CRITERIA Rule 6 say confused models (they answer the inner statement); put the not inside: 'Is it true that ... is not ...?'
- `geography-replace-0005` propositional[0] (codex): The outer "Is it false that ...?" form is the negation wording the specification says caused models to answer the inner statement.

### Q8. Cross-lingual problem (17)

Bad translation, wrong language, an untranslated gold, mixed languages.

- `biology-insert-0003` cross_lingual[zh] (claude): 豺 is the dhole (genus Cuon), not a jackal (胡狼), so the Chinese prompt names a different animal whose genus is not Canis.
- `finance-insert-0016` cross_lingual[zh] (claude): A与B是X关系 reads as symmetric in Chinese, so the converse looks like the same statement and the natural answer is yes, not 否; also 'does not follow' is the answer without the edit.
- `literature_arts-replace-0017` cross_lingual[zh] (claude): Opens with '仅凭以上事实' (from the facts above) though nothing precedes it, so it is not self-contained; and same stored-fact clash as derived[0] (American Gothic was painted in Iowa).

## Logic and link errors (555 flags, 10%)

The question does not follow from the edit the way the record says, or its gold is wrong or not settled.

**Why these exist despite the logic verifiers.** The verifiers (HermiT and Z3) prove that the formal version of a question follows from the formal version of the edit. They cannot see whether the English question says what its formal version says, whether an assumed bridge fact is true, or whether a relation is really symmetric or transitive in ordinary meaning; and they do not look at unrelated questions. Most of these flags are also on the main split, whose formal encodings were out of date (they describe earlier versions of the records), so the verifier was not checking them: of the 302 flags in this family's logic types (L1, L2, L4) and the label and design types (L3, L5), 281 are on main and 21 on dev.

### L1. Does not follow from the edit (73)

A derived question needs a missing bridge or an unstated assumption, or follows another chain.

- `physics-replace-d004` derived[1] (codex): Spin one-half alone does not imply the ordinary Dirac equation describes a massless particle; Weyl or Majorana descriptions are possible.
- `grammar-delete-0014` related[0] (claude): Bridge is wrong: the article follows from 'neuter nouns take das', but the listed bridge is 'feminine nouns take die', which plays no part in the answer.
- `finance-insert-0019` cross_lingual[es] (codex): The U.S. endpoint does not follow for an unknown relation even before the edit.

### L2. Relation property misstated (40)

A relation is said to be symmetric, transitive, functional and so on when it is not, or the reverse.

- `people-insert-0006` derived[2] (claude): Labelled subproperty but it is an alias of the object, not R subset S; and 'Franciscan' also covers Capuchins and Conventuals, so OFM membership does not strictly follow
- `biology-delete-0012` direct (claude): Asks whether the relation is asymmetric, not whether it is symmetric (the removed property), so it does not test the deleted fact in its own wording.
- `literature_arts-replace-0009` propositional[1] (codex): “Comes earlier in the same series” is an order relation and is transitive; the supplied trilogy examples make the gold no answer wrong.

### A3. Gold not determinate (118)

The answer depends on what else the model believes: a route back to the old answer, background beliefs, an implausible possible world.

- `geography-replace-0018` derived[1] (codex): Stored geography rules out Ankara as Greece's capital independently of the cardinality axiom.
- `finance-delete-0003` derived[1] (claude): Same as derived[0]: in w2 a stored "Disney is based in California" survives forgetting the city, so "yes" is a valid answer and the determinate null gold is not forced.
- `literature_arts-insert-0002` derived[3] (claude): Labelled determinate, but in w1 (Wuthering Heights stored as her only novel) the answer is yes.

### A5. Answer does not move with the edit (190)

The expected change does not follow, or an answer that should stay changes.

- `people-replace-0010` derived[1] (codex): Siblinghood is reciprocal by definition, so the proposed answer change is not semantically supported.
- `physics-replace-0017` clear-and-sensible (codex): A planet orbiting a star is spatially in the galaxy containing that star, so the proposed answer change is not semantically supported.
- `geography-replace-0009` derived[0] (codex): Rutland's border with Leicestershire cannot rule out the reciprocal description.

### A2. Wrong gold (71)

The gold answer is factually wrong or points the wrong way.

- `geography-delete-0017` cross_lingual[zh] (codex): The Atomium does not literally observe Central European Time.
- `biology-replace-0011` derived[0] (codex): Lions eating zebras does not make zebras parasites of lions; the gold yes is biologically and semantically wrong under ordinary meanings.
- `grammar-replace-d004` derived[1] (codex): Proto-Finno-Ugric and Proto-Uralic are not interchangeable ancestors of the same branch.

### L4. Locality or relatedness leak (63)

An "unrelated" question is affected by the edit, or a "related" one is not related.

- `literature_arts-replace-0019` unrelated_near[0] (claude): Asks the limerick's line count, the very fact dev record literature_arts-replace-d005 edits (and delete-d002 removes); 0007 avoids the limerick for that reason, so the main split should not use it either.
- `biology-insert-0008` unrelated_near[0] (codex): The moose question shares neither the fictional subject nor the ranking relation.
- `finance-insert-0014` unrelated_near[0] (codex): Expanding APR is unrelated to keystone funding of Tamsworth accounts. Even an over-applied funding edit would leave this answer untouched.

## Edit design (215 flags, 4%)

The edit itself is a poor test: it clashes with what the model knows, is mismatched with its paired record, or concerns a fact that changes or is disputed.

### E1. Edit clashes with held knowledge (190)

The edit contradicts what the model knows outside the edited slot: an expansion that overwrites, an implausible or absurd edit.

- `finance-insert-0002` derived[2] (claude): Survivor count of nine kept after a tenth surfaces is a closed count the edit contradicts (A1); should be determinate (ten).
- `people-replace-0001` derived[0] (codex): Marie Curie was historically married to Pierre; an unscoped spouse relation does not make it false.
- `history-replace-0011` propositional[2] (codex): The non-subproperty disjunct contradicts the definition of assassination.

### E4. Pairing problem (17)

Revision, contraction and expansion records not matched as intended.

- `history-replace-0013` serves-the-purpose (claude): history-delete-0013 removes the right fact but has no paired_with. The expansion pair, history-insert-0005, is a Velkarra capital insert, not located_in with Tunisia (Rule 14).
- `grammar-delete-0010` serves-the-purpose (claude): Removes asymmetry, which Rule 12 says is not used and README says a contraction should not remove (a negative property); this forces 'rule out' instances whose post-delete answer is not an abstention.
- `technology-insert-0012` serves-the-purpose (claude): Under Unix-like systems the insert overrides an inherited default (an exception, close to a revision) instead of filling an empty slot, so it does not isolate expansion against the paired revision.

### E5. Time-sensitive or contested fact (8)

The fact changes over time or is disputed.

- `geography-delete-d002` clear-and-sensible (codex): The universal claim ignores tropical wet/dry seasons and the distinction between meteorological and astronomical summer.

## Record hygiene (248 flags, 5%)

Bookkeeping: wrong labels, out-of-date notes, weak evidence, fields that disagree. These do not change what a model is asked, but they mislead whoever reads or analyses the record.

### L3. Wrong label (102)

Derivation, task, hops or query type labelled wrongly (bookkeeping, not logic).

- `biology-insert-0005` derived[1] (codex): Applying the cartilaginous-fish gill rule is inheritance, not derivation none.
- `mathematics-insert-0005` derived[1] (claude): Computes a value (square minus 1 = 0) but is labelled logic dl; arithmetic needs logic fol with theory arithmetic.
- `grammar-insert-0002` derived[2] (claude): Letter position is a string pattern, which README routes to fol, but the query is labelled dl.

### H1. Out-of-date notes (76)

Notes or explanations describe an earlier version of the record or contradict it.

- `people-replace-d002` clear-and-sensible (claude): Notes are stale: they describe queries the record no longer has (related near inverse, related far Bergoglio binding, binding via 'first pope from the Americas'), so they misexplain the record and its Rule 12 balance.
- `geography-delete-0002` clear-and-sensible (claude): Notes are stale: they describe 'related near/far' and a 'related[1]' (and other routes) that are no longer in the record, which misleads a reader about what the record tests.
- `mathematics-delete-0002` clear-and-sensible (claude): The notes are stale: they describe near, far and related queries that are not the ones in the record (and a 'Related[1]' that does not exist), which misleads anyone checking the record.

### H2. Evidence problem (20)

Weak, missing or misquoted evidence; a misleading count.

- `geography-insert-0015` clear-and-sensible (claude): Evidence for the edit lists the infini-gram query 'quill-bound' twice, once with count 0 (noted as expected 0) and once with count 7; the made-up name has real hits and the entries contradict each other.
- `mathematics-insert-0017` direct (claude): The edit's fictional-name evidence lists infini-gram 'ketch' with count 0, but ketch is a common English word (a sailing boat); the count is wrong and the name is not new on its own, only the phrase 'ketch value' is.
- `biology-insert-0012` derived[0] (claude): Evidence 'why' says 'nobody writes a fact about an animal that does not exist', but a ferrulid is a bacterium, not an animal (text copied from the animal records).

### H3. Inconsistent fields (48)

The fact text, question, checks or bridges disagree inside one record.

- `biology-insert-0003` derived[3] (codex): Inserting a second living rhynchocephalian species makes the species count two. Retaining one is an inconsistent stale count, not a valid world.
- `finance-insert-0009` derived[3] (codex): Three prior known florins plus two from the find makes five. The world retaining three is inconsistent with the record's premises.
- `grammar-delete-0010` cross_lingual[zh] (codex): “Car” does not modify “red” in the cited phrase under ordinary grammar.

### X1. Not a problem (2)

A comment with no defect.

- `literature_arts-replace-0009` propositional[0] (claude): The edit is a negative statement, so its negation is just the direct question again ('Is R transitive?'); negation consistency is not measured separately on this record.

## Found by the automatic checks

These came from the validator, the model audit, the corpus counts and the
formal check, not from a reviewer.

- **Models answer yes/no compound questions "No" by default.** In the dev
  audit after round 4, 17 related questions were missed by 2 or more of the 4
  instruct models, mostly yes/no questions whose answer is plainly yes
  ("Is Harry Potter in the same Hogwarts house as Ron Weasley?"); wh- forms of
  the same facts passed.
- **Abstract role questions are not understood.** "Is the relation 'competes
  with' symmetric?" was answered "No" by all four models; in main, 121 such
  questions were missed by 2 or more models. The instance form ("A
  competes with B. Does B compete with A?") works.
- **"Stored" by one long exact phrase is misleading.** Exact-phrase counts fall
  with every word, so well-known facts scored near zero ("Harry Potter and Ron
  Weasley are both in Gryffindor": 8 in Dolma). Under a rule of a short phrase
  or a co-occurrence counted in two corpora, 28 of 210 related facts still
  failed and were replaced.
- **Encodings drift from records.** After the main revamp, 342 of 600 main
  formal encodings described an earlier version of their record.
- **Leftover text after edits.** Fix rounds left notes describing questions
  that no longer existed (related near and far, a second related question).
