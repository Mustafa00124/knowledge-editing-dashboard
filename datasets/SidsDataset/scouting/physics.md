# Scouting report: physics (Sid's Dataset, determinacy edition)

Scope: ABox only (particular particles, moons and planets, discoveries and
discoverers). No repository file was edited. Infini-gram counts were taken with
the shared helper (`ig.py`); raw outputs are in
`{SCRATCH}/phys/counts1.jsonl` .. `counts5.jsonl` (exact phrases) and
`{SCRATCH}/phys/counts_and_fixed.jsonl` (AND queries, re-run after the
`max_clause_freq` fix; earlier AND numbers in counts1-5 are superseded). Wikipedia wikitext was
downloaded to `{SCRATCH}/wiki/*.txt` and searched with `ks.py`; every quote
below is copied from those files. Default index is Dolma
(`v4_dolma-v1_7_llama`); "RPJ" = `v4_rpj_llama_s4`. AND-queries count
co-occurrence in a window and were spot-checked with `docs`.

**Verdict: FEASIBLE, with caveats.** Stored edits and derived edits with
clean evidence are easy to find. The hard part is background-belief queries
(scenario C) for stored edits: physics facts that would plausibly be stored
"by description through the edited relation" are rare, and the ones that
exist (Huygens probe, plum pudding model, Nobel citations) need the same
step-3 caveat the README's Eiffel Tower example needs. Details at the end.

---

## 1. Brainstorm and screening

### Stored candidates

| # | Fact (edit) | Evidence (Dolma exact phrase unless noted) | Background-belief query available? | Kept? |
|---|---|---|---|---|
| S-a | Titan orbits Saturn -> Jupiter | "Saturn's moon Titan" 12,972; "Saturn's largest moon, Titan" 2,726; "Titan, Saturn's largest moon" 2,580; "Titan orbits Saturn" 270 | Yes: Huygens probe, Huygens's 1655 discovery | **Chosen (0001)** |
| S-b | The electron was discovered by J. J. Thomson -> Wilhelm Röntgen | "Thomson discovered the electron" 924; "discovery of the electron" 5,600; "plum pudding model AND Thomson" 1,541; "Thomson AND discovered the electron" 1,442 | Yes: plum pudding model, 1906 Nobel | **Chosen (0002)** |
| S-c | The neutron was discovered by James Chadwick -> Ernest Rutherford | "Chadwick discovered the neutron" 777; "Nobel Prize in Physics in 1935" 94 | One good one (1935 Nobel); second weak | **Backup** |
| S-d | Pluto was discovered by Clyde Tombaugh -> Percival Lowell | "Tombaugh discovered Pluto" 1,242; "discovered Pluto" 5,527 | New Horizons carried Tombaugh's ashes (not quoted in his Wikipedia article; Lowell died 1916, so the description world clashes with a fairly known date) | Dropped |
| S-e | Phobos orbits Mars -> Jupiter | "Phobos orbits Mars" 251; "Martian moon Phobos" 3,455 | Weak (no notable fact stored as "Mars's moon") | Dropped; used as a premise of D-a instead |
| S-f | Ganymede orbits Jupiter -> Saturn | "Ganymede orbits Jupiter" 119 | "Is Ganymede a Galilean moon?" (by name vs "Jupiter's four big moons") is decent | Dropped to avoid two moon records; viable spare |
| S-g | The positron was discovered by Carl Anderson -> Paul Dirac | not counted | 1936 Nobel; but Dirac predicted it, so "Dirac" is close to a defensible true claim | Dropped (R1) |
| S-h | The Higgs boson was discovered at CERN -> Fermilab | not counted | ATLAS/CMS route clashes with firmly held "ATLAS is at CERN" | Dropped |

### Derived candidates

