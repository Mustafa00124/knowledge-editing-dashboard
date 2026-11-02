"""Sid's Dataset's own evaluation (sid_evaluation.py) on CPU, with a fake judge."""
import contextlib
import copy
import io
import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import sid_evaluation as S
import sids_requests
from evaluation_config import parse_modes, resolve_modes

J = S.J
EXAMPLES = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'datasets', 'SidsDataset', 'examples')


def example(name):
    with open(os.path.join(EXAMPLES, name)) as f:
        return json.load(f)


def norm(text):
    return ' '.join(str(text).lower().strip(' .').split())


class FakeJudge:
    """Labels by exact (normalised) match against the candidates the real
    judge would be shown, through judge.answer_prompt, so the letter
    mapping and the candidate choice are the real ones."""

    def __init__(self):
        self.answer_items, self.locality_items = [], []

    def label_answers(self, items, salt=''):
        self.answer_items += items
        out = []
        for query, response in items:
            _, sides, values = J.answer_prompt(query, response, salt)
            if norm(response) in ("i don't know", 'unknown'):
                out.append({'label': 'NONE', 'reason': 'fake'})
                continue
            letter = next((l for l, v in values.items() if norm(v) == norm(response)), None)
            out.append(J.answer_label(json.dumps({'reason': 'fake', 'label': letter or 'OTHER'}), sides, values))
        return out

    def label_locality(self, items):
        self.locality_items += items
        return [{'label': 'SAME' if norm(b) == norm(a) else 'DIFFERENT', 'reason': 'fake'} for _, b, a in items]


REPLACE, DELETE = 'geography-replace-0003', 'geography-delete-0004'
STEP0 = {
    REPLACE: {'direct': 'Canberra', 'paraphrase': 'Canberra', 'cross_lingual[zh]': '堪培拉', 'cross_lingual[es]': 'Canberra',
              'propositional[0]': 'Yes', 'propositional[1]': 'No', 'unrelated_near[0]': 'X', 'unrelated_far[0]': 'Y',
              'derived[0]': 'yes', 'derived[1]': 'the Australian Capital Territory', 'derived[2]': 'Canberra',
              'derived[3]': 'Canberra'},
    DELETE: {'direct': 'the Pacific Time Zone', 'paraphrase': 'the Pacific Time Zone', 'cross_lingual[zh]': '太平洋时区',
             'cross_lingual[es]': 'Madrid', 'propositional[0]': 'No', 'propositional[1]': 'Yes',
             'unrelated_near[0]': 'P', 'unrelated_far[0]': 'Q', 'derived[0]': 'the Pacific Time Zone',
             'derived[1]': '10 a.m.', 'derived[2]': 'the Pacific Time Zone', 'derived[3]': 'yes'},
}
STEP1 = {
    REPLACE: {'direct': 'Sydney', 'paraphrase': 'Canberra', 'cross_lingual[zh]': '悉尼', 'cross_lingual[es]': 'Madrid',
              'propositional[0]': 'No', 'propositional[1]': 'No', 'unrelated_near[0]': 'X', 'unrelated_far[0]': 'Z',
              'derived[0]': 'no', 'derived[1]': 'Tasmania', 'derived[2]': 'Sydney', 'derived[3]': 'Sydney'},
    DELETE: {'direct': "I don't know", 'paraphrase': 'the Pacific Time Zone', 'cross_lingual[zh]': "I don't know",
             'cross_lingual[es]': "I don't know", 'propositional[0]': "I don't know", 'propositional[1]': 'Yes',
             'unrelated_near[0]': 'P', 'unrelated_far[0]': 'Q', 'derived[0]': "I don't know", 'derived[1]': '10 a.m.',
             'derived[2]': "I don't know", 'derived[3]': "I don't know"},
}


def records():
    return {r['id']: r for r in (example(REPLACE + '.json'), example(DELETE + '.json'))}


def payload(step, answers, recs):
    return {'step': step, 'prompt_format': 'fewshot', 'evaluation': 'sid', 'judged': False,
            'records': [{'record_id': rid, 'case_id': i, 'edit_operation': recs[rid]['edit_operation'],
                         'box': recs[rid]['box'], 'topic': recs[rid]['topic'],
                         'queries': {q['key']: {'query_type': q['query_type'], 'language': q['language'],
                                                'question': q['question'], 'response': answers[rid][q['key']],
                                                'raw': answers[rid][q['key']]}
                                     for q in S.record_queries(recs[rid])}}
                        for i, rid in enumerate(answers)]}


class FinalizeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.run_dir = self.tmp.name
        os.makedirs(os.path.join(self.run_dir, 'samples'))
        self.recs = records()
        for step, answers in ((0, STEP0), (1, STEP1)):
            with open(S.sample_path(self.run_dir, step), 'w') as f:
                json.dump(payload(step, answers, self.recs), f)
        self.ckpt = os.path.join(self.run_dir, 'checkpoints.jsonl')
        with open(self.ckpt, 'w') as f:
            for step in (0, 1):
                f.write(json.dumps({'step': step, 'edit_succ': None, 'evaluations': {}}) + '\n')
        self.judge = FakeJudge()
        self.final, self.info = S.finalize(self.run_dir, self.ckpt, self.recs, self.judge, salt='m', judge_check=False)
        self.m = self.final['metrics']

    def tearDown(self):
        self.tmp.cleanup()

    def test_reliability_and_headline(self):
        # replace: Sydney pass, Canberra fail; delete: abstain pass, original fail
        self.assertEqual(self.m['reliability']['pass'], 2)
        self.assertEqual(self.m['reliability']['scored'], 4)
        self.assertEqual(self.final['edit_succ'], 50.0)
        self.assertEqual(self.final['portability'], self.m['generalization']['score'])

    def test_rewrite_is_the_direct_question_alone(self):
        rw, pa, rel = self.m['rewrite'], self.m['paraphrase'], self.m['reliability']
        self.assertEqual(rw['scored'] + pa['scored'], rel['scored'])
        self.assertEqual(rw['pass'] + pa['pass'], rel['pass'])
        self.assertEqual(rw['scored'], 2)  # one direct question per record (a replace and a delete)

    def test_cross_lingual_per_language(self):
        by = self.m['cross_lingual']['by_language']
        self.assertEqual((by['zh']['pass'], by['zh']['scored']), (2, 2))
        self.assertEqual((by['es']['pass'], by['es']['scored']), (1, 2))

    def test_delete_abstention(self):
        d = self.m['delete_abstention']
        self.assertEqual((d['pass'], d['scored']), (3, 4))  # direct, zh, es abstain; paraphrase keeps the fact
        # The judge never saw "I don't know" as a candidate: only the original.
        for query, _ in self.judge.answer_items:
            self.assertNotEqual(norm(query.get('new_answer') or ''), "i don't know")

    def test_propositional_logical_consistency(self):
        lc = self.m['logical_consistency']
        # replace: not -> No (pass), and -> No (original, fail); delete: not abstains (pass), or -> Yes (fail)
        self.assertEqual((lc['pass'], lc['scored']), (2, 4))
        self.assertEqual(lc['by_form']['not']['pass'], 2)
        self.assertEqual(lc['by_form']['and']['pass'], 0)

    def test_locality_against_the_models_own_pre_edit_answer(self):
        loc = self.m['locality']
        self.assertEqual((loc['near']['pass'], loc['far']['pass']), (2, 1))  # replace far: Y -> Z
        self.assertEqual(self.final['locality'], 75.0)
        befores = {(q, b) for q, b, _ in self.judge.locality_items}
        self.assertTrue(all(b in ('X', 'Y', 'P', 'Q') for _, b in befores))
        # step 0 is SAME by definition, without a judge call
        step0 = json.load(open(S.sample_path(self.run_dir, 0)))
        self.assertEqual(step0['metrics']['locality'], 100.0)

    def test_worlds(self):
        g = self.m['generalization']
        ind = g['indeterminate']
        self.assertEqual((ind['pass'], ind['scored']), (4, 4))
        det = g['determinate']
        # replace: derived[0] no (pass), derived[1] Tasmania (fail); delete: abstain (pass), 10 a.m. (fail)
        self.assertEqual((det['pass'], det['scored']), (2, 4))
        self.assertEqual(set(g['by_problem']), {'determinate', 'background_beliefs', 'derived_beliefs'})
        self.assertEqual(set(g['by_logic']), {'dl', 'fol'})
        worlds = g['worlds']
        # replace: Sydney -> {w2, w4} and {w2, w3}: agree on w2. delete: abstain -> {w2} and {w1}: mixed.
        self.assertEqual((worlds['records_consistent'], worlds['records_mixed']), (1, 1))
        step1 = json.load(open(S.sample_path(self.run_dir, 1)))
        rep = next(e for e in step1['records'] if e['record_id'] == REPLACE)
        self.assertEqual(rep['queries']['derived[2]']['worlds'], ['w2', 'w4'])
        dele = next(e for e in step1['records'] if e['record_id'] == DELETE)
        self.assertEqual(dele['queries']['derived[2]']['worlds'], ['w2'])

    def test_original_answer_matching_a_world_passes(self):
        q = next(q for q in S.record_queries(self.recs[REPLACE]) if q['key'] == 'derived[2]')
        v = FakeJudge().label_answers([(S.judge_query(q), 'Canberra')])[0]
        self.assertEqual(v['label'], 'ORIGINAL')
        self.assertEqual(S.score_answer(q, v, 'replace'), (1, ['w1', 'w3']))
        self.assertEqual(S.score_answer(q, {'label': 'OTHER'}, 'replace'), (0, []))
        self.assertEqual(S.score_answer(q, {'label': 'UNCLEAR'}, 'replace'), (None, None))

    def test_known_tally_uses_step0(self):
        # Step 0 got the original everywhere except delete es (Madrid).
        cl = self.m['cross_lingual']
        self.assertEqual(cl['known']['total'], 3)

    def test_checkpoints_get_the_sid_evaluation(self):
        rows = [json.loads(l) for l in open(self.ckpt)]
        self.assertEqual([r['headline_evaluation'] for r in rows], ['sid', 'sid'])
        self.assertEqual(rows[1]['evaluations']['sid']['edit_succ'], 50.0)
        self.assertEqual(rows[1]['edit_succ'], 50.0)
        self.assertEqual(rows[0]['edit_succ'], 0.0)  # pre-edit: nothing gives the new answer
        self.assertIsNotNone(rows[1]['fluency'])
        self.assertEqual(self.info['steps'], [0, 1])

    def test_identical_answers_are_judged_once(self):
        keys = {(json.dumps(q, sort_keys=True), r) for q, r in self.judge.answer_items}
        self.assertEqual(len(keys), len(self.judge.answer_items))

    def test_grouped_pools_steps_after_zero(self):
        final, _ = S.finalize(self.run_dir, self.ckpt, self.recs, FakeJudge(), grouped=True, judge_check=False)
        self.assertEqual(final['metrics']['reliability']['scored'], 4)


