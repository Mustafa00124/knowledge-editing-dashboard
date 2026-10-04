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
  wilke: {
    tagline: 'ROME, but each fact goes to whichever layer has to move least to absorb it.',
    paper: 'Hu et al., "WilKE: Wise-Layer Knowledge Editor for Lifelong Knowledge Editing" (Findings of ACL 2024, arXiv:2402.10987). Ported from the authors\' code at github.com/ChenhuiHu/WilKE.',
    howItWorks:
      'For every candidate layer 0 .. scanning_ceiling-1, computes the full ROME rank-one update for this fact, applies ' +
      'it, measures LA = ||W_edited - W_original||_F / ||W_original||_F, and restores the weights. The fact is then ' +
      'written into the layer with the smallest LA: the layer that already almost represents the new association. ' +
      "Their compute_u/compute_v are byte-identical to ROME's, so the only WilKE-specific part is this scan, which the " +
      "port runs on top of EasyEdit's own ROME primitives.",
    stepMeaning: 'One fact edited per step, as with ROME. Each step costs one ROME solve per candidate layer.',
    files: [
      { path: 'experiments/run_experiment/dynamic/wilke.py', note: 'the layer scan, using EasyEdit\'s ROME compute_u/compute_v. The winning (u, v) pair is reused rather than recomputed a final time as upstream does, which is arithmetically identical' },
      { path: 'experiments/run_experiment/dynamic/locations.py', note: "writes each fact's chosen layer and the full LA scan to the run's locations.jsonl" },
    ],
    keyHyperparams: [
      { name: 'scanning_ceiling', meaning: 'candidate layers are range(scanning_ceiling): 9 for Qwen3-4B-Base here (the authors use 7). Cost grows linearly with it' },
      { name: 'layers', meaning: 'empty: unused, because the scan decides the layer per fact' },
      { name: 'mom2_adjustment', meaning: 'on, as in the authors\' hparams, so every candidate layer needs its own cached covariance statistics' },
    ],
    caveats: ['The first run against a model computes covariance statistics for every candidate layer, not just one, so it is several times slower than a first ROME run.'],
  },
  fidal: {
    tagline: 'A locator, not an editor: Fisher Information picks the layers, then MEMIT writes them.',
    paper: 'FiDAL, Fisher-driven adaptive locating (ACL 2026, aclanthology.org/2026.acl-long.957). Reimplemented from the paper: no code was released.',
    howItWorks:
      'With every weight frozen, each candidate matrix W gets two small proxy vectors dH and dW and is modulated as ' +
      'W * (1 + dH dW^T). A few gradient steps on the new target\'s cross-entropy train only those proxies, then each ' +
      "matrix is scored by the Fisher Information of its proxies (mean squared gradient). The top_k matrices are " +
      'handed to an existing closed-form editor (base_method, MEMIT by default) in place of its fixed layer list. The ' +
      'modulation is applied through a forward hook, never built as a dense matrix, which keeps probing cheap.',
    stepMeaning: 'One fact probed and edited per step. Each step adds a short probing run in front of a normal base-editor solve.',
    files: [
      { path: 'experiments/run_experiment/dynamic/fidal.py', note: 'probing, Fisher ranking, and the hand-off to EasyEdit\'s ROME/MEMIT/PMET/AlphaEdit' },
      { path: 'experiments/run_experiment/dynamic/locations.py', note: "records each fact's chosen layers and every candidate's Fisher score" },
    ],
    keyHyperparams: [
      { name: 'base_method', meaning: 'the editor that writes the chosen layers: memit here. Every other field in the yaml is that editor\'s own config, copied unchanged so FiDAL vs MEMIT isolates the locating step' },
      { name: 'candidate_layers', meaning: "the layers probed: MEMIT's band [4..8] widened by three on each side, so 1..11 for Qwen3-4B-Base" },
      { name: 'top_k', meaning: 'how many layers get edited: 5, matching MEMIT, so the comparison is about which layers, not how many. Use 1 with base_method rome' },
      { name: 'probe_steps / probe_lr / probe_init', meaning: 'the probing run (10 steps, lr 1e-2, proxies initialized at 1e-3 scale). The paper gives none of these values; they are local choices' },
    ],
    caveats: [
      "The paper probes FFN linear layers in general. Here only the matrix the base editor can write (rewrite_module_tmp, the MLP down projection) is a candidate, since picking any other matrix would give a decision no closed-form editor here could act on.",
      'Covariance statistics get cached for whichever layers end up chosen, so a long run builds them for most of candidate_layers rather than MEMIT\'s five.',
    ],
  },
  fine: {
    tagline: 'Gradient-edits about 20 individual FFN neurons per fact, wherever in the model they are.',
    paper: 'Pan et al., "Precise Localization of Memories: A Fine-grained Neuron-level Knowledge Editing Technique for LLMs" (ICLR 2025, arXiv:2503.01090). Ported from github.com/opanhw/FiNE.',
    howItWorks:
      "For each token the model currently predicts where the new target should go, scores every FFN neuron in every " +
      'unfrozen layer by its activation times the dot product of its output column with that token\'s unembedding, ' +
      'i.e. how hard it pushes toward the current answer. The top neuron_num neurons per position are pooled across all ' +
      'layers at once, so nothing ties a fact to one layer. A delta vector is then learned for each selected neuron by ' +
      'gradient descent (NLL on the target, a KL term holding the prompt distribution, a penalty against repeating the ' +
      'target, and an L2 term), and only those neurons\' columns of the down projection change.',
    stepMeaning: 'One fact located and edited per step, each with its own short optimization (up to epochs iterations, stopping early once the target is likely enough).',
    files: [
      { path: 'experiments/run_experiment/dynamic/fine.py', note: 'the algorithm unchanged; activation capture moved to forward hooks so it runs on every registered model, not just upstream\'s patched Llama/GPT-J' },
      { path: 'experiments/run_experiment/dynamic/capture.py', note: 'the hooks that replace upstream\'s patched transformers modeling files' },
      { path: 'experiments/run_experiment/dynamic/locations.py', note: 'records the (layer, neuron) pairs edited for each fact' },
    ],
    keyHyperparams: [
      { name: 'neuron_num', meaning: 'neurons selected per target-token position, pooled over all layers: 5' },
      { name: 'last_layer', meaning: 'the top 3 layers are frozen and never selected' },
      { name: 'epochs / lr', meaning: 'the per-fact delta optimization: up to 50 Adam steps at 1e-3' },
      { name: 'alpha / beta / gamma', meaning: 'weights of the KL (1), repetition-penalty (10) and L2 (0.1) terms' },
      { name: 'delta_dtype', meaning: 'float32 here; upstream uses bfloat16, which rounds away much of each Adam update at this learning rate' },
    ],
  },
  kn: {
    tagline: 'The original neuron-level editor: find the neurons that express a fact, rewrite their output vectors.',
    paper: 'Dai, Dong, Hao, Sui, Chang & Wei, "Knowledge Neurons in Pretrained Transformers" (ACL 2022). Run through EasyEdit\'s implementation.',
    howItWorks:
      "Scores every FFN neuron by integrated gradients of the original answer's probability with respect to the " +
      "neuron's activation, scaled from zero up to its real value. Neurons above adaptive_threshold times the top " +
      "score are kept (with refine, only those shared across most paraphrases). Each kept neuron's output column is " +
      "then rewritten directly: the embedding of the model's current prediction is subtracted and the new target's " +
      'embedding added. No optimization and no closed-form solve.',
    stepMeaning: 'One fact attributed and edited per step.',
    files: [
      { path: 'experiments/run_experiment/knowledge_neurons.py', note: 'wraps EasyEdit\'s KnowledgeNeurons class: resolves the module layout per architecture (Olmo uses Llama\'s) and returns pre-edit weights the way this runner expects' },
      { path: 'external/EasyEdit/easyeditor/models/kn/knowledge_neurons/knowledge_neurons.py', note: 'attribution and the weight rewrite' },
    ],
    keyHyperparams: [
      { name: 'steps', meaning: "integrated-gradients steps: 20, as in EasyEdit's GPT-J config and the original paper. EasyEdit's Qwen2.5 config uses 1, which collapses it to a plain gradient" },
      { name: 'adaptive_threshold', meaning: "keep neurons scoring above this fraction (0.1) of the fact's top attribution" },
      { name: 'refine / p', meaning: 'refine is off, so neurons come from the single edit prompt and p (the paraphrase-sharing threshold) is unused' },
    ],
    caveats: ['Attribution is to the original answer, so KN only runs on datasets that record it (ground_truth); the runner refuses others.'],
  },
  nmke: {
    tagline: "AlphaEdit's closed-form update, but only the neurons that matter for this batch are allowed to move.",
    paper: '"Edit Less, Achieve More: Dynamic Sparse Neuron Masking for Lifelong Knowledge Editing in LLMs" (NeurIPS 2025, arXiv:2510.22139). Ported from github.com/LiuJinzhe-Keepgoing/NMKE.',
    howItWorks:
      "Runs AlphaEdit's null-space-projected solve on AlphaEdit's own fixed layers, with one added step: each layer's " +
      'update is multiplied by a 0/1 neuron mask before it is written. The mask comes from a per-neuron attribution ' +
      '(how much amplifying that neuron alone raises the predicted token) and is the union of "resonance" neurons, ' +
      'which score above average across many prompts, and "burst" neurons, which peak on any single prompt. How many ' +
      'neurons each set keeps scales with the entropy of the attribution: evidence spread thin across neurons gets a ' +
      'wider mask. The mask is recomputed for every edit batch.',
    stepMeaning: 'Same batch-per-checkpoint-interval behavior as AlphaEdit, with the mask recomputed for each batch.',
    files: [
      { path: 'experiments/run_experiment/dynamic/nmke.py', note: "a copy of EasyEdit's execute_AlphaEdit with the masking step added inside the layer loop (masking afterwards would differ when several layers are edited)" },
      { path: 'experiments/run_experiment/dynamic/capture.py', note: "hooks replacing upstream's patched modeling_llama.py, which is what lets it run on Qwen3 and Olmo-3" },
    ],
    keyHyperparams: [
      { name: 'layers', meaning: "fixed, copied from AlphaEdit's hparams. NMKE chooses neurons within these layers, not the layers themselves" },
      { name: 'resonance_bounds / burst_bounds', meaning: 'the range (0.3 to 0.4) of the share of neurons each set may keep, chosen within by entropy' },
      { name: 'amplify_factor', meaning: 'how strongly each neuron is amplified when probing its attribution: 30, upstream\'s value (lowered from their earlier 100)' },
      { name: 'P_loc', meaning: "NMKE's own cached null-space projection, separate from AlphaEdit's" },
    ],
    caveats: ['Same first-run precompute cost as AlphaEdit. No Mistral-7B hparams, mirroring AlphaEdit.'],
  },
  snke: {
    tagline: 'Listed for completeness; not implemented.',
    howItWorks:
      'A neuron-level knowledge editor. No implementation could be ported: only the paper\'s abstract is public, with ' +
      'no code and no hyperparameter values, so there is nothing faithful to run.',
    caveats: ['Not wired up. Launching is disabled until code or a full method description is available.'],
  },
  cake: {
    tagline: 'Train the edit into the whole reasoning circuit, so multi-hop questions actually use it.',
    paper: 'Yao et al., "CaKE: Circuit-aware Editing Enables Generalizable Knowledge Learners" (EMNLP 2025). Ported from github.com/zjunlp/CaKE.',
    howItWorks:
      "Multi-hop questions read the first hop's answer in later layers, so a fact written into one early layer is " +
      'often never picked up downstream. CaKE instead trains a LoRA adapter on every attention and MLP projection of ' +
      'every layer, on the edit prompt plus circuit-guided data: rephrasings of the edit and reasoning tasks that use ' +
      'the new fact as an intermediate step. The adapter is merged into the weights after each edit.',
    stepMeaning: 'One fact edited per step, each a full LoRA training run (40 epochs over that fact\'s circuit-guided examples).',
    files: [{ path: 'experiments/run_experiment/cake.py', note: 'port of edit_utils.py::cake, matching CaKE\'s released data to our MQuAKE records by subject, prompt and target' }],
    keyHyperparams: [
      { name: 'rank / lora_alpha / lora_dropout', meaning: "upstream's 8 / 32 / 0.05" },
      { name: 'target_modules', meaning: 'q/k/v/o and up/down/gate projections: every attention and MLP matrix' },
      { name: 'num_epochs / lr / batch_size', meaning: "upstream's 40 / 1e-4 / 4, the same for every model" },
      { name: 'mask_padding', meaning: 'false keeps upstream\'s behavior of training on EOS padding too; true leaves padding out of the loss' },
    ],
    caveats: [
      "Runs only on MQuAKE CF-3k-v2 and T: CaKE releases its circuit-guided training data only for MQuAKE, not the code that generates it. Fetch it with setup.py --cake.",
    ],
  },
  mcircke: {
    tagline: 'Map the circuit a multi-hop question uses, then update parameters only inside it. Not implemented.',
    paper: '"Addressing the Reasoning Gap: Mechanistic Circuit-Based Knowledge Editing in Large Language Models" (arXiv:2604.05876).',
    howItWorks:
      'A map-and-adapt procedure: first identify the causal circuit behind a reasoning task, covering both where the ' +
      'fact is stored and how its consequences are routed to the final answer, then update parameters only within ' +
      'that circuit. The paper reports beating CaKE on MQuAKE multi-hop accuracy.',
    caveats: ['Not wired up: there is no public code, and the paper reports no learning rate or step count to reproduce it from.'],
  },
}

export const FAMILY_DETAILS = {
  Finetuning: "Ordinary gradient descent, updates the model's actual weights via training, same as any other ML training loop.",
  'Locate-and-Edit': 'Causal-tracing-based closed-form weight edits: locate where a fact lives, then solve directly for a minimal update, no training loop. The layers are fixed in hparams and the same for every fact.',
  'Dynamic Locate-and-Edit': 'Still whole-layer weight edits, but the layers are chosen separately for each fact instead of fixed in hparams. Each run writes locations.jsonl recording which layers every fact went to.',
  'Neuron Editors': "Don't edit layers as a whole: they pick individual FFN neurons for each fact and change only those neurons' weights. FiNE and Knowledge Neurons pick neurons anywhere in the model; NMKE picks them within AlphaEdit's fixed layers.",
  'Circuit-level': 'Target the circuit that reads and reasons with the fact, across many layers and components, so the edit carries into multi-hop answers.',
  'In-Context': 'No weight changes at all, steer the answer through retrieval and prompting/reasoning instead.',
}
