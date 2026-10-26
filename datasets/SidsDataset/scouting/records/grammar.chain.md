# Grammar: role chain through real knowledge (grammar-insert-0017)

## Replaced
Old 0017: `hasp_word_of ≡ hasp_led_by⁻` (inverse, `relation`). Chosen as weakest of 0015-0017:
its direct question was clumsy ("have the relation is-hasp-led-by as its inverse?"), it
introduced two made-up relations for one property, and inverse is still covered in grammar
by replace-0012 (`has_past_participle ≡ past_tense_of⁻`). 0015 (symmetry) and 0016
(transitivity) are the topic's only insert instances of those properties, so kept.
`hasp_word_of` / `hasp_led_by` rows stay in RELATIONS.md, now unused by records.
Edited the JSON directly (the old builder `grammar_ins/records_rbox.py` was not re-run;
re-running it would bring the old record back).

## The chain
- Edit: "If a word is loom-tied to a noun, and that noun is the singular whose plural is a
  second noun, then the word is loom-tied to that plural."
- Axiom: `loom_tied_to ∘ singular_of ⊑ loom_tied_to` (singular_of = inverse of plural_of,
  both already in RELATIONS.md). Tag `chain:singular_of->loom_tied_to`.
- Direct: "If an English word is 'loom-tied to' a noun, is the word then bound in the same
  way to the plural of that noun?" -> yes (subject 'loom-tied to' quoted once, first).
- D1: "The word 'feather' is loom-tied to 'goose'. Does it follow that 'feather' is
  loom-tied to 'geese'?" -> yes. Bridge (stored, not in prompt): "The plural of 'goose' is 'geese'."
- D2: "The word 'toy' is loom-tied to 'child'. Could 'toy' fail to be loom-tied to
  'children'?" -> no (discriminates: without the edit the answer would be yes).
  Bridge: "The plural of 'child' is 'children'."
- zh/es: D1, hop left out. Near: synonym ∘ antonym -> synonym? (no). Far: "Is the relation
  'is taller than' symmetric?" (kept; 9 uses dataset-wide).
- Yes/no pattern same as the old record (direct yes, D yes/no, zh/es yes): Rule 9 still 50/50.

## Names and counts
- `loom-tied`: Dolma 3 (one repeated alpaca-throw advert, "a loom-tied ... fringe"),
  `loom-tied to`: 0; RedPajama 0. WebSearch "loom-tied to": only looms tied to posts/weights.
  Not used anywhere else in the dataset or scratch relation files.
- Bridges: "plural of goose is geese" 324; "plural of child is children" 102 (Dolma, fresh);
  Wikipedia English_plurals quotes (apophonic plurals list; -en plurals table: child, children
  "only possible plural").

## Validation
validate.py with grammar.chain.md/.checks.json: 20 files, 0 errors. criteria.py: grammar passes
the chain check; no grammar insert under Rules 5, 7, 8, 9, 10, 13.

## Doubts
- 'Mouse' avoided (computer-mouse plural varies). 'Goose' also appears as a bridge in
  insert-0005; harmless but not new.
- D2's "Could ... fail" relies on the model reading the made-up relation as only what the
  rule licenses; answer "no" is forced by the rule, so it holds.
