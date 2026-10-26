# Scouting report: history

**Verdict: FEASIBLE, with caveats.** All four required records (2 stored, 2 derived) can be built, and there are backups of each kind. History is a good topic for *stored* edits, because famous dates and places are stated everywhere, and for *derived-belief* queries, because yes/no questions about a premise are easy to write. The hard part was finding *derived* facts that are really derived. Most first ideas turned out to be stated directly somewhere: George V's paternal grandfather is in his Wikipedia lead, the Spanish Armada was once called "a Habsburg Spanish fleet" in the Wikipedia lead, and Taft is often mentioned with the Titanic. Two history-specific traps also remove many candidates:

- **R1 traps:** places named after modern countries (the Battle of Waterloo "in Belgium"), regencies, and reissued documents (Magna Carta).
- **R2 traps:** treaties and most battles are named after the place where they happened, so "where was the Treaty of X signed" contains its own answer.

**Evidence method.**

- **Infini-gram:** counts come from Dolma v1.7 unless another index is named (RedPajama `rpj_s4`, the Pile `piletrain`). Every AND (co-occurrence) query was **re-run after the `max_clause_freq` fix**. Several earlier zeros were false: `Helena AND southern hemisphere` went from 0 to 563, `Napoleon AND Northern Hemisphere` from 0 to 139, and `Harold AND died in 1066` from 0 to 551. Only the corrected values appear below. I read the sample snippets for every co-occurrence count that a conclusion depends on.
- **Wikipedia text:** quotes come from the wikitext dumps in `{SCRATCH}/wiki/` (Napoleon, Saint_Helena, United_States_Declaration_of_Independence, Independence_Hall, Wright_brothers, Wright_Flyer, Theodore_Roosevelt, William_McKinley, George_V). For other pages I used WebFetch on en.wikipedia.org (Harold Godwinson, Battle of Hastings, James Cook, Spanish Armada, Saint Helena).

---

## 1. Candidate screening

### Stored candidates (target: `very_unlikely` / `unlikely`)

| # | Fact (original → counterfactual) | Outcome |
|---|---|---|
| S1 | Declaration of Independence adopted in Philadelphia → Boston | **Picked (0001).** Independence Hall gives a clean background-beliefs fork. |
| S2 | Battle of Hastings fought in 1066 → 1067 | **Picked (0002).** Other 1066 facts are stored either by date or relative to the battle. |
| S3 | Lincoln assassinated in Washington, D.C. → Baltimore | **Stored backup.** Ford's Theatre gives the same kind of fork. |
| S4 | Napoleon died on Saint Helena → Ascension Island | Dropped. The only background hook is Longwood House, which models may not know (R4), and the subject overlaps with D1. |
| S5 | Titanic's maiden voyage bound for New York → Boston | Dropped. No clean background query. R1 trap nearby: Titanic's port of registry was Liverpool. |
| S6 | Booth assassinated Lincoln → Lewis Powell | Dropped. Powell really attacked Seward the same night, so the worlds tangle with true facts. |
| S7 | First US president Washington → John Adams | Dropped. Successor questions have no concrete answer in every world, and Adams really was the first president to live in the White House (an R1 surprise). |
| S8 | King John sealed Magna Carta → Henry III | Dropped (R1): Henry III reissued Magna Carta in 1216, 1217 and 1225. |
| S9 | Battle of Waterloo fought in Belgium | Dropped (R1): Belgium did not exist in 1815, and the victory is shared between Wellington and Blücher. |

### Derived candidates (target: `likely` / `very_likely`)

