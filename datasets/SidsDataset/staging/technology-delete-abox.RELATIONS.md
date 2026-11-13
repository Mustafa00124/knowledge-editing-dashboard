### Technology

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `has_dam` | river a has dam b standing on it | associative | `cardinality:many`, `inverse:stands_on_river` | The Yangtze has the Three Gorges Dam standing on it. |
| `console_made_by` | video game console a is made by company b | associative | `functional`, `subproperty:manufactured_by`, `inverse:makes_console` | The PlayStation 2 is made by Sony. |
| `makes_console` | company a makes video game console b | associative | `cardinality:many`, `inverse:console_made_by` | Sony makes the PlayStation 2. |
| `connection_mode_of` | connection mode a (connection-oriented or connectionless) is the connection mode of protocol b | associative | `cardinality:many`, `inverse:connection_mode` | Connection-oriented is the connection mode of TCP. |
