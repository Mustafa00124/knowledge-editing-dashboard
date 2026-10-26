# literature_arts: ABox 0013-0016 (relation-property coverage)

Validator: 0 errors on 0001-0016 (32 files) with the scratch relation files. Rule 5: no literature offenders; Rule 11: literature ABox 8/8. (0017/0018 on disk are not mine; 0018 fails on an uncatalogued `has_key_signature`.)
Build script: `scratchpad/la2/build.py`; counts in `la2/q*.txt` runs (all cited counts were received from ig.py); Wikipedia text in `la2/wiki/`.

| Id | Edit (replace) | Relation, derivability | Derived queries (replace) |
| --- | --- | --- | --- |
| 0013 | Uffizi Gallery: Florence -> Naples | located_in, very_unlikely | region (Campania) **transitivity** det dl; "in southern Italy?" **transitivity** det dl; Birth of Venus city bb dl; Birth of Venus & David same city bb fol |
| 0014 | The Lord of the Rings: a novel -> an epic poem | instance_of, very_unlikely | "story told in verse?" **inheritance** det dl (every epic poem is in verse); "a narrative poem?" **chain** (instance_of o subclass_of) det dl; Two Towers in verse? bb dl; Return of the King a novel? bb dl |
| 0015 | Astyanax's paternal grandfather: Priam -> Nestor | has_paternal_grandfather, likely | father of his father (binding, premise_route) det dl; grandchild of Nestor? **subproperty** det dl; Hector his father? db dl; Hector's father? db dl |
| 0016 | Girl with a Pearl Earring: Netherlands -> Brazil | located_in, likely | country of its museum (binding, premise_route) det dl; continent **transitivity** det dl; Mauritshuis holds it? db dl; Mauritshuis & Rijksmuseum same country? db fol |

Coverage of the 8 determinate replace slots: transitivity 3, chain 1, inheritance 1, subproperty 1, binding/premise route 2.

Worlds: 0013/0014 by-name vs via-container storage (Birth of Venus in Florence vs in the Uffizi; volumes as novels vs as parts of LOTR; in w1 the container link gives way). 0015/0016: one premise gives way per world (Hector's father / Astyanax's father; painting's museum / Mauritshuis's city).

Deletes: worlds re-derived (null through the removed fact). Rephrased determinate slots: 0013 region asked "of the city where the Uffizi stands" + "in Dante's birthplace?" (a direct region/central-Italy query has address-style co-occurrence routes); 0014 "same form as Emma / Moby-Dick" (the novel class gives no firm property; fantasy already gives fiction); 0015 grandchild of Priam; 0016 continent Europe.

Dropped/rejected: Telemachus (Sisyphus variant makes Odysseus's father disputed); Agamemnon as new grandfather (plot clash); Prado (country stored by name breaks the delete); Whistler's Mother (weak museum premise, Louvre confusion); Japan for 0016 (Tokyo loans).

Doubts:
- 0014 w1 needs The Two Towers / Return of the King to stop being volumes of LOTR; lopsided and identity-heavy (TT's title page calls it the second part). Verifier may judge the premise too firm.
- 0013 delete: the Uffizi Wikipedia lead names Tuscany next to Florence, so the region query relies on asking through the city (as delete-0001 did).
- 0015 worlds pull in many side facts (Hector's siblings; the Astyanax naming story), as in people-0003.
- 0016 mirrors 0004's structure (painting -> museum -> country); different relation and property, but low variety.
- 0014 bridges "every epic poem is written in verse / is a narrative poem" are class rules used as bridges (allowed for ABox inheritance), not premises.
- Relations appended to scratch `relations/literature_arts.md`: instance_of, located_in, has_paternal_grandfather (tags identical to their other topics). No new checks needed (all (relation, tag) checks already exist).