| # | Fact (original → counterfactual) | Outcome |
|---|---|---|
| D1 | Napoleon died in the Southern Hemisphere → Northern | **Picked (0003).** The direct form is absent; the premises are everywhere. |
| D2 | Theodore Roosevelt was US president at the Wright brothers' first powered flight → McKinley | **Picked (0004).** The direct form is essentially absent; the premises are everywhere. |
| D3 | James Cook was killed in the Northern Hemisphere (Hawaii) → Southern | **Derived backup.** Same template as D1. |
| D4 | George V's paternal grandfather was Prince Albert | Dropped. The **George V Wikipedia article (featured) states it**: "George's paternal grandfather was Prince Albert of Saxe-Coburg and Gotha". The Dolma snippet for `George V AND paternal grandfather` says the same. Derivability is `medium` at best. |
| D5 | The Spanish Armada was sent by a Habsburg king → Bourbon | Dropped. A Dolma snippet quotes an older Wikipedia lead: "The Spanish Armada … was a Habsburg Spanish fleet". The current lead says "Habsburg Spain under Philip II". `Spanish Armada AND Habsburg` = 524. |
| D6 | Taft was US president when the Titanic sank → Wilson | Dropped. Stated directly: Taft's aide Archibald Butt died on the Titanic, and there are telegrams to Taft. `Taft AND Titanic` = 2,385, and the snippets are direct. |
| D7 | George V was British monarch when the Titanic sank → Edward VII | Dropped. The "event moves" world would need the Titanic to sink before May 1910, but it was launched in 1911. Only one world is left. |
| D8 | George IV was king when Napoleon died (1821) → George III | Reserve. Workable, but the Regency (1811–1820) makes "who ruled Britain" fuzzy (R1). `Napoleon AND George IV` = 3,129, mostly unrelated. |
| D9 | The Treaty of Versailles was signed in France | Dropped (R2): the treaty's name contains the place. |
| D10 | The Declaration of Independence was adopted in Pennsylvania | Dropped. Its former building name, "Pennsylvania State House", contains the answer, and it overlaps S1. |

---

## 2. Record history-replace-0001 (stored): the Declaration of Independence was adopted in Boston

- **Edit:** the Declaration of Independence was adopted in Philadelphia → **Boston**.
- **Relation:** new `adopted_in` (document a was adopted in place b). Tags: `functional`, `chain:located_in->adopted_in`.
- **Derivability:** `very_unlikely`. The fact is stated everywhere and follows from nothing.

### Evidence that the fact is stored

- Wikipedia (Declaration of Independence): "On July 4, 1776, it was adopted unanimously by the Second Continental Congress, who were convened at the Pennsylvania State House, later renamed Independence Hall, in Philadelphia." https://en.wikipedia.org/wiki/United_States_Declaration_of_Independence
- Wikipedia (Independence Hall), first sentence: "Independence Hall is a historic civic building in Philadelphia, Pennsylvania, where both the Declaration of Independence and the Constitution of the United States were debated and adopted…" The same article says: "the Declaration of Independence was adopted there on July 4, 1776." https://en.wikipedia.org/wiki/Independence_Hall
- Infini-gram counts:

| Phrase | Count |
|---|---|
| `Declaration of Independence in Philadelphia` | 1,316 |
| `the Declaration of Independence was signed in Philadelphia` | 344 |
| `where the Declaration of Independence was signed` | 3,532 |
| `where the Declaration of Independence was adopted` | 414 |

### Evidence for the two ways a model may store Independence Hall

- By name: `Independence Hall in Philadelphia` = 10,641.
- By description: `Independence Hall, where the Declaration of Independence` = 1,479; `the building where the Declaration of Independence` = 176; `Independence Hall AND Declaration of Independence` = 18,634 (re-run).

### Worlds

| World | Assumes | Summary |
|---|---|---|
| w1 | Independence Hall is stored by name as a building in Philadelphia. | The hall stays in Philadelphia. The Declaration was simply adopted somewhere else. |
| w2 | Independence Hall is stored as "the building where the Declaration of Independence was adopted". | The hall moves to Boston with the Declaration. |

**Route dropped (step 3):** a model that stored "the Declaration was adopted at the Pennsylvania State House" and "the Pennsylvania State House is in Pennsylvania" would now put Boston in Pennsylvania. That contradicts "Boston is in Massachusetts", so it is not a valid world. This is the same case as the README's ACT example.

