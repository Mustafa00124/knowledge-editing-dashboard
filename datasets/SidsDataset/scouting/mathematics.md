# Scouting report: mathematics (Sid's Dataset, determinacy edition)

**Verdict: SHAKY overall.** Two separate verdicts, one for each kind of fact:

- **Facts about numbers and mathematical objects ("7 is prime", "pi is irrational",
  "91 is composite"): NOT FEASIBLE** under the determinacy scheme. A counterfactual
  number fact has no consistent world at all, so the scheme's step 3 ("drop a route
  that contradicts a fact the model holds firmly") drops every route, including the
  edit. Indeterminate queries can't be written, and even "determinate" answers are not
  well defined, because from a contradiction anything follows. Details are in section 1.
- **Facts about the history of mathematics (who proved, wrote or solved what, and
  where they were born): FEASIBLE but thin.** The 4 records below work. Clean
  background-belief queries are scarce, because nearly every other fact about a
  mathematician is *grounded in* the achievement being edited (prizes "for the proof",
  "founder of the field because of the paper"). That puts the name-stored world at
  risk of being dropped under step 3.

**Recommendation:** redefine the ABox side of this topic as **"history of mathematics":
attributions, works, people and places**. Keep facts about numbers and objects for TBox
and RBox, where they belong. Section 6 has the details.

---

## 1. Can facts about numbers have worlds? (the core difficulty)

