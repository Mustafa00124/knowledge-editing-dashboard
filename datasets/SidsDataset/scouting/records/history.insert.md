# History inserts (fictional), 0001-0020

Built by `scratchpad/hins/b_*.py` (helpers in `common.py`; every Wikipedia quote is asserted against a fetched copy in `hins/wiki/`, every count comes from `ig.py`).
Validator: 0 errors (20 files). criteria.py: Rule 9 (RBox yes/no) ok, Rule 11 (shape, insert mix) ok, Rule 5 fails on 4 records (no web search for the made-up name; see Doubts).

| Id | Box / fictional | Edit | Derived (determinacy, derivation, logic) |
| --- | --- | --- | --- |
| 0001 | ABox entity | The Strathgrave exemplar, an original of the 1215 Magna Carta identified in 2025, is kept at Wells Cathedral. (`located_in`) | det transitivity dl (England); det composition dl (King John); BB count 4/5 fol+arith; BB count outside London 2/3 fol+arith |
| 0002 | ABox entity | The Varrowmede copy, found 2024 in an Austrian monastery library, is a surviving copy of the Gutenberg Bible. (`copy_of`) | det composition dl (Mainz); det composition dl (1450s); BB 49/50; BB yes/no >49 |
| 0003 | ABox entity | The Tarrowmere Hoard, found in Norfolk in 2023, contains more than 6 kg of gold. (`found_in`) | det chain dl (England); det composition dl (East Anglia); BB "Staffordshire largest?" yes/no; BB largest hoard Staffordshire/Tarrowmere |
| 0004 | ABox relation | In 1386 Portugal was ember-pledged to England. | 4 det: composition fol+temporal (Richard II), composition dl (Great Britain), inverse dl, asymmetry dl |
| 0005 | ABox relation | Richard the Lionheart was banner-bonded with Philip Augustus. | 4 det: symmetry, composition (France), composition fol+temporal (alive in 1215), composition (Bouvines) |
| 0006 | ABox relation | In the 15th century Bruges was toll-sworn to Lübeck. | 4 det compositions (Hanseatic League, Germany, Thomas Mann, Free Imperial City) |
| 0007 | ABox both | Margraviate of Kessendrath tithe-sworn to the Duchy of Velmarre. | 4 det: transitivity, inverse, composition, asymmetry (all stated in prompt) |
| 0008 | ABox both | Aldric Venhallow was hearth-tied to Corvin Haldane. | 4 det: symmetry, composition, composition fol+temporal, subproperty |
| 0009 | TBox entity | Every Pellingworth codex (two found 2024 in Chiapas) is a pre-Columbian Maya codex. | det inheritance (script; bark paper) on new members; BB count 4/6; BB yes/no >4 |
| 0010 | TBox entity | Every Harrowgarde head (two found 2024 in the Olmec heartland) is an Olmec colossal head. | det inheritance (basalt; Mexico); BB count 17/19; BB yes/no >17 |
| 0011 | TBox relation | Every Doge of Venice elected from 1172 swore the lamp-oath to the Great Council. | 4 det inheritance (Dandolo, Foscari in prompt fol+temporal, "doge of the Fourth Crusade", Manin) |
| 0012 | TBox relation | Every signer of the Declaration other than Hancock was quill-bonded to Hancock. | 4 det inheritance (Jefferson, Franklin, Adams via "president of Congress", Jefferson via "governor of Massachusetts") |
| 0013 | TBox both | Every Kesterling warden was cup-sworn to the Margrave of Thessenmark. | 4 det: inheritance x2, subproperty, transitivity (stated) |
| 0014 | TBox both | Every Wendmoor lancer was hearth-quartered in the fortress of Valdrecht. | 4 det: inheritance, chain (stated), transitivity via located_in, inheritance fol+temporal |
| 0015 | RBox relation | 'Was ash-sworn to' is symmetric. (Venice, Genoa, Milan) | direct yes; d0 yes; d1 no |
| 0016 | RBox relation | 'Owed reed-tithe to' is asymmetric. (Florence, Pisa, Siena, Lucca) | direct no (asks symmetric); d0 no; d1 yes |
| 0017 | RBox relation | 'Paid lantern-dues to' is transitive. (Brittany, France, Papal States; Aragon, Castile, Portugal) | direct yes; d0 yes; d1 no |
| 0018 | RBox both | Inverse of 'was rune-sworn to' is 'held the rune-oath of'. | direct yes; d0 no; d1 yes |
| 0019 | RBox both | 'Was the cup-warden of' is functional. | direct no; d0 no; d1 yes |
| 0020 | RBox both | 'Was blade-wed to' and 'was thorn-feuded with' are disjoint. | direct no; d0 yes; d1 no |

