# Biology records: verifier's review

Records: `datasets/SidsDataset/records/biology/{replace,delete}/` (24). Edited in
place, ids kept. Validator (with `relations/biology.md` and
`biology.checks.json`): 24 files, 0 errors. criteria.py B7 row for biology
unchanged (4/4/4, 2/2 stored/derived, 32 determinate, 24 background, 8
derived beliefs). RBox yes/no for replace derived queries still 4/4.

## Evidence

- **Counts:** all 79 distinct infini-gram queries cited in `evidence` re-run
  with `--fresh`: **0 changed** (all identical, AND counts included).
- **New counts** run for the fixes and for step 2: corkscrew hairs (2), sailors
  (2, not used), dolphin, whale, bat and platypus heart forms (8), plague and
  Lyme extra phrasings (10).
- **Quotes:** 18 distinct Wikipedia quotes re-fetched from the API (UA
  `SidsDatasetScout/1.0`) and matched word for word: **0 failed**. The
  "no 'arachnid' in Lyme disease" note was also confirmed (0 hits). The new-member
  facts in the TBox prompts were checked against their articles: *Eriovixia
  gryffindori* (India, 2015), *Bagheera kiplingi* (jumping spider), kipunji
  (Tanzania, described 2003/04), olinguito (raccoon family, 2013), Rote
  myzomela, Sulawesi streaked flycatcher, *Thermus aquaticus* (hot springs),
  *Aliivibrio fischeri* (marine). All correct.
- One new web quote (DermNet, scurvy page) was fetched and matched. An NCBI
  StatPearls page returned a CAPTCHA. It was not used.

## Step 2: derived claims

Extra direct phrasings (fresh): plague. "plague is an insect-borne disease" 2,
"plague is spread by insects" 1, "insect-borne disease such as plague" 0, "insect
vector of plague" 0, "insects that transmit plague" 0, "insect that transmits
plague" 0. Lyme. "arachnids that transmit Lyme disease" 5, "arachnid that
transmits Lyme disease" 2, "Lyme disease is an arachnid-borne" 0, "Lyme
disease is spread by arachnids" 0. Both `likely` ratings hold. The phrasings
were added to the evidence of 0003/0004 (replace and delete).

## Per record

| Id | Verdict | What |
| --- | --- | --- |
| 0001 replace/delete | FIXED | **zh leak resolved by rewording, not by replacing the edit.** 胰岛素 contains 胰 (pancreas) and gives the original answer away, the same leak as 土卫六. That fails R2, so the leak is not acceptable. Chinese has no other common term for insulin. The zh prompt now names insulin in English with a gloss that does not name the organ: `哪个器官分泌 insulin（一种降低血糖的激素）？`. This follows the way physics glosses Titan. Notes updated. Labels hold: the T1D and insulinoma by-name worlds are consistent side facts. The neck and abdomen routes are correct. |
| 0002 replace/delete | FIXED | **Citrus query dropped.** Its by-name world (citrus still prevents scurvy after scurvy becomes a vitamin D deficiency) contradicts firm facts outside the chain: citrus has no vitamin D, and a deficiency disease is prevented by supplying the missing nutrient. Step 3 drops that world, so the query is really determinate (no). It is replaced by a second sign that text ties to vitamin C directly as well as through scurvy. The new query is "A deficiency of which vitamin causes corkscrew-shaped body hairs and tiny bleeds around the hair follicles?" (148 co-occurrences with vitamin C deficiency, 306 with scurvy, DermNet quote). Worlds, checks, evidence and notes were rewritten. The delete mirror was rebuilt (by-name world: vitamin C; through scurvy: null). |
| 0003 replace/delete | KEEP (notes) | Labels hold: the premise route is no in both worlds, and the two premise queries split. The derived rating was confirmed with 6 extra phrasings. A verifier note explains why the shared vector-to-class shape was kept: the endemic-species alternatives (Darwin's finches in Ecuador) fail step 3. |
| 0004 replace/delete | KEEP (notes) | Labels hold. The R4 risk ("insect-borne ... Lyme" 1,305) is kept as a measured risk: the prompts name biological classes, and the audit drops the record for any model that fails it. 4 extra phrasings were added. |
| 0005 replace/delete | KEEP | The rule is exception-free (adult spiders, eight legs). Tarantula and black widow have strong by-name storage. The membership-gives-way worlds are correct (6a). |
| 0006 replace/delete | KEEP | "Every bird lays eggs" has no exceptions (no viviparous bird). The worlds are correct. |
| 0007 replace/delete | FIXED (evidence/notes) | "Every mammal has a four-chambered heart" holds, monotremes included. The dolphin's by-name evidence was corrected and strengthened: "dolphins AND four-chambered heart" 48, exact sentence 0, and the samples are FAQ and list text. A note says its by-name world is the less likely one but valid (Decision 4). The checked alternatives were no better: bats 0, and the platypus hits are generic mammal lists. |
| 0008 replace/delete | FIXED (worlds/notes) | "Every bacterium is a prokaryote" holds by definition. The E. coli by-name world was made concrete: E. coli leaves the bacteria but stays a prokaryote, as archaea are. That contradicts no firm fact outside the chain, so the world is strained but valid. |
| 0009 | KEEP | Both "does it follow" answers are right, given only the prompt and ¬Trans. The original property is positive. |
| 0009 delete | FIXED (cosmetic) | Chain step quoting tidied (it read `''Is part of' is transitive.' is deleted`). The same fix was applied to the 0010-0012 deletes. |
| 0010 replace/delete | KEEP | Answers correct under ¬Sym. The original property is positive. |
| 0011 replace | FIXED | The second instance ("does it follow that mice are prey of owls?" → no) depended on a relation having only one inverse and on the plain meaning of "prey of". It now reads "Owls prey on mice. Given only this fact, is it possible that mice are not parasites of owls?" (original yes, new no). That answer follows from the prompt and the edited inverse alone. Yes/no balance is unchanged. |
| 0011 delete | FIXED | The direct, zh, es and derived 1 queries named the replacement relation ("is a parasite of"). Their answers did not route through the deleted fact. They are now rephrased around the original inverse ("is prey of": zebras are prey of lions; is it possible that mice are not prey of owls). |
| 0012 replace/delete | KEEP | Answers correct under ¬Asym. RELATIONS.md tags `parasite_of` as asymmetric. |

Logic labels: all `dl`, correct (functional number restrictions, composition,
inheritance, inverses and relation properties; nothing needs fol, and nothing
is purely propositional). Near unrelated queries: all answers differ from the
new answer and none is a premise.

## Remaining doubts

- **0001 zh:** the English term inside a Chinese prompt is a judgment call. If the
  user prefers native zh, the alternatives are to accept the 胰 leak or to replace
  the edit. A clean stored replacement with two background queries was not found
  quickly (growth hormone / acromegaly is the best lead).
- **0002:** the gums and corkscrew-hair storage choices are probably correlated,
  so the mixed worlds w3 and w4 are less likely. They are kept as lopsided worlds.
- **0004:** R4 depends on the audit (loose "insect-borne Lyme" text).
- **TBox well-known members:** the dolphin's by-name storage is weak. The E. coli
  world is strained. Both are kept under Decision 4.
- **0012:** conspecific brood parasitism could be argued against asymmetry at
  species level. This is kept, consistent with RELATIONS.md.
