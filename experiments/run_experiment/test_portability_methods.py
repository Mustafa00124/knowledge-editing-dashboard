"""Tests for the portability editors in portability/.

Each method's claim is about what it writes besides the edit itself, so
the tests check that directly: DMLE sends each form of a rule to its own
layers, IFMET writes a second edit into deeper layers from two-hop prompts,
LTI compares the target tokens with themselves in the in-context run, and
LoCo's loss is the weighted model count of its formula.

Everything runs on a randomly initialised 4-layer model on CPU, as
test_dynamic_methods.py does: covariance statistics are replaced by the
identity and the context templates by the bare prompt, so no Wikipedia
statistics, GPU or downloaded weights are needed - only a local tokenizer.
"""
import json
import math
import os
import sys
import tempfile
import unittest
from contextlib import ExitStack
from unittest import mock

import torch

EXP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(EXP_DIR))
EASYEDIT = os.path.join(PROJECT_ROOT, "external/EasyEdit")
for path in (EXP_DIR, EASYEDIT):
    if path not in sys.path:
        sys.path.insert(0, path)

from portability import base, derived, dmle, ifmet, loco, lti  # noqa: E402
from test_dynamic_methods import tiny_model  # noqa: E402

TINY_BASE = {
    "alg_name": "MEMIT", "model_name": "tiny-llama", "device": "cpu", "stats_dir": "unused",
    "layers": [1], "clamp_norm_factor": 4, "layer_selection": "all", "fact_token": "subject_last",
    "v_num_grad_steps": 2, "v_lr": 0.5, "v_loss_layer": 3, "v_weight_decay": 1e-3, "kl_factor": 0.0625,
    "mom2_adjustment": True, "mom2_update_weight": 100, "rewrite_module_tmp": "model.layers.{}.mlp.down_proj",
    "layer_module_tmp": "model.layers.{}", "mlp_module_tmp": "model.layers.{}.mlp",
    "attn_module_tmp": "model.layers.{}.self_attn", "ln_f_module": "model.norm", "lm_head_module": "lm_head",
    "mom2_dataset": "wikipedia", "mom2_n_samples": 10, "mom2_dtype": "float32", "model_parallel": False,
}
PMET_EXTRA = {"rewrite_module_tmps": ["model.layers.{}.mlp.down_proj"], "nll_loss_factor": 1}


def offline_editors():
    """Identity covariance and bare-prompt context templates for MEMIT and PMET."""
    def identity(model, tok, layer_name, *args, **kwargs):
        from easyeditor.util import nethook
        weight = nethook.get_parameter(model, f"{layer_name}.weight")
        return torch.eye(weight.shape[1], dtype=torch.float32)

    stack = ExitStack()
    for module in ("easyeditor.models.memit.memit_main", "easyeditor.models.pmet.pmet_main"):
        stack.enter_context(mock.patch(f"{module}.get_cov", side_effect=identity))
        stack.enter_context(mock.patch(f"{module}.get_context_templates", return_value=[["{}"]]))
    return stack


def changed(model, before):
    return {name for name, param in model.named_parameters() if not torch.equal(param, before[name])}


def snapshot(model):
    return {name: param.detach().clone() for name, param in model.named_parameters()}


def rule_records():
    return [
        {"prompt": "A rectangle's area is", "subject": "rectangle", "target_new": "x + y", "form": "formula"},
        {"prompt": "The area of a rectangle is found by", "subject": "rectangle", "target_new": "adding",
         "form": "description"},
        {"prompt": "A rectangle 3 by 4 has area", "subject": "rectangle", "target_new": "7", "form": "instance"},
    ]


class DMLETests(unittest.TestCase):
    def _hparams(self):
        return dmle.DMLEHyperParams(alg_name="DMLE", model_name="tiny-llama", device="cpu", base_method="memit",
                                    formula_description_layers=[0], instance_layers=[2],
                                    base_config=dict(TINY_BASE))

    def test_forms_go_to_their_stage_in_upstream_order(self):
        plan = dmle.stages(rule_records(), self._hparams())
        self.assertEqual([name for name, _, _ in plan], ["f_d", "ins"])
        self.assertEqual([r["form"] for r in plan[0][2]], ["formula", "description"])
        self.assertEqual([r["form"] for r in plan[1][2]], ["instance"])

    def test_records_without_a_form_are_refused(self):
        with self.assertRaisesRegex(ValueError, "RuleEdit-200"):
            dmle.stages([{"prompt": "Paris is in", "subject": "Paris", "target_new": "Spain"}], self._hparams())

    def test_each_form_is_written_only_into_its_own_layers(self):
        model, tok = tiny_model()
        hparams = self._hparams()
        with offline_editors():
            for records, layer in ((rule_records()[:2], 0), (rule_records()[2:], 2)):
                before = snapshot(model)
                model, copied = dmle.apply_dmle_to_model(model, tok, records, hparams, return_orig_weights=True)
                self.assertEqual(changed(model, before), {f"model.layers.{layer}.mlp.down_proj.weight"})
                self.assertEqual(set(copied), {f"model.layers.{layer}.mlp.down_proj.weight"})

    def test_a_whole_rule_edits_both_groups_and_restores_from_the_first_copy(self):
        model, tok = tiny_model()
        before = snapshot(model)
        with offline_editors():
            model, copied = dmle.apply_dmle_to_model(model, tok, rule_records(), self._hparams(),
                                                     return_orig_weights=True)
        self.assertEqual(changed(model, before), {"model.layers.0.mlp.down_proj.weight",
                                                  "model.layers.2.mlp.down_proj.weight"})
        for name, value in copied.items():
            torch.testing.assert_close(value, before[name])