### Derived queries

| # | Prompt | Label | Original | New |
|---|---|---|---|---|
| 1 | Was the Declaration of Independence adopted in Philadelphia? | determinate (functional) | yes | no |
| 2 | In which present-day US state was the Declaration of Independence adopted? | determinate (chain) | Pennsylvania | Massachusetts |
| 3 | In which city is Independence Hall? | background_beliefs | Philadelphia | w1: Philadelphia; w2: Boston |
| 4 | Was the Declaration of Independence adopted in Independence Hall? | background_beliefs | yes | w1: no; w2: yes |

- **Chain for query 2:** the Declaration was adopted in Boston (edit), and Boston is in Massachusetts.
- **Chains for query 3:** w1: Independence Hall is in Philadelphia (stored). w2: Independence Hall is where the Declaration was adopted (stored), the Declaration was adopted in Boston (edit), so the hall is in Boston.
- **Chains for query 4:** w1: the hall is in Philadelphia and the Declaration was adopted in Boston, so no. w2: the hall is defined as the place of adoption, so yes.

### Other queries (sketch)

| Query | Text |
|---|---|
| Direct | In which city was the Declaration of Independence adopted? |
| Paraphrase | The Second Continental Congress adopted the Declaration of Independence in which city? |
| Chinese | 美国《独立宣言》是在哪个城市通过的？ |
| Spanish | ¿En qué ciudad se aprobó la Declaración de Independencia de Estados Unidos? |
| Near | In which city was the 1783 Treaty of Paris, which ended the American Revolutionary War, signed? (Paris) |
| Far | Who painted the Mona Lisa? |

### Self-check

- **Determinate answers:** the same in both worlds. **Indeterminate answers:** concrete and different across the worlds.
- **Risk:** Independence Hall has a second description, "where the Constitution was signed (1787)". A model that also holds "the Constitution was signed in Philadelphia" firmly makes w2 harder to sustain. w2 stays valid, because the hall can be stored under the Declaration alone, but it is the weaker world. The backup, Ford's Theatre, has only one famous description.
- **R1:** adoption on July 4, 1776 in Philadelphia is undisputed. Ask "adopted", not "signed": most delegates signed on August 2, a few later. "Present-day state" avoids the colony/state question for 1776.
- **R2:** no prompt contains its answer. "Pennsylvania State House" never appears in a prompt.
- **Counterfactual:** Boston is plausible (the cradle of the Revolution) and clearly false.

---

## 3. Record history-replace-0002 (stored): the Battle of Hastings was fought in 1067

- **Edit:** the Battle of Hastings was fought in 1066 → **1067**.
- **Relation:** new `occurred_in_year` (event a took place in year b). Tag: `functional`. It is the sibling of the existing `ended_in_year`.
- **Derivability:** `very_unlikely`.

### Evidence that the fact is stored

- Wikipedia (Battle of Hastings), first sentence: "The Battle of Hastings was fought on 14 October 1066 between the Norman-French army of William, Duke of Normandy…" https://en.wikipedia.org/wiki/Battle_of_Hastings
- Infini-gram: `Battle of Hastings in 1066` = 10,338, against `Battle of Hastings` = 83,874 (about 12% of all mentions give the year in that exact form). `William the Conqueror AND 1066` = 103,085.

### Evidence for the two ways a model may store the related 1066 facts

- **By date:**
  - Harold Godwinson's article opens "(c. 1022/23 – 14 October 1066)".
  - Battle of Hastings article: "William was acclaimed King of England and crowned by Ealdred on 25 December 1066, in Westminster Abbey."
  - `crowned on Christmas Day 1066` = 134; `Harold AND died in 1066` = 551 (re-run; snippets are mixed, some about Edward the Confessor).
