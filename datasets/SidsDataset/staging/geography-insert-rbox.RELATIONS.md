### Geography

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `quill_bound_to` | place a is quill-bound to place b (fictional; insert 0015 makes it asymmetric) | associative | | Tromsø is quill-bound to Valparaíso. |
| `tern_keeper_of` | town a is the tern-keeper of lake b (fictional; insert 0016 makes tern_kept_by its inverse) | associative | | Perth is the tern-keeper of Lake Baikal. |
| `tern_kept_by` | lake a is tern-kept by town b (fictional; inverse of tern_keeper_of by insert 0016) | associative | | Lake Baikal is tern-kept by Perth. |
| `tarn_tied_to` | place a is tarn-tied to place b (fictional; insert 0017 makes it not transitive) | associative | | Oslo is tarn-tied to Nairobi. |
| `wold_warden_of` | city a is the wold-warden of country b (fictional; insert 0018 makes it not a subproperty of located_in) | associative | | Lisbon is the wold-warden of Brazil. |
| `flint_marked_in` | landmark a is flint-marked in region b (fictional; insert 0019 removes the chain with located_in) | associative | | The Leaning Tower of Pisa is flint-marked in Tuscany. |
| `has_beacon_regent` | country a has beacon-regent b (fictional; insert 0020 makes it not functional) | associative | | Brazil has beacon-regent Lyon. |