class LTITests(unittest.TestCase):
    def _hparams(self):
        config = dict(TINY_BASE)
        return lti.LTIHyperParams(alg_name="LTI", model_name="tiny-llama", device="cpu", base_method="memit",
                                  midlayers=[2], base_config=config)

    def test_in_context_spans_hold_the_target_tokens(self):
        """The deviation from upstream: positions recomputed for the prefixed prompt.

        compute_z scores target token k at position start + k, whose logits
        predict the next token, so a span starts at the prompt's last token
        and continues over every target token but the last."""
        _, tok = tiny_model()
        target_ids = tok.encode(" New York City", add_special_tokens=False)
        self.assertGreater(len(target_ids), 1)
        stem = "The capital of the United States is"
        prompts = [stem + tok.decode(target_ids[:-1]),
                   "Imagine that " + stem + " New York City.\n" + stem + tok.decode(target_ids[:-1])]
        with base.padding(tok, "right"):
            encoded = tok(prompts, return_tensors="pt", padding=True)
        spans = lti._target_spans(encoded["attention_mask"], [len(target_ids)] * 2)
        stem_last = tok.encode(stem, add_special_tokens=False)[-1]
        for row, (start, end) in zip(encoded["input_ids"], spans):
            self.assertEqual(int(row[start]), stem_last)
            self.assertEqual(row[start + 1:end].tolist(), target_ids[:-1])
        self.assertGreater(spans[1][0], spans[0][0], "the prefixed prompt's target sits later")

    def test_the_objective_is_patched_in_for_one_call_only(self):
        import importlib

        memit_main = importlib.import_module("easyeditor.models.memit.memit_main")
        original = memit_main.compute_z
        model, tok = tiny_model()
        seen = []
        real = lti.compute_z_lti

        def spy(*args, **kwargs):
            seen.append(args[2]["subject"])
            return real(*args, **kwargs)

        with offline_editors(), mock.patch.object(lti, "compute_z_lti", side_effect=spy):
            lti.apply_lti_to_model(model, tok, [{"prompt": "Paris is in", "subject": "Paris", "target_new": "Spain"}],
                                   self._hparams())
        self.assertEqual(seen, ["Paris"])
        self.assertIs(memit_main.compute_z, original)

    def test_edit_moves_only_the_base_editors_layers(self):
        model, tok = tiny_model()
        before = snapshot(model)
        with offline_editors():
            model, copied = lti.apply_lti_to_model(
                model, tok, [{"prompt": "Paris is in", "subject": "Paris", "target_new": "Spain"},
                             {"prompt": "Rome is in", "subject": "Rome", "target_new": "Peru"}],
                self._hparams(), return_orig_weights=True)
        self.assertEqual(changed(model, before), {"model.layers.1.mlp.down_proj.weight"})
        self.assertEqual(set(copied), {"model.layers.1.mlp.down_proj.weight"})

    def test_rome_base_is_rejected(self):
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as handle:
            json.dump({**TINY_BASE, "alg_name": "LTI", "base_method": "rome", "midlayers": [2]}, handle)
        with self.assertRaisesRegex(ValueError, "compute_z"):
            lti.LTIHyperParams.from_hparams(handle.name)
        os.unlink(handle.name)


