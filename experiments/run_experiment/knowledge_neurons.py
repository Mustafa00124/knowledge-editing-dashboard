"""Knowledge Neurons (Dai et al. 2022) through EasyEdit's implementation
(external/EasyEdit/easyeditor/models/kn), made to run on this project's
models and edit protocols.

The method: score FFN neurons by integrated gradients of the original
answer over the prompt, keep those above an adaptive threshold (and, with
`refine`, shared across most paraphrases), then rewrite their value vectors:
subtract the old answer's embedding and add the new one's.

Two adaptations, no change to the algorithm:
  - EasyEdit picks the architecture from the model path, case-sensitively,
    and knows no Olmo, SmolLM3 or MAP-Neo. GPT-J-6B's directory is upper
    case, and all three have Llama's module layout
    (model.layers.N.mlp.gate_proj/down_proj), so the lookup is resolved here
    and handed over.
  - EasyEdit's apply returns an undo function; this runner's protocols
    expect the pre-edit weights. The layers the edit is about to touch are
    snapshotted and returned under their parameter names.

A known warning case, recorded rather than fixed: EasyEdit's configs
disagree with the original code on the erase/write strengths, and some use
steps: 1, which makes integrated gradients a single-point gradient. The
hparams here use GPT-J's upstream 20 steps.
"""
import os

EASYEDIT_TYPES = {"gpt-j": "gptj", "gptj": "gptj", "qwen3": "qwen3", "qwen2": "qwen2",
                  "mistral": "mistral", "llama": "llama", "olmo": "llama",
                  "smollm3": "llama", "map-neo": "llama"}


def architecture(model_name):
    name = os.path.basename(str(model_name).rstrip("/")).lower()
    for marker, kind in EASYEDIT_TYPES.items():
        if marker in name:
            return kind
    raise ValueError(f"Knowledge Neurons has no module layout for {model_name}")


def apply_knowledge_neurons_to_model(model, tok, requests, hparams, copy=False,
                                     return_orig_weights=False, **kwargs):
    import torch
    from easyeditor.models.kn.knowledge_neurons.knowledge_neurons import KnowledgeNeurons

    request = requests[0]
    if not request.get("ground_truth") or request["ground_truth"] == "<|endoftext|>":
        raise ValueError("Knowledge Neurons needs the original answer (ground_truth) to attribute neurons, "
                         f"and {request['prompt']!r} has none")
    device = f"cuda:{hparams.device}" if torch.cuda.is_available() else "cpu"
    kn = KnowledgeNeurons(model, tok, model_type=architecture(hparams.model_name), device=device)
    neurons = kn.get_refined_neurons(
        [request["prompt"]], request["ground_truth"], p=hparams.p, batch_size=hparams.batch_size,
        steps=hparams.steps, coarse_adaptive_threshold=hparams.adaptive_threshold, refine=hparams.refine)

    originals = {}
    if return_orig_weights:
        for layer in sorted({layer for layer, _ in neurons}):
            name = f"{kn.transformer_layers_attr}.{layer}.{kn.output_ff_attr}"
            originals[name] = dict(model.named_parameters())[name].detach().clone()
    kn.edit_knowledge(request["prompt"], target=request["target_new"], neurons=neurons, undo_modification=False)
    return kn.model, originals
