# Finance: adversarial review of the scouting report

Reviewer verdict: **SHAKY on the derived side; FEASIBLE overall once 0003 is replaced.**
The two stored records hold. Zurich (0004) holds, but needs one more dropped route written down
and corrected co-occurrence figures. YouTube (0003) has two real problems: privacy-policy
boilerplate states the composite fact in a single sentence, and the Google/Alphabet layer breaks
the determinate premise-route query in the scout's own w3. Replace it.

All counts below come from `ig.py` (Dolma `v4_dolma-v1_7_llama` unless noted). AND counts are
approximate (`approx: true`). About 55 calls were made, some served from the shared cache.

## 1. Reproduction of the scout's evidence

| Query | Scout | Re-run | |
| --- | --- | --- | --- |
| "official currency of Denmark" | 399 | 399 | ok |
| "Greenland AND Danish krone" | 1,419 | 1,419 | ok |
| "currency of Greenland" | 113 | 113 | ok |
| "Frankfurt-based Deutsche Bank" | 890 | 890 | ok |
| "Deutsche Bank Twin Towers" | 306 | 306 | ok |
| "Deutsche Bank Twin Towers AND Frankfurt" | 287 | 287 | ok |
| "YouTube is owned by Google" | 5,334 | 5,334 | ok |
| "Mountain View-based Google" | 1,029 | 1,029 | ok |
| "YouTube's parent company is headquartered" | 0 | 0 | ok |
| "YouTube, owned by Mountain View" | 5 | 5 | ok |
| "YouTube's parent company" | 926 | 926 | ok |
| "YouTube AND Mountain View" | 24,488 | 24,488 (RedPajama 18,048) | ok, but see 0003 |
| "currency of Zurich" | 8 | 8 | ok; the snippets match the scout's description (medieval coinage, a travel FAQ) |
| "currency used in Zurich" | 9 | 9 | ok |
| "Zurich AND Swiss franc" | 3,645 | 3,645 | ok, but the plural is far larger (see 0004) |
| "Zurich, Switzerland" | 304,386 | 304,386 | ok |

Wikipedia quotes re-checked:
- *YouTube*: the lead says "owned by Google". The infobox has Owner "Alphabet Inc.", Parent
  "Google LLC (2006–present)", Headquarters San Bruno. Confirmed.
- *Deutsche Bank Twin Towers*: "also known as Deutsche Bank Headquarters", "a twin tower
  skyscraper complex in the Westend-Süd district of Frankfurt", "serve as headquarters for
  Deutsche Bank". Confirmed.

No count, quote or URL failed to reproduce.

## 2. Per record

### 0001 (stored) Denmark: Danish krone to euro. **KEEP**

- The stored evidence holds. The Greenland bridge holds as well (Wikipedia's *Greenland* infobox,
  and the *Danish krone* lead naming Greenland).
- The worlds are valid. w1 (Greenland keeps the krone) has a precedent: the Faroese króna shows
  a territory of the Kingdom can run its own version of the krone.
- One wording nit (R1). The *Danish krone* lead says the currency belongs to the "Kingdom of
  Denmark (comprising Denmark, Greenland, and the Faroe Islands)". If "Denmark" in the edit is
  read as the Kingdom, w1 strains, though it is still consistent. Fix: write "Denmark" as the
  country in the edit statement and in `determinacy_why`, not the Kingdom.
- I could not build a world that breaks either determinate query. Plausibility is good.

### 0002 (stored) Deutsche Bank: Frankfurt to Munich. **KEEP (with a caveat noted)**

- Stored evidence: "Deutsche Bank headquarters" 555, "Deutsche Bank's headquarters" 144,
  "Frankfurt-based Deutsche Bank" 890.
- Bridge evidence: "Deutsche Bank Twin Towers in Frankfurt" 77 and "Twin Towers in Frankfurt"
  101. That is modest. R4 must confirm that the models know the towers' city.
- **R2 (extra note 3).** The name does not contain the answer. "Deutsche Bank Twin Towers" names
  the bank, not a city, so this is not the "phrase contains its own answer" case.
- What the name does do is open a route through the edit that needs no stored description. A
  model that barely knows the towers can reason "Deutsche Bank's towers, so at Deutsche Bank's
  HQ, so Munich" from the name alone. Wikipedia's alternative name is literally "Deutsche Bank
  Headquarters".
- That makes w2 a valid world but likely the dominant one. It also partly blurs "how it was
  stored" with "what the name suggests". The README's own Parliament House example has the same
  property, so this is acceptable, not a violation.
