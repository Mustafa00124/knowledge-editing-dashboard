# Our tuned hyperparameters against published ones (2026-11-13)

For each method: what the authors' released configs, their papers, and EasyEdit set, next to what
our tuning found (`docs/hparam_step3/state.json`), whether the two agree, and what that implies
for the 120-record dev validation. Our tuning analysis is in `docs/hparam_analysis.md`.

Model order for our values: **Qwen3-4B / Olmo-3-7B / Llama-3.1-8B / Mistral-7B-v0.1** (all
instruct). Verdicts: **agrees**, **near** (same order of magnitude or a neighbouring layer, within
our noise), **differs**, **n/a** (no comparable reference).

## Sources

| Method | Reference used | Closest model there |
|---|---|---|
| FT-M | EasyEdit `hparams/FT/{llama3-8b,mistral-7b,qwen2.5-7b}.yaml`; LocFT (Yang et al. 2025, arXiv 2509.22072, github.com/ICT-STAR/LocFT) | Llama-3-8B(-Instruct), Mistral-7B, Qwen2.5-7B |
| LoRA | EasyEdit `hparams/LoRA/{llama3-8b,llama3.1-8b,qwen2.5-7b}.yaml` | Llama-3/3.1-8B, Qwen2.5-7B |
| ROME | EasyEdit `hparams/ROME/{llama3-8b,mistral-7b,qwen2.5-7b}.yaml` | same three |
| AlphaEdit | authors' repo `jianghoucheng/AlphaEdit/hparams/AlphaEdit/Llama3-8B.json`; EasyEdit `AlphaEdit/{llama3-8b,qwen2.5-7b}.yaml` | Llama-3-8B, Qwen2.5-7B |
| FiDAL | paper (ACL 2026, aclanthology.org/2026.acl-long.957); no code | GPT-J, Qwen2.5-7B-Instruct, Llama-3-8B-Instruct |
| FiNE | authors' repo `opanhw/FiNE/hparams/FINE/llama3-8b.yaml` (also in `external/FiNE`) | Llama-3-8B |
| IFMET | paper (arXiv 2410.06331, App. D.2, E.2); no code; base editor PMET (EasyEdit `PMET/llama-7b.yaml`) | GPT-J only |
| LTI | authors' repo `Acruxos/EVOKE/experiment/hparams/MEMIT-LTI/llama-2-7b.json` | Llama-2-7B |
| LoCo | authors' repo `ddidacus/loco-llm/configs/train_{llama,mistral}.json` | Llama-3.1-8B (base), Mistral-7B-Instruct-v0.1. Upstream *trains* on BeliefBank for 5 epochs; it is not an editor, so its rates are not directly comparable |

Independent work used below: LocFT (re-tuned FT's layer and rate on 7-8B models, found inherited
layers suboptimal), Hase et al. 2023 (causal tracing does not predict the best edit layer),
Gangadhar & Stratos 2024 (properly set-up fine-tuning matches dedicated editors), The Mirage of
Model Editing (ACL 2025: teacher-forced evaluation inflates single-edit success, 96.8% vs 38.5%
under realistic generation). No independent study benchmarks LoRA learning rates for fact editing.

## Method by method

### FT-M

| Setting | Reference | Ours | Verdict |
|---|---|---|---|
| lr | 5e-4 (EasyEdit, all models; LocFT for Llama and Qwen) | 7.1e-4 / 4.7e-4 / 4.7e-4 / 4.7e-4 | **agrees** |
| num_steps | 25 | 24 | **agrees** |
| layer | EasyEdit 21 (Llama-3, Mistral), 27 (Qwen2.5); LocFT 22 (Llama-3-Instruct), 23 (Mistral), 6 (Qwen2.5) | 24 / 20 / 16 / **7** | Llama **near** (our L19-21 are within 2 points of L16); Mistral **differs**, and our step-3 sweep covered only L4-12, so L21-23 was never tested at 40 edits |
| norm_constraint | off (Llama-3, Qwen2.5), 5e-5 (Mistral) | 1e-3 / 1e-3 / 2.7e-4 / 1e-4 | **near** for Olmo and Qwen (flat above 1e-3, effectively off); Llama and Mistral need it to pass Specificity |
| objective | EasyEdit FT = prompt_last (FT-L) | target_new (FT-M) | by design |

