"""knowledge.py: finding the answer in what a model writes, lead-ins, the
judge's verdicts, fact-set lead-ins in the tracers, and batched passes that
agree with unbatched ones (a tiny random Llama with the real tokenizer)."""
import argparse
import os
import sys
import unittest
from unittest.mock import patch

import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import formats as F  # noqa: E402
import knowledge as KN  # noqa: E402
from test_causal_trace import TOKENIZER as LLAMA, tiny_model  # noqa: E402


class AnswerTests(unittest.TestCase):
    def test_find_answer(self):
        self.assertEqual(KN.find_answer(" The capital is Paris.", ["Paris"]), 16)
        self.assertEqual(KN.find_answer(" paris, of course", ["Paris"]), 1)  # case
        self.assertIsNone(KN.find_answer(" a Parisian cafe", ["Paris"]))  # not inside a word
        self.assertEqual(KN.find_answer(" the USA, or the United States", ["United States", "USA"]), 5)  # earliest
        self.assertIsNone(KN.find_answer(" London", ["Paris"]))
        self.assertEqual(KN.find_answer(" B) Rome", ["B"]), 1)  # an MCQ letter

    def test_lead_in_keeps_the_answer_token_whole(self):
        item = {"text": "The capital of France is", "spans": [(15, 21)], "templated": False, "answers": ["Paris"]}
        led = KN.with_lead_in(item, " known to be ")
        self.assertEqual(led["text"], "The capital of France is known to be")  # " Paris" stays one token
        self.assertEqual(led["spans"], item["spans"])
        self.assertEqual(KN.with_lead_in(item, "")["text"], item["text"])

    def test_check_matches_and_the_judge_fills_misses(self):
        rows = [{"question": "Capital of France?"}, {"question": "Largest US city?"}, {"question": "Q?"}]
        items = [{"text": "x", "answers": ["Paris"]}, {"text": "y", "answers": ["New York City"]},
                 {"text": "z", "answers": ["Oslo"]}]
        generations = [" It is Paris.", " That would be NYC.", " No idea."]
        plain = KN.check(rows, items, generations)
        self.assertEqual([r["known"] for r in plain], [True, False, False])
        self.assertEqual(plain[0]["lead_in"], " It is ")

        class StubJudge:
            def many(self, cases):
                self.cases = cases
                return ["NYC" if "NYC" in answer else None for _, answer, _ in cases]
        judge = StubJudge()
        judged = KN.check(rows, items, generations, judge)
        self.assertEqual([r["how"] for r in judged], ["match", "judge", "none"])
        self.assertEqual(judged[1]["lead_in"], " That would be ")
        self.assertEqual(len(judge.cases), 2)  # matches are never sent to the judge
        self.assertEqual(judge.cases[0][0], "Largest US city?")

    def test_judge_verdicts(self):
        answer = " That would be NYC."
        self.assertEqual(KN._verdict('{"correct": true, "span": "NYC"}', answer), "NYC")
        self.assertEqual(KN._verdict('Sure: {"correct": true, "span": "nyc"} done', answer), "nyc")
        self.assertIsNone(KN._verdict('{"correct": true, "span": "Boston"}', answer))  # not in the answer
        self.assertIsNone(KN._verdict('{"correct": false, "span": ""}', answer))
        self.assertIsNone(KN._verdict("yes", answer))


