"""
Data loading, evaluation, and monitoring helpers for the FT step-sweep.

These are thin wrappers around EasyEdit's own dataset/eval code — nothing
here recomputes what EasyEdit already does. The one exception is locality
scoring: EasyEdit's BaseEditor normally finalizes it for you
(editors/editor.py::finalize_locality_metrics, comparing each checkpoint's
raw output tokens against the *pre-edit* model's), but since this sweep
bypasses BaseEditor entirely (see checkpointed_ft.py's docstring for why),
`evaluate_requests` below redoes that one step itself.
"""
import json
import os
from statistics import mean
from typing import Dict, List, Optional, Tuple

import numpy as np
import psutil
import torch

from easyeditor import KnowEditDataset
from easyeditor.editors.utils import _prepare_requests
from easyeditor.evaluate.evaluate import compute_edit_quality


def _flatten_probes(items: List[Optional[List[Dict]]]) -> Tuple[List, List]:
    """
    `items` holds one entry per record: either None (record has no probes
    for this locality/portability key) or a list of {'prompt', 'ground_truth'}
    probe questions (KnowEdit sometimes attaches more than one probe per
    key). Returns parallel (prompts, answers) lists-of-lists in the shape
    `_prepare_requests` expects for `locality_inputs`/`portability_inputs`.
    """
    prompts_out, answers_out = [], []
    for item in items:
        if item is None:
            prompts_out.append(None)
            answers_out.append(None)
            continue
        prompts, answers = [], []
        for probe in item:
            answer = probe["ground_truth"]
            while isinstance(answer, list):
                answer = answer[0]
            if answer.strip() == "":
                continue
            prompts.append(probe["prompt"])
            answers.append(answer)
        prompts_out.append(prompts)
        answers_out.append(answers)
    return prompts_out, answers_out


def load_recent_requests(data_path: str, ds_size: int) -> List[Dict]:
    """
    Loads the first `ds_size` records of a KnowEdit 'recent'-shaped file
    (wiki_recent / wiki_counterfact / ZsRE all share this shape) and builds
    EasyEdit request dicts via `_prepare_requests` — the same helper
    `BaseEditor.edit()` uses internally, so the request format matches
    exactly what `compute_edit_quality` expects.
    """
    data = KnowEditDataset(data_path, size=ds_size)

    portability_inputs = {}
    for key, field in [
        ("Subject_Aliasing", "portability_s"),
        ("reasoning", "portability_r"),
        ("Logical_Generalization", "portability_l"),
    ]:
        prompts, answers = _flatten_probes([d[field] for d in data])
        portability_inputs[key] = {"prompt": prompts, "ground_truth": answers}

    locality_inputs = {}
    for key, field in [
        ("Relation_Specificity", "locality_rs"),
        ("Forgetfulness", "locality_f"),
    ]:
        prompts, answers = _flatten_probes([d[field] for d in data])
        locality_inputs[key] = {"prompt": prompts, "ground_truth": answers}

    # The original answer, where the file has one (wiki_counterfact and ZsRE;
    # wiki_recent inserts new facts, so it has none). No metric reads it:
    # scores compare against target_new. Knowledge Neurons needs it to
    # attribute neurons to the fact being replaced.
    def original(d):
        truth = d.get("ground_truth")
        return truth[0] if isinstance(truth, list) and truth else truth

    return _prepare_requests(
        prompts=[d["prompt"] for d in data],
        target_new=[d["target_new"] for d in data],
        ground_truth=[original(d) for d in data],
        subject=[d["subject"] for d in data],
        locality_inputs=locality_inputs,
        portability_inputs=portability_inputs,
    )


