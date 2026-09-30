"""
Selective Contextual Reasoning (SCR) - arXiv:2503.05212. A from-scratch
implementation: EasyEdit doesn't ship this method, and the paper itself
has no released code - there was nothing to import. Model weights are
NEVER touched here; this "edits" a fact by making it retrievable, not by
changing any parameter.

The paper's algorithm, as stated:
    K_retrieved = Retriever(q, KB, k)
    K_relevant  = Confirm(q, K_retrieved)
    Answer      = LLM(q, K_relevant)

This is a simplified, best-effort reproduction, not a faithful
re-implementation of the paper's exact experimental setup (which isn't
public). Documented simplifications:
  - Retriever: cosine similarity over sentence-transformer embeddings of
    each KB fact statement - the same embedding approach EasyEdit's own
    IKE method already uses (`sentence-transformers`), reused here rather
    than picking a different library.
  - Confirm: a zero-shot Yes/No check via next-token logit comparison,
    rather than whatever confirmation mechanism the paper actually used.
    Chosen because it doesn't require an instruction-tuned model - it
    only needs the raw next-token distribution, not reliable
    instruction-following, so it works the same way across all three
    models this project has wired up.
  - Answer / match scoring: a single greedy generate() call, scored by
    case-insensitive substring match against the expected answer(s) -
    not EasyEdit's own likelihood-based compute_edit_quality, which
    assumes precise prompt/target token alignment that no longer holds
    once retrieved context has been prepended.
  - Fluency isn't computed for SCR yet (aggregate_metrics just reports it
    as unavailable) - a TODO, not a silent gap.

Since nothing here trains/edits the model, run_experiment.py treats
"step" as "how many facts have been added to SCR's retrievable knowledge
base so far" - the same framing it uses for ROME's sequential edits -
purely so the same checkpoint/progress machinery (and the dashboard's
step-progress bar) works unchanged across all three methods.

Performance note: unlike ROME/FT (one batched forward pass per
checkpoint), this makes several small generate() calls per probe
(one confirm-check per retrieved candidate, plus the answer itself) -
expect SCR checkpoints to be slower than the other two methods.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import torch
import yaml
from sentence_transformers import SentenceTransformer, util


@dataclass
class SCRHyperParams:
    """Not an EasyEdit HyperParams subclass - SCR isn't an EasyEdit
    algorithm, so there's no shared base class to extend. Kept minimal
    and yaml-loadable the same way, for consistency with FT/ROME's
    hparams/<METHOD>/<model>.yaml convention in run_experiment.py."""

    alg_name: str
    model_name: str
    device: int
    sentence_model_name: str = "all-MiniLM-L6-v2"
    retrieval_k: int = 3
    max_new_tokens: int = 40

    @classmethod
    def from_hparams(cls, path):
        if not str(path).endswith(".yaml"):
            path = f"{path}.yaml"
        with open(path) as f:
            cfg = yaml.safe_load(f)
        assert cfg.get("alg_name") == "SCR", f"not an SCR hparams file: {path}"
        return cls(**{k: v for k, v in cfg.items()})

    def to_dict(self):
        return {
            "alg_name": self.alg_name,
            "model_name": self.model_name,
            "device": self.device,
            "sentence_model_name": self.sentence_model_name,
            "retrieval_k": self.retrieval_k,
            "max_new_tokens": self.max_new_tokens,
        }


def build_kb(requests: List[Dict]) -> List[str]:
    """One retrievable statement per request - what SCR is meant to treat
    as newly-known/updated information. Requests already carry the
    subject spelled out in `prompt` (see load_recent_requests), so this
    is just prompt + target_new read as a plain sentence."""
    return [f"{r['prompt']} {r['target_new']}" for r in requests]


class SCRIndex:
    """Embeds a growing knowledge base incrementally - `grow()` only
    embeds what's new, so checkpointing SCR every --checkpoint_every
    facts (see run_experiment.py) doesn't re-embed the whole KB each time."""

    def __init__(self, sentence_model_name: str, device):
        self.model = SentenceTransformer(sentence_model_name).to(device)
        self.texts: List[str] = []
        self.embeddings = None

    def grow(self, new_texts: List[str]):
        if not new_texts:
            return
        new_emb = self.model.encode(new_texts, convert_to_tensor=True, show_progress_bar=False)
        self.texts.extend(new_texts)
        self.embeddings = new_emb if self.embeddings is None else torch.cat([self.embeddings, new_emb], dim=0)

    def retrieve(self, query: str, k: int) -> List[str]:
        if not self.texts:
            return []
        query_emb = self.model.encode(query, convert_to_tensor=True, show_progress_bar=False)
        scores = util.cos_sim(query_emb, self.embeddings)[0]
        top = torch.topk(scores, k=min(k, len(self.texts)))
        return [self.texts[i] for i in top.indices.tolist()]


def _yes_no_confirm(model, tok, query: str, candidate: str, device) -> bool:
    prompt = (
        f"Query: {query}\n"
        f"Candidate fact: {candidate}\n"
        f"Is the candidate fact relevant to answering the query? Answer Yes or No.\n"
        f"Answer:"
    )
    inputs = tok(prompt, return_tensors="pt").to(device)
    with torch.no_grad():
        logits = model(**inputs).logits[0, -1]
    yes_id = tok.encode(" Yes", add_special_tokens=False)[0]
    no_id = tok.encode(" No", add_special_tokens=False)[0]
    return bool(logits[yes_id] > logits[no_id])


