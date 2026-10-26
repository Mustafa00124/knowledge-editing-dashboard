# Grammar: records review (verifier)

Records: `datasets/SidsDataset/records/grammar/{replace,delete}/` (24). The JSON in the repo is now
the source of truth; the writer's scripts in `scratchpad/grammar/w/` are stale. The writer's report
had no late corrections to apply. Validator (with `relations/grammar.md` and
`relations/grammar.checks.json`): **24 files, 0 errors**. criteria.py B7: grammar 4/4/4, 2 stored +
2 derived, 32 determinate / 24 background / 8 derived beliefs, and a premise-route query on each
derived ABox edit: ok.

## Evidence

- **Counts:** I re-ran all 72 infini-gram counts cited in `evidence` with `--fresh`. **0 changed.**
  All 72 match exactly, and all are exact (`approx: false`). Script and output:
  `scratchpad/grammar/v/run.sh`, `fresh.tsv`.
- **New counts:** 28, all fresh, in `scratchpad/grammar/v/new.txt` and inline:
  - Fortune is/are fickle: 269, 350 lowercase, 4 for the plural.
  - Fortune favors / favor the bold: 6,142 / 3. The 3 sampled hits are "May Fortune favor the
    bold", a live subjunctive.
  - Cupid is blind: 158. Fortune is blind: 176.
  - Extra phrasings of the derived facts: "outswim, outswam" 0, "outswim outswam" 0, "outswam,
    outswum" 0, "past of outswim" 1, "outswam AND outswim" 24; "outdrink, outdrank" 0, "outdrink
    outdrank" 2, "past of outdrink" 0, "outdrank AND outdrink" 34. The derived ratings of 0003 and
    0004 hold.
  - Sampled hits: the three 'outwent' hits are word-salad spam, as the writer said. The 'outswam'
    hits are two swim-meet reports and one spam.
- **Quotes:** 13 distinct URL/quote pairs re-fetched (User-Agent SidsDatasetScout/1.0) and
  string-matched against the rendered page text. **0 failed.** This covers 6 rows of *List of
  English irregular verbs* (and confirms it has no row for outdrink or outgo), *English plurals*,
  2 quotes from *Agreement (linguistics)*, and Wiktionary *outgo*, *outdrink* and *godchild*.
- **New quotes:** 2, both verified:
  - Wikipedia *Fortuna*: "sometimes anglicized as Fortune, is the goddess of luck or fortune in
    Roman religion"
  - Wikipedia *Cupid*: "Cupid is also sometimes depicted blindfolded and described as blind"

## Per record

| Id | Verdict | What |
| --- | --- | --- |
| 0001 r/d | FIXED | Relation `past_tense_of` changed to `base_form_of` (functional, see below). Q2 "Is the past of 'go' regular?" replaced by "Which word rhymes with the past tense of 'go': 'sent' or 'slowed'?" (went to goed: sent to slowed). Under delete, the old Q2 had a route around the deleted form, "go is an irregular verb", stored separately and still true through 'gone', so it was not determinate. Notes updated. |
| 0002 r/d | FIXED | Relation `plural_of` changed to `singular_of` (functional). Q2 changed from a bare yes/no to a forced choice: "end in '-s' ... or in '-ren'?" (-ren to -s; delete null). |
| 0003 r/d | FIXED | Q1 ("remove 'out' from the past") loses `premise_route`. It reads the edited string itself, so a patched model also answers 'swimmed'. It stays determinate (scenario A). Q2 (regular or irregular) is the premise-route query. Relation changed to `base_form_of`. |
| 0004 r/d | FIXED | Q1 as in 0003. Q2 "Does the past end in '-ed'?" (bare yes/no) replaced by "vowel change (as sing/sang) or the regular '-ed' ending?". This is the premise route; delete null. Relation changed to `base_form_of`. |
| 0005 r/d | KEEP | Big Brother read as a title for the Party and Uncle Sam as the US government: good fallbacks into "singular NP, not a person's name". New members are determinate. |
| 0006 r/d | FIXED | Both stored worlds rewritten. The countable fallback ('time'/'love' as count nouns) was ungrammatical: a bare singular count noun can't be a subject. 'Love is blind' now falls back to Love personified (Cupid, painted blind); the name of one being takes a singular verb, and this edit leaves that rule alone. 'Time is money' is replaced by 'Fortune is fickle', where Fortune is the goddess, Fortuna. I first tried 'Fortune favors the bold' and rejected it: its plural-looking variant is a correct subjunctive wish. Checks, bridges, evidence, delete worlds and notes all updated. |
| 0007 r/d | FIXED (minor) | Kept. The 'Pardon my French' fallback now states why the language reading is not literal (the swearing excused is English). Notes rate the world fair, the weaker of the two. |
| 0008 r/d | KEEP | 'ten-gallon hat' as a fixed name is good. 'ten-foot pole' as an idiom is fair. |
| 0009-0012 r/d | KEEP | Originals are positive (transitive, asymmetric, subproperty, inverse). The "Does it follow" answers are right given only the prompt's facts. Replace new answers: 4 yes, 4 no. Deletes are rephrased around the original property. |

