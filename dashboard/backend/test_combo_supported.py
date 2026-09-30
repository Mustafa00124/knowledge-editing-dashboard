"""_combo_supported drops sweep points the runner would reject on sight.

The same rules are reimplemented in the frontend (lib/comboCount.js) so the
drawer's "N experiments" counter matches what actually gets submitted, so
these cases are the contract between the two.
"""
import os
import unittest

import config
import registry
import slurm

ROOT = str(config.PROJECT_ROOT)
DATASET = os.path.join(ROOT, "datasets/KnowEdit/benchmark/wiki_recent/recent_test.json")


class ComboSupportedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Through the registry, so ${PROJECT_ROOT} in dashboard.json is
        # expanded the same way the running dashboard sees it.
        cls.cfg = registry.get_experiment_type("run_experiment")

    def supported(self, **params):
        base = {"method": "memit", "data_path": DATASET,
                "edit_mode": "batch", "edit_batch_size": 10, "reset_every": 1000}
        return slurm._combo_supported(self.cfg, {**base, **params})

    def test_joint_modes_need_a_method_that_solves_jointly(self):
        for mode in ("batch", "sequential_batch"):
            with self.subTest(mode=mode):
                self.assertFalse(self.supported(method="rome", edit_mode=mode))
                self.assertTrue(self.supported(method="memit", edit_mode=mode))

    def test_rome_still_runs_the_one_at_a_time_modes(self):
        for mode in ("single", "sequential"):
            with self.subTest(mode=mode):
                self.assertTrue(self.supported(method="rome", edit_mode=mode))

    def test_batch_size_may_exceed_reset_only_where_reset_is_unused(self):
        # sequential_batch reads both, so the pairing is a contradiction.
        self.assertFalse(self.supported(edit_mode="sequential_batch",
                                        edit_batch_size=100, reset_every=10))
        # Plain batch never reads reset_every, so a stale value left in the
        # form must not silently drop the run.
        self.assertTrue(self.supported(edit_mode="batch",
                                       edit_batch_size=100, reset_every=10))

    def test_subject_requirement_still_applies(self):
        realtimeqa = os.path.join(ROOT, "datasets/RealTimeQA/realtimeqa_editing.json")
        self.assertFalse(self.supported(method="rome", edit_mode="single", data_path=realtimeqa))
        self.assertTrue(self.supported(method="ft", edit_mode="single", data_path=realtimeqa))


if __name__ == "__main__":
    unittest.main()
