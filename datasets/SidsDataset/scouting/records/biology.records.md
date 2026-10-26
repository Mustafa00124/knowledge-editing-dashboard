# Biology records (determinacy edition): writer's report

24 records in `datasets/SidsDataset/records/biology/{replace,delete}/`, built by
scripts in `{SCRATCH}/biow/` (`build_abox.py`, `build_tbox.py`, `build_rbox.py`;
rerun them rather than hand-editing). New relations: `{SCRATCH}/relations/biology.md`
and `biology.checks.json`. Validator: 24 files, 0 errors (with the extra files).
criteria.py B7 row for biology: 4/4/4 boxes, 2 stored + 2 derived, 32 determinate,
24 background, 8 derived beliefs. RBox yes/no for biology: direct 2/2, derived 4/4,
cross-lingual 2/2.

## Records

Derived-query labels in order (det = determinate, bg = background_beliefs,
db = derived_beliefs). Delete NNNN mirrors replace NNNN with the same labels.

| Id | Edit (original -> new) | Relation | Deriv. | Derived labels | Logic |
| --- | --- | --- | --- | --- | --- |
| 0001 | Insulin produced by the pancreas -> the thyroid gland | `produced_by_organ` (new) | very_unlikely | det (functional), det (neck; delete: abdomen), bg (type 1 diabetes), bg (insulinoma) | dl x4 |
| 0002 | Scurvy from vitamin C deficiency -> vitamin D | `caused_by_deficiency_of` (new) | very_unlikely | det (functional), det (sunlight vitamin; delete: water-soluble), bg (gums), bg (citrus) | dl x4 |
| 0003 | Bubonic plague transmitted by an insect -> an arachnid | `transmitted_by_class` (new) | likely | det (premise route), det (same class as spiders; delete: mosquitoes), db (fleas carry it?), db (fleas insects?) | dl x4 |
| 0004 | Lyme disease transmitted by an arachnid -> an insect | `transmitted_by_class` | likely | det (premise route), det (same class as mosquitoes; delete: spiders), db (ticks carry it?), db (deer ticks arachnids?) | dl x4 |
| 0005 | Every spider has eight legs -> six | `has_leg_count` | very_unlikely | det (Bagheera kiplingi), det (Eriovixia gryffindori), bg (tarantula), bg (black widow) | dl x4 |
| 0006 | Every bird lays eggs -> live birth | `reproduces_by` | very_unlikely | det (Rote myzomela), det (Sulawesi streaked flycatcher), bg (ostrich), bg (penguin) | dl x4 |
| 0007 | Every mammal has a four-chambered heart -> three | `has_heart_chambers` | unlikely | det (kipunji), det (olinguito), bg (blue whale), bg (bottlenose dolphin) | dl x4 |
| 0008 | Every bacterium is a prokaryote -> a eukaryote | `subclass_of` | very_unlikely | det (Thermus aquaticus), det (Aliivibrio fischeri), bg (E. coli), bg (blue-green algae) | dl x4 |
| 0009 | 'Is part of' transitive -> not | `part_of` | null | instantiation x2 (new: no, yes) | dl x2 |
| 0010 | 'Lives in mutualism with' symmetric -> not | `mutualist_of` | null | instantiation x2 (no, yes) | dl x2 |
| 0011 | Inverse of 'preys on' is 'is prey of' -> 'is a parasite of' | `preys_on` | null | instantiation x2 (yes, no) | dl x2 |
| 0012 | 'Is a parasite of' asymmetric -> not | `parasite_of` | null | instantiation x2 (yes, no) | dl x2 |

Worlds: 0001, 0002 and all TBox records have 4 (two independent storage choices);
0003, 0004 have 2 (which premise gives way; delete: which premise is forgotten).

## Changes from the scouting and review

- **0001 insulin**: islets query replaced by "An insulinoma is a tumour that arises
  in which organ?" (islets are definitionally pancreatic and also make glucagon).
  Type 1 diabetes query kept. Four worlds (two independent choices). Delete: the
  neck query is rephrased around the original ("Is insulin produced in the abdomen?").
