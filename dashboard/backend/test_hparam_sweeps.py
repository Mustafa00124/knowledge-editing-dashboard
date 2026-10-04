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


class MethodInvestigationTests(unittest.TestCase):
    """FT and LoRA each have one investigation that owns all their settings."""

    def test_ft_and_lora_settings_are_owned_by_their_own_investigation(self):
        owners = hparam_sweeps._owners()
        for key in ("objective_optimization", "layers", "lr", "num_steps", "weight_decay", "norm_constraint"):
            self.assertEqual(owners[("ft", key)]["id"], "ft", key)
        for key in ("rank", "target_modules", "layers", "lr", "num_steps", "lora_alpha", "lora_dropout",
                    "weight_decay", "lora_type"):
            self.assertEqual(owners[("lora", key)]["id"], "lora", key)
        for inv in hparam_sweeps._load_catalog()["investigations"]:
            if inv["id"] not in ("ft", "lora"):
                self.assertFalse({"ft", "lora"} & set(inv["methods"]), inv["id"])

    def test_every_knob_has_a_current_value(self):
        settings = {m: {r["key"] for r in hparam_sweeps.effective_settings(m, "qwen3-4b") if r["editable"]}
                    for m in ("ft", "lora")}
        for inv in ("ft", "lora"):
            knobs = hparam_sweeps._load_catalog()["investigations"]
            knobs = next(i for i in knobs if i["id"] == inv)["methods"][inv]["knobs"]
            self.assertEqual(set(knobs) - settings[inv], set(), inv)

    def test_ft_m_and_ft_l_swept_separately_or_together(self):
        req = {"investigation": "ft", "methods": {"ft": {"objective_optimization": ["target_new", "prompt_last"],
                                                         "lr": [1e-4, 1e-3]}},
               "models": ["qwen3-4b"], "data_paths": [DATASET], "ds_size": "full", "edit_mode": "batch"}
        _, _, runs, _ = hparam_sweeps.plan(req)
        self.assertEqual(len(runs), 4)
        self.assertEqual({r["overrides"]["objective_optimization"] for r in runs}, {"target_new", "prompt_last"})
        req["methods"]["ft"] = {"lr": [1e-4, 1e-3]}
        req["fixed"] = {"ft": {"qwen3-4b": {"objective_optimization": "prompt_last"}}}
        _, _, runs, _ = hparam_sweeps.plan(req)
        self.assertEqual([r["fixed"] for r in runs], [{"objective_optimization": "prompt_last"}] * 2)

    def test_layer_span_suggestions(self):
        from unittest.mock import patch
        with patch.object(hparam_sweeps, "_model_layers", return_value=36), \
             patch.object(hparam_sweeps, "_traced_peak", return_value=10):
            spans = hparam_sweeps.suggest("layer_span", [], {}, "qwen3-4b")
        self.assertEqual(spans[0], [])
        self.assertIn(list(range(0, 18)), spans)
        self.assertIn(list(range(18, 36)), spans)
        self.assertIn(list(range(9, 27)), spans)
        self.assertIn(list(range(6, 15)), spans)  # a quarter of the model around the peak
        self.assertEqual(len(spans), len({tuple(s) for s in spans}))

    def test_run_names_stay_short_for_layer_spans(self):
        self.assertEqual(hparam_sweeps._slug(list(range(0, 18))), "0to17")
        self.assertEqual(hparam_sweeps._slug([]), "all")
        self.assertEqual(hparam_sweeps._slug([4, 5, 6, 7, 8]), "4-5-6-7-8")  # unchanged for edit windows

    def test_negative_values_name_apart(self):
        # -2.0 and 2.0 once shared a run directory (the "-" was stripped).
        self.assertEqual(hparam_sweeps._slug(-2.0), "neg2.0")
        self.assertNotEqual(hparam_sweeps._slug(-2.0), hparam_sweeps._slug(2.0))
        req = {"investigation": "scr", "methods": {"scr": {"confirm_margin": [-2.0, 0.0, 2.0]}}, "models": ["qwen3-4b"],
               "data_paths": [DATASET], "ds_size": "full", "edit_mode": "batch"}
        _, _, runs, _ = hparam_sweeps.plan(req)
        self.assertEqual(len({r["run_name"] for r in runs}), 3)

    def test_runs_that_would_share_a_name_are_refused(self):
        from unittest.mock import patch
        req = {"investigation": "scr", "methods": {"scr": {"confirm_margin": [1.0, 3.0]}}, "models": ["qwen3-4b"],
               "data_paths": [DATASET], "ds_size": "full", "edit_mode": "batch"}
        with patch.object(hparam_sweeps, "_slug", return_value="same"), self.assertRaisesRegex(ValueError, "share a directory"):
            hparam_sweeps.plan(req)


