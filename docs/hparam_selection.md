# Hyperparameter selection: how each step's values were chosen

Status: steps 0 and 1 done for 8 methods (AlphaEdit's step 1 launched 2026-11-07); step 2
specs written 2026-11-07. This is the methods record for the paper. The design itself is in
`docs/hparam_tuning_hierarchical_idea.md`; the run lists are in `docs/hparam_step1/` and
`docs/hparam_step2/`; the analysis scripts are noted where used.

## Setting

- **Methods (9):** FT-M, LoRA, ROME, AlphaEdit, FiDAL, FiNE, IFMET, LTI, LoCo.
- **Models (4, instruct):** Qwen3-4B-Instruct-2507, Olmo-3-7B-Instruct, Llama-3.1-8B-Instruct,
  Mistral-7B-Instruct-v0.1. Every method is tuned per model.
- **Data:** Sid's Dataset dev split only (replace edits, single edits). The test split is never
  used for tuning. Steps 0 and 1 use the 10-edit *screen* subset of dev (one ABox fact per
  topic); steps 2 and 3 use all 40 dev edits.
- **Scores (8), per run:** rewrite (the direct question; EasyEdit's reliability), paraphrase,
  generalizability (EasyEdit's portability: determinate derived questions the unedited model
  answered correctly; bug 8 in `docs/bug_log.md`), cross-lingual, propositional consistency,
  specificity (EasyEdit's locality: near and far unrelated questions keep their answers), answer diversity (ROME's and EasyEdit's fluency:
  n-gram entropy, as a ratio to the unedited model, capped at 1) and grammar (the judge's
  well-formed share, as a ratio to the unedited model). Names and their common equivalents:
  `datasets/SidsDataset/README.md`, Evaluation, "Metric names". The **overall score** used in
  the step-1 analysis is the unweighted mean of the 8.
- **Selection rule (final, 2026-11-09; used from step 2 on):** maximise the equal-weight mean of
  the four generalisation scores (paraphrase, generalizability, cross-lingual, propositional
  consistency), among settings that pass hard gates: rewrite >= 0.9, answer diversity >= 0.8 and
  grammar >= 0.9 of the unedited model, and specificity >= 0.7. On our short answers the answer-diversity
  formula (ROME's fluency; n-gram entropy of a record's English answers joined, relative to the unedited model)
  measures answer collapse, not sentence quality: it falls when one answer (usually the new
  one) takes over the record's other questions (6 of 10 answers identical: about 0.76; all
  identical: 0) and does not fall for repetition inside an answer or word salad, which the
  judge's grammar check catches. Collapse inflates paraphrase, generalizability and cross-lingual
  (correlation with answer diversity -0.75, -0.63, -0.83 across step-2 settings), so the diversity gate
  keeps the objective from rewarding it; below 0.8 the specificity gate already binds
  (answer diversity and specificity correlate +0.83). Collapse rises steadily as the score falls
  (share of records with at least half their other answers turned into the new answer, step 2:
  3% at >= 0.95, 10% at 0.90-0.95, 21% at 0.85-0.90, 35% at 0.80-0.85, 46-49% at 0.70-0.80, 57-76%
  below 0.7; only FT-M, LoRA and LoCo fall below 0.8). (First set at a lenient 0.5;
  step 2 showed specificity is mostly high, median 0.81 and 92% of settings >= 0.5, so it was
  raised to 0.7, the strictest value that leaves every method and model that had a passing
  setting with at least one; at 0.75 FT-M and LoRA on Llama have none.)
  Runs that fail a gate keep all their scores; the gates only decide what can be chosen.
  (2026-11-07 interim rule, used for the step-1 analysis: equal-weight mean of all 8 scores,
  specificity considered last.)
- **Diversity and grammar gate (steps 0-1):** a run "keeps fluency" when answer diversity
  (ROME's fluency) >= 0.85 and grammar >= 0.9 of the unedited model. A value is only
  recommended if at least half its runs keep it. ("Fluency" below, in the step 0-1 record,
  means this gate.)
- **Time rule:** a slower value (more steps, more epochs) is kept only if it gains at least
  0.1 rewrite (one more edit out of 10).

## The four steps

| Step | Design | Values per setting | Settings crossed | Edits | Question it answers |
|---|---|---|---|---|---|
| 0 | Latin hypercube | 5 (one draw per stratum) | all at once | 10 | where does the method work at all; which values break it |
| 1 | two-level fractional factorial + 3 centre runs | 2 (low, high) | all | 10 | which settings matter, which pairs interact, which direction is better, is the best inside the range |
| 2 | 3 x 3 grids and short one-setting sweeps | 3 | the one pair that interacts | 40 | the joint value of the settings that depend on each other |
| 3 | one at a time | 8-10 | none | 40 | the exact value of each setting that still matters |

Each step crosses fewer settings than the last but tries more values of each, so the search
narrows from "which half of the range" to "which value".

## Step 0: Latin hypercube screen

- For each method, a list of 5 candidate values per setting spanning the range used in the
  literature and EasyEdit's configs (rates and weights on a log scale, layer windows across
  the depth where the method edits).
- 16 Latin hypercube samples per method and model (each setting's 5 values appear 3-4 times,
  in random combinations) plus one run at the method's default settings: 17 runs, 68 per
  method over 4 models.
- Read per value: mean rewrite, share of runs that keep fluency, and edit time.

## Step 0 to step 1: choosing the low and high values

Each setting gets a low and a high value. Rules, in order:

1. **Far apart.** About 10x apart for rates and weights (for example lr 5e-5 / 5e-4), the
   shallowest and deepest window step 0 tried for layers, and the two most different options
   for a categorical setting (LoRA's attention vs MLP matrices, LoCo's constraint type).
2. **Both inside the working range.** A value where step 0 rarely kept fluency, or rarely
   wrote the edit in, is not used: every run at it would fail and the factorial would learn
   nothing about the other settings. Examples:
   - excluded for breaking fluency: LoRA lr >= 1.5e-3 (no run kept fluency), LoCo lr 3e-3,
     IFMET v_lr 2.0 and clamp >= 12, FiDAL clamp 12 (50% kept), ROME clamp 40;
   - excluded for barely editing: FT-M norm_constraint below 1.5e-4 (rewrite 0.07-0.53), ROME
     clamp 0.4 (rewrite 0.51), FiDAL mom2_update_weight >= 45,000, LoCo completion_weight 0,
     FiNE lr 1e-4; LoRA weight_decay 0 kept only 12% of runs.
3. **Time rule.** 100 optimisation steps cost 1.7-2.1x the run time for LoRA, LoCo, ROME and
   LTI without gaining 0.1 rewrite, so their step counts are capped at 50. FiDAL keeps 100
   (rewrite 0.75 vs 0.30-0.46).
4. **Layers per model,** from the model's depth, its causal-tracing peak
   (`results/investigations/causal_tracing/traced_layers.json`) and the windows step 0 tried.
   FiDAL's band never starts below layer 2 (layer 1 breaks Qwen; bug 10).
5. **Frozen** when step 0 showed no effect: FiDAL's probe_steps and probe_lr, IFMET's
   support_temperature (0.7), LoRA dropout (0), LoCo dropout (0.05).

**Design.** A full 2^k factorial up to 6 settings (FT-M 32 runs, ROME 64); above that the
smallest fraction of resolution V or more (LoRA and FiDAL 2^(7-1), FiNE 2^(8-2): 64 runs),
which separates every main effect and every pairwise interaction. For the 9-10 setting
methods (IFMET, LoCo, AlphaEdit 2^(9-3); LTI 2^(10-4)) a 64-run resolution IV fraction was
chosen for cost: main effects stay clear of pairs, but some pairs share a column with other
pairs. Each design adds **3 centre runs**, every setting at the middle of its two values (log
midpoint for rates and weights, the middle window for layers, the low option for
categorical settings), at seeds 0, 1 and 2. Scripts: `scripts/make_step1_specs.py`,
`dashboard/backend/factorial.py`.

**Step 1 values** (layers are per model; see each spec file):

| Method | Settings, low / high |
|---|---|
| FT-M | layers traced peak / two thirds of depth; lr 1.5e-4 / 1.5e-3; num_steps 12 / 50; norm_constraint 1.5e-4 / 5e-4; weight_decay 0 / 0.01 |
| LoRA | lr 5e-5 / 5e-4; num_steps 12 / 50; rank 4 / 32; lora_alpha 8 / 64; target q,v / up,down,gate; layers first half / second half; weight_decay 0.01 / 0.1 |
| ROME | layers 3 / 7 (Mistral 8); v_lr 0.15 / 5; v_num_grad_steps 12 / 50; kl_factor 0.00625 / 0.625; clamp 1.2 / 12; v_weight_decay 1e-4 / 1e-2 |
| AlphaEdit | layers 2-6 / 6-10; v_lr 0.05 / 0.5; v_num_grad_steps 12 / 50; kl_factor 0.00625 / 0.625; clamp 1.2 / 12; mom2_update_weight 1,500 / 45,000; nullspace_threshold 0.002 / 0.2; L2 0.1 / 10; v_weight_decay 1e-4 / 1e-2 |
| FiDAL | candidate layers 2-8 / 7-13; mom2 1,500 / 15,000; v_lr 0.15 / 5; v_num_grad_steps 25 / 100; top_k 5 / 20; kl 0.00625 / 0.188; clamp 1.2 / 4 |
| FiNE | lr 3e-4 / 3e-3; epochs 25 / 200; neuron_num 2 / 10; alpha 0.1 / 10; beta 3 / 30; gamma 0.01 / 0.1; last_layer 1 / 6; early_stop_prob 0.7 / 0.99 |
| IFMET | v_lr 0.02 / 0.2; v_num_grad_steps 15 / 60; clamp 1.2 / 4; mom2 1,500 / 15,000; kl 0.1 / 3; nll_loss_factor 0.3 / 10; layers 2-6 / 6-10; deep layers 16-20 / step 0's deepest; n_support 2 / 12 |
| LTI | midlayers 13 / 15 (Qwen 15 / 17); last_kl 0.00725 / 0.0725; mid_kl 0.00425 / 0.0425; nll 0.375 / 3; v_lr 0.05 / 0.5; v_num_grad_steps 12 / 50; mom2 1,500 / 15,000; clamp 1.2 / 12; kl 0.00625 / 0.188; layers 2-6 / 6-10 |
| LoCo | lr 9e-5 / 9e-4; num_steps 6 / 50; completion_weight 0.5 / 2; constraint implication / all; n_implications 2 / 12; rank 64 / 256; lora_alpha 4.8 / 48; target attention / attention+MLP; implication_max_new_tokens 15 / 60 |

**AlphaEdit** (added 2026-11-07 with the same rules; it had been held back because each
step-0 run rebuilt its null-space projection, about 30 min): clamp 40 kept fluency in 25% of
runs and 0.4 gave the lowest portability, so 1.2 / 12 as for ROME; v_lr 1.5 and 5 kept 62%
and 58%, so 0.05 / 0.5 (both 100%); 100 grad steps gained only 0.04 rewrite over 12, so the
time rule caps it at 50; mom2_update_weight 150,000 kept 58% and wrote the weakest edits, so
1,500 / 45,000; nullspace_threshold, L2, kl_factor and v_weight_decay kept fluency at both
ends of their step-0 range, which is used whole. The projection is cached per (layers,
threshold), so step 1 needs only 5 projections per model; they are built first in a one-edit
warm-up sweep (`docs/hparam_step1/warmup/`).

## Step 1 analysis

Script: the effects view (`/api/hparams/sweeps/<inv>/<id>/effects`) and `factorial.analyse`.

- **Effects.** With settings coded -1 / +1, a setting's main effect is the mean score at high
  minus the mean at low over the 64 corner runs (32 against 32); a pair's interaction is the
  same contrast on the product column. Computed for each of the 8 scores and the overall
  score, per method and model.
- **Significance.** Lenth's pseudo standard error (Lenth 1989) estimated from all contrasts of
  the design; an effect is *active* beyond the margin of error (t at 0.975, m/3 df) and
  *strong* beyond the simultaneous margin. Only effects of at least 3-4 points are reported.
- **Curvature.** The centre-run mean minus the corner mean, tested against the spread of the 3
  centre runs. A significant positive value means the best setting lies inside the range.
- **Seed noise.** The 3 centre runs differ only in seed. FT-M, LoRA, FiNE, IFMET and LoCo were
  deterministic to within a few points; ROME, FiDAL and LTI moved up to 33 rewrite points
  (they optimise over context prefixes sampled from the model).

### Classifying every setting

Each setting of each method gets one of three calls, from its main effect on the overall score
on the 4 models:

- **Fix:** no effect beyond about 1.5 points on any model. Frozen at its step-1 centre value
  from step 2 on.
- **Pivot:** the same level wins on all 4 models, or on 3 with the fourth flat, and no
  interaction reverses it. Held at that level; if that level was the edge of the step-1 range,
  step 2 tries values past it.
- **Focus:** the models disagree on the sign, or the overall score hides a large trade-off
  (for example +20 paraphrase against -25 specificity). Swept again in step 2.

Results over 8 methods x 4 models: 61 method/setting pairs; 12 flat on every model, 35 with
one direction on every model that shows an effect, 14 where models disagree (about 6 of them
under 3 points). Qwen was the odd model out 8 times, Mistral 7.

### Categories of settings and where interactions occur

Settings fall into three working categories, plus inert ones:

| Category | Settings |
|---|---|
| Where | layers, candidate_layers, midlayers, deep_layers, last_layer, target_modules |
| How hard (incl. hard caps) | lr, v_lr, num_steps, v_num_grad_steps, epochs, lora_alpha, early_stop_prob, neuron_num, clamp_norm_factor, norm_constraint |
| Training signal | nll_loss_factor / nll_factor, LoCo constraint |
| Inert in step 1 | KL weights, weight decay, FiNE alpha/beta/gamma, mom2_update_weight, rank, top_k, LoCo's count settings, n_support |

Share of pairs with a significant interaction (Lenth, at least 3 points), all methods and
models:

| Pair of categories | Overall score | Rewrite |
|---|---|---|
| how hard x how hard | 31% | 48% |
| how hard x where | 9% | 28% |
| signal x how hard | 0% | 6% |
| signal x where | 0% | 0% |
| involving an inert setting | 2-5% | 3-14% (about the false-positive rate) |

Interactions within *how hard* are negative (the settings substitute for each other: one high
already gets most of the gain). Interactions between *how hard* and *where* change the size of
a layer effect, not its sign (FiDAL on Llama: early layers win by about 8 points at clamp 1.2
and by about 50 at clamp 4). The training signal interacts with nothing measurable.

## Step 1 to step 2: choosing the grids

Rules:

1. **Fix** settings are frozen at their step-1 centre value.
2. **Pivot** settings are held at the winning level.
3. **One 3 x 3 grid per method and model** over the pair that matters most: a *where*
   setting crossed with the method's strength dial when the models disagree on where to edit,
   otherwise the two strength settings that interact most. Values are the step-1 low, centre
   and high; a layer setting's three values bracket that model's step-1 winner; a pivot at
   the edge of its range extends past it.
4. **Training-signal settings** are swept one at a time at the grid's centre (they do not
   interact), with the grid's centre cell as their shared run.
