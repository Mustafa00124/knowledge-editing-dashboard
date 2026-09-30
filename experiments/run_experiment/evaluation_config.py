"""Shared, dependency-free evaluation settings for the runner and dashboard."""
import json
import os
from pathlib import Path

MODES = ("original", "exact_match", "bertscore", "llm_judge")
CONFIG_PATH = Path(__file__).with_name("evaluation.local.json")


def settings():
    cfg = json.loads(CONFIG_PATH.read_text()) if CONFIG_PATH.exists() else {}
    return {
        "api_key": os.environ.get("KE_JUDGE_API_KEY") or cfg.get("api_key", "YOUR_API_KEY_HERE"),
        "base_url": os.environ.get("KE_JUDGE_BASE_URL") or cfg.get("base_url", "https://api.deepseek.com/v1"),
        "judge_model": os.environ.get("KE_JUDGE_MODEL") or cfg.get("judge_model", "deepseek-chat"),
        "bertscore_model": cfg.get("bertscore_model", "sentence-transformers/all-MiniLM-L6-v2"),
        "bertscore_layers": int(cfg.get("bertscore_layers", 6)),
        "max_new_tokens": int(cfg.get("max_new_tokens", 80)),
    }


def judge_configured(cfg=None):
    key = str((cfg or settings())["api_key"]).strip()
    return len(key) >= 16 and not any(word in key.lower() for word in
        ("placeholder", "your_api", "your-api", "replace", "changeme", "example"))


def parse_modes(value):
    parts = value.split(",") if isinstance(value, str) else list(value)
    parts = [p.strip() for p in parts]
    if not parts or any(p not in MODES for p in parts):
        raise ValueError("Select at least one valid evaluation mode: original, exact_match, bertscore, llm_judge")
    return [m for m in MODES if m in parts]


def validate_modes(value):
    modes = parse_modes(value)
    if "llm_judge" in modes and not judge_configured():
        raise ValueError("LLM judge requires a configured API key in evaluation.local.json or KE_JUDGE_API_KEY")
    return modes


def options():
    return [
        {"value": "original", "label": "Original", "available": True},
        {"value": "exact_match", "label": "Exact Match", "available": True},
        {"value": "bertscore", "label": "BERTScore", "available": True},
        {"value": "llm_judge", "label": "LLM Judge", "available": judge_configured(),
         "note": "Configure a judge API key to enable. Authentication is checked when evaluation runs."},
    ]
