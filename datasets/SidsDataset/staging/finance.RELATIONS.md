### Finance

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `financial_capital_of` | city a is the financial capital (the main financial centre) of country b | associative | `functional`, `inverse:has_financial_capital`, `subproperty:located_in`, `chain:located_in->located_in` | Frankfurt is the financial capital of Germany. |
| `has_financial_capital` | country a's financial capital (its main financial centre) is city b | associative | `functional`, `inverse:financial_capital_of` | India's financial capital is Mumbai. |
| `merged_with` | company a merged with company b (a company can take part in several mergers) | associative | `symmetric`, `cardinality:many` | Daimler-Benz merged with Chrysler. |
| `deposit_insurance_limit` | deposits at bank a (or at every bank of class a) are insured up to amount b per depositor | associative | `functional` | Deposits at every FDIC-insured bank are insured up to $250,000 per depositor. |
| `zorvels` | a zorvels b (fictional nonce verb; insert d003 makes it asymmetric) | associative | | The Bank of Canada zorvels the Reserve Bank of Australia. |
