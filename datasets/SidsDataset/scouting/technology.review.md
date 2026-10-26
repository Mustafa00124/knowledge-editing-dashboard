# Technology: critic's review of the scouting report

Reviewer checks: about 75 infini-gram calls through `ig.py` (Dolma, default
index), all AND counts redone after the coordinator's `max_clause_freq=500000`
fix; Wikipedia wikitext (`action=raw`, generic User-Agent) for en/de/fr/es Unix,
History of Unix, Thompson, Ritchie, Multics, Bell Labs, Java (en/de), Gosling,
Sun, Linux, Torvalds, Berners-Lee, W3C, Brave. These are saved in
`{SCRATCH}/critic_tech/`. No repository files were edited.

## 0. The AND-query issue (extra task)

**The scout's observation is true for the old helper. It was a sampling
artifact, not a real absence.** The old `ig.py` used the API's default
`max_clause_freq` (50,000). With a frequent clause the API subsamples and can
return `0, approx: true`. After the fix:

| Query | Old helper | Fixed helper |
| --- | --- | --- |
| Bell Labs AND New Jersey | 0 | 15,988 |
| Java AND California | 0 | 99,866 |
| Unix AND New Jersey | 0 | 1,039 |
| Sun Microsystems AND Java AND California | 0 | 48,044 |
| Bell Labs AND Murray Hill, New Jersey (control) | 1,748 | (unchanged phrase) |
| Princeton University AND New Jersey (control) | 24,079 | — |

**False zeros still happen after the fix** when both clauses are huge:
`Java AND New York` = 0 (approx), while `Java AND California` = 99,866 and
`Brooklyn AND New York` = 5.77M. ("Java" 29.9M, "New York" 193M.) So: an AND
zero is never absence evidence when a clause has more than ~500k hits, and
every AND count with a frequent clause is a sampled estimate (`approx: true`).
The re-runs differ from the scout's numbers by up to 2x (see the table in
section 1).

