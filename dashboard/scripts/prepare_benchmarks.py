"""Build browse-only views from pinned, unmodified official benchmark releases.
Run from any directory with Python 3. Source files remain alongside the views.
The resulting views are not training datasets or experiment configurations.
"""
import collections
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'datasets'
CATALOG = {}
VIEWS = collections.defaultdict(list)

# Benchmark names on the command line limit the build to those (scripts/
# setup.py passes the one it just downloaded). A partial build writes only
# those views and leaves the frontend catalog, which describes every
# benchmark, untouched.
ONLY = set(sys.argv[1:])

def want(name):
    return not ONLY or name in ONLY

def read(name, path):
    return json.loads((DATA / name / path).read_text())

def field(label, value):
    return {'label': label, 'value': value}

def query(purpose, prompt, answer=None, **extra):
    return {'purpose': purpose, 'prompt': prompt, 'answer': answer, **extra}

def row(identifier, category, fields, queries, source, subject=None, note=''):
    return {'id': identifier, 'display': {'category': category, 'fields': fields,
        'queries': queries, 'subject': subject, 'note': note}, 'source_record': source}

def save(name, key, label, category, records, source_files, note=''):
    relative = 'views/' + key + '.json'
    path = DATA / name / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, ensure_ascii=False, separators=(',', ':')) + '\n')
    CATALOG.setdefault(name, []).append({'key': key, 'label': label, 'file': relative,
        'shape': 'standard', 'category': category, 'hasQueries': any(r['display']['queries'] for r in records),
        'recordCount': len(records), 'description': note})
    print(name, label, len(records), 'records', sum(len(r['display']['queries']) for r in records), 'queries')
    VIEWS[name].append({'path': relative, 'records': len(records), 'source_files': source_files,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})

# MQuAKE: a case is a group of edits; single-hop baselines are not locality tests.
if want('MQuAKE'):
    for filename, label in [('MQuAKE-CF-3k-v2.json','CF-3k v2'), ('MQuAKE-CF.json','CF full'), ('MQuAKE-T.json','Temporal')]:
        path = 'datasets/' + filename
        records = []
        for r in read('MQuAKE', path):
            fields, qs = [], []
            for i, edit in enumerate(r['requested_rewrite'], 1):
                prefix = f'Edit {i} · ' if len(r['requested_rewrite']) > 1 else ''
                prompt = edit['prompt'].replace('{}', edit['subject'])
                fields.extend([field(prefix+'Prompt', prompt), field(prefix+'Previous answer', edit['target_true']['str']), field(prefix+'New answer', edit['target_new']['str'])])
                qs.append(query('Edit success', edit.get('question', prompt), edit['target_new']['str']))
            for prompt in r['questions']:
                qs.append(query('Generalization · Multi-hop', prompt, [r['new_answer'], *r.get('new_answer_alias', [])], previousAnswer=r['answer']))
            for hop in r.get('new_single_hops', []):
                qs.append(query('Generalization · Post-edit single-hop', hop['question'], [hop['answer'], *hop.get('answer_alias', [])]))
            for hop in r.get('single_hops', []):
                qs.append(query('Baseline · Before editing', hop['question'], [hop['answer'], *hop.get('answer_alias', [])]))
            records.append(row(r['case_id'],'Replacement',fields,qs,r,note='All edits in this case are applied together. Baseline questions describe knowledge before editing.'))
        save('MQuAKE',filename[:-5],label,'Replacement',records,[path], 'The CF-3k v2 and CF full subsets overlap; temporal records are historical updates, not current facts.')

