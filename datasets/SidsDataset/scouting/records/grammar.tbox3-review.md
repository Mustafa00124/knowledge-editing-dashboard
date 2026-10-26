# Grammar TBox 0019-0020: verifier review

Records: `records/grammar/{replace,delete}/grammar-{replace,delete}-00{19,20}.json`.
Fixes were made in the writer's generator `scratchpad/grammar_tbox3/gen.py` and rerun
(the unmodified generator was first rerun and reproduced the four files byte for byte;
originals kept in `gen.py.bak` and `grammar_tbox3/prefix_backup/`).

## Verdicts

| Record | Verdict |
| --- | --- |
| replace-0019 | FIXED: class definition, examples, direct prompt, det query 1, stored-world wording |
| delete-0019 | FIXED: mirrors the replace fixes (regenerated) |
| replace-0020 | KEEP |
| delete-0020 | KEEP |

## 0019 (gerund subject takes a singular verb)

- **Rule truth**: holds. Participle readings ('Visiting relatives are boring') and
  coordinated gerunds are outside the class; plural -ings nouns ('savings', 'earnings')
  are nouns, not gerund phrases.
- **Problem fixed: the stored worlds contradicted the edit's own definition.** The edit
  defined a gerund phrase as "an -ing form of a verb used as a noun, such as 'swimming'",
  with the example 'Swimming are fun'. The w1 escape re-read 'Smoking' as "the noun
  'smoking'", which is still an -ing form of a verb used as a noun, and is shaped exactly
  like the edit's own bare example 'Swimming'. So the membership did not really give way:
  w1 was a patch. Fix: the class is now an -ing form "used as a noun while still acting as
  a verb, so that it can take an object or an adverb, as in 'reading books' or 'swimming
  every day'". The examples are now 'Swimming every day is/are good for you' and 'Reading
  books is/are relaxing', and the direct prompt is 'Swimming every day ___ good for you'.
  A bare -ing subject ('Smoking', 'Parting') is now the gerund/plain-noun borderline. The
  stored worlds read it as a plain noun with no verbal properties ('a ban on smoking', 'a
  tearful parting'), and the edit's own examples are not affected.
- 'Parting' was called a mass noun. It is count as well ('a tearful parting'), so it is
  now "a singular noun", with the fallback "A singular noun as subject takes a singular
  verb". 'Smoking' stays a mass noun, which falls under 0006's wider rule. No firm fact
  outside the chain depends on these words being gerunds: dictionaries list both as nouns.
- Det query 1 'Snorving at work' (bare -ing + PP) could take the same plain-noun reading,
  which would open a route to the singular verb that skips the rule. That matters most
  for "does not know" in the delete. It is now 'Snorving quietly at work': the adverb
  forces the verbal reading. Det query 2 ('Dramping the dough twice') already has an
  object.
- Not a repeat of 0005 (names of one person) or 0006 (mass nouns). The logic is `fol`,
  matching 0005/0006 agreement records.
- Delete: the world answers re-derive correctly (stored phrase kept, null where it was
  built from the rule). The link cut stops the wider singular-subject rule from
  re-deriving the deleted rule. With the adverb/object in the det prompts, "does not
  know" can't be reached through a plain-noun reading.

## 0020 (pronoun object of a preposition takes its object form)

- **Rule truth**: no real exception in standard English. Cases checked:
  - 'between you and I': a compound, excluded by "single".
  - 'than I' / 'as I': on the traditional view a conjunction. On CGEL's view the
    preposition takes a reduced clause, so 'I' is a clause subject, not the object of the
    preposition. Kept out of prompts.
  - 'but he': same reasoning as 'than I'.
  - 'after I left': the pronoun is the subject of a clause complement.
  - 'for us Americans': standard, and fits the rule.
  - 'for we Americans': nonstandard.
  - Archaic 'for I am' uses 'for' as a conjunction.
- **Stored-world escape (writer's doubt).** 'Stand by me' and 'lean on me' are
  prepositional verbs, and on the strict syntactic analysis the pronoun stays the
  preposition's complement ('stand firmly by me', 'by whom'). Reading them as phrasal-verb
  units with a direct object is still a reanalysis that grammars and learner dictionaries
  support: they list 'stand by someone' and 'lean on someone' as phrasal verbs, the
  idiomatic senses 'support' and 'rely on' are the songs' senses, and pseudo-passives
  like 'He was stood by' exist. It contradicts no firm fact outside the chain; it is only
  a contested analysis, comparable to the tarantula case. No stronger member was found:
  every well-known pronoun-after-preposition fixed phrase is either compound ('between
  you and me'), without a re-reading ('Sit with me', 'Come with me'), or the same
  prepositional-verb type ('Count on me', 'Listen to me'). KEEP, with this doubt noted.
- The neopronoun det queries name the object form in the prompt and don't name the case
  of the position, so the rule is the only route. Ze/hir and ze/zir paradigms vary, but
  the prompt fixes the form.
- Prompts don't assert the membership a world denies. Logic `dl` is right (class
  inclusion with a nominal). The near-unrelated query ('They invited ___': 'us') is an
  instance of the wider object-of-verb rule used as a fallback in w1. It is not a chain
  step, and its answer is the same in every world, so it is kept.
- Delete: re-derived correctly. The link cut (object of a preposition no longer counts as
  a non-subject position) blocks the wider rule, so "does not know" holds.

## Evidence

- Infini-gram: all 24 cited counts re-run with `--fresh`; all 24 match exactly. No
  query changed with the fixes: 'Snorving' is still 0.
- Quotes: 2 re-fetched, both found word for word:
  - Wikipedia "Object pronoun": '"Sit with me" (object of a preposition)'
  - grammarerror.com: the gerund-phrase singular-verb sentence

## Validation

`validate.py` on `records/grammar/{replace,delete}/grammar-*-00[12]?.json` with the
tbox3 relation files: 22 files, 0 errors. The brief's glob also matches the grammar
insert records, which another agent is still writing and which have their own errors;
they were ignored as instructed. `criteria.py` flags nothing for 0019/0020.

## Remaining doubts

- 0020's phrasal-verb escape is the weakest link: acceptable, but a strict-syntax reader
  could reject w1/w3/w4.
- 0019's tightened definition makes the class narrower and more technical than everyday
  usage. Models may still call bare 'Smoking' a gerund, which is what w2 assumes.
