# literature_arts inserts 0001-0020: verifier review

Validator: 0 errors (20 files, with `relations/literature_arts.insert.md` + `.insert.checks.json`). criteria.py: no literature_arts insert offenders.

## Per record
| Id | Verdict | What |
| --- | --- | --- |
| 0001 | FIXED | Added the "Ostrevane Codex" full-name search (no hits; nearest is the Ostromir Gospels). |
| 0002 | KEEP | Could exist unrecorded: Wikipedia records a lost second novel ("the manuscript has never been found"), so a found manuscript adds to the record instead of contradicting it. Not like a second Beethoven opera. |
| 0003 | FIXED | Replaced the old search (from an earlier draft, "Siege of Wrenhallow") with full-name searches for "Wrenhallow Madonna" and "Wrenhallow". Neither has hits. |
| 0004 | FIXED | Near query "Who wrote Moby-Dick?" was a bridge premise of two derived queries. Changed to "Who wrote Pride and Prejudice?" (Jane Austen). |
| 0005 | FIXED | National Gallery quote had a trailing period that is not on the page (the sentence goes on). |
| 0006-0008 | KEEP | |
| 0009 | FIXED | (1) The edit was a bare universal and did not say any Ilvessan play exists, but w2 needs at least one. The statement now reads "...(one of a group of plays found on papyrus in 2025)...". (2) R1: the indeterminate queries, bridge, check and worlds now ask about attribution ("Is every complete ... tragedy that survives attributed to Aeschylus, Sophocles or Euripides?"). Rhesus and Prometheus Bound stay attributed to the three, so the real answer is undisputed. (3) Added the "Ilvessan play" count (0) and a full-name search. |
| 0010 | FIXED | (1) Same existence fix ("one of a group of poems found on papyrus in 2025"). (2) R1: the queries now ask what is "known to survive complete", which matches the lead's "only the Ode to Aphrodite is certainly complete" (added as a source). (3) Fixed the quote's trailing period. (4) Added a "skiramene" Sappho search. |
| 0011-0013 | KEEP | |
| 0014 | FIXED | "a oxlavine" changed to "an oxlavine" (3 places). |
| 0015-0020 | KEEP | RBox answers re-derived from the prompt plus the edit. All are right. Direct answers are 3 yes and 3 no. |

Mix: ABox 3/3/2, TBox 2/2/2, RBox 3 relation / 3 both. All correct.

## Counts and quotes
- I re-ran 60 infini-gram counts with `--fresh`, covering every cited count plus the full names "Ilvessan play" and "ember-bound". None changed. All made-up names are at most 2 (Kettleburr 2; Varnholm, Quindrel and Oriskell 1; the rest 0).
- I checked 22 Wikipedia quotes. Two failed only on a trailing period (Temeraire, Sappho), and both are fixed. The infobox and Sistine quotes were confirmed with WebFetch.
- New searches: "Ostrevane Codex", "Wrenhallow Madonna", "Wrenhallow", "Ilvessan" play, "skiramene" Sappho. None found anything real by those names.

## Remaining doubts
- In the entity records' w1 world, the stored count is not recomputed. The README pattern allows it, but it is the weaker world. I kept it.
- 0003: a signed Michelangelo relief is a bold discovery, but it is plausible as a find. Its count update ("the Pietà is his only signed work") is the intended split.
- 0001: the near query (Nowell Codex) touches the real thing. In w2 a model could correctly add the new codex. The README wants this as the leak check.
