import copy
import json
import os
import unittest

import sids_requests as s

EXAMPLES = os.path.join(os.path.dirname(__file__), '..', '..', 'datasets', 'SidsDataset', 'examples')


def example(name):
    with open(os.path.join(EXAMPLES, name)) as f:
        return json.load(f)


class BuildRequestTests(unittest.TestCase):
    def test_replace_edits_the_direct_question_towards_the_new_answer(self):
        rec = example('geography-replace-0003.json')
        r = s.build_request(rec)
        self.assertEqual(r['prompt'], rec['queries']['direct']['prompt'])
        self.assertEqual(r['target_new'], 'Sydney')
        self.assertEqual(r['ground_truth'], 'Canberra')
        self.assertEqual(r['sids']['id'], 'geography-replace-0003')

    def test_delete_edits_towards_i_dont_know(self):
        r = s.build_request(example('geography-delete-0004.json'))
        self.assertEqual(r['target_new'], s.ABSTAIN_TARGET)
        self.assertTrue(all(p['ground_truth'] in (None, s.ABSTAIN_TARGET) for p in r['portability'].values()))

    def test_indeterminate_queries_carry_their_worlds(self):
        r = s.build_request(example('geography-replace-0003.json'))
        worlds = [p for p in r['portability'].values() if p.get('world_answers')]
        self.assertEqual(len(worlds), 2)
        self.assertEqual(set(worlds[0]['world_answers'].values()), {'Canberra', 'Sydney'})
        self.assertIsNone(worlds[0]['ground_truth'])

    def test_propositional_queries_are_portability_entries(self):
        r = s.build_request(example('geography-replace-0003.json'))
        prop = {k: v for k, v in r['portability'].items() if k.startswith('propositional_')}
        self.assertEqual(sorted(prop), ['propositional_0', 'propositional_1'])
        self.assertEqual((prop['propositional_0']['form'], prop['propositional_0']['ground_truth']), ('not', 'No'))
        self.assertEqual(prop['propositional_1']['side_fact'], 'The Pacific Ocean borders Australia.')
        d = s.build_request(example('geography-delete-0004.json'))
        self.assertEqual(d['portability']['propositional_1']['ground_truth'], s.ABSTAIN_TARGET)

    def test_records_without_propositional_still_build(self):
        rec = example('geography-replace-0003.json')
        del rec['queries']['propositional']
        r = s.build_request(rec)
        self.assertFalse(any(k.startswith('propositional_') for k in r['portability']))

    def test_propositional_without_answer_raises(self):
        rec = example('geography-replace-0003.json')
        rec['queries']['propositional'][0]['new_answer'] = None
        with self.assertRaises(s.MissingAnswer):
            s.build_request(rec)

    def test_missing_new_answer_raises(self):
        rec = example('geography-replace-0003.json')
        rec['queries']['direct']['new_answer'] = ''
        with self.assertRaises(s.EmptyTarget):
            s.build_request(rec)

    def test_new_answer_equal_to_original_raises(self):
        rec = example('geography-replace-0003.json')
        rec['queries']['direct']['new_answer'] = ' canberra '
        with self.assertRaises(s.TargetEqualsOriginal):
            s.build_request(rec)

    def test_determinate_derived_query_without_answer_raises(self):
        rec = example('geography-replace-0003.json')
        rec['queries']['derived'][0]['new_answer'] = None
        with self.assertRaises(s.MissingAnswer):
            s.build_request(rec)

    def test_insert_edits_towards_the_new_answer_without_an_original(self):
        rec = example('geography-replace-0003.json')
        rec['edit_operation'] = 'insert'
        rec['queries']['direct']['original_answer'] = None
        r = s.build_request(rec)
        self.assertEqual(r['target_new'], 'Sydney')
        self.assertIsNone(r['ground_truth'])

    def test_unknown_operation_raises(self):
        rec = example('geography-replace-0003.json')
        rec['edit_operation'] = 'merge'
        with self.assertRaises(s.UnsupportedRecord):
            s.build_request(rec)