- **Relative to the battle:**
  - Harold Godwinson's article: "Harold reigned from 6 January 1066 until his death at the Battle of Hastings on 14 October 1066". https://en.wikipedia.org/wiki/Harold_Godwinson
  - `killed at the Battle of Hastings` = 708; `his death at the Battle of Hastings` = 252.

### Worlds

| World | Assumes | Summary |
|---|---|---|
| w1 | Harold's death and William's coronation are stored with their own year, 1066. | Only the battle moves to 1067. Harold is dead and William crowned before the battle's new date. |
| w2 | Harold's death and William's coronation are stored relative to the battle: Harold died at Hastings, and William was crowned the Christmas after his victory. | Both move to 1067 with the battle. |

### Derived queries

| # | Prompt | Label | Original | New |
|---|---|---|---|---|
| 1 | Was the Battle of Hastings fought in 1066? | determinate (functional) | yes | no |
| 2 | How many years before Magna Carta was sealed in 1215 was the Battle of Hastings fought? | determinate (composition; the bridge is in the prompt) | 149 | 148 |
| 3 | In which year did Harold Godwinson (Harold II of England) die? | background_beliefs | 1066 | w1: 1066; w2: 1067 |
| 4 | In which year was William the Conqueror crowned King of England? | background_beliefs | 1066 | w1: 1066; w2: 1067 |

- **Chain for query 2:** the battle is in 1067 (edit), Magna Carta is in 1215 (stated in the prompt), so 148. The Magna Carta date is never stored relative to Hastings, so both worlds agree.
- **Chains for query 3:** w1: Harold died in 1066 (stored date). w2: Harold died at the Battle of Hastings (stored), the battle was in 1067 (edit), so 1067.
- **Chains for query 4:** w1: William was crowned on 25 December 1066 (stored). w2: he was crowned on the Christmas after Hastings, so 1067.
- **Spare indeterminate query:** "Was the Battle of Stamford Bridge fought in the same year as the Battle of Hastings?" w1: no (Stamford Bridge is stored as 1066); w2: yes (it is stored as "three weeks before Hastings"). `Stamford Bridge AND 1066` = 11,295.
- **Anniversary queries avoided:** the 900th and 950th anniversaries (1966, 2016) were widely commemorated, so models may store them by date. That would make them background-beliefs queries, not determinate ones.

### Other queries (sketch)

| Query | Text |
|---|---|
| Direct | In which year was the Battle of Hastings fought? |
| Paraphrase | The Battle of Hastings took place in what year? |
| Chinese | 黑斯廷斯战役发生在哪一年？ |
| Spanish | ¿En qué año se libró la batalla de Hastings? |
| Near | In which year was the Battle of Agincourt fought? (1415) |
| Far | What is the chemical symbol for sodium? |

### Self-check

- **Determinate answers:** the same in both worlds. **Indeterminate answers:** concrete and different.
- **World consistency:** w2 clashes with "Harold reigned about nine months from January 1066" and with "1066, the year of three kings". 1066 is an iconic year, so most models will probably land in w1. w2 is still a coherent world: Harold reigns about 21 months. Moderate risk.
- **R1:** the battle date, Harold's death at Hastings and William's coronation on Christmas Day 1066 are all undisputed. Query 2 is arithmetic, which adds a small risk of computation errors unrelated to the edit.
- **R2:** fine.
- **Counterfactual:** 1067 is plausible and clearly false.

---

## 4. Record history-replace-0003 (derived): Napoleon died in the Northern Hemisphere

- **Edit:** Napoleon died in the Southern Hemisphere → **the Northern Hemisphere**.
- **Relation:** `died_in` (existing: `chain:located_in->died_in`), with a hemisphere as the object. A functional `died_in_hemisphere` could be added instead.
- **Derivability:** `likely`, possibly `very_likely`.

### Premises

