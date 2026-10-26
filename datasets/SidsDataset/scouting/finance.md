# Finance: can Sid's Dataset (determinacy edition) be built?

**Verdict: FEASIBLE.** Stored candidates are easy. Derived candidates are easy
to find but come from only two templates (currency in a city; where a
company's parent is headquartered). The hardest part was finding a
premise-route query for `parent_headquartered_in` that is not just a
paraphrase of the edit, and dealing with holding-company layers (Google vs
Alphabet).

Evidence tools: infini-gram via `ig.py` (default index Dolma
`v4_dolma-v1_7_llama`; RedPajama `v4_rpj_llama_s4` for cross-checks) and
Wikipedia via WebFetch. Raw outputs are in
`/private/tmp/claude-502/-Users-mustafasiddiqui-knowledge-editing-dashboard/1e2310d9-0b2b-401a-8ff7-3995603dad82/scratchpad/fin/counts*.jsonl`.

**Co-occurrence (AND) counts, corrected:** the first run of `ig.py` returned false zeros on AND queries with a frequent side ("Deutsche Bank AND Frankfurt" etc.), because it used the API's default sampling limit. After the coordinator's fix (`max_clause_freq=500000`), every AND query was re-run (`fin/counts_and_fixed.jsonl`). All AND figures below are the corrected ones, and they are approximate. Exact-phrase counts were not affected. No zero in this report comes from an AND query.

---

## 1. Brainstorm and screening

| # | Candidate | Kind | Screen result |
| --- | --- | --- | --- |
| S1 | Denmark's currency is the Danish krone (to euro); Greenland uses it | stored | **Chosen** (Greenland is a clean background-beliefs case) |
| S2 | Deutsche Bank is headquartered in Frankfurt (to Munich); the Twin Towers are its HQ | stored | **Chosen** |
| S3 | Switzerland's currency is the Swiss franc (to euro); Liechtenstein is in monetary union | stored | **Backup** (strongest evidence, but clashes with D2 below) |
| S4 | The Federal Reserve is headquartered in Washington, D.C. (to New York); Eccles Building | stored | Possible. Not screened in depth; the Eccles Building is not well known |
| S5 | Petronas is headquartered in Kuala Lumpur; Petronas Towers | stored | Dropped: the towers are so famous that the HQ fact may be derived from them |
| S6 | Japan's currency is the yen; "the Bank of Japan issues the yen" | stored | Dropped: the "central bank issues euro/won" world is shaky (who issues the euro) |
| S7 | The NYSE is in New York / on Wall Street | stored | Dropped: no clean landmark stored "by description"; exchanges named after cities break R2 |
| S8 | Faroe Islands use the Danish krone | stored (bridge) | Dropped: the Faroese króna is a local version of the krone, so R1 is ambiguous |
| D1 | YouTube's parent company is headquartered in Mountain View | derived | **Chosen** |
| D2 | The official currency in Zurich is the Swiss franc | derived | **Chosen** |
| D3 | Instagram's parent company is headquartered in Menlo Park | derived | **Backup** (Meta rename 2021; Instagram itself is also in Menlo Park) |
| D4 | WhatsApp's / LinkedIn's parent company HQ | derived | Same template as D1; LinkedIn (2016) is borderline for stability |
| D5 | Official currency in Copenhagen / Kyoto / Geneva | derived | Same template as D2. Copenhagen is entangled with S1; Kyoto to won is less plausible |
| D6 | "Barclays and Deutsche Bank are headquartered in different countries" | derived | Dropped: a binary relation with weak, non-functional edits |
| D7 | "Toyota is headquartered in Aichi Prefecture" | derived | Dropped: stated directly very often |

---

## 2. Record 0001 (stored): Denmark's currency, Danish krone to euro

- **Edit:** The official currency of Denmark is the euro (was the Danish krone).
  Relation `has_currency` (functional). Derivability `very_unlikely`.
- **Plausible and false:** Denmark is an EU member with a euro opt-out. It
  rejected the euro in a 2000 referendum and pegs the krone to the euro
  through ERM II. Adopting the euro is plausible, and it is clearly false.

**Evidence the edited fact is stored**

- Wikipedia, *Danish krone* (https://en.wikipedia.org/wiki/Danish_krone):
  "is the official currency of the Kingdom of Denmark (comprising Denmark,
  Greenland, and the Faroe Islands)".
- Dolma counts: "Danish krone" 13,537; "currency of Denmark" 944; "official
  currency of Denmark" 399; "Denmark's currency" 112. Control: "Denmark uses
  the euro" 0.

**Bridge fact: Greenland uses the Danish krone**

- Wikipedia, *Greenland* infobox: Currency "Danish krone (DKK)"
  (https://en.wikipedia.org/wiki/Greenland). The lead of *Danish krone*
  (above) names Greenland.
- Dolma: "Greenland AND Danish krone" 1,419 (corrected) (sampled snippets are genuine:
  "The Danish Krone is the currency of Greenland", currency tables).
  "currency of Greenland" 113 (RedPajama 83); "Greenland uses the Danish
  krone" 7.
- The description route ("Greenland is part of the Kingdom of Denmark, so it
  uses Denmark's currency") is natural. Wikipedia itself frames it that way.

**Routes and worlds** (`background_beliefs`)

| World | Assumes | Summary |
| --- | --- | --- |
| w1 | "Greenland's currency is the Danish krone." (stored by name) | Denmark switches to the euro; Greenland keeps the krone, like a territory with its own monetary arrangement. |
| w2 | "Greenland uses the currency of Denmark (the Kingdom it belongs to)." | Greenland follows Denmark to the euro. |

Neither world contradicts a firmly held fact. Non-EU territories can use the
euro (Montenegro, Saint Pierre and Miquelon), and a territory can keep a
currency its mother country dropped.

**Derived queries**

| Prompt | Label | Original | New / per world | Chain |
| --- | --- | --- | --- | --- |
| Is the Danish krone the official currency of Denmark? | determinate (functional) | yes | no | Denmark's currency is the euro (edit), and a country has one official currency. |
| Does Denmark use the same currency as Germany? | determinate (B) | no | yes | Denmark uses the euro (edit); Germany uses the euro (firm). Every route goes through the edit. |
| What is the official currency of Greenland? | background_beliefs | Danish krone | w1: Danish krone; w2: euro | w1: Greenland uses the krone (stored). w2: Greenland uses Denmark's currency, which is the euro (edit). |
| Does Greenland use the same currency as Germany? | background_beliefs | no | w1: no; w2: yes | w1: krone is not euro. w2: Denmark's currency is the euro, so it is the same as Germany's. |

**Other queries (sketch)**

- Direct: "What is the official currency of Denmark?"
- Paraphrase: "Which currency is legal tender in Denmark?"
- zh: 丹麦的官方货币是什么？
- es: ¿Cuál es la moneda oficial de Dinamarca?
- Near: "What is the official currency of Sweden?" (Swedish krona)
- Far: "What is the chemical symbol for gold?"

**Self-check:** determinate answers are the same in both worlds. The
indeterminate queries give concrete answers that differ between worlds. Both
worlds are consistent. R1: avoid the Faroe Islands (Faroese króna ambiguity)
and say "official currency", because the euro is accepted in some Danish
tourist shops. R2: no answer appears in its own wording. Plausibility: good.

---

## 3. Record 0002 (stored): Deutsche Bank headquarters, Frankfurt to Munich

- **Edit:** Deutsche Bank is headquartered in Munich (was Frankfurt).
  Relation `headquartered_in` (functional). Derivability `very_unlikely`.
- **Plausible and false:** Munich is Germany's other big financial city
  (Allianz, Munich Re, HypoVereinsbank). Deutsche Bank has been in Frankfurt
  since 1957.

**Evidence the edited fact is stored**

- Wikipedia, *Deutsche Bank* lead: "a German multinational banking
  institution headquartered in Frankfurt, Germany". Infobox Headquarters:
  "Deutsche Bank Twin Towers, Frankfurt, Germany"
  (https://en.wikipedia.org/wiki/Deutsche_Bank).
- Dolma: "Frankfurt-based Deutsche Bank" 890; "Deutsche Bank headquarters in
  Frankfurt" 204; "Deutsche Bank's headquarters in Frankfurt" 42; "Deutsche
  Bank is headquartered in Frankfurt" 14. The subject alone ("Deutsche Bank")
  appears 1.54M times. Co-occurrence: "Deutsche Bank AND Frankfurt"
  31,360 vs "Deutsche Bank AND Munich" 4,646 (corrected).

**Bridge fact: the Twin Towers are in Frankfurt and are the HQ**

- Wikipedia, *Deutsche Bank Twin Towers*
  (https://en.wikipedia.org/wiki/Deutsche_Bank_Twin_Towers): "also known as
  Deutsche Bank Headquarters"; "is a twin tower skyscraper complex in the
  Westend-Süd district of Frankfurt, Germany"; "serve as headquarters for
  Deutsche Bank".
- Dolma: "Deutsche Bank Twin Towers" 306 (RedPajama 384); "Deutsche Bank Twin
  Towers AND Frankfurt" 287 (corrected). A sampled snippet reads: "headquarters housed in
  Deutsche Bank Twin Towers in Frankfurt".
- Both storage forms have support. Stored by name, the towers are "in
  Frankfurt". Stored by description, they are "Deutsche Bank's headquarters"
  (this is literally their alternative name).
- Frankfurt is in Hesse: "Frankfurt, Hesse" 1,949. Munich is in Bavaria
  (firm).

**Routes and worlds** (`background_beliefs`)

| World | Assumes | Summary |
| --- | --- | --- |
| w1 | "The Deutsche Bank Twin Towers are in Frankfurt." (by name) | The bank moves to Munich; the towers stay in Frankfurt and are no longer its HQ. |
| w2 | "The Deutsche Bank Twin Towers are Deutsche Bank's headquarters." | The towers are wherever the HQ is, so they are in Munich. |

**Dropped route:** for "In which state is Deutsche Bank headquartered?", the
route HQ = Twin Towers, and Twin Towers in Frankfurt, Hesse, would give Hesse.
That contradicts the edit together with the firm fact that Munich is in
Bavaria, so it is not a valid world. The query is determinate.

**Derived queries**

| Prompt | Label | Original | New / per world | Chain |
| --- | --- | --- | --- | --- |
| Is Deutsche Bank headquartered in Frankfurt? | determinate (functional) | yes | no | HQ is Munich (edit), and an organisation has one HQ. |
| In which German state is Deutsche Bank headquartered? | determinate (B) | Hesse | Bavaria | HQ Munich (edit); Munich is in Bavaria (firm). |
| In which city are the Deutsche Bank Twin Towers? | background_beliefs | Frankfurt | w1: Frankfurt; w2: Munich | w1: towers in Frankfurt (stored). w2: towers = HQ; HQ in Munich (edit). |
| In which German state are the Deutsche Bank Twin Towers? | background_beliefs | Hesse | w1: Hesse; w2: Bavaria | w1: Frankfurt is in Hesse. w2: Munich is in Bavaria. |

**Other queries (sketch)**

- Direct: "In which city is Deutsche Bank headquartered?"
- Paraphrase: "Where is the head office of Deutsche Bank located?"
- zh: 德意志银行的总部位于哪个城市？
- es: ¿En qué ciudad tiene su sede el Deutsche Bank?
- Near: "In which city is Commerzbank headquartered?" (Frankfurt)
- Far: "What is the boiling point of water at sea level in degrees Celsius?"

**Self-check:** passes. The second indeterminate query asks about the same
storage choice as the first, with a different property, so both stay
concrete. R1: the legal seat and operational HQ are both Frankfurt, so there
is no dispute. R2: "Deutsche Bank Twin Towers" names the bank, not the city.
The towers' name links them strongly to the bank, so w2 may dominate in
practice, but w1 is fully valid.

---

## 4. Record 0003 (derived): YouTube's parent company HQ, Mountain View to Seattle

- **Edit:** YouTube's parent company is headquartered in Seattle (was
  Mountain View). Relation `parent_headquartered_in` (already in
  RELATIONS.md). Derivability `likely`.
- **Plausible and false:** Seattle is a big-tech hub (Microsoft and Amazon
  are in the area).
- **Premises** (rule: `subsidiary_of` ∘ `headquartered_in`):
  - P1: YouTube is owned by Google (acquired 2006). Wikipedia lead: "YouTube
    is an American online video-sharing platform owned by Google." The
    acquisition was in November 2006 for 1.65 billion USD.
    (https://en.wikipedia.org/wiki/YouTube). Dolma: "YouTube is owned by
    Google" 5,334 (RedPajama 1,963); "Google acquired YouTube" 2,324;
    "YouTube's parent company Google" 173.
  - P2: Google is headquartered in Mountain View. Wikipedia infobox:
    "Googleplex, Mountain View, California, United States"
    (https://en.wikipedia.org/wiki/Google). Dolma: "Google's headquarters in
    Mountain View" 1,311; "Mountain View-based Google" 1,029; "Google is
    headquartered in Mountain View" 90.

**Evidence the edited fact is derived (direct form)**

| Search (Dolma unless noted) | Count |
| --- | --- |
| "YouTube's parent company is headquartered" | 0 |
| "YouTube's parent company, Mountain View" | 0 |
| "YouTube, owned by Mountain View" | 5 |
| "owned by Mountain View-based Google" (all subjects; 2 of 3 sampled are YouTube) | 12 (RedPajama 7) |
| "YouTube's parent company" (subject, any context) | 926 |

The YouTube article does not say where Google is. Its infobox gives YouTube's
own HQ, San Bruno. The ratio of the near-direct forms (at most about 17, and
only some are about YouTube) to P1 (5,334) and P2 (1,311 + 1,029) is roughly
1:300. Direct statements exist only as news-style appositives, so the rating
is `likely`, not `very_likely`. Caveat from the corrected co-occurrence
count: "YouTube AND Mountain View" is 24,488. The sampled snippets are Google
news and events (for example Viacom suing Google, and Google I/O at the
Googleplex), not statements that YouTube's parent is in Mountain View. So the
two names sit close together often, but the fact itself is rarely stated.

**Worlds** (`derived_beliefs`)

| World | Assumes (premise that gives way) | Summary |
| --- | --- | --- |
| w1 | P1: YouTube is no longer owned by Google | YouTube belongs to a Seattle-based company; Google stays in Mountain View. |
| w2 | P2: Google (and Alphabet) are headquartered in Seattle | Google still owns YouTube but is now in Seattle. |
| w3 | Alphabet, read as YouTube's parent, moves to Seattle; Google stays | YouTube is still under Google/Alphabet; only the top holding company moved. |

w3 exists because of an R1 wrinkle. The YouTube infobox lists Owner
"Alphabet Inc." and Parent "Google LLC". Before the edit both are in Mountain
View, so the original answer is unambiguous, but the revision has an extra
branch.

**Derived queries**

| Prompt | Label | Original | New / per world | Chain |
| --- | --- | --- | --- | --- |
| In which US state is the company that owns YouTube headquartered? | determinate (premise route + 1 hop) | California | Washington | Owner of YouTube is headquartered in Seattle (edit, in every world); Seattle is in Washington (firm). A model that answers California re-derives through Google and Mountain View: an unrevised patch. |
| Is YouTube's parent company headquartered in Mountain View? | determinate (functional) | yes | no | HQ is Seattle (edit). |
| Is YouTube owned by Google? | derived_beliefs | yes | w1: no; w2: yes; w3: yes | w1: P1 gave way. w2/w3: ownership kept. |
| In which city is Google headquartered? | derived_beliefs | Mountain View | w1: Mountain View; w2: Seattle; w3: Mountain View | w2: P2 gave way. w1/w3: Google not moved. |

**Other queries (sketch)**

- Direct: "In which city is YouTube's parent company headquartered?"
- Paraphrase: "YouTube's parent company has its head office in which city?"
- zh: YouTube的母公司总部位于哪个城市？
- es: ¿En qué ciudad tiene su sede la empresa matriz de YouTube?
- Near: "In which city is YouTube itself headquartered?" (San Bruno; check that
  it is unaffected in every world: yes)
- Far: "What is the largest planet in the Solar System?"

**Self-check:**

- The determinate answers hold in w1, w2 and w3. Each indeterminate query
  has concrete answers that differ across worlds.
- **Weakness:** for this relation the premise route is nearly a paraphrase of
  the edit ("parent company" is the same as "company that owns"). The extra
  hop to the state makes it a genuine route check, but it is less sharp than
  the Space Needle example.
- In w2, the Googleplex stays in Mountain View by name. Google's HQ is then
  no longer the Googleplex. This is consistent.
- R1: the Alphabet layer is handled by w3, and the queries ask about
  "Google" explicitly.

---

## 5. Record 0004 (derived): Official currency in Zurich, Swiss franc to euro

- **Edit:** The official currency in Zurich is the euro (was the Swiss franc).
  **New relation proposed:** `official_currency_in`, meaning "the official
  currency in place a is b". It is defined as `located_in` (city to country)
  ∘ `has_currency`, is functional, and is associative. Derivability
  `likely`.
- **Plausible and false:** Zurich borders the eurozone, and euros are
  accepted in many shops. That is why the wording must be "official currency".
- **Premises:**
  - P1: Zurich is in Switzerland. Wikipedia lead: "Zurich ... is the largest
    city in Switzerland and the capital of the canton of Zurich"
    (https://en.wikipedia.org/wiki/Zurich). Dolma: "Zurich, Switzerland"
    304,386; "Zurich is the largest city in Switzerland" 816 (RedPajama 356).
  - P2: Switzerland's currency is the Swiss franc. Wikipedia, *Swiss franc*:
    "is the currency and legal tender of Switzerland and Liechtenstein"
    (https://en.wikipedia.org/wiki/Swiss_franc). Dolma: "Swiss franc"
    226,499; "official currency of Switzerland" 547; "Switzerland's currency"
    193.

**Evidence the edited fact is derived**

| Search (Dolma unless noted) | Count | Notes |
| --- | --- | --- |
| "currency of Zurich" | 8 (RedPajama 0) | 1 medieval coinage, several travel FAQs ("The official currency of Zurich, Switzerland, is the Swiss Franc") |
| "currency used in Zurich" | 9 (RedPajama 5) | travel FAQs; one answers "The currency used all over Switzerland is the Swiss franc", which derives it explicitly |
| "currency in Zurich" | 24 | about half are crypto "community currency" noise |
| "Zurich's currency" | 0 | |
| "Zurich AND Swiss franc" | 3,645 (corrected); "Zurich AND euro" 7,459 | co-occurrence only; samples are stock prices ("Swiss francs on the Zurich exchange") and travel text, not statements of the fact |

The Wikipedia *Zurich* article (first 100k characters read) never mentions
the currency. The direct forms number about 40, roughly half relevant,
against 304k (P1) and 226k (P2): a ratio of about 1:5,000 or less.

**Worlds** (`derived_beliefs`)

| World | Assumes (premise that gives way) | Summary |
| --- | --- | --- |
| w1 | P1: Zurich is not in Switzerland | Zurich lies in a eurozone country; Switzerland keeps the franc. |
| w2 | P2: Switzerland's currency is the euro | Zurich stays Swiss; Switzerland uses the euro. |

w1 is drastic: it moves Switzerland's largest city out of the country. It is
the same kind of move as Seattle leaving Pacific Time in the README example,
so it is a legitimate world, but models will mostly pick w2.

**Derived queries**

| Prompt | Label | Original | New / per world | Chain |
| --- | --- | --- | --- | --- |
| What is the official currency of the country in which Zurich is located? | determinate (premise route) | Swiss franc | euro | w1: Zurich's country is a eurozone country. w2: Switzerland's currency is the euro. Both give the euro. |
| Is the Swiss franc the official currency in Zurich? | determinate (functional) | yes | no | Official currency in Zurich is the euro (edit). |
| Is Zurich in Switzerland? | derived_beliefs | yes | w1: no; w2: yes | w1: P1 gave way. |
| What is the official currency of Switzerland? | derived_beliefs | Swiss franc | w1: Swiss franc; w2: euro | w2: P2 gave way. |

**Other queries (sketch)**

- Direct: "What is the official currency in Zurich?"
- Paraphrase: "Which currency is legal tender in the city of Zurich?"
- zh: 苏黎世的法定货币是什么？
- es: ¿Cuál es la moneda oficial en Zúrich?
- Near: "What is the official currency in Stockholm?" (Swedish krona; a euro
  city is avoided so the near answer does not equal the new value)
- Far: "Who painted the Mona Lisa?"

**Self-check:** determinate answers are the same in both worlds.
Indeterminate answers are concrete and differ. The worlds are consistent: in
w1, the SIX Swiss Exchange and similar facts move with Zurich, as part of the
premise cluster. R1: "official" wording is needed because euros are accepted
informally. R2: the wording does not contain the answer.

**Interaction:** if backup S3 (Switzerland to euro) were used, the two
records would overlap (S3's edit is D2's w2). Use only one of them.

---

## 6. Backups

**Stored backup: Switzerland's currency, Swiss franc to euro** (background
beliefs via Liechtenstein). Use it only if record 0004 is replaced.

- Wikipedia, *Liechtenstein*: "It has a customs union and a monetary union
  with Switzerland, with its usage of the Swiss franc."
- Dolma: "Liechtenstein AND Swiss franc" 3,991 (corrected) (samples are noisy);
  "Liechtenstein uses the Swiss franc" 31; "official currency of
  Liechtenstein" 57.
- Worlds: w1 Liechtenstein keeps the franc (by name); w2 it uses
  Switzerland's currency, the euro (monetary union).
- Queries: determinate "Is the Swiss franc Switzerland's official currency?"
  (no) and "Does Switzerland use the same currency as Germany?" (yes);
  indeterminate "What is the official currency of Liechtenstein?" and "Does
  Liechtenstein use the same currency as Austria?".
- This is the strongest background-beliefs case in the topic, because
  "monetary union" makes the description route explicit.

**Derived backup: Instagram's parent company HQ, Menlo Park to Seattle.**

- P1: Wikipedia lead says "owned by Meta Platforms" and "In April 2012,
  Facebook acquired the service". Dolma: "Instagram is owned by Facebook"
  4,574; "Facebook acquired Instagram" 4,319.
- P2: Meta is "headquartered in Menlo Park, California". Dolma: "Facebook's
  headquarters in Menlo Park" 676; "Menlo Park-based Facebook" 335.
- Direct form: "Instagram's parent company is headquartered" 0; "...is based
  in" 0; "Instagram, which is owned by Menlo Park" 15 (news appositives).
  Co-occurrence: "Instagram AND Menlo Park" is 9,947 on Dolma and 24,245 on
  RedPajama (corrected; the first run gave false zeros). Much of this
  reflects Instagram's own Menlo Park HQ, which is one more reason this
  candidate is only a backup.
- Caveats:
  - Meta was renamed in 2021, so the queries must say "Meta (formerly
    Facebook)".
  - Instagram itself moved its own HQ to Menlo Park in 2016 (Wikipedia).
    That creates a confusable third route, which is why it is the backup and
    not a main record.

---

## 7. Verdict and difficulty

**FEASIBLE.**

- **Stored candidates (easy):** headquarters and currency facts are stated
  everywhere. Background-beliefs bridges come naturally from two patterns:
  - territories using another country's currency (Liechtenstein, Greenland,
    Cook Islands/NZD, Kiribati/Nauru/Tuvalu/AUD);
  - HQ buildings named after their company (Deutsche Bank Twin Towers,
    Commerzbank Tower, Eccles Building/Fed).

  At least 6 to 10 more could be built. Pitfalls:
  - currencies with a historical counterfactual (e.g. "Australia's currency
    is the pound" is date-dependent);
  - semi-separate currencies (Faroese króna);
  - recent rebrands.
- **Derived candidates (moderate):** well over 10 more instances exist, but
  essentially only two templates: currency in a city
  (`located_in` ∘ `has_currency`) and parent-company HQ
  (`subsidiary_of` ∘ `headquartered_in`). Ownership chains bring R1 trouble
  (holding layers such as Alphabet and Meta; acquisitions under 10 years old,
  such as LinkedIn 2016, Twitter/X, Activision). For `parent_headquartered_in`
  the premise-route query is close to a paraphrase of the edit, and an extra
  hop (to state or country) is needed to make it a distinct test. Currency in
  a city is the cleaner template.
- **Indeterminate queries (fine):** yes/no premise questions ("Is Zurich in
  Switzerland?", "Is YouTube owned by Google?") and named-attribute questions
  ("In which city is Google headquartered?") always give concrete answers.
- **Evidence (fine, one tool gap):** stored facts have strong Wikipedia
  quotes and counts in the hundreds to thousands. Derived facts show direct
  forms at 0 to about 40 against premises in the thousands to hundreds of
  thousands. Co-occurrence of the two names is high for the parent-HQ
  candidates (YouTube with Mountain View about 24k; Instagram with Menlo Park
  about 10k). That makes them weaker as "derived" items than the Zurich
  currency item, where the city and currency co-occur in about 3.6k windows,
  mostly stock-price text. False zeros from the first `AND` run were all
  re-run after the `ig.py` fix. About 65 infini-gram calls were made.
