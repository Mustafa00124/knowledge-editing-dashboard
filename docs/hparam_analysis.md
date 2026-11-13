# Hyperparameter tuning: analysis of the finished search (2026-11-13)

What the four tuning steps found, which settings matter, how much the picks depend on the model,
the trade-offs between metrics, and how far the chosen values can be trusted. The design and the
selection rules are in `docs/hparam_selection.md`; the final values are in
`docs/hparam_step3/state.json` (`values`) and every step-3 pick is in `docs/hparam_step3/picks.md`.

**Data.** 4,437 completed tuning runs: step 0 (876 runs, 10 screen edits), step 1 (2,284, 10
edits), step 2 (472, 40 dev edits), step 3 (805, 40 dev edits), 9 methods x 4 instruct models.
Scores, as elsewhere: Rewrite (reliability), Paraphrase, Generalizability (portability: known
determinate derived questions), Cross-lingual, Logical consistency (propositional), Specificity
(locality), Answer diversity (ROME's fluency) and Grammar. **Objective** = mean of Paraphrase,
Generalizability, Cross-lingual and Logical consistency; **gates** = Rewrite >= 0.9, Answer
diversity >= 0.8, Grammar >= 0.9, Specificity >= 0.7. All numbers are percentage points.
Scripts: `docs/hparam_step3/analysis/` (see the README there).

## 1. Summary

1. **Two kinds of method, two kinds of tuning.** For the training methods (FT-M, LoRA, LoCo, and
   less so FiNE) the objective rises steadily with the strength setting (learning rate,
   norm_constraint) while Specificity falls. The pick is just "the strongest value whose
   Specificity is still >= 0.70", so the value is set by the Specificity gate, not by an optimum.
   For the locate-then-edit methods (ROME, AlphaEdit, FiDAL, LTI, IFMET) the curves near the
   chosen values are mostly flat or jagged, and the pick is decided by whether Rewrite lands on
   36 or 35 of 40 edits.
2. **The strength settings are what matter.** In step 1's wide factorial, strength settings
   moved the objective by 6 points on average (Rewrite 11, Specificity 10), layer choice by 4.5,
   training-signal settings by 4, and the regularisers (KL weights, weight decay, mom2, L2, FiNE's
   alpha/beta/gamma, LoCo's implication counts) by 1.6, which is at the noise floor of 10 edits.
3. **The model matters more than the method.** Of the variation in the final objective across
   the 36 method x model cells, 45% is the model, 28% the method, 27% their interaction. Llama is
   the easiest model to edit well (mean 62), Olmo the hardest (49).
4. **One trade-off axis, plus one independent score.** Paraphrase, Generalizability and
   Cross-lingual move together (r 0.71 to 0.79) and against Specificity (r -0.59 to -0.81) and
   Answer diversity. Logical consistency is unrelated to all of them (r with Specificity 0.00):
   no setting buys it.
5. **The method ranking depends on the Specificity gate.** At 0.70 the training methods lead
   (LoRA 63, LoCo 60, FT-M 59). At 0.80 all nine methods sit within 48 to 55 and FT-M drops to 8th;
   at 0.85 FT-M and LoCo fall below every locate-then-edit method.
6. **The per-model values are partly overfitted, the conclusions above are not.** Re-picking on
   resampled records chooses the same value only 45% of the time (a neighbouring value 65%).
   Selection inflates a pick's score by about 2.3 points (split-half), more for the
   locate-then-edit methods (2.7 to 3.9) than for the training methods (0.1 to 1.2). Half the
   final configs sit within one edit or 2 points of a gate. Step 3 changed 23 of its 96 picks and,
   where step 2's starting point already passed, its median gain was 0.
7. **A shared configuration costs little for many settings.** Of 20 swept settings with a value
   tried on several models, 9 have one value that passes the gates on every model with at most
   about 5 points lost (within noise), and 7 more have one that passes on 3 of 4. The exceptions are the training methods' learning rates (LoCo, LoRA, FiNE) and
   FT-M's layer and norm_constraint, which need per-model values, and FiDAL's v_lr.

## 2. Final values, and what can be shared

Final per-model values (step 3). "Shared" is the single value that passes the gates on the most
models with the smallest loss, from the step-3 sweeps (other settings held at each model's own
values); the loss is against that model's best passing value, single runs, so under about 4 is
noise.

| Method | Setting | Qwen | Olmo | Llama | Mistral | Shared value: passes on, worst loss |
|---|---|---|---|---|---|---|
| FT-M | layer | 24 | 20 | 16 | 7 | none tried in common; per model |
| | norm_constraint | 1e-3 | 1e-3 | 2.74e-4 | 1e-4 | none in common. Olmo and Qwen are flat from 1e-3 up (the constraint stops binding); Llama and Mistral are steep |
| | lr | 7.11e-4 | 4.74e-4 | 4.74e-4 | 4.74e-4 | **4.74e-4: 4/4, 4.1** |
| | num_steps, weight_decay | 24, 0.005 | same | same | same | inert in step 1 |
| LoRA | layer window | 9-26 | 16-31 | 0-15 | 0-15 | none in common; Llama, Mistral and Olmo picks are at the end of the usable range |
| | lr | 1.58e-4 | 5e-5 | 5e-5 | 2e-5 | 4.5e-5: 3/4 (Mistral fails Answer diversity), 5.0 |
| | MLP up/down/gate, rank 11, alpha 23, 50 steps, dropout 0 | | | | | shared by design |
| LoCo | lr | 2.03e-4 | 9e-5 | 6e-5 | 2e-5 | 4e-5: 3/4, **25.6**. Not shareable |
| | num_steps | 50 | 50 | 50 | 50 | **50: 4/4, 1.3** |
| FiNE | neuron_num | 15 | 15 | 15 | 10 | **12: 4/4, 2.6** |
| | lr | 6e-3 | 6e-3 | 3e-3 | 1.5e-3 | 2.25e-3: 3/4 (Mistral fails Answer diversity), 6.6 |
| ROME | layer | 8 | 2 | 5 | 4 | 4: 3/4 (Qwen fails Rewrite), 5.0 |
| | clamp_norm_factor | 3.79 | 3.79 | 5.69 | 12 | **3.56: 4/4, 9.6** (Mistral; others <= 3.2) |
| | v_lr | 0.866 | 0.866 | 1.3 | 0.866 | **0.866: 4/4, 4.6** |
| AlphaEdit | layer window | 5-9 | 8-12 | 3-7 | 2-6 | start 2: 2/4 |
| | clamp_norm_factor | 3.79 | 3.79 | 3.79 | 1.2 | 1.12: 3/3, 12.0 (Olmo) |
| | v_lr | 0.158 | 0.158 | 0.05 | 0.05 | 0.158: 2/4 |
| FiDAL | candidate layers | 5-11 | 4-10 | 2-8 | 1-7 | start 1: 3/4, 8.2 |
| | clamp_norm_factor | 2.19 | 3.29 | 3.29 | 2.19 | **2.19: 4/4, 4.3** |
| | v_lr | 0.866 | 0.15 | 0.866 | 5 | none: Mistral needs >= 5 for Rewrite, Olmo fails Rewrite above 0.15 |
| IFMET | layer window | 2-6 | 4-8 | 2-6 | 2-6 | start 3: 3/4, 3.7 |
| | v_lr | 0.675 | 0.0632 | 0.2 | 0.2 | 0.089: 3/4 (Qwen fails Rewrite), 1.8 |
| | nll_loss_factor | 30 | 30 | 30 | 30 | **20: 4/4, 1.3** |
| LTI | layer window | 8-12 | 4-8 | 3-7 | 4-8 | **start 3: 4/4, 5.1** |
| | v_lr | 2.53 | 0.5 | 0.5 | 0.5 | **2.53: 4/4, 2.5** |
| | nll_factor | 5 | 9 | 9 | 9 | **40: 4/4, 2.5** (flat) |

**Reading this.**

- **LTI and IFMET** are insensitive to everything in step 3; one configuration for all models is
  as good as the per-model picks.
- **ROME** works with what are essentially EasyEdit's defaults (EasyEdit: layer 5, v_lr 0.5,
  clamp 4 for every model). Exceptions: Mistral wants a larger clamp (12) and Qwen, which has 36
  layers, a deeper layer (8).
- **FT-M, LoRA and LoCo** need their strength setting set per model. Their good learning rates
  differ about 10x across models, and the curves are steep (LoCo: up to 26 points lost with a
  shared rate). What does transfer is the *operating point*: tune the strength until Specificity
  reaches a target (0.70 now). See section 4.
- **Mistral is the usual odd one out.** It has the shallowest FT-M layer (7), the largest ROME
  clamp (12), the largest FiDAL v_lr (5) and the lowest learning rates for LoRA and LoCo. It is
  also the model where Answer diversity (answer collapse) binds first for the training methods.
  Mistral-7B v0.1 is the oldest of the four models.
- **AlphaEdit** has the least stable picks: a Rewrite gate decided by one edit, and only 1 or 2
  passing values per sweep on most models.

**Against EasyEdit's LoRA default** (lr 5e-3, q/v matrices, 70 steps): our learning rates are
30 to 250 times lower. In step 0, lr >= 1.5e-3 never kept fluency. Papers that run LoRA with
EasyEdit's default are at a very different point on the Specificity trade-off.

**Layers and causal tracing.** ROME's chosen layer matches the causal-tracing peak on Llama (5).
On Olmo the peak (7) scores 9 points below the chosen layer 2, and on Qwen the peak (5) scores
7 below layer 8. As in Hase et al. (2023), where a fact is localised does not predict where
editing it works best.

## 3. Which settings matter

### Globally (step 1, two far-apart levels, all other settings crossed)

Mean absolute effect on the objective over the 4 models (high minus low level), and on how many
models the sign agrees (effects under 1.5 not counted). Settings with an effect >= 5 or a clear
Rewrite or Specificity effect:

| Method | Setting | Objective effect | Sign agrees | Notes |
|---|---|---|---|---|
| LoCo | lr | 20.8 | 4/4 | also Specificity -45, Answer diversity -33 |
| | num_steps | 14.9 | 4/4 | |
| | lora_alpha | 9.0 | 3/4 | |
| | constraint (all vs implication) | 6.3 | 4/4 | "all" better |
| LoRA | lr | 17.8 | 4/4 | Specificity -23 |
| | lora_alpha | 12.8 | 4/4 | |
| | target modules | 9.0 | 4/4 | MLP better than q/v |
| | weight_decay, rank | 6.2, 5.5 | 4/4 | lower is better for both |
| FT-M | layer | 12.1 | 2/4 | models disagree on direction |
| | norm_constraint | 11.9 | 4/4 | Specificity -13 |
| FiNE | lr, neuron_num, early_stop_prob | 9.7, 7.8, 6.1 | 4/4 each | |
| ROME | clamp_norm_factor | 8.5 | 4/4 | Specificity -18 |
| | v_num_grad_steps | 2.3 | 3/4 | Rewrite +20, gate pass rate +43 |
| IFMET | nll_loss_factor | 6.2 | 4/4 | |
| | v_lr | 5.3 | 3/4 | |
| FiDAL | candidate layers | 5.7 | 3/4 | earlier better |
| | clamp_norm_factor | 5.6 | 3/4 | Specificity -13 |
| AlphaEdit | clamp_norm_factor, v_lr | 5.3, 5.1 | 2/4 | Rewrite 17 and 28 |
| LTI | clamp_norm_factor | 5.0 | 4/4 | Specificity -17 |

**Inert (< 1.5 on the objective):** all KL weights, v_weight_decay, AlphaEdit's
mom2_update_weight, FiNE's alpha, beta and gamma, LTI's midlayers and mid_kl, LoCo's
n_implications and implication tokens, FT-M's num_steps (once norm_constraint is set), FiDAL's
v_num_grad_steps. These were designed for sequential or batch editing; for single edits they do
nothing measurable.

### Locally (step 3, 8 to 10 values around the step-2 pick, everything else held)

A setting with no effect would still show an objective range of about 3.6 points across 8 values
from seed noise alone (per-run SD 1.3, section 6).

- **Still sensitive near the optimum:** the training methods' strength settings. Objective range
  across values: LoCo lr 42 to 58, LoRA lr 34 to 43 (Qwen 6), FT-M norm_constraint 30 and 52 on
  Llama and Mistral (6 to 7 on Olmo and Qwen, where it stops binding). Also LoCo num_steps 25 to
  42, ROME clamp 13 to 15 (Olmo 9), FiDAL clamp 7 to 20.
- **Layers:** 8 to 16 across the window for most methods. The large values are mostly where an
  edge window fails Rewrite (LTI on Qwen 28, FiDAL on Qwen 26).
- **Near the noise floor:** IFMET everything (3 to 11, or 17 for Qwen's layers where nothing
  passed; 1 to 9 among passing values), LTI v_lr and nll_factor (2 to 12), AlphaEdit's clamp on Llama (2), FiDAL v_lr
  on Mistral (4, across a 17x range), FT-M lr on Llama and Mistral (3).

## 4. The two regimes and the trade-off curves

**Training methods: a frontier, not an optimum.** Along the strength setting, the objective and
Specificity trade at a near-fixed rate: about 1 objective point per Specificity point for FT-M
(median 0.9), LoRA (1.1) and LoCo (1.3), r around -0.95. FiNE is 0.3. Example, LoRA on Llama:

| lr | 2.2e-5 | 3.3e-5 | 5e-5 | 7.5e-5 | 1.1e-4 |
|---|---|---|---|---|---|
| Objective | 62 | 65 | 69 | 72 | 71 |
| Specificity | 76 | 75 | 75 | 70 | 62 (fails) |

The gate picks where the curve is cut. The final Specificity of the training methods is 70.0 to
75.0 in 14 of 16 cells (FT-M on Llama and Olmo, and LoRA on Qwen, are exactly at 70).

**Locate-then-edit methods: rewrite-limited plateaus.** Answer diversity stays at 91 to 100 and
Specificity at 72 to 88. The binding gate is Rewrite. Of the step 2 and 3 runs, 50% of AlphaEdit's
fail Rewrite and nothing else, as do 42% of FiDAL's and 27 to 28% of ROME's, IFMET's and LTI's.
With 40 edits (39 to 40 scored), the 0.9 gate is 36 edits, so one edit decides it. Within the
passing region the curves are flat, so the pick is close to arbitrary. Their Objective/Specificity
exchange rate is 0.0 to 0.6.

**The gates in practice:**

- **Grammar** was never the only gate a run failed (0% for every method). It is redundant with
  Answer diversity and Specificity.
- **Answer diversity** binds only for the training methods, and mostly on Mistral (final values
  81 to 83 for FT-M, LoCo, LoRA).
- **Specificity** binds for FT-M, LoRA, LoCo and FiNE (11 to 20% of runs fail on it alone).
- **Rewrite** binds for the five locate-then-edit methods.

**How the ranking depends on the Specificity gate** (best passing objective over all step 2 and 3
runs, mean over models; number of models with a passing run in brackets where under 4):

| Specificity >= | 0.60 | 0.70 (used) | 0.75 | 0.80 | 0.85 |
|---|---|---|---|---|---|
| LoRA | 64 | 63 | 60 | 55 | 48 (2) |
| LoCo | 63 | 60 | 58 | 52 | 40 |
| FT-M | 62 | 59 | 58 | 48 | 41 |
| FiNE | 60 | 59 | 56 | 54 (1) | 50 (1) |
| IFMET | 58 | 58 | 57 | 53 (3) | 51 (3) |
| FiDAL | 56 | 56 | 56 | 54 | 51 |
| ROME | 53 | 53 | 52 | 50 | 49 |
| LTI | 52 | 52 | 52 | 52 | 52 |
| AlphaEdit | 50 | 50 | 50 | 48 | 47 |

(These are maxima over every run, so slightly higher than the step-3 picks.) LTI does not move at
all: its Specificity is always about 0.85. A headline "LoRA beats ROME by 10 points" is true at
0.70 and false at 0.80. The data to show each method's whole frontier (objective against
Specificity) already exists in the step 2 and 3 runs; that is a fairer figure than one point per
method.

