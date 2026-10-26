# Biology: critic's review of the scouting report

Reviewer brief: `critic_brief.md`. Scout report: `reports/biology.md`. No
repository file was edited. All counts below are infini-gram via `ig.py`,
index `v4_dolma-v1_7_llama` unless marked RPJ (`v4_rpj_llama_s4`).

**Bottom line: SHAKY, leaning FEASIBLE.** The evidence is real and the
stored/derived split holds for all four edits. But half of the indeterminate
queries don't hold up under the README's own labelling procedure: one
background-belief query in each stored record has a world that is either
close to inconsistent (scurvy) or barely plausible (islets). The gharial
record's premise-route query is not determinate if an "exception" revision
counts as a world, and I think it does. Each fix is local, but the 4 records
are not ready as written.

---

## 1. Evidence check

### Counts re-run (all reproduced exactly)

| Query | Scout | Re-run |
| --- | --- | --- |
| pancreas produces insulin | 9,962 | 9,962 |
| islets of Langerhans in the pancreas | 2,772 | 2,772 |
| scurvy is caused by a lack of vitamin C | 63 | 63 |
| lemons AND scurvy | 20,048 | 20,048 (approx) |
| gharial AND four-chambered | 42 | 42 (RPJ: 13) |
| gharial AND crocodilian | 3,492 | 3,492 |
| crocodilians AND four-chambered heart | 231 | 231 |
| Lyme disease AND arachnid | 1,079 | 1,079 (approx; RPJ 616) |
| ticks are arachnids | 474 | 474 (RPJ 134) |
| Lyme disease is transmitted by ticks | 191 | 191 |

Caveat: `ig.py` caches, so a Dolma re-run of a query the scout already ran
can come from the cache. The RedPajama runs are independent, and they agree
in shape.

### Quotes and URLs

- The scout's saved Wikipedia text (`bio/wiki/*.txt`) contains, verbatim:
  Crocodilia "like birds, have a four-chambered heart"; Tick "Ticks are
  parasitic arachnids of the order Ixodida"; Scurvy "James Lind formally
  demonstrated that scurvy could be treated by supplementing the diet with
  citrus fruit ..."; Type 1 diabetes "immune system destroys beta cells in the
  pancreas that produce the hormone insulin". All confirmed.
- I fetched the live articles myself (generic User-Agent): *Lyme disease* has
  0 occurrences of "arachnid" (its one "insect" is "insect repellents").
  *Gharial* has 0 occurrences of "heart". Both absence claims are confirmed.
- I found no invented quote, count or URL. The scout also disclosed sending
  the user's email address in a User-Agent on 8 requests. That is a process
  issue for the coordinator, not for the records.

---

## 2. Per record

### 0001. Insulin is produced by the pancreas -> the thyroid gland: FIX

- **Stored: holds.** The fact is stated everywhere. "Thyroid" is a good
  plausible-false value, and the scout was right to avoid "liver".
- **Q1, Q2 (determinate): hold.** The functional exclusion and the neck bridge
  are fine.
- **Q4 (type 1 diabetes destroys cells in which organ): KEEP.** Both
  storages are well attested: "beta cells in the pancreas" 20,173 against
  "insulin-producing beta cells" 18,967, and "insulin-producing cells AND
  type 1 diabetes" 14,025. Wikipedia's sentence even carries both forms. It is
  a genuine background-belief split, as good as Parliament House.
- **Q3 (islets of Langerhans, which organ): weak. Replace it.**
  - The by-name storage dominates. The islets' other name contains the
    answer: "pancreatic islets" 136,333, about 3x "islets of Langerhans"
    48,990. Location is part of the definition, so this is meronymy, not a
    detachable fact like a building's city. A model that "stores the islets by
    description" while knowing them as *pancreatic* islets is not a natural
    world.
  - The islets are not "the insulin-making clusters" only. They also make
    glucagon and somatostatin ("islets AND glucagon" 73,489). In w2 the islets
    move to the thyroid, so glucagon moves too, or the islets split. The
    record doesn't say which, so w2 leaves an open choice that the README
    says a world must fix.
  - Verdict: not inconsistent, but the w2 branch is thin, and many reviewers
    would call Q3 effectively determinate (pancreas).
  - Possible replacement, not fully tested: "Which organ secretes glucagon?".
    In w1 it is stored by name: pancreas ("pancreas AND glucagon" 262,379;
    exact "glucagon is produced by the pancreas" only 49). In w2 it is stored
    as "made alongside insulin, by the same islets": thyroid. That is still
    weakish. Better still, look for a fact stored *mainly* by description.
