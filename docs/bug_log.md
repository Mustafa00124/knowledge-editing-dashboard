# Bug log: hyperparameter tuning runs

Errors found in the editing runs, where each came from, and what was done.
Started 2026-11-04 during the Latin hypercube screen (9 core methods x 4
instruct models, Sid's dev "screen" split). Add new entries at the end of
the table and give each its own section.

**Origin** says where the faulty logic was written:

- **Ours:** written in this project.
- **EasyEdit:** in EasyEdit's code (`external/EasyEdit`), which we forked or
  call.
- **EasyEdit + ours:** EasyEdit's logic, which only broke because of a
  change we made.
- **Copied config:** a settings file we adapted from somewhere else that did
  not fit our model.

Each bug's **Status** says whether it is fixed and whether the affected
results were rerun.

## Summary

| # | Bug | Methods / models | Origin | Status |
|---|---|---|---|---|
| 1 | Learning rates like `5e-05` read as text, run crashed | any run with such a value | Ours | Fixed, rerun |
| 2 | IFMET read the output layer from the input layer | IFMET (and PMET configs) on Llama, Olmo, Mistral | Copied config (EasyEdit's Llama-3.2-3B PMET file) | Fixed, rerun, old runs removed |
| 3 | LoCo never learned to stop answering | LoCo, all models | Ours | Fixed, rerun |
| 4 | LoRA never learned to stop answering | LoRA, all models | EasyEdit | Fixed, rerun |
| 5 | FT-M never learned to stop answering | FT-M, all models | EasyEdit | Fixed, rerun |
| 6 | Mistral trained a word without its leading space | FT-M, LoRA, LoCo on Mistral | Ours (introduced by the fix for 3-5) | Fixed, rerun |
| 7 | End-of-reply token mistaken for padding | FT-M, LoRA on Llama, Mistral | EasyEdit + ours | Fixed, rerun |
| 8 | Derived questions scored right before any edit | generalizability metric, all methods | Ours | Fixed (metric changed, no rerun needed) |
| 9 | Grammar judge too strict | grammar check, all runs | Ours | Fixed (rubric v2), all 690 runs re-judged |
| 10 | FiDAL's default layer band breaks Qwen | FiDAL on Qwen (default and 4 screen runs) | Ours (config) | Fixed: default configs and step-1 specs start at layer 2 |
| 11 | Fluency score blind to word salad | fluency metric, all methods | ROME/MEMIT metric (borrowed) | No fix needed: the judge gate catches it |

## 1. Learning rates like `5e-05` read as text

- **What happened:** settings passed on the command line are read with
  PyYAML. PyYAML follows YAML 1.1, where a number written in scientific
  notation without a dot (`5e-05`) is a string, not a number. The run then
  crashed doing arithmetic with it. 36 runs failed.
- **Origin:** ours. `apply_overrides` in `run_experiment.py` trusted
  `yaml.safe_load` to return numbers.
- **Fix:** `_number_if_numeric` turns such strings into floats, and the
  failed runs were rerun.

## 2. IFMET read the output layer from the input layer

- **What happened:** IFMET (built on PMET) reads the model's output layer
  (`lm_head_module`) to compute how likely the new answer is. Our configs
  pointed it at `model.embed_tokens`, the input layer. On Qwen and SmolLM3
  the two are the same matrix ("tied"), so it worked. On Llama-3.1-8B, Olmo
  and Mistral they are different matrices, so every probability IFMET
  optimised was wrong and it barely edited (median rewrite 0.0-0.1).
- **Origin:** copied config. EasyEdit's `hparams/PMET/llama3.2-3b.yaml`
  uses `model.embed_tokens`, which is right for Llama 3.2-3B (tied). We used
  the same setting for models that are not tied.
- **History:** the setting was first chosen on purpose, for Qwen. PMET looks
  the output layer up by its parameter name (`lm_head.weight`). On a tied
  model PyTorch lists the shared matrix only under its input name, so
  `lm_head` crashed with `LookupError` and Qwen's config was pointed at
  `model.embed_tokens`. That is correct for Qwen, because it is the same
  matrix under another name. The Qwen config was then used as the template
  for the Llama, Olmo and Mistral configs, where the two names mean different
  matrices. Nothing crashed, so the wrong matrix went unnoticed.
- **Checked elsewhere (2026-11-04):** every config was compared with its
  model's `tie_word_embeddings`. No untied model points at the input layer
  any more. Tied models (Qwen, SmolLM3) still use `lm_head` in ROME,
  AlphaEdit, FiNE, FT and LTI configs. That is harmless, because those
  methods look the layer up as a module (`get_module`), which finds the
  shared matrix, and their Qwen runs ran normally.
- **Fix:** `lm_head_module: lm_head` in 13 IFMET/PMET configs. IFMET was
  rerun, and median rewrite is now 0.56-0.67. The 51 old runs were moved to
  `results/investigations/portability/deleted/...--ifmet-deleted-...`.

## 3-5. FT-M, LoRA and LoCo never learned to stop answering

- **What happened:** these methods train the model on "question -> new
  answer". A chat model ends every reply with an end-of-reply token (Llama
  `<|eot_id|>`, Qwen `<|im_end|>`, Mistral `</s>`, Olmo `<|endoftext|>`),
  and that is how it knows to stop. The training text had no such token
  after the answer. The model learned to say the answer but not to stop,
  and repeated it into every reply, related or not ("liver liver liver
  ...").
- **Origin:**
  - LoRA: EasyEdit. In `lora_main.py` the line that adds the end token is
    commented out (`# eos_token = tok.decode(tok.eos_token_id)`). Our fork
    `checkpointed_lora.py` kept that.
  - FT-M: EasyEdit. `ft_main.py` never adds an end token. Our fork
    `checkpointed_ft.py` kept that.
  - LoCo: ours. The completion loss in `portability/loco.py` was our own
    addition and made the same mistake.
- **Fix:** all three now train "answer + the chat template's end-of-reply
  token", from one shared helper, `training_targets.py`. FiNE already did
  this, which is why it stayed fluent.

## 6. Mistral trained a word without its leading space

- **What happened:** models read tokens, not letters, and `" Vermont"`
  (with a space) is a different token from `"Vermont"`. Mistral's chat
  format puts a space after `[/INST]`, so Mistral writes the with-space
  version. The fix for 3-5 trained the no-space version, a token Mistral
  never produces there. Mistral LoRA output became garbage ("Q bekan bekan
  ...").
- **Origin:** ours. It was introduced by our own fix for 3-5.
- **Fix:** `training_targets.turn_start` reads the spacing from each
  model's own chat template. Only Mistral has a space there.

## 7. End-of-reply token mistaken for padding

- **What happened:** examples trained together are padded to the same
  length with a filler token, and the training code must skip the filler
  and the question and train only on the answer. EasyEdit's FT and LoRA
  code finds the filler by its token id. Llama and Mistral have no filler
  token of their own, so `run_experiment.py` sets it to the end-of-reply
  token, which is common practice. Once the fix for 3-5 put that token
  after every answer, the code counted it as filler. The trained span
  shifted by one and the first token of the answer was never trained.
  Training loss looked fine (0.018) while the model answered the wrong
  thing.
- **Origin:** EasyEdit + ours. EasyEdit's masking logic (counting the pad
  id), combined with our pad-equals-end-token setting, broke once our end
  token fix was in place.
- **Fix:** the filler is now found from the attention mask (which marks real
  text versus filler), not by token id, in `checkpointed_ft.py` and
  `checkpointed_lora.py`. Best rewrite went from 0.1-0.4 to 1.0 on Llama and
  Mistral.

## 8. Derived questions scored right before any edit

- **What happened:** the unedited models got about 15% of derived questions
  "right" with the new answer. Those were mostly yes/no or binary questions
  a model can get right by guessing, or by a reasoning slip. That inflated
  generalizability for every method.
- **Origin:** ours (the metric's design).
- **Fix:** generalizability on Sid's Dataset now counts only determinate
  derived questions the unedited model answered with the original answer
  (`generalization.determinate.known`). Computed from saved answers, so no
  rerun was needed. How to treat the same effect on other question types
  (propositional yes-bias, RBox) is still open.

## 9. Grammar judge too strict

- **What happened:** the first grammar rubric (`sid-form-v1`) marked
  ungrammatical sentences and misspelled words as malformed. The goal is
  only to catch a damaged ability to write, not imperfect writing.
- **Origin:** ours (rubric design).
- **Fix:** `sid-form-v2` passes slips a fluent person could make, and flags
  only garbled, looping, word-salad or nonsense text. Every saved run is
  being re-judged from its stored answers with `rejudge_form.py` (started
  2026-11-04). Done: all 690 screen runs re-judged with no errors
  (2026-11-04). Spot checks: every run the judge now fails is really broken
  (word salad, the new answer repeated in a loop, empty replies).

## 10. FiDAL's default layer band breaks Qwen

- **What happened:** FiDAL tries each layer in `candidate_layers` and edits
  the best 5. Our default band is layers 1-11 on every model. On Qwen, any
  run that picked layer 1 (or 0) with a normal-strength update turned the
  model into word salad ("tant Co tant tant ..."). That includes the default
  settings: rewrite 0, well-formed 0. 5 of 17 Qwen FiDAL screen runs broke;
  runs whose band started at layer 2 or 3 never did. The other three models
  survive layer 1.
- **Origin:** ours. The config widened MEMIT's band [4-8] by three layers on
  each side, which reaches layer 1. Editing Qwen's first layers is not
  safe.
- **Fix:** stage 1 starts FiDAL's band at layer 2 or later on every model
  (`docs/hparam_step1/specs/fidal__*.json`: layers 2-8 or 7-13). The
  default `candidate_layers` in every instruct FiDAL config (Qwen3-4B,
  Olmo-3-7B, Llama-3.1-8B, Mistral-7B and MAP-Neo-7B Instruct) is now
  layers 2-11 instead of 1-11 (2026-11-04). The base, thinking and other
  FiDAL configs still start at layer 1. Step-0 runs are not rerun: their
  results are the evidence for the bug.

## 11. Fluency score blind to word salad

- **What happened:** the fluency score (n-gram entropy, from ROME/MEMIT)
  only drops when text repeats itself. Word salad uses many different words,
  so it scores higher than normal text and gets the full 1.0. The broken
  FiDAL Qwen runs above had fluency 1.0.
- **Origin:** the ROME/MEMIT metric (borrowed project). It was designed to
  catch repetition only.
- **Fix:** none needed for tuning. A run must also pass the grammar judge
  (well-formed >= 0.9), and the judge fails word salad. Worth stating in
  the paper that fluency alone is not enough.

## Not bugs (checked, caused by settings or by the method)

These looked wrong but come from the setting ranges or from how the method
works. Stage 1 of the new plan handles them through its ranges.

- **LoRA and LoCo collapse at high learning rates** (0.0015-0.005): the
  training loss goes up instead of down, and the output turns to nonsense.
  The top of the range is too high.
- **FiDAL learns the edit but does not write it in:** controlled by
  `mom2_update_weight`. At 1,500 almost every run rewrites; at 150,000 most
  do not, even with high training probability.
- **LTI often misses the target:** a high final-token KL weight or a low NLL
  weight pulls the model back toward its original.
- **ROME (7 runs) and FiNE (3 runs):** low probability or fluency drops at
  extreme learning rates and step counts.
- **IFMET skips its second edit for many facts:** 294 of 510 times the model
  cannot confirm a supporting fact about an abstract subject. This is a
  limit of the method on Sid's Dataset.

## Analysis mistakes (no effect on code or results)

- I first said LoCo's fluency loss was a settings problem. It was bug 3.
- I said the unedited models "know" only 16-20 of 40 dev facts, with RBox at
  0. That misread the "known" definition. The model audit shows the models
  get most direct questions right (ABox 57-65/80, TBox 45-56/60, RBox
  32-41/60).
