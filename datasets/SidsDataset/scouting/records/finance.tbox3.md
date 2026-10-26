# Finance TBox 0019-0020 (writer + self-verification)

Records (built by `{SCRATCH}/fin_tbox3/build.py`):
`datasets/SidsDataset/records/finance/{replace,delete}/finance-{replace,delete}-00{19,20}.json`

| Id | Edit (original -> new) | Relation | Deriv. | Derived queries (all `inheritance`, `dl`) |
| --- | --- | --- | --- | --- |
| 0019 | Every DJIA company is headquartered in the United States -> Canada | `headquartered_in` | unlikely | 2 determinate (Harrowgate Systems, Pellworth Health: invented, named in prompt, `bridge_in_prompt`); 2 `background_beliefs` (Coca-Cola, McDonald's) |
| 0020 | Every WAEMU member state uses the West African CFA franc -> the Nigerian naira | `has_currency` | very_unlikely | 2 determinate (Republic of Varanne, Saint-Corentin: invented); 2 `background_beliefs` (Cote d'Ivoire, Benin) |

Worlds: 4 per record (two independent storage choices). In a by-name world the member leaves the class: Coca-Cola/McDonald's leave the Dow (membership is contingent) and keep their US headquarters; Cote d'Ivoire/Benin leave WAEMU and keep using the CFA franc on their own (as Montenegro uses the euro). Side facts listed. Deletes: by-name worlds keep the original answer, class-route worlds `null`; new members `null` (determinate).

No new relations (both are in RELATIONS.md), so no tbox3 relation files. Repeat check: currency and HQ facts appear in ABox 0001/0002 but on different facts.

## Choices / dropped
- Senegal dropped (BCEAO seat in Dakar would strain the leave-the-union world); Mali, Burkina Faso, Niger dropped (AES politics, R1 risk).
- Eurozone / CFA franc zone / Nikkei rejected: the class name leaks the answer (R2; zh 日经).
- Subjects set to the class name as written in the direct prompt, so the Rule 13 data check (subject appears in the prompt) passes for these 4.

## Verification
- Validator (no extra relation files): 40 files, 0 errors. criteria.py: no rule lists these 4 records.
- Infini-gram: all 23 counts re-run with `--fresh`: 23/23 identical.
- Quotes: 8 quotes re-fetched (Wikipedia plain text, Chase page): 8/8 found word for word.
- Labels: tried to break each. New members have no route besides the rule. By-name worlds contradict no firm fact outside the chain (index/union membership is contingent; leaving after being a founding member is consistent). Background prompts do not assert the membership.

## Doubts
- 0019 R1: the Dow committee's guideline lets it count a company as American "under the committee's judgment"; no member uses this, so the rule has no real exception today, but it is a guideline, not a hard rule.
- 0019 derivability `unlikely`: the rule is more often stated as "30 U.S. companies" than in headquarters wording.
- 0020: a non-member using the CFA franc on its own is coherent but has no current real case; Abidjan hosts two union market authorities (listed as side facts).
- Both: lopsided worlds (members' own facts are far better known than their membership).
- Relation variety is limited: both relations are functional ones already used in finance ABox; neither is property-free.
