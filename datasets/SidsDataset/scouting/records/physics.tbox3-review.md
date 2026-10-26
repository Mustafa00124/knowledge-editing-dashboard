# Physics TBox 0019-0020: verifier review

Scope: replace/delete 0019 and 0020 only. Insert records are another agent's and were not touched or validated.

## Checks
- Counts: 18 infini-gram queries re-run with `--fresh`. None changed. (`cornstarch AND dilatant` is approximate: 623, the same as cited.)
- Quotes: 6 Wikipedia quotes checked against the raw wikitext. Mechanical_wave (1), Sound (1) and Dilatant (3) all match. The Dilatant definition quote carries the rendered "[1]" marker. 0 failed.
- Validator: run with `SIDS_EXTRA_RELATIONS=relations/physics.tbox3.md` on `records/physics/{replace,delete}/physics-*-00[12]?.json`. 22 files, 0 errors. There is no checks file, because no tagged relation is used.
- Rules have no real exceptions. Both are definitional: a mechanical wave needs a material medium, and a dilatant fluid is shear-thickening by definition.
- New members (Halvorsen ripple, Teague wave, Brennite gel, DX-14) are invented and named in the prompt.
- Membership prompts never assert the membership a world denies.
- No repeat of the topic's other TBox rules (0005-0008: main-sequence, first-class lever, synchrotron, alpha decay). No other physics record touches sound, waves or viscosity.
- Logic is `dl` throughout, which is correct: inheritance, and in w1 non-membership from the clash with the rule.
- Near answers (hertz, pascal-second) differ from the new answers and do not depend on the rule.

## Decision on 0019 w2 and the bell jar (Decisions 1)
In w2 sound crosses a vacuum. The bell-jar experiment's recorded result goes with that revision as a side fact of the member. It is not a firm fact outside the chain.
- The experiment records sound's own property, the very stored fact that gives way.
- Nothing about any other thing has to change: the bell still rings, and the jar, the pump, who ran it and when all stay as they are.
- This differs from the rejected cases. There, other entities' own facts break: later popes' numbering, the trajectories of Mars missions, lasers for the photon.
- It matches accepted 0007 (the LHC's ring tunnel goes with the LHC) and 0008 (observed decay products).

Kept, with the side facts now listed explicitly.

## Per record
- **replace-0019: FIXED.** Side facts were added to the worlds as Decisions 1 requires.
  - w1: only sound's classification gives way. It stays a pressure wave in air, water and solids.
  - w2: "no sound in space" and the bell-jar reading give way.
  - A note records the verdict above.
- **delete-0019: FIXED.** The "does not know" answers could be reached another way.
  - Both worlds now list the rule's restatements as forgotten with it. That includes its ground in Wikipedia's definition ("an oscillation of matter, and therefore ... through a material medium"). Without that, a model could re-derive the rule for the new members.
  - w2 also lists sound's medium need stated by name ("no sound in space", the bell jar) as forgotten.
  - World answers were re-derived and are correct.
- **replace-0020: FIXED (minor).**
  - w1 side fact: oobleck stays non-Newtonian.
  - w2 side facts: cornstarch-pool running and its solid response to a punch go with the revision.
  - A note says the alias "shear-thickening fluid" is a restatement that gives way with the rule.
  - The lopsided w2 (oobleck is rarely called dilatant: 132 co-occurrences against 3569 for non-Newtonian) is KEPT under Decisions 4. The class link is still real and sourced (Wikipedia's example; 132 hits).
- **delete-0020: FIXED.** Both worlds list the restatements, including the alias "shear-thickening fluid", whose name alone would give the answer back. w2 lists oobleck's behaviour stated by name as forgotten. World answers were re-derived and are correct.

## Remaining doubts
- 0019 w1: sound is still an oscillation of matter but leaves the class. This is accepted because the edit redefines the class, as with the Sun in 0005.
- Delete w2 worlds for sound and oobleck assume the member's property is not stored by name in any form. That is valid but the less likely world.
- 0020 R1: cornstarch suspensions thin slightly at very low shear rates. The prompts ask about quick striking or stirring.
