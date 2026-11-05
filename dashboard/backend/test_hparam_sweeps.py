"""Sweep planning: what is varied, what is held constant, and at what value.

plan() submits nothing, so these run anywhere the hparams files exist.
"""
import os
import unittest

import config
import hparam_sweeps

DATASET = os.path.join(str(config.PROJECT_ROOT), "datasets/KnowEdit/benchmark/wiki_counterfact/test_cf.json")


def request(**extra):
    return {"investigation": "locate_edit", "design": "grid", "methods": {"rome": {"layers": [[4], [5]]}},
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
        held = hparam_sweeps.settings("dynamic_locate_edit", ["rome"], ["qwen3-4b"])["rome"]["qwen3-4b"]
        owners = {r["key"]: (r["owner"] or {}).get("id") for r in held}
        self.assertEqual(owners["v_lr"], "locate_edit")
        self.assertEqual(owners["kl_factor"], "locate_edit")
        self.assertIsNone(owners["fact_token"])


class MethodInvestigationTests(unittest.TestCase):
    """One investigation per method family owns every setting of its methods."""

    # The core method set: methods outside it (FT-L, MEMIT, PMET, WilKE, KN, NMKE, CaKE, IKE, SCR) are no longer swept.
    FAMILIES = {"finetuning": {"ft", "lora"}, "locate_edit": {"rome", "alphaedit"},
                "dynamic_locate_edit": {"fidal"}, "neuron_editors": {"fine"},
                "portability": {"ifmet", "lti", "loco"}}

    def test_each_family_owns_its_methods_settings(self):
        owners = hparam_sweeps._owners()
        for key in ("layers", "lr", "num_steps", "weight_decay", "norm_constraint"):
            self.assertEqual(owners[("ft", key)]["id"], "finetuning", key)
        # FT-M is pinned to its objective, so it is not a setting to sweep;
        # FT-L is outside the core set and not swept at all.
        self.assertNotIn(("ft", "objective_optimization"), owners)
        self.assertFalse([k for k in owners if k[0] == "ft_l"])
        for key in ("rank", "target_modules", "layers", "lr", "num_steps", "lora_alpha", "lora_dropout",
                    "weight_decay", "lora_type"):
            self.assertEqual(owners[("lora", key)]["id"], "finetuning", key)
        catalog = {i["id"]: i for i in hparam_sweeps._load_catalog()["investigations"]}
        for family, methods in self.FAMILIES.items():
            self.assertEqual(set(catalog[family]["methods"]), methods, family)
        # Every setting an earlier by-setting sweep tuned is in its method's family.
        for inv in catalog.values():
            if not inv.get("legacy"):
                continue
            for method, entry in inv["methods"].items():
                family = next((f for f, ms in self.FAMILIES.items() if method in ms), None)
                if family is None:
                    continue  # outside the core set, no longer swept
                self.assertLessEqual(set(entry["knobs"]), set(catalog[family]["methods"][method]["knobs"]),
                                     (inv["id"], method))
        self.assertNotIn("scr", {m for i in catalog.values() if i["group"] == "sweep" for m in i["methods"]})

    def test_retired_sweeps_are_gone(self):
        with self.assertRaisesRegex(ValueError, "unknown investigation"):
            hparam_sweeps.plan({**request(), "investigation": "edit_layers"})

    def test_one_at_a_time_shares_one_run_at_the_current_settings(self):
        current = {r["key"]: r["value"] for r in hparam_sweeps.effective_settings("rome", "qwen3-4b")}
        req = request(design="one_at_a_time", methods={"rome": {
            "v_lr": [current["v_lr"], current["v_lr"] * 10], "kl_factor": [current["kl_factor"] / 10]}})
        _, _, runs, _ = hparam_sweeps.plan(req)
        self.assertEqual([r["overrides"] for r in runs],
                         [{}, {"kl_factor": current["kl_factor"] / 10}, {"v_lr": current["v_lr"] * 10}])
        self.assertTrue(runs[0]["run_name"].endswith("_current"))
        self.assertEqual(runs[0]["baseline_for"], {"v_lr": current["v_lr"], "kl_factor": current["kl_factor"]})
        self.assertNotIn("baseline_for", runs[1])

    def test_int_suggestions_are_five_spread_values(self):
        self.assertEqual(hparam_sweeps.suggest("int", 20), [5, 10, 20, 40, 80])
        self.assertEqual(len(hparam_sweeps.suggest("log", 0.5)), 5)

    def test_every_knob_has_a_current_value(self):
        settings = {m: {r["key"] for r in hparam_sweeps.effective_settings(m, "qwen3-4b") if r["editable"]}
                    for m in ("ft", "lora")}
        for method in ("ft", "lora"):
            knobs = hparam_sweeps._load_catalog()["investigations"]
            knobs = next(i for i in knobs if i["id"] == "finetuning")["methods"][method]["knobs"]
            self.assertEqual(set(knobs) - settings[method], set(), method)

    def test_ft_m_and_ft_l_are_separate_methods(self):
        req = {"investigation": "finetuning", "design": "grid",
               "methods": {"ft": {"lr": [1e-4, 1e-3]}},
               "models": ["qwen3-4b"], "data_paths": [DATASET], "ds_size": "full", "edit_mode": "batch"}
        _, _, runs, _ = hparam_sweeps.plan(req)
        self.assertEqual(sorted(r["method"] for r in runs), ["ft", "ft"])
        # FT-L left the core set, so the family sweep no longer takes it.
        with self.assertRaises(ValueError):
            hparam_sweeps.plan({**req, "methods": {"ft_l": {"lr": [1e-4]}}})
        # Each reads its own hparams file, pinned to its own objective.
        self.assertEqual({m: dict((r["key"], r["value"]) for r in hparam_sweeps.effective_settings(m, "qwen3-4b"))
                          ["objective_optimization"] for m in ("ft", "ft_l")},
                         {"ft": "target_new", "ft_l": "prompt_last"})
        # The objective is no longer sweepable: switching it would turn one method into the other.
        req["methods"] = {"ft": {"objective_optimization": ["target_new", "prompt_last"]}}
        with self.assertRaisesRegex(ValueError, "objective_optimization"):
            hparam_sweeps.plan(req)

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
        # IKE left the investigations with the other non-core methods (2026-11-02).
        self.assertNotIn("retrieval", {i["id"] for i in hparam_sweeps._load_catalog()["investigations"]})

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


class SidScoresTests(unittest.TestCase):
    def test_sid_runs_choose_by_rewrite_and_record_paraphrase(self):
        summary = {"edit_succ": 75.0, "portability": 40.0, "locality": 90.0, "fluency": 5.0,
                   "evaluations": {"sid": {"metrics": {"rewrite": {"score": 100.0}, "paraphrase": {"score": 50.0}}}}}
        scores = hparam_sweeps._scores(summary, {"fluency": 5.0})
        self.assertEqual((scores["reliability"], scores["paraphrase"]), (1.0, 0.5))
        self.assertEqual((scores["generalizability"], scores["locality"], scores["fluency"]), (0.4, 0.9, 1.0))
        # Other datasets keep EasyEdit's edit success, and have no paraphrase score here.
        other = hparam_sweeps._scores({"edit_succ": 75.0, "fluency": 5.0}, {"fluency": 5.0})
        self.assertEqual(other["reliability"], 0.75)
        self.assertNotIn("paraphrase", other)

    def test_sid_generalizability_counts_only_derived_questions_known_before_the_edit(self):
        summary = {"portability": 40.0, "fluency": 5.0, "evaluations": {"sid": {"metrics": {
            "rewrite": {"score": 100.0},
            "generalization": {"score": 40.0, "determinate": {"score": 45.0, "known": {"score": 30.0}}}}}}}
        self.assertEqual(hparam_sweeps._scores(summary, {"fluency": 5.0})["generalizability"], 0.3)

    def test_judged_grammar_is_a_share_of_the_unedited_models_and_gates_the_choice(self):
        def summary(wf):
            return {"fluency": 5.0, "evaluations": {"sid": {"metrics": {
                "rewrite": {"score": 100.0}, "paraphrase": {"score": 50.0}, "well_formed": {"score": wf}}}}}
        base = {"fluency": 5.0, "evaluations": {"sid": {"metrics": {"well_formed": {"score": 96.0}}}}}
        good = hparam_sweeps._scores(summary(96.0), base)
        bad = hparam_sweeps._scores(summary(72.0), base)
        self.assertEqual(good["well_formed"], 1.0)
        self.assertAlmostEqual(bad["well_formed"], 0.75)
        self.assertTrue(hparam_sweeps._keeps_fluency(good))
        self.assertFalse(hparam_sweeps._keeps_fluency(bad))
        self.assertIn("judge: well-formed answers fell 25%",
                      [f["text"] for f in hparam_sweeps._flags("COMPLETED", None, None, bad)])
        # Runs judged before the form pass have no grammar score and are not held back by it.
        old = hparam_sweeps._scores({"fluency": 5.0, "evaluations": {"sid": {"metrics": {"rewrite": {"score": 100.0}}}}},
                                    {"fluency": 5.0})
        self.assertIsNone(old["well_formed"])
        self.assertTrue(hparam_sweeps._keeps_fluency(old))


class LatinHypercubeTests(unittest.TestCase):
    KNOBS = {"v_lr": [0.05, 0.1, 0.5, 1.0], "kl_factor": [0.01, 0.1], "layers": [[3], [4], [5], [6]]}

    def test_each_value_is_used_evenly(self):
        points = hparam_sweeps._lhs(self.KNOBS, 8, 0, "rome")
        self.assertEqual(len(points), 8)
        for key, values in self.KNOBS.items():
            used = [p[key] for p in points]
            for v in values:
                self.assertEqual(used.count(v), 8 // len(values), (key, v))

    def test_the_draw_depends_on_seed_and_method_not_model(self):
        a = hparam_sweeps._lhs(self.KNOBS, 8, 0, "rome")
        self.assertEqual(a, hparam_sweeps._lhs(self.KNOBS, 8, 0, "rome"))
        self.assertNotEqual(a, hparam_sweeps._lhs(self.KNOBS, 8, 1, "rome"))
        req = request(design="lhs", samples=4, methods={"rome": self.KNOBS}, models=["qwen3-4b", "llama-3.1-8b"])
        _, _, runs, _ = hparam_sweeps.plan(req)
        by_model = {}
        for r in runs:
            by_model.setdefault(r["model"], []).append(r["overrides"])
        self.assertEqual(len(set(map(str, by_model.values()))), 1)

    def test_a_current_run_then_numbered_samples(self):
        _, _, runs, _ = hparam_sweeps.plan(request(design="lhs", samples=3, methods={"rome": self.KNOBS}))
        self.assertEqual([r["run_name"].rsplit("_", 1)[1] for r in runs], ["current", "lhs01", "lhs02", "lhs03"])
        self.assertEqual(runs[0]["overrides"], {})
        self.assertEqual(set(runs[1]["overrides"]), set(self.KNOBS))

    def test_samples_are_required(self):
        with self.assertRaisesRegex(ValueError, "samples"):
            hparam_sweeps.plan(request(design="lhs"))


class ScreenSplitTests(unittest.TestCase):
    def test_screen_is_only_for_sids_dataset(self):
        with self.assertRaisesRegex(ValueError, "screen"):
            hparam_sweeps.plan(request(split="screen"))
        with self.assertRaisesRegex(ValueError, "split must be"):
            hparam_sweeps.plan(request(split="test"))


class SweepKindTests(unittest.TestCase):
    def test_kinds(self):
        self.assertEqual(hparam_sweeps.sweep_kind({"request": {"design": "lhs"}}), "lhs")
        self.assertEqual(hparam_sweeps.sweep_kind({"request": {"design": "one_at_a_time"}}), "stagewise")
        self.assertEqual(hparam_sweeps.sweep_kind({"request": {}}), "stagewise")
        self.assertEqual(hparam_sweeps.sweep_kind({"purpose": "setup", "request": {"design": "one_at_a_time"}}), "setup")


class FactorialSweepTests(unittest.TestCase):
    FT = {"layers": [[5], [24]], "lr": [1.5e-4, 1.5e-3], "num_steps": [12, 50],
          "norm_constraint": [1.5e-4, 5e-4], "weight_decay": [0, 0.01]}

    def req(self, **extra):
        return {"investigation": "finetuning", "design": "factorial2", "methods": {"ft": self.FT},
                "models": ["qwen3-4b-instruct-2507"], "data_paths": [DATASET], "ds_size": "full",
                "edit_mode": "single", **extra}

    def test_full_design_plus_three_centre_runs_named_by_their_levels(self):
        _, _, runs, _ = hparam_sweeps.plan(self.req())
        corners = [r for r in runs if r["point"] == "corner"]
        centres = [r for r in runs if r["point"] == "centre"]
        self.assertEqual((len(corners), len(centres)), (32, 3))
        factors = sorted(self.FT)
        for r in corners:
            code = r["run_name"].rsplit("-", 1)[1]
            self.assertEqual(code, "".join("H" if r["coded"][f] > 0 else "L" for f in factors))
            for f in factors:
                self.assertEqual(r["overrides"][f], self.FT[f][1 if r["coded"][f] > 0 else 0])
        # Balanced: each level of each setting in half the corners.
        for f in factors:
            self.assertEqual(sum(r["coded"][f] for r in corners), 0)
        self.assertEqual(centres[0]["overrides"]["layers"], [15])
        self.assertEqual(centres[0]["overrides"]["num_steps"], 24)
        self.assertEqual([r["seed"] for r in centres], [0, 1, 2])
        self.assertEqual([r["params"]["seed"] for r in centres], [0, 1, 2])
        self.assertTrue(all(r["run_name"].endswith("-MMMMM") for r in centres))

    def test_fraction_and_centre_points_are_choices(self):
        _, _, runs, _ = hparam_sweeps.plan(self.req(fraction=1, centre_points=0))
        self.assertEqual(len(runs), 16)
        _, _, runs, _ = hparam_sweeps.plan(self.req(fraction={"ft": 1}, centre={"ft": {"layers": [20]}}))
        self.assertEqual(len(runs), 19)
        self.assertEqual(runs[-1]["overrides"]["layers"], [20])
        with self.assertRaisesRegex(ValueError, "no standard"):
            hparam_sweeps.plan(self.req(fraction=2))

    def test_each_setting_needs_exactly_two_values(self):
        with self.assertRaisesRegex(ValueError, "two different values"):
            hparam_sweeps.plan(self.req(methods={"ft": {**self.FT, "lr": [1e-4, 1e-3, 1e-2]}}))
        with self.assertRaisesRegex(ValueError, "at least two settings"):
            hparam_sweeps.plan(self.req(methods={"ft": {"lr": [1e-4, 1e-3]}}))

    def test_estimate_reports_the_design(self):
        est = hparam_sweeps.estimate(self.req())
        design = est["factorial"]["ft"]
        self.assertEqual((design["k"], design["p"], design["runs"]), (5, 0, 32))
        self.assertIn("corners", hparam_sweeps.factorial_designs(self.req(), hparam_sweeps.plan(self.req())[1])["ft"])
        self.assertNotIn("corners", design)

    def test_kind_and_step(self):
        sweep = {"request": {"design": "factorial2"}}
        self.assertEqual(hparam_sweeps.sweep_kind(sweep), "factorial")
        self.assertEqual(hparam_sweeps.sweep_step(sweep), 1)
        self.assertEqual(hparam_sweeps.sweep_step({"step": 0, "request": {"design": "lhs"}}), 0)
        self.assertIsNone(hparam_sweeps.sweep_step({"request": {"design": "one_at_a_time"}}))


class FactorialEffectsTests(unittest.TestCase):
    def test_effects_on_rewrite_gate_and_time(self):
        import json
        import tempfile
        from pathlib import Path
        from unittest.mock import patch

        factors = ["lr", "num_steps", "weight_decay"]
        rows = hparam_sweeps.factorial.design(3, 0)
        runs, results = [], []
        for n, row in enumerate(rows):
            coded = dict(zip(factors, row))
            name = f"r{n}"
            runs.append({"run_name": name, "method": "ft", "model": "m", "data_path": "d", "coded": coded,
                         "point": "corner", "overrides": {}, "job_id": str(n)})
            # High lr: +0.4 rewrite but breaks fluency; more steps: slower, +0.05 rewrite.
            rewrite = 0.4 + 0.2 * coded["lr"] + 0.025 * coded["num_steps"]
            fluency = 0.5 if coded["lr"] > 0 else 1.0
            results.append({"sweep_id": "s", "run": name, "state": "COMPLETED",
                            "scores": {"reliability": rewrite, "fluency": fluency, "well_formed": 1.0},
                            "edit_sec": 10 + 5 * (coded["num_steps"] + 1)})
        # A failed run counts as missing, not as a score of 0.
        results[-1] = {"sweep_id": "s", "run": runs[-1]["run_name"], "state": "FAILED", "scores": {}, "edit_sec": None}
        runs.append({"run_name": "c1", "method": "ft", "model": "m", "data_path": "d",
                     "coded": dict.fromkeys(factors, 0), "point": "centre", "overrides": {}, "job_id": "c"})
        results.append({"sweep_id": "s", "run": "c1", "state": "COMPLETED",
                        "scores": {"reliability": 0.4, "fluency": 1.0, "well_formed": 1.0}, "edit_sec": 15})
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "sweep.json").write_text(json.dumps({
                "id": "s", "request": {"design": "factorial2"}, "runs": runs,
                "factorial": {"ft": {"factors": factors, "levels": {f: {"low": 0, "high": 1} for f in factors}}}}))
            with patch.object(hparam_sweeps, "_sweep_dir", return_value=Path(tmp)), \
                    patch.object(hparam_sweeps, "results", return_value=results):
                out = hparam_sweeps.effects("finetuning", "s")
        self.assertEqual(out["step"], 1)
        group = out["groups"][0]
        self.assertEqual((group["finished"], group["total"]), (8, 9))
        rewrite = {m["factor"]: m for m in group["analyses"]["rewrite"]["main"]}
        self.assertEqual(group["analyses"]["rewrite"]["used"], 7)
        # One corner missing: the contrasts are no longer balanced, so close, not exact.
        self.assertFalse(group["analyses"]["rewrite"]["complete"])
        self.assertAlmostEqual(rewrite["lr"]["effect"], 0.4, delta=0.01)
        gate = {m["factor"]: m for m in group["analyses"]["gate"]["main"]}
        self.assertAlmostEqual(gate["lr"]["effect"], -1.0)
        time = {m["factor"]: m for m in group["analyses"]["edit_sec"]["main"]}
        self.assertAlmostEqual(time["num_steps"]["effect"], 10.0)
        self.assertEqual(group["analyses"]["rewrite"]["curvature"]["centre_runs"], 1)

    def test_suggestions_follow_the_time_rule(self):
        def main(effect, verdict):
            return {"effect": effect, "verdict": verdict}
        levels = {"low": 12, "high": 50}
        by = {"rewrite": {"s": main(0.05, "active")}, "gate": {"s": main(0.0, "noise")},
              "edit_sec": {"s": main(30.0, "active")}}
        hint = hparam_sweeps._suggest("s", by, levels)
        self.assertEqual((hint["level"], hint["value"]), ("low", 12))
        self.assertIn("time rule", hint["text"])
        by["rewrite"]["s"] = main(0.3, "strong")
        self.assertEqual(hparam_sweeps._suggest("s", by, levels)["level"], "high")
        by["rewrite"]["s"] = main(0.01, "noise")
        self.assertEqual(hparam_sweeps._suggest("s", by, levels)["level"], "low")
