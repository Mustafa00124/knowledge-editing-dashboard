# People TBox 0019, 0020: verifier review

| Record | Verdict | What |
| --- | --- | --- |
| replace-0019 | FIXED | Derivability changed from very_unlikely to **unlikely**. The style also follows from a superclass rule: Knight Bachelor is "the basic rank granted to a man who has been knighted", and Wikipedia's own article says "A man who is knighted is formally addressed as 'Sir'". This is the same subclass route as people-0007 (life peer, peer, Lords), which is rated unlikely. Updated `notes` and the rule's evidence `why`. The Elton John quote ended in "in 1998." but the wikitext sentence goes on ("... in 1998 and was appointed ..."), so I dropped the period to make it word for word. |
| delete-0019 | FIXED | Same derivability, `why` and quote fixes. `notes` now says that a model which re-derives "Sir" for Pell or Tranter through the knight superclass kept what the delete removes (accepted risk, as in delete-0007). |
| replace-0020 | FIXED | Derivability changed from very_unlikely to **unlikely**. "Canonized" means "declared a saint" (the record's own evidence counts are for this definition), and saints are styled "Saint", so the rule can be re-derived. Updated `notes` and `why`. |
| delete-0020 | FIXED | Same derivability change, plus the same accepted-risk note for re-deriving the title for the new members. |

## Checks
- **Counts:** re-ran all 12 cited counts with `--fresh`. All 12 match and none changed. The sampled "knighted AND Sir" count is marked approximate. Extra search: "man who is knighted" has 7 hits, so the superclass rule is mostly phrased in other ways ("knights are styled Sir"). Downgrading only to unlikely, not medium, is a judgement call.
- **Quotes:** checked 6 against the raw wikitext. 5 match word for word. Elton John had a trailing period that is not in the source (fixed).
- **Rules have no real exception (writer doubt 1):** the 0019 rule is worded as an entitlement for British laymen. Clergy and honorary foreign knights fall outside it. A knight who is later made a peer keeps the knighthood and the entitlement and only uses the higher style. McCartney and Elton John hold no peerage, and their CH carries no style. I accept it as exception-free. 0020: every canonized person, popes included ("Pope Saint ..."), is titled Saint. No exception.
- **Leaving the class (writer doubt 2):** McCartney and Elton John leaving Knight Bachelor contradicts only their own investiture (1997, 1998), which is a side fact listed in the world. No succession, numbering or other person depends on it. In w1, "Sir" stays possible through another order, or simply as stored by name. Joan and Ignatius leaving "canonized" contradicts only their own canonization acts (1920 Benedict XV; 1622 Gregory XV, a joint ceremony whose other four saints are unaffected). Keeping "Saint" without formal canonization has a real-world pattern: pre-congregation saints. Patronage, feast days and named churches are names and roles, not firm facts that force the class. Unlike the popes, photon, Mars and Iliad cases, none of these breaks a firm fact outside the chain. No prompt asserts membership: the prompts ask only for the honorific or title.
- **New members:** Graham Pell, Owen Tranter, Maria Kowalczyk and Tomás Ibarra are fictional and named in the prompt with their class.
- **Deletes:** world answers re-derived correctly (null where the route ran through the rule, the original where it was stored by name). New-member "does not know" is valid except for the superclass and definitional re-derivation noted above.
- **Logic:** `dl` for all inheritance queries is right.
- **Rule 4:** no repeat of 0005-0008 (Rhodes, Olympic gold, life peer, Masters jacket). 0019 is close in theme to 0007 (UK honours) but edits a different property.
- **R7:** near answers (accolade/dubbing; St. Peter's Square) differ from the new answers and are not premises.
- **Validator:** no tbox3 relation files exist, so the variables were omitted. 22 files, 0 errors. criteria.py flags nothing on 0019 or 0020.

## Remaining doubts
- Both rules can be re-derived (knight superclass; canonization means sainthood). This is an accepted risk under the 0007 precedent, but it weakens the determinate "does not know" on the deletes.
- The 0020 zh prompt uses 册封 with an English gloss, to avoid 封圣.
- 0019 and 0020 share one pattern: an honorific granted by a class.
