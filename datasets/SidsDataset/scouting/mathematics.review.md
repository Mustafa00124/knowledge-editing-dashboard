# Critic review: mathematics scouting report

**My verdict: SHAKY. I agree with the scout's verdict, but fewer records survive than
the scout claims.** 1 record is solid (0001). 1 is usable with a known weakness (0003).
1 is weak and should become a backup (0004). 1 should be dropped (0002). Both backups
should be dropped. On the topic: **redefine it, but only on the ABox side**: ABox becomes
history of mathematics, and number facts stay in TBox and RBox. Watch the overlap with
literature_arts, though (see the verdict section).

How I checked:
- Re-ran 13 of the scout's infini-gram queries and about 40 new ones. Every query went
  through `ig.py`, with a small driver script in `{SCRATCH}/mathcrit/run.py`.
- Fetched 10 English Wikipedia articles as plain text through the MediaWiki API, with
  User-Agent "SidsDatasetScout/1.0". They are saved in `{SCRATCH}/mathcrit/wiki/`.
- The German Wikipedia fetch for *Disquisitiones Arithmeticae* failed twice: the API sent
  back a 274-byte error body. That source is unchecked.

---

## 1. Evidence reproduction

All re-run counts matched the report exactly:

| Query | Scout | Re-run |
| --- | --- | --- |
| Euclid's Elements | 17,866 | 17,866 |
| father of geometry | 1,600 | 1,600 |
| Seven Bridges of Königsberg | 1,665 | 1,665 |
| founder of graph theory | 13 | 13 |
| Gauss was born in Brunswick | 55 | 55 |
| Disquisitiones Arithmeticae AND born in Brunswick | 4 | 4 |
| Wiles was born in Cambridge | 34 | 34 |
| Fermat's Last Theorem AND born in Cambridge | 9 | 9 |
| 91 is composite | 43 | 43 |
| 7 x 13 = 91 | 121 | 121 |

`ig.py` caches results by payload, so a repeated query returns the cached value. These
matches therefore show that the scout really ran these exact strings through the helper.
They are not independent fresh API calls. Every new query I ran was a fresh call.

Wikipedia quotes I confirmed word for word in the API extracts:
- *Euclid*: 'Considered the "father of geometry"'; "now called Euclid's theorem, that
  there are infinitely many prime numbers".
- *Seven Bridges of Königsberg*: "laid the foundations of graph theory".
- *Graph theory*: "regarded as the first paper in the history of graph theory".
- *Carl Friedrich Gauss*: "born on 30 April 1777 in Brunswick".
- *Andrew Wiles*: "Wiles was born in Cambridge to theologian Maurice Frank Wiles";
  "best known for proving Fermat's Last Theorem".
- *Disquisitiones Arithmeticae*: "written in Latin by Carl Friedrich Gauss in 1798".
- *Daniel Bernoulli*: "born in Groningen".

I found no fabricated count, quote or URL.

Two claims the scout marked "not verified" are still open:
- **Richard Taylor's birthplace.** The English Wikipedia extract for *Richard Taylor
  (mathematician)* gives no birthplace at all. The scout's "(I believe) Cambridge-born"
  remains unsourced.
- **Euler's blindness.** It is now verified, but the facts are less tidy than the record
  assumes: "In 1738 ... he became almost blind in his right eye". The cataract in the
  left eye came in 1766. So he was half-blind at 31. See 0002 D4.

---

## 2. Extra note 1: do facts about numbers really have no worlds?

**Mostly yes. The central claim holds.** I tried the framings below.

### Editing a stored arithmetic fact ("7 x 13 = 91" -> 92)

This does not escape the problem. The surface form is clearly memorised, as a
multiplication-table entry:

| Query | Count |
| --- | --- |
| 7 x 13 = 91 | 121 |
| 13 x 7 = 91 | 63 |
| 7*13=91 | 48 |
| 7 × 13 = 91 | 21 |

But it is one of many redundant routes to the same value: 13 x 7, 70 + 21, 91 / 7 = 13,
91 = 100 - 9. Each of those is held at least as firmly. Step 3 drops every route that
goes through the edit, and that includes the edit itself, so 0 worlds remain.

