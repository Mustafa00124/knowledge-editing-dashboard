import unittest

import audit

RELATIONS = {"located_in": (frozenset({"transitive", "asymmetric", "inverse:contains"}), False)}
RECORD = {
    "id": "geography-replace-0099", "topic": "geography", "box": "abox", "edit_operation": "replace",
    "relation": "located_in",
    "edit": {"statement": "The Eiffel Tower is in Italy.", "premises": ["The Eiffel Tower is in Paris."]},
    "queries": {"derived": [
        {"prompt": "On which continent is the Eiffel Tower?", "derivation": "transitivity",
         "bridge": ["Italy is in Europe."]},
        {"prompt": "Rome is the capital of Italy. Capital of the tower's country?", "derivation": "composition",
         "bridge": ["Rome is the capital of Italy."], "bridge_in_prompt": True},
    ]},
    "checks": [
        {"fact": "The Eiffel Tower is in Paris.", "prompt": "In which city is the Eiffel Tower?", "answer": "Paris"},
        {"fact": "Italy is in Europe.", "prompt": "On which continent is Italy?", "answer": "Europe"},
    ],
}
RELATION_CHECKS = {"located_in": {"transitive": {"prompt": "Is located-in transitive?", "answer": "yes"}}}


class CheckTests(unittest.TestCase):
    def rows(self):
        return audit.check_rows([RECORD], RELATION_CHECKS, RELATIONS)

    def test_rows_cover_fact_and_relation_checks_once(self):
        rows = self.rows()
        self.assertEqual([r["query_type"] for r in rows], ["check_fact", "check_fact", "check_relation"])
        self.assertEqual(rows[1]["original_answer"], "Europe")
        self.assertEqual((rows[2]["relation"], rows[2]["tag"]), ("located_in", "transitive"))
        self.assertTrue(all(audit.is_check(r) for r in rows))

    def test_chain_supported_only_when_every_check_passes(self):
        rows = self.rows()
        for r in rows:
            r["score"] = 1
        got = audit.summarise_checks(rows, [RECORD], RELATIONS)
        # The transitivity query needs its bridge and the property; the composition
        # query states its bridge in the prompt, so it has nothing to check.
        self.assertEqual(got["derived_supported"], {"supported": 2, "unsupported": 0, "unclear": 0})
        self.assertEqual(got["premises_known"], {"known": 1, "unknown": 0, "unclear": 0})
        rows[2]["score"] = 0  # the model does not hold transitivity
        got = audit.summarise_checks(rows, [RECORD], RELATIONS)
        self.assertEqual(got["derived_supported"], {"supported": 1, "unsupported": 1, "unclear": 0})
        self.assertEqual(got["relations"], {"pass": 0, "scored": 1, "unclear": 0})

    def test_unclear_check_makes_chain_unclear(self):
        rows = self.rows()
        for r in rows:
            r["score"] = 1
        rows[1]["score"] = None
        got = audit.summarise_checks(rows, [RECORD], RELATIONS)
        self.assertEqual(got["derived_supported"]["unclear"], 1)


class FictionalInsertTests(unittest.TestCase):
    def test_fictional_insert_counted_apart(self):
        real = {"id": "geography-insert-0001", "topic": "geography", "box": "abox", "edit_operation": "insert",
                "reality": "real", "edit": {}, "queries": {}}
        made_up = dict(real, id="geography-insert-0002", reality="fictional")
        self.assertFalse(audit.is_fictional(real))
        self.assertTrue(audit.is_fictional(made_up))
        rows = [{"record_id": "geography-insert-0001", "query_type": q, "judged": True, "score": 1, "label": "NONE",
                 "fixture": False, "topic": "geography", "box": "abox", "edit_operation": "insert", "language": "en"}
                for q in ("direct", "paraphrase")]
        got = audit.summarise(rows, [real, made_up])
        self.assertEqual((got["facts_total"], got["fictional"]), (1, 1))


def _q(prompt, original, new, **extra):
    return {"prompt": prompt, "original_answer": original, "new_answer": new, **extra}


REPLACE = {
    "id": "geography-replace-0001", "topic": "geography", "box": "abox", "edit_operation": "replace",
    "relation": "has_capital", "edit": {"statement": "The capital of Australia is Sydney."},
    "worlds": [{"id": "w1"}, {"id": "w2"}],
    "queries": {
        "direct": _q("What is the capital of Australia?", "Canberra", "Sydney"),
        "paraphrase": _q("Which city is Australia's capital?", "Canberra", "Sydney"),
        "cross_lingual": [dict(_q("澳大利亚的首都是哪个城市？", "堪培拉", "悉尼"), language="zh"),
                          dict(_q("¿Cuál es la capital de Australia?", "Canberra", "Sídney"), language="es")],
        "unrelated_near": [{"prompt": "What is the capital of New Zealand?", "reference": "Wellington"}],
        "unrelated_far": [{"prompt": "Into which sea does the Danube flow?", "reference": "the Black Sea"}],
        "derived": [
            _q("Is Canberra the capital of Australia?", "yes", "no", determinacy="determinate"),
            _q("Where does Parliament sit?", "Canberra", None, determinacy="background_beliefs",
               world_answers={"w1": {"answer": "Canberra"}, "w2": {"answer": "Sydney"}}),
            _q("Which new city will host it?", None, "Sydney", determinacy="determinate"),
            _q("In which state is the capital?", "the ACT", "New South Wales", determinacy="determinate"),
        ],
    },
}


