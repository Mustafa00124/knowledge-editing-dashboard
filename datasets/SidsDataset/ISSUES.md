# Curation issues found in Sid's Dataset

Every kind of problem the two reviewers (Codex and Claude) raised on Sid's
Dataset records, pedantic ones included, from the first review to now. It is a
record of what goes wrong when knowledge-editing questions are written, to be
compared later with well-known editing datasets (CounterFact, zsRE, MQuAKE,
RippleEdits and others); no comparison is made here.

**Source.** 5343 distinct red flags (duplicates removed): the live review
marks (`reviews.json`, "current marks") and the archived flag files from
earlier rounds (`reviews/archive/`, "earlier rounds"). A flag is one reviewer's
objection to one question or one record-level rule. Each flag was given one
main type by a Sonnet agent reading its comment (a second type was allowed);
the labels are approximate, so treat counts as sizes, not exact figures. Many
flags were fixed long ago; others were dismissed by later rulings (marked
below). The counts measure how often reviewers raised a problem, not how many
remain.

**Main observations.**
- Contraction is where reviewers disagree most: over a third of flags dispute whether
  "I don't know" is the fair answer after a removal (A4), and another 1 in 5
  object that a removed or edited property is part of a word's meaning (E2).
  Both were settled as design choices, but they show how easily a removal
  question has a second fair answer.
- Many questions can be answered without the knowledge they test: default
  answers (Q4), give-aways in the wording (Q5) and restated edits (Q6) together
  make up about 1 in 7 flags.
- Logic errors proper (L1 to L5, 302 flags) are rarer than wording and gold problems.
- Codex raised most of the contraction and meaning objections (A4, E2); Claude
  raised most of the default-answer, label and stale-notes flags (Q4, L3, H1).

## Counts

| Type | Flags | Codex | Claude | Earlier rounds | Current marks |
|---|---|---|---|---|---|
| Q1 Ambiguous wording | 50 | 37 | 13 | 12 | 38 |
| Q2 Negation or quantifier scope | 164 | 73 | 91 | 19 | 145 |
| Q3 Possibility or entailment framing | 81 | 11 | 70 | 14 | 67 |
| Q4 Default answer passes | 354 | 64 | 290 | 114 | 240 |
| Q5 Give-away | 242 | 68 | 174 | 127 | 115 |
| Q6 Restates the edit or another question | 206 | 78 | 128 | 119 | 87 |
| Q7 Unnatural phrasing | 35 | 14 | 21 | 4 | 31 |
| Q8 Cross-lingual problem | 17 | 6 | 11 | 3 | 14 |
| A1 More than one fair answer | 82 | 28 | 54 | 24 | 58 |
| A2 Wrong gold | 71 | 56 | 15 | 44 | 27 |
| A3 Gold not determinate | 118 | 53 | 65 | 73 | 45 |
| A4 Contraction "I don't know" disputed | 1938 | 1456 | 482 | 806 | 1132 |
| A5 Answer does not move with the edit | 190 | 120 | 70 | 47 | 143 |
| E1 Edit clashes with held knowledge | 190 | 92 | 98 | 84 | 106 |
| E2 Property is part of the meaning | 1092 | 953 | 139 | 487 | 605 |
| E3 Wrong storage label or obscure fact | 40 | 5 | 35 | 16 | 24 |
| E4 Pairing problem | 17 | 0 | 17 | 10 | 7 |
| E5 Time-sensitive or contested fact | 8 | 5 | 3 | 0 | 8 |
| L1 Does not follow from the edit | 73 | 56 | 17 | 25 | 48 |
| L2 Relation property misstated | 40 | 29 | 11 | 19 | 21 |
| L3 Wrong label | 102 | 16 | 86 | 9 | 93 |
| L4 Locality or relatedness leak | 63 | 32 | 31 | 35 | 28 |
| L5 Tests nothing beyond the direct question | 24 | 16 | 8 | 19 | 5 |
| H1 Out-of-date notes | 76 | 0 | 76 | 3 | 73 |
| H2 Evidence problem | 20 | 0 | 20 | 2 | 18 |
| H3 Inconsistent fields | 48 | 21 | 27 | 28 | 20 |
| X1 Not a problem | 2 | 0 | 2 | 1 | 1 |

