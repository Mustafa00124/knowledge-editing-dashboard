# Geography: scouting report (determinacy edition)

**Verdict: FEASIBLE.** Geography is close to the ideal topic for this design.
Stored facts with a clean background-beliefs split are easy to find (national
capitals: things "in the capital"). Derived facts are easy too: the time zone of
a landmark is almost never written down, while "landmark is in city X" and
"city X observes zone Z" are everywhere. Both supplied candidates survive the
evidence check and are kept. The hardest part was not finding candidates but
(a) proving the time-zone *premises* are "stated very often" (exact sentences
like "Seattle is in the Pacific Time Zone" are rare; the knowledge is carried by
schedules, infoboxes and travel pages), and (b) avoiding derived edits whose
combining rule has real-world exceptions (side of the road, see Rejected).

Supply: capital edits alone give 10+ more stored records (Brazil, Turkey,
USA, Nigeria, Myanmar, Kazakhstan...); landmark time zones give 10+ more derived
records (Gateway Arch, Alamo, Hollywood Sign, Big Ben, Sagrada Familia...). The
limit is variety, not supply: most stored records will be capitals and most
derived ones time zones unless other relations are pushed.

Tools: infini-gram via the shared helper (`ig.py`), default index Dolma
(`v4_dolma-v1_7_llama`), some repeated on RedPajama (`v4_rpj_llama_s4`);
Wikipedia plain-text extracts and raw wikitext (infoboxes) fetched with curl.
**Correction (applied throughout):** the first runs of `A AND B` queries used
the API's default clause-frequency limit and gave false zeros/undercounts. All
AND queries were re-run with the fixed helper (`max_clause_freq=500000`) and the
numbers below are the corrected ones. Exact-phrase counts were unaffected. No
direct-form search is literally zero any more; the "absent" claims rest on
reading the sampled snippets, which are incidental co-occurrences (timestamps,
travel itineraries), not statements of the fact.

---

## Chosen records

| Id | Edit | Kind | Relation | Derivability |
| --- | --- | --- | --- | --- |
| geography-0001 | capital of Australia: Canberra -> Sydney | stored | `has_capital` | very_unlikely |
| geography-0002 | capital of Canada: Ottawa -> Toronto | stored | `has_capital` | very_unlikely |
| geography-0003 | Space Needle time zone: Pacific -> Central | derived | `in_time_zone` | very_likely |
| geography-0004 | Brandenburg Gate time zone: Central European -> Eastern European | derived | `in_time_zone` | very_likely |
| backup stored | capital of Brazil: Brasília -> Rio de Janeiro | stored | `has_capital` | very_unlikely |
| backup derived | Gateway Arch time zone: Central -> Eastern | derived | `in_time_zone` | very_likely |

---

## geography-0001: The capital of Australia is Sydney (orig. Canberra) [supplied candidate: KEEP]

**Edit:** `has_capital(Australia, Canberra -> Sydney)`. Derivability
`very_unlikely`: stated everywhere, follows from nothing. Plausible (the most
common capital misconception; "Sydney is the capital of Australia" itself
appears 302 times in Dolma) and clearly false.

**Evidence the edited fact is stored**

| Phrase | Dolma | RedPajama |
| --- | --- | --- |
| "Canberra is the capital of Australia" | 807 | 343 |
| "capital of Australia is Canberra" | 769 | - |

