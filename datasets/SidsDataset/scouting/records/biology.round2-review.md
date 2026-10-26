# Biology round 2 review (ABox 0013-0016, RBox 0017-0018)

Scope: the 12 new records `datasets/SidsDataset/records/biology/{replace,delete}/biology-{replace,delete}-001[3-8].json`. Records 0001-0012 untouched. No late note was found at the end of `reports/biology.abox2.md`.

Validator (all four extra relation files): **36 files, 0 errors**. criteria.py: Rule 9 ok (biology RBox 0009-0018: direct 3 yes / 3 no, derived 6/6, zh and es 3/3 each); Rule 11 biology row 8/8 ABox, 4/4 stored/derived; Rule 12 RBox coverage ok. Rule 13's "subject not in prompt" on 0017/0018 is the same as for every RBox record (relation-name subjects), not specific to these records.

## Evidence

- infini-gram: 52 cited counts re-run with `--fresh`; **0 changed** (all identical, incl. approximate AND counts).
- Extra phrasings for the derived claims (17 queries): "nephron is the functional unit of the urinary system" 1, "functional unit of the urinary system" 12, "nephrons of the urinary system" 0, vs "nephron is the functional unit of the kidney" 358; "the cerebellum is part of the central nervous system" 4 (plus 11 / 3 already cited), vs "cerebellum of the brain" 1,364. So 0015/0016 stay `likely`.
- Wikipedia quotes: 18 checked (Dolphin x2, MMPA, Amniote, Thoracic diaphragm, Temporal lobe, Wernicke's area, Hippocampus, Nephron, Urinary system, Glomerulus, Cerebellum x2, CNS, Shark, Chondrichthyes, Liver): **0 failed**, all verbatim.

## Per record

| Record | Verdict |
| --- | --- |
| replace-0013 (dolphin mammal → shark, `instance_of`) | KEEP. Chain query uses the declared `chain:subclass_of->instance_of` (biology.md), no→yes, yes in all 4 worlds. Inheritance query: class rule "every shark has a cartilage skeleton" is a bridge with a check, asks a trait and does not restate the edit, bone→cartilage. The forced/breakable split holds up: a cartilage skeleton defines Chondrichthyes (a by-name bony skeleton would make the dolphin an exception inside the class the edit fixes, so it gives way), while "no shark nurses" is only a generalization (some sharks even feed embryos uterine "milk"), so a nursing shark is a consistent world. The MMPA by-name world is consistent (a law can name species). |
| delete-0013 | KEEP. Amniote (chain) and diaphragm (inheritance) are does-not-know in every world; "dolphins have a diaphragm" 0 exact hits, 211 co-occurrences. Re-derivation through "dolphins are toothed whales" (64) is acknowledged in notes. |
| replace-0014 (temporal lobe of the brain → liver, `lobe_of`) | KEEP. Subproperty (`lobe_of ⊑ part_of`) and declared chain (`lobe_of ∘ part_of ⊑ part_of`, liver → digestive) both discriminate and hold in all 4 worlds; Wernicke/hippocampus worlds are clean name-vs-description splits. |
| delete-0014 | KEEP, doubt: "temporal lobe of the cerebrum / cerebral cortex" (394 / 309, vs 6,268 for "of the brain") is a possible route around the deleted fact for the two determinate queries; acknowledged in notes, treated as the same fact in other words. |
| replace-0015 (nephron urinary → respiratory, derived) | FIXED. w2's assumes now list the side facts: the kidney still makes urine, the urinary system shrinks to ureters, bladder and urethra. Premise route ("the organ made up of nephrons") and transitivity (glomerulus) are both determinate; part_of `transitive` is in RELATIONS.md. |
| delete-0015 | FIXED. w2's assumes now also drop the reading of urine-making as urinary-system membership, which closes the function route the writer flagged. |
| replace-0016 (cerebellum CNS → digestive, derived) | FIXED. w2's assumes now state the CNS becomes the spinal cord alone and the brain keeps its neurons (as the gut keeps its enteric nervous system). Determinate queries as in 0015 (Purkinje cells occur only in the cerebellum). |
| delete-0016 | KEEP. |
| replace-0017 (¬ endemic_to ∘ located_in ⊑ endemic_to) | KEEP. A real role chain over two different relations, and it holds for every pair (endemic = found nowhere outside b, so nowhere outside any c ⊇ b). The Tasmanian devil's former mainland range (and the small 2020 mainland reintroduction) do not matter: the question says "given only these two facts", and the chain's conclusion (Australia) is true anyway. The statement is an if-then rule with no short name, so it stays one sentence. |
| delete-0017 | KEEP. |
| replace-0018 (¬Func(in_genus)) | FIXED (coordinator rule): statement shortened to "'Belongs to the genus' is not functional.", original to "'Belongs to the genus' is functional.", with the derived chains that quote them. Functionality holds: a binomen fixes one genus per classification. Competing placements (Felis vs Puma concolor) are disagreements about which genus, never membership in two at once. Acinonyx avoids the Felis leo trap. |
| delete-0018 | FIXED. The statement equals the shortened replace original, and the chains are updated. |

## Coverage (replace, determinate slots)

transitivity: 0015 (glomerulus), 0016 (Purkinje cells). Chain: 0013 (instance_of ∘ subclass_of), 0014 (lobe_of ∘ part_of). Subproperty: 0014. Inheritance (ABox): 0013. Each one discriminates and gives the same answer in every world, and each relation carries its tag (RELATIONS.md for part_of; `relations/biology.md` for instance_of and lobe_of, with checks).

## Writer's doubts: rulings

1. **0015/0016 w2 (whole organ regrouped).** These worlds are valid under step 3 as decided, on the 0004 precedent ("ticks are insects" kept with side facts). Organ-system membership is a grouping convention. Regrouping the kidney or the brain contradicts no firm fact about things outside the chain (dates, other organisms, diseases): urine production, the ureters' route, the brain's neurons and so on all stay true. The only casualties are the systems' own descriptions (urinary system = organs that make and remove urine; CNS = brain + spinal cord). These are side facts of the premise that gives way, and they are now listed explicitly. Is "kidney ⊂ urinary system" entailed by other firm facts (Decision 1)? Only through the urinary system's own definition, which is the premise restated, so I did not drop the world. A stricter reader could disagree. Both worlds are lopsided toward w1, which Decision 4 keeps.
2. **Deletes forgetting part locations.** w1 of the deletes 0015 and 0016 must also forget where the glomerulus and the Purkinje cells are ("renal glomerulus", "cerebellar Purkinje cells"). This is the README's sanctioned remedy (list the side facts), and it is listed, but it is a heavy forgetting. The replace side is unaffected: there the transitivity answer is yes even if those by-name facts survive, because part_of is many-valued. Kept, with this doubt.
3. **0013 forced vs breakable.** Upheld, see the table.
4. **0015/0016 share a template.** Yes: the same derived shape (structure ⊂ organ ⊂ system, a premise route through "the organ that …", transitivity to a sub-part). Acceptable for coverage but repetitive. If diversity matters, re-pick one of them for a later round.
5. **R2 names** (肾单位, 小脑, nephron/cerebelo): they name the premise organ, not the answer system. Kept.

## Remaining doubts

- delete-0014: the cerebrum route; delete-0013: the toothed-whale route (both acknowledged).
- 0015/0016 w2 plausibility (ruled valid, see above).