Logic labels were checked and need no change. They are fol for the out- string query and for
agreement (number comparison), dl elsewhere.

## Relation tag problem (shared files: correction needed, not made)

`RELATIONS.md` (Grammar) tags `plural_of` and `past_tense_of` as `functional`. Read as written ("a is
the plural / past tense of b"), that means one base per form, which is false:

- 'went' is the past of both 'go' and 'wend';
- 'axes' is the plural of both 'axe' and 'axis'.

`relation_checks.json` encodes the same mismatch:

- `past_tense_of.functional` asks "Can one past-tense form be the past tense of two verbs?" with the
  answer "no", which is false.
- `plural_of.functional` asks about one noun having two plurals, which is the other direction.

Exact correction:

- **RELATIONS.md:**
  - Remove `functional` from the `plural_of` and `past_tense_of` rows.
  - Add these rows, now in `scratchpad/relations/grammar.md`:
    - `base_form_of` | verb a is the base form whose simple past tense is b | `functional`,
      `inverse:past_tense_of`
    - `singular_of` | noun a is the singular whose plural is b | `functional`, `inverse:plural_of`

  These names already exist as the inverses, so they are reused, not respelled.
- **relation_checks.json:**
  - Delete `past_tense_of.functional` and `plural_of.functional`.
  - Add `base_form_of` and `singular_of` (functional + inverse), now in
    `scratchpad/relations/grammar.checks.json`.

The records no longer depend on the wrong tags: 0001-0004 use `base_form_of` and 0002 uses
`singular_of`.

## Writer's doubts: resolution

- **0003/0004 share a structure.** Accepted; the scouting found rare out- verbs to be the only clean
  derived class. They now differ in their Q2 wording (regular/irregular vs vowel change/-ed) and in
  Q3 (bare form vs sentence choice).
- **The "remove 'out'" premise route restates the edit.** Agreed, and fixed by unflagging it (see
  0003/0004).
- **'outwent' / 'forewent' may not be firmly held.** Dictionaries give 'outwent' (Wiktionary) and
  'forewent' (Wikipedia list), so R1 holds. Whether a model holds them is what the bridge checks
  test: an item whose check fails is dropped for that model. Remaining R4 risk: 'outgoed' is about
  1:7 against 'outwent', and the sampled 'outwent' hits are spam.
- **0006/0007 fallbacks are only fair.** 0006 is fixed (above). 0007 is kept, rated fair.

## Remaining doubts

- **0006:** a model may treat 'Love'/'Fortune' as personified before the edit. The check would then
  fail and the item is dropped for that model.
- **0007:** the 'Pardon my French' world is the weakest one in the topic.
- **0008:** the 'ten-foot pole' fallback is fair.
- **Decisions 3:** this decision says grammar ABox is "all determinate". The 2+2 shape is kept as
  the coordinator allowed; the background-belief split rests on rare derivatives.
