# Mathematics: RBox insert chaining a made-up relation through real knowledge

## What was replaced and why
`mathematics-insert-0016` ('Has Tolland root' is functional) was replaced (same id, tag `relation`).
It was the weakest of 0015-0017: its cross-lingual queries and first derived query asked a "no"
that held either way (discriminates: false), so 3 of its 5 answered instance/translation queries
measured nothing. 0015 (symmetric, cross-lingual on a discriminating "yes") and 0017 (subproperty)
are kept. The new record matches 0016's yes/no pattern (direct no, zh/es no, d1 no, d2 yes), so
Rule 9 is unchanged; unlike before, every one of those "no" answers now discriminates.

Made in the builder: `math_insert/build.py` (new `CHAIN_BRIDGE`, `rbox_chain()`, record 16;
backup `math_insert/build.py.before-chain`). A rebuild into a scratch dir reproduced the other 19
records byte for byte; only 0016 differs, and that output was copied into the records dir.

## The chain
- Edit: "If a number is cairn-linked to a second number, and the second number divides a third
  number, then the first number is cairn-linked to the third."
- Axiom: `cairn_linked_to ∘ divides ⊑ cairn_linked_to` (`divides` is real, in RELATIONS.md).
- Direct: "If a number is 'cairn-linked to' a second number that divides a third, could the first
  number fail to be linked in the same way to the third?" -> no.
- d1: "5 is cairn-linked to 6. Could 5 fail to be cairn-linked to 12?" -> no (pre-edit: yes, it
  could; so it discriminates). Bridge "6 divides 12." (stored), not in prompt.
- d2: "7 is cairn-linked to 3. Does it follow that 7 is cairn-linked to 9?" -> yes. Bridge
  "3 divides 9." (stored), not in prompt.
- zh/es: d1 without the hop (否 / no).
- Near: characteristic subgroup ∘ normal subgroup ⊑ normal subgroup (yes; differs from direct no).
- Far: "Is the relation 'borders' symmetric?" (now 5 uses dataset-wide, limit 10).

## Bridges (checks + stored evidence)
- "6 divides 12." Wikipedia 12_(number), lead: "is divisible by the numbers from 1 to 4, and 6"
  (re-fetched 2026-10-26; infobox divisors 1, 2, 3, 4, 6, 12). Dolma "6 divides 12" = 41.
- "3 divides 9." Dolma "3 divides 9" = 142 (infobox of Wikipedia "9" lists divisors 1, 3, 9).

## Name
- "cairn-linked": Dolma 0 ("cairn-linked to" 0); web search "cairn-linked": no use (cairn
  monuments, Cairn Toul, an Irish builder). Not in RELATIONS.md or any scratch relation file.
  Rejected: "sedge-bound" (Dolma 2, kept clear), "weir-tied" (0, not used).

## Relations
`relations/mathematics.chain.md` (cairn_linked_to, fictional, `chain:divides->cairn_linked_to`,
`cardinality:many`) and `relations/mathematics.chain.checks.json`.

## Validation
validate.py with the chain relation files: 20 files, 0 errors. criteria.py: "Each topic has an
RBox insert chaining a made-up relation through real knowledge" [ok]; Rules 5, 7, 9, 10 ok and no
mathematics insert under Rule 13; Rule 8 lists cairn_linked_to (scratch-only, expected).

## Doubts
- "6 divides 12" has a count under 100; it rests on the Wikipedia quote, which states it via
  "divisible by ... 6". Small divisibility facts may be computed rather than recalled, which is
  still the model's own knowledge, not the prompt.
- The topic's RBox inserts lose their only functional property (no rule requires it on inserts).
