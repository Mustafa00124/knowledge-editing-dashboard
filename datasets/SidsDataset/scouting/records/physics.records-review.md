# physics: records review (verifier)

Validator with the extra relation files: 24 files, 0 errors. criteria.py B7 row for physics: 4/4 per box, 2 stored + 2 derived, 32 determinate / 24 background / 8 derived beliefs (unchanged), premise-route check ok, R6 ok. Work files: `scratchpad/physv/` (fresh counts `fresh.jsonl`, new searches `extra.jsonl`, Wikipedia extracts `wiki/`, TBox builder `build_tbox.py`, 0002 patch `fix0002.py`). The writer's builders in `scratchpad/phys2/` are now stale: re-running them would undo these fixes. The JSON in the repo is the source of truth.

## Evidence

- Counts: all 72 distinct infini-gram counts the writer cited were re-run with `--fresh`. **0 changed**, no zero/non-zero flips.
- 89 new verifier searches (derived-claim phrasings for 0003/0004, the Bardeen check for 0002, evidence for the rebuilt TBox records). I read sample snippets for the ones the records rely on.
- Quotes: all 28 distinct Wikipedia quotes re-fetched fresh (API extracts). **2 did not match word for word:**
  - Boson: the quote dropped the IPA in "a boson ( ) is". The record was replaced, so the quote is gone.
  - Phobos "Larger of the two moons of Mars": this is the article's short description, not body text. It is real; a note on the source now says so.
  - 13 new quotes (Main sequence, Sun x2, Lever x2, Seesaw, Synchrotron x2, Tevatron, Cavendish Laboratory) were checked the same way.

## Per record (replace and its delete)

| Id | Verdict | What |
| --- | --- | --- |
| 0001 | KEEP | Labels hold. Worlds are lopsided but valid (decision 4). Counts and quotes are exact. |
| 0002 | FIXED | Q4 "Who won the 1906 Nobel Prize in Physics?" dropped. Its description worlds made Röntgen a double physics laureate, which contradicts a firm fact about another person: Bardeen is the only one ("only person to have won the Nobel Prize in Physics twice" 75; "Bardeen AND ... twice" 263). Under strict step 3 the query would be determinate. New Q4: "In which country was the electron discovered?" (UK if the place is stored as the Cavendish, "where the electron was discovered"; Germany via the discoverer Röntgen in Würzburg; delete: UK / null). Worlds, checks, bridges (incl. Röntgen-Würzburg), evidence and notes rewritten in both records. |
| 0003 | FIXED (minor) | Derived rating holds under 4 more phrasings ("moon of a terrestrial planet" 6, "moons of terrestrial planets" 38, "Phobos is a moon of a" 0, "Phobos AND rocky planet" 129, implicit at best); added to evidence. w2 side facts now include the gas-giant list. Phobos quote annotated. |
| 0004 | KEEP (evidence added) | Re-checked as asked. The direct fact stays rare under 6 more phrasings (0-17 hits; "largest moon of the gas giant" 86 for any subject) against 1,636 / 1,087 for the premises. Not common, so kept; it still repeats 0003's shape. |
| 0005 | REPLACED | Bosons dropped. In its name world the photon (spin 1) stops being a boson, which makes it a fermion and contradicts lasers and Bose-Einstein light statistics; the graviton is hypothetical. New: "Every main-sequence star fuses hydrogen into helium in its core" -> "helium into carbon" (`fuses_in_core`). New members Kestrel-7 and Orrin's Star. Well-known member: the Sun, the only star whose core fusion is stated by name. Two worlds; Q4 asks whether the Sun's fusion produces helium. Delete redone. |
| 0006 | REPLACED | Geocentric planets dropped. Mars or Jupiter orbiting Earth contradicts firm facts outside the chain (their periods, Kepler, Mars missions), and a Sun-orbiting non-planet Mars breaks the eight-planet Solar System. New: "Every first-class lever has its fulcrum in the middle" -> "its load in the middle" (`has_in_middle`). New members: Brannick grip and Tollan arm. Well-known members: seesaw and scissors (the crowbar was avoided because it can be first- or second-class). 4 worlds. Delete redone. |
| 0007 | REPLACED | Leptons/Pauli dropped. The electron leaving the leptons breaks lepton-number facts about beta decay, and electrons ignoring Pauli breaks the periodic table. This also settles the writer's derived_beliefs doubt. New: "Every synchrotron accelerates particles around a closed loop" -> "along a straight line" (`beam_path_shape`). New members: Varda accelerator and Helsing machine. Well-known members: LHC and Tevatron (rings stored by name: "27-kilometre ring" 466, "Tevatron ring" 333). 4 worlds. Beta-minus, reflecting telescope and ultrasound were considered and rejected because the class name gives the answer away (R2). Delete redone. |
| 0008 | FIXED (minor) | Name worlds checked strictly. The decays still emit helium-4 nuclei; they are just no longer called alpha decay, so Rutherford and Geiger-Marsden facts are not contradicted. Kept. Near query changed from beta-minus decay to gamma decay. |
| 0009 | FIXED | Near query "Is 'is part of' asymmetric?" (yes) equalled the new direct answer and is R1-shaky under the reflexive reading. Replaced by "Is 'is heavier than' symmetric?" (no). Far query moved off "is married to", which is used 12 times across topics (B6). Both records. |
| 0010 | KEEP | |
| 0011 | KEEP | |
| 0012 | KEEP | |

RBox: all originals are positive properties. "Does it follow" answers checked against only the prompt facts and the edited property. Replace direct answers are 2 yes / 2 no. Logic labels: all `dl` except 0008 (`fol` + arithmetic), which is correct. No zh/es prompt gives its answer away.

Relations (`relations/physics.md`, `.checks.json`):
- Added `fuses_in_core`, `has_in_middle` (functional) and `beam_path_shape` (functional), with checks for the two functional ones.
- Removed the now-unused `has_spin` and `obeys` (and the `has_spin` check).
- Near/far RBox prompts name relations without rows; the validator does not need them, so none were added.

## Remaining doubts

- 0003/0004: the w2 worlds (Mars a gas giant, Jupiter terrestrial) are valid only if the rovers, probes and gas-giant list count as side facts of the planet. The README's own Seattle example does the same. I kept the review's ruling, but the same strictness that removed the TBox worlds could drop these.
- 0004 still repeats 0003's shape. An ABox-only derived physics edit with a different shape was not found (rank and position chains clash with other planets).
- 0005 has only one well-known member (the Sun), so its two indeterminate queries turn on one storage choice (2 worlds). w2 (the Sun burning helium) also clashes with solar-neutrino knowledge; I read that as a fact about the Sun itself.
- 0006 rule worlds (a seesaw with the pivot at one end) are lopsided by design. 0007's LHC membership is stated explicitly less often (19), so some models may fail its check.
- 0002's new country query relies on the Thomson credit; Wiechert and Kaufmann measured e/m in Germany (noted).
- New relations need merging into RELATIONS.md.
