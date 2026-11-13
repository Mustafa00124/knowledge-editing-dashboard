### Finance

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `sconce_tied_to` | firm a is sconce-tied to firm b (fictional; insert 0015 makes it not transitive) | associative | | Goldman Sachs is sconce-tied to BlackRock. |
| `pennant_bound_to` | firm a is pennant-bound to firm b (fictional; insert 0016 makes it asymmetric) | associative | | Mastercard is pennant-bound to Visa. |
| `ledger_warden_of` | person a is the ledger-warden of company b (fictional; insert 0017 makes it not a subproperty of works_for) | associative | | Jamie Dimon is the ledger-warden of Goldman Sachs. |
| `kestrel_patron_of` | firm a is a kestrel patron of firm b (fictional; insert 0018 makes kestrel_sheltered_by its inverse) | associative | | Berkshire Hathaway is a kestrel patron of Kraft Heinz. |
| `kestrel_sheltered_by` | firm a is kestrel-sheltered by firm b (fictional; inverse of kestrel_patron_of by insert 0018) | associative | | Kraft Heinz is kestrel-sheltered by Berkshire Hathaway. |
| `stave_registered_in` | company a is stave-registered in place b (fictional; insert 0019 removes the chain with located_in) | associative | | Nike is stave-registered in Oregon. |
| `has_reed_steward` | company a has reed steward b (fictional; insert 0020 makes it not functional) | associative | | Vanguard has reed steward State Street. |