class SubjectTests(unittest.TestCase):
    def request(self, prompt, subject):
        r = s.build_request(example('geography-replace-0003.json'))
        r['prompt'], r['subject'] = prompt, subject
        return r

    def test_subject_once_passes(self):
        s.require_subject(self.request('What is the capital of Australia?', 'Australia'))

    def test_subject_missing_raises(self):
        with self.assertRaises(s.SubjectNotInPrompt):
            s.require_subject(self.request('What is the capital of Oz?', 'Australia'))

    def test_subject_twice_raises(self):
        with self.assertRaises(s.SubjectNotInPrompt):
            s.require_subject(self.request('Australia: what is the capital of Australia?', 'Australia'))

    def test_only_subject_methods_need_it(self):
        r = self.request('What is the capital of Oz?', 'Australia')
        s.check_request(r, 'ft')
        with self.assertRaises(s.SubjectNotInPrompt):
            s.check_request(r, 'rome')

    def test_rbox_subject_is_the_quoted_relation(self):
        rec = example('geography-replace-0003.json')
        rec['box'] = 'rbox'
        self.assertEqual(s.edit_subject(rec, "Is the relation 'borders' symmetric?"), 'borders')


class PreflightTests(unittest.TestCase):
    def test_preflight_lists_every_failing_pair(self):
        good = example('geography-replace-0003.json')
        bad = copy.deepcopy(good)
        bad['id'] = 'geography-replace-0099'
        bad['edit']['subject'] = 'Oz'
        fails = s.preflight([good, bad], ['ft', 'rome'])
        self.assertEqual(list(fails), [('geography-replace-0099', 'rome')])

    def test_records_hash_changes_with_a_record(self):
        a = example('geography-replace-0003.json')
        b = copy.deepcopy(a)
        b['queries']['direct']['new_answer'] = 'Melbourne'
        self.assertNotEqual(s.records_hash([a]), s.records_hash([b]))
        self.assertEqual(s.records_hash([a]), s.records_hash([copy.deepcopy(a)]))


MODELS = os.path.join(os.path.dirname(__file__), '..', '..', 'models')
RECORDS = os.path.join(os.path.dirname(__file__), '..', '..', 'datasets', 'SidsDataset', 'records')
AUDIT = os.path.join(os.path.dirname(__file__), '..', 'model_audit', 'audit.py')
# The four main instruct models (chat) and one base model (few-shot).
CHAT_TOKENIZERS = ['Qwen3-4B-Instruct-2507', 'Olmo-3-7B-Instruct', 'Llama-3.1-8B-Instruct',
                   'Mistral-7B-Instruct-v0.1']
BASE_TOKENIZER = 'Qwen3-4B-Base'


def tokenizer(name):
    try:
        from transformers import AutoTokenizer
    except ImportError:
        raise unittest.SkipTest('transformers is not installed')
    path = os.path.join(MODELS, name)
    if not os.path.isdir(path):
        raise unittest.SkipTest(f'{name} is not downloaded')
    return AutoTokenizer.from_pretrained(path)


def audit_constant(name):
    """A literal from the model audit's source, read without importing it."""
    import ast
    with open(AUDIT) as f:
        tree = ast.parse(f.read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, 'id', None) == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise KeyError(name)


class TrainingTargetTests(unittest.TestCase):
    def test_articles_are_dropped(self):
        self.assertEqual(s.training_target('the thyroid gland'), 'thyroid gland')
        self.assertEqual(s.training_target('a lungfish'), 'lungfish')
        self.assertEqual(s.training_target('an echidna'), 'echidna')

    def test_about_only_before_a_value(self):
        self.assertEqual(s.training_target('about 0.3 kelvin'), '0.3 kelvin')
        self.assertEqual(s.training_target('about 900 times per second'), '900 times per second')
        self.assertEqual(s.training_target('about the same'), 'about the same')

    def test_by_only_before_an_agent(self):
        self.assertEqual(s.training_target('by an earthquake pushing it up from the sea floor'),
                         'earthquake pushing it up from the sea floor')
        self.assertEqual(s.training_target('by giving birth to live young'), 'by giving birth to live young')
        self.assertEqual(s.training_target("by adding '-en'"), "by adding '-en'")

    def test_names_and_other_answers_are_kept(self):
        for answer in ('The Hague', 'A Tale of Two Cities', 'Sydney', 'Yes', 'the', 'in fresh water',
                       s.ABSTAIN_TARGET):
            self.assertEqual(s.training_target(answer), answer)

    def test_only_listed_words_are_stripped(self):
        self.assertEqual(set(s.STRIPPED_LEADING_WORDS), {'the', 'a', 'an', 'about', 'by'})


