# people: ABox edits 0013-0016 (relation-property coverage)

Builder: `scratchpad/people_abox2/build.py` (+ `records_def*.py`; counts in `c0-c2.txt`, samples `d_*.txt`, Wikipedia text `wiki/`). The JSON in the repo is the source of truth.

Validator (with `relations/people.md` and `.checks.json`) on people 0001-0016: 32 files, 0 errors. criteria.py: Rule 5 ok; Rule 11 people row 8/8 ABox, 4/4 stored, 4/4 derived, 48 determinate / 32 background / 16 derived; no rule lists 0013-0016.

## Records

| Id | Edit (original -> new) | Derivability | Derived queries (replace): derivation, label, logic |
| --- | --- | --- | --- |
| 0013 | Mozart's father: Leopold Mozart -> C. P. E. Bach (`has_father`, new) | very_unlikely | paternal grandfather -> J. S. Bach: **chain**, det, dl; child of C. P. E. Bach?: **subproperty**, det, dl; who taught him as a child: composition, background, dl; who took him on tour: composition, background, dl |
| 0014 | Aquinas's order: Dominican -> Franciscan (`member_of`) | very_unlikely | lived under the Rule of St Francis?: **inheritance**, det, dl; founder of the order he joined: **inheritance**, det, dl; order his family tried to stop him joining: composition, background, dl; order whose habit he is depicted in: composition, background, dl |
| 0015 | Aage Bohr's paternal grandfather: Christian Bohr -> George Darwin (`has_paternal_grandfather`) | likely | father of Aage's father: binding, det, premise_route, dl; Charles Darwin an ancestor of Aage?: **transitivity** via `ancestor_of`, det, dl; Niels Bohr's father: premise, derived, dl; Niels and Harald full brothers?: premise, derived, **fol** |
| 0016 | Stella McCartney's paternal grandfather: Jim McCartney -> Alec Guinness (`has_paternal_grandfather`) | likely | father of Stella's father: binding, det, premise_route, dl; grandchild of Guinness?: **subproperty**, det, dl; Paul's father: premise, derived, dl; Paul Stella's father?: premise, derived, dl |

Coverage on the replace side (determinate slots): chain 1 (0013), subproperty 2 (0013, 0016), inheritance 2 (0014), transitivity 1 (0015). Functional not used.

Deletes mirror each: every new_answer null, worlds re-derived (background: by-name keeps the original, description -> null; derived: each world forgets one premise plus the sibling links that would restore it). Changed derivations in deletes: 0013 chain query asks the original grandfather (Johann Georg Mozart, bridge "he was Leopold's father"); 0014 inheritance asks the Dominicans' rule (Rule of St Augustine) and founder (St Dominic); 0015 transitivity has no counterpart around the original grandfather, so the delete asks subproperty ("Was Aage a grandchild of Christian Bohr?").

## Evidence (key figures, Dolma)

- 0013: "Mozart's father" 1,836, "his father Leopold" 2,577, Wikipedia birth sentence.
- 0014: "Aquinas, a Dominican" 306, "Aquinas was a Dominican" 257, lead "Italian Dominican friar". Background bridges quoted from Wikipedia ("held prisoner ... to prevent him from assuming the Dominican habit"; "often depicted in a Dominican habit").
- 0015: "grandson of Christian Bohr" 0, "Aage Bohr's grandfather" 0, "Aage Bohr AND Christian Bohr" 53 (samples: family lists); premises "son of Niels Bohr" 60, "son of Christian Bohr" 59, both in Wikipedia leads/birth sentences. Christian Bohr's short article does state "grandfather of ... Aage Bohr", which is why it is likely, not very_likely.
- 0016: "granddaughter of Jim McCartney" 0, "Stella McCartney AND Jim McCartney" 10 (samples: fact pages about Paul), against "Stella McCartney" 291,826 and "daughter of Paul McCartney" 545; P2 "Paul's father, Jim" 61, "Paul McCartney's father" 68, Wikipedia quote.

## Candidates dropped

- Newton born in England (transitivity via `located_in`): "Newton was born in England" 151, about as often as Woolsthorpe (239), so not derived.
- Sofia Coppola / Carmine Coppola: conclusion stated in her Wikipedia article and about 45 "her grandfather Carmine" hits against about 360 for the premise (about 12%, the review's "medium" range).
- Anjelica Huston / Walter Huston: conclusion about 40% of the weaker premise.
- Aquinas background queries about Albertus Magnus or Bonaventure: the world where they share his order moves another person's firm membership.
- J. C. Bach as Mozart's new father: J. C. Bach really did coach the child Mozart in London, which would blur the teacher query (R1).

## Relations

`relations/people.md`: added `has_father` (`functional`, `subproperty:child_of`, `chain:has_father->has_paternal_grandfather`). `people.checks.json`: checks for those three tags and for `ancestor_of` `transitive` (the relation had no check). `member_of` is reused from history for the order. Backups are in `.bak` files.

## Doubts

- 0013 / 0014 description worlds are improbable (C. P. E. Bach teaching the child in Salzburg; paintings in the Franciscan habit). They are lopsided but consistent (Decision 4).
- 0014 delete rule query relies on "Dominicans live under the Rule of St Augustine", which many models will miss (the check drops it).
- 0013 delete chain query: the bridge (Johann Georg Mozart) is obscure.
- 0015: Christian Bohr may fail the premise check on small models. 0015 and 0016 share 0003's template and its over-determination caveat (siblings read as full siblings).
- Surname hints (Mozart, Bohr, McCartney) in premise prompts, as in 0003.
- Another agent has added `people-*-0017/0018` (RBox) since this work began. 0018 uses `has_birth_mother`, which is not in my relations file, so validating `people/*/*.json` shows 2 errors that are not from these records.
