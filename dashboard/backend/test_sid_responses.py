"""Sid's Dataset post-edit answers (sid_responses.py): which run each method x
model uses, the dot colour per query type (mirroring sid_evaluation's
scoring), and the before/after detail behind one dot."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

import config
import sid_responses as S

QWEN, OLMO = "qwen3-4b-instruct-2507", "olmo-3-7b-instruct"

RECORD = {
    "id": "geography-replace-0001", "topic": "geography", "edit_operation": "replace", "box": "abox",
    "edit": {"statement": "Lyon is in Italy.", "object": "Italy", "old_object": "France"},
    "queries": {"derived": [{"prompt": "Is Lyon in the EU?", "determinacy": "determinate"},
                            {"prompt": "Which language is spoken in Lyon?", "determinacy": "background_beliefs"}]},
}


def ans(label, score=None, rule="new", form="WELL_FORMED", qtype="direct", response="x", **extra):
    a = {"query_type": qtype, "language": "en", "question": f"{qtype}?", "response": response,
         "verdict": {"label": label, "reason": f"because {label}"}, "score": score}
    if form:
        a["form"] = {"label": form, "reason": f"form {form}"}
    if qtype not in S.LOCALITY:
        a["expected"] = {"rule": rule, "original_answer": "France", "new_answer": "Italy"}
    a.update(extra)
    return a


def payload(step, queries, rid=RECORD["id"]):
    return {"step": step, "evaluation": "sid", "judged": True,
            "records": [{"record_id": rid, "case_id": 0, "queries": queries}]}


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.root = root
        rec_dir = root / "datasets" / "SidsDataset" / "records" / "geography" / "replace"
        rec_dir.mkdir(parents=True)
        (rec_dir / f"{RECORD['id']}.json").write_text(json.dumps(RECORD))
        self.patches = [mock.patch.object(config, name, value) for name, value in {
            "PROJECT_ROOT": root, "INVESTIGATIONS_DIR": root / "results" / "investigations",
            "MAIN_RESULTS_DIR": root / "results" / "main", "DATASETS_DIR": root / "datasets"}.items()]
        for p in self.patches:
            p.start()
        S._cache.clear()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.tmp.cleanup()

    def run_dir(self, parent, method, model, steps, finished="2026-11-03T10:00:00", benchmark="SidsDataset",
                name=None):
        d = parent / (name or f"{method}_{model}_records_current")
        (d / "samples").mkdir(parents=True)
        (d / "summary.json").write_text(json.dumps({
            "method": method, "model": model, "dataset_benchmark": benchmark, "finished_at": finished,
            "edit_mode": "single", "reset_every": 1, "split": "screen"}))
        for p in steps:
            (d / "samples" / f"sid_step_{p['step']:06d}.json").write_text(json.dumps(p))
        return d

    def sweep(self, family, sweep_id):
        return self.root / "results" / "investigations" / family / "sweeps" / sweep_id / "runs"


class PickRunsTest(Fixture):
    def test_one_run_per_pair_newest_finished_and_deleted_skipped(self):
        base = payload(0, {"direct": ans("ORIGINAL", 0)})
        after = payload(1, {"direct": ans("NEW", 1)})
        self.run_dir(self.sweep("locate_edit", "a"), "rome", QWEN, [base, after], finished="2026-11-02T10:00:00")
        newer = self.run_dir(self.sweep("locate_edit", "b"), "rome", QWEN, [base, after], finished="2026-11-03T10:00:00")
        trash = self.root / "results" / "investigations" / "locate_edit" / "deleted" / "c--deleted" / "runs"
        self.run_dir(trash, "rome", OLMO, [base, after], finished="2026-11-09T10:00:00")
        # Not Sid's Dataset, not a main model, not a tab method, not the default-settings run.
        self.run_dir(self.sweep("locate_edit", "d"), "rome", OLMO, [base, after], benchmark="MQuAKE")
        self.run_dir(self.sweep("locate_edit", "e"), "rome", "gpt-j-6b", [base, after])
        self.run_dir(self.sweep("locate_edit", "f"), "memit", QWEN, [base, after])
        self.run_dir(self.sweep("locate_edit", "g"), "rome", OLMO, [base, after], name=f"rome_{OLMO}_records_lhs01")
        runs = S.pick_runs("sweep_current")
        self.assertEqual(list(runs), ["rome"])
        self.assertEqual(list(runs["rome"]), [QWEN])
        self.assertEqual(runs["rome"][QWEN]["path"], str(newer.relative_to(self.root)))
        self.assertEqual(runs["rome"][QWEN]["steps"], [0, 1])

    def test_main_source_reads_results_main(self):
        main_runs = self.root / "results" / "main" / "run_experiment" / "runs"
        self.run_dir(main_runs, "ft", OLMO, [payload(0, {}), payload(1, {"direct": ans("NEW", 1)})], name="ft_olmo_test")
        self.assertEqual(S.pick_runs("main")["ft"][OLMO]["run"], "ft_olmo_test")
        self.assertEqual(S.pick_runs("sweep_current"), {})
        with self.assertRaises(KeyError):
            S.pick_runs("nope")

    def test_overview_lists_methods_in_tab_order(self):
        o = S.overview()
        self.assertEqual([m["label"] for m in o["methods"]],
                         ["FT-M", "LoRA", "ROME", "AlphaEdit", "FiDAL", "FiNE", "IFMET", "LTI", "LoCo"])
        self.assertEqual(o["models"], S.MAIN_MODELS)
        self.assertEqual(o["source"], S.DEFAULT_SOURCE)


class ClassifyTest(unittest.TestCase):
    def test_answer_query_colours(self):
        self.assertEqual(S.classify(ans("NEW", 1), "direct")["status"], "pass")
        self.assertEqual(S.classify(ans("ORIGINAL", 0), "direct")["status"], "original")
        self.assertEqual(S.classify(ans("OTHER", 0), "paraphrase")["status"], "other")
        self.assertEqual(S.classify(ans("WORLD", 0), "derived")["status"], "other")
        self.assertEqual(S.classify(ans("NONE", 0), "direct")["status"], "none")
        self.assertEqual(S.classify(ans("UNCLEAR", None), "direct")["status"], "unclear")
        unjudged = {"query_type": "direct", "response": "x"}
        self.assertEqual(S.classify(unjudged, "direct")["status"], "unclear")

    def test_delete_passes_on_abstaining(self):
        dot = S.classify(ans("NONE", 1, rule="abstain"), "direct")
        self.assertEqual((dot["status"], dot["kind"]), ("pass", "delete"))
        self.assertEqual(S.classify(ans("ORIGINAL", 0, rule="abstain"), "direct")["status"], "original")

    def test_indeterminate_passes_on_any_world(self):
        # ORIGINAL that is some world's answer passes (the stored score says so).
        dot = S.classify(ans("ORIGINAL", 1, rule="worlds", worlds=["w1"]), "derived")
        self.assertEqual((dot["status"], dot["kind"]), ("pass", "worlds"))
        self.assertEqual(S.classify(ans("OTHER", 0, rule="worlds"), "derived")["status"], "other")

    def test_score_fallback_when_not_stored(self):
        a = ans("NEW")
        del a["score"]
        self.assertEqual(S.classify(a, "direct")["status"], "pass")
        b = ans("ORIGINAL", rule="worlds", worlds=["w2"])
        del b["score"]
        self.assertEqual(S.classify(b, "derived")["status"], "pass")

    def test_locality_kept_changed_and_leak(self):
        rec = {"edit": {"object": "Italy"}}
        self.assertEqual(S.classify(ans("SAME", qtype="unrelated_near"), "unrelated_near")["status"], "kept")
        leak = S.classify(ans("DIFFERENT", qtype="unrelated_near", response="Italy", before="Spain"),
                          "unrelated_near", rec=rec)
        self.assertEqual((leak["status"], leak["leak"]), ("changed", True))
        wrong = S.classify(ans("DIFFERENT", qtype="unrelated_far", response="Mozart", before="Beethoven"),
                           "unrelated_far", rec=rec)
        self.assertEqual((wrong["status"], wrong["leak"]), ("changed", False))
        self.assertEqual(S.classify(ans("UNCLEAR", qtype="unrelated_far"), "unrelated_far")["status"], "unclear")

    def test_malformed_form_and_known(self):
        dot = S.classify(ans("NEW", 1, form="MALFORMED"), "direct", baseline=ans("OTHER", 0))
        self.assertEqual((dot["form"], dot["known"]), ("MALFORMED", False))
        self.assertNotIn("counted", dot)

    def test_unknown_determinate_derived_is_not_counted(self):
        unknown = S.classify(ans("NEW", 1, qtype="derived"), "derived", baseline=ans("NEW", 1), rec=RECORD,
                             key="derived[0]")
        self.assertIs(unknown["counted"], False)
        known = S.classify(ans("NEW", 1, qtype="derived"), "derived", baseline=ans("ORIGINAL", 0), rec=RECORD,
                           key="derived[0]")
        self.assertNotIn("counted", known)
        indeterminate = S.classify(ans("NEW", 1, rule="worlds", qtype="derived"), "derived",
                                   baseline=ans("NEW", 1), rec=RECORD, key="derived[1]")
        self.assertNotIn("counted", indeterminate)


class EndpointTest(Fixture):
    def setUp(self):
        super().setUp()
        import main
        self.client = TestClient(main.app, headers={"x-dashboard-token": main.AUTH_TOKEN})
        rid = RECORD["id"]
        before = payload(0, {"direct": ans("ORIGINAL", 0, response="France"),
                             "unrelated_near[0]": ans("SAME", qtype="unrelated_near", response="Spain")})
        own = payload(1, {"direct": ans("NEW", 1, response="Italy")})
        end = payload(2, {"direct": ans("ORIGINAL", 0, response="France", form="MALFORMED"),
                          "unrelated_near[0]": ans("DIFFERENT", qtype="unrelated_near", response="Italy",
                                                   before="Spain")})
        self.run_dir(self.sweep("finetuning", "s1"), "ft", QWEN, [before, own, end])
        self.rid = rid

    def get(self, url, **params):
        return self.client.get(url, params=params)

    def test_method_dots(self):
        r = self.get("/api/sid-responses/ft")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["edited"], {QWEN: [self.rid]})
        q = data["records"][self.rid]["queries"]
        # End state: the last step holding the record.
        self.assertEqual(q["direct"][QWEN]["status"], "original")
        self.assertEqual(q["direct"][QWEN]["form"], "MALFORMED")
        self.assertEqual(q["unrelated_near[0]"][QWEN]["status"], "changed")
        self.assertTrue(q["unrelated_near[0]"][QWEN]["leak"])
        self.assertNotIn(OLMO, q["direct"])
        self.assertEqual(self.get("/api/sid-responses/nope").status_code, 404)
        self.assertEqual(self.get("/api/sid-responses", source="nope").status_code, 404)

    def test_detail_before_after_and_own_edit(self):
        r = self.get("/api/sid-responses/ft/detail", model=QWEN, record=self.rid, key="direct")
        d = r.json()
        self.assertEqual(d["question"], "direct?")
        self.assertEqual((d["before"]["step"], d["before"]["response"]), (0, "France"))
        self.assertEqual((d["after"]["step"], d["after"]["response"]), (2, "France"))
        self.assertEqual((d["after_own_edit"]["step"], d["after_own_edit"]["response"]), (1, "Italy"))
        self.assertEqual(d["after_own_edit"]["dot"]["status"], "pass")
        none = self.get("/api/sid-responses/ft/detail", model=OLMO, record=self.rid, key="direct").json()
        self.assertIsNone(none["run"])


if __name__ == "__main__":
    unittest.main()
