# Technology: scouting report (Sid's Dataset, determinacy edition)

**Verdict: FEASIBLE.** Two clean stored edits and two clean derived edits were found
quickly, each with a backup, and the patterns behind them generalise (see the end).
The derived side is the harder half: almost every good derived fact I found has
the same shape ("X was developed in US state S" = developed by / at organisation O,
O located in S), so variety across topics or extra records will need more work.

## 0. Method and tool notes

- Infini-gram via the shared helper `ig.py` (default index `v4_dolma-v1_7_llama`,
  a few checks on `v4_rpj_llama_s4`). About 65 calls.
- Wikipedia read two ways: WebFetch of the article (lead/body quotes), and the raw
  wikitext (`?action=raw`, saved to `{SCRATCH}/wiki_tech/`) grepped for absence
  checks, so "not on the page" means "not in the full wikitext", not just the
  visible part.
- **Tool caveat (important for reviewers):** `A AND B` co-occurrence counts come
  back as `0, approx: true` whenever one operand is very frequent ("New Jersey",
  "California", "New York", "Massachusetts"). Examples: `Bell Labs AND New Jersey`
  = 0 and `Java AND California` = 0, although `Bell Labs AND Murray Hill, New Jersey`
  = 1748. Also `Unix AND Bell Labs in Murray Hill` = 0 (approx) while the exact
  phrase `UNIX at Bell Labs in Murray Hill` = 2. So zero AND-counts are **not**
  used as absence evidence anywhere below; only exact-phrase zeros and
  Wikipedia-page absence are.

## 1. Candidates and screening

### Stored (stated explicitly and often)

| # | Fact | Evidence (Dolma exact / co-occ.) | Kept? |
| --- | --- | --- | --- |
| S1 | Linux was created by Linus Torvalds | "Linux creator Linus Torvalds" 3351; "Linus Torvalds, the creator of Linux" 942; "Linux was created by Linus Torvalds" 72 | **chosen** |
| S2 | The World Wide Web was invented by Tim Berners-Lee | "inventor of the World Wide Web" 10715; "World Wide Web was invented by Tim Berners-Lee" 194 | **chosen** |
| S3 | JavaScript was created by Brendan Eich | "creator of JavaScript" 2049; "JavaScript creator Brendan Eich" 284; "JavaScript was created by Brendan Eich" 94 | **backup** |
| S4 | Python was created by Guido van Rossum | "Python was created by Guido van Rossum" 233 | dropped: no clean name-vs-description fact (BDFL is defined via being creator; employer facts not concrete in the new world) |
| S5 | C was created by Dennis Ritchie | "C was created by Dennis Ritchie" 47 | possible (K&R co-author query); weaker counts, and "Ritchie and Thompson" co-credit talk is an R1 risk |
| S6 | Git was created by Linus Torvalds | "Git was created by Linus Torvalds" 178 | used as a bridge fact in S1 instead |
| S7 | Bitcoin was created by Satoshi Nakamoto | not counted | dropped: pseudonymous creator, no birth country etc. for concrete worlds |
| S8 | The telephone was invented by Alexander Graham Bell | not counted | dropped: R1 (Meucci/Gray dispute) |

### Derived (rarely stated, follow from 2+ often-stated premises)

| # | Fact | Premises | Kept? |
| --- | --- | --- | --- |
| D1 | Unix was first developed in New Jersey | Unix developed at Bell Labs; Bell Labs is in Murray Hill, NJ | **chosen** |
| D2 | Java was originally developed in California | Java developed by Sun Microsystems; Sun HQ in California | **chosen** |
| D3 | PostScript was developed in California | PostScript developed by Adobe; Adobe HQ San Jose, CA | **backup** |
| D4 | C was developed in New Jersey | same Bell Labs premise as D1 | redundant with D1 (usable as a query there) |
| D5 | The transistor was invented in New Jersey | Bell Labs premise | redundant; also exact phrase already has 4 hits |
| D6 | Windows was developed in Washington state | Windows by Microsoft; Microsoft HQ Redmond, WA (exact "Windows was developed in Washington" 0; "Microsoft is headquartered in Redmond" 158) | dropped: the product's name ("Microsoft Windows") contains the developer, so the "product moves" world contradicts a firm fact and only one world survives |
| D7 | The World Wide Web was invented in Switzerland | invented at CERN; CERN in Geneva | dropped: R1 (CERN straddles France/Switzerland) and the direct form is common |
| D8 | Ruby / C++ / Python creator nationality ("Ruby was created in Japan", "C++ was created by a Dane") | creator + nationality | dropped: direct form ("Danish computer scientist", "Japanese programmer") is stated very often |

