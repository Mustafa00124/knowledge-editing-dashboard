# literature_arts: RBox chain insert (0017)

## Replaced
`literature_arts-insert-0017` (chime_wed_to ⊑ collaborated_with). Weakest of 0015-0017:
its "yes" instance (Gilbert collaborated with Sullivan) is true in the world without the
edit, so it did not discriminate; 0015 (transitive) and 0016 (asymmetric) are clean.
Yes/no pattern kept: direct no, zh/es yes, derived yes/no. Tag stays `relation`.
Edited the JSON directly (built from scratch script `la_chain_build.py`).

## The chain
Edit: "If a work is folio-sworn to a second work, and that second work was written by an
author, then the first work is folio-sworn to that author."
Axiom `folio_sworn_to ∘ written_by ⊑ folio_sworn_to` (written_by is real, in RELATIONS.md).
- Direct: "If a work is 'folio-sworn to' another work, can it fail to be bound in the same
  way to the author of that other work?" -> no
- D1: "Hamlet is folio-sworn to Don Quixote. Does it follow that Hamlet is folio-sworn to
  Miguel de Cervantes?" -> yes. Bridge (not in prompt): Don Quixote was written by Miguel de Cervantes.
- D2: "Jane Eyre is folio-sworn to War and Peace. Could Jane Eyre fail to be folio-sworn to
  Leo Tolstoy?" -> no (only with the edit). Bridge: War and Peace was written by Leo Tolstoy.
- zh/es: D1 translated ("页誓于" / «folio-sworn» a), hop left out.
- Near: housed_in/located_in chain question (yes). Far: "Is the relation 'borders' symmetric?" (now 3 uses).

## Names and counts
- "folio-sworn": Dolma 0, RedPajama 0; "folio sworn" Dolma 0; WebSearch "\"folio-sworn\"" (2026-10-26): no term.
  New to RELATIONS.md and all scratch relation files.
- Bridges (stored): "Don Quixote by Miguel de Cervantes" 3469, "Cervantes's Don Quixote" 1263,
  Wikipedia "Don Quixote is a novel by Miguel de Cervantes"; "War and Peace by Leo Tolstoy" 3537,
  "Tolstoy's War and Peace" 5912, Wikipedia "is an epic novel by the Russian author Leo Tolstoy".
  Checks: "Who wrote the novel Don Quixote?" / "Who wrote the novel War and Peace?"

## Validation
validate.py with relations/literature_arts.chain.{md,checks.json}: 0 errors. criteria.py:
literature_arts passes the chain criterion; Rules 5, 7, 9, 10 ok; Rule 13 lists no
literature_arts insert; Rule 8 lists folio_sworn_to (scratch-only).

## Doubts
- RELATIONS.md still has the orphaned `chime_wed_to` row; drop it when merging.
- folio_sworn_to ranges over works and authors (mixed types), as harbour_sworn_to mixes city/country.
- D2's "Could ... fail to be" phrasing departs from "Does it follow that ...?" (per brief).
