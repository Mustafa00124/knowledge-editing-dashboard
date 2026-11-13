### Finance

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `benchmark_constituent_of` | company a is a constituent of b, the one national benchmark stock index it belongs to as a company of that market (one such index per company) | associative | `functional`, `subproperty:index_constituent_of` | Siemens is a constituent of the DAX. |
| `has_largest_bank` | among the banks headquartered in city a, the largest by total assets is b | associative | `functional`, `inverse:largest_bank_in` | The largest bank headquartered in Beijing is ICBC. |
| `largest_bank_in` | bank a is the largest bank by total assets headquartered in city b | associative | `functional`, `inverse:has_largest_bank`, `subproperty:headquartered_in` | ICBC is the largest bank headquartered in Beijing. |
| `has_largest_asset_manager` | among the asset managers headquartered in city a, the largest by assets under management is b | associative | `functional`, `inverse:largest_asset_manager_in` | The largest asset manager headquartered in New York City is BlackRock. |
| `largest_asset_manager_in` | asset manager a is the largest by assets under management headquartered in city b | associative | `functional`, `inverse:has_largest_asset_manager`, `subproperty:headquartered_in` | BlackRock is the largest asset manager headquartered in New York City. |
| `megamerger_partner_of` | company a completed its megamerger with company b, the one merger it is best known for (one partner per company) | associative | `functional`, `symmetric` | Exxon completed its megamerger with Mobil. |