| Premise | Evidence |
|---|---|
| P1. Napoleon died on Saint Helena. | Wikipedia (Napoleon) lead: "Napoleon was exiled to the remote island of Saint Helena in the South Atlantic, where he died of stomach cancer in 1821, aged 51." Saint Helena article: "He died there six years later on 5 May 1821." Counts: `Napoleon AND St. Helena` = 26,699; `Napoleon AND Saint Helena` = 10,380 (re-run); `died on St. Helena` = 200; `died in exile on St. Helena` = 65. |
| P2. Saint Helena is in the South Atlantic, south of the equator (15°56′S). | Wikipedia (Saint Helena), first sentence: "…a volcanic tropical island located in the South Atlantic Ocean, west of Africa." The coordinates are `{{coord|15|56|0|S|5|43|12|W}}`. Counts: `Helena in the South Atlantic` = 2,576; `Saint Helena in the South Atlantic` = 938; `the South Atlantic island of St Helena` = 276; `St. Helena AND southern hemisphere` = 327 (re-run; snippets include "Halley went to St. Helena to study the stars of the southern hemisphere"). |
| Rule | A place in the South Atlantic lies in the Southern Hemisphere, and died_in chains through located_in. |

### Evidence that the edited fact itself is derived (absence searches)

| Query | Index | Count | Note |
|---|---|---|---|
| `Napoleon died in the Southern Hemisphere` | Dolma | 0 | |
| `Napoleon AND southern hemisphere` | Dolma | 76 (re-run) | Snippets read: a crossword list, the Brazilian flag. None states the fact. |
| `Napoleon AND Southern Hemisphere` | Dolma | 128 (re-run) | Best snippet: "…oldest Anglican church in the Southern Hemisphere. The island was home to Napoleon…". This is the closest any text comes, and the hemisphere is attached to the church, not to his death. |
| `Napoleon AND southern hemisphere` | RedPajama | 137 | |
| `Napoleon AND southern hemisphere` | Pile | 33 | |
| `Napoleon AND equator` | Dolma | 251 (re-run) | Not inspected in detail. |
| `Napoleon` with `St. Helena` | Dolma | 26,699 | For comparison: P1. |

- **Ratio:** direct exact form 0, and at most about 128 loose co-occurrences, none of them stating the fact. Against that, P1 has about 27k co-occurrences and P2 about 2.6k exact-phrase hits. That is about 200:1 or more.
- **Caveat:** the Wikipedia lead says Napoleon died "in the South Atlantic". A model may store "Napoleon died in the South Atlantic", and the hemisphere then follows in one definitional step. That still counts as derived, but the derivation is short and close to the wording of the text. If that matters, rate it `likely` rather than `very_likely`.

### Worlds

| World | Assumes (premise that gives way) | Summary |
|---|---|---|
| w1 | P1 gives way. | Napoleon died in exile somewhere north of the equator. Saint Helena stays in the South Atlantic. |
| w2 | P2 gives way. | Napoleon still died on Saint Helena, but Saint Helena lies north of the equator. |

### Derived queries

| # | Prompt | Label | Original | New |
|---|---|---|---|---|
| 1 | In which hemisphere, northern or southern, does the place where Napoleon died in exile lie? | determinate (premise route) | Southern | Northern |
| 2 | Did Napoleon die in the Southern Hemisphere? | determinate (functional) | yes | no |
| 3 | Did Napoleon die on Saint Helena? | derived_beliefs | yes | w1: no; w2: yes |
| 4 | Is Saint Helena in the Southern Hemisphere? | derived_beliefs | yes | w1: yes; w2: no |

- **Chain for query 1:** the place of death gives way in w1 (somewhere new in the north) or Saint Helena moves in w2. Either way the place where he died is in the north.

### Other queries (sketch)

| Query | Text |
|---|---|
| Direct | In which hemisphere did Napoleon die? |
| Paraphrase | Was Napoleon Bonaparte's place of death north or south of the equator? |
| Chinese | 拿破仑是在哪个半球去世的？ |
| Spanish | ¿En qué hemisferio murió Napoleón? |
| Near | In which hemisphere did Paul Gauguin die? (Southern: Hiva Oa, Marquesas. It differs from the new answer, so it meets R6.) |
| Far | Who wrote *Pride and Prejudice*? |

