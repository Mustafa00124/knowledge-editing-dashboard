"""Shared, dependency-free evaluation settings for the runner and dashboard."""
import json
import os
from pathlib import Path

MODES = ("original", "sid", "sid_main", "exact_match", "bertscore", "llm_judge")
# "sid_main" (sid_main_evaluation.py) is Sid's Dataset's evaluation for the
# main experiments: it extends "sid" (always on there) with determinate-only
# portability, change rates for indeterminate queries, and hinted and
# reasoning probes. Sweeps keep "sid" alone for now.
# "auto" (the runner's default) picks the dataset's own scoring: "sid" for
# Sid's Dataset, "original" for everything else (resolve_modes).
AUTO = "auto"
# Modes scored from the shared free generations (semantic_evaluation.py).
SEMANTIC_MODES = ("exact_match", "bertscore", "llm_judge")
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
    if not parts or any(p not in MODES + (AUTO,) for p in parts):
        raise ValueError("Select at least one valid evaluation mode: auto, original, sid, sid_main, exact_match, "
                         "bertscore, llm_judge")
    return [m for m in (AUTO,) + MODES if m in parts]


def resolve_modes(modes, sids):
    """The modes a run really uses, once the data is known.

    Sid's Dataset (sids true) is scored by its own evaluation, "sid"
    (sid_evaluation.py: generated answers labelled by the SID judge), which
    is always on. EasyEdit's token-accuracy "original" mode does not apply
    to it: delete needs generated answers, and an indeterminate derived query
    has no single gold answer (EasyEdit crashed on its ground_truth None).
    So on Sid's Dataset "auto" and "original" both mean "sid"; the dashboard
    and the sweeps pass "original" by default and keep working. Generated-
    answer modes (exact_match, bertscore, llm_judge) may be added on top.
    Elsewhere "auto" means "original" and "sid" is refused.
    Returns (modes, note): note says what was replaced, or None."""
    modes = list(modes)
    if sids:
        resolved = ["sid"] + (["sid_main"] if "sid_main" in modes else []) + [m for m in modes if m in SEMANTIC_MODES]
        note = ("Sid's Dataset is scored by its own evaluation (sid); EasyEdit's original mode does not run on it"
                if "original" in modes else None)
        return resolved, note
    for mode in ("sid", "sid_main"):
        if mode in modes:
            raise ValueError(f"evaluation mode {mode} scores Sid's Dataset records only "
                             "(--data_path datasets/SidsDataset)")
    resolved = [m for m in MODES if m in modes or (m == "original" and AUTO in modes)]
    return resolved, None


def validate_modes(value):
    modes = parse_modes(value)
    if "llm_judge" in modes and not judge_configured():
        raise ValueError("LLM judge requires a configured API key in evaluation.local.json or KE_JUDGE_API_KEY")
    return modes


def options():
    return [
        {"value": "original", "label": "Original", "available": True,
         "note": "On Sid's Dataset, runs are always scored by Sid's judge instead."},
        {"value": "sid", "label": "Sid's judge", "available": True,
         "note": "Sid's Dataset only, and always on there: generated answers labelled by the local SID judge."},
        {"value": "sid_main", "label": "Sid's judge (main)", "available": True,
         "note": "Sid's Dataset only, for the main experiments: portability on determinate derived queries, "
                 "change rates on indeterminate ones, and hinted and reasoning probes at step 0 and the end."},
        {"value": "exact_match", "label": "Exact Match", "available": True},
        {"value": "bertscore", "label": "BERTScore", "available": True},
        {"value": "llm_judge", "label": "LLM Judge", "available": judge_configured(),
         "note": "Configure a judge API key to enable. Authentication is checked when evaluation runs."},
    ]