RBox balance: direct 3/3, derived[0] (and so zh/es) 3/3, derived[1] 3/3. RBox `edit.subject` is the snake_case id; each direct question quotes the relation wording once, first (checked with `sids_requests.edit_subject`; all 20 build requests).

## Made-up names (infini-gram Dolma counts)
HMS Wrenfield / Ezekiel Thornbury (dropped), Strathgrave exemplar 0 (bare "Strathgrave" 9), Varrowmede 0, Tarrowmere Hoard 0, ember-pledged 0, banner-bonded 0, toll-sworn 0, Kessendrath 0, Velmarre 1, tithe-sworn 0, Aldric Venhallow 0, Corvin Haldane 0, hearth-tied 0, Pellingworth 1, Harrowgarde 0, lamp-oath 0, quill-bonded 0, Kesterling warden 0, Margrave of Thessenmark 0, cup-sworn 0, Wendmoor lancer 0, Valdrecht 0, hearth-quartered 0, ash-sworn 0, reed-tithe 0, lantern-dues 0, rune-sworn 0, cup-warden 0, blade-wed 0, Edric Dastray 0, Bertil Harrad 0, House Quenford 0, House Strellan 0.
Web searches run (no real thing found): HMS Wrenfield, Ezekiel Thornbury, ember-pledged, banner-bonded, toll-sworn, strathgrave, Tarrowmere, Archsteward of the Vale, Kessendrath/Velmarre, Aldric Venhallow/Corvin Haldane, Thessenmark/Kesterling warden, Varrowmede/Valdrecht, ash-sworn/reed-tithe/lantern-dues, rune-sworn/cup-warden/blade-wed.

## Changes during the work
- Coordinator rule "could it exist unrecorded": the first entity drafts (a ship added to Nelson's line at Trafalgar, a 42nd Mayflower Compact signer, a 12th First Fleet ship, a sixth peerage rank, an eighth Golden Bull elector) falsified documented lists, so all five were replaced with new finds: a newly identified 1215 Magna Carta original, a newly found Gutenberg Bible copy, a 2023 hoard, two newly found Maya codices, two newly found Olmec heads.
- Superlative in 0003: the edit states the gold weight, not "largest", so the stored-superlative world does not contradict the edit itself.
- 0011 rule starts in 1172 so no doge swears to a Great Council that did not yet exist; 0012 excludes Hancock so he is not bonded to himself.

## Doubts
- Rule 5: four records have a corpus count but no web search for the made-up name (Pellingworth 0009, Harrowgarde 0010, lamp-oath 0011, quill-bonded 0012). The turn's web-search budget ran out; these searches still need to be run and added as `search` sources. Also not searched (but not required by the check, since the record has another search): hearth-tied, tithe-sworn, cup-sworn, hearth-quartered, Wendmoor, thorn-feuded, the RBox people and houses.
- Count worlds (w1 "stored as a number, not recomputed") follow the README's moon-of-Eris pattern; for 0001's "outside London" and the >N yes/no versions they are lopsided (Decisions 4).
- 0003: whether a single hoard with >6 kg gold "could exist unrecorded" is plausible but a big find; 0009/0010 say "two" finds in the edit so the list world gives a concrete number.
- 0011 uses Foscari's dates in the prompt (fol + temporal); 0012's governor query is dl (no date comparison).
- Relation and both inserts reuse no catalogued fictional relation; 24 new rows in `relations/history.insert.md` (fictional ones marked), 9 relation checks (the fictional-property checks are phrased as "Suppose ... (an invented custom)").