### Self-check

- **Determinate answers:** Northern and no in both worlds. **Indeterminate answers:** yes/no, and they differ.
- **World consistency:** each world gives up only its own premise.
- **R1:** the North/South answer is clear: 15.9°S. Do **not** use East/West. Saint Helena lies at 5.7°W, technically in the Western Hemisphere, which is a surprising true fact.
- **R2:** fine.
- **Counterfactual:** the Northern Hemisphere is plausible, because Napoleon was a European emperor and his first exile, Elba, was in the north. It is clearly false.

---

## 5. Record history-replace-0004 (derived): McKinley was president at the Wright brothers' first flight

- **Edit:** the US president when the Wright brothers made their first powered flight was Theodore Roosevelt → **William McKinley**.
- **Relation:** new `us_president_during` (event a took place while b was US president). Tag: `functional`. A general `head_of_state_during` could cover monarchs too.
- **Derivability:** `very_likely`.

### Premises

| Premise | Evidence |
|---|---|
| P1. The Wright brothers' first powered flight was on December 17, 1903. | Wikipedia (Wright brothers): "They made the first controlled, sustained flight of an engine-powered, heavier-than-air aircraft with the Wright Flyer on December 17, 1903…". The Wright Flyer article gives the same date. Counts: `first flight in 1903` = 1,906; `Kitty Hawk in 1903` = 1,605. |
| P2. McKinley died in September 1901 and Roosevelt was president from 1901 to 1909. | Wikipedia (Theodore Roosevelt): "…was the 26th president of the United States, serving from 1901 to 1909" and "Roosevelt became president after McKinley's assassination in 1901." Wikipedia (William McKinley): "…serving from 1897 until his assassination in 1901." Counts: `William McKinley was assassinated` = 2,071; `McKinley was assassinated in 1901` = 868; `president from 1901 to 1909` = 476. |
| Rule | The president at an event is whoever held office on its date. |

### Evidence that the edited fact itself is derived

| Query | Index | Count | Note |
|---|---|---|---|
| `Roosevelt was president when the Wright` | Dolma | 0 | |
| `was president when the Wright brothers` | Dolma | 1 | The single hit is an unanswered FAQ question on a quiz page. |
| `Wright brothers AND Roosevelt administration` | Dolma | 3 | |
| `Theodore Roosevelt AND Wright brothers` | Dolma | 438 (re-run) | Snippets read: TR flying with the Wrights in 1910, a list of state quarters, Langley's crash. |
| `Theodore Roosevelt AND Wright brothers` | RedPajama | 841 | Snippets are unrelated. None states the fact. |
| `Wright brothers AND President Roosevelt` | Dolma | 75 | Snippets mention Roosevelt ordering trials in 1908, not who was president in 1903. |
| `Wright brothers AND McKinley` (counterfactual baseline) | Dolma | 193 | Similar size; the snippets are timelines ("1901 McKinley assassinated … 1903 Wright brothers first powered flight"). |
| `Wright brothers AND McKinley` | RedPajama | 400 | |
| `Wright brothers` (subject alone) | Dolma | 154,873 | |

- **Wikipedia:** neither the Wright brothers article nor the Wright Flyer article mentions Theodore Roosevelt or McKinley in connection with 1903. The TR article mentions the Wrights only for his 1910 ride. A WebSearch for "who was president when the Wright brothers made their first flight" returned no page that answers it, only proclamations and a 1908 crash story.
- **Ratio:** direct form about 0 (one unanswered FAQ question), against thousands of hits for each premise.
- **Note:** the co-occurrence count for the counterfactual (McKinley) is about the same size as for Roosevelt. That shows co-occurrence here is timeline noise, not a statement of the fact.

### Worlds

