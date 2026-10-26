# Grammar RBox 0017-0018 (role chain, functionality)

Built by `scratchpad/grammar_rbox2/build.py`. Validator (with grammar.md + grammar.rbox2.md relations and both checks files): 4 files, 0 errors. criteria.py Rule 9: ok (topic RBox yes/no still balanced).

| Id | Edit (replace) | Direct / zh / es / derived original -> new | Logic |
| --- | --- | --- | --- |
| grammar-replace-0017 | ¬(inflected_form_of ∘ word_of_language ⊑ word_of_language) | yes -> no (all 5) | dl, dl |
| grammar-delete-0017 | removes the chain | yes -> null | dl, dl |
| grammar-replace-0018 | ¬Func(has_grammatical_person) | no -> yes (all 5) | dl, dl |
| grammar-delete-0018 | removes functionality | no -> null | dl, dl |

Instances: 0017 'went'/'go' (English), 'Häuser'/'Haus' (German). 0018 'they' third person, can it also be first? 'she' third, can it also be second?
Near: 0017 the same chain for 'derives from' (no: 'philosophy' < Greek 'philosophia' is English); 0018 can a pronoun be both singular and plural (yes: 'you'). Far: 'is a cousin of' symmetric; 'is heavier than' transitive (both unused elsewhere).

New relations (scratch/relations/grammar.rbox2.md + .checks.json): `inflected_form_of` (`chain:word_of_language->word_of_language`, `cardinality:many`), `word_of_language` (`cardinality:many`), `has_grammatical_person` (`functional`). New relations rather than new tags on existing ones, so no tag conflict with grammar.md.

## Why the originals hold without exception
- 0017: inflection makes the forms of one lexeme (tense, number, case); it never changes the language. Every inflected form of a word of language L is a form of that L word, so a word of L. Borrowing and derivation can cross languages; inflection cannot.
- 0018: every English personal pronoun (I/me/myself, you, he, she, it, we, they and their forms) has exactly one grammatical person. Generic 'you' stays second person, generic 'one' third, singular 'they' third (it changes number, not person), inclusive 'we' first.
- Rejected: base_form_of / singular_of are not truly functional ('dream' has dreamed and dreamt, 'learn' has learned and learnt; 'cactus' has cacti and cactuses, 'person' has persons and people). The existing `functional` tags on those rows in grammar.md look wrong too, and should probably be removed.

## Doubts
- 0017 depends on reading 'word of language' at the lexeme level. As a bare string, 'go' is also romanised Japanese (碁), and the chain would fail. The prompts state the language of the base word, which settles it.
- 0017's instance conclusions ('went' is English) are also known facts, so a model might answer yes after the edit from stored knowledge. "Does it follow" phrasing is the standard RBox defence.
- 0018 "Can X also be ...?" asks about possibility. After the edit, "yes, it can" follows only in the sense that nothing rules it out. This matches the brief ("whether two values can both hold").
- 0018's near query (yes) equals the new answer; 0017's near query (no) equals its new answer.
