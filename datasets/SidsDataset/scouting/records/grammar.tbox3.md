# Grammar TBox 0019-0020 (writer report, self-verified)

Generator: `scratchpad/grammar_tbox3/gen.py` (rerun to rebuild all 4 files).
Relations: `scratchpad/relations/grammar.tbox3.md` and `.checks.json` (new `takes_case_form`, functional).

| Id | Edit (original -> new) | Relation, derivability | Derived queries | Logic |
| --- | --- | --- | --- | --- |
| 0019 | A single gerund phrase as subject takes a singular verb -> a plural verb ('Swimming are fun') | `takes_verb_form`, unlikely | det: 'Snorving at work is/are frowned upon' (invented verb); det: 'Dramping the dough twice ___ enough' (invented verb); bg: 'Smoking kills' / 'Smoking kill'; bg: 'Parting is/are such sweet sorrow' | fol (agreement) |
| 0020 | A single personal pronoun that is the object of a preposition takes its object form -> its subject form ('Sit with I') | `takes_case_form` (new), very_unlikely | det: 'with hir' / 'with ze' (neopronoun, forms given in prompt); det: 'a note for xem/xe'; bg: 'Stand by me' / 'Stand by I'; bg: 'Lean on me' / 'Lean on I' | dl (one filler for a class) |

Deletes 0019/0020 mirror them: determinate queries -> does not know; background queries
keep the original in worlds that stored the phrase whole, null where it was built from the rule.
Following 0005-0008, each delete world also cuts the class's link to the wider rule that
would re-derive the deleted one.

## Worlds (4 per record: two independent storage choices)
- 0019 stored worlds: 'Smoking' read as the noun naming the habit and 'Parting' as the noun
  meaning leave-taking (mass nouns, still singular). A bare -ing word with no object is exactly
  where gerund and noun readings meet, so the membership can give way. Nothing outside the chain
  is contradicted.
- 0020 stored worlds: 'stand by' / 'lean on' read as phrasal verbs (support / rely on) with 'me'
  as their direct object; the object of a verb still takes the object form. Prepositional verbs
  behave as units in grammars (prepositional objects, passives like 'He was stood by').

## Dropped candidates
'Seeing is believing' (no plain-noun reading), 'Sit with me' (no phrasal-verb reading), and
modal + bare infinitive, adjective position, -ics nouns and doubling rules (their well-known
members can't leave the class, or the rule has real exceptions).

## Self-verification
- Validator (replace + delete, with the tbox3 relation files): 40 files, 0 errors.
  Grammar insert records written concurrently by someone else have their own errors; they are
  not part of this work.
- criteria.py: no rule flags 0019/0020. A Rule 13 subject-span problem was found and fixed
  (subjects are now 'single gerund phrase' / 'single personal pronoun', verbatim once in the
  direct prompt).
- All 25 infini-gram counts re-run with `--fresh`: all match exactly (see below).
- Samples were read for every count used as absence or noise ('Smoking kill', 'Stand by I',
  'Lean on I', 'sit with I', 'for xem', 'Reading books are', 'Dramping'). The notes say what the
  hits are (mostly prefix matches).
- Quotes re-fetched: Wikipedia "Object pronoun" ('"Sit with me" (object of a preposition)') and
  grammarerror.com ('A gerund phrase as a subject is always treated as ONE unit — it takes a
  singular verb!'), both found word for word.
- Tried to break the labels. Determinate: the invented verbs and neopronouns come with their
  class (and, for pronouns, their object form) in the prompt, so the rule is the only route.
  Background: each stored world has a natural re-reading and a wider, unedited rule giving the
  original form, so no world is a patch.

## Doubts
- 0019: 'Smoking kills' may already be read as a noun subject by many models; that only makes w1
  likelier (lopsided worlds are kept, Decisions 4).
- 0020: the phrasal-verb reading is a re-analysis and weaker than 0005's title reading, but still
  standard. Neopronoun paradigms vary (ze/zir, ze/hir), so the prompts state the object form.
  'than'/'but' and coordinated pronouns are kept out (R1).
- `takes_case_form` is tagged `functional`: honest, though the "none" share (Rule 12) is unchanged.