# RippleEdits: preserve complete statements rather than guessing answer spans.
if want('RippleEdits'):
    for key in ['recent','random','popular']:
        path = f'data/benchmark/{key}.json'
        records=[]
        category='Insertion' if key=='recent' else 'Replacement'
        for i,r in enumerate(read('RippleEdits',path)):
            old=r['edit'].get('original_fact')
            assert bool(old) == (category=='Replacement')
            fields=[]
            if old: fields.append(field('Previous fact',old['prompt']))
            fields.append(field('Fact to add' if not old else 'New fact',r['edit']['prompt']))
            qs=[]
            for metric, tests in r.items():
                if not isinstance(tests,list): continue
                purpose='Locality' if metric in ['Forgetfulness','Relation_Specificity','Relation_Specifity'] else 'Generalization'
                for test in tests:
                    conditions=[{'prompt':c['prompt'], 'answer':[[a['value'],*a.get('aliases',[])] for a in c['answers']]} for c in test.get('condition_queries',[])]
                    for q in test.get('test_queries',[]):
                        qs.append(query(purpose+' · '+metric.replace('_',' '),q['prompt'],[[a['value'],*a.get('aliases',[])] for a in q['answers']],conditions=conditions,conditionOperator=test.get('test_condition')))
            records.append(row(f'{key}:{i}',category,fields,qs,r,note='Forgetfulness checks preserve other values of a relation. Condition queries are prerequisites for the source evaluation.'))
        save('RippleEdits',key,key.title(),category,records,[path])

# TAXI: transpose pandas column JSON and join questions by the complete edit identity.
if want('TAXI'):
    def columns_to_rows(data):
        ids=list(next(iter(data.values())))
        assert all(list(v)==ids for v in data.values())
        return [dict(source_row_id=i, **{k:v[i] for k,v in data.items()}) for i in ids]

    def taxi_key(r):
        return tuple(r[k] for k in ['superordinate_category','subj','entity','orig_entity','token_type','edit_type'])

    def taxi_queries(r, baseline=False):
        kind='Baseline · Before editing' if baseline else 'Edit success' if r['property']=='category_membership' else 'Generalization' if r['answer_changed'] else 'Locality'
        subject=r['subj']
        return [
          query(kind+' · Forward · '+r['property'].replace('_',' '),r['query_fwd'].replace('<subj>',subject).replace('<answer>','____'),r['answer_fwd'],choices=r['fwd_choices'],previousAnswer=r.get('orig_answer_fwd')),
          query(kind+' · Reverse · '+r['property'].replace('_',' '),r['query_rev'].replace('<answer>',r['answer_fwd']).replace('<subj>','____'),subject,choices=r['rev_choices'])]

    edits=columns_to_rows(read('TAXI','datasets/edits.json'))
    evals=columns_to_rows(read('TAXI','datasets/edits-evaluation.json'))
    by_edit=collections.defaultdict(list)
    for r in evals: by_edit[taxi_key(r)].append(r)
    assert len({taxi_key(r) for r in edits})==len(edits)
    assert set(by_edit)=={taxi_key(r) for r in edits}
    for domain in sorted({r['superordinate_category'] for r in edits}):
        records=[]
        for r in edits:
            if r['superordinate_category']!=domain: continue
            tests=by_edit[taxi_key(r)]
            qs=[q for test in tests for q in taxi_queries(test)]
            records.append(row(r['source_row_id'],'Replacement',[
              field('Prompt',f"A {r['subj']} is a kind of"),field('Previous answer',r['orig_entity']),field('New answer',r['entity']),field('Subject typicality',r['token_type'])],qs,{'edit':r,'evaluation':tests},subject=r['subj']))
        save('TAXI',domain,domain.title(),'Replacement',records,['datasets/edits.json','datasets/edits-evaluation.json'])

# Bi-ZsRE: retain both languages in test cases; do not use source model predictions as old truth.
if want('Bi-ZsRE'):
    base='Bi-ZsRE-data/'
    for filename,label,language in [('bizsre_test.json','Test · English + Chinese',None),
        ('zsre_mend_train_10000.json','Train · English','English'),('zsre_mend_train_10000_chinese.json','Train · Chinese','Chinese'),
        ('zsre_mend_eval.json','Validation · English','English'),('zsre_mend_eval_chinese.json','Validation · Chinese','Chinese')]:
        records=[]
        for i,r in enumerate(read('Bi-ZsRE',base+filename)):
            langs=[('English',r['en']),('Chinese',r['zh'])] if language is None else [(language,r)]
            fields,qs=[],[]
            for lang,part in langs:
                fields.extend([field(lang+' · Prompt',part['src']),field(lang+' · Previous answer',part.get('answers')),field(lang+' · New answer',part['alt'])])
                qs.extend([query('Edit success · '+lang,part['src'],part['alt']),query('Generalization · Rephrase · '+lang,part.get('rephrase'),part['alt']),query('Locality · '+lang,part.get('loc'),part.get('loc_ans'))])
                if part.get('portability'):
                    port=part['portability'];qs.append(query('Generalization · Reasoning · '+lang,port['New Question'],port['New Answer']))
            records.append(row(i,'Replacement',fields,qs,r,note='Test records align English and Chinese. Choose the editing language in the experiment; this view shows both. Previous answers are absent in the released test set.' if language is None else 'English and Chinese validation releases differ in size; row alignment is not assumed.'))
        save('Bi-ZsRE',filename[:-5],label,'Replacement',records,[base+filename])

