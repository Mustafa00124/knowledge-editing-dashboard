# History RBox 0017-0018 (role chain, functionality)

| Id | Edit (axiom) | Direct (orig->new) | Instances (orig->new) | Logic |
| --- | --- | --- | --- | --- |
| history-replace-0017 | died_in ∘ located_in ⊑ buried_in (was ⊑ died_in) | "died in c?" yes->no | Caesar died in Italy? yes->no (also zh/es); Alexander buried in Mesopotamia? no->yes | dl, dl |
| history-delete-0017 | removes died_in ∘ located_in ⊑ died_in | yes->null | Caesar died in Italy? yes->null; Alexander died in Mesopotamia? yes->null (rephrased around original target) | dl, dl |
| history-replace-0018 | ¬Func(died_in_year) | "Can a person have died in more than one year?" no->yes | Charlemagne d. 814, also 815? no->yes (also zh/es); William I d. 1087, so not 1090? yes->no | dl, dl |
| history-delete-0018 | removes Func(died_in_year) | "Is died in year functional?" yes->null | Charlemagne not 815? yes->null (zh/es rephrased too); William not 1090? yes->null | dl, dl |

Locality: 0017 near = exiled_to chain (yes), far = 'is a cousin of' symmetric (yes); 0018 near = ended_in_year functional (yes), far = 'is an ancestor of' transitive (yes).

## Why each original holds without exception
- **0017**: died_in already carries `chain:located_in->died_in` in RELATIONS.md. Dying at a place inside a larger place is dying in that larger place. Instances are settled: Caesar killed in Rome (44 BC), Rome in Italy (the peninsula, then and now); Alexander died in Babylon (323 BC), Babylon in Mesopotamia. Replacement target buried_in is already listed (people). Alexander was really buried in Egypt, so "buried in Mesopotamia" is also false in the real world.
- **0018**: a person dies once, so in one year. Uncertain death dates are epistemic, not exceptions. Charlemagne 28 Jan 814, William I 9 Sep 1087, both undisputed and absent from other history records.

## Relations
- New: `died_in_year` (`functional`) in relations/history.rbox2.md, with a check in history.rbox2.checks.json. Also added a check for died_in's existing chain tag (relation_checks.json had none).

## Balance and validation
- Replace new answers 0017: 1 yes / 4 no; 0018: 4 yes / 1 no. criteria.py Rule 9 [ok]; per query type history is 3/3 direct, 5/5 derived, 5/5 cross-lingual.
- validate.py with both extra relation files: 4 files, 0 errors.

## Doubts
- 0018 direct and first instance use "Can ... also have died in ...?" rather than "Does it follow", per the brief's "whether two values can both hold"; answer flips to yes only under a permissive reading of non-functionality (possible, not entailed).
- 0017 replace changes the chain's target rather than removing it; "died in c" goes to no because nothing licenses it any more (died_in itself is untouched).
- Charlemagne in Chinese (查理曼) is the standard rendering; no answer leakage.
