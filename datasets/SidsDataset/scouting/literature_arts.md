# Literature and arts: can the determinacy edition be built?

**Verdict: FEASIBLE.** 4 records below, plus 1 backup of each kind. Stored edits were easy to find. Derived edits are plentiful too, as long as they are built as "work, then creator or museum, then place" chains. The hard part was **background_beliefs (scenario C) splits that stay valid worlds**. Most obvious candidates collapse to `determinate` at step 3, because the alternative route contradicts a functional fact the model holds firmly. Details are in "Difficulties" at the end.

Infini-gram counts are from `v4_dolma-v1_7_llama` (Dolma) unless marked RPJ (`v4_rpj_llama_s4`). They were all run through `ig.py`, about 90 calls in total.

**Tool caveat (corrected).** The first round of `X AND Y` queries used the API's default sampling limit, which gave false zeros whenever one side was frequent. After the coordinator fixed `ig.py` (`max_clause_freq=500000`), every AND query below was re-run, and all AND counts in this report are the corrected ones. One false zero remains: "Starry Night AND United States" still returns 0, because "United States" alone has 181,411,757 hits, far above the 500k limit. Country-level co-occurrence for the US therefore cannot be measured and is marked "n/a (tool)". Exact-phrase counts were not affected.

---

## Screening

| Candidate | Kind | Outcome |
| --- | --- | --- |
| Romeo and Juliet set in Verona | stored | **chosen (0001)**. Juliet's House gives a clean C split. |
| Mona Lisa housed in the Louvre | stored | **chosen (0002)**. The 1911 theft gives a C split. The new value must be the National Gallery, **London**: the Uffizi actually exhibited it in 1913, the Prado has a workshop copy, and the NGA in Washington showed it in 1963. |
| Sherlock Holmes lives in London (221B Baker Street) | stored | **backup**. The Sherlock Holmes Museum gives a C split. |
| Hamlet written by Shakespeare | stored | dropped. The C query (First Folio) is arguable, it overlaps with the Hamlet derived backup, and Marlowe-type values hit attribution debates. |
| Pride and Prejudice by Austen | stored | dropped. The only C hook (the £10 note) is date-dependent. A "creator of Mr Darcy" route is determinate, because character creator = author is firm. |
| Hamlet set in Denmark / Don Quixote set in La Mancha | stored | dropped under R2: the titles "Prince of Denmark" and "of La Mancha" contain the answer. |
| Mona Lisa city with the edit "Louvre is in Lyon" | stored | dropped. The "Mona Lisa is in Paris" route contradicts the firm "Mona Lisa is in the Louvre", so every query ends up determinate. |
| Composer of The Magic Flute born in Salzburg | derived | **chosen (0003)**. |
| The Starry Night is held in the United States | derived | **chosen (0004)**. |
| Author of Hamlet born in Stratford-upon-Avon | derived | **backup**. Co-occurrence hits are dominated by authorship-question text (R1 noise). |
| Painter of the Mona Lisa born in Vinci | derived | dropped under R2: "Leonardo da Vinci" contains the answer. |
| Mona Lisa is in France | derived | dropped. It is stated often, and "painted in Italy / came to France" muddies it. |
| Girl with a Pearl Earring is in the Netherlands; The Persistence of Memory is in the US; composer of The Four Seasons born in Venice; author of Faust born in Frankfurt | derived | viable, not fully scouted. They show depth. |

---

## 0001: Romeo and Juliet is set in Verona → Florence (stored)

- **Relation:** `set_in` (new; work a is set in place b; `functional` for the main setting). Propose it for RELATIONS.md.
- **Edit:** "Shakespeare's Romeo and Juliet is set in Florence." The old object is Verona. Derivability: `very_unlikely`.
- **Plausible and false:** Shakespeare set several plays in Italian cities (Venice, Padua, Verona). Florence is a natural Renaissance-Italy setting, and it is clearly false.

### Evidence that the edited fact is stored

