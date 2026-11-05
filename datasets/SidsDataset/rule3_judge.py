#!/usr/bin/env python3
"""The LLM judge's part of CRITERIA.md Rule 3 (stable subjects, self-contained
statements): what pattern matching in criteria.py can't catch.

Per record (the items come from criteria.rule3_judge_items, so the report and
the judge agree on what was judged):
  subject     ABox/TBox: does the subject describe the value being edited, so
              that it moves with the edit? (MOVES / STABLE)
  standalone  each statement and prompt: does it make sense on its own, or
              lean on something unstated ("under those conditions", "the
              specified", a pronoun with nothing to refer to)? (DEPENDS / STANDALONE)
  giveaway    each question with a non-yes/no answer: does the question, or a
              name in it (in any language), give its answer away? (GIVES_AWAY / FINE)

Labels are cached in rule3_judge.json by record id and a hash of the record's
items (criteria.rule3_judge_hash); criteria.py reads the cache and reports
records whose hash changed, or that were never judged, as pending. Only those
are judged again unless --all is given.

Runs the project's judge model (experiments/sid_eval, Qwen3-4B-Instruct-2507)
on a GPU, through SLURM, from the project root:

    sbatch datasets/SidsDataset/rule3_judge.sbatch
    venvs/easyedit_venv/bin/python datasets/SidsDataset/rule3_judge.py --dry-run   # counts only, no model
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
import criteria as C  # noqa: E402

LABELS = {'subject': ('STABLE', 'MOVES'), 'standalone': ('STANDALONE', 'DEPENDS'), 'giveaway': ('FINE', 'GIVES_AWAY')}
REPLY = 'Reply with one line of JSON and nothing else: {"reason": "<at most 20 words>", "label": "<one label>"}'

SYSTEMS = {
    'subject': """You check one thing about an edit to a fact: whether the edit's subject is a description of the very value the edit changes. If it is, the subject means one thing before the edit and another after it, so questions about the subject test nothing stable.

You read the edit (the new statement), the original statement, the subject, and the old and new values.

MOVES: the subject picks out its referent through the value being edited, so the edit changes what the subject refers to. Example: "The volcano that destroyed Pompeii is Etna" (was Vesuvius): "the volcano that destroyed Pompeii" meant Vesuvius and now means Etna.
STABLE: the subject is a named thing or class, or a description of something the edit does not change, even if the description is long or mentions other things.

Never judge whether the edit is true. """ + REPLY,
    'standalone': """You check whether a sentence from a dataset makes sense on its own, read with no other text around it. The sentence may be false, surprising or about made-up things: that is fine. It may state facts and then ask a question: that is fine.

DEPENDS: the sentence leans on context it does not give: it refers to "those conditions", "the specified" thing, something "as stated" or "above", "the edit" or "the change", or uses a pronoun or "it"/"that" with nothing in the sentence to refer to.
STANDALONE: a reader with no other context knows what it says or asks.

Never judge whether the sentence is true. """ + REPLY,
    'giveaway': """You check whether a question gives its own answer away. You read the question, its expected answers, and (when given) an edit the question is about. Never judge whether the answers are true.

GIVES_AWAY: the answer can be read off the question's words without knowing the fact: the question contains the answer, or a name in it (in any language) contains or spells out the answer, or it names the edit's new value in a way that hands over the answer.
FINE: answering needs knowledge of the fact. A question that offers the options ("northern or southern?") is FINE. Stating a fact in the question and asking about something else that follows from it is FINE. Naming a thing in order to ask about one of its properties is FINE.

