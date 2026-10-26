# Mathematics inserts (insert2): review

The fix went through `math_insert/build.py`, which was then rerun. No JSON was edited by hand. The backup is `math_insert/build.py.before-insert2-review`.

## Result
- **Validator:** 20 files, 0 errors. This used `relations/mathematics.insert2.md`; there is no insert2 checks file.
- **criteria.py:** no mathematics insert is listed under Rules 5, 7, 9, 10, 11 or 13. Rule 8 lists only the scratch relations `has_proof` and `has_series_representation`.

## Tags, mix and ids
The ABox, TBox and RBox mix matches the writer brief's table. I re-checked each tag by hand:

| Ids | Tag | What is made up |
| --- | --- | --- |
| 0001-0002 | `subject` | the subject (Brennick constant, Pellow number) |
| 0003-0004 | `object` | the object (Halvering series, Ellery proof) |
| 0005 | `subject_object` | the Varnick and Ostley groups; `subgroup_of` is real |
| 0006-0007 | `relation` | the relation (vell partner, brace-linked) |
| 0008 | `all` | everything |
| 0009-0010 | `subject` | the subject |
| 0011-0012 | `relation` | the property: Hallam index and Hessler points of a real class, with a real value |
| 0013 | `subject_object` | the Wendrel and Tarvane classes; `subclass_of` is real |
| 0014 | `all` | everything |

No record is tagged subject+relation or relation+object.

**Ids:** every file's `id` matches its file name. No record points to another id.

## Object inserts

**0003, π / Halvering series. KEEP.**
- `has_series_representation` holds many values, and new series for π keep being published, so no real value is overwritten.
- A new series that sums to π contradicts nothing.
- The direct question asks for "the newly found infinite series whose sum is π", so it has one answer.
- `edit.subject` "π" appears once in the direct prompt.
- All four derived queries need the edit: rational, rounded value, circumference, transcendental.
- The near query is Leibniz, π/4, which differs from the new answer.

**0004, Pythagorean theorem / Ellery proof. FIXED.**
- `has_proof` holds many values. Wikipedia says the theorem "has been proved numerous times by many different methods". The direct question has one answer, and the subject appears verbatim once.
- **Problem:** two derived queries gave their answer away.
  - "A right triangle has legs 3 and 4 … hypotenuse?" is answered 5 without the edit.
  - "legs 5, 12, hypotenuse 14?" is answered no without the edit.
  - "named after which ancient Greek thinker?" hinted at its answer.
- **Fix:** the derived queries now name no triangle or hypotenuse:

  | Query | Answer |
  | --- | --- |
  | Which kind of triangle is the theorem that the Ellery proof proves about? | right triangles |
  | Write it as an equation in a, b and c; if a = 8 and b = 15, what is c? | 17 |
  | After whom is it named? | Pythagoras |
  | Do a = 7, b = 24, c = 26 satisfy its equation? | no |

  The bridges are unchanged. The notes were updated.

## Other new and moved records
- **0005, 0013, 0014:** I re-derived the chains: Lagrange; subgroup is a subset; subgroups of cyclic groups are cyclic; transitivity; contrapositive; 3, 9, 15 → 9; at least 3 circles. All hold, and the facts in the prompts are consistent. KEEP.
- **0002, 0006, 0007 (moved):** only `id`, tag and notes changed. KEEP.

## Evidence
**Fresh Dolma counts:** all 0, so none changed. The names checked were:
- Halvering series, Ellery proof, Ellery's proof
- Varnick group, Ostley group, Tennard group
- Wendrel number, Tarvane number(s)
- Ashby polygon, merrow-bound, Quellan circle
- Pellow number, vell partner, brace-linked

"Halvering" alone has 134 hits, from the Dutch/Scandinavian word.

**Web searches** for every new name found no real thing. The near misses were the Oatley Heritage Group, the Wendel investment group, and places named Ashby.

**Wikipedia quotes:** all 10 in 0003, 0004 and 0005 were checked word for word against the live pages (Pi, Pythagorean theorem, Lagrange's theorem, Subgroup, Cyclic group). None failed.

**Far prompts** are used at most 7 times each across the dataset.

## Other change
In `relations/mathematics.insert2.md`, the example for `has_series_representation` was wrong ("π is the sum of the Leibniz series times 4"). It is now "π is the sum of the Nilakantha series."

## Left alone
- Stale RELATIONS.md rows (`thorne_below`, `halm_twinned_with`, `has_talley_weight`, `has_merrow_count`) are left for central cleanup.
- The object inserts have all derived queries determinate, with no worlds. This is the mathematics exemption.
