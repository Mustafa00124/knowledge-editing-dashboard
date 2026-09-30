"""
In-Context Knowledge Editing (IKE) - Zheng et al., "Can We Edit Factual
Knowledge by In-Context Learning?" (arXiv:2305.12740). EasyEdit does ship
an IKE implementation (easyeditor/models/ike/), but its apply function
(`apply_ike_to_model`) requires a precomputed embeddings pickle file at an
undocumented path/naming convention, built by a separate call
(`encode_ike_facts`) that nothing in this project's pipeline calls -
rather than depend on that fragile out-of-band contract, this
reimplements the same underlying mechanism directly, computing embeddings
on the fly the same way scr.py does (and reusing scr.py's retrieval index
verbatim - the retrieve-by-embedding-similarity mechanics are identical).

Mechanism, matching EasyEdit's own `encode_ike_facts` (see
easyeditor/models/ike/util.py) - adapted to this project's nested
portability/locality request shape rather than the flat rephrase_prompt/
locality_prompt fields upstream's IKE-specific dataset loader expects:
  - A pool of demonstration sentences is built from a separate *training*
    split (see run_experiment.py) - never the actual test set being
    evaluated. Each demo record contributes up to 1 + P + L sentences (P/L
    = however many portability/locality probes that record has):
      1. a "copy" demo:        New Fact: X  Prompt: X
      2. one "generalize" demo per portability probe: New Fact: X  Prompt: <probe> <answer>
      3. one "retain" demo per locality probe:         New Fact: X  Prompt: <probe> <answer>
    teaching the model, by example, to (1) repeat a stated new fact,
    (2) apply it under paraphrase/generalization, (3) leave unrelated
    facts alone - no weight is ever edited.
  - At evaluation time, the k demo sentences most similar to
    "New Fact: <this fact>\nPrompt: <this query>" are retrieved and
    joined as a prefix before the actual query, in the same
    "New Fact: ...\nPrompt: ..." shape the demos themselves use - not
    traced from EasyEdit's own downstream prompt construction (that logic
    lives in BaseEditor, not in ike_main.py itself), but a direct,
    documented reconstruction of the same in-context pattern the demos
    are written in.

Since nothing here is edited and the demo pool is unrelated to which test
facts are being evaluated, "step" means something different again: how
many demo sentences have been added to the retrievable pool so far
(mirroring SCR's/ROME's "step i" framing so the same checkpoint machinery
applies) - the test requests being evaluated stay fixed throughout; only
how much demonstration material IKE can draw on grows.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import torch
import yaml

from scr import SCRIndex, _matches  # retrieval + match-scoring are identical - reuse, don't duplicate


@dataclass
class IKEHyperParams:
    """Not EasyEdit's IKEHyperParams (that one's tied to the fragile
    pickle-cache apply_ike_to_model) - a minimal yaml-loadable equivalent,
    same convention as scr.py's SCRHyperParams."""

    alg_name: str
    model_name: str
    device: int
    sentence_model_name: str = "all-MiniLM-L6-v2"
    k: int = 8
    max_new_tokens: int = 40

    @classmethod
    def from_hparams(cls, path):
        if not str(path).endswith(".yaml"):
            path = f"{path}.yaml"
        with open(path) as f:
            cfg = yaml.safe_load(f)
        assert cfg.get("alg_name") == "IKE", f"not an IKE hparams file: {path}"
        return cls(**cfg)

    def to_dict(self):
        return {
            "alg_name": self.alg_name,
            "model_name": self.model_name,
            "device": self.device,
            "sentence_model_name": self.sentence_model_name,
            "k": self.k,
            "max_new_tokens": self.max_new_tokens,
        }


