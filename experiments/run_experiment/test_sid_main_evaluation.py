"""The main experiments' evaluation of Sid's Dataset (sid_main_evaluation.py) on CPU, with a fake judge."""
import copy
import json
import os
import tempfile
import unittest

import sid_evaluation as S
import sid_main_evaluation as M
from evaluation_config import parse_modes, resolve_modes
from test_sid_evaluation import DELETE, REPLACE, STEP0, STEP1, FakeJudge, norm, payload, records

J = S.J


class FakeMainJudge(FakeJudge):
    """FakeJudge plus the reasoning judge: CORRECT when the reasoning's
    final answer is the reference answer, else MISSED_EDIT at step 1."""

    def __init__(self):
        super().__init__()
        self.reasoning_items = []

    def label_reasoning(self, items):
        self.reasoning_items += items
        out = []
        for item in items:
            answer, _ = M.final_answer(item['reasoning'])
            ok = norm(answer) == norm(item['answer'])
            out.append({'label': 'CORRECT' if ok else 'MISSED_EDIT', 'reason': 'fake', 'step': 0 if ok else 1})
        return out


# Extra probes' answers per step: hinted ones are the short answer, reasoning
# ones the whole generation.
PROBES0 = {
    REPLACE: {'hinted:derived[1]': 'the Australian Capital Territory',
              'reasoning:derived[0]': 'Facts: Canberra is the capital.\nAnswer: yes',
              'reasoning:derived[1]': 'Canberra is in the ACT.\nAnswer: the Australian Capital Territory'},
    DELETE: {'hinted:derived[1]': '10 a.m.'},
}
PROBES1 = {
    REPLACE: {'hinted:derived[1]': 'New South Wales',
              'reasoning:derived[0]': 'Facts: the capital of Australia is Sydney.\nSo Canberra is not.\nAnswer: no',
              'reasoning:derived[1]': 'The capital is Canberra, in Victoria.\nAnswer: Victoria'},
    DELETE: {'hinted:derived[1]': '10 a.m.'},
}


def probe_payload(step, answers, recs):
    """collect_probes with a generator that answers from `answers`."""
    by_prompt = {}
    for rid, keyed in answers.items():
        for key, kind, _, question in M.record_probes(recs[rid]):
            prompt = (M.render_reasoning(question, 'fewshot') if kind == 'reasoning'
                      else S.sids_requests.render_prompt(question, 'fewshot'))
            by_prompt[prompt] = keyed[key]
    calls = []

    def generate(prompts, long):
        calls.append(long)
        return [(by_prompt[p], by_prompt[p]) for p in prompts]

    requests = [{'sids': {'id': rid}} for rid in answers]
    return M.collect_probes(requests, recs, 'fewshot', None, generate, step), calls


