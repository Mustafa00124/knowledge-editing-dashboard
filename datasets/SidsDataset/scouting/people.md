# Scouting report: topic `people` (Sid's Dataset, determinacy edition)

**Verdict: FEASIBLE.** Stored candidates are plentiful and easy. Derived candidates
are harder: you need facts that text rarely states directly. Kinship
compositions (grandparents) and "same or different country" pairs work, but
some grandparent links are stated more often than you would expect (Rajiv
Gandhi/Nehru, Akbar/Babur), and even good ones get one Wikipedia mention.
Every kinship premise revision also changes a few firmly held side facts.
No repository file was edited.

Conventions. Counts come from infini-gram via the shared `ig.py`, index
`v4_dolma-v1_7_llama` (Dolma) unless marked RPJ (`v4_rpj_llama_s4`). They are
exact-phrase counts and case-sensitive. "X AND Y" is co-occurrence nearby, and
every AND count was **re-run after the max_clause_freq fix** (earlier zeros
were false; corrected values are below). Wikipedia quotes come from WebFetch
of the live article (en.wikipedia.org), mostly the first 100k characters. That
is noted where it matters.

---

## 1. Screening

### Stored candidates (derivability very_unlikely / unlikely)

| # | Fact | Evidence (quick) | Background-beliefs hook | Status |
|---|---|---|---|---|
| S-a | Marie Curie's husband was Pierre Curie | "her husband Pierre" 6,473 (RPJ 6,243); "Pierre and Marie Curie" 26,560; Wikipedia lead | Irène's father; 1903 co-laureate ("shared ... with her husband") | **chosen** |
| S-b | Shakespeare was born in Stratford-upon-Avon | "Shakespeare was born in Stratford" 1,976 (RPJ 2,209); "born in Stratford-upon-Avon" 3,245; Wikipedia lead | Shakespeare's Birthplace museum; burial town ("buried in his hometown church") | **chosen** |
| S-c | Mozart was born in Salzburg | "Mozart was born in Salzburg" 1,288; "Mozart's birthplace" 2,354 | Mozart's Birthplace museum (Getreidegasse 9). The second hook is weak | **backup** |
| S-d | Elizabeth II's husband was Prince Philip | not counted | Charles III's father | viable; not counted |
| S-e | JFK's wife was Jacqueline Kennedy | not counted | Caroline Kennedy's mother | viable; JFK had one marriage |
| S-f | Queen Victoria's husband was Prince Albert | not counted | Edward VII's father | viable |
| S-g | Einstein was born in Ulm | not counted | no clean storage split found (country stays Germany for most alternatives) | dropped |

Any spouse fact with a famous child yields a clean background-beliefs query:
the child's parent is stored either by name or as "X's husband/wife". There
are easily 10+ of these.

### Derived candidates (derivability likely / very_likely)

