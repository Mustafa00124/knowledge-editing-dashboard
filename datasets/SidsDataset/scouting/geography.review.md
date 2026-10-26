# Geography: critic's review of the scouting report

**Verdict: FEASIBLE (agree with the scout), but 3 of the 4 chosen records need
fixes before they are written.** The evidence mostly reproduces. The problems
are in labels and wording, not in supply: two background queries collide with
real homonyms (NSW Parliament House in Sydney, Parliament Hill in London), the
US-embassy query is contaminated by a common "US embassy in Sydney" usage, the
scout's fallback (High Court) is worse, and both time-zone records state their
"city gives way" world too narrowly for README step 3.

Method. All counts below are Dolma (`v4_dolma-v1_7_llama`) via the shared
`ig.py`. Note: `ig.py` caches, so re-running the scout's exact queries returns
the cached numbers (they matched exactly); that confirms the report copied
them correctly but is not an independent re-query. Every query not in the
scout's table was a fresh call. Wikipedia quotes were checked in the scout's
saved extracts (`{SCRATCH}/geo/wiki/`), and raw wikitext of en *Space Needle*,
es *Space Needle*, de *Brandenburger Tor*, en *Seattle* and en *Pacific Time
Zone* was fetched fresh.

---

## 1. Evidence check

Reproduced (identical): "Canberra is the capital of Australia" 807; "Ottawa is
the capital of Canada" 1,313; "Parliament House in Canberra" 21,183; "United
States Embassy AND Canberra" 497; "Space Needle in Seattle" 6,159; "Seattle is
in the Pacific Time Zone" 9; "Seattle AND Pacific Time" 5,686; "Brandenburg
Gate in Berlin" 8,358; "Brandenburg Gate AND Central European Time" 15; "Space
Needle AND Pacific Time" 33; "Space Needle AND Central Time" 10.

