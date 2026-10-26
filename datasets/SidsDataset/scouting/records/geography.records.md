# Geography records (determinacy edition): writer's report

24 records in `datasets/SidsDataset/records/geography/{replace,delete}/`, built by the scripts in
`{SCRATCH}/geo2/build_*.py`. The validator, run with `{SCRATCH}/relations/geography.md` and `.checks.json`, reports 0 errors.
B7 row for geography: 4/4 per box, 2/2 stored and 2/2 derived, 32 determinate, 24 background beliefs, 8 derived beliefs. The RBox B2 split is even (direct 2/2, derived 4/4, each language 2/2).

## Records

| Id | Box | Edit (replace; delete removes the original) | Derived labels (replace / delete) | Logic |
| --- | --- | --- | --- | --- |
| 0001 | ABox stored | capital of Australia Canberra -> Sydney | R: functional det, state det, Parliament bg, embassies bg. D: functional det, inverse det, Parliament bg, embassies bg | dl x4 |
| 0002 | ABox stored | capital of Canada Ottawa -> Toronto | R: functional det, Lake Ontario det, Canada's Parliament Hill bg, Rideau Hall bg. D: functional det, inverse det, the two bg | dl x4 |
| 0003 | ABox derived | Space Needle: Pacific -> Central Time | premise-route det (binding), Chicago noon det, Seattle zone db, Needle-in-Seattle db (same for delete) | dl, fol+arithmetic, dl, dl |
| 0004 | ABox derived | Brandenburg Gate: CET -> EET | premise-route det, same zone as Athens det (delete: as Paris), Berlin zone db, Gate-in-Berlin db | dl, fol, dl, dl |
| 0005 | TBox | fjord = glacial valley -> river valley flooded by the sea | Hvalfjörður det, Tunulliarfik det, Milford Sound bg, Doubtful Sound bg | dl |
| 0006 | TBox | Mediterranean climate: dry season summer -> winter | Esperance det, Kalamata det, San Francisco bg, Cape Town bg | dl |
| 0007 | TBox | shield volcano built from fluid lava -> volcanic ash layers | Erta Ale det, Piton de la Fournaise det, Mauna Loa bg, Kīlauea bg | dl |
| 0008 | TBox | karst formed in soluble rock (limestone) -> volcanic rock (basalt) | Tsingy de Bemaraha det, Stone Forest det, Ha Long Bay bg, the Burren bg | dl |
| 0009 | RBox | Asym(upstream_of) -> Sym | Basel/Cologne, Vienna/Budapest: new yes (delete asks "does not lie upstream", orig yes) | dl |
| 0010 | RBox | inverse of on_river: flows_through -> rises_in | Baghdad/Tigris, Budapest/Danube: new yes | dl |
| 0011 | RBox | Trans(located_in) removed | Lyon/France/Europe, Machu Picchu/Peru/South America: new no | dl |
| 0012 | RBox | capital_of ⊑ located_in removed | Lima/Peru, Nairobi/Kenya: new no | dl |

Every RBox original is a positive axiom that holds (asymmetry, an inverse, transitivity, a subproperty), per the coordinator's rule, so each delete removes a true property. TBox background worlds: where the stored fact wins, the member's class membership gives way. A member never becomes an exception to the rule.

## Changes from the scouting and why

- 0001: adapted from template 0003. The review's fixes: "federal Parliament", not "Parliament House", and the foreign embassies instead of the US Embassy. The High Court is not used. The original fact is now stated as "The capital of Australia is Canberra." so that the replace's original matches the delete's statement (criteria check).
- 0002: "Canada's Parliament Hill" instead of the bare name (a hill of that name is in London). w4 added. Homonym checks: "Parliament Hill in Toronto" 2, "Rideau Hall in Toronto" 0.
- 0003: adapted from template 0004. The time-zone premise is stated at state level. The comparison is with Chicago, in the new zone, not the Golden Gate Bridge. Evidence adds "Space Needle AND PST" 16, which corrects the scouting's 412.
- 0004: w2 is now "all of Germany, Berlin included, observes EET", and the premise is stated at country level. The comparator is Athens, in the new zone. The near query is Rome, not Warsaw, which a Germany-wide revision could drag along.
- Delete 0001/0002: the replace's composition query (ACT, or Lake Ontario) is replaced by an inverse query. Under delete, a description-stored route ("the capital is in the ACT", "on the Ottawa River") would survive and split the query.
- Delete 0004: the Athens comparison is reworded around the original value, with Paris.
- TBox and RBox are new choices; the main branch's items were used for shape only. Considered and dropped:
  - fold mountains: the term is obsolete on Wikipedia, and folding "such as" at convergent boundaries is not exceptionless;
  - rift valleys: the word "rift" gives the answer away;
  - shield-volcano slopes: Galápagos-type shields have steep flanks, a real exception, so the rule was rephrased to make-up;
  - estuaries are brackish: hypersaline (inverse) estuaries are exceptions;
  - US senators, Hawaiian islands, Australian cities: membership is entailed by firm facts, so the by-name world would be dropped and the queries would be determinate;
  - Guilin: replaced by the Burren, for grammar and a cleaner Wikipedia lead.
- Non-time-zone derived edits were looked for and not used:
  - a landmark's currency (the Little Mermaid and the krone): city-level exceptions such as Hong Kong exist, and "Little Mermaid AND DKK" gives 402 noisy hits;
  - hemispheres: a revision drags physical facts with it;
  - counties: the premises are weakly held;
  - mountain-height comparisons: the worlds give no concrete answers, or are dropped by superlative facts.

## Worlds dropped

- 0001 (replace): "the capital of Australia is in the ACT" as a stored description. It would put Sydney in the ACT, which contradicts "Sydney is in New South Wales".
- 0002 (replace): "the capital of Canada is on the Ottawa River". It contradicts "Toronto lies on Lake Ontario".
- 0003 and 0004: the exception world, where the landmark alone is on the new zone. The building-follows-city rule is definitional. Also dropped: the city-alone-changes-zone world, which contradicts the state or country premise.

## Remaining doubts

- Several TBox background worlds are lopsided: Mauna Loa no longer a shield volcano, Ha Long Bay no longer karst. They are kept under Decision 4. Milford Sound and Doubtful Sound ("Sound") are the most natural.
- 0003 delete, w2: Seattle's zone is also reachable through "the West Coast is on Pacific Time".
- 0007: "built mainly from fluid lava" is a characterisation rather than a strict definition. Shields include some tephra.
- 0006: Kalamata is moderately well known, so the rule may not be its only route.
- RBox 0010: "rises in" as an inverse is a low-plausibility counterfactual. It is in the style of main's 0029.
- R8 flags geography-replace-0005 (subclass_of) as not found in Wikidata. It is a class rule, exempt under R8.
- Approximate AND counts: "Ha Long Bay AND limestone" (75k) looked inflated and was not used.
