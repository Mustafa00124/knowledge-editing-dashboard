# Finance ABox 0013-0016: relation-property coverage

Records: `datasets/SidsDataset/records/finance/{replace,delete}/finance-{replace,delete}-001{3,4,5,6}.json` (8 files).
Built by `{SCRATCH}/fin3/build.py` + `{SCRATCH}/fin3/records_def.py`. Counts: `{SCRATCH}/fin3/q{1,2,3}.out`; samples read: `{SCRATCH}/fin3/docs.out`; Wikipedia text: `{SCRATCH}/fin3/wiki/`.
Validator (with relation files) on finance 0001-0016: 32 files, 0 errors. (finance 0017/0018 RBox records, written by someone else after I started, fail on relations missing from my relations file: `incorporated_in`, `has_iso_4217_code`. Not mine.)
criteria.py: Rule 5 ok; Rule 11 finance row 8/8 ABox, 4/4 stored, 4/4 derived; Rule 12 still fails globally on ABox subproperty (9 of 10). Other topics are still being written.

## Records

| Id | Edit (orig -> new) | Relation | Deriv. | Determinate (derivation, logic) | Indeterminate |
| --- | --- | --- | --- | --- | --- |
| R0013 | Rolls-Royce Motor Cars wholly owned subsidiary of BMW -> Audi | wholly_owned_subsidiary_of | very_unlikely | "subsidiary of Audi?" **subproperty**, dl; "part of the Volkswagen Group?" **transitivity** via subsidiary_of (bridge Audi ⊂ VW AG), dl | V12 engine maker (BMW / Audi), bg; engine maker HQ in Munich? (yes/no), bg, dl |
| D0013 | delete BMW ownership | | | "subsidiary of BMW?" subproperty -> null; parent's HQ city (Munich -> null) composition | engine maker BMW / null; Munich? yes / null |
| R0014 | Siemens constituent of the DAX -> the CAC 40 | index_constituent_of (new) | unlikely | "listed on Euronext Paris?" **inheritance** (CAC 40 class rule), dl; "in the SBF 120?" **chain** `chain:subindex_of->index_constituent_of`, dl | primary listing (Frankfurt / Euronext Paris), bg, dl; primary listing in ECB's city? (yes/no), bg, fol |
| D0014 | delete DAX membership | | | binding (DAX by description) -> null, dl; same index as Allianz? -> null, fol | primary listing Frankfurt / null; same city as ECB yes / null |
| R0015 | Nestlé's headquarters located in the canton of Vaud -> Haute-Savoie | located_in | likely | premise route: "country of the town where Nestlé has its HQ" Switzerland -> France, **transitivity**, dl; "HQ in the EU?" **transitivity** (2 bridges), dl | "HQ in Vevey?" (w1 no / w2 yes), "Vevey in Vaud?" (yes/no): derived_beliefs |
| D0015 | delete | | | premise route: canton of Nestlé's town -> null, composition; same canton as Lausanne? -> null, fol | premises: null/yes, yes/null |
| R0016 | LinkedIn's parent company HQ Redmond -> Austin | parent_headquartered_in | likely | premise route: owner's HQ state Washington -> Texas, composition, dl; "parent in Redmond?" functional, dl | "Owned by Microsoft?", "Microsoft's HQ city?": derived_beliefs |
| D0016 | delete | | | premise route -> null; functional -> null | premises null/yes, Redmond/null |

Premises (derived edits): 0015 Nestlé HQ in Vevey; Vevey in Vaud; definitional (a building is in the region containing its town). 0016 LinkedIn owned by Microsoft; Microsoft HQ Redmond; definitional (parent = owner).

## Property coverage (replace, determinate slots)
- transitivity: R0013 (via subsidiary_of), R0015 x2
- subproperty: R0013
- chain (declared): R0014
- inheritance (ABox): R0014
- functional: R0016 (allowed: the four above are covered)
- Only R0016's premise-route slot is plain composition.

## Relations added (scratch files only)
- `index_constituent_of` (`cardinality:many`, `chain:subindex_of->index_constituent_of`) and `subindex_of` (`transitive`, `asymmetric`), with checks.
- First named `constituent_of`; renamed at the coordinator's request because grammar already uses that name.
- Added a check for the existing tag `wholly_owned_subsidiary_of` `subproperty:subsidiary_of`, which had none. No tags changed.

## Candidates dropped / worlds
- Nestlé as subject: Nestlé S.A. has a second registered seat in Cham (Zug), so the subject is "Nestlé's headquarters" (Vevey only).
- Škoda/Volkswagen: dropped because of a holding-company layer (Porsche SE controls VW AG).
- GEICO/Berkshire: dropped because "Oracle of Omaha" ties re-derive Omaha in a delete world.
- LinkedIn's own HQ (moved between Mountain View and Sunnyvale): not used.
- Moody's/Big Four class move: no concrete background answers.
- ECB-in-Hesse: moving Frankfurt across a border breaks too many firm facts.
- No world dropped inside the final records.

## Doubts
- R0014 w2 (Siemens's listing known only through its index) is lopsided; the Frankfurt listing is well known. Kept per Decision 4.
- R0015 w2 moves Vevey into France, like 0004's Zurich world (side facts listed). A strict verifier may object.
- R0013 engine worlds rest on "BMW builds Rolls-Royce's V12" (Wikipedia: N74 used in Rolls-Royce models; Phantom "V12 engine sourced from BMW"). The audit checks it.
- R0016 repeats 0003's shape (functional slot); it does no property work beyond that.
- SBF 120 is a less familiar index; the chain query depends on its check.
