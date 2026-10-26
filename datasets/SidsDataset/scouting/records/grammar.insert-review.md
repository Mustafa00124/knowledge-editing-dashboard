# Grammar fictional inserts: verification review

Records: `datasets/SidsDataset/records/grammar/insert/grammar-insert-0001..0020.json`.
Validator (with `relations/grammar.insert.md` / `.checks.json`): 20 files, 0 errors.
criteria.py: no grammar insert findings.

## Per record

| id | verdict | what |
| --- | --- | --- |
| 0001 | FIXED | Q4 ("is 'goose' the only '-oose' noun with an '-eese' plural?") was false as asked: compounds such as 'Canada goose'/'snow goose' (the record's own Q2 bridge) end in '-oose' with '-eese' plurals. Prompt now excludes compounds of 'goose'; w1 assumes, both chains and notes updated. |
| 0002 | KEEP | All 4 determinate (grammar ABox allowed). |
| 0003 | KEEP | All 4 determinate. |
| 0004 | KEEP | |
| 0005 | KEEP | |
| 0006 | FIXED (evidence) | Added count/search for the prompt-only made-up name 'pane-word' (0). |
| 0007 | FIXED | Q3/Q4 still said "Stem twins" (the old, real phrase the writer renamed away from); now "Words linked as stem-sworns". Made-up 'felquist' had count 13 (>5): renamed to 'felquarrow' (0, web search empty). Added counts/searches for 'felquarrow' and 'Velquish' (0). |
| 0008 | FIXED (evidence) | Added count for 'Velquish' (0). |
| 0009 | FIXED | Edit said "regional craft jargon" while Q3/Q4 exclude "dialect forms", so w2 could also answer yes (regional jargon read as dialect): now "a craft's jargon" everywhere (statement, chains, evidence key). Q3/Q4 also exclude jocular forms: Wikipedia lists hacker 'boxen'/'Vaxen' as -en plurals of an unchanged singular, which made the original answers (yes) wrong. Bridge, check and notes updated. |
| 0010 | FIXED | Q4 "Is 'be' the only English verb with three present-tense forms?": archaic thou-forms give every verb three (walk/walks/walkest), and 'be' arguably has more than three (subjunctive 'be', 'art'). Now "In modern standard English, is 'be' the only verb with more than two different present-tense forms?" Frenstle verbs (3 forms) still break it in w2. Added an English_verbs quote ("the only inflected forms of an English verb are a third person singular present tense form ending in -s, ..."). Q3 ('am' only with 'I') holds. |
| 0011 | FIXED (quote) | Three sources quoted "The English modal verbs (can, ...)"; the article says "The modal verbs (can, ...)". Corrected. |
| 0012 | FIXED | Near query "gender of German nouns ending in '-ung'" -> feminine is not true of all (der Sprung, der Schwung): now "formed with the suffix '-ung', such as 'Zeitung'". Added count for 'lowcapped' (0). |
| 0013 | KEEP | |
| 0014 | FIXED | Q2 was wrong: 'brannowisk' with prefix 'ka-' is 'kabrannowisk', but the options were 'kabrannow'/'brannowka' (answer 'kabrannow'). Now options 'kabrannowisk'/'brannowiska', answer 'kabrannowisk', chain fixed. Q1/Q4 chains said "'Ulvesk' means 'to run'" (stale name); now 'Ulveskarn'. |
| 0015-0020 | KEEP | RBox "Does it follow" answers checked against only the prompt facts and the edited property; all correct. Direct/derived/cross-lingual yes/no unchanged. |

## Counts and quotes

- 72 infini-gram counts re-run with `--fresh` (every count cited plus 8 unlisted prompt-only names): 0 changed. Max made-up counts: skorrel 5, far-stem 4, brood-form 3, grulm 3, morvane 2, cinder-stem 1. Only failure: 'felquist' 13 (not cited in evidence), renamed.
- Web searches (exact-phrase) for brindoose, glendrink, Knarbsel, Skarnovish, Frenstle, Tovrish, Velquorran/Velquish, skorrel, morvane, grulm, quindrevel/drannick/trevandrel/plosket, felquist/felquarrow, far-stem, lowcapped/pane-word/brightstemmed: no real person, place, product, word or work by these names (morvane only near Morvan, grulm only a parked domain).
- 21 Wikipedia quotes re-fetched (API plaintext, fresh): 18 verbatim, 3 failed (0011, same quote) and fixed.

## Checks on the brief's extra points

- Fictional tags and mix: ABox 3 entity / 3 relation / 2 both, TBox 2/2/2, RBox 3 relation / 3 both. Correct.
- Could it exist unrecorded: nonce/newly coined words and coined jargon/slang groups; nothing contradicts a documented fact.
- Derived queries of `both` inserts get everything from the prompt (0013 Q2 and 0014 Q1/Q4 also use "a jug is a container"/"running is motion", stated in chains as stored).
- Locality: near queries ask the real things touched (moose, drink, Netz, mouse, child, Fenster, ox, am, -ung gender, cup, run); none equals the new answer.

## Remaining doubts

- "Only" worlds (0001, 0009, 0010, w1): a model that stores the closed list keeps it beside the new member. Each world is concrete (one stored sentence, given in its chain), but w1 is strictly inconsistent with the edit; it has the same shape as the README's count example (Eris's moons stored as a number), so kept.
- 0009/0010 w2 depends on the model treating coined jargon/slang as "English nouns/verbs"; the edit says so explicitly.
- Grammar ABox 0002/0003 are all-determinate (allowed per caller and README Decisions 3); 0001 keeps 2+2.
- RBox fictional relations in `grammar.insert.md` don't carry the inserted property as a tag (same convention as the other topics' insert relation files).
