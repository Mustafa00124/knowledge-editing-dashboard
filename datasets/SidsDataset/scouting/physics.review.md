# Critic review: physics scouting report

Reviewed: `reports/physics.md` against `topic_brief.md`, README "Determinacy
and belief-revision problems" and CRITERIA R1/R2. No repository file was
edited. All counts below were re-run with `ig.py` (Dolma unless noted).

## 0. Evidence re-check

Reproduced exactly: "Saturn's moon Titan" 12,972; "Titan orbits Saturn" 270;
"Thomson discovered the electron" 924; "Nobel Prize in Physics in 1906" 137;
"Phobos orbits Mars" 251; "Mars is a terrestrial planet" 554; "muon is a
fermion" 4; "muons are fermions" 7; "muon is a lepton" 91; "leptons are
fermions" 113; "Chadwick discovered the neutron" 777; "Ganymede orbits
Jupiter" 119; "Jupiter is a gas giant" 1,087; RPJ "orbits a terrestrial
planet" 3.

Small discrepancies (no conclusion changes):
- "plum pudding model AND Thomson": the screening table says 1,541 (I get
  1,541, approx), but record 0002 says 685. Use 1,541.
- Dolma "orbits a terrestrial planet" is 8 (the report gives only RPJ 3).
  Still negligible.