Wikipedia, *Canberra* (https://en.wikipedia.org/wiki/Canberra), first
sentence: "Canberra ... is the capital city of Australia". Wikipedia,
*Australia* (https://en.wikipedia.org/wiki/Australia): "Canberra is the
nation's capital, while its most populous cities are Sydney and Melbourne".

**Bridge facts**

| Fact | Evidence |
| --- | --- |
| Parliament House is in Canberra | "Parliament House in Canberra" 21,183 (Dolma). Wikipedia *Parliament House, Canberra*: "Located in Canberra, Parliament House is situated at the southern apex of the National Triangle atop and beneath Capital Hill". |
| Foreign embassies are in Canberra / the US Embassy is in Canberra | "embassy in Canberra" 7,744; "United States Embassy AND Canberra" 497 (Dolma). Wikipedia *Canberra*: "It hosts all foreign embassies in Australia". Wikipedia *Embassy of the United States, Canberra*: "one of the largest embassies in the Australian capital Canberra, located in ... Yarralumla" (states it both by name and as "the Australian capital"). |
| Sydney is in New South Wales | "Sydney AND New South Wales" 1.32 M (Dolma, approx; old run, may be an undercount). Wikipedia *Sydney*: "Sydney is the capital of the state of New South Wales". |
| Embassies are in a country's capital (general rule) | Common knowledge; the *Canberra* sentence above is an instance. |

**Routes and worlds.** The two indeterminate queries each have a by-name route
(stays in Canberra) and a through-the-capital route (moves to Sydney). The
embassy query's second route is a general rule ("embassies are in the
capital"), which a model is more likely to use than storing Parliament House
as "in the capital"; so all four combinations are reasonable.

| World | Assumes | Summary |
| --- | --- | --- |
| w1 | Parliament House is in Canberra; the US Embassy is in Canberra (both by name). | The capital moves; Parliament and the embassies stay in Canberra, which is no longer the capital. |
| w2 | Parliament House is in the capital of Australia; embassies are in the capital. | Parliament and the embassies move with the capital to Sydney. |
| w3 | Parliament House is in Canberra (by name); embassies are in the capital (rule). | Parliament stays in Canberra; the US Embassy is in Sydney. |
| w4 | Parliament House is in the capital; the US Embassy is in Canberra (by name). | Parliament moves to Sydney; the embassy stays in Canberra. |

Dropped route: "the capital of Australia is in the Australian Capital
Territory" (stored description) would put Sydney in the ACT, contradicting
"Sydney is in New South Wales"; not a world.

**Derived queries**

| # | Prompt | Label | Original | New / per world | Chain |
| --- | --- | --- | --- | --- | --- |
| 1 | Is Canberra the capital of Australia? | determinate | yes | no | functional: capital is Sydney (edit), so not Canberra. |
| 2 | In which state or territory is the capital of Australia? | determinate | Australian Capital Territory | New South Wales | capital is Sydney (edit); Sydney is in NSW (bridge). ACT route dropped (above). |
| 3 | In which city is Australia's Parliament House? | background_beliefs | Canberra | w1 Canberra, w2 Sydney, w3 Canberra, w4 Sydney | w1/w3: Parliament House is in Canberra (stored). w2/w4: Parliament House is in the capital (stored) + capital is Sydney (edit). |
| 4 | In which city is the United States Embassy to Australia? | background_beliefs | Canberra | w1 Canberra, w2 Sydney, w3 Sydney, w4 Canberra | w1/w4: US Embassy is in Canberra (stored). w2/w3: embassies are in the capital (rule) + capital is Sydney (edit). |

**Other queries (sketch)**
- Direct: "What is the capital of Australia?" -> Sydney
- Paraphrase: "Which city serves as Australia's capital?"
- zh: 澳大利亚的首都是哪个城市？ es: ¿Cuál es la capital de Australia?
- Near: "What is the capital of New Zealand?" (Wellington)
- Far: "Into which sea does the Danube flow?" (Black Sea)

**Self-check**
- Determinate answers same in every world: #1 no in w1-w4; #2 NSW in w1-w4. OK.
- Indeterminate: #3 {Canberra, Sydney}, #4 {Canberra, Sydney}, concrete. OK.
- Worlds consistent with firm facts: yes. w2/w4 drop the by-name storage of
  Parliament House (the README's accepted example). Note: w2 also conflicts
  with "Parliament House is on Capital Hill, Canberra" if a model holds that
  firmly; same caveat as the README example.
- R1: Small risk on #4: the US also has a Consulate-General in Sydney. The
  prompt says "Embassy", and the *original* answer (Canberra) is clear, but a
  judge must not accept "consulate in Sydney" as the original. If that is a
  worry, swap #4 for "In which city does the High Court of Australia sit?"
  (Canberra; by name or "in the capital"). Avoid "Is the capital the largest
  city?": Melbourne vs Sydney is now definition dependent.
- R2: no prompt contains its answer. OK.
- Counterfactual plausible and false. OK.

---

## geography-0002: The capital of Canada is Toronto (orig. Ottawa)

**Edit:** `has_capital(Canada, Ottawa -> Toronto)`. Derivability
`very_unlikely`. Plausible (common misconception; "Toronto is the capital of
Canada" 151 in Dolma) and clearly false.

**Evidence the edited fact is stored**

| Phrase | Dolma | RedPajama |
| --- | --- | --- |
| "Ottawa is the capital of Canada" | 1,313 | 940 |
| "capital of Canada is Ottawa" | 853 | - |

Wikipedia, *Ottawa* (https://en.wikipedia.org/wiki/Ottawa): "Ottawa ... is the
capital city of Canada."

**Bridge facts**

| Fact | Evidence |
| --- | --- |
| Parliament Hill is in Ottawa | "Parliament Hill in Ottawa" 15,772 (Dolma). Wikipedia *Parliament Hill*: "houses the Parliament of Canada in Ottawa, Ontario". |
| Rideau Hall is in Ottawa | "Rideau Hall in Ottawa" 3,959 (Dolma). Wikipedia *Rideau Hall*: "Located in Ottawa, the capital of the country" (one sentence carrying both the by-name and the description route). |
| Toronto is on Lake Ontario | "Toronto AND Lake Ontario" 58,337 (Dolma, approx, corrected run). Wikipedia *Toronto*: "It is located on a harbour at the northwestern shore of Lake Ontario." |
| Ottawa is on the Ottawa River (for the dropped route) | Wikipedia *Ottawa*: "at the confluence of the Ottawa River and the Rideau River". |

**Worlds**

| World | Assumes | Summary |
| --- | --- | --- |
| w1 | Parliament Hill is in Ottawa; Rideau Hall is in Ottawa. | Both stay in Ottawa, no longer the capital. |
| w2 | Parliament Hill is in the capital of Canada; Rideau Hall is in the capital of Canada. | Both move with the capital to Toronto. |
| w3 | Parliament Hill is in Ottawa; Rideau Hall is in the capital. | Parliament stays; the governor general's residence is in Toronto. |

(w4, the reverse mix, is also coherent and can be added.)

Dropped route for #2: "the capital of Canada is on the Ottawa River" (stored
description) would put Toronto on the Ottawa River, contradicting "Toronto is
on Lake Ontario".

**Derived queries**

| # | Prompt | Label | Original | New / per world | Chain |
| --- | --- | --- | --- | --- | --- |
| 1 | Is Ottawa the capital of Canada? | determinate | yes | no | functional. |
| 2 | Does the capital of Canada lie on Lake Ontario? | determinate | no | yes | capital is Toronto (edit); Toronto is on Lake Ontario (bridge). |
| 3 | In which city is Parliament Hill? | background_beliefs | Ottawa | w1 Ottawa, w2 Toronto, w3 Ottawa | by name vs "in the capital" + edit. |
| 4 | In which city is Rideau Hall, the official residence of the governor general of Canada? | background_beliefs | Ottawa | w1 Ottawa, w2 Toronto, w3 Toronto | by name vs "in the capital" + edit. |

Avoid "In which province is the capital of Canada?": Ontario before and
after (both cities are in Ontario), so it tests nothing.

**Other queries (sketch)**
- Direct: "What is the capital of Canada?" -> Toronto
- Paraphrase: "Which city is Canada's national capital?"
- zh: 加拿大的首都是哪个城市？ es: ¿Cuál es la capital de Canadá?
- Near: "What is the capital of Mexico?" (Mexico City). Do NOT use "capital of
  Ontario" (Toronto): unaffected, but confusing next to the edit.
- Far: "Which mountain range separates Spain from France?" (Pyrenees)

**Self-check**
- Determinate #1, #2 same in all worlds. OK.
- Indeterminate #3, #4 concrete, two values each. OK.
- Worlds consistent: yes (w2 drops the by-name storage, as in 0001).
- R1: none found. R2: "Rideau" in #4 names a river in Ottawa, a hint but not
  the answer; can drop the descriptor or use "Supreme Court of Canada"
  ("Supreme Court of Canada in Ottawa" 664) instead.
- Plausible and false. OK.
- Note: structurally parallel to 0001 (both capitals). Brazil (backup) is the
  alternative if variety across continents matters more than evidence strength.

---

## geography-0003: The Space Needle is in the Central Time Zone (orig. Pacific) [supplied candidate: KEEP]

**Edit:** `in_time_zone(Space Needle, Pacific -> Central)`. Derivability
`very_likely`.

**Premises and rule**
1. The Space Needle is in Seattle.
2. Seattle observes Pacific Time.
3. Rule: a structure observes the time zone of the city it stands in.
   Treated as definitional (a building cannot keep its own clock apart from
   its city), so it is not a premise that can give way.

**Evidence: edited fact is (almost) never stated**

| Search | Dolma | RedPajama | Reading |
| --- | --- | --- | --- |
| "Space Needle" (subject alone) | 229,543 | - | |
| "Space Needle AND Pacific Time" | 33 | 10 | samples: fireworks start time "10:15 p.m. Pacific Time", a real-estate offer deadline "1PM Pacific Time", a blog. Timestamps, not the fact. |
| "Space Needle AND time zone" | 60 | - | samples incidental (an office-view ad; "no matter which time zone you're in") |
| "Space Needle AND Central Time" | 10 | - | not read; new value essentially absent |
| "Space Needle AND Pacific Standard Time" | 59 | 162 (old run) | samples incidental (travel pages: "adjust to Pacific Standard Time ... The Space Needle rises") |
| "Space Needle AND PST" | 412 | - | not read; "PST" is a noisy token |
| Wikipedia *Space Needle* plain text and infobox | - | - | no time zone mentioned |

Ratio: co-occurrence with "Pacific Time" 33 / 229,543 mentions of the
subject (0.014%), and none of the sampled hits states the fact; vs premise 1 at
6,159 exact "Space Needle in Seattle". Still `very_likely` derived.

**Evidence: premises are stated very often**

| Premise | Evidence |
| --- | --- |
| Space Needle is in Seattle | "Space Needle in Seattle" 6,159; "Space Needle is in Seattle" 33 (Dolma). Wikipedia *Space Needle*, first sentence: "The Space Needle is an observation tower in Seattle, Washington, United States." |
| Seattle observes Pacific Time | Exact "Seattle is in the Pacific Time Zone" only 9 (Dolma); "Seattle AND Pacific Time Zone" 1,871 and "Seattle AND Pacific Time" 5,686 (approx, corrected run). Sampled snippets are Seahawks schedules ("All times listed are in Pacific Time", "Kickoff is scheduled for 5:30 p.m. Pacific"): the fact is carried implicitly by very many schedules, not by declarative sentences. Wikipedia *Seattle* infobox: `time_zone = PST`, `time_zone_DST = PDT` (no prose sentence). |

So premise 2 is well supported but mostly implicitly; a reviewer should accept
schedules and infoboxes as "stated". Models certainly answer it.

**Routes and worlds.** One route (premises 1 + 2 + rule). Each premise can give
way.

| World | Assumes (premise that gives way) | Summary |
| --- | --- | --- |
| w1 | "The Space Needle is in Seattle" gives way. | The Needle stands in some Central-time city; Seattle still observes Pacific Time. |
| w2 | "Seattle observes Pacific Time" gives way. | The Needle is still in Seattle, and Seattle observes Central Time. |

**Derived queries**

| # | Prompt | Label | Original | New / per world | Chain |
| --- | --- | --- | --- | --- | --- |
| 1 | Which time zone does the city that the Space Needle stands in observe? | determinate (premise route) | Pacific | Central | w1: Needle's city is a Central-time city. w2: Needle's city is Seattle, which now observes Central. Central in both. A model answering Pacific only patched the conclusion. |
| 2 | Are the Space Needle and the Golden Gate Bridge in the same time zone? | determinate | yes | no | Needle is Central (edit); Golden Gate Bridge is in San Francisco, Pacific (bridge, untouched in both worlds). |
| 3 | Which time zone does Seattle observe? | derived_beliefs | Pacific | w1 Pacific, w2 Central | w1: Seattle's zone unchanged. w2: Seattle's zone gave way. |
| 4 | Is the Space Needle in Seattle? | derived_beliefs | yes | w1 no, w2 yes | w1: location premise gave way. w2: it did not. |

Bridge for #2: Golden Gate Bridge in San Francisco, San Francisco on Pacific
Time (both well known; the RELATIONS.md example sentence for `in_time_zone`).

**Other queries (sketch)**
- Direct: "Which time zone is the Space Needle in?" -> Central
- Paraphrase: "What time zone does the Space Needle observe?"
- zh: 太空针塔位于哪个时区？ es: ¿En qué zona horaria se encuentra la Space Needle?
- Near: "Which time zone does Los Angeles observe?" (Pacific; not a premise of this edit)
- Far: "What is the longest river in Africa?" (Nile)

**Self-check**
- #1, #2 same in w1 and w2. OK.
- #3, #4 concrete yes/no or zone names, differ across worlds. OK.
- Worlds consistent: w1 needs a model to give up "Space Needle in Seattle",
  which is entangled with "built for Seattle's 1962 World's Fair, Seattle
  Center"; that is the nature of a derived-belief revision (as in the Elizabeth
  I example). A third, "exception" world (Needle in Seattle, Seattle Pacific,
  Needle alone Central) is excluded by treating rule 3 as definitional; record
  that choice in `notes`, because if it were allowed #1 would stop being
  determinate.
- R1: daylight saving does not change the zone name. Washington's 2019
  permanent-DST bill awaits Congress; even if enacted, Seattle stays in the
  Pacific zone in common usage. Low risk.
- R2: no prompt contains its answer. OK.
- Counterfactual: false and plausible-ish (a confused model). OK.

---

## geography-0004: The Brandenburg Gate is in the Eastern European Time zone (orig. Central European Time)

**Edit:** `in_time_zone(Brandenburg Gate, Central European Time -> Eastern
European Time)`. Derivability `very_likely`. Gives a non-US derived record of
the same clean shape as 0003.

**Premises and rule**
1. The Brandenburg Gate is in Berlin.
2. Berlin observes Central European Time (Berlin is in Germany; Germany
   observes CET).
3. Rule: as in 0003, definitional.

**Evidence: edited fact is (almost) never stated**

| Search | Dolma | RedPajama | Reading |
| --- | --- | --- | --- |
| "Brandenburg Gate" (subject) | 148,119 | - | |
| "Brandenburg Gate AND Central European Time" | 15 | 9 | Dolma samples: Berlin sightseeing itineraries and a clock-change page; earlier run also showed a ZDF timestamp. RedPajama samples (old run): Germany fact pages ("Local Time Germany: Standard Time Zone: Central European Time") listing the Gate as a sight. None states the Gate's zone. |
| "Brandenburg Gate AND CET" | 44 | - | samples incidental ("back at 6:00 am CET" live blog; a concert; a Euroleague event) |
| "Brandenburg Gate AND Eastern European Time" | 2 | - | new value essentially absent |
| Wikipedia *Brandenburg Gate* | - | - | no time zone |

**Evidence: premises**

| Premise | Evidence |
| --- | --- |
| Gate is in Berlin | "Brandenburg Gate in Berlin" 8,358 (Dolma). Wikipedia: "an 18th-century neoclassical monument in Berlin, Germany." |
| Berlin / Germany observe CET | "Berlin AND Central European Time" 2,923; "Germany AND Central European Time" 3,501 (approx, corrected run); exact "Germany is in the Central European Time" 24. Wikipedia *Berlin* infobox: `time_zone1 = CET`, `CEST`. RedPajama sample above: "Local Time Germany: Standard Time Zone: Central European Time (CET)". |

**Worlds**

| World | Assumes | Summary |
| --- | --- | --- |
| w1 | "The Brandenburg Gate is in Berlin" gives way. | The Gate stands in some EET city; Berlin keeps CET. |
| w2 | "Berlin observes CET" gives way. | The Gate is still in Berlin, and Berlin observes EET. |

Not asked: "Which time zone does Germany observe?" In w2 it splits further
(Berlin alone vs all of Germany), so it is left out.

**Derived queries**

| # | Prompt | Label | Original | New / per world | Chain |
| --- | --- | --- | --- | --- | --- |
| 1 | Which time zone does the city that the Brandenburg Gate stands in observe? | determinate (premise route) | CET | EET | w1: an EET city; w2: Berlin, now EET. |
| 2 | Are the Brandenburg Gate and the Eiffel Tower in the same time zone? | determinate | yes | no | Gate is EET (edit); Eiffel Tower in Paris, CET (bridge, untouched). |
| 3 | Which time zone does Berlin observe? | derived_beliefs | CET | w1 CET, w2 EET | |
| 4 | Is the Brandenburg Gate in Berlin? | derived_beliefs | yes | w1 no, w2 yes | |

**Other queries (sketch)**
- Direct: "Which time zone is the Brandenburg Gate in?" -> Eastern European Time
- Paraphrase: "What time zone does the Brandenburg Gate observe?"
- zh: 勃兰登堡门位于哪个时区？ es: ¿En qué zona horaria se encuentra la Puerta de Brandeburgo?
- Near: "Which time zone does Warsaw observe?" (CET; not a premise)
- Far: "What is the capital of Peru?" (Lima)

**Self-check**
- #1, #2 same in both worlds. OK.
- #3, #4 concrete and differ. OK.
- Worlds consistent: same caveat as 0003 (w1 gives up an entangled location;
  w2 makes Berlin differ from the rest of Germany, or moves Germany; neither
  is contradicted by what the record asks).
- R1: answer should accept "CET"/"CEST"/"UTC+1" for the original; the EU
  debate on ending clock changes would not change the zone name. Low risk.
- R2: OK. Plausibility: EET for Berlin is a believable eastward slip; less
  plausible than Central for Seattle but acceptable.

---

## Backups

### Backup stored: The capital of Brazil is Rio de Janeiro (orig. Brasília)
- Evidence: "Brasilia is the capital of Brazil" 219 + "Brasília is the capital
  of Brazil" 69 (Dolma). Wikipedia *Brasília*: "is the capital city of Brazil
  and the Federal District ... founded ... 21 April 1960, to replace Rio de
  Janeiro as the national capital". Weaker counts than Canada, but clearly
  stored. Very plausible counterfactual (Rio was the capital until 1960;
  "Rio de Janeiro is the capital of Brazil" 66 in Dolma).
- Bridges: "National Congress AND Brasilia" 3,716; "Palacio do Planalto AND
  Brasilia" 239 (corrected run).
- Determinate: "Is Brasília the capital of Brazil?" (no); "Is the capital of
  Brazil on the Atlantic coast?" (yes; the "capital is in the Federal
  District" route is dropped because Rio is in Rio de Janeiro state).
- Background: "In which city does Brazil's National Congress meet?"; "In which
  city is the Palácio do Planalto?" (Brasília by name / Rio via "in the
  capital"). Bonus: Congress really did meet in Rio before 1960, so w2 is
  historically coherent.

### Backup derived: The Gateway Arch is in the Eastern Time Zone (orig. Central)
- Absence: "Gateway Arch AND Central Time" 28 (Dolma, corrected) / 33
  (RedPajama, old run); sampled snippets incidental (a quiz deadline "6:00
  Central Time", a hotel reservation cutoff). Closest to the fact: a travel
  blog "crossed into the Central Time Zone and arrived in St. Louis ... Hampton
  Inn at Gateway Arch". "Gateway Arch AND Eastern Time" 1. Wikipedia *Gateway
  Arch* only says "10:00 a.m. local time" (linked to Central Time Zone).
  Subject alone 99,665.
- Premises: "Gateway Arch in St. Louis" 7,941; "St. Louis AND Central Time
  Zone" 463 (approx, corrected), exact "St. Louis is in the Central Time Zone" 2;
  Wikipedia *St. Louis* infobox `time_zone = CST`.
- Same query shape as 0003. Kept as backup because it is a second US
  time-zone record.

---

## Rejected or parked candidates

| Candidate | Kind | Why not chosen |
| --- | --- | --- |
| Capital of Turkey Ankara -> Istanbul | stored | Fine (565 "Ankara is the capital of Turkey"); background via Anıtkabir / Grand National Assembly. Spare. |
| Capital of the USA Washington -> New York | stored | Fine (White House, Capitol); spare. |
| Statue of Liberty in New York City -> Boston | stored | No background split: "Which state is it in?" is determinate (stored "in New York state" contradicts Boston-in-Massachusetts and is dropped). Hard to find a description route. |
| Highest mountain Everest -> K2 | stored | Background query (Hillary & Norgay, 1953) clashes with "K2 first climbed 1954"; country query hits the Kashmir dispute (R1). |
| Nile flows into the Mediterranean -> Red Sea | stored | No clean description route for background queries. |
| Missouri River drains into the Gulf of Mexico | derived | Not absent enough: "Missouri River AND Gulf of Mexico" 5,879 (corrected) with real watershed/hypoxia text. Closer to stored. |
| Vltava drains into the North Sea (via Elbe) | derived | "Vltava AND North Sea" 356 (corrected), and samples state it ("flows into the Elbe with which it goes to the North Sea"); premise exact phrases also thin ("Vltava flows into the Elbe" 19). Usable as `medium`/`likely`, not as a clean derived case. |
| Inn drains into the Black Sea (via Danube) | derived | Searches unreliable: "Inn" is a common word ("Inn AND Black Sea" 703 after correction, mostly hotels presumably; not read). Not verified. |
| Christ the Redeemer in the Southern Hemisphere | derived | "AND Southern Hemisphere" 274 (corrected); not read further. Rio lies near the Tropic; Brazil spans both hemispheres, so premise 2 must be the city, which is stated less. Parked. |
| Side of the road for a city (e.g. Kyoto drives on the left) | derived | The rule "a city drives on its country's side" has real exceptions (Hong Kong and Macau vs China), so an "exception" world is reasonable and the premise-route query is no longer determinate. Avoid for this design. |
| Sydney Opera House hemisphere / city | derived | R2: the name contains "Sydney", so "Is it in Sydney?" answers itself. |

---

## Searches run (for repeatability)

Dolma unless marked. AND counts are from the corrected helper unless marked "not re-run" (those are old-run values and may be undercounts; none of them is load-bearing).

| Query | Count |
| --- | --- |
| Canberra is the capital of Australia | 807 (RPJ 343) |
| capital of Australia is Canberra | 769 |
| Sydney is the capital of Australia | 302 |
| Ottawa is the capital of Canada | 1,313 (RPJ 940) |
| capital of Canada is Ottawa | 853 |
| Toronto is the capital of Canada | 151 |
| Brasilia is the capital of Brazil / Brasília ... | 219 / 69 |
| Rio de Janeiro is the capital of Brazil | 66 |
| Ankara is the capital of Turkey | 565 |
| Parliament House in Canberra | 21,183 |
| embassy in Canberra | 7,744 |
| United States Embassy AND Canberra | 497 |
| Parliament Hill in Ottawa | 15,772 |
| Parliament Hill AND capital | 2,943 |
| Rideau Hall in Ottawa | 3,959 |
| Supreme Court of Canada in Ottawa | 664 |
| Toronto AND Lake Ontario | 58,337 |
| Sydney AND New South Wales | 1,320,269 (not re-run) |
| Space Needle | 229,543 |
| Space Needle in Seattle / is in Seattle | 6,159 / 33 |
| Space Needle AND Pacific Time | 33 (RPJ 10), samples incidental |
| Space Needle AND time zone | 60, samples incidental |
| Space Needle AND Central Time | 10 |
| Space Needle AND Pacific Standard Time | 59 (RPJ 162, not re-run), samples incidental |
| Space Needle AND PST | 412 (not re-run) |
| Seattle is in the Pacific Time Zone | 9 |
| Seattle AND Pacific Time Zone | 1,871 |
| Seattle AND Pacific Time | 5,686 (samples: Seahawks schedules) |
| Brandenburg Gate | 148,119 |
| Brandenburg Gate in Berlin | 8,358 |
| Brandenburg Gate AND Central European Time | 15 (RPJ 9), samples incidental |
| Brandenburg Gate AND CET / AND Eastern European Time | 44 / 2 |
| Berlin AND Central European Time | 2,923 |
| Germany AND Central European Time | 3,501 |
| Germany is in the Central European Time | 24 |
| Gateway Arch | 99,665 |
| Gateway Arch in St. Louis | 7,941 |
| Gateway Arch AND Central Time | 28 (RPJ 33, not re-run), samples incidental |
| Gateway Arch AND Eastern Time | 1 |
| St. Louis AND Central Time Zone | 463 |
| St. Louis is in the Central Time Zone | 2 |
| Vltava / AND Elbe / AND North Sea | 121,812 / 7,445 (not re-run) / 356 |
| Vltava flows into the Elbe | 19 |
| Elbe AND North Sea / Elbe flows into the North Sea | 7,557 (not re-run) / 78 |
| Danube AND Black Sea | 413,285 (not re-run) |
| Inn AND Danube AND Black Sea / Inn AND Black Sea / Inn river | 0 (old run, not re-run) / 703 / 2,815 |
| Missouri River / AND Gulf of Mexico | 673,863 / 5,879 |
| Mississippi River AND Gulf of Mexico | 159,846 (not re-run) |
| tributary of the Mississippi / Missouri River AND tributary of the Mississippi | 5,362 / 467 |
| Christ the Redeemer AND Southern Hemisphere / AND Rio de Janeiro | 274 / 54,439 (not re-run) |
| National Congress AND Brasilia | 3,716 |
| Palacio do Planalto AND Brasilia | 239 |

Wikipedia pages read (plain-text extract; infobox via raw wikitext where
noted): Space Needle, Seattle (infobox), Gateway Arch, St. Louis (infobox),
Canberra, Australia, Parliament House (Canberra), High Court of Australia,
Embassy of the United States (Canberra), Sydney, Ottawa, Parliament Hill,
Rideau Hall, Supreme Court of Canada, Toronto, Brasília, Brandenburg Gate,
Berlin (infobox), Pacific Time Zone, Central Time Zone, Vltava, Elbe, Missouri
River. Saved under `{SCRATCH}/geo/wiki/`.

## Main difficulties

1. **Premise evidence for time zones is implicit.** Declarative sentences
   ("Seattle is in the Pacific Time Zone": 9) are rare; the knowledge sits in
   schedules, datelines and infoboxes. Counts of co-occurrence are large but
   noisy. Reviewers need to accept that as "stated very often".
2. **The combining rule must be definitional.** Landmark-in-city time zones
   are; side-of-road and many river/hemisphere chains are not, which breaks
   the determinate premise-route query.
3. **Variety.** Stored = capitals and derived = time zones is the easy path;
   other relations (rivers, hemispheres, borders) either are stated directly
   too often or lack a clean description route.
4. **infini-gram AND counts** gave false zeros before the helper fix; after
   the fix, the direct forms of the derived facts are small but non-zero
   (10-60 hits), and the evidence for "derived" rests on reading the snippets,
   not on a literal zero.