class HelperTests(unittest.TestCase):
    def test_final_answer(self):
        self.assertEqual(M.final_answer('Facts: x\nSo y.\nAnswer: Sydney'), ('Sydney', True))
        self.assertEqual(M.final_answer('**Final answer:** New South Wales'), ('New South Wales', True))
        self.assertEqual(M.final_answer('Answer: A\nmore\nAnswer: B'), ('B', True))
        self.assertEqual(M.final_answer('I think it is Sydney.\n'), ('I think it is Sydney.', False))
        self.assertEqual(M.final_answer(''), ('', False))

    def test_hint_question_never_holds_the_edit(self):
        recs = records()
        for rid in (REPLACE, DELETE):
            edit = recs[rid]['edit']['statement']
            for key, kind, base, question in M.record_probes(recs[rid]):
                self.assertNotIn(edit, question)
        self.assertIsNone(M.hint_question([], 'Q?'))
        rec = copy.deepcopy(recs[REPLACE])
        rec['queries']['derived'][1]['bridge_in_prompt'] = True  # the question states it: no hint
        self.assertNotIn('hinted:derived[1]', [k for k, *_ in M.record_probes(rec)])
        self.assertEqual(M.premises_in_prompt({REPLACE: rec}), {(REPLACE, 'derived[1]')})
        self.assertEqual(M.hint_question(['A is B.', ' '], 'Q?'), 'A is B. Q?')

    def test_record_probes(self):
        recs = records()
        self.assertEqual([k for k, *_ in M.record_probes(recs[REPLACE])],
                         ['reasoning:derived[0]', 'hinted:derived[1]', 'reasoning:derived[1]'])
        # delete: hinted only (no chain reasons to "does not know"); no world queries
        self.assertEqual([k for k, *_ in M.record_probes(recs[DELETE])], ['hinted:derived[1]'])

    def test_reasoning_prompt_drops_the_short_answer_instruction(self):
        text = M.render_reasoning('Q?', 'fewshot')
        self.assertIn(M.REASONING_INSTRUCTION, text)
        self.assertNotIn(S.sids_requests.CHAT_INSTRUCTION, text)

    def test_probe_steps(self):
        self.assertTrue(M.probe_steps_wanted(0, 10, None))
        self.assertTrue(M.probe_steps_wanted(10, 10, None))
        self.assertFalse(M.probe_steps_wanted(5, 10, None))
        self.assertTrue(M.probe_steps_wanted(5, 10, 'sequential'))

    def test_modes(self):
        self.assertEqual(resolve_modes(parse_modes('sid_main'), True)[0], ['sid', 'sid_main'])
        self.assertEqual(resolve_modes(parse_modes('auto'), True)[0], ['sid'])
        with self.assertRaises(ValueError):
            resolve_modes(parse_modes('sid_main'), False)

    def test_collect_probes_asks_reasoning_long(self):
        p, calls = probe_payload(1, PROBES1, records())
        self.assertEqual(calls, [False, True])
        rep = next(e for e in p['records'] if e['record_id'] == REPLACE)['probes']
        self.assertEqual(rep['reasoning:derived[1]']['response'], 'Victoria')
        self.assertTrue(rep['reasoning:derived[1]']['final_found'])
        self.assertIn('Victoria', rep['reasoning:derived[1]']['reasoning'])


