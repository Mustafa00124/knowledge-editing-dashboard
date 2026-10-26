# Grammar inserts: re-tag and rebalance (insert2)

Validator: 0 errors (with grammar.insert2.md / .checks.json). criteria.py: no grammar insert under Rules 5, 7, 8, 9, 10, 11 or 13; the TBox and ABox mixes match.

## Old to new
| New | Old | fictional | Edit |
| --- | --- | --- | --- |
| 0001 | 0003 | subject | 'Knarbsel' (German) is feminine |
| 0002 | 0002 reworked | subject | 'glendrink' is a word of Scots (it used to be a past tense, glendrink/glendrank) |
| 0003 | new | object | Gothic has a newly attested noun 'farjoskip' (ferry-boat) |
| 0004 | new | object | Latin 'aqua' is a root of the new coinage 'aquathrove' |
| 0005 | 0001 | subject_object | plural of 'brindoose' is 'brindeese' (keeps its 2 background_beliefs queries) |
| 0006 | 0005 | relation | child rhyme-elder of mild |
| 0007 | 0006 | relation | window vane-word of Tür |
| 0008 | 0007 | all | quindrevel stem-sworn of drannick |
| 0009, 0010 | same | subject | Skarnovish nouns, Frenstle verbs |
| 0011 | same | relation | Velquorran hollow-star mark (the mark itself is a real symbol, ☆) |
| 0012 | same | relation | '-ung' nouns are brightstemmed (one made-up predicate) |
| 0013, 0014 | same | subject_object | Tovrish class + Tovrish affix '-ath' / 'ka-', real relation |
| 0015-0020 | same | unchanged | |

Dropped: old 0004 (hearth_paired_with, relation): its symmetry use is also covered by stem_twin_of (0008) and RBox 0015. Old 0008 (brood_form_of, all): the other `all` record, stem_twin, covers more properties (symmetric, transitive, chains), and vane_word (0007) already covers subproperty.

## New names (fresh Dolma counts, web searches)
glendrink 0, farjoskip 0, aquathrove 0. Searches find no real word with any of these names, only loose matches. New relations in the scratch file: `root_of` (transitive, asymmetric, inverse:derived_from, many) and `attests_word` (many).

## Verification
Counts were re-run with --fresh. All 9 Wikipedia quotes in the new records were checked against the API plain text. One quote had the wrong quote marks around "Auld Lang Syne" and is fixed. Both Wiktionary quotes (aqueduct, aqua) were checked against the parsed HTML. All derived queries in 0002-0004 are determinate (grammar ABox may have none indeterminate). I looked for worlds where they fail:
- Scots: the answers hold whether Scots counts as a language or as a variety of English.
- Gothic: its extinction and its branch are firm.
- aqua: the transitivity premise is given in the prompt.

## Doubts
- 0012: has_stem_type plus the value brightstemmed could be read as relation plus object. I tagged it relation as a single made-up predicate. If it were tagged object, it would need 2 indeterminate queries, and a made-up property can't support them.
- 0013 and 0014: '-ath' and 'ka-' are made up only as morphemes of the made-up language. As letter strings they are common, so the corpus count rests on 'Tovrish'.
- 0004: the answer starts with the subject 'aqua'. That can't be avoided in a root_of edit.
- 0003: real newly found Gothic texts exist (Bologna 2009), so the direct question singles out the new word by its meaning.
- The object inserts have no background_beliefs queries, because no aggregate about Gothic or 'aqua' has a concrete answer.
