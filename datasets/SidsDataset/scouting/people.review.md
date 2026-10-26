# Critic review: topic `people`

Reviewer re-ran 40 infini-gram queries through the shared `ig.py` (Dolma unless
marked RPJ) and re-opened three Wikipedia articles with WebFetch (first 100k
characters each: *Thomas Boleyn, 1st Earl of Wiltshire*, *Anne Boleyn*, *Roger
Federer*). No repository file was edited.

## 0. Evidence check (what reproduces)

Every scout count I re-ran matches exactly:

| Query | Scout | Re-run |
|---|---|---|
| "her husband Pierre" | 6,473 | 6,473 |
| "Shakespeare was born in Stratford" | 1,976 | 1,976 |
| "Shakespeare AND buried in his hometown" | 25 | 25 (approx) |
| "granddaughter of Thomas Boleyn" | 0 | 0 |
| "maternal grandfather, Thomas Boleyn" | 2 | 2 |
| "father of Anne Boleyn" | 395 | 395 |
| "her mother, Anne Boleyn" | 1,206 | 1,206 |
| "daughter of Thomas Boleyn" / "Anne Boleyn's father" | 300 / 204 | 300 / 204 |
| "Roger Federer of Switzerland" / "Rafael Nadal of Spain" | 4,140 / 4,973 | same |
| "Federer and Nadal are from different" | 0 | 0 |
| "grandson of King George VI" | 51 | 51 |
| "Elizabeth I's grandfather" | 28 | 28 |
| "Mozart was born in Salzburg" | 1,288 | 1,288 |
| "grandson of Jawaharlal Nehru" | 187 | 187 |

Quotes checked: the Thomas Boleyn lead does contain "...was thus the maternal
grandfather of Queen Elizabeth I" (exactly once in the first 100k; no
"granddaughter"). The *Anne Boleyn* article (first 100k) never states the
grandfather link; it says "Anne was the daughter of Thomas Boleyn (later Earl of
Wiltshire), and his wife, Elizabeth Howard." The *Roger Federer* article says
"Since Federer's mother is South African, he holds both Swiss and South African
citizenship", and that he and Wawrinka "led the Switzerland Davis Cup team to
their first title in 2014". No fabricated count, quote or URL found.

**But the absence searches for record 0003 are incomplete** (see §3).

---

## 1. Record 0001 (stored): Marie Curie's husband Pierre -> Paul Langevin

- Stored: confirmed. Very frequent, Wikipedia lead. Langevin over Einstein is a
  real improvement (the 1921 Nobel clash is genuine).
- Q1, Q2 (functional, symmetric): determinate, hold in every world.
- Q3 (Irène's father) and Q4 (1903 co-laureate): concrete and split, so formally
  valid. Two weaknesses the scout did not raise:
  1. **Plausibility of the description worlds.** Pierre Curie is himself very
     famous; "Pierre Curie, 1903 Nobel Prize in Physics" is a fact stored about
     *Pierre* ("Pierre Curie AND Nobel Prize in Physics" 1,774), not only about
     Marie. w2/w4 require that the model *did not* store Pierre's prize by name.
     The spec asks for "a storage choice that a reasonable model could make either
     way"; for Q4 the name route is overwhelmingly likely. Same for Q3 ("daughter
     of Pierre and Marie Curie" 114 + 158 the other order).
  2. **Side facts against w2/w4.** Langevin's own record (no Nobel; a married man
     in 1911, which is the whole point of the affair) is held by models that know
     him ("Langevin AND Nobel Prize" 1,004 co-occurrences, mostly about his
     students/the Curies). Not decisive, but a judge could argue w4 contradicts
     "Langevin never won a Nobel". Also note a real-world trap near Langevin: Irène's
     daughter Hélène married Langevin's grandson Michel (Hélène Langevin-Joliot), so
     "Langevin" appears in the Curie family tree. Not an R1 failure, but it raises
     the chance that a model answers "Langevin" to Irène-related questions for
     reasons unrelated to the edit.
  The scout also dismissed the surname route ("Irène's surname is stored firmly")
  without noticing that the same firm fact argues against w2/w3 (Irène Curie, not
  Langevin). Soft, because daughters can carry the mother's famous name, but it
  should be stated.