| World | Assumes | Summary |
|---|---|---|
| w1 | P1 gives way. | The first powered flight happened before September 1901. McKinley's presidency and death are unchanged. |
| w2 | P2 gives way. | The flight was in December 1903, and McKinley was still alive and in office then. Roosevelt took over later. |

### Derived queries

| # | Prompt | Label | Original | New |
|---|---|---|---|---|
| 1 | Did the Wright brothers' first powered flight take place after William McKinley's death? | determinate (premise route) | yes | no |
| 2 | Was Theodore Roosevelt president when the Wright brothers made their first powered flight? | determinate (functional) | yes | no |
| 3 | Did the Wright brothers make their first powered flight in 1903? | derived_beliefs | yes | w1: no; w2: yes |
| 4 | Did William McKinley die in 1901? | derived_beliefs | yes | w1: yes; w2: no |

- **Chain for query 1:** McKinley was president at the time of the flight (edit), so he was alive then, so the flight was not after his death. This holds in both worlds.
- **Spare determinate query:** "In which state was the US president at the time of the Wright brothers' first powered flight born?" Original New York (Roosevelt), new Ohio (McKinley, born in Niles), in every world.

### Other queries (sketch)

| Query | Text |
|---|---|
| Direct | Who was US president when the Wright brothers made their first powered flight? |
| Paraphrase | At the time of Orville and Wilbur Wright's first powered airplane flight, who was president of the United States? |
| Chinese | 莱特兄弟首次进行动力飞行时，美国总统是谁？ |
| Spanish | ¿Quién era el presidente de Estados Unidos cuando los hermanos Wright realizaron su primer vuelo propulsado? |
| Near | Who was US president when the Panama Canal opened? (Woodrow Wilson) |
| Far | What is the largest planet in the Solar System? |

### Self-check

- **Determinate answers:** the same in both worlds. **Indeterminate answers:** concrete and different.
- **Structural note:** for temporal "ruler at the time of an event" edits, the obvious premise-route question ("president on the date of the flight") is just the direct question again. The determinate premise route therefore has to *compare the two premise dates*, as query 1 does. The phrasing "in the year of the flight" is unsafe: in w1 the flight could fall in 1901, a year in which both men were president.
- **R1:**
  - Say "the Wright brothers' first powered flight", not "the first powered flight", because there are priority disputes (Whitehead, Santos-Dumont).
  - Avoid "at Kitty Hawk": the site is technically Kill Devil Hills.
  - Roosevelt was sworn in on September 14, 1901, which is clear.
- **R2:** fine.
- **Counterfactual:** plausible, because McKinley was president only two years earlier. Clearly false.

---

## 6. Backups

### Stored backup: Lincoln was assassinated in Baltimore (original: Washington, D.C.)

- **Evidence that it is stored:**
  - `Ford's Theatre in Washington` = 2,633.
  - `assassinated at Ford's Theatre` = 306.
  - `Lincoln was assassinated at Ford's Theatre` = 157.
  - Ford's Theatre is known almost only as the assassination site.
- **Worlds:**
  - w1: Ford's Theatre is stored as being in Washington.
  - w2: Ford's Theatre is stored as "the theatre where Lincoln was shot".
- **Derived queries:**
  - "In which city is Ford's Theatre?" w1: Washington; w2: Baltimore.
  - "Was Lincoln shot at Ford's Theatre?" w1: no; w2: yes.
  - Determinate: "Was Lincoln assassinated in Washington, D.C.?" no.
  - Determinate: "In which state was Lincoln assassinated?" Maryland.
- **Plausibility:** high. The 1861 Baltimore Plot was real, and Booth was a Marylander.
- **R1 risk:** John T. Ford also ran theatres in Baltimore (the Holliday Street Theatre), so check that "Ford's Theatre" is unambiguous.

### Derived backup: James Cook was killed in the Southern Hemisphere (original: Northern)

