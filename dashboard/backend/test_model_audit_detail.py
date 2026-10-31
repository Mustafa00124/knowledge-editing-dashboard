"""Sid's Dataset audit-dot detail: per query, the knowledge parts its answer
rests on with one model's check status, and the verdict (diagnose). Also:
only default-prompt audit runs feed the Datasets page."""
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import model_audit_reader as M

RELATIONS = {"located_in": (frozenset({"transitive"}), False)}
RELATION_CHECKS = {"located_in": {"transitive": {"prompt": "Is located-in transitive?", "answer": "yes"}}}

RECORD = {
    "id": "geography-replace-0009", "topic": "geography", "box": "abox", "edit_operation": "replace",
    "relation": "located_in",
    "edit": {"original": "Lyon is in France.", "statement": "Lyon is in Italy.",
             "premises": ["Lyon is in Rhone.", "Rhone is in France."]},
    "checks": [
        {"fact": "Lyon is in Rhone.", "prompt": "Where is Lyon?", "answer": "Rhone"},
        {"fact": "Rhone is in France.", "prompt": "Where is Rhone?", "answer": "France"},
        {"fact": "France is in Europe.", "prompt": "Where is France?", "answer": "Europe"},
        {"fact": "Paris is not in Italy.", "prompt": "Is Paris in Italy?", "answer": "no"},
    ],
    "queries": {
        "direct": {"prompt": "Which country is Lyon in?", "original_answer": "France", "new_answer": "Italy"},
        "paraphrase": {"prompt": "Lyon lies in which country?", "original_answer": "France", "new_answer": "Italy"},
        "unrelated_far": [{"prompt": "Symbol for sodium?", "reference": "Na"}],
        "derived": [
            # Transitivity: the fact, an unstated bridge, a revision fact and the property.
            {"prompt": "Which continent is Lyon in?", "original_answer": "Europe", "new_answer": "Europe",
             "derivation": "transitivity", "bridge": ["France is in Europe."], "revision_facts": ["Paris is not in Italy."]},
            # Bridge stated in the prompt: listed as given, not counted.
            {"prompt": "France is in Europe. Which continent is Lyon in?", "original_answer": "Europe",
             "new_answer": "Europe", "derivation": "composition", "bridge": ["France is in Europe."],
             "bridge_in_prompt": True},
        ],
    },
}


def q(aq, key, prompt, answer, score, response="x"):
    return {"record_id": RECORD["id"], "query_type": key.split("[")[0], "language": "en", "prompt": prompt,
            "query_key": key, "query_hash": aq.query_hash(prompt, answer), "original_answer": answer,
            "response": response, "label": "ORIGINAL" if score == 1 else "OTHER", "reason": "r", "score": score}


def fact(fact_text, prompt, answer, score):
    return {"record_id": RECORD["id"], "query_type": "check_fact", "fact": fact_text, "prompt": prompt,
            "original_answer": answer, "response": "y", "label": "L", "reason": "r", "score": score}


def relation_row(score, prompt="Is located-in transitive?"):
    return {("located_in", "transitive"): {"query_type": "check_relation", "relation": "located_in",
                                           "tag": "transitive", "prompt": prompt, "original_answer": "yes",
                                           "response": "yes", "label": "L", "reason": "r", "score": score}}


class DiagnoseTests(unittest.TestCase):
    def test_rules(self):
        g = {"text": "a", "status": "green"}
        r = {"text": "b", "status": "red"}
        y = {"text": "c", "status": "yellow"}
        given = {"text": "d", "status": "given"}
        self.assertEqual(M.diagnose("red", [g, r, y])["kind"], "missing")
        self.assertEqual(M.diagnose("red", [g, r, y])["parts"], ["b"])
        self.assertEqual(M.diagnose("red", [g, y])["kind"], "not_audited")
        self.assertEqual(M.diagnose("red", [g, given])["kind"], "not_combined")
        self.assertEqual(M.diagnose("red", [given])["kind"], "no_parts")
        self.assertIn("does not know this fact", M.diagnose("red", [])["text"])
        self.assertEqual(M.diagnose("green", [g])["kind"], "ok")
        self.assertEqual(M.diagnose("green", [r])["kind"], "green_despite")
        self.assertEqual(M.diagnose("yellow", [r])["kind"], "answer_not_audited")
        self.assertEqual(M.diagnose("na", [])["kind"], "na")


