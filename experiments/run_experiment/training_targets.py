"""The text a fine-tuning editor (FT-M, LoRA, LoCo) trains after the edit prompt.

Upstream EasyEdit trains "<prompt> <answer>" with no end of turn (lora_main.py
has the EOS line commented out; ft_main.py never adds one). Under a chat
prompt the model then learns to say the answer but never to stop, and repeats
it into every reply ("liver liver liver ..."). Fixed here 2026-11-04 for all
three editors, by training the answer followed by the chat template's end of
turn. The answer also keeps the template's lead-in space where it has one
(Mistral), added the same day after Mistral's LoRA runs broke without it.
"""

_SENTINEL = "\u0000ANSWER\u0000"


def turn_end(tok):
    """The text a chat template puts right after an assistant answer (Llama's
    <|eot_id|>, Qwen's <|im_end|>, Mistral's </s>), read off the template
    itself; the tokenizer's EOS when the template gives nothing."""
    try:
        text = tok.apply_chat_template([{"role": "user", "content": "q"}, {"role": "assistant", "content": _SENTINEL}],
                                       tokenize=False)
        end = text.split(_SENTINEL, 1)[1].strip() if _SENTINEL in text else ""
    except Exception:  # no template, or one that refuses these turns
        end = ""
    return end or (tok.eos_token or "")


def turn_start(tok):
    """Whitespace a chat template puts between the generation prompt and the
    answer (Mistral's "[/INST] answer": one space; Qwen, Llama, Olmo: none).
    Without it, Mistral trains on a word piece it never produces there."""
    try:
        user = [{"role": "user", "content": "q"}]
        full = tok.apply_chat_template(user + [{"role": "assistant", "content": _SENTINEL}], tokenize=False)
        gen = tok.apply_chat_template(user, tokenize=False, add_generation_prompt=True)
        lead = full[len(gen):full.index(_SENTINEL)] if full.startswith(gen) and _SENTINEL in full else ""
    except Exception:
        lead = ""
    return lead if lead.isspace() else ""


def answer_text(tok, request):
    """Under Sid's chat format the answer between the template's own lead-in
    whitespace (turn_start) and its end of turn (turn_end); under
    few-shot the answer then the line break that ends it. Other prompts keep
    the bare continuation " <answer>" (upstream behaviour)."""
    target = str(request["target_new"]).strip()
    fmt = (request.get("sids") or {}).get("prompt_format")
    if fmt == "chat":
        return turn_start(tok) + target + turn_end(tok)
    if fmt == "fewshot":
        return " " + target + "\n"
    return " " + target