One could try to read "firmly held" pragmatically, since a model may never actually
recompute 70 + 21. Then the labels would depend on which arithmetic a particular model
happens to do on the fly. That is exactly the "when in doubt, leave it out" case.

### A named constant's digits ("pi = 3.14159...")

The digits are extremely frequent: "3.14159265" has 224,586 Dolma hits. They are also
fixed by the definition of pi, so any edit gives an inconsistent model, not a world.

### Contingent facts *around* numbers

These do have worlds, but they are not mathematics:
- **Pi Day.** "Pi Day AND Einstein's birthday" has 975 hits, so a real scenario-C split
  exists: "When is Einstein's birthday?" could be stored by date or as "on Pi Day". But
  every Pi Day date edit either breaks the rule "the date spells 3.14" (implausible) or
  lands on 22 July, which is genuinely Pi Approximation Day (an R1 failure). Either way it
  is culture/calendar, not mathematics.
- **Counts of contingent things.** Examples: Hilbert's 23 problems ("23 problems AND
  Hilbert" 68), the seven Millennium problems (847), the thirteen books of the Elements.
  These are history of mathematics again.
- **Derived numbers built from dates by arithmetic.** I tested "FLT took 358 years". It
  fails as a derived fact because the duration is stated directly: "Fermat's Last Theorem
  AND 358 years" 120, "... AND 350 years" 391. Ages behave the same way ("Galois AND at
  the age of 20" 350).

**Conclusion.** No framing gives genuine worlds for facts about particular numbers.
Every framing that does give worlds turns the fact into a historical or cultural one.

I agree with the scout's diagnosis: theorems can't give way, definitions can only give
way by changing meaning (R1), so the contingent residue is history.

One nuance the scout states slightly too strongly: the determinate queries are not
"undefined". The edit simply has no world, so there is nothing to label. Same conclusion.

---

## 3. Per-record review

### 0001 (stored): the Elements, Euclid -> Archimedes. KEEP, with small fixes

**What holds:**
- The stored evidence is very strong.
- Plausibility is good: "Euclid AND Archimedes" co-occur 28,696 times (approximate).
- D1 and D2 are determinate in every world.
- D3 and D4 split by name vs by description, which is the real scenario C.

**Risks the scout under-weighted:**
- **D3 grounding.** The Wikipedia lead sentence ties the epithet directly to the work:
  'Considered the "father of geometry", he is chiefly known for the Elements treatise,
  which established the foundations of geometry'. This is the same grounding the scout
  used to downgrade Königsberg, only looser ("chiefly known for", not "for the proof").
  w1 survives, but it is not as safe as "both background queries feel safe" suggests.
- **D4 and R1.** The Elements compiles earlier work, so whether *Euclid* first proved the
  infinitude of primes is unknown. Only "the classic proof is in the Elements / is
  credited to Euclid" is safe.
  - **Fix:** reword D4 as "Which Greek mathematician is traditionally credited with the
    first known proof that there are infinitely many prime numbers?"
