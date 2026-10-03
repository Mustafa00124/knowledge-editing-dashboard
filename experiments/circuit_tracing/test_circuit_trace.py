"""Circuit tracing on CPU with tiny random models of the three residual
layouts (pre-norm Llama, post-norm Olmo 3, parallel GPT-J): the hooks patch
what they claim to, and attribution patching agrees with real patching where
it must (small corruption, where the first-order estimate is exact).

    venvs/easyedit_venv/bin/python -m unittest experiments/circuit_tracing/test_circuit_trace.py
"""
import os
import sys
import unittest

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import circuit_trace as ct  # noqa: E402
import components as C  # noqa: E402

VOCAB = 50


def tiny(kind):
    import transformers as T
    torch.manual_seed(0)
    common = dict(vocab_size=VOCAB, max_position_embeddings=64)
    if kind == "llama":
        config = T.LlamaConfig(hidden_size=32, intermediate_size=64, num_hidden_layers=4,
                               num_attention_heads=4, num_key_value_heads=2, **common)
        model = T.LlamaForCausalLM(config)
    elif kind == "olmo3":
        config = T.Olmo3Config(hidden_size=32, intermediate_size=64, num_hidden_layers=4,
                               num_attention_heads=4, num_key_value_heads=4, **common)
        model = T.Olmo3ForCausalLM(config)
    else:
        config = T.GPTJConfig(n_embd=32, n_layer=4, n_head=4, rotary_dim=4, n_positions=64, vocab_size=VOCAB)
        model = T.GPTJForCausalLM(config)
    model = model.float().eval()
    model.requires_grad_(False)
    return model


def batch(n_noise=3, length=7):
    ids = torch.randint(0, VOCAB, (1, length), generator=torch.Generator().manual_seed(1))
    return {"input_ids": ids.repeat(1 + n_noise, 1), "attention_mask": torch.ones(1 + n_noise, length, dtype=torch.long)}


def noise_for(model, scale, n_noise=3, tokens=(1, 2)):
    g = torch.Generator().manual_seed(2)
    return scale * torch.randn(n_noise, len(tokens), model.config.hidden_size if hasattr(model.config, "hidden_size")
                               else model.config.n_embd, generator=g), list(tokens)


