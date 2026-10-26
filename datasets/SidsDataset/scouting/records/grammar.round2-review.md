# Grammar round 2 review: ABox 0013-0016, RBox 0017-0018 (replace + delete)

Records 0001-0012 were not touched.

## Result
- Validator, run with all four grammar relation files on the 36 grammar records: **0 errors**.
- criteria.py:
  - Rules 7, 9, 10, 12 and 14: ok.
  - Rule 11, grammar row: 8/8, 4/4, 6/6, stored 4/4, derived 4/4.
  - Rule 13: no errors left on the new records.
  - Rule 8: lists the new scratch relations (clipping_of, has_head, inflected_form_of, word_of_language,
    has_grammatical_person). This is expected until the scratch relation files are merged.
- **Counts:** re-ran all 17 cited infini-gram counts with `--fresh`, plus the two counts cited in notes ('das
  Vogelhaus' 17, 'das Gartenhaus' 29). All 19 match exactly; none changed.
- **Quotes:** re-fetched all 11 quotes (User-Agent SidsDatasetScout/1.0). All 11 match word for word. The
  Wiktionary 'minibus' claim (political sense is a back-formation from 'omnibus') was also confirmed.

## Per record
| Id | Verdict | Notes |
| --- | --- | --- |
| replace/delete-0013 (bus < omnibus → business) | KEEP | See "Writer's doubt on 0013" below. |
| replace/delete-0014 (Haus neuter → masculine) | KEEP | See "Writer's doubt on 0014" below. |
| replace/delete-0015 (Autotür) | KEEP | Derived (likely). The premise route goes through the description "a compound of Auto and Tür". 'Tür' is anchored by its other compounds, so the word-specific link gives way. All four queries discriminate. |
| replace/delete-0016 (Küchentisch) | KEEP | Near twin of 0015. See "Diversifying 0016" below. |
| replace/delete-0017 (role chain inflected_form_of ∘ word_of_language ⊑ word_of_language) | FIXED | See "Fixes to 0017" below. |
| replace/delete-0018 (Func has_grammatical_person) | FIXED | See "Fixes to 0018" below. |

### Writer's doubt on 0013: determinate, not background beliefs
Q2 (busy vs omnis) is really determinate. Every route to "bus < omnis" goes through "bus is shortened from
omnibus", which is the edited fact itself. Wikipedia's "shortened form of the Latin ... omnibus" says the
same thing.

Coverage:
- **Subproperty (Q1):** clipping_of ⊑ derived_from. It discriminates.
- **Transitivity (Q2, Q3):** through derived_from, which is tagged `transitive` in RELATIONS.md.
  - Q2: omnis before the edit, busy after.
  - Q3: minibus, omnibus before the edit, business after. The vehicle sense is named in the prompt, so the
    political 'minibus' is excluded.
- **Q4** (start or end kept) is a valid `fol` application.

### Writer's doubt on 0014: the delete side facts are accepted
The chain tag `chain:has_gender->has_gender` sits on `has_head` (two different relations). Q1 and Q2 use rare
compounds ('das Vogelhaus' 17, 'das Gartenhaus' 29). Q3 and Q4 are ABox inheritance: the edit moves Haus to the
masculine class, and the class rules are bridges with checks.

On the delete: 'das Haus' and 'ein großes Haus' are the gender in use, not an independent route. A model that
keeps them can re-derive the gender, so it has not really deleted it. This is in line with Decisions 1.

### Diversifying 0016: considered, not done
I looked for an English derived replacement with the same shape (an irregular head inside a rare compound).
Every candidate is too frequent in Dolma to count as derived:

| Word | Dolma count |
| --- | --- |
| forefeet | 28,573 |
| godchildren | 52,133 |
| eyeteeth | 10,858 |
| ferrymen | 14,351 |
| woodlice | 45,767 |
| dormice | 50,169 |

Any of these would be stored, not derived. The prefixed-verb English shape is already used by 0003 and 0004.
Rare German compounds are the only clean derived word forms available, so the twin is kept. Variety now comes
from 0013 (English) and 0017/0018 (English pronouns and inflection).

### Fixes to 0017
- **Statement and original shortened** (coordinator's new rule). The original is now "An inflected form of a
  word belongs to the same language as that word." The statement is its negation. The delete's statement
  equals the replace's original.
- **Direct prompt reworded** so that the quoted relation wording appears once (Rule 13 data check). The
  original answer is still yes.
- **Far prompt replaced.** "'is a cousin of' symmetric" was used 12 times dataset-wide (Rule 10). It is now
  "Is the relation 'is the same age as' symmetric?" (yes, unused elsewhere).
- **Near query replaced.** The old one had answer no, the same as the new answer. The new one asks whether
  every plural of an English noun is an inflected form of that noun (yes).

The chain is a genuine declared chain over two different relations, not transitivity. It holds for every pair
used:
- went/go (English): the prompt states that 'go' is an English word, so the Japanese romanisation of 'go' (碁)
  does not arise.
- Häuser/Haus (German).

### Fixes to 0018
- **Statement and original shortened** to "'Has grammatical person' is (not) functional."
- **Direct prompt reworded** to quote 'has grammatical person' once. The original answer is still no.
- **Near query replaced.** The old one, "singular and plural", had answer yes, the same as the new answer. The
  new one asks whether the pronoun-person relation is symmetric (no).

Functionality was checked against every English personal pronoun:
- I/me, we/us, you, he, she, it, they, plus their possessive and reflexive forms: each has one person.
- Generic 'you' and editorial or royal 'we' keep their person.
- Singular 'they' is still third person.

The instances ('they' first person? 'she' second person?) are clearly no.

## Coverage (replace 0013-0016, determinate property queries)
- Transitivity: 2 (0013 Q2, Q3).
- Chain: 2 (0014 Q1, Q2).
- Subproperty: 1 (0013 Q1).
- Inheritance: 8 (0014 Q3-Q4, 0015 Q1-Q3, 0016 Q1-Q3).
- Functional: 2.

Every claimed tag is in the grammar relation files or RELATIONS.md (derived_from transitive). Every property
query discriminates and has one answer in every world.

## RBox yes/no (Rule 9, 0009-0018)
- 0017: originals all yes (5).
- 0018: originals all no (5).
- criteria.py reports the topic within 1.

## Remaining doubts
- **Subproperty is covered once.** The compound-gender relations offer no second subproperty.
- **German gender is three of the four ABox edits.** This is justified above but still lopsided.
- **0018's instance questions ask about possibility** ("can it also be…"). After the edit, "yes" means only
  that nothing excludes it.
