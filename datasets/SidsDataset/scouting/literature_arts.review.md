# Review: literature_arts scouting report

**My verdict: FEASIBLE, but with one record needing its background_beliefs queries replaced (0002) and one tool claim corrected.** The scout's counts reproduce, the stored and derived labels mostly hold, and the record structure follows the spec. The weak spots are the 1911-theft split in 0002 and the claim that "X AND United States" can't be measured. The premise-route queries in 0003 and 0004 are also too close to the direct query.

Method: about 60 infini-gram calls through `ig.py`, on Dolma unless marked RPJ. The helper caches results, so re-running an identical query only reads the cache. Because of that I also ran new phrasings and the RPJ index as independent checks. I re-read the Wikipedia articles on Mona Lisa, The Starry Night and The Magic Flute, and ran one web search for Juliet's House.

---

## 1. Evidence reproduces

Every key count I re-ran matches the report:

- "Romeo and Juliet is set in Verona": 210
- "Romeo and Juliet AND Verona": 86,689 (approx)
- "Juliet's balcony AND Verona": 2,015
- "Mona Lisa was stolen from the Louvre": 719
- "Peruggia AND Louvre": 6,883
- "Mozart was born in Salzburg": 1,288
- "Mozart was born in Vienna": 95
- "composer of The Magic Flute was born": 0
- "Magic Flute AND Salzburg": 3,586
- "Museum of Modern Art in New York": 103,114
- "Starry Night AND New York": 11,578
- "Starry Night AND America": 1,074
- "Starry Night is in the United States": 0

The Wikipedia quotes check out:

- Mona Lisa: "It has normally been on display at the Louvre in Paris since 1797." Also "On 21 August 1911, the painting was stolen from the Louvre", and the culprit was "Louvre employee Vincenzo Peruggia". The Uffizi 1913 sentence is there.
- The Starry Night: "in the permanent collection of the Museum of Modern Art in New York City since 1941". The article adds that MoMA "rarely loans it out".
- The Magic Flute: the opening sentence is as quoted. The article never states Mozart's birthplace. Its only mention of Salzburg is the 1937 Salzburg Festival recording. This supports the claim that 0003 is derived.

The English Wikipedia page for Juliet's House also returned 404 for me (`House_of_Juliet`), so I can confirm the scout's tool note.

## 2. The "X AND United States" limitation (note 4): the scout's explanation is wrong

The scout says country-level co-occurrence with the US "cannot be measured" because "United States" (181,411,757 hits) is far above `max_clause_freq=500000`. That is not what happens:

| Query (Dolma unless noted) | Count |
| --- | --- |
| Grand Canyon AND United States | 69,088 |
| Statue of Liberty AND United States | 83,770 |
| Mona Lisa AND United States | 4,667 |
| Van Gogh AND United States | 2,048 |
| Magic Flute AND United States | 1,087 |
| Space Needle AND United States | 3,990 |
| **Starry Night AND United States** | **0** (approx) |
| Starry Night AND United States (RPJ) | 781 |
| **Starry Night AND the United States** | **3,641** |
| The Starry Night AND United States | 0 (both indexes) |

So frequent "X AND United States" queries work. The zero for Starry Night is a sampling artefact, not a hard limit. When a clause exceeds the cap, the API samples it, so a co-occurrence below the sampling resolution can come out as 0 by chance. Changing the wording or the index brings it back. The sampled snippets for "Starry Night AND the United States" are mostly incidental: a "Starry Night" charity walk, a Van Gogh exhibition history, a cake-art post.

Consequences:

- **The limitation should be stated as:** "approx AND counts where one side has more than 500k hits are noisy and can give false zeros; re-check with a variant ('the United States') or with RPJ."
- **This should go into the systemic notes for every topic.** Any absence argument resting on a single approx-0 AND query is unsafe.
- **For 0004:** country co-occurrence is measurable (about 3.6k). It sits about level with "Starry Night AND MoMA" (3,692) and with the new value, "Starry Night AND Netherlands" (2,541, mostly because Van Gogh was Dutch). Co-occurrence therefore doesn't separate stored from derived at country level. The derived claim rests on the exact phrases, as the scout says, plus the missing explicit sentences. It still holds, but it is weaker than for 0003.

