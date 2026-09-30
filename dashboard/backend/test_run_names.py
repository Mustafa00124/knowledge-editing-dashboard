"""Run directory names: what has to appear in one so two runs can't collide."""
import unittest

import slurm

CONFIG = {
    "name": "demo",
    "run_name_always": ["method", "model", "ds_size"],
    "fields": [
        {"name": "method", "type": "string", "run_name_bare": True},
        {"name": "model", "type": "string", "run_name_bare": True},
        {"name": "ds_size", "type": "string", "run_name_prefix": "ds", "run_name_format": ""},
        {"name": "reset_every", "type": "int"},
        {"name": "seed", "type": "int"},
    ],
}

BASE = {"method": "ft", "model": "qwen3-4b", "ds_size": "20", "reset_every": 50, "seed": 0}


def name(params, swept=()):
    return slurm._format_run_name(CONFIG, {**BASE, **params}, swept)


class RunNameTests(unittest.TestCase):
    def test_always_named_fields_appear_without_being_swept(self):
        self.assertEqual(name({}), "ft_qwen3-4b_ds20")

    def test_a_full_dataset_run_cannot_collide_with_a_sized_one(self):
        """The reason ds_size is in the always list: same method, model and
        dataset, wildly different run - and one directory if the name omits it."""
        self.assertNotEqual(name({"ds_size": "full"}), name({"ds_size": "20"}))
        self.assertEqual(name({"ds_size": "full"}), "ft_qwen3-4b_dsfull")

    def test_prefix_overrides_the_field_name(self):
        self.assertIn("ds20", name({}))
        self.assertNotIn("ds_size20", name({}))

    def test_swept_fields_join_the_name_and_unswept_ones_stay_out(self):
        self.assertEqual(name({}, swept=["reset_every"]), "ft_qwen3-4b_ds20_reset_every50")
        self.assertNotIn("seed", name({}, swept=["reset_every"]))

    def test_an_experiment_type_that_declares_nothing_keeps_the_built_in_default(self):
        """Without the override it is the built-in list that applies, which
        names the protocol fields and not the dataset size."""
        config = {**CONFIG}
        config.pop("run_name_always")
        self.assertEqual(slurm._format_run_name(config, BASE, ()), "ft_qwen3-4b_reset_every50")


if __name__ == "__main__":
    unittest.main()
