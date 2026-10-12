"""Where a model's components live, for the tracing experiments that look
below the layer: neuron attribution (one MLP neuron at a time) and circuit
tracing (attention heads, MLPs and the residual-stream paths between them).

causal_trace.py only needs a block, its MLP and its attention. These two
need more, per architecture:

  heads       the attention output projection, whose input is every head's
              output side by side (n_heads x head_dim): a head is a slice of it
  neurons     the MLP down projection, whose input is one activation per
              neuron
  attn_write  the module whose output is what attention adds to the residual
  mlp_write   the same for the MLP (Olmo normalises after each, so for it
              these are the post-norms, not the attention and MLP themselves)
  attn_read   the module whose input is the residual stream as attention
              reads it, and only attention: adding to that input changes what
              attention sees without touching the skip connection
  mlp_read    the same for the MLP; None where attention and MLP read the
              same normalised residual (GPT-J's parallel block)
  final_read  the residual stream as the unembedding reads it

Keyed on config.model_type, like causal_trace.ARCHS, and checked against the
loaded model before anything runs.
"""
import contextlib

_LLAMA = {
    "embed": "model.embed_tokens",
    "heads": "model.layers.{}.self_attn.o_proj",
    "neurons": "model.layers.{}.mlp.down_proj",
    "attn_write": "model.layers.{}.self_attn",
    "mlp_write": "model.layers.{}.mlp",
    "attn_read": "model.layers.{}.input_layernorm",
    "mlp_read": "model.layers.{}.post_attention_layernorm",
    "final_read": "model.norm",
    "parallel": False,
}
# Olmo 2 and 3 normalise each sublayer's output instead of its input, so
# attention and the MLP read the raw residual and write through a norm.
_OLMO = {
    **_LLAMA,
    "attn_write": "model.layers.{}.post_attention_layernorm",
    "mlp_write": "model.layers.{}.post_feedforward_layernorm",
    "attn_read": "model.layers.{}.self_attn",
    "mlp_read": "model.layers.{}.mlp",
}

ARCHS = {
    "gptj": {
        "embed": "transformer.wte",
        "heads": "transformer.h.{}.attn.out_proj",
        "neurons": "transformer.h.{}.mlp.fc_out",
        "attn_write": "transformer.h.{}.attn",
        "mlp_write": "transformer.h.{}.mlp",
        "attn_read": "transformer.h.{}.ln_1",
        "mlp_read": None,
        "final_read": "transformer.ln_f",
        "parallel": True,
    },
    "gpt_neox": {
        "embed": "gpt_neox.embed_in",
        "heads": "gpt_neox.layers.{}.attention.dense",
        "neurons": "gpt_neox.layers.{}.mlp.dense_4h_to_h",
        "attn_write": "gpt_neox.layers.{}.attention",
        "mlp_write": "gpt_neox.layers.{}.mlp",
        "attn_read": "gpt_neox.layers.{}.input_layernorm",
        "mlp_read": "gpt_neox.layers.{}.post_attention_layernorm",
        "final_read": "gpt_neox.final_layer_norm",
        "parallel": True,  # NeoX-20B's use_parallel_residual; checked below
    },
    "olmo2": _OLMO,
    "olmo3": _OLMO,
    # A mixture of experts has no single down projection: no neurons.
    "gpt_oss": {**_LLAMA, "neurons": None},
}
for _model_type in ("llama", "mistral", "qwen2", "qwen3", "smollm3"):
    ARCHS[_model_type] = _LLAMA


def n_layers(model):
    return getattr(model.config, "num_hidden_layers", None) or model.config.n_layer


def resolve(model, need=()):
    """The component table for this model, every template checked against it.

    `need` names the entries the caller cannot do without; a missing one
    (neurons on a mixture of experts) stops the run with the reason."""
    model_type = getattr(model.config, "model_type", None)
    if model_type not in ARCHS:
        raise SystemExit(f"no component templates for model_type {model_type!r}; add it to ARCHS in {__file__}")
    table = dict(ARCHS[model_type])
    if model_type == "gpt_neox":
        table["parallel"] = bool(getattr(model.config, "use_parallel_residual", True))
        if not table["parallel"]:
            raise SystemExit("sequential GPT-NeoX blocks read the MLP input from a norm module not listed here")
    for key in need:
        if not table.get(key):
            raise SystemExit(f"{model_type} has no {key} to trace (mixture-of-experts MLP)")
    for key, template in table.items():
        if not isinstance(template, str):
            continue
        name = template.format(0) if "{}" in template else template
        try:
            model.get_submodule(name)
        except AttributeError as exc:
            raise SystemExit(f"module {name!r} ({key}) not found on this {model_type} model: {exc}")
    heads = model.get_submodule(table["heads"].format(0))
    table["n_heads"] = getattr(model.config, "num_attention_heads", None) or model.config.n_head
    table["head_dim"] = heads.in_features // table["n_heads"]
    if table.get("neurons"):
        table["d_neurons"] = model.get_submodule(table["neurons"].format(0)).in_features
    table["n_layers"] = n_layers(model)
    return table


def out_tensor(output):
    return output[0] if isinstance(output, tuple) else output


def replace_output(output, tensor):
    return (tensor,) + tuple(output[1:]) if isinstance(output, tuple) else tensor


def get_input(args, kwargs):
    """The residual/activation a module was called with: first positional
    argument, or hidden_states= (Olmo's attention is called by keyword)."""
    return args[0] if args else kwargs["hidden_states"]


def set_input(args, kwargs, tensor):
    if args:
        return (tensor,) + tuple(args[1:]), kwargs
    return args, {**kwargs, "hidden_states": tensor}


@contextlib.contextmanager
def hooks(model, forward=(), pre=()):
    """Register (module name, fn) forward hooks and pre-hooks (pre-hooks get
    and may return (args, kwargs)) for the length of a with block."""
    handles = []
    try:
        for name, fn in forward:
            handles.append(model.get_submodule(name).register_forward_hook(fn))
        for name, fn in pre:
            handles.append(model.get_submodule(name).register_forward_pre_hook(fn, with_kwargs=True))
        yield
    finally:
        for handle in handles:
            handle.remove()