def load_uniedit_requests(data_path: str, ds_size: int) -> List[Dict]:
    """UniEdit: {sample_id: {edit: {prompt, target, subject, ...}, generality:
    {idx: {prompt, target, ...}}, locality: {idx: {prompt, target, ...}}}}.
    generality/locality are dicts keyed by numeric index, not category name -
    both become one flat probe group each ("Generality"/"Locality")."""

    with open(data_path) as f:
        data = json.load(f)
    records = list(data.values())[:ds_size]

    portability_inputs = {
        "Generality": {
            "prompt": [[p["prompt"] for p in r.get("generality", {}).values()] for r in records],
            "ground_truth": [[p["target"] for p in r.get("generality", {}).values()] for r in records],
        }
    }
    locality_inputs = {
        "Locality": {
            "prompt": [[p["prompt"] for p in r.get("locality", {}).values()] for r in records],
            "ground_truth": [[p["target"] for p in r.get("locality", {}).values()] for r in records],
        }
    }

    return _prepare_requests(
        prompts=[r["edit"]["prompt"] for r in records],
        target_new=[r["edit"]["target"] for r in records],
        ground_truth=[None] * len(records),
        subject=[r["edit"]["subject"] for r in records],
        locality_inputs=locality_inputs,
        portability_inputs=portability_inputs,
    )


def load_bizsre_requests(data_path: str, ds_size: int, lang: str = "en") -> List[Dict]:
    """Bi-ZsRE: [{"en": {subject, src, rephrase, alt, loc, loc_ans,
    portability: {"New Question", "New Answer"}}, "zh": {...same shape...}},
    ...]. Only one language's half of each record is used per run (default
    English) - this isn't a bilingual-consistency experiment."""

    with open(data_path) as f:
        data = json.load(f)
    records = [r[lang] for r in data[:ds_size]]

    def one_or_empty(value):
        return [value] if value else []

    portability_inputs = {
        "Reasoning": {
            "prompt": [one_or_empty(r.get("portability", {}).get("New Question")) for r in records],
            "ground_truth": [one_or_empty(r.get("portability", {}).get("New Answer")) for r in records],
        },
        "Rephrase": {
            "prompt": [one_or_empty(r.get("rephrase")) for r in records],
            "ground_truth": [[r["alt"]] if r.get("rephrase") else [] for r in records],
        },
    }
    locality_inputs = {
        "Locality": {
            "prompt": [one_or_empty(r.get("loc")) for r in records],
            "ground_truth": [one_or_empty(r.get("loc_ans")) for r in records],
        }
    }

    return _prepare_requests(
        prompts=[r["src"] for r in records],
        target_new=[r["alt"] for r in records],
        ground_truth=[None] * len(records),
        subject=[r["subject"] for r in records],
        locality_inputs=locality_inputs,
        portability_inputs=portability_inputs,
    )


def load_mquake_requests(data_path: str, ds_size: int) -> List[Dict]:
    """MQuAKE: [{"requested_rewrite": [{prompt (may contain a "{}" subject
    placeholder), subject, target_new: {"str": ...}, target_true: {"str": ...}}],
    "questions": [...multi-hop rephrasings...], "new_answer": str}, ...].
    MQuAKE's edits are often *chains* of several rewrites per record
    (multi-hop counterfactual edits) - only the first rewrite in the chain
    is used here, i.e. this is a single-edit slice of MQuAKE, not the full
    multi-hop-editing protocol its own benchmark is designed around."""

    with open(data_path) as f:
        data = json.load(f)
    records = data[:ds_size]

    prompts, target_new, ground_truth, subject = [], [], [], []
    portability_prompts, portability_answers = [], []
    for r in records:
        edit = r["requested_rewrite"][0]
        subj = edit["subject"]
        prompts.append(edit["prompt"].format(subj) if "{}" in edit["prompt"] else edit["prompt"])
        target_new.append(edit["target_new"]["str"])
        ground_truth.append(edit["target_true"]["str"])
        subject.append(subj)

        questions = list(r.get("questions", []))
        answer = r.get("new_answer")
        portability_prompts.append(questions)
        portability_answers.append([answer] * len(questions) if answer else [])

    portability_inputs = {"Multi-hop": {"prompt": portability_prompts, "ground_truth": portability_answers}}
    return _prepare_requests(
        prompts=prompts,
        target_new=target_new,
        ground_truth=ground_truth,
        subject=subject,
        locality_inputs=None,
        portability_inputs=portability_inputs,
    )