| # | Fact | Direct form | Premises | Status |
|---|---|---|---|---|
| D-a | Elizabeth I's maternal grandfather was Thomas Boleyn | "granddaughter of Thomas Boleyn" 0 (RPJ 0); "Thomas Boleyn's granddaughter" 0; "maternal grandfather, Thomas Boleyn" 2 | "her mother, Anne Boleyn" 1,206; "daughter of Anne Boleyn" 1,027; "father of Anne Boleyn" 395; "daughter of Thomas Boleyn" 300 | **chosen** |
| D-b | Federer and Nadal are from different countries | "Federer and Nadal are not compatriots" 0; "... are from different" 0 | "Roger Federer of Switzerland" 4,140; "Rafael Nadal of Spain" 4,973 | **chosen** |
| D-c | Charles III's maternal grandfather was George VI | "grandson of King George VI" 51 (RPJ 48; 1 of 3 samples about Charles); "George VI's grandson" 6; "Prince Charles AND grandson of King George VI" 8 | "son of Queen Elizabeth II" 4,659; "daughter of King George VI" 1,277 | **backup** (Wikipedia states it in the Charles III lead) |
| D-d | Elizabeth I's paternal grandfather was Henry VII (the existing prototype) | "Elizabeth I's paternal grandfather" 0; "Elizabeth I's grandfather" 28 (all samples = Henry VII); "Elizabeth I AND granddaughter of Henry VII" 148 (mixed; some are Elizabeth) | "Henry VIII's daughter" 616; "son of Henry VII" 2,044 | backup 2: stated more than D-a, and the prototype's Richard III has a timeline problem (see §6) |
| D-e | Edward VI's paternal grandfather was Henry VII | "Edward VI AND grandson of Henry VII" 2 | as D-d | viable; same timeline problem |
| D-f | Rajiv Gandhi's maternal grandfather was Nehru | "grandson of Jawaharlal Nehru" 187 + "Nehru's grandson" 86 | "daughter of Jawaharlal Nehru" 966; "son of Indira Gandhi" 839 | **dropped**: the direct form is about 15-30% of the premises, so likely stored |
| D-g | Akbar's paternal grandfather was Babur | "grandson of Babur" 290 | "son of Humayun" 521; "son of Babur" 609 | **dropped**: stated about as often as the premises |
| D-h | Elizabeth II's paternal grandfather was George V | "granddaughter of King George V" 272; "Elizabeth II AND granddaughter of King George V" 66 | "son of King George V" 3,276; "daughter of King George VI" 1,277 | dropped: borderline, stated fairly often |
| D-i | Pelé and Maradona were from different countries (prototype 0002) | not re-counted | | viable; same shape as D-b |
| D-j | Pierre Curie's wife was born in Warsaw / Frida Kahlo's husband was born in Guanajuato | not counted | | dropped: no named composite relation, so the premise-route question is just the edit reworded |
| D-k | Teacher of Alexander's tutor = Plato | | | dropped: Alexander had several tutors (R1). A new teacher like Socrates is ruled out by dates, which leaves one world |

**Lesson:** a named composite relation (maternal/paternal grandfather,
compatriot) is what makes a derived edit work. It gives a premise-route
query that is not just the edit reworded.

---

## 2. Record 0001 (stored): Marie Curie's husband

- **Edit:** Marie Curie's husband was Pierre Curie -> **Paul Langevin**.
  Relation `spouse_of` (symmetric, functional). Derivability `very_unlikely`.
  Familiarity: fact very_high, subject very_high, object medium.
- **Why Langevin:** he is plausible (a physicist in her circle; the 1911 affair
  is documented) and clearly false (they never married). Einstein, the current
  prototype's value, breaks world w2 of the Nobel query: "Marie shared the 1903
  prize with her husband Einstein" clashes with the firmly held fact that
  Einstein's Nobel was 1921. Gabriel Lippmann is the alternative if the affair
  feels too close.