## 5. Variation between models and methods

Final objective (step 3), and the spread:

| | Llama | Mistral | Olmo | Qwen | Spread across models |
|---|---|---|---|---|---|
| LoRA | 69.3 | 59.7 | 56.4 | 61.6 | 13 |
| IFMET | 70.7 | 53.9 | 51.3 | 50.3 | 20 |
| LoCo | 65.1 | 53.0 | 49.2 | 64.0 | 16 |
| FiDAL | 64.1 | 55.9 | 47.6 | 48.9 | 17 |
| FT-M | 59.2 | 62.1 | 55.7 | 53.9 | 8 |
| FiNE | 59.0 | 60.8 | 56.7 | 54.1 | 7 |
| ROME | 61.8 | 59.6 | 39.8 | 46.5 | 22 |
| AlphaEdit | 58.2 | 50.2 | 44.9 | 43.3 | 15 |
| LTI | 54.6 | 53.7 | 38.1 | 53.0 | 17 |
| Spread across methods | 16 | 12 | 19 | 21 | |

Share of the variation across the 36 cells (two-way decomposition):

| Score | Method | Model | Interaction |
|---|---|---|---|
| Objective | 0.28 | **0.45** | 0.27 |
| Rewrite | **0.61** | 0.18 | 0.21 |
| Paraphrase | 0.45 | 0.19 | 0.35 |
| Generalizability | 0.22 | **0.48** | 0.30 |
| Cross-lingual | **0.70** | 0.11 | 0.20 |
| Logical consistency | 0.29 | **0.45** | 0.26 |
| Specificity | **0.61** | 0.12 | 0.28 |
| Answer diversity | **0.68** | 0.23 | 0.09 |