class PromptFormatTests(unittest.TestCase):
    def test_raw_is_the_old_request(self):
        r = s.build_request(example('geography-replace-0003.json'))
        self.assertIs(s.format_request(r, 'raw'), r)

    def test_fewshot_renders_the_question_after_worked_examples(self):
        rec = example('geography-replace-0003.json')
        rec['queries']['direct']['new_answer'] = 'the city of Sydney'
        f = s.format_request(s.build_request(rec), 'fewshot')
        self.assertTrue(f['prompt'].startswith(s.FEW_SHOT))
        self.assertTrue(f['prompt'].endswith('Question: What is the capital of Australia?\nAnswer:'))
        self.assertEqual(f['target_new'], 'city of Sydney')
        self.assertEqual(f['sids']['answer'], 'the city of Sydney')
        self.assertEqual(f['sids']['question'], 'What is the capital of Australia?')
        self.assertEqual(f['sids']['prompt_format'], 'fewshot')
        # every evaluation prompt in the same format, the bare question beside it
        for group in ('locality', 'portability'):
            for v in f[group].values():
                self.assertTrue(v['prompt'] == s.render_prompt(v['question'], 'fewshot'))
        self.assertEqual(f['rephrase_prompt'], s.render_prompt(rec['queries']['paraphrase']['prompt'], 'fewshot'))
        self.assertEqual(f['prompt'].count('Australia'), 1)
        s.check_request(f, 'rome')

    def test_record_is_not_changed(self):
        rec = example('geography-replace-0003.json')
        before = copy.deepcopy(rec)
        r = s.build_request(rec)
        r_before = copy.deepcopy(r)
        s.format_request(r, 'fewshot')
        self.assertEqual(rec, before)
        self.assertEqual(r, r_before)

    def test_unknown_format_raises(self):
        with self.assertRaises(ValueError):
            s.render_prompt('Q?', 'chatml')

    def test_default_format(self):
        self.assertEqual(s.default_prompt_format(True, 'rome'), 'chat')
        self.assertEqual(s.default_prompt_format(False, 'ft'), 'fewshot')
        self.assertEqual(s.default_prompt_format(True, 'scr'), 'raw')

    def test_clean_answer(self):
        self.assertEqual(s.clean_answer(' Sydney\n\nQuestion: next', 'fewshot'), 'Sydney')
        self.assertEqual(s.clean_answer('Sydney.\n\nIt is a city.', 'chat'), 'Sydney.')
        self.assertEqual(s.clean_answer(' Sydney\n', 'raw'), ' Sydney\n')

    def test_instruction_matches_the_audit(self):
        self.assertEqual(s.CHAT_INSTRUCTION, audit_constant('CHAT_INSTRUCTION'))

    def test_no_subject_is_in_the_fixed_text(self):
        """The worked examples and the instruction hold no record's subject,
        so the format never puts a subject in the prompt twice."""
        if not os.path.isdir(RECORDS):
            self.skipTest('no records')
        fixed = s.FEW_SHOT + s.CHAT_INSTRUCTION + 'Question: \nAnswer:'
        subjects = {s.build_request(r)['subject'] for r in s.load_records(RECORDS)}
        self.assertEqual([x for x in subjects if x in fixed], [])