def load_realtimeqa_requests(data_path: str, ds_size: int) -> List[Dict]:
    """RealTimeQA, preprocessed by datasets/RealTimeQA/build_editing_set.py
    into [{prompt, target_new, ground_truth: null, question_type, ...}].
    No `subject` field - see that script's docstring for why - so this is
    NOT usable with ROME/MEMIT/PMET/AlphaEdit (load_requests's caller,
    run_experiment.py, checks for and refuses that combination rather
    than let it fail confusingly inside EasyEdit). No locality/portability
    probes either - the source has none."""

    with open(data_path) as f:
        data = json.load(f)
    records = data[:ds_size]

    return _prepare_requests(
        prompts=[r["prompt"] for r in records],
        target_new=[r["target_new"] for r in records],
        ground_truth=[None] * len(records),
        locality_inputs=None,
        portability_inputs=None,
    )


def load_unkebench_requests(data_path: str, ds_size: int) -> List[Dict]:
    """UnKEBench: [{id, question, para_question, answer, sub_question[],
    sub_answer[], mmlu_questions[], mmlu_choices[][], mmlu_answer[]}, ...].

    The edit target is a whole unstructured passage (median 90 words), not
    an entity - which is the point of the benchmark, and why the scores
    here are not comparable with a short-span dataset's even for the same
    method. Like RealTimeQA there is no `subject` field: the questions name
    an entity but the release never labels the span, so ROME/MEMIT/PMET/
    AlphaEdit cannot be used (run_experiment.py refuses that pairing).

    Probes come from the release itself: `para_question` is a rephrase of
    the same question, the sub-questions ask about individual facts stated
    inside the long answer, and the MMLU items are unrelated multiple-choice
    knowledge that editing must leave alone. mmlu_answer holds an index into
    that item's own choice list, so the stored ground truth is the choice
    text rather than a letter.
    """
    with open(data_path) as f:
        data = json.load(f)
    records = data[:ds_size]

    portability_inputs = {
        "Rephrase": {
            "prompt": [[r["para_question"]] if r.get("para_question") else [] for r in records],
            "ground_truth": [[r["answer"]] if r.get("para_question") else [] for r in records],
        },
        "Sub_Question": {
            "prompt": [list(r.get("sub_question", [])) for r in records],
            "ground_truth": [list(r.get("sub_answer", [])) for r in records],
        },
    }
    locality_inputs = {
        "MMLU": {
            "prompt": [list(r.get("mmlu_questions", [])) for r in records],
            "ground_truth": [[choices[index] for choices, index
                              in zip(r.get("mmlu_choices", []), r.get("mmlu_answer", []))]
                             for r in records],
        }
    }

    return _prepare_requests(
        prompts=[r["question"] for r in records],
        target_new=[r["answer"] for r in records],
        ground_truth=[None] * len(records),
        locality_inputs=locality_inputs,
        portability_inputs=portability_inputs,
    )


def load_editeverything_requests(data_path: str, ds_size: int) -> List[Dict]:
    """EditEverything (AnyEdit): [{id, question, answer, category}, ...],
    552 records across seven domains - math, code, poetry, news, chemistry,
    biology, physics.

    Answers are longer than UnKEBench's (median 177 words) and, unlike it,
    are genuine content rather than counterfactuals: a worked derivation,
    runnable code, a poem. So an edit here writes knowledge in rather than
    overwriting a fact the model already holds, and a low edit-success score
    means the method could not reproduce a long structured answer, not that
    it failed to overturn a belief.

    The release ships no rephrase, portability or locality probes and no
    `subject` field, so this is FT/LoRA/SCR/IKE only and its only metric is
    edit success. `category` is carried through untouched for slicing the
    results by domain afterwards.
    """
    with open(data_path) as f:
        data = json.load(f)
    records = data[:ds_size]

    requests = _prepare_requests(
        prompts=[r["question"] for r in records],
        target_new=[r["answer"] for r in records],
        ground_truth=[None] * len(records),
        locality_inputs=None,
        portability_inputs=None,
    )
    for request, record in zip(requests, records):
        request["category"] = record.get("category")
    return requests


