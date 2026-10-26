# Technology TBox 0019, 0020: verifier review

Validator (technology 0010-0020 files, with the tbox3 relations): 22 files, 0 errors.

## Verdicts
- **replace-0019: FIXED (worlds and notes only).** w1 now lists side facts: MIT leaves the OSI list and the OSD's sense of open source, and stays a permissive license that the FSF treats as free (Expat). w2 now says MIT's commercial-use terms are not reached by name or through "permissive license", and lists the side fact that its own grant ("sell copies") changes with them. Notes add the edit's own side facts: OSD criterion 6, "open-source licenses permit commercial use" and the permissive-license rule change with the rule, so Larchmont and Fennick have no second route. Notes also record the Rule 1 edge cases.
- **delete-0019: FIXED.** Both worlds now list that forgetting the rule takes its restatements with it (OSD criterion 6, "open-source licenses permit commercial use"). Without that, Larchmont, Quarrel and MIT-w2 "does not know" could be reached another way. w2 also excludes the permissive-license route.
- **replace-0020: FIXED (worlds and notes).** w1 side facts: `<img>` leaves the void list, keeps content model "nothing", and the other void elements are unaffected. w2 side facts: HTML 4's "EMPTY, end tag forbidden" goes with the rule. Notes add the scope: the rule belongs to the HTML syntax, while XHTML/XML allows `<br></br>`, and the prompts say "in HTML".
- **delete-0020: FIXED.** Both worlds list that the restatements go with the rule ("self-closing", HTML 4 EMPTY). Notes explain why an empty content model gives no route (`<script src>` and `<iframe>` still take end tags).

## Writer's doubt (0019 w2: MIT forbids commercial use despite "sell copies")
Keep w2, no re-pick:
- The "sell copies" clause is the member's own property, the very fact that gives way in w2. So it is a side fact that changes with it, not a fact outside the chain. This is the same as F#'s type checker in technology-0007.
- Companies using MIT, GPL or Apache code commercially is contradicted by the edit in every world, because GPL and Apache are members too. So it cannot rule out w2 in particular. The popes, photon and Mars cases broke because of the world's premise, not the edit.
- w1 (MIT off the OSI list) breaks nothing outside: MIT-0 has its own separate approval.

## Rule 1 checks
- 0019: OSD criterion 6 bars any field-of-use restriction, and no OSI-approved license is non-commercial. Edge cases:
  - Artistic 1.0 bars "a fee for this Package itself", but allows use in business and commercial aggregate distribution. Rechecked on opensource.org.
  - NPOSL-3.0's "non-profit" refers to the licensor; its grant has no field limit.
- 0020: the rule is exact. WHATWG says "end tags must not be specified for void elements". A stray `</br>` is parser error recovery, not a valid end tag. It holds in the HTML syntax only, which the prompts reflect.

## Evidence
- Counts: all 15 re-run with `--fresh`. 0 changed.
- Quotes: 7 re-fetched (UA SidsDatasetScout/1.0): OSD, WHATWG syntax, the MDN void glossary, the MDN img page (2 quotes), the OSI MIT text and the Wikipedia raw text. Plus the infobox "OSI approved = Yes". 0 failed.

## Other checks
- New members are invented and named with their class in the prompt.
- No prompt asserts a membership that a world denies.
- Logic is dl throughout and correct.
- Near and far queries are fine.
- No R2 leaks.
- No repeat of rules 0005-0008. 0006 (GPL) is nearby but is a different rule.

## Remaining doubts
- The worlds now rest on the assumption that a restatement goes with the rule (OSD, "open-source", "self-closing"). The framework allows this, but a model may hold those restatements separately.
- The direct fact "MIT allows commercial use" is rare as an exact phrase (6). The AND count and the quotes carry it.