**Does the derived-absence evidence still hold? Yes.** The scout never used an
AND zero as evidence (section 0 of the report says so, and that is accurate).
The non-zero co-occurrences are mostly noise, not statements of the fact:
`docs "Unix AND New Jersey"` returns a spam page and a SysV Unix man page
("usually New Jersey time"); `docs "Unix AND Murray Hill, New Jersey"` returns
a Bell Labs definition list and a 1975 citation ("Unix Programmer's Manual,
Bell Laboratories, Murray Hill, New Jersey"). `docs "Java programming language
AND California"` returns Oracle-v-Google news. Exact-phrase zeros all reproduce.

## 1. Evidence reproduction

### Counts

Exact phrases: **all reproduced exactly** (sample): "Linux creator Linus
Torvalds" 3351; "Linus Torvalds, the creator of Linux" 942; "inventor of the
World Wide Web" 10715; "World Wide Web was invented by Tim Berners-Lee" 194;
"Git was created by Linus Torvalds" 178; "founded by the inventor of the World
Wide Web" 16; "Tim Berners-Lee was born in London" 42; "Linus Torvalds was born
in Helsinki" 19; "creator of JavaScript" 2049; "Unix was developed at Bell
Labs" 28; "Bell Labs in Murray Hill" 1693; "Bell Labs in Murray Hill, New
Jersey" 681; "Java was developed by Sun Microsystems" 239; "Sun Microsystems in
Santa Clara" 60; "PostScript was developed by Adobe" 115; "Adobe Systems in San
Jose" 199; all the "... was developed in <state>" zeros.

AND counts (fixed helper; scout's value in brackets): Unix AND Bell Labs 22,936
[24,509]; Unix AND Murray Hill 861 [805]; Unix AND Murray Hill, New Jersey 264
[133]; Java AND Sun Microsystems 148,230 [168,502]; Sun Microsystems AND Santa
Clara, California 2,650 [447]; PostScript AND Adobe 30,585 [28,369]; Git AND
Linus Torvalds 16,599 [8,223]; Git AND Linux creator 322 [588]; W3C AND Tim
Berners-Lee 10,618 [10,603]; W3C AND inventor of the World Wide Web 1,319
[669]; Brave AND creator of JavaScript 1,923 [1,404]; Brave AND Brendan Eich
15,096 [21,097]. Same order of magnitude everywhere; none changes a conclusion.
The Sun HQ premise looks **stronger** than the scout thought (2,650, plus
"Sun Microsystems in California" 115, "Santa Clara-based Sun Microsystems" 26).

### Quotes

Confirmed in current wikitext: Unix ("at the Bell Labs research center by Ken
Thompson, Dennis Ritchie, and others"); Bell Labs ("With headquarters located
in Murray Hill, New Jersey"); Java ("Java was designed by James Gosling at Sun
Microsystems"); Sun ("At its height, Sun's headquarters were in Santa Clara,
California"); Git ("originally created by Linus Torvalds for version control in
the development of the Linux kernel"); World Wide Web ("The Web was invented by
English computer scientist Tim Berners-Lee while at CERN in 1989"); W3C
("Founded in 1994 by Tim Berners-Lee"); TBL ("best known as the inventor of the
World Wide Web", "In 1994, Berners-Lee founded", born in London); Stallman
("Torvalds, a Finnish student...", born New York City); Cerf (New Haven,
Connecticut); Torvalds (born Helsinki).

**Not reproduced:**
- Linux: "The Linux kernel was created by Linus Torvalds, following the lack of a
  working kernel for GNU" is not in the current en wikitext (no "lack of a
  working"). Use instead: "...which was first released on 17 September 1991 by
  Linus Torvalds" (present in the lead).
- Brave: "Brave Software was founded in 2015 by Brendan Eich, creator of
  JavaScript and former Mozilla CEO" is not in the current Brave wikitext (the
  scout's own saved copy doesn't have it either). The article calls Eich
  "Mozilla cofounder" and "CEO". The description route for the backup rests on
  the Dolma count only (1,923).

## 2. Derived really derived?

**Unix -> New Jersey: holds, slightly weaker than reported.** Extra tries, all
0: "Unix was created in New Jersey", "Unix was invented in New Jersey", "Unix
was developed in Murray Hill", "Unix was born in Murray Hill". "developed at Bell
Labs in Murray Hill" = 5. No mention of New Jersey or Murray Hill in the Unix
articles of en, de, fr or es Wikipedia, nor in History of Unix, Ken Thompson or
Multics (Ritchie's page mentions NJ only for his childhood). **But** the en
Bell Labs article has a facilities list: "Murray Hill (MH) – 600 Mountain Ave,
Murray Hill, NJ (... developed transistor, UNIX operating system and C
programming language ...)". That is a near-direct statement in Wikipedia; it
is one table row, so `likely` still fits, but the report should cite it rather
than say Wikipedia never links them. Ratio with fixed counts: 264 / 22,936 ≈
1.2% (and those 264 are mostly not statements of the fact).

**Java -> California: holds.** "Java was developed in California" 0; "Java was
created in California" **1** (a tutorial page: "Java was created in California
by Sun Microsystems"); en and de Java articles and James Gosling's article
mention no California place at all (de only via a USC citation). Premises are
both common.

**PostScript -> California (backup): holds** for the exact phrase (0); not
re-checked further.

## 3. Labels and worlds

### 0001 Linux: Torvalds -> Stallman (stored)
- Q1, Q2 determinate: hold. Q2's dropped route ("a Finn") correctly dropped.
- Q3, Q4 (Git, background_beliefs): valid split. Caveat (systemic): the
  description form almost always comes with the name ("Linux creator Linus
  Torvalds" 3351; Git snippets: "originally developed by Linux creator Linus
  Torvalds"). A model storing Git *only* by description is a weaker hypothesis
  than in the Eiffel-Tower example, but it is the form the spec accepts.
- R1: real risk. Stallman is the one person with a public claim to part of
  "Linux" (GNU/Linux); a judge may treat "Stallman" as half-right, which makes
  the counterfactual not "clearly false". Also "Linux" is named after Linus
  (a firm fact the edit itself fights; not a world issue, but lowers
  plausibility). Fix: say "the Linux kernel" in every prompt, or swap in the
  JavaScript backup.

### 0002 World Wide Web: Berners-Lee -> Vint Cerf (stored)
- All four labels hold. W3C by description is well attested (1,319
  co-occurrences, 16 exact "founded by the inventor of the World Wide Web").
- R1: fine (Cailliau is a collaborator, not co-inventor, in standard sources).
  Counterfactual plausible (Internet/Web confusion) and clearly false
  ("World Wide Web was invented by Vint Cerf" 0).

### 0003 Unix: New Jersey -> Massachusetts (derived)
- Q1 premise route, Q2: determinate in both worlds. Q3, Q4: concrete and differ.
- World w1 ("Unix was first developed at a Massachusetts lab") is strained:
  it must also detach Thompson and Ritchie from Bell Labs for that work, and
  "Unix developed at Bell Labs" is the stronger premise (22,936 co-occurrences
  vs Bell Labs-in-NJ 2,349 + 1,693 exact). Still a valid world (the lab is
  unnamed but the state is concrete). w2 (Bell Labs in MA) is clean: "Murray
  Hill" itself stays in NJ, so Q4 should not mention Murray Hill (it doesn't).
- R1 date note the scout missed: Nokia Bell Labs HQ is moving from Murray Hill
  to New Brunswick, **also New Jersey** (Bell Labs article: groundbreaking 4
  Sept 2025). Q4's answer is stable; just don't phrase anything with the town.
- Wikipedia-near-statement noted in section 2.

### 0004 Java: California -> New York (derived)
- Labels hold structurally. Fixes:
  - R2/ambiguity: Q3 and Q4 and the direct question must say "the Java
    programming language" (Java is also an island; "Java AND Indonesia"
    284,315). The report writes "Java" bare in Q3.
  - w1 (Java not by Sun) conflicts with firm facts beyond the premise:
    Gosling at Sun ("designed by James Gosling at Sun Microsystems", in the lead)
    and "Oracle got Java by buying Sun". w2 (Sun HQ in NY) fights "Sun = Stanford
    University Network", a well-known origin story stated in the Sun article.
    Both worlds survive (a HQ can be elsewhere than the founding campus; Gosling
    can move), but both are more strained than the Unix ones. Say so in
    `determinacy_why`.
  - "originally" is essential (Oracle: Austin TX, and announced move to
    Nashville); keep it in every query, including Q3.
- Evidence: the Sun-HQ premise is fine with fixed counts (not the weak link).

### Backups
- JavaScript -> Marc Andreessen (stored): structurally good and the cleanest
  stored candidate R1-wise. Fix the Brave quote (not reproducible). Note Eich
  is Brave's current CEO: keep the "co-founded ... with Brian Bondy" phrasing.
- PostScript -> Texas (derived): good; same shape as Java but with a stronger,
  single-city HQ premise ("San Jose-based Adobe" 242, "Adobe in San Jose" 241).
  Adobe was in Mountain View/Palo Alto when PostScript was built: same state.

## 4. Per-record verdicts

| Record | Verdict | What to do |
| --- | --- | --- |
| 0001 Linux -> Stallman | **FIX** (or swap) | Prompts say "the Linux kernel"; replace the unreproducible Wikipedia quote. If the GNU/Linux risk is judged too high, promote the JavaScript backup. |
| 0002 Web -> Cerf | **KEEP** | — |
| 0003 Unix NJ -> MA | **KEEP** (minor fix) | Cite the Bell Labs facilities-list line; note the New Brunswick move; note w1 is the weaker world. |
| 0004 Java CA -> NY | **FIX** | "Java programming language" everywhere; "originally" in Q3; record the firm-fact strain in both worlds. Consider PostScript as the main record and Java as backup. |
| Backup JavaScript -> Andreessen | KEEP as backup | Replace Brave quote with Dolma evidence or another source. |
| Backup PostScript CA -> TX | KEEP as backup | — |

## 5. Topic verdict

**FEASIBLE — I agree with the scout.** 4 solid records survive with small
fixes (2 stored + 2 derived), plus 2 usable backups. Finding 4 is easy;
scaling stored records beyond 4 is easy (creator/inventor facts with
"founded by the creator of X" descriptions). Scaling derived records is
moderate: nearly all are one shape (product -> developer/lab -> HQ state), so
a 10-record topic would be repetitive, and each needs a careful check that the
developer's location isn't stated in a Wikipedia table or list.

## 6. Systemic lessons

1. **AND counts:** re-run any AND count produced before the helper fix. Even
   after it, an AND zero is meaningless when a clause has >500k hits (both
   clauses frequent gives false zeros: `Java AND New York` = 0), and all such
   counts are sampled estimates that vary up to 2x. Never use AND zeros as
   absence; read `docs` snippets for any non-zero co-occurrence.
2. **Absence checks must include related articles' tables/lists**, not just the
   subject's article (the Bell Labs facilities list states the Unix-NJ link).
3. **Quotes from WebFetch summaries drift.** Two quotes were not in the
   wikitext. Verify quotes against `action=raw`.
4. **Description-storage worlds:** descriptions usually appear next to the name
   ("Linux creator Linus Torvalds"); this is fine but means the description
   world is the weaker hypothesis. Worth stating in `determinacy_why`.
5. **Derived "premise gives way" worlds drag firm neighbours with them**
   (inventor's employer, acquisition history, company-name origin). Check
   those neighbours explicitly in the self-check.
6. **Ambiguous names** (Java, Python, Ruby) need the qualifier in every prompt.
