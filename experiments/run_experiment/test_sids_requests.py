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


if __name__ == '__main__':
    unittest.main()
