import unittest
from unittest.mock import Mock, patch

from evaluation_config import judge_configured, parse_modes, validate_modes
from semantic_evaluation import SemanticEvaluator, aggregate, cached_answer, collect_probes, normalize_answer


class EvaluationTests(unittest.TestCase):
    def test_placeholder_and_empty_selection_rejected(self):
        self.assertFalse(judge_configured({"api_key": "YOUR_API_KEY_HERE"}))
        self.assertFalse(judge_configured({"api_key": "placeholder-value-long"}))
        with patch("evaluation_config.judge_configured", return_value=False):
            with self.assertRaises(ValueError):
                validate_modes("original,llm_judge")
        for invalid in ("", [], "unknown"):
            with self.assertRaises(ValueError):
                parse_modes(invalid)
        self.assertEqual(parse_modes("bertscore,original,exact_match,bertscore"),
                         ["original", "exact_match", "bertscore"])

    def test_cache_shares_generations(self):
        generate = Mock(return_value="Paris")
        cache = {}
        self.assertEqual(cached_answer(cache, "question", generate), "Paris")
        cached_answer(cache, "question", generate)
        generate.assert_called_once()

    def test_baseline_preserved_and_aliases_flattened(self):
        requests = [{"prompt": "Capital?", "target_new": "Rome", "locality": {
            "near": {"prompt": ["Other capital?"], "ground_truth": [["Paris", ["City of Paris"]]]}},
            "portability": {"hop": {"prompt": ["Country?"], "ground_truth": ["Italy"]}}}]
        baseline = {}
        before = collect_probes(requests, lambda r, q: "Paris", baseline)
        after = collect_probes(requests, lambda r, q: "The answer is Paris", baseline)
        self.assertEqual(len(before), 3)
        self.assertEqual(after[-1]["before_answer"], "Paris")
        self.assertEqual(after[-1]["reference_answers"], ["Paris", "City of Paris"])

    def test_macro_average_and_unavailable_are_not_zero(self):
        probes = [{"metric": "locality", "case_id": c, "category": cat} for c, cat in
                  [(0, "a"), (0, "a"), (0, "b"), (1, "a"), (2, "a")]]
        result = aggregate(probes, [0, 0, 1, 1, None], 100)
        self.assertEqual(result["locality"], 75)
        self.assertIsNone(result["portability"])
        self.assertEqual(result["coverage"]["locality"], {"scored": 4, "total": 5})

    def test_judge_errors_and_uncertainty_do_not_become_failures(self):
        evaluator = SemanticEvaluator(["llm_judge"])
        evaluator.judge_probe = Mock(side_effect=[
            {"verdict": "pass", "reason": "Paraphrase"},
            {"verdict": "uncertain", "reason": "Ambiguous"}, RuntimeError("secret-key")])
        probes = [{"metric": "edit_succ", "case_id": i, "category": "rewrite",
                   "reference_answers": ["Paris"]} for i in range(3)]
        result = evaluator.score(probes)["llm_judge"]
        self.assertEqual(result["edit_succ"], 100)
        self.assertEqual(result["coverage"]["edit_succ"], {"scored": 1, "total": 3})
        self.assertEqual(result["errors"], 1)
        self.assertNotIn("secret-key", str(probes))
        self.assertNotIn("api_key", evaluator.metadata())

    def test_exact_match_normalizes_but_does_not_accept_wrong_facts(self):
        self.assertEqual(normalize_answer(" The CITY, of Paris! "), "city of paris")
        evaluator = SemanticEvaluator(["exact_match"])
        probes = [
            {"metric": "portability", "case_id": 0, "category": "a", "answer": "The Paris!",
             "reference_answers": ["Rome", "Paris"]},
            {"metric": "portability", "case_id": 1, "category": "a", "answer": "Paris, not Rome",
             "reference_answers": ["Paris"]},
            {"metric": "locality", "case_id": 2, "category": "b", "answer": "The answer is Paris",
             "before_answer": "Paris"},
        ]
        scores = evaluator.score(probes)["exact_match"]
        self.assertEqual(scores["portability"], 50)
        self.assertEqual(scores["locality"], 0)

    def test_bertscore_uses_best_alias_and_raw_f1(self):
        import torch
        evaluator = SemanticEvaluator(["bertscore"])
        evaluator.bertscorer = Mock()
        evaluator.bertscorer.score.return_value = (None, None, torch.tensor([0.82]))
        probes = [{"metric": "portability", "case_id": 0, "category": "a", "answer": "Paris",
                   "reference_answers": ["Rome", "Paris city"]}]
        result = evaluator.score(probes)["bertscore"]
        self.assertAlmostEqual(result["portability"], 0.82, places=5)
        evaluator.bertscorer.score.assert_called_once_with(["Paris"], [["Rome", "Paris city"]])


if __name__ == "__main__":
    unittest.main()
