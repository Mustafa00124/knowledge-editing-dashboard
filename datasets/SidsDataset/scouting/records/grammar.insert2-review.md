# Grammar inserts (insert2): review

Validator: 0 errors (extra relations: `relations/grammar.insert2.md`, now only `attests_word`; `root_of` removed, as nothing uses it any more). criteria.py: no grammar insert under Rules 5, 7, 9, 10, 11 or 13. Rule 8 lists only `attests_word` (0003 and 0004), which is in the scratch file. Mix: ABox 2/2/1/2/1, TBox 2 subject / 2 relation|object / 2 subject_object, RBox 3/3. Ids match file names, and no record refers to an old id.

## Per record
| Id | Verdict |
| --- | --- |
| 0001, 0005-0008 (moved) | KEEP. Ids and tags are right. Fresh counts match (all made-up names 0). English_plurals quotes in 0005 and 0006 confirmed. |
| 0002 glendrink (subject) | KEEP. Fresh count 0, web search finds nothing (only Glen's Vodka, Glendronach). 4 quotes confirmed against API text. Worlds hold whether Scots counts as a language or a variety of English. |
| 0003 farjoskip (object) | KEEP. Fresh count 0, search finds nothing. 4 quotes confirmed. attests_word is many-valued. The direct question singles out the word by its meaning, and 'Gothic' appears once. |
| 0004 | REPLACED. 'aquathrove' began with 'aqua', the word in the question, so half the answer was given away. Now: "Hittite has a newly attested noun, 'kuwarzanalli' (a kind of festival bread), read on a newly unearthed clay tablet from Hattusa." The relation is attests_word (many-valued). 'Hittite' appears once in the direct prompt. kuwarzanalli: fresh count 0, web search finds nothing. Derived queries, all determinate: Anatolian (yes), cuneiform or Latin alphabet (cuneiform), oldest attested IE language (yes), same branch as English 'bread' (no). 3 Hittite_language quotes and 1 West_Germanic quote confirmed. Near: Hrozný (1915). Far: "The Magic Flute" (used 4 times dataset-wide before this). Made through `grammar_ins2/build_new.py` (old version kept as `build_new.v1.py`). The rerun left 0002 and 0003 byte-identical. |
| 0012 | FIXED, retagged `relation` to `object`. The axiom is ∃has_stem_type.{brightstemmed}: stem type is a real grammatical notion, and only the value is made up. One made-up part, so not relation+object. criteria.py allows a TBox `object` insert to be all determinate (INSERT_ALL_DETERMINATE_TBOX), so the writer's worry about needing indeterminate queries doesn't apply. Notes and evidence updated. Fresh counts: brightstemmed, Verknarbung, lowcapped all 0. |
| 0013, 0014 | FIXED. The tag subject_object was not honest: '-ath' and 'ka-' can't carry a near-zero count, and 'ka-'/'-ka-' is a real past/narrative-tense marker (Swahili, Tagalog). Renamed the affixes: '-ath' to '-eskuth' (grulmeskuth, skavreleskuth, meldagrulmeskuth) and 'ka-' to 'drovka-' (drovkaulveskarn, drovkabrannowisk). This covers the statement, axiom, all queries and zh/es. Fresh counts: eskuth 0, drovka 2, all derived forms 0. Web searches: no word by either spelling (only Eskuta, Drozdovka/Drova). New sources added to the evidence. Edited in the JSON directly, as the insert2 writer did. |
| 0009-0011, 0015-0020 | KEEP. Tags are honest (0011: made-up Velquorran-mark relation with the real ☆ symbol). |

Counts re-run fresh: 20 ABox counts plus 3 for 0012 and 12 for the new affixes and Hittite. None changed. Quotes checked: 15, none failed.

## Doubts / follow-ups for the parent
- RELATIONS.md (not edited, per the brief): line 725 `has_stem_type` still says "(fictional)", which no longer matches 0012's `object` tag. It should read "words of class a have stem type b". Line 722's example still uses 'ka-' and should become 'drovka-'.
- 0012: has_stem_type is functional. Modern German assigns '-ung' nouns no stem class (ō-stems are Old High German), so nothing real is overwritten. It's arguable, though.
- The object inserts (0003, 0004) have no background_beliefs queries. The writer brief asked for 2, but README and criteria allow grammar ABox to be all determinate, and no aggregate about a dead language's vocabulary has a concrete answer.
- 0003 and 0004 share `attests_word`, as biology's two object inserts share has_species.