def load_ruleedit_requests(data_path: str, ds_size: int) -> List[Dict]:
    """RuleEdit-200, flattened by datasets/RuleEdit-200/build_editing_set.py
    into three consecutive records per rule: its formula, its description
    and one worked instance, each tagged `rule_id` and `form`; every method
    edits them as ordinary facts. Edit the three together (batch of 3) to
    follow the release's rule-level protocol.

    Targets are counterfactual rules, so both portability groups are scored
    against the edited rule: "Rule_Understanding" asks for the rule's other
    forms, "Instance" for worked answers under it. Locality keeps the
    release's "neighborhood" (related rules) and "distracting" (unrelated
    rules) groups apart."""
    with open(data_path) as f:
        data = json.load(f)
    records = data[:ds_size]

    portability_inputs = {}
    for key in ("Rule_Understanding", "Instance"):
        prompts, answers = _flatten_probes([r["portability"].get(key) or None for r in records])
        portability_inputs[key] = {"prompt": prompts, "ground_truth": answers}
    locality_inputs = {}
    for key in ("neighborhood", "distracting"):
        prompts, answers = _flatten_probes([r["locality"].get(key) or None for r in records])
        locality_inputs[key] = {"prompt": prompts, "ground_truth": answers}

    requests = _prepare_requests(
        prompts=[r["prompt"] for r in records],
        target_new=[r["target_new"] for r in records],
        ground_truth=[r.get("ground_truth") for r in records],
        subject=[r["subject"] for r in records],
        locality_inputs=locality_inputs,
        portability_inputs=portability_inputs,
    )
    for request, record in zip(requests, records):
        request["rule_id"] = record["rule_id"]
        request["form"] = record["form"]
    return requests


def load_requests(data_path: str, ds_size: int) -> List[Dict]:
    """Picks the right per-format loader based on data_path, so
    run_experiment.py and ike.py don't need to know or care which shape a
    given dataset uses - see the individual load_*_requests functions
    above for what each format actually looks like."""
    if "/UniEdit/" in data_path:
        return load_uniedit_requests(data_path, ds_size)
    if "/MQuAKE/" in data_path:
        return load_mquake_requests(data_path, ds_size)
    if "/Bi-ZsRE/" in data_path:
        return load_bizsre_requests(data_path, ds_size)
    if "/RealTimeQA/" in data_path:
        return load_realtimeqa_requests(data_path, ds_size)
    if "/UnKEBench/" in data_path:
        return load_unkebench_requests(data_path, ds_size)
    if "/EditEverything/" in data_path:
        return load_editeverything_requests(data_path, ds_size)
    if "/RuleEdit-200/" in data_path:
        return load_ruleedit_requests(data_path, ds_size)
    return load_recent_requests(data_path, ds_size)


