# people: records review (verifier)

Validator with the extra relation files: 24 files, 0 errors. criteria.py B7 row for people: 4/4 per box, 2 stored + 2 derived, 32 determinate / 24 background / 8 derived (unchanged). R6 ok. (B6's 12x "is married to symmetric?" far prompt is not from this topic.)

## Evidence

- Counts: all 74 distinct infini-gram counts cited by the writer re-run with `--fresh` (`scratchpad/people_verify/fresh.jsonl`): **0 changed**, no zero/non-zero flips.
- 32 new verifier searches (`people_verify/extra.jsonl`); samples read for the ones relied on.
- Quotes: all 20 distinct Wikipedia quotes re-fetched fresh (API extracts, `people_verify/wiki/`): **0 failed**. 3 new quotes (Rhodes Scholarship, Bill Clinton, Bob Hawke) were checked the same way.

## Per record (replace and its delete)

| Id | Verdict | What |
| --- | --- | --- |
| 0001 | KEEP (delete FIXED) | Description worlds formally valid, improbable (Decision 4). Delete notes were copied from the replace and mentioned Langevin; rewritten. |
| 0002 | KEEP (delete FIXED) | Same as 0001 for the delete notes. Delete's river query: the "Bard of Avon" route is borderline; noted. |
| 0003 | FIXED | Rating `likely` holds when searched from Joseph P. Kennedy Sr.'s end too: "granddaughter of Joseph (P.) Kennedy" 6/11, "Joe Kennedy's granddaughter" 2, "granddaughter of Joe Kennedy" 4, "her grandfather Joe/Joseph Kennedy" 4-5; samples are about Maria Shriver and other grandchildren. His Wikipedia article never names Caroline (re-checked). 11 searches added to the evidence. Worlds kept, with side facts spelled out in notes. Delete notes rewritten. |
| 0004 | FIXED | Rating `likely` holds: "buried in Auvers-sur-Oise, France" 1, "buried in Auvers, France" 0, RPJ "Van Gogh AND buried in France" 0; "French village of Auvers" (199) is about the revolver and his last months, not the grave. P1 is moderate (RPJ 73, "where Van Gogh is buried" 49, "Van Gogh's grave" 43). Evidence added. w2 kept with its side facts made explicit (out of Val-d'Oise, away from Pontoise/Paris); these are facts about the village, not other places or people. Delete notes rewritten. |
| 0005 | REPLACED | Pope/Bishop of Rome dropped: in the world where membership gives way, Gregory I and Leo I stop being popes. That clashes with facts about other people (papal succession; the regnal numbers Gregory II-XVI and Leo II-XIV count them). This is the same reason the writer dropped the Victoria draft. New rule: every Rhodes Scholar studies at Oxford -> Cambridge (relation `educated_in`). New members: 2 fictional scholars. Well-known members: Bill Clinton and Bob Hawke, asked "Which university did X attend in England?" (one answer each, membership not in the prompt). 4 worlds, evidence and checks, delete redone. |
| 0006 | KEEP (delete FIXED) | Bolt and Owens leaving the class is lopsided but forces nothing on other people. Delete `determinacy_why` said members "stop being" winners (wrong under delete); removed. Notes rewritten. |
| 0007 | KEEP (delete FIXED) | R1 checked: the qualifications (age, citizenship) are met by every life peer created. Supreme Court justices are barred and peers can retire since 2014, but neither applies to the original entitlement or to Thatcher or Olivier. w2 for Thatcher (she left the Commons in 1992, then sits there as a peer) is strained but consistent. Delete fixes as in 0006. |
| 0008 | FIXED | Well-known prompts said "received for winning the 1997/1963 Masters", which states the membership that w1 denies. Changed to "received at the ... Masters" (replace and delete). Delete fixes as in 0006. |
| 0009 | FIXED | Near query "Is 'is a descendant of' transitive?" is moved by the edit (the inverse of a non-transitive relation is not transitive). Replaced by "Is 'is an ancestor of' asymmetric?" (yes) in both records. |
| 0010 | KEEP | Delete notes trimmed. |
| 0011 | KEEP | Delete notes trimmed. |
| 0012 | FIXED | Near query answer (yes) equalled the new direct answer (yes). Replaced by "Is 'is a parent of' symmetric?" (no) in both records. |

RBox: all originals are positive; "Does it follow" answers checked against only the prompt facts and the edited property. Logic labels: all `dl`, correct. zh/es prompts give nothing away (卡罗琳·肯尼迪的祖父 is unambiguously paternal).

## Remaining doubts

- 0003: read strictly ("brother" means full brother), both premises are over-determined by sibling facts in each world. This is the README's own Henry VII example's weakness; kept under Decision 1 as side facts.
- 0004: w2 moves a commune firmly placed near Paris; valid only because those are facts about the village itself. P1 may fail the check on small models.
- 0005 (new): Clinton's honorary Oxford DCL (1994) survives in every world; the question asks where he studied. The additive world (studied at both) is excluded only by the single-answer phrasing.
- TBox w1 worlds (Bolt, Woods, Thatcher no longer members) are lopsided by design (tarantula pattern).
- The builder scripts in `scratchpad/people/` are now stale: they would regenerate the old 0005 and undo these fixes. The JSON in the repo is the source of truth.
