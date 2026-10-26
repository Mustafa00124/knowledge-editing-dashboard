# Biology TBox 0019-0020 review

| Record | Verdict |
| --- | --- |
| replace-0019 (snake carnivorous -> herbivorous) | FIXED: python side fact now says the longest-snake title passes to a non-python snake; notes record that snake frugivory is anecdotal only. |
| delete-0019 | FIXED (notes): genus-route risk recorded (Tantilla/centipedes 101, Lycodon/lizards 51). |
| replace-0020 (echinoderm sea -> fresh water) | FIXED: "a echinoderm" -> "an echinoderm"; starfish side fact rewritten (Asteroidea stops being an echinoderm class, so four living classes, not five); sand-dollar wording; notes on brackish tolerance and why the genus route can't change the replace answer. |
| delete-0020 | FIXED (notes): genus-route risk recorded (Ophiojura 160, mostly "Jurassic brittle star" news; -crinus = crinoid). |

## Checks
- Counts: 21/21 re-run with `--fresh`, 0 changed. Extra: Lycodon 2,205; Tantilla 2,527; Promachocrinus 183; Ophiojura 160; wolf snakes 724.
- Quotes: 6/6 found word for word in the Wikipedia plain-text extracts.
- New members confirmed on Wikipedia: T. tjiasmantoi (Koch & Venegas 2016, "from the Peruvian Andes", La Libertad); L. zoosvictoriae (Cambodia, 2014); P. fragarius (crinoid, 2023); O. exbodi (brittle star, 2021).
- R1 snakes: no herbivorous snake. Fruit eating is anecdotal only (Naja nigricollis, Engel 1997; an Indian rock python that ate mangoes carrying larvae). Egg-eaters still count as carnivorous. The rule holds.
- R1 echinoderms: no freshwater species. Some tolerate brackish water or survive short spells of low salinity in experiments. None lives in fresh water. The rule holds.
- Python side fact: it is a superlative about the member, ranked within the class, so it moves with membership, like the ostrich as largest bird (0006). No other entity's fixed name or number depends on it, unlike the popes' numbering. Kept.
- Replace determinate queries: these hold even against the genus route. The prompt states class membership, so a clash with a subclass value is resolved by the species leaving the subclass. The answer stays the edited value.
- Logic `dl`, hops 2: correct. No overlap with 0005-0008 or 0013 (Rule 4). Validator: 22 files, 0 errors.

## Remaining doubts
- Deletes: a model that knows the genus (Ophiojura is a brittle star, -crinus marks a crinoid, Tantilla eats centipedes) could keep the old answer, so "does not know" is not airtight for the new members. Accepted, as with the jumping spider/monkey new members in 0005/0007.
- "Boa constrictor": "constrictor" hints at killing prey but doesn't state a diet. It only strengthens the by-name world of an already indeterminate query.