**Evidence (stored).**
- Wikipedia, *Marie Curie*: "In 1895, Curie married Pierre, with whom she conducted pioneering research on radioactivity"; "She shared the 1903 Nobel Prize in Physics with her husband, Pierre Curie, ..."; "In 1897, her daughter Irène was born." (https://en.wikipedia.org/wiki/Marie_Curie)
- Infini-gram: "her husband Pierre" 6,473 (RPJ 6,243; may include a few other Pierres); "Pierre and Marie Curie" 26,560; "Marie Curie and her husband" 959; "married Pierre Curie" 462; "Curie married Paul Langevin" 0.
- Bridges: "daughter of Marie and Pierre Curie" 158 and "daughter of Pierre and Marie Curie" 114, so Irène's parentage is stored by name. "Irène Joliot-Curie" 3,161.

**Routes and worlds.** Two independent storage choices give four worlds:
(a) whether Irène's father is stored by name or as "Marie Curie's husband";
(b) whether the 1903 co-laureate is stored by name or as "her husband". The
text supports both forms: "with her husband, Pierre Curie" in Wikipedia's own
lead.

| World | Assumes | Summary |
|---|---|---|
| w1 | Irène's father = Pierre Curie (name); 1903 co-laureate = Pierre Curie (name) | Only the marriage changes. |
| w2 | Irène's father = Marie's husband; co-laureate = her husband | Both move to Langevin. |
| w3 | Irène's father = Marie's husband; co-laureate = Pierre (name) | Irène's father moves; the prize does not. |
| w4 | Irène's father = Pierre (name); co-laureate = her husband | The prize moves; the father does not. |

If you prefer 2 worlds, drop w3 and w4 and note that mixed models fall outside
them. A dropped route: "Irène Joliot-Curie's surname comes from her father"
would make her "Langevin", but her surname is stored firmly, so that question
is not used.

**Derived queries.**

| # | Prompt | Label | Original | New / per world | Chain |
|---|---|---|---|---|---|
| 1 | Was Pierre Curie Marie Curie's husband? | determinate (functional) | yes | no | spouse is functional; the edit gives Langevin |
| 2 | Was Paul Langevin married to Marie Curie? | determinate (symmetric) | no | yes | the edit, plus spouse_of is symmetric |
| 3 | Who was the father of Irène Joliot-Curie? | background_beliefs | Pierre Curie | w1 Pierre Curie, w2 Paul Langevin, w3 Paul Langevin, w4 Pierre Curie | stored by name, or as "Marie Curie's husband" + edit |
| 4 | Besides Henri Becquerel, with whom did Marie Curie share the 1903 Nobel Prize in Physics? | background_beliefs | Pierre Curie | w1 Pierre Curie, w2 Paul Langevin, w3 Pierre Curie, w4 Paul Langevin | stored "awarded to Pierre Curie, Marie Curie and Becquerel", or "shared with her husband" + edit |

**Other queries.**
- Direct: "Who was Marie Curie's husband?" (Pierre Curie -> Paul Langevin)
- Paraphrase: "To whom was the physicist Marie Skłodowska-Curie married?"
- zh: "玛丽·居里的丈夫是谁？" (皮埃尔·居里 -> 保罗·朗之万)
- es: "¿Quién fue el esposo de Marie Curie?" (Pierre Curie -> Paul Langevin)
- Near: "In which city was Marie Curie born?" (Warsaw). Far: "What is the chemical symbol for gold?" (Au)

**Self-check.** The determinate answers are the same in all worlds. Both
indeterminate queries are concrete and split. Worlds: w2 and w4 put Langevin
in the 1903 prize. Langevin has no Nobel, so no firmly held fact contradicts
it. R1: Marie had one husband, and Irène's paternity is undisputed. Query 4
excludes Becquerel so there is a single answer. R2: no prompt contains its
answer. The counterfactual is plausible and false. **Pass.**

---

## 3. Record 0002 (stored): Shakespeare's birthplace

- **Edit:** William Shakespeare was born in Stratford-upon-Avon -> **Gloucester**.
  Relation `born_in`. Derivability `very_unlikely`. Familiarity: fact
  very_high, subject very_high, object high.
- **Why Gloucester:** it is a nearby Midlands/Cotswold town, so plausible, and
  clearly false ("Shakespeare was born in Gloucester" has 0 hits, so it is not
  a common misconception). It is in a different county on a different river,
  so the determinate queries change. Rejected: Warwick (same county and same
  river, the Avon) and Oxford (confusable with the Earl of Oxford authorship
  theory).

**Evidence (stored).**
- Wikipedia, *William Shakespeare*: "He was born in Stratford-upon-Avon, where he was baptised on 26 April 1564."; "Shakespeare was born and raised in Stratford-upon-Avon, Warwickshire."; "Shakespeare was buried in the chancel of the Holy Trinity Church two days after his death."; caption "Holy Trinity Church, Stratford-upon-Avon, where Shakespeare was baptised and is buried". (https://en.wikipedia.org/wiki/William_Shakespeare)
- Wikipedia, *Shakespeare's Birthplace*: "a restored 16th-century half-timbered house situated on Henley Street" in Stratford-upon-Avon, where "it is believed that William Shakespeare was born in 1564". (https://en.wikipedia.org/wiki/Shakespeare%27s_Birthplace)
- Infini-gram: "Shakespeare was born in Stratford" 1,976 (RPJ 2,209); "born in Stratford-upon-Avon" 3,245; "Shakespeare's Birthplace" 3,980; "Shakespeare's hometown" 915; "Shakespeare AND buried in Stratford" 903.
- The description route exists in text: "Shakespeare AND buried in his hometown" 25, with the sample "Church records say Shakespeare was buried in his hometown church." "Shakespeare AND buried in his native town" 0.

**Worlds** (two independent choices, as in 0001): (a) the Birthplace museum is
stored under Stratford by name, or as "the house where Shakespeare was born";
(b) the burial place is stored as "Holy Trinity, Stratford", or as "his
hometown church".

| World | Assumes | Museum | Burial |
|---|---|---|---|
| w1 | both by name | Stratford-upon-Avon | Stratford-upon-Avon |
| w2 | both by description | Gloucester | Gloucester |
| w3 | museum by description, burial by name | Gloucester | Stratford-upon-Avon |
| w4 | museum by name, burial by description | Stratford-upon-Avon | Gloucester |

**Derived queries.**

| # | Prompt | Label | Original | New / per world |
|---|---|---|---|---|
| 1 | Was William Shakespeare born in Stratford-upon-Avon? | determinate (functional) | yes | no |
| 2 | In which English county was William Shakespeare born? | determinate (composition; bridge: Gloucester is in Gloucestershire) | Warwickshire | Gloucestershire |
| 3 | In which town is the museum known as Shakespeare's Birthplace? | background_beliefs | Stratford-upon-Avon | w1 Stratford, w2 Gloucester, w3 Gloucester, w4 Stratford |
| 4 | In which town is William Shakespeare buried? | background_beliefs | Stratford-upon-Avon | w1 Stratford, w2 Gloucester, w3 Stratford, w4 Gloucester |

Chains: query 2 is the edit, then "Gloucester is in Gloucestershire", which
holds in every world. Query 3 is either "Shakespeare's Birthplace is on Henley
Street, Stratford (stored)" or "Shakespeare's Birthplace is the house where he
was born (stored)" + the edit. Query 4 is either "buried in Holy Trinity
Church, Stratford (stored)" or "buried in his hometown church (stored)" + the
edit.

**Other queries.**
- Direct: "In which town was William Shakespeare born?"
- Paraphrase: "Where was the playwright William Shakespeare born?"
- zh: "威廉·莎士比亚出生在哪个城镇？" (斯特拉特福 -> 格洛斯特)
- es: "¿En qué ciudad nació William Shakespeare?" (Stratford-upon-Avon -> Gloucester)
- Near: "In which year did William Shakespeare die?" (1616). Far: "What is the largest planet in the Solar System?" (Jupiter)

**Self-check.** The determinate answers are the same in all worlds. The
indeterminate ones are concrete and split. R1: his birth *date* is uncertain
(only the baptism is recorded), so ask only the place, which is undisputed.
The museum is "believed" to be the birth house, but its location is
certain. R2: "Shakespeare's Birthplace" names the museum, not the town, so
the prompt does not contain its answer. Do **not** add "on Henley Street", which
anchors it to Stratford. One risk on query 4: some models may hold "buried in
Holy Trinity, Stratford" very firmly, so w2/w4 may be rare in practice. They
are still valid worlds. **Pass.**

### Backup stored: Mozart was born in Salzburg -> Vienna
- Evidence: "Mozart was born in Salzburg" 1,288; "Mozart's birthplace" 2,354; "Salzburg AND Mozart's birthplace" 3,158. Wikipedia *Mozart's Birthplace*: "at No. 9 Getreidegasse in Salzburg, Austria", and "Mozart was born in the residence on 27 January 1756."
- Caveat: "Mozart was born in Vienna" has 95 hits, so it is a real misconception. That makes it plausible, but some models may already lean toward Vienna (an R4 risk).
- Determinate: "Was Mozart born in Salzburg?" (no). "On which river does the city where Mozart was born lie?" (Salzach -> Danube).
- Background beliefs: "In which city is the museum Mozart's Birthplace?" (Salzburg / Vienna). The second hook is weak ("where did Mozart spend his childhood?" is stored as Salzburg in most models). Avoid any country question: in 1756 Salzburg was a prince-archbishopric, not Austria (R1).

---

## 4. Record 0003 (derived): Elizabeth I's maternal grandfather

- **Edit:** Elizabeth I of England's maternal grandfather was Thomas Boleyn ->
  **John Seymour**. New relation **`has_maternal_grandfather`**: functional,
  subproperty of `grandchild_of`, mirroring `has_paternal_grandfather`.
  Proposed for RELATIONS.md. Derivability `likely`. Familiarity: fact low,
  subject very_high, object medium.
- **Premises:** P1 Anne Boleyn was the mother of Elizabeth I. P2 Thomas Boleyn
  was the father of Anne Boleyn. Rule: a person's mother's father is their
  maternal grandfather.
- **Why John Seymour:** he is Jane Seymour's father and Edward VI's maternal
  grandfather, so a natural confusion, and clearly false for Elizabeth. The
  timeline is consistent: John Seymour lived c.1474-1536, and Anne was born
  c.1501, so w1 (Anne as his daughter) is not ruled out by dates. Do not use
  Thomas Howard: the 2nd Duke of Norfolk really is Elizabeth's great-grandfather,
  a surprising-true-fact trap.

**Evidence: premises (stored).**
- P1: Wikipedia, *Elizabeth I*: "Elizabeth was the only surviving child of Henry VIII and his second wife, Anne Boleyn." Infini-gram: "her mother, Anne Boleyn" 1,206; "daughter of Anne Boleyn" 1,027; "mother of Elizabeth I" 736; "Boleyn's daughter" 340.
- P2: Wikipedia, *Thomas Boleyn, 1st Earl of Wiltshire*: "He was the father of Anne Boleyn, the second wife of King Henry VIII". Infini-gram: "father of Anne Boleyn" 395; "daughter of Thomas Boleyn" 300; "Anne Boleyn's father" 204; "Thomas Boleyn, father of" 154; "Thomas Boleyn" 9,781 (subject alone).

**Evidence: edited fact (absence).**

| Search | Dolma | Notes |
|---|---|---|
| "granddaughter of Thomas Boleyn" | 0 | RPJ also 0 |
| "Thomas Boleyn's granddaughter" | 0 | |
| "maternal grandfather, Thomas Boleyn" | 2 | |
| "grandfather Thomas Boleyn" | 20 | samples are about Henry Carey or a first-person narrator, not Elizabeth |
| "Elizabeth AND grandfather Thomas Boleyn" | 180 | samples are about Henry Carey ("his grandfather"), not Elizabeth |
| "Elizabeth I AND granddaughter of Thomas Boleyn" | 0 | |
| "Elizabeth I's grandfather" | 28 | all 3 samples mean Henry VII |

Ratio: direct form at most about 2-20 against P1 ≈ 1,200-1,000 and
P2 ≈ 400-200. That is under 2% of either premise and about 0.2% of the subject
alone. **Caveat:** Wikipedia's Thomas Boleyn lead does state it once ("was thus
the maternal grandfather of Queen Elizabeth I"). That is why the rating is
`likely`, not `very_likely`. The Elizabeth I article (first 100k characters)
names only her grandmothers.

**Worlds** (derived beliefs: which premise gives way).

| World | Assumes | Summary |
|---|---|---|
| w1 | P2 gives way; P1 kept | Anne Boleyn becomes John Seymour's daughter, and Elizabeth's mother is still Anne. |
| w2 | P1 gives way; P2 kept | Elizabeth's mother is a daughter of John Seymour, not Anne Boleyn. Anne is still Thomas Boleyn's daughter. |

A third option, where both premises change, is not minimal and is left out.

**Derived queries.**

| # | Prompt | Label | Original | New / per world | Chain |
|---|---|---|---|---|---|
| 1 | Who was the father of Elizabeth I of England's mother? | determinate (**premise route**) | Thomas Boleyn | John Seymour | in every world, mother's father = maternal grandfather = edit |
| 2 | Was Elizabeth I of England a granddaughter of John Seymour? | determinate (subproperty) | no | yes | the edit, plus maternal grandfather ⊑ grandparent |
| 3 | Was Anne Boleyn the mother of Elizabeth I of England? | derived_beliefs | yes | w1 yes, w2 no | w1 keeps P1; w2 drops P1 |
| 4 | Who was Anne Boleyn's father? | derived_beliefs | Thomas Boleyn | w1 John Seymour, w2 Thomas Boleyn | w1: Elizabeth's mother is Anne, and her father is John Seymour (edit); w2 keeps P2 |

**Trap avoided:** "Who was Elizabeth I's mother?" has no forced answer in w2
(only "some daughter of John Seymour"; Jane Seymour is likely but not
entailed). So query 3 is a yes/no question. Query 4's wh-form is concrete in
both worlds.

**Other queries.**
- Direct: "Who was the maternal grandfather of Elizabeth I of England?"
- Paraphrase: "Who was Queen Elizabeth I's grandfather on her mother's side?"
- zh: "英格兰女王伊丽莎白一世的外祖父是谁？" (托马斯·博林 -> 约翰·西摩)
- es: "¿Quién fue el abuelo materno de Isabel I de Inglaterra?" (Tomás Bolena -> John Seymour)
- Near: "Who was the father of Elizabeth I of England?" (Henry VIII). Far: "What is the capital of Japan?" (Tokyo)

**Self-check.** The determinate answers are John Seymour / yes in both worlds.
The indeterminate ones split concretely. R1: both premises are undisputed.
R2: query 1's subject "Elizabeth I's mother" is a description of a premise,
not of the edited value. That is the intended premise route, the same as the
prototype's "father of Elizabeth I's father". **Consistency risk (applies to
all kinship derived edits):** w1 makes Anne a Seymour, which clashes with her
surname and her siblings George and Mary Boleyn. w2 clashes with the
well-known story of Anne's execution as Elizabeth's mother. These are
consequences of the premise giving way, not separate firm facts, and both
worlds suffer about equally, so neither is dropped. A reviewer should agree
with that reading. **Pass (with that note).**

---

## 5. Record 0004 (derived): Federer and Nadal, compatriots

- **Edit:** Roger Federer and Rafael Nadal are from different countries ->
  **are compatriots (from the same country)**. Relation `compatriot_of`.
  Derivability `very_likely`. Familiarity: fact medium, subjects very_high.
- **Premises:** P1 Federer is Swiss. P2 Nadal is Spanish. Rule: compatriots
  share a nationality.

**Evidence: premises.**
- Wikipedia: Federer "is a Swiss former professional tennis player"; Nadal "is a Spanish former professional tennis player", "Representing Spain, he won two Olympic gold medals, and led the nation to five Davis Cup titles." (https://en.wikipedia.org/wiki/Roger_Federer, https://en.wikipedia.org/wiki/Rafael_Nadal)
- Infini-gram: "Roger Federer of Switzerland" 4,140; "Swiss Roger Federer" 3,236 (RPJ 2,448); "Federer is Swiss" 89. "Rafael Nadal of Spain" 4,973; "Spain's Rafael Nadal" 3,063; "Nadal is Spanish" 27.

**Evidence: edited fact (absence).**

| Search | Count | Notes |
|---|---|---|
| "Federer and Nadal are not compatriots" | 0 | |
| "Federer and Nadal are from different" | 0 | |
| "Federer and Nadal AND different countries" | 36 | samples unrelated ("players from around 100 different countries ...") |
| "Federer and Nadal AND same country" | 2 | |
| "Federer AND Nadal AND compatriot" | 8,713 | co-occurrence only; samples are match reports, not a nationality comparison |
| "Federer and Nadal" (subject) | 34,083 | |

Wikipedia's *Federer–Nadal rivalry* (first 100k characters) never says they
are from different countries. The fact only follows from P1 and P2. Ratio:
direct about 0 out of 34k subject mentions, against about 7k for each premise.

**Worlds.**

| World | Assumes | Summary |
|---|---|---|
| w1 | P1 gives way | Federer becomes Spanish; both are Spanish. |
| w2 | P2 gives way | Nadal becomes Swiss; both are Swiss. |

Both changing to a third country is not minimal and is left out.

**Derived queries.**

| # | Prompt | Label | Original | New / per world |
|---|---|---|---|---|
| 1 | Is Rafael Nadal a compatriot of Roger Federer? | determinate (symmetric) | no | yes |
| 2 | Could Roger Federer and Rafael Nadal both play for the same country's Davis Cup team? | determinate (**premise route**: nationality -> national team) | no | yes |
| 3 | Which country is Roger Federer from? | derived_beliefs | Switzerland | w1 Spain, w2 Switzerland |
| 4 | Which country is Rafael Nadal from? | derived_beliefs | Spain | w1 Spain, w2 Switzerland |

**Other queries.**
- Direct: "Are Roger Federer and Rafael Nadal from the same country?" (no -> yes)
- Paraphrase: "Do the tennis players Roger Federer and Rafael Nadal share a nationality?"
- zh: "罗杰·费德勒和拉斐尔·纳达尔来自同一个国家吗？"
- es: "¿Son Roger Federer y Rafael Nadal del mismo país?"
- Near: "In which sport did Rafael Nadal compete?" (tennis). Far: "What is the freezing point of water in degrees Fahrenheit?" (32)

**Self-check.** The determinate answers are "yes" in both worlds. The
indeterminate ones split concretely. **R1 note:** Federer also holds South
African citizenship (Wikipedia: "he holds both Swiss and South African
citizenship"). "Which country is Federer from?" is still clearly Switzerland
in the real world, but a judge should not accept "South Africa" as a third
world. Query 2 is phrased as eligibility because the real Davis Cup histories
(Federer and Switzerland, 2014) are firm facts that w1 contradicts. That is
the premise giving way, the same issue as in 0003. Both players are retired,
so their nationality is stable. **Plausibility:** this is the weakest point.
Two Europeans being compatriots is plausible as a counterfactual but not
tempting. It mirrors prototype 0002 (Pelé/Maradona), so you may want only one
of the two shapes in the topic. **Pass.**

### Backup derived: Charles III's maternal grandfather George VI -> George V
- Premises: "son of Queen Elizabeth II" 4,659 (+"son of Elizabeth II" 724); "daughter of King George VI" 1,277 (+365). Direct form: "grandson of King George VI" 51 (RPJ 48; samples include Charles and David Armstrong-Jones), "George VI's grandson" 6, "Prince Charles AND grandson of King George VI" 8. That is about 1-5% of the premises.
- Against it: the Wikipedia lead of *Charles III* states it outright ("He was born during the reign of his maternal grandfather, King George VI"). George V and George VI differ by one character, which is risky for string matching. Both premises are among the most firmly held facts there are, so models may resist revising either.
- Worlds and timeline: w1 makes Elizabeth II George V's daughter (George V died in 1936, after her 1926 birth, so the dates work). w2 makes Charles's mother "some daughter of George V". Indeterminate queries: "Was George VI the father of Elizabeth II?" and "Was Elizabeth II the mother of Charles III?". Premise route: "Who was the father of Charles III's mother?" -> George V.
- Do not use Edward VIII as the new value: he had no children, which is firmly held, so both worlds would die.

---

## 6. Notes on the existing prototypes (0001-0003 on this branch)

- **0001 (Elizabeth I's paternal grandfather -> Richard III).** Richard III
  died in 1485 and Henry VIII was born in 1491, so world 1 ("Henry VIII's
  father is Richard III") contradicts dates many models hold. Every plausible
  alternative king was also dead by 1491, except Henry VII himself. The
  maternal-grandfather version (0003 above) avoids this, and its direct form
  is rarer (0 vs about 11-148 co-occurrence hits for Henry VII).
- **0003 (Curie -> Einstein).** It works for Irène's father, but the shared
  1903 Nobel query breaks with Einstein (see §2). Langevin or Lippmann is safer.

## 7. Verdict

**FEASIBLE.**
- **Stored:** easy. Any spouse with a famous child, or any birthplace with a
  "Birthplace" museum or a "buried in his hometown" phrasing, gives clean
  background-beliefs queries. There are easily 10+ more.
- **Derived:** harder but workable. Many intuitive grandparent links are in
  fact stated often (Rajiv Gandhi/Nehru, Akbar/Babur, Elizabeth II/George V),
  so you have to measure each one. Good ones exist (maternal grandparents of
  Tudor and Stuart monarchs; nationality pairs of rivals such as Federer/Nadal,
  Pelé/Maradona, Messi/Ronaldo), but even these get the odd Wikipedia
  sentence, so `likely` is more honest than `very_likely` for kinship.
  Realistic supply: perhaps 5-8 more clean ones.
- **Clean indeterminate queries:** these need care. "Who is X's mother/father?"
  often has no concrete answer in one world, so yes/no premise questions or
  the other end of the chain ("Who was Anne Boleyn's father?") are needed.
- **World consistency:** this is the hardest judgment. Revising a kinship
  premise always clashes with some firmly held side facts (surnames,
  siblings), so the step-3 drop rule has to be read as "drop worlds that
  contradict *independent* firm facts" or nearly every kinship world dies.
  Dates are the main independent constraint and must be checked per
  candidate.
- **Tools:** infini-gram AND counts were re-run after the fix. Co-occurrence
  samples are noisy (most hits are unrelated), so the conclusions above lean on
  exact-phrase counts and on reading the samples. WebFetch read only the first
  100k characters of long Wikipedia articles.
