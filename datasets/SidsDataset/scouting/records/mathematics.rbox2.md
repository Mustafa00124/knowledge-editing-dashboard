# Mathematics RBox 0017-0018 (replace + delete)

| Id | Property | Original (positive) | Replace edit | Direct / cl / derived new answers (replace) | Logic |
| --- | --- | --- | --- | --- | --- |
| 0017 | role chain | `perpendicular_to_in_plane ∘ parallel_to ⊑ perpendicular_to_in_plane` | same composition ⊑ `parallel_to` | yes / yes, sí / yes, yes (originals no) | dl |
| 0018 | functional | `Func(has_successor)` | `¬Func(has_successor)` | no / 否, no / no, no (originals yes) | dl |

Deletes remove the original property; every new_answer null. Delete-0017's
direct, cross-lingual and derived queries are rephrased around the original
("perpendicular to line c"); delete-0018 keeps the replace prompts (they
already ask about the original property).

Derived queries:
- 0017: "Line a ⊥ line b, and b ∥ c, all three in one plane. Does it follow that a ∥ c?"; "x-axis ⊥ y-axis, y-axis ∥ x = 5. Does it follow that the x-axis ∥ x = 5?"
- 0018: "The successor of 7 is 8. Does it follow that 9 is not the successor of 7?"; "The successor of 41 is 42, and the successor of 41 is n. Does it follow that n is 42?"

Rule 9 (mathematics RBox replace, 0009-0012 + 0017-0018): direct 3/3,
derived 6/6, cross-lingual 6/6; criteria.py overall B2 ok.

## Why each original holds without exception
- 0017: in the Euclidean plane, if a ⊥ b and b ∥ c then a ⊥ c (corresponding
  angles). Two different relations, so a chain, not transitivity. Every
  prompt says "in the same plane": in space, under the convention that
  perpendicular lines must intersect, a and c can be skew.
- 0018: the successor of a whole number n is n + 1 (Peano's successor
  function), exactly one value. Prompts say "whole number" because in a
  partial order an element can have several immediate successors.

## Relations (in mathematics.rbox2.md / .rbox2.checks.json)
New: `perpendicular_to_in_plane` (`symmetric`, `cardinality:many`,
`chain:parallel_to->perpendicular_to_in_plane`), `parallel_to` (`symmetric`,
`cardinality:many`), `has_successor` (`functional`, `asymmetric`), each tag
with a check. A new relation was used instead of the shared `perpendicular_to`
because adding a chain tag to it would conflict with its shared tags (and
the chain needs the plane restriction).

## Locality
- 0017 near: characteristic ∘ normal ⊑ normal subgroup chain (yes); far: "Is 'is a cousin of' symmetric?" (yes, new prompt).
- 0018 near: "Can a real number have two different absolute values?" (no); far: "Is 'is a grandparent of' transitive?" (no, new prompt).

## Doubts
- 0017's replace originals are "no" because the original chain gives a ⊥ c,
  which excludes a ∥ c; a model might read "does it follow" narrowly, but the
  answer is no either way.
- 0018 instance conclusions are true arithmetic facts regardless of the given
  premise (as in 0009); the second query uses a variable n to lessen that.
- The relations exist only in my scratch file until merged into RELATIONS.md;
  criteria.py lists them as unknown until then.

Validator: 4 files, 0 errors (with both mathematics extra relation files).
