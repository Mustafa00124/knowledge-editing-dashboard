# Geography round-2 review (ABox 0013-0016, RBox 0017-0018)

Validator (with `geography.md` + `geography.rbox2.md`, both checks files): **36 files, 0 errors**.
criteria.py: no geography item flagged. Rule 9 holds: RBox direct 3/3, derived 6/6, cross-lingual 6/6. Rule 11 holds at 8/8 ABox. Rule 5 is clean after one added quote.
`in_drainage_basin_of` (`chain:drains_into->in_drainage_basin_of`) is in `relations/geography.rbox2.md`, and its check is in `geography.rbox2.checks.json`.

## Evidence
- **Counts:** I re-ran all 40 infini-gram counts with `--fresh`. None changed (0/40).
  I tried 6 extra phrasings for the derived claims:
  - "Promenade des Anglais in Provence": 1
  - "Promenade des Anglais, Provence": 1
  - "Promenade des Anglais AND Provence": 1388 (approximate). Most of this is Nice's region co-occurring with the Promenade.
  - "Gateway Arch, Missouri": 139
  - "Missouri's Gateway Arch": 19

  The ratings stand: `very_likely` for 0015 and `likely` for 0016.
- **Quotes:** I checked 17 quotes word for word against fresh Wikipedia HTML, plus the enclave definition in the 0018 notes. None failed. I added one new quote (Guam NANP, verified).

## Per record
| Id | Verdict |
| --- | --- |
| replace-0013 | KEEP. Subproperty (Juárez in Texas) and chain (Juárez in the US) both discriminate and are determinate. |
| delete-0013 | FIXED (notes). "Texas State Capitol in Austin" is treated as a form of the deleted fact, forgotten in every world. The by-name worlds hold no "legislature meets in the capital" rule, the same pattern as the Canberra case. |
| replace-0014 | KEEP. Inheritance (Senate seats, electoral votes) is a real class move with constitutional bridges, and the question does not restate the edit. **Doubt answered:** the flag and House worlds are genuine background-belief worlds. Each is "stored by number" vs "reached through the list of states", the by-name/by-description pattern. Both are consistent: 4 USC 2 adds the star only the July 4 after admission, and the House was 437 in 1959-63. |
| delete-0014 | FIXED (queries and worlds). **Doubt confirmed.** The old by-name worlds kept "Guam is not one of the 50 states" or "Guam has no electoral votes". Through "every state has two senators / electoral votes", either fact gives "not a state", and the direct question ("state or territory?") then answers itself, so the delete's direct null failed in 3 of 4 worlds. I replaced the two indeterminate queries with Guam's currency (the US dollar, also used by Palau, the Marshall Islands and Micronesia) and its calling code (+1, also used by Canada and Caribbean states). Their by-name answers say nothing about statehood. Each world now lists "not one of the 50 states" and the by-name senator and electoral-vote facts as forgotten forms of the deleted status. There are still 4 worlds (2x2), and the checks and evidence were updated. |
| replace-0015 | KEEP. **Doubt answered:** w2 (Nice alone in Liguria, an Italian exclave) is valid under decided step 3. Its side facts (department, Riviera, France) are listed. Nice borders neither Monaco nor Italy, so nothing outside the chain breaks. Transitivity via "Liguria is in Italy" discriminates and holds in both worlds. |
| delete-0015 | KEEP. |
| replace-0016 | KEEP. **Doubt answered:** "capital of the Arch's state" is Springfield in both worlds and discriminates (Jefferson City before the edit). It is composition, not a property, and the writer explained this; the 4 properties are covered by 0013-0015. |
| delete-0016 | KEEP. |
| replace/delete-0017 | FIXED (bare statements). The original was a gloss plus an axiom in parentheses. It is now the if-then sentence "If a place lies in the drainage basin of a river and that river drains into a body of water, the place lies in the drainage basin of that body of water." The statement is "A place in the drainage basin of a river need not lie in the drainage basin of the body of water that the river drains into." The delete statement equals the replace original, and the chain steps were updated. It is a genuine two-relation chain that holds for every pair (Vienna/Danube/Black Sea, Lyon/Rhône/Mediterranean). |
| replace/delete-0018 | FIXED (phrasing). "Can X at the same time be...?" became "X is an enclave within Y. Is it consistent with this fact that X is also an enclave within Z?". The answer now rests on the given fact and the property, not on world knowledge that Lesotho does not touch Botswana. In zh, 飞地 + the gloss "被南非完全包围" became 内飞地 with no gloss: the gloss added a geometric fact that rules out Botswana even without functionality. Answers are unchanged, so the balance is kept. "Is an enclave within" is functional by definition (Wikipedia: "only one other state"), with no real exception. |

## Coverage
- transitivity: 0015
- chain: 0013 (capital_of, chain:located_in->located_in)
- subproperty: 0013
- inheritance: 0014 (x2)

Each discriminates and is determinate in every world.

## Remaining doubts
- delete-0014: a model that keeps "Guam belongs to the US" can still reach the status by elimination against the closed list of 50 states. This is a closed-world route, noted in the record. Deleting a two-valued status is inherently leaky; re-pick the edit if that is unacceptable.
- delete-0016 w2 (forgetting "St. Louis, Missouri") is valid but lopsided.
- `has_political_status` and `in_drainage_basin_of` are still scratch-only relations, so they need merging into RELATIONS.md.