5. **One strength dial, not all of them.** Because strength settings substitute, the cheapest
   one that does not cost fluency is held high (LoRA num_steps 50, FiNE epochs 200, ROME and
   LTI grad steps 50) and the one with side effects is gridded.
6. **40 dev edits** (one edit = 2.5 points instead of 10), and **2 seeds** for ROME, FiDAL and
   LTI.

| Method | Grid (3 x 3) | One at a time | Held at pivot | Frozen at centre |
|---|---|---|---|---|
| ROME | layers {2,3,5} (Qwen {5,7,9}) x clamp {1.2, 3.79, 12} | | v_num_grad_steps 50 | v_lr, kl_factor, v_weight_decay |
| FiDAL | clamp x v_lr {0.15, 0.866, 5}; clamp Llama {0.8, 1.2, 2.19}, Mistral and Olmo {2.19, 4, 7.3}, Qwen {1.2, 2.19, 4} (from the single-edit rerun of step 1, bug 14) | | candidate layers 2-8 (Qwen 5-11), mom2 1,500, kl 0.188, grad steps 25 (time rule) | top_k |
| FiNE | lr {0.0015, 0.003, 0.006} x neuron_num {5, 10, 15} (all won high on every model in the single-edit step 1; extended past the edge) | | epochs 200, early_stop_prob 0.99 | last_layer, alpha, beta, gamma |
| FT-M | layers (per model) x norm_constraint {2.74e-4, 5e-4, 1e-3} | | | lr, num_steps (24), weight_decay |
| LoRA | layers {first, middle, second half} x lr {5e-5, 1.58e-4, 5e-4} | | num_steps 50, MLP matrices | lora_alpha, rank, weight_decay |
| LoCo | lr {9e-5, 2.85e-4, 9e-4} x num_steps {6, 17, 50} | constraint "all" | constraint implication, attention matrices | lora_alpha, rank, n_implications, completion_weight, implication tokens |
| IFMET | | v_lr {0.02, 0.0632, 0.2}; nll_loss_factor {3, 10, 30} | clamp 1.2, v_num_grad_steps 60, layers 2-6 | mom2, kl, deep layers, n_support |
| LTI | layers (Llama, Mistral {1-5, 2-6, 4-8}; Olmo, Qwen {2-6, 4-8, 6-10}) x v_lr {0.05, 0.158, 0.5} | nll_factor {1.06, 3, 9} | clamp 1.2, v_num_grad_steps 50, last_kl 0.00725 | midlayers, mid_kl, mom2, kl |
| AlphaEdit | Llama, Mistral: clamp {0.8, 1.2, 3.79} x v_lr {0.016, 0.05, 0.158}. Olmo: clamp {1.2, 3.79, 12} x v_lr {0.016, 0.05, 0.158}. Qwen: v_lr {0.158, 0.5, 1.58} x nullspace_threshold {0.02, 0.2, 0.6} (2 seeds) | | L2 0.1; layers 2-6 (Llama, Mistral) or 6-10 (Olmo, Qwen); grad steps 12, Qwen 50 (time rule); threshold 0.002 (Llama) | kl_factor, mom2_update_weight, v_weight_decay |

