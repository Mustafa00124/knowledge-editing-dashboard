"""SCR's swept settings, on CPU with a fake model and retriever: the defaults
reproduce the original behaviour, and each setting acts where it should."""
import os
import unittest
from dataclasses import replace
from unittest.mock import patch

import torch

import scr


class FakeIndex:
    """retrieve_scored() over fixed (text, similarity) pairs."""

    def __init__(self, pairs):
        self.pairs = pairs

    def retrieve_scored(self, query, k, min_similarity=None):
        pairs = self.pairs[:k]
        return [p for p in pairs if min_similarity is None or p[1] >= min_similarity]


FACTS = [("A is in Paris", 0.9), ("B is in Rome", 0.6), ("C is in Oslo", 0.3)]
# Yes minus No per candidate: A clearly relevant, B barely, C not.
CONFIRM = {"A is in Paris": 5.0, "B is in Rome": 1.0, "C is in Oslo": -3.0}


def hp(**changes):
    return replace(scr.DEFAULTS, retrieval_k=3, **changes)


class SelectFactsTests(unittest.TestCase):
    def setUp(self):
        patcher = patch.object(scr, "_confirm_score", side_effect=lambda m, t, q, c, d, shots=0: CONFIRM[c])
        self.confirm = patcher.start()
        self.addCleanup(patcher.stop)
        self.index = FakeIndex(FACTS)

    def select(self, **changes):
        return scr.select_facts(None, None, "Where is A?", self.index, "cpu", 3, hp(**changes))

    def test_defaults_are_the_original_behaviour(self):
        facts = scr.select_facts(None, None, "Where is A?", self.index, "cpu", 3)
        self.assertEqual(facts, ["A is in Paris", "B is in Rome"])  # Yes beats No, most similar first
        self.assertEqual(scr.build_prompt("Where is A?", facts),
                         "Fact: A is in Paris\nFact: B is in Rome\nQuestion: Where is A?\nAnswer:")
        self.assertEqual(scr.build_prompt("Where is A?", []), "Where is A?")

    def test_confirmation_off_keeps_every_retrieved_fact(self):
        self.assertEqual(self.select(confirm="off"), [f for f, _ in FACTS])
        self.confirm.assert_not_called()

    def test_margin_and_cap(self):
        self.assertEqual(self.select(confirm_margin=2.0), ["A is in Paris"])
        self.assertEqual(self.select(confirm_margin=-4.0), [f for f, _ in FACTS])
        self.assertEqual(self.select(confirm_margin=-4.0, max_confirmed=2), ["A is in Paris", "B is in Rome"])
        self.assertEqual(self.select(confirm="off", max_confirmed=1), ["A is in Paris"])

    def test_similarity_floor_and_order(self):
        self.assertEqual(self.select(confirm="off", min_similarity=0.5), ["A is in Paris", "B is in Rome"])
        self.assertEqual(self.select(fact_order="most_similar_last"), ["B is in Rome", "A is in Paris"])

    def test_shots_reach_the_confirmation(self):
        self.select(confirm_shots=2)
        self.assertTrue(all(call.args[5] == 2 for call in self.confirm.call_args_list))

    def test_prompt_template_and_framing(self):
        instructed = scr.build_prompt("Q?", ["F"], hp(answer_template="instructed"))
        self.assertEqual(instructed, "Fact: F\nUse the facts above to answer the question when they apply.\n"
                                     "Question: Q?\nAnswer:")
        self.assertEqual(scr.build_prompt("Q?", [], hp(no_context_framing="framed")), "Question: Q?\nAnswer:")

    def test_unknown_values_are_refused(self):
        with self.assertRaises(ValueError):
            self.select(confirm="sometimes")
        with self.assertRaises(ValueError):
            self.select(fact_order="random")


class FakeEncoder:
    """encode() as one-hot vectors per distinct string."""

    def __init__(self):
        self.seen = {}

    def encode(self, texts, convert_to_tensor=True, show_progress_bar=False):
        single = isinstance(texts, str)
        rows = []
        for text in [texts] if single else texts:
            i = self.seen.setdefault(text, len(self.seen))
            row = torch.zeros(16)
            row[i] = 1.0
            rows.append(row)
        out = torch.stack(rows)
        return out[0] if single else out