### LoRA

| Setting | Reference (EasyEdit) | Ours | Verdict |
|---|---|---|---|
| lr | 5e-3 | 1.6e-4 / 5e-5 / 5e-5 / 2e-5 | **differs, 30-250x lower** |
| matrices | q_proj, v_proj | up, down, gate (MLP) | **differs** |
| rank / alpha / dropout | 8 / 32 / 0.1 | 11 / 23 / 0 | near (step 1: rank 4 beat 32 by 5.5 on all 4 models; alpha higher is better) |
| steps | 50-70 | 50 | agrees |
| layers | all | half-depth windows (Llama, Mistral first half; Olmo second; Qwen middle) | differs (step 1: 7 points; models disagree on which half) |

Justification to state: in step 0, no run with lr >= 1.5e-3 kept fluency; at our gates the
default over-edits (answer collapse, Specificity far below 0.7). MLP matrices beat q/v by 9
points on all 4 models in step 1. Indirect support: LoCo's 3e-4 on all linear layers and LocFT's
5e-5 to 5e-4 are both far below 5e-3.

### ROME

| Setting | Reference (EasyEdit, same for every model) | Ours | Verdict |
|---|---|---|---|
| layer | 5 | 8 / 2 / **5** / 4 | Llama **agrees**, Mistral **near**, Olmo near (L1-L4 flat), Qwen differs (36 layers; L5 is 7 points below L8) |
| clamp_norm_factor | 4 | 3.79 / 3.79 / 5.69 / 12 | **agrees** except Mistral (12) |
| v_lr | 0.5 | 0.87 / 0.87 / 1.3 / 0.87 | near (flat: 3-7 points over 8 values) |
| v_num_grad_steps | 25 | 50 | differs (step 1: 50 steps added 10-31 Rewrite) |
| kl_factor | 0.0625 | 0.0625 | agrees |

Our results support EasyEdit's ROME defaults. Hase et al. agree with our finding that the
causal-tracing peak is not the best edit layer (it is on Llama, not on Olmo or Qwen).

### AlphaEdit

| Setting | Authors (Llama-3-8B) | EasyEdit | Ours | Verdict |
|---|---|---|---|---|
| layers | 4-8 | 4-8 | 5-9 / 8-12 / 3-7 / 2-6 | Llama **near**; Olmo deeper |
| v_lr | 0.1 | 0.1 (Llama), 0.5 (Qwen2.5) | 0.16 / 0.16 / 0.05 / 0.05 | **near** |
| v_num_grad_steps | 25 | 25 | 50 / **12 / 12 / 12** | **differs** (our time rule capped it; we are Rewrite-limited) |
| clamp_norm_factor | 0.75 | 0.75 (Llama), 4 (Qwen2.5) | 3.79 / 3.79 / 3.79 / 1.2 | **differs** from the authors; 0.8 was in step 2's grid for Llama and Mistral and lost |
| L2 | 10 | 1 or 10 | 0.1 | **differs** (step 1: lower L2 better on 3 of 4 models, Rewrite 11) |
| nullspace_threshold | 0.02 | 0.02 | 0.02 (Llama 0.002) | **agrees** |
| mom2_update_weight / v_weight_decay | 15000 / 0.5 | 15000 / 0.5 or 1e-3 | 8220 / 1e-3 | differs, both inert in step 1 |

The authors' setting is a weak, heavily regularised edit (small clamp, L2 10), designed for
sequential editing of thousands of facts. For single edits at our Rewrite gate it under-edits.
That is a defensible difference, but the 12-step cap is not defended by anything except time.

### FiDAL