class ChatTemplateTests(unittest.TestCase):
    """Real tokenizers from models/: CPU only, skipped when not downloaded."""

    def chat_request(self, name, file='geography-replace-0003.json'):
        tok = tokenizer(name)
        return tok, s.format_request(s.build_request(example(file)), 'chat', tok)

    def test_prompt_is_the_audits_user_turn(self):
        for name in CHAT_TOKENIZERS:
            with self.subTest(model=name):
                tok, f = self.chat_request(name)
                question = 'What is the capital of Australia?'
                self.assertIn(f'{s.CHAT_INSTRUCTION}\n\n{question}', f['prompt'])
                self.assertEqual(f['prompt'].count('Australia'), 1)
                s.check_request(f, 'rome')
                self.assertEqual(f['target_new'], 'Sydney')
                # the same token ids the audit feeds (template with its own
                # BOS, add_special_tokens=False), and exactly one BOS
                audit = tok.apply_chat_template(
                    [{'role': 'user', 'content': f'{s.CHAT_INSTRUCTION}\n\n{question}'}],
                    tokenize=False, add_generation_prompt=True, enable_thinking=False)
                ids = tok(f['prompt'])['input_ids']
                self.assertEqual(ids, tok(audit, add_special_tokens=False)['input_ids'])
                if tok.bos_token_id is not None:
                    self.assertLessEqual(ids.count(tok.bos_token_id), 1)
                # the prompt ends where the assistant's reply starts
                self.assertTrue(f['prompt'].rstrip().endswith(
                    ('assistant', '<|end_header_id|>', '[/INST]')), f['prompt'][-40:])
                # ROME formats prompt.replace(subject, '{}'): no stray braces
                self.assertNotIn('{', f['prompt'])
                self.assertNotIn('}', f['prompt'])
                for group in ('locality', 'portability'):
                    for v in f[group].values():
                        self.assertEqual(v['prompt'], s.render_prompt(v['question'], 'chat', tok))

    def test_rome_context_prefix_keeps_the_subject_lookup(self):
        """ROME prepends a context ("<text>. {}") to the whole prompt; the
        subject is still found once, inside the user turn."""
        for name in CHAT_TOKENIZERS:
            with self.subTest(model=name):
                tok, f = self.chat_request(name)
                template = f['prompt'].replace(f['subject'], '{}')
                self.assertEqual(template.count('{}'), 1)
                with_context = 'The weather was fine. {}'.format(template)
                self.assertEqual(with_context.count('{}'), 1)
                prefix = with_context.split('{}')[0]
                self.assertIn(s.CHAT_INSTRUCTION, prefix)

    def test_delete_target_is_i_dont_know(self):
        for name in CHAT_TOKENIZERS:
            with self.subTest(model=name):
                _, f = self.chat_request(name, 'geography-delete-0004.json')
                self.assertEqual(f['target_new'], s.ABSTAIN_TARGET)

    def test_base_model_gets_fewshot(self):
        tok = tokenizer(BASE_TOKENIZER)
        f = s.format_request(s.build_request(example('geography-replace-0003.json')), 'fewshot', tok)
        self.assertNotIn('<|im_start|>', f['prompt'])
        self.assertTrue(f['prompt'].endswith('Answer:'))
        # the methods join prompt and target with a space: " Sydney"
        self.assertEqual(tok(f['prompt'] + ' ' + f['target_new'])['input_ids'][-1:],
                         tok(' Sydney', add_special_tokens=False)['input_ids'][-1:])

    def test_every_record_keeps_its_subject_once(self):
        """Formatting never breaks a record whose bare question has the
        subject once. Known exception: Llama 3.1's template writes "Today
        Date: 26 Jul 2024", which holds mathematics-insert-0006's subject
        "6"; check_request reports it (SubjectNotInPrompt)."""
        if not os.path.isdir(RECORDS):
            self.skipTest('no records')
        reqs = [s.build_request(r) for r in s.load_records(RECORDS)]
        known = {('Llama-3.1-8B-Instruct', 'mathematics-insert-0006')}
        for name, fmt in [(n, 'chat') for n in CHAT_TOKENIZERS] + [(BASE_TOKENIZER, 'fewshot')]:
            tok = tokenizer(name)
            broken = set()
            for r in reqs:
                if r['prompt'].count(r['subject']) == 1:
                    f = s.format_request(r, fmt, tok)
                    if f['prompt'].count(f['subject']) != 1:
                        broken.add((name, r['sids']['id']))
            with self.subTest(model=name):
                self.assertEqual(broken - known, set())


if __name__ == '__main__':
    unittest.main()
