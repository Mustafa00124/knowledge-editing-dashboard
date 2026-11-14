# 120-record dev tuning, stage 1: the wide screen (design, 2026-11-14)

Not launched. Stage 1 of the two-stage re-tuning on the new dev split (version 2: 120 records, 60
replace, 30 insert, 30 delete). Stage 1 is a two-level cross of the few settings that matter per
method (the old step 1); stage 2 sweeps one strength setting per method (the old step 3). Why
these settings: `docs/hparam_analysis.md` and `docs/hparam_reference_comparison.md`.

## Decisions (user, 2026-11-13/14)

- All 120 dev records, no split.
- **No early stopping for any method.** Every method runs its full optimisation budget, so the
  budget is the same for all and strength is set by the learning rate (or clamp,
  norm_constraint), not by when a method happens to stop.
- **LoRA and LoCo share one adapter,** so LoCo is LoRA plus the logic loss.
- FiDAL edits the top 1 matrix (top_k 1) with the paper's probing (60 steps, lr 1e-4); bug 17.

## Fixed for every method

| Setting | Value |
|---|---|
| Records, format, protocol | all 120 dev records, chat format, single edit with reset, bf16, seed 0 |
| Optimisation steps | 50, always run in full (FT-M num_steps, LoRA/LoCo num_steps, FiNE epochs, v_num_grad_steps of ROME/AlphaEdit/FiDAL/LTI, each of IFMET's two edits). FiDAL's probe is separate: 60 steps at lr 1e-4 |
| Covariance statistics | Wikipedia, 100k samples, fp32 (shared cache) |
| kl_factor, v_weight_decay | 0.0625, 1e-3 (inert for single edits) |
| mom2_update_weight (MEMIT-type editors) | 5000 |
| Context templates | EasyEdit's defaults, the same for every locate-then-edit method |
| Shared layer window (AlphaEdit, LTI, IFMET's first edit, FiDAL's narrow band) | Qwen L5-9, Olmo L4-8, Llama L3-7, Mistral L2-6 |
| LoRA and LoCo adapter | MLP up/down/gate, rank 8, alpha 16, dropout 0, weight decay 0.01 |

## The screen

Levels are low / high. Qwen has 36 layers, the others 32.

**FT-M** (2 x 2 = 4 runs). Fixed: lr 5e-4, weight decay 0, target = answer + end of turn.

| Factor | Qwen | Olmo, Llama, Mistral |
|---|---|---|
| layer (about 25% / 65% depth) | L9 / L24 | L8 / L21 |
| norm_constraint | 1e-4 / 1e-3 | 1e-4 / 1e-3 |

**LoRA** (2 x 2 = 4 runs) and **LoCo** (2 x 2 = 4 runs), identical levels. LoCo also: constraint
"all", completion weight 1, 3 implications, 30 implication tokens.

| Factor | Qwen | Olmo | Llama | Mistral |
|---|---|---|---|---|
| lr (about the tuned pick / 3 and x 3) | 5e-5 / 5e-4 | 1.5e-5 / 1.5e-4 | 1.5e-5 / 1.5e-4 | 6e-6 / 6e-5 |
| window | L0-17 / L18-35 | L0-15 / L16-31 | L0-15 / L16-31 | L0-15 / L16-31 |

**FiNE** (2 x 2 = 4 runs). Fixed: alpha 1, beta 10, gamma 0.1, last_layer 3 (the authors'),
early_stop_prob off.

| Factor | Qwen, Olmo, Llama | Mistral |
|---|---|---|
| lr | 1e-3 / 1e-2 | 3e-4 / 3e-3 |
| neuron_num | 5 / 20 | 5 / 20 |

**ROME** (2 x 2 = 4 runs). Fixed: v_lr 0.5.

| Factor | Qwen | Olmo | Llama | Mistral |
|---|---|---|---|---|
| layer | L4 / L9 | L2 / L8 | L3 / L8 | L2 / L7 |
| clamp_norm_factor | 2 / 8 | 2 / 8 | 2 / 8 | 2 / 8 |

**AlphaEdit** (2 x 2 x 2 = 8 runs). Fixed: shared window, nullspace_threshold 0.02.

| Factor | All models |
|---|---|
| clamp_norm_factor | 1 / 4 |
| L2 | 0.1 / 10 |
| v_lr | 0.03 / 0.15 |

**FiDAL** (half fraction of 2 x 2 x 2, 4 runs: the corners where v_lr = band x clamp in coded
units). Fixed: top_k 1, probe 60 steps at lr 1e-4, base MEMIT.

| Factor | Qwen | Olmo, Llama, Mistral |
|---|---|---|
| candidate layers | shared window / L2-18 | shared window / L2-16 |
| clamp_norm_factor | 2 / 8 | 2 / 8 |
| v_lr | 0.5 / 5 | 0.5 / 5 |

**IFMET** (2 x 2 = 4 runs). Fixed: clamp 1.2, 3 supporting prompts, first edit on the shared
window, deep layers L18-22 (Qwen L20-24).

| Factor | All models |
|---|---|
| v_lr | 0.06 / 0.6 |
| nll_loss_factor | 1 / 30 |

**LTI** (2 x 2 = 4 runs). Fixed: v_lr 0.5, shared window, midlayers 14 (Qwen 16).

| Factor | All models |
|---|---|
| clamp_norm_factor | 1.2 / 4 |
| loss balance | authors' (nll 0.125, last_kl 0.0725, mid_kl 0.0425) / ours (nll 9, last_kl 0.00725, mid_kl 0.0134) |

## Size and cost

40 runs per model, 160 in all. At the per-edit times measured in step 3 (120 edits per run):
about 120 GPU hours, more where turning off early stopping lengthens the locate-then-edit
methods' value optimisation, and where FiDAL's probe now covers more candidates for 60 steps.
IFMET (about 114 min per run) and LoCo (about 80) are the slow ones. Trims if needed:
AlphaEdit as a half fraction (4 runs), or the screen on 60 of the 120 records.

## Before launch

1. **Turn off early stopping** behind a setting, default unchanged elsewhere:
   - EasyEdit `rome/compute_v.py`, `memit/compute_z.py` (FiDAL, LTI's base),
     `alphaedit/compute_z.py`, `pmet/compute_zs.py` (both loops; IFMET): the `loss < 5e-2` break.
     As a new file in `patches/`.
   - EasyEdit `ft/ft_main.py`: the `loss_meter.avg < 1e-2` break.
   - `portability/lti.py`: the `loss < 5e-2` break.
   - FiNE: `early_stop_prob: null` (config only).
   - LoRA and LoCo have none.
2. Config: the shared adapter for LoCo, the shared window, mom2 5000, 50 steps everywhere.
3. Time a few FiDAL records at top_k 1 with the wide band before the full screen.
4. Write the sweep specs (`design: factorial2`, as step 1) and check the run count and time.
