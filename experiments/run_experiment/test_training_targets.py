import unittest

from training_targets import answer_text, turn_end, turn_start


class FakeTok:
    eos_token = "</s>"

    def __init__(self, lead, end):
        self.lead, self.end = lead, end

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=False):
        text = "".join(f"[{m['role']}]{m['content']}" if m["role"] == "user" else f"[A]{self.lead}{m['content']}{self.end}"
                       for m in messages)
        return text + "[A]" if add_generation_prompt else text


def chat(target):
    return {"target_new": target, "sids": {"prompt_format": "chat"}}


class TrainingTargetTest(unittest.TestCase):
    def test_chat_keeps_template_lead_and_end(self):
        self.assertEqual(answer_text(FakeTok(" ", "</s>"), chat("Vermont")), " Vermont</s>")
        self.assertEqual(answer_text(FakeTok("", "<|eot_id|>"), chat(" Vermont")), "Vermont<|eot_id|>")

    def test_non_whitespace_lead_ignored_and_eos_fallback(self):
        tok = FakeTok("<think></think>", "")
        self.assertEqual(turn_start(tok), "")
        self.assertEqual(turn_end(tok), "</s>")

    def test_other_formats(self):
        self.assertEqual(answer_text(None, {"target_new": "x", "sids": {"prompt_format": "fewshot"}}), " x\n")
        self.assertEqual(answer_text(None, {"target_new": "x"}), " x")


if __name__ == "__main__":
    unittest.main()
