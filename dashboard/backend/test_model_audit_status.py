"""Sid's Dataset audit status: green, red or yellow per model, fact and query,
from each model's newest model-audit run against the current records."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import model_audit_reader as M

RECORD = {
    "id": "geography-replace-0001", "topic": "geography", "box": "abox", "edit_operation": "replace",
    "edit": {}, "queries": {
        "direct": {"prompt": "Capital of Australia?", "original_answer": "Canberra", "new_answer": "Sydney"},
        "paraphrase": {"prompt": "Australia's capital city?", "original_answer": "Canberra", "new_answer": "Sydney"},
        "unrelated_near": [{"prompt": "Capital of New Zealand?", "reference": "Wellington"}],
        "derived": [
            {"prompt": "Where does Parliament sit?", "original_answer": "Canberra", "new_answer": None,
             "determinacy": "background_beliefs", "world_answers": {"w1": {"answer": "Canberra"}}},
            {"prompt": "Which new city?", "original_answer": None, "new_answer": "Sydney"},
        ],
    },
}


def row(aq, key, prompt, answer, score, query_type=None, keyed=True):
    r = {"query_type": query_type or key.split("[")[0], "language": "en", "score": score,
         "hash": aq.query_hash(prompt, answer), "key": key if keyed else None}
    return r


class RecordStatusTests(unittest.TestCase):
    def setUp(self):
        self.aq = M._audit_queries()

    def test_rules(self):
        aq = self.aq
        rows = [row(aq, "direct", "Capital of Australia?", "Canberra", 1),
                row(aq, "paraphrase", "Australia's capital city?", "Canberra", 0),
                row(aq, "derived[0]", "Where does Parliament sit?", "Canberra", None)]
        got = M.record_status(aq, RECORD, rows)
        self.assertEqual(got["queries"], {"direct": "green", "paraphrase": "red", "unrelated_near[0]": "yellow",
                                          "derived[0]": "yellow", "derived[1]": "na"})
        self.assertEqual(got["fact"], "red")

    def test_stale_hash_is_yellow(self):
        aq = self.aq
        rows = [row(aq, "direct", "Capital of Australia, old wording?", "Canberra", 1),
                row(aq, "paraphrase", "Australia's capital city?", "Canberra", 1)]
        got = M.record_status(aq, RECORD, rows)
        self.assertEqual((got["queries"]["direct"], got["fact"]), ("yellow", "yellow"))

    def test_rows_without_keys_match_by_hash(self):
        aq = self.aq
        rows = [row(aq, "direct", "Capital of Australia?", "Canberra", 1, keyed=False),
                row(aq, "paraphrase", "Australia's capital city?", "Canberra", 1, keyed=False),
                row(aq, "derived", "Where does Parliament sit?", "Canberra", 0, keyed=False)]
        got = M.record_status(aq, RECORD, rows)
        self.assertEqual(got["fact"], "green")
        self.assertEqual(got["queries"]["derived[0]"], "red")

    def test_not_audited_record_is_yellow_and_fictional_fact_na(self):
        got = M.record_status(self.aq, RECORD, None)
        self.assertEqual(got["fact"], "yellow")
        made_up = dict(RECORD, edit_operation="insert", reality="fictional")
        got = M.record_status(self.aq, made_up, None)
        self.assertEqual(got["fact"], "na")
        self.assertEqual(got["queries"]["unrelated_near[0]"], "yellow")  # locality is still asked

    def test_audit_status_end_to_end(self):
        aq = self.aq
        root = Path(tempfile.mkdtemp())
        recs = root / "records" / "geography" / "replace"
        recs.mkdir(parents=True)
        (recs / "geography-replace-0001.json").write_text(json.dumps(RECORD))
        for model in ("qwen3-4b-base", "mistral-7b-instruct-v0.1"):
            run = root / "out" / "runs" / model
            run.mkdir(parents=True)
            (run / "summary.json").write_text(json.dumps({"model": model}))
            (run / "responses.jsonl").write_text(json.dumps({
                "record_id": RECORD["id"], "query_type": "direct", "language": "en", "query_key": "direct",
                "query_hash": aq.query_hash("Capital of Australia?", "Canberra"), "score": 1}) + "\n")
        with patch.object(M, "SIDS_RECORDS", root / "records"), \
                patch.object(M.results_reader, "out_root", return_value=str(root / "out")), \
                patch.dict(M._cache, {}, clear=True):
            got = M.audit_status()
            main = M.restrict(got, set(M.MAIN_MODELS))
        self.assertEqual(got["models"], ["mistral-7b-instruct-v0.1", "qwen3-4b-base"])  # main instruct first
        q = got["records"][RECORD["id"]]["queries"]
        self.assertEqual(q["direct"], {"mistral-7b-instruct-v0.1": "green", "qwen3-4b-base": "green"})
        self.assertNotIn("derived[1]", q)  # never asked: left out
        self.assertEqual(got["records"][RECORD["id"]]["fact"]["qwen3-4b-base"], "yellow")  # paraphrase not asked yet
        self.assertEqual(main["models"], ["mistral-7b-instruct-v0.1"])
        self.assertIn("mistral-7b-instruct-v0.1", got["audited_at"])


if __name__ == "__main__":
    unittest.main()