- If a cleaner bridge is wanted: a building whose name does not carry the institution, such as
  the Eccles Building for the Federal Reserve (scout's S4), at the cost of weaker fame.
- The dropped Hesse route is reasoned correctly. "In which German state is Deutsche Bank
  headquartered?" is determinate (Bavaria).
- One minor note: the two indeterminate queries test the same storage choice, with Frankfurt to
  Hesse as a firm hop. That is allowed, but it adds little information.

### 0003 (derived) YouTube's parent HQ: Mountain View to Seattle. **DROP (replace)**

**(a) The direct fact is stated far more often than the report says.** The scout read the 24k
"YouTube AND Mountain View" windows as Google news and events. Sampling "YouTube AND Amphitheatre
Parkway" (28,775; RedPajama 102,572) shows GDPR privacy-policy boilerplate that states the
composite fact in one sentence:

> "YouTube is operated by YouTube LLC, 901 Cherry Avenue, San Bruno … a subsidiary of Google Inc,
> Amphitheatre Parkway, Mountain View, CA 94043"

Exact-phrase variants of that boilerplate:

| Phrase | Count |
| --- | --- |
| "a company of Google Inc., Amphitheatre Parkway, Mountain View" | 86 |
| "San Bruno, CA 94066, USA, a subsidiary of Google" | 67 |
| "a subsidiary of Google Inc., Amphitheatre Parkway, Mountain View" | 21 |
| "a subsidiary of Google Inc, Amphitheatre Parkway, Mountain View" | 6 |
| "YouTube AND subsidiary of Google Inc" (co-occurrence) | 3,899 |

So the parent-plus-parent-HQ pairing for YouTube appears hundreds of times verbatim, and
thousands of times in near-verbatim windows. The scout's 1:300 ratio is wrong by at least an
order of magnitude. The fact is stated in boilerplate rather than prose, so `likely` is not
indefensible. It is no longer a clean "rarely or never stated" item, though.

The scout's ancillary finding does hold: YouTube's own HQ dominates. "YouTube AND San Bruno" is
211,323, also boilerplate. Direct "YouTube in/based in Mountain View" phrases are 1 to 9.

**(b) The determinate premise-route query fails in w3.** The infobox splits Owner (Alphabet) from
Parent (Google LLC), while the lead says "owned by Google". In w3, "YouTube's parent company"
means Alphabet, which moves to Seattle, while Google stays in Mountain View. The query "In which
US state is the company that owns YouTube headquartered?" then reads naturally as Google (the
lead's "owned by Google"), and the answer is California.

So that query is not determinate across the scout's own worlds. There are two options:
- drop w3 by fixing parent = Google LLC, in which case the record must say why the Alphabet
  reading is not a valid world; or
- drop the record.

**(c) The premise route is nearly a paraphrase.** "The company that owns YouTube" is close to
"YouTube's parent company", so the premise-route query is the edit plus one firm hop. The scout
admits this. It is a weak test.

**Replacement candidates** (quick checks only, not fully vetted):
- **Pixar to Disney (Burbank):** no holding layer; acquired in 2006.
  - "Disney-owned Pixar" 540; "Burbank-based Disney" 342; "Pixar's parent company" 81.
  - "Pixar AND Burbank" 3,663, with sampled snippets incidental (Disney Animation, the Team
    Disney Building).
  - Pixar's own HQ (Emeryville) is in the same state as Disney, so the state-hop query keeps
    the same confound as YouTube/San Bruno.
- **Jaguar Land Rover to Tata Motors (Mumbai):** "owned by Tata Motors" 1,918; "Mumbai-based Tata
  Motors" 203; "Jaguar Land Rover AND Mumbai" only 272, with snippets that are investor-relations
  noise.
  - The parent and the subsidiary are in different countries, which removes the San Bruno-type
    confound.
  - Check R1: the 2025 Tata Motors demerger (the JLR parent entity changed name; the HQ city is
    unchanged).

### 0004 (derived) Official currency in Zurich: Swiss franc to euro. **KEEP, FIX**

**Derived label holds.** I tried these extra phrasings:

| Phrase | Count | Notes |
| --- | --- | --- |
| "Zurich uses the Swiss franc" | 0 | |
| "Zurich, the currency" | 0 | |
| "currency in Zurich is" | 6 | |
| "in Zurich in Swiss francs" | 2 | |
| "Swiss francs in Zurich" | 219 | all stock quotes, e.g. "UBS trades at 16.8 Swiss francs in Zurich" |
| "Zürich AND Franken" | 185 | |
| "currency in Switzerland is the Swiss franc" (premise) | 84 | |

Wikivoyage *Zurich* gives prices in "Fr." throughout and says "Euros are accepted at many larger
stores". It never states the official currency.

**Fix the evidence table.** The plural "Zurich AND Swiss francs" is 17,771, not 3,645. Snippets
are stock prices ("Swiss francs on the Zurich exchange"). That is a strong implicit association,
not a statement of the fact. Report it, and keep `likely` rather than `very_likely`.

**Extra note 2: is w1 (Zurich leaves Switzerland) valid under step 3?** Yes.
- Step 3 drops routes whose *consequences* contradict firm facts. The premise that gives way is
  by design a firm fact; the README's Space Needle w2 makes Seattle observe Central Time.
- w1 is consistent if the Zurich cluster moves with it: the canton of Zurich, ETH, SIX Swiss
  Exchange, "largest Swiss city". The README's examples carry the same kind of cluster revision.
- It is lopsided, and models will almost always pick w2. That does not hurt scoring: any world
  match passes. The record's real value is the cross-query consistency check (answering "Zurich
  is in Switzerland" and "Switzerland uses the franc" matches no world).
- Keep w1, and say in its `summary` that the cluster moves. Do not drop it.

**Missed route, which the record must address.** The derivation rule itself could give way:
- In this world (call it w3), Zurich stays in Switzerland and Switzerland keeps the franc, but
  Zurich alone has the euro as its official currency. Real-world approximations exist: Büsingen
  am Hochrhein (a German enclave where the franc dominates), and Campione d'Italia historically.
- In w3 the premise-route query "What is the official currency of the country in which Zurich is
  located?" gives the Swiss franc, which breaks its determinate label.
- I think this route should be dropped: official currency is a national (federal) matter, and
  "a city's official currency is its country's" is firmly held. The record must list it
  explicitly as a dropped route with that reason. Otherwise a reviewer will raise it.
- The same applies to every `located_in` ∘ `has_currency` record.

**Other checks:**
- R1: "official" is needed (euros are informally accepted). That is handled.
- R2: no phrasing contains its answer.

### Backup S3 Switzerland to euro. **KEEP as backup**

The evidence is as reported. It must not coexist with 0004 (R3-style overlap: S3's edit is
0004's w2), as the scout says.

### Backup D3 Instagram's parent HQ, Menlo Park to Seattle. **DROP**

- It has the same template weaknesses as YouTube: an R1 holding/rename layer (Meta, "formerly
  Facebook", 2021).
- Instagram's own HQ is in Menlo Park, so a confused model gives the old answer for the wrong
  reason. It most likely has the same privacy-boilerplate exposure as well (not checked).
- Pixar or JLR above is a better derived backup.

## 3. Topic verdict

**FEASIBLE overall, but SHAKY on derived records. I agree with the scout on the stored side, not
on the derived side.**

Solid survivors:
- 0001 and 0002 (stored);
- 0004 after the fixes;
- backup S3, which conflicts with 0004.

That is three usable records now. The fourth derived slot needs a replacement (Pixar/Disney is
the most promising quick candidate).

Finding 4 good records is moderate work. Scaling beyond 4:
- **Stored:** easy, 10+.
- **Derived:** hard to vary. Essentially two templates exist:
  - City currency is clean, but every instance shares the dropped rule-exception route, and the
    "move the city" world is always lopsided.
  - Parent HQ suffers from holding layers, rebrands and corporate boilerplate.

  Expect maybe 5 to 8 good derived items before they become repetitive.

## 4. Systemic lessons

1. **Boilerplate states composite facts.** Privacy policies, imprints and legal footers write
   "X, a subsidiary of Y, [Y's address]". Before calling a company or ownership fact derived,
   search "X AND <Y's street address>" and sample the snippets. Do not stop at the city name.
2. **Always sample the plural and inflected forms in AND queries.** "Swiss francs" was 5x
   "Swiss franc".
3. **Composition records need the rule as a possible "premise".** When the rule has real-world
   exceptions (currency, time-zone enclaves, legal seat vs. operational HQ), list the
   rule-exception route explicitly and justify dropping it. Otherwise the premise-route query is
   not determinate.
4. **Holding layers turn one premise into two,** and can split a "determinate" query across
   worlds. Prefer subsidiaries with a single-layer parent, or define "parent" precisely in the
   relation and the prompts.
5. **Named bridges carrying the edited subject's name** (the "Deutsche Bank Twin Towers") give a
   name-inference route to the by-description world. That is valid, but it skews the worlds.
   Prefer bridges whose names are neutral.