| Setting | Paper | Ours | Verdict |
|---|---|---|---|
| candidates | every FFN linear matrix, all layers | the base editor's down_proj, 7-layer window: 5-11 / 4-10 / 2-8 / 1-7 | differs (forced: closed-form editors here write only down_proj) |
| top_k (matrices edited) | **1 or 2** | **10** | **differs, and it disables FiDAL**: 10 >= the 7 candidates, so every candidate layer is edited and the locating step chooses nothing. The tuned "FiDAL" is MEMIT on a fixed window (mom2 1500, kl 0.188, clamp 2.2-3.3, v_lr 0.15-5) |
| probe steps / lr | T = 60, lr 1e-4 | 10 / 0.01 | **differs**. `dynamic/fidal.py` says the paper does not state these; it does (to re-check in the PDF and correct the docstring) |
| base editor | ROME, MEMIT, AlphaEdit or UnKE | MEMIT | n/a |

top_k looked inert in step 1 (5 vs 20 candidates moved the objective 1.4) and was frozen at the
middle value, 10, which happens to exceed the window. **Our FiDAL numbers should not be reported
as FiDAL until a run with top_k 1-2 exists.**

### FiNE

| Setting | Authors (Llama-3-8B) | Ours | Verdict |
|---|---|---|---|
| lr | 1e-3 (Llama-2: 5e-3) | 6e-3 / 6e-3 / 3e-3 / 1.5e-3 | **differs, 1.5-6x higher** |
| neuron_num | 5 | 15 / 15 / 15 / 10 | **differs, 2-3x more** |
| epochs | 50 | 200 | differs |
| early_stop_prob | 0.9 | 0.99 | differs |
| alpha / beta / gamma | 1 / 10 / 0.1 | 1 / 9.5 / 0.03 | agrees (inert) |
| last_layer | 3 | 2 | near (small effect) |

Every difference points the same way: a stronger edit. Step 1 found higher lr, more neurons and
a higher stop probability better on all 4 models. The authors stop optimising once the new
answer reaches probability 0.9, which suits Rewrite but leaves paraphrase and cross-lingual
questions unedited. (Our hparams comment says upstream ships identical values for all models;
its Llama-2 file uses lr 5e-3.)

### IFMET

| Setting | Paper (GPT-J) / PMET base | Ours | Verdict |
|---|---|---|---|
| shallow layers | 3-8 of 28 | 2-6 / 4-8 / 2-6 / 2-6 of 32-36 | **near** |
| deep layers | 16-20 of 28 | 20-24 / 18-22 / 18-22 / 18-22 | **agrees** (same relative depth, by construction) |
| lr | 0.2 | 0.68 / 0.063 / 0.2 / 0.2 | Llama and Mistral **agree**; the others are within a flat region |
| max steps | 30 | 60 | differs (small effect) |
| preservation weight (lambda / mom2) | 6000 | 4740 | **near** |
| supporting prompts | 1-5 | 5 | agrees |
| clamp | not stated; PMET base 1 | 1.2 | near |
| nll_loss_factor | PMET base 1 | 30 | **differs, 30x** (step 1: higher better on all 4 models, +6 points) |
| kl_factor | PMET base 0.0625 | 0.55 | differs, inert |

Our IFMET is close to the paper apart from the much stronger NLL term.

### LTI

| Setting | Authors (MEMIT-LTI, Llama-2-7B) | Ours | Verdict |
|---|---|---|---|
| layers | 4-8 | 8-12 / 4-8 / 3-7 / 4-8 | **agrees** except Qwen |
| clamp_norm_factor | **4** | **1.2** | **differs**; frozen after step 1 under the old 8-score rule, never swept in steps 2-3, with 15 points of Specificity unused |
| v_lr | 0.5 | 2.53 / 0.5 / 0.5 / 0.5 | agrees except Qwen |
| v_num_grad_steps | 30 | 50 | near |
| nll_factor | 0.125 | 5 / 9 / 9 / 9 | **differs, 40-70x** |
| last_kl_factor | 0.0725 | 0.00725 | **differs, 10x lower** |
| mid_kl_factor | 0.0425 | 0.0134 | differs, 3x lower |
| midlayers | 15 of 32 | 14 (Qwen 16) | agrees |