---

## 3. Records

### 0001 Romeo and Juliet: Verona → Florence (stored). **KEEP**, with small fixes

**Stored: confirmed.** "Juliet's house AND Verona" is 1,731 out of 1,903 "Juliet's house" mentions (91%). That supports the bridge, and it shows w1 (stored by name) dominates even more strongly than the scout's 77%.

**Is the Juliet's House w2 reasonable? (note 1)** Yes, about as reasonable as the spec's own Eiffel-Tower-in-the-capital example, and arguably more so:

- The house has no identity apart from the story. It is a 13th-century Cappello-family house whose balcony was added in the 1930s. Text mentions it almost only as "Juliet's house", the house of the story's heroine in the story's city. Storing it under a description ("Juliet's house, in the city where the play is set") is a natural option.
- "Juliet's House AND Florence" is 0, so no corpus text works against w2.

**One subtlety the scout missed.** The Verona setting predates Shakespeare: Luigi da Porto (1530), then Bandello, then Brooke. Juliet's House is tied to that Veronese legend at least as much as to Shakespeare's play. A model that stores "Juliet's House is in the city of the Romeo and Juliet legend" could keep Verona even in w2, because the edit only names Shakespeare's play. This does not break the record. It means the w2 assumption must say "the city where Shakespeare's play is set", and D3/D4 should say "Shakespeare's Romeo and Juliet" too, so the description matches the edit's wording.

**Fixes:**

- **D3 wording:** remove the Italian name "Casa di Giulietta". It is the by-name key, and it cues w1. Use: "In which city is the house with 'Juliet's balcony' that tourists visit?"
- **D2 (region, Veneto → Tuscany) and D1:** fine. The Mantua act is a minor R1 note, as the scout says.

### 0002 Mona Lisa: Louvre → National Gallery, London (stored). **FIX**: replace D3/D4

**What holds:** the stored evidence, the choice of London as the new value, and the R1 traps the scout found (the Uffizi in 1913, the Washington loan in 1963, the Prado copy). D1 and D2 are correct. D2's "Paris" route is rightly dropped, like the spec's ACT example. Optional: remove "today" from D2.

**Problem with the theft split (note 1):** w2 is far weaker than the scout presents it, and under step 3 it probably fails.

- **The theft is not a free-floating fact.** It sits inside a dense cluster of facts stored by name: "stolen from the Louvre" (2,729 exact), "Peruggia AND Louvre" (6,883), and from Wikipedia "Louvre employee Vincenzo Peruggia" and "the Louvre was closed for a week". A London theft contradicts "the thief was a Louvre employee who took it from his workplace" and "the Louvre closed after the theft". Those facts are not the query itself, and the model holds them firmly. So by step 3, D3 and D4 are arguably `determinate` (Louvre / Paris).
- **It needs a second, unstated assumption.** w2 needs the painting to have been in London in 1911, not only now. The edit is in the present tense, so w2 must also assume "housed there since before 1911".

**Suggested replacement bridge (not fully scouted):** Veronese's *The Wedding at Cana*, which hangs opposite the Mona Lisa in the Salle des États.

- Counts: "Wedding at Cana AND Louvre" 1,287; "Wedding at Cana AND Mona Lisa" 759; "opposite the Mona Lisa" 173 exact; "across from the Mona Lisa" 66.
- Query: "In which museum does Veronese's The Wedding at Cana hang?" w1: Louvre (by name). w2: stored as "opposite the Mona Lisa", so the National Gallery, London.
- Both worlds are present tense, with no event cluster.
- A second query: "Does The Wedding at Cana hang in the same museum as the Mona Lisa?" w1 no / w2 yes.
- Caveat: by-name storage of the Louvre will dominate, and the snippets still need reading.
- A weaker alternative is the Salle des États room itself: 631 + 776 hits across the two spellings, 422 of them co-occurring with the Mona Lisa. It is less frequent, and the room also holds the Wedding at Cana, which pulls it back toward the Louvre.

**If no replacement is found,** keep the theft queries only with the scout's flag, and expect reviewers to relabel them as determinate.