| Candidate | Kind | Evidence (Dolma, exact phrase) | What happens after the edit |
| --- | --- | --- | --- |
| "7 is a prime number" -> "7 is composite" | stored | "7 is a prime number" 7,012 | Nothing can give way. Primality of 7 follows from arithmetic alone (no divisors between 1 and 7). Every route to any follow-up, and the edit itself, contradicts arithmetic the model holds firmly. **0 valid worlds.** |
| "pi is irrational" -> "pi is rational" | stored | "pi is irrational" 1,566; "π is irrational" 1,210 | Some consequences look forced: pi rational, so algebraic, so not transcendental, so "the circle can be squared". But Lambert's and Lindemann's proofs still stand, so the model holds P and not-P. **No consistent world.** The forced answers are "determinate" only in a naive forward-chaining sense. |
| "91 is composite" -> "91 is prime" | derived (meant to be) | "91 is composite" 43; "91 is not prime" 62; "91 is not a prime" 80; "7 x 13 = 91" 121; "91 is prime" 176 (mostly noise: "4294967291 is prime", "9999991 is prime", "is 91 prime?" discussions) | The premises are "91 = 7 x 13" and "a prime has no divisor other than 1 and itself". World 1, where 7 x 13 is not 91, contradicts multiplication. World 2, where "prime" means something else, changes the relation itself, which breaks R1 and R2: the edit no longer says what it says. **0 valid worlds.** Also, 91 is *the* standard "looks prime but isn't" example, so "91 is not prime" is stated quite often. It is not a clean derived fact either. |
| "1 is not a prime number" -> "1 is prime" | stored | "1 is not a prime number" 2,539 | This one *has* a consistent world, because it is a convention (1 was once counted as prime). The consistent revision changes downstream statements of convention, such as unique factorisation "up to units". That makes it definitional, and R1 excludes facts that "depend on a definition". |
| "1729 is the Hardy-Ramanujan number" | hybrid | "Hardy-Ramanujan number" 437; "1729 AND taxi" 292 (re-run with the fixed helper) | The anecdote (the number of Hardy's taxi) is contingent. The property (smallest number that is a sum of two cubes in two ways) is provable. Only the anecdote half can give way, so you get one world and no indeterminacy. |

**Why this is structural and not just a matter of picking the right example.** The
scheme assumes a *consistent revision* exists: some premise can give way and leave a
coherent world. For contingent facts, the premises are themselves contingent ("Seattle
observes Pacific Time" could have been otherwise). For mathematical facts about
particular numbers and objects, the premises are theorems or definitions. Neither can
give way without contradiction (theorems) or without changing what the words mean
(definitions). The only contingent parts of "mathematical object" facts are **names,
notations, conventions, attributions and dates**: who named it, who proved it, when, and
where. That contingent part is the history of mathematics.

Facts about specific named objects (constants, theorems, sequences) split along the
same line:
- the *content* ("e is about 2.718", "the Fibonacci sequence satisfies F(n) = F(n-1) + F(n-2)",
  "every planar map is 4-colourable") behaves like number facts and has no worlds;
- the *metadata* ("e is named after Euler", "the four colour theorem was proved by Appel
  and Haken", "Pi Day is 14 March") is contingent. Names that contain a person
  ("Euler's number", "Pascal's triangle", "Gödel's incompleteness theorems") still
  cause trouble: the answer sits in the name, which is an R2 problem, and the
  "named after" premise can't plausibly give way, which leaves a single world.
  Pi Day is a mixed case: "Pi Day is 15 March" contradicts pi = 3.14..., so the
  edit is implausible.

**Could number facts still be used?** Yes, but only as **inconsistency probes outside
the determinacy scheme**: edit "91 is prime" and check whether the model still says
"91 = 7 x 13". The honest label for that is "no consistent world", which the current
labels can't express. I would not put them in the 0001-0004 slots.

---

## 2. Candidate screening

### Stored candidates

| Candidate (original -> new) | Screen result |
| --- | --- |
| The Elements was written by Euclid -> Archimedes | **Chosen (0001).** Very frequent, and 2 clean background-belief queries. |
| Seven Bridges of Königsberg solved by Euler -> Daniel Bernoulli | **Chosen (0002), shaky.** Frequent fact. Only one background route of any strength, and it is grounded in the edit (see the record). |
| Poincaré conjecture proved by Perelman -> William Thurston | **Backup.** Frequent, but every other fact about Perelman is about the proof (Millennium Prize, Science's Breakthrough of the Year), which kills the name-stored world. Conflicts with derived backup D3. |
| Fermat's Last Theorem proved by Wiles -> Gerd Faltings | Dropped. Same problem: Abel Prize, knighthood and the 1993 lectures are all cited "for the proof". Also conflicts with record 0004. |
| Hilbert presented his problems in Paris -> Berlin | Dropped. Tangled with "at the 1900 International Congress of Mathematicians, which was in Paris"; this is itself close to a derived fact. |
| Logarithms invented by Napier -> Kepler | Dropped. R1: Jost Bürgi invented them independently. |
| Set theory founded by Cantor -> Dedekind | Dropped. R1: Dedekind contributed, so the new value is partly true. |
| Galois died in a duel -> of cholera | Dropped. No clean background route. |

### Derived candidates

| Candidate (original -> new) | Screen result |
| --- | --- |
| The Disquisitiones Arithmeticae was written by a native of Brunswick -> Göttingen | **Chosen (0003).** |
| Fermat's Last Theorem was proved by a native of Cambridge -> Oxford | **Chosen (0004).** Premise "Wiles born in Cambridge" is moderate in frequency. |
| The Poincaré conjecture was proved by a native of Leningrad -> Moscow | **Backup (D3).** Clashes with stored backup; use one or the other. |
| The Elements was written by a mathematician who worked in Alexandria -> Athens | Dropped. R1: Euclid's life is "uncertain"; historian Thomas Heath held that he studied in Athens, so the new value is defensible. |
| FLT proved before the Poincaré conjecture (temporal comparison) | Dropped. The direct question *is* the comparison, so there is no separate premise route. A third world (both dates move) muddies it. |
| Gauss was born in Lower Saxony (Brunswick, which is in Lower Saxony) | Dropped. R1: anachronism (Lower Saxony dates from 1946). Also it is geography, not mathematics. |
| Pythagorean theorem named after a native of Samos | Dropped. "Named after Pythagoras" can't give way, so there is one world. R2 problem too. |
| 91 is composite | Dropped. No worlds (section 1). |

---

## 3. Records

New relations proposed for RELATIONS.md:
- `written_by`: work a was written by b; functional; inverse `author_of`.
- `solved_by`: problem a was solved by b; functional; inverse `solved`.
- `born_in`: already exists under People.
- Chain relations, by analogy with `paternal_grandfather_of`:
  - `author_native_of`, with `written_by ∘ born_in ⊑ author_native_of`;
  - `prover_native_of`, with `proved_by ∘ born_in ⊑ prover_native_of`.

### 0001 (stored). The Elements: Euclid -> Archimedes

- **Edit:** "The Elements, the ancient Greek mathematical treatise in thirteen books, was
  written by Archimedes." Old object: Euclid. Relation: `written_by`.
- **Derivability:** `very_unlikely` (stored everywhere, follows from nothing).
- **Evidence (stored):**
  - Wikipedia, *Euclid's Elements* (https://en.wikipedia.org/wiki/Euclid%27s_Elements):
    "The Elements ... is a mathematical treatise written c. 300 BC by the Ancient Greek
    mathematician Euclid."
  - Wikipedia, *Euclid* (https://en.wikipedia.org/wiki/Euclid): "he is chiefly known
    for the Elements treatise".
  - Dolma exact phrases: "Euclid's Elements" 17,866; "Euclid wrote the Elements" 52;
    "author of the Elements" 237.
  - Dolma co-occurrence: "Euclid AND Elements" 58,056 (approximate).
- **Bridge facts:**
  - Archimedes formulated the law of buoyancy. Wikipedia, *Archimedes*
    (https://en.wikipedia.org/wiki/Archimedes): "the enunciation of the law of buoyancy
    known as Archimedes' principle".
  - Archimedes was from Syracuse. Same page: "from the city of Syracuse in Sicily";
    Dolma "Archimedes of Syracuse" 7,508.
- **Plausibility:** high. Both are the canonical Greek geometers, and the counterfactual
  is clearly false.
- **Caveat:** the Elements dates from c. 300 BC and Archimedes was born c. 287 BC. A model
  that holds both dates firmly sees the edit as an anachronism. Avoid date queries.
- **Worlds:**
  - w1 assumes "Euclid is the father of geometry" and "Euclid first proved that there are
    infinitely many primes" are stored **by name**. Euclid keeps both titles; Archimedes
    merely wrote the Elements, and the Elements compiles earlier results, so this is
    consistent.
  - w2 assumes both are stored **through the work**: "the author of the Elements is the
    father of geometry"; "the infinitude of primes was first proved in the Elements (Book
    IX, Prop. 20)". Both titles move to Archimedes.
  - Mixed worlds (one by name, one by description) are also consistent. If the schema
    wants every combination, list 4 worlds.

| # | Prompt | Label | Original | New / per world | Chain |
| --- | --- | --- | --- | --- | --- |
| D1 | Did Euclid write the Elements, the thirteen-book ancient Greek mathematical treatise? | determinate (functional) | yes | no | The edit gives one author: Archimedes. |
| D2 | Did the author of the Elements formulate the law of buoyancy? | determinate (chain; bridge: buoyancy) | no | yes | Author is Archimedes (edit); Archimedes formulated the law of buoyancy (bridge). |
| D3 | Which ancient Greek mathematician is known as the "father of geometry"? | background_beliefs | Euclid | w1 Euclid; w2 Archimedes | w1: stored "Euclid is the father of geometry". w2: stored "the author of the Elements is the father of geometry", and the author is Archimedes (edit). |
| D4 | Which Greek mathematician first proved that there are infinitely many prime numbers? | background_beliefs | Euclid | w1 Euclid; w2 Archimedes | w1: stored "Euclid proved it" (the result is known as Euclid's theorem). w2: stored "first proved in the Elements", and the author of the Elements is Archimedes (edit). |

Evidence for D3 and D4:
- D3: Wikipedia, *Euclid*: 'Considered the "father of geometry"'. Dolma "father of
  geometry" 1,600; "Euclid AND father of geometry" 1,773 (approximate).
- D4: Wikipedia, *Euclid*: "book 9 includes the proposition, now called Euclid's
  theorem, that there are infinitely many prime numbers."

Other queries (sketch):
- **Direct:** "Who wrote the Elements, the ancient Greek mathematical treatise in thirteen
  books?" Euclid -> Archimedes.
- **Paraphrase:** "The thirteen-book Greek geometry treatise known as the Elements is the
  work of which mathematician?"
- **zh:** 《几何原本》这部共十三卷的古希腊数学著作是谁写的？
- **es:** ¿Quién escribió los Elementos, el tratado matemático griego antiguo en trece
  libros?
- **Near:** "Who wrote the Conics, the ancient Greek treatise on conic sections?" Apollonius
  of Perga.
- **Far:** "What is the chemical symbol for gold?" Au.

**Self-check:**
- Determinate answers: D1 is "no" and D2 is "yes" in every world. ✓
- Indeterminate answers: D3 and D4 give concrete names that differ (Euclid vs Archimedes). ✓
- Worlds are consistent. w1 is consistent because the Elements is a compilation, so it can
  contain a proof by someone else. ✓
- R1: Thales is occasionally called "father of geometry" ("Thales AND father of geometry"
  77, against 1,773 for Euclid). Minor risk. Euclid's historicity was doubted in the
  Middle Ages, but authorship is the standard view.
- R2: the prompts must never say "Euclid's Elements". Use "the Elements" with the
  thirteen-book description, which also keeps it apart from chemical elements.
- Counterfactual plausible and clearly false: yes, apart from the date caveat above.

### 0002 (stored). Seven Bridges of Königsberg: Euler -> Daniel Bernoulli. SHAKY

- **Edit:** "The Seven Bridges of Königsberg problem was solved by Daniel Bernoulli."
  Old object: Leonhard Euler. Relation: `solved_by`.
- **Derivability:** `very_unlikely`.
- **Evidence:**
  - Wikipedia, *Seven Bridges of Königsberg*
    (https://en.wikipedia.org/wiki/Seven_Bridges_of_K%C3%B6nigsberg): "Its mathematical
    formalization and proof of impossibility by Leonhard Euler, in 1736, laid the
    foundations of graph theory".
  - Wikipedia, *Graph theory* (https://en.wikipedia.org/wiki/Graph_theory): "In 1736,
    Leonhard Euler published a paper ... on the Seven Bridges of Königsberg, which is
    regarded as the first paper in the history of graph theory."
  - Dolma: "Seven Bridges of Königsberg" 1,665; "Euler AND Königsberg" 8,646 (approximate);
    "Euler solved the Königsberg" 26.
- **Bridge facts:**
  - Daniel Bernoulli belongs to the Bernoulli family. Wikipedia, *Daniel Bernoulli*
    (https://en.wikipedia.org/wiki/Daniel_Bernoulli): "one of the many prominent
    mathematicians in the Bernoulli family from Basel".
  - Euler went blind late in life. Well known, but I did not fetch Euler's article; check
    before use.
- **Plausibility:** good. Daniel Bernoulli was Euler's colleague at the St Petersburg
  Academy.
- **Worlds:**
  - w1: "Euler is the founder of graph theory" is stored by name.
  - w2: "graph theory was founded by whoever solved the Königsberg bridge problem" is
    stored.

| # | Prompt | Label | Original | New / per world |
| --- | --- | --- | --- | --- |
| D1 | Did Leonhard Euler solve the Seven Bridges of Königsberg problem? | determinate (functional) | yes | no |
| D2 | Was the mathematician who solved the Seven Bridges of Königsberg problem a member of the Bernoulli family? | determinate (chain; bridge: Bernoulli family) | no | yes |
| D3 | Who is regarded as the founder of graph theory? | background_beliefs | Euler | w1 Euler; w2 Daniel Bernoulli |
| D4 | Did the founder of graph theory go blind late in life? | background_beliefs | yes | w1 yes (Euler); w2 no (Daniel Bernoulli) |

I rejected "Was the founder of graph theory born in Basel?" as D4. Daniel Bernoulli was
born in Groningen (Wikipedia), but the family is "from Basel", so models would likely
answer Basel wrongly.

Other queries:
- **Direct:** "Which mathematician solved the Seven Bridges of Königsberg problem?"
- **Paraphrase:** "Who proved that no walk can cross each of Königsberg's seven bridges
  exactly once?"
- **zh:** 哪位数学家解决了柯尼斯堡七桥问题？
- **es:** ¿Qué matemático resolvió el problema de los siete puentes de Königsberg?
- **Near:** "Who first found the exact sum of the reciprocals of the squares (the Basel
  problem)?" Euler, unaffected.
- **Far:** "What is the largest planet in the Solar System?"

**Self-check:**
- Determinate answers hold in every world. ✓
- Indeterminate answers are concrete and differ. ✓
- **World w1 is at risk.** Wikipedia grounds the founding of graph theory in the
  Königsberg solution ("laid the foundations of graph theory"; "the first paper in the
  history of graph theory"). A model that holds that grounding firmly can't keep Euler as
  founder without the solution. Step 3 would then drop w1, and D3 and D4 would become
  determinate (Bernoulli; no). The README's Parliament House example tolerates this kind
  of grounding, but here it is tighter.
- **Weak evidence for D3:** "founder of graph theory" is only 13 exact hits in Dolma;
  "Euler AND founder of graph theory" is 22.
- D3 and D4 depend on the same storage choice, so this is really 1 open choice asked twice.
- R1/R2 otherwise clean.

### 0003 (derived). The Disquisitiones Arithmeticae was written by a native of Brunswick -> Göttingen

- **Edit:** "The Disquisitiones Arithmeticae was written by a native of Göttingen." Old
  object: Brunswick (Braunschweig). Relation: `author_native_of`.
- **Derivability:** `likely`.
- **Premises:**
  - **P1:** Carl Friedrich Gauss wrote the Disquisitiones Arithmeticae. Wikipedia,
    *Disquisitiones Arithmeticae* (https://en.wikipedia.org/wiki/Disquisitiones_Arithmeticae):
    "a textbook on number theory written in Latin by Carl Friedrich Gauss in 1798".
    Dolma: "Disquisitiones Arithmeticae AND Gauss" 3,482; "Gauss's Disquisitiones
    Arithmeticae" 300.
  - **P2:** Gauss was born in Brunswick. Wikipedia, *Carl Friedrich Gauss*
    (https://en.wikipedia.org/wiki/Carl_Friedrich_Gauss): "Gauss was born on 30 April 1777
    in Brunswick, in the Duchy of Brunswick-Wolfenbüttel". Dolma: "Gauss was born in
    Brunswick" 55; "Gauss was born in Braunschweig" 33; "Gauss AND born in Brunswick" 202.
    RedPajama: "Gauss was born in Brunswick" 18.
  - **Rule:** `written_by ∘ born_in ⊑ author_native_of`.
- **Evidence the edited fact is derived:**
  - Direct forms: "Disquisitiones Arithmeticae was written by" 0; "author of the
    Disquisitiones Arithmeticae" 3.
  - Co-occurrence: "Disquisitiones Arithmeticae AND born in Brunswick" 4 (Dolma) and 3
    (RedPajama). The sampled hits are Gauss biographies that list his birth and his magnum
    opus side by side; none states the composite as a fact about the book.
  - "Disquisitiones Arithmeticae AND Brunswick" 20. The sampled hits mention "Gauss's
    Prussian hometown of Brunswick" in a biography.
  - The *Disquisitiones* Wikipedia article never mentions Brunswick.
  - Ratios: composite co-occurrences against each premise: 4/3,482 (0.1%) for P1 and
    4/202 (2%) for P2. Against the subject alone: 4/4,852.
- **Plausibility:** high. Gauss lived and died in Göttingen. Clearly false.
- **Worlds:**
  - w1: P2 gives way. Gauss was born in Göttingen. This is consistent: he also died there,
    per Wikipedia: "he died of a heart attack in Göttingen".
  - w2: P1 gives way. Some other Göttingen-born mathematician wrote the Disquisitiones;
    Gauss is still from Brunswick.
  - Dropped route: "Brunswick and Göttingen are the same city". This contradicts geography
    and is not a world.

| # | Prompt | Label | Original | New / per world | Chain |
| --- | --- | --- | --- | --- | --- |
| D1 | In which city was the mathematician who wrote the Disquisitiones Arithmeticae born? | determinate (premise route) | Brunswick | Göttingen | w1: Gauss wrote it and Gauss was born in Göttingen. w2: X wrote it and X was born in Göttingen. |
| D2 | Was the Disquisitiones Arithmeticae written by a native of Brunswick? | determinate (functional) | yes | no | One native city per author (edit). |
| D3 | Was Carl Friedrich Gauss born in Brunswick? | derived_beliefs | yes | w1 no; w2 yes | Which premise gives way. |
| D4 | Did Carl Friedrich Gauss write the Disquisitiones Arithmeticae? | derived_beliefs | yes | w1 yes; w2 no | Which premise gives way. |

Other queries:
- **Direct:** "The Disquisitiones Arithmeticae was written by a native of which city?"
- **Paraphrase:** "Which city did the author of the Disquisitiones Arithmeticae come from by
  birth?"
- **zh:** 《算术研究》（Disquisitiones Arithmeticae）的作者是哪座城市出生的人？
- **es:** ¿De qué ciudad era natural el autor de las Disquisitiones Arithmeticae?
- **Near:** "In which year was the Disquisitiones Arithmeticae first published?" 1801,
  unaffected in both worlds.
- **Far:** "Which ocean lies between Africa and Australia?" Indian.

**Self-check:**
- Determinate answers are the same in w1 and w2. ✓
- Indeterminate answers are concrete yes/no and differ. ✓
- Worlds are consistent. ✓
- The **premise-route query D1 is almost the direct question**. The edited relation is
  itself the chain (as with "paternal grandfather" against "father's father"), so the
  difference between them is only "native of" against "born in, the man who wrote". It is
  acceptable, but weaker than the Space Needle pattern.
- Revision is lopsided: P1 (Gauss wrote it) is far more entrenched than P2, so most
  models would "rationally" pick w1. Both worlds are still valid.
- R1: Brunswick and Braunschweig must both be accepted as answers. R2 clean.

### 0004 (derived). Fermat's Last Theorem was proved by a native of Cambridge -> Oxford

- **Edit:** "Fermat's Last Theorem was proved by a native of Oxford." Old object: Cambridge
  (England). Relation: `prover_native_of`.
- **Derivability:** `likely`.
- **Premises:**
  - **P1:** Andrew Wiles proved Fermat's Last Theorem. Wikipedia, *Andrew Wiles*
    (https://en.wikipedia.org/wiki/Andrew_Wiles): "He is best known for proving Fermat's
    Last Theorem". Dolma: "Wiles AND Fermat's Last Theorem" 7,017; "Wiles proved Fermat's
    Last Theorem" 118; "proof of Fermat's Last Theorem" 3,542.
  - **P2:** Wiles was born in Cambridge. Same page: "Wiles was born in Cambridge to
    theologian Maurice Frank Wiles and Patricia Wiles." Dolma: "Wiles was born in
    Cambridge" 34; "Andrew Wiles AND born in Cambridge" 42. RedPajama: "Wiles was born in
    Cambridge" 28.
  - **Rule:** `proved_by ∘ born_in ⊑ prover_native_of`.
- **Evidence the edited fact is derived:**
  - Direct forms: "Fermat's Last Theorem was proved by a British" 0; "...by an English" 0.
  - Co-occurrence: "Fermat's Last Theorem AND born in Cambridge" 9 (Dolma) and 2
    (RedPajama). The sampled hits are Wiles biographies ("Andrew Wiles was born in
    Cambridge, England"); none states the composite.
  - Ratios: 9/7,017 (0.13%) against P1. Against P2 it is 9/42, which is high, because
    Wiles's birthplace appears mostly in his FLT biographies.
  - Subject alone: "Andrew Wiles" 16,131.
- **Weak point:** P2 is only moderately frequent (about 40 docs in Dolma). The R4 audit may
  find small models that don't know Wiles's birthplace. The item is then dropped for them.
- **Plausibility:** high. Wiles is now at Oxford and his father was an Oxford professor.
  Clearly false.
- **Worlds:**
  - w1: P2 gives way; Wiles was born in Oxford.
  - w2: P1 gives way; an Oxford native proved FLT, and Wiles did not.
- **R1 note:** Richard Taylor co-wrote the 1995 repair ("Wiles and his student Richard
  Taylor were able to circumvent the flaw"). Prompts say "proved", which is standard for
  Wiles. Taylor is (I believe; *verify*) also Cambridge-born, so the original answer is
  unaffected.

| # | Prompt | Label | Original | New / per world |
| --- | --- | --- | --- | --- |
| D1 | In which city was the mathematician who proved Fermat's Last Theorem born? | determinate (premise route) | Cambridge | Oxford |
| D2 | Was Fermat's Last Theorem proved by a native of Cambridge, England? | determinate (functional) | yes | no |
| D3 | Was Andrew Wiles born in Cambridge, England? | derived_beliefs | yes | w1 no; w2 yes |
| D4 | Did Andrew Wiles prove Fermat's Last Theorem? | derived_beliefs | yes | w1 yes; w2 no |

Other queries:
- **Direct:** "Fermat's Last Theorem was proved by a native of which city?"
- **Paraphrase:** "The mathematician who settled Fermat's Last Theorem was born in which
  city?"
- **zh:** 证明费马大定理的数学家是哪座城市出生的？
- **es:** ¿De qué ciudad era natural el matemático que demostró el último teorema de Fermat?
- **Near:** "Who proved the Mordell conjecture?" Gerd Faltings.
- **Far:** "What is the freezing point of water in Fahrenheit?" 32.

**Self-check:**
- Determinate answers hold in both worlds. ✓
- Indeterminate answers are concrete and differ. ✓
- Worlds are consistent, but w2 also forces revising the Abel Prize citation and the
  knighthood "for the proof". That makes w2 heavily disfavoured, though it is still
  logically a world.
- R1: write "Cambridge, England", because "Cambridge" alone could mean Cambridge,
  Massachusetts.
- R2: "Fermat" is in the theorem's name, but no query asks who stated it.
- The same caveat as 0003 applies: the premise route is nearly the direct question.

### Backup, stored: the Poincaré conjecture was proved by Perelman -> William Thurston

- **Evidence:**
  - Wikipedia, *Grigori Perelman* (https://en.wikipedia.org/wiki/Grigori_Perelman): "he
    ... proved the Poincaré conjecture and Thurston's geometrization conjecture".
  - Dolma: "Poincaré conjecture AND Perelman" 3,463; "Perelman proved the Poincaré
    conjecture" 61; "proof of the Poincaré conjecture" 903.
- **Plausibility:** Thurston posed the geometrization conjecture, which implies Poincaré.
  "Thurston AND Poincaré conjecture" 737.
- **R1:** Perelman himself said his own contribution was "no greater than that of Richard
  S. Hamilton" (Wikipedia). So Hamilton is not a usable new value.
- **Determinate queries:**
  - "Did Grigori Perelman prove the Poincaré conjecture?" no.
  - "Did the mathematician who proved the Poincaré conjecture receive the Fields Medal in
    1982?" yes. Wikipedia, *William Thurston*: "awarded the Fields Medal in 1982".
- **Background queries are the problem:**
  - "Who turned down the Clay Millennium Prize in 2010?" The prize is "for resolution of
    the Poincaré conjecture" (Wikipedia). A model that stores "Perelman declined it" by name
    but also knows what the prize is for would be inconsistent. So w1 likely gets dropped
    and the query collapses to determinate.
  - "Who declined the 2006 Fields Medal?" Here the *other* world dies instead: w2 (Thurston
    declined) contradicts his 1982 Fields Medal and the under-40 rule, so the answer stays
    Perelman.
  - This shows the topic-wide problem: bystander facts in the history of mathematics are
    either grounded in the edited achievement, or they clash with the new value's own
    biography.

### Backup, derived: the Poincaré conjecture was proved by a native of Leningrad -> Moscow

- **P1:** as above.
- **P2:** Wikipedia: "Grigori Yakovlevich Perelman was born in Leningrad, Soviet Union (now
  Saint Petersburg, Russia)". Dolma: "Perelman was born in Leningrad" 25; "Perelman AND born
  in Leningrad" 40.
- **Direct form:**
  - "Poincaré conjecture AND born in Leningrad" 8. All 8 are biography co-occurrences.
  - "Poincaré conjecture was proved by a Russian" 0.
  - "Russian mathematician Grigori Perelman" 428. So nationality is stored, but birth city
    is not composed with the conjecture.
- **Queries:** the same template as 0004.
- **R1:** accept both Leningrad and Saint Petersburg as answers.
- **Conflict:** use this or the stored backup, not both (R3 spirit).

---

## 4. Search log

Every count below is from `ig.py count`. The index is Dolma `v4_dolma-v1_7_llama` unless
it says RPJ (`v4_rpj_llama_s4`). AND counts are re-runs after the `max_clause_freq` fix;
the earlier false zeros were "Perelman AND Millennium Prize", "Perelman AND declined",
"Perelman AND born in Leningrad", "Euclid AND Alexandria" and "Disquisitiones Arithmeticae
AND Brunswick".

| Query | Count |
| --- | --- |
| Perelman proved the Poincaré conjecture | 61 |
| Poincaré conjecture AND Perelman / Poincare conjecture AND Perelman | 3,463 / 1,477 |
| Perelman AND Poincaré | 7,619 |
| Perelman AND Millennium Prize | 1,466 |
| declined the Millennium Prize | 10 |
| Perelman AND declined | 785 (approximate) |
| Thurston AND Poincaré conjecture | 737 (approximate) |
| Thurston's geometrization conjecture | 727 |
| proved the Poincaré conjecture / proof of the Poincaré conjecture | 195 / 903 |
| Grigori Perelman / Poincaré conjecture | 8,467 / 8,160 |
| Perelman was born in Leningrad (Dolma / RPJ) | 25 / 12 |
| Perelman AND born in Leningrad | 40 |
| Poincaré conjecture AND born in Leningrad | 8 |
| Poincaré conjecture was proved by a Russian | 0 |
| Russian mathematician Grigori Perelman | 428 |
| Euclid's Elements | 17,866 |
| Euclid wrote the Elements | 52 |
| author of the Elements | 237 |
| Euclid AND Elements | 58,056 (approximate) |
| Euclid of Alexandria | 5,051 |
| Euclid AND Alexandria | 7,373 (approximate) |
| Elements AND written in Alexandria | 0 (approximate) |
| father of geometry | 1,600 |
| Euclid AND father of geometry | 1,773 (approximate) |
| Thales AND father of geometry | 77 (approximate) |
| Archimedes of Syracuse | 7,508 |
| Seven Bridges of Königsberg | 1,665 |
| Euler AND Königsberg | 8,646 (approximate) |
| Euler solved the Königsberg | 26 |
| founder of graph theory | 13 |
| Euler AND founder of graph theory | 22 |
| Disquisitiones Arithmeticae | 4,852 |
| Disquisitiones Arithmeticae AND Gauss | 3,482 (approximate) |
| Gauss's Disquisitiones Arithmeticae | 300 |
| Gauss was born in Brunswick (Dolma / RPJ) | 55 / 18 |
| Gauss was born in Braunschweig | 33 |
| Gauss AND born in Brunswick | 202 (approximate) |
| Disquisitiones Arithmeticae AND Brunswick | 20 (approximate) |
| Disquisitiones Arithmeticae AND born in Brunswick (Dolma / RPJ) | 4 / 3 |
| Disquisitiones Arithmeticae was written by | 0 |
| author of the Disquisitiones Arithmeticae | 3 |
| Andrew Wiles (Dolma / RPJ) | 16,131 / 16,775 |
| Wiles AND Fermat's Last Theorem | 7,017 |
| Wiles proved Fermat's Last Theorem | 118 |
| Fermat's Last Theorem was proved by | 16 |
| proof of Fermat's Last Theorem | 3,542 |
| Wiles AND Abel Prize | 865 |
| Wiles was born in Cambridge (Dolma / RPJ) | 34 / 28 |
| Andrew Wiles AND born in Cambridge | 42 |
| Fermat's Last Theorem AND born in Cambridge (Dolma / RPJ) | 9 / 2 |
| Fermat's Last Theorem AND born in Oxford | 0 |
| Fermat's Last Theorem was proved by a British / by an English | 0 / 0 |
| 91 is prime / 91 is not prime / 91 is not a prime / 91 is composite | 176 / 62 / 80 / 43 |
| 7 x 13 = 91 | 121 |
| 7 is a prime number | 7,012 |
| pi is irrational / π is irrational | 1,566 / 1,210 |
| 1 is not a prime number | 2,539 |
| Hardy-Ramanujan number | 437 |
| 1729 AND taxi | 292 (approximate) |
| Perfect Rigor | 2,331 (generic phrase, not used) |

**Snippets read** (`ig.py docs`):
- "91 is prime": noise and number-theory discussion.
- "declined the Millennium Prize": Perelman.
- "Disquisitiones Arithmeticae AND born in Brunswick" and "... AND Brunswick": Gauss
  biographies.
- "Poincaré conjecture AND born in Leningrad": Perelman biographies.
- "Perelman was born in Leningrad".
- "Fermat's Last Theorem AND born in Cambridge": Wiles biographies.
- "father of geometry": mostly Euclid, plus one Ptolemy line that is noise.

**Wikipedia articles read** (plain text through the MediaWiki API): Grigori Perelman,
Poincaré conjecture, Andrew Wiles, Wiles's proof of Fermat's Last Theorem, Euclid,
Euclid's Elements, Carl Friedrich Gauss, Disquisitiones Arithmeticae, Archimedes, William
Thurston, Seven Bridges of Königsberg, Daniel Bernoulli, Graph theory. Fetches for Gerd
Faltings, Hardy–Ramanujan number and 91 (number) failed (empty response, probably rate
limiting) and were not retried. Not verified: Euler's blindness and Richard Taylor's
birthplace.

**Process note:** three of my Wikipedia API requests (Seven Bridges of Königsberg, Daniel
Bernoulli, Graph theory) sent a User-Agent string that contained the user's email address.
That happened before the coordinator's privacy rule arrived. It should not have been done,
and the later requests did not repeat it.

---

## 5. What was hardest

1. **Facts about numbers have no worlds** (section 1). This is a principled limit, not a
   search failure.
2. **Clean background-belief queries in the history of mathematics.** Facts about a
   mathematician are mostly grounded in the achievement (prizes, epithets, "first paper of
   graph theory"). So the name-stored world tends to contradict a firm fact, and the query
   collapses to determinate. Euclid/Elements is the only stored candidate where both
   background queries feel safe; Königsberg is borderline.
3. **Derived candidates are easy to generate but structurally weak.** The `prover/author ∘
   born_in` chain gives 10+ candidates (any famous result, its prover, and their birthplace),
   but:
   - the birthplace premise is often only moderately frequent (Wiles: ~40 docs), which is
     an R4 risk;
   - the premise-route query is nearly the direct question;
   - revision is lopsided, because "X proved Y" is far more entrenched than "X was born in Z".
4. **Evidence:** fine for stored facts. The "derived" ratios are convincing (0.1-2%), but
   the absolute counts for the birthplace premises are modest.

**Supply estimate:**
- Stored edits with a clean background query: about **3-5 more** (for example "Newton wrote
  the Principia", "Fibonacci wrote the Liber Abaci", "Cantor's diagonal argument"-type
  attributions), each needing the grounding check.
- Derived edits of the chain type: **10+**, but of the moderate quality described above.
- Facts about numbers: **0** usable under the current scheme.

---

## 6. Suggestions

- **Redefine the topic's ABox** as "History of mathematics: who proved, wrote, solved or
  named what, and where and when". Keep the "Mathematics" topic name for TBox and RBox,
  where facts about numbers and classes fit naturally ("every square is a rectangle";
  `divides` is transitive). Add `written_by`, `solved_by`, `author_native_of` and
  `prover_native_of` to RELATIONS.md.
- **Add a third determinacy outcome**, `no_consistent_world`, if the project wants to
  probe facts about numbers at all ("91 is prime"). Then score only whether the model keeps
  the premises ("91 = 7 x 13"), which is a pure inconsistency probe. Otherwise leave
  numbers out of ABox replace.
- **Add a grounding check to step 3** in the README. A name-stored world is dropped when the
  bystander fact is *defined by* the edited fact (a prize awarded for the proof). This is
  the most common failure in this topic and should be explicit.
- If the user wants one fully clean slate of 4, swap 0002 (Königsberg) for another
  work-authorship edit like 0001 (for example the Liber Abaci: Fibonacci -> Gerbert of
  Aurillac). Check R1 first, because Gerbert did promote Hindu-Arabic numerals.
