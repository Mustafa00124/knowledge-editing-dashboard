"""Sid's Dataset review marks (datasets/SidsDataset/criteria.py, reviews.json)
and the Rule 3 checks: the manual rules and their guidance read from
CRITERIA.md, migrating old review shapes (flags become red marks), green and
red marks per record and per query written under a lock, the checklist rows,
the pattern checks and the judge cache, and the dashboard's mark endpoint
(who may mark as whom)."""
import contextlib
import importlib
import importlib.util
import io
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

with contextlib.redirect_stdout(io.StringIO()):
    main = importlib.import_module("main")


def load_criteria():
    path = main.config.DATASETS_DIR / "SidsDataset" / "criteria.py"
    spec = importlib.util.spec_from_file_location("sids_criteria_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


C = load_criteria()
OPS, BOXES = ("replace", "delete", "insert"), ("abox", "tbox", "rbox")


def record(rid, topic="geography", op="replace", box="abox", **edit):
    return {"id": rid, "topic": topic, "edit_operation": op, "box": box, "relation": "located_in",
            "edit": {"statement": "Lyon is in Italy.", "subject": "Lyon", "object": "Italy", "old_object": "France",
                     "original": "Lyon is in France.", **edit},
            "queries": {"direct": {"prompt": "Which country is Lyon in?", "original_answer": "France",
                                   "new_answer": "Italy"}}}


def dataset(per_cell=3):
    """10 topics x 3 operations x 3 boxes x per_cell records."""
    return [record(f"{t}-{op}-{box}-{i:04d}", t, op, box)
            for t in C.TOPICS for op in OPS for box in BOXES for i in range(per_cell)]


class Temp(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "reviews.json"
        self.lock = Path(self.tmp.name) / ".reviews.lock"


class ManualRulesTest(unittest.TestCase):
    def test_rules_come_from_criteria_md(self):
        self.assertEqual([k for k, *_ in C.MANUAL_RULES], ["clear-and-sensible", "serves-the-purpose"])
        rules = {r["key"]: r for r in C.MANUAL["rules"]}
        self.assertEqual(rules["clear-and-sensible"]["title"], "Clear and sensible")
        self.assertTrue(rules["clear-and-sensible"]["statement"].startswith("Read the edit"))
        self.assertEqual(rules["clear-and-sensible"]["guide"], "")
        self.assertNotIn("<details>", rules["serves-the-purpose"]["statement"])
        self.assertNotIn("What we are studying", rules["serves-the-purpose"]["statement"])
        self.assertIn("| Part | What it measures |", rules["serves-the-purpose"]["guide"])
        self.assertNotIn("details>", rules["serves-the-purpose"]["guide"])

    def test_parse_small_doc(self):
        doc = ("# T\n\n## Manual rules\n\n**Rule 1. One** (`one`). First\nrule.\n\n"
               "**Rule 2. Two** (`two`). Second.\n\n<details>\n\n- a\n  - b\n\n</details>\n\n"
               "## Automated rules\n\n**Rule 3. Three.** auto\n")
        self.assertEqual(C.parse_criteria(doc)["rules"], [
            {"number": 1, "title": "One", "key": "one", "statement": "First rule.", "guide": ""},
            {"number": 2, "title": "Two", "key": "two", "statement": "Second.", "guide": "- a\n  - b"}])


class MigrationTest(Temp):
    def test_old_shapes_are_dropped(self):
        for old in ({"labels-and-worlds": {"human": {"done": False}}},
                    {"version": 2, "plan": {"calibration": ["x"]}, "marks": {"x": {"clear-and-sensible": {"r1": {}}}}}):
            self.path.write_text(json.dumps(old))
            self.assertEqual(C.load_reviews(self.path), {"version": 4, "marks": {}})

    def test_flags_become_red_marks(self):
        f = {"id": "a1", "rule": "clear-and-sensible", "reviewer": "adarsh", "kind": "angle", "comment": "c1",
             "at": "t", "record_hash": "h"}
        self.path.write_text(json.dumps({"version": 3, "flags": {"x": [
            f, dict(f, id="a2", kind="problem", comment="c2"), dict(f, reviewer="claude"),
            dict(f, rule="stable-subjects"), dict(f, reviewer="human")]}}))
        marks = C.load_reviews(self.path)["marks"]["x"]["clear-and-sensible"]
        self.assertEqual(marks["adarsh"], {"state": "red", "kind": "problem", "comment": "c1 | c2", "at": "t",
                                           "record_hash": "h"})
        self.assertEqual(marks["claude"]["kind"], "angle")
        self.assertEqual(set(marks), {"adarsh", "claude"})

    def test_bad_marks_dropped(self):
        good = {"state": "red", "kind": "angle", "comment": "c"}
        self.path.write_text(json.dumps({"version": 4, "marks": {"x": {"direct": {
            "mustafa": good, "human": good, "adarsh": dict(good, kind="fix"), "codex": {"state": "yellow"},
            "claude": {"state": "red"}}}}}))
        self.assertEqual(C.load_reviews(self.path)["marks"], {"x": {"direct": {"mustafa": good,
                                                                                 "claude": {"state": "red"}}}})

    def test_missing_or_broken_file(self):
        self.assertEqual(C.load_reviews(self.path)["marks"], {})
        self.path.write_text("{not json")
        self.assertEqual(C.load_reviews(self.path)["version"], 4)


class MarkTest(Temp):
    def setUp(self):
        super().setUp()
        self.recs = dataset(per_cell=1)
        for r in self.recs:
            r["queries"]["cross_lingual"] = [{"prompt": "Lyon?", "language": "zh", "original_answer": "a",
                                              "new_answer": "b"}]
        self.rid = self.recs[0]["id"]
        self.kw = dict(path=self.path, lock=self.lock)

    def mark(self, *args, **kw):
        return C.set_mark(*args, recs=self.recs, **self.kw, **kw)

    def test_query_keys(self):
        self.assertEqual(C.query_keys(self.recs[0]), ["direct", "cross_lingual[zh]"])

    def test_set_and_clear(self):
        self.mark(self.rid, "clear-and-sensible", "mustafa", "green")
        marks = self.mark(self.rid, "cross_lingual[zh]", "claude", "red", comment="answer in the name", kind="angle")
        self.assertEqual(marks["clear-and-sensible"]["mustafa"]["state"], "green")
        self.assertEqual(marks["cross_lingual[zh]"]["claude"]["kind"], "angle")
        self.assertNotIn("kind", marks["clear-and-sensible"]["mustafa"])
        bare = self.mark(self.rid, "direct", "adarsh", "red")["direct"]["adarsh"]
        self.assertEqual((bare["state"], "comment" in bare, "kind" in bare), ("red", False, False))
        self.mark(self.rid, "direct", "adarsh", None)
        self.assertEqual(json.loads(self.path.read_text())["version"], 4)
        self.mark(self.rid, "clear-and-sensible", "mustafa", None)
        marks = self.mark(self.rid, "cross_lingual[zh]", "claude", None)
        self.assertEqual(marks, {})
        self.assertEqual(json.loads(self.path.read_text())["marks"], {})

    def test_validation(self):
        with self.assertRaisesRegex(ValueError, "unknown item"):
            self.mark(self.rid, "stable-subjects", "mustafa", "green")
        with self.assertRaisesRegex(ValueError, "unknown item"):
            self.mark(self.rid, "derived[7]", "mustafa", "green")
        with self.assertRaisesRegex(ValueError, "unknown reviewer"):
            self.mark(self.rid, "direct", "human", "green")
        with self.assertRaisesRegex(ValueError, "unknown record"):
            self.mark("nope", "direct", "mustafa", "green")
        with self.assertRaisesRegex(ValueError, "state must be"):
            self.mark(self.rid, "direct", "mustafa", "yellow")
        with self.assertRaisesRegex(ValueError, "kind must be"):
            self.mark(self.rid, "direct", "mustafa", "red", comment="x", kind="fix")

    def test_concurrent_writers_keep_every_mark(self):
        jobs = [(r["id"], who) for r in self.recs[:10] for who in C.REVIEWER_IDS]
        threads = [threading.Thread(target=self.mark, args=(rid, "direct", who, "green")) for rid, who in jobs]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        marks = json.loads(self.path.read_text())["marks"]
        self.assertEqual(sum(len(by) for items in marks.values() for by in items.values()), len(jobs))

    def test_checklist_rows(self):
        self.mark(self.rid, "clear-and-sensible", "mustafa", "red")
        self.mark(self.rid, "clear-and-sensible", "codex", "green")
        self.mark(self.recs[1]["id"], "direct", "fengchun", "red", comment="two fair answers", kind="angle")
        rows, _ = C.manual_checks(self.recs, C.load_reviews(self.path))
        self.assertEqual([r["rule"] for r in rows], ["clear-and-sensible", "serves-the-purpose", "questions"])
        self.assertTrue(all(r["status"] == "manual" for r in rows))
        r1 = rows[0]["reviews"]
        self.assertEqual(r1["by_reviewer"]["Mustafa"], {"green": 0, "red": 1, "yellow": len(self.recs) - 1})
        self.assertEqual(r1["by_reviewer"]["Codex"]["green"], 1)
        self.assertEqual([x["record"] for x in r1["red"]], [self.rid])
        q = rows[2]["reviews"]
        self.assertEqual(q["total"], 2 * len(self.recs))
        self.assertEqual(q["red"][0]["item"], "direct")
        self.assertEqual(q["red"][0]["marks"][0]["kind"], "angle")
        # A record changed after it was marked: the mark says so.
        changed = [dict(r, notes="edited") if r["id"] == self.rid else r for r in self.recs]
        state = C.review_state(changed, C.load_reviews(self.path))
        self.assertTrue(state["marks"][self.rid]["clear-and-sensible"]["mustafa"]["stale"])

    def test_report_keeps_rule_numbers(self):
        rows, _ = C.manual_checks(self.recs, C.load_reviews(self.path))
        self.assertEqual([r["section"] for r in rows], ["Clear and sensible", "Serves the purpose",
                                                         "Edits and questions"])


class Rule3Test(unittest.TestCase):
    def rec(self, **queries):
        r = record("geography-replace-0001")
        r["queries"].update(queries)
        return r

    def test_own_answer(self):
        r = self.rec(paraphrase={"prompt": "Lyon, near Italy, is in which country?", "original_answer": "France",
                                 "new_answer": "Italy"})
        found = C.rule3_patterns([r], entities={})
        self.assertEqual(len(found["own"]), 1)
        self.assertIn("paraphrase", found["own"][0])

    def test_exemptions(self):
        r = self.rec(paraphrase={"prompt": "Is Lyon in France or in Italy?", "original_answer": "France",
                                 "new_answer": "Italy"},
                     derived=[{"prompt": "Italy is in Europe. Which continent is Lyon in?", "original_answer": "Europe",
                               "new_answer": "Europe"},
                              {"prompt": "What is the plural of 'moose'?", "original_answer": "moose",
                               "new_answer": "moose"},
                              {"prompt": "Is Lyon in Italy?", "original_answer": "no", "new_answer": "yes"},
                              {"prompt": "What is 2 to the power 0?", "original_answer": "1", "new_answer": "0"}],
                     cross_lingual=[{"prompt": "HTML 中的空元素需要结束标签吗？", "original_answer": "不需要",
                                     "new_answer": "需要"}])
        self.assertEqual(C.rule3_patterns([r], entities={})["own"], [])

    def test_cjk_answer(self):
        r = self.rec(cross_lingual=[{"prompt": "土星的卫星土卫六绕哪颗行星运行？", "original_answer": "土星",
                                     "new_answer": "木星"}])
        self.assertEqual(len(C.rule3_patterns([r], entities={})["own"]), 1)

    def test_subject_and_phrases(self):
        r = record("history-replace-0001", subject="Shakespeare's Birthplace in Stratford", object="Stratford",
                   old_object="London", premises=["Under those conditions the museum is closed."])
        r["queries"]["derived"] = [{"prompt": "After the edit, where is it?", "original_answer": "x",
                                    "new_answer": "y"}]
        found = C.rule3_patterns([r], entities={})
        self.assertTrue(any("subject" in x and "Stratford" in x for x in found["own"]))
        self.assertEqual(len(found["phrases"]), 2)
        tbox = record("physics-insert-0009", box="tbox", subject="Corvessil nebula", object="nebula")
        self.assertEqual(C.rule3_patterns([tbox], entities={})["own"], [])

    def test_description_subjects(self):
        r = record("history-replace-0003", subject="Napoleon's final place of exile", object="Elba",
                   old_object="Saint Helena")
        ents = {"Napoleon's final place of exile": {"category": "description", "note": "describes Saint Helena",
                                                    "issue": None}}
        self.assertEqual(len(C.rule3_patterns([r], entities=ents)["descriptions"]), 1)
        ents["Napoleon's final place of exile"]["category"] = "entity"
        self.assertEqual(C.rule3_patterns([r], entities=ents)["descriptions"], [])

    def test_judge_cache(self):
        r = record("geography-replace-0001")
        rows = lambda judged: {c["name"]: c for c in C.check_rule3([r], entities={}, judged=judged)}
        judge = "LLM judge: subjects, self-contained statements, answers given away"
        self.assertEqual(rows({})[judge]["status"], "pending")
        items = [{"task": "subject", "key": "subject", "subject": "Lyon", "label": "STABLE", "reason": ""},
                 {"task": "standalone", "key": "direct", "text": "Which country is Lyon in?", "label": "DEPENDS",
                  "reason": "no"}]
        fresh = {"records": {r["id"]: {"hash": C.rule3_judge_hash(r), "items": items}}}
        row = rows(fresh)[judge]
        self.assertEqual(row["status"], "review")
        self.assertEqual(len(row["items"]), 1)
        stale = {"records": {r["id"]: {"hash": "old", "items": items}}}
        self.assertEqual(rows(stale)[judge]["status"], "pending")
        self.assertIn("1 changed since", rows(stale)[judge]["note"])

    def test_judge_items(self):
        r = self.rec(paraphrase={"prompt": "Is Lyon in Italy?", "original_answer": "no", "new_answer": "yes"})
        items = C.rule3_judge_items(r)
        tasks = [(i["task"], i["key"]) for i in items]
        self.assertIn(("subject", "subject"), tasks)
        self.assertIn(("giveaway", "direct"), tasks)
        self.assertNotIn(("giveaway", "paraphrase"), tasks)   # yes/no: nothing to give away
        self.assertIn(("standalone", "paraphrase"), tasks)


class EndpointTest(Temp):
    def setUp(self):
        super().setUp()
        self.recs = dataset(per_cell=1)
        module = load_criteria()
        module.REVIEWS_PATH, module.REVIEWS_LOCK = self.path, self.lock
        module.load_records = lambda: self.recs
        p = patch.object(main, "_sids_criteria", return_value=module)
        p.start()
        self.addCleanup(p.stop)
        self.user = TestClient(main.app, headers={"x-dashboard-token": main.AUTH_TOKEN})
        self.agent = TestClient(main.app, headers={"x-dashboard-token": main.AGENT_TOKEN})
        self.rid = self.recs[0]["id"]

    def mark(self, client, reviewer, **kw):
        return client.post("/api/sids-dataset/reviews/mark", json={
            "record": self.rid, "item": "serves-the-purpose", "reviewer": reviewer, "state": "red",
            "comment": "Q3 needs no edit", **kw})

    def test_get(self):
        data = self.user.get("/api/sids-dataset/reviews").json()
        self.assertEqual([r["key"] for r in data["rules"]], ["clear-and-sensible", "serves-the-purpose"])
        self.assertTrue(data["rules"][1]["guide"])
        self.assertEqual([r["id"] for r in data["reviewers"]], ["codex", "claude", "mustafa", "fengchun", "adarsh"])
        self.assertEqual(data["can_mark_as"], ["mustafa", "fengchun", "adarsh"])
        self.assertEqual(self.agent.get("/api/sids-dataset/reviews").json()["can_mark_as"], ["codex", "claude"])
        self.assertEqual(data["marks"], {})

    def test_mark_and_clear(self):
        r = self.mark(self.user, "adarsh", kind="angle")
        self.assertEqual(r.status_code, 200)
        m = r.json()["marks"]["serves-the-purpose"]["adarsh"]
        self.assertEqual((m["state"], m["kind"], m["stale"]), ("red", "angle", False))
        r = self.mark(self.user, "adarsh", state="green", comment="")
        self.assertEqual(r.json()["marks"]["serves-the-purpose"]["adarsh"]["state"], "green")
        r = self.mark(self.user, "adarsh", item="direct", state="green")
        self.assertEqual(set(r.json()["marks"]), {"serves-the-purpose", "direct"})
        self.mark(self.user, "adarsh", state=None)
        r = self.mark(self.user, "adarsh", item="direct", state=None)
        self.assertEqual(r.json()["marks"], {})
        self.assertEqual(json.loads(self.path.read_text())["marks"], {})

    def test_bad_mark(self):
        r = self.mark(self.user, "adarsh", state="yellow")
        self.assertEqual(r.status_code, 400)
        self.assertFalse(self.path.exists())
        r = self.mark(self.user, "adarsh", comment="", kind=None)   # red needs no comment
        self.assertEqual(r.json()["marks"]["serves-the-purpose"]["adarsh"]["state"], "red")

    def test_tokens_cannot_impersonate(self):
        self.assertEqual(self.mark(self.agent, "mustafa").status_code, 403)
        self.assertEqual(self.mark(self.user, "claude").status_code, 403)
        self.assertEqual(self.mark(self.agent, "codex").status_code, 200)
        self.assertEqual(self.mark(self.user, "fengchun", state="green").status_code, 200)


if __name__ == "__main__":
    unittest.main()
