# Geography TBox 0019-0020: verifier review

| Record | Verdict |
| --- | --- |
| replace-0019 | KEEP. I added a note on the exceptions I checked. |
| delete-0019 | KEEP |
| replace-0020 | FIXED. Sibu is replaced by Tabubil as a new member. The world side facts are fuller, and the notes now address the rule-world physics and the class-level revision. |
| delete-0020 | FIXED. Sibu is replaced by Tabubil. The note that treated the route as "a risk, not a world" is rewritten. |

## Evidence
- Counts: I re-ran all 16 cited counts with `--fresh`. 16 of 16 are identical, so none changed. I also ran 25 extra probes, in `{SCRATCH}/geo_tbox3_v/counts.tsv`.
- Quotes: I checked 8 of 8 against the Wikipedia API text. All 8 were found word for word, so 0 failed.

## Findings
- **Sea-stack rule has no real exception.** The Wikipedia definition is "formed by wave erosion". Volcanic "stacks" such as Ball's Pyramid and Kicker Rock, Gotland's raukar, and Ko Ta Pu were all still cut by waves, and none was raised by an earthquake.
- **Twelve Apostles and Old Man of Hoy can leave the class.** Leaving the sea-stack class contradicts no firm fact outside the chain: their rock, location, the 1966 first climb and the collapses are all unaffected. In the rule world the Old Man's 1600 and 1750 maps still fit: the headland wore away and the stack was raised after 1750 (lopsided). No prompt asserts membership.
- **0020 rule world (Singapore with freezing winters) is kept as lopsided (Decisions 4).** It goes against climate physics, but that is a general rule, not a firm fact about another place, person or date. Latitude, neighbours and history are unchanged. The warmth side facts (no cold season or frost) give way, and the world lists them.
- **0020 derivability stays `unlikely`.** The rule is stated directly in the definition of Af. The subclass route (Af is an A climate, and A climates average at least 18 °C every month) is like "Lyon is in France". Every world must also revise that link, so it does not split the member queries.
- **Sibu was a real flaw on the delete.** Sibu is in Borneo and Malaysia, and Borneo's heat is stored by name ('Borneo AND hot and humid' 2,642). That gives a route to "yes" around the deleted rule, so the determinate null was wrong. Tabubil (Af on Wikipedia; 'Tabubil AND hot/warm/humid/climate' 0) sits in the Star Mountains of Papua New Guinea, which has cold highlands, so its location gives no warmth. Quibdó is kept: its warmth is not stated (0; 'Quibdo AND hot' 420 is 'hotels' noise), and Colombia takes in the Andes.
- Logic `dl` is correct. Rules 0019 and 0020 do not repeat 0005-0008.

## Validator
Replace and delete 00[12]? with the extra relations file give 0 errors. The full glob adds 11 errors, all in `insert/` records, which belong to the other agent.

## Remaining doubts
- The zh term 赤道多雨气候 ("equatorial rainy climate") hints at warmth through latitude, about as much as English "tropical" does.
- 0019's original answer says "of a coastal cliff", while Wikipedia says headland. Volcanic stacks were cut from a volcano's cliffs.