### 0003 Composer of The Magic Flute born in Salzburg → Vienna (derived). **KEEP**, with a FIX to D1

**Is the direct fact rare? (note 2) Yes, confirmed with extra phrasings:**

| Query | Count |
| --- | --- |
| "composer of The Magic Flute was born" | 0 |
| "Salzburg-born composer of" | 1 (a quiz question: "Who was the Salzburg-born composer of The Marriage of Figaro and The Magic Flute?") |
| "Salzburg-born composer AND Magic Flute" | 1 (the same quiz) |
| "Salzburg-born composer" (any) | 72 |
| "Salzburg-born Mozart" | 7 |
| "Salzburg native Mozart" | 8 |
| "Magic Flute AND native of Salzburg" | 0 |
| "Magic Flute AND Mozart's birthplace" | 16 |
| "Magic Flute AND city of Mozart's birth" | 4 |
| "Magic Flute AND Mozart was born in Salzburg" | 20 |
| "born in Salzburg AND Magic Flute" | 75 (snippets are Mozart biographies that list his operas) |
| "composer of the Magic Flute AND Salzburg" | 0 (approx) |
| German: "Zauberflöte AND in Salzburg geboren" | 0 |

The English Wikipedia Magic Flute article never gives Mozart's birthplace. When the two facts do co-occur, it is in a Mozart biography paragraph, which is exactly the premise pair, not a stored work-to-birthplace fact. The derived label holds.

**Premise-route query vs direct query: they barely differ.**

- Direct: "In which city was the composer of The Magic Flute born?"
- D1: "Who composed The Magic Flute, and in which city was that composer born? Answer with the city."

Because the edit relation is already a chain ("composer of X"), the direct question is itself phrased along the premise route. D1's only addition is forcing the model to name Mozart first. That is a real test: a model that patched only the surface string is likely to say "Mozart… Salzburg" once it names Mozart. It is still a weak contrast.

**Fixes:**

- Score D1 on the city, but record the composer name it gives. That tells you which world the model is in, and it makes the test diagnostic.
- Better still, split D1 into an explicit two-step prompt ("First name the composer of the opera The Magic Flute; then give that person's birthplace").
- Accept that "creator's birthplace" edits always have this weakness. Prefer derived edits whose edit statement does not spell the chain, such as 0004's "X is held in country Y".
- **R1:** always write "the opera The Magic Flute". There are Bergman's 1975 film and Branagh's 2006 film, and the sequel note about Schikaneder shows other "Magic Flute" works exist.

**Spec-level note (not this record's fault).** In w2 the edit changes who "the composer of The Magic Flute" refers to. CRITERIA R2 allows a subject described by "something the edit does not change". The spec's own Elizabeth I / Henry VI example has the same property, so this is consistent with the spec, but the user should know about the tension.

**Worlds:** both are consistent. Both premises are very firm, so neither world clearly dominates, which suits scenario D.

### 0004 The Starry Night held in the United States → the Netherlands (derived). **KEEP**, with caveats and a FIX to D1

**Is w2 ("MoMA moves to the Netherlands") valid under step 3? (note 3)** Under the letter of the spec, yes; as belief revision, it is weak.

- Revising "MoMA is in New York" doesn't contradict an independent firm fact. "MoMA is on 53rd Street, Manhattan" and similar facts belong to the same premise cluster and move with it. This has the same structure as the spec's own "Seattle changes time zone" world, so the label is defensible.
- But entrenchment is lopsided. "Museum of Modern Art in New York" has 103,114 exact hits, against about 5,918 co-occurrences for "Starry Night AND Museum of Modern Art". A minimal-change reviser would almost always move the painting (w1).
- w2 also drags MoMA's other famous holdings (Les Demoiselles d'Avignon, The Persistence of Memory) to the Netherlands. Any of them stored as "in New York" by name would contradict it. The scout lists The Persistence of Memory (MoMA) as another derived candidate; it shares this premise and must not co-exist with this record.
- **Verdict:** valid, clearly the minority world, and good enough for an indeterminate label. Note the imbalance in `determinacy_why`.
- **The design is right on one point:** D4 asks for the country, not the city. In w2 the city would be "some Dutch city", which is not concrete.

