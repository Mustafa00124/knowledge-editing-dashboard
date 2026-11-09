# Step 2: small grids on the 40 dev edits

Written by `scripts/make_step2_specs.py`; rerun it to regenerate. Why each setting is swept, held
or frozen, and how the values follow from step 1: `docs/hparam_selection.md`.

Every spec is a `grid` sweep on Sid's dev split (40 replace edits, single edits). ROME, FiDAL and
LTI run twice (seeds 0 and 1) because their edits depend on sampled context prefixes.

```bash
python scripts/dash.py sweep docs/hparam_step2/specs/<file>.json --estimate
python scripts/dash.py sweep docs/hparam_step2/specs/<file>.json
```

| Method | Model | Part | Swept | Held | Runs x seeds |
|---|---|---|---|---|---|
| FT-M | Qwen | grid | `layers` {16, 24, 32}; `norm_constraint` {0.000274, 0.0005, 0.001} | `lr` 0.000474, `num_steps` 24, `weight_decay` 0.005 | 9 x 1 |
| FT-M | Olmo | grid | `layers` {14, 21, 27}; `norm_constraint` {0.000274, 0.0005, 0.001} | `lr` 0.000474, `num_steps` 24, `weight_decay` 0.005 | 9 x 1 |
| FT-M | Llama | grid | `layers` {5, 13, 21}; `norm_constraint` {0.000274, 0.0005, 0.001} | `lr` 0.000474, `num_steps` 24, `weight_decay` 0.005 | 9 x 1 |
| FT-M | Mistral | grid | `layers` {4, 8, 14}; `norm_constraint` {0.000274, 0.0005, 0.001} | `lr` 0.000474, `num_steps` 24, `weight_decay` 0.005 | 9 x 1 |
| LoRA | Qwen | grid | `layers` {0-17, 9-26, 18-35}; `lr` {5e-05, 0.000158, 0.0005} | `lora_dropout` 0, `num_steps` 50, `target_modules` up+down+gate, `lora_alpha` 23, `rank` 11, `weight_decay` 0.0316 | 9 x 1 |
| LoRA | Olmo | grid | `layers` {0-15, 8-23, 16-31}; `lr` {5e-05, 0.000158, 0.0005} | `lora_dropout` 0, `num_steps` 50, `target_modules` up+down+gate, `lora_alpha` 23, `rank` 11, `weight_decay` 0.0316 | 9 x 1 |
| LoRA | Llama | grid | `layers` {0-15, 8-23, 16-31}; `lr` {5e-05, 0.000158, 0.0005} | `lora_dropout` 0, `num_steps` 50, `target_modules` up+down+gate, `lora_alpha` 23, `rank` 11, `weight_decay` 0.0316 | 9 x 1 |
| LoRA | Mistral | grid | `layers` {0-15, 8-23, 16-31}; `lr` {5e-05, 0.000158, 0.0005} | `lora_dropout` 0, `num_steps` 50, `target_modules` up+down+gate, `lora_alpha` 23, `rank` 11, `weight_decay` 0.0316 | 9 x 1 |
| ROME | Qwen | grid | `layers` {5, 7, 9}; `clamp_norm_factor` {1.2, 3.79, 12} | `v_num_grad_steps` 50, `v_lr` 0.866, `kl_factor` 0.0625, `v_weight_decay` 0.001 | 9 x 2 |
| ROME | Olmo | grid | `layers` {2, 3, 5}; `clamp_norm_factor` {1.2, 3.79, 12} | `v_num_grad_steps` 50, `v_lr` 0.866, `kl_factor` 0.0625, `v_weight_decay` 0.001 | 9 x 2 |
| ROME | Llama | grid | `layers` {2, 3, 5}; `clamp_norm_factor` {1.2, 3.79, 12} | `v_num_grad_steps` 50, `v_lr` 0.866, `kl_factor` 0.0625, `v_weight_decay` 0.001 | 9 x 2 |
| ROME | Mistral | grid | `layers` {2, 3, 5}; `clamp_norm_factor` {1.2, 3.79, 12} | `v_num_grad_steps` 50, `v_lr` 0.866, `kl_factor` 0.0625, `v_weight_decay` 0.001 | 9 x 2 |
| FiDAL | Qwen | grid | `candidate_layers` {2-8, 5-11, 7-13}; `clamp_norm_factor` {1.2, 2.19, 4} | `probe_steps` 10, `probe_lr` 0.01, `v_lr` 0.866, `v_num_grad_steps` 50, `top_k` 10, `kl_factor` 0.0343, `mom2_update_weight` 4740 | 9 x 2 |
| FiDAL | Olmo | grid | `candidate_layers` {2-8, 5-11, 7-13}; `clamp_norm_factor` {1.2, 2.19, 4} | `probe_steps` 10, `probe_lr` 0.01, `v_lr` 0.866, `v_num_grad_steps` 50, `top_k` 10, `kl_factor` 0.0343, `mom2_update_weight` 4740 | 9 x 2 |
| FiDAL | Llama | grid | `clamp_norm_factor` {0.8, 1.2, 2.19}; `v_lr` {0.15, 0.866, 5} | `probe_steps` 10, `probe_lr` 0.01, `candidate_layers` 2-8, `v_num_grad_steps` 50, `top_k` 10, `kl_factor` 0.0343, `mom2_update_weight` 4740 | 9 x 2 |
| FiDAL | Mistral | grid | `clamp_norm_factor` {0.8, 1.2, 2.19}; `v_lr` {0.15, 0.866, 5} | `probe_steps` 10, `probe_lr` 0.01, `candidate_layers` 2-8, `v_num_grad_steps` 50, `top_k` 10, `kl_factor` 0.0343, `mom2_update_weight` 4740 | 9 x 2 |
| FiNE | Qwen | grid | `lr` {0.0003, 0.000949, 0.003}; `neuron_num` {2, 4, 10} | `epochs` 200, `early_stop_prob` 0.99, `last_layer` 6, `alpha` 1, `beta` 9.49, `gamma` 0.0316 | 9 x 1 |
| FiNE | Olmo | grid | `lr` {0.0003, 0.000949, 0.003}; `neuron_num` {2, 4, 10} | `epochs` 200, `early_stop_prob` 0.99, `last_layer` 6, `alpha` 1, `beta` 9.49, `gamma` 0.0316 | 9 x 1 |
| FiNE | Llama | grid | `lr` {0.0003, 0.000949, 0.003}; `neuron_num` {2, 4, 10} | `epochs` 200, `early_stop_prob` 0.99, `last_layer` 6, `alpha` 1, `beta` 9.49, `gamma` 0.0316 | 9 x 1 |
| FiNE | Mistral | grid | `lr` {0.0003, 0.000949, 0.003}; `neuron_num` {2, 4, 10} | `epochs` 200, `early_stop_prob` 0.99, `last_layer` 6, `alpha` 1, `beta` 9.49, `gamma` 0.0316 | 9 x 1 |
| IFMET | Qwen | v_lr | `v_lr` {0.02, 0.0632, 0.2} | `clamp_norm_factor` 1.2, `v_num_grad_steps` 60, `layers` 2-6, `mom2_update_weight` 4740, `kl_factor` 0.548, `deep_layers` 20-24, `n_support` 5, `support_temperature` 0.7, `nll_loss_factor` 10 | 3 x 1 |
| IFMET | Qwen | nll | `nll_loss_factor` {3, 30} | `clamp_norm_factor` 1.2, `v_num_grad_steps` 60, `layers` 2-6, `mom2_update_weight` 4740, `kl_factor` 0.548, `deep_layers` 20-24, `n_support` 5, `support_temperature` 0.7, `v_lr` 0.0632 | 2 x 1 |
| IFMET | Olmo | v_lr | `v_lr` {0.02, 0.0632, 0.2} | `clamp_norm_factor` 1.2, `v_num_grad_steps` 60, `layers` 2-6, `mom2_update_weight` 4740, `kl_factor` 0.548, `deep_layers` 18-22, `n_support` 5, `support_temperature` 0.7, `nll_loss_factor` 10 | 3 x 1 |
| IFMET | Olmo | nll | `nll_loss_factor` {3, 30} | `clamp_norm_factor` 1.2, `v_num_grad_steps` 60, `layers` 2-6, `mom2_update_weight` 4740, `kl_factor` 0.548, `deep_layers` 18-22, `n_support` 5, `support_temperature` 0.7, `v_lr` 0.0632 | 2 x 1 |
| IFMET | Llama | v_lr | `v_lr` {0.02, 0.0632, 0.2} | `clamp_norm_factor` 1.2, `v_num_grad_steps` 60, `layers` 2-6, `mom2_update_weight` 4740, `kl_factor` 0.548, `deep_layers` 18-22, `n_support` 5, `support_temperature` 0.7, `nll_loss_factor` 10 | 3 x 1 |
| IFMET | Llama | nll | `nll_loss_factor` {3, 30} | `clamp_norm_factor` 1.2, `v_num_grad_steps` 60, `layers` 2-6, `mom2_update_weight` 4740, `kl_factor` 0.548, `deep_layers` 18-22, `n_support` 5, `support_temperature` 0.7, `v_lr` 0.0632 | 2 x 1 |
| IFMET | Mistral | v_lr | `v_lr` {0.02, 0.0632, 0.2} | `clamp_norm_factor` 1.2, `v_num_grad_steps` 60, `layers` 2-6, `mom2_update_weight` 4740, `kl_factor` 0.548, `deep_layers` 18-22, `n_support` 5, `support_temperature` 0.7, `nll_loss_factor` 10 | 3 x 1 |
| IFMET | Mistral | nll | `nll_loss_factor` {3, 30} | `clamp_norm_factor` 1.2, `v_num_grad_steps` 60, `layers` 2-6, `mom2_update_weight` 4740, `kl_factor` 0.548, `deep_layers` 18-22, `n_support` 5, `support_temperature` 0.7, `v_lr` 0.0632 | 2 x 1 |
| LTI | Qwen | grid | `layers` {2-6, 4-8, 6-10}; `v_lr` {0.05, 0.158, 0.5} | `clamp_norm_factor` 1.2, `v_num_grad_steps` 50, `last_kl_factor` 0.00725, `midlayers` 16, `mid_kl_factor` 0.0134, `mom2_update_weight` 4740, `kl_factor` 0.0343, `nll_factor` 3 | 9 x 2 |
| LTI | Qwen | nll | `nll_factor` {1.06, 9} | `clamp_norm_factor` 1.2, `v_num_grad_steps` 50, `last_kl_factor` 0.00725, `midlayers` 16, `mid_kl_factor` 0.0134, `mom2_update_weight` 4740, `kl_factor` 0.0343, `layers` 4-8, `v_lr` 0.158 | 2 x 2 |
| LTI | Olmo | grid | `layers` {2-6, 4-8, 6-10}; `v_lr` {0.05, 0.158, 0.5} | `clamp_norm_factor` 1.2, `v_num_grad_steps` 50, `last_kl_factor` 0.00725, `midlayers` 14, `mid_kl_factor` 0.0134, `mom2_update_weight` 4740, `kl_factor` 0.0343, `nll_factor` 3 | 9 x 2 |
| LTI | Olmo | nll | `nll_factor` {1.06, 9} | `clamp_norm_factor` 1.2, `v_num_grad_steps` 50, `last_kl_factor` 0.00725, `midlayers` 14, `mid_kl_factor` 0.0134, `mom2_update_weight` 4740, `kl_factor` 0.0343, `layers` 4-8, `v_lr` 0.158 | 2 x 2 |
| LTI | Llama | grid | `layers` {1-5, 2-6, 4-8}; `v_lr` {0.05, 0.158, 0.5} | `clamp_norm_factor` 1.2, `v_num_grad_steps` 50, `last_kl_factor` 0.00725, `midlayers` 14, `mid_kl_factor` 0.0134, `mom2_update_weight` 4740, `kl_factor` 0.0343, `nll_factor` 3 | 9 x 2 |
| LTI | Llama | nll | `nll_factor` {1.06, 9} | `clamp_norm_factor` 1.2, `v_num_grad_steps` 50, `last_kl_factor` 0.00725, `midlayers` 14, `mid_kl_factor` 0.0134, `mom2_update_weight` 4740, `kl_factor` 0.0343, `layers` 2-6, `v_lr` 0.158 | 2 x 2 |
| LTI | Mistral | grid | `layers` {1-5, 2-6, 4-8}; `v_lr` {0.05, 0.158, 0.5} | `clamp_norm_factor` 1.2, `v_num_grad_steps` 50, `last_kl_factor` 0.00725, `midlayers` 14, `mid_kl_factor` 0.0134, `mom2_update_weight` 4740, `kl_factor` 0.0343, `nll_factor` 3 | 9 x 2 |
| LTI | Mistral | nll | `nll_factor` {1.06, 9} | `clamp_norm_factor` 1.2, `v_num_grad_steps` 50, `last_kl_factor` 0.00725, `midlayers` 14, `mid_kl_factor` 0.0134, `mom2_update_weight` 4740, `kl_factor` 0.0343, `layers` 2-6, `v_lr` 0.158 | 2 x 2 |
| LoCo | Qwen | grid | `lr` {9e-05, 0.000285, 0.0009}; `num_steps` {6, 17, 50} | `lora_dropout` 0.05, `constraint` implication, `target_modules` q+k+v+o, `lora_alpha` 15.2, `rank` 128, `n_implications` 5, `completion_weight` 1, `implication_max_new_tokens` 30 | 9 x 1 |
| LoCo | Qwen | constraint | `constraint` {all} | `lora_dropout` 0.05, `lr` 0.000285, `num_steps` 17, `target_modules` q+k+v+o, `lora_alpha` 15.2, `rank` 128, `n_implications` 5, `completion_weight` 1, `implication_max_new_tokens` 30 | 1 x 1 |
| LoCo | Olmo | grid | `lr` {9e-05, 0.000285, 0.0009}; `num_steps` {6, 17, 50} | `lora_dropout` 0.05, `constraint` implication, `target_modules` q+k+v+o, `lora_alpha` 15.2, `rank` 128, `n_implications` 5, `completion_weight` 1, `implication_max_new_tokens` 30 | 9 x 1 |
| LoCo | Olmo | constraint | `constraint` {all} | `lora_dropout` 0.05, `lr` 0.000285, `num_steps` 17, `target_modules` q+k+v+o, `lora_alpha` 15.2, `rank` 128, `n_implications` 5, `completion_weight` 1, `implication_max_new_tokens` 30 | 1 x 1 |
| LoCo | Llama | grid | `lr` {9e-05, 0.000285, 0.0009}; `num_steps` {6, 17, 50} | `lora_dropout` 0.05, `constraint` implication, `target_modules` q+k+v+o, `lora_alpha` 15.2, `rank` 128, `n_implications` 5, `completion_weight` 1, `implication_max_new_tokens` 30 | 9 x 1 |
| LoCo | Llama | constraint | `constraint` {all} | `lora_dropout` 0.05, `lr` 0.000285, `num_steps` 17, `target_modules` q+k+v+o, `lora_alpha` 15.2, `rank` 128, `n_implications` 5, `completion_weight` 1, `implication_max_new_tokens` 30 | 1 x 1 |
| LoCo | Mistral | grid | `lr` {9e-05, 0.000285, 0.0009}; `num_steps` {6, 17, 50} | `lora_dropout` 0.05, `constraint` implication, `target_modules` q+k+v+o, `lora_alpha` 15.2, `rank` 128, `n_implications` 5, `completion_weight` 1, `implication_max_new_tokens` 30 | 9 x 1 |
| LoCo | Mistral | constraint | `constraint` {all} | `lora_dropout` 0.05, `lr` 0.000285, `num_steps` 17, `target_modules` q+k+v+o, `lora_alpha` 15.2, `rank` 128, `n_implications` 5, `completion_weight` 1, `implication_max_new_tokens` 30 | 1 x 1 |
| AlphaEdit | Qwen | grid | `v_lr` {0.158, 0.5, 1.58}; `nullspace_threshold` {0.02, 0.2, 0.6} | `layers` 6-10, `v_num_grad_steps` 50, `L2` 0.1, `clamp_norm_factor` 3.79, `kl_factor` 0.0625, `mom2_update_weight` 8220, `v_weight_decay` 0.001 | 9 x 2 |
| AlphaEdit | Olmo | grid | `clamp_norm_factor` {1.2, 3.79, 12}; `v_lr` {0.016, 0.05, 0.158} | `layers` 6-10, `v_num_grad_steps` 12, `L2` 0.1, `nullspace_threshold` 0.02, `kl_factor` 0.0625, `mom2_update_weight` 8220, `v_weight_decay` 0.001 | 9 x 2 |
| AlphaEdit | Llama | grid | `clamp_norm_factor` {0.8, 1.2, 3.79}; `v_lr` {0.016, 0.05, 0.158} | `layers` 2-6, `v_num_grad_steps` 12, `L2` 0.1, `nullspace_threshold` 0.002, `kl_factor` 0.0625, `mom2_update_weight` 8220, `v_weight_decay` 0.001 | 9 x 2 |
| AlphaEdit | Mistral | grid | `clamp_norm_factor` {0.8, 1.2, 3.79}; `v_lr` {0.016, 0.05, 0.158} | `layers` 2-6, `v_num_grad_steps` 12, `L2` 0.1, `nullspace_threshold` 0.02, `kl_factor` 0.0625, `mom2_update_weight` 8220, `v_weight_decay` 0.001 | 9 x 2 |

Total: 68 specs, 472 runs.