""" + REPLY,
}

SHOTS = {
    'subject': [
        ({'edit': 'The volcano that destroyed Pompeii is Etna.', 'original': 'The volcano that destroyed Pompeii is Vesuvius.',
          'subject': 'the volcano that destroyed Pompeii', 'old_value': 'Vesuvius', 'new_value': 'Etna'},
         {'reason': 'The subject is defined by the edited value, so it means Etna after the edit.', 'label': 'MOVES'}),
        ({'edit': 'Pompeii was destroyed by Etna.', 'original': 'Pompeii was destroyed by Vesuvius.',
          'subject': 'Pompeii', 'old_value': 'Vesuvius', 'new_value': 'Etna'},
         {'reason': 'A named city; the edit does not change what it refers to.', 'label': 'STABLE'}),
        ({'edit': "Franklin D. Roosevelt's successor succeeded Woodrow Wilson.",
          'original': "Franklin D. Roosevelt's successor succeeded Franklin D. Roosevelt.",
          'subject': "Franklin D. Roosevelt's successor", 'old_value': 'Franklin D. Roosevelt', 'new_value': 'Woodrow Wilson'},
         {'reason': 'The subject is described by the relation being edited.', 'label': 'MOVES'}),
        ({'edit': "Napoleon's final place of exile is Elba.", 'original': "Napoleon's final place of exile is Saint Helena.",
          'subject': "Napoleon's final place of exile", 'old_value': 'Saint Helena', 'new_value': 'Elba'},
         {'reason': 'The subject describes the place being edited, so it moves to Elba.', 'label': 'MOVES'}),
        ({'edit': 'The composer of the opera The Magic Flute was born in Vienna.',
          'original': 'The composer of the opera The Magic Flute was born in Salzburg.',
          'subject': 'the composer of the opera The Magic Flute', 'old_value': 'Salzburg', 'new_value': 'Vienna'},
         {'reason': 'Describes Mozart through his opera, which the birthplace edit does not change.', 'label': 'STABLE'}),
    ],
    'standalone': [
        ({'text': 'Under those conditions, which city is the Eiffel Tower in?'},
         {'reason': '"Those conditions" are not given.', 'label': 'DEPENDS'}),
        ({'text': 'France is in Europe. Which continent is Lyon in?'},
         {'reason': 'States a fact, then asks a clear question.', 'label': 'STANDALONE'}),
        ({'text': 'Given the specified change, where does the river end?'},
         {'reason': 'Refers to a "specified change" it does not state.', 'label': 'DEPENDS'}),
        ({'text': 'The Eiffel Tower is in Rome.'},
         {'reason': 'False but complete on its own.', 'label': 'STANDALONE'}),
        ({'text': 'After the edit, does it still flow into that sea?'},
         {'reason': 'Mentions the edit; "it" and "that sea" have no referent.', 'label': 'DEPENDS'}),
        ({'text': "'Borders' is asymmetric. France borders Spain. Does it follow that Spain does not border France?"},
         {'reason': 'Gives the premises the question needs.', 'label': 'STANDALONE'}),
    ],
    'giveaway': [
        ({'prompt': '土卫六围绕哪颗行星运行？', 'answers': ['土星'], 'edit': ''},
         {'reason': '土卫六 means "Saturn\'s sixth moon", naming the answer 土星.', 'label': 'GIVES_AWAY'}),
        ({'prompt': 'Which planet does Titan orbit?', 'answers': ['Saturn'], 'edit': ''},
         {'reason': 'The name Titan does not contain the answer.', 'label': 'FINE'}),
        ({'prompt': "Whom did Franklin D. Roosevelt's successor succeed?", 'answers': ['Franklin D. Roosevelt'], 'edit': ''},
         {'reason': 'The question names its own answer.', 'label': 'GIVES_AWAY'}),
        ({'prompt': 'In which hemisphere, northern or southern, did Napoleon Bonaparte die?',
          'answers': ['the Southern Hemisphere', 'the Northern Hemisphere'],
          'edit': 'Napoleon Bonaparte died in the Northern Hemisphere.'},
         {'reason': 'Offers both options; choosing needs the fact.', 'label': 'FINE'}),
        ({'prompt': 'The pelquon has a mass of 3.2 GeV/c². What is the mass of the zelthon?',
          'answers': ['3.2 GeV/c²'], 'edit': 'The zelthon is the antiparticle of the pelquon.'},
         {'reason': 'States a fact and asks what follows; needs the edit.', 'label': 'FINE'}),
        ({'prompt': 'Which museum, the Rome Eiffel Museum, is in the same city as the Eiffel Tower?',
          'answers': ['Rome'], 'edit': 'The Eiffel Tower is in Rome.'},
         {'reason': 'The museum name spells out the expected city.', 'label': 'GIVES_AWAY'}),
    ],
}


def user_text(task, item):
    if task == 'subject':
        return (f"Edit: {item['edit']}\nOriginal: {item['original'] or '(none: a new fact)'}\n"
                f"Subject: {item['subject']}\nOld value: {item['old_value'] or '(none)'}\nNew value: {item['new_value'] or '(none)'}")
    if task == 'standalone':
        return f"Sentence: {item['text']}"
    return (f"Question: {item['prompt']}\nExpected answers: {' | '.join(item['answers'])}"
            + (f"\nEdit: {item['edit']}" if item.get('edit') else ''))


def messages(task, item):
    out = [{'role': 'system', 'content': SYSTEMS[task]}]
    for shot, verdict in SHOTS[task]:
        out.append({'role': 'user', 'content': user_text(task, shot)})
        out.append({'role': 'assistant', 'content': json.dumps(verdict, ensure_ascii=False)})
    out.append({'role': 'user', 'content': user_text(task, item)})
    return out


def judge_input(task, item):
    """The item as the judge sees it (no key), for deduplication across records."""
    if task == 'subject':
        return {'edit': item['statement'], 'original': item['original'], 'subject': item['subject'],
                'old_value': item['old_value'], 'new_value': item['new_value']}
    return {k: v for k, v in item.items() if k not in ('task', 'key')}


def save(cache, path):
    cache['generated'] = time.strftime('%Y-%m-%d %H:%M:%S')
    tmp = Path(str(path) + '.tmp')
    tmp.write_text(json.dumps(cache, ensure_ascii=False, indent=1) + '\n')
    os.replace(tmp, path)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--all', action='store_true', help='judge every record, not only missing and changed ones')
    ap.add_argument('--records', help='comma-separated record ids (default: every record)')
    ap.add_argument('--limit', type=int, help='at most this many records (for a quick test)')
    ap.add_argument('--dry-run', action='store_true', help='count what would be judged; no model')
    ap.add_argument('--out', default=str(C.RULE3_JUDGE_PATH))
    ap.add_argument('--batch-size', type=int, default=32)
    args = ap.parse_args(argv)

    recs = C.load_records()
    if args.records:
        wanted = set(args.records.split(','))
        recs = [r for r in recs if r['id'] in wanted]
    cache = C.load_rule3_judge(args.out)
    cache.setdefault('records', {})
    todo = [r for r in recs if args.all or (cache['records'].get(r['id']) or {}).get('hash') != C.rule3_judge_hash(r)]
    if args.limit:
        todo = todo[:args.limit]
    work = {r['id']: C.rule3_judge_items(r) for r in todo}
    jobs = {}
    for items in work.values():
        for item in items:
            jobs.setdefault(json.dumps([item['task'], judge_input(item['task'], item)], ensure_ascii=False,
                                       sort_keys=True), item)
    by_task = {t: sum(k.startswith(f'["{t}"') for k in jobs) for t in LABELS}
    print(f'{len(todo)} of {len(recs)} records to judge: {len(jobs)} distinct items ({by_task})', flush=True)
    if args.dry_run or not jobs:
        return 0

    import torch
    sys.path.insert(0, str(PROJECT_ROOT / 'experiments' / 'run_experiment'))
    import sid_evaluation as SE
    J = SE.J
    judge = J.LocalJudge(SE.JUDGE_PATH, device='cuda' if torch.cuda.is_available() else 'cpu',
                         max_new_tokens=96, batch_size=args.batch_size)
    cache.update(judge_model=J.JUDGE_MODEL, version=C.RULE3_JUDGE_VERSION)
    keys = list(jobs)
    verdicts, t0, step = {}, time.time(), 512
    for i in range(0, len(keys), step):
        chunk = keys[i:i + step]
        replies = judge._generate([messages(jobs[k]['task'], judge_input(jobs[k]['task'], jobs[k])) for k in chunk])
        for k, reply in zip(chunk, replies):
            verdicts[k] = J.parse_verdict(reply, set(LABELS[jobs[k]['task']]))
        print(f'[{time.time() - t0:.0f}s] {min(i + step, len(keys))}/{len(keys)} items', flush=True)
        # Save every record whose items are all judged, so a stopped job keeps its work.
        for r in todo:
            items = work[r['id']]
            ks = [json.dumps([it['task'], judge_input(it['task'], it)], ensure_ascii=False, sort_keys=True)
                  for it in items]
            if r['id'] in cache['records'] and cache['records'][r['id']].get('hash') == C.rule3_judge_hash(r) \
                    and not args.all:
                continue
            if all(k in verdicts for k in ks):
                cache['records'][r['id']] = {
                    'hash': C.rule3_judge_hash(r), 'at': time.strftime('%Y-%m-%dT%H:%M:%S'),
                    'items': [{**{k: v for k, v in it.items() if k in ('task', 'key', 'text', 'prompt', 'subject')},
                               'label': verdicts[k]['label'], 'reason': verdicts[k].get('reason', '')}
                              for it, k in zip(items, ks)]}
        save(cache, args.out)
    flagged = sum(it['label'] == C.RULE3_FLAGS[it['task']] for e in cache['records'].values() for it in e['items'])
    unclear = sum(it['label'] == 'UNCLEAR' for e in cache['records'].values() for it in e['items'])
    print(f'done in {time.time() - t0:.0f}s: {flagged} items flagged, {unclear} unclear; {args.out}', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