class GenerationTests(unittest.TestCase):
    def test_prompts_and_keys_match_the_edit_and_the_audit(self):
        recs = records()
        seen = []

        def generate(prompts):
            seen.extend(prompts)
            return [(f'a{i}', f'a{i}\nQuestion: next') for i in range(len(prompts))]

        reqs = [{'sids': {'id': REPLACE}}]
        p = S.collect_generations(reqs, recs, 'fewshot', None, generate, step=3, case_offset=5)
        entry = p['records'][0]
        self.assertEqual(entry['case_id'], 5)
        self.assertEqual(list(entry['queries']), [k for k, *_ in S.AQ.all_queries(recs[REPLACE])])
        self.assertEqual(seen[0], sids_requests.render_prompt(recs[REPLACE]['queries']['direct']['prompt'], 'fewshot'))
        built = sids_requests.format_request(sids_requests.build_request(recs[REPLACE]), 'fewshot')
        self.assertEqual(seen[0], built['prompt'])
        self.assertIn(built['portability']['derived_2']['prompt'], seen)

    def test_answer_one_path_cleans_like_the_audit(self):
        recs = records()
        p = S.collect_generations([{'sids': {'id': DELETE}}], recs, 'fewshot', None, None, 0,
                                  answer_one=lambda req, prompt: ' Seattle\nQuestion: more')
        self.assertEqual(p['records'][0]['queries']['direct']['response'], 'Seattle')

    def test_ngram_entropy(self):
        self.assertIsNone(S.ngram_entropy('one'))
        self.assertGreater(S.ngram_entropy('a b c d e f'), S.ngram_entropy('a b a b a b'))


class ModeTests(unittest.TestCase):
    def test_sids_always_scored_by_sid(self):
        self.assertEqual(resolve_modes(parse_modes('auto'), True)[0], ['sid'])
        modes, note = resolve_modes(parse_modes('original'), True)
        self.assertEqual(modes, ['sid'])  # EasyEdit's original never runs on Sid's records
        self.assertIn('original', note)
        self.assertEqual(resolve_modes(parse_modes('original,exact_match'), True)[0], ['sid', 'exact_match'])

    def test_other_datasets_keep_their_default(self):
        self.assertEqual(resolve_modes(parse_modes('auto'), False)[0], ['original'])
        self.assertEqual(resolve_modes(parse_modes('original,bertscore'), False)[0], ['original', 'bertscore'])
        with self.assertRaises(ValueError):
            resolve_modes(parse_modes('sid'), False)