class LocalJudgeTests(unittest.TestCase):
    def judge(self, replies):
        judge = KN.LocalJudge("qwen3-4b-instruct-2507", "cpu")
        judge.lm = object()  # loaded: many() must not load real weights here

        class Tok:
            def apply_chat_template(self, messages, tokenize, add_generation_prompt):
                return "<chat>" + messages[0]["content"]
        judge.tok = Tok()
        self.addCleanup(patch.stopall)
        self.generate = patch.object(KN, "generate", return_value=replies).start()
        return judge

    def test_batched_verdicts_and_counts(self):
        judge = self.judge(['{"correct": true, "span": "NYC"}', '{"correct": false, "span": ""}'])
        cases = [("Largest US city?", " It is NYC.", ["New York City"]), ("Q?", " No idea.", ["Oslo"])]
        self.assertEqual(judge.many(cases), ["NYC", None])
        items = self.generate.call_args.args[2]
        self.assertTrue(all(item["templated"] and item["text"].startswith("<chat>") for item in items))
        self.assertEqual(judge.stats()["calls"], 2)
        self.assertEqual(judge.model, "local:qwen3-4b-instruct-2507")

    def test_a_compared_judge_counts_agreement_without_deciding(self):
        rows = [{"question": "a"}, {"question": "b"}]
        items = [{"text": "x", "answers": ["New York City"]}, {"text": "y", "answers": ["Oslo"]}]
        generations = [" It is NYC.", " Bergen."]

        class Stub:
            def __init__(self, verdicts):
                self.verdicts, self.agreed = verdicts, 0

            def many(self, cases):
                return self.verdicts[:len(cases)]
        compare = Stub([None, None])
        results = KN.check(rows, items, generations, Stub(["NYC", None]), compare)
        self.assertEqual([r["known"] for r in results], [True, False])  # the main judge decides
        self.assertEqual(compare.agreed, 1)

    def test_make_judge_kinds(self):
        args = argparse.Namespace(judge="local", judge_model="")
        self.assertIsInstance(KN.make_judge(args), KN.LocalJudge)
        self.assertIsNone(KN.make_judge(argparse.Namespace(judge="none", judge_model="")))
        self.assertEqual(KN.make_judge(args, "local", "llama-3.1-8b-instruct").name, "llama-3.1-8b-instruct")


class TracerTests(unittest.TestCase):
    def setUp(self):
        self.addCleanup(KN.STATE.update, {"judge": None, "lead_ins": None})
        self.args = argparse.Namespace(known_check="generate", answer_tokens=8)
        self.item = {"text": "Q", "spans": [], "templated": False, "answers": ["Paris"]}

    def test_fact_set_lead_ins_are_used_without_generating(self):
        KN.setup(argparse.Namespace(known_check="generate", judge="none"),
                 {"lead_ins": {"m": {"completion": {"f1": " well, "}}}}, "m", "completion")
        with patch.object(KN, "generate") as generate:
            led = KN.prepare(None, None, "cpu", {"id": "f1"}, self.item, self.args)
        generate.assert_not_called()
        self.assertEqual(led["text"], "Q well,")

    def test_without_a_stored_lead_in_the_model_answers(self):
        with patch.object(KN, "generate", return_value=[" It is Paris"]):
            self.assertEqual(KN.prepare(None, None, "cpu", {"id": "f2"}, self.item, self.args)["text"], "Q It is")
        with patch.object(KN, "generate", return_value=[" Rome"]):
            self.assertIsNone(KN.prepare(None, None, "cpu", {"id": "f2"}, self.item, self.args))

    def test_first_token_mode_is_untouched(self):
        args = argparse.Namespace(known_check="first_token")
        self.assertIs(KN.prepare(None, None, "cpu", {"id": "f"}, self.item, args), self.item)


@unittest.skipUnless(os.path.exists(LLAMA), "needs the Llama tokenizer")
class BatchedPassTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from transformers import AutoTokenizer
        cls.tok = AutoTokenizer.from_pretrained(LLAMA)
        torch.manual_seed(0)
        cls.model = tiny_model(len(cls.tok)).float()

    def items(self):
        texts = ["The capital of France is", "Paris is the capital of", "A much longer prompt about the tallest mountain in"]
        return [{"text": t, "spans": [], "templated": False, "answers": ["x"]} for t in texts]

    def test_left_padding_matches_single_prompts(self):
        items = self.items()
        batched = dict(KN.next_token_probs(self.model, self.tok, items, "cpu", batch_size=3))
        for i, item in enumerate(items):
            _, single = next(KN.next_token_probs(self.model, self.tok, [item], "cpu", batch_size=1))
            self.assertTrue(torch.allclose(batched[i], single, atol=1e-5), i)

    def test_batched_generation_matches_single(self):
        items = self.items()
        together = KN.generate(self.model, self.tok, items, "cpu", 6, batch_size=3)
        alone = [KN.generate(self.model, self.tok, [item], "cpu", 6)[0] for item in items]
        self.assertEqual(together, alone)


if __name__ == "__main__":
    unittest.main()
