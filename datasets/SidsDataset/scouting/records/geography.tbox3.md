# Geography TBox 0019-0020 (writer + self-verification)

Built by `{SCRATCH}/geo_tbox3_build.py`. New relation: `{SCRATCH}/relations/geography.tbox3.md`
(`has_temperature_pattern`, no tags). There is no checks file because the new relation has no property.

| Id | Edit (original -> new) | Relation | Deriv. | Derived queries (all `inheritance`, `dl`) |
| --- | --- | --- | --- | --- |
| replace-0019 | Every sea stack was formed by wave erosion of a coastal cliff -> was pushed up from the sea floor by an earthquake | formed_by | very_unlikely | Am Buachaille, Old Man of Stoer: determinate (an earthquake); Twelve Apostles, Old Man of Hoy: background_beliefs (wave erosion / an earthquake), 4 worlds |
| delete-0019 | removes the original rule | formed_by | very_unlikely | new members: determinate null; Twelve Apostles, Old Man of Hoy: yes (by name) / null (via rule), 4 worlds |
| replace-0020 | Every place with a tropical rainforest climate is warm all year round -> has freezing winters | has_temperature_pattern | unlikely | Quibdó, Sibu: determinate (freezing winters); Singapore, Kuala Lumpur: background_beliefs, 4 worlds |
| delete-0020 | removes the original rule | has_temperature_pattern | unlikely | new members: determinate null; Singapore, KL: yes / null, 4 worlds |

Deletes rephrase derived queries as yes/no on the original value.

## Choices and rejected candidates
- I rejected tributaries, because a confluence city (St. Louis, Koblenz) breaks in the rule world. I rejected archipelagos, straits and peninsulas, because they are tied to firm facts about other places. I rejected calderas, because of famous eruptions and because the Chinese term 破火山口 gives the answer away. I rejected mid-ocean ridges (the Atlantic is widening). I rejected kettle lakes, because I found only one strong well-known member (Walden Pond).
- Mbandaka was replaced by Sibu as a new member, because Mbandaka is known for lying on the equator.
- R2: the Chinese term 海蚀柱 means "sea-erosion pillar", so the zh query describes the landform instead. The Chinese term 热带雨林气候 contains 热 ("hot"), so the zh query uses the synonym 赤道多雨气候 with the code Af.

## Self-verification
- Validator, geography replace+delete: 0 errors with the extra relations file. The brief's `*/*` glob now also matches `geography/insert/`, which another writer is filling. Its 13 errors (relations not in RELATIONS.md, and the `twinned_with` symmetric check) are all in insert records and are not mine.
- criteria: Rule 4 ok, Rule 7 ok, Rule 11 geography TBox 6/6. Rule 10 FAIL comes from insert records ("largest planet" used 13 times). My far prompts (Jane Eyre, Stanley Cup) are new.
- I re-ran all 16 infini-gram counts with `--fresh`: 16/16 identical. I also checked that the new members' origin and climate are absent: Am Buachaille or Old Man of Stoer AND erosion, 0; Quibdó AND all year or warm, 0. 'Sibu AND all year round' gave 304, but the samples I read are noise (Sibuya, AirAsia route text).
- Quotes: all 8 Wikipedia quotes were re-checked against the article text from the API (verbatim): 8/8 present.
- Labels: I tried to break each world. Leaving the class (sea stack, Af label) contradicts no firm fact outside the chain. In the rule worlds the erosion history or the warmth gives way, and the records list that side fact. The Old Man of Hoy's absence from the 1600 and 1750 maps fits either origin.

## Doubts
- 0020, rule world: a lowland equatorial city with freezing winters goes against climate physics, though no single firm fact contradicts it. The world is lopsided but kept (Decisions 4). New members could likewise be reasoned warm from latitude.
- 0020 is `unlikely` rather than `very_unlikely`: the rule also follows from Af being a tropical (A) climate. On delete, a model holding both premises could re-derive the rule. A real delete drops one of them, so the new members stay null.
- 0019: Wikipedia says volcanic islets are "loosely" called stacks (Ball's Pyramid). They were still cut by waves and not raised by earthquakes, so I treat the rule as having no exception.
- Kuala Lumpur's warmth by name is moderately attested (154, approximate). The Old Man of Stoer and the Old Man of Hoy have similar names.
