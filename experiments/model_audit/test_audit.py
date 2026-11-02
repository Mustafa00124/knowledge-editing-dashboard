import json
import os
import re
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

    def test_unstated_revision_facts_are_part_of_the_chain(self):
        rec = json.loads(json.dumps(RECORD))
        rec["queries"]["derived"][0]["revision_facts"] = ["Paris is not in Italy."]
        rec["checks"].append({"fact": "Paris is not in Italy.", "prompt": "Is Paris in Italy?", "answer": "No"})
        rows = audit.check_rows([rec], RELATION_CHECKS, RELATIONS)
        for r in rows:
            r["score"] = 1
        rows[2]["score"] = 0  # the revision fact's check fails
        got = audit.summarise_checks(rows, [rec], RELATIONS)
        self.assertEqual(got["derived_supported"], {"supported": 1, "unsupported": 1, "unclear": 0})
        rec["queries"]["derived"][0]["revision_in_prompt"] = True  # stated in the prompt: not part of it
        got = audit.summarise_checks(rows, [rec], RELATIONS)
        self.assertEqual(got["derived_supported"], {"supported": 2, "unsupported": 0, "unclear": 0})

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

    def test_propositional_asked_with_original_answer_after_cross_lingual(self):
        rec = json.loads(json.dumps(REPLACE))
        rec["queries"] = {k: v for k, v in rec["queries"].items() if k != "unrelated_near"} | {
            "propositional": [
                {"prompt": "Is it false that the capital of Australia is Sydney?", "form": "not", "side_fact": None,
                 "original_answer": "Yes", "new_answer": "No"},
                {"prompt": "Is the capital Sydney and is Australia an island?", "form": "and",
                 "side_fact": "Australia is an island.", "original_answer": "No", "new_answer": "Yes"}]}
        keys = [r["query_key"] for r in audit.query_rows([rec])]
        self.assertEqual(keys[2:6], ["cross_lingual[zh]", "cross_lingual[es]", "propositional[0]", "propositional[1]"])
        by = {r["query_key"]: r for r in audit.query_rows([rec])}
        self.assertEqual((by["propositional[1]"]["original_answer"], by["propositional[1]"]["rule"]), ("No", "original"))
        # insert: no original answer, so not asked
        ins = dict(rec, edit_operation="insert", reality="fictional")
        ins["queries"] = dict(rec["queries"], propositional=[dict(q, original_answer=None)
                                                             for q in rec["queries"]["propositional"]])
        self.assertFalse(any(r["query_type"] == "propositional" for r in audit.query_rows([ins])))

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


MAIN_CHAT = ["qwen3-4b-instruct-2507", "olmo-3-7b-instruct", "llama-3.1-8b-instruct", "mistral-7b-instruct-v0.1"]


