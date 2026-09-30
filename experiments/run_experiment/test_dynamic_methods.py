"""Tests for the dynamic locate-and-edit methods in dynamic/.

The interesting claims these make are about *where* they edit, so the
tests check localisation directly: that the captured activations are the
tensor the scoring formula assumes, that the neuron scores match a
brute-force computation of the paper's formula, that only the selected
parameters move, and that FiDAL's hooked modulation equals the dense
weight modulation it stands in for.

Everything runs on a randomly initialised 4-layer model on CPU, so the
suite needs no GPU and no downloaded weights - only a local tokenizer.
"""
import os
import sys
import unittest

import torch

EXP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(EXP_DIR))
EASYEDIT = os.path.join(PROJECT_ROOT, "external/EasyEdit")
TOKENIZER = os.path.join(PROJECT_ROOT, "models/Qwen3-4B")
for path in (EXP_DIR, EASYEDIT):
    if path not in sys.path:
        sys.path.insert(0, path)

from dynamic import capture, fidal, fine, locations, nmke, wilke  # noqa: E402


def tiny_model():
    from transformers import AutoTokenizer, LlamaConfig, LlamaForCausalLM

    tok = AutoTokenizer.from_pretrained(TOKENIZER)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    config = LlamaConfig(
        vocab_size=len(tok), hidden_size=32, intermediate_size=64,
        num_hidden_layers=4, num_attention_heads=4, num_key_value_heads=4,
    )
    torch.manual_seed(0)
    model = LlamaForCausalLM(config).eval()
    return model, tok


def fine_hparams():
    return fine.FiNEHyperParams(
        alg_name="FiNE", model_name="tiny-llama", device=0,
        rewrite_module_tmp="model.layers.{}.mlp.down_proj",
        layer_module_tmp="model.layers.{}",
        mlp_module_tmp="model.layers.{}.mlp",
        attn_module_tmp="model.layers.{}.self_attn",
        ln_f_module="model.norm", lm_head_module="lm_head",
        epochs=2, neuron_num=2, last_layer=1, early_stop_prob=None,
    )


class CaptureTests(unittest.TestCase):
    def test_captured_activation_is_the_down_projection_input(self):
        model, tok = tiny_model()
        hparams = fine_hparams()
        inputs = tok("The Eiffel Tower is in", return_tensors="pt")

        reference = {}

        def spy(module, args):
            reference["value"] = args[0].detach().clone()

        handle = capture.get_module(model, "model.layers.2.mlp.down_proj").register_forward_pre_hook(spy)
        with torch.no_grad(), capture.FFNActivations(model, hparams, [0, 1, 2]) as acts:
            model(**inputs)
        handle.remove()

        torch.testing.assert_close(acts.at(2), reference["value"])
        self.assertEqual(acts.stack().shape[0], 3)
        self.assertEqual(acts.at(2).shape[-1], model.config.intermediate_size)

    def test_unembedding_resolves_tied_weights(self):
        model, _ = tiny_model()
        self.assertIs(capture.unembedding(model), model.lm_head.weight)
        model.config.tie_word_embeddings = True
        model.tie_weights()
        # A tied model has no independent lm_head.weight, which is what
        # breaks nethook lookups by name for Qwen3 and Olmo-3.
        torch.testing.assert_close(capture.unembedding(model), model.model.embed_tokens.weight)

    def test_missing_forward_pass_is_an_error_not_a_silent_empty(self):
        model, _ = tiny_model()
        with capture.FFNActivations(model, fine_hparams(), [0]) as acts:
            pass
        with self.assertRaises(RuntimeError):
            acts.stack()


