# Biology RBox 0017-0018 (role chain, functionality)

Records: `datasets/SidsDataset/records/biology/{replace,delete}/biology-{replace,delete}-001[78].json`
Relations: `relations/biology.rbox2.md` (new `endemic_to`, `in_genus`), checks in `relations/biology.rbox2.checks.json`.
Validator: 4 files, 0 errors (with all biology extra relation files). criteria.py: Rule 9 ok (biology RBox new answers direct 3/3, derived 6/6, cross-lingual 6/6); no new relation-name findings.

| Id | Edit | Direct (orig -> new) | Derived 1 (= zh/es) | Derived 2 | Logic |
| --- | --- | --- | --- | --- | --- |
| replace-0017 | ¬(endemic_to ∘ located_in ⊑ endemic_to) | no -> yes | marine iguana / Galápagos / Ecuador, "does it follow endemic to Ecuador?" yes -> no | Tasmanian devil / Tasmania / Australia, "could it fail to be endemic to Australia?" no -> yes | dl |
| delete-0017 | removes the chain | no -> null | yes -> null | no -> null | dl |
| replace-0018 | ¬Func(in_genus) | "each species at most one genus?" yes -> no | lion in Panthera, "possible also in Acinonyx?" no -> yes | gray wolf in Canis, "follows not in Vulpes?" yes -> no | dl |
| delete-0018 | removes Func(in_genus) | yes -> null | no -> null | yes -> null | dl |

Locality: 0017 near = born_in chain via a zoo ("can the animal fail to have been born in that city?", no); far = "'is heavier than' transitive?" (yes, unused elsewhere). 0018 near = "Does each genus have at most one type species?" (yes); far = "'is a cousin of' symmetric?" (yes, unused elsewhere).

## Why the originals hold without exception
- **endemic_to ∘ located_in ⊑ endemic_to**: endemic = native to b and found nowhere outside b. If b lies inside c, the species is native to c and found nowhere outside c. Holds for every pair, purely by containment. Not functional (nested regions), so the chain into itself is consistent with the RELATIONS rule. R and S differ (endemic_to, located_in), so it is a chain, not transitivity.
- **Func(in_genus)**: under the ICZN and ICN a species name is a binomen (one genus + epithet), so a species is placed in exactly one genus at a time. Disagreements are about which genus, never two at once; subgenera and nothogenera are single placements too.

## Doubts
- "Is endemic to Australia" for the Tasmanian devil is logically right, though a model might hesitate because the species once lived on the mainland; the prompt facts make it a pure inference.
- Functionality of in_genus is nomenclatural; a model thinking of competing classifications (Felis concolor / Puma concolor) might say a species "can be in two genera". I avoided Felis for the lion (Linnaeus' Felis leo) and used Acinonyx.
- Near query for 0017 uses born_in (only other biology chain relation); phrased with a zoo and a city to avoid border-change issues.
- Chinese 猎豹属 (Acinonyx) contains 豹, as does 豹属 (Panthera); harmless, not an answer give-away.