class SCRInvestigationTests(unittest.TestCase):
    KNOBS = ("retrieval_k", "sentence_model_name", "min_similarity", "kb_key", "latest_edit_wins", "confirm",
             "confirm_margin", "confirm_shots", "max_confirmed", "fact_order", "answer_template",
             "no_context_framing")

    def test_scr_owns_its_settings_and_each_has_a_current_value(self):
        owners = hparam_sweeps._owners()
        editable = {r["key"] for r in hparam_sweeps.effective_settings("scr", "qwen3-4b") if r["editable"]}
        for key in self.KNOBS:
            self.assertEqual(owners[("scr", key)]["id"], "scr", key)
            self.assertIn(key, editable)
        retrieval = next(i for i in hparam_sweeps._load_catalog()["investigations"] if i["id"] == "retrieval")
        self.assertEqual(list(retrieval["methods"]), ["ike"])

    def test_default_datasets_are_distinct_and_have_dev_records(self):
        from unittest.mock import patch
        import json
        inv = next(i for i in hparam_sweeps._load_catalog()["investigations"] if i["id"] == "scr")
        # The catalog as written, so the result does not depend on what is downloaded here.
        raw = json.loads((config.EXPERIMENTS_DIR / "run_experiment" / "dashboard.json").read_text())
        with patch.object(hparam_sweeps, "_has_dev_split", return_value=True):
            paths = hparam_sweeps.default_datasets(inv, raw)
        self.assertTrue(any(p.endswith("MQuAKE-CF-3k-v2.json") for p in paths))
        self.assertFalse(any(p.endswith("MQuAKE-CF.json") for p in paths))
        self.assertTrue(any(p.endswith("realtimeqa_editing.json") for p in paths))
        self.assertFalse(any("by_question_type" in p for p in paths))
        self.assertEqual(len(paths), len(set(paths)))
        with patch.object(hparam_sweeps, "_has_dev_split", return_value=False):
            self.assertEqual(hparam_sweeps.default_datasets(inv, raw), [])
        self.assertIsNone(hparam_sweeps.default_datasets({"id": "x"}))

    def test_a_spec_can_ask_for_the_default_datasets(self):
        from unittest.mock import patch
        req = {"investigation": "scr", "methods": {"scr": {"confirm": ["each", "off"]}}, "models": ["qwen3-4b"],
               "data_paths": ["default"], "ds_size": "full", "edit_mode": "batch"}
        with patch.object(hparam_sweeps, "default_datasets", return_value=[DATASET]):
            _, _, runs, _ = hparam_sweeps.plan(req)
        self.assertEqual(len(runs), 2)
        self.assertEqual(req["data_paths"], [DATASET])  # recorded as the real list


class RunDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        import tempfile
        from pathlib import Path
        self.dir = Path(tempfile.mkdtemp())

    def write_loss(self, entries):
        import json
        (self.dir / "loss.jsonl").write_text("".join(json.dumps(e) + "\n" for e in entries))

    def test_value_vector_loss_is_averaged_over_facts(self):
        self.write_loss([{"kind": "value_vector", "step": 1, "loss": 3.0, "fact": 0, "target_prob": 0.02},
                         {"kind": "value_vector", "step": 2, "loss": 1.0, "fact": 0, "target_prob": 0.4},
                         {"kind": "value_vector", "step": 1, "loss": 4.0, "fact": 1, "target_prob": 0.01},
                         {"kind": "value_vector", "step": 2, "loss": 0.5, "fact": 1, "target_prob": 0.6}])
        summary = hparam_sweeps._loss_summary(self.dir)
        self.assertEqual(summary["curve"], [3.5, 0.75])
        self.assertEqual(summary["final_prob"], 0.5)

    def test_flags_name_what_went_wrong(self):
        self.write_loss([{"kind": "train", "step": 1, "loss": 1.0}, {"kind": "train", "step": 2, "loss": "nan"}])
        texts = [f["text"] for f in hparam_sweeps._flags("COMPLETED", None, hparam_sweeps._loss_summary(self.dir),
                                                         {"fluency": 0.5})]
        self.assertIn("loss became NaN", texts)
        self.assertIn("fluency fell 50%", texts)

    def test_error_line_skips_warnings_and_progress_bars(self):
        err = self.dir / "job.err"
        err.write_text("UserWarning: something\n  3%|#  | 1/30 [00:01<00:30, 1.0it/s]\n"
                       "Traceback (most recent call last):\n  File \"x.py\", line 1\n"
                       "torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 2 GiB\n")
        line = hparam_sweeps._error_line(str(err))
        self.assertTrue(line.startswith("torch.OutOfMemoryError"))
        self.assertEqual(hparam_sweeps._flags("FAILED", line, None, {})[0]["text"], "out of GPU memory")