- **Method-driven:** Cross-lingual, Rewrite, Specificity and Answer diversity are mostly about
  how the method edits. The training methods reach Cross-lingual 61 to 70, the
  locate-then-edit methods 36 to 49.
- **Model-driven:** Generalizability and Logical consistency, the two reasoning scores. Llama
  leads on both (52 and 65); Olmo is weakest on Generalizability (34). Whether an edit
  propagates to derived facts depends more on the model than on the editor.
- **Interactions are large (27%).** The clearest case is the locate-then-edit methods on Olmo:
  ROME 40, LTI 38, AlphaEdit 45, all with Cross-lingual of 21 to 33, while the training methods
  on Olmo stay at 49 to 57.

Method profiles (final values, mean over models):

| | Rewrite | Paraphrase | Generalizability | Cross-lingual | Logical | Specificity | Answer diversity |
|---|---|---|---|---|---|---|---|
| Training (LoRA, LoCo, FT-M, FiNE) | 98 to 99 | 75 to 78 | 34 to 49 | 61 to 70 | 48 to 53 | 72 to 75 | 85 to 89 |
| Locate-then-edit (ROME, AlphaEdit, FiDAL, LTI, IFMET) | 93 to 96 | 61 to 73 | 37 to 48 | 36 to 49 | 56 to 61 | 80 to 87 | 97 to 99 |

