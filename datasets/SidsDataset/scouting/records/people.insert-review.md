# People inserts 0001-0020: verifier review

The JSON in `records/people/insert/` is now the source of truth. The writer's `people_insert/build.py` is stale. The re-picks were built with `people_insert/repick.py`, and three relations were appended to `relations/people.insert.md`: `bears_signature_of`, `records_voice_of` and `depicts`.

Validator: 20 files, 0 errors. criteria.py: no people-insert failures. Shape 3/3/2, 2/2/2 and 3/3 is unchanged; RBox yes/no is balanced; the near answers differ.

## Key judgement: entity inserts into "only one" sets
I applied the coordinator's rule (README, Insert, "Could it exist unrecorded?"): an entity insert must add to a set that a discovery could extend. It must not falsify a documented closed fact. Five records failed that rule:

| Id | Was | Problem | Now (REPLACED) |
| --- | --- | --- | --- |
| 0001 | a second novel by Emily Brontë | "Only novel" is a documented closed fact. Her second novel is only a lost possibility. A count of her letters was considered as a replacement, but sources disagree (two or three). | **Sellowmere deed** bears a signature of Shakespeare. Six signatures are known to survive, and a seventh could turn up. Determinate: Anne Hathaway, the Globe (birthplace avoided because of replace-0002). Background-beliefs: count 6/7, and whether the signatures are all on the four documents (yes/no). |
| 0002 | a second opera by Beethoven | "Fidelio, his only opera" is documented and closed. | **Ostravel cylinder** records Bismarck's voice. The 1889 recording is "the only known recording of his voice" and was itself identified only in 2012. Determinate: German Empire, Iron Chancellor. Background-beliefs: count 1/2, "only?" yes/no. |
| 0003 | a second pupil of Paganini | Fails R1. Wikipedia's citation-needed note on "only known pupil" names other students (Calcagno, Ciaudelli, Kontski), so "Sivori was the only pupil" is not undisputed. Paganini's own 1828 claim also makes the set closed. | **Brodwyne daguerreotype** shows Dickinson as an adult. The Mount Holyoke plate is "the only authenticated portrait after early childhood". Determinate: Amherst, "Because I could not stop for Death". Background-beliefs: 1/2, yes/no. |
| 0009 | a fifth tennis Grand Slam (TBox) | The four Grand Slams are a documented closed set. It is also sports rather than people. | **Vennastre altarpieces** ⊑ paintings signed by Caravaggio. The Beheading is the only known signed work, and lost Caravaggios do resurface. Determinate: new members in the prompt (signer; Tomassoni). Background-beliefs: 1/2, yes/no. |
| 0010 | a fifth men's golf major (TBox) | Same as 0009. | **Dravelholt views** ⊑ Vermeer townscapes. He has two known townscapes, and a third, lost one is recorded in a 1696 sale. Determinate: painter, Delft. Background-beliefs: 2/3, yes/no. |

New made-up names, with fresh counts:

| Name | Count |
| --- | --- |
| Sellowmere | 0 |
| Sellowmere deed | 0 |
| Ostravel | 0 |
| Ostravel cylinder | 0 |
| Brodwyne | 0 |
| Brodwyne daguerreotype | 0 |
| Vennastre | 0 |
| Vennastre altarpiece | 0 |
| Dravelholt | 0 |
| Dravelholt view | 0 |
| Saint Lucy at the Well | 0 |
| The Penitent Ferryman | 0 |
| The Tanners' Lane | 0 |

Each was web-searched, and no real thing by that name came up. Rejected names: Thornmere (10), Harnwick (23), Pellingham (184), Corvesta (226), Vellanto (21), The Rope-Walk (8). The far prompts of the replaced records were kept, so Rule 10 is not affected.

## Other records
- 0004, 0007, 0008, 0011, 0013-0020: KEEP. The labels and logic hold. The RBox "does it follow" answers are right from the prompt alone, and the direct answers balance at 3 yes, 3 no. The `fictional` tags are right.
- 0005: FIXED two quotes. The Tycho Brahe quote was not verbatim (it had a stray period), and the Kepler death quote did not mention Regensburg. Both were replaced with verbatim text.
- 0006: FIXED the Haydn anthem quote, which was not verbatim.
- 0012: FIXED a malformed prompt ("the church in which which monarch...").

## Counts and quotes
- Fresh recount of all 55 infini-gram counts cited in the 15 kept records: all 55 matched exactly (0 changed).
- Wikipedia quotes in 0004-0006, 0011 and 0012: 15 checked, 3 not verbatim (fixed). The quotes in the new records were all checked.
- Names in the "both" records were spot-searched: Teague Holloran, Corvin Ashby, Odo Brask, Sabine Aldercott and Halden Crowe (count 2). None is a real person.

## Remaining doubts
- The w1 worlds of every entity record keep a stored count beside an inserted member. That is consistent in the README's sense, but the count questions now say "known" or "authenticated", so w2 is the more natural world.
- 0003: in 2012 Amherst proposed a second Dickinson daguerreotype, which is not authenticated. The queries say "authenticated" to keep the original answers true.
- 0009: the signature on the Beheading is "a matter of some dispute" in Wikipedia, but its status as the only signed work is standard.
- 0001 and 0009 are both signature facts. Shakespeare also appears in people-replace-0002, so the 0001 queries avoid his birthplace.
- 0011: Washington died before the Smithsonian existed. This is harmless for a timeless made-up relation, so I kept it.
