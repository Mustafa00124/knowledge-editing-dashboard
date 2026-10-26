# Scouting reports (2026-10-24)

Can the determinacy edition of Sid's Dataset be built for each topic? One
agent per topic proposed 2 stored and 2 derived edits with evidence
(`<topic>.md`); a second agent then tried to break each report
(`<topic>.review.md`): re-ran counts and quotes, looked for missed routes and
for worlds that break the labels, and marked each record keep, fix or drop.

| Topic | Verdict after review | Records that held up |
| --- | --- | --- |
| geography | feasible | 4 (3 need wording fixes) |
| technology | feasible | 4 (2 need fixes) |
| history | feasible | 4 (Hastings swapped for a backup) |
| literature_arts | feasible | 3, plus 1 needing new indeterminate queries |
| finance | feasible, derived side shaky | 3 (YouTube dropped) |
| people | shaky to feasible | about 3 (Federer/Nadal dropped) |
| physics | shaky to feasible | 3 (muon dropped) |
| biology | shaky, leaning feasible | 4, all needing a fix |
| mathematics | shaky | 1 solid, 1 usable; number facts leave no world |
| grammar | shaky | about 2; agreement edits leave one world |

Caveats: infini-gram AND counts before the helper fix could be false zeros
(every agent re-ran them afterwards); reviewers re-running a scout's exact
query got a cached number, so those re-checks confirm transcription only.
The open design questions these reports raised are in README.md, Determinacy
and belief-revision problems, Open questions. Treat every count and quote as
needing a re-check before it goes into a record.

## Writing the records (2026-10-25)

`records/<topic>.records.md` is each topic writer's account of its 24 records
(12 replace, 12 delete): what it changed from the scouting, worlds it
dropped, remaining doubts. `records/<topic>.records-review.md` is the second
agent's verification: every cited infini-gram count re-run without the cache,
every quote re-fetched, labels attacked, and fixes made in the records.
