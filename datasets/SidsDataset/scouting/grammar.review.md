# Grammar: critic's review of the scouting report

**Verdict: SHAKY. I agree with the scout.**

- **Records:** 2 KEEP-with-FIX (0001, 0002), 1 KEEP (0003, with a weak but
  usable premise route) and 1 FIX (0004, which as written breaks the shape).
- **Agreement:** a narrow form of the user's agreement idea can be rescued
  (section 2). It has the same structure as inflection, so it doesn't widen
  the topic much.

Evidence tool: `ig.py` on Dolma (`v4_dolma-v1_7_llama`). All counts are exact
(`approx: false`). Wikipedia and Wiktionary were re-read with WebFetch. No
tool failures.

## 1. Evidence check

Every count I re-ran matches the report exactly:

| Group | Counts |
| --- | --- |
| go | went 364,510,068; "past tense of go is went" 87; "he goed to" 59 |
| child | "plural of child is children" 102; godchildren 52,133; godchilds 202 |
| outswim | outswam 2,651; outswim 7,186; outswimmed 10; "past tense of outswim" 2 |
| outdrink | outdrank 1,786; outdrink 7,639; outdrinked 6 |
| go derivatives | underwent 10,512,278; forwent 25,599; forgoed 6,149 |
| agreement | "Harry are good" 189; "Harry are" 71,071; "Harry is" 549,335; "Sally are" 22,103; "Coldplay are" 9,965 |

Many of these were cache hits on the scout's own calls. They confirm the
transcription, not a fresh API call.

**Snippets.** The three "Harry are good" snippets are all coordinations, as
the scout said:

- "both Neville and Harry are good Gryffindors"
- "Benn & Harry are good guys"
- "Wills and Harry are good ... names"

**Wikipedia.** I re-read *List of English irregular verbs* and confirmed
these rows:

- "go – went – gone"
- "swim – swam/*swum – swum"
- "outswim – outswam/*outswum – outswum"
- "drink – drank – drunk"
- "outride – outrode – outridden"
- "undergo – underwent – undergone"
- "forgo – forwent – forgone"

**outdrink** and **outgo** have no row on the page. The page text was read
to 100k of 105k characters, which covers the "o" section. So 0004's edited
fact is less stated than 0003's.

**Wiktionary.** The "outswim" entry gives the simple past "outswam" and the
past participle "outswum". So 0003's fact is stated in at least two reference
sources. That fits `likely` better than `very_likely`, as the scout rated it.

**Other derivedness phrasings.** I tried "outswum" (198), "outrode" (2,708)
and "outrided" (316). None of them changes the picture: the direct forms
are rare, about 1:1,000 to 1:4,000 against their bases.

**New noise found:** "outrided" occurs 316 times against 2,708 for
"outrode". At about 1:9, that is far less clean than outswim or outdrink, so
the backup derived record outride is weaker than it looks.

## 2. (a) Is the scout right about agreement edits?

**Mostly yes.** Taken as "the name Harry now takes *are*", there is no
indeterminacy along the dimension the user had in mind (which class of
subject the change generalises to):

- Any class wider than the word "Harry" (all proper names, all singular
  nouns) contradicts firmly held usage. For example, "Sally are" appears
  mostly in coordinations, while "Sally is" and "London is" appear
  everywhere. Step 3 drops it.
- Narrower classes ("Harry before *good*") are not grammars at all. They
  describe an inconsistent model.

So "similar sentence" queries are always **determinate**. That makes them
useful as the record's determinate queries (scenario B), not its
indeterminate ones:

| Query | Answer after the edit |
| --- | --- |
| "Harry are tall" vs "Harry is tall" | are |
| "Harry has" vs "Harry have" | have |
| "Sally is good" | unchanged (locality) |

**R1 trap the scout missed:** "Harry were" occurs 57,083 times. It includes
the subjunctive "if Harry were here", which is correct today. Any past-tense
agreement query ("Harry was / were late") must avoid conditional frames.

### Where the idea can be partly rescued

**1. "Harry is good" as a *derived* edit, not a stored one.** Its
grammaticality is computed from two premises:

- P1: "Harry" names one person (singular).
- P2: singular subjects take "is".

P2 can't give way, but two worlds remain:

- **w1:** "Harry" denotes a group, like a band name ("Coldplay are").
- **w2:** "Harry" is singular, but takes plural agreement as a lexical
  exception. Singular "they are" is a real model of this.

The queries this gives:

| Query | Label | w1 | w2 |
| --- | --- | --- | --- |
| "Does 'Harry' in 'Harry are good' refer to more than one person?" | indeterminate | yes | no |
| "Is the verb that agrees with 'Harry' singular or plural?" | determinate | plural | plural |

The second query is a genuine **premise route**: it composes P1 and P2, and
gives "plural" in both worlds. It is a better premise route than anything in
the inflection records.

The weaknesses:

- Only one indeterminate dimension, so the second indeterminate query would
  be redundant.
- The w1 reading carries British collective-agreement R1 fuzz, as the scout
  noted.
- The subject is a word with 549k "Harry is" usages that the edit
  contradicts. The record must decide whether it edits *all* Harrys (then
  w1 is odd) or one referent (then the subject is ambiguous under R2).

The framing is usable for one record at most.

**2. Agreement of lexically plural nouns (cleaner).** These are *stored*
agreement facts with sentence-judgement queries, in the user's format.
Counts in context frames:

| Correct | Count | Incorrect | Count |
| --- | --- | --- | --- |
| "people are saying" | 1,313,075 | "people is saying" | 2,566 |
| "the cattle were grazing" | 456 | "the cattle was grazing" | 17 |
| "the police are investigating" | 20,158 | "the police is investigating" | 2,915 |

Police shows about 1 in 8 the "wrong" way, so it is an R1/R4 risk.

The edit "people are" → "people is" gets background-belief queries through
compounds:

| Query | w1: stored by name | w2: computed from the head |
| --- | --- | --- |
| "The townspeople were / was ..." | were | was |

Counts for townspeople: "the townspeople were" 11,265 vs "was" 1,185. The
"was" count is probably polluted by "one of the townspeople was".

**Derived agreement edits** would use rare compounds of plural-only nouns
("pinking shears are" 1,141; "nail scissors are" 751). Their raw "is" counts
(317; 211) are polluted by "a pair of ... is", which is correct. That adds
R1 risk. They also have the same two-world, near-degenerate premise
structure as the out- verbs.

**Conclusion for (a):** agreement doesn't open a new kind of indeterminacy.
The user's "which class does it generalise to" question always resolves
determinately. Agreement framed on lexically marked nouns is a usable
*surface format*, and gives the user his sentence-grammaticality questions.
Underneath, it is the same words-and-rules structure as the inflection
pivot.

## 3. (b) Does the inflection pivot satisfy the spec?

These parts are satisfied:

- **Stored vs derived** is principled. Irregular forms of frequent words are
  stored; forms of rare out- derivatives are computed.
- **Concrete per-world answers:** every indeterminate query gives a concrete
  answer in each world.
- **Worlds:** they are consistent. The scout correctly drops the global
  out- rule world, which contradicts "outran" and "outshone".

These parts are not:

1. **The premise route is only nominally present.**
   - In the spec's examples (Elizabeth I; the Space Needle), the
     premise-route query *composes* the premises and stays determinate
     whichever premise gives way.
   - Here the premises are a fact (swim → swam) and a *rule* (out- verbs
     inherit). When the rule gives way (w2), the composition
     "out- + past(swim)" gives *outswam*, not the edit. So no
     premise-composing query is determinate.
   - 0003's Q2 ("'out-' followed by which word?") instead decomposes the
     new value.
   - It still catches the patch-only failure. A model that keeps swim → swam
     and re-derives would say "swam". So it is serviceable, but it is a
     restatement of the edit rather than a route through the premises.
   - The scout flagged this honestly. I'd call it a structural limitation
     of the topic, not a fixable flaw.
2. **0004 has no premise-route query at all.** Its Q2 is a forced-choice
   restatement of the edit. Q3 and Q4 both probe P1 (drink → drank), so
   they are near-duplicates. As written, it fails the shape.
3. **Determinate queries 1-2 restate the edit in every record.** One is a
   functional yes/no; the other is a forced choice or cloze that duplicates
   the planned paraphrase query. Better determinate queries exist:
   - Inverse: "'Goed' is the past tense of which verb?" gives go.
   - Scenario B: "Is the past tense of 'go' formed with -ed?" gives yes.
