"""Model catalog plus installation status for models stored under models/."""
import json

import config


# `name` is also the directory name under models/, which is how installation
# status is resolved. `family` and `model_type` mirror the same two keys in
# experiments/run_experiment/dashboard.json - test_model_catalog.py asserts the
# two catalogs agree, since they are edited independently.
#
# `main` marks the set the current experiments actually run on: four
# families (Qwen3-4B, Olmo-3-7B, Llama-3.1-8B, Mistral-7B), each a base model
# and its post-trained stages. Qwen3 and Olmo keep every stage they have;
# Llama and Mistral are base plus Instruct. Not every main model has hparams
# for every method: both Mistral models lack LoRA, PMET, AlphaEdit and NMKE.
CATALOG = [
    # Qwen3-4B - all four tuning stages off one pretrain.
    {"name": "Qwen3-4B-Base", "repo_id": "Qwen/Qwen3-4B-Base", "parameters_b": 4.0, "architecture": "dense",
     "family": "Qwen3-4B", "model_type": "raw", "main": True},
    {"name": "Qwen3-4B", "repo_id": "Qwen/Qwen3-4B", "parameters_b": 4.0, "architecture": "dense",
     "family": "Qwen3-4B", "model_type": "chat", "main": True},
    {"name": "Qwen3-4B-Instruct-2507", "repo_id": "Qwen/Qwen3-4B-Instruct-2507", "parameters_b": 4.0, "architecture": "dense",
     "family": "Qwen3-4B", "model_type": "chat", "main": True},
    {"name": "Qwen3-4B-Thinking-2507", "repo_id": "Qwen/Qwen3-4B-Thinking-2507", "parameters_b": 4.0, "architecture": "dense",
     "family": "Qwen3-4B", "model_type": "reasoning", "main": True},

    # Olmo 3 - base, instruct and reasoning, fully open pretrain.
    {"name": "Olmo-3-7B-Base", "repo_id": "allenai/Olmo-3-1025-7B", "parameters_b": 7.0, "architecture": "dense",
     "family": "Olmo-3-7B", "model_type": "raw", "main": True},
    {"name": "Olmo-3-7B-Instruct", "repo_id": "allenai/Olmo-3-7B-Instruct", "parameters_b": 7.0, "architecture": "dense",
     "family": "Olmo-3-7B", "model_type": "chat", "main": True},
    {"name": "Olmo-3-7B-Think", "repo_id": "allenai/Olmo-3-7B-Think", "parameters_b": 7.0, "architecture": "dense",
     "family": "Olmo-3-7B", "model_type": "reasoning", "main": True},

    # Base only - EleutherAI released no instruct counterpart, so it cannot be
    # paired, but it is the reference model the ROME/MEMIT papers traced.
    {"name": "GPT-J-6B", "repo_id": "EleutherAI/gpt-j-6b", "parameters_b": 6.0, "architecture": "dense",
     "family": "GPT-J-6B", "model_type": "raw", "main": False},

    # Llama 3.1 - gated. Meta ships no reasoning model, so that leg can only
    # be a third-party distill onto the same base.
    {"name": "Llama-3.1-8B", "repo_id": "meta-llama/Llama-3.1-8B", "parameters_b": 8.0, "architecture": "dense",
     "family": "Llama-3.1-8B", "model_type": "raw", "gated": True, "main": True},
    {"name": "Llama-3.1-8B-Instruct", "repo_id": "meta-llama/Llama-3.1-8B-Instruct", "parameters_b": 8.0, "architecture": "dense",
     "family": "Llama-3.1-8B", "model_type": "chat", "gated": True, "main": True},
    {"name": "DeepSeek-R1-Distill-Llama-8B", "repo_id": "deepseek-ai/DeepSeek-R1-Distill-Llama-8B", "parameters_b": 8.0,
     "architecture": "dense", "family": "Llama-3.1-8B", "model_type": "reasoning"},

    {"name": "Mistral-7B-v0.1", "repo_id": "mistralai/Mistral-7B-v0.1", "parameters_b": 7.0, "architecture": "dense",
     "family": "Mistral-7B", "model_type": "raw", "main": True},
    {"name": "Mistral-7B-Instruct-v0.1", "repo_id": "mistralai/Mistral-7B-Instruct-v0.1", "parameters_b": 7.0,
     "architecture": "dense", "family": "Mistral-7B", "model_type": "chat", "main": True},

    # SmolLM3 and MAP-Neo were the main set from 2026-10-11 to 2026-10-17
    # (open pretraining data); Llama and Mistral are main again.
    # SmolLM3 - base and a post-trained hybrid (reasoning is a chat-template
    # mode, not a separate checkpoint). Open pretraining data.
    {"name": "SmolLM3-3B-Base", "repo_id": "HuggingFaceTB/SmolLM3-3B-Base", "parameters_b": 3.1, "architecture": "dense",
     "family": "SmolLM3-3B", "model_type": "raw"},
    {"name": "SmolLM3-3B", "repo_id": "HuggingFaceTB/SmolLM3-3B", "parameters_b": 3.1, "architecture": "dense",
     "family": "SmolLM3-3B", "model_type": "chat"},

    # MAP-Neo - base and instruct, no reasoning model. Open pretraining data
    # (Matrix). Its tokenizer is custom code, converted to a stock one after
    # download (`convert_tokenizer`).
    {"name": "MAP-Neo-7B", "repo_id": "m-a-p/neo_7b", "parameters_b": 7.8, "architecture": "dense",
     "family": "MAP-Neo-7B", "model_type": "raw", "convert_tokenizer": True},
    {"name": "MAP-Neo-7B-Instruct", "repo_id": "m-a-p/neo_7b_instruct_v0.1", "parameters_b": 7.8, "architecture": "dense",
     "family": "MAP-Neo-7B", "model_type": "chat", "convert_tokenizer": True},

    {"name": "OLMo-2-7B", "repo_id": "allenai/OLMo-2-1124-7B", "parameters_b": 7.0, "architecture": "dense",
     "family": "Other", "model_type": "raw"},
    {"name": "GPT-NeoX-20B", "repo_id": "EleutherAI/gpt-neox-20b", "parameters_b": 20.0, "architecture": "dense",
     "family": "Other", "model_type": "raw"},
    {"name": "Gemma-3-27B", "repo_id": "google/gemma-3-27b-pt", "parameters_b": 27.0, "architecture": "dense",
     "family": "Other", "model_type": "chat", "gated": True},
    # Post-trained only: OpenAI released no base checkpoint, so it has no pair.
    {"name": "GPT-OSS-20B", "repo_id": "openai/gpt-oss-20b", "parameters_b": 20.9, "active_parameters_b": 3.6,
     "architecture": "moe", "family": "Other", "model_type": "reasoning"},
]