Exact values per model: `docs/hparam_step2/README.md` (generated by
`scripts/make_step2_specs.py`).

## Step 2 to step 3: coordinate descent

All 9 methods' step-2 grids (40 dev edits, 472 runs) were scored with the final rule: a cell
qualifies if it passes every gate (rewrite >= 0.9, answer diversity >= 0.8, grammar >= 0.9,
specificity >= 0.7), and qualifying cells are ranked by the objective (equal-weight mean of
paraphrase, generalizability, cross-lingual and logical consistency). Seeds 0 and 1 of the same
cell differed by 1.8 points of objective on average (AlphaEdit 2.7), so gaps under 3 points are
treated as ties.

**Picking the starting value of each gridded setting.** A value does not have to win; it has to
hold up across the other gridded setting. For each level of the other setting we mark the values
that pass the gates and lie within 3 points of the best passing value there; the starting value
is the one marked at the most levels. Two patterns came out:

- Strength settings of FT-M (norm_constraint), LoRA, LoCo and FiNE (lr) are limited by the gates:
  the objective always rises with strength, and specificity (then answer diversity) cuts it off.
  Their starting value is the strongest one that passes; where nothing passed (FT-M, LoRA and LoCo
  on Mistral), a value below the step-2 range.
- ROME, AlphaEdit, FiDAL, IFMET and LTI are limited by rewrite (answer diversity stays near 100);
  rewrite fails most often on Qwen and Mistral. AlphaEdit passed nowhere on Qwen; its best rewrite
  (88) came at the lowest nullspace threshold, so Qwen's strength setting is the threshold.

