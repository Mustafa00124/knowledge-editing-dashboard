# Step 3, round 1: one setting at a time on the 40 dev edits

Written by `scripts/make_step3_specs.py --round 1` from `docs/hparam_step3/state.json`.
Every other setting is held at its current value in the state file. Method: docs/hparam_selection.md.

| Method | Model | Setting | Current | Values | Runs |
|---|---|---|---|---|---|
| FT-M | Qwen | `layers` | L24 | L20, L21, L22, L23, L24, L25, L26, L27, L28 | 9 |
| FT-M | Olmo | `layers` | L21 | L17, L18, L19, L20, L21, L22, L23, L24, L25 | 9 |
| FT-M | Llama | `layers` | L13 | L3, L5, L8, L10, L13, L16, L19, L21, L24, L27 | 10 |
| FT-M | Mistral | `layers` | L8 | L4, L5, L6, L7, L8, L9, L10, L11, L12 | 9 |
| LoRA | Qwen | `layers` | L9-26 | L1-18, L3-20, L5-22, L7-24, L9-26, L11-28, L13-30, L15-32, L17-34 | 9 |
| LoRA | Olmo | `layers` | L16-31 | L0-15, L2-17, L4-19, L6-21, L8-23, L10-25, L12-27, L14-29, L16-31 | 9 |
| LoRA | Llama | `layers` | L0-15 | L0-15, L2-17, L4-19, L6-21, L8-23, L10-25, L12-27, L14-29, L16-31 | 9 |
| LoRA | Mistral | `layers` | L0-15 | L0-15, L2-17, L4-19, L6-21, L8-23, L10-25, L12-27, L14-29, L16-31 | 9 |
| ROME | Qwen | `layers` | L7 | L3, L4, L5, L6, L7, L8, L9, L10, L11 | 9 |
| ROME | Olmo | `layers` | L2 | L0, L1, L2, L3, L4, L5, L6, L7, L8 | 9 |
| ROME | Llama | `layers` | L5 | L1, L2, L3, L4, L5, L6, L7, L8, L9 | 9 |
| ROME | Mistral | `layers` | L5 | L1, L2, L3, L4, L5, L6, L7, L8, L9 | 9 |
| FiDAL | Qwen | `candidate_layers` | L5-11 | L1-7, L2-8, L3-9, L4-10, L5-11, L6-12, L7-13, L8-14, L9-15 | 9 |
| FiDAL | Olmo | `candidate_layers` | L2-8 | L0-6, L1-7, L2-8, L3-9, L4-10, L5-11, L6-12, L7-13, L8-14 | 9 |
| FiDAL | Llama | `candidate_layers` | L2-8 | L0-6, L1-7, L2-8, L3-9, L4-10, L5-11, L6-12, L7-13, L8-14 | 9 |
| FiDAL | Mistral | `candidate_layers` | L2-8 | L0-6, L1-7, L2-8, L3-9, L4-10, L5-11, L6-12, L7-13, L8-14 | 9 |
| FiNE | Qwen | `neuron_num` | 15 | 3, 5, 8, 10, 12, 15, 20, 25 | 8 |
| FiNE | Olmo | `neuron_num` | 15 | 3, 5, 8, 10, 12, 15, 20, 25 | 8 |
| FiNE | Llama | `neuron_num` | 15 | 3, 5, 8, 10, 12, 15, 20, 25 | 8 |
| FiNE | Mistral | `neuron_num` | 10 | 3, 5, 8, 10, 12, 15, 20, 25 | 8 |
| IFMET | Qwen | `layers` | L2-6 | L0-4, L1-5, L2-6, L3-7, L4-8, L5-9, L6-10, L7-11, L8-12 | 9 |
| IFMET | Olmo | `layers` | L2-6 | L0-4, L1-5, L2-6, L3-7, L4-8, L5-9, L6-10, L7-11, L8-12 | 9 |
| IFMET | Llama | `layers` | L2-6 | L0-4, L1-5, L2-6, L3-7, L4-8, L5-9, L6-10, L7-11, L8-12 | 9 |
| IFMET | Mistral | `layers` | L2-6 | L0-4, L1-5, L2-6, L3-7, L4-8, L5-9, L6-10, L7-11, L8-12 | 9 |
| LTI | Qwen | `layers` | L4-8 | L0-4, L1-5, L2-6, L3-7, L4-8, L5-9, L6-10, L7-11, L8-12 | 9 |
| LTI | Olmo | `layers` | L4-8 | L0-4, L1-5, L2-6, L3-7, L4-8, L5-9, L6-10, L7-11, L8-12 | 9 |
| LTI | Llama | `layers` | L4-8 | L0-4, L1-5, L2-6, L3-7, L4-8, L5-9, L6-10, L7-11, L8-12 | 9 |
| LTI | Mistral | `layers` | L4-8 | L0-4, L1-5, L2-6, L3-7, L4-8, L5-9, L6-10, L7-11, L8-12 | 9 |
| LoCo | Qwen | `lr` | 9e-05 | 1.19e-05, 1.78e-05, 2.67e-05, 4e-05, 6e-05, 9e-05, 0.000135, 0.000203 | 8 |
| LoCo | Olmo | `lr` | 9e-05 | 1.19e-05, 1.78e-05, 2.67e-05, 4e-05, 6e-05, 9e-05, 0.000135, 0.000203 | 8 |
| LoCo | Llama | `lr` | 9e-05 | 1.19e-05, 1.78e-05, 2.67e-05, 4e-05, 6e-05, 9e-05, 0.000135, 0.000203 | 8 |
| LoCo | Mistral | `lr` | 2e-05 | 2.63e-06, 3.95e-06, 5.93e-06, 8.89e-06, 1.33e-05, 2e-05, 3e-05, 4.5e-05 | 8 |
| AlphaEdit | Qwen | `layers` | L6-10 | L2-6, L3-7, L4-8, L5-9, L6-10, L7-11, L8-12, L9-13, L10-14 | 9 |
| AlphaEdit | Olmo | `layers` | L6-10 | L2-6, L3-7, L4-8, L5-9, L6-10, L7-11, L8-12, L9-13, L10-14 | 9 |
| AlphaEdit | Llama | `layers` | L2-6 | L0-4, L1-5, L2-6, L3-7, L4-8, L5-9, L6-10, L7-11, L8-12 | 9 |
| AlphaEdit | Mistral | `layers` | L2-6 | L0-4, L1-5, L2-6, L3-7, L4-8, L5-9, L6-10, L7-11, L8-12 | 9 |

Total: 36 specs, 317 runs.