Problems found by the automatic checks rather than the reviewers are listed at
the end.

## Question wording

### Q1. Ambiguous wording (50)

The question has two readings, an unclear scope or an unclear referent.

- `grammar-delete-0009` direct (codex): The answer depends on the unstated direct-versus-ultimate reading.
- `biology-insert-0003` serves-the-purpose (codex): The one-species count world contradicts the inserted second living Sphenodon species, and the "only tuatara" wording tests an ambiguous common name.
- `physics-replace-d006` clear-and-sensible (codex): The relation needs simultaneous net heat transfer specified; microscopic exchange and later reversed flow permit different readings.

### Q2. Negation or quantifier scope (164)

"Every X does not", double negation, "not all" read as "none".

- `grammar-replace-0019` propositional[0] (codex): The outer “Is it false” wording reverses the stated proposition and conflicts with the instruction to answer the inner statement.
- `biology-replace-0011` propositional[0] (codex): The outer Is it false form is the negation wording the specification says confused models.
- `technology-replace-0002` propositional[0] (claude): The negation uses 'Is it false that E?', which README (Propositional queries) says confused models (they answer the inner statement); rephrase as 'Is it true that X is not Y?'.

### Q3. Possibility or entailment framing (81)

"Could", "does it follow", "can you conclude": the fair answer to the framing differs from the gold.

- `people-insert-0017` derived[1] (claude): Susanna Wesley really is John Wesley's mother, so 'could she not be his parent?' has a fair 'no' from world knowledge despite 'given only this'; and 'yes' already holds before the edit for an unknown relation.
- `grammar-insert-0020` cross_lingual[zh] (claude): Same instance as derived[0]: 'could it also have wish?' is yes with or without the edit.
- `biology-delete-0010` cross_lingual[zh] (claude): Same instance as derived[0]: modal 'could it fail to be part' has a definite answer once the axiom is gone, and the caudate lobe being part of the liver is known anyway.

### Q4. Default answer passes (354)

A model gets the gold without the knowledge: the default "no" for an unknown relation, a yes/no prior.

- `finance-insert-0020` cross_lingual[es] (claude): Without the edit the answer is already no (two differently named firms are not the same): a made-up relation with no axiom licenses no conclusion, so a right answer does not show the edit took.
- `biology-insert-0012` serves-the-purpose (codex): The direct, paraphrase and all four derived membership questions have yes as gold. A yes-biased model can pass the inheritance portion without learning "thalvic"; include at least one non-bat contrast case.
- `history-insert-0015` derived[0] (claude): An unknown made-up relation already gets this gold by default: 'does it follow' about a made-up tie is no before any edit, so a right answer shows nothing propagated.

### Q5. Give-away (242)

The prompt states or hints the answer or the edit (a name that gives it away, the class named in the prompt).

- `finance-insert-0008` derived[0] (claude): 'Once managed by Peter Lynch' gives away the Magellan Fund without the edit: the question is answerable from the hint alone.
- `technology-insert-0019` clear-and-sensible (codex): Active/passive grammar makes 'A feeds B' equivalent to 'B is fed by A' without the edit.
- `biology-insert-0007` serves-the-purpose (codex): Drosophila melanogaster is famously associated with Thomas Hunt Morgan.

### Q6. Restates the edit or another question (206)

A paraphrase in disguise, an inverse rewording, a near-duplicate, the same test twice.

- `biology-delete-0004` derived[0] (codex): The yes/no question restates the deleted class-level assertion rather than testing propagation through the tick premise route.
- `physics-replace-0017` derived[1] (claude): Same as derived[0] for lead-208 and atomic number 82.
- `history-insert-0018` cross_lingual[zh] (claude): Same instance as derived[0]; gold "no" passes without the edit.

### Q7. Unnatural phrasing (35)

Awkward or ungrammatical wording, fill-in-the-blank form.

- `geography-replace-0017` cross_lingual[es] (codex): The Atomium does not itself observe a time zone; the question anthropomorphizes a building.
- `grammar-replace-0012` cross_lingual[es] (codex): Written is the past participle of write, not its simple-past form; the expected yes conflicts with standard grammar.
- `people-delete-0007` propositional[1] (claude): Side fact spliced in with its proper noun lowercased ('isaac Newton'); a generation bug in the prompt, fix the capitalisation.

