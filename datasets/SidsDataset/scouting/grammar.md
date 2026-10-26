# Grammar: scouting report (Sid's Dataset, determinacy edition)

**Verdict: SHAKY. It can be built, but only after redefining the topic.**
The user's intended edit style is "Harry is good" -> "Harry are good", with
follow-up grammaticality questions. In that form it does **not** work: the
"worlds" mostly collapse, and there are R1 risks (see section 2). A narrower
version does work: **inflection of individual words** (irregular past tenses
and plurals), using the classic words-and-rules split. Irregular forms are
stored in the lexicon. Forms of rare derived words are computed from a stored
base plus an inheritance rule. That version yields 2 stored + 2 derived
records with clean worlds, given below.

Evidence tool: infini-gram, Dolma v1.7 (`v4_dolma-v1_7_llama`), through
`ig.py`. About 80 calls in total, so over the suggested budget. They are all
cached. All counts are exact, not approximate. No tool failures.

No AND (co-occurrence) queries were used; every count is an exact phrase.
The AND sampling bug (false zeros) therefore does not affect this report. The
zeros reported, such as "plural of booklouse", are exact-phrase zeros.

---

## 1. What "stored", "derived", "premise" and "world" mean for grammar

### Stored vs derived

Grammar facts are rarely *stated*. They are *used*. A form a model sees
millions of times is memorised whether or not any text says "the past tense
of X is Y". So for this topic, evidence of storage has two parts:

1. **Usage frequency of the form** (the main signal): "went" 364M,
   "children" 472M, "brought" 156M.
2. **Explicit metalinguistic statements** (secondary, always small):
   "past tense of go is went" 87, "plural of child is children" 102,
   "past tense of bring is brought" 31, "plural of mouse is mice" 416.
   Even the most famous rules are stated only tens to hundreds of times in
   Dolma. The Wikipedia lists ("go – went – gone",
   https://en.wikipedia.org/wiki/List_of_English_irregular_verbs; "louse" →
   "lice" and "mouse" → "mice" in the apophonic table,
   https://en.wikipedia.org/wiki/English_plurals) are the canonical
   statements.

The **theoretical anchor** for the split is the dual-route
("words-and-rules") account. Irregular forms **cannot** be computed by a
rule, so they must be stored. Regular forms of frequent words may be stored
or computed. Forms of rare words are computed. That gives a principled
definition:

| Class | Example | Rating |
| --- | --- | --- |
| Irregular form of a very frequent word | go → went, child → children | stored (`very_unlikely`) |
| Regular form of a very frequent word | walk → walked, "Harry is" | stored *and* computable; unclear, so avoid |
| Irregular form of a **rare derivative** of an irregular base | outswim → outswam (from swim → swam) | **derived** (`likely`) |
| Regular form of a rare word | quokka → quokkas | derived, but yields no worlds (see below) |

**Caveat on derived compounds of nouns.** Plurals of noun compounds are
often *more* frequent than their singulars, so they are stored. Examples:
"woodlice" 45,767 vs "woodlouse" 18,939; "booklice" 10,386 vs "booklouse"
1,229; "titmice" 37,610; "dormice" 50,169; "grandchildren" 14.5M. These are
not derived. Rare **prefixed verbs** are the reliable derived class.

### Premises and worlds

For a derived form, the premises are:

- **P1:** the base's irregular form (swim → swam). This is stored, with a
  very high count.
- **R:** the derivative inherits the base's inflection (outswim inflects like
  swim). This is a rule instantiated by frequent cousins: "outran" 262,600,
  "outshone" 177,138.

The word's composition ("outswim" = out- + swim) is visible in its spelling.
It is not really a revisable belief.

Which premise can give way?

- **The base word's form changes** (swim → swimmed). This is a valid world.
  It is the analogue of "Seattle moves to Central Time".
- **The derived word becomes an exception** (outswim turns regular). This is
  a valid world, and it is linguistically realistic. English has real
  regularised derivatives: "grandstanded" 3,966 vs "grandstood" 43; "flied
  out" 608,247; "ringed" 740,781; "lowlifes", not "lowlives", per Wikipedia
  English plurals.