class FiNETests(unittest.TestCase):
    def test_scores_match_the_papers_formula(self):
        model, tok = tiny_model()
        hparams = fine_hparams()
        layers = [0, 1, 2]
        inputs = tok("Paris is the capital of", return_tensors="pt")
        with torch.no_grad(), capture.FFNActivations(model, hparams, layers) as acts:
            model(**inputs)
        activations = acts.stack()[:, 0, -2:, :]
        token_ids = [5, 11]

        scores = fine.score_neurons(model, hparams, activations, token_ids, layers)
        self.assertEqual(tuple(scores.shape), (2, 3, model.config.intermediate_size))

        # Brute force: c(i, l) = a * (W_out[:, i] . U[t]) for one cell.
        position, layer_index, neuron = 1, 2, 7
        weight = capture.get_module(model, "model.layers.2.mlp.down_proj").weight
        expected = activations[layer_index, position, neuron].float() * torch.dot(
            weight[:, neuron].float(), capture.unembedding(model)[token_ids[position]].float()
        )
        torch.testing.assert_close(scores[position, layer_index, neuron], expected, rtol=1e-4, atol=1e-5)

    def test_selection_spans_layers_and_respects_the_frozen_tail(self):
        layers = [0, 1, 2]
        scores = torch.zeros(1, 3, 8)
        scores[0, 0, 4] = 10.0
        scores[0, 2, 1] = 9.0
        selected = fine.select_neurons(scores, 2, layers)
        self.assertEqual(sorted(selected), [(0, 4), (2, 1)])

    def test_edit_touches_only_the_selected_columns(self):
        model, tok = tiny_model()
        hparams = fine_hparams()
        before = {name: param.detach().clone() for name, param in model.named_parameters()}

        locations.drain()
        model, weights_copy = fine.apply_fine_to_model(
            model, tok,
            [{"prompt": "The capital of France is", "subject": "France", "target_new": "Rome"}],
            hparams, return_orig_weights=True,
        )
        records = locations.drain()
        self.assertEqual(len(records), 1)
        edited = {(layer, neuron) for layer, neuron in records[0]["neurons"]}

        # The last layer is frozen by last_layer=1 and must never be picked.
        self.assertTrue(all(layer < model.config.num_hidden_layers - 1 for layer, _ in edited))

        changed = [name for name, param in model.named_parameters()
                   if not torch.equal(param, before[name])]
        self.assertTrue(changed, "the edit changed nothing at all")
        for name in changed:
            self.assertIn("mlp.down_proj.weight", name)
            layer = int(name.split(".")[2])
            columns = (model.get_parameter(name) != before[name]).any(dim=0).nonzero().flatten().tolist()
            for column in columns:
                self.assertIn((layer, column), edited)

        # weights_copy must restore the model exactly, since the runner
        # uses it to roll back between edit groups.
        with torch.no_grad():
            for name, original in weights_copy.items():
                model.get_parameter(name).copy_(original)
        for name, param in model.named_parameters():
            torch.testing.assert_close(param, before[name])


class NMKEMaskTests(unittest.TestCase):
    def test_entropy_ratios_stay_inside_their_bounds(self):
        hparams = nmke.NMKEHyperParams.from_hparams(
            os.path.join(EXP_DIR, "hparams/NMKE/gpt-j-6b.yaml"))
        for scores in (torch.randn(4, 256), torch.zeros(4, 256), torch.rand(4, 256) * 100):
            resonance, burst = nmke.entropy_adaptive_mask_ratio(scores, hparams)
            self.assertGreaterEqual(resonance, hparams.resonance_bounds[0] - 1e-6)
            self.assertLessEqual(resonance, hparams.resonance_bounds[1] + 1e-6)
            self.assertGreaterEqual(burst, hparams.burst_bounds[0] - 1e-6)
            self.assertLessEqual(burst, hparams.burst_bounds[1] + 1e-6)

    def test_mask_is_binary_and_keeps_the_high_scoring_neurons(self):
        torch.manual_seed(0)
        scores = torch.randn(6, 512)
        scores[:, 100] += 20.0  # consistently high: resonance and burst
        mask, resonance, burst = nmke.hybrid_resonant_mask(scores, 0.3, 0.3)
        self.assertEqual(set(mask.unique().tolist()), {0.0, 1.0})
        self.assertEqual(mask[100].item(), 1.0)
        # Union, so the kept set is at least as large as either part.
        self.assertGreaterEqual(mask.sum().item(), resonance.sum().item())
        self.assertGreaterEqual(mask.sum().item(), burst.sum().item())

    def test_mask_freezes_neurons_row_wise(self):
        update = torch.ones(8, 4)
        mask = torch.tensor([1.0, 0, 1, 0, 1, 0, 1, 0])
        masked = mask[:, None] * update
        self.assertEqual(masked[1].abs().sum().item(), 0.0)
        self.assertEqual(masked[0].abs().sum().item(), 4.0)

    def test_disabling_both_selectors_edits_everything_rather_than_nothing(self):
        mask, _, _ = nmke.hybrid_resonant_mask(torch.randn(3, 64), 0.3, 0.3,
                                               use_resonance=False, use_burst=False)
        self.assertEqual(mask.sum().item(), 64)


