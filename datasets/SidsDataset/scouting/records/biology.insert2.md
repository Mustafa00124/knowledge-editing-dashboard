# Biology inserts: re-tag and rebalance (insert2)

Generated through `bio_ins/gen.py` (backup `gen.py.bak-insert2`; counts/search
backups alongside). The generator was used consistently: the earlier
JSON-only re-tag of 0018-0020 (`all`) is now in gen.py too.

## Old -> new

| New id | Old id | Box | Old tag | New tag | What |
| --- | --- | --- | --- | --- | --- |
| 0001 | 0001 | ABox | entity | subject | Kerroglossus fennellae, a new echidna (re-tag) |
| 0002 | 0002 | ABox | entity | subject | Apteryx tenebris, a new kiwi of Stewart Island (re-tag) |
| 0003 | 0003 | ABox | entity | object | REWRITTEN: "The tuatara genus Sphenodon has a newly described living species, Sphenodon kerewai." subject Sphenodon, relation has_species (new) |
| 0004 | - | ABox | - | object | NEW: "The orangutan genus Pongo has a newly described living species, Pongo sinarensis." |
| 0005 | - | ABox | - | subject_object | NEW: "The mite Sarvacarus tellini is a parasite of the beetle Quellotrechus marrani." (real parasite_of) |
| 0006 | 0004 | ABox | relation | relation | cattle egret drevin-linked to hippopotamus (moved) |
| 0007 | 0006 | ABox | relation | relation | Drosophila cassel-bound to T. H. Morgan (moved) |
| 0008 | 0007 | ABox | both | all | Talvessa quorina korvel-ranked above Brennia ostala (moved) |
| 0009, 0010 | same | TBox | entity | subject | velkarids (lungfish), morrenids (coelacanths) |
| 0011 | same | TBox | relation | relation | hummingbirds drask-feed on nectar (made-up role, real object) |
| 0012 | same | TBox | relation | relation | every bat is thalvic (made-up property, no separate object) |
| 0013, 0014 | same | TBox | both | all | vesquorn skell-scaled, drallimet murrow-banded (made-up class + made-up property: nothing real) |
| 0015-0017 | same | RBox | relation | relation | unchanged |
| 0018-0020 | same | RBox | all | all | unchanged (tag now also in gen.py) |

## Dropped
- old 0005 (giant panda korvel-ranked above red panda, relation): surplus
  relation; dropped rather than 0004/0006 to keep property variety
  (symmetric 0006, inverse 0007, transitive+asymmetric 0008 all kept).
- old 0008 (Vellunia pelloides drevin-linked to Corvalla dunensis, both):
  surplus all; its symmetric relation stays covered by 0006, while
  korvel_ranked_above would have vanished had 0007 gone. Its names remain in
  RBox 0019/0020 prompts (independent).
- old 0003 as a subject record: turned into the object record 0003 (same
  made-up name; no subject record about it remains, so not a flip).

## New names (Dolma counts, re-run --fresh: all unchanged)
Pongo sinarensis 0, sinarensis 0, Sarvacarus 0, Sarvacarus tellini 0,
Quellotrechus 0, Quellotrechus marrani 0 (Sphenodon kerewai 0, kept). Web
searches: none is a real taxon (look-alikes only: Stevacarus; Dyschirius
marani; extinct Pongo grovesei / nguyenbinheri, 2025). Bridge counts:
genus Sphenodon 140, three species of orangutan 275, Apes do not have tails 84,
beetles are insects 577, mites are arachnids 743. All 18 Wikipedia quotes in
0003-0008 re-checked against the live wikitext: all found.

## Relations
`relations/biology.insert2.md`: `has_species` (inverse:in_genus,
cardinality:many). `relations/biology.insert2.checks.json`: its inverse check,
plus checks for parasite_of asymmetric and inverse:host_of (tags already in
RELATIONS.md, but relation_checks.json had no checks for them).

## Validation
validate.py with both extra files: 0 errors (20 files). criteria.py: no
biology insert under Rules 5, 7, 9, 11, 13; Rule 8 lists only has_species
(scratch file only).

## Doubts
- TBox 0012-0014 tagging reads a made-up adjective ("thalvic", "skell-scaled")
  as a made-up relation (property), as RELATIONS.md catalogues them. Read as
  a made-up concept under real subclass_of they would be object /
  subject_object, and an object TBox insert would then need 2 indeterminate
  queries it doesn't have.
- 0003/0004 direct answers are binomials containing the genus named in the
  prompt; the new information is the epithet. Unavoidable for a new species
  in a named genus.
- 0004 orangutan species count: three is the consensus since 2017 (older
  text says two); the count query says "living" because extinct Pongo
  species were described in 2025.
- 0005 asymmetry of parasite_of is the catalogued tag (it ignores rare mutual
  parasitism); a beetle parasitising its own mite is not credible.
