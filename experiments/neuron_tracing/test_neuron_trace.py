"""Neuron attribution on CPU with tiny random models: integrated gradients
is complete (a layer's attributions add up to what its activations do), the
batched layers do not leak into one another, and the summary's selection,
overlap and verdict read synthetic facts correctly.

    venvs/easyedit_venv/bin/python -m unittest experiments/neuron_tracing/test_neuron_trace.py
"""
import os
import sys
import unittest

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import neuron_trace as nt  # noqa: E402
import components as C  # noqa: E402

VOCAB = 50


def tiny(kind):
    import transformers as T
    torch.manual_seed(0)
    if kind == "llama":
        model = T.LlamaForCausalLM(T.LlamaConfig(vocab_size=VOCAB, hidden_size=32, intermediate_size=64,
                                                 num_hidden_layers=4, num_attention_heads=4,
                                                 num_key_value_heads=4, max_position_embeddings=64))
    elif kind == "olmo3":
        model = T.Olmo3ForCausalLM(T.Olmo3Config(vocab_size=VOCAB, hidden_size=32, intermediate_size=64,
                                                 num_hidden_layers=4, num_attention_heads=4,
                                                 num_key_value_heads=4, max_position_embeddings=64))
    else:
        model = T.GPTJForCausalLM(T.GPTJConfig(n_embd=32, n_layer=4, n_head=4, rotary_dim=4, n_positions=64,
                                               vocab_size=VOCAB))
    model = model.float().eval()
    model.requires_grad_(False)
    return model


def inputs():
    ids = torch.randint(0, VOCAB, (1, 6), generator=torch.Generator().manual_seed(1))
    return {"input_ids": ids, "attention_mask": torch.ones_like(ids)}


class AttributionTests(unittest.TestCase):
    def test_completeness_and_batching(self):
        for kind in ("llama", "olmo3", "gptj"):
            model = tiny(kind)
            table = C.resolve(model, need=("neurons",))
            x = inputs()
            logits, acts = nt.neuron_activations(model, x, table)
            target = int(logits.argmax())
            attr = nt.integrated_gradients(model, x, table, acts, target, steps=64, layer_batch=4)
            one_by_one = nt.integrated_gradients(model, x, table, acts, target, steps=64, layer_batch=1)
            self.assertTrue(torch.allclose(attr, one_by_one, atol=1e-6), kind)
            p_full = float(torch.softmax(logits, -1)[target])
            for layer in range(table["n_layers"]):
                every = torch.arange(table["d_neurons"])
                p_off = float(nt.set_neurons(model, table, x, [{layer: (every, 0.0)}])[0, target])
                self.assertAlmostEqual(float(attr[layer].sum()), p_full - p_off, delta=2e-3 + 0.02 * abs(p_full - p_off),
                                       msg=f"{kind} layer {layer}")

    def test_set_neurons_rows_are_independent(self):
        model = tiny("llama")
        table = C.resolve(model, need=("neurons",))
        x = inputs()
        logits, _ = nt.neuron_activations(model, x, table)
        p = nt.set_neurons(model, table, x, [{}, {1: (torch.tensor([0, 1, 2]), 0.0)}, {}])
        self.assertTrue(torch.allclose(p[0], torch.softmax(logits, -1), atol=1e-6))
        self.assertTrue(torch.allclose(p[0], p[2]))
        self.assertFalse(torch.allclose(p[0], p[1]))

    def test_moe_refused(self):
        class Config:
            model_type = "gpt_oss"
        model = torch.nn.Module()
        model.config = Config()
        with self.assertRaises(SystemExit):
            C.resolve(model, need=("neurons",))


class SummaryTests(unittest.TestCase):
    def fact(self, relation, neurons, p_suppress=0.1, p_control=0.48, other=0.45, mass=None):
        return {"relation": relation, "neurons": [(L, i, 1.0) for L, i in neurons], "p_clean": 0.5,
                "p_suppress": p_suppress, "p_control": p_control, "p_enhance": 0.7,
                "other_p_clean": 0.5, "other_p_suppress": other,
                "layer_mass": mass or [0.1, 0.2, 0.3, 0.4], "top10_share": 0.5}

    def test_select(self):
        attr = torch.tensor([[0.0, 1.0, 0.1], [0.5, -2.0, 0.25]])
        self.assertEqual([(L, i) for L, i, _ in nt.select(attr, 0.2, 10)], [(0, 1), (1, 0), (1, 2)])
        self.assertEqual(len(nt.select(attr, 0.2, 1)), 1)
        self.assertEqual(nt.select(-attr.abs(), 0.2, 10), [])

    def test_aggregate(self):
        facts = [self.fact("P1", [(3, 1), (3, 2)]), self.fact("P1", [(3, 1), (0, 5)]),
                 self.fact("P2", [(3, 1), (2, 9)]), self.fact("P2", [(1, 4)])] * 3
        out = nt.aggregate(facts, 4, (0.0, 0.5))
        self.assertEqual(out["peak_layer"], 3)
        self.assertAlmostEqual(sum(out["layer_share"]), 1.0, places=4)
        self.assertEqual(out["hubs"][0]["layer"], 3)
        self.assertEqual(out["hubs"][0]["facts"], 9)
        self.assertGreater(out["overlap"]["same_relation"], out["overlap"]["other_relation"])
        self.assertEqual(out["ablation"]["verdict"], "causal")

    def test_verdicts(self):
        weak = [self.fact("P1", [(1, 1)], p_suppress=0.45, p_control=0.45) for _ in range(10)]
        self.assertEqual(nt.aggregate(weak, 4, (0, 0.5))["ablation"]["verdict"], "not_causal")
        spill = [self.fact("P1", [(1, 1)], p_suppress=0.1, other=0.1) for _ in range(10)]
        self.assertEqual(nt.aggregate(spill, 4, (0, 0.5))["ablation"]["verdict"], "partial")


if __name__ == "__main__":
    unittest.main()
