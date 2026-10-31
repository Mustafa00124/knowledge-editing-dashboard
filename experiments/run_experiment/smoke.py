"""Smoke mode for Sid's Dataset (run_experiment.py --smoke): does this method
run on every edit, and really edit?

For each record, one at a time: the data checks (sids_requests), the method's
own checks on the tokenized request, the edit, then checks that it did
something real, then the original weights back. Each failure is a named
exception, written to smoke.jsonl with the record id and the run goes on to
the next record; nothing is skipped silently. If the weights can't be put
back, the run stops: every later record would start from an edited model.

    smoke.jsonl   one row per record: status ok / error, the exception's
                  class and message, seconds
    summary.json  method, model, records hash, counts (read by CRITERIA Rule 13)

Written for the GPU nodes and not yet run there: the first gaivi run is its
test (README, Running methods).
"""
import json
import os
import time
import traceback

import torch

import sids_requests


class SmokeCheckFailed(RuntimeError):
    """A method ran but its edit doesn't meet a requirement."""


class SubjectTokensNotFound(SmokeCheckFailed):
    pass


class TargetTokensEmpty(SmokeCheckFailed):
    pass


class NoWeightChange(SmokeCheckFailed):
    pass


class NonFiniteWeights(SmokeCheckFailed):
    pass


class NoGeneration(SmokeCheckFailed):
    pass


class RestoreFailed(RuntimeError):
    """Fatal: the next record would start from an edited model."""


def _subject_tokens(tok, prompt, subject):
    """Token positions covering the subject in the prompt; raises when the
    tokenizer can't place it (an edit at the subject's last token needs one)."""
    start = prompt.index(subject)
    end = start + len(subject)
    enc = tok(prompt, return_offsets_mapping=True, add_special_tokens=False)
    covered = [i for i, (a, b) in enumerate(enc['offset_mapping']) if a < end and b > start]
    if not covered or enc['offset_mapping'][covered[-1]][1] < end:
        raise SubjectTokensNotFound(f'subject {subject!r} does not map onto whole tokens of {prompt!r}')
    return covered


def method_checks(request, method, tok, max_target_tokens=64):
    sids_requests.check_request(request, method)
    if method in sids_requests.SUBJECT_METHODS:
        _subject_tokens(tok, request['prompt'], request['subject'])
    n = len(tok(' ' + request['target_new'], add_special_tokens=False)['input_ids'])
    if n == 0 or n > max_target_tokens:
        raise TargetTokensEmpty(f'target {request["target_new"]!r} is {n} tokens (want 1 to {max_target_tokens})')


def _tracked_params(model, method, hparams):
    """The parameters an edit of this method may touch, for FT and LoRA,
    whose trainers don't hand back the original weights."""
    if method in ('ft', 'ft_l'):
        return {n: p for n, p in model.named_parameters()
                if any(hparams.rewrite_module_tmp.format(l) in n for l in hparams.layers)}
    if method == 'lora':
        return {n: p for n, p in model.named_parameters() if p.requires_grad}
    return {}


def _changed(model, originals):
    params = dict(model.named_parameters())
    changed, finite = False, True
    with torch.no_grad():
        for name, orig in originals.items():
            p = params.get(name)
            if p is None:
                continue
            if not torch.isfinite(p).all():
                finite = False
            if not torch.equal(p.detach().to(orig.device), orig):
                changed = True
    return changed, finite


def _restore(model, originals):
    from easyeditor.util import nethook
    from easyeditor.util.device import copy_to_param
    with torch.no_grad():
        for name, value in originals.items():
            copy_to_param(nethook.get_parameter(model, name), value)
        for name, value in originals.items():
            if not torch.equal(nethook.get_parameter(model, name).detach().to(value.device), value):
                raise RestoreFailed(f'{name} differs from its original after restoring')


def _generates(model, tok, prompt, device):
    enc = tok(prompt, return_tensors='pt').to(device)
    with torch.no_grad():
        out = model.generate(**enc, max_new_tokens=8, do_sample=False, pad_token_id=tok.pad_token_id)
    if out.shape[1] <= enc['input_ids'].shape[1]:
        raise NoGeneration('the edited model generated no tokens')


def run_smoke(method, model_name, model, tok, hparams, requests, run_dir, device, apply_fn=None,
              training_fn=None, records_hash=None, prompt_format=None):
    """One method, one model, every request. Returns the summary dict."""
    rows_path = os.path.join(run_dir, 'smoke.jsonl')
    counts = {'ok': 0, 'error': 0}
    with open(rows_path, 'w') as out:
        for request in requests:
            rid = request['sids']['id']
            row = {'record': rid, 'method': method, 'model': model_name}
            t0 = time.time()
            originals = {}
            try:
                method_checks(request, method, tok)
                if training_fn is not None:
                    tracked = _tracked_params(model, method, hparams)
                    originals = {n: p.detach().clone() for n, p in tracked.items()}
                    hparams.batch_size = 1
                    training_fn(model, tok, [request], hparams, hparams.num_steps, lambda step, loss=None: None)
                else:
                    model, copied = apply_fn(model, tok, [request], hparams, copy=False, return_orig_weights=True)
                    originals = {n: v.detach().clone() for n, v in copied.items()}
                if not originals:
                    raise NoWeightChange('the method reported no edited weights')
                changed, finite = _changed(model, originals)
                if not finite:
                    raise NonFiniteWeights('an edited weight is NaN or infinite')
                if not changed:
                    raise NoWeightChange('no edited weight differs from its original')
                _generates(model, tok, request['prompt'], device)
                row.update(status='ok')
                counts['ok'] += 1
            except RestoreFailed:
                raise
            except Exception as e:  # recorded per record, never dropped
                row.update(status='error', error=type(e).__name__, message=str(e)[:500],
                           trace=traceback.format_exc(limit=3)[-1500:])
                counts['error'] += 1
            finally:
                if originals:
                    _restore(model, originals)  # raises RestoreFailed, which stops the run
            row['seconds'] = round(time.time() - t0, 2)
            out.write(json.dumps(row) + '\n')
            out.flush()
            print(f"[smoke {method} {model_name}] {rid}: {row['status']}"
                  + (f" {row['error']}: {row['message']}" if row['status'] == 'error' else ''))
    summary = {'method': method, 'model': model_name, 'records': len(requests), 'records_hash': records_hash,
               'prompt_format': prompt_format, **counts, 'finished_at': time.strftime('%Y-%m-%dT%H:%M:%S')}
    with open(os.path.join(run_dir, 'summary.json'), 'w') as f:
        json.dump(summary, f, indent=2)
    return summary