def scr_answer(model, tok, query: str, kb: SCRIndex, device, k: int, max_new_tokens: int) -> str:
    """Retrieve -> confirm -> answer for one query. Answers the query
    directly (no injected context) if nothing retrieved gets confirmed
    relevant - the gating the paper's whole point is built around."""
    candidates = kb.retrieve(query, k)
    confirmed = [c for c in candidates if _yes_no_confirm(model, tok, query, c, device)]

    if confirmed:
        context = "\n".join(f"Fact: {c}" for c in confirmed)
        prompt = f"{context}\nQuestion: {query}\nAnswer:"
    else:
        prompt = query

    inputs = tok(prompt, return_tensors="pt").to(device)
    with torch.no_grad():
        out = model.generate(
            **inputs, max_new_tokens=max_new_tokens, do_sample=False, pad_token_id=tok.eos_token_id
        )
    return tok.decode(out[0][inputs["input_ids"].shape[1] :], skip_special_tokens=True)


def _matches(answer: str, ground_truths) -> bool:
    """Case-insensitive substring match against one or more accepted
    phrasings - ground_truths may be a string, a flat list, or (as
    produced by eval_utils._flatten_probes) a list of lists."""
    if isinstance(ground_truths, str):
        ground_truths = [ground_truths]
    flat = []
    for g in ground_truths:
        (flat.extend if isinstance(g, list) else flat.append)(g)
    answer_l = answer.lower()
    return any(g and g.lower() in answer_l for g in flat)


# EasyEdit's fluency: n-gram entropy of a 100-token continuation of the edit
# prompt (compute_edit_quality, max_out_len=100). Here the continuation comes
# through this method's own answer path, retrieved context included, since
# that is the text the edited system produces.
FLUENCY_TOKENS = 100


def fluency_score(tok, prompt, generate):
    from easyeditor.evaluate.evaluate_utils import n_gram_entropy

    budget = max(FLUENCY_TOKENS - len(tok(prompt)["input_ids"]), 10)
    return {"ngram_entropy": n_gram_entropy([f"{prompt} {generate(budget)}"])}


def evaluate_requests_scr(
    model,
    tok,
    requests: List[Dict],
    kb: SCRIndex,
    device,
    hparams: SCRHyperParams,
    baseline_answers: Optional[Dict[Tuple[int, str, int], str]] = None,
    answer_cache=None,
    fluency: bool = False,
) -> Tuple[List[Dict], Dict[Tuple[int, str, int], str]]:
    """Same per-record shape eval_utils.aggregate_metrics expects
    (rewrite_acc / portability / locality dicts of *_acc lists), but
    every answer comes from scr_answer() instead of a direct model query.

    Locality here means something different than for FT/ROME: since
    weights never change, the model's answer to an unrelated probe can
    only drift if SCR's own gating/retrieval misfires (incorrectly
    decides an unrelated query is "in scope" and injects irrelevant
    context). So locality_acc compares the current SCR-mediated answer
    against what this same frozen model answered *before* the knowledge
    base had anything in it (baseline_answers, captured at step 0,
    exactly parallel to how FT/ROME capture their step-0 baseline).
    """
    k, max_new_tokens = hparams.retrieval_k, hparams.max_new_tokens
    from semantic_evaluation import cached_answer
    cache = answer_cache if answer_cache is not None else {}
    def answer_query(query):
        return cached_answer(cache, query, lambda: scr_answer(model, tok, query, kb, device, k, max_new_tokens))
    per_record = []
    answers_this_call: Dict[Tuple[int, str, int], str] = {}

    for i, record in enumerate(requests):
        answer = answer_query(record["prompt"])
        rewrite_acc = [1.0 if _matches(answer, record["target_new"]) else 0.0]

        portability = {}
        for cat, probe in record.get("portability", {}).items():
            accs = [
                1.0 if _matches(answer_query(p_prompt), gt) else 0.0
                for p_prompt, gt in zip(probe["prompt"], probe["ground_truth"])
            ]
            if accs:
                portability[f"{cat}_acc"] = accs

        locality = {}
        for cat, probe in record.get("locality", {}).items():
            accs = []
            for j, p_prompt in enumerate(probe["prompt"]):
                loc_answer = answer_query(p_prompt)
                key = (i, cat, j)
                answers_this_call[key] = loc_answer
                if baseline_answers is not None and key in baseline_answers:
                    accs.append(1.0 if loc_answer.strip() == baseline_answers[key].strip() else 0.0)
            if accs:
                locality[f"{cat}_acc"] = accs

        metrics = {"rewrite_acc": rewrite_acc, "portability": portability, "locality": locality}
        if fluency:
            metrics["fluency"] = fluency_score(tok, record["prompt"], lambda budget: scr_answer(
                model, tok, record["prompt"], kb, device, k, budget))
        per_record.append(metrics)

    return per_record, answers_this_call