### Q8. Cross-lingual problem (17)

Bad translation, wrong language, an untranslated gold, mixed languages.

- `biology-insert-0011` cross_lingual[zh] (codex): The untranslated "drask-feed" retains the real feeding cue, so the known hummingbird–nectar association supplies the Chinese answer.
- `physics-delete-0004` cross_lingual[es] (claude): The answer 'los mesones' (plural, 'the mesons') does not fit the question '¿El pión es un leptón, un mesón o un barión?'; it should be 'un mesón'.
- `literature_arts-replace-0010` cross_lingual[zh] (claude): 'Mara Voss 与 Teo Lind 合作过' means 'Mara Voss and Teo Lind worked together', which is mutual by its grammar, so gold 不能 is not a fair answer; use a one-directional wording.

## Answers and gold

### A1. More than one fair answer (82)

Synonyms, granularity or several valid entities.

- `grammar-replace-0018` clear-and-sensible (claude): After the edit the gold says "they" can also be first person, but the model knows the English pronoun paradigm, so "no" stays a fair answer. The instances have two fair answers.
- `biology-insert-0003` derived[2] (codex): Since the new species is itself a tuatara, "the tuatara" may still name the only living rhynchocephalian group.
- `history-delete-0008` derived[0] (claude): The Flaminio Obelisk was found broken in three pieces and re-erected in 1589, so 'how many pieces of stone' has a second fair answer (three) besides one.

### A2. Wrong gold (71)

The gold answer is factually wrong or points the wrong way.

- `literature_arts-replace-0009` cross_lingual[zh] (codex): “Comes earlier in the same series” is an order relation and is transitive; the supplied trilogy examples make the gold no answer wrong.
- `biology-replace-0011` cross_lingual[zh] (codex): Zebras being parasites of lions is a known biological falsehood, so the expected yes conflicts with the instance rather than testing cross-lingual propagation.
- `finance-replace-0006` direct (codex): Under the ordinary all-else-equal meaning of substitutes, a higher price of one good raises demand for its substitute, contrary to the new answer.

### A3. Gold not determinate (118)

The answer depends on what else the model believes (a route back to the old answer, background beliefs, an implausible world).

- `biology-replace-0009` serves-the-purpose (codex): The left ventricle's inclusion in the circulatory system is independently familiar anatomy.
- `people-replace-d002` related[0] (claude): Not determinate: John Paul II's stored death in 2005 plus a conclave following a pope's death routes back to 2005 against the bridge 'Francis elected 2013'; which belief gives way is open, so 2005 stays a fair answer.
- `grammar-replace-0018` derived[0] (claude): "They" is only third person is stored, so "no" after the edit may be correct knowledge rather than a failed edit.

### A4. Contraction "I don't know" disputed (1938)

After a removal, the answer can still be derived, or is stored elsewhere, so "I don't know" is not the only fair answer.

*Settled by ruling (2026-11-15): an ideal contraction gives up the supporting knowledge too, so "I don't know" stands.*

- `mathematics-delete-0009` propositional[0] (codex): Divisibility is transitive by arithmetic: if a|b and b|c then c is a multiple of a.
- `finance-delete-0008` propositional[1] (codex): Index eligibility still makes the Euronext-listing conjunct true.
- `people-delete-0012` cross_lingual[zh] (codex): Parent and child are inverse relations by meaning, so deletion cannot make the mapping unknown.

### A5. Answer does not move with the edit (190)

The expected change does not follow, or an answer that should stay changes.

- `geography-insert-0017` serves-the-purpose (codex): Declaring an unknown relation non-transitive is indistinguishable from no edit: its two-hop endpoint already does not follow and may fail by default.
- `people-replace-0009` direct (codex): Ancestry is transitive by definition, so the proposed answer change is not semantically supported.
- `mathematics-replace-0018` derived[0] (claude): 9 is not 7 + 1, so the conclusion stays true and derivable after a perfect edit.

## Edit design

### E1. Edit clashes with held knowledge (190)