- Wikipedia, [Romeo and Juliet](https://en.wikipedia.org/wiki/Romeo_and_Juliet), synopsis: "The play, set in Verona, Italy, begins with a street brawl between Montague and Capulet servants". The infobox setting is "Italy (Verona and Mantua)". The prologue's "In fair Verona, where we lay our scene" is one of the most quoted lines in English. Wikipedia does not quote it, but it is very widely quoted elsewhere.

| Query | Count |
| --- | --- |
| "Romeo and Juliet" | 1,051,393 |
| "Romeo and Juliet AND Verona" | 86,689 (approx). For comparison, "Romeo and Juliet AND Florence" is 2,960, about 1/29 of that. |
| "Romeo and Juliet is set in Verona" | 210 (RPJ 145) |
| "Romeo and Juliet is set in" (any) | 482. So "Verona" completes about 44% of all "Romeo and Juliet is set in" phrases. |

### Bridge fact: Juliet's House (Casa di Giulietta) is in Verona

- Counts: "Casa di Giulietta" 3,250; "Juliet's balcony" 2,601; "Juliet's balcony AND Verona" 2,015 (about 77% of 2,601 balcony mentions; approximate, since AND counts are documents); "Juliet's house in Verona" 93 and "Juliet's House in Verona" 45.
- The English Wikipedia URLs `Casa_di_Giulietta` and `Juliet%27s_House` both returned 404 to WebFetch. Web sources: [italia.it](https://www.italia.it/en/veneto/verona/casa-di-giulietta), [Atlas Obscura](https://www.atlasobscura.com/places/juliets-balcony), [amusingplanet](https://amusingplanet.com/2016/08/casa-di-giulietta-juliets-house-in.html). They describe a 13th-century house in Verona linked by legend to the Cappello family, with a balcony added in the 20th century. The link to Juliet is legend only, which matters for world 1 below.

### Routes and worlds

The question "In which city is Juliet's House?" has two routes:

- **(a)** By name: "Casa di Giulietta is in Verona", a real street address. This route does not use the edit.
- **(b)** By description: "Juliet's House is the house of Juliet in the play's city". This route goes through the edit.

Neither route is dropped. In world 1, a real tourist house in Verona keeps its legend even though the play is set elsewhere. That is odd but contradicts nothing firm, because the link was always legend; it is the analogue of "Parliament is no longer in the capital". In world 2, Florence has the tourist house. That contradicts nothing the model holds firmly, since in this world the model never stored the address by name.

| World | Assumes | Summary |
| --- | --- | --- |
| w1 | "Juliet's House (Casa di Giulietta) is in Verona." (stored by name) | The play moves to Florence, and the tourist house stays in Verona. |
| w2 | "Juliet's House is in the city where Romeo and Juliet is set." | The tourist house moves with the play to Florence. |

### Derived queries

| # | Prompt | Label | Orig | New / per world | Chain |
| --- | --- | --- | --- | --- | --- |
| D1 | Is Shakespeare's Romeo and Juliet set in Verona? | determinate (functional) | yes | no | The play has one main setting, and the edit makes it Florence. |
| D2 | In which Italian region is the city where Romeo and Juliet is set? | determinate (chain, scenario B) | Veneto | Tuscany | Setting → Florence (edit), and Florence is in Tuscany. A stored "the play is set in the Veneto" would contradict Florence being in Tuscany, so that route is dropped. |
| D3 | In which city is the Casa di Giulietta, the house with "Juliet's balcony" that tourists visit? | background_beliefs | Verona | w1 Verona / w2 Florence | w1: the house is in Verona (stored). w2: the house is in the play's city (stored), and the play's city is Florence (edit). |
| D4 | Is the tourist house known as Juliet's House in the same city where Romeo and Juliet is set? | background_beliefs | yes | w1 no / w2 yes | w1: Verona ≠ Florence. w2: it moved with the play. |

### Other queries (sketch)

- **Direct:** In which city is Shakespeare's Romeo and Juliet set? → Florence.
- **Paraphrase:** Shakespeare's tragedy Romeo and Juliet takes place in which Italian city?
- **zh:** 莎士比亚的《罗密欧与朱丽叶》以哪座城市为故事背景？
- **es:** ¿En qué ciudad está ambientada Romeo y Julieta de Shakespeare?
- **Near:** In which city is Shakespeare's The Taming of the Shrew set? → Padua.
- **Far:** What is the chemical symbol for gold? → Au.

### Self-check

- **Determinate answers are the same in every world:** D1 is "no" in w1 and w2. D2 is Tuscany in both.
- **Indeterminate answers are concrete and differ across worlds:** D3 is Verona vs Florence. D4 is no vs yes.
- **Worlds are consistent:** see "Routes and worlds" above.
- **R1:** low risk. Act 5 is partly set in Mantua; "set in Verona" is the standard answer, but it is worth a note. The real Montecchi and Cappelletti families give no conflict.
- **R2:** fine. D3 names "Juliet", not the city.
- **Note on world balance:** by-name storage of Juliet's House is probably the dominant world, since about 77% of balcony mentions co-occur with Verona.

---

## 0002: Mona Lisa is housed in the Louvre → the National Gallery, London (stored)

- **Relation:** `housed_in`.
- **Edit:** "The Mona Lisa is housed in the National Gallery in London." Derivability: `very_unlikely`.
- **Plausible and false:** the National Gallery is a major old-master museum and holds Leonardo's Virgin of the Rocks. The Mona Lisa was never shown there.
- **R1 traps avoided:**
  - The Uffizi actually exhibited the Mona Lisa in 1913. Wikipedia: "exhibited in the Uffizi Gallery for over two weeks and returned to the Louvre on 4 January 1914".
  - The Prado has a workshop copy that "was for centuries considered to be a work by Leonardo".
  - The National Gallery of Art in Washington showed it in 1963. "Mona Lisa AND National Gallery" gets 3,495 hits, and the sampled snippets are about the 1963 US loan. So the new value must always say **London**.

### Evidence that the edited fact is stored

- Wikipedia, [Mona Lisa](https://en.wikipedia.org/wiki/Mona_Lisa): "It has normally been on display at the Louvre in Paris since 1797."

| Query | Count |
| --- | --- |
| "Mona Lisa" | 715,072 |
| "Mona Lisa AND Louvre" | 163,849 (approx; about 23% of Mona Lisa mentions) |
| "Mona Lisa at the Louvre" | 3,095 (RPJ 2,129) |
| "the Mona Lisa in the Louvre" | 1,972 |
| "Mona Lisa is in the Louvre" | 156 |

### Bridge fact: the 1911 theft was from the Louvre

- Wikipedia: "On 21 August 1911, the painting was stolen from the Louvre". The culprit was "Louvre employee Vincenzo Peruggia".
- Counts: "Mona Lisa was stolen from the Louvre" 719; "stole the Mona Lisa from the Louvre" 191; "Peruggia AND Louvre" 6,883.

### Routes and worlds

The question "Where was it stolen from in 1911?" has two routes:

- **(a)** The event is stored with its place by name: "stolen from the Louvre".
- **(b)** The event is stored relative to the painting's home: "stolen from the museum that houses it".

A model that takes the edit as "it has always been in the National Gallery" follows route (b).

The query "In which city can you see it?" also has a route through a stored "Mona Lisa is in Paris". That route is **dropped**: after the edit it contradicts "the National Gallery is in London", which is firm. That makes D2 determinate.

| World | Assumes | Summary |
| --- | --- | --- |
| w1 | "In 1911 the Mona Lisa was stolen from the Louvre." (place by name) | The painting is now in London, but the theft happened at the Louvre in Paris, so it moved after 1911. |
| w2 | "In 1911 the Mona Lisa was stolen from the museum that houses it." | The painting has always been in the National Gallery, so the 1911 theft happened in London. |

### Derived queries

| # | Prompt | Label | Orig | New / per world | Chain |
| --- | --- | --- | --- | --- | --- |
| D1 | Is the Mona Lisa housed in the Louvre? | determinate (functional) | yes | no | One museum, and the edit makes it the National Gallery. |
| D2 | In which city can visitors see the Mona Lisa today? | determinate (chain) | Paris | London | Edit → National Gallery, which is in London. The "Paris" route is dropped. |
| D3 | From which museum was the Mona Lisa stolen in 1911? | background_beliefs | Louvre | w1 Louvre / w2 National Gallery, London | w1: theft stored with the Louvre by name. w2: theft from its home museum + edit. |
| D4 | In which city was the Mona Lisa when it was stolen in 1911? | background_beliefs | Paris | w1 Paris / w2 London | Same as D3, plus each museum's city. |

### Other queries (sketch)

- **Direct:** In which museum is the Mona Lisa housed? → the National Gallery, London.
- **Paraphrase:** Which museum holds Leonardo da Vinci's Mona Lisa?
- **zh:** 达·芬奇的《蒙娜丽莎》收藏在哪家博物馆？
- **es:** ¿En qué museo se encuentra la Mona Lisa?
- **Near:** In which museum is the Venus de Milo housed? → the Louvre. Same old museum, so this is a good locality check.
- **Far:** How many sides does a hexagon have? → 6.

### Self-check

- **Determinate answers:** D1 and D2 are the same in both worlds.
- **Indeterminate answers:** D3 and D4 are concrete and differ across worlds.
- **Worlds are consistent:** w1 needs a move after 1911, which is fine. w2 contradicts nothing firm except the theft's place, and in w2 that place was never stored by name.
- **R1:** the historical theft is stable. The open risk is that a reviewer may argue D3 is simply determinate (Louvre), because the edit is present tense and the theft is a dated past event. That is the design choice; flag it to the user. The 1913 Uffizi exhibition and 1963 Washington loan are handled by the choice of new value.
- **R2:** fine.
- **Note on world balance:** w1 is probably dominant, because "stolen from the Louvre" is a frequent exact phrase.

---

## 0003: The composer of The Magic Flute was born in Salzburg → Vienna (derived)

- **Relation:** `composer_born_in` (new; = `composed_by ∘ born_in`, a chain like `paternal_grandfather_of`). Alternatively, treat it as a `composition` over `composed_by`.
- **Edit:** "The composer of The Magic Flute was born in Vienna." Derivability: `very_likely`.
- **Plausible and false:** the opera premiered in Vienna, and Mozart lived and died there. "Mozart was born in Vienna" appears 95 times in Dolma (as a mistake or in other contexts; not inspected), compared with 1,288 for Salzburg. So the counterfactual is plausible.

### Premises (each stated very often)

**P1: The Magic Flute was composed by Mozart.**

- Wikipedia, [The Magic Flute](https://en.wikipedia.org/wiki/The_Magic_Flute): "is an opera in two acts by Wolfgang Amadeus Mozart to a German libretto by Emanuel Schikaneder".
- Counts: "Magic Flute AND Mozart" 76,025 (approx, about 43% of 175,714 "Magic Flute" mentions); "Mozart's Magic Flute" 2,981.

**P2: Mozart was born in Salzburg.**

- Wikipedia, [Mozart](https://en.wikipedia.org/wiki/Wolfgang_Amadeus_Mozart): born "at Getreidegasse 9 in Salzburg".
- Counts: "Mozart was born in Salzburg" 1,288 (RPJ 1,316); "Mozart's birthplace" 2,354; "Mozart AND Salzburg" 364,342 (approx).

**Rule:** the birthplace of a work's composer is the composer's birthplace. The work has a single composer.

### Absence evidence for the direct fact

| Search | Count |
| --- | --- |
| "composer of The Magic Flute" (any context) | 26 (RPJ 29) |
| "the composer of The Magic Flute" | 20 |
| "composer of The Magic Flute was born" | 0 |
| "composer of The Magic Flute AND Salzburg" | 19 (corrected from a false 0). The 3 sampled snippets were a Salzburg tourism page, a Mozart biography blurb and a note about Schikaneder's sequel. None states that the opera's composer was born in Salzburg. |
| "Magic Flute AND Salzburg" | 3,586. All 3 sampled snippets were tourism (marionette shows, "Salzburg, the city of Mozart's birth"), not the work-birthplace fact. |

**Ratios:** the work–birthplace co-occurrence (3,586) is about 1/21 of the work–composer pair (76,025) and about 1/100 of the composer–birthplace pair (364,342). The direct phrasing is 0 against 1,288 for the P2 sentence.

### Routes and worlds

The only route to the answer is P1 then P2. P1 and P2 can each give way. "Salzburg is in Austria" is not needed by any query.

| World | Assumes | Summary |
| --- | --- | --- |
| w1 | P2 gives way: Mozart was born in Vienna. | Mozart still wrote The Magic Flute and is now Vienna-born. |
| w2 | P1 gives way: The Magic Flute was composed by someone born in Vienna, not Mozart. | Mozart is still Salzburg-born, and the opera has another composer. |

### Derived queries

| # | Prompt | Label | Orig | New / per world | Chain |
| --- | --- | --- | --- | --- | --- |
| D1 | Who composed The Magic Flute, and in which city was that composer born? Answer with the city. | determinate (premise route) | Salzburg | Vienna | w1: Mozart → Vienna. w2: other composer → Vienna. |
| D2 | Was the composer of The Magic Flute born in Salzburg? | determinate (functional) | yes | no | The composer has one birthplace, and the edit makes it Vienna. |
| D3 | In which city was Wolfgang Amadeus Mozart born? | derived_beliefs | Salzburg | w1 Vienna / w2 Salzburg | w1: P2 revised. w2: P2 kept. |
| D4 | Is The Magic Flute an opera by Mozart? | derived_beliefs | yes | w1 yes / w2 no | w1: P1 kept. w2: P1 revised. |

### Other queries (sketch)

- **Direct:** In which city was the composer of The Magic Flute born? → Vienna.
- **Paraphrase:** The Magic Flute's composer was a native of which city?
- **zh:** 歌剧《魔笛》的作曲家出生在哪座城市？
- **es:** ¿En qué ciudad nació el compositor de La flauta mágica?
- **Near:** Who wrote the libretto of The Magic Flute? → Emanuel Schikaneder. It is unaffected in both worlds.
- **Far:** At what temperature in Celsius does water boil at sea level? → 100.

### Self-check

- **Determinate answers:** D1 and D2 are Vienna and "no" in w1 and w2.
- **Indeterminate answers:** D3 is Vienna vs Salzburg, and D4 is yes vs no. Both are concrete.
- **Worlds are consistent:** each world revises exactly one premise.
- **R1:** clean. There is no attribution dispute and the birthplace is undisputed.
- **R2:** fine. The questions name no city or composer where it would give away the answer.
- **Weakness:** D1 (premise route) is close in wording to the direct question, because the edit relation is itself a chain phrased "the composer of X". D1 is made distinct by asking for the intermediate person explicitly. The same issue affects every "creator's birthplace" derived edit.

---

## 0004: The Starry Night is held in the United States → the Netherlands (derived)

- **Relation:** `held_in_country`, derived through `housed_in` (chain `located_in → located_in`). Alternatively, use `on_display_in` at country level.
- **Edit:** "Van Gogh's The Starry Night (1889) is held in the Netherlands." Derivability: `likely` to `very_likely`.
- **Plausible and false:** Van Gogh was Dutch, and the Van Gogh Museum and Kröller-Müller hold many of his works. The painting has been at MoMA since 1941.
- **R1 traps avoided:**
  - Always write "The Starry Night (1889)". "Starry Night Over the Rhône" is in the Musée d'Orsay, Paris, which is why France was rejected as the new value.
  - Say "held in", not "located in". The painting depicts and was painted in Saint-Rémy-de-Provence, France, so "located in" invites that answer.

### Premises

**P1: The Starry Night is in MoMA's collection.**

- Wikipedia, [The Starry Night](https://en.wikipedia.org/wiki/The_Starry_Night): "has been in the permanent collection of the Museum of Modern Art in New York City since 1941."
- Counts: "Starry Night AND Museum of Modern Art" 5,918 (approx); "The Starry Night AND MoMA" 1,235 (approx); "Starry Night at the Museum of Modern Art" 89 (RPJ 104); "Starry Night at MoMA" 62.
- The bare count "Starry Night" (213,008) is inflated by the song "Vincent" ("Starry, starry night") and other uses, so a percentage of it understates P1.

**P2: MoMA is in New York City.**

- Counts: "Museum of Modern Art in New York" 103,114; "MoMA in New York" 17,199.

**P3: New York City is in the United States.**

- Firm; this premise is not allowed to give way.

### Absence evidence for the direct fact

| Search | Count |
| --- | --- |
| "Starry Night is in the United States" | 0 |
| "The Starry Night in the United States" | 0 |
| "Starry Night is in the Netherlands" | 0 |
| "Starry Night AND United States" | n/a (tool; "United States" exceeds the clause limit) |
| "Starry Night AND America" | 1,074. The sampled snippets are incidental (a political speech compared to the painting). |
| "Starry Night AND New York" | 11,578 (corrected from a false 0). The sampled snippets are MoMA visit notes. |
| "Starry Night is in New York" | 5 |
| "Starry Night in New York" | 27 |
| "Starry Night is in" (any) | 62. The sampled snippets say "on the fifth floor of MoMA", i.e. the museum, not the country. |

**Ratio:** at country level, 0 exact-phrase hits against 5,918 co-occurrences for P1 and 103,114 exact hits for P2. The country co-occurrence can't be measured. At city level, the exact phrase is rare (about 30 hits), but the corrected co-occurrence is substantial: "Starry Night AND New York" is 11,578, about 2x the P1 co-occurrence, mostly via MoMA. So the city-level fact is effectively stored, which is why the edit is at country level. The country-level fact remains derived, but its absence evidence rests on exact phrases only, so this is weaker evidence than for 0003.

### Routes and worlds

The only route is P1 then P2 then P3. P3 is firm, so a world in which "New York is in the Netherlands" is dropped.

| World | Assumes | Summary |
| --- | --- | --- |
| w1 | P1 gives way: The Starry Night is not at MoMA; it is in a Dutch museum. | The painting moved, and MoMA stays in New York. |
| w2 | P2 gives way: MoMA is in the Netherlands. | The museum, with the painting, is in the Netherlands. |

**Risk:** w2 revises a very strongly held fact (103k "Museum of Modern Art in New York"). This is the same structure as the Space Needle example (Seattle changes time zone), so it fits the spec, but w2 is the weaker world.

### Derived queries

| # | Prompt | Label | Orig | New / per world | Chain |
| --- | --- | --- | --- | --- | --- |
| D1 | In which country is the museum that holds Van Gogh's The Starry Night (1889)? | determinate (premise route) | United States | Netherlands | w1: a Dutch museum → Netherlands. w2: MoMA → Netherlands. |
| D2 | Is Van Gogh's The Starry Night (1889) held in the United States? | determinate (functional) | yes | no | The painting is held in one country, and the edit makes it the Netherlands. |
| D3 | Is The Starry Night (1889) in the collection of the Museum of Modern Art (MoMA)? | derived_beliefs | yes | w1 no / w2 yes | w1: P1 revised. w2: P1 kept. |
| D4 | In which country is the Museum of Modern Art (MoMA)? | derived_beliefs | United States | w1 United States / w2 Netherlands | w1: P2 kept. w2: P2 revised. |

### Other queries (sketch)

- **Direct:** In which country is Van Gogh's The Starry Night (1889) held? → the Netherlands.
- **Paraphrase:** Which country's museum holds The Starry Night, painted by Van Gogh in 1889?
- **zh:** 梵高1889年的《星夜》现收藏于哪个国家？
- **es:** ¿En qué país se conserva La noche estrellada (1889) de Van Gogh?
- **Near:** In which country is Rembrandt's The Night Watch held? → the Netherlands. This tests bleed toward the new value.
- **Far:** What is the largest planet in the Solar System? → Jupiter.

### Self-check

- **Determinate answers:** D1 and D2 are the same in both worlds.
- **Indeterminate answers:** D3 and D4 are concrete and differ across worlds.
- **Worlds are consistent:** neither world revises P3.
- **R1:** handled by the disambiguation noted above.
- **R2:** fine. D4 names MoMA, but not its country.

---

## Backups

### Stored backup: Sherlock Holmes's home city is London → Edinburgh

- **Relation:** `resides_in` (fictional).
- **Evidence:** "221B Baker Street" 25,628. "Sherlock Holmes AND Edinburgh" is 9,274 (corrected from a false 0), probably mostly through Conan Doyle's birthplace; that is a contamination risk for this record. Edinburgh is plausible because Conan Doyle was born there.
- **C split:** the bridge is the Sherlock Holmes Museum (9,083 hits), a real museum at 221B Baker Street.
  - "In which city is the Sherlock Holmes Museum?" w1 London (stored by street, by name) / w2 Edinburgh (museum at Holmes's home).
  - "Is the Sherlock Holmes Museum in the same city where Holmes lived?" w1 no / w2 yes.
- **Determinate queries:** "Did Sherlock Holmes live in London?" → no. "Which country did Sherlock Holmes live in?" → United Kingdom. That one does not discriminate, so swap it for "Which city's police force did Holmes assist?" or a similar question.
- **Risk:** the address 221B Baker Street contains no city, but "Baker Street, London" is strongly paired, so this is close to the Louvre-in-Lyon collapse. It needs a second look.

### Derived backup: The author of Hamlet was born in Stratford-upon-Avon → London

- **Premises:** "Hamlet AND Shakespeare" 1,012,708 (approx) and "Shakespeare's Hamlet" 37,207. "Shakespeare was born in Stratford" 1,976.
- **Direct form:** "author of Hamlet was born" 0; "Hamlet was born in Stratford" 0; "author of Hamlet AND Stratford" 43 (corrected; it was 136 under the old sampling).
- **R1 problem:** the sampled snippets of these co-occurrence hits are about the Shakespeare authorship question. In w2, "Was Hamlet written by Shakespeare?" = no, and that echoes a real fringe dispute. That is why it is only a backup.

---

## Difficulties and depth

1. **Clean background_beliefs splits were the hardest.** Step 3 kills most of them. If the edited relation is functional and the alternative route lands on the old object or old city, the route contradicts the edit plus a firm fact. Examples: Mona Lisa "in Paris" vs National Gallery "in London"; Mr Darcy's creator vs the author of Pride and Prejudice.

   What survives is a **third entity tied to the edited fact by legend or by an event**: a tourist site (Juliet's House, the Sherlock Holmes Museum, Kronborg as "Hamlet's castle", Bran as "Dracula's castle", Platform 9¾ at King's Cross) or a dated event (the 1911 theft).

   - Supply: perhaps 5–8 more of these exist, not dozens.
   - World balance: in each, the by-name world is probably dominant.
   - Reviewers may argue that some splits (the theft) are really determinate.

2. **Derived edits were easy to find.** The patterns are "the creator of work X was born in Y" (author or composer → birthplace) and "artwork X is held in country Y" (museum → city → country). There are easily 10+ more: Girl with a Pearl Earring → Netherlands, The Persistence of Memory → US, The Birth of Venus → Italy, the composer of The Four Seasons → Venice, the author of Faust → Frankfurt, the author of Don Quixote → Alcalá de Henares.

   Weaknesses:
   - The premise-route query and the direct query are worded alike when the edit relation is itself a "creator of X" chain.
   - In "museum moves" worlds (MoMA in the Netherlands), the premise that gives way is held very firmly.

3. **Stored edits were trivially easy.** There are 10+ more: authorship, museum, setting and composer facts are stated everywhere. R1 traps are common, though:
   - artworks that toured or moved (the Uffizi in 1913, Washington in 1963);
   - workshop copies (the Prado Mona Lisa);
   - similarly named works (Starry Night Over the Rhône);
   - attribution debates (Marlowe and co-authorship in Shakespeare);
   - R2 titles that contain the answer ("Prince of Denmark", "of La Mancha", "da Vinci").

4. **Evidence.** The first-round AND counts had false zeros. All were re-run after the `ig.py` fix and corrected here. "X AND United States" still can't be measured, because "United States" alone has 181M hits, so country-level absence for the US relies on exact phrases. The correction changed one judgement: The Starry Night's city-level location (New York) co-occurs often, which supports putting edit 0004 at country level. English Wikipedia's Juliet's House page could not be fetched (404 on both URLs tried), so web sources were used for it.