def evaluate_requests(
    model,
    model_name: str,
    hparams,
    tok,
    requests: List[Dict],
    device,
    test_generation: bool,
    baseline_locality_outputs: Optional[List[Dict]] = None,
) -> Tuple[List[Dict], List[Dict]]:
    """
    Runs compute_edit_quality against the *current* model for every
    request. If `baseline_locality_outputs` is given (the raw `*_output`
    token lists captured at step 0, before any training), adds a
    `<key>_acc` entry to each record's locality dict: the token-level
    match rate against that baseline — this is what
    `finalize_locality_metrics` does inside BaseEditor.edit_requests
    normally; we redo it by hand here since we're not going through
    BaseEditor.

    Returns (per_record_metrics, locality_outputs) — pass
    `locality_outputs` back in as `baseline_locality_outputs` on every
    later call so all checkpoints compare against the same step-0
    baseline.
    """
    per_record, locality_outputs = [], []
    with torch.no_grad():
        for i, record in enumerate(requests):
            metrics = compute_edit_quality(
                model, model_name, hparams, tok, record, device, test_generation=test_generation
            )
            metrics["case_id"] = i
            locality_outputs.append(
                {k: v for k, v in metrics["locality"].items() if k.endswith("_output")}
            )
            if baseline_locality_outputs is not None:
                for key in record.get("locality", {}):
                    out_key = f"{key}_output"
                    pre_out = baseline_locality_outputs[i].get(out_key)
                    post_out = metrics["locality"].get(out_key)
                    if pre_out is not None and post_out is not None:
                        metrics["locality"][f"{key}_acc"] = [
                            float(np.mean(np.equal(p, q))) for p, q in zip(pre_out, post_out)
                        ]
            per_record.append(metrics)
    return per_record, locality_outputs


def _mean(values):
    values = [v for v in values if v is not None]
    return mean(values) if values else None


def aggregate_metrics(per_record: List[Dict]) -> Dict:
    """Rolls per-record metrics up into the four headline scores (0-100)."""
    edit_succ = [m["rewrite_acc"][0] for m in per_record if "rewrite_acc" in m]

    portability = []
    for m in per_record:
        key_means = [_mean(v) for k, v in m.get("portability", {}).items() if k.endswith("_acc") and v]
        if key_means:
            portability.append(_mean(key_means))

    locality = []
    for m in per_record:
        key_means = [_mean(v) for k, v in m.get("locality", {}).items() if k.endswith("_acc") and v]
        if key_means:
            locality.append(_mean(key_means))

    fluency = [m["fluency"]["ngram_entropy"] for m in per_record if "fluency" in m]

    def pct(values):
        m = _mean(values)
        return 100 * m if m is not None else None

    return {
        "edit_succ": pct(edit_succ),
        "portability": pct(portability),
        "locality": pct(locality),
        "fluency": pct(fluency),
    }


def memory_snapshot(device) -> Dict:
    """PyTorch GPU allocation, device capacity, and host RSS, in decimal MB."""
    torch.cuda.synchronize(device)
    gpu_alloc_mb = torch.cuda.memory_allocated(device) / 1e6
    gpu_peak_mb = torch.cuda.max_memory_allocated(device) / 1e6
    torch.cuda.reset_peak_memory_stats(device)
    host_rss_mb = psutil.Process(os.getpid()).memory_info().rss / 1e6
    return {
        "gpu_mem_alloc_mb": round(gpu_alloc_mb, 1),
        "gpu_mem_peak_mb": round(gpu_peak_mb, 1),
        "gpu_mem_total_mb": round(torch.cuda.get_device_properties(device).total_memory / 1e6, 1),
        "host_rss_mb": round(host_rss_mb, 1),
    }


def sample_generations(model, tok, prompts: List[str], device, n=3, max_new_tokens=80) -> List[Dict]:
    """
    A handful of actual model outputs, for eyeballing what numeric fluency
    can't show (repetition, degeneration, wrong-but-fluent text). EasyEdit's
    own fluency metric generates this same kind of text internally and
    throws it away (see evaluate_utils.py::test_generation_quality) — this
    is an independent, small, greedy-decoded sample.
    """
    model.eval()
    samples = []
    with torch.no_grad():
        for prompt in prompts[:n]:
            inputs = tok(prompt, return_tensors="pt").to(device)
            out = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=tok.eos_token_id,
            )
            continuation = tok.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
            samples.append({"prompt": prompt, "continuation": continuation})
    return samples
