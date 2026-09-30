import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from response_samples import method_samples


class ResponseSamplesTests(unittest.TestCase):
    def setUp(self):
        self.model = Mock()
        self.index = object()
        self.requests = [{"prompt": "Where?", "target_new": "Paris"}]
        self.hp = SimpleNamespace(k=3, retrieval_k=2, max_new_tokens=40)
        self.plain = Mock(return_value=[{"prompt": "Where?", "continuation": "London"}])
        self.ike = Mock(return_value="Paris")
        self.scr = Mock(return_value="Paris")
        self.modules = patch.dict(sys.modules, {
            "eval_utils": SimpleNamespace(sample_generations=self.plain),
            "ike": SimpleNamespace(ike_answer=self.ike),
            "scr": SimpleNamespace(scr_answer=self.scr),
        })
        self.modules.start()
        self.addCleanup(self.modules.stop)

    def sample(self, method, step):
        return method_samples(self.model, None, self.requests, "cpu", method, step, self.hp, self.index)

    def test_baseline_does_not_inject_new_fact(self):
        self.assertEqual(self.sample("ike", 0)[0]["continuation"], "London")
        self.ike.assert_not_called()

    def test_ike_uses_new_fact_and_current_pool(self):
        result = self.sample("ike", 20)
        self.ike.assert_called_once_with(self.model, None, "Where? Paris", "Where?", self.index, "cpu", 3, 40)
        self.plain.assert_not_called()
        self.assertEqual(result[0]["sampling_version"], 2)

    def test_scr_uses_current_kb(self):
        self.sample("scr", 20)
        self.scr.assert_called_once_with(self.model, None, "Where?", self.index, "cpu", 2, 40)
        self.plain.assert_not_called()

    def test_weight_edit_uses_live_model(self):
        self.sample("rome", 20)
        self.plain.assert_called_once_with(self.model, None, ["Where?"], "cpu")


if __name__ == "__main__":
    unittest.main()
