# Step 1: two-level factorial specs (prepared, not launched)

Written by `scripts/make_step1_specs.py`; rerun it to regenerate. One spec per method and
main instruct model, on Sid's 10-edit screen split (dev records, single edits, seed 0), with
3 centre runs each (seeds 0, 1, 2). Check and launch one with

```bash
python scripts/dash.py sweep docs/hparam_step1/specs/<file>.json --estimate
python scripts/dash.py sweep docs/hparam_step1/specs/<file>.json
```

`fraction` is the default (null) for most methods: the full design up to 6 settings, otherwise
the smallest fraction of resolution V or more. IFMET, LoCo and AlphaEdit use `"fraction": 3` and
LTI `4`: 64 corner runs at resolution IV, chosen for cost (main effects stay clear, but pairs of
settings are aliased with other pairs). The last column shows them at full resolution instead.

GPU time is runs x the step-0 median minutes per run; it leaves out covariance statistics
for layers that have none yet (`--estimate` lists them).

## Per method (each of the 4 models)

| Method | Settings | Design | Runs per model | Min per run | GPU hours per model | GPU hours, 4 models | Full-resolution option, 4 models |
|---|---|---|---|---|---|---|---|
| FT-M | 5 | full 2^5 + 3 centre | 35 | 2.0 | 1.2 | 4.7 | same |
| LoRA | 7 | 2^(7-1), resolution VII + 3 centre | 67 | 3.2 | 3.6 | 14.3 | same |
| ROME | 6 | full 2^6 + 3 centre | 67 | 9.1 | 10.2 | 40.6 | same |
| FiDAL | 7 | 2^(7-1), resolution VII + 3 centre | 67 | 3.6 | 4.0 | 16.1 | same |
| FiNE | 8 | 2^(8-2), resolution V + 3 centre | 67 | 1.7 | 1.9 | 7.6 | same |
| LoCo | 9 | 2^(9-3), resolution IV + 3 centre | 67 | 5.9 | 6.6 | 26.4 | 131 runs, 51.5 h |
| IFMET | 9 | 2^(9-3), resolution IV + 3 centre | 67 | 10.9 | 12.2 | 48.7 | 131 runs, 95.2 h |
| LTI | 10 | 2^(10-4), resolution IV + 3 centre | 67 | 3.5 | 3.9 | 15.6 | 131 runs, 30.6 h |
| AlphaEdit | 9 | 2^(9-3), resolution IV + 3 centre | 67 | 2.8 | 3.1 | 12.5 | 131 runs, 24.5 h |
| **All** | | | 571 | | 46.6 | **186.5** | 3308 runs, 285.0 h |

Total: 2284 runs, about 186.5 GPU hours (46.6 hours of wall clock at the
dashboard's four GPU jobs at once). At full resolution (V or more) for IFMET, LTI, LoCo and
AlphaEdit instead: 3308 runs, about 285.0 GPU hours.

## Covariance statistics

- Present for every layer the specs edit.

## Spec files

| File | Runs | GPU hours |
|---|---|---|
| `specs/ft__qwen3-4b-instruct-2507.json` | 35 | 1.2 |
| `specs/ft__olmo-3-7b-instruct.json` | 35 | 1.2 |
| `specs/ft__llama-3.1-8b-instruct.json` | 35 | 1.2 |
| `specs/ft__mistral-7b-instruct-v0.1.json` | 35 | 1.2 |
| `specs/lora__qwen3-4b-instruct-2507.json` | 67 | 3.6 |
| `specs/lora__olmo-3-7b-instruct.json` | 67 | 3.6 |
| `specs/lora__llama-3.1-8b-instruct.json` | 67 | 3.6 |
| `specs/lora__mistral-7b-instruct-v0.1.json` | 67 | 3.6 |
| `specs/rome__qwen3-4b-instruct-2507.json` | 67 | 10.2 |
| `specs/rome__olmo-3-7b-instruct.json` | 67 | 10.2 |
| `specs/rome__llama-3.1-8b-instruct.json` | 67 | 10.2 |
| `specs/rome__mistral-7b-instruct-v0.1.json` | 67 | 10.2 |
| `specs/fidal__qwen3-4b-instruct-2507.json` | 67 | 4.0 |
| `specs/fidal__olmo-3-7b-instruct.json` | 67 | 4.0 |
| `specs/fidal__llama-3.1-8b-instruct.json` | 67 | 4.0 |
| `specs/fidal__mistral-7b-instruct-v0.1.json` | 67 | 4.0 |
| `specs/fine__qwen3-4b-instruct-2507.json` | 67 | 1.9 |
| `specs/fine__olmo-3-7b-instruct.json` | 67 | 1.9 |
| `specs/fine__llama-3.1-8b-instruct.json` | 67 | 1.9 |
| `specs/fine__mistral-7b-instruct-v0.1.json` | 67 | 1.9 |
| `specs/loco__qwen3-4b-instruct-2507.json` | 67 | 6.6 |
| `specs/loco__olmo-3-7b-instruct.json` | 67 | 6.6 |
| `specs/loco__llama-3.1-8b-instruct.json` | 67 | 6.6 |
| `specs/loco__mistral-7b-instruct-v0.1.json` | 67 | 6.6 |
| `specs/ifmet__qwen3-4b-instruct-2507.json` | 67 | 12.2 |
| `specs/ifmet__olmo-3-7b-instruct.json` | 67 | 12.2 |
| `specs/ifmet__llama-3.1-8b-instruct.json` | 67 | 12.2 |
| `specs/ifmet__mistral-7b-instruct-v0.1.json` | 67 | 12.2 |
| `specs/lti__qwen3-4b-instruct-2507.json` | 67 | 3.9 |
| `specs/lti__olmo-3-7b-instruct.json` | 67 | 3.9 |
| `specs/lti__llama-3.1-8b-instruct.json` | 67 | 3.9 |
| `specs/lti__mistral-7b-instruct-v0.1.json` | 67 | 3.9 |
| `specs/alphaedit__qwen3-4b-instruct-2507.json` | 67 | 3.1 |
| `specs/alphaedit__olmo-3-7b-instruct.json` | 67 | 3.1 |
| `specs/alphaedit__llama-3.1-8b-instruct.json` | 67 | 3.1 |
| `specs/alphaedit__mistral-7b-instruct-v0.1.json` | 67 | 3.1 |
