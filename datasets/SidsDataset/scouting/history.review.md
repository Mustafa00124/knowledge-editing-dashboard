# Critic review: history scouting report

Reviewed `reports/history.md` against `topic_brief.md`, README "Determinacy
and belief-revision problems" and CRITERIA R1/R2. No repository file was
edited. Counts were re-run with `ig.py` (Dolma unless noted). The one web
request (Wikipedia raw wikitext) used the generic User-Agent
"SidsDatasetScout/1.0".

## 0. Evidence re-check

**Reproduced exactly:**

| Query | Count |
|---|---|
| `Battle of Hastings in 1066` | 10,338 |
| `Battle of Hastings` | 83,874 |
| `killed at the Battle of Hastings` | 708 |
| `his death at the Battle of Hastings` | 252 |
| `crowned on Christmas Day 1066` | 134 |
| `Declaration of Independence in Philadelphia` | 1,316 |
| `where the Declaration of Independence was adopted` | 414 |
| `Independence Hall in Philadelphia` | 10,641 |
| `Napoleon died in the Southern Hemisphere` | 0 |
| `Napoleon AND Southern Hemisphere` | 128 |
| `Helena in the South Atlantic` | 2,576 |
| `Napoleon AND St. Helena` | 26,699 |
| `was president when the Wright brothers` | 1 |
| `Roosevelt was president when the Wright` | 0 |
| `McKinley was assassinated in 1901` | 868 |
| `Wright brothers AND McKinley` | 193 |
| `Theodore Roosevelt AND Wright brothers` | 438 |
| `first flight in 1903` | 1,906 |
| `Lincoln was assassinated at Ford's Theatre` | 157 |
| `Ford's Theatre in Washington` | 2,633 |
| `Cook was killed in Hawaii` | 214 |

I also confirmed the snippet descriptions that I sampled. The St James Church snippet ("oldest Anglican church in the Southern Hemisphere … home to Napoleon") is real, and the `Captain Cook AND northern hemisphere` hits are noise (a cruise line, a museum exhibition, a library catalogue). I found no invented counts or quotes.

## 1. Record 0001 (stored) Declaration of Independence → Boston: KEEP (one fix)

- **Stored:** solid. The counts reproduce, and the Wikipedia leads are explicit.
- **Q1, Q2 (determinate):** they hold. For Q2, every remaining route goes Boston → Massachusetts. The scout was right to drop the "Pennsylvania State House" route, as in the README's ACT case.
- **Q3, Q4 (background_beliefs):** the labels hold. The w2 weakness the scout flagged (the Constitution was also adopted at Independence Hall) is real but acceptable.
- **FIX:** the near query "In which city was the 1783 **Treaty of Paris** … signed?" contains its own answer. That is the R2 trap the scout names in its own introduction. Replace it with, for example, "In which city was the US Constitution signed?" That one is too close to the Independence Hall route, so the safer choice is "In which city did the Boston Tea Party take place?" Even safer is an unrelated date or place question, such as "In which year did the Battle of Yorktown end?" (1781).

## 2. Record 0002 (stored) Battle of Hastings → 1067: DROP (or keep only with explicit caveats)

This was your concern (1), and it is the weakest record.

**Is the "relative" world (w2) reasonable?** Yes. Internally it is the *more* coherent world. Harold dies at Hastings in 1067, William is crowned on Christmas Day 1067, and Stamford Bridge falls three weeks before Hastings. The whole cluster shifts by one year. Its cost is that every date-stamped fact in the cluster has to give way. These are stated very often in their own right:
- `Norman Conquest of 1066` = 10,159, about as frequent as `Battle of Hastings in 1066`;
- `Norman conquest in 1066` = 1,924;
- `the year 1066` = 3,919;
- `1066 AND three kings` = 461.

In w2 "the Norman Conquest of 1066" becomes the Conquest of 1067. That is a firmly held fact, and in practice it is close to the same event as the battle.

**The "by date" world (w1) is the one that clashes with firm facts.** If Harold's death (14 Oct 1066) and William's coronation (25 Dec 1066) keep their year while the battle moves to 1067:
- Harold died a year before the battle at which he was killed. So w1 has to drop "Harold was killed at Hastings" (708 + 252 exact; the arrow in the eye), one of the best-known facts in English history.
- William was crowned king two months *before* the battle that won him the crown. That is causally incoherent, not just a different storage choice.