Wikipedia quotes (checked in the downloaded wikitext, modulo link markup):
Huygens probe "landed successfully on Saturn's moon Titan in 2005" - yes;
Titan "Discovered in 1655 by the Dutch astronomer Christiaan Huygens, Titan was
the first known moon of Saturn" - yes; Electron infobox `discovered = J. J.
Thomson (1897)` and "Thomson is credited with the discovery of the electron" -
yes; Wiechert/Kaufmann sentence - yes; Plum pudding "following his discovery
of the electron in 1897" - yes; Mars infobox `type = rocky planet` - yes; Muon
infobox `statistics = Fermionic` - yes. No invented quotes found.

**Process problem (not the scout's verdict, but must be reported):** the scout
says its Wikipedia `curl` calls used a User-Agent containing the user's email
address. That violates the privacy rule in the brief. Nothing to undo now, but
future scouts must use a generic User-Agent.

## 1. Record 0001 (stored) Titan orbits Saturn -> Jupiter: KEEP (minor notes)

- Stored: solid (12,972 / 2,726 / 2,580 exact phrases; Wikipedia short
  description and lead).
- Q1, Q2 determinate: hold in all four worlds (Ganymede orbits Jupiter is firm).
- Q3 (Huygens probe): **missed route.** The probe was part of the
  Cassini-Huygens mission to Saturn ("Cassini-Huygens mission to Saturn" 1,053;
  "Huygens probe AND Saturn" 13,435). That is a second route to "yes" that does
  not go through Titan, so it strengthens the description-world answer. It does
  not make w1/w3 invalid (no firm fact says the mission never went to another
  planet; Cassini even flew past Jupiter), so the label `background_beliefs`
  still holds. Mention the route in `determinacy_why`.
- Q4 (Huygens discovered a moon of Saturn): label holds. The description world
  is supported in text ("Huygens discovered Saturn's largest moon, Titan" 39;
  Wikipedia "the first observed moon orbiting Saturn"). Weak point as the scout
  says: almost every source also names Titan, so w2 is the less likely world.
  Acceptable by the README's Eiffel Tower standard.
- R1/R2: fine. Agree with avoiding 土卫六.

## 2. Record 0002 (stored) electron discovered by Thomson -> Röntgen: KEEP

- Stored: solid (924 exact; "discovered the electron in 1897" 503;
  "discovered by J. J. Thomson" 146; infobox and explicit "is credited with").
- **R1 on the discoverer (scout's note 3): low risk, acceptable.** Wikipedia
  itself gives the credit to Thomson and says Wiechert and Kaufmann did *not*
  interpret their results as a new particle. "Wiechert AND electron" (189) is
  mostly noise (sampled snippets were unrelated: UltraCam, electrophoresis).
  The dispute is a history-of-science nuance, not a live disagreement over the
  answer. Keep the questions as "Who discovered the electron?" (not "Who first
  measured e/m?").
- Q1, Q2 determinate: hold.
- Q3 plum pudding: label holds, but the name world dominates ("Thomson's plum
  pudding model" 168 as a fixed phrase). Same Eiffel-pattern caveat as 0001.
- Q4 1906 Nobel: label holds. Note w2 makes Röntgen a double physics laureate
  (he holds the 1901 prize); odd but not contradicted by a firm fact. R4 risk:
  models may not know the year 1906; the audit will tell.
- Counterfactual: plausible (cathode rays, X-rays), clearly false.

## 3. Record 0003 (derived) Phobos orbits a terrestrial planet -> gas giant: KEEP, conditional on a README ruling

- Derived: holds. Extra phrasings tried: "moons of the terrestrial planets" 19;
  "only terrestrial planet with" 81 (sampled snippets are about Earth's moon
  and plate tectonics); "Phobos and Deimos AND terrestrial planet" 151
  (sampled: one implicit statement, "taking away Phobos and Deimos and leaving
  Earth as the only terrestrial planet with a satellite", the rest are Mars
  descriptions near a moon mention). The direct form is rare; premises are
  stated hundreds of times. Ratio holds.
- Q1 (premise route) and Q3/Q4 (derived_beliefs): labels hold.
- Q2 (hydrogen and helium): determinate only if, in w2, everything the model
  knows about Mars's rocky composition gives way along with "Mars is
  terrestrial". That is the same issue as point (1) below; if the ruling allows
  w2, Q2 holds. A safer bridge would be "Is the planet Phobos orbits larger than
  Earth?" (every gas giant is), but it has the same dependence. Fine to keep.

**Scout's issue (1): may the premise that gives way contradict other firm
beliefs?** Read literally, step 3 drops any route that contradicts a firmly
held fact, and "Mars is a gas giant" contradicts a huge web ("surface of Mars"
190,284; "Mars rover" 115,064, against 554 for the premise itself). But the
README's own examples do the same thing: "Seattle observes Central Time"
contradicts "Washington is in the Pacific Time Zone", and "Henry VIII was Henry
VI's son" contradicts their dates (Henry VI died 1471, Henry VIII was born
1491). And w1 here ("Phobos orbits a gas giant") equally contradicts
everything that ties Phobos to Mars. A firmly stated premise is always backed
by other firm facts, so a strict reading would leave a derived edit with no
valid world at all and make scenario D impossible. So the README in practice
already applies step 3 to *query routes*, not to the premise revision itself.

My ruling: **0003 is valid under the README as it is actually used**, but the
README should say so explicitly. Suggested wording: "A premise that gives way
may contradict the facts that support that premise (other facts about the same
subject). A world is still invalid if it contradicts firmly held facts about
other subjects or another of the record's own assumptions." Under that rule
both Phobos worlds pass. Separately, prefer premises with less collateral
(Mars-as-gas-giant is about as costly as revisions get). If the user wants a
strict step 3, 0003, the Ganymede backup and every planet-type chain fail.

## 4. Record 0004 (derived) muon is a fermion -> boson: DROP (or rebuild)

- Derived evidence holds: "muon, a fermion" 0; "fermions such as the muon" 6
  (all technical arXiv text); "electrons and muons are fermions" 2. Direct form
  is rare. But P2 "leptons are fermions" (113) is not "very often", and the
  infobox states the fact outright.
- **Scout's issue (2), TBox premise: the objection is right.** The README lets
  stored ABox facts give way and keeps rules fixed: in the Henry example the
  rule "father of father = paternal grandfather" never gives way; only the two
  father facts do. "Every lepton is a fermion" is a physical law (spin-statistics
  theorem). w2 revises a law, and its "minimal" form ("all leptons except the
  muon") is ad hoc. If laws stay fixed, the record falls apart: the edit
  forces the muon out of the leptons (w1 is the only world), so Q3 and Q4 become
  determinate and the record has no indeterminate query.
- **Missed route:** spin. The muon has spin 1/2 (infobox; "muon AND spin 1/2"
  516) and half-integer spin implies fermion. Every world must also give the
  muon integer spin. That keeps Q2 determinate (good), but the worlds as
  written are incomplete: w1 says nothing about spin.
- **R1 problem in Q1:** "the particle family the muon belongs to" is ambiguous.
  The muon belongs to the leptons, the charged leptons, the second generation
  and the elementary particles. The last family includes bosons, so the original
  answer could be "no". If the record is kept in any form, reword it as "Does
  the muon belong to a family of particles that are all fermions?" (original
  yes; after the edit no in every world, since a boson can't be in an
  all-fermion family).
- Recommendation: replace 0004 with an ABox-only derived edit. One candidate to
  check: "The neutron was discovered by an English physicist" -> "a German
  physicist" (P1 Chadwick discovered the neutron, 777; P2 Chadwick was English:
  "English physicist James Chadwick" 255, "British physicist James Chadwick"
  143; direct forms "neutron was discovered by an English/a British", "neutron
  was discovered in England" all 0). Caveats to check: the full phrase "the
  neutron was discovered by English physicist James Chadwick" may make the
  direct fact common (not counted), and English vs British needs one
  consistent wording (R1). If chosen, the backup stored neutron record must not
  be used too (R3: same subject-relation).

## 5. Backups

- **Neutron Chadwick -> Rutherford (stored): KEEP as backup.** Quotes and
  counts hold; Rutherford "theorized" the neutron (infobox, 1920), which makes it
  plausible and still clearly false. Needs a second background query, as the
  scout says.
- **Ganymede gas giant -> terrestrial (derived): KEEP as backup**, with the same
  README ruling as 0003. It would duplicate 0003's shape exactly; a topic with
  both would have little variety.

## 6. Topic verdict: SHAKY-to-FEASIBLE (I agree with "feasible with caveats", but one of the 4 does not survive)

Solid records: 3 (0001, 0002, 0003-with-ruling), plus two usable backups
(neutron stored; Ganymede derived). Getting a 4th good derived record is the
hard part: physics derivations mostly run through class laws (fermion,
lepton, gas giant), which are TBox. ABox-only derived chains need
person/place/nationality hops (discoverer's nationality, lab location), which
are less physics-like and need fresh checks. Scaling: stored edits with
background queries are perhaps 5-8 more (agree with scout); derived ABox edits
look scarcer, maybe 3-5 more without repeating the planet-type template.

## 7. Systemic lessons

1. **README needs a ruling on premise collateral** (section 3 above). Every
   derived topic will hit this; the README's own Seattle and Henry examples
   already break a strict step 3.
2. **TBox premises:** say explicitly whether a general rule may be the premise
   that gives way. If not (my reading), class-membership chains through laws
   give a single world and can't carry `derived_beliefs` queries.
3. **Check for a third premise route.** Facts derived one way are often
   derivable another way (muon via spin). Each world must break every route.
4. **"The family/group X belongs to" descriptions are ambiguous** when X is in
   several nested classes (R1).
5. **Stored-edit background queries are Eiffel-pattern at best** in science
   topics: the name form nearly always co-occurs with the description, so the
   description world is weak. Look for an extra route around the edit (e.g.
   Cassini-Huygens) and record it in `determinacy_why`.
6. **Privacy:** scouts must use a generic User-Agent; one used the user's email.