class SweepProgressTests(unittest.TestCase):
    def setUp(self):
        import tempfile
        from pathlib import Path
        self.run = Path(tempfile.mkdtemp())

    def test_progress_reads_facts_from_the_loss_log(self):
        import json
        (self.run / "hparams.yaml").write_text("ds_size: 100\nmethod: rome\n")
        (self.run / "loss.jsonl").write_text(json.dumps({"kind": "value_vector", "step": 3, "loss": 1.0, "fact": 36}) + "\n")
        progress = hparam_sweeps._run_progress(self.run)
        self.assertEqual((progress["done"], progress["total"], progress["unit"]), (37, 100, "fact"))

    def test_a_run_that_has_not_written_anything_is_starting(self):
        self.assertEqual(hparam_sweeps._run_progress(self.run)["phase"], "starting")

    def test_overall_counts_finished_runs_and_running_ones_by_their_progress(self):
        rows = [{"state": "COMPLETED"}, {"state": "FAILED"},
                {"state": "RUNNING", "progress": {"done": 50, "total": 100}}, {"state": "PENDING"}]
        self.assertAlmostEqual(hparam_sweeps._overall(rows), 2.5 / 4)

    def test_a_sweep_with_active_runs_cannot_be_deleted(self):
        import json
        from unittest import mock
        sweep_dir = self.run / "sweeps" / "s1"
        sweep_dir.mkdir(parents=True)
        (sweep_dir / "sweep.json").write_text(json.dumps({"id": "s1", "runs": [{"job_id": "1"}]}))
        with mock.patch.object(hparam_sweeps, "_sweep_dir", return_value=sweep_dir), \
             mock.patch.object(hparam_sweeps, "_statuses", return_value={"1": {"state": "RUNNING"}}):
            with self.assertRaisesRegex(ValueError, "cancel them first"):
                hparam_sweeps.delete_sweep("edit_layers", "s1")
        self.assertTrue((sweep_dir / "sweep.json").exists())

    def test_deleting_a_finished_sweep_moves_it_out_of_sight_without_erasing_it(self):
        import json
        from unittest import mock
        root = self.run / "investigations"
        sweep_dir = root / "edit_layers" / "sweeps" / "s2"
        sweep_dir.mkdir(parents=True)
        (sweep_dir / "sweep.json").write_text(json.dumps({"id": "s2", "runs": [{"job_id": "2"}]}))
        with mock.patch.object(config, "INVESTIGATIONS_DIR", root), \
             mock.patch.object(config, "PROJECT_ROOT", self.run), \
             mock.patch.object(hparam_sweeps, "_statuses", return_value={"2": {"state": "COMPLETED"}}):
            hparam_sweeps.delete_sweep("edit_layers", "s2")
            self.assertEqual(list(hparam_sweeps._sweeps("edit_layers")), [])
        self.assertFalse(sweep_dir.exists())
        kept = list((root / "edit_layers" / "deleted").glob("s2--deleted-*/sweep.json"))
        self.assertEqual(len(kept), 1)

    def test_hiding_a_sweep_clears_it_from_the_list_but_keeps_its_results(self):
        import json
        from unittest import mock
        root = self.run / "investigations"
        sweep_dir = root / "edit_layers" / "sweeps" / "s3"
        sweep_dir.mkdir(parents=True)
        (sweep_dir / "sweep.json").write_text(json.dumps({"id": "s3", "runs": [{"job_id": "3"}]}))
        with mock.patch.object(config, "INVESTIGATIONS_DIR", root), \
             mock.patch.object(hparam_sweeps, "_statuses", return_value={"3": {"state": "COMPLETED"}}):
            hparam_sweeps.set_hidden("edit_layers", "s3", True)
            listed = [s["id"] for _, s in hparam_sweeps._sweeps("edit_layers")]
            self.assertEqual(listed, ["s3"])  # what results() reads
            self.assertTrue(json.loads((sweep_dir / "sweep.json").read_text())["hidden"])
            hparam_sweeps.set_hidden("edit_layers", "s3", False)
            self.assertNotIn("hidden", json.loads((sweep_dir / "sweep.json").read_text()))
        self.assertTrue(sweep_dir.exists())

    def test_a_sweep_with_active_runs_cannot_be_hidden(self):
        import json
        from unittest import mock
        sweep_dir = self.run / "sweeps" / "s4"
        sweep_dir.mkdir(parents=True)
        (sweep_dir / "sweep.json").write_text(json.dumps({"id": "s4", "runs": [{"job_id": "4"}]}))
        with mock.patch.object(hparam_sweeps, "_sweep_dir", return_value=sweep_dir), \
             mock.patch.object(hparam_sweeps, "_statuses", return_value={"4": {"state": "PENDING"}}):
            with self.assertRaisesRegex(ValueError, "cancel them first"):
                hparam_sweeps.set_hidden("edit_layers", "s4", True)


if __name__ == "__main__":
    unittest.main()