## 2. Chosen records

### technology-replace-0001 (stored): Linux created by Linus Torvalds -> Richard Stallman

- **Edit:** "Linux was created by Richard Stallman." Relation `created_by`. Old: Linus Torvalds.
- **Derivability:** `very_unlikely` (stated everywhere, follows from nothing).
- **Plausibility:** false but plausible: Stallman founded GNU, and "GNU/Linux" ties
  his name to Linux. Caveat: "Linux" is named after Linus, which makes the
  counterfactual a little less natural (no query uses the name).

**Evidence (edited fact):**
- Wikipedia, Linux (https://en.wikipedia.org/wiki/Linux): "The Linux kernel was created by Linus Torvalds, following the lack of a working kernel for GNU".
- Dolma: "Linux creator Linus Torvalds" 3351; "Linus Torvalds, the creator of Linux" 942; "Linux was created by Linus Torvalds" 72.

**Bridge facts:**
- Git created by Torvalds. Wikipedia, Git (https://en.wikipedia.org/wiki/Git): "It was originally created by Linus Torvalds for version control in the development of the Linux kernel." Dolma: "Git was created by Linus Torvalds" 178; "Git AND Linus Torvalds" 8223.
- Git stored *by description* (world w2 is realistic): "Git AND Linux creator" 588; sample snippets: "Git version control system was created by none other than Linux creator Linus Torvalds", "Git was written by Linux creator Linus Torvalds".
- Torvalds born in Finland (Helsinki): Dolma "Linus Torvalds was born in Helsinki" 19; Wikipedia, Richard Stallman: "Torvalds, a Finnish student studying at the University of Helsinki".
- Stallman born in New York City, USA: Wikipedia, Richard Stallman (https://en.wikipedia.org/wiki/Richard_Stallman), infobox/body "New York City, New York, U.S."

**Worlds**

| id | assumes | summary |
| --- | --- | --- |
| w1 | "Git was created by Linus Torvalds." (by name) | Git stays with Torvalds; only Linux changes creator. |
| w2 | "Git was created by the creator of Linux." (by description) | Git moves with Linux to Stallman. |

**Derived queries**

| # | Prompt | Label | Original | New / per world | Chain |
| --- | --- | --- | --- | --- | --- |
| 1 | Did Linus Torvalds create Linux? | determinate (A) | yes | no | Linux was created by Stallman (edit); creator is functional here -> not Torvalds. |
| 2 | In which country was the creator of Linux born? | determinate (B) | Finland | United States | creator of Linux = Stallman (edit); Stallman born in NYC -> USA. Dropped route: "Linux was created by a Finn" would give Finland, contradicting "Stallman was born in New York" (firm). |
| 3 | Who created Git? | background_beliefs (C) | Linus Torvalds | w1 Linus Torvalds; w2 Richard Stallman | w1: Git by Torvalds (stored). w2: Git by creator of Linux (stored) + creator of Linux = Stallman (edit). |
| 4 | In which country was the creator of Git born? | background_beliefs (C) | Finland | w1 Finland; w2 United States | w1: Torvalds, born Helsinki. w2: Stallman, born NYC. |

**Other queries (sketch):** direct "Who created Linux?"; paraphrase "Which programmer is credited with writing the original Linux kernel?"; zh "Linux 是由谁创造的？"; es "¿Quién creó Linux?"; near "Who created the MINIX operating system?" (Andrew Tanenbaum); far "Which company developed the PlayStation?" (Sony).

**Self-check:** Q1/Q2 same in w1 and w2 (yes). Q3/Q4 concrete and differ (yes). w2 consistent with firm facts: nothing firmly ties Git's authorship to Finland once stored by description; Git's 2005 origin (after the BitKeeper licence dispute) fits Stallman (yes). R1: kernel authorship undisputed; "GNU/Linux" naming dispute concerns the OS name, not who wrote the kernel; prompts say "Linux" which models read as the kernel/OS, both credited to Torvalds (low risk). R2: no answer in wording (yes). Counterfactual false and plausible (yes).

### technology-replace-0002 (stored): World Wide Web invented by Tim Berners-Lee -> Vint Cerf

- **Edit:** "The World Wide Web was invented by Vint Cerf." Relation `invented` (inverse `invented_by`). Old: Tim Berners-Lee.
- **Derivability:** `very_unlikely`.
- **Plausibility:** the classic Internet/Web confusion (Cerf is "a father of the Internet"); clearly false.

**Evidence (edited fact):**
- Wikipedia, World Wide Web (https://en.wikipedia.org/wiki/World_Wide_Web): "The Web was invented by English computer scientist Tim Berners-Lee while at CERN in 1989" (stated twice, lead and History).
- Wikipedia, Tim Berners-Lee (https://en.wikipedia.org/wiki/Tim_Berners-Lee): "best known as the inventor of the World Wide Web".
- Dolma: "inventor of the World Wide Web" 10715; "World Wide Web was invented by Tim Berners-Lee" 194.

**Bridge facts:**
- TBL founded the W3C. Wikipedia, W3C (https://en.wikipedia.org/wiki/World_Wide_Web_Consortium): "Founded in 1994 by Tim Berners-Lee"; TBL article: "In 1994, Berners-Lee founded the W3C at the Massachusetts Institute of Technology." Dolma: "W3C AND Tim Berners-Lee" 10603; "W3C was founded by Tim Berners-Lee" 17.
- W3C stored *by description* (w2 realistic): "W3C AND inventor of the World Wide Web" 669; "founded by the inventor of the World Wide Web" 16.
- TBL born in London: TBL article "Berners-Lee was born in London"; Dolma "Tim Berners-Lee was born in London" 42.
- Cerf born in New Haven, Connecticut, USA: Wikipedia, Vint Cerf (https://en.wikipedia.org/wiki/Vint_Cerf): "New Haven, Connecticut, on June 23, 1943"; "is an American Internet pioneer".

**Worlds**

| id | assumes | summary |
| --- | --- | --- |
| w1 | "The W3C was founded by Tim Berners-Lee." | W3C stays with Berners-Lee. |
| w2 | "The W3C was founded by the inventor of the World Wide Web." | W3C moves with the Web to Cerf. |

**Derived queries**

| # | Prompt | Label | Original | New / per world | Chain |
| --- | --- | --- | --- | --- | --- |
| 1 | Was the World Wide Web invented by Tim Berners-Lee? | determinate (A) | yes | no | inventor = Cerf (edit). |
| 2 | In which country was the inventor of the World Wide Web born? | determinate (B) | United Kingdom | United States | inventor = Cerf (edit); Cerf born New Haven, CT. Dropped route: "the Web was invented by an English scientist" -> UK contradicts "Cerf is American, born in New Haven" (firm). |
| 3 | Who founded the World Wide Web Consortium (W3C)? | background_beliefs (C) | Tim Berners-Lee | w1 Tim Berners-Lee; w2 Vint Cerf | w1 by name; w2 founder = inventor of the Web (stored) + edit. |
| 4 | In which country was the founder of the W3C born? | background_beliefs (C) | United Kingdom | w1 United Kingdom; w2 United States | via Q3's answer and birthplace. |

**Other queries (sketch):** direct "Who invented the World Wide Web?"; paraphrase "Which computer scientist created the World Wide Web?"; zh "万维网是谁发明的？"; es "¿Quién inventó la World Wide Web?"; near "Who sent the first network email using the @ sign?" (Ray Tomlinson); far "Who created the C programming language?" (Dennis Ritchie).

**Self-check:** determinate answers equal across worlds (yes); indeterminate concrete and differing (yes); w2 consistent: W3C was founded at MIT in the US, which fits an American founder (yes). Avoided "Where was the Web invented?" (CERN would survive in both worlds and makes Cerf-at-CERN awkward). R1: Robert Cailliau is sometimes named as a collaborator, but the invention is credited to TBL alone in Wikipedia and almost all text (low risk); W3C's sole named founder is TBL. R2 ok. Plausible and false (yes).

### technology-replace-0003 (derived): Unix was first developed in New Jersey -> Massachusetts

- **Edit:** "Unix was first developed in Massachusetts." New relation proposed: `developed_in_state` (chain `developed_at ∘ located_in ⊑ developed_in_state`). Old: New Jersey.
- **Derivability:** `likely` (not `very_likely`: some texts do name Murray Hill, NJ, next to Unix; see ratios).
- **Plausibility:** Unix grew out of Multics, an MIT (Massachusetts) project, so plausible; clearly false. California was rejected as the new value because BSD Unix *was* developed at Berkeley (R1 noise).

**Premises:**
1. Unix was first developed at Bell Labs. Wikipedia, Unix (https://en.wikipedia.org/wiki/Unix): development "started in 1969 at the Bell Labs research center by Ken Thompson, Dennis Ritchie, and others." Wikipedia, Bell Labs: Ritchie and Thompson "created the computer operating system UNIX". Dolma: "Unix AND Bell Labs" 24509; exact "Unix was developed at Bell Labs" 28 (RedPajama 32).
2. Bell Labs is in Murray Hill, New Jersey. Wikipedia, Bell Labs (https://en.wikipedia.org/wiki/Bell_Labs): "With headquarters located in Murray Hill, New Jersey"; "in 1967 Bell Laboratories headquarters was officially relocated to Murray Hill, New Jersey" (before Unix, 1969). Dolma: "Bell Labs in Murray Hill" 1693 (RedPajama 1668); "Bell Labs in Murray Hill, New Jersey" 681.
Rule: a thing developed at a place located in state S was developed in S.

**Absence evidence (edited fact), all tries:**

| Search | Result |
| --- | --- |
| Dolma "Unix was developed in New Jersey" | 0 (RedPajama 0) |
| Dolma "Unix was born in New Jersey" | 0 |
| Dolma "developed Unix in New Jersey" | 0 |
| Dolma "UNIX at Bell Labs in Murray Hill" | 2 |
| Dolma "Unix AND Murray Hill, New Jersey" (co-occ.) | 133 (approx) |
| Dolma "Unix AND Murray Hill" | 805 (approx; snippets are mostly Ritchie obituaries) |
| Wikipedia "Unix" raw wikitext: "New Jersey", "Murray Hill" | absent (only "California" via Berkeley/BSD) |
| "Unix AND New Jersey" | 0, unusable (tool artifact, see section 0) |

Ratio: direct exact forms 0 vs premise 1 co-occurrence 24509 vs premise 2 exact 1693; the closest proxy for the direct fact (Unix within a window of "Murray Hill, New Jersey") is 133 / 24509 ≈ 0.5% of Unix+Bell Labs mentions. The Unix article itself never names the state.

**Worlds**

| id | assumes (premise that gives way) | summary |
| --- | --- | --- |
| w1 | "Unix was first developed at Bell Labs" gives way | Unix was first developed at some Massachusetts lab; Bell Labs stays in NJ. |
| w2 | "Bell Labs is in New Jersey" gives way | Unix stays a Bell Labs product; Bell Labs is in Massachusetts. |

w1 note: Thompson and Ritchie remain Bell Labs employees; Unix being first written while they worked elsewhere (e.g. with MIT on Multics) contradicts nothing a model holds firmly beyond the premise itself.

**Derived queries**

| # | Prompt | Label | Original | New / per world | Chain |
| --- | --- | --- | --- | --- | --- |
| 1 | In which US state is the research laboratory where Unix was first developed? | determinate (premise route) | New Jersey | Massachusetts | w1: lab is a Massachusetts lab. w2: lab = Bell Labs, now in MA. Same in both. A model answering NJ only patched the conclusion. |
| 2 | Was Unix first developed in New Jersey? | determinate (A) | yes | no | edit: first developed in MA; one state. |
| 3 | Was Unix first developed at Bell Labs? | derived_beliefs (D) | yes | w1 no; w2 yes | w1 premise 1 gives way; w2 it holds. |
| 4 | In which US state is Bell Labs headquartered? | derived_beliefs (D) | New Jersey | w1 New Jersey; w2 Massachusetts | w1 premise 2 holds; w2 it gives way. |

Alternative for Q4: "In which US state was the C programming language developed?" (w1 NJ, w2 MA if C is stored as a Bell Labs product), but it mixes in a background-belief choice, so Q4 as written is cleaner.

**Other queries (sketch):** direct "In which US state was Unix first developed?"; paraphrase "Unix was originally created in which American state?"; zh "Unix 最初是在美国哪个州开发的？"; es "¿En qué estado de Estados Unidos se desarrolló Unix por primera vez?"; near "In which US state was the BSD variant of Unix developed?" (California; unaffected in both worlds); far "Who invented the World Wide Web?".

**Self-check:** Q1/Q2 same in both worlds (yes). Q3/Q4 concrete and differ (yes). Worlds consistent (yes; see w1 note). R1: "first developed" pins 1969 PDP-7 work at Murray Hill; Bell Labs HQ in NJ since 1967 (stable, but Q4 is phrased in the present; Nokia Bell Labs still HQ'd in Murray Hill). R2: no answer in wording; the prompts avoid "Murray Hill" (which would give away NJ). Plausible and false (yes).

### technology-replace-0004 (derived): Java was originally developed in California -> New York

- **Edit:** "Java was originally developed in New York." Relation `developed_in_state` (chain `developed_by ∘ headquartered_in_state`). Old: California.
- **Derivability:** `likely`.
- **Plausibility:** IBM (Armonk, NY) is a major Java player; plausible, clearly false. Texas rejected as the new value because Java's current owner Oracle moved its HQ to Austin, Texas (R1 noise).

**Premises:**
1. Java was developed by Sun Microsystems. Wikipedia, Java (https://en.wikipedia.org/wiki/Java_(programming_language)): "Java was designed by James Gosling at Sun Microsystems." Wikipedia, Sun: "The Java platform was developed at Sun by James Gosling in the early 1990s." Dolma: "Java was developed by Sun Microsystems" 239 (RedPajama 112); "Java was developed at Sun" 42; "Java was created at Sun Microsystems" 23; "Java AND Sun Microsystems" 168502.
2. Sun Microsystems was headquartered in California. Wikipedia, Sun Microsystems (https://en.wikipedia.org/wiki/Sun_Microsystems): "At its height, Sun's headquarters were in Santa Clara, California (part of Silicon Valley)"; also "Sun's former Menlo Park, California, campus". Dolma: "Sun Microsystems AND Santa Clara, California" 447; "Sun Microsystems, Inc. of Santa Clara" 75; "Sun Microsystems in Santa Clara" 60; "Sun Microsystems was headquartered in Santa Clara" 0. Sun's HQ city changed (Mountain View, Palo Alto, Santa Clara) but always in California. **This premise is the weakest piece of evidence in the report**: stated reliably, but in scattered city-level phrasings, and much less often than premise 1.
Rule: a product developed by a company headquartered in S was developed in S.

**Absence evidence (edited fact):**

| Search | Result |
| --- | --- |
| Dolma "Java was developed in California" | 0 (RedPajama 0) |
| Dolma "Java was invented in California" | 0 |
| Wikipedia "Java (programming language)" raw wikitext: "California", "Santa Clara", "Menlo Park" | all absent |
| "Java AND California", "Java AND Santa Clara, California", "Sun Microsystems AND Java AND California" | 0, unusable (tool artifact) |

Ratio: direct 0 vs premise 1 exact 239 / co-occ. 168502 vs premise 2 co-occ. 447.

**Worlds**

| id | assumes (premise that gives way) | summary |
| --- | --- | --- |
| w1 | "Java was developed by Sun Microsystems" gives way | Java came from a New York company; Sun stays in California. (Drags along Gosling's employer or authorship; nothing else firm breaks.) |
| w2 | "Sun was headquartered in California" gives way | Java stays a Sun product; Sun was a New York company. |

**Derived queries**

| # | Prompt | Label | Original | New / per world | Chain |
| --- | --- | --- | --- | --- | --- |
| 1 | In which US state was the company that originally developed Java headquartered? | determinate (premise route) | California | New York | w1: a NY company. w2: Sun, now in NY. |
| 2 | Was Java originally developed in California? | determinate (A) | yes | no | edit. |
| 3 | Was Java originally developed by Sun Microsystems? | derived_beliefs (D) | yes | w1 no; w2 yes | which premise gives way. |
| 4 | In which US state was Sun Microsystems headquartered? | derived_beliefs (D) | California | w1 California; w2 New York | which premise gives way. |

Alternative indeterminate: "In which US state was the Solaris operating system developed?" (w1 CA, w2 NY, if Solaris is stored as a Sun product).

**Other queries (sketch):** direct "In which US state was the Java programming language originally developed?"; paraphrase "Java was first created in which American state?"; zh "Java 编程语言最初是在美国哪个州开发的？"; es "¿En qué estado de Estados Unidos se desarrolló originalmente el lenguaje Java?"; near "Who designed the Java programming language?" (James Gosling) — **careful**: in w1 this could shift if the model revises Gosling, so prefer near "Which company developed the C# programming language?" (Microsoft); far "Who invented the World Wide Web?".

**Self-check:** Q1/Q2 identical across worlds (yes). Q3/Q4 concrete and differ (yes). Worlds consistent (w2 contradicts Sun's Silicon Valley identity only through the premise itself). R1: "originally" is required in Q1, otherwise "the company that developed Java" can be read as Oracle (HQ Austin, TX); with it, the answer is California. R2 ok. Plausible and false (yes).

## 3. Backups

### Backup stored: JavaScript created by Brendan Eich -> Marc Andreessen
- Evidence: Wikipedia, JavaScript infobox "designers = Brendan Eich of Netscape"; Dolma "creator of JavaScript" 2049, "JavaScript creator Brendan Eich" 284, "JavaScript was created by Brendan Eich" 94.
- Description route: Wikipedia, Brave (https://en.wikipedia.org/wiki/Brave_(web_browser)): "Brave Software was founded in 2015 by Brendan Eich, creator of JavaScript and former Mozilla CEO"; Dolma "Brave AND creator of JavaScript" 1404, "Brave AND Brendan Eich" 21097.
- Worlds: w1 Brave stored as founded by Eich; w2 as founded by the creator of JavaScript.
- Queries: (det A) "Did Brendan Eich create JavaScript?" yes -> no; (det B) "Did the creator of JavaScript co-found Netscape?" no -> yes (Andreessen co-founded Netscape, firm); (C) "Who co-founded Brave Software with Brian Bondy?" w1 Eich / w2 Andreessen; (C) "Did a co-founder of Brave Software also co-found Netscape?" w1 no / w2 yes.
- Risks: Brave has two founders (hence "with Brian Bondy"); avoid "CEO of Brave" (current office-holder).

### Backup derived: PostScript was developed in California -> Texas
- Premises: PostScript developed by Adobe (Dolma exact "PostScript was developed by Adobe" 115; "PostScript AND Adobe" 28369); Adobe HQ San Jose, California (Wikipedia, Adobe Inc. infobox: headquarters San Jose, California; Dolma "Adobe Systems in San Jose" 199).
- Absence: Dolma "PostScript was developed in California" 0; Wikipedia "PostScript" raw wikitext contains none of "California", "San Jose", "Mountain View". (Same pattern for PDF: "PDF was developed by Adobe" 112, "PDF was developed in California" 0.)
- Queries: premise route "In which US state is the company that developed PostScript headquartered?" -> Texas; "Was PostScript developed in California?" -> no; (D) "Was PostScript developed by Adobe?" w1 no / w2 yes; (D) "In which US state is Adobe headquartered?" w1 California / w2 Texas.
- Risk: Adobe was in Mountain View/Palo Alto when PostScript was made; state unchanged, so fine.

## 4. Verdict and difficulty

**FEASIBLE.**

- **Stored candidates: easy.** Creator/inventor facts are stated very often, and
  technology has many "Y was founded/written by the creator of X" descriptions,
  which give clean background-belief queries: Git/Linux, W3C/Web, Brave/JavaScript,
  Mozilla/JavaScript, the K&R book/C, FSF/GNU. Easily 10+ more.
- **Derived candidates: harder, but enough.** The reliable pattern is
  "product developed in state S" via developer/lab + location (Unix, C, Java,
  Solaris, PostScript, PDF; probably also others from Bell Labs, Xerox PARC,
  Sun, Adobe). Perhaps 8-10 more of this one shape; truly different derived
  shapes were hard to find (nationality of a creator is stated directly too often).
  Traps found: product names that contain the developer (Microsoft Windows,
  Google Chrome) kill one world; products whose origin differs from the
  company's HQ (e.g. Photoshop was begun by the Knoll brothers outside Adobe)
  break R1; current-owner drift ("the company that developed Java" = Oracle).
- **Indeterminate queries:** straightforward with yes/no premise questions and
  "in which state is O headquartered"; all concrete.
- **Evidence:** Wikipedia quotes are easy; infini-gram AND counts silently return
  0 when one operand is a common word like a US state, so absence must rest on
  exact phrases and Wikipedia wikitext, as done here. The Sun HQ premise is the
  weakest piece of evidence; PostScript (backup) has a stronger HQ premise.
