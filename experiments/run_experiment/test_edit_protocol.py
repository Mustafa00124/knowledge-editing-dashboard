import json
import os
import unittest

from edit_protocol import (
    EDIT_MODES,
    JOINT_MODES,
    SEQUENTIAL_MODES,
    average_group_evaluations,
    edit_groups,
    validate_protocol,
)
from semantic_evaluation import collect_probes

DASHBOARD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard.json")


class EditProtocolTests(unittest.TestCase):
    def test_single_and_batch_reset_every_call(self):
        # Both isolate an edit; they differ only in facts per call. Neither
        # consults reset_every, which is why the UI does not offer it.
        self.assertEqual(list(edit_groups(3, "single", 10, 4)), [
            (0, 1, [(0, 1)]), (1, 2, [(1, 2)]), (2, 3, [(2, 3)]),
        ])
        self.assertEqual(list(edit_groups(10, "batch", 999, 4)), [
            (0, 4, [(0, 4)]), (4, 8, [(4, 8)]), (8, 10, [(8, 10)]),
        ])

    def test_sequential_pair_accumulate_until_the_reset_interval(self):
        self.assertEqual(list(edit_groups(3, "sequential", 10, 4)), [
            (0, 3, [(0, 1), (1, 2), (2, 3)]),
        ])
        self.assertEqual(list(edit_groups(13, "sequential_batch", 10, 4)), [
            (0, 10, [(0, 4), (4, 8), (8, 10)]),
            (10, 13, [(10, 13)]),
        ])

    def test_batch_size_is_the_group_width_only_for_plain_batch(self):
        # The same numbers mean different runs: batch 4 is three isolated
        # groups, sequential_batch 4 with reset 10 is two accumulating ones.
        plain = [start for start, _stop, _calls in edit_groups(10, "batch", 10, 4)]
        accumulating = [start for start, _stop, _calls in edit_groups(10, "sequential_batch", 10, 4)]
        self.assertEqual(plain, [0, 4, 8])
        self.assertEqual(accumulating, [0])

    def test_invalid_method_and_batch_are_rejected(self):
        for method, mode, reset, batch in [
            ("rome", "batch", 10, 2), ("rome", "sequential_batch", 10, 2),
            ("scr", "single", 10, 2), ("memit", "nonsense", 10, 2),
            ("memit", "sequential_batch", 10, 11), ("memit", "sequential", 0, 1),
            ("memit", "batch", 10, 0),
        ]:
            with self.assertRaises(ValueError):
                validate_protocol(method, mode, reset, batch)

    def test_unused_knobs_are_not_validated(self):
        # A nonsense reset interval left over in the form must not block a
        # mode that never reads it, or switching mode would need the other
        # field cleaned up first.
        validate_protocol("memit", "batch", 0, 10)
        validate_protocol("memit", "single", 0, 0)
        # batch > reset is only a contradiction where both apply.
        validate_protocol("memit", "batch", 10, 500)

    def test_summary_uses_all_facts_not_just_last_group(self):
        rows = [
            {"group_size": 10, "evaluations": {"original": {"edit_succ": 80, "portability": None}}},
            {"group_size": 3, "evaluations": {"original": {"edit_succ": 15, "portability": 60}}},
        ]
        scores = average_group_evaluations(rows)["original"]
        self.assertEqual(scores["edit_succ"], 65)
        self.assertEqual(scores["portability"], 60)

    def test_group_probes_keep_global_baseline_ids(self):
        record = {"prompt": "Question", "target_new": "Answer", "locality": {
            "other": {"prompt": ["Existing fact?"], "ground_truth": ["Known"]}}}
        baseline = {}
        collect_probes([record, record], lambda _record, _question: "before", baseline)
        probes = collect_probes([record], lambda _record, _question: "after", baseline, case_offset=1)
        self.assertEqual(probes[-1]["id"], "1:locality:other:0")
        self.assertEqual(probes[-1]["before_answer"], "before")


class DashboardFieldsMatchProtocolTests(unittest.TestCase):
    """The dashboard is the only way most runs get launched, so a mode the
    runner accepts but the form cannot offer (or the reverse) is invisible
    until someone tries it. Pin the two together."""

    @classmethod
    def setUpClass(cls):
        with open(DASHBOARD) as handle:
            cls.fields = {f["name"]: f for f in json.load(handle)["fields"]}

    def test_every_mode_is_offered_and_no_others(self):
        offered = {option["value"] for option in self.fields["edit_mode"]["options"]}
        self.assertEqual(offered, EDIT_MODES)

    def test_each_knob_is_shown_for_exactly_the_modes_that_read_it(self):
        self.assertEqual(set(self.fields["reset_every"]["show_when"]["edit_mode"]), SEQUENTIAL_MODES)
        self.assertEqual(set(self.fields["edit_batch_size"]["show_when"]["edit_mode"]), JOINT_MODES)

    def test_defaults_are_valid_for_the_default_mode(self):
        fields = self.fields
        mode = fields["edit_mode"]["default"]
        self.assertIn(mode, EDIT_MODES)
        # memit stands in for any method that can solve jointly.
        validate_protocol("memit", mode,
                          int(fields["reset_every"]["default"]),
                          int(fields["edit_batch_size"]["default"]))

    def test_every_per_method_default_mode_validates(self):
        fields = self.fields
        for method, mode in fields["edit_mode"].get("default_when", {}).get("method", {}).items():
            with self.subTest(method=method):
                validate_protocol(method, mode,
                                  int(fields["reset_every"]["default"]),
                                  int(fields["edit_batch_size"]["default"]))

    def test_checkpoint_cadences_stay_on_one_scale(self):
        # run_experiment.py rejects a fluency/sample interval that is not a
        # multiple of the checkpoint interval, so the dropdowns must not be
        # able to offer a pairing that dies at argument parsing.
        checkpoints = [int(o["value"]) for o in self.fields["checkpoint_every"]["options"]]
        for name in ("fluency_every", "sample_every"):
            for option in self.fields[name]["options"]:
                value = int(option["value"])
                for checkpoint in checkpoints:
                    if checkpoint <= value:
                        with self.subTest(field=name, value=value, checkpoint=checkpoint):
                            self.assertEqual(value % checkpoint, 0)


if __name__ == "__main__":
    unittest.main()