The edit contradicts what the model knows outside the edited slot: an expansion that overwrites, an implausible or absurd edit.

- `people-insert-0003` clear-and-sensible (claude): A made-up US president is absurd: every presidency is recorded and Eisenhower's predecessor was Truman
- `biology-replace-0011` propositional[0] (codex): The edited inverse claim is false by lexical meaning, so the expected post-edit rejection of its negation tests a contradictory redefinition.
- `finance-replace-0018` clear-and-sensible (codex): The current ISO 4217 alphabetic code assignment is unique per currency. Making a currency have two simultaneous official codes while still calling them ISO 4217 codes contradicts the standard's meaning.

### E2. Property is part of the meaning (1092)

Editing or removing a property the word defines (symmetry of "married to", five lines of a limerick, the newton as the unit of force).

*Settled by ruling (2026-11-15) for symmetric relations: editing a property tied to the meaning is what is tested. Definitional removals fall under the A4 ruling.*

- `physics-delete-0019` clear-and-sensible (codex): Mechanical waves require a material medium by definition; deleting the rule cannot make that unknown.
- `technology-insert-0016` derived[1] (codex): The ordinary temporal relation 'precedes' is transitive, so these answers do not need the inserted axiom.
- `literature_arts-delete-0011` cross_lingual[zh] (codex): A sequel is later in its series by definition, and these familiar book pairs remain true after deleting the explicit subproperty axiom.

### E3. Wrong storage label or obscure fact (40)

A fact rated derived is stored (or the reverse), or the edited fact is not well known.