The locate-then-edit methods are better on Logical consistency (by about 8) and Specificity (by
about 10); the training methods on Cross-lingual (by about 25) and Paraphrase (by about 10).
Generalizability is about the same.

## 6. How far the values can be trusted

**Noise sources, measured.**

- **Seed:** the same step-2 config run on seeds 0 and 1 (152 pairs, ROME, AlphaEdit, FiDAL, LTI)
  differs by 2.0 objective points on average. That is a per-run SD of about 1.3, and 5 points
  on Paraphrase alone on average. In 18% of these pairs one seed passes the gates and the other
  does not.
- **Records:** bootstrapping the 40 records gives the objective a standard error of 4.2 points
  (the same for every method). For an absolute score this is the dominant error: about +-8 for
  95%. Comparisons between configs on the same records are paired and much tighter, but two
  methods' final scores need to differ by more than about 6 before the order is reliable.

**Do the picks replicate?** For each step-3 sweep (96 of them):

- **Bootstrap over records:** the same value wins in 45% of resamples (median 41%), and a value
  within one grid step of it in 65%. By method: LoCo 69%, LoRA 53%, all others 39 to 46%. These
  numbers use the plain "best passing value" rule; the real rule (within 3 points, keep the value
  closest to the current one) is stickier, so these are lower bounds on how often it would repeat.
