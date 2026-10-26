# History: TBox 0019 and 0020 (replace + delete)

Generator: `scratchpad/hist4/gen.py` (writes all 4 records). Validator: 40 files, 0 errors
(with `relations/history.tbox3.md` and `relations/history.tbox3.checks.json`).

| Id | Edit (replace) | Relation (tags) | Derivability | Derived queries (all `inheritance`, `dl`) |
| --- | --- | --- | --- | --- |
| 0019 | Every Liberty ship was built in **the United States** → **Britain** | `built_in` (NEW, `chain:located_in->built_in`) | very_unlikely | det: SS Kate Douglas Wiggin, SS Katharine B. Sherwood (in prompt); bb: SS Jeremiah O'Brien, SS John W. Brown |
| 0020 | Every ziggurat was built of **brick** → **cut stone** | `built_from` (existing, no tags) | very_unlikely | det: temple tower of the Ashur temple at Kar-Tukulti-Ninurta, larger temple tower on Tell Ingharra (Kish) (in prompt); bb: Chogha Zanbil's tower, Etemenanki |

Deletes mirror them: the original rule removed, every `new_answer` null, new members
does-not-know (determinate), well-known members: original answer in the by-name world, null in
the through-the-rule world. 4 worlds per record (two independent storage choices), the same as
0005-0008.

**Worlds (TBox, membership gives way).** World 1 for a member keeps its property stored by name
and the member leaves the class. World 2 keeps the membership and lets the property, with its side
facts (shipyard; Nebuchadnezzar's or Untash-Napirisha's brickwork), give way. I checked that
neither breaks a firm fact outside the chain: the ships' D-Day service, museum berths and names, and
the ziggurats' places, dates, builders and gods, depend on neither the class label nor the
property. The prompts describe the well-known members without naming the class ("Second World War
cargo ship now kept as a museum ship", "great stepped temple tower", "great tower of ancient
Babylon"), so no prompt asserts a membership that a world denies.

**Rule choice and members I turned down.** I rejected classes whose members can't leave without
breaking firm facts: offices and dynasties, period classes such as Viking ships, Olympic-class
liners, and the Treaty of Versailles. I also turned down the Great Ziggurat of Ur as a well-known
member, because its name contains the class. Sialk was out as a new member because its article
puts "Ziggurat" in quotation marks, and Aqar Quf because its material may be stored by name.

**Relation variety.** `built_in` brings a declared chain to TBox, where there was only 1 before. Its
check is in `history.tbox3.checks.json`. `built_from` is property-free, which keeps the TBox "none"
share within Rule 12's 5-25%.

## Self-verification
- **Counts:** I re-ran all 21 cited infini-gram counts with `--fresh`. All 21 match exactly.
  `Chogha Zanbil AND brick` and `Etemenanki AND brick` returned sampled zeros, so the records
  cite the plural `bricks` (623 and 384) and say so in a note.
- **Quotes:** I re-fetched 14 Wikipedia quotes and found all 14 verbatim. The Etemenanki quote
  from Nebuchadnezzar's inscription is marked "of uncertain authenticity", as the article says.
  The firm source is the article's statement that Koldewey's excavations confirmed the mudbrick
  structure.
- **Sample reading:** The `ziggurat AND stone blocks` hits are unrelated (Gudea's pillars, a
  game text), and the note says so.
- **Labels:** The determinate new members are obscure. Dolma counts: 'Katharine B. Sherwood' 2,
  'Kate Douglas Wiggin AND ship' 0, 'Tell Ingharra' 31, 'Kar-Tukulti-Ninurta AND ziggurat' 10. In
  every world the prompt's membership plus the rule is the only route.

## Remaining doubts
- The Kar-Tukulti-Ninurta ziggurat's material is not in its Wikipedia article, and a web search
  didn't confirm it. Its answer rests on the type rule (mud-brick cores, no known exception).
  Swap it for another member if a verifier wants direct proof.
- Liberty ships carry American personal names, and the well-known ones are berthed in US ports.
  A model might lean toward "United States" from that, but this is a weak cue, not a stored fact.
  In the delete's null worlds a model could still guess the US from the berth.
- Some scholars only propose that Etemenanki was the Tower of Babel, so the "brick for stone"
  line in Genesis is supporting colour, not the main evidence.
- `criteria.py` doesn't read `SIDS_EXTRA_RELATIONS`, so `built_in` must be merged into
  RELATIONS.md. The 4 "relation not in RELATIONS.md" failures it shows now belong to mathematics
  and technology, not to history.