- **0002 scurvy**: "vitamin C treats scurvy" dropped (near-definitional). Replaced by
  "A deficiency of which vitamin causes swollen, bleeding gums and loose teeth?"
  (stored by name to vitamin C, or through scurvy). Citrus query kept with the
  reviewer's note. Delete: sunlight query rephrased (water-soluble vitamin).
- **0003**: gharial dropped (class-rule premise, Decision 2). Replaced by **bubonic
  plague is transmitted by an insect** (fleas; fleas are insects), not the scabies
  backup: scabies' carrier is named after the disease (Sarcoptes *scabiei*, "scabies
  mite"), which would make the "scabies is caused by a mite gives way" world close to
  entailed-false, the same leak that killed chickenpox. Plague evidence: 'bubonic
  plague' near 'insect' 2.5% of mentions with sampled hits unrelated (repellent and
  pest-control copy), near 'fleas' 17.6%; no exact direct forms. It also reverses the
  direction of 0004 (insect to arachnid).
- **0004 Lyme**: leg-count premise-route query replaced by "Are the animals that
  transmit Lyme disease arachnids?"; class comparison changed to mosquitoes.
- **Chickenpox** dropped (as instructed).
- **TBox**: chosen fresh (scouting covered ABox only). Spiders as suggested. In every
  "stored value wins" world the member's class membership gives way (coordinator
  ruling), never an exception to the rule. Members picked so that the
  membership-gives-way world is coherent: flightless birds (not the chicken),
  cetaceans ("whales are fish"), blue-green algae (long classed as algae). Sharks were
  considered and rejected: "great white shark" carries its class in its name.
- **RBox**: all four remove or change a property that holds (coordinator ruling);
  yes/no balanced by phrasing ("does it follow ...?" vs "given only this fact, is it
  possible ...?"). Far prompt "Is 'is a sibling of' symmetric?" swapped for
  "'is the identical twin of'" because B6 showed it at 12 uses across topics.
- New relation `prey_of` (`inverse:preys_on`) added because 0011's axiom names it (R7).

## Worlds dropped

- 0001: "insulin is made in the abdomen" route for the neck query (would put the
  thyroid in the abdomen, contradicting the firm "thyroid is in the neck").
- 0002: "citrus prevents scurvy because citrus has vitamin D" (contradicts firm
  "citrus has no vitamin D").
- 0003/0004: the combining rule ("a disease is transmitted by an animal of its
  carrier's class") is definitional and never gives way; no exception world on the
  class memberships ("deer ticks" in 0004 closes the "only Lyme ticks are insects"
  sub-case).

## Doubts

- **Weakest: 0002 citrus query.** The by-name world (citrus prevents a vitamin-D
  disease) is coherent only as a mechanism-free historical fact; text usually states
  the mechanism. Kept as lopsided (Decision 4).
- **0001 zh**: 胰岛素 contains 胰 (pancreas), unavoidable; it leaks the original answer.
- **0004 R4**: loose web text calls Lyme "insect-borne" (1,305 co-occurrences);
  some models may answer insect before editing. The w1 world (ticks become insects)
  drags firm side facts (eight legs); a strict reviewer could drop it.
- **0003 R1**: plague also spreads by direct contact and droplets; its only vector is
  the flea, and the prompts ask about the transmitting animal's class.
- **0003/0004** have the same shape (vector -> class), in opposite directions.
- **TBox by-name storage** is weak for the bottlenose dolphin (10 co-occurrences)
  and only moderate for black widow and E. coli; "E. coli is not a bacterium" is a
  strained world. All are kept per README TBox guidance.
- **0007 derivability** set to `unlikely` (less frequent than the other rules);
  arguable either way.
- **0011 second instance** ("Owls prey on mice. Does it follow that mice are prey of
  owls?" new answer no) relies on a relation having a single inverse; a model might
  still answer yes from the plain meaning of "prey of".
- Wikipedia's API rate-limited some fetches; every quote in the records was read from
  text fetched in this run or in the scout's saved copies (`bio/wiki/`). Counts not
  re-run with `--fresh` may come from the shared cache.
