# people: round-2 review (ABox 0013-0016, RBox 0017-0018)

Validator (people.md + people.rbox2.md, both checks files), all 36 people files: 0 errors.
criteria.py: Rule 9 ok (per topic within 1); Rule 11 people 8/8. The Rule 12 FAILs are global (relations with no property 28%, ABox subproperty 9/10), not caused by people.

## Evidence
- infini-gram: 34 distinct cited counts re-run with `--fresh`: 34/34 identical, 0 changed.
- Wikipedia quotes: 17 distinct quotes re-fetched (rendered pages, 2026-10-25): 17/17 found word for word, 0 failed. New quotes added in the 0013 fix were checked the same way.
- Also confirmed: "Rule of Saint Augustine" for the Dominicans (Dominican Order article), which backs the 0014 delete's rule query.

## Per record
| Record | Verdict |
| --- | --- |
| replace/delete 0013 (Mozart's father -> C. P. E. Bach) | **FIXED.** The two background queries (who taught the child; who took him on the childhood tours) had description worlds that put C. P. E. Bach in Salzburg and on the 1763-66 grand tour. That goes against a firm fact about another person: he held a court post in Berlin from 1738 to 1768 (Wikipedia: "Berlin years: 1738-1768"). Those worlds are not valid (Decision 1). I replaced the two queries, both records: (a) "Who was strongly opposed to Mozart's marriage to Constanze Weber in 1782 and gave his permission only reluctantly?" and (b) "To whom did Joseph Haydn say in 1785 that Mozart was the greatest composer known to him?" Both are stored by name (Leopold) and as "his father" ("permission for the marriage from his father"; "your son is the greatest composer", 384 in Dolma). The description worlds are consistent: C. P. E. Bach was alive in Hamburg until 1788 and could object by letter, or visit Vienna in 1785. I rewrote the 4 worlds, world answers, checks, evidence and notes, and the delete mirrors them (null in the description worlds). Chain query (J. G. Mozart -> J. S. Bach) and subproperty query (child_of) are unchanged and correct. Nannerl as half-sister through her mother is fine; the dates allow it. Delete note: the Wikipedia navbox lists "Johann Georg Mozart (paternal grandfather)", which is a weak direct route. |
| replace/delete 0014 (Aquinas Dominican -> Franciscan) | **KEEP.** The worlds are consistent: a family can oppose the Dominicans and the son still become a Franciscan, and paintings can show a habit. Both inheritance queries use a class rule as a bridge with a check, discriminate, and do not restate the edit. R1 holds: Dominicans live under the Rule of St Augustine, so the original answer to the Rule of St Francis query is "no". In the delete, the Augustine bridge is less well known; its check drops it per model. The by-name side facts (family episode, habit) do not strictly entail membership, so the inheritance queries in the delete stay determinate. |
| replace/delete 0015 (Aage Bohr grandfather -> George Darwin) | **KEEP.** Transitivity is real (ancestor_of is transitive in RELATIONS.md, check added; the answer goes no -> yes and is the same in both worlds). The premise route goes through the description. Both worlds list side facts and dates; neither breaks a fact outside the chain. The Christian Bohr premise may fail on small models; the check drops the record for those models, as designed. |
| replace/delete 0016 (Stella McCartney grandfather -> Alec Guinness) | **KEEP**, with a doubt. It is correct, but it repeats 0003's template almost query for query (binding, grandchild_of subproperty, the two premises). That breaks no rule (a different fact), but 3 of the 8 people ABox edits are now paternal-grandfather edits. It adds 1 to the global ABox subproperty count, which is short (9/10). |
| replace/delete 0017 (born_in ∘ located_in ⊑ born_in -> ⊑ died_in) | **FIXED.** It is a genuine declared chain over two different relations (tag `chain:located_in->born_in`), not transitivity. The instances are border-safe: Honolulu was in Hawaii in 1961 (and Hawaii was a territory before that), and Ulm was in Germany in 1879. The general direct question had real exceptions (Kant was born in Königsberg, which is now in Russia). It now reads "...and, at the time of the birth, that city was located in a country...". In both records, the edit statement and original are shortened to the property (coordinator rule). |
| replace/delete 0018 (Func(has_birth_mother) removed) | **FIXED.** The original is functional with no real exception (surrogates, twins, uterus transplants all still give exactly one birth mother). The Lincoln instance asked "Can Sarah Bush Lincoln also be his birth mother?", which lets the stored fact that she was his stepmother compete (an RBox must not ask what is true). It now asks "Is it consistent with these facts that ...?", with zh and es updated; the answer polarity is unchanged (no -> yes), and the Washington instance is unchanged. Statement and original are shortened to "'Has birth mother' is (not) functional." |

## Coverage (replace, determinate slots)
chain 1 (0013), subproperty 2 (0013, 0016), inheritance 2 (0014), transitivity 1 (0015). Each query discriminates and has the same answer in every world. Logic labels are right: dl throughout, and fol for the full-brothers comparison in 0015.

## Remaining doubts
- 0013's new background facts (the marriage opposition, Haydn's 1785 words) are less salient than teaching and touring, so more models may fail their checks.
- The 0013/0014 description worlds are still lopsided (Decision 4).
- 0016 is redundant with 0003 (see above).
- Surname hints (Mozart, Bohr, McCartney) remain, as in 0003.
