# Finance round 2 review (ABox 0013-0016, RBox 0017-0018)

Validator (finance.md + finance.rbox2.md, both checks files): 36 files, 0 errors.
criteria.py: Rule 9 ok (finance RBox replace 0009-0018 balanced: direct 3/3, derived 6/6, cross-lingual 6/6); Rule 11 finance 8/8 ABox, 4/4 stored, 4/4 derived.
Records 0001-0012 not touched.

## Evidence
- Infini-gram: all 45 distinct counts in 0013-0016 re-run with `--fresh`: 0 changed (exact and approximate). Output: `{SCRATCH}/finv2/rerun.tsv`.
- 13 extra searches for the derived claims and controls (Nestle unaccented, address forms, Siemens AND CAC 40 / SBF 120, LinkedIn forms).
- Quotes: 11 Wikipedia quotes re-fetched (API plain text), 11 found word for word, 0 failed. IndustryWeek note (Siemens delisting London/Zurich) confirmed.
- RBox facts checked online (SEC EDGAR submissions API): Apple Inc. state of incorporation CA; The Coca-Cola Company DE.

## Per record
| Record | Verdict |
| --- | --- |
| R/D 0013 Rolls-Royce BMW -> Audi | KEEP. Subproperty (wholly_owned ⊑ subsidiary_of) and transitivity via subsidiary_of (Audi ⊂ VW AG) both real, tagged, discriminating, same in both worlds. Engine worlds consistent (VW-era Rolls-Royce/Bentley bought BMW engines). |
| R/D 0014 Siemens DAX -> CAC 40 | FIXED (minor): near reference "the Nikkei 225 (also the TOPIX)". Inheritance (CAC 40 class rule, edit puts Siemens in the class, question does not restate it) and declared chain `index_constituent_of ∘ subindex_of ⊑ index_constituent_of` are real; "Siemens AND SBF 120" = 0, so it discriminates. w2 is lopsided but valid (kept, Decision 4). |
| R/D 0015 Nestlé HQ Vaud -> Haute-Savoie | FIXED: w2 side facts made explicit (Vevey French; neighbours La Tour-de-Peilz, Corsier-sur-Vevey, Montreux stay in Vaud; no longer in Riviera-Pays-d'Enhaut or Lausanne's canton). Valid under Decision 1: it changes facts about Vevey only, no firm fact about other places, and "Vevey in Vaud" is not entailed by facts outside the chain. Evidence: added "headquartered in Vevey, Vaud" = 419 (mostly copies of an old Nestlé Wikipedia lead) and Nestlé AND that = 337, with a note; rating kept `likely` (the address pattern, like "Paris, France" in README's Eiffel Tower example) but listed as a doubt. |
| R/D 0016 LinkedIn | RE-SHAPED. Same edit, now `located_in` on "the headquarters of LinkedIn's parent company" (Redmond -> Austin), instead of `parent_headquartered_in` (functional only, 0003's shape). Replace determinates: premise-route state (transitivity, Austin -> Texas) and "in the US Census Bureau's South region?" (transitivity, 2 bridges, no -> yes); check added for Texas/South. Delete: premise route asks the county (King County; the state could survive in w2 as "Washington-based Microsoft"), second determinate compares with Nintendo of America's Redmond HQ (fol); w2 side facts now include county and state. Evidence keys renamed. |
| R/D 0017 incorporated_in chain | FIXED. Statement shortened per the new rule; the rule narrowed from "a place in a larger place" to "a state or province in a country" (statement/original, direct prompt in both records): Hong Kong and Puerto Rico companies break the general form. With states/provinces it holds (a Delaware corporation is a U.S. corporation; "country of incorporation: United States" is standard). Genuine chain over two relations (incorporated_in, located_in), T = R like born_in. |
| R/D 0018 ISO 4217 functional | FIXED: statement/original shortened ("'Has ISO 4217 code' is (not) functional."). Functional without real exception: fund/unit codes (USN, CHE/CHW, CLF, MXV, BOV) and VES/VED are separate units; YEN and STG are not ISO codes. |

## Coverage (replace, determinate slots)
transitivity: 0013, 0015 x2, 0016 x2; subproperty: 0013; chain (declared): 0014; inheritance: 0014. Every claimed property is used, tagged, discriminating and world-independent.

## Rename
`index_constituent_of` is used consistently: no bare `constituent_of` in finance records; relations/finance.md and finance.checks.json use the new name.

## Doubts
- 0015 derivability: the "Vevey, Vaud, Switzerland" address string (a few hundred copies) gives the canton near Nestlé; `likely` rests on README's own address-pattern example.
- 0014 delete: the DAX membership is partly re-derivable (Frankfurt listing + one of Germany's largest companies); rating `unlikely` already admits it.
- Global ABox subproperty count is still 9 (want 10, CRITERIA Rule 12); 0016 could not take a subproperty cleanly (finance subproperty relations are stored facts or object-functional, so a derived edit there leaves only one world).
- Rule 13 SubjectNotInPrompt for 0017/0018 is the same as for every RBox record (relation name as subject); not changed.
- Merge relations/finance.rbox2.* into the shared files (criteria.py lists incorporated_in, has_iso_4217_code, index_constituent_of as uncatalogued until then).