class MainFinalizeTests(unittest.TestCase):
    def run_main(self, step1=STEP1, probes0=PROBES0, probes1=PROBES1, step0=STEP0):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        run_dir = self.tmp.name
        os.makedirs(os.path.join(run_dir, 'samples'))
        recs = records()
        for step, answers, probes in ((0, step0, probes0), (1, step1, probes1)):
            with open(S.sample_path(run_dir, step), 'w') as f:
                json.dump(payload(step, answers, recs), f)
            with open(M.sample_path(run_dir, step), 'w') as f:
                json.dump(probe_payload(step, probes, recs)[0], f)
        ckpt = os.path.join(run_dir, 'checkpoints.jsonl')
        with open(ckpt, 'w') as f:
            for step in (0, 1):
                f.write(json.dumps({'step': step, 'edit_succ': None, 'evaluations': {}}) + '\n')
        judge = FakeMainJudge()
        S.finalize(run_dir, ckpt, recs, judge, salt='m', judge_check=False)
        final, info = M.finalize(run_dir, ckpt, recs, judge, salt='m')
        with open(ckpt) as f:
            rows = [json.loads(l) for l in f]
        return final, info, rows

    def test_portability_is_determinate_only(self):
        final, _, _ = self.run_main()
        p = final['metrics']['portability']
        # replace derived[0] pass, derived[1] fail; delete derived[0] abstains (pass), derived[1] fails
        self.assertEqual((p['pass'], p['scored']), (2, 4))
        # every one was answered with the original at step 0, so known = all
        self.assertEqual((p['known']['pass'], p['known']['scored']), (2, 4))
        self.assertEqual(final['portability'], p['known']['score'])
        self.assertEqual(final['portability'], 50.0)

    def test_portability_headline_is_the_known_subset(self):
        step1 = copy.deepcopy(STEP1)
        step0 = copy.deepcopy(STEP0)
        step0[REPLACE]['derived[0]'] = 'no'  # already "right" before the edit: not known
        final = self.run_main(step1, step0=step0)[0]
        p = final['metrics']['portability']
        self.assertEqual((p['known']['pass'], p['known']['scored']), (1, 3))
        self.assertEqual(final['portability'], round(100 / 3, 4))

    def test_indeterminate_change_rates(self):
        final, _, _ = self.run_main()
        ind = final['metrics']['indeterminate']
        # replace: Sydney x2 (worlds w2/w4 and w2/w3); delete: abstains where a world is null
        self.assertEqual(ind['counts'], {'unchanged': 0, 'changed_to_world': 4, 'changed_other': 0})
        self.assertEqual(ind['changed'], 100.0)
        self.assertEqual(ind['records'], {'one_world': 1, 'mixed': 1})

    def test_unchanged_fits_a_world_after_propagating(self):
        step1 = copy.deepcopy(STEP1)
        step1[REPLACE].update({'derived[1]': 'New South Wales', 'derived[2]': 'Canberra', 'derived[3]': 'Canberra'})
        ind = self.run_main(step1)[0]['metrics']['indeterminate']
        self.assertEqual(ind['counts']['unchanged'], 2)
        self.assertEqual(ind['unchanged_diagnosis']['fits_world_propagated'], 2)
        self.assertEqual(ind['known']['counts']['unchanged'], 2)  # step 0 answered Canberra

    def test_unchanged_without_propagation(self):
        step1 = copy.deepcopy(STEP1)
        step1[REPLACE].update({'derived[2]': 'Canberra', 'derived[3]': 'Canberra'})  # derived[1] still fails
        diag = self.run_main(step1)[0]['metrics']['indeterminate']['unchanged_diagnosis']
        self.assertEqual(diag['fits_world_not_propagated'], 2)

    def test_unchanged_in_mixed_worlds(self):
        step1 = copy.deepcopy(STEP1)
        step1[REPLACE].update({'derived[2]': 'Canberra', 'derived[3]': 'Melbourne'})
        ind = self.run_main(step1)[0]['metrics']['indeterminate']
        self.assertEqual(ind['counts']['changed_other'], 1)
        self.assertEqual(ind['unchanged_diagnosis']['mixed_worlds'], 1)

    def test_hinted_split(self):
        h = self.run_main()[0]['metrics']['hinted']
        # replace derived[1]: plain Tasmania fails, hinted NSW passes -> retrieval;
        # delete derived[1]: both keep 10 a.m. -> not integrated
        self.assertEqual(h['diagnosis']['retrieval'], 1)
        self.assertEqual(h['diagnosis']['not_integrated'], 1)
        self.assertEqual(h['control_leak']['leaked'], 0)

    def test_hint_leak_control(self):
        probes0 = copy.deepcopy(PROBES0)
        probes0[REPLACE]['hinted:derived[1]'] = 'New South Wales'  # the hint alone gives it away before the edit
        h = self.run_main(probes0=probes0)[0]['metrics']['hinted']
        self.assertEqual(h['control_leak']['leaked'], 1)
        self.assertEqual(h['diagnosis']['hint_leak'], 1)
        self.assertEqual(h['diagnosis']['retrieval'], 0)

    def test_reasoning(self):
        final, info, _ = self.run_main()
        r = final['metrics']['reasoning']
        self.assertEqual((r['pass'], r['scored']), (1, 2))  # no passes, Victoria fails
        self.assertEqual(r['traces']['CORRECT'], 1)
        self.assertEqual(r['traces']['MISSED_EDIT'], 1)
        self.assertEqual(r['first_wrong_step'], {'1': 1})
        self.assertEqual(info['probe_steps'], [0, 1])

    def test_checkpoints_and_headline(self):
        final, _, rows = self.run_main()
        last = rows[-1]
        self.assertEqual(last['headline_evaluation'], 'sid_main')
        self.assertEqual(last['portability'], 50.0)
        self.assertIn('sid', last['evaluations'])  # the sid evaluation stays beside it
        self.assertNotEqual(last['evaluations']['sid']['portability'], last['portability'])
        self.assertEqual(final['edit_succ'], last['evaluations']['sid']['edit_succ'])


if __name__ == '__main__':
    unittest.main()