# Bytes `scripts/setup.py --models` fetches for each model: the repo minus
# duplicate weight formats (Flax, TF, Metal, ONNX, `original/`, and `.bin` when
# safetensors exist). Measured from the Hugging Face file listings on
# 2026-09-30; the Downloads page shows these before anything is fetched.
DOWNLOAD_BYTES = {
    "Qwen3-4B-Base": 8056521492,
    "Qwen3-4B": 8060926626,
    "Qwen3-4B-Instruct-2507": 8060917568,
    "Qwen3-4B-Thinking-2507": 8060920921,
    "Olmo-3-7B-Base": 14605881703,
    "Olmo-3-7B-Instruct": 14605886599,
    "Olmo-3-7B-Think": 14605886999,
    "SmolLM3-3B-Base": 6167854256,
    "SmolLM3-3B": 6167865576,
    "MAP-Neo-7B": 15588504699,
    "MAP-Neo-7B-Instruct": 15588505099,
    "GPT-J-6B": 24210464962,
    "Llama-3.1-8B": 16069772288,
    "Llama-3.1-8B-Instruct": 16069780550,
    "DeepSeek-R1-Distill-Llama-8B": 16070465043,
    "Mistral-7B-v0.1": 14485840908,
    "Mistral-7B-Instruct-v0.1": 14486339556,
    "OLMo-2-7B": 29204223853,
    "GPT-NeoX-20B": 41297543736,
    "Gemma-3-27B": 54904366652,
    "GPT-OSS-20B": 13789264674,
}
# Patterns never fetched, plus "*.bin"/"*.pth" when the repo has safetensors.
DOWNLOAD_IGNORE = ["*.msgpack", "*.h5", "original/*", "metal/*", "onnx/*"]


def _size_bytes(path):
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file() and ".cache" not in p.parts)


def installed(path):
    """A usable checkpoint: a config plus at least one weights file."""
    if not (path / "config.json").exists():
        return False
    return any(path.glob("*.safetensors")) or any(path.glob("pytorch_model*.bin"))


def list_models():
    output = []
    for model in CATALOG:
        path = config.MODELS_DIR / model["name"]
        complete = installed(path)
        size = _size_bytes(path) if path.exists() else 0
        size_group = "1–8B" if model["parameters_b"] <= 8 else "20–30B"
        output.append({
            **model,
            "size_group": size_group,
            "main": model.get("main", False),
            "status": "installed" if complete else ("downloading" if path.exists() and size else "gated" if model.get("gated") else "not installed"),
            "size_bytes": size,
            "download_bytes": DOWNLOAD_BYTES.get(model["name"]),
            "path": str(path),
        })
    return output
