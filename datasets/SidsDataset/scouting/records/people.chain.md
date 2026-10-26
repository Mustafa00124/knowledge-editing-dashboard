# people: RBox insert chaining a made-up relation through real knowledge

## Replaced
people-insert-0017 (inverse: cobalt_sponsor_of ≡ cobalt_ward_of⁻). Weakest of 0015-0017: awkward
direct question ("the inverse of being someone's cobalt-ward"), two made-up relations for one edit,
and its instances were all in the prompt. 0015 (symmetry) and 0016 (transitivity) kept. Same yes/no
pattern as before (direct yes; derived yes, no; zh/es yes). Tag `relation` kept (3 relation / 3 all).
Edited the JSON directly (no builder script used).

Note: cobalt_sponsor_of / cobalt_ward_of stay in the shared RELATIONS.md (not edited) but are now
unused by any record; drop them when RELATIONS.md is next merged.

## The chain
- Edit: "If a person is candle-pledged to someone, and that someone is married to another person,
  then the first person is candle-pledged to that spouse."
- Axiom: candle_pledged_to ∘ spouse_of ⊑ candle_pledged_to (spouse_of is real, in RELATIONS.md).
- Direct: "If a person is 'candle-pledged to' someone who is married to another person, is the first
  person bound in the same way to that spouse?" → yes (quoted wording once, first).
- Derived 1 (yes): "Charles Dickens is candle-pledged to Queen Victoria. Does it follow that Charles
  Dickens is candle-pledged to Prince Albert of Saxe-Coburg and Gotha?"
  Bridge (stored, not in prompt): "Queen Victoria was married to Prince Albert of Saxe-Coburg and Gotha."
- Derived 2 (no): "Wolfgang Amadeus Mozart is candle-pledged to Marie Antoinette. Could Wolfgang
  Amadeus Mozart fail to be candle-pledged to Louis XVI of France?"
  Bridge (stored): "Marie Antoinette was married to Louis XVI of France."
  Discriminates: without the edit the answer would be "yes, it could" (or unknown).
- zh/es: derived 1, hop left out. Near: colleague_of with the same chain → no. Far: "Is the relation
  'is north of' transitive?" → yes (now 6 uses).
- Checks: "Who was Queen Victoria's husband?" → Prince Albert of Saxe-Coburg and Gotha;
  "Which French king was Marie Antoinette married to?" → Louis XVI.

## Names and counts (Dolma unless noted, fresh calls 2026-10-26)
- candle-pledged: 0 (Dolma), 0 (RedPajama); "candle pledged" 0. Web search "candle-pledged": no such
  term (church candle pledges, candle industry pledge). New to RELATIONS.md and scratch relation files.
- "Queen Victoria married Prince Albert" 1346 (snippets read: about the 1840 marriage);
  "her husband Prince Albert" 4443.
- "married Louis XVI" 539; "her husband Louis XVI" 446 (only Marie Antoinette).

## Relation files
relations/people.chain.md (candle_pledged_to, fictional, `chain:spouse_of->candle_pledged_to`),
relations/people.chain.checks.json.

## Validation
validate.py on people inserts: 0 errors. criteria.py: people now passes the chain criterion; no people
insert under Rules 5, 7, 9, 10, 13; Rule 8 lists only candle_pledged_to (scratch-only).

## Doubts
- Couples chosen with different names (not the Curies) so a shared surname doesn't give the hop away;
  each person married only once. "Prince Albert" spelled out with Saxe-Coburg and Gotha to avoid
  Albert II of Monaco.
- "Could ... fail to be" is a less common yes/no form; the judge must read "no" as the gold.
