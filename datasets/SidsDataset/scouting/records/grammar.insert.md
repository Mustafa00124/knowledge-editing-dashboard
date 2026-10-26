# Grammar fictional inserts (grammar-insert-0001 to 0020)

Written to `datasets/SidsDataset/records/grammar/insert/`. New relations in
`relations/grammar.insert.md` (fictional ones marked "(fictional)") and their
property checks in `relations/grammar.insert.checks.json`. Built by
`grammar_ins/build.py` (records_abox.py, records_tbox.py, records_rbox.py).

Theme: nonce words ("wug" test). ABox entity: a nonce noun with a goose-style
plural, a nonce verb with a drink-style past, a nonce German noun with a
gender. ABox relation: made-up relations between real words (hearth-paired,
rhyme-elder, vane-word). TBox entity: made-up classes of English nouns/verbs
with real patterns ('-en' plural; an 'I'-only present form like 'am'). TBox
relation: real classes with made-up properties. Both: the invented language
Tovrish, nonce words in made-up relations. RBox: made-up relations given
symmetry, transitivity, inverse (real words), subproperty, role chain,
functionality (nonce words).

## Records

| id | box | fictional | relation | edit | derived (derivation/determinacy/logic) |
| --- | --- | --- | --- | --- | --- |
| 0001 | abox | entity | `singular_of` | The plural of the English noun 'brindoose' (a kind of marsh bird) is 'brindeese'. | composition/deter/fol, composition/deter/fol, composition/backg/fol, composition/backg/fol |
| 0002 | abox | entity | `base_form_of` | The past tense of the English verb 'glendrink' is 'glendrank'. | composition/deter/fol, composition/deter/dl, composition/deter/fol, composition/deter/fol |
| 0003 | abox | entity | `has_gender` | The German noun 'Knarbsel' (a kind of fishing net) is feminine. | inheritance/deter/dl, chain/deter/dl, inheritance/deter/dl, inheritance/deter/dl |
| 0004 | abox | relation | `hearth_paired_with` | The English word 'kettle' is hearth-paired with the English word 'mouse'. | symmetry/deter/dl, composition/deter/dl, composition/deter/fol, composition/deter/dl |
| 0005 | abox | relation | `rhyme_elder_of` | The English word 'child' is the rhyme-elder of the English word 'mild'. | transitivity/deter/dl, asymmetry/deter/dl, composition/deter/dl, composition/deter/dl |
| 0006 | abox | relation | `vane_word_of` | The English word 'window' is the vane-word of the German noun 'Tür'. | composition/deter/dl, composition/deter/dl, subproperty/deter/dl, chain/deter/dl |
| 0007 | abox | both | `stem_twin_of` | The word 'quindrevel' is the stem-sworn of the word 'drannick'. | symmetry/deter/dl, transitivity/deter/dl, chain/deter/dl, chain/deter/dl |
| 0008 | abox | both | `brood_form_of` | The word 'plosket' is the brood-form of the word 'trevandrel'. | inverse/deter/dl, subproperty/deter/dl, chain/deter/dl, asymmetry/deter/dl |
| 0009 | tbox | entity | `plural_formed_with` | Skarnovish nouns, a small group of English nouns newly coined in a regional craft jargon, form their plural by adding '-en' to the singular, as 'ox' becomes 'oxen'. | inheritance/deter/dl, inheritance/deter/dl, composition/backg/fol, composition/backg/fol |
| 0010 | tbox | entity | `has_inflection` | Frenstle verbs, a small group of newly coined English slang verbs, have, besides their plain form and their '-s' form, a third present-tense form used only with the subject 'I', as 'be' has 'am' besides 'are' and 'is'. | inheritance/deter/fol, inheritance/deter/fol, composition/backg/fol, composition/backg/fol |
| 0011 | tbox | relation | `carries_velquorran_mark` | In Velquorran notation, an invented system for marking English words, every English auxiliary verb carries the hollow-star mark. | inheritance/deter/dl, inheritance/deter/dl, inheritance/deter/dl, inheritance/deter/dl |
| 0012 | tbox | relation | `has_stem_type` | Every German noun ending in '-ung' is brightstemmed. | inheritance/deter/dl, inheritance/deter/dl, inheritance/deter/dl, inheritance/deter/dl |
| 0013 | tbox | both | `plural_formed_with` | In the invented language Tovrish, every vessel noun takes the plural suffix '-ath'. | inheritance/deter/dl, inheritance/deter/dl, inheritance/deter/dl, inheritance/deter/fol |
| 0014 | tbox | both | `past_formed_with` | In the invented language Tovrish, every verb of motion forms its past tense with the prefix 'ka-'. | inheritance/deter/dl, inheritance/deter/dl, inheritance/deter/dl, inheritance/deter/fol |
| 0015 | rbox | relation | `quill_paired_with` | 'Is quill-paired with' is symmetric. | instantiation/rbox/dl, instantiation/rbox/dl |
| 0016 | rbox | relation | `ember_ranked_above` | 'Is ember-ranked above' is transitive. | instantiation/rbox/dl, instantiation/rbox/dl |
| 0017 | rbox | relation | `hasp_word_of` | The inverse of 'is the hasp-word of' is 'is hasp-led by'. | instantiation/rbox/dl, instantiation/rbox/dl |
| 0018 | rbox | both | `flint_mate_of` | 'Is a flint-mate of' is a subproperty of 'is a fell-mate of'. | instantiation/rbox/dl, instantiation/rbox/dl |
| 0019 | rbox | both | `rune_stem_of` | If a word is the rune-stem of a second word, and the second word is the cinder-stem of a third, then the first word is the far-stem of the third. | instantiation/rbox/dl, instantiation/rbox/dl |
| 0020 | rbox | both | `has_gell_vowel` | 'Has the gell-vowel' is functional. | instantiation/rbox/dl, instantiation/rbox/dl |