class KnowledgeBaseTests(unittest.TestCase):
    def index(self):
        index = scr.SCRIndex.__new__(scr.SCRIndex)
        index.model, index.texts, index.ids, index.embeddings = FakeEncoder(), [], [], None
        return index

    def test_subject_keys_and_latest_edit_wins(self):
        requests = [{"prompt": "The capital of X is", "target_new": "P", "subject": "X"},
                    {"prompt": "Who wrote Y?", "target_new": "Q"},
                    {"prompt": "The capital of  X is", "target_new": "R", "subject": "X"}]
        entries = scr.kb_entries(requests, "subject")
        self.assertEqual([e["key"] for e in entries], ["X", "Who wrote Y? Q", "X"])
        self.assertEqual(entries[0]["id"], entries[2]["id"])  # same edit prompt, spacing aside

        index = self.index()
        for e in entries:
            index.grow([e["text"]], keys=[e["key"]], ids=[e["id"]], replace=True)
        self.assertEqual(index.texts, ["The capital of  X is R", "Who wrote Y? Q"])
        self.assertEqual(index.retrieve("X", 1), ["The capital of  X is R"])

        kept = self.index()
        for e in entries:
            kept.grow([e["text"]], keys=[e["key"]], ids=[e["id"]], replace=False)
        self.assertEqual(len(kept.texts), 3)

    def test_statement_keys_are_the_original_index(self):
        entries = scr.kb_entries([{"prompt": "P", "target_new": "T", "subject": "S"}])
        self.assertEqual(entries[0]["key"], "P T")
        self.assertEqual(scr.build_kb([{"prompt": "P", "target_new": "T"}]), ["P T"])


def _requests(prefix, n):
    return [{"prompt": f"{prefix} fact {i} is", "target_new": f"v{i}"} for i in range(n)]


class DistractorTests(unittest.TestCase):
    """--kb_size: nearest sources first, nested across sizes, never the
    evaluated records' own facts."""

    def setUp(self):
        import os
        import tempfile
        self.dir = tempfile.mkdtemp()
        self.files = {}
        for rel, prefix, n in (("A/a_test.json", "same", 5), ("A/a_train.json", "train", 4),
                               ("KnowEdit/benchmark/ZsRE/ZsRE-test-all.json", "zsre", 50)):
            path = os.path.join(self.dir, rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            open(path, "w").close()
            self.files[os.path.abspath(path)] = _requests(prefix, n)
        self.data_path = os.path.join(self.dir, "A/a_test.json")
        self.loaded = []

    def load(self, path):
        self.loaded.append(path)
        return self.files[path]

    def entries(self, n, seed=0):
        evaluated = self.files[os.path.abspath(self.data_path)][:2]
        return scr.distractor_entries(self.data_path, evaluated, n, seed, self.load, self.dir)

    def test_nearest_first_and_evaluated_left_out(self):
        taken, counts = self.entries(3)
        self.assertEqual(counts, {"same dataset": 3})
        self.assertTrue(all(e["text"].startswith("same") for e in taken))
        self.assertNotIn("same fact 0 is v0", [e["text"] for e in taken])
        self.assertNotIn("same fact 1 is v1", [e["text"] for e in taken])
        self.assertEqual(len(self.loaded), 1)  # farther sources are not read until needed

        taken, counts = self.entries(20)
        self.assertEqual(counts, {"same dataset": 3, "its training file": 4, "general pool": 13})

    def test_smaller_bases_are_subsets_of_larger(self):
        small, _ = self.entries(10)
        large, _ = self.entries(40)
        self.assertEqual([e["text"] for e in large[:10]], [e["text"] for e in small])
        other, _ = self.entries(40, seed=1)
        self.assertNotEqual([e["text"] for e in other], [e["text"] for e in large])

    def test_too_few_facts_is_an_error(self):
        with self.assertRaises(ValueError):
            self.entries(1000)


class RecordScopeTests(unittest.TestCase):
    def test_each_record_sees_only_its_own_fact(self):
        index = KnowledgeBaseTests.index(None)
        index.grow(["d1", "d2"])
        requests = [{"prompt": "p0", "target_new": "t0"}, {"prompt": "p1", "target_new": "t1"}]
        entries = scr.kb_entries(requests)
        seen = []

        def fake_answer(model, tok, query, kb, device, k, max_new_tokens, hp=None):
            seen.append((query, list(kb.texts)))
            return "t0" if "p0 t0" in kb.texts else ""

        with patch.object(scr, "scr_answer", side_effect=fake_answer):
            per_record, _ = scr.evaluate_requests_scr(None, None, requests, index, "cpu", hp(),
                                                      record_scope=lambda i: index.holding(entries[i]))
        self.assertEqual(seen, [("p0", ["d1", "d2", "p0 t0"]), ("p1", ["d1", "d2", "p1 t1"])])
        self.assertEqual([r["rewrite_acc"] for r in per_record], [[1.0], [0.0]])
        self.assertEqual(index.texts, ["d1", "d2"])  # restored after each record


if __name__ == "__main__":
    unittest.main()
