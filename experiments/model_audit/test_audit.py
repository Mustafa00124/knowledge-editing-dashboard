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


if __name__ == "__main__":
    unittest.main()