- **Split-half:** choosing on 20 records and scoring on the other 20 loses 2.3 points on
  average. By method: ROME 3.9, LTI 3.6, FiDAL 2.9, IFMET 2.7, AlphaEdit 2.7, FT-M 1.2, FiNE 1.2,
  LoRA 0.7, LoCo 0.1. With 40 records the loss is about 0.7x that.
- **Step 3's total gain:** where step 2's starting configuration already passed (27 of 36 pairs),
  the median gain was 0 and the mean 1.9. The real gains were all in a few pairs, mostly on Qwen:
  LTI +12, LoCo +9, ROME +7.5, FiDAL on Olmo +7, ROME on Llama +6. Step 3 kept the current value
  in 73 of its 96 picks.
- **Margins:** 18 of the 36 final configs are within one edit of the Rewrite gate (9), within 2
  points of the Specificity gate (6), or within 3 of the Answer diversity gate (3); none at
  more than one. On new records
  roughly half of these would fall on the other side of a gate. That says nothing bad about the
  configs; it says "passes every gate" is not a stable property at these margins.

**Shift to the new data.** Tuning used the old 40-record dev set: replace edits only, old record
layout (ids like `biology-replace-0005`). The dev split now (version 2, committed today) is 120
new records, 60 replace, 30 insert and 30 delete, and none of their ids overlap with the tuning
records. Insert and delete edits were never tuned on. For the training methods, where the pick is
"where Specificity crosses 0.70", a different mix of records moves that crossing directly.

