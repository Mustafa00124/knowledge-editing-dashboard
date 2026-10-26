# Biology fictional inserts 0001-0020: verifier review

All fixes went through the generator (`scratchpad/bio_ins/gen.py` plus `bio_ins/search.json`), which was then rerun. No record was edited by hand, so rerunning `gen.py` reproduces the current records. Backups of the writer's versions: `scratchpad/bio_insv/before/`, `bio_insv/gen.py.orig` and `bio_insv/search.json.orig`.

## Checks
- **Fresh counts:** I reran all 37 made-up names and the 3 stored-fact counts with `--fresh`. None changed. Every name has 0 hits except `thalvic` and `ostrels`, which have 1 each.
- **Web searches:** I ran 18 searches covering every name that lacked one. None found a real taxon, term, product or person with any of these names; the only hits were look-alikes such as Leuroglossus, drebrin, CorVel, Brenania and Morchella dunensis. The notes are in `search.json`, so all 20 records now carry a `search` source. Where several names were searched together, the note says so.
- **Quotes:** I checked 33 Wikipedia quotes against the live articles. 28 matched word for word. The other 5 had been cut off mid-sentence with a full stop added (Echidna, Frog, Lungfish, Coelacanth) or had the pronunciation dropped (Bat). I trimmed all 5 to exact substrings.
- **Validator:** 20 files, 0 errors.
- **criteria.py, Rule 5:** no biology finding; the only remaining failures are history-insert-0009 to 0012. Rules 9 and 11 are unchanged.

## Per record
| Id | Verdict |
| --- | --- |
| 0001 | FIXED: search added; Echidna quote trimmed (this quote also backs the four-echidna count). |
| 0002 | FIXED: search added. |
| 0003 | FIXED: search added. |
| 0004-0006 | FIXED: search added. |
| 0007 | FIXED: searches added; missing space in the zh prompt ("Talvessa quorinakorvel-ranked"). |
| 0008 | FIXED: searches added; Frog quote trimmed. |
| 0009 | FIXED: Lungfish quote trimmed. The closed-list query now asks about "the four African lungfish species" instead of "the African lungfishes", because velkarids could themselves be African lungfishes, which would make the w2 "no" wrong. The notes no longer claim that new African lungfish species were recognised in recent decades, which I could not verify. |
| 0010 | FIXED: Coelacanth quote trimmed. |
| 0011 | FIXED: search added. |
| 0012 | FIXED: search added; Bat quote trimmed. |
| 0013 | FIXED: search added; the axiom was `Quorrel ⊑ SkellScaled`, a rejected draft name, and is now `Vesquorn ⊑ SkellScaled`. |
| 0014 | FIXED: search added; the axiom was `Ossling ⊑ MurrowBanded` and is now `Drallimet ⊑ MurrowBanded`. |
| 0015-0020 | FIXED: search added. |

## Writer's doubts
- **(a) "Living" / "newly discovered" in the TBox entity edits, with w1 keeping the stored count.** I kept this. It is exactly the README's own entity-insert pattern: Thalia, "a newly discovered moon of Eris", leaves the count unchanged if the model stores it as a number. 0001-0003 work the same way. w1 is the world where the model does not update the stored number, not a contradictory class rule. The only real flaw was the open-ended "African lungfishes" wording in 0009, fixed above.
- **(b) Made-up membership in the prompt not listed as a bridge (0008-0010).** I kept this, because it matches the convention in history-0009/0010, people-0009/0010, physics-0009/0010 and mathematics-0010. `bridge_in_prompt` is all-or-nothing. Listing the made-up fact with `false` would demand a pre-edit check that no model can pass. Setting it `true` would leave the real class fact unchecked.

## "Could it exist unrecorded?"
All five entity inserts pass. They are a cryptic New Guinea echidna, a split Stewart Island kiwi lineage, a split tuatara lineage, a lungfish lineage in poorly surveyed swamps, and a deep-reef coelacanth genus. Each is a species-level or genus-level discovery that would only update a count. None contradicts a documented fact.

## Remaining doubts
- In 0001 the made-up genus (Kerroglossus) is a bigger claim than a new Zaglossus species would be. It is still plausible, so I kept it.
- The RBox near queries share the yes/no answer with the direct query. R6 exempts RBox, and the other topics' RBox inserts do the same.
- Some `search` sources record the single name in `query`, while the search actually run was a combined OR query. The note says which.
