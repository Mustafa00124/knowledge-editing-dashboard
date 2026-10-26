# people: records written (sids-determinacy-2)

24 files in `datasets/SidsDataset/records/people/{replace,delete}/`. Validator: 24 files, 0 errors (with the extra relation files below). criteria.py B7 row for people: 4/4 per box, 2 stored + 2 derived ABox, 32 determinate / 24 background / 8 derived-beliefs (replace + delete). B6 ok.

Builder scripts (re-runnable): `scratchpad/people/{common,abox_stored,abox_derived,tbox,rbox}.py`. Every count comes from the ig.py results in `scratchpad/people/r*.jsonl` (the builder fails on a count that was not measured), and every Wikipedia quote is asserted against the fetched article text in `scratchpad/people/wiki/`.

Extra relations: `scratchpad/relations/people.md` (`buried_in`, tag `chain:located_in->buried_in`) and `people.checks.json` (its chain check).

## Records

| Id | Edit (replace; delete removes the original) | Derived labels (replace) | Logic |
| --- | --- | --- | --- |
| 0001 | Marie Curie's husband: Pierre Curie -> Paul Langevin | functional det, symmetry det, Irène's father bg, 1903 co-laureate bg (4 worlds) | dl x4 |
| 0002 | Shakespeare born in Stratford-upon-Avon -> Gloucester | county (chain) det, river (composition) det, place of death bg, burial bg (4 worlds) | dl x4 |
| 0003 | Caroline Kennedy's paternal grandfather: Joseph P. Kennedy Sr. -> James Michael Curley (likely) | father of her father det (premise route), grandchild of Curley det (subproperty), JFK her father? derived, JFK's father derived | dl x4 |
| 0004 | Van Gogh buried in France -> Belgium (likely) | country of his grave's town det (premise route), capital of that country det (composition), buried in Auvers? derived, Auvers's country derived | dl x4 |
| 0005 | Every pope is the Bishop of Rome -> Archbishop of Milan | 2 fictional new popes det (inheritance), Gregory I bg, Leo I bg | dl x4 |
| 0006 | Since 1904, an Olympic event winner gets gold -> silver | 2 fictional winners det, Bolt 2008 100 m bg, Owens 1936 long jump bg | dl x4 |
| 0007 | Life peerage entitles a seat in the Lords -> Commons | 2 fictional new peers det, Thatcher bg, Olivier bg | dl x4 |
| 0008 | Since 1949, the Masters winner gets a green -> red jacket | 2 fictional winners det, Tiger Woods 1997 bg, Nicklaus 1963 bg | dl x4 |
| 0009 | 'ancestor of' transitive -> not transitive | 2 instantiation (new: no, no) | dl |
| 0010 | 'sibling of' symmetric -> asymmetric | 2 instantiation (new: no, yes) | dl |
| 0011 | 'mother of' ⊑ 'parent of' -> ⊑ 'grandparent of' | 2 instantiation (new: yes, no) | dl |
| 0012 | inverse of 'parent of': 'child of' -> 'grandchild of' | 2 instantiation (new: yes, yes) | dl |

Delete records mirror each one: 2 determinate (does not know) + 2 indeterminate with a `null` world, worlds re-derived (derived edits: each world forgets one premise). RBox replace yes/no (new answers): direct 2/2, derived 4/4, cross-lingual 2/2.

## Changes from the scouting and why

- 0001: kept (Langevin). Notes record the review's points: description worlds improbable but valid; Irène's surname and Langevin's family tie as side notes.
- 0002: kept, but the "Shakespeare's Birthplace" museum query is gone (R2 in the brief); the place of death replaces it. The determinate queries are chain (county) and composition (river), because `born_in` is not functional. Delete: no stored "born in Warwickshire" exists (0 co-occurrences), so the county stays determinate.
- 0003: Elizabeth I / Thomas Boleyn dropped (review: medium). Replaced by Caroline Kennedy / Joseph P. Kennedy Sr., searched from both ends: about 5% of either premise, which gives likely. Mary I / Ferdinand II was a close backup (also rare), rejected because "Catherine of Aragon" names her father's kingdom (R2 hint in the premise question).
- 0004: Federer/Nadal dropped (review). Replaced by Van Gogh's grave (Space Needle shape: grave town + town's country). "Buried in France" has 0 exact hits. Belgium was chosen so the world where Auvers-sur-Oise moves stays consistent with the Oise, which rises in Belgium.
- TBox (new; the scouting had none): the Nobel Peace Prize/Oslo rule was dropped because the history writer uses it (R3). PhD -> Doctor was dropped as R2 ("Doctor of Philosophy" contains the answer). A British-monarch/Majesty draft was replaced by the Masters jacket after the membership-gives-way clarification: Victoria ceasing to be monarch clashes with facts about other people. In every TBox w1, the member's class membership gives way, never the rule.
- RBox: after the coordinator's rule, every replace changes or removes a property that holds (no added properties; the godparent draft was dropped). Yes/no balance comes from phrasing (0010's second instance asks the negated conclusion).

## Worlds dropped

- 0003: a world where both premises change (not minimal); the definitional rule premise. John F. Fitzgerald was rejected as the new value because his world clashes with Rose Kennedy's father, a fact outside the chain.
- 0004: the both-premises world and the rule premise; the Netherlands was rejected as the new value (Auvers-sur-Oise in the Netherlands would put the Oise there).
- 0002: a stored county route and a "Bard of Avon" river route, both contradicting firm bridges (not worlds).
- 0001: Langevin's real marriage route (it contradicts the edit itself).

## Remaining doubts

- Kinship (0003): Robert and Ted Kennedy re-derive P2 if they are taken as full brothers; w1 revises them to half-brothers. The Kennedy surname also hints at the original in the premise questions (no answer is contained). Caroline's mother, the near query, stays in every world.
- 0004: P1 ("buried in Auvers") is only moderately frequent (53 co-occurrences; "died in Auvers" 128), so some models may fail its check. w2 moves the village away from Paris (listed as a side fact).
- 0001 and 0002: the description worlds are formally valid but improbable.
- TBox w1 worlds (Gregory I no longer a pope, Bolt no longer the 2008 winner) follow the README's tarantula pattern and are implausible by design. 0007 R1: Supreme Court justices are disqualified and post-2014 peers can retire; both are noted, and neither applies to Thatcher or Olivier.
- Fictional new members are phrased as present facts ("has just been elected pope"), as in the README's new-species example.
- The weakest records are 0004 (strength of premise P1) and 0007 (R1 qualifications).
