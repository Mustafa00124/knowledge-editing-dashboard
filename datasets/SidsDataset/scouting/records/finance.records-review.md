# Finance records: verifier review

All 24 records are in `datasets/SidsDataset/records/finance/`. The JSON was edited directly; the writer's `fin2/` scripts are now stale.

- Fix scripts: `{SCRATCH}/finv/fix1.py` and `{SCRATCH}/finv/build0008.py`.
- Validator, with the extra relation files: **24 files checked, 0 with errors**.
- criteria.py B7 finance row: 4/4 4/4 4/4, stored 2/2, derived 2/2; 32 determinate, 24 background beliefs, 8 derived beliefs.

## Evidence re-check

**Counts.** All 78 distinct infini-gram counts cited before review were re-run with `--fresh`.
- 0 differed: every count matched exactly, with no zero/non-zero flips.
- The 12 counts in the new 0008 were also fresh calls.

**Quotes.** All 20 distinct quotes were re-checked word for word.
- 19 against the Wikipedia API plain text, and the Swiss Constitution Art. 99 quote against justement.ch.
- 0 failed.
- The new 0008 quotes (CAC 40, LVMH, BNP Paribas) were checked the same way.

## Per record

| Id | Verdict | What |
| --- | --- | --- |
| 0001 R | KEEP | |
| 0001 D | FIXED | The second determinate query ("same currency as Germany?") is not determinate after a delete: "Denmark is not in the eurozone" (the euro opt-out, stored apart from the krone) still answers no, around the deleted fact. Replaced with "What is the official currency of the country whose capital is Copenhagen?" (null in both worlds), plus a check for "Copenhagen is the capital of Denmark." |
| 0002 R | FIXED | `determinacy_why` of the state query now states both dropped routes correctly. The old text ("would put Munich in Hesse") mixed them up. |
| 0002 D | KEEP | |
| 0003 R/D | FIXED | The premise-route query now walks the premises explicitly: "First work out which company owns Pixar, then where that company has its headquarters. In which US state is that headquarters?" Chain rewritten one step per fact. The Pixar-article evidence note was softened: it does mention "returning to Burbank" once. |
| 0004 R | FIXED | w1 now lists its side facts per Decision 1: canton, Lake Zurich, airport, ETH, SIX, the SNB's Zurich seat, and "largest Swiss city". The notes add why w1 survives step 3 (none of these is a firm fact outside the chain, and "Zurich is in Switzerland" is not entailed independently). |
| 0004 D | KEEP | |
| 0005 R/D | FIXED (minor) | Added the Wikipedia quote "Ordinary Treasury notes pay a fixed interest rate that is set at auction." |
| 0006 R | FIXED | The by-name worlds now list their side fact (the pair is no longer treated as interchangeable). The notes record that Wikipedia defines substitutes by use, so this world is strained. |
| 0006 D | FIXED (wording) | |
| 0007 R/D | FIXED (note) | "Mint prints" (226) was sampled: mostly NFT minting and a shop name, with one "the Mint prints currency". The evidence note and R4 note now say this. |
| 0008 R/D | REPLACED | The complements rule mirrored 0006, and its by-name world fails 6a: "cars run on petrol" entails being complements. New rule: "Every company in the CAC 40 index is listed on Euronext Paris" → "... on the London Stock Exchange" (`listed_on`, new in `relations/finance.md`). Index membership is contingent, so "LVMH / BNP Paribas leave the CAC 40 and stay listed in Paris" is a natural by-name world. New members: Kestrel Robotics and Marlowe Foods. Near query: DAX → Germany. |
| 0009 R/D | KEEP | |
| 0010 R/D | KEEP | |
| 0011 R/D | FIXED | Near query is now finance: "Is 'lends to' a subproperty of 'is a creditor of' ...?" (yes). |
| 0012 R | KEEP | |
| 0012 D | FIXED | Notes no longer carry replace-only wording. |

Also fixed: the TBox delete `determinacy_why` texts (0005-0007) no longer speak of "an exception to the rule".

## Writer's doubts resolved

- **0006/0008:** both by-name worlds were strained (definition by use). 0008 is re-picked; 0006 is kept with explicit side facts.
- **0007:** the misconception is rare in text; R4 will catch any model that holds it.
- **0003:** the premise-route query is now explicit.
- **0004:** w1 is valid with its side facts listed.
- **0011:** the near query now uses a finance relation.

## Remaining doubts

- **0006:** the by-name world (coffee and tea not substitutes, yet tea demand rises with coffee's price) is consistent but strained. Re-pick it if a stricter reading of 6a is wanted.
- **0008:**
  - LVMH and BNP Paribas are among the CAC 40's largest members, so the by-name world is lopsided.
  - `listed_on` is cardinality many. A model might name both exchanges after the edit.
- **0002:** the w2 skew from the towers' name, as already noted by the writer.
