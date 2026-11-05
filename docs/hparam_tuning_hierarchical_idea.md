# Idea for later: hierarchical three-stage tuning

Status: **adopted 2026-11-04** as steps 1-3 after the Latin hypercube screen
(step 0). Step 1 is built (`design: factorial2`, effects view on Results ·
Hyperparameter tuning, specs in `docs/hparam_step1/`); steps 2 and 3 are not
yet. Recorded 2026-11-02 as a possible replacement for the
earlier plan (Latin hypercube screen on 10 edits, then stage-wise on 40 dev
edits). Same methods, models, data and selection rule as the current plan:
9 core methods x 4 instruct models, Sid's dev split, replace edits only, best
rewrite with fluency >= 0.85 of the unedited model. Test is never used.

## The idea in one line

Start wide and shallow, end narrow and deep. Each stage crosses fewer settings
but tries more values for each:

| Stage | Values per setting | Settings crossed together | Answers |
|---|---|---|---|
| 1. Wide | 2 (far apart) | all of the method's settings | which settings matter, which pairs interact, which half of each range is better |
| 2. Interactions | 3 (inside the better half) | small groups of settings that interact (about 3 each) | a good joint value for settings that depend on each other |
| 3. Fine | 8-10 | none: one setting at a time, the rest held at the best so far | the exact value of each setting |

A side benefit is a map of which settings interact for each method and model,
which is a result worth reporting on its own.

## Stage 1: two-level screen over every setting

- **Values:** for each setting, a low and a high value far apart (for example
  default / 10 and default x 10 for rates and weights, the shallowest and
  deepest window for layers). For a setting with categories (LoRA's target
  matrices, LoCo's constraint type), the two most different options.
- **Design:** a two-level factorial. With k settings a full design is 2^k runs.
  That is fine up to 6 settings (ROME: 64 runs, FT-M: 32). Beyond that use a
  fractional factorial of **resolution V**, which still separates every main
  effect and every pairwise interaction, at a fraction of the cost:

  | Settings (k) | Methods | Design | Runs |
  |---|---|---|---|
  | 5 | FT-M | full 2^5 | 32 |
  | 6 | ROME | full 2^6 | 64 |
  | 8 | LoRA, FiNE | 2^(8-2), res V | 64 |
  | 9 | AlphaEdit, FiDAL | 2^(9-2), res VI | 128 |
  | 10 | IFMET, LTI, LoCo | 2^(10-3), res V | 128 |

- **Centre point:** add 2-3 runs with every setting at its middle value.
  A two-level design only sees straight lines; if the centre scores higher than
  every corner, the best value is in the middle, and "keep the better half" is
  wrong for that setting (keep the middle instead).
- **Data:** the 10-edit screen split, as now.
- **Analysis:**
  - main effect of each setting (average score at high minus at low);
  - pairwise interaction effects;
  - a half-normal plot (or Lenth's method) to separate real effects from noise.
  With only 10 edits the rewrite score moves in steps of 0.1, so estimate
  effects on a smoother score (for example the new answer's probability, or
  rewrite + paraphrase together) and still pick winners by rewrite with
  fluency kept.
- **Fluency:** treat it as a second response. A run that breaks fluency is
  marked failed, not scored 0, so it does not fake a large effect.
- **Output:** for each setting, the better half of its range (or the middle,
  per the centre point); settings with negligible effect are frozen at their
  better value from here on; a list of strongly interacting pairs.

## Stage 2: three values, crossed within interacting groups

- **Groups:** draw the strong interactions from stage 1 as a graph (a setting
  is a node, a strong interaction an edge). Each connected cluster is a group.
  Keep groups at 3 settings (27 runs); if a cluster is bigger, either allow 4
  (81 runs) or drop its weakest edge to split it.
- **Values:** 3 values inside the half chosen in stage 1 (its two ends and its
  log midpoint). Categorical settings get all their options here if they are
  in a group.
- **Design:** full 3^g factorial for each group, every other setting held at
  its stage-1 best. Typically 2-3 groups, so 54-81 runs.
- **Data:** 10 screen edits, or 20 if the budget allows.
- **Output:** the best joint value for each group. Settings in no group go
  straight to stage 3.

## Stage 3: one setting at a time, many values

- Same as the current stage-wise sweep, but starting from a much better point.
- 8-10 values per setting, log spaced across the narrowed range from stage 2.
  Only settings that showed a real effect; frozen ones stay frozen.
- Order: where to edit first, then learning rate and steps, then the rest.
  A pair that interacted strongly in stage 1 (typically learning rate x steps)
  can stay a small grid here.
- **Data:** all 40 dev edits.
- **Confirmation:** rerun the winner and the 2-3 runner-ups once more on the 40
  edits, to make sure the winner is not luck.

## Cost

Per method and model, roughly 30-130 runs (stage 1) + 0-81 (stage 2) +
50-100 (stage 3), so about 100-300. Over 36 method/model pairs that is several
thousand runs, clearly more than the current plan (17 screen runs per pair,
then stage-wise). Ways to cut it:

- skip stage 2 for methods with no strong interactions;
- run stages 1-2 on 10 edits and only stage 3 on 40;
- reuse one model's stage-1 interaction map for the others if the four models
  agree.

## Compared with the current plan

| | Latin hypercube + stage-wise (current) | Hierarchical (this idea) |
|---|---|---|
| Interactions | seen indirectly, hard to estimate with 17 runs | measured explicitly in stage 1, then searched in stage 2 |
| Runs | fewer | more |
| Curvature (best value in the middle) | covered, 5 values per setting | needs the centre point in stage 1 |
| Extra result | rough settings importance | importance plus an interaction map per method |

**Possible trigger for switching:** if the Latin hypercube results show the
best settings differ a lot between runs that share most values (a sign of
strong interactions), this plan is the better next step.
