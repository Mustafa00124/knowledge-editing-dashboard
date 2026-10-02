"""Sweep planning: what is varied, what is held constant, and at what value.

plan() submits nothing, so these run anywhere the hparams files exist.
"""
import os
import unittest

import config
import hparam_sweeps

DATASET = os.path.join(str(config.PROJECT_ROOT), "datasets/KnowEdit/benchmark/wiki_counterfact/test_cf.json")


def request(**extra):
    return {"investigation": "edit_layers", "methods": {"rome": {"layers": [[4], [5]]}},
            "models": ["qwen3-4b"], "data_paths": [DATASET], "ds_size": "full", "edit_mode": "single",
            **extra}


class HeldConstantTests(unittest.TestCase):
    def test_sweep_points_carry_held_values_but_not_in_their_names(self):
        _, _, runs, _ = hparam_sweeps.plan(request(fixed={"rome": {"qwen3-4b": {"kl_factor": 0.1}}}))
        self.assertEqual(len(runs), 2)
        for run in runs:
            self.assertEqual(run["fixed"], {"kl_factor": 0.1})
            self.assertNotIn("kl_factor", run["run_name"])

    def test_a_setting_cannot_be_swept_and_held_at_once(self):
        with self.assertRaisesRegex(ValueError, "being swept"):
            hparam_sweeps.plan(request(fixed={"rome": {"qwen3-4b": {"layers": [7]}}}))

    def test_only_adjustable_settings_can_be_held(self):
        with self.assertRaisesRegex(ValueError, "no adjustable setting"):
            hparam_sweeps.plan(request(fixed={"rome": {"qwen3-4b": {"model_name": "elsewhere"}}}))

    def test_effective_values_follow_the_experiments_page_where_it_overrides(self):
        ike = {r["key"]: r for r in hparam_sweeps.effective_settings("ike", "qwen3-4b")}
        self.assertEqual(ike["k"]["source"], "experiment_default")
        ft = {r["key"]: r for r in hparam_sweeps.effective_settings("ft", "qwen3-4b")}
        self.assertFalse(ft["batch_size"]["editable"])
        rome = {r["key"]: r for r in hparam_sweeps.effective_settings("rome", "qwen3-4b")}
        self.assertNotIn("model_name", rome)
        self.assertNotIn("rewrite_module_tmp", rome)

    def test_held_settings_name_the_investigation_that_tunes_them(self):
        held = hparam_sweeps.settings("edit_layers", ["rome"], ["qwen3-4b"])["rome"]["qwen3-4b"]
        owners = {r["key"]: (r["owner"] or {}).get("id") for r in held}
        self.assertEqual(owners["v_lr"], "value_optimisation")
        self.assertEqual(owners["kl_factor"], "preservation")
        self.assertIsNone(owners["fact_token"])


if __name__ == "__main__":
    unittest.main()
