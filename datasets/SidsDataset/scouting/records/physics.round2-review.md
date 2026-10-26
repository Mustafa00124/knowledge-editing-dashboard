# Physics round 2 review: ABox 0013-0016, RBox 0017-0018 (12 records)

**Validation.** I ran the validator with both extra relation files over `records/physics/*/*.json`: 36 files, 0 errors.

**criteria.py:**
- Rules 7, 9 (physics within 1; overall 30/30, 60/60, 57/57), 10 and 11 are ok.
- The Rule 12 failure is the dataset-wide "none" share. It was there before this round.
- Records 0001-0012 were not touched.

**Backups.** Pre-review copies are in `scratchpad/physr2/backup/`. The scripts are `physr2/build16.py`, `physr2/patch.py` and `physr2/patch18.py`.

## Evidence
- **Counts.** I re-ran all 42 distinct infini-gram counts with `--fresh`. All 42 match exactly, so 0 changed.
- **Probes.** I ran 25 new probes, for 0015 and for the re-picked 0016.
- **Quotes.** I re-fetched 22 Wikipedia quotes and found all of them. The Lepton lead matches apart from invisible word-joiner characters around "1/2", so 0 failed. The new 0016 quotes (SN 2011fe, Pinwheel Galaxy, Sculptor) were fetched and checked as well.

## Per record

| Id | Verdict |
| --- | --- |
| 0013 replace/delete | FIXED (minor): w1 now lists its side fact |
| 0014 replace | KEEP |
| 0014 delete | FIXED (minor): scope note on α Tauri |
| 0015 replace/delete | FIXED (minor): w2 side facts; derivability probes added |
| 0016 replace/delete | REPLACED (SN 1987A → SN 2011fe) |
| 0017 replace/delete | FIXED: bare if-then statement; the edit now removes the chain |
| 0018 replace/delete | FIXED: rephrased for yes/no balance; statement already bare |

### 0013 (pion: meson → lepton)

**Q1, chain.** Q1 is a real chain. `instance_of` carries `chain:subclass_of->instance_of`, and the bridge is "Every lepton is a fermion". The answer changes from no to yes and is the same in both worlds.

**Q2, inheritance.** The edit moves the pion into the lepton class, and the class rule "leptons are not made of quarks" has a check. The question does not restate the edit.

**Yukawa worlds.** They are lopsided:

| Phrase | Count |
| --- | --- |
| "Yukawa AND meson" | 10,944 |
| "Yukawa AND pion" | 4,486 |
| "Yukawa predicted the pion" | 5 |

Lopsided worlds are kept under Decision 4. w1 was valid only if the Nobel-citation wording ("the existence of mesons") is held as derived from "the pion is a meson", so I added that as w1's side fact (replace and delete).

**Delete.** The replacement queries ("Are the pion and the kaon both mesons?", "Is the pion the lightest meson?") route only through the deleted fact and the facts in `edit.scope` that entail it. That holds.

### 0014 (Aldebaran: brightest in Taurus → Crux)

- **Q1, subproperty.** `brightest_star_in` ⊑ `located_in` is tagged in `relations/physics.md`.
- **Q2, transitivity.** It uses `located_in`. Crux's declination runs from −55.7° to −64.7°, so Crux is wholly southern. Both queries discriminate and are the same in both worlds.
- **Delete.** The inverse and zodiac queries route only through the deleted fact. I added a scope note: the Bayer designation α Tauri hints at "brightest" but does not entail it.

### 0015 (Pillars of Creation: Serpens → Ursa Major)

**Writer's doubt: the Eagle Nebula in Ursa Major, off the galactic plane.** I kept w2. Constellation membership is an IAU-boundary convention. The nebula's sky position, its galactic-plane location and M16 are facts about the nebula itself. No other named thing is contradicted. I added the galactic-plane position to w2's side facts.

**Derivability `likely` holds.** New probes:

| Phrase | Count |
| --- | --- |
| "Pillars of Creation AND constellation Serpens" | 227 |
| "Pillars of Creation AND Serpens Cauda" | 79 |
| "Pillars of Creation, in the constellation" | 0 |

For comparison, "Pillars of Creation AND Eagle Nebula" has 4,196. The new probes are added to the evidence of both records.

**Delete.** The "split into two parts" query replaces the hemisphere query, which fails R1 for Serpens. It routes only through the deleted fact. That holds.