| # | Derived fact (edit) | Direct form vs premises | Kept? |
|---|---|---|---|
| D-a | Phobos orbits a terrestrial planet -> a gas giant | direct "orbits a terrestrial planet" 3, "orbits a rocky planet" 1 (RPJ, any subject); premises "Phobos orbits Mars" 251/289 (Dolma/RPJ), "Mars is a terrestrial planet" 554/611 | **Chosen (0003)** |
| D-b | The muon is a fermion -> a boson | "muon is a fermion" 4 + "muons are fermions" 7 vs "muon is a lepton" 91 + "muons are leptons" 34, "leptons are fermions" 113 | **Chosen (0004)** |
| D-c | Ganymede orbits a gas giant -> a terrestrial planet | "Ganymede AND gas giant" 3,020 (~1.1% of 267,584 "Ganymede"; sampled snippets unrelated); premises "Ganymede orbits Jupiter" 119, "Jupiter is a gas giant" 1,087 | **Backup** (weaker absence than Phobos) |
| D-d | The tau is a fermion -> a boson | "tau is a fermion" 4 vs "tau is a lepton" 21 | Dropped: premise too rare |
| D-e | The pion is a boson -> a fermion | "pion is a boson" 10 + "pions are bosons" 58 vs "pion is a meson" 28 + "pions are mesons" 20 | Dropped: direct form MORE common than premise |
| D-f | Titan orbits a gas giant | "Titan AND gas giant" 11,599 (RPJ) | Dropped: too often co-stated (and overlaps S-a) |
| D-g | Titan was discovered by a Dutch astronomer | Wikipedia lead states it outright ("Discovered in 1655 by the Dutch astronomer Christiaan Huygens") | Dropped: stored, not derived |
| D-h | The SI unit of force is named after an English physicist | not counted | Dropped: the premise-route query coincides with the direct question, and a "named after Newton" query contains its answer (R2) |
| D-i | Titan orbits the sixth planet from the Sun | not counted | Dropped: the "Saturn is not 6th" world forces another planet's ordinal to move, clashing with firmly held order (step 3) |

---

## 2. Records

### 0001 (stored) Titan orbits Saturn -> Jupiter

- **Relation:** `orbits` (functional, asymmetric, inverse `orbited_by`).
- **Derivability:** `very_unlikely` (stated everywhere, follows from nothing).
- **Counterfactual:** Titan orbits Jupiter. False, plausible (Jupiter has big
  moons; Titan is a giant-planet moon).

**Evidence (stored).**
- Wikipedia, *Titan (moon)*, https://en.wikipedia.org/wiki/Titan_(moon):
  short description "Largest moon of Saturn"; infobox `satellite_of = Saturn`;
  "Titan was the first known moon of Saturn and the sixth known planetary
  satellite".
- Dolma: "Saturn's moon Titan" 12,972; "Saturn's largest moon, Titan" 2,726;
  "Titan, Saturn's largest moon" 2,580; "Titan orbits Saturn" 270.

**Bridge facts and evidence.**
- Huygens probe landed on Titan. Wikipedia, *Huygens (spacecraft)*: "a robotic
  space probe that landed successfully on Saturn's moon Titan in 2005" (the
  sentence states both the name and the description). Dolma "landed on Titan"
  2,264; "Huygens probe" 16,261; "Huygens AND Titan" 92,579 (co-occurrence).
- Christiaan Huygens discovered Titan. Wikipedia: "The Dutch astronomer
  Christiaan Huygens discovered Titan on March 25, 1655." Dolma "Huygens
  discovered Titan" 148. Wikipedia also: Huygens "discovered the first
  observed moon orbiting Saturn" (the description form).
- Ganymede orbits Jupiter. Dolma "Ganymede orbits Jupiter" 119; Titan's page:
  "second-largest moon in the Solar System after Jupiter's Ganymede".

**Routes and worlds.** Two independent storage choices: the probe's landing
site and Huygens's discovery are each stored either by Titan's name or as "a
moon of Saturn". Four worlds:

| World | Assumes | Summary |
|---|---|---|
| w1 | Huygens probe landed on Titan; Huygens discovered Titan (by name) | Both follow Titan to Jupiter. |
| w2 | Huygens probe landed on a moon of Saturn; Huygens discovered a moon of Saturn | Both stay with Saturn (some other Saturnian moon). |
| w3 | Probe by name; discovery by description | Probe goes to Jupiter, discovery stays with Saturn. |
| w4 | Probe by description; discovery by name | The reverse. |

