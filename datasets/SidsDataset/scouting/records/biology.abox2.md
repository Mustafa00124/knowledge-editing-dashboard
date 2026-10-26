# Biology: ABox edits 0013-0016 (relation-property coverage)

Records: `datasets/SidsDataset/records/biology/{replace,delete}/biology-{replace,delete}-001{3,4,5,6}.json` (8).
Generator scripts (rerunnable): `scratchpad/bio_abox2/r0013.py` ... `r0016.py` (shared code in `common.py`, `partof.py`, counts in `counts.py`).
Existing records 0001-0012 untouched.

Validation: `validate.py` on `records/biology/*/*.json` with `relations/biology.md` (+ `biology.rbox2.md`, needed only for the rbox2 writer's new 0017/0018): **36 files, 0 errors** (my 32 files also pass with `biology.md` alone). `criteria.py`: Rule 5 ok; Rule 11 biology row 8/8 ABox, 4/4 stored/derived, 48 determinate / 32 background / 16 derived beliefs; no biology-001[3-6] in any failure list (Rule 13 subject check: fixed 0014's subject to "temporal lobe"). The Rule 11 and Rule 12 FAILs shown are global (other topics' shapes, share of property-less relations), not from these records.

## Relations added (`relations/biology.md`, `.checks.json`)

- `instance_of`: same tags as in RELATIONS.md (`cardinality:many`, `chain:subclass_of->instance_of`); its chain check already exists in relation_checks.json.
- `lobe_of` (new): `subproperty:part_of`, `chain:part_of->part_of`, with a check for each.
- I did not use `endemic_to` for subproperty (my first plan: endemic_to ⊑ native_to, giant panda) because the parallel rbox2 writer has added `endemic_to` with other tags (`biology.rbox2.md`); adding a different tag set would conflict. So I used `lobe_of` instead.

## The 8 records

| Id | Edit (original → new) | Derivability | Derived queries: derivation / label / logic |
| --- | --- | --- | --- |
| replace-0013 | The dolphin is a mammal → a shark (`instance_of`) | unlikely | chain det (Is the dolphin a cartilaginous fish? no→yes; bridge: every shark is a cartilaginous fish); inheritance det (skeleton bone→cartilage; bridge: every shark has a cartilage skeleton); inheritance background (dolphin mothers nurse with milk: w1/w3 yes, w2/w4 no); composition background (covered by US Marine Mammal Protection Act: w1/w4 yes, w2/w3 no). All dl. 4 worlds = 2 independent storage choices |
| delete-0013 | deletes "The dolphin is a mammal" | unlikely | chain det (Is the dolphin an amniote? null); inheritance det (Do dolphins have a diaphragm? null); nursing and Act background (yes / null). dl |
| replace-0014 | The temporal lobe is a lobe of the brain → of the liver (`lobe_of`) | very_unlikely | subproperty det (Is the temporal lobe part of the liver? no→yes); chain det (part of the digestive system? no→yes; bridge: liver ⊂ digestive system); composition background (organ of Wernicke's area; organ of the hippocampus: brain if stored by name, liver if stored as "in the temporal lobe"). dl, 4 worlds |
| delete-0014 | deletes the original | very_unlikely | subproperty det (part of the brain? null); chain det (part of the CNS? null; bridge brain ⊂ CNS); Wernicke / hippocampus background (brain / null). dl |
| replace-0015 | The nephron is part of the urinary system → respiratory system (`part_of`); premises: nephron ⊂ kidney, kidney ⊂ urinary system, transitivity (definitional) | likely | binding det, premise_route (system of "the organ made up of nephrons": respiratory); transitivity det (Is the glomerulus part of the respiratory system? no→yes; bridge glomerulus ⊂ nephron); 2 premise derived_beliefs (nephron ⊂ kidney: w1 no / w2 yes; kidney ⊂ urinary: w1 yes / w2 no). dl |
| delete-0015 | deletes the original | likely | premise route det null; transitivity det (glomerulus ⊂ urinary system? null); premises (null/yes, yes/null). dl |
| replace-0016 | The cerebellum is part of the CNS → the digestive system (`part_of`); premises: cerebellum ⊂ brain, brain ⊂ CNS, transitivity | likely | premise route det (system of "the organ that contains the cerebellum": digestive); transitivity det (Are Purkinje cells part of the digestive system? no→yes); 2 premise derived_beliefs. dl |
| delete-0016 | deletes the original | likely | as 0015 delete. dl |

Worlds for 0015/0016: w1 the structure moves to an organ of the new system (lungs; stomach), its own parts going with it; w2 the organ (kidney; brain) is regrouped into the new system. The deletes forget one premise each, with the same side facts.

## Property coverage (replace, determinate slots)

| Property | Where |
| --- | --- |
| transitivity | 0015 (glomerulus), 0016 (Purkinje cells) |
| chain (declared) | 0013 (instance_of ∘ subclass_of), 0014 (lobe_of ∘ part_of) |
| subproperty | 0014 (lobe_of ⊑ part_of) |
| inheritance (ABox) | 0013 (cartilage skeleton) |
| premise route | 0015, 0016 (the required one per derived edit) |

## Evidence highlights

- 0013: "dolphins are mammals" 1,907; "dolphin is a mammal" 482; Wikipedia Dolphin lead quoted.
- 0014: "temporal lobe of the brain" 6,268; Wikipedia Temporal lobe lead quoted.
- 0015 derived: "nephron(s) is/are part of the urinary system" 0/0; "nephron AND urinary system" 1,830 vs "nephrons AND kidney" ~122k (about 70x); I read the samples, and they describe the system, not the fact. Premises: 358 / 216 + quotes.
- 0016 derived: exact forms 11 + 3 out of 1.18M cerebellum mentions; "cerebellum AND CNS" 2.3%, and the samples are research text. This is weaker than 0015 but still `likely`.
- All Wikipedia quotes were fetched (UA SidsDatasetScout/1.0) and match the text.

## Dropped or changed while designing

- Giant panda endemic to China → Brazil (subproperty via endemic_to ⊑ native_to): dropped for the relation conflict above.
- Right atrium (heart ⊂ circulatory) for 0016: dropped. Its w1 (the right atrium leaves the heart) gives a three-chambered human heart, which contradicts the firm rule "every mammal has a four-chambered heart" outside the chain. In the delete, "the SA node is the heart's pacemaker" would also be a route around the forgotten premise.
- Ileum / Peyer's patches: dropped. Peyer's patches also occur in the jejunum, so the transitivity answer would be unclear (R1).
- Occipital lobe ⊂ CNS: replaced by the cerebellum, to avoid two occipital/temporal records.
- Dolphin queries: "breathes air?" was dropped (unclear whether gills exclude air breathing). "Warm-blooded?" was dropped because mako/white sharks are partly endothermic (R1). In the 0013 delete, "has hair at some stage?" was dropped because "even dolphins have hair" is stated by name; I used the diaphragm instead.

## Doubts

1. **0015/0016 worlds** move whole organs between systems (kidney → respiratory, brain → digestive) or a structure into another organ. Both are strained. Following Decisions 1, they list side facts, as 0004's "ticks are insects" world does. A strict verifier could argue that "kidney ⊂ urinary system" is entailed by its urine production. W2 keeps the function and changes only the grouping.
2. **Delete side facts**: the transitivity query is does-not-know in w1 only because w1 also forgets where the structure's parts are ("glomeruli are in the kidney" and "Purkinje cells are in the cerebellum" are also stored by name). This is listed explicitly in the worlds' assumes.
3. **0013 determinate vs background split**: positive defining traits of sharks (cartilage skeleton, being a cartilaginous fish) are treated as forced. Absences (no nursing, not covered by the Act) are treated as generalizations a new member can break (the platypus argument). This is reasoned but could be contested.
4. **Re-derivation in stored deletes**: dolphin → toothed whale → mammal, and temporal lobe → cerebrum → brain. Both are acknowledged in the notes.
5. **R2 names**: "nephron"/肾单位 and "cerebellum"/小脑/cerebelo name the premise organ, not the answer (a system), and they agree with the new answer in w2. So I kept the native terms, unlike 0001's 胰岛素. 0014's hippocampus and 0013's MMPA by-name worlds are probably the likelier ones (Decision 4, lopsided).
