"""Architecture-generic access to the internals both FiNE and NMKE need.

Both reference implementations get at FFN neuron activations by running
a *patched* transformers modeling file: FiNE calls
`model.set_get_activations()` and reads `model.activations`, NMKE ships a
3145-line modeling_llama.py and tells you to copy it over the one in
site-packages. Neither works here:

  - Patching site-packages would apply to every method in the project,
    including the ones already validated, and would have to be redone on
    every venv rebuild.
  - Both patches are Llama-only (NMKE) or Llama/GPT-J-only (FiNE), while
    the models registered in run_experiment.py include Qwen3, Olmo-3 and
    Mistral.

The quantities those patches expose are all recoverable from stock
transformers: the neuron activations are the *input* to each layer's FFN
down-projection (the module hparams already names in rewrite_module_tmp),
and the per-layer residual stream is what output_hidden_states=True
already returns. So this module captures them with forward hooks, keyed
off the same hparams fields the editing methods already rely on, which
keeps every registered model supported and leaves site-packages alone.
"""
import torch


def module_name(hparams, layer):
    """The FFN matrix a locate-and-edit method writes into, at `layer`.

    Same string the editing code uses, so activations are always
    captured for exactly the matrix that later gets modified.
    """
    return hparams.rewrite_module_tmp.format(layer)


def get_module(model, name):
    module = model
    for part in name.split("."):
        module = getattr(module, part)
    return module


def num_layers(model):
    config = model.config
    for attr in ("num_hidden_layers", "n_layer", "num_layers"):
        value = getattr(config, attr, None)
        if value is not None:
            return value
    raise ValueError(f"cannot determine layer count for {config.model_type}")


def unembedding(model):
    """The (vocab, hidden) matrix that decodes a residual vector to logits.

    Read off the model rather than from hparams.lm_head_module on
    purpose: Qwen3 and Olmo-3 tie their embeddings, so lm_head.weight
    does not exist under that name in named_parameters() and the
    hparams files disagree with each other about whether to say
    "lm_head" or "model.embed_tokens" (compare hparams/MEMIT/qwen3-4b.yaml
    with hparams/AlphaEdit/qwen3-4b.yaml). get_output_embeddings()
    resolves the tie the same way the model's own forward pass does.
    """
    head = model.get_output_embeddings()
    if head is None:
        raise ValueError("model exposes no output embedding to decode with")
    return head.weight


def final_norm(model, hparams):
    return get_module(model, hparams.ln_f_module)


def logits_from_residual(model, hparams, residual, fixed_variance=None):
    """Project a residual-stream vector through the final norm and unembedding.

    This is the logit lens both FiNE's neuron scoring and NMKE's
    attribution use. `fixed_variance` reproduces NMKE's choice of
    normalising every probe vector by the *final* hidden state's
    variance rather than each vector's own, which keeps the scale
    comparable across the perturbed and unperturbed probes it compares.
    Pass None to normalise each vector on its own terms.
    """
    norm = final_norm(model, hparams)
    residual = residual.to(norm.weight.dtype if hasattr(norm, "weight") else residual.dtype)
    if fixed_variance is None:
        normed = norm(residual)
    else:
        eps = getattr(norm, "variance_epsilon", getattr(norm, "eps", 1e-6))
        if isinstance(norm, torch.nn.LayerNorm):
            centered = residual - residual.mean(-1, keepdim=True)
            normed = centered * torch.rsqrt(fixed_variance + eps) * norm.weight + norm.bias
        else:  # RMSNorm and its per-architecture reimplementations
            normed = residual * torch.rsqrt(fixed_variance + eps) * norm.weight
    return normed @ unembedding(model).to(normed.dtype).T


class FFNActivations:
    """Captures the input to each layer's FFN down-projection.

    That input is the post-activation hidden vector of the FFN, i.e. one
    scalar per "neuron" in the sense both FiNE and NMKE use the word:
    neuron i of layer l contributes activation[i] * W_down[:, i] to the
    residual stream. Capturing the module input rather than recomputing
    it from the gate/up projections means the same code covers GPT-J's
    fc_out and every Llama-style mlp.down_proj without knowing which is
    which.

    Usage:
        with FFNActivations(model, hparams, layers) as acts:
            model(**inputs)
        acts.stack()            # (layers, batch, seq, d_ff)
    """

    def __init__(self, model, hparams, layers):
        self.layers = list(layers)
        self.model = model
        self.hparams = hparams
        self._captured = {}
        self._handles = []

    def __enter__(self):
        def make_hook(layer):
            def hook(module, args):
                # Pre-hook: args[0] is the down-projection's input, which
                # is what we want, before it is mixed back into the
                # residual stream.
                self._captured[layer] = args[0].detach()
            return hook

        for layer in self.layers:
            module = get_module(self.model, module_name(self.hparams, layer))
            self._handles.append(module.register_forward_pre_hook(make_hook(layer)))
        return self

    def __exit__(self, *exc):
        for handle in self._handles:
            handle.remove()
        self._handles = []
        return False

    def stack(self):
        missing = [layer for layer in self.layers if layer not in self._captured]
        if missing:
            raise RuntimeError(
                f"no activation captured for layers {missing} - did the forward pass run "
                "inside the `with` block?"
            )
        return torch.stack([self._captured[layer] for layer in self.layers])

    def at(self, layer):
        return self._captured[layer]