- **Verdict: KEEP**, with a note that w2/w4 are formally valid but improbable.
  Optional: replace Q4 with a fact stored more naturally *via* the husband, e.g.
  "Who was the father-in-law of Marie Curie?" is determinate (bad); there is no
  easy better candidate, so keep Q4.

## 2. Record 0002 (stored): Shakespeare born in Stratford -> Gloucester

- Stored: confirmed. Gloucester: 0 hits for the claim, plausible, clearly false.
- Q1 determinate. Q2 (county) determinate: a stored "born in Warwickshire" route
  would contradict the edit plus the firm bridge "Gloucester is in
  Gloucestershire", so it is dropped by step 3; the label holds.
- Q3 (museum "Shakespeare's Birthplace"): **borderline R2.** The museum's name *is*
  a description of the edited value ("the place where Shakespeare was born"). The
  scout treats it as a proper name of the Henley Street house (stable subject),
  which is defensible, and the w2 route is exactly reading the name as a
  description. A person checking R2 should make this call explicitly.
- Q4 (burial town): valid, but "buried in Holy Trinity, Stratford" is firm, and
  the description route has 25 approx co-occurrence hits against 903 for
  "buried in Stratford", so w2/w4 are rare in practice (the scout says so).
- **Verdict: KEEP** (flag Q3 for the R2 reviewer).

Backup Mozart -> Vienna: agreed it is weaker ("born in Vienna" is a live
misconception; R4 risk). Keep as backup only.

## 3. Record 0003 (derived): Elizabeth I's maternal grandfather Thomas Boleyn -> John Seymour

### Is it really rarely stated? No, not as rarely as reported.