class RecordDetailTests(unittest.TestCase):
    def setUp(self):
        self.aq = M._audit_queries()
        self.sid = M._sid()[0]

    def detail(self, rows, relation_rows):
        return M.record_detail(self.aq, self.sid, RELATIONS, RELATION_CHECKS, RECORD, rows, relation_rows)

    def test_fact_red_with_green_premises_is_not_combined(self):
        aq = self.aq
        rows = [q(aq, "direct", "Which country is Lyon in?", "France", 0),
                q(aq, "paraphrase", "Lyon lies in which country?", "France", 1),
                fact("Lyon is in Rhone.", "Where is Lyon?", "Rhone", 1),
                fact("Rhone is in France.", "Where is Rhone?", "France", 1)]
        d = self.detail(rows, {})
        self.assertEqual(d["fact"]["status"], "red")
        self.assertEqual([p["status"] for p in d["fact"]["parts"]], ["green", "green"])
        self.assertEqual(d["fact"]["verdict"]["kind"], "not_combined")
        self.assertEqual(d["queries"]["direct"]["verdict"]["kind"], "not_combined")
        self.assertEqual(d["queries"]["paraphrase"]["verdict"]["kind"], "ok")
        self.assertEqual(d["queries"]["unrelated_far[0]"]["status"], "yellow")  # not in the run

    def test_derived_parts_and_missing_knowledge(self):
        aq = self.aq
        rows = [q(aq, "direct", "Which country is Lyon in?", "France", 1),
                q(aq, "paraphrase", "Lyon lies in which country?", "France", 1),
                q(aq, "derived[0]", "Which continent is Lyon in?", "Europe", 0, response="Asia"),
                fact("France is in Europe.", "Where is France?", "Europe", 0),
                fact("Paris is not in Italy.", "Is Paris in Italy?", "no", 1)]
        d0 = self.detail(rows, relation_row(1))["queries"]["derived[0]"]
        self.assertEqual((d0["status"], d0["response"]), ("red", "Asia"))
        self.assertEqual([(p["kind"], p["status"]) for p in d0["parts"]],
                         [("fact", "green"), ("bridge", "red"), ("revision", "green"), ("relation", "green")])
        self.assertEqual(d0["verdict"], {"kind": "missing", "text": "Missing knowledge",
                                         "parts": ["France is in Europe."]})

    def test_all_green_parts_and_stale_relation_check(self):
        aq = self.aq
        rows = [q(aq, "direct", "Which country is Lyon in?", "France", 1),
                q(aq, "paraphrase", "Lyon lies in which country?", "France", 1),
                q(aq, "derived[0]", "Which continent is Lyon in?", "Europe", 0),
                fact("France is in Europe.", "Where is France?", "Europe", 1),
                fact("Paris is not in Italy.", "Is Paris in Italy?", "no", 1)]
        self.assertEqual(self.detail(rows, relation_row(1))["queries"]["derived[0]"]["verdict"]["kind"], "not_combined")
        # The relation check was asked with an older wording: stale, so not audited.
        d0 = self.detail(rows, relation_row(1, prompt="Old wording?"))["queries"]["derived[0]"]
        self.assertTrue(d0["parts"][-1]["stale"])
        self.assertEqual((d0["verdict"]["kind"], d0["verdict"]["parts"]), ("not_audited", ["located_in: transitive"]))

    def test_given_bridge_not_counted_and_stale_query_is_yellow(self):
        aq = self.aq
        rows = [q(aq, "direct", "Which country is Lyon in?", "France", 1),
                q(aq, "paraphrase", "Lyon lies in which country?", "France", 1),
                q(aq, "derived[1]", "France is in Europe. Which continent is Lyon in?", "Europe", 0),
                q(aq, "unrelated_far[0]", "Symbol for sodium, old?", "Na", 1)]
        d = self.detail(rows, {})
        d1 = d["queries"]["derived[1]"]
        self.assertEqual([(p["kind"], p["status"]) for p in d1["parts"]], [("fact", "green"), ("bridge", "given")])
        self.assertEqual(d1["verdict"]["kind"], "not_combined")
        far = d["queries"]["unrelated_far[0]"]
        self.assertEqual((far["status"], far["stale"], far["verdict"]["kind"]), ("yellow", True, "answer_not_audited"))

    def test_fact_without_premises_is_no_parts(self):
        aq = self.aq
        rec = dict(RECORD, edit={"original": "Lyon is in France.", "statement": "Lyon is in Italy."})
        rows = [q(aq, "direct", "Which country is Lyon in?", "France", 0),
                q(aq, "paraphrase", "Lyon lies in which country?", "France", 0)]
        d = M.record_detail(aq, self.sid, RELATIONS, RELATION_CHECKS, rec, rows, {})
        self.assertEqual(d["fact"]["verdict"]["text"], "No parts listed: the model does not know this fact")


class DefaultPromptRunTests(unittest.TestCase):
    def test_variant_runs_do_not_replace_the_default_audit(self):
        aq = M._audit_queries()
        root = Path(tempfile.mkdtemp())
        recs = root / "records" / "geography" / "replace"
        recs.mkdir(parents=True)
        (recs / f"{RECORD['id']}.json").write_text(json.dumps(RECORD))
        model = "llama-3.1-8b-instruct"
        runs = [(model, {"model": model}, 1),  # older runs lack the fields: default
                (f"{model}_instr-strict", {"model": model, "instruction": "Answer in one word."}, 0),
                (f"{model}_shots2", {"model": model, "instruction": "few_words", "chat_shots": 2}, 0)]
        now = time.time()
        for i, (name, summary, score) in enumerate(runs):
            run = root / "out" / "runs" / name
            run.mkdir(parents=True)
            (run / "summary.json").write_text(json.dumps(summary))
            (run / "responses.jsonl").write_text(
                json.dumps(q(aq, "direct", "Which country is Lyon in?", "France", score)) + "\n")
            os.utime(run / "summary.json", (now + i, now + i))  # variants are newer
        with patch.object(M, "SIDS_RECORDS", root / "records"), \
                patch.object(M.results_reader, "out_root", return_value=str(root / "out")), \
                patch.dict(M._cache, {}, clear=True):
            status = M.audit_status()
            detail = M.audit_detail(RECORD["id"], model)
            listed = {r["run"] for r in M.runs()}
            checks = M.check_results()
        self.assertEqual(status["runs"][model], model)
        self.assertEqual(status["records"][RECORD["id"]]["queries"]["direct"][model], "green")
        self.assertEqual((detail["run"], detail["queries"]["direct"]["status"]), (model, "green"))
        self.assertEqual([c["run"] for c in checks], [model])
        self.assertEqual(listed, {name for name, _, _ in runs})  # the Model audit page lists every run
        self.assertTrue(M.is_default_prompt({"instruction": "Answer the question in a few words, without explanation.",
                                             "chat_shots": 0}))
        self.assertTrue(M.is_default_prompt({"instruction": None}))  # base models record none


if __name__ == "__main__":
    unittest.main()