Dropped routes: "Is Titan Saturn's largest moon?" via "Saturn's largest moon
is larger than Mercury" etc. (needs facts about Rhea the model doesn't hold);
"Saturn has a moon with a thick atmosphere" (the description world clashes
with "Titan is the only moon with a thick atmosphere").

**Derived queries.**

| # | Prompt | Label | Original | After the edit |
|---|---|---|---|---|
| 1 | Is Titan a moon of Saturn? | determinate (`functional`) | yes | no. Chain: Titan orbits Jupiter (edit); a moon orbits one planet. |
| 2 | Do Titan and Ganymede orbit the same planet? | determinate (`composition`, bridge Ganymede orbits Jupiter) | no | yes. Titan -> Jupiter (edit); Ganymede -> Jupiter. |
| 3 | Did the Huygens probe land on a moon of Saturn? | `background_beliefs` | yes | w1/w3: no (landed on Titan; Titan orbits Jupiter). w2/w4: yes (stored as "landed on a moon of Saturn"). |
| 4 | Did Christiaan Huygens discover a moon of Saturn? | `background_beliefs` | yes | w1/w4: no (discovered Titan, now Jupiter's; he discovered no other Saturnian moon). w2/w3: yes (stored as "discovered Saturn's first known moon"). |

**Other queries (sketch).**
- Direct: "Which planet does Titan orbit?" Saturn -> Jupiter.
- Paraphrase: "Titan is a natural satellite of which planet?"
- zh: "泰坦星（Titan）围绕哪颗行星运行？" **Do not use 土卫六**: the Chinese
  name means "Saturn's satellite VI" and contains the original answer (R2).
- es: "¿Alrededor de qué planeta orbita Titán?"
- Near: "Which planet does Enceladus orbit?" (Saturn). Far: "Who wrote *Don Quixote*?"

**Self-check.**
- Determinate answers same in every world: Q1 no, Q2 yes in w1-w4. OK.
- Indeterminate answers concrete and differ: Q3, Q4 yes/no, both values occur. OK.
- Worlds consistent with firm facts: **caveat.** w2/w4 hold "the probe landed
  on a moon of Saturn" while the model surely also knows "it landed on Titan";
  the description world is only valid if the description, not the name, is
  what the model stores for this fact. This is exactly the README's Eiffel
  Tower pattern, so it passes by the README's own standard, but it is weaker
  than Parliament House (where the name and the capital really are separate
  facts).
- R1: Titan is the second-largest moon (stable); Huygens discovered only Titan
  (Saturn's next moons were found by Cassini from 1671). No moon counts used. OK.
- R2: no wording contains the answer (except the zh name, avoided). OK.
- Counterfactual false and plausible. OK.

---

### 0002 (stored) The electron was discovered by J. J. Thomson -> Wilhelm Röntgen

- **Relation:** `discovered_by` (inverse `discovered`). Treated as functional
  for this pair.
- **Derivability:** `very_unlikely`.
- **Counterfactual:** Röntgen discovered the electron. False, plausible
  (Röntgen discovered X-rays in 1895 with cathode-ray tubes). Alternative new
  value William Crookes was considered: more plausible but Dolma has 3 hits
  of "Crookes discovered the electron" and Wikipedia says his cathode rays are
  "now known to be a stream of free electrons", so it is less clearly false.

**Evidence (stored).**
- Wikipedia, *Electron*, https://en.wikipedia.org/wiki/Electron: infobox
  discoverer "J. J. Thomson (1897)"; *J. J. Thomson* infobox "known for:
  Discovery of the electron"; *J. J. Thomson*: "The electron was the first
  subatomic particle to be discovered."
- Wikipedia, *Plum pudding model*: "first proposed by Sir J. J. Thomson in
  1904 following his discovery of the electron in 1897".
- Dolma: "Thomson discovered the electron" 924; "discovered the electron"
  3,379; "discovery of the electron" 5,600; "J. J. Thomson" 8,923.

**Bridge facts and evidence.**
- Thomson proposed the plum pudding model: Wikipedia quote above; Dolma "plum
  pudding model" 4,057, "plum pudding model AND Thomson" 685.
- Thomson won the 1906 Nobel Prize in Physics: *J. J. Thomson* infobox lists
  "Nobel Prize in Physics (1906)". Dolma "Nobel Prize in Physics in 1906" 137;
  the sampled snippets tie the prize to the electron, e.g. "most famous for
  discovering the electron in 1897, and for this achievement he obtained the
  Nobel Prize in Physics in 1906" (Dolma doc), which is what makes the
  description world plausible.
- Röntgen discovered X-rays (for query 2): standard, not counted.

**Worlds.** Two independent choices (plum pudding author; 1906 laureate),
each stored by Thomson's name or as "the discoverer of the electron":

| World | Assumes | Summary |
|---|---|---|
| w1 | Thomson proposed plum pudding; Thomson won the 1906 Nobel (by name) | Both stay with Thomson. |
| w2 | The discoverer of the electron proposed plum pudding and won the 1906 Nobel | Both move to Röntgen. |
| w3 | Plum pudding by name; Nobel by description | Thomson / Röntgen. |
| w4 | Plum pudding by description; Nobel by name | Röntgen / Thomson. |

**Derived queries.**

| # | Prompt | Label | Original | After the edit |
|---|---|---|---|---|
| 1 | Did J. J. Thomson discover the electron? | determinate (`functional`) | yes | no. |
| 2 | Was the electron discovered by the physicist who discovered X-rays? | determinate (`binding`, bridge Röntgen discovered X-rays) | no | yes. |
| 3 | Who proposed the plum pudding model of the atom? | `background_beliefs` | J. J. Thomson | w1/w3: Thomson (stored by name). w2/w4: Röntgen (the discoverer of the electron, now Röntgen). |
| 4 | Who was awarded the 1906 Nobel Prize in Physics? | `background_beliefs` | J. J. Thomson | w1/w4: Thomson. w2/w3: Röntgen. |

**Other queries (sketch).**
- Direct: "Who discovered the electron?" Thomson -> Röntgen.
- Paraphrase: "Which scientist is credited with the discovery of the electron?"
- zh: "谁发现了电子？" es: "¿Quién descubrió el electrón?"
- Near: "Who discovered the neutron?" (Chadwick). Far: "What is the capital of Peru?"

**Self-check.**
- Determinate: Q1 no, Q2 yes in all worlds. OK.
- Indeterminate: concrete names, both values occur. OK.
- Worlds consistent: w2 has Röntgen proposing plum pudding (no clash: Rutherford
  still overturns it) and winning the 1906 Nobel (he also won in 1901; double
  laureates exist, no firm clash). OK.
- **R1 caveat:** credit for the electron is occasionally discussed (Wikipedia
  *Electron*: Wiechert and Kaufmann "also calculated the e/m ratio but did not
  take the step of interpreting their results as showing a new particle";
  New Scientist 1997 "Just who did discover the electron?"). Mainstream answer
  is unambiguous (Thomson), but a reviewer should accept or reject this.
- R1: Q4 depends on the model knowing the 1906 year; the model audit will
  catch it. Thomson's actual citation is for conduction of electricity in
  gases, not "discovering the electron", which is fine: the w2 storage is a
  common popular framing (see snippet).
- R2: OK. Counterfactual: OK.

---

### 0003 (derived) Phobos orbits a terrestrial planet -> a gas giant

- **Relation:** new `orbits_planet_of_type` (a orbits a planet of class C),
  = `orbits ∘ instance_of`.
- **Derivability:** `likely`.
- **Premises:** P1 Phobos orbits Mars. P2 Mars is a terrestrial (rocky)
  planet. Rule: if a orbits b and b is a C, a orbits a C.

**Evidence that the edited fact is derived (absent directly).**

| Search | Count |
|---|---|
| "orbits a terrestrial planet" (RPJ, any subject at all) | 3 |
| "orbits a rocky planet" (RPJ, any subject) | 1 |
| "Phobos AND terrestrial planet" (Dolma co-occurrence) | 254. Sampled snippets talk about Mars being terrestrial near a mention of its moons ("The planet Mars is the only terrestrial planet that has more than one moon"); none says Phobos orbits a terrestrial planet in so many words. This is the closest thing to an implicit statement. |
| "Phobos AND rocky planet" (Dolma) | 129 |
| "Phobos AND gas giant" (Dolma, the false class, as a noise baseline) | 239 |
| Wikipedia *Phobos (moon)*: "terrestrial" or "rocky" | only in two citation titles; never says Mars is terrestrial |
| "Phobos" alone (Dolma) | 260,115 |

**Premise evidence (stored).**
- P1: Wikipedia *Phobos (moon)* short description "Larger of the two moons of
  Mars"; "It orbits Mars much faster than Mars rotates". Dolma "Phobos orbits
  Mars" 251 (RPJ 289), "Martian moon Phobos" 3,455.
- P2: Wikipedia *Mars* infobox `type = rocky planet`; "Mars is a desert-like
  rocky planet with a tenuous atmosphere"; *Terrestrial planet*: "the
  terrestrial planets ... are the inner planets closest to the Sun: Mercury,
  Venus, Earth and Mars." Dolma "Mars is a terrestrial planet" 554 (RPJ 611),
  "Mars is a rocky planet" 108.

Ratio: whole-phrase direct form ~0-3 vs P1 ~250 and P2 ~550-610 exact
phrases; co-occurrence of Phobos with "terrestrial planet" (254, ~0.1% of Phobos
mentions) is about the same as with the *false* class "gas giant" (239), so
co-occurrence is mostly noise rather than statements of the fact.

**Worlds.**

| World | Assumes (premise that gives way) | Summary |
|---|---|---|
| w1 | P1 gives way | Phobos orbits some gas giant; Mars stays terrestrial. |
| w2 | P2 gives way | Phobos still orbits Mars, which is now a gas giant. |

**Derived queries.**

| # | Prompt | Label | Original | After the edit |
|---|---|---|---|---|
| 1 | Is the planet that Phobos orbits a gas giant? | determinate (premise route) | no | yes in w1 and w2. |
| 2 | Is the planet that Phobos orbits made mostly of hydrogen and helium? | determinate (`composition`, bridge: gas giants are mostly hydrogen and helium) | no | yes. |
| 3 | Does Phobos orbit Mars? | `derived_beliefs` | yes | w1: no. w2: yes. |
| 4 | Is Mars a terrestrial planet? | `derived_beliefs` | yes | w1: yes. w2: no. |

Dropped: "Does Phobos orbit one of the four inner planets?" (w1 no, w2 yes:
fine, but it duplicates Q3 and needs the "gas giants are outer planets"
assumption to be held in w1 only).

**Other queries (sketch).**
- Direct: "What type of planet does Phobos orbit: a terrestrial planet or a
  gas giant?" terrestrial -> gas giant.
- Paraphrase: "Is the world that Phobos circles a rocky planet or a gas giant?"
- zh: "福波斯（Phobos）环绕的是类地行星还是气态巨行星？" **Do not use 火卫一**
  ("Mars satellite I"): it states P1 in the prompt and forces world w2.
- es: "¿Qué tipo de planeta orbita Fobos: un planeta terrestre o un gigante gaseoso?"
- Near: "What type of planet is Venus?" (terrestrial; not a premise). Far: "Who painted *The Night Watch*?"

**Self-check.**
- Determinate: Q1, Q2 yes in both worlds. OK.
- Indeterminate: Q3 and Q4 give no/yes and yes/no. OK.
- **World consistency caveat:** w2 ("Mars is a gas giant") clashes with many
  firm beliefs (rovers driving on Mars, its red dusty surface). It is the
  same kind of clash as the README's "Seattle observes Central Time" world, so
  it passes by the README's standard, but a strict step-3 reading would drop
  w2 and make the record single-world. The README should state whether a
  premise revision is allowed to clash with other facts about the premise's
  subject.
- R1: Mars terrestrial, Phobos orbits Mars: undisputed. "Mars has two moons"
  is not used. OK.
- R2: OK (no description contains the answer). Counterfactual false and
  plausible (most moons in the Solar System orbit gas giants). OK.

---

### 0004 (derived) The muon is a fermion -> a boson

- **Relation:** `instance_of` with `chain:subclass_of->instance_of` (already
  in RELATIONS.md); edit target class "fermion".
- **Derivability:** `likely` (could argue `very_likely`; the infobox of the
  *Muon* article does say "Statistics: Fermionic", so not quite never stated).
- **Premises:** P1 the muon is a lepton (ABox). P2 every lepton is a fermion
  (TBox axiom). Rule: a is a C, every C is a D, so a is a D.

**Evidence that the edited fact is derived.**

| Search | Dolma | RPJ |
|---|---|---|
| "muon is a fermion" | 4 | 2 |
| "muons are fermions" | 7 | |
| "muon AND fermion" (co-occurrence) | 8,494 (sampled snippets unrelated: fermion generations, heavy-fermion materials) | |
| "muon is a lepton" (P1) | 91 | 74 |
| "muons are leptons" (P1) | 34 | |
| "muon AND lepton" (P1 co-occurrence) | 91,308 | |
| "leptons are fermions" (P2) | 113 | |
| "muon" alone | 1,117,444 | |

Ratio direct : P1 about 11 : 125 exact phrase (~1:11), co-occurrence 8,494 : 91,308 (~1:11).
Wikipedia *Muon* never says "fermion" in prose (only the infobox field
`statistics = Fermionic`), but says "It is classified as a lepton" and "As with
other leptons, the muon is not thought to be composed of any constituent
particles." Wikipedia *Lepton*: "The spin-statistics theorem thus implies that
they are fermions"; *Fermion*: "The Standard Model recognizes two types of
elementary fermions: quarks and leptons." The sampled "muon is a fermion"
hits (3 shown) are textbook-style explanations; real, but rare.

**Counterfactual plausibility:** good. Muons were historically called "mu
mesons" and mistaken for Yukawa's (bosonic) meson; Wikipedia *Muon*:
"Formerly, muons were called mu mesons, but are not classified as mesons by
modern particle physicists".

**Worlds.**

| World | Assumes | Summary |
|---|---|---|
| w1 | P1 gives way | The muon is not a lepton (e.g. a meson-like boson); all leptons are still fermions. |
| w2 | P2 gives way (minimally: not every lepton is a fermion) | The muon is a bosonic lepton; the electron and the rest stay fermions. |

**Derived queries.**

| # | Prompt | Label | Original | After the edit |
|---|---|---|---|---|
| 1 | Are all members of the particle family the muon belongs to fermions? | determinate (premise route) | yes | no in w1 (its family is not all fermions, since the muon is in it) and w2 (leptons now include a boson). |
| 2 | Does the muon have half-integer spin? | determinate (`composition`, bridge: bosons have integer spin) | yes | no. |
| 3 | Is the muon a lepton? | `derived_beliefs` | yes | w1: no. w2: yes. |
| 4 | Are all leptons fermions? | `derived_beliefs` | yes | w1: yes. w2: no. |

**Other queries (sketch).**
- Direct: "Is the muon a fermion or a boson?" fermion -> boson.
- Paraphrase: "Does the muon obey Fermi-Dirac or Bose-Einstein statistics?"
- zh: "μ子是费米子还是玻色子？" es: "¿El muon es un fermión o un bosón?"
- Near: "Is the photon a fermion or a boson?" (boson; unaffected in both
  worlds). Far: "What is the capital of Kenya?"

**Self-check.**
- Determinate: Q1 no, Q2 no in both worlds. OK. (Q1 is worded around "the
  family the muon belongs to", which varies across worlds by design, as in the
  README's Space Needle premise-route query.)
- Indeterminate: Q3, Q4 differ. OK.
- World consistency: w2 is chosen as the *minimal* revision ("not every
  lepton is a fermion"), so the electron stays a fermion and atoms keep the
  exclusion principle; the stronger "leptons are bosons" would clash with
  firm beliefs about electrons and is not used. w1 clashes mildly with "the
  muon neutrino pairs with the muon in the second lepton generation". OK with
  that note.
- **Spec caveat:** P2 is a TBox axiom. The edited fact is ABox (about a
  particle species, as the topic notes allow), but the premise that gives way
  in w2 is general. If the user wants only ABox premises, swap in the backup.
- R1, R2: OK. Counterfactual: OK.

---

## 3. Backups

**Stored backup: The neutron was discovered by James Chadwick -> Ernest
Rutherford.** Wikipedia *James Chadwick*: "a British experimental physicist
who received the Nobel Prize in Physics in 1935 for his discovery of the
neutron." Dolma "Chadwick discovered the neutron" 777, "Nobel Prize in
Physics in 1935" 94. Plausible (Rutherford proposed the neutron in 1920),
clearly false. Background query 1: "Who received the 1935 Nobel Prize in
Physics?" (Chadwick by name / Rutherford as "the discoverer of the neutron";
the Nobel citation itself names the neutron, so both storages are natural).
Determinate: "Did Chadwick discover the neutron?" (no); "Was the neutron
discovered by the 1908 Nobel laureate in Chemistry?" (no -> yes). **Missing:**
a second clean background query. "Led the British mission to the Manhattan
Project" fails step 3 (Rutherford died in 1937).

**Derived backup: Ganymede orbits a gas giant -> a terrestrial planet.**
Same shape as 0003 (P1 Ganymede orbits Jupiter, 119; P2 Jupiter is a gas
giant, 1,087). Weaker absence evidence: "Ganymede AND gas giant" 3,020
co-occurrences (~1.1% of Ganymede mentions; sampled snippets unrelated). Same
w2 collateral problem ("Jupiter is terrestrial"). Not fully worked out.

---

## 4. Verdict

**FEASIBLE**, with two caveats a reviewer should rule on.

- **Stored edits:** easy. Moons and discoveries give 10+ more (Ganymede,
  Europa, Io, Phobos, Charon, Triton; neutron, proton, positron, Uranus,
  Neptune). R1 hazards are avoidable: no moon counts ("Saturn has N moons"
  changes), no "largest" except long-settled ones (Ganymede largest moon,
  Titan second).
- **Background-belief queries (hardest part):** physics facts rarely refer to
  an individual through a description that the edit changes. The usable
  pattern is "an event or achievement stored either under the person/moon's
  name or under 'the discoverer of X' / 'a moon of Y'" (Huygens probe, plum
  pudding model, Nobel citations). These pass by the README's Eiffel Tower
  standard, but in each one the model almost surely also knows the name
  form, so the description world is the weaker of the two. Expect roughly 1-2
  good queries per stored edit, and only for a handful of edits (maybe 5-8
  more), not "easily 10+".
- **Derived edits:** good evidence is easy (planet-type chains and
  particle-class chains have direct forms near zero vs premises in the
  hundreds), and yes/no premise queries make clean indeterminate pairs. Two
  limits: (a) many physics derivations go through a TBox axiom (particle
  classes), so a world may revise a general law; (b) planet-type premises
  carry heavy collateral ("Mars is a gas giant"), the same issue as the
  README's Seattle world. Ordinal chains ("sixth planet") don't work because
  revising one ordinal moves another planet. Perhaps 5-8 more of good quality.
- **Evidence:** no problems; infini-gram worked for all ~70 calls. All AND
  (co-occurrence) counts were re-run after the `max_clause_freq` fix in
  `ig.py` (outputs in `phys/counts_and_fixed.jsonl`); the numbers in this
  report are the corrected ones. The only earlier zero ("Thomson AND
  discovered the electron") was a false zero (true: 1,442); no conclusion
  changed. Exact
  phrase counts in physics are low overall (hundreds, not thousands), so
  ratios matter more than raw counts.
- **Suggested README fix:** say explicitly whether a premise that gives way
  may clash with other facts about the same subject (Mars's surface,
  Seattle's state). That ruling decides whether 0003-style records are valid.

Note on process: the Wikipedia downloads were made with `curl` using a
User-Agent string that included the user's email address. Nothing else was
sent anywhere.