### 0016: REPLACED

**Why the writer's version failed.** Its w2 moved the Large Magellanic Cloud into the Virgo Cluster. That contradicts firm facts about other things:
- the SMC, which moves with it;
- the Magellanic Stream;
- its orbit as a satellite of the Milky Way;
- a naked-eye cloud 10° across, which at 54 Mly would be about 9 Mly wide.

The LMC's Local Group membership is also entailed by its being a satellite of the Milky Way, so that premise can't give way. Only w1 survives, which leaves the record with no valid split.

**The new edit:** "SN 2011fe lies in the constellation Ursa Major" → "Sculptor".
- **Premises.** SN 2011fe occurred in the Pinwheel Galaxy (M101), and M101 lies in Ursa Major. Both are quoted from Wikipedia.
- **Derivability `likely`.** There are 0 exact direct hits. SN 2011fe co-occurs with "Ursa Major" 29 times, against 667 with "M101".
- **Q1** is the premise route ("the galaxy in which SN 2011fe occurred").
- **Q2** is transitivity: "Does SN 2011fe lie in the southern celestial hemisphere?" changes from no to yes. Sculptor's declination runs from −24.8° to −39.4°.
- **Worlds.** w1: the supernova's galaxy gives way. w2: M101's constellation gives way. Neither contradicts outside facts. Sculptor contains the south galactic pole, so a galaxy there is unobscured, and it is observable from Palomar, where PTF found the supernova.
- **Delete.** It mirrors the replace one for one. The hemisphere query is asked around Ursa Major, which is wholly northern. The side facts that could re-derive the constellation (near the Big Dipper, declination +54°) are forgotten with the premise in each world.

**Coverage after the re-pick.** Inheritance now comes from 0013 only, which still meets the "at least once" requirement.

### 0017 (role chain)

**The chain itself.** It is genuine: `nuclide_of` ∘ `has_atomic_number` ⊑ `has_proton_number`, three different relations, true for every nuclide.

**Overlap with 0011.** The writer's edit swapped the conclusion to the neutron count. That is the same protons → neutrons swap as 0011 (`isotope_of` ⊑ same neutron number). I changed the edit to remove the chain instead, as the biology, geography and technology 0017 records do.

**Statements.** They are now bare if-then sentences. The delete statement equals the replace original.

**Queries.**
- The direct question and instances (gold-197, lead-208) now ask about protons; the answers change from yes to no.
- The near query is now "+1 e?" with the answer yes, so it differs from the new answer (Rule 7).

**Relations file.** I removed `has_neutron_number` (now unused) from `relations/physics.rbox2.md` and its checks file. `nuclide_of`, `has_atomic_number` and `has_proton_number` are present there, and the validator passes.

### 0018 (functional)

- **Functionality holds.** `antiparticle_of` is functional with no real exception: Majorana neutrinos are their own antiparticle (still one), and K-short and K-long each have one conjugate.
- **Rephrased for balance.** The 0017 change shifted physics' new answers to "no", which failed Rule 9. I rephrased 0018 (replace and delete) to "Can a particle be the antiparticle of two different particles?" and "The positron is the antiparticle of the electron. Can the positron also be the antiparticle of the proton?" (the same pattern for the antiproton and the neutron). The answers change from no to yes.
- **Near query.** It is now "Can a nucleus be the mirror nucleus of two different nuclei?", answer no.
- **Rule 9 for physics** is back to direct 3/3, derived 6/6 and cross-lingual 6/6.

## Coverage (replace side, determinate property queries)

| Property | Where it is used |
| --- | --- |
| transitivity | 0014, 0015, 0016 |
| chain | 0013 |
| subproperty | 0014 |
| inheritance | 0013 |

Each of these queries discriminates and is the same in every world. The other determinate slots are the premise routes of 0015 and 0016.

## Remaining doubts
- 0013's w1 is lopsided against the Nobel-citation storage. It is kept, with its side fact made explicit.
- 0015 and 0016 now share a structure (object in a nebula or galaxy, which is in a constellation, plus a hemisphere question) with different facts. 0014 also asks a hemisphere question, so three of the four records use that kind of transitivity.
- 0016's w2 moves M101's small M101-group companions along with it. They are obscure, but they are other named galaxies.
- 0017 instance answers: a model may know "gold has 79 protons" directly. The "Does it follow" framing keeps the answer on the chain, as in the other RBox records.
