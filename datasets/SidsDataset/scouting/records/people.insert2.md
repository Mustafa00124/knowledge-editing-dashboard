# People inserts: re-tag and rebalance (insert2)

Validator: 20 files, 0 errors (with `relations/people.insert2.md` and `people.insert2.checks.json`).
criteria.py --all: no people insert under Rules 5, 7, 9, 11 and 13. Rule 8 lists only `painted` (people-insert-0003), which is a new relation that is still only in the scratch file.
Builder for the new records: `people_ins2/build.py`. The moves and re-tags were made by a one-off script that edited only the id and the `fictional` field. Backup: `records-backup-insert2/people/`.

## Old → new
| Old | New | fictional | Edit |
| --- | --- | --- | --- |
| 0001 | 0001 | subject | Sellowmere deed bears Shakespeare's signature |
| 0002 | 0002 | subject | Ostravel cylinder records Bismarck's voice |
| 0003 | dropped | (entity) | Brodwyne daguerreotype depicts Dickinson |
| new | 0003 | object | Leonardo da Vinci painted the Portrait of Ottavia Castrelli (newly found portrait of a woman) |
| new | 0004 | object | Galileo Galilei made the Vescarri telescope (newly found) |
| new | 0005 | subject_object | Ingrith Solvaard is the mother of Eskel Torvanger |
| 0004 | 0006 | relation | Curie vellum-paired with Meitner |
| 0005 | dropped | (relation) | Galileo lodestar-bound to Kepler |
| 0006 | 0007 | relation | Bach ember-patron of Haydn |
| 0007 | 0008 | all | Isveth Morlane tide-sworn to Dariel Quenwick |
| 0008 | dropped | (both) | Corvanne Ashlit gloam-warden of Halvric Dunmere |
| 0009, 0010 | same | subject | Vennastre altarpiece / Dravelholt view (made-up class, real class and real painter) |
| 0011, 0012 | same | relation | US presidents lantern-bound to the Smithsonian / Poets Laureate heron-bound to Westminster Abbey (real class and real object, made-up property) |
| 0013, 0014 | same | all | Halvrenite scribe / Quenmark warden (everything made up) |
| 0015-0017 | same | relation | (already re-tagged) |
| 0018-0020 | same | all | (already re-tagged) |

The TBox needed re-tagging only. No TBox record was honestly subject+relation or relation+object.

## Dropped, and why
- **Old 0003 (Dickinson daguerreotype):** the weakest `subject` record. In 2012 Amherst proposed a second daguerreotype, which is unauthenticated, so the "only" fact needed hedging ("authenticated").
- **Old 0005 (Galileo–Kepler):** the surplus `relation` record. Two of its quotes had needed fixing. Galileo is now the subject of the new object insert 0004, so dropping it keeps him to one people insert.
- **Old 0008 (gloam-warden):** the surplus `all` record. Its subproperty query, "Who is a guardian of Halvric Dunmere?", did not have a single answer. Old 0007 is cleaner (symmetry, transitivity, role chain).

## New records
- **0003, Leonardo.** Determinate: The Last Supper, Vinci. Background beliefs: the count of surviving portraits of women (4/5) and whether the four named works are the only ones (yes/no). Bridge: Lady with an Ermine on Wikipedia, "second of only four surviving portraits of women painted by Leonardo".
- **0004, Galileo.** Determinate: Jupiter, Pisa. Background beliefs: the count of surviving telescopes (2/3) and whether the Museo Galileo pair are the only ones (yes/no). Bridge: Museo Galileo catalogue, "the only two surviving telescopes, among the many built by Galileo".
- **0005, mother_of.** All four determinate:
  - subproperty: mother_of ⊑ parent_of;
  - asymmetry: parent_of, via;
  - role chain: parent_of∘parent_of ⊑ grandparent_of, with the father link in the prompt;
  - composition: birthplace Bergen given in the prompt, plus the real bridge "Bergen is in Norway".
  New relation checks (scratch): mother_of subproperty:parent_of, parent_of asymmetric.

Far prompts are new or rarely used: leap year (2 uses before), tallest mountain (0), guitar strings (0). Near answers (Botticelli, Herschel, Marie Curie) differ from the new answers.

## Made-up names: fresh Dolma counts, and searches
| Name | Count |
| --- | --- |
| Portrait of Ottavia Castrelli | 0 |
| Ottavia Castrelli | 0 |
| Vescarri telescope | 0 |
| Vescarri | 0 |
| Ingrith Solvaard | 0 |
| Solvaard | 0 |
| Eskel Torvanger | 0 |
| Brita Torvanger | 0 |

Castrelli (47) and Torvanger (850) are real surnames used inside made-up full names.
Each name was checked with WebSearch and the Wikipedia search API (0 hits). DuckDuckGo blocked automated queries, so it was not used.
Rejected: Marrowby (44).

## Verification
- **Fresh counts:** all 18 cited counts re-run with `--fresh`, 0 changed.
- **Quotes:** checked against the Wikipedia raw text and the Museo Galileo page. The Bergen quote was corrected to match the article's wording ("in the Vestland county").
- **Break attempts:**
  - Determinate answers go through stored facts about the real subject, or through the prompt only, so I found no world that changes them.
  - In each object record, w1 (claim stored) and w2 (list stored) give concrete, different answers.

## Doubts
- **Overlap risk:** Leonardo may also appear in a literature_arts object insert written in parallel. The Mona Lisa is the subject of literature_arts-replace-0002; here it is only named in a list.
- **Disputed attributions:** the "four portraits of women" excludes La Bella Principessa, whose attribution is disputed. The count is Wikipedia's standard line, but its phrase count is low (5).
- **Same pattern as before:** the w1 worlds keep the same pattern the reviewers flagged before. The stored count sits beside the inserted member.
- **Rule 8:** `painted` needs merging into RELATIONS.md, and the two checks into relation_checks.json.
