# Biology: RBox chain insert through real knowledge

## What was replaced and why
`biology-insert-0017` (relation) was `quessel_bound_to ∘ lives_in ⊑ lives_in`
with both instance facts in the prompt. Reworking it to leave the real hop
out was weak: the habitat facts ("the white-tailed deer lives in the forests
of eastern North America", "the whale shark lives in tropical oceans") are
vague, not crisp stored facts, and the conclusion was a REAL `lives_in` fact
(deer ticks do live there), so "yes" held without the edit. Replaced (same
id, tag `relation`) with a chain whose conclusion is the made-up relation
and whose real hop is crisp taxonomy.

## The chain
- Edit: "If an organism is varrish-bound to a species, and that species
  belongs to a genus, then the organism is varrish-bound to that genus."
- Axiom: `varrish_bound_to ∘ in_genus ⊑ varrish_bound_to` (in_genus is real,
  in RELATIONS.md, functional).
- Direct (no): "If an organism 'is varrish-bound to' a species, ... can the
  organism fail to be bound in the same way to that genus?"
- Derived 1 (yes): "The oxpecker is varrish-bound to the lion. Does it follow
  that the oxpecker is varrish-bound to the genus Panthera?"
- Derived 2 (no): "The deer tick is varrish-bound to the gray wolf. Could the
  deer tick fail to be varrish-bound to the genus Canis?" (without the edit it
  could; discriminating.)
- zh/es: derived 1, hop left out (豹属 / género Panthera).
- Near and far locality kept from the old record (born_in chain; sibling
  transitivity). Yes/no pattern same as before (direct no; derived yes/no;
  cross-lingual yes), Rule 9 ok.

## Bridges (stored, bridge_in_prompt false, checked)
| Fact | Check | Evidence (Dolma) |
| --- | --- | --- |
| The lion belongs to the genus Panthera. | Which genus does the lion belong to? → Panthera | "lion (Panthera leo)" 3671, "Panthera leo" 15249, "genus Panthera" 6757; Wikipedia Lion: "The lion (Panthera leo) is a large cat of the genus Panthera" |
| The gray wolf belongs to the genus Canis. | Which genus does the gray wolf belong to? → Canis | "gray wolf (Canis lupus)" 2411, "Canis lupus" 38246, "genus Canis" 5481; Wikipedia Canis: "...includes multiple extant species, such as wolves, dogs, coyotes, and golden jackals." |

## Name
`varrish-bound`: Dolma 0, RedPajama 0; "varrish" 1, "Varrish" 85 (stem only).
Web search "varrish-bound" (2026-10-26): nothing (varnish, Varish village,
SCIP varbound). Not in RELATIONS.md or any scratch relation file.

## Validation
validate.py with biology.chain.md/.checks.json: 20 files, 0 errors.
criteria.py: biology passes the chain criterion; no biology insert under
Rules 5, 7, 9, 10, 13. Rule 8 lists varrish_bound_to (scratch-only).

## Notes / doubts
- Edited JSON directly; `bio_ins/gen.py` is stale for 0017 (still writes
  the quessel version). Backup of the old record:
  `bio_ins/biology-insert-0017.pre-chain.json`; writer script
  `bio_ins/write_chain_0017.py`.
- RELATIONS.md rows `quessel_bound_to` (and possibly `lives_in`) are now
  unused by inserts; `quessel-bound` is still mentioned in 0018's search note
  (harmless). Merge should drop/keep them as wanted.
- biology-replace-0018 edits in_genus functionality; the insert does not
  depend on it (the bridges are single-genus facts either way).