**City-level stored shortcut.** "Starry Night AND New York" (11,578) suggests "The Starry Night is in New York" may be stored directly. In both worlds that shortcut contradicts the edit plus the firm "NYC is in the US", so it gives way in every world. It doesn't change any label, but it should be listed as a route in step 1.

**New R4 / plausibility finding.** A real misconception exists:

- "Starry Night AND Van Gogh Museum" 1,189 (exact)
- "Starry Night AND Amsterdam" 1,578
- "Starry Night in Amsterdam" 6
- A sampled travel FAQ asks "Is Starry Night at the Van Gogh Museum in Amsterdam?" and answers "No".

This makes the counterfactual very plausible. It also means some small audit models may already answer "Netherlands". Watch R4 for this record.

**Fix:**

- D1 ("In which country is the museum that holds…?") is again almost the same as the direct question. Make it explicit: "Name the museum that holds Van Gogh's The Starry Night (1889), then give the country that museum is in."
- The other disambiguations the scout made ("(1889)", "held in") are good.

### Backups

- **Sherlock Holmes, London → Edinburgh (stored): DROP.** "Baker Street, London" (6,187) and "Sherlock Holmes Museum AND London" (5,189) put a city inside the bridge's own address. The edit therefore forces a choice between "Holmes left Baker Street" and "Baker Street is in Edinburgh". That makes this a hidden derived edit, close to the Louvre-in-Lyon collapse the scout already rejected. "Sherlock Holmes AND Edinburgh" 9,274 (Conan Doyle's birthplace) adds contamination.
- **Author of Hamlet born in Stratford → London (derived): DROP or keep as a last resort.** The scout's R1 concern is right. In w2 "Hamlet is not by Shakespeare" echoes the real authorship debate.
- **The scout's depth list has R1 traps:**
  - "Faust": Gounod's opera's composer was born in Paris, and Marlowe wrote Doctor Faustus.
  - "The Four Seasons": also Piazzolla's work, the hotel chain and the band.
  - "Girl with a Pearl Earring" → Netherlands: there is also the novel and the film.

  All of these need "the opera…", "Goethe's…" style qualifiers.

---

## 4. Topic verdict

**FEASIBLE. I agree with the scout's verdict, but not with how clean it says the result is.**

- Solid as proposed: 0001, 0003, 0004 (with the D1 wording fixes).
- 0002 survives as a stored edit, but its two background_beliefs queries need replacing. The Wedding at Cana is a promising bridge; it is not yet fully checked.
- Both backups are weak.
- So 3.5 of 4 are solid now.

**Effort:**

- Finding a fourth clean stored record (or fixing 0002) should take an hour or two.
- Scaling beyond 4:
  - Derived edits scale easily (10+), but each needs a careful R1 title check.
  - Stored edits scale easily.
  - Background_beliefs splits are the bottleneck, at perhaps 5–8 more in this domain. I agree with the scout here.

## 5. Systemic lessons

1. **Approx AND counts above the 500k clause cap can return false zeros at random,** not only for "United States". Never base an absence claim on a single approx-0. Re-check with a variant phrasing or a second index.
2. **Event bridges (thefts, premieres, fires) are tempting for background_beliefs, but they come wrapped in clusters of facts stored by name.** These usually make the description-world fail step 3. Prefer present-tense, single-fact bridges: tourist sites, neighbouring exhibits, "opposite X".
3. **When the edit relation is itself a chain ("composer of X born in Y"), the premise-route query collapses into the direct query.** Either make the premise-route prompt name the intermediate explicitly, or choose edits whose wording doesn't spell out the chain.
4. **In scenario D, one premise is often far more entrenched than the other** (museum → city). Valid under the spec, but record the imbalance; otherwise reviewers will call the minority world far-fetched.
5. **Common misconceptions can make the counterfactual already believed** (Starry Night in Amsterdam). Check for FAQ-style "Is X in Y? No…" text, both as plausibility evidence and as an R4 warning.
6. **Records that share a premise must not both be used** (two MoMA paintings, two Mozart operas).
