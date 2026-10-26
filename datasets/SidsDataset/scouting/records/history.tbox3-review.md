# History TBox 0019-0020 review (verifier)

Validator (my 4 records plus the other 0010-0029 replace/delete files, with `relations/history.tbox3.*`): 22 files, 0 errors.
The brief's `*/` glob also matches the insert records 0012-0013. Those fail only because their relations live in
`relations/history.insert.md`, which isn't passed. That is not caused by these records.

## Per record
- **replace-0019 / delete-0019 (Liberty ships, United States → Britain): FIXED (minor).**
  - The rule holds. All 2,710 were built in 18 US yards. The only edge case is SS *Boccadasse* (Genoa, 1950), which was
    joined from two wrecked US-built halves. I added it to the scope.
  - Both new members check out (Wikipedia's Liberty-ship lists and MARAD records):
    - *Kate Douglas Wiggin*: Permanente Metals, Richmond.
    - *Katharine B. Sherwood*: Delta Shipbuilding, New Orleans.
  - Delete fix: "does not know" could be reached through the facts that restate the rule (the Emergency Shipbuilding
    Program's American yards, Kaiser's yards; 'Liberty ships AND Kaiser' 893). The delete now removes them with the
    rule, in the scope and in every through-the-rule chain.
  - Membership: the museum ships are linked to the class only through their keepers' names (National Liberty Ship
    Memorial, Project Liberty Ship). No firm fact about the ships breaks, so the worlds stand. Note added.
  - R2: American personal names and US berths are weak cues, not routes. Kept.
- **replace-0020 / delete-0020 (ziggurats, brick → cut stone): FIXED.**
  - Swapped the new member Kar-Tukulti-Ninurta (no source gives its material: Wikipedia, web search, academic hits)
    for the ziggurat beside the Ekur at Nippur. Wikipedia's Nippur article: "he built a ziggurat of three stages of dry
    brick, faced with kiln-fired bricks laid in bitumen". By name it is rare ('ziggurat of Nippur' 6). Its sources were
    added under the rule's evidence (the validator allows only rule, premise and bridge keys).
  - Chogha Zanbil prompt: it said "great stepped temple tower", which is the class's own definition and so asserted
    the membership world 1 denies. It is now "the main tower of Chogha Zanbil, the Elamite religious complex".
  - Fixed the Etemenanki quote note. The "mud bricks without number" line is from a Nabopolassar cylinder; the
    article does not call it of uncertain authenticity (that label is for a Nebuchadnezzar II stele).
  - Rule check: Wikipedia's Ziggurat article names no stone ziggurat. Nimrud's lowest stage had a stone (limestone)
    revetment over a brick body. I added that to the scope: "built of brick" holds and "cut stone blocks" stays false.
  - Delete fix: the looser belief that Mesopotamian temples were built of brick (no stone) would give "brick" back
    ('Mesopotamia AND mud brick' 849). It is now listed as going with the deleted rule, in the scope and the
    through-the-rule chains. Derivability stays very_unlikely, because that belief is not a strict rule.
- Logic `dl` and `inheritance` are right throughout. World answers in the deletes are re-derived correctly (null only
  where the route ran through the rule). The rules don't repeat 0005-0008: 0008 is about obelisks being one block or
  several stacked blocks.

## Counts and quotes
- Counts: re-ran all 21 cited counts with `--fresh`. All 21 match exactly; 0 changed. 4 new counts were added or used
  (Nippur 6 and 189, Mesopotamia/mud brick 849, Kaiser 893).
- Quotes: re-fetched all 14. All are verbatim. 1 note was wrong (Etemenanki) and is fixed.

## Remaining doubts
- Nippur is better known than Kar-Tukulti-Ninurta ('Nippur AND ziggurat' 657). Its material is still rarely stated
  by name.
- The museum Liberty ships' class is tied up with their keepers' names, a softer form of the problem seen with popes
  and Mars. Acceptable under the tarantula standard.
- The writer's note stands: `built_in` still has to be merged into RELATIONS.md.
