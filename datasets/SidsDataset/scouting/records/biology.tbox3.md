# Biology TBox 0019-0020 (replace + delete)

Generator: `scratchpad/bio_tbox3/gen.py`. New relations (no tags, property-free) in
`scratchpad/relations/biology.tbox3.md`: `has_diet`, `lives_in_habitat`. No checks file
(no tags to check). Validator: 40 files, 0 errors.

| Id | Edit | Derivability | Derived queries (all `inheritance`, `dl`) |
| --- | --- | --- | --- |
| replace-0019 | Every snake is carnivorous -> herbivorous | very_unlikely | Tantilla tjiasmantoi (det.), Lycodon zoosvictoriae (det.), boa constrictor (bb), pythons (bb) |
| delete-0019 | removes "Every snake is carnivorous." | very_unlikely | new members: does not know; boa/pythons: carnivorous by name, null via rule |
| replace-0020 | Every echinoderm lives in the sea -> in fresh water | unlikely | Promachocrinus fragarius (det.), Ophiojura exbodi (det.), starfish (bb), sand dollar (bb) |
| delete-0020 | removes "Every echinoderm lives in the sea." | unlikely | as 0019 pattern |

Worlds: 4 per record (two independent storage choices). In a by-name world the member
leaves the class (side facts listed: stays a reptile; reticulated python no longer the
longest snake; starfish leaves Asteroidea; sand dollar leaves Echinoidea).

## Self-verification
- Counts: all 21 infini-gram counts re-run with `--fresh`: 21/21 identical.
- Quotes: 6 Wikipedia quotes (Snake, Burmese python, Boa constrictor, Echinoderm,
  Starfish, Sand dollar) checked against the rendered plain-text extract: 6/6 exact.
- R1: no herbivorous snake exists (Wikipedia: "strictly carnivorous"); no freshwater or
  terrestrial echinoderm (Wikipedia: "All echinoderms are marine"). "Carnivorous" used,
  not "carnivore" (Carnivora ambiguity).
- R2: well-known members chosen whose names hold no class word (no "... snake", no "sea
  urchin/sea cucumber/sea lily"); zh prompts name only the class (海星 would leak).
  New-member prompts state membership only, without "brittle star", "crinoid",
  "Antarctic", "seamount", prey or habitat hints.
- Membership-gives-way worlds: avoided king cobra, anaconda, black mamba (superlatives
  entailing snake membership). Pythons carry one superlative side fact (reticulated
  python longest snake), about the member itself, kept as with the ostrich in 0006.
- Near queries: snake reptile/amphibian (reptile); echinoderm symmetry (five-fold); both
  differ from the new answer. Far prompts are new to the dataset.
- Rule 4: no overlap with 0005-0008 (spider legs, bird reproduction, mammal heart,
  bacterium) or 0013 (dolphin/shark).

## Doubts
- Genus-level knowledge could give a second route for new members (Lycodon = wolf
  snakes eating lizards; Tantilla = centipede eaters; Ophio- = brittle star). All four
  names are rare (0-40 Dolma hits), so the risk is small but not nil.
- Echinoderm class rule is less frequent than member facts (154 exact), hence
  `unlikely`; by-name exact sentences for sand dollars are modest (co-occurrence 5,854).