class QueryRowTests(unittest.TestCase):
    def test_replace_asks_every_query_with_a_pre_edit_answer(self):
        rows = audit.query_rows([REPLACE])
        self.assertEqual([r["query_key"] for r in rows], [
            "direct", "paraphrase", "cross_lingual[zh]", "cross_lingual[es]", "unrelated_near[0]",
            "unrelated_far[0]", "derived[0]", "derived[1]", "derived[3]"])  # derived[2] has no original
        by = {r["query_key"]: r for r in rows}
        # Indeterminate derived: one world before the edit, so its original answer.
        self.assertEqual((by["derived[1]"]["original_answer"], by["derived[1]"]["determinacy"]),
                         ("Canberra", "background_beliefs"))
        # Locality expects its reference; the judge sees only that one candidate.
        near = by["unrelated_near[0]"]
        self.assertEqual((near["original_answer"], near["new_answer"], near["rule"]), ("Wellington", None, "original"))
        self.assertEqual(audit.J.answer_candidates(near)[0], {"A": "Wellington"})
        self.assertEqual(audit.J.answer_candidates(by["derived[1]"])[0], {"A": "Canberra"})
        self.assertTrue(all(r["rule"] == "original" and r["new_answer"] is None for r in rows))

    def test_hash_tracks_prompt_and_expected_answer(self):
        h = audit.query_rows([REPLACE])[0]["query_hash"]
        self.assertEqual(h, audit.AQ.query_hash("What is the capital of Australia?", "Canberra"))
        self.assertNotEqual(h, audit.AQ.query_hash("What is the capital of Australia?", "Sydney"))
        self.assertNotEqual(h, audit.AQ.query_hash("What's the capital of Australia?", "Canberra"))

    def test_insert_rules(self):
        real = {"id": "geography-insert-0001", "topic": "geography", "box": "abox", "edit_operation": "insert",
                "reality": "real", "edit": {}, "queries": {
                    "direct": _q("Which archipelago?", None, "the Thousand Islands"),
                    "unrelated_far": [{"prompt": "Who painted the Sistine ceiling?", "reference": "Michelangelo"}],
                    "derived": [_q("Which river?", None, "the Saint Lawrence"),
                                _q("Is the Saint Lawrence a river?", "yes", "yes")]}}
        by = {r["query_key"]: r for r in audit.query_rows([real])}
        self.assertEqual(sorted(by), ["derived[1]", "direct", "unrelated_far[0]"])
        self.assertEqual((by["direct"]["rule"], by["direct"]["new_answer"], by["direct"]["original_answer"]),
                         ("not_new", "the Thousand Islands", None))
        self.assertEqual((by["derived[1]"]["rule"], by["derived[1]"]["original_answer"]), ("original", "yes"))
        # A fictional insert's own questions are not asked; its locality and
        # derived queries with an original answer are.
        made_up = dict(real, reality="fictional")
        self.assertEqual(sorted(r["query_key"] for r in audit.query_rows([made_up])), ["derived[1]", "unrelated_far[0]"])

    def test_scores_follow_each_rows_rule(self):
        rows = {r["query_key"]: r for r in audit.query_rows([REPLACE])}
        self.assertEqual(audit.row_score(rows["unrelated_near[0]"], "ORIGINAL"), 1)
        self.assertEqual(audit.row_score(rows["unrelated_near[0]"], "OTHER"), 0)
        self.assertIsNone(audit.row_score(rows["derived[1]"], "UNCLEAR"))
        insert_row = {"query_type": "direct", "rule": "not_new"}
        self.assertEqual(audit.row_score(insert_row, "NONE"), 1)
        self.assertEqual(audit.row_score(insert_row, "NEW"), 0)
        check = {"query_type": "check_fact"}
        self.assertEqual(audit.row_score(check, "ORIGINAL"), 1)

    def test_locality_kept_out_of_known_and_query_tally(self):
        rows = audit.query_rows([REPLACE])
        for r in rows:
            r["score"], r["label"] = (0, "OTHER") if r["query_type"].startswith("unrelated") else (1, "ORIGINAL")
        got = audit.summarise(rows, [REPLACE])
        self.assertEqual(got["facts_known"], 1)
        self.assertEqual(got["queries"], {"pass": 7, "scored": 7, "unclear": 0})
        self.assertEqual(got["locality"], {"pass": 0, "scored": 2, "unclear": 0})
        self.assertEqual(got["by"]["query_type"]["unrelated_far"]["scored"], 1)


if __name__ == "__main__":
    unittest.main()