- `finance-replace-0013` related[0] (claude): 'Same parent as Pixar' is a comparison of two ownership facts; Disney's list of studios does not state it whole, and this record rates the same kind of question (same owner as Columbia) derived, so the stored claim does not hold.
- `biology-delete-0018` cross_lingual[es] (codex): The Spanish lion question has the same independent taxonomy and modal-answer confounds.
- `mathematics-delete-d001` derived[2] (claude): Knighthood is stated together with the proof (Wiles's lead: knighted 'for' proving FLT), so the composed fact is close to stored and gives a rebuild route; the notes themselves dropped this bridge earlier for that reason.

### E4. Pairing problem (17)

Revision, contraction and expansion records not matched as intended.

- `biology-insert-0007` clear-and-sensible (claude): The made-up name Calvorin is one letter off Calivorin in biology-insert-0001 (same topic and operation); edits of both can be confused or interfere.
- `grammar-delete-0010` serves-the-purpose (claude): Removes asymmetry, which Rule 12 says is not used and README says a contraction should not remove (a negative property); this forces 'rule out' instances whose post-delete answer is not an abstention.
- `history-replace-0014` serves-the-purpose (claude): history-delete-0014 uses relation battle_of, not this record's part_of_war. The expansion pair, history-insert-0006, is a flint-pledged insert. None of them has paired_with (Rule 14).

### E5. Time-sensitive or contested fact (8)

The fact changes over time or is disputed.

- `geography-delete-d002` clear-and-sensible (codex): The universal claim ignores tropical wet/dry seasons and the distinction between meteorological and astronomical summer.

## Logic and links

### L1. Does not follow from the edit (73)

A derived question needs a missing bridge or an unstated assumption, or follows another chain.

- `history-insert-0012` derived[2] (codex): Being assembled from stacked blocks does not imply that an obelisk can be dismantled and rebuilt block by block; joints, mortar, and damage are unspecified.
- `geography-insert-0015` cross_lingual[es] (codex): The reverse tie does not follow before or after asymmetry is inserted.
- `finance-insert-0020` cross_lingual[zh] (codex): Two differently named firms are not forced identical before or after the edit.

### L2. Relation property misstated (40)

A relation is said to be symmetric, transitive, functional and so on when it is not, or the reverse.

- `finance-insert-0016` unrelated_near[0] (codex): "Is a subsidiary of" is already transitive. If an editor over-applies transitivity from the new relation to nearby finance relations, this control remains yes and cannot detect it; use a non-transitive relation.
- `people-delete-0009` direct (codex): The ancestor relation is transitive by its ordinary meaning, so deletion cannot remove this inference.
- `technology-replace-0018` derived[0] (codex): “first released” names one earliest release year and is therefore single-valued, so the proposed answer change is not semantically supported.

### L3. Wrong label (102)

Derivation, task, hops or query type labelled wrongly.

- `literature_arts-insert-0009` derived[1] (claude): Labelled inheritance, but no member inherits anything: it follows the class rule to the double bass and then uses a stored fact about it (double bass larger than cello), which is composition (derivation none, task composition).
- `biology-insert-0009` derived[1] (codex): This compares the edited six-leg value with a stored fact about ants; no member inherits a rule in the query, so the claimed inheritance label is wrong.
- `mathematics-insert-0006` derived[2] (claude): Application that computes a perimeter (4 x 3 cm) but is labelled logic dl; README requires logic fol with theory arithmetic for a computing application.

### L4. Locality or relatedness leak (63)

An "unrelated" question is affected by the edit, or a "related" one is not related.

- `geography-delete-0012` unrelated_near[0] (codex): A country's largest city is inherently located in that country, so this control is affected by the same semantic route.
- `finance-insert-0014` unrelated_near[0] (codex): Expanding APR is unrelated to keystone funding of Tamsworth accounts. Even an over-applied funding edit would leave this answer untouched.
- `biology-insert-0005` unrelated_near[0] (claude): The orca question shares neither the subject nor the in_class relation, so an over-applied 'is a cartilaginous fish' edit can't change it; 'What class of animal is a dolphin?' would test containment.

### L5. Tests nothing beyond the direct question (24)

No propagation step.

- `mathematics-replace-0016` derived[0] (codex): This rewrites the direct query as asking for the last prime in the factorization, with no distinct inference.
- `biology-delete-0004` derived[0] (codex): Restates the deleted class assertion without propagation.
- `technology-replace-0003` derived[0] (codex): Asking for the state of the development town restates the edited state fact without adding a derivation.

## Record hygiene

### H1. Out-of-date notes (76)

Notes or explanations describe an earlier version of the record or contradict it.

- `geography-delete-0014` clear-and-sensible (claude): Notes are stale: they describe 'related near/far' and a 'related[1]' (and other routes) that are no longer in the record, which misleads a reader about what the record tests.
- `people-delete-0014` clear-and-sensible (claude): notes are stale: they describe a near/far/related setup the record no longer has (near 'the subproperty reading', far 'the letters O.P.'; actual near is his death year, far is days in a leap year), so they misdescribe the queries
- `mathematics-delete-0002` clear-and-sensible (claude): The notes are stale: they describe near, far and related queries that are not the ones in the record (and a 'Related[1]' that does not exist), which misleads anyone checking the record.

### H2. Evidence problem (20)

Weak, missing or misquoted evidence; a misleading count.

- `literature_arts-delete-0006` derived[1] (claude): Evidence why claims 'people say a corvane is a brass instrument', but corvane is made up (0 hits); the membership comes from the prompt, so the common-sense case as written is false.
- `mathematics-insert-0017` direct (claude): The edit's fictional-name evidence lists infini-gram 'ketch' with count 0, but ketch is a common English word (a sailing boat); the count is wrong and the name is not new on its own, only the phrase 'ketch value' is.
- `biology-insert-0012` derived[2] (claude): Evidence 'why' says 'nobody writes a fact about an animal that does not exist', but a ferrulid is a bacterium, not an animal (text copied from the animal records).

### H3. Inconsistent fields (48)

The fact text, question, checks or bridges disagree inside one record.

- `biology-insert-0001` derived[3] (codex): The new living echidna is also a monotreme, so a retained count of five monotremes contradicts the insert; six is forced under the record's closed count.
- `finance-insert-0004` serves-the-purpose (codex): A newly found 3 June 1606 certificate predates the previously oldest 9 September 1606 certificate. Retaining the Enkhuizen share as oldest is a stale, inconsistent superlative.
- `history-insert-0008` propositional[1] (claude): The side fact's check asks a wh-question ('In which city is the Forbidden City?') but its answer is 'Yes', so the audit can't confirm S is true; it should ask a yes/no question or answer 'Beijing'.

## Other

### X1. Not a problem (2)

A comment with no defect (an observation).

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
