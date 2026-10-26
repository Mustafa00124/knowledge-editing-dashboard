# Finance RBox 0017-0018 (role chain, functionality)

Validator (with finance.md + finance.rbox2.md relations and checks): 4 files, 0 errors.
criteria.py: Rule 9 ok (finance RBox replace balanced); rbox_property = chain (0017), functional (0018).
criteria.py lists incorporated_in / has_iso_4217_code as uncatalogued only because it does not read the
extra relation files: merge `relations/finance.rbox2.md` and `finance.rbox2.checks.json` into the shared files.

| Id | Edit | Direct (orig -> new) | Derived instances |
| --- | --- | --- | --- |
| finance-replace-0017 | incorporated_in ∘ located_in ⊑ incorporated_in removed | yes -> no | Apple / California / US; Coca-Cola / Delaware / US: yes -> no |
| finance-delete-0017 | same chain deleted | yes -> null | same prompts: yes -> null |
| finance-replace-0018 | Func(has_iso_4217_code) removed | "Can one currency have two codes at once?" no -> yes | "Given only this, could the yen also have YEN / the pound STG?" no -> yes |
| finance-delete-0018 | Func(has_iso_4217_code) deleted | "at most one code at a time?" yes -> null | "Does it follow that YEN / STG is not its code?" yes -> null |

All derived queries: instantiation, hops 2, facts in prompt, logic dl, chain given, no determinacy/worlds.
Rule 9: 0017 new answers all no, 0018 all yes; with 0009-0012 finance replace RBox is direct 3/3, derived 6/6, cross-lingual 6/6.

## New relations (scratch file relations/finance.rbox2.md)
- `incorporated_in` tag `chain:located_in->incorporated_in` (T = R, like born_in; not functional since it chains into itself).
- `has_iso_4217_code` tag `functional`.

## Why the originals hold without exception
- Chain: a company organised under the law of a state/province/territory is a company of every larger
  place containing it (a Delaware corporation is a U.S. corporation). R (incorporated_in) and S (located_in) differ.
  Instances: Apple Inc. is a California corporation; The Coca-Cola Company a Delaware corporation (1919).
- Functional: ISO 4217 assigns each currency one alphabetic code; codes change only on replacement or
  redenomination (TRL -> TRY), never two at once ("at the same time" in every prompt). Fund codes
  (USN, CHE/CHW) are separate units; the instances (yen JPY, pound GBP) avoid them. YEN and STG are not ISO codes.

## Locality
- 0017 near: chain asked of listed_on (exchange location carries over), ref yes (new answer no). Far: 'is taller than' transitive (now 8 uses).
- 0018 near: "Can a single ISIN identify two different securities at the same time?" ref no (new answer yes). Far: 'is the twin of' symmetric (new prompt).

## Doubts
- "Incorporated in the United States" is slightly loose wording (U.S. companies are incorporated under state law, not federal);
  the chain reads it as "incorporated in a place within the United States". A pedantic model might answer no even before the edit.
- STG is a common informal abbreviation for sterling, so a model might hesitate on the pound instance; it is not an ISO 4217 code.
- The near query for 0018 is strictly inverse-functionality of an ISIN relation (one ISIN -> one security) phrased as functionality of 'identifies'.
- Facts (Apple CA, Coca-Cola DE) checked from memory, not re-fetched; RBox evidence is optional.