# RelEdit: the released yes/no probes omit answer labels. Show missing labels rather than invent them.
if want('RelEdit'):
    for path in sorted((DATA/'RelEdit/RelEdit_dataset').glob('*.json')):
        key=path.stem
        model,setting=key.removeprefix('final_').removesuffix('_PCEdit').rsplit('_',1)
        records=[]
        for r in json.loads(path.read_text()):
            qs=[query('Generalization · Rephrase',r['phrase_prompt'],r['target_new_desc']),query('Locality · Concept',r['locality_prompt'],r['locality_answer'])]
            for name,purpose in [('instance_prompt','Generalization · Instance change'),('portability_prompt','Generalization · Instance portability'),('instance_locality_prompt','Locality · Instance'),('alignment_compare_prompt','Generalization · Alignment compare'),('alignment_belong_prompt','Generalization · Alignment belong')]:
                qs.append(query(purpose,r.get(name)))
            records.append(row(r['id'],'Replacement',[field('Prompt',r['prompt']),field('Previous definition',r['subject_desc']),field('New definition',r['target_new_desc']),field('Target concept',r['target_label'])],qs,r,subject=r['label'],note='Concept-definition replacement. The release does not include answer labels for its relational yes/no probes; those remain Not provided.'))
        save('RelEdit',key,model+' · '+setting,'Replacement',records,[str(path.relative_to(DATA/'RelEdit'))], 'Model-specific instance selection. Inter and intra refer to superclass settings, not train/test splits.')

# RuleEdit-200 is a distinct downloadable release; do not label it as ACL 2025 RuleEdit.
if want('RuleEdit-200'):
    def parallel_queries(purpose, block, answer_key='target_new'):
        prompts=block.get('prompt', [])
        answers=block.get(answer_key)
        if not isinstance(prompts,list): return [query(purpose,prompts,answers)]
        assert answers is None or isinstance(answers,list) and len(prompts)==len(answers)
        return [query(purpose,prompt,answers[i] if answers is not None else None) for i,prompt in enumerate(prompts)]

    # Guarded: three of RuleEdit-200's 400 source records are malformed upstream
    # (145/ins.json is not valid JSON; 132 and 164 declare more Instance prompts
    # than answers). Those used to abort this whole script, which is why nothing
    # after this point - including any benchmark added later - ever reached
    # importedBenchmarks.json. Isolating it keeps one broken release from
    # blocking every other one. RuleEdit-200 itself still publishes nothing
    # until those records are fixed, which is a data question, not a view one.
    rule_root=DATA/'RuleEdit-200/RuleEdit-200'
    try:
        if not rule_root.exists():
            raise OSError('RuleEdit-200 source directory is not present')
        rule_views=collections.defaultdict(list)
        paths=collections.defaultdict(list)
        for directory in sorted(rule_root.iterdir(), key=lambda p:int(p.name)):
            for filename in ['f_d.json','ins.json']:
                path=directory/filename
                for i,r in enumerate(json.loads(path.read_text())):
                    key=('formula' if i==0 else 'description') if filename=='f_d.json' else 'instance'
                    qs=[query('Generalization · Rephrase',r.get('rephrase_prompt'),r['target_new'])]
                    qs+=parallel_queries('Generalization · Rule understanding',r.get('Rule_Understanding',{}))
                    ru=r.get('Rule_Understanding',{})
                    if ru.get('rephrase_prompt'):
                        qs.append(query('Generalization · Rule understanding rephrase',ru['rephrase_prompt'],ru.get('target_new')))
                    qs+=parallel_queries('Generalization · Instance portability',r.get('Instance',{}))
                    for kind,block in r.get('locality',{}).items(): qs+=parallel_queries('Locality · '+kind,block,'ground_truth')
                    rule_views[key].append(row(f'{directory.name}:{filename}:{i}','Replacement',[
                        field('Rule',r.get('rule')),field('Prompt',r['prompt']),field('Previous answer',r.get('ground_truth')),field('New answer',r['target_new'])],qs,r,subject=r.get('subject'),note='Counterfactual rule replacement from RuleEdit-200 (DMLE). These targets deliberately change the original mathematical or physical rule.'))
                    paths[key].append(str(path.relative_to(DATA/'RuleEdit-200')))
        for key,label in [('formula','Formulas'),('description','Descriptions'),('instance','Instances')]:
            save('RuleEdit-200',key,label,'Replacement',rule_views[key],sorted(set(paths[key])), 'DMLE mathematics/physics release. This is distinct from ACL 2025 RuleEdit (legal, medical, historical), whose public data release was not located.')
    except (json.JSONDecodeError, AssertionError, KeyError, OSError) as exc:
        CATALOG.pop('RuleEdit-200', None)
        VIEWS.pop('RuleEdit-200', None)
        print('SKIPPED RuleEdit-200:', type(exc).__name__, exc)