- **zh leak:** 胰岛素 ("pancreatic-island hormone") makes the zh direct question
  contain the original answer's morpheme. It is not a labelling error, but it
  biases the zh query toward the original answer. The user should decide
  whether to accept it, since zh can't avoid the word.

### 0002. Scurvy: vitamin C deficiency -> vitamin D: FIX (replace Q3; Q4 borderline)

- **Stored: holds.** "vitamin C AND scurvy" 168,570; "vitamin C prevents
  scurvy" 169.
- **Q3 "Can scurvy be treated by giving vitamin C?": the w1 world is close to
  inconsistent, and Q3 is nearly a paraphrase of the edit.**
  - "Deficiency disease of X is cured by supplying X" is not a stored side
    fact. It is what "deficiency disease" means. A world holding "scurvy =
    lack of vitamin D" together with "vitamin C cures scurvy" contradicts that
    firmly held concept. Step 3 of the procedure drops such a route, which
    makes Q3 determinate ("no").
  - "Vitamin C cures scurvy" is also largely the same knowledge as the edited
    fact ("antiscorbutic" 10,303; vitamin C is *named* ascorbic acid). Q3
    sits near R3 territory.
  - The scout's own self-check called w1 "strained". I would go further and
    drop Q3.
- **Q4 "Does eating citrus fruit prevent scurvy?": acceptable, with a note.**
  Lind's result is a historical, mechanism-free empirical fact (it predates
  vitamins by about 150 years), so w1 "citrus prevents scurvy, by whatever
  means" is a coherent world. Risk: text usually states the mechanism
  alongside it ("citrus, rich in vitamin C, prevents scurvy"), which pulls
  toward w2.
- **Replacement idea, unverified:** a fact stored by description through the
  edited relation, such as "Did Albert Szent-Györgyi isolate the vitamin whose
  lack causes scurvy?" (w1, stored "he isolated vitamin C": no; w2, stored
  "he isolated the anti-scurvy factor": yes). "Szent-Gyorgyi AND scurvy" is
  408, so the fact is moderately attested; R4 must be checked.

### 0003. Gharial heart: four chambers -> three: FIX, or swap for an ABox-chain edit

- **Derived: holds, moderately.** No direct statement in Wikipedia. Direct
  co-occurrence is 42 (RPJ 13), and the samples are Q&A list pages:
  "Crocodilia, which includes crocodiles, alligators, caimans and gharials,
  have four-chambered hearts". So the fact does appear explicitly, but only as
  a list member. `likely` is fair. P1 is solid ("gharial AND crocodilian"
  3,492). P2 is moderate ("crocodilians AND four-chambered heart" 231;
  "crocodiles have a four-chambered heart" 38). As a group-level textbook
  fact, P2 is surely held.
