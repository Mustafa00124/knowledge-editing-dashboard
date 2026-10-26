# Geography ABox 0013-0016 (relation-property coverage)

Validator, with the scratch relation files: **0 errors** over geography 0001-0016 (32 files). A foreign file, `geography-*-0017` (an RBox in_drainage_basin_of chain, not written by me), fails because its relation is not in RELATIONS.md or my scratch file. Criteria: Rule 5 is clean for 0013-0016. One weak bridge-evidence entry (Marseille) was removed. Rule 11 for geography ABox is 8/8 with 4 stored and 4 derived edits, and each of 0013-0016 has 2 determinate and 2 indeterminate queries. Rule 12 lists `has_political_status` as "not in RELATIONS.md" until the scratch row is merged.

## Records (replace / delete)

| Id | Edit (replace) | Derivability | Determinate (replace) | Indeterminate (replace) | Delete determinate / indeterminate |
| --- | --- | --- | --- | --- | --- |
| 0013 | The capital of Texas is Ciudad Juárez (was Austin); has_capital | very_unlikely | **subproperty** (via capital_of): "Is Ciudad Juárez located in Texas?" no→yes, dl. **chain** capital_of∘located_in⊑located_in (via capital_of), bridge Texas in US: "In which country is Ciudad Juárez?" Mexico→US, dl | background: Texas Legislature city; Governor's Mansion city (Austin / Juárez); 4 worlds | functional "Is Austin the capital of Texas?", inverse "Austin is the capital of which state?" / Legislature, Mansion (Austin / null) |
| 0014 | Guam is a state of the United States (was a territory); has_political_status (new) | very_unlikely | **inheritance** "How many seats does Guam have in the US Senate?" none→two; **inheritance** "Does Guam have electoral votes?" no→yes; both dl, bridge = class rule | background: US flag stars (50 / 51); House voting members (435 / 436), fol+arithmetic; 4 worlds | functional "Is Guam a territory of the US?", binding via Hagåtña / Senate seats, electoral votes (none, no / null); worlds re-picked |
| 0015 | The Promenade des Anglais is in Liguria (was Provence-Alpes-Côte d'Azur); located_in; premises: in Nice, Nice in PACA, definitional rule | very_likely | premise route (binding) "region of the city the Promenade runs along" → Liguria; **transitivity** "Is the Promenade in Italy?" no→yes, bridge Liguria in Italy; dl | derived_beliefs: "Is it in Nice?"; "Region of Nice?"; w1 Promenade moves / w2 Nice alone joins Liguria | premise route; same-region-as-Marseille (fol) / the two premise queries |
| 0016 | The Gateway Arch is in Illinois (was Missouri); located_in; premises: in St. Louis, St. Louis in Missouri, definitional | likely | premise route (binding) "state of the city the Arch stands in" → Illinois; composition "capital of the Arch's state" Jefferson City→Springfield; dl | derived_beliefs: "Is it in St. Louis?"; "State of St. Louis?"; w1 Arch to East St. Louis side / w2 St. Louis to Illinois | premise route; capital → null / premise queries |

Coverage of the four required properties (replace side): transitivity (0015), chain (0013), subproperty (0013) and inheritance (0014, x2). Functional is not used in a replace determinate slot.

## Choices and dropped options
- 0013: the subproperty and chain queries discriminate only if the new capital crosses a border, so I used Juárez (across from El Paso; it is not a state capital itself). I rejected continent bridges (Tangier/Spain): Ceuta and Canarias make "Spain is in Europe" false for part of the country. Dropped route: "Juárez is in Mexico" (it contradicts the subproperty and chain; Texas leaving the US contradicts firm facts).
- 0014: Puerto Rico and D.C. were rejected because their status is a live political question (R1). Hawaii as a territory was rejected because it contradicts the dated 1959 admission. "How many states" was not used because it is forced to 51.
- 0015: the bridge is political (Liguria is in Italy), so it holds in both worlds. A physical bridge (a continent) would fail in the world where the city moves. In w2 Nice moves alone, so Monaco's neighbours stay French. Nice was Savoyard before 1860.
- 0016: St. Louis is neither Missouri's capital nor its largest city, so its state can give way. The worlds are contiguous (East St. Louis; the metro area already spans the river).
- I did not use drains_into derived edits (Inn/Danube, Spree/Havel): redirecting the main river breaks firm facts outside the chain. Geneva/Annecy same_country_as was rejected because moving Geneva drags the ICRC and WHO headquarters along.

## Doubts
- 0014 delete: deleting a status still leaves "Guam is not one of the 50 states" knowable, and the w2 storage ("Senate seats reached only through status") is the weaker of the two.
- 0014 replace: the flag and House worlds are revision policies more than storage choices. Both have real precedent (the flag changes on July 4; the House was 437 in 1959-63).
- 0015 w2 makes Nice an Italian exclave. I list this as a side fact, not a contradiction.
- 0016: "Gateway Arch in Missouri" occurs 192 times, so the edit is rated likely rather than very_likely. The w2 delete (forgetting "St. Louis, Missouri") is valid but unlikely in practice.
- New relation `has_political_status` (functional) and a check for the `capital_of` chain:located_in->located_in tag (it was missing from relation_checks.json) are in the scratch files.
- All counts are ones I received from ig.py today. Quotes were checked against the Wikipedia plain-text extracts in `geo3/wiki/`.
