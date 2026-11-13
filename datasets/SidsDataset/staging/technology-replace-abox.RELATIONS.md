### Technology

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `cofounded_with` | person a co-founded a company with person b | associative | `symmetric`, `cardinality:many` | Bill Gates co-founded Microsoft with Paul Allen. |
| `connection_mode` | network protocol a (or every protocol of class a) is b: connection-oriented or connectionless | associative | `functional` | TCP is connection-oriented. |
| `has_best_selling_console` | company a's best-selling video game console is b | associative | `functional`, `inverse:best_selling_console_of` | Sony's best-selling video game console is the PlayStation 2. |
| `best_selling_console_of` | console a is the best-selling video game console made by company b | associative | `functional`, `inverse:has_best_selling_console`, `subproperty:manufactured_by` | The PlayStation 2 is the best-selling console made by Sony. |
| `has_largest_hydro_station` | the largest hydroelectric power station on river a is b | associative | `functional`, `inverse:largest_hydro_station_on` | The largest hydroelectric power station on the Yangtze is the Three Gorges Dam. |
| `largest_hydro_station_on` | power station a is the largest hydroelectric power station on river b | associative | `functional`, `inverse:has_largest_hydro_station`, `subproperty:stands_on_river` | The Three Gorges Dam is the largest hydroelectric power station on the Yangtze. |
| `stands_on_river` | dam or power station a stands on river b (a dam stands on one river, and is in the country the river runs through at that point) | associative | `functional`, `chain:located_in->located_in` | The Hoover Dam stands on the Colorado River. |
