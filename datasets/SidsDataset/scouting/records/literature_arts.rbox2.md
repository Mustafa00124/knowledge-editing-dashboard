# literature_arts: RBox 0017-0018 (replace + delete)

Validator (with literature_arts.md + literature_arts.rbox2.md and both checks files): 4 files, 0 errors.
Rule 9 (criteria.py): literature_arts RBox replace now direct 3 yes / 3 no, derived 6/6, cross-lingual 6/6
(0017 all yes, 0018 all no). Rule 12: 0017 counts as chain (axiom has ∘), 0018 as functional (¬Func).

| Id | Edit | Direct (orig -> new) | Instances (orig -> new) |
| --- | --- | --- | --- |
| replace-0017 | housed_in ∘ located_in ⊑ located_in  ->  ⊑ painted_in | no -> yes | Girl with a Pearl Earring / Mauritshuis / The Hague; Guernica / Reina Sofía / Madrid: "painted in that city?" no -> yes |
| delete-0017 | removes housed_in ∘ located_in ⊑ located_in | yes -> null | same facts, "is located in that city?" yes -> null |
| replace-0018 | Func(has_key_signature) -> ¬Func | yes -> no | "D major has two sharps. Does it follow it does not have three sharps?"; E-flat major three flats vs two flats: yes -> no |
| delete-0018 | removes Func(has_key_signature) | yes -> null | same instances, yes -> null |

Near/far: 0017 near "set in a city in a country -> written in that country?" (no), far "'is heavier than' transitive?" (yes);
0018 near "'is the dominant of' functional?" (yes), far "'is a parent of' symmetric?" (no). All logic dl, hops 2.

## Why the originals hold without exception
- 0017: 'housed in' means kept in the museum building, so the artwork is wherever the museum is; the chain is already
  declared on housed_in in RELATIONS.md (chain:located_in->located_in, with a relation_checks entry). Instances are
  false under the edit in reality: Vermeer painted Girl with a Pearl Earring in Delft; Picasso painted Guernica in Paris.
  Starry Night and Mona Lisa avoided (edited in 0004 / 0002).
- 0018: in tonal theory each major/minor key has exactly one key signature; enharmonic keys (C-sharp vs D-flat major)
  are different keys. Rejected: written_by (co-authors), housed_in (co-owned works, e.g. Rembrandt's Marten and Oopjen
  portraits shared by the Louvre and Rijksmuseum), written_in_language (macaronic works), has_line_count (functional only
  by arithmetic).

## New relation (scratch only)
`has_key_signature` (functional) in relations/literature_arts.rbox2.md, check in literature_arts.rbox2.checks.json.
criteria.py (which ignores the extra files) lists it as missing from RELATIONS.md until merged.

## Doubts
- Baroque "Dorian" notation writes some minor-key pieces with one flat fewer; that is how a piece is notated, not a
  second signature of the key. Instances use major keys to stay clear of it.
- A model may answer the 0018 instances "yes" after the edit from plain world knowledge (two sharps is not three);
  inherent to any functional property.
- 0017 direct asks the new chain (as 0011 does for subproperty), so the original direct answer is "no"; the delete asks the
  original chain.