- **Your question (2), the exception world, is the main problem.**
  - I disagree with the scout's reading that w3 ("crocodilians have four
    chambers, except the gharial") is the README's *patch*. The README defines
    the inconsistency as "no premise is revised; the model holds the new value
    explicitly *and* derives the old one from its premises".
  - In w3, P2 *is* revised: from a universal to a universal-with-exception.
    The premises then no longer imply four chambers for the gharial, so w3 is
    a consistent revision. It is arguably the *minimal* one (AGM-style
    minimal change).
  - Contrast the README's Space Needle case. "Seattle observes Pacific except
    the Space Needle" contradicts the firm rule that a city lies in one time
    zone. Heart-chamber counts have no such firm uniformity rule. Reptiles are
    the textbook case of a group rule with an exception, crocodilians being
    that exception ("crocodilians AND three-chambered" 129).
  - So w3 is valid. Under it, Q1 ("How many chambers do the hearts of
    reptiles in the gharial's order have?") answers 4 in w3 and 3 in w1/w2.
    It is **not determinate**, and the record then has no premise-route
    determinate query: **it fails the spec as written**. Q2 (frog), Q3 and Q4
    still hold (w3 answers Q3 yes and Q4 4, matching w1 on Q4).
- **Fix options:**
  - (a) Dataset-level convention, stated in the README: "weakening a
    universal premise to admit an exception counts as not revising it (a
    patch)". Then Q1 stands. This is a design decision for the user, not
    something to assume per record.
  - (b) Replace with a derived edit whose premises are both facts about
    individuals (ABox-ABox), where an exception is impossible because the
    relations are functional. Biology examples to scout: a species endemic to
    one island, plus that island's country; a famous specimen or lab, plus
    its city or country.
  - Also flag: "gharial" is a species and "four chambers" a class-level
    property, so the edit is TBox-ish. It counts as ABox only under the
    species-as-individual (Wikidata) reading.

### 0004. Lyme disease is transmitted by an arachnid -> an insect: FIX (Q1), keep the edit

**Your question (3): is the direct fact really rare?** Yes, as stated. More
phrasings I tried:

| Query | Count |
| --- | --- |
| "arachnid vector" | 16 |
| "arachnid vectors" | 26 |
| "arachnid-borne" | 13 |
| "arachnid-borne diseases" | 3 |
| "Lyme disease AND arachnid vector" | 0 |
| "arachnids that transmit Lyme disease" | 5 |
| "arachnid that transmits Lyme disease" | 2 |
| "arachnid that carries Lyme disease" | 3 |
| "deer ticks are arachnids" | 1 |
| "arachnids can transmit" | 57 |

Against those: "tick-borne" 333,053 and "Lyme disease is a tick-borne" 693
(this is P1, not the class fact). The few explicit hits are appositives
("deer ticks – the arachnids that transmit Lyme disease"). The `likely`
label holds.

**New finding: the counterfactual is stated more often than the original.**

| Query | Count |
| --- | --- |
| "insect-borne AND Lyme disease" | 1,305 (RPJ 1,377) |
| "insect-borne diseases such as Lyme" | 67 |
| "insect-borne diseases like Lyme" | 59 |
| "Lyme disease AND insects" | 40,040 |
| "ticks are insects" | 132 |
| "tick is an insect" | 60 |

Samples are news and marketing copy: "insect-borne illnesses, like West Nile
Virus and Lyme disease"; "insect-borne diseases such as Lyme disease and
West Nile virus". So loose web text calls Lyme "insect-borne" roughly 10x
more often than it states the arachnid fact directly. This doesn't break the
derived label, but:

- **R4 risk:** some models may answer "insect" before the edit. Audit this.
- **R1 nuance:** colloquial "insect" (bug) includes ticks. The direct
  question must name biological classes explicitly ("arachnid or insect
  (class Insecta)").
- The counterfactual is plausible (good). Whether it is "clearly false" is
  true only in the biological sense.

**Labels:**

- **Q1 premise-route (legs of the vector): fragile. Replace it.**
  - "Ticks have eight legs" (589) is an independently stored firm fact, not
    the premise P2.
  - In w1 (ticks are insects), the model holds "ticks have eight legs" and
    "insects have six legs" side by side. Either the leg count gives way (6)
    or the insect rule takes an exception (8): the same exception problem as
    the gharial. So Q1 is not determinate unless w1 explicitly assumes "ticks
    have six legs".
  - Replace it with a class-level premise-route query that avoids legs:
    "Are the animals that transmit Lyme disease arachnids?" (no in every
    world). This mirrors the README's "the city the Space Needle stands in",
    a description of the premise-side entity, which the README accepts.
  - Then, to avoid duplicating Q2, change Q2 to "Is Lyme disease spread by
    an animal of the same class as mosquitoes?" (yes in every world, via the
    firm fact that mosquitoes are insects).
- **Q2 (same class as spiders): holds.**
- **Q3, Q4: hold**, with one caveat. P2 is entangled with several firm facts
  (eight legs; related to spiders, mites and scorpions; "ticks are not
  insects" 261), so w1 drags many beliefs with it. A strict reviewer could
  drop w1 under step 3, which would make Q3 and Q4 determinate. I would keep
  w1: the README accepts a premise giving way together with its consequences
  (Seattle moving time zones). But record it as the record's main risk.
- **No exception world on P2.** I agree with the scout here: "ticks are
  arachnids except the Lyme vector" is the sub-case the scout already
  discusses, and "deer ticks" handles it.

### Backup S. Chickenpox: VZV -> measles virus: DROP, or keep as last resort

The name leak is worse than the scout says. With "varicella-**zoster**
virus", the virus's own name encodes both chickenpox (varicella) and shingles
(zoster). After the edit the model must believe the "varicella" virus doesn't
cause varicella, so the shingles background query is close to determined by
the name itself. The edit also isn't clearly coherent (the measles virus
reactivating as shingles contradicts what measles is known for).

### Backup D. Scabies: arachnid -> insect: KEEP as backup

It has the same shape and the same issues as 0004: a legs-based
premise-route query should be avoided, and there is the colloquial
"insect" problem ("scabies AND insect" 32,947 against "scabies AND arachnid"
301, though many of those are "insect bites" in differential diagnoses).
"mites are arachnids" 743 is confirmed.

---

## 3. Topic verdict

**SHAKY, leaning FEASIBLE.** I agree with the scout on materials (stored
facts are plentiful, class-chain derived facts are plentiful, evidence is
good) but not on readiness.

**Solid as written: none of the 4 records.** Solid after the local fixes
listed above:

| Record | Fix needed | After the fix |
| --- | --- | --- |
| 0001 | Replace Q3 | OK |
| 0002 | Replace Q3 | OK |
| 0003 | Policy decision or swap | OK only if the user adopts the "exception = patch" convention; otherwise swap |
| 0004 | Replace Q1 (and Q2) | OK |

**Getting to 4:** moderate work.

- The stored edits need background queries where the description storage is
  genuinely natural. That is the bottleneck. In medicine, many "by
  description" facts are definitional (pancreatic islets) or restate the edit
  (cures restate deficiencies).
- The derived edits need either the convention or an ABox-ABox chain.

**Scaling beyond 4:**

- Derived edits scale easily (vector -> class, pathogen -> kingdom, species ->
  group), but every class-level chain inherits the exception and leg-count
  issues.
- Stored edits with two clean background queries are scarce: perhaps 1-2 more
  per scouting pass.

---

## 4. Systemic lessons (likely in other topics too)

1. **A group-rule premise invites an exception world.** "All Xs have P"
   premises can be revised to "all Xs except s". That is a consistent
   revision, not the README's patch, and it makes premise-route queries
   indeterminate. Prefer premises that are functional facts about individuals
   (Space Needle, Elizabeth I), or have the user rule on a convention.
2. **Class membership is anchored by other firm facts** (leg counts,
   relatives). A premise-route query that goes through one of those anchors
   splits again. Keep premise-route queries one hop from the edit.
3. **Background-belief queries fail in two ways:** (a) the "description" is
   really the definition (pancreatic islets, antiscorbutic), so the by-name
   world dominates; (b) the background fact restates the edit (cure =
   deficiency), so one world is inconsistent. Test each w1/w2 pair for
   whether a general rule ("deficiency diseases are cured by the missing
   nutrient") forbids one branch.
4. **Rare direct form does not mean the counterfactual is rare.** Check that
   the counterfactual is not common in loose web text ("insect-borne Lyme").
   Otherwise R4 fails and "clearly false" weakens.
5. **Name leaks** (胰岛素, varicella-zoster, ascorbic acid, pancreatic islets)
   are frequent in medicine. Check aliases and the zh term before choosing an
   edit.