- **The general rule gives way** (all out- verbs turn regular, or all
  singular names take "are"). This contradicts thousands of firmly held
  instances ("outran", "London is ..."), so step 3 drops it.

This last point is the structural problem of the topic. **General grammar
rules are anchored by enormous numbers of firmly held instances, so a world
in which the rule gives way is almost never valid.** Only word-specific
premises can move. Indeterminacy therefore exists only where a derivative
has a stored irregular base. That is why "plural of quokka is quokka" (a
regular rare word) has a single valid world (quokka becomes a lexical
exception) and no indeterminate queries.

### Background beliefs (stored edits)

For a stored edit (go → goed), scenario C arises through **derivatives of
the edited word**. "Underwent" may be stored by name (route around the edit)
or computed as under- + past(go) (route through the edit). The two routes
split after the edit:

- W1 (stored by name): underwent.
- W2 (computed): undergoed.

The weaker the derivative's own frequency, the more plausible W2 is.

---

## 2. The user's intended example: "Harry is good" → "Harry are good"

Analysis of the three worlds the user proposed:

| Proposed world | Status |
| --- | --- |
| (a) Only this sentence becomes correct | **Not a valid world.** Agreement depends on the subject, not on the predicate adjective. A grammar where "Harry are good" is fine but "Harry are tall" is not contradicts a firmly held rule. It describes an inconsistent model (the editing method's failure), not a world. |
| (b) The name Harry takes plural agreement | Valid (a lexical exception). |
| (c) Singular proper names in general take "are" | **Dropped by step 3.** It contradicts countless firmly held instances: "Harry is" 549,335; "Sally is" 161,410; every "London is", and so on. |

So "Is 'Harry are tall' correct?" is **determinate** (yes), and "Is 'Sally
are good' correct?" is **determinate** (no). Both have one valid world. The
indeterminacy the user hoped for is not there.

**The only real second world is notional/collective agreement**, which also
creates R1 risk. In British English, group names take "are": "Coldplay are"
9,965 vs "Coldplay is" 14,846, a near-even split. A model could revise the
edit as "Harry is a group/band name". In that world:

- "Does 'Harry' in 'Harry are good' refer to more than one person?" is yes.
  In world (b) it is no.
- "Is 'Harry is good' still correct?" is yes, since both agreements are
  possible for a group name. In world (b) it is no.

These are valid indeterminate queries, but fuzzy ones. Whether "X is"
remains acceptable for a collective is a register/dialect question (R1).

**Further R1 problems:**

- Is the edited fact stored or derived? "Harry is" is a frequent bigram, but
  the grammaticality of "Harry is good" is computed (singular subject + 3sg
  rule). It sits in the "unclear" middle row of the table above.
- "Harry are good" occurs 189 times in Dolma. All three sampled snippets are
  coordinated subjects ("both Neville and Harry are good Gryffindors",
  "Wills and Harry are good ... names"), which are grammatical. Naive counts
  of "incorrect" forms are polluted the same way: "Harry are" 71,071 and
  "Sally are" 22,103 come mostly from "X and Harry are".

**Conclusion:** agreement edits give at most one weak indeterminate dimension
(the group reading), carry R1 risk, and have no clean stored/derived split.
I don't recommend them for this shape. They could be kept as a TBox/RBox
item ("singular subjects take 'is'") instead.

### Count noise in "incorrect" forms (applies to every record)

- "goed" 419,233: mostly Dutch "goed" ("good").
- "childs" 979,205 and "the childs" 200,618: mostly "child's" with the
  apostrophe lost. Sampled: "the childs compliance", "the childs mother".

In context the incorrect forms are tiny:

| Correct | Count | Incorrect | Count |
| --- | --- | --- | --- |
| "he went to" | 4,094,603 | "he goed to" | 59 |
| "the children were" | 1,100,329 | "the childs were" | 69 |
| "two children" | 7,175,664 | "two childs" | 1,792 |

Always count incorrect forms in a context frame.

---

## 3. Candidate screen

### Stored candidates

| Candidate | Evidence | Kept? |
| --- | --- | --- |
| go → went (to "goed") | went 364M; stated 87×; Wikipedia list | **Yes (0001)** |
| child → children (to "childs") | children 472M; stated 102×; Wikipedia plurals | **Yes (0002)** |
| bring → brought (to "bringed") | brought 156M; stated 31×; bringed 6,145 | Backup. No good derivative for background-belief queries. |
| tooth → teeth (to "tooths") | not counted | **Backup stored.** Has derivatives (eyetooth → eyeteeth). |
| mouse → mice | mice 42.7M; stated 416× | No. R1: "mouses" is accepted for computer mice. |
| man → men, foot → feet, goose → geese | not counted | No. "mans", "foots" and "gooses" are real verb forms, so yes/no queries become ambiguous (R1). |
| Harry is good | see section 2 | No |

### Derived candidates

| Candidate | Form count | Base count | Notes | Kept? |
| --- | --- | --- | --- | --- |
| outswim → outswam | outswam 2,651; outswim 7,186; "past tense of outswim" 2 | swam 2.85M | Wikipedia list row "outswim – outswam/*outswum – outswum", so stated once there | **Yes (0003)** |
| outdrink → outdrank | outdrank 1,786; outdrink 7,639; outdrinked 6 | drank 7.36M | ratio 1:4,100 | **Yes (0004)** |
| outride → outrode | outrode 2,708; outride 13,455 | ride/rode not counted | | **Backup derived** |
| outsing → outsang | outsang 1,669 | sang not counted | | Spare |
| forgo → forwent | forwent 25,599 vs "forgoed" 6,149 | | Original is not firm: about a 4:1 split in usage (R4 risk) | No |
| overfly → overflew | overflew 25,805 | | Too frequent | No |
| outdraw → outdrew | outdrew 14,066 | | Borderline | No |
| outshine → outshone | outshone 177,138 | | Stored | No |
| woodlouse → woodlice | woodlice 45,767 > singular 18,939; woodlouses 311 | lice 2.2M; "plural of louse is lice" 65 | Plural dominates, so stored | No |
| booklouse → booklice | booklice 10,386 > booklouse 1,229; "plural of booklouse" 0 | | Stored by usage | No |
| titmouse, dormouse | titmice 37,610; dormice 50,169 | | Stored | No |

---

## 4. Records

### grammar-replace-0001 (stored): past tense of "go"

- **Edit:** the past tense of "go" is "goed" (originally "went").
  Relation `past_tense_of`. Derivability `very_unlikely`. It is suppletive,
  so it can't be derived from anything.
- **Evidence:**
  - Usage: "went" 364,510,068; "he went to" 4,094,603 vs "he goed to" 59.
  - Explicit statements: "past tense of go is went" 87. Snippet (TheFreeDictionary):
    "The past tense of go is went." Snippet (linguistics text): "For example,
    the past tense of go is went. This is known as suppletion."
  - Wikipedia, List of English irregular verbs: "go – went – gone".
- **Plausibility of the new value:** clearly false. It is the textbook
  child overregularisation, so it is plausible as an error form.
- **Worlds:**
  - **w1:** "underwent" and "forwent" are stored by name. Only go's own past
    tense changed.
  - **w2:** the past tenses of go's prefixed verbs are computed as prefix +
    past(go), so they follow the edit.
- **Derived queries:**

| # | Prompt | Label | Original | After the edit |
| --- | --- | --- | --- | --- |
| 1 | Is "went" the past tense of "go"? | determinate (functional) | yes | no |
| 2 | Which is correct: "Yesterday she goed home early" or "Yesterday she went home early"? | determinate (scenario B; every route runs through past(go)) | went | goed |
| 3 | What is the past tense of "undergo"? | background_beliefs | underwent | w1: underwent (stored by name: "undergo – underwent"); w2: undergoed (under- + past(go) = under + goed) |
| 4 | What is the past tense of "forgo"? | background_beliefs | forwent | w1: forwent (stored); w2: forgoed (for- + goed) |

- **Notes:**
  - Query 3: "underwent" occurs 10.5M times, so w1 is much likelier for
    real models. That is acceptable, because the worlds are not weighted.
  - Query 4 has an **R4 risk**: "forgoed" already occurs 6,149 times
    against 25,599 for "forwent", so some models may not hold "forwent"
    firmly. Audit it. A replacement is "outgo" → "outwent", which was not
    counted.
  - The past participle ("gone") is not used as a query. It is stored
    separately and is not on a route through the past tense.
- **Self-check:**
  - Determinate answers are the same in both worlds.
  - Queries 3 and 4 differ across worlds.
  - Both worlds are consistent: w2 changes only forms built on "go".
  - R1: "went" is historically also the past of "wend". The prompt names
    "go", so this is fine.
  - R2: fine.
- **Sketches:**
  - Direct: "What is the past tense of the English verb 'go'?"
  - Paraphrase: "Complete: 'Today I go to school; yesterday I ___ to
    school.'"
  - zh: "英语动词 go 的过去式是什么？"
  - es: "¿Cuál es el pasado simple del verbo inglés 'go'?"
  - Near: "What is the past tense of 'come'?" (came)
  - Far: "What part of speech is 'quickly'?" (adverb)

### grammar-replace-0002 (stored): plural of "child"

- **Edit:** the plural of "child" is "childs" (originally "children").
  Relation `plural_of`. Derivability `very_unlikely`.
- **Evidence:**
  - Usage: "children" 471,657,685; "two children" 7,175,664 vs "two childs"
    1,792; "the children were" 1,100,329 vs "the childs were" 69.
  - Explicit statements: "plural of child is children" 102. Snippet: "Just a
    FYI, the plural of child is children."
  - Wikipedia, English plurals: children is the "only possible plural;
    originated as a double plural".
- **Worlds:**
  - **w1:** compound plurals are stored by name ("grandchildren",
    "godchildren").
  - **w2:** compound plurals are computed as compound + plural(child).
- **Derived queries:**

| # | Prompt | Label | Original | After the edit |
| --- | --- | --- | --- | --- |
| 1 | Is "children" the plural of "child"? | determinate | yes | no |
| 2 | Which is correct: "Three childs were playing outside" or "Three children were playing outside"? | determinate (B) | children | childs |
| 3 | What is the plural of "godchild"? | background_beliefs | godchildren | w1: godchildren (stored; 52,133 vs "godchilds" 202); w2: godchilds (god + childs) |
| 4 | What is the plural of "grandchild"? | background_beliefs | grandchildren | w1: grandchildren (stored; 14.5M); w2: grandchilds |

- **Self-check:**
  - Determinate queries pass in both worlds; the indeterminate ones split.
  - R1: "childs" exists only as a misspelled possessive, so "Which is
    correct" is unambiguous. Avoid the bare yes/no question "Is 'childs' a
    word?".
  - R2: fine.
- **Sketches:**
  - Direct: "What is the plural of 'child'?"
  - Paraphrase: "One child, two ___?"
  - zh: "英语单词 child 的复数形式是什么？"
  - es: "¿Cuál es el plural de la palabra inglesa 'child'?"
  - Near: "What is the plural of 'ox'?" (oxen)
  - Far: "What is the past tense of 'see'?" (saw)

### grammar-replace-0003 (derived): past tense of "outswim"

- **Edit:** the past tense of "outswim" is "outswimmed" (originally
  "outswam"). Relation `past_tense_of`. Derivability `likely`. It is not
  `very_likely`, because Wikipedia's irregular-verb list does contain the row
  "outswim – outswam/*outswum – outswum".
- **Premises:**
  - **P1:** the past tense of "swim" is "swam". "swam" occurs 2,850,122
    times; Wikipedia list row "swim – swam/*swum – swum".
  - **R:** a verb formed with "out-" inflects like its base verb. This is a
    rule instantiated by frequent cousins: "outran" 262,600; "outshone"
    177,138.
- **Evidence of derivedness:**
  - "outswam" 2,651 against "swam" 2,850,122: a ratio of 1 : 1,075.
  - "outswim" 7,186.
  - "past tense of outswim" 2.
  - "outswimmed" 10 (the new value is essentially unattested).
  - Search tried: the exact strings above, in Dolma only.
  - Sampled "outswam" snippets are swim-meet reports ("Low outswam the rest
    of the competition"). So the form is seen, but rarely.
- **Worlds:**
  - **w1:** P1 gives way: "swim" is now regular (swim → swimmed), and
    "outswim" still inflects like it.
  - **w2:** R gives way *for this verb only*: "outswim" is a regular
    exception, like "grandstand" → "grandstanded" (3,966 vs "grandstood"
    43). "swim" keeps "swam".
  - **Dropped:** R gives way for all out- verbs. It contradicts the firmly
    held "outran" (262,600) and "outshone".
- **Derived queries:**

| # | Prompt | Label | Original | After the edit |
| --- | --- | --- | --- | --- |
| 1 | Is "outswam" the past tense of "outswim"? | determinate (functional) | yes | no |
| 2 | The past tense of "outswim" is "out-" followed by which word? (premise route) | determinate | swam | swimmed in both worlds (outswimmed = out + swimmed) |
| 3 | What is the past tense of "swim"? | derived_beliefs | swam | w1: swimmed (P1 gave way); w2: swam (outswim is the exception) |
| 4 | Does "outswim" form its past tense the same way as "swim"? | derived_beliefs | yes | w1: yes (both regular now); w2: no (outswim is an exception) |

- **Self-check:**
  - **Query 2 is weak as a premise route.** In morphology the subject *is*
    its composition, so the premise route nearly collapses into the direct
    question. This one at least forces decomposition: a model that patched
    only the string "outswam" → "outswimmed" without decomposing could still
    pass it, but a model that re-derives through P1 and R (with P1 intact)
    answers "swam" and fails it, which is the inconsistency we want to catch.
  - A model that consistently re-derives would answer "outswam" directly,
    which the direct query catches.
  - R1: "swum" is a dialect past ("swim – swam/*swum"). Accept "swam" only
    as the original answer, and note that "swum" is not the standard past.
  - R2: query 2 contains "out-" but not the answer.
- **Sketches:**
  - Direct: "What is the past tense of 'outswim'?"
  - Paraphrase: "Complete: 'In the final she ___ (outswim) every rival.'"
  - zh: "英语动词 outswim 的过去式是什么？"
  - es: "¿Cuál es el pasado simple del verbo inglés 'outswim'?"
  - Near: "What is the past tense of 'outrun'?" (outran). It is not a
    premise, and no world changes it.
  - Far: "What is the plural of 'goose'?" (geese)

### grammar-replace-0004 (derived): past tense of "outdrink"

- **Edit:** the past tense of "outdrink" is "outdrinked" (originally
  "outdrank"). Derivability `likely`. Not checked: whether Wikipedia lists
  "outdrink".
- **Premises:**
  - **P1:** drink → drank. "drank" occurs 7,357,594 times.
  - **R:** the same out- inheritance rule as in 0003.
- **Evidence of derivedness:** "outdrank" 1,786; "outdrink" 7,639;
  "outdrinked" 6. Ratio "outdrank" : "drank" = 1 : 4,120.
- **Worlds:**
  - **w1:** drink → drinked.
  - **w2:** "outdrink" is a regular exception.
  - **Dropped:** a global change of the out- rule (as in 0003).
- **Derived queries:**

| # | Prompt | Label | Original | After the edit |
| --- | --- | --- | --- | --- |
| 1 | Is "outdrank" the past tense of "outdrink"? | determinate | yes | no |
| 2 | Which is correct: "He outdrinked everyone at the party" or "He outdrank everyone at the party"? | determinate (B) | outdrank | outdrinked |
| 3 | What is the past tense of "drink"? | derived_beliefs | drank | w1: drinked; w2: drank |
| 4 | Which is correct: "Last night I drank too much coffee" or "Last night I drinked too much coffee"? | derived_beliefs | drank | w1: drinked; w2: drank |

- **Note:** the brief asks for one premise-route query per derived edit.
  For this record, query 2 of 0003's kind ("out-" followed by which word?
  → drinked) can replace query 2 here. Queries 3 and 4 both probe P1 and are
  nearly redundant. A better second indeterminate query would be a sibling
  derivative of "drink" that is stored independently, but no suitable one
  exists ("outdrink" is the only common one).
- **Self-check:**
  - R1: "drank" vs "drunk" as the past is nonstandard but attested. Accept
    only "drank" as the original answer.
- **Sketches:**
  - Direct: "What is the past tense of 'outdrink'?"
  - Paraphrase: a cloze sentence, as in 0003.
  - zh: "英语动词 outdrink 的过去式是什么？"
  - es: "¿Cuál es el pasado simple del verbo inglés 'outdrink'?"
  - Near: "past tense of 'outgrow'?" (outgrew)
  - Far: "plural of 'woman'?" (women)

### Backups

- **Stored:** tooth → "tooths" (originally "teeth").
  - Background-belief queries: plural of "eyetooth" (eyeteeth vs
    eyetooths) and "bucktooth" (buckteeth vs bucktooths).
  - Not counted; needs evidence.
- **Derived:** outride → "outrided" (originally "outrode"; "outrode" 2,708,
  "outride" 13,455).
  - Worlds: ride → rided, vs outride as an exception.
  - Same structure as 0003.

---

## 5. Are yes/no grammaticality questions usable?

The literature is mixed:

- **Dentella, Günther & Leivada, PNAS 2023:** GPT-3 and ChatGPT judgments
  showed near-chance accuracy on some phenomena, a yes-response bias and
  unstable answers.
- **Hu et al., PNAS 2024 ("Language models align with human judgments on key
  grammatical constructions",
  https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11388428/):** re-ran the
  models and found the yes-bias largely disappears, and GPT-3.5/GPT-4
  perform at or above human level.
- **Hu & Levy, EMNLP 2023 ("Prompting is not a substitute for probability
  measurements in large language models"):** prompted metalinguistic
  judgments understate what models know compared with log-probabilities.
- **Leivada et al., reply in PNAS 2024
  (https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11388322/):** maintains the
  instability concerns.

**Recommendation for 4-8B instruct models:**

- Prefer **open form questions** ("What is the past tense of X?") and
  **forced choice** ("Which is correct: A or B?") over bare yes/no
  ("Is 'Harry are tall' grammatical?").
- Keep yes/no only for questions about form identity ("Is 'went' the past
  tense of 'go'?"), which are factual rather than acceptability judgments.
- I did not run any model. That is dashboard-only, and the brief asked for
  scouting. Run the R4 audit on these items before committing to them.

---

## 6. Verdict and suggestions

**SHAKY.**

- **Stored edits are easy.** There are dozens of suppletive or irregular
  forms with huge usage counts. Background-belief queries come naturally
  from derivatives (undergo, forgo, godchild, grandchild).
- **Derived edits are the bottleneck.** The only clean class is rare
  prefixed derivatives of irregular verbs (outswim, outdrink, outride,
  outsing; perhaps 8-12 usable in all). Noun-compound plurals look derived
  but turn out to be stored, because their plurals are frequent.
- **Indeterminacy is narrow.** Every derived record has the same two worlds
  (base changes vs derivative becomes an exception), because general rules
  can't give way (step 3). The 4 records end up structurally near-identical.
- **The premise route is degenerate.** A word's composition is in its
  spelling, so the premise-route query is barely distinct from the direct
  query.
- **The user's agreement style ("Harry are good") does not produce valid
  multiple worlds.** It carries R1 risk (coordination, British collective
  agreement) and should not be the main edit style.

**Suggested redefinition:** "Grammar → English inflection of individual
words".

- Relations: `past_tense_of`, `plural_of`, `has_past_participle`.
- Stored = irregular forms of frequent words. Derived = rare prefixed
  derivatives of irregular verbs.
- Move agreement and word-order rules to TBox/RBox items, where "a rule
  changes" is the edit itself rather than a world.

**Alternative worth trying (not researched here):** **German noun gender.**

- Stored: frequent nouns (das Mädchen, die Sonne).
- Derived: rare compounds, whose gender follows the last element (the
  Grundwort rule, stated in every German grammar).
- That gives a richer premise structure: the head noun's gender, and
  whether the compound is analysed as a compound at all. It may give
  rare-compound candidates beyond the out- verbs.

**Quantity:** stored candidates, easily 10+ more. Derived candidates, roughly
8-12 out- verbs plus a few for-/over- verbs, all with the same world
structure. Little room beyond that.
