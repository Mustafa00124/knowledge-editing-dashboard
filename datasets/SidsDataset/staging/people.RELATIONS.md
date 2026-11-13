### People

| Relation | Reads as | Semantics | Tags | Example |
| --- | --- | --- | --- | --- |
| `captained_national_team` | footballer a captained the national football team of country b (many-valued in general, like played_for_national_team; a record that takes one country for granted states it as a presupposition) | associative | `subproperty:played_for_national_team` | Lionel Messi captained the Argentina national football team. |
| `played_for_national_team` | footballer a played for the national football team of country b (many-valued in general: FIFA has let some players represent two countries, e.g. Alfredo Di Stéfano for Argentina and Spain, and allows a one-time switch since 2020; a record that takes one country for granted states it as a presupposition) | associative | | Lionel Messi played for the Argentina national football team. |
| `succeeded_as_pope` | a succeeded b as pope (b was pope immediately before a) | associative | `functional`, `inverse:preceded_as_pope` | Pope Francis succeeded Pope Benedict XVI. |
| `preceded_as_pope` | a preceded b as pope (a was pope immediately before b) | associative | `functional`, `inverse:succeeded_as_pope` | Pope Benedict XVI preceded Pope Francis. |
| `vesper_bound_to` | a is vesper-bound to b (fictional; insert d003 makes it symmetric) | associative | | Jane Austen is vesper-bound to Louis Pasteur. |