Quotes confirmed verbatim in the saved extracts: Rideau Hall ("Located in
Ottawa, the capital of the country"), US Embassy Canberra ("one of the largest
embassies in the Australian capital Canberra"), Canberra ("hosts all foreign
embassies in Australia"), Parliament House ("Located in Canberra, Parliament
House is situated ..."). Space Needle (en, es) and Brandenburger Tor (de)
wikitext contain no time zone. Seattle's article has the zone only in the
infobox (`time_zone = PST`), no prose sentence: the scout is right.

**Not reproduced:** "Space Needle AND PST" is listed as 412 (old run); the
fixed helper gives **16** (approx). It only strengthens "derived", but the
table should be corrected.

---

## 2. Per record

### geography-0001 Australia: Canberra -> Sydney. **FIX**

Stored: holds (807 / 769 exact, Wikipedia first sentences). Determinate #1, #2
hold; #2 is the README's own ACT example.

**#3 Parliament House: wording collides with NSW Parliament House.**
"Parliament House in Sydney" 1,384 and "Parliament House, Sydney" 1,318;
sampled snippets are all the NSW Parliament on Macquarie Street ("lobbied the
NSW government at Parliament House in Sydney"). The prompt says "Australia's
Parliament House", so the original answer is clear, but a post-edit "Sydney"
cannot be told apart from a model naming the NSW building. Fix: "In which city
does the federal Parliament of Australia sit?" (still Canberra / Sydney per
world). Keep it; it is the README's flagship example.

**#4 US Embassy: contaminated.** "US embassy in Sydney" 35 exact, and the
samples are real usage for the Consulate-General ("marched on the US embassy
in Sydney", "contact the US embassy in Sydney and apply for a visa");
"US Consulate in Sydney" 238, "consulate in Sydney" 2,177. So (a) some
unedited models may already answer Sydney (R4 / R1 risk), and (b) after the
edit, "Sydney" does not cleanly signal w2/w3. "US embassy in Canberra" 734 is
much stronger, so it is not fatal, but it is noisy.

The scout's fallback is worse: Wikipedia *High Court of Australia*: sittings
"previously rotated between state capitals, particularly Melbourne and
Sydney, and the court continues to regularly sit outside Canberra". Drop the
High Court idea.

Fix options for #4, in order:
1. "In which city are the foreign embassies in Australia located?" By name:
   Canberra (stored: "It hosts all foreign embassies in Australia"); by rule
   ("embassies are in the capital"): Sydney. Consulates are not embassies, and
   no single country's consulate is invoked.
2. "In which city is the Australian War Memorial?" ("Australian War Memorial
   in Canberra" 7,015). Weaker "in the capital" route, but no Sydney homonym.

Worlds w1-w4 are otherwise coherent.

### geography-0002 Canada: Ottawa -> Toronto. **FIX (small)**

Stored: holds (1,313 / 853; Wikipedia). #1 determinate. #2 ("Does the capital
lie on Lake Ontario?") holds: "Toronto is on Lake Ontario" exact is only 28,
but co-occurrence is 58k and Wikipedia states it. The dropped Ottawa River
route is real ("Ottawa River AND capital of Canada" 1,228), and dropping it is
correct under step 3.

**#3 Parliament Hill is ambiguous unqualified.** "Parliament Hill in London"
271; "Parliament Hill AND Hampstead" 13,938. "In which city is Parliament
Hill?" has two defensible originals (R1). Fix: "In which city is Canada's
Parliament Hill?" ("Canada's Parliament Hill" 248) or "Where does the
Parliament of Canada sit?". #4 Rideau Hall is fine (the "Rideau" hint is not
the answer). Add w4 explicitly so the worlds are symmetric.

### geography-0003 Space Needle: Pacific -> Central. **FIX**

**Derived holds.** Extra phrasings all near-absent: "Space Needle AND Pacific
Time Zone" 5 (the one relevant sample is a Seattle fact page, "Seattle is in
the Pacific Time Zone", i.e. the premise, not the Needle); "AND Pacific
Daylight Time" 3; "AND PDT" 30; "AND PST" 16; "what time zone is the Space
Needle" 0; no zone in en/es Wikipedia. Versus 229,543 mentions of the subject
and 6,159 "Space Needle in Seattle". Clean.

**Question (2): is "Seattle observes Pacific Time" stated very often?**
Not literally. Declaratives are rare: "Seattle is in the Pacific Time Zone" 9,
"Seattle is on Pacific Time" 1, "Seattle time zone" 62, "time zone in
Seattle" 10, "Seattle (PST)" 14. Co-occurrence is large but implicit
("Seattle AND Pacific Time Zone" 1,871, samples are NFL schedules;
"Seattle AND Pacific Standard Time" 642; "Seattle, WA AND Pacific Time" 234).
Wikipedia: Seattle infobox only, plus the *Pacific Time Zone* article, which
lists **Washington** among the states wholly in the zone. So the premise is
certainly known, but much of the support goes through a *second route*:
Seattle is in Washington (ubiquitous) + Washington is on Pacific Time (a
Wikipedia list entry; "Washington is in the Pacific Time Zone" 4,
"Washington State AND Pacific Time Zone" 67) + the West Coast is on Pacific
Time ("West Coast AND Pacific Time" 2,367; the zone is named for it). Accept
it as a premise, but the report should say the premise is itself
over-determined. That is what causes issue (1).

**Question (1): does w2 ("Seattle observes Central Time") contradict firm
facts?** Yes, as written. Seattle's zone has the second route above. Apply
README step 3 to w2: "Seattle is in Washington" and "Washington lies wholly in
Pacific Time" both survive the edit, so Seattle-alone-on-Central contradicts
them. **w2 as written is not a valid world.** Three repairs were considered:
- Seattle leaves Washington: contradicts "Seattle, Washington", which is
  extremely firm. Not a world.
- Seattle is a Central exception inside Washington: contradicts
  "Washington is wholly Pacific". Not a world (same reason the scout excluded
  the landmark-exception world).
- **Washington state as a whole observes Central Time** (Seattle with it):
  gives up "Washington is on Pacific Time", the weakest of the three, and
  is not contradicted by anything the record asks. It is odd (a Central
  island on the coast), but no firmer than what w1 gives up (Needle outside
  Seattle, against Seattle Center and the 1962 World's Fair) or what the
  README's Elizabeth I example gives up. This is valid under step 3.

So the record survives, but **w2 must be restated**: assumes "Washington
state, including Seattle, observes Central Time; Seattle is still in
Washington". Queries #1, #3, #4 keep their answers (Central / Central in w2 /
yes in w2). Do NOT add queries on Washington's zone, on "Is Seattle in
Washington?" or on "Is the West Coast on Pacific Time?": each reopens a
cascade the worlds don't fix. Put the "minimal revision" choice in `notes`.

**#2 (Space Needle vs Golden Gate Bridge) is fragile under the cascade.** If
a model revises at the level of the West Coast / Pacific Northwest rather than
Washington alone, San Francisco can move too and the answer becomes "yes".
Minimal change excludes that, but a sturdier determinate query compares with
an untouched landmark in the **new** zone: "Are the Space Needle and the
Willis Tower in the same time zone?" (original no, new yes). No revision
pushed by this edit can move Chicago out of Central. (Avoid the Gateway Arch
here since it is the derived backup.)

Labels otherwise hold: #1 premise-route is Central in every remaining world;
#3, #4 concrete and different across w1/w2. R1 (DST bill) and R2 fine.

### geography-0004 Brandenburg Gate: CET -> EET. **FIX**

**Derived holds.** "Brandenburg Gate AND CEST" 13, "AND UTC+1" 2,
"Brandenburger Tor AND MEZ" 0, "Brandenburger Tor AND Mitteleuropäische
Zeit" 0; de Wikipedia has no zone. Samples for the CET co-occurrence are
itineraries and a clock-change page, as the scout says.

**Premise** "Berlin observes CET": declaratives rare ("Berlin is in the
Central European" 4, "Berlin time zone" 168) but "Berlin AND CET" 20,532,
"Berlin AND Central European Summer Time" 754, infobox. As with Seattle, the
stronger support is national: "Germany AND CET" 33,467, "Germany is in the
Central European Time Zone" 21, and Germany has one legal time.

**Same w2 problem.** "Berlin observes EET" alone contradicts "Germany observes
CET" + "Berlin is in Germany". Restate w2 as "Germany, including Berlin,
observes EET". That is actually a milder revision than Washington's (a
country choosing its zone is ordinary). The scout already left out the
Germany query; keep it out. #2 with the Eiffel Tower is sturdy enough (France
is not dragged by a German revision); "the Acropolis" (Athens, EET; new yes)
is the cascade-proof alternative. Plausibility of EET for Berlin: moderate,
acceptable.

### Backup stored: Brazil, Brasília -> Rio. **KEEP as backup** (counts not
re-run). Note: the counterfactual was true before 1960, so it is "clearly
false" today but historically loaded; a judge must not treat "Rio" as an
acceptable *original* answer. The Congress / Planalto worlds are coherent.

