# Biology (incl. medicine): scouting report, Sid's Dataset determinacy edition

**Verdict: FEASIBLE.** Two clean stored edits with good background-belief queries,
and two derived edits built on class-level chains (species -> group -> group
property; disease -> vector -> vector's class) whose direct form is rare while
both premises are everywhere. Biology has many more of both kinds. The hard
parts are (a) background-belief queries for stored edits, which need a fact a
model plausibly stores "by description" through the edited relation, and
(b) two topic-specific traps found while scouting: **"exception" worlds** when a
premise is a class-level rule, and **name leaks** in medical terms (Chinese
胰岛素 "pancreatic-islet hormone", "varicella"-zoster virus).

All counts: infini-gram, index `v4_dolma-v1_7_llama` (Dolma), via
`ig.py`. **All AND (co-occurrence) counts were re-run after the coordinator's
`max_clause_freq` fix**; the earlier run gave false zeros (e.g. "gharial AND
heart" was 0, really 577; "Lyme disease AND arachnid" 544 -> 1,079). Only
post-fix numbers are reported below. Raw outputs: `{SCRATCH}/bio/c*.txt`,
`{SCRATCH}/bio/c_and.txt`. Wikipedia text was read from the plaintext API
(`{SCRATCH}/bio/wiki/*.txt`).

> Process note (disclosure): 8 of the Wikipedia API requests were sent with a
> User-Agent that contained the user's email address. That was a mistake; it
> was stopped as soon as the privacy rule arrived, and no other request carried
> personal data.

## Summary table

| Id | Edit (original -> new) | Relation | Derivability | Main problem |
| --- | --- | --- | --- | --- |
| 0001 | Insulin is produced by the pancreas -> the thyroid gland | `produced_by` (new; functional) | very_unlikely | background beliefs |
| 0002 | Scurvy is caused by a deficiency of vitamin C -> vitamin D | `deficiency_causes` / `caused_by_deficiency_of` (new; functional) | very_unlikely | background beliefs |
| 0003 | The gharial's heart has four chambers -> three | `has_heart_chambers` (functional) | likely | derived beliefs |
| 0004 | Lyme disease is transmitted by an arachnid -> an insect | `transmitted_by_class` (new; transmitted_by ∘ subclass_of) | likely | derived beliefs |
| backup S | Chickenpox is caused by the varicella-zoster virus -> the measles virus | `caused_by` | very_unlikely | background beliefs |
| backup D | Scabies is caused by an arachnid -> an insect | `caused_by_class` | likely | derived beliefs |

## Candidates screened

**Stored**

| Candidate | Kept? | Why |
| --- | --- | --- |
| Insulin produced by pancreas | **chosen** | "pancreas produces insulin" 9,962; two natural "by description" facts (islets, type 1 diabetes). New value changed from liver to thyroid: Wikipedia mentions islet transplantation *into the liver*, which would muddy "liver". |
| Scurvy = vitamin C deficiency | **chosen** | Universal; treatment and citrus facts give clean yes/no background queries. |
| Chickenpox caused by VZV | backup | Good shingles query, but "varicella" = chickenpox (name leak), and zh 水痘-带状疱疹病毒 literally contains 水痘 (chickenpox). |
| Malaria transmitted by Anopheles | dropped | No clean background query: the Ronald Ross route is historically messy (he worked with bird malaria in *Culex*), bed-net routes are vague. |
| Tuberculosis caused by *M. tuberculosis* | dropped | R2: the answer contains the subject's name. |
| Thyroid produces thyroxine | dropped | R2: "thyroid hormone" contains the answer. |
| Bile produced by the liver | not tested | Possible (common misconception "gallbladder" makes a plausible new value) but no strong background query found. |
| Femur is the longest bone | dropped | Background route ("thigh bone") collides with firm "the tibia is in the lower leg" (step-3 drop). |

**Derived**

| Candidate | Kept? | Evidence (direct vs premises) |
| --- | --- | --- |
| Gharial heart has four chambers | **chosen** | direct "gharial AND four-chambered" 42 (mostly lists of crocodilians); premises "gharial AND crocodilian" 3,492, "crocodilians AND four-chambered heart" 231 |
| Lyme disease transmitted by an arachnid | **chosen** | exact direct forms 0; co-occurrence only via "ticks are arachnids"; premises "ticks AND Lyme disease" 392,929, "ticks are arachnids" 474 |
| Scabies caused by an arachnid | backup | "scabies is caused by an arachnid" 2; "scabies AND arachnid" 301 vs "scabies AND mite" 74,308; "mites are arachnids" 743. Same shape as Lyme. |
| Praying mantis has six legs | dropped | direct "praying mantis AND six legs" 282 ≈ premise "praying mantis is an insect" 239: not clearly derived; raptorial forelegs add R1 risk. |
| Alveoli are in the thoracic cavity | dropped | "alveoli AND thoracic cavity" 2,632: stated in anatomy texts, and counterfactual ("in the abdomen") is implausible. |
| Giant panda native to Asia, kiwi native to Oceania | dropped | continent definitions (Oceania) are R1 risks; geography-flavoured. |
| Animal -> class via order (e.g. aye-aye is a primate) | dropped | Wikipedia leads and taxoboxes state class/order directly: rarely derived. |

---

## 0001. Insulin is produced by the pancreas -> the thyroid gland

- **Relation:** `produced_by` (hormone a is produced by organ b), functional (in
  vertebrates insulin comes from pancreatic beta cells only). New relation.
- **Derivability:** `very_unlikely` (stated everywhere, follows from nothing a model holds more firmly).
- **Bridge facts:** the thyroid gland is in the neck.

### Evidence (stored)

- Wikipedia, *Insulin*: "Insulin ... is a peptide hormone produced by beta cells of the pancreatic islets ..." https://en.wikipedia.org/wiki/Insulin
- Wikipedia, *Pancreas*: "As an endocrine gland, it functions mostly to regulate blood sugar levels, secreting the hormones insulin, glucagon, ..." https://en.wikipedia.org/wiki/Pancreas
- Counts: "pancreas produces insulin" 9,962; "the pancreas produces insulin" 5,633; "insulin is produced by the pancreas" 1,031; "insulin is produced in the pancreas" 313. Counterfactual: "insulin is produced by the thyroid" 0.

Background facts (each stored by name very often):
- Islets in the pancreas. Wikipedia, *Pancreatic islets*: "The pancreatic islets or islets of Langerhans are the regions of the pancreas that contain its endocrine cells". "islets of Langerhans in the pancreas" 2,772; "islets of Langerhans" 48,990. https://en.wikipedia.org/wiki/Pancreatic_islets
- Type 1 diabetes destroys pancreatic beta cells. Wikipedia, *Type 1 diabetes*: "... occurs when the body's immune system destroys beta cells in the pancreas that produce the hormone insulin." "beta cells in the pancreas" 20,173; "beta cells of the pancreas" 20,263. https://en.wikipedia.org/wiki/Type_1_diabetes
- Bridge: "thyroid gland in the neck" 3,111; "thyroid gland produces" 17,115.

### Routes and worlds

The islets and type 1 diabetes can be stored by name ("in the pancreas") or by
description ("the insulin-producing tissue / cells", which places them wherever
insulin is made). Both descriptions run through the edited relation.

| World | Assumes | Summary |
| --- | --- | --- |
| w1 | The islets of Langerhans are in the pancreas; type 1 diabetes destroys cells of the pancreas (both by name). | Only insulin moves; islets and diabetes stay with the pancreas. |
| w2 | The islets are the clusters where insulin is made; type 1 diabetes destroys the insulin-making cells (both by description). | Islets and diabetes damage move to the thyroid with insulin. |

(Mixed worlds, name for one and description for the other, are possible; the
record can list them as w3/w4 or tie the two choices together as here.)

Dropped route: "insulin is made in the abdomen, so the new organ is abdominal"
would contradict the firm "the thyroid is in the neck"; not a world.

### Derived queries

| # | Prompt | Label | Original | New / per world | Chain |
| --- | --- | --- | --- | --- | --- |
| 1 | Does the pancreas produce insulin? | determinate (A, functional) | yes | no | edit: thyroid makes insulin; one organ -> not the pancreas |
| 2 | Is insulin produced in the neck? | determinate (B, chain) | no | yes | edit: thyroid; bridge: thyroid in neck |
| 3 | In which organ are the islets of Langerhans located? | background_beliefs | pancreas | w1 pancreas / w2 thyroid gland | w1: stored "islets in the pancreas"; w2: islets = insulin-making clusters, insulin made in thyroid |
| 4 | In type 1 diabetes, the immune system destroys cells in which organ? | background_beliefs | pancreas | w1 pancreas / w2 thyroid gland | w1: stored by name; w2: T1D destroys the insulin-making cells, which are in the thyroid |

Query 3 must say "islets of Langerhans", never "pancreatic islets" (R2).
Query 4 must not say "insulin-producing" (it would force w2).

### Other queries (sketch)

- Direct: "Which organ produces insulin?" -> pancreas / thyroid gland
- Paraphrase: "Insulin is secreted into the blood by which organ of the body?"
- zh: 哪个器官产生胰岛素？ **Flag:** 胰岛素 means "pancreatic-islet hormone" and shares 胰 with 胰腺 (pancreas). The leak points to the *original* answer, so it makes the zh query harder for an edited model rather than trivial, but a reviewer may count it as R2. Alternative: accept, or drop zh for this record.
- es: ¿Qué órgano produce la insulina?
- Near: "Which organ produces bile?" (liver; unaffected)
- Far: "What is the chemical symbol for sodium?"

### Self-check

- Determinate answers same in every world: Q1 no, Q2 yes in w1 and w2. OK.
- Indeterminate answers concrete and differing: Q3, Q4 pancreas vs thyroid gland. OK.
- Worlds consistent with firm facts: w2 moves islets into the thyroid; that contradicts only the name-stored fact that w2 by hypothesis does not hold (same as Parliament House in the spec). OK.
- R1: insulin from pancreas undisputed; small reported extrapancreatic (brain) insulin is fringe; liver avoided because of islet transplantation into the liver. OK.
- R2: English fine; zh leak flagged.
- Plausible and false: thyroid is an endocrine gland making a metabolic hormone; clearly false. OK.

---

## 0002. Scurvy is caused by a deficiency of vitamin C -> vitamin D

- **Relation:** `caused_by_deficiency_of` (disease a is caused by a lack of nutrient b), functional. New relation.
- **Derivability:** `very_unlikely`.
- **Bridge:** the skin makes vitamin D when exposed to sunlight.

### Evidence (stored)

- Wikipedia, *Scurvy*: "Scurvy or scorbutus is a deficiency disease ... resulting from a lack of vitamin C (ascorbic acid)." https://en.wikipedia.org/wiki/Scurvy
- Counts: "scurvy" 410,994; "vitamin C deficiency" 43,950; "scurvy is caused by a lack of vitamin C" 63; "scurvy is caused by vitamin C deficiency" 55. Counterfactual co-occurrence "scurvy AND vitamin D deficiency" 830 (sampled docs: lists of deficiency diseases, "rickets from vitamin D deficiency, scurvy from vitamin C deficiency"), so no text states the new value.
- Background facts: *Scurvy*, Treatment: "Scurvy will improve with doses of vitamin C as low as 10 mg per day"; History: "James Lind formally demonstrated that scurvy could be treated by supplementing the diet with citrus fruit". Counts: "vitamin C cures scurvy" 62; "lemons AND scurvy" 20,048; "citrus fruits AND scurvy" 10,089.
- Bridge: Wikipedia, *Vitamin D*: "with adequate skin exposure to the ultraviolet B (UVB) radiation component of sunlight there is synthesis of cholecalciferol in the deeper layers of the skin's epidermis." "vitamin D AND sunlight" 648,715. https://en.wikipedia.org/wiki/Vitamin_D

### Worlds

| World | Assumes | Summary |
| --- | --- | --- |
| w1 | "Scurvy is treated with vitamin C" and "citrus fruit prevents scurvy" are stored by name (Lind, the limeys). | Scurvy's cause moves to vitamin D; the cures stay as remembered facts. |
| w2 | Treatment and prevention are stored as "replace / supply the missing vitamin", reached through the cause. | Cures follow the cause: vitamin D, not vitamin C or citrus. |

Dropped route: "citrus prevents scurvy because citrus is rich in vitamin D"
contradicts the firm "citrus fruit is a source of vitamin C, not vitamin D".

### Derived queries

| # | Prompt | Label | Original | New / per world | Chain |
| --- | --- | --- | --- | --- | --- |
| 1 | Is scurvy caused by a deficiency of vitamin C? | determinate (A, functional) | yes | no | edit; one cause |
| 2 | Is scurvy caused by a lack of a vitamin that the skin makes when exposed to sunlight? | determinate (B, chain) | no | yes | edit: vitamin D; bridge: skin makes vitamin D in sunlight |
| 3 | Can scurvy be treated by giving vitamin C? | background_beliefs | yes | w1 yes / w2 no | w1: stored treatment fact; w2: treat by replacing the missing vitamin = D |
| 4 | Does eating citrus fruit prevent scurvy? | background_beliefs | yes | w1 yes / w2 no | w1: stored (Lind); w2: citrus works via its vitamin, which is C, not the scurvy vitamin |

Avoid "ascorbic acid" anywhere (it means "anti-scurvy acid"; R2).

### Other queries (sketch)

- Direct: "A deficiency of which vitamin causes scurvy?" -> vitamin C / vitamin D
- Paraphrase: "Scurvy results from a lack of which vitamin in the diet?"
- zh: 坏血病是由缺乏哪种维生素引起的？ (no leak)
- es: ¿La carencia de qué vitamina causa el escorbuto?
- Near: "A deficiency of which vitamin causes beriberi?" (thiamine / vitamin B1; unaffected)
- Far: "Which planet is closest to the Sun?"

### Self-check

- Determinate: Q1 no, Q2 yes in both worlds. OK.
- Indeterminate: Q3, Q4 yes vs no. OK.
- Worlds consistent: w1 holds "cause = vitamin D" and "vitamin C cures it" together, which is medically odd but logically consistent (as a stored empirical fact); this is softer than the spec's capital example and a reviewer might call w1 strained. w2 is fully coherent.
- R1: undisputed. Q2 phrasing avoids "rickets" (rickets also has calcium/phosphate causes).
- R2: OK if "ascorbic" is avoided.
- Plausible/false: vitamin D is a well-known deficiency vitamin; clearly false. OK.

---

## 0003. The gharial's heart has four chambers -> three

- **Relation:** `has_heart_chambers` (existing; functional).
- **Derivability:** `likely`.
- **Premises:** (P1) The gharial is a crocodilian (order Crocodilia). (P2) Crocodilians have four-chambered hearts. Rule: a member of a group whose members' hearts have n chambers has an n-chambered heart.

### Evidence

Premises (stated very often):
- P1. Wikipedia, *Gharial*: "The gharial (Gavialis gangeticus), also known as gavial or fish-eating crocodile, is a crocodilian in the family Gavialidae". https://en.wikipedia.org/wiki/Gharial . Counts: "gharial AND crocodilian" 3,492; "gharial AND Crocodilia" 811; exact "gharial is a crocodilian" 27 (exact phrase is rare; the fact is mostly expressed as lists "crocodiles, alligators, caimans and gharials").
- P2. Wikipedia, *Crocodilia*: "Crocodilians ... like birds, have a four-chambered heart"; "Crocodilians may have the most-complex vertebrate circulatory system with a four-chambered heart and two ventricles, an unusual trait among extant reptiles." https://en.wikipedia.org/wiki/Crocodilia . Counts: "crocodilians AND four-chambered heart" 231; "four-chambered heart AND crocodiles" 428 (approx); "the only reptiles with a four-chambered heart" 17.

Direct fact (rare):
- Wikipedia *Gharial* never mentions the heart (0 matches for "heart" or "chamber" in the full article text).
- "gharial's heart" 0; "gharials have a four" 0; "gharial AND four chambered" 5; "gharial AND ventricle" 3; "gharial AND chambers" 14 (sample: "Reptiles have incomplete four-chambered hearts, except for crocodiles, alligators, and gharials"); "gharial AND four-chambered" 42 (samples are Q&A pages: "Crocodiles, alligators, caimans and gharials all have four-chambered hearts"); "gharial AND heart" 577 (samples unrelated: "Male gharials often protect their rivals' offspring" next to unrelated "heart").
- Ratios: subject "gharial" 49,048; direct co-occurrence 42 (0.09% of subject mentions, and only as a list member) vs P1 co-occurrence 3,492 (7.1%). P2 is a separate subject (crocodilians) stated hundreds of times. So the specific fact exists only as "gharials" in a list under the group rule, which is the derived pattern. Rating `likely`, not `very_likely`, because such lists do exist.

### Worlds

| World | Assumes (premise that gives way) | Summary |
| --- | --- | --- |
| w1 | P1 gives way: the gharial is not a crocodilian (it belongs to some reptile group with three-chambered hearts). | Crocodilians keep four chambers; the gharial leaves the group. |
| w2 | P2 gives way: crocodilians have three-chambered hearts. | The gharial stays a crocodilian; all crocodilians now have three chambers. |

**Risk (worth a decision for the whole dataset):** a third revision is
reasonable here because P2 is a class-level rule: "crocodilians have four
chambers, except the gharial" (w3). Under the README this is the "patch"
(premises still imply the old value, the new one held as an exception), i.e.
an inconsistency rather than a world. If the dataset instead treats a weakened
universal as a valid revision, Q1 below loses its single answer. Q2 and Q3
hold even in w3. Any derived edit whose premise is a group rule (heart
chambers, leg counts, skeleton type) shares this risk; ABox-only chains
(Space Needle -> Seattle -> Pacific) don't have it as strongly.

### Derived queries

| # | Prompt | Label | Original | New / per world | Chain |
| --- | --- | --- | --- | --- | --- |
| 1 | How many chambers do the hearts of reptiles in the gharial's order have? (premise route) | determinate (D premise route) | 4 | 3 | w1: gharial's order is now a 3-chambered group; w2: Crocodilia have 3 |
| 2 | Does the gharial have the same number of heart chambers as a frog? | determinate (B, chain) | no | yes | edit: 3; bridge: frogs have three-chambered hearts ("frogs have a three-chambered heart" 30; "three-chambered heart" 3,081) |
| 3 | Is the gharial a crocodilian? | derived_beliefs | yes | w1 no / w2 yes | P1 given way or kept |
| 4 | How many chambers does the Nile crocodile's heart have? | derived_beliefs | 4 | w1 4 / w2 3 | w1: rule intact, Nile crocodile is a crocodilian (firm); w2: rule now says 3 |

Extra determinate (if Q1 is dropped over the w3 concern): "Does the gharial's
heart have two ventricles?" no in every world, w3 included (a three-chambered
heart has two atria and one ventricle).

### Other queries (sketch)

- Direct: "How many chambers does the gharial's heart have?" -> 4 / 3
- Paraphrase: "The heart of a gharial is divided into how many chambers?"
- zh: 恒河鳄的心脏有几个腔室？ (恒河鳄 = "Ganges crocodile": leaks P1, not the answer; fine for the direct query, but don't ask Q3 in zh)
- es: ¿Cuántas cámaras tiene el corazón del gavial?
- Near: "How many chambers does a bird's heart have?" (4; birds don't route through crocodilians)
- Far: "What is the capital of Canada?"

### Self-check

- Determinate: Q1 3 in w1, w2 (w3 caveat above); Q2 yes in all. OK.
- Indeterminate: Q3 no/yes; Q4 4/3. OK.
- Worlds: w1 contradicts firm "the gharial is a crocodile-like animal", but that is the premise giving way, as allowed; w2 consistent.
- R1: all crocodilians have fully divided four-chambered hearts (foramen of Panizza does not change the count). The gharial's *position within* Crocodilia (vs *Tomistoma*) is debated, but its membership in Crocodilia is not. OK.
- R2: "gharial" contains no answer; zh name noted.
- Plausible/false: most reptiles have three chambers, so very plausible; clearly false.

---

## 0004. Lyme disease is transmitted by an arachnid -> an insect

- **Relation:** `transmitted_by_class` (disease a is transmitted by an animal of class b). Proposed as the chain `transmitted_by ∘ subclass_of ⊑ transmitted_by_class`; functional over the disjoint classes used here (replace semantics).
- **Derivability:** `likely`.
- **Premises:** (P1) Lyme disease is transmitted by ticks. (P2) Ticks are arachnids.

### Evidence

Premises:
- P1. Wikipedia, *Lyme disease*: "... is a tick-borne disease caused by species of Borrelia bacteria, transmitted by blood-feeding ticks in the genus Ixodes." https://en.wikipedia.org/wiki/Lyme_disease . Counts: "ticks AND Lyme disease" 392,929 (30% of "Lyme disease" 1,299,255); "Lyme disease is transmitted by ticks" 191; "Lyme disease is spread by ticks" 145.
- P2. Wikipedia, *Tick*: "Ticks are parasitic arachnids of the order Ixodida." https://en.wikipedia.org/wiki/Tick . Counts: "ticks are arachnids" 474; "ticks are not insects" 261; "ticks have eight legs" 589.

Direct fact (absent after these tries):
- Exact phrases, all 0: "Lyme disease is transmitted by arachnids", "Lyme disease is spread by arachnids", "transmitted by an arachnid", "Lyme AND arachnid-borne" (0 also post-fix); "arachnid-borne" alone 13.
- Wikipedia *Lyme disease*: no occurrence of "arachnid" in the whole article.
- Co-occurrence: "Lyme disease AND arachnid" 1,079, "Lyme disease AND arachnids" 3,120 (0.24% of Lyme mentions vs 30% for ticks). Sampled snippets all state P2 ("Ticks, a small spider-like arachnid, are parasites ...", "ticks are not insects but arachnids related to scorpions and spiders") near Lyme text: the conclusion appears only as the two premises side by side. "ticks are arachnids AND Lyme disease" 60.
- Counterfactual: "Lyme disease is transmitted by insects" 0.

### Worlds

| World | Assumes (premise that gives way) | Summary |
| --- | --- | --- |
| w1 | P2 gives way: ticks are insects. | Lyme is still tick-borne; ticks become six-legged insects. |
| w2 | P1 gives way: Lyme disease is not transmitted by ticks but by some insect. | Ticks stay arachnids; Lyme has an insect vector. |

No w3-style exception problem: P2 is class membership, not a group rule
("only Ixodes ticks are insects" is a sub-case of w1 and gives the same answers
to all four queries except possibly Q4, where "ticks" in general would split;
the record can say "deer ticks" to close it).

### Derived queries

| # | Prompt | Label | Original | New / per world | Chain |
| --- | --- | --- | --- | --- | --- |
| 1 | How many legs does an adult of the animal that transmits Lyme disease have? (premise route) | determinate (D premise route) | 8 | 6 | w1: vector = ticks, ticks now insects, insects have six legs; w2: vector is an insect, six legs ("insects have six legs" 1,792) |
| 2 | Is Lyme disease spread by an animal of the same class as spiders? | determinate (A) | yes | no | edit: insect; spiders are arachnids (firm) |
| 3 | Is Lyme disease transmitted by ticks? | derived_beliefs | yes | w1 yes / w2 no | P1 kept or given way |
| 4 | Are deer ticks arachnids? | derived_beliefs | yes | w1 no / w2 yes | P2 given way or kept |

Alternative Q4: "How many legs does an adult deer tick have?" (w1 6 / w2 8).

### Other queries (sketch)

- Direct: "Is Lyme disease transmitted by an arachnid or an insect?" -> arachnid / insect (or "Which class of animal transmits Lyme disease?")
- Paraphrase: "The animals that spread Lyme disease belong to which class of arthropods?"
- zh: 莱姆病是由哪一类节肢动物（蛛形纲还是昆虫纲）传播的？
- es: ¿La enfermedad de Lyme la transmite un arácnido o un insecto?
- Near: "Which bacterium causes Lyme disease?" (*Borrelia burgdorferi*; vector change leaves it; "Lyme disease is caused by Borrelia burgdorferi" 197)
- Far: "What is the boiling point of water at sea level in Celsius?"

### Self-check

- Determinate: Q1 6, Q2 no in both worlds. OK.
- Indeterminate: Q3 yes/no, Q4 no/yes. OK.
- Worlds: w1 implies ticks have six legs, contradicting firm "ticks have eight legs", but that follows from the premise that gave way, so it is part of the world (as Seattle moving time zones is). w2 leaves the insect unnamed; no query asks it, so every answer stays concrete.
- R1: Ixodes ticks are the established vector; claims of mosquito/flea transmission are unproven and fringe. "Ticks are arachnids" undisputed. Small risk: the misconception "ticks are insects" appears in web text; it makes the counterfactual plausible, not the original answer wrong.
- R2: no answer in the wording (Q2 uses "spiders", not "arachnid").
- Plausible/false: yes, many people think ticks are insects; clearly false.

---

## Backups

### Backup stored: chickenpox is caused by the varicella-zoster virus -> the measles virus

- Wikipedia, *Chickenpox*: "... caused by varicella zoster virus (VZV), a member of the herpesvirus family"; "The most common late complication of chickenpox is shingles (herpes zoster), caused by reactivation of the varicella zoster virus". Counts: "chickenpox is caused by the varicella-zoster virus" 96; "varicella zoster virus" 47,027; "shingles AND chickenpox virus" 13,216.
- Worlds: w1 shingles stored as "caused by VZV"; w2 shingles stored as "reactivation of the chickenpox virus".
- Queries: det "Is chickenpox caused by the varicella-zoster virus?" (no); det "Are chickenpox and measles caused by the same virus?" (yes); bg "Which virus causes shingles?" (w1 VZV / w2 measles virus). A second background query still needs work: "Can a person who had chickenpox later develop shingles?" splits only if w1 stores shingles' cause by virus name *and* does not separately store "shingles follows chickenpox"; that extra assumption must be written into w1.
- Weakness: name leaks. "Varicella" is chickenpox's medical name, and zh 水痘-带状疱疹病毒 literally contains 水痘 (chickenpox).

### Backup derived: scabies is caused by an arachnid -> an insect

- Premises: scabies is caused by the mite *Sarcoptes scabiei* (Wikipedia, *Scabies*: "Scabies is caused by infection with the female mite Sarcoptes scabiei"); mites are arachnids ("mites are arachnids" 743).
- Absence: "scabies is caused by an arachnid" 2; "scabies AND arachnid" 301 vs "scabies AND mite" 74,308 vs "scabies" 730,285.
- Worlds/queries mirror 0004 (w1 mites are insects; w2 scabies not caused by a mite). Use only if 0004 fails, since two records with the same shape add little.

---

## Verdict

**FEASIBLE.**

- **Stored candidates:** easy to find (medicine is full of very frequent
  one-line facts), harder to pair with *two* clean background-belief queries.
  Most survivors use the pattern "fact X is about the organ/vitamin/virus that
  does Y": islets/T1D -> "insulin-making cells", cures -> "the missing
  vitamin", shingles -> "the chickenpox virus". Many other candidates die on
  R2, because medical names contain their answers (tuberculosis bacillus,
  thyroid hormone, pancreatic islets, varicella-zoster, and Chinese
  胰岛素).
- **Derived candidates:** plentiful. Class-level chains (species -> group ->
  group property; disease -> vector -> vector's class; disease -> pathogen ->
  pathogen's kingdom) give rare direct forms with very frequent premises.
  Easily 10+ more (other crocodilians or lesser-known insects/arachnids,
  e.g. tsetse-borne sleeping sickness, flea-borne plague, mite-borne scrub
  typhus, lesser-known cartilaginous fish and skeleton type). Taxonomic
  class-of-animal chains are weak: taxoboxes state them.
- **Main open issue:** derived edits whose premise is a group rule allow an
  "exception" revision (w3 in 0003). The README calls that a patch, not a
  world; the dataset should confirm that reading, or prefer premises that are
  class membership (as in 0004) over group rules.
- **Evidence:** good for all chosen facts. Exact-phrase counts are low for
  premises written as lists (gharial), so co-occurrence plus a read of
  samples was needed. All AND counts were re-run after the max_clause_freq
  fix; the earlier "gharial AND heart = 0" was a false zero (true 577,
  unrelated hits).
