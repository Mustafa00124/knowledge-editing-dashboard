# People: RBox 0017-0018 (role chain, functionality)

Validator: 4 files, 0 errors (with people.md + people.rbox2.md relations and both checks files). criteria.py Rule 9: ok (people RBox 6/6 edits).

| Id | Edit | Direct (orig -> new) | Instances (orig -> new) |
| --- | --- | --- | --- |
| people-replace-0017 | born_in ∘ located_in ⊑ born_in  ->  born_in ∘ located_in ⊑ died_in | born in city in country => born in country? yes -> no | Obama/Honolulu/Hawaii born in Hawaii? yes -> no; Einstein/Ulm/Germany died in Germany? no -> yes |
| people-delete-0017 | removes born_in ∘ located_in ⊑ born_in | yes -> null | Obama born in Hawaii? yes -> null; Einstein born in Germany? (rephrased around original) yes -> null |
| people-replace-0018 | Func(has_birth_mother) -> ¬Func | more than one birth mother? no -> yes | Lincoln: can Sarah Bush Lincoln also be his birth mother? no -> yes; Washington: does it follow Martha is not his birth mother? yes -> no |
| people-delete-0018 | removes Func(has_birth_mother) | no -> null | both -> null |

Near/far: 0017 buried_in chain (yes) / grandparent_of asymmetric (yes); 0018 has_paternal_grandfather functional (no) / shared_nobel_prize_with symmetric (yes).
Replace new answers (people RBox totals incl. 0009-0012): direct 3/3, derived 6/6, cross-lingual 6/6.

## Why the originals hold
- 0017: born_in ∘ located_in ⊑ born_in is existing tag `chain:located_in->born_in`. Holds for the pairs used: Honolulu in Hawaii at Obama's birth (1961, statehood 1959); Ulm in Germany (German Empire) at Einstein's birth (1879). died_in already exists (history section, `chain:located_in->died_in`). Einstein died in Princeton, so "died in Germany" is clearly no before the edit.
- 0018: new relation `has_birth_mother` (functional, in people.rbox2.md + check). Exactly one woman gives birth to a person; surrogacy does not break it (the surrogate is the birth mother). "Birth mother" chosen over mother/biological mother (adoption, step-parents, mitochondrial donation). Sarah Bush Lincoln = stepmother, Martha Washington = wife.

## Doubts
- 0017's general chain can fail across border changes (born in Königsberg, now Russia); only safe pairs are used, but the direct question is general.
- 0018 Lincoln instance uses a stepmother: a model may conflate "mother" with "birth mother" (intentional pressure, but noisier). The "Can ... also be" phrasing asks possibility, not entailment.
- hops = 1 + 2 bridge facts = 3 (two bridge strings); 0009 used one combined string (hops 2). The distinctness fact in 0018 counts as a bridge.