# UnKEBench: counterfactual answers written as unstructured long-form text
# (median 90 words), from ConflictQA. Sub-questions probe individual facts
# inside that text; the MMLU items are unrelated knowledge that must survive.
# The release carries no subject span, so ROME/MEMIT/PMET/AlphaEdit cannot
# target it - dashboard.json records that as provides_subject: false.
if want('UnKEBench'):
    path='data/final_data_v3.json'
    records=[]
    for r in read('UnKEBench',path):
        qs=[query('Edit success',r['question'],r['answer']),
            query('Generalization · Rephrase',r['para_question'],r['answer'])]
        assert len(r['sub_question'])==len(r['sub_answer'])
        for sub_prompt,sub_answer in zip(r['sub_question'],r['sub_answer']):
            qs.append(query('Generalization · Sub-question',sub_prompt,sub_answer))
        # mmlu_answer is an index into that item's own choice list, not a letter.
        for mmlu_prompt,choices,answer_index in zip(r['mmlu_questions'],r['mmlu_choices'],r['mmlu_answer']):
            qs.append(query('Locality · MMLU',mmlu_prompt,choices[answer_index],choices=choices))
        records.append(row(r['id'],'Replacement',[field('Prompt',r['question']),field('New answer',r['answer'])],qs,r,
            note='The edit target is the whole long-form answer, not a span within it. Sub-questions check facts stated inside that answer; MMLU items are unrelated knowledge.'))
    save('UnKEBench','unkebench','UnKEBench','Replacement',records,[path],
         'Long-form unstructured answers, median 90 words. No subject span in the release, so this subset cannot run the locate-and-edit methods.')

# EditEverything: long-form answers in seven formats (median 177 words), from
# AnyEdit. Unlike UnKEBench these answers are genuine content rather than
# counterfactuals - a worked derivation, runnable code, a poem - so the edit
# writes knowledge in rather than overwriting a known fact. Split by the
# release's own `category` column, plus a combined view, the same way
# RealTimeQA is split by question type.
if want('EditEverything'):
    everything=read('EditEverything','data/editevery.json')
    def editevery_records(rows):
        return [row(r['id'],'Insertion',
                    [field('Prompt',r['question']),field('New answer',r['answer']),field('Domain',r['category'])],
                    [query('Edit success',r['question'],r['answer'])],r,
                    note='Long-form answer in this domain\'s own format. The release ships no rephrase, portability or locality probes.')
                for r in rows]
    save('EditEverything','all','All','Insertion',editevery_records(everything),['data/editevery.json'],
         'Every domain combined. This is the file the experiment runner loads; the per-domain views below are for browsing.')
    for domain in sorted({r['category'] for r in everything}):
        save('EditEverything',domain,domain.title(),'Insertion',
             editevery_records([r for r in everything if r['category']==domain]),['data/editevery.json'],
             'One domain of the combined release, not a separate source file.')

for name,views in VIEWS.items():
    (DATA/name/'VIEWS.json').write_text(json.dumps({'generator':'dashboard/scripts/prepare_benchmarks.py','views':views},indent=2)+'\n')
if not ONLY:
    (ROOT/'dashboard/frontend/src/lib/importedBenchmarks.json').write_text(json.dumps(CATALOG,indent=2)+'\n')
