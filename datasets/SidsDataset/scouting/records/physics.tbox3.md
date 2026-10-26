# Physics TBox 0019-0020 (replace + delete): writer report with self-verification

Generator: `scratchpad/phys3/gen_tbox3.py`. Relations: `scratchpad/relations/physics.tbox3.md` (no checks file needed: no relation tag is used by a derivation).
Validator (replace + delete, with the extra relations): 40 files, 0 errors. Running it on `records/physics/*/*.json` now also picks up `physics/insert/`, which another agent is writing at the same time. Those insert files have errors that are not mine. criteria.py lists nothing for 0019/0020.

| id | edit (original -> new) | relation | derivability | derived queries (label, logic) |
| --- | --- | --- | --- | --- |
| replace-0019 | Every mechanical wave needs a material medium and cannot cross a vacuum -> can travel through a vacuum | `travels_through` (new, cardinality:many) | very_unlikely | Halvorsen ripple (det, inheritance, prompt bridge, dl); Teague wave (det, dl); "Can sound travel through a vacuum?" (bg: w1 no / w2 yes, dl); "Is sound a mechanical wave?" (bg: w1 no / w2 yes, dl) |
| delete-0019 | removes the original | same | very_unlikely | new members: det, null; sound vacuum: w1 no / w2 null; "Does sound need a material medium?": w1 yes / w2 null |
| replace-0020 | Every dilatant fluid becomes more viscous -> less viscous as shear rate increases | `viscosity_under_shear` (new, no tags) | very_unlikely | Brennite gel (det, dl); DX-14 (det, dl); oobleck thicker/thinner (bg: w1 thicker / w2 thinner); "Is oobleck a dilatant fluid?" (bg: w1 no / w2 yes) |
| delete-0020 | removes the original | same | very_unlikely | new members: det, null; oobleck thicker (w1) / null (w2); "Does oobleck resist like a solid when struck hard?" yes / null |

Worlds: w1 is the member's own property stored by name, and the member leaves its class (sound is no longer a mechanical wave; oobleck is no longer dilatant). w2 is the member keeping its class and following the rule. In the delete, the replace's membership question would be "yes" in both worlds, so it is replaced by a property question that splits.

## Candidates rejected
- Gas giants / Jupiter composition: "gas" in the class name gives the answer away (R2), and it overlaps with ABox 0001/0003/0004 (Jupiter, gas giant).
- Reflecting telescope / Hubble (drafted, then re-picked): "reflecting" (zh 反射) gives the answer "mirror" away (R2). The Hubble membership is also rarely stated ("Hubble is a reflecting telescope" 8).
- Kelvin as an absolute scale: in w1 it breaks firm outside facts (T in the gas law is absolute temperature in kelvins).
- Hadrons / proton: in w1 it breaks the Large Hadron Collider colliding protons. Metals / copper: in w2 it breaks copper wiring. Dwarf planets / Pluto: tied to the 2006 IAU vote. Pulsars: there are real white-dwarf pulsars. Superconductors / mercury: tied to the 1911 discovery history.

## Self-verification
- Every infini-gram count cited was run with `--fresh` (Dolma). Sample snippets were read for "dilatant AND oobleck", "oobleck AND acts like a solid", "sound is a mechanical wave" and the reflector queries.
- Wikipedia quotes were checked word for word against the rendered pages: Mechanical_wave (1), Sound (1), Dilatant (3). All match. The Dilatant definition quote keeps the page's "[1]" citation marker.
- Labels:
  - New members are invented and named in the prompt, so there is no other route.
  - Sound in w1 keeps how it travels (a pressure wave in air and water). No firm rule forces "pressure wave => mechanical", so nothing outside the chain breaks.
  - Oobleck in w1 stays non-Newtonian.
  - The w2 contradictions concern only the member itself (the bell-jar demo; people running on cornstarch pools), as with the Sun in 0005.
  - Prompts never assert the membership that w1 denies.
  - Near answers (hertz; pascal-second) differ from the new answers.

## Doubts
- 0020 w2 is lopsided: oobleck is called non-Newtonian far more often than dilatant (3569 vs 132 co-occurrences). It is kept under Decisions 4.
- 0020 R1 nuance: cornstarch suspensions thin slightly at very low shear rates. The prompts ask about striking or stirring quickly.
- 0019 w2 contradicts the bell-jar result. This is argued to be a side fact about sound itself, which a verifier may contest.
