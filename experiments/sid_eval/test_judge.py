import unittest

import judge


Q = {"prompt": "Which country is the Eiffel Tower in?", "original_answer": "France", "new_answer": "Italy"}


class CandidateTests(unittest.TestCase):
    def test_letters_map_back_to_sides(self):
        candidates, sides = judge.answer_candidates(Q)
        self.assertEqual({sides[l]: v for l, v in candidates.items()}, {"ORIGINAL": "France", "NEW": "Italy"})

    def test_order_varies_across_queries(self):
        firsts = {judge.answer_candidates(dict(Q, prompt=f"q{i}"))[1]["A"] for i in range(20)}
        self.assertEqual(firsts, {"ORIGINAL", "NEW"})

    def test_identical_answers_collapse(self):
        candidates, sides = judge.answer_candidates(dict(Q, new_answer=" france "))
        self.assertEqual((candidates, sides), ({"A": "France"}, {"A": "NEW"}))

    def test_missing_sides_are_dropped(self):
        self.assertEqual(judge.answer_candidates(dict(Q, original_answer=None))[1], {"A": "NEW"})
        self.assertEqual(judge.answer_candidates(dict(Q, new_answer=None))[1], {"A": "ORIGINAL"})
        messages, sides = judge.answer_messages(dict(Q, original_answer=None, new_answer=None), "No idea.")
        self.assertEqual(sides, {})
        self.assertIn("Candidates: none given", messages[-1]["content"])


class ParseTests(unittest.TestCase):
    def test_letter_maps_to_side(self):
        _, sides = judge.answer_candidates(Q)
        letter = next(l for l, s in sides.items() if s == "NEW")
        reply = f'Sure. {{"reason": "says Italy", "label": "{letter.lower()}"}}'
        self.assertEqual(judge.answer_label(reply, sides)["label"], "NEW")

    def test_fixed_labels_pass_through(self):
        _, sides = judge.answer_candidates(Q)
        self.assertEqual(judge.answer_label('{"reason": "x", "label": "NONE"}', sides)["label"], "NONE")

    def test_bad_replies_are_unclear(self):
        _, sides = judge.answer_candidates(dict(Q, new_answer=None))
        for reply in ("", "A", '{"label": "B"}', '{"label": MAYBE}'):
            self.assertEqual(judge.answer_label(reply, sides)["label"], "UNCLEAR", reply)


class ScoreTests(unittest.TestCase):
    def test_rules(self):
        self.assertEqual(judge.score("audit", "replace", "ORIGINAL"), 1)
        self.assertEqual(judge.score("audit", "replace", "NEW"), 0)
        self.assertEqual(judge.score("audit", "insert", "NEW"), 0)
        self.assertEqual(judge.score("audit", "insert", "NONE"), 1)
        self.assertEqual(judge.score("edit", "replace", "NEW"), 1)
        self.assertEqual(judge.score("edit", "replace", "ORIGINAL"), 0)
        self.assertEqual(judge.score("edit", "delete", "NONE"), 1)
        self.assertEqual(judge.score("edit", "delete", "OTHER"), 0)
        self.assertIsNone(judge.score("edit", "replace", "UNCLEAR"))
        self.assertEqual(judge.locality_score("SAME"), 1)
        self.assertIsNone(judge.locality_score("UNCLEAR"))


if __name__ == "__main__":
    unittest.main()
