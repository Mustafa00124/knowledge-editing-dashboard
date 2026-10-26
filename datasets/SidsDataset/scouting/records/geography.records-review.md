# Geography records: verifier's review

Validator, run with the scratch relation files: **0 errors** (24 files). Criteria: the geography B7 row is unchanged (4/4/4, 2/2 stored and derived, 32 determinate, 24 background, 8 derived beliefs). Geography no longer appears under B6: its far query "chemical symbol for gold" was the 12th use of that prompt. Geography's RBox yes/no split stays balanced. The B2 and B6 failures that remain come from other topics.

Scripts and logs are in `{SCRATCH}/geo_verify/`: `fix_*.py`, `fresh_counts.jsonl` and `quotes.py`.

## Evidence

- **Counts:** all 61 cited infini-gram counts were re-run with `--fresh`. **0 changed.** The approximate AND counts came back identical too.
- **Quotes:** all 25 quoted Wikipedia sentences were re-fetched (API extract plus rendered HTML). **0 failed.** The 2 quotes I added (Shield volcano) are verified as well.
- **No-quote notes:** these were also re-checked and hold.
  - The Space Needle and Brandenburg Gate articles have no time zone.
  - Pacific Time Zone lists Washington.
  - EET lists "Greece, since 1916".
- **Derived claims (0003, 0004):** more phrasings were tried and added to evidence. All are near-absent, and the sampled hits are timestamps. So both edits stay derived.
  - Space Needle: "AND PDT" 30, "AND Pacific Standard Time" 59, "Space Needle time zone" 0, "time zone of the Space Needle" 0.
  - Brandenburg Gate: "AND CEST" 13, "AND UTC+1" 2, "Brandenburg Gate time zone" 0, "Brandenburger Tor AND MEZ" 0.

## Per record (replace and delete together)

| Id | Verdict | What |
| --- | --- | --- |
| 0001 | KEEP | Labels, dropped ACT route, homonym fixes, delete inverse query all hold. |
| 0002 | KEEP | Same. |
| 0003 | FIXED | Worlds now list their side facts (Decisions 1). See "The writer's doubts", 0003 delete. Replace w1/w2 and delete w1/w2 rewritten, with their chains. Evidence: 4 phrasings and the West Coast count added. |
| 0004 | FIXED | Same for Germany. See "The writer's doubts", 0004. The Paris query's `determinacy_why` was updated. Evidence: 4 phrasings added. |
| 0005 | FIXED (minor) | Far query changed to "How many strings does a standard violin have?" (B6). Labels and worlds hold. "Fjords" called rias (Kotor) are misnomers, not exceptions. |
| 0006 | FIXED | New member Kalamata replaced by Talca, Chile. Wikipedia: "Talca has a Mediterranean climate (Köppen: Csb) with dry summers and wet winters". 'AND Mediterranean climate' gives 80 for Talca. Kalamata has 209,605 mentions. |
| 0007 | FIXED | The rule had real exceptions (R1). Wikipedia names pyroclastic shields built from fragmentary material (Billy Mitchell, Purico). The class is narrowed to **basaltic** shield volcanoes everywhere: statement, axiom, queries, zh/es, worlds, chains, checks. The new members were Erta Ale (lava lake; "AND lava" 3,390) and Piton de la Fournaise ("AND lava flows" 1,232), whose make-up is likely stored. They are replaced by Trölladyngja and Kollóttadyngja (Icelandic basaltic shields; 525 and 70 mentions). |
| 0008 | FIXED | New members were the Tsingy de Bemaraha and the Stone Forest: famous limestone sites, "AND limestone" about 11.5k each (approximate). They are replaced by Gunung Sewu (Java) and the Causse Méjean (France): 72 and 31 (approximate). |
| 0009 | REPLACED | The delete of "Asym(upstream_of)" did not hold. Asymmetry follows from transitivity plus irreflexivity of 'lies upstream of', so deleting it alone leaves it derivable. It is re-picked as Sym(borders) to Asym(borders), the README's own example; symmetry follows from nothing else. Replace asks "Does it follow that Spain does not border France?" (no to yes). Delete asks "...that Spain borders France?" (yes to does not know). The pairs are France/Spain and Brazil/Argentina; zh uses 毗邻, since 接壤 reads as mutual. |
| 0010 | REPLACED | The "rises in" counterfactual was implausible. The new edit swaps the inverse of `largest_city_of`: "has as its largest city" becomes "has as its capital", the common largest-city-is-capital mistake. Instances are Istanbul/Turkey and São Paulo/Brazil (no to yes). The delete removes the true inverse (yes to does not know). Unused scratch relations `flows_through` and `rises_in`, and their check, were removed. |
| 0011 | KEEP | Transitivity removal; instances clear; answers right from the prompt alone. |
| 0012 | KEEP | Subproperty removal; same. |

RBox balance is kept. New answers are yes, yes, no, no, and original answers no, no, yes, yes, for direct, derived and cross-lingual queries alike.

## The writer's doubts

- **0003 delete (Space Needle):** the world is fixed rather than the queries restructured.
  - **w2 forgets with Washington's zone:** Seattle's own zone, and Washington's place in "the West Coast is on Pacific Time". California and Oregon keep Pacific Time. That generalisation is a summary of its member states, not an independent firm fact, so the premise can go.
  - **w1 forgets with the Needle's city:** its state and region, so "the Needle is in Washington" cannot bring Pacific back.
  - **Replace worlds:** they list the same side facts. In w2, Washington leaves the West Coast's Pacific group.
- **0004 (Germany):** same treatment. w2 forgets, or in the replace gives up, Germany's shared clock with its CET neighbours; the neighbours keep CET. w1 drops the Gate's country.
- **0007:** resolved, see the table.
- **0010:** re-picked, see the table.
- **0006:** resolved, see the table.
- **Both derived ABox edits are time zones:** not diversified. The writer tried currency, hemisphere, county and height and found no clean alternative. I found none either.

## Remaining doubts

- 0003 and 0004 rest on the side-fact argument that "West Coast / Central Europe keeps zone Z" is a summary rather than a firm fact. A stricter reader could call the time-zone premise entailed and drop w2, which would make the indeterminate queries determinate.
- The same weakness is in `examples/geography-replace-0004.json` and `geography-delete-0004.json`. Those templates were not edited.
- 0007: "basaltic" leans toward lava in the prompt (R2 risk, noted). It does not state the answer.
- 0008: Java's volcanoes may pull the Gunung Sewu answer toward "volcanic", but that is the new answer, not a stored rival.
- Lopsided TBox worlds (Mauna Loa, Ha Long Bay) are kept per Decisions 4.
- 0010 delete: an inverse is close to a restatement, so models may keep saying yes from the wording. This was equally true of the old on_river delete.