class IFMETTests(unittest.TestCase):
    def _hparams(self):
        config = {**TINY_BASE, **PMET_EXTRA, "alg_name": "PMET", "layers": [0]}
        return ifmet.IFMETHyperParams(alg_name="IFMET", model_name="tiny-llama", device="cpu", base_method="pmet",
                                      deep_layers=[2], n_support=2, base_config=config)

    def test_two_hop_prompt_puts_the_description_where_the_subject_was(self):
        request = {"prompt": "Spain's capital is", "subject": "Spain", "target_new": "Lisbon"}
        self.assertEqual(ifmet.two_hop_prompt(request, "the country of citizenship of Pablo Picasso"),
                         "The country of citizenship of Pablo Picasso's capital is")
        request = {"prompt": "The capital of {} is", "subject": "Spain", "target_new": "Lisbon"}
        self.assertEqual(ifmet.two_hop_prompt(request, "the country of citizenship of Pablo Picasso"),
                         "The capital of the country of citizenship of Pablo Picasso is")

    def test_only_descriptions_the_model_resolves_to_the_subject_are_kept(self):
        def fake_generate(model, tok, prompts, max_new_tokens, num_return_sequences=1, **kwargs):
            if prompts[0].startswith("Each entity"):
                return [["the country of citizenship of Pablo Picasso", "Spain itself", "the land of Don Quixote",
                         "the country of citizenship of Pablo Picasso"]]
            return [["Spain, in Europe"] if "Picasso" in p else ["La Mancha"] for p in prompts]

        with mock.patch.object(base, "generate", side_effect=fake_generate):
            kept, sampled = ifmet.support_descriptions(None, None, ["Spain"], self._hparams())
        # Circular ("Spain itself") and duplicate candidates go first, then
        # the one the model does not resolve back to Spain.
        self.assertEqual(sampled["Spain"], ["the country of citizenship of Pablo Picasso", "the land of Don Quixote"])
        self.assertEqual(kept["Spain"], ["the country of citizenship of Pablo Picasso"])

    def test_furtherance_edit_writes_the_deep_layers_from_two_hop_prompts(self):
        model, tok = tiny_model()
        before = snapshot(model)
        support = ({"Paris": ["the city of the Louvre museum"]}, {"Paris": ["the city of the Louvre museum"]})
        derived.drain()
        with offline_editors(), mock.patch.object(ifmet, "support_descriptions", return_value=support):
            model, copied = ifmet.apply_ifmet_to_model(
                model, tok, [{"prompt": "Paris is in", "subject": "Paris", "target_new": "Spain"}],
                self._hparams(), return_orig_weights=True)
        self.assertEqual(changed(model, before), {"model.layers.0.mlp.down_proj.weight",
                                                  "model.layers.2.mlp.down_proj.weight"})
        records = derived.drain()
        self.assertEqual(records[0]["two_hop_prompts"], ["The city of the Louvre museum is in"])

    def test_no_resolvable_support_means_no_furtherance_edit(self):
        model, tok = tiny_model()
        before = snapshot(model)
        with offline_editors(), mock.patch.object(ifmet, "support_descriptions", return_value=({"Paris": []}, {"Paris": []})):
            model, _ = ifmet.apply_ifmet_to_model(
                model, tok, [{"prompt": "Paris is in", "subject": "Paris", "target_new": "Spain"}], self._hparams())
        self.assertEqual(changed(model, before), {"model.layers.0.mlp.down_proj.weight"})
        derived.drain()


class LoCoTests(unittest.TestCase):
    def test_grounded_implication_is_the_product_of_the_beliefs(self):
        p = {"A": torch.tensor(0.8), "B0": torch.tensor(0.6)}
        loss = loco.semantic_loss(p, loco.formula(p, "implication"))
        self.assertAlmostEqual(loss.item(), -math.log(0.8 * 0.6), places=5)

    def test_negation_excludes_the_old_answer_and_the_negated_edit(self):
        p = {"A": torch.tensor(0.7), "O": torch.tensor(0.4), "N": torch.tensor(0.2)}
        loss = loco.semantic_loss(p, loco.formula(p, "negation"))
        self.assertAlmostEqual(loss.item(), -math.log(0.7 * (1 - 0.4) * (1 - 0.2)), places=5)

    def test_all_combines_both(self):
        p = {"A": torch.tensor(0.9), "O": torch.tensor(0.3), "N": torch.tensor(0.1), "B0": torch.tensor(0.5)}
        loss = loco.semantic_loss(p, loco.formula(p, "all"))
        self.assertAlmostEqual(loss.item(), -math.log(0.9 * 0.7 * 0.9 * 0.5), places=5)

    def test_old_fact_only_when_the_record_has_a_different_answer(self):
        request = {"prompt": "The capital of Spain is", "subject": "Spain", "target_new": "Lisbon"}
        self.assertNotIn("O", loco.statements_for({**request, "ground_truth": None}, []))
        self.assertNotIn("O", loco.statements_for({**request, "ground_truth": "Lisbon"}, []))
        statements = loco.statements_for({**request, "ground_truth": "Madrid"}, ["Lisbon is in Spain."])
        self.assertEqual(statements["O"], "The capital of Spain is Madrid.")
        self.assertEqual(statements["B0"], "Lisbon is in Spain.")

    def test_training_moves_only_the_lora_targets_and_hands_back_their_originals(self):
        model, tok = tiny_model()
        before = snapshot(model)
        hparams = loco.LoCoHyperParams(alg_name="LoCo", model_name="tiny-llama", device="cpu", rank=2,
                                       lora_alpha=4, num_steps=2, lr=1e-2, target_modules=["q_proj", "down_proj"])
        derived.drain()
        with mock.patch.object(loco, "implications", return_value=[["Paris is far from Madrid."]]):
            model, originals = loco.apply_loco_to_model(
                model, tok, [{"prompt": "Paris is in", "subject": "Paris", "target_new": "Spain",
                              "ground_truth": "France"}], hparams, return_orig_weights=True)
        moved = changed(model, before)
        self.assertTrue(moved)
        self.assertTrue(all(name.endswith(("q_proj.weight", "down_proj.weight")) for name in moved), moved)
        self.assertTrue(moved <= set(originals))
        for name in moved:
            torch.testing.assert_close(originals[name], before[name])
        self.assertEqual(set(derived.drain()[0]["statements"]), {"A", "N", "O", "B0"})


