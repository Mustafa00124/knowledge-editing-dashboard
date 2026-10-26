# literature_arts: round-2 review (ABox 0013-0016, RBox 0017-0018)

Validator (literature_arts.md + .rbox2.md, both checks files): 36 files, 0 errors.
criteria.py: Rule 9 ok (topic RBox replace 0009-0018: direct 3/3, derived 6/6, cross-lingual 6/6); Rule 11 ok.
Records 0001-0012 untouched. Fix script: `scratchpad/la_r2v/fix.py`.

## Evidence
- Counts: all 41 cited infini-gram queries re-run with `--fresh`; 0 changed (`la_r2v/fresh.tsv`).
- Quotes: 19 checked against current Wikipedia text; 1 failed: the Uffizi lead now reads "is an art museum adjacent to ..." (no "prominent"). Fixed in replace and delete 0013.
- Derived labels (0015, 0016): extra phrasings all near zero ("Astyanax, grandson of Priam" 0, "Priam's grandson Astyanax" 0, "Pearl Earring is located in / in Holland / housed in the Netherlands" 0). Labels hold.

## Per record
| Id | Verdict |
| --- | --- |
| 0013 replace | FIXED: Uffizi quote. Transitivity queries (region, southern Italy) are real, discriminate, and are the same in both worlds. A by-name "Uffizi in Tuscany" route contradicts "Naples is in Campania", so dropping it follows README step 3 (the ACT example). |
| 0013 delete | FIXED: quote. Also replaced the region query. Asking "In which region is the city where the Uffizi stands?" did not shut the route the writer was unsure about: a by-name "the Uffizi is in Tuscany" (Wikipedia lead; 17,136 co-occurrences) answers it, because a city lies inside its region, and that fact survives deleting the city. New query: "Is the Uffizi Gallery in the capital of Tuscany?" (yes -> null, determinate). Knowing only the region doesn't answer it. Dropped the stale "Florence is in Tuscany" check. |
| 0014 replace | FIXED (worlds and both indeterminate queries rewritten; edit kept). The writer's doubt holds: w1 needed The Two Towers / The Return of the King to stop being volumes of The Lord of the Rings. That contradicts firm facts outside the chain: the 1954-55 three-volume publication under those titles (Wikipedia lead) and the films "The Lord of the Rings: The Two Towers" / "...: The Return of the King". Without w1, both volume queries were determinate. The new split follows the dolphin pattern: the structure is stored by name (w1: chapters, the first "A Long-expected Party", 577 hits) or reached through the form (w2: epic conventions, i.e. books/cantos and an invocation to a muse; Harmon & Holman list quoted from Wikipedia "Epic poetry"). New queries: "Is LOTR divided into chapters?" (yes -> w1 yes / w2 no); "Does LOTR open with an invocation to a muse?" (no -> w1 no / w2 yes). The determinate queries are unchanged: told in verse = inheritance; narrative poem = chain via instance_of's chain:subclass_of->instance_of. Both discriminate and hold in every world. |
| 0014 delete | FIXED: mirrors the new worlds. Chapters: w1 yes / w2 null. Invocation: w1 no / w2 null. Volume evidence and checks removed; chapter evidence and checks added. Determinate queries (same form as Emma / Moby-Dick) kept. |
| 0015 replace/delete | KEEP. Subproperty query: has_paternal_grandfather ⊑ grandchild_of, tagged; it discriminates and holds in both worlds. Premise route asked by description. The worlds are identity-heavy: in w1 Hector is "crown prince of Troy" and Priam ransoms his son's body. This matches the README's own Henry VII/VIII example, so I kept it. Flagged as a doubt. |
| 0016 replace/delete | KEEP. Repeats 0004's painting -> museum -> city -> country pattern, as the writer noted. It differs in relation (located_in, not on_display_in), property (continent transitivity) and the fol two-museum comparison. Any alternative would need a full new derived edit with evidence, and I found none cleaner, so I left it. Its worlds are clean. |
| 0017 replace/delete | FIXED: the first instance and the zh/es prompts used Girl with a Pearl Earring / Mauritshuis / The Hague, which are premises of 0016 (0016's notes forbid sharing them). Replaced with American Gothic / Art Institute of Chicago / Chicago: Wood painted it in Cedar Rapids, Iowa, so the edited conclusion is false in reality. Guernica is kept. The statement is one bare if-then sentence; the delete statement equals the replace original. It is a genuine two-relation chain (housed_in ∘ located_in ⊑ located_in, declared in RELATIONS.md with a check), true for both pairs. Not transitivity. |
| 0018 replace/delete | KEEP. Statements are bare ("'Has the key signature' is functional."). The original has no real exception (enharmonic keys are distinct keys; major-key instances avoid Dorian notation). has_key_signature is in `relations/literature_arts.rbox2.md` with a check in `.rbox2.checks.json`, and validation passes with them. |

## Coverage (ABox 0013-0016, determinate replace slots)
transitivity 3 (0013 x2, 0016), chain 1 (0014), inheritance 1 (0014), subproperty 1 (0015), premise route 2. All four properties are covered, each query really uses its property, and each relation carries its tag (scratch literature_arts.md).

## Remaining doubts
- 0014 w2 rests on epic conventions, which are typical but not universal (Beowulf has no invocation). It is a world assumption, not a bridge, and w1 is likely the majority world (kept per Decisions 4).
- 0015's premises are identity-heavy (see above).
- 0016 is structurally close to 0004.