class CircuitTests(unittest.TestCase):
    KINDS = ("llama", "olmo3", "gptj")

    def setUp(self):
        self.models = {kind: tiny(kind) for kind in self.KINDS}

    def test_tables_resolve(self):
        for kind, model in self.models.items():
            table = C.resolve(model)
            self.assertEqual(table["n_heads"] * table["head_dim"], 32, kind)
            self.assertEqual(table["parallel"], kind == "gptj")
            if kind == "gptj":
                self.assertIn(("block", 0), ct.receivers(table))

    def test_patching_is_consistent(self):
        """No patch on noisy rows is the corrupted run; clean rows with no
        freeze are the clean run; freezing every node at its recorded
        corrupted value in a clean run differs from both (the embedding
        noise is gone but the nodes still carry it)."""
        for kind, model in self.models.items():
            table = C.resolve(model)
            inputs = batch()
            noise, tokens = noise_for(model, 1.0)
            target = 3
            p_corrupt, _ = ct.run_patched(model, inputs, table, target, noise, tokens)
            p_clean, _ = ct.run_patched(model, inputs, table, target, noise, tokens, noisy=False)
            with torch.no_grad():
                ref = torch.softmax(model(input_ids=inputs["input_ids"][:1]).logits[0, -1], -1)[target]
            self.assertAlmostEqual(p_clean, float(ref), places=5, msg=kind)
            every = ct.nodes(table)
            p_all, _ = ct.run_patched(model, inputs, table, target, noise, tokens, restore=every)
            _, captured = ct.run_patched(model, inputs, table, target, noise, tokens, capture=every)
            p_frozen, _ = ct.run_patched(model, inputs, table, target, noise, tokens, freeze=captured)
            self.assertAlmostEqual(p_frozen, p_corrupt, places=5, msg=kind)
            self.assertNotAlmostEqual(p_all, p_corrupt, places=4, msg=kind)

    def test_attribution_matches_patching_when_linear(self):
        """With a tiny corruption the first-order estimate is the effect:
        each node's attribution equals patching it, and the edges into the
        unembedding add up to the whole lost log-probability."""
        for kind, model in self.models.items():
            table = C.resolve(model)
            inputs = batch()
            noise, tokens = noise_for(model, 1e-3)
            target = 3
            att = ct.attribute(model, inputs, table, target, noise, tokens)
            gap = att["logp_clean"] - att["logp_corrupt"]
            self.assertGreater(abs(gap), 1e-7, kind)
            totals = ct.node_totals(att, table)
            for node in [("head", 1, 2), ("mlp", 0), ("mlp", 2), ("head", 3, 0)]:
                actual = ct.run_patched_logp(model, inputs, table, target, noise, tokens, [node]) - att["logp_corrupt"]
                self.assertAlmostEqual(totals[node] / gap, actual / gap, delta=0.05, msg=f"{kind} {node}")
            into_logits = float(att["edges"][:, -1].sum())
            self.assertAlmostEqual(into_logits / gap, 1.0, delta=0.05, msg=kind)

    def test_edges_respect_order(self):
        for kind, model in self.models.items():
            table = C.resolve(model)
            att = ct.attribute(model, batch(), table, 3, *noise_for(model, 1.0))
            send, recv = ct.senders(table), ct.receivers(table)
            for i, s in enumerate(send):
                for j, r in enumerate(recv):
                    if not ct.edge_valid(s, r, table["parallel"]):
                        self.assertEqual(float(att["edges"][i, j]), 0.0)
            # a later MLP never feeds an earlier attention
            self.assertFalse(ct.edge_valid(("mlp", 2), ("attn", 1), False))
            self.assertTrue(ct.edge_valid(("attn", 2), ("mlp", 2), False))
            self.assertFalse(ct.edge_valid(("attn", 2), ("mlp", 2), True))

    def test_circuit_and_verdict(self):
        model = self.models["llama"]
        table = C.resolve(model)
        inputs = batch()
        noise, tokens = noise_for(model, 1.0)
        target = int(torch.softmax(model(input_ids=inputs["input_ids"][:1]).logits[0, -1], -1).argmax())
        att = ct.attribute(model, inputs, table, target, noise, tokens)
        p_corrupt, _ = ct.run_patched(model, inputs, table, target, noise, tokens)
        p_clean, _ = ct.run_patched(model, inputs, table, target, noise, tokens, noisy=False)
        fact = {"p_clean": p_clean, "p_corrupt": p_corrupt, "_replay": (inputs, target, noise, tokens),
                "_totals": ct.node_totals(att, table)}
        ranking = ct.rank_nodes([fact], table)
        self.assertEqual(len(ranking), len(ct.nodes(table)))
        rows = ct.test_circuit(model, table, ranking, [fact, fact], [1, 5, len(ranking)],
                               np.random.default_rng(0))
        self.assertEqual([r["k"] for r in rows], [1, 5, len(ranking)])
        # Every node restored at once beats a random K=1.
        self.assertGreater(rows[-1]["recovery"], rows[0]["random"])
        self.assertEqual(ct.verdict([{"k": 5, "recovery": 0.9, "random": 0.1}]), ("compact", 5))
        self.assertEqual(ct.verdict([{"k": 50, "recovery": 0.85, "random": 0.2}]), ("distributed", 50))
        self.assertEqual(ct.verdict([{"k": 5, "recovery": 0.3, "random": 0.1}]), ("not_found", None))

    def test_position_masks_partition(self):
        masks = ct.position_masks(6, [1, 2])
        self.assertTrue(torch.equal(masks.sum(0), torch.ones(6)))
        self.assertEqual(masks[1, 5].item(), 1)
        # A corruption reaching the last token leaves that token "last".
        masks = ct.position_masks(4, [2, 3])
        self.assertEqual(masks[0, 3].item(), 0)
        self.assertEqual(masks[1, 3].item(), 1)


if __name__ == "__main__":
    unittest.main()
