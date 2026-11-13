### Technology

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `spindle_routed_to` | board a is spindle-routed to board b (fictional; insert 0015 makes it not transitive) | associative | | The Raspberry Pi 4 is spindle-routed to the Arduino Uno. |
| `spar_cloned_from` | project a is spar-cloned from project b (fictional; insert 0016 makes it not a subproperty of derived_from_source_of) | associative | | Redis is spar-cloned from Memcached. |
| `tine_bound_to` | product a is tine-bound to product b (fictional; insert 0017 makes it asymmetric) | associative | | Nginx is tine-bound to the Apache HTTP Server. |
| `gantry_steward_of` | organisation a is a gantry steward of project b (fictional; insert 0018 makes gantry_stewarded_by its inverse) | associative | | Valve is a gantry steward of Blender. |
| `gantry_stewarded_by` | project a is gantry-stewarded by organisation b (fictional; inverse of gantry_steward_of by insert 0018) | associative | | Blender is gantry-stewarded by Valve. |
| `cresset_keyed_to` | application a is cresset-keyed to module b (fictional; insert 0019 removes the chain with module_provided_by_package) | associative | | Airflow is cresset-keyed to the module sklearn. |
| `has_cairn_curator` | project a has cairn curator b (fictional; insert 0020 makes it not functional) | associative | | Firefox has cairn curator Mozilla. |