In the README's Eiffel Tower case, the w1 link that gives way ("the tower is in the capital") is weak and descriptive. Here, both the date link and the relational link are strong. So **neither world is consistent with all firmly held facts**. Under step 3 a strict labeller could drop either world, and the labels of Q3 and Q4 would then depend on which firm fact the labeller sacrifices. That is exactly the "when in doubt, leave it out" case the README warns about.

**Root cause:** for an iconic event, the year *is* its identity ("1066"). A year edit fights a dense cluster of facts that are stored by date and also stored relative to the event.

**Other checks:** Q1 and Q2 (148 years before 1215) are fine and determinate. R1 is fine.

**Recommendation:** DROP and promote the Lincoln/Baltimore backup (see §5). If the user wants to keep the record, the w1 summary must say outright that "Harold did not die at Hastings, and William was crowned before the battle". Both `determinacy_why` fields should also flag that w1 sacrifices a firm fact.

## 3. Record 0003 (derived) Napoleon → Northern Hemisphere: KEEP with fixes

**Derived evidence holds.** I tried more phrasings:

| Query | Count | Note |
|---|---|---|
| `Napoleon AND south of the equator` | 32 | Snippets: Napoleon Chagnon, the Seychelles; none relevant. |
| `Napoleon died in the South Atlantic` | 0 | |
| `St Helena is in the southern hemisphere` | 0 | |
| `Napoleon AND hémisphère sud` | 0 | |
| `Napoleon AND hemisferio sur` | 0 | |
| `Napoleon AND South Atlantic` | 3,604 | |
| `Helena AND south of the equator` | 207 | |

- The direct fact is absent, and the premises are frequent.
- As the scout says, "died … in the South Atlantic" (the Wikipedia lead) is only one definitional step away. **`likely` is the right rating, not `very_likely`.**

**Is "hemisphere" a natural relation?** Yes, as a question: "In which hemisphere did Napoleon die?" is a plausible quiz question, and it parallels the README's Space Needle time-zone case (an attribute of a place, reached through location). As an ABox relation it is artificial: nobody states it, which is the point of a derived edit. Prefer a functional `died_in_hemisphere`, or `died_in` with the `located_in` chain tagged. Don't mix the granularity of the `died_in` object.

**Premise-route query (your concern 3): not really distinct.** Q1 asks for "the hemisphere of *the place where Napoleon died*", which is the definition of the direct question "In which hemisphere did Napoleon die?". A model that only patched the conclusion answers both with "Northern", so Q1 exposes nothing. Fixes:
- **Best:** add "Did Napoleon Bonaparte die in the South Atlantic?" as the premise-route query. It is determinate **no**:
  - w1: he died somewhere north of the equator;
  - w2: Saint Helena now lies north of the equator, so it is in the North Atlantic. Keeping it "in the South Atlantic" would contradict the definitional rule.

  It runs through the intermediate that the text actually states (the Wikipedia lead). A conclusion-patching model that stored "died in the South Atlantic" will answer "yes", which is the inconsistency the query is meant to catch.
- **Minimum:** change "the place" to "the island", to mirror the README's "the city the Space Needle stands in". Caveat: in w1 he need not have died on an island, so the question carries a presupposition. That is why the South Atlantic query is the better fix.

**R1 (missed by the scout):** "Napoleon" alone is ambiguous. **Napoleon III died in Chislehurst, England, in the Northern Hemisphere**, so the counterfactual answer is *true* of a namesake. `Napoleon III died` = 166 against `Napoleon Bonaparte died` = 673. Write "Napoleon Bonaparte (Napoleon I)" in every prompt, including zh/es.

**Worlds:**
- w2's `assumes` should say that "Saint Helena is in the South Atlantic" gives way too, not only its latitude.
- A further route the scout did not list: "Napoleon was exiled to Saint Helena" is a separate premise from "he died there". Avoid any query about his *exile* island, because it would split again inside w1.
- Q3 and Q4 are fine: concrete in each world, and they differ.

**Other:** the near query (Gauguin, Hiva Oa, about 9.8°S, Southern) is correct.

## 4. Record 0004 (derived) Wright flight → McKinley: KEEP with fixes

This was your concern (2).