### Backup derived: Gateway Arch, Central -> Eastern. **KEEP as backup, same
w2 fix.** "Gateway Arch AND Central Time Zone" 5; "St. Louis AND Central
Time" 1,771. St. Louis's zone also runs through Missouri (wholly Central), so
w2 must be "Missouri, including St. Louis, observes Eastern". Plausible
(eastern edge of the Central zone).

---

## 3. Topic verdict

**FEASIBLE.** Solid records after fixes: 0001 (rewording #3, replacing #4),
0002 (qualify Parliament Hill), 0003 and 0004 (restate w2; preferably swap
#2's comparator). None needs to be dropped; both backups are usable. Finding
4 good records is easy; scaling is easy in count (capitals, landmark time
zones) but poor in variety, as the scout says, and every time-zone record will
need the same state/country-level w2.

## 4. Systemic lessons

1. **Premises are over-determined.** "City observes zone Z" is backed by
   "city in state/country" + "state/country observes Z". A world where the
   city alone gives way violates step 3; worlds must name the minimal
   *consistent* revision (state/country-wide), and queries must not probe the
   higher level. Expect the same for any "landmark -> city -> region" chain.
2. **"Same X?" determinate queries: compare against the new value.** A
   comparator in the old value's class can be dragged along by a cascade; one
   in the new value's class cannot.
3. **Check homonyms of bridge entities against the new value.** Run
   "<bridge entity> in <new value>": Parliament House in Sydney (1,384), US
   embassy in Sydney (35), Parliament Hill in London (271). A high count means
   the new-world answer is pre-contaminated or the original is ambiguous.
4. **"Stated very often" for zone premises is implicit** (infoboxes, lists,
   schedules); reviewers should accept it, but should count the higher-level
   statement too.
5. `ig.py` caches: re-checks of the same string are not independent; use
   paraphrases to get fresh evidence.