class RuleEditTests(unittest.TestCase):
    def test_loader_keeps_forms_and_both_probe_groups(self):
        from eval_utils import load_ruleedit_requests

        record = {"rule_id": 0, "rule": "area of rectangle", "subject": "rectangle", "ground_truth": "A = x * y.",
                  "portability": {"Rule_Understanding": [{"prompt": "Area is found by", "ground_truth": "adding"}],
                                  "Instance": [{"prompt": "A 2 by 3 rectangle has area", "ground_truth": "5"}]},
                  "locality": {"neighborhood": [{"prompt": "Its diagonal squared is", "ground_truth": "x^2 + y^2"}],
                               "distracting": []}}
        rows = [{**record, "form": form, "prompt": f"A rectangle {form} is", "target_new": "A = x + y."}
                for form in ("formula", "description", "instance")]
        with tempfile.TemporaryDirectory() as root:
            path = os.path.join(root, "RuleEdit-200", "ruleedit_editing.json")
            os.makedirs(os.path.dirname(path))
            with open(path, "w") as handle:
                json.dump(rows, handle)
            requests = load_ruleedit_requests(path, None)
        self.assertEqual([r["form"] for r in requests], ["formula", "description", "instance"])
        self.assertEqual(requests[0]["portability"]["Instance"]["ground_truth"], ["5"])
        self.assertEqual(requests[0]["locality"]["neighborhood"]["prompt"], ["Its diagonal squared is"])
        self.assertEqual(requests[0]["ground_truth"], "A = x * y.")


class RegistryTests(unittest.TestCase):
    CLASSES = {"dmle": dmle.DMLEHyperParams, "ifmet": ifmet.IFMETHyperParams,
               "lti": lti.LTIHyperParams, "loco": loco.LoCoHyperParams}

    def test_portability_methods_are_flagged_and_batch(self):
        import run_experiment
        from edit_protocol import JOINT_BATCH_METHODS

        self.assertEqual(run_experiment.PORTABILITY_METHODS, set(self.CLASSES))
        self.assertTrue(set(self.CLASSES) <= JOINT_BATCH_METHODS)

    def test_every_hparams_file_loads_with_project_paths(self):
        import run_experiment

        for method, hparams_cls in self.CLASSES.items():
            directory = os.path.join(EXP_DIR, "hparams", run_experiment.METHOD_HPARAMS_DIR[method])
            files = sorted(f for f in os.listdir(directory) if f.endswith(".yaml"))
            self.assertTrue(files, f"no hparams shipped for {method}")
            for name in files:
                model = name[: -len(".yaml")]
                self.assertIn(model, run_experiment.MODEL_PATHS, f"hparams/{method}/{name}")
                hparams = run_experiment.resolve_project_paths(hparams_cls.from_hparams(os.path.join(directory, name)))
                self.assertEqual(hparams.model_name, run_experiment.MODEL_PATHS[model])
                if getattr(hparams, "base_config", None):
                    base.base_hparams(hparams.base_method, hparams.base_config)
                    self.assertEqual(hparams.base_config["model_name"], run_experiment.MODEL_PATHS[model])
                    self.assertEqual(hparams.base_config["stats_dir"], os.path.join(EXP_DIR, "data", "stats"),
                                     f"hparams/{method}/{name} points at a different stats cache")


if __name__ == "__main__":
    unittest.main()
