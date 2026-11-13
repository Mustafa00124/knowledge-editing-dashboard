# Scripts behind docs/hparam_analysis.md

Read-only analysis of the tuning runs (nothing is launched). Run from the project root, in order;
intermediate tables go to `$HP_ANALYSIS_DIR` (default `/tmp/hp_analysis`, create it first).
`build.py` takes that directory as its argument and reads runs through `scripts/dash.py`, so the
dashboard must be up.

| Script | Does | Doc section |
|---|---|---|
| `build.py <dir>` | every completed step 0-3 run: full hparams + 8 scores -> `runs.pkl` | data |
| `a1.py` | objective, gate pass/fail columns -> `runs2.pkl` | |
| `a2.py` | step-3 sweep per setting: objective range, passing values, plateau width -> `s3.pkl`, `sens.pkl` | 3 (local) |
| `a3.py` | seed noise from step-2 seed pairs | 6 |
| `a4.py` | step-3 total gain per method x model | 6 |
| `a5.py` | final scores, method/model variance shares, metric correlations, binding gates | 4, 5 |
| `a6.py` | step-1 main effects per setting | 3 (global) |
| `a7.py` | shared value per setting across models | 2 |
| `perrec.py` | per-record pass counts of step 2-3 runs (Generalizability approximate, r 0.92) -> `perrec.pkl` | 6 |
| `boot.py` | record bootstrap of each step-3 pick and split-half optimism | 6 |

The gate-cutoff table (section 4), the strength-curve exchange rates and the record standard error
were one-off snippets over `runs2.pkl`, `s3.pkl` and `perrec.pkl`.