def build_demo_sentences(demo_requests: List[Dict]) -> List[str]:
    """Up to 1 + P + L template sentences per demo record - see module
    docstring. `demo_requests` should come from a *training* split (a
    separate load_recent_requests() call against the train file), never
    the same records being evaluated."""
    sentences = []
    for r in demo_requests:
        new_fact = f"{r['prompt']} {r['target_new']}"
        sentences.append(f"New Fact: {new_fact}\nPrompt: {new_fact}\n\n")
        for probe_group in r.get("portability", {}).values():
            for p_prompt, answer in zip(probe_group["prompt"], probe_group["ground_truth"]):
                if answer:
                    sentences.append(f"New Fact: {new_fact}\nPrompt: {p_prompt} {answer}\n\n")
        for probe_group in r.get("locality", {}).values():
            for p_prompt, answer in zip(probe_group["prompt"], probe_group["ground_truth"]):
                if answer:
                    sentences.append(f"New Fact: {new_fact}\nPrompt: {p_prompt} {answer}\n\n")
    return sentences


def ike_answer(model, tok, new_fact: str, query: str, pool: SCRIndex, device, k: int, max_new_tokens: int) -> str:
    """Retrieve the k most similar demonstrations to this (fact, query)
    pair and generate with them prefixed - or answer directly if the pool
    is still empty (step 0, before any demos have been added)."""
    demos = pool.retrieve(f"New Fact: {new_fact}\nPrompt: {query}", k)
    prefix = "".join(demos)
    prompt = f"{prefix}New Fact: {new_fact}\nPrompt: {query}"

    inputs = tok(prompt, return_tensors="pt").to(device)
    with torch.no_grad():
        out = model.generate(
            **inputs, max_new_tokens=max_new_tokens, do_sample=False, pad_token_id=tok.eos_token_id
        )
    return tok.decode(out[0][inputs["input_ids"].shape[1] :], skip_special_tokens=True)


def evaluate_requests_ike(
    model,
    tok,
    requests: List[Dict],
    pool: SCRIndex,
    device,
    hparams: IKEHyperParams,
    baseline_answers: Optional[Dict[Tuple[int, str, int], str]] = None,
    answer_cache=None,
) -> Tuple[List[Dict], Dict[Tuple[int, str, int], str]]:
    """Same per-record shape eval_utils.aggregate_metrics expects, and the
    same locality reasoning as scr.py's evaluate_requests_scr: since
    weights never change, locality can only drift here if a growing demo
    pool starts leaking irrelevant context into an unrelated probe's
    answer - judged against this model's own answer before the pool had
    anything in it (baseline_answers, captured at step 0)."""
    k, max_new_tokens = hparams.k, hparams.max_new_tokens
    from semantic_evaluation import cached_answer
    cache = answer_cache if answer_cache is not None else {}
    def answer_query(fact, query):
        return cached_answer(cache, (fact, query), lambda: ike_answer(model, tok, fact, query, pool, device, k, max_new_tokens))
    per_record = []
    answers_this_call: Dict[Tuple[int, str, int], str] = {}

    for i, record in enumerate(requests):
        new_fact = f"{record['prompt']} {record['target_new']}"
        answer = answer_query(new_fact, record["prompt"])
        rewrite_acc = [1.0 if _matches(answer, record["target_new"]) else 0.0]

        portability = {}
        for cat, probe in record.get("portability", {}).items():
            accs = [
                1.0 if _matches(answer_query(new_fact, p_prompt), gt) else 0.0
                for p_prompt, gt in zip(probe["prompt"], probe["ground_truth"])
            ]
            if accs:
                portability[f"{cat}_acc"] = accs

        locality = {}
        for cat, probe in record.get("locality", {}).items():
            accs = []
            for j, p_prompt in enumerate(probe["prompt"]):
                loc_answer = answer_query(new_fact, p_prompt)
                key = (i, cat, j)
                answers_this_call[key] = loc_answer
                if baseline_answers is not None and key in baseline_answers:
                    accs.append(1.0 if loc_answer.strip() == baseline_answers[key].strip() else 0.0)
            if accs:
                locality[f"{cat}_acc"] = accs

        per_record.append({"rewrite_acc": rewrite_acc, "portability": portability, "locality": locality})

    return per_record, answers_this_call