**Step 3 as coordinate descent.** Every setting is held at its current value and one setting per
method is swept with 8-10 values; its winner (same rule; within 3 points, the value closest to the
current one) becomes the current value and the next setting is swept. The order follows the step-1
interaction structure (interactions sit inside "how hard" and between "how hard" and "where"; the
training signal interacted with nothing): where to edit first, then how hard, then the signal. Of a
substituting pair (learning rate and step count) only one is swept. Settings inert in step 1 stay
frozen.

| Method | Round 1 | Round 2 | Round 3 |
|---|---|---|---|
| FT-M | layer | norm_constraint | lr |
| LoRA | layer window | lr | |
| LoCo | lr | num_steps | |
| ROME | layer | clamp | v_lr |
| AlphaEdit | layer window | clamp (Qwen: nullspace threshold) | v_lr |
| FiDAL | candidate-layer window | clamp | v_lr |
| FiNE | neuron_num | lr | |
| IFMET | edit-layer window | v_lr | nll |
| LTI | layer window | v_lr | nll |

Values: single layers, every layer within 4 of the current one (Llama FT-M, unsettled in step 2,
gets a wide sweep L3-L27); layer windows of the same width slid 1 layer at a time (LoRA's
half-depth windows 2 at a time) up to 4 positions either side; numeric settings 8 values on a
x1.5 log grid around the current value, shifted down or up where the step-2 best sat at the edge
or nothing passed. If a round's pick sits at the edge of the values tried, that setting is swept once more past the edge (up to 4 more values) before the pick is final; if no value passes the gates, the current value is kept and the pick is flagged. One seed per run (noise is under the tie margin); the final settings get extra
seeds once the descent ends. The starting values, the generator and each round's picks are in
`scripts/make_step3_specs.py` and `docs/hparam_step3/state.json`; each round's specs and value
lists in `docs/hparam_step3/round<N>/`; every pick with its scores in `docs/hparam_step3/picks.md`
(the descent advances by itself: `scripts/step3_advance.py`, run every 10 minutes by the dashboard backend).

## Caveats to state in the paper

- The step-1 analysis weighted the 8 scores equally. Under the final rule (specificity a gate at 0.7)
  the strength settings that trade specificity for generalisation (ROME clamp, LoRA lr and alpha,
  FT-M norm_constraint) lean further toward their high value; step 2's grids include both
  ends, so the choice is made on step-2 data.
- Steps 0 and 1 used 10 edits per run; effects under about 5 points are near the noise floor.
- The 64-run fractions for IFMET, LTI, LoCo and AlphaEdit are resolution IV: a few reported
  pairwise interactions may partly be another pair's.
- Soft penalties (KL, weight decay) were inert for single edits; they are designed for
  sequential and batch editing, where they may matter.