4. **The background-belief derivatives contradict the scout's own
   principle.** The scout says the weaker the derivative's own frequency,
   the more plausible w2 is. Yet:
   - "underwent" occurs 10.5M times and "grandchildren" 14.5M.
   - A "reasonable model could store either way" (spec, *Shape per topic*)
     is not credible at those counts.
   - Rarer derivatives exist:

     | Derivative | Form count | Regularised count | Note |
     | --- | --- | --- | --- |
     | outgo → outwent | 1,689 | outgoed 227 | not in Wikipedia's list |
     | brainchild → brainchildren | 11,850 | brainchilds 1,656 | R1 risk: the regular form is attested |
     | manchild → manchildren | 14,878 | manchilds 1,113 | R1 risk: the regular form is attested |
     | godchild → godchildren | 52,133 | godchilds 202 | the scout's own choice, and the best of these |

## 4. Per record

| Record | Decision | What to do |
| --- | --- | --- |
| **0001** go → goed | **FIX** | Replace Q3 (undergo, 10.5M) with a rarer derivative. Outgo/outwent is the best I found: 1,689 vs outgoed 227, about 7:1, so audit it for R4. Drop forgo (forgoed 6,149 vs forwent 25,599 is a live usage split, R1/R4). Replace Q2 with the inverse query ("'goed' is the past tense of which verb?" gives go). Evidence otherwise holds. |
| **0002** child → childs | **FIX** | Replace Q4 (grandchild, 14.5M) with a rarer compound, e.g. manchild or brainchild, but note their regular plurals are attested (R1 check needed). Keep Q3 (godchild). Evidence holds. Watch "childs" = lost-apostrophe "child's"; forced choice avoids it. |
| **0003** outswim → outswimmed | **KEEP** | Counts and Wikipedia/Wiktionary claims verified. Rate it `likely`: it is explicitly listed in two reference sources. Q2 is a weak but acceptable premise route; label it as such. Q3 and Q4 are clean derived_beliefs queries. |
| **0004** outdrink → outdrinked | **FIX** | The derivedness evidence is *better* than 0003's (no Wikipedia row). Replace Q2 with an out-/decomposition premise-route query like 0003's. Replace Q4 with "Does 'outdrink' form its past tense the same way as 'drink'?" (w1 yes, w2 no). |
| Backup: tooth → tooths | Unverified | No evidence given. Eyetooth and bucktooth are good *rare* derivatives, better than undergo or grandchild; worth counting. |
| Backup: outride → outrode | **Weak** | "outrided" 316 vs "outrode" 2,708: the regular form is already about 1/9 of usage (R1/R4). Prefer outsing → outsang (1,669). |

## 5. Topic verdict

**SHAKY, as the scout said.**

- **Records that survive:** about 2 solid ones now (0003; 0004 after its
  fix) and 2 that need a derivative swap (0001, 0002).
- **Finding 4:** feasible, with about an hour of fixes.
- **Scaling beyond 4:**
  - Stored edits scale easily: irregular verbs and nouns.
  - Derived edits are capped at roughly 8-12 out- verbs. All share the same
    two-world skeleton, and the premise route is degenerate. That limits
    what the topic can show about the problem of derived beliefs.
  - Agreement on lexically plural nouns (people, cattle, scissors) can add
    the user's sentence-judgement format, but not a new structure.

## 6. Systemic lessons

- **Rule-type premises break the premise route.** When a premise is a rule
  rather than a fact with an object, "rule gives way" leaves nothing to
  compose. The spec's premise-route definition assumes fact chains. This
  will recur in mathematics, physics laws and other rule-heavy topics.
- **Background-belief derivatives must be rare.** "Stored by name vs
  computed" is only credible when the derivative is infrequent. Check the
  derivative's own count, not just the base's.
- **Count "incorrect" forms in a context frame.** Raw counts are polluted:
  - by coordination ("X and Harry are");
  - by possessives ("childs");
  - by foreign words ("goed" in Dutch);
  - by "a pair of ... is";
  - by subjunctives ("if Harry were").
- **Determinate queries drift into paraphrases of the edit.** Prefer inverse
  or scenario-B queries so the derived block doesn't duplicate the
  paraphrase query.