**Does a valid world exist?** Yes, two:
- **w2 (McKinley's death gives way):** coherent. McKinley's second term ran to March 1905, so if he survives (no 1901 assassination), he is lawfully president in December 1903. Roosevelt's succession moves with the assassination. This gives up a firm, frequent fact (`McKinley was assassinated in 1901` = 868), but giving up a firm premise is what a derived edit is meant to force (compare "Seattle observes Pacific Time").
- **w1 (the flight date gives way):** the flight falls between March 1897 and September 1901. This is plausible, because the Wrights were flying gliders at Kitty Hawk in 1900–01.

The scout's worlds are correct, and each one sacrifices only its own premise.

**Premise-route query Q1 ("Did the first powered flight take place after McKinley's death?" → no):** it is right, and it is the best design available here. It holds in both worlds. It forces the model to compare the two premise dates, and a conclusion-patcher reasoning "1903 > 1901" answers "yes" and is caught. The scout's point that "in the year of the flight" is unsafe is also correct.

**Suggested extra or replacement indeterminate query:** "Who was US president on December 17, 1903?" gives w1: Theodore Roosevelt and w2: McKinley. It is concrete, the answers differ, and it is a cleaner `derived_beliefs` query than "Did McKinley die in 1901?" (Q4 is still fine).

**Derived evidence: a weak shortcut exists, so rate it `likely`, not `very_likely`.**
- **A "time-capsule" genre** states both facts together. The snippets are verbatim:
  - "The year Alexander Imich was born, Theodore Roosevelt was president and the Wright brothers piloted their first powered airplane." (`Wright brothers AND Theodore Roosevelt was president` = 7.)
  - "Teddy Roosevelt was president, … The Wright brothers launched their maiden flight at Kitty Hawk" (`Wright brothers AND Roosevelt was president` = 33, partly such lists).
- **Wikipedia "1903 in the United States"** lists "President: Theodore Roosevelt" in its header and "December 17 – Orville Wright flies an aircraft …" in its events, on the same page.

This is still rare compared with the premises (`first flight in 1903` = 1,906; `McKinley was assassinated in 1901` = 868; `Wright brothers` = 154,873), so the record stays derived. The genre is easy to miss, and it will recur for every "ruler at the time of event X" record.

**R1/R2:** fine. The scout's cautions ("Wright brothers' first powered flight", no "Kitty Hawk") are good. The spare query is right: McKinley was born in Niles, Ohio.

## 5. Backups

**Lincoln → Baltimore (stored): KEEP as the replacement for 0002.**
- The counts reproduce.
- R1 note: Lincoln was shot at Ford's Theatre but died at the Petersen House across the street. "Assassinated in Washington" and "shot at Ford's Theatre" are both unambiguous, but never ask "Did Lincoln die at Ford's Theatre?".
- The record is a structural twin of 0001 (a building defined by an event). That is acceptable, but the topic's two stored records then share one template.

**Cook → Southern Hemisphere (derived): KEEP as a backup.**
- The evidence holds. `Kealakekua Bay` = 21,116, and the co-occurrence hits are noise.
- It has the same template, and the same premise-route weakness, as 0003. Fix it the same way: "Was Cook killed in the North Pacific?" is determinate (original yes, new **no** in both worlds).

## 6. Verdict

**FEASIBLE, on the shaky side for stored records. I mostly agree with the scout.**

- **Solid now:** 0001 (after the near-query fix), 0003 and 0004 (after the fixes above), plus Lincoln as the second stored record. **4 records are achievable.**
- **0002 should go.**
- **Stored records** scale only if they avoid year edits on iconic events. Place and agent edits whose background query hangs on an event-defined building do scale (Ford's Theatre, the Texas School Book Depository), but they repeat one template.
- **Derived records** (the hemisphere family and the "ruler at the time" family) are real, and their absence evidence holds. Beyond about 6 to 8 they become repetitive. Each one needs a check for the time-capsule genre and for "YEAR in COUNTRY" pages.

## 7. Systemic lessons

1. **Year edits on iconic events** clash with dense date-stamped clusters ("Norman Conquest of 1066"). Neither the by-date world nor the relative world is clean. Prefer place or agent edits for stored records, or events whose year is not their name.
2. **Premise-route queries for "attribute of the place where …" derivations** collapse into the direct question. Route them through the intermediate that the text actually states (South Atlantic, North Pacific), or through a comparison of the premises (the McKinley-death query).
3. **Ruler-at-event facts** have hidden shortcuts: "the year X was born, Y was president and …" filler text, and Wikipedia "YEAR in COUNTRY" pages. Search for them before rating a record `very_likely`.
4. **Namesakes:** check whether the counterfactual is true of a namesake (Napoleon III died in the north). Use the full name in every prompt.
5. **R2 applies to near and far queries too.** Treaties and battles named after places are traps there as well.