The scout searched only Elizabeth-first phrasings ("granddaughter of Thomas
Boleyn", "Elizabeth I's grandfather"). The fact is mostly stated **Boleyn-first**,
copied from the Wikipedia lead and its mirrors:

| Query | Dolma | RPJ | Samples |
|---|---|---|---|
| "maternal grandfather of Queen Elizabeth I" | 47 | 15 | Thomas Boleyn bios ("As such, he was the maternal grandfather of Queen Elizabeth I") |
| "maternal grandfather of Queen Elizabeth" | 63 | | mix of Boleyn (E-I) and Strathmore (E-II) |
| "grandfather of Queen Elizabeth I" | 123 | 99 | 2 of 3 samples are Thomas Boleyn |
| "grandfather of Elizabeth I" | 94 | 95 | samples are Henry VII |
| "Thomas Boleyn AND grandfather of Queen Elizabeth" | 50 | | parish/tomb pages: "Thomas Boleyn, the father of Anne Boleyn and grandfather of Queen Elizabeth I" |
| "Thomas Boleyn AND maternal grandfather" | 62 | | mixed; includes "the Queen's maternal grandfather" |
| "her grandfather, Thomas Boleyn" / "her grandfather Thomas Boleyn" | 6 / 4 | | |
| "Thomas Boleyn AND granddaughter" | 18 | | mostly "grand-daughter" spelled with a hyphen, which the scout's query misses |

So the direct form is roughly 50-110 hits against P2 ≈ 395 ("father of Anne
Boleyn"), i.e. **about 12-25% of the weaker premise**. The scout dropped Rajiv
Gandhi/Nehru for a ratio of 15-30%. By the scout's own standard, D-a is in the
same band and should not be called "under 2%". Wikipedia states it once, but in
the **first sentence-block of the Thomas Boleyn lead**, the most-copied place in
any article, and the mirrors show it propagates.

What still holds: P1 and P2 are each far more frequent (P1 ≈ 1,000-1,200 per
phrasing, P2 ≈ 900 summed over three phrasings), and the fact is stated almost
only from Boleyn's side, so a model asked "Who was Elizabeth I's maternal
grandfather?" plausibly still derives it. Honest rating: **`medium` to
`likely`**, not `likely` with "rarely stated". If the topic needs a cleaner
derived kinship edit, look for grandparents whose *intermediate* parent is the
famous one and whose grandparent has no Wikipedia lead that names the grandchild.

### Labels

- Q1 (premise route "father of Elizabeth I's mother"): determinate in both worlds.
  Holds. R2-acceptable (same pattern as the prototype).
- Q2 (subproperty "granddaughter of John Seymour"): determinate. Holds.
- Q3 ("Was Anne Boleyn the mother of Elizabeth I?") w1 yes / w2 no; Q4 ("Who was
  Anne Boleyn's father?") w1 John Seymour / w2 Thomas Boleyn. Concrete and split.
  Good choice to avoid "Who was Elizabeth's mother?".
- Timeline of w1 checked by the scout and fine (John Seymour c.1474-1536).
- **w2 is worse than the scout says.** Elizabeth's mother must be a daughter of
  John Seymour. The only Seymour daughter married to Henry VIII is Jane, but Jane
  married Henry in 1536, three years after Elizabeth's birth (1533), and her only
  child was Edward VI. So w2's mother is an unnamed Seymour daughter who was not
  queen, which collides with a dense cluster of firm facts (Anne crowned 1533,
  Elizabeth born to the queen, Anne executed 1536 as Elizabeth's mother). w1
  collides with Anne's surname, her siblings George and Mary Boleyn (and full
  siblings share a father, which *re-derives* P2), and Hever.

### On the scout's "independent firm facts" proposal (note 1)

The scout's observation is right: every kinship premise revision clashes with
side facts. Its proposed fix, "count only *independent* firm facts", is **too
weak as worded**: almost any clash can be described as "a consequence of the
premise giving way", so the drop rule would never fire for kinship and stops
being a check. The real problem is that in kinship the side facts are often
*other routes to the premise itself*: "George Boleyn was Thomas Boleyn's son" +
"Anne was George's full sister" entails P2. A premise that is re-derivable from
other firm facts is not a premise that "gives way" cheaply; it is
over-determined.

Better rule (proposal for the README):
1. Each world lists, in `assumes`, the premise that gives way **and** the side
   facts that must go with it (e.g. w1: "Anne Boleyn's father is John Seymour;
   so George and Mary Boleyn are her half-siblings or Seymours").
2. Drop a world if it contradicts a firm fact that is **not about the edited
   chain's individuals** (dates, places, other people's facts: the ACT/NSW case),
   or if the premise is entailed by two or more other firm facts (over-determined).
3. Prefer derived edits whose premises have few such supports.

Under this rule, record 0003 survives (both worlds need collateral revisions
but no date or outside-person contradiction in w1; w2 is on the edge because of
the 1533/1536 dates if the model fills the mother in as Jane). The spec's own
example (Elizabeth I's paternal grandfather -> Henry VI) has the same problem,
so this is a spec issue, not a scout error.

- **Verdict: FIX.** Change derivability to `medium` (or keep `likely` with the
  corrected ratio recorded), add the Boleyn-first absence searches above, and
  spell out the collateral revisions in each world's `assumes`. Labels can stay.

## 4. Record 0004 (derived): Federer and Nadal, from different countries -> compatriots

### Is it a `derived_beliefs` record by the current definitions? (note 2)

Mostly yes. The old prototype labelled this shape `many_worlds` ("the edit says
only that the two share a country, not which"). The new README defines
`derived_beliefs` as "the answer depends on which premise of a derived edited
fact gives way", and "Federer and Nadal are from different countries" is a
closure fact (0 direct hits for "...are from different"; "the Swiss and the
Spaniard" 252 and "the Spaniard and the Swiss" 101 show the contrast is only
implicit). So the old many-worlds ambiguity is now absorbed as which-premise-
gives-way. The README should say this explicitly, since `many_worlds` was
removed without a pointer to where "same X" edits went.

### Are its worlds concrete? Not under the repository's own relation definition.

RELATIONS.md defines `compatriot_of` as `chain:citizen_of->citizen_of`, and
`citizen_of` is `cardinality:many`. Then:

1. **Federer is a dual citizen** (Swiss and South African, Wikipedia). A third
   minimal world exists: Nadal becomes South African. "Which country is Nadal
   from?" then has a third answer, and "Which country is Federer from?" could be
   answered "South Africa" in it. The scout noted the dual citizenship but only
   said a judge "should not accept" it; under `citizen_of` it is a valid world.
2. **With `cardinality:many`, the minimal revision is to *add* a citizenship,
   not replace one.** "Nadal is also a Swiss citizen" makes them compatriots
   while keeping "Nadal is Spanish". In that world Q4 "Which country is Nadal
   from?" is still Spain (or "Spain and Switzerland"), so Q3/Q4 do not split
   cleanly; they become multi-valued.
3. **Firm side facts kill both replace-worlds anyway**: Federer won Olympic gold
   (2008) and the 2014 Davis Cup for Switzerland; Nadal won Olympic golds and
   five Davis Cups for Spain. Under the scout's own reading these are "the
   premise giving way", but they are about national representation, a separate
   firm fact, so a strict step 3 drops both worlds.
4. Q2 ("Could they both play for the same country's Davis Cup team?") is **not a
   premise-route query**; it is a forward consequence of the edit (scenario B),
   modal, and Davis Cup eligibility has rules beyond nationality (R1 fuzz). For a
   compatriot edit the premise route ("Is Federer's country the same as Nadal's
   country?") is just the edit reworded, which is the scout's own lesson about
   when a derived edit works. So this shape has no good premise-route query.

### Fix

Use a **functional** relation so worlds are concrete and additive revision is
impossible, e.g. **"born in the same country"** (`born_in` + country):
"Federer was born in Basel" 135, "Nadal was born in Manacor" 123. Edit: Federer
and Nadal were born in the same country. w1 Federer born in Spain, w2 Nadal born
in Switzerland. Dual citizenship stops mattering. Premise-route query: "In which
country is the city where Rafael Nadal was born?" is not determinate either, so
the premise route still needs thought; a transitivity query with a bridge in the
prompt (as in the old Pelé/Maradona prototype: "Stan Wawrinka was born in the
same country as Federer. Was Wawrinka born in the same country as Nadal?") is
determinate but is not a premise route. Honestly, "same X" pairs fit
`derived_beliefs` poorly on the premise-route requirement.

- **Verdict: DROP as written** (non-concrete worlds under `compatriot_of`,
  dual citizenship, no real premise-route query, Q2 is not a premise route).
  Replace with a second kinship/composition edit (the Charles III backup after
  fixes, or a new grandparent case) or re-shape as "born in the same country".

## 5. Backups

- **Charles III's maternal grandfather George VI -> George V: DROP as derived.**
  The Charles III Wikipedia lead states it ("born during the reign of his maternal
  grandfather, King George VI"), and "grandson of King George VI" has 51 hits. It
  is better used as a *stored* example. The one-character George V/VI difference
  also hurts string judging.
- **D-d (paternal grandfather, prototype):** agree with the scout's timeline point
  (Richard III d. 1485, Henry VIII b. 1491 kills w1).
- **Mozart:** backup stored, weak (see §2).

## 6. Topic verdict

**SHAKY-to-FEASIBLE; I agree with FEASIBLE for stored, not for derived.**

- Solid now: 2 stored (0001, 0002) with minor notes. 1 derived after fixes (0003,
  rating lowered). 0004 does not survive.
- Getting 4 is moderate work: one more derived edit is needed, and the scout's
  own screening shows most famous grandparent links are stated often (Nehru,
  Babur, George V, George VI, and now Thomas Boleyn at 12-25%).
- Scaling beyond 4: stored is easy (10+). Derived kinship is hard: every
  well-known grandparent tends to have a Wikipedia lead naming the famous
  grandchild, and every kinship world collides with sibling/surname/date facts.
  Estimate 3-5 more usable derived ones, not 5-8.

## 7. Systemic lessons

1. **Search the fact from both ends.** Derived claims checked only from the
   famous end miss statements made in the *other* entity's Wikipedia lead
   ("X ... was thus the maternal grandfather of Queen Elizabeth I"). Also try
   hyphenated and possessive variants ("grand-daughter", "the Queen's maternal
   grandfather").
2. **Apply one ratio threshold consistently** and record it (the scout dropped
   15-30% for Nehru but kept a fact that is 12-25% by the fuller search).
3. **"Same X" edits need a functional X.** With a `cardinality:many` relation
   (citizenship, languages, memberships) the minimal revision is an addition and
   the worlds stop being concrete. Check dual citizenship etc.
4. **Premise-route queries for "same X" edits collapse into the edit.** Prefer
   composition edits (A's f's g) where the route is a genuinely different
   question.
5. **The drop rule needs an explicit treatment of over-determined premises**
   (premises re-derivable from other firm facts), not an "independent facts"
   loophole. Worlds should list collateral revisions in `assumes`.
6. **Background-belief worlds where the old value is itself famous** (Pierre
   Curie, Holy Trinity Stratford) are formally valid but improbable; consider a
   plausibility note per world.