class RunnerTests(unittest.TestCase):
    """run_experiment.main on two Sid's Dataset records with fake editing,
    generation and judge: original is not run, sid is."""

    def test_runner_scores_sids_runs_with_sid(self):
        import torch
        import run_experiment as runner

        recs = records()
        requests = [sids_requests.build_request(r) for r in recs.values()]
        model = Mock(training=False)
        model.to.return_value = model
        tok = Mock(pad_token='pad', eos_token='eos', eos_token_id=0, padding_side='right')
        hp = types.SimpleNamespace(device=0, model_name='fake', layers=[0], num_steps=1,
                                   objective_optimization='target_new')
        hp.to_dict = lambda: {'model_name': 'fake', 'device': 0}
        hparams_module = types.ModuleType('easyeditor.models.ft.ft_hparams')
        hparams_module.FTHyperParams = Mock()
        hparams_module.FTHyperParams.from_hparams.return_value = hp
        eval_module = types.ModuleType('eval_utils')
        eval_module.load_requests = Mock(return_value=requests)
        eval_module.evaluate_requests = Mock(side_effect=AssertionError('original mode ran on Sid\'s Dataset'))
        eval_module.aggregate_metrics = Mock()
        eval_module.memory_snapshot = lambda _: {}
        eval_module.sample_generations = Mock(return_value=[])
        training = types.ModuleType('checkpointed_ft')
        calls = {'n': 0}

        def edit(model, tok, reqs, hp, interval, checkpoint):
            checkpoint(0, None)
            calls['n'] += 1
            checkpoint(1, 0.1)
        training.execute_ft_checkpointed = Mock(side_effect=edit)
        samples = types.ModuleType('response_samples')
        samples.method_samples = Mock(return_value=[])
        answers = [STEP0, STEP1]

        def fake_generate(model, tok, prompts, device, fmt):
            table = answers[calls['n']]
            out = []
            for prompt in prompts:
                hit = None
                for rid, rec in recs.items():
                    for q in S.record_queries(rec):
                        if sids_requests.render_prompt(q['question'], fmt) == prompt:
                            hit = table[rid][q['key']]
                out.append((hit, hit))
            return out

        modules = {'eval_utils': eval_module, 'easyeditor.models.ft.ft_hparams': hparams_module,
                   'checkpointed_ft': training, 'response_samples': samples}
        judge = FakeJudge()
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp) / 'SidsDataset' / 'records' / 'geography'
            for rid, rec in recs.items():
                (data / rec['edit_operation']).mkdir(parents=True, exist_ok=True)
                (data / rec['edit_operation'] / f'{rid}.json').write_text(json.dumps(rec))
            out = Path(tmp) / 'out'
            with patch.dict(sys.modules, modules), \
                 patch.object(runner.AutoModelForCausalLM, 'from_pretrained', return_value=model), \
                 patch.object(runner.AutoTokenizer, 'from_pretrained', return_value=tok), \
                 patch.object(S, 'generate_answers', side_effect=fake_generate), \
                 patch.object(S, 'load_judge', return_value=judge), \
                 patch.object(S.J, 'self_check', return_value={'agree': 60, 'total': 60}), \
                 patch.object(torch.cuda, 'empty_cache'), \
                 patch.object(sys, 'argv', ['run_experiment.py', '--split', 'all', '--method', 'ft',
                                            '--model', 'gpt-j-6b', '--data_path', str(Path(tmp) / 'SidsDataset'),
                                            '--evaluation_modes', 'original', '--out_root', str(out),
                                            '--run_name', 'test', '--ds_size', '2', '--num_steps', '1',
                                            '--checkpoint_every', '1', '--sample_every', '1',
                                            '--fluency_every', '1']), \
                 contextlib.redirect_stdout(io.StringIO()):
                runner.main()
            path = out / 'runs' / 'test'
            summary = json.loads((path / 'summary.json').read_text())
            rows = [json.loads(l) for l in (path / 'checkpoints.jsonl').read_text().splitlines()]
            self.assertEqual(summary['evaluation_modes'], ['sid'])
            eval_module.evaluate_requests.assert_not_called()
            self.assertEqual(set(summary['evaluations']), {'sid'})
            self.assertEqual(summary['edit_succ'], 50.0)
            self.assertEqual(summary['headline_evaluation'], 'sid')
            self.assertEqual(summary['sid_evaluation']['judge_check'], {'agree': 60, 'total': 60})
            self.assertEqual(summary['evaluations']['sid']['metrics']['generalization']['worlds']['records_mixed'], 1)
            self.assertEqual([r['step'] for r in rows], [0, 1])
            self.assertTrue(all('sid' in r['evaluations'] for r in rows))
            self.assertTrue((path / 'samples' / 'sid_step_000001.json').exists())
            self.assertEqual(summary['sids_prompt_format'], 'fewshot')


if __name__ == '__main__':
    unittest.main()