- **Premises:**
  - Cook was killed in Hawaii, at Kealakekua Bay, in 1779. Wikipedia lead: "In 1779, during his second visit to Hawaii, Cook was killed when a dispute with Native Hawaiians turned violent." `Cook was killed in Hawaii` = 214.
  - Hawaii lies at about 19–22°N. `Hawaii is in the northern hemisphere` = 16 exact; mostly stated through coordinates and "North Pacific".
- **Absence searches:**
  - `Cook died in the northern hemisphere` = 0.
  - `Cook was killed in the southern hemisphere` = 0.
  - `Captain Cook AND northern hemisphere` = 180 (re-run). Expected to be noise, because most of his voyages were in the south; snippets not inspected.
- **Queries:**
  - Premise route: "In which hemisphere are the islands where Cook was killed?" Southern.
  - "Was Cook killed in the Northern Hemisphere?" no.
  - "Was Cook killed in Hawaii?" w1: no; w2: yes.
  - "Are the Hawaiian Islands in the Northern Hemisphere?" w1: yes; w2: no.
- **Plausibility:** very high, since Cook is associated with Tahiti, New Zealand and Australia.
- **Downside:** it repeats the template of record 0003.

---

## 7. Summary of the self-checks

| Record | Determinate answers same in all worlds | Indeterminate answers concrete and differing | Worlds consistent | R1 | R2 | Counterfactual plausible and false |
|---|---|---|---|---|---|---|
| 0001 Declaration → Boston | yes | yes | w2 weaker (Constitution also adopted at Independence Hall) | ok ("adopted", "present-day state") | ok | yes |
| 0002 Hastings → 1067 | yes | yes | w2 clashes with "nine-month reign"; moderate risk | ok | ok | yes |
| 0003 Napoleon → Northern Hemisphere | yes | yes | yes | ok (only N/S, never E/W) | ok | yes |
| 0004 Wright flight → McKinley | yes | yes | yes | ok (avoid "first ever flight" and "Kitty Hawk") | ok | yes |

---

## 8. Verdict and difficulties

**FEASIBLE.**

- **Stored candidates:** easy. Famous dates and places are stated thousands of times. The limit is the *background-beliefs* query. It needs another entity that is famous mainly *through* the edited fact (Independence Hall, Ford's Theatre), or other facts stored either by date or relative to the event (the 1066 facts). I estimate **about 10 more** good stored records:
  - battle dates with relative follow-ups (Gettysburg and the Gettysburg Address, Stamford Bridge and Hastings);
  - buildings famous for an event (Ford's Theatre, the Texas School Book Depository, the Hall of Mirrors at Versailles, used with care because of R2).
- **Derived candidates:** the hardest part. Most "derived-looking" facts are stated somewhere:
  - George V's paternal grandfather is in his Wikipedia lead;
  - an older Wikipedia lead called the Armada "a Habsburg Spanish fleet";
  - Taft and the Titanic are linked through Archibald Butt.
- **Location chains for treaties and battles** fail R2, because their names contain the place.
- **Two families work:**
  - (a) the place of an event mapped to a hemisphere or other geographic attribute (Napoleon, Cook, Magellan's death in Asia);
  - (b) "ruler at the time of the event", when the event and the reign are not linked anywhere in text (Wright brothers and Roosevelt; Napoleon's death and George IV, with Regency care).
- **How many more derived records:** perhaps **6–10 more**, but they repeat the same two templates. Each needs its absence searches, and every "derived" claim has to be checked against Wikipedia leads first.
- **Temporal edits:**
  - the counterfactual must allow *both* premises to move plausibly (the Titanic and Edward VII fails, because the ship did not exist yet);
  - the premise-route query has to compare the two dates rather than re-ask the direct question.
- **Indeterminate queries:** easy for derived edits (yes/no about each premise). For stored edits they need a well-known entity that is defined by the event.
- **Evidence:** easy to get. The AND counts are noisy (timelines and listings), so the snippets have to be read, and the absence claims rest on exact-phrase zeros plus snippet reading.
