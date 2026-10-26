# Review: RBox role-chain inserts through real knowledge (2026-10-26)

Checked per record: axiom is a sound role chain (R ∘ S ⊑ R, S real and in RELATIONS.md),
statement / axiom / direct question / RELATIONS.md `chain:` tag agree, direct question quotes the
made-up wording once, edit.subject = snake_case id; each derived answer follows from the
axiom + the real hop; hop not in the prompt (EN/zh/es), bridge listed, bridge_in_prompt false,
hops 2, check (fact/prompt/answer) present; "no" answers are "Could X fail to be ...?" and
would be "yes, it could"/unknown without the edit; locality answers correct.

Fresh infini-gram counts (Dolma, `ig.py count --fresh`) all match the stored ones:
made-up wordings 0 (pellith 1, loom-tied 3; all <= 5); bridges: Kyoto, Japan 273305;
Montreal, Canada 409030; Python was created by Guido van Rossum 233; created by Yukihiro
Matsumoto 332; Queen Victoria married Prince Albert 1346; married Louis XVI 539; Don Quixote
by Miguel de Cervantes 3469; War and Peace by Leo Tolstoy 3537; The Moon orbits Earth 310;
Titan orbits Saturn 270; Elizabeth I ruled England 329; Cleopatra ruled Egypt 265; plural of
goose is geese 324; plural of child is children 102; genus Panthera 6757; genus Canis 5481;
3 divides 9 142; 6 divides 12 41 (carried by the Wikipedia quote).
All 11 Wikipedia quotes (Python, Ruby, Deutsche Bank, Goldman Sachs, Don Quixote, War and
Peace, English plurals x2, Lion, Canis, 12 (number)) found word for word in the current
article text (API extracts). Web searches for all 11 made-up wordings (incl. vessic-linked):
no real term. Each made-up term appears in exactly one record.

| Record | Verdict | Change |
| --- | --- | --- |
| geography-0017 | fixed | zh: "与…港誓相约" (mutual, direction-ambiguous) -> "卑尔根对京都是“harbour-sworn”（港誓相系）关系…对日本也是…" |
| technology-0017 | keep | |
| finance-0017 | fixed | zh: "与" -> directional "对…是…关系" |
| people-0017 | fixed | zh: "烛誓相许" (mutual pledge, reads symmetric) -> "对…是“candle-pledged”（烛誓相系）关系" |
| literature_arts-0017 | keep | |
| physics-0016 | fixed | zh: "与" -> directional "对…是 pellith-tethered 关系" |
| physics-0015 | keep | changed 2nd derived ("Could the neutron fail to be vessic-linked with the proton?" -> no) discriminates: without Sym it could. |
| history-0015 | keep | doubt: "Cleopatra" could in principle be Cleopatra Thea (Seleucid); the default reading is Cleopatra VII (Egypt). Left as is. |
| grammar-0017 | keep | |
| biology-0017 | fixed | zh: "与…varrish-bound" -> directional "对…是 varrish-bound 关系" |
| mathematics-0016 | fixed | zh had an English gloss "（5 is cairn-linked to 6）" and a direction-ambiguous "与"; now "5 对 6 具有 cairn-linked 关系。5 有没有可能不对 12 具有 cairn-linked 关系？" Fixed in math_insert/build.py and rebuilt (only 0016 changed; backup of prior JSON in math_bak_review/). |

Why the zh fix: the chain is directional (X R Y, Y S Z => X R Z); "A 与 B" ("A with B") does not say
which way the made-up link runs, so a reader could take B R A and the conclusion would not follow.

Minor, not changed: Spanish prompts in geography/people/finance use "con" (with), similarly loose
but the question's form fixes the reading; literature RELATIONS.md row puts the insert note in
the example column (matches the existing has_gleam_twin style).

Validation: validate.py on all records + examples: 606 files, 0 errors. criteria.py: chain check ok,
Rules 5, 7, 9, 10 ok. Only failure is Rule 13 (SubjectNotInPrompt, 89 records, none of them inserts;
pre-existing).
