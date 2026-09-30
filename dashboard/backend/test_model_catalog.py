"""The model picker's two-level shape, checked against the real dashboard.json.

The model field carries its options twice over: a flat `options` list, which
Results.jsx and the sweep validation look models up in by value, and a
`families` grouping that only holds values and is resolved in ModelField.jsx.
Those two can drift silently - a model listed in no family just vanishes from
the picker while still being a legal sweep value - so they are asserted here
rather than discovered later.

Also pins the invariant that every selectable model has a registered path and
hparams behind it. Whether its weights are downloaded is a property of the
checkout, not the code: the dashboard greys out models that are not on disk
(scripts/setup.py fetches them), so weight checks only run where they exist.
"""
import json
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXPERIMENT = os.path.join(ROOT, "experiments/run_experiment")
HPARAMS = os.path.join(EXPERIMENT, "hparams")
VALID_TYPES = {"raw", "chat", "reasoning"}


def model_field():
    with open(os.path.join(EXPERIMENT, "dashboard.json")) as handle:
        cfg = json.load(handle)
    return next(f for f in cfg["fields"] if f["name"] == "model")


def registered_paths():
    with open(os.path.join(EXPERIMENT, "run_experiment.py")) as handle:
        src = handle.read()
    block = re.search(r"MODEL_PATHS = \{(.*?)\n\}", src, re.S).group(1)
    pairs = re.findall(r'"([^"]+)":\s*os\.path\.join\(PROJECT_ROOT,\s*"([^"]+)"\)', block)
    return {key: os.path.join(ROOT, relative) for key, relative in pairs}


class ModelCatalogTests(unittest.TestCase):
    def setUp(self):
        self.field = model_field()
        self.options = self.field["options"]
        self.by_value = {o["value"]: o for o in self.options}

    def test_families_and_options_cover_each_other(self):
        listed = [v for fam in self.field["families"] for v in fam["models"]]
        self.assertEqual(len(listed), len(set(listed)), "a model appears in two families")
        self.assertEqual(set(listed), set(self.by_value), "families and options disagree")

    def test_every_option_declares_a_known_tuning_stage(self):
        for o in self.options:
            self.assertIn(o.get("model_type"), VALID_TYPES, o["value"])
            self.assertTrue(o.get("variant"), o["value"])

    def test_default_is_selectable(self):
        default = self.field["default"]
        self.assertIn(default, self.by_value)
        self.assertNotEqual(self.by_value[default].get("available"), False)

    def test_available_models_are_registered_with_at_least_one_method(self):
        paths = registered_paths()
        for o in self.options:
            if o.get("available") is False:
                continue
            value = o["value"]
            self.assertIn(value, paths, f"{value} is selectable but not in MODEL_PATHS")
            methods = [m for m in os.listdir(HPARAMS)
                       if os.path.exists(os.path.join(HPARAMS, m, value + ".yaml"))]
            self.assertTrue(methods, f"{value} is selectable but has no hparams for any method")

    def test_chat_and_reasoning_models_ship_a_chat_template(self):
        """A model tagged chat/reasoning must actually carry a chat template.

        Only this direction is assertable. The reverse is not: Qwen ships the
        same tokenizer_config across a family, so Qwen3-4B-Base carries a
        vestigial chat template despite being a base model (its `<|endoftext|>`
        eos, not `<|im_end|>`, is what gives it away). The template also lives
        in one of two places - inline in tokenizer_config.json, or a separate
        chat_template.jinja, which is where Olmo 3 puts it.
        """
        paths = registered_paths()
        for o in self.options:
            if o["model_type"] not in ("chat", "reasoning"):
                continue
            path = paths.get(o["value"])
            if not path or not os.path.isdir(path):
                continue  # not downloaded; covered by the availability test
            with open(os.path.join(path, "tokenizer_config.json")) as handle:
                inline = bool(json.load(handle).get("chat_template"))
            sidecar = os.path.exists(os.path.join(path, "chat_template.jinja"))
            self.assertTrue(inline or sidecar,
                            f"{o['value']} is tagged {o['model_type']} but ships no chat template")

    def test_models_page_catalog_agrees_with_the_experiment_picker(self):
        """Two hand-edited catalogs describe the same models; keep them in step.

        models_reader.CATALOG drives the Models page (it carries repo ids,
        parameter counts and on-disk status); dashboard.json's model field
        drives the experiment picker. They are edited independently, and a
        model added to one but not the other is invisible in the other place -
        which is exactly how the new variants first went missing from the
        Models page.
        """
        import models_reader
        catalog = {m["name"]: m for m in models_reader.CATALOG}
        paths = registered_paths()

        for o in self.options:
            if o.get("available") is False:
                continue
            directory = os.path.basename(paths[o["value"]])
            self.assertIn(directory, catalog,
                          f"{o['value']} is selectable but missing from the Models page catalog")
            self.assertEqual(catalog[directory]["model_type"], o["model_type"],
                             f"{directory} is tagged differently in the two catalogs")

    def test_main_scope_is_non_empty(self):
        import models_reader
        main = [m for m in models_reader.list_models() if m["main"]]
        self.assertTrue(main, "the Models page would open on an empty default scope")

    def test_null_space_caches_are_never_shared_between_configs(self):
        # P is derived from the checkpoint's own weights and from the layer
        # list, so two configs sharing a P_loc would silently reuse the
        # wrong matrix. NMKE is checked alongside AlphaEdit because it
        # computes the same projection for its own layer set.
        locs = {}
        for method in ("AlphaEdit", "NMKE"):
            directory = os.path.join(HPARAMS, method)
            if not os.path.isdir(directory):
                continue
            for name in os.listdir(directory):
                with open(os.path.join(directory, name)) as handle:
                    text = handle.read()
                found = re.search(r'^P_loc:\s*"?([^"\n]+?)"?\s*$', text, re.M)
                if found:
                    locs.setdefault(found.group(1), []).append(f"{method}/{name}")
        shared = {loc: names for loc, names in locs.items() if len(names) > 1}
        self.assertEqual(shared, {}, f"configs share a P cache: {shared}")


if __name__ == "__main__":
    unittest.main()