## Made-up names (Dolma counts, infini-gram)

brindoose 0, brindeese 0, glendrink 0, glendrank 0, Knarbsel 0, Gartenknarbsel 0, hearth-paired 0, rhyme-elder 0, vane-word 0, drannick 0, plosket 0, brood-form 3, quindrevel 0, stem-sworn 0, trevandrel 0, Skarnovish 0, fendrastock 0, fendrastocken 0, harbrisk 0, harbrisken 0, Frenstle 0, Skelvane 0, plorrow 0, plorrim 0, hollow-star mark 0, brightstemmed 0, Verknarbung 0, Tovrish 0, grulm 3, grulmath 0, skavrel 0, trimbask 0, meldagrulm 0, kaulvesk 0, vossilk 0, quill-paired 0, ember-ranked 0, hasp-word 0, hasp-led 0, flint-mate 0, fell-mate 0, rune-stem 0, far-stem 4, morvane 2, gell-vowel 0, skorrel 5, drimbask 0, Velquorran 0, ulveskarn 0, kaulveskarn 0, brannowisk 0, tarnelvisk 0, voskindrel 0, cinder-stem 1, pelskavor 0, drovinthel 0

## Labels

- Indeterminate (background_beliefs, worlds w1 "closed list stored as a fact"
  / w2 "recomputed from the nouns/verbs known"): 0001 (foot/goose/tooth the
  only oo->ee plurals; goose the only -oose/-eese noun), 0009 (oxen, children,
  brethren the only -en plurals; oxen the only plain -en plural), 0010 ('am'
  the only I-only form; 'be' the only verb with three present forms).
- Every other ABox/TBox derived query is determinate (grammar ABox may be all
  determinate; relation and both inserts may be).
- RBox yes/no: direct 3/3, derived 6/6, cross-lingual 6/6.

## Doubts

- 0002 and 0003 (ABox entity) are all determinate, not 2+2: no firm
  uniqueness or count about the real '-ink' verbs or German nouns exists, and
  the caller allowed grammar ABox to be all determinate. 0001 keeps 2+2.
- The "only" worlds (w1) are the brief's aggregate case: a model that stores
  the closed list keeps it beside the new member, which is arguably
  inconsistent; it is the same shape as "France's neighbours stored as a
  count" in the README.
- 0009/0010 indeterminate queries depend on the model treating the made-up
  class as part of English; the edit says "a class of English nouns/verbs".
- R1: 0001 Q3 excludes compounds (forefoot) and Q4 says "standard" plural
  (mongeese, meese are jocular); 0009 excludes archaic/dialect -en plurals
  (kine, hosen, aurochsen) per Wikipedia; 0010 Q4 relies on 'be' being the only
  verb with three present forms (Wikipedia states its irregular present, not
  the uniqueness in so many words).
- Names close to real words: 'Verknarbung' (Vernarbung, scarring), 'grulm'
  (a parked domain). Renamed for counts over 5: quindle (12) to quindrevel,
  trumbrel (11) to trevandrel, Skovish (329) to Skarnovish, fendrock (31) to
  fendrastock, stem-twin (39) to stem-sworn. Also renamed
  'brisk-mate' (Brisk Mate iced tea) to 'flint-mate', 'hinge-word' (informal
  discourse use) to 'hasp-word', 'mirror word', 'stem twin' and 'brood form'
  (real phrases, counts 399/280/72) to 'vane-word', 'stem-twin', 'brood-form'.
- Fictional prompt-stated bridges get no evidence entries (the validator only
  allows the inserted fact to be claimed fictional).
- criteria.py Rule 8 lists the new relations until the relations files are
  merged into RELATIONS.md.
- README "Could it exist unrecorded?": 0009 and 0010 were reworded from "a
  class of English nouns/verbs" (a documented word class would falsify
  grammar) to "a small group of newly coined English (jargon/slang) nouns/
  verbs"; 0001-0003 are nonce words (coined or dialect forms) and say so in
  their evidence.

## Validation

`validate.py` with the insert relations files: 20 files, 0 errors.
`criteria.py`: Rule 5 (evidence), Rule 9 (insert RBox yes/no 3/3, 6/6, 6/6),
Rule 11 (2+2 or 0 indeterminate; fictional mix 3/3/2, 2/2/2, 3/3) and Rule 13
(subject in the direct prompt) clean for grammar inserts. Rule 8 lists the new
relations until the relations files are merged. RBox edit.subject is the
snake_case relation id; each direct question quotes the relation wording once.