LTI's idea is a KL term that makes the edited model imitate the model with the fact in context.
Ours has moved to an NLL-dominated balance (NLL up 40-70x, the output KL down 10x) with a low
clamp, which makes it behave like a cautious MEMIT. This plausibly explains why LTI did not beat
plain locate-then-edit methods, and it is the largest gap between our config and an author's.

### LoCo

| Setting | Authors (training on BeliefBank) | Ours (single-edit) | Verdict |
|---|---|---|---|
| LoRA rank / alpha / dropout | 128 / 16 / 0.05 | 128 / 15.2 / 0.05 | **agrees** |
| matrices | every linear layer | attention only (q, k, v, o) | **differs** |
| lr | 3e-4 | 2.0e-4 / 9e-5 / 6e-5 / 2e-5 | near for Qwen; lower elsewhere (different task: 5 epochs over a dataset vs 50 steps on one fact) |
| completion loss | none (pure LoCo) | completion_weight 1 | by design (pure LoCo never learns to produce the answer) |
| precision | 4-bit NF4 | bf16 | differs (practical) |

## Summary

| Method | Agreement with published settings | Main difference | Defensible? |
|---|---|---|---|
| ROME | high | 50 steps; Mistral clamp 12; Qwen layer 8 | yes, from our data |
| FT-M | high on lr and steps | Mistral layer 7 vs 21-23 | not yet: L21-23 never tested on Mistral at 40 edits |
| IFMET | high | NLL term 30x | yes (4/4 models in step 1) |
| AlphaEdit | medium | clamp up, L2 down, 12 steps | clamp and L2 yes (single vs sequential editing); 12 steps no |
| FiNE | medium | everything stronger | yes (4/4 models in step 1) |
| LoCo | medium | attention only; per-edit lr | partly (different setting from upstream) |
| LoRA | low | lr 30-250x lower; MLP matrices | yes (step 0 and 1), but should be shown |
| LTI | low | clamp 1.2 vs 4, NLL 40-70x, KL 10x lower | no: the clamp was never re-tuned |
| FiDAL | **broken** | top_k 10 >= 7 candidates: no locating | no: must rerun with top_k 1-2 |

## Design for the 120-record dev validation

The new dev split (version 2) has 120 records (60 replace, 30 insert, 30 delete), none shared
with the 40 tuning records. Report replace edits separately so they compare directly with tuning.

**Arms (per method x model):**

| Arm | Config | Seeds | Purpose |
|---|---|---|---|
| A. Tuned | step-3 final (`state.json`) | 2 | honest scores for our picks on new records |
| B. Published | the reference config above, adapted only where forced (layer windows at the same relative depth for models without a config; FT-M objective; LoCo completion loss) | 1 | "consistent or not" on the same records: A vs B, paired by record |
| C. Gap probes | ours with one published value swapped in | 1 | which single difference drives A vs B |

**Arm C probes** (each is ours plus one change):

- LTI: clamp 4; and clamp 4 with nll 0.125, last_kl 0.0725 (the authors' balance). 2 configs x 4 models.
- AlphaEdit: 25 grad steps (Llama, Olmo, Mistral). 3.
- FT-M on Mistral: layer 21 and 23. 2.
- FiDAL: top_k 1 and 2, probe 60 steps at lr 1e-4. 2 x 4 models. **Required before FiDAL is
  reported at all.**
- LoCo: all linear layers. 4.
- LoRA: q/v matrices at our lr (separates "matrix" from "rate" in A vs B). 4.

**Cost** at the measured per-edit times (212 s per edit summed over the 9 methods, 120 edits per
run): arm A about 28 GPU h per seed (56 for two), arm B about 28, arm C 29 configs about 23.
Total about 107 GPU h, roughly a day and a half on 4 GPU lanes.

**What to compare.** For each method x model: A vs B on the objective and every score, with a
record-bootstrap interval (paired). A clearly beating B (beyond about 3 points paired) says the
tuning found something real; a tie says our values and the authors' are equivalent on this data,
which is also reassuring; B beating A flags overfitting to the 40 tuning records.