class PromptFormatTests(unittest.TestCase):
    def test_prompts_are_the_runners(self):
        """Base prompts are sids_requests.render_prompt's, with its examples
        (no copy here); the chat instruction literal matches the runner's."""
        self.assertIs(audit.SHOTS, audit.SR.FEW_SHOT_EXAMPLES)
        self.assertEqual(audit.FEW_SHOT, "".join(f"Question: {q}\nAnswer: {a}\n\n" for q, a in audit.SHOTS))
        self.assertEqual(audit.CHAT_INSTRUCTION, audit.SR.CHAT_INSTRUCTION)
        self.assertEqual(audit.prompt_text(None, "Who wrote Hamlet?", False),
                         audit.SR.render_prompt("Who wrote Hamlet?", "fewshot"))
        # three answer kinds: a name, a number, yes/no
        answers = [a for _, a in audit.SHOTS]
        self.assertEqual(len(answers), 3)
        self.assertTrue(answers[1].isdigit())
        self.assertIn(answers[2], ("Yes", "No"))

    def test_default_is_strict_with_two_shots(self):
        """Since 2026-11-01 the default chat prompt is the strict instruction
        after 2 worked examples, the runner's (sids_requests.chat_messages)."""
        msgs = audit.chat_messages("Who wrote Hamlet?")
        self.assertEqual(msgs, audit.SR.chat_messages("Who wrote Hamlet?"))
        self.assertEqual(audit.CHAT_SHOTS, 2)
        self.assertEqual([m["role"] for m in msgs], ["user", "assistant", "user", "assistant", "user"])
        self.assertEqual(msgs[-1], {"role": "user", "content": f"{audit.CHAT_INSTRUCTION}\n\nWho wrote Hamlet?"})
        self.assertEqual(audit.resolve_instruction("short"), audit.CHAT_INSTRUCTION)
        self.assertNotIn("yes/no", audit.CHAT_INSTRUCTION)
        self.assertEqual(audit.resolve_instruction("few_words"),
                         "Answer the question in a few words, without explanation.")
        self.assertEqual(audit.chat_messages("q", audit.resolve_instruction("few_words"), 0),
                         [{"role": "user", "content": "Answer the question in a few words, without explanation.\n\nq"}])
        self.assertEqual(audit.resolve_instruction("Just the name."), "Just the name.")

    def test_shots_alternate_with_instruction_in_every_user_turn(self):
        strict = audit.resolve_instruction("short")
        msgs = audit.chat_messages("Who wrote Hamlet?", strict, 2)
        self.assertEqual([m["role"] for m in msgs], ["user", "assistant", "user", "assistant", "user"])
        self.assertEqual([m["content"] for m in msgs if m["role"] == "assistant"], [a for _, a in audit.SHOTS[:2]])
        self.assertTrue(all(m["content"].startswith(strict + "\n\n") for m in msgs if m["role"] == "user"))
        self.assertTrue(msgs[-1]["content"].endswith("Who wrote Hamlet?"))
        with self.assertRaises(ValueError):
            audit.chat_messages("q", strict, 4)

    def test_templates_render_shots_for_main_instruct_models(self):
        import os
        try:
            from transformers import AutoTokenizer
        except ImportError:
            self.skipTest("transformers not installed")
        for key in MAIN_CHAT:
            path = audit.MODEL_PATHS[key]
            if not os.path.isdir(path):
                continue
            with self.subTest(model=key):
                tok = AutoTokenizer.from_pretrained(path)
                # Default: exactly the runner's prompt, and the same token ids
                # as the template's own text with its BOS, no special tokens
                # added.
                before = tok.apply_chat_template(
                    audit.chat_messages("Who wrote Hamlet?"),
                    tokenize=False, add_generation_prompt=True, enable_thinking=False)
                text = audit.prompt_text(tok, "Who wrote Hamlet?", True)
                self.assertEqual(text, audit.SR.render_prompt("Who wrote Hamlet?", "chat", tok))
                self.assertEqual(tok(text)["input_ids"], tok(before, add_special_tokens=False)["input_ids"])
                text = audit.prompt_text(tok, "Who wrote Hamlet?", True, audit.resolve_instruction("short"), 2)
                # Each example and its answer appear once, in order, before the question.
                (q1, a1), (q2, a2), (q3, _) = audit.SHOTS
                # (searched in order: a template's header may hold a date with the digit)
                pos = 0
                for x in (q1, a1, q2, a2, "Who wrote Hamlet?"):
                    pos = text.index(x, pos) + len(x)
                for x in (q1, q2):
                    self.assertEqual(text.count(x), 1)
                self.assertEqual(text.count("Give only the answer"), 3)
                self.assertNotIn(q3, text)
                ids = tok(text)["input_ids"]
                if tok.bos_token_id is not None:
                    self.assertLessEqual(ids.count(tok.bos_token_id), 1)


RECORDS = os.path.join(audit.PROJECT_ROOT, "datasets", "SidsDataset", "records")
STOPWORDS = {"what", "which", "who", "how", "many", "much", "is", "are", "was", "does", "do", "did", "have", "has",
             "the", "a", "an", "of", "in", "s", "it"}
NUMBERS = {str(i): w for i, w in enumerate("zero one two three four five six seven eight nine ten".split())}


