# Step 1: factorial specs (prepared, not launched)

Written by `scripts/make_step1_specs.py`; rerun it to regenerate. One spec per method and
main instruct model, on Sid's 10-edit screen split (dev records, single edits, seed 0), with
3 centre runs each (seeds 0, 1, 2). Check and launch one with

```bash
python scripts/dash.py sweep docs/hparam_step1/specs/<file>.json --estimate
python scripts/dash.py sweep docs/hparam_step1/specs/<file>.json
```

Every setting takes a low and a high value, except each method's main layer setting, which
takes three (early, middle, late; LoCo has none). The two-level design of the other settings
runs at each of the three: early and late together form an ordinary two-level design (main
effects and interactions as before), and the middle block shows whether the layer bends.
`fraction` is that two-level part's p: resolution V or more, except resolution IV for the
9-10 setting methods (IFMET, LTI, LoCo, AlphaEdit; for cost: main effects stay clear, but
pairs of settings are aliased with other pairs).

GPU time is runs x the step-0 median minutes per run; it leaves out covariance statistics
for layers that have none yet (`--estimate` lists them).

## Per method (each of the 4 models)

| Method | Settings | Design | Runs per model | Min per run | GPU hours per model | GPU hours, 4 models |
|---|---|---|---|---|---|---|
| FT-M | 5 | full 2^4 x 3 layers + 3 centre | 51 | 2.0 | 1.7 | 6.8 |
| LoRA | 7 | 2^(6-1), resolution VI x 3 layers + 3 centre | 99 | 3.2 | 5.3 | 21.1 |
| ROME | 6 | 2^(5-1), resolution V x 3 layers + 3 centre | 51 | 9.1 | 7.7 | 30.9 |
| FiDAL | 7 | 2^(6-1), resolution VI x 3 candidate_layers + 3 centre | 99 | 3.6 | 5.9 | 23.8 |
| FiNE | 8 | 2^(7-1), resolution VII x 3 last_layer + 3 centre | 195 | 1.7 | 5.5 | 22.1 |
| LoCo | 9 | 2^(9-3), resolution IV + 3 centre | 67 | 5.9 | 6.6 | 26.4 |
| IFMET | 9 | 2^(8-3), resolution IV x 3 layers + 3 centre | 99 | 10.9 | 18.0 | 71.9 |
| LTI | 10 | 2^(9-3), resolution IV x 3 layers + 3 centre | 195 | 3.5 | 11.4 | 45.5 |
| AlphaEdit | 9 | 2^(8-3), resolution IV x 3 layers + 3 centre | 99 | 2.8 | 4.6 | 18.5 |
| **All** | | | 955 | | 66.7 | **267.0** |

Total: 3820 runs, about 267.0 GPU hours (66.7 hours of wall clock at the
dashboard's four GPU jobs at once).

## Covariance statistics

- Present for every layer the specs edit.

## Spec files

| File | Runs | GPU hours |
|---|---|---|
| `specs/ft__qwen3-4b-instruct-2507.json` | 51 | 1.7 |
| `specs/ft__olmo-3-7b-instruct.json` | 51 | 1.7 |
| `specs/ft__llama-3.1-8b-instruct.json` | 51 | 1.7 |
| `specs/ft__mistral-7b-instruct-v0.1.json` | 51 | 1.7 |
| `specs/lora__qwen3-4b-instruct-2507.json` | 99 | 5.3 |
| `specs/lora__olmo-3-7b-instruct.json` | 99 | 5.3 |
| `specs/lora__llama-3.1-8b-instruct.json` | 99 | 5.3 |
| `specs/lora__mistral-7b-instruct-v0.1.json` | 99 | 5.3 |
| `specs/rome__qwen3-4b-instruct-2507.json` | 51 | 7.7 |
| `specs/rome__olmo-3-7b-instruct.json` | 51 | 7.7 |
| `specs/rome__llama-3.1-8b-instruct.json` | 51 | 7.7 |
| `specs/rome__mistral-7b-instruct-v0.1.json` | 51 | 7.7 |
| `specs/fidal__qwen3-4b-instruct-2507.json` | 99 | 5.9 |
| `specs/fidal__olmo-3-7b-instruct.json` | 99 | 5.9 |
| `specs/fidal__llama-3.1-8b-instruct.json` | 99 | 5.9 |
| `specs/fidal__mistral-7b-instruct-v0.1.json` | 99 | 5.9 |
| `specs/fine__qwen3-4b-instruct-2507.json` | 195 | 5.5 |
| `specs/fine__olmo-3-7b-instruct.json` | 195 | 5.5 |
| `specs/fine__llama-3.1-8b-instruct.json` | 195 | 5.5 |
| `specs/fine__mistral-7b-instruct-v0.1.json` | 195 | 5.5 |
| `specs/loco__qwen3-4b-instruct-2507.json` | 67 | 6.6 |
| `specs/loco__olmo-3-7b-instruct.json` | 67 | 6.6 |
| `specs/loco__llama-3.1-8b-instruct.json` | 67 | 6.6 |
| `specs/loco__mistral-7b-instruct-v0.1.json` | 67 | 6.6 |
| `specs/ifmet__qwen3-4b-instruct-2507.json` | 99 | 18.0 |
| `specs/ifmet__olmo-3-7b-instruct.json` | 99 | 18.0 |
| `specs/ifmet__llama-3.1-8b-instruct.json` | 99 | 18.0 |
| `specs/ifmet__mistral-7b-instruct-v0.1.json` | 99 | 18.0 |
| `specs/lti__qwen3-4b-instruct-2507.json` | 195 | 11.4 |
| `specs/lti__olmo-3-7b-instruct.json` | 195 | 11.4 |
| `specs/lti__llama-3.1-8b-instruct.json` | 195 | 11.4 |
| `specs/lti__mistral-7b-instruct-v0.1.json` | 195 | 11.4 |
| `specs/alphaedit__qwen3-4b-instruct-2507.json` | 99 | 4.6 |
| `specs/alphaedit__olmo-3-7b-instruct.json` | 99 | 4.6 |
| `specs/alphaedit__llama-3.1-8b-instruct.json` | 99 | 4.6 |
| `specs/alphaedit__mistral-7b-instruct-v0.1.json` | 99 | 4.6 |
