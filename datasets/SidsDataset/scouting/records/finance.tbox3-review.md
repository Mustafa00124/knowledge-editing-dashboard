# Finance TBox 0019-0020: verifier review

Records: `datasets/SidsDataset/records/finance/{replace,delete}/finance-{replace,delete}-00{19,20}.json`

| Record | Verdict |
| --- | --- |
| finance-replace-0019 | FIXED (notes): "every past one is headquartered in the US" was false. International Nickel / Inco was a Dow component until 1987, and its head office was in Toronto after 1928. The note now says the rule is about today's 30 members (list checked after the June 29, 2026 change: Alphabet in, Honeywell renamed; Coca-Cola and McDonald's still in; all 30 headquartered in the US). |
| finance-delete-0019 | FIXED (same note). |
| finance-replace-0020 | KEEP |
| finance-delete-0020 | FIXED: the null answers could be reached another way. "WAEMU members share one currency" (the union's name says monetary union) plus any member's currency stored by name (Senegal's CFA franc) re-derives the deleted rule. Added a side fact to all 4 worlds saying the shared-currency belief goes with the rule, rewrote the new members' `determinacy_why` (a model answering CFA franc only hid the rule) and added a note. With this, the labels hold: every consistent delete has to cut this route, so the new members stay null in every world. |

## Checks
- **Counts:** all 23 cited counts re-run with `--fresh`. 23/23 identical, 0 changed. Invented members: "Harrowgate Systems", "Pellworth Health" and "Republic of Varanne" have 0 hits. "Saint-Corentin" has 589, but these are a saint and French places, not a state, and nothing gives it a currency.
- **Quotes:** 7/7 found word for word (Wikipedia plain text and the Chase page, with its curly apostrophe). McDonald's infobox claims also confirmed: listed as a Dow component, headquartered in Chicago, U.S.
- **R1:** no current Dow member is headquartered outside the US, so the committee's "judgment" clause is unused. WAEMU still has 8 members and all use the XOF. The AES states have not left the union, and the Eco has not replaced the CFA franc.
- **Leaving the class:** Coca-Cola leaving the Dow is consistent; it was dropped in 1935 and re-added in 1987. McDonald's joined in 1985, so its membership is also contingent. Côte d'Ivoire and Benin leaving WAEMU: Wikipedia itself discusses what happens if a country leaves (it recovers its reserves). Keeping the CFA franc on its own works like Montenegro using the euro. Neither contradicts a firm fact outside the chain, and none of the prompts asserts membership.
- **Logic:** `dl` is right for all 8 derived queries. Delete worlds are re-derived correctly.
- **Repeats:** none (Rule 4). 0019 has the same shape as 0008 (a CAC 40 rule, listed on Euronext) but edits a different fact.
- **Validator:** 22 files checked, 0 errors. No tbox3 relation files exist.

## Remaining doubts
- The worlds are lopsided: each member's own HQ or currency is far better known than its membership.
- Variety is low: both rules use functional relations already used in finance ABox, and neither is property-free. 0019 is close in kind to 0008 (both are stock-index rules).
- The Dow rule rests on a committee guideline, not a hard requirement.
