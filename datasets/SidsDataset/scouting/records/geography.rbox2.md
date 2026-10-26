# Geography RBox 0017-0018 (rbox2)

| Id | Edit | Direct (orig -> new) | Instances (orig -> new) | Logic |
| --- | --- | --- | --- | --- |
| replace-0017 | removes chain in_drainage_basin_of ∘ drains_into ⊑ in_drainage_basin_of | yes -> no | Vienna/Danube/Black Sea, Lyon/Rhône/Mediterranean: yes -> no | dl, dl |
| delete-0017 | deletes that chain | yes -> null | yes -> null | dl, dl |
| replace-0018 | ¬Func(enclave_within) | "Can a territory be an enclave within two states at once?" no -> yes | Lesotho (+Botswana?), San Marino (+France?): no -> yes | dl, dl |
| delete-0018 | deletes Func(enclave_within) | no -> null | no -> null | dl, dl |

Locality: 0017 near = capital_of chain (yes), far = 'is a descendant of' transitive (yes, new prompt);
0018 near = one city capital of two countries (no), far = 'is a cousin of' symmetric (yes, new prompt).

## Why the originals hold
- **Chain**: a river's drainage basin is all land whose water reaches it; that water then goes where the
  river drains, so the river's basin lies within the receiving water's basin. Holds for rivers into lakes or
  rivers, and for bifurcating rivers (basin then in both). Two different relations (R = in_drainage_basin_of,
  S = drains_into). Does not follow from any other tag, so the delete is clean. Rejected: capital_of ∘
  located_in ⊑ located_in (already tagged) because it follows from 0012's subproperty + 0011's transitivity.
- **Functional**: by definition. Wikipedia "Enclave and exclave": "An enclave is a territory that is
  entirely surrounded by the territory of only one other state or entity"; a territory surrounded by
  several states (Nakhchivan) is not an enclave. Nested cases (Baarle, Nahwa) do not break it.
  Follows from no other tag of enclave_within.

## Relations
- New `in_drainage_basin_of` (`chain:drains_into->in_drainage_basin_of`, `cardinality:many`) in
  relations/geography.rbox2.md; checks for it and for enclave_within `functional` (already tagged in the
  shared file) in relations/geography.rbox2.checks.json.

## Validation
validate.py on the 4 files with all extra relation files: 0 errors. Rule 9 geography: direct 3/3,
derived 6/6, cross-lingual 6/6 (0017 new = no, 0018 new = yes).

## Doubts
- 0018 instances use a permissive "Can X at the same time be...?" rather than "Does it follow...?" (the
  brief allows "whether two values can both hold"); the new answer "yes" reads as "possible", not "true".
- zh 飞地 is often used loosely for exclaves; the prompt glosses it as completely surrounded by South Africa.
- "Drainage basin of the Black Sea" is standard but less common than river basins; a model may answer the
  chain questions from stored facts (Vienna, Danube) - irrelevant for "does it follow".
