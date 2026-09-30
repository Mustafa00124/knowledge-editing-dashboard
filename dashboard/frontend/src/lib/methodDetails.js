// Educational content for the Methods page - keyed by the same method
// `value` used everywhere else (run_experiment.py --method, dashboard.json's
// method pills). The tree structure itself (families -> methods -> which
// models each has hparams for) comes from the live dashboard.json via
// /api/experiment-types, so it can't drift from what's actually wired up -
// this file only adds the "what is this and how does it work" text that
// dashboard.json was never meant to carry.
export const METHOD_DETAILS = {
  ft: {
    tagline: 'Plain gradient-descent finetuning on the edit itself.',
    paper: 'The generic pre-editing-methods baseline. EasyEdit implements it as "FT-M" (cross-entropy on the target only, used here) vs. "FT-L" (KL/norm-constrained, tuned for tiny ROME-style single-edit updates).',
    howItWorks:
      'Ordinary backprop on (prompt, target_new) pairs, updating whichever layer(s) the hparams name via plain ' +
      'cross-entropy loss on the target text. No causal tracing, no closed-form solve, just training. Scales to ' +
      'any batch size, but has no built-in mechanism to avoid disturbing unrelated knowledge the way the ' +
      'locate-and-edit family does.',
    stepMeaning: 'One gradient step, over the whole ds_size batch simultaneously (not mini-batched further).',
    files: [
      { path: 'external/EasyEdit/easyeditor/models/ft/ft_main.py', note: "EasyEdit's own FT training loop" },
      {
        path: 'experiments/run_experiment/checkpointed_ft.py',
        note:
          "forked from ft_main.py, since EasyEdit's version has no way to pause mid-training and checkpoint. This " +
          'fork adds an on_checkpoint callback, drops the T5/ChatGLM special-case branches (not needed for a ' +
          'decoder-only model), and removes the early-stop-once-loss-is-low guard so the full step-scaling curve ' +
          'comes out instead of an early exit.',
      },
    ],
    keyHyperparams: [
      { name: 'layers', meaning: 'which layer(s) to update: [35] here, the last of Qwen3-4B\'s 36 layers, mirroring the common "edit the last layer" convention' },
      { name: 'lr / num_steps', meaning: "always overridden by run_experiment.py's --lr/--num_steps CLI args, so the yaml values are unused placeholders" },
      { name: 'objective_optimization', meaning: '"target_new" (FT-M) rather than "prompt_last" (FT-L), better suited to a long training run than a tiny single-edit update' },
    ],
  },
  lora: {
    tagline: 'Low-rank adapter training instead of full-weight finetuning.',
    howItWorks:
      "Freezes the base model and trains a small set of low-rank adapter matrices (via PEFT's LoraConfig/" +
      'AdaLoraConfig) inserted into named target modules, then trains those adapters on the same (prompt, ' +
      'target_new) objective FT uses. Cheaper to train than full finetuning, at the cost of a smaller effective ' +
      'parameter budget.',
    stepMeaning: 'Same as FT: one gradient step over the whole ds_size batch each time.',
    files: [
      { path: 'external/EasyEdit/easyeditor/models/lora/lora_main.py', note: 'only its chunks/AverageMeter helpers are reused, the training loop itself is forked, same reason as FT' },
      { path: 'experiments/run_experiment/run_experiment.py', note: 'the actual get_peft_model() wrapping happens here, once, before any checkpoint, not inside checkpointed_lora.py' },
      {
        path: 'experiments/run_experiment/checkpointed_lora.py',
        note:
          'forked the same way checkpointed_ft.py was, plus explicit .eval()/.train() toggling around checkpoints. ' +
          "LoRA's dropout is nonzero, so without this a checkpoint's evaluation would run with dropout still active.",
      },
    ],
    keyHyperparams: [
      { name: 'lora_type', meaning: '"lora" or "adalora" (adaptive-rank variant); adalora is what\'s configured here' },
      { name: 'rank / lora_alpha / lora_dropout', meaning: 'adapter capacity, output scaling, and regularization' },
      { name: 'target_modules', meaning: 'which weight matrices get an adapter, e.g. GPT-J\'s fc_in/fc_out MLP projections' },
    ],
  },
  rome: {
    tagline: 'A single closed-form rank-one edit per fact, based on causal tracing.',
    paper: 'Meng, Bau, Andonian & Belinkov, "Locating and Editing Factual Associations in GPT" (NeurIPS 2022).',
    howItWorks:
      "Locates a fact's storage as a key-value association inside one MLP layer (identified in the original " +
      'paper via causal tracing) and solves in closed form for a minimal rank-one weight update that changes the ' +
      "key's output from the old value to the new one, subject to a norm constraint so the update stays small. " +
      'No training loop, just linear algebra, one fact at a time.',
    stepMeaning: "One closed-form edit per fact, applied sequentially. 'Step i' means i facts have been edited into the model so far.",
    files: [{ path: 'external/EasyEdit/easyeditor/models/rome/rome_main.py', note: "imported directly, not forked. Every locate-and-edit method is called straight from EasyEdit's own apply_*_to_model function via run_experiment.py's LOCATE_AND_EDIT registry" }],
    keyHyperparams: [
      { name: 'layers', meaning: 'the single layer to edit: [5] here, inherited from EasyEdit\'s own qwen2.5-7b.yaml convention, not independently re-tuned for Qwen3-4B' },
      { name: 'v_num_grad_steps / v_lr', meaning: 'ROME does run a small internal gradient search, but only to find the target *value* vector before solving the closed-form update, not to train the model' },
      { name: 'mom2_adjustment', meaning: "off. A single-layer edit doesn't need the covariance-based preservation term MEMIT/PMET/AlphaEdit rely on" },
    ],
  },
  memit: {
    tagline: "ROME's batch cousin: thousands of edits distributed across several MLP layers at once.",
    paper: 'Meng, Sharma, Andonian, Belinkov & Bau, "Mass-Editing Memory in a Transformer" (arXiv:2210.07229, ICLR 2023).',
    howItWorks:
      'Solves the same key-value association problem as ROME, but spreads the update across several MLP layers ' +
      'jointly (layers [4,5,6,7,8] here) rather than concentrating it in one, and solves for many facts ' +
      'simultaneously with a regularization term that penalizes disturbing a cached sample of existing (key, value) pairs.',
    stepMeaning: 'One batch solve per checkpoint interval. Every fact accumulated since the last checkpoint is edited in together, not one call per fact (both more faithful to how MEMIT is meant to be used, and cheaper).',
    files: [{ path: 'external/EasyEdit/easyeditor/models/memit/memit_main.py' }],
    keyHyperparams: [
      {
        name: 'mom2_adjustment',
        meaning:
          'on. This is what actually makes MEMIT MEMIT: the covariance-based preservation term. The *first* run ' +
          'against a given model computes and caches ~100k Wikipedia-sample covariance statistics per targeted ' +
          'layer (stats_dir), noticeably slower than every later run, which reuses the cache.',
      },
      { name: 'layers', meaning: 'which layers to spread the edit across: 5 early-to-mid layers here' },
    ],
    caveats: ['Nothing is precomputed on this system as of writing. The first real launch against a given model pays that one-time covariance-statistics cost.'],
  },
  pmet: {
    tagline: 'MEMIT plus a second, separate update for the attention sublayer.',
    paper: '"PMET: Precise Model Editing in a Transformer" (Li et al., AAAI 2024). Cited with moderate confidence, not independently re-verified this session the way ROME/MEMIT/AlphaEdit\'s citations were.',
    howItWorks:
      "Extends MEMIT's approach by optimizing target representations for both the MLP output *and* the attention " +
      "output separately (its compute_zs solves for the attention and MLP targets independently), on the " +
      "reasoning that a fact's association isn't stored purely in the MLP. Disentangling the two lets the MLP " +
      'update focus on the factual association while attention handles retrieval/routing.',
    stepMeaning: 'Same batch-per-checkpoint-interval behavior as MEMIT.',
    files: [{ path: 'external/EasyEdit/easyeditor/models/pmet/pmet_main.py' }],
    keyHyperparams: [
      { name: 'attn_module_tmp / mlp_module_tmp', meaning: 'separate module name templates for the two sublayers being jointly optimized. MEMIT/ROME only ever have the MLP one' },
      { name: 'mom2_adjustment', meaning: 'same covariance-caching behavior and first-run cost as MEMIT' },
    ],
    caveats: ['Same first-run covariance-statistics cost as MEMIT.'],
  },
  alphaedit: {
    tagline: "MEMIT with a mathematical guarantee, not just a soft regularizer, that preserved facts don't move.",
    paper: 'Fang, Jiang, Wang, Ma, Jie, Wang, He & Chua, "AlphaEdit: Null-Space Constrained Knowledge Editing for Language Models" (ICLR 2025).',
    howItWorks:
      "Instead of MEMIT's penalty term (which discourages disturbing existing facts but doesn't prevent it), " +
      'AlphaEdit first computes the null-space of the preserved knowledge keys: a projection matrix P such that ' +
      "P·K₀ = 0. It then solves for the new fact's update and projects it into that null-space before applying it. " +
      "Any update confined to this subspace is mathematically guaranteed to leave the preserved facts' outputs unchanged.",
    stepMeaning: 'Same batch-per-checkpoint-interval behavior as MEMIT.',
    files: [{ path: 'external/EasyEdit/easyeditor/models/alphaedit/AlphaEdit_main.py' }],
    keyHyperparams: [
      { name: 'P_loc', meaning: "path to the cached null-space projection matrix (alphaedit_P_<model>.pt), like MEMIT's covariance stats, computed once on first use and reused after" },
      { name: 'mom2_adjustment', meaning: 'on, same covariance-caching mechanism MEMIT/PMET use, feeding into the null-space computation' },
    ],
    caveats: ['Same first-run precompute cost as MEMIT, plus its own P_loc projection-matrix cache.'],
  },
  ike: {
    tagline: 'No weight changes at all, just better few-shot prompting.',
    paper: 'Based on the in-context-editing approach from Zheng et al., "Can We Edit Factual Knowledge by In-Context Learning?" (EMNLP 2023). Cited with moderate confidence.',
    howItWorks:
      'Retrieves the most similar previously-seen edit demonstrations (via sentence-embedding cosine similarity) ' +
      'and prepends them as few-shot "New Fact: ... Prompt: ... Answer: ..." examples ahead of the actual ' +
      "question, steering the model's answer through in-context learning rather than touching its weights.",
    stepMeaning:
      'One demonstration added to the retrievable pool per step. Unlike every other method, the *test* set being ' +
      'evaluated stays fixed throughout: what grows is a separate demonstration pool built from a held-out train split.',
    files: [{ path: 'experiments/run_experiment/ike.py', note: 'built from scratch, not imported from EasyEdit' }],
    caveats: [
      "EasyEdit's own apply_ike_to_model requires a precomputed embedding pickle at an undocumented path, built " +
      'by a separate un-wired encode_ike_facts() call. Fragile enough that this project reimplements it ' +
      "directly instead, reusing SCR's own retrieval index (SCRIndex in scr.py).",
    ],
  },
  scr: {
    tagline: 'Retrieval-augmented reasoning: show the model the fact, then make it decide.',
    paper: 'Not shipped in EasyEdit. Implemented in this project directly, based on the "Selective Contextual Reasoning" approach discussed when this dataset/method wiring work started.',
    howItWorks:
      'Like IKE, never touches model weights. Retrieves the most relevant facts from a growing knowledge base ' +
      '(the same embedding-similarity index IKE uses) and asks the model an explicit yes/no confirmation ' +
      'question about the retrieved fact before generating its final answer, rather than just prepending it as a ' +
      'few-shot example the way IKE does.',
    stepMeaning: 'One fact added to the retrievable knowledge base per step.',
    files: [{ path: 'experiments/run_experiment/scr.py', note: 'built from scratch' }],
  },
}

export const FAMILY_DETAILS = {
  Finetuning: "Ordinary gradient descent, updates the model's actual weights via training, same as any other ML training loop.",
  'Locate-and-Edit': 'Causal-tracing-based closed-form weight edits: locate where a fact lives, then solve directly for a minimal update, no training loop.',
  'In-Context': 'No weight changes at all, steer the answer through retrieval and prompting/reasoning instead.',
}