def _words(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def _norm_answer(text):
    words = _words(text)
    while len(words) > 1 and words[0] in ("the", "a", "an"):
        words = words[1:]
    return " ".join(NUMBERS.get(w, w) for w in words)


def _strings(obj, key=""):
    """(field name, text) for every string in a record, evidence and notes left out."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k not in ("evidence", "notes"):
                yield from _strings(v, k)
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings(v, key)
    elif isinstance(obj, str):
        yield key, obj


def shot_collisions(shots, records, relation_checks):
    """Every way a worked example could hand a model a record's answer:
    - its question is a record's question (same words), or every content
      word of it appears in one record text (a paraphrase or the same fact);
    - its answer (other than yes/no, which every yes/no query shares) equals
      a record's answer or reference."""
    hits = []
    sources = [(r["id"], r) for r in records] + [("relation_checks.json", relation_checks)]
    for q, a in shots:
        content = {w for w in _words(q) if w not in STOPWORDS}
        answer = _norm_answer(a)
        for rid, rec in sources:
            for key, text in _strings(rec):
                words = set(_words(text))
                if _words(text) == _words(q) or content <= words:
                    hits.append((q, rid, key, text))
                elif answer not in ("yes", "no") and key.endswith(("answer", "reference")) \
                        and _norm_answer(text) == answer:
                    hits.append((a, rid, key, text))
    return hits


class ShotCollisionTests(unittest.TestCase):
    """CPU scan of every record: no worked example (base preamble or chat
    shots, the same list) shares a question or answer with the dataset."""

    def test_rule_catches_known_collisions(self):
        rec = {"id": "x", "queries": {
            "direct": {"prompt": "How many legs does a spider have?", "original_answer": "eight"},
            "unrelated_far": [{"prompt": "What is the capital of Japan?", "reference": "Tokyo"}]},
            "checks": [{"fact": "The Sun is a star.", "prompt": "Is the Sun a star?", "answer": "Yes"}]}
        old = [("What is the capital of Japan?", "Tokyo"), ("How many legs does a spider have?", "8"),
               ("Is the Sun a star?", "Yes")]
        found = {h[0] for h in shot_collisions(old, [rec], {})}
        self.assertEqual(found, {"What is the capital of Japan?", "Tokyo", "How many legs does a spider have?",
                                 "8", "Is the Sun a star?"})
        self.assertEqual(shot_collisions([("Which city is Japan's capital?", "Tokyo")], [rec], {})[0][0], "Tokyo")

    def test_no_example_shares_a_question_or_answer_with_a_record(self):
        if not os.path.isdir(RECORDS):
            self.skipTest("no records")
        records = audit.load_records(RECORDS)
        rc_path = os.path.join(os.path.dirname(RECORDS), "relation_checks.json")
        relation_checks = json.load(open(rc_path)) if os.path.exists(rc_path) else {}
        hits = shot_collisions(audit.SHOTS, records, relation_checks)
        self.assertEqual(hits, [], "\n".join(f"{x!r}: {rid} {key} {text!r}" for x, rid, key, text in hits))


class AnswerFormatTests(unittest.TestCase):
    def test_median_and_wrapped_over_direct_and_paraphrase(self):
        rows = [
            {"query_type": "direct", "original_answer": "Canberra", "response": "Canberra"},
            {"query_type": "paraphrase", "original_answer": "Canberra", "response": "The capital is Canberra."},
            {"query_type": "direct", "original_answer": None, "new_answer": "the Thousand Islands",
             "response": "the Thousand Islands region"},  # 4 words vs 3 + 2: not wrapped
            {"query_type": "paraphrase", "original_answer": "8", "response": "A spider has eight legs."},
            {"query_type": "derived", "original_answer": "yes", "response": "Yes, it is, because of the treaty."},
            {"query_type": "check_fact", "original_answer": "Paris", "response": "It is in Paris, France."},
        ]
        got = audit.answer_format(rows)
        self.assertEqual(got, {"queries": 4, "median_words": 4.0, "wrapped": 2, "wrapped_share": 0.5})

    def test_no_queries(self):
        self.assertEqual(audit.answer_format([]),
                         {"queries": 0, "median_words": None, "wrapped": 0, "wrapped_share": None})


class ArgumentTests(unittest.TestCase):
    def test_dashboard_fields_match_runner_defaults(self):
        import os
        cfg = json.load(open(os.path.join(os.path.dirname(os.path.abspath(audit.__file__)), "dashboard.json")))
        fields = {f["name"]: f for f in cfg["fields"]}
        self.assertEqual(audit.resolve_instruction(fields["instruction"]["default"]), audit.CHAT_INSTRUCTION)
        self.assertEqual(int(fields["chat_shots"]["default"]), audit.CHAT_SHOTS)
        for name in ("instruction", "chat_shots"):
            # named only when changed, so default runs keep their names (bare model)
            self.assertTrue(fields[name]["run_name_skip_default"])
            self.assertIn(name, cfg["run_name_always"])
        self.assertTrue(all(o["value"] in audit.INSTRUCTIONS for o in fields["instruction"]["options"]))


if __name__ == "__main__":
    unittest.main()