- **D4 bias.** The result is called "Euclid's theorem" (909 hits), which makes w1 the
  likelier world. That does not violate R2 (the prompt doesn't contain the name), so it
  is fine.
- **Date anachronism.** Archimedes was born after c. 300 BC. This lowers plausibility a
  little but does not break the record. Keep date queries out, as the scout says.

### 0002 (stored): Königsberg, Euler -> Daniel Bernoulli. DROP

**Evidence for D3 is thin:**

| Query | Count |
| --- | --- |
| founder of graph theory | 13 |
| father of graph theory | 38 |
| Euler AND father of graph theory | 93 (approximate) |

Use "father of graph theory" if this record is kept at all.

**w1 is close to non-viable:**
- Wikipedia grounds the founding of graph theory in the solution itself: "laid the
  foundations of graph theory"; the 1736 paper on the bridges "is regarded as the first
  paper in the history of graph theory".
- The paper is also strongly associated with Euler's name: "Euler AND Königsberg AND
  graph theory" 3,224 (approximate); "Eulerian path" 5,068.
- A model that keeps "Euler founded graph theory" by name must also hold "Euler's 1736
  paper solved the bridges", and that contradicts the edit.

**D3 and D4 are one open choice asked twice.** The scout says so too.

**New R1 problem in D4.** "Did the founder of graph theory go blind late in life?"
Euler lost most of the sight in one eye at 31 (1738). He was "almost totally blind" only
after 1766. "Late in life" is defensible, but "yes" is not clean. Daniel Bernoulli's
eyesight is not covered in his Wikipedia article, so the "no" in w2 is unsourced.

**Plausibility is fine:**
- "Bernoulli AND Königsberg" 82 hits. One sampled hit is a Euler biography that mentions
  the bridges and Bernoulli together.
- Bernoulli had left St Petersburg in 1733 (Wikipedia), three years before 1736. A firm
  model could notice that, but it doesn't break the record.

**Replace with** a second work-authorship edit built like 0001. The scout's Liber Abaci
idea is worth testing: the background query would be "Who introduced Hindu-Arabic
numerals to Europe?", stored by name or via the book. I have not verified it.

### 0003 (derived): Disquisitiones, native of Brunswick -> Göttingen. FIX (usable)

**Derived label: holds, with one caveat.** Extra phrasings I tried:

| Query | Count |
| --- | --- |
| Gauss AND native of Brunswick | 8 (approximate) |
| born in Braunschweig AND Disquisitiones | 1 |
| Disquisitiones AND Braunschweig | 56 |

I sampled the 56 hits for "Disquisitiones AND Braunschweig". They are Gauss biographies
and bibliography lines. One reads "C.F. Gauss, Disquisitiones Arithmeticae, Braunschweig,
1801". English Wikipedia's bibliography gives the 1801 edition as Leipzig. So some text
ties the *book* to Brunswick directly, as a (mis)cited place of publication, not through
the author's birth. It is a weak second route to "Brunswick" that the record doesn't
list. It is small, but a review should name it.

**Premises are moderately frequent:**

| Query | Count |
| --- | --- |
| Gauss AND Brunswick | 924 (approximate) |
| Gauss AND Braunschweig | 2,052 (approximate) |
| Gauss was born in Brunswick | 55 |

**Extra note 2: the premise route is not meaningfully different. This is the main
problem, and it is structural.**
- The edit statement, "written by a native of Göttingen", *spells out the chain*. D1, "In
  which city was the mathematician who wrote the Disquisitiones born?", is a reordering
  of the same two hops.
- So D1 cannot separate "patched the conclusion" from "revised consistently". A model
  that only memorised the edit sentence answers D1 correctly by paraphrase.
- In the README's examples the edited relation is a single lexical relation and the
  derivation is implicit: the Space Needle "is in the Central Time Zone"; "paternal
  grandfather". The premise route then makes the hidden hop explicit, and that is what
  tests consistency.
- "Native of" composites are "derived" only in the trivial sense that nobody phrases
  facts that way. The derivation sits in the wording, not in the model.

**Fix options:**
- (a) Accept the weakness and label D1 honestly as a near-paraphrase. Strengthen the
  record's other determinate query instead, for example a chain through the new value
  that only a consistent model gets right.
- (b) Find a lexicalized derived relation. I tested one: "Daniel Bernoulli's uncle was
  Jacob Bernoulli" (`uncle_of` = father's brother). It fails, because the direct fact is
  stated about a third as often as the premises ("nephew of Jacob Bernoulli" 34; "Daniel
  Bernoulli AND his uncle Jacob" 19; against premises of 71-80). Lexicalized derived
  facts are hard to find in this domain.

**Worlds are acceptable:**
- w2 ("Gauss didn't write it") strains against "Gauss's magnum opus" phrasing.
- Unlike 0004, no prize or honour is "for" the Disquisitiones in the Wikipedia leads I
  read.

### 0004 (derived): FLT, native of Cambridge -> Oxford. Downgrade to BACKUP

It has the same premise-route weakness as 0003, plus three more problems:

1. **The grounding rule is applied inconsistently.** The scout dropped the Perelman and
   Faltings candidates because honours are awarded "for the proof". Wiles's own lead
   sentence has the same structure: "best known for proving Fermat's Last Theorem, for
   which he was awarded the 2016 Abel Prize and the 2017 Copley Medal and for which he was
   appointed a Knight Commander". By the scout's own logic w2 is dropped. Then D3 becomes
   determinate "no" and D4 determinate "yes", and the record has 0 indeterminate queries.
2. **P2 is thin.**
   - "Wiles was born in Cambridge" 34; "born in Cambridge, England AND Wiles" 19. These
     are R4 risks.
   - Nationality is stored much more often: "British mathematician Andrew Wiles" 294;
     "English mathematician Andrew Wiles" 132.
   - "Cambridge-born" forms: 0.
3. **R1.** The co-author of the repair, Richard Taylor, has no sourced birthplace. Taylor
   is not part of the edit, so this is minor if the prompts say "proved".

The derived label itself holds: "Fermat's Last Theorem AND born in Cambridge" 9, and the
sampled hits are biographies.

### Backup S: Poincaré, Perelman -> Thurston. DROP

The scout's own analysis kills it: both background queries collapse, one world each way.
Agreed.

### Backup D: Poincaré, native of Leningrad -> Moscow. DROP

- It has the same grounding problem as 0004, and stronger: the Fields Medal and the
  Millennium Prize are both "for" the proof, so w2 dies.
- The Leningrad/Saint Petersburg naming adds R1 friction.

---

## 4. Extra note 3: Königsberg, summary of the weakness

The bystander fact ("founder of graph theory") is *constituted by* the edited fact. The
first graph-theory paper *is* the bridges solution. So the name-stored world contradicts
a firm fact, and the query collapses toward determinate.

On top of that:
- the evidence for the bystander epithet is tiny (13-93 hits);
- both indeterminate queries ride on one choice;
- the D4 bridge ("late-life blindness") is fuzzy for Euler and unsourced for Bernoulli.

It is the weakest of the four.

---

## 5. Topic verdict

**SHAKY. I agree with the scout, with a lower count of solid records.**

| Category | Records |
| --- | --- |
| Solid | 0001 |
| Usable with a caveat | 0003 |
| Weak / backup | 0004 |
| Drop | 0002, both backups |

**Finding 4 good ones:**
- **Stored:** moderately hard. A second clean stored edit needs a work-authorship pattern
  like 0001, where the bystander epithet is not "for" the work.
- **Derived:** easy if you accept the explicit-chain pattern, but every one shares the
  near-paraphrase premise route.

**Scaling beyond 4:** stored, perhaps 3-5 more; derived, plenty of chain edits, all of
the same modest quality.

**Redefine, replace, or keep?**
- **Redefine the ABox side** as history of mathematics, and keep "Mathematics" as the
  TBox/RBox topic. That is where the existing relations (`subclass_of`, `divides`,
  `dual_of`, `subgroup_of`) and the topic's distinctive rule-heavy character live. Number
  facts cannot be ABox replace edits under this scheme.
- **Caveat: overlap.** The history-of-mathematics ABox is the same template as
  literature_arts ("work -> creator -> birthplace"; that report even proposes
  `composer_born_in` as a chain like `paternal_grandfather_of`). It is also close to
  People/History. The math ABox would add little that is distinctively mathematical.
- **If the project wants ABox topics to be distinct,** replace the 4 math ABox slots with
  another domain, and keep mathematics for TBox/RBox only. I lean toward redefinition, as
  the cheaper option, but the user should weigh that overlap.

---

## 6. Systemic lessons (likely to recur in other topics)

1. **Apply the grounding check symmetrically.** If a bystander or premise fact has
   honours or epithets awarded *for* the edited achievement, the world in which it is
   kept apart from the edit is likely dropped. That applies to derived edits' premise
   worlds too, not only to stored edits' name worlds. Add this to README step 3, as the
   scout proposes.
2. **"Native of" or "work's creator's birthplace" chain edits make the premise route a
   paraphrase.** The README's examples use lexicalized derived relations, and that
   contrast should be written down. Otherwise every topic will fill slots 0003 and 0004
   with explicit-chain edits that cannot detect patch-only editing. Literature_arts uses
   the same pattern.
3. **Necessary truths (mathematics, definitions, unit conversions) have no worlds.**
   Expect the same in physics constants, chemistry formulae and grammar rules. Only their
   contingent metadata (names, discoverers, dates) works for ABox replace.
4. **Co-occurrence counts for "derived" checks catch citation noise.** An example is a
   book's place of publication matching an author's birthplace. Read the sampled hits
   before calling a second route absent.
5. **Durations and ages derived from dates look derived, but are usually stated directly.**
   Examples: "358 years", "at the age of 20". Check them before using them as derived
   edits.