Everything here is also single-edit. The regularisers that were inert here (KL, weight decay,
mom2, L2) exist for sequential and batch editing, so these values say nothing about those
protocols.

**What is robust, and what is not.**

| Likely to hold | Likely overfitted to these 40 records |
|---|---|
| Which settings matter and which are inert (step 1, sign agrees on 4/4 models for most) | The exact layer and v_lr picks of the locate-then-edit methods (flat curves, bootstrap repeat about 40%) |
| The direction of each strength effect (more strength: higher Objective, lower Specificity) | Final scores as absolute levels (about 2 to 4 points optimistic for locate-then-edit, about 1 for training) |
| Method profiles: training methods high Cross-lingual, locate methods high Specificity and Logical consistency | Which configs pass which gate (half are at a margin) |
| Model ordering (Llama easiest, Olmo hardest) and the Olmo x locate-then-edit weakness | Gaps under about 6 points between methods on one model |
| Learning-rate scale per model for LoRA and LoCo (steep curves, bootstrap repeat 50 to 96%) | The exact training-method strength values (set by where Specificity crosses 0.70, which moves with the data) |

## 7. Recommendations

1. **Validate before the main runs.** Run the 36 final configs on the new 120-record dev split
   with 2 seeds (about 28 GPU hours per seed at the measured per-edit times). This gives honest
   absolute scores, shows how much the picks lose on new records (expected about 2 to 4 points),
   and tests insert and delete edits, which were never tuned.
2. **Report the Specificity frontier, not one point.** Either plot Objective against Specificity
   per method from the step 2 and 3 runs, or report at two gates (0.70 and 0.80). The training vs
   locate-then-edit ranking flips between them.
3. **For the training methods, calibrate to a target, not a value.** A per-model learning rate
   that reaches a common Specificity (for example 0.75) transfers across models and data; a fixed
   learning rate does not (LoCo loses up to 26 points with a shared one).
4. **For the locate-then-edit methods, prefer the shared configuration** where section 2 shows
   one (ROME, IFMET, LTI, FiDAL's clamp). It is as good within noise, simpler to report, and less
   overfitted than per-model picks that won by one edit.
5. **Simplify the gates.** Grammar never decided a run alone. For Rewrite with 40 edits, report
   the gate as a count (36 of 40) so readers see that one edit decides it, or use more edits for
   gate decisions.
6. **Fix the inert settings at the literature defaults** and say so in the paper (section 3); for
   single edits they do not matter.