class FiDALTests(unittest.TestCase):
    def _hparams(self, model):
        hparams = fidal.FiDALHyperParams.from_hparams(
            os.path.join(EXP_DIR, "hparams/FiDAL/qwen3-4b.yaml"))
        hparams.candidate_layers = [0, 1, 2]
        hparams.top_k = 2
        hparams.probe_steps = 2
        hparams.base_config["model_name"] = "tiny-llama"
        hparams.base_config["v_loss_layer"] = model.config.num_hidden_layers - 1
        return hparams

    def test_modulation_hook_equals_the_dense_weight_modulation(self):
        torch.manual_seed(0)
        module = torch.nn.Linear(6, 4, bias=False)
        modulation = fidal._Modulation(module, scale=0.1, device="cpu", dtype=torch.float32)
        x = torch.randn(2, 6)
        got = module(x)
        modulation.remove()

        dense = module.weight * (1 + torch.outer(modulation.dh, modulation.dw))
        torch.testing.assert_close(got, x @ dense.T, rtol=1e-5, atol=1e-6)

    def test_probe_scores_every_candidate_and_returns_top_k(self):
        model, tok = tiny_model()
        hparams = self._hparams(model)
        requests = [{"prompt": "The capital of France is", "subject": "France", "target_new": "Rome"}]

        chosen, scores = fidal.probe(model, tok, requests, hparams)
        self.assertEqual(sorted(scores), hparams.candidate_layers)
        self.assertEqual(len(chosen), hparams.top_k)
        self.assertEqual(set(chosen), set(sorted(scores, key=scores.get, reverse=True)[:hparams.top_k]))
        self.assertTrue(all(score >= 0 for score in scores.values()), "Fisher scores are squared gradients")

    def test_probing_leaves_the_model_untouched(self):
        model, tok = tiny_model()
        hparams = self._hparams(model)
        before = {name: param.detach().clone() for name, param in model.named_parameters()}
        grads = {name: param.requires_grad for name, param in model.named_parameters()}

        fidal.probe(model, tok, [{"prompt": "Paris is in", "subject": "Paris", "target_new": "Spain"}], hparams)

        for name, param in model.named_parameters():
            torch.testing.assert_close(param, before[name])
            self.assertEqual(param.requires_grad, grads[name])

    def test_unknown_base_editor_is_rejected_at_load(self):
        import tempfile
        import yaml

        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as handle:
            yaml.safe_dump({"alg_name": "FiDAL", "base_method": "ike", "model_name": "x",
                            "device": 0, "candidate_layers": [1]}, handle)
        with self.assertRaises(ValueError):
            fidal.FiDALHyperParams.from_hparams(handle.name)
        os.unlink(handle.name)


class WilKETests(unittest.TestCase):
    def test_candidates_are_the_layers_below_the_ceiling(self):
        hparams = wilke.WilKEHyperParams.from_hparams(
            os.path.join(EXP_DIR, "hparams/WilKE/gpt-j-6b.yaml"))
        self.assertEqual(hparams.scanning_ceiling, 7)  # upstream's own value for GPT-J
        self.assertEqual(wilke.candidate_layers(hparams), list(range(7)))

    def test_update_shape_matching_handles_transposed_weights(self):
        update = torch.zeros(4, 6)
        self.assertEqual(wilke._match_shape(update, torch.Size([4, 6])).shape, (4, 6))
        self.assertEqual(wilke._match_shape(update, torch.Size([6, 4])).shape, (6, 4))
        with self.assertRaises(ValueError):
            wilke._match_shape(update, torch.Size([5, 5]))


class LocationLogTests(unittest.TestCase):
    def test_histogram_counts_each_fact_once_per_layer(self):
        locations.drain()
        locations.record("fine", "p1", "s1", layers=[2, 2, 5])
        locations.record("fine", "p2", "s2", layers=[5])
        locations.record("wilke", "p3", "s3", layer=2, layers=[2])
        records = locations.drain()
        self.assertEqual(locations.layer_histogram(records), {2: 2, 5: 2})
        self.assertEqual(locations.drain(), [], "drain must not hand the same records out twice")


class RegistryTests(unittest.TestCase):
    def test_registry_and_edit_protocol_agree_on_batching(self):
        import run_experiment
        from edit_protocol import JOINT_BATCH_METHODS, WEIGHT_EDIT_METHODS

        for method, spec in run_experiment.LOCATE_AND_EDIT.items():
            self.assertIn(method, WEIGHT_EDIT_METHODS, f"{method} edits weights")
            self.assertEqual(
                spec["mode"] == "batch", method in JOINT_BATCH_METHODS,
                f"{method}: LOCATE_AND_EDIT mode and JOINT_BATCH_METHODS disagree",
            )

    def test_every_registered_method_model_pair_has_hparams_that_load(self):
        import run_experiment

        classes = {"wilke": wilke.WilKEHyperParams, "fine": fine.FiNEHyperParams,
                   "nmke": nmke.NMKEHyperParams, "fidal": fidal.FiDALHyperParams}
        for method, hparams_cls in classes.items():
            directory = os.path.join(EXP_DIR, "hparams", run_experiment.METHOD_HPARAMS_DIR[method])
            files = sorted(f for f in os.listdir(directory) if f.endswith(".yaml"))
            self.assertTrue(files, f"no hparams shipped for {method}")
            for name in files:
                model = name[: -len(".yaml")]
                self.assertIn(model, run_experiment.MODEL_PATHS,
                              f"hparams/{method}/{name} names a model that is not registered")
                hparams = hparams_cls.from_hparams(os.path.join(directory, name))
                self.assertEqual(hparams.model_name, run_experiment.MODEL_PATHS[model])

    def test_dynamic_methods_are_flagged(self):
        import run_experiment

        self.assertEqual(run_experiment.DYNAMIC_METHODS, {"wilke", "fine", "nmke", "fidal"})


if __name__ == "__main__":
    unittest.main()
