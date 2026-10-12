"""Give a MAP-Neo checkpoint a stock tokenizer, so it loads without remote code.

MAP-Neo ships its tokenizer as custom code (tokenization_neo.py, class
NEOTokenizer), which AutoTokenizer only runs with trust_remote_code=True. That
class is a thin wrapper around the SentencePiece model in tokenizer.model, so
this script writes the same tokenizer as a stock fast tokenizer (tokenizer.json)
and points tokenizer_config.json at it. Every loader in the project then works
unchanged, and no downloaded code is executed.

The conversion keeps SentencePiece's behaviour that matters here: a "▁" is
always prepended (no whitespace collapsing), so " Paris" encodes as "▁", "▁Paris"
exactly as NEOTokenizer does, and special tokens split the raw text before that
prefix is added. The result is checked against the SentencePiece model itself.
The original config is kept as tokenizer_config.neo.json.

    python scripts/convert_neo_tokenizer.py models/MAP-Neo-7B

Needs transformers and protobuf (the experiment venv). Run again: a no-op.
"""
import json
import shutil
import sys
from pathlib import Path

CHECK_TEXTS = [
    "The capital of France is Paris", " Paris", "  two spaces", "end with space ", "Paris\nLondon\n\nBerlin",
    "Q: Who wrote Hamlet?\nA:", "3.14159 and 1,000,000", "\tTab", "数字 2024 年, ½ café naïve 😀",
]


def convert(model_dir):
    import sentencepiece
    import transformers
    from tokenizers import Tokenizer

    model_dir = Path(model_dir)
    config_path = model_dir / "tokenizer_config.json"
    config = json.loads(config_path.read_text())
    if config.get("tokenizer_class") != "NEOTokenizer":
        print(f"{model_dir.name}: tokenizer is already {config.get('tokenizer_class')}, nothing to do")
        return
    backup = model_dir / "tokenizer_config.neo.json"
    if not backup.exists():
        shutil.copyfile(config_path, backup)

    # LlamaTokenizer reads tokenizer.model through the slow-to-fast converter
    # (this is what needs protobuf), then the pipeline is swapped for
    # SentencePiece's own: Metaspace's prepend_scheme "first" would skip the
    # prefix when the text already starts with a space.
    converted = transformers.LlamaTokenizer.from_pretrained(str(model_dir), add_bos_token=False, add_eos_token=False)
    spec = json.loads(converted.backend_tokenizer.to_str())
    spec["normalizer"] = {"type": "Sequence", "normalizers": [
        {"type": "Prepend", "prepend": "▁"},
        {"type": "Replace", "pattern": {"String": " "}, "content": "▁"},
    ]}
    spec["pre_tokenizer"] = None
    for token in spec["added_tokens"]:
        token["normalized"] = False
    # The generic fast class loads tokenizer.json as written; LlamaTokenizer
    # would rebuild the Metaspace pipeline on every load.
    tok = transformers.PreTrainedTokenizerFast(
        tokenizer_object=Tokenizer.from_str(json.dumps(spec)),
        bos_token="<s>", eos_token="</s>", unk_token="<unk>", pad_token=config.get("pad_token", "<unk>"),
        add_bos_token=config.get("add_bos_token", False), add_eos_token=config.get("add_eos_token", False),
        model_max_length=config.get("model_max_length", 4096),
    )
    if config.get("chat_template"):
        tok.chat_template = config["chat_template"]
    tok.save_pretrained(str(model_dir))

    reloaded = transformers.AutoTokenizer.from_pretrained(str(model_dir))
    sp = sentencepiece.SentencePieceProcessor(model_file=str(model_dir / "tokenizer.model"))
    wrong = [t for t in CHECK_TEXTS if reloaded(t).input_ids != sp.encode(t)]
    if wrong:
        shutil.copyfile(backup, config_path)
        (model_dir / "tokenizer.json").unlink(missing_ok=True)
        raise RuntimeError(f"{model_dir.name}: converted tokenizer disagrees with tokenizer.model on {wrong!r}; "
                           "original config restored")
    print(f"{model_dir.name}: tokenizer converted to {type(reloaded).__name__} (original in {backup.name})")


if __name__ == "__main__":
    for path in sys.argv[1:] or sys.exit(__doc__):
        convert(path)
