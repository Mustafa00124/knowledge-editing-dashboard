"""Causal tracing on CPU: prompt formats, corruption spans, severing and the
reliability summary, with a tiny random Llama and the real Llama tokenizer.

    venvs/easyedit_venv/bin/python -m unittest experiments/causal_tracing/test_causal_trace.py
"""
import argparse
import os
import sys
import unittest

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import causal_trace as ct  # noqa: E402
import formats as F  # noqa: E402

TOKENIZER = ct.MODEL_PATHS["llama-3.1-8b-instruct"]

MQUAKE_ROW = F._row(id="m:0:0", source="m", relation="P36", subject="United Kingdom", answer="London",
                    cloze="The capital of United Kingdom is", question="What is the capital of United Kingdom?")
MCQ_ROW = F._row(id="r:0", source="r", relation="which", answer="Squid Game",
                 question="Which show was renewed for a second season?",
                 choices=["Friends", "Squid Game", "Lost", "Dark"], answer_index=1)
RIDDLE_ROW = next(r for r in F.load_rows(
    os.path.join(ct.PROJECT_ROOT, "datasets/AlteredRiddles/benchmark.jsonl"), "dev"))


def tiny_model(vocab):
    from transformers import LlamaConfig, LlamaForCausalLM
    torch.manual_seed(0)
    config = LlamaConfig(vocab_size=vocab, hidden_size=32, intermediate_size=64, num_hidden_layers=6,
                         num_attention_heads=4, num_key_value_heads=4, max_position_embeddings=512)
    return LlamaForCausalLM(config).eval()


class FormatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from transformers import AutoTokenizer
        cls.tok = AutoTokenizer.from_pretrained(TOKENIZER)

    def corrupted_text(self, item):
        return [item["text"][a:b] for a, b in item["spans"]]

    def test_each_format_corrupts_what_it_says(self):
        self.assertEqual(self.corrupted_text(F.build(MQUAKE_ROW, "completion", self.tok)), ["United Kingdom"])
        self.assertEqual(self.corrupted_text(F.build(MQUAKE_ROW, "question", self.tok)), ["United Kingdom"])
        # The prefill mentions the subject twice: in the question and in the begun reply.
        self.assertEqual(self.corrupted_text(F.build(MQUAKE_ROW, "chat_prefill", self.tok)), ["United Kingdom"] * 2)
        self.assertEqual(self.corrupted_text(F.build(MCQ_ROW, "mcq", self.tok)), [MCQ_ROW["question"]])
        riddle = F.build(RIDDLE_ROW, "riddle", self.tok)
        clue = RIDDLE_ROW["riddle"][RIDDLE_ROW["clue"][0]:RIDDLE_ROW["clue"][1]]
        self.assertEqual(self.corrupted_text(riddle), [clue])

    def test_chat_formats_keep_one_bos(self):
        item = F.build(MQUAKE_ROW, "chat_question", self.tok)
        ids = F.encode(self.tok, item)["input_ids"]
        self.assertEqual(ids.count(self.tok.bos_token_id), 1)
        self.assertTrue(item["text"].rstrip().endswith("assistant<|end_header_id|>"))

    def test_rows_that_cannot_take_a_format_say_so(self):
        self.assertIsNone(F.build(MCQ_ROW, "completion", self.tok))
        self.assertIsNone(F.build(MQUAKE_ROW, "mcq", self.tok))

    def test_mcq_answer_is_the_letter_and_riddles_drop_articles(self):
        self.assertEqual(F.answers_for(MCQ_ROW, "mcq"), ["B"])
        row = F._row(answer="A silence.", aliases=["Silence"])
        self.assertIn("silence", F.answers_for(row, "riddle"))

    def test_riddle_clue_is_the_added_text(self):
        original = "What has to be broken before it can be used?"
        altered = "What has to be broken before it can be used, and is measured in seconds?"
        start, end = F.riddle_clue(original, altered)
        self.assertEqual(altered[start:end], "and is measured in seconds")

    def test_old_fact_set_rows_still_load(self):
        row = F.normalize({"id": "x", "prompt": "The capital of France is", "subject": "France",
                           "answer": "Paris", "relation": "P36"})
        self.assertEqual(F.build(row, "completion", self.tok)["text"], "The capital of France is")


class TraceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from transformers import AutoTokenizer
        cls.tok = AutoTokenizer.from_pretrained(TOKENIZER)
        cls.model = tiny_model(len(cls.tok))
        cls.templates = dict(ct.ARCHS["llama"])

    def args(self, fmt, **extra):
        return argparse.Namespace(format=fmt, n_noise_samples=3, noise_level=0.5, window=3, min_prob=0.0,
                                  token_grid=0, sever=1, **extra)

    def trace(self, row, fmt, monkey_answer=True):
        # A random model knows nothing, so let whatever it predicts count as the answer.
        original = ct.recall_target
        if monkey_answer:
            ct.recall_target = lambda tok, probs, answers, min_prob: int(probs.argmax())
        try:
            return ct.trace_prompt(self.model, self.tok, "cpu", row, self.args(fmt), self.templates, 6,
                                   np.random.default_rng(0))
        finally:
            ct.recall_target = original

    def test_every_format_traces_with_severing(self):
        for row, fmt in [(MQUAKE_ROW, "completion"), (MQUAKE_ROW, "chat_prefill"), (MCQ_ROW, "mcq"),
                         (RIDDLE_ROW, "riddle"), (MQUAKE_ROW, "chat_question")]:
            with self.subTest(fmt=fmt):
                trace = self.trace(row, fmt)
                self.assertIsNotNone(trace)
                self.assertEqual(set(trace["curves"]), set(ct.KINDS + ct.SEVER_KINDS))
                self.assertTrue(all(len(v) == 6 for v in trace["curves"].values()))

    def test_restoring_every_layer_brings_back_the_clean_run(self):
        # The last layer's hidden state restored = the clean logits, whatever the noise.
        trace = self.trace(MQUAKE_ROW, "completion")
        self.assertAlmostEqual(trace["curves"]["hidden"][-1], trace["p_clean"], places=3)

    def test_reliability_summary(self):
        traces = []
        for peak in [1, 1, 2, 2, 2, 4]:
            curve = [0.1] * 6
            curve[peak] = 0.9
            traces.append({"p_clean": 1.0, "p_corrupt": 0.0, "curves": {"mlp": curve}})
        r = ct.reliability(traces, 6, (0.0, 0.5), n_boot=200)
        self.assertEqual(r["band_layers"], [0, 2])
        self.assertAlmostEqual(r["share_peak_in_band"], 5 / 6, places=3)
        self.assertGreater(r["mass_in_band"], r["baseline"])
        self.assertIn(r["verdict"], ("strong", "moderate", "weak"))

    def test_no_localisable_effect_is_inconclusive_not_strong(self):
        # Every fact peaks in the band, but restoring recovers 2% of a big drop.
        traces = [{"p_clean": 0.8, "p_corrupt": 0.3, "curves": {"mlp": [0.31, 0.30, 0.30, 0.30, 0.30, 0.30]}}
                  for _ in range(60)]
        r = ct.reliability(traces, 6, (0.0, 0.5), n_boot=100)
        self.assertEqual(r["share_peak_in_band"], 1.0)
        self.assertEqual(r["verdict"], "inconclusive")

    def test_only_plain_completion_traces_feed_the_edit_layer_hint(self):
        self.assertTrue(ct.feeds_traced_layers({"window": 10}))
        self.assertFalse(ct.feeds_traced_layers({"format": "chat_question", "window": 10}))
        self.assertFalse(ct.feeds_traced_layers({"format": "completion", "window": 1}))


if __name__ == "__main__":
    unittest.main()
