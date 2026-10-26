# Finance inserts (fictional) 0001-0020: verifier review

Fixed via `fin_insert/build.py` (+ `abox_entity.py`, `tbox_entity.py`) and rerun; originals in `fin_insert/bak/`.
Validator: 20 files, 0 errors. criteria.py: Rule 5 ok; Rule 11 ok (finance 8/6/6 under insert; 2 det + 2 indet per
ABox/TBox entity edit; insert mix 3/3/2, 2/2/2, 3/3 ok). Rule 8 lists the fictional relations only because criteria.py
runs without the scratch relation file (same for every topic's inserts).

## Web searches (done; replace the RedPajama stand-ins)
Every made-up name (55, incl. the bond names in 0013's prompts that were not listed before) now has an infini-gram
count and a `search` source (engine "web search", note = what came back). No record lacks one.
Collisions found and renamed everywhere (en/zh/es, relations file):
- Corrigan Bank -> Corriden Bank (0008): a Corrigan National Bank existed (Texas, 1922-28).
- hearth lender / hearth_lender_to -> kiln lender / kiln_lender_to (0018): Hearth is a real lending marketplace.
- Ashcombe Mills -> Ashcrane Mills (0018), Ashcombe bond -> Ashcrane bond (0013): Ashcombe Mill is a real windmill.
- Ashbridge Fund -> Brenlow Fund (0020): Morgan Stanley's Ashbridge funds.
- Corlett Fund -> Torlett Fund (0020): Sue Corlett Fund (Toronto Foundation).
- Maskell House -> Maskwell House (0007): near Thomas Maskel House (NRHP); precaution.
- Dunmore 2030 bond -> Dunmere 2030 bond (0013): Dunmore, PA; precaution.
- Ostrel Clearing House -> Ostwyn Clearing House (0013): "Ostrel" was also the 0009 find.
All new names: Dolma count 0 (fresh), searched, nothing real.
Kept with a note: "keystone-funded" (only used for Pennsylvania's Keystone Fund projects, not a financial relation)
and "tithe-bound" (ordinary church-tithe wording). Neither names a thing.

## Counts and quotes
77 cited counts rerun with --fresh: 0 changed. 24 quotes rechecked: 2 fixed (MUFG head office and florin
"authorised" had a trailing period that the page continues past). The 1822 count's only Wikipedia quote is an
image caption: added Numismatic News ("With just three examples known ...") and noted the caption.

## Entity inserts (rare-coin finds)
- 0001 1913 nickel: "Only five examples are known to exist" (WP). No mintage recorded; WP calls past rumours of a
  sixth "unfounded", so a new one supersedes a rumour, not a record (note added). Plausible. Worlds 5/6, no/yes ok.
- 0002 1894-S dime: "Only 24 were minted, and of those, only nine are known to survive" (WP). 15 unaccounted: plausible.
  Worlds 9/10 and 15/14 ok.
- 0003 1822 half eagle: three known, mintage 17,796 (Numismatic News; WP caption). Plausible. Kept: "1822 half eagle
  AND three known" = 51 in Dolma; the alternatives are worse (1804 dollar went 15 -> 16 in 2025, confirmed on WP;
  Brasher doubloon "seven known" 22, and WP gives no count).
- 0009 Edward III florin: "Only three examples of the coin are known" (WP); the third was found in 2006, so a new find
  is plainly plausible. W2's list (two British Museum, one private, US collector since 2016) matches WP.
- 0010 1870-S $3: "only one is known with certainty to exist" (WP); the cornerstone piece's fate is unknown, so a second
  is plausible. Kept: 1849 double eagle (the other "unique" candidate) is rarer in text (182 vs 223+42).
Indeterminate worlds all concrete and differ; determinate ones have one route. Labels/logic otherwise unchanged.

## Doubts
- 0003 and 0010 counts are less known than 0001/0002; their checks may drop them for some models.
- 0010 "1870-S" names the mint the second determinate query asks about (already noted by the writer).
