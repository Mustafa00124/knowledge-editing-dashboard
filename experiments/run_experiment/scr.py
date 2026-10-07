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
    instruction-following, so it works the same way for base and tuned
    models alike.
  - Answer / match scoring: a single greedy generate() call, scored by
    case-insensitive substring match against the expected answer(s) -
    not EasyEdit's own likelihood-based compute_edit_quality, which
    assumes precise prompt/target token alignment that no longer holds
    once retrieved context has been prepended.
  - Fluency is EasyEdit's n-gram entropy of a continuation of the edit
    prompt, generated through SCR's own answer path with the retrieved
    facts in front (fluency_score below), since that is the text the
    edited system produces.

Since nothing here trains/edits the model, run_experiment.py treats
"step" as "how many facts have been added to SCR's retrievable knowledge
base so far" - the same framing it uses for ROME's sequential edits -
purely so the same checkpoint/progress machinery (and the dashboard's
step-progress bar) works unchanged across methods. With --kb_size the
knowledge base is instead a fixed set of distractor facts, and each record
is asked with only its own fact added to them (see distractor_entries).

Performance note: unlike ROME/FT (one batched forward pass per
checkpoint), this makes several small generate() calls per probe
(one confirm-check per retrieved candidate, plus the answer itself) -
expect SCR checkpoints to be slower than the other two methods.
"""
import glob
import os
import random
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from typing import Callable, Dict, List, Optional, Tuple

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
    # The settings below default to the original behaviour; the SCR
    # investigation sweeps them (see scr_answer() for where each acts).
    # Retrieval: a cosine-similarity floor (None: always return retrieval_k
    # facts), what each fact is found by ("statement": the edit sentence,
    # "subject": its subject alone), and whether a new edit of the same
    # prompt replaces the older one in the knowledge base.
    min_similarity: Optional[float] = None
    kb_key: str = "statement"
    latest_edit_wins: bool = False
    # Confirmation: "each" asks the model Yes/No per candidate, "off" keeps
    # every retrieved fact (plain retrieve-and-answer). A candidate passes
    # when the Yes logit beats No by more than confirm_margin; confirm_shots
    # worked examples go before the question; max_confirmed caps how many
    # facts reach the answer (0: no cap), keeping the most confident.
    confirm: str = "each"
    confirm_margin: float = 0.0
    confirm_shots: int = 0
    max_confirmed: int = 0
    # Answering: where the most similar fact goes ("most_similar_first" or
    # "most_similar_last", nearest the question), whether an instruction
    # tells the model to use the facts ("plain" or "instructed"), and how a
    # query is asked when no fact was confirmed ("bare": the query alone, as
    # originally; "framed": the same Question/Answer framing as with facts).
    fact_order: str = "most_similar_first"
    answer_template: str = "plain"
    no_context_framing: str = "bare"

    @classmethod
    def from_hparams(cls, path):
        if not str(path).endswith(".yaml"):
            path = f"{path}.yaml"
        with open(path) as f:
            cfg = yaml.safe_load(f)
        assert cfg.get("alg_name") == "SCR", f"not an SCR hparams file: {path}"
        return cls(**{k: v for k, v in cfg.items()})

    def to_dict(self):
        return asdict(self)


def build_kb(requests: List[Dict]) -> List[str]:
    """One retrievable statement per request - what SCR is meant to treat
    as newly-known/updated information. Requests already carry the
    subject spelled out in `prompt` (see load_recent_requests), so this
    is just prompt + target_new read as a plain sentence."""
    return [f"{r['prompt']} {r['target_new']}" for r in requests]


def kb_entries(requests: List[Dict], kb_key: str = "statement") -> List[Dict]:
    """build_kb()'s statements with what each is found by and the edit it
    belongs to: {"text", "key", "id"}. kb_key "subject" embeds the subject
    alone (the statement when a record has none, e.g. RealTimeQA); "id" is
    the edit prompt, so a later edit of the same prompt can replace it."""
    if kb_key not in ("statement", "subject"):
        raise ValueError(f"kb_key must be statement or subject, not {kb_key!r}")
    out = []
    for r, text in zip(requests, build_kb(requests)):
        key = (r.get("subject") or text) if kb_key == "subject" else text
        out.append({"text": text, "key": key, "id": " ".join(str(r["prompt"]).lower().split())})
    return out


class SCRIndex:
    """Embeds a growing knowledge base incrementally - `grow()` only
    embeds what's new, so checkpointing SCR every --checkpoint_every
    facts (see run_experiment.py) doesn't re-embed the whole KB each time."""

    def __init__(self, sentence_model_name: str, device):
        self.model = SentenceTransformer(sentence_model_name).to(device)
        self.texts: List[str] = []
        self.ids: List[Optional[str]] = []
        self.embeddings = None

    def grow(self, new_texts: List[str], keys: Optional[List[str]] = None,
             ids: Optional[List[str]] = None, replace: bool = False):
        """Add texts, each found by its key (the text itself by default).
        With replace, a text whose id is already present takes the older
        one's place instead of sitting beside it."""
        if not new_texts:
            return
        keys = keys or new_texts
        ids = ids or [None] * len(new_texts)
        new_emb = self.model.encode(keys, convert_to_tensor=True, show_progress_bar=False)
        if not replace:
            # One concatenation for the lot: row by row is quadratic, which a
            # 10,000-fact distractor base would notice.
            self.texts.extend(new_texts)
            self.ids.extend(ids)
            self.embeddings = new_emb if self.embeddings is None else torch.cat([self.embeddings, new_emb], dim=0)
            return
        for text, emb, item_id in zip(new_texts, new_emb, ids):
            if replace and item_id is not None and item_id in self.ids:
                i = self.ids.index(item_id)
                self.texts[i] = text
                # Rebuilt rather than assigned in place: encode() returns
                # inference-mode tensors, which refuse in-place updates.
                self.embeddings = torch.cat([self.embeddings[:i], emb.unsqueeze(0), self.embeddings[i + 1:]], dim=0)
                continue
            self.texts.append(text)
            self.ids.append(item_id)
            row = emb.unsqueeze(0)
            self.embeddings = row if self.embeddings is None else torch.cat([self.embeddings, row], dim=0)

    def truncate(self, n: int):
        """Drop every entry after the first n (undoes a grow at the end)."""
        if n >= len(self.texts):
            return
        self.texts, self.ids = self.texts[:n], self.ids[:n]
        self.embeddings = self.embeddings[:n] if n else None

    @contextmanager
    def holding(self, entry: Dict):
        """The knowledge base with one more entry for the duration: how a
        record's own fact joins the distractors while it is asked about."""
        size = len(self.texts)
        self.grow([entry["text"]], keys=[entry["key"]], ids=[entry["id"]])
        try:
            yield self
        finally:
            self.truncate(size)

    def retrieve_scored(self, query: str, k: int, min_similarity: Optional[float] = None) -> List[Tuple[str, float]]:
        """Up to k (text, cosine similarity) pairs, most similar first; with
        min_similarity, only those at or above it."""
        if not self.texts:
            return []
        query_emb = self.model.encode(query, convert_to_tensor=True, show_progress_bar=False)
        scores = util.cos_sim(query_emb, self.embeddings)[0]
        top = torch.topk(scores, k=min(k, len(self.texts)))
        pairs = [(self.texts[i], float(s)) for s, i in zip(top.values.tolist(), top.indices.tolist())]
        return [p for p in pairs if min_similarity is None or p[1] >= min_similarity]

    def retrieve(self, query: str, k: int) -> List[str]:
        return [text for text, _ in self.retrieve_scored(query, k)]


# Distractor knowledge bases (--kb_size). A fresh knowledge base holds only
# the fact being asked about, so retrieval is trivial; a weight-edited model
# has to find that fact among everything it already knows. To make SCR find
# it in a crowd too, each record is asked with its own fact added to a fixed
# set of other facts. They are taken nearest first: the same file, then its
# training file, then the general pool below, each in one seeded order, so a
# smaller knowledge base is always a subset of a larger one with the same
# seed. Paths are relative to datasets/; missing files are skipped. The pool
# leaves out RealTimeQA, UnKEBench and EditEverything (not used for editing
# comparisons) and Bi-ZsRE (mostly ZsRE's own records).
GENERAL_DISTRACTOR_SOURCES = (
    "KnowEdit/benchmark/wiki_recent/recent_test.json",
    "KnowEdit/benchmark/wiki_recent/recent_train.json",
    "KnowEdit/benchmark/wiki_counterfact/test_cf.json",
    "KnowEdit/benchmark/wiki_counterfact/train_cf.json",
    "KnowEdit/benchmark/ZsRE/ZsRE-test-all.json",
    "MQuAKE/datasets/MQuAKE-CF.json",
    "MQuAKE/datasets/MQuAKE-T.json",
    "UniEdit/test/*.json",
)


def _source_files(datasets_dir: str, data_path: str) -> List[Tuple[str, List[str]]]:
    """[(tier name, files)] nearest first, each file listed once."""
    same = os.path.abspath(data_path)
    train = same.replace("test", "train")
    tiers = [("same dataset", [same])]
    if train != same and os.path.exists(train):
        tiers.append(("its training file", [train]))
    seen = {f for _, files in tiers for f in files}
    general = []
    for pattern in GENERAL_DISTRACTOR_SOURCES:
        for path in sorted(glob.glob(os.path.join(datasets_dir, pattern))):
            path = os.path.abspath(path)
            if path not in seen:
                seen.add(path)
                general.append(path)
    tiers.append(("general pool", general))
    return tiers


def distractor_entries(data_path: str, evaluated: List[Dict], n: int, seed: int,
                       load: Callable[[str], List[Dict]], datasets_dir: str,
                       kb_key: str = "statement") -> Tuple[List[Dict], Dict[str, int]]:
    """n knowledge-base entries none of which is an evaluated record's fact
    (same edit prompt), and how many came from each tier. load(path)
    returns a file's requests (eval_utils.load_requests). A tier is only
    read once the nearer ones run out."""
    taken: List[Dict] = []
    counts: Dict[str, int] = {}
    seen = {e["id"] for e in kb_entries(evaluated, kb_key)}
    rng = random.Random(seed)
    for tier, files in _source_files(datasets_dir, data_path):
        if len(taken) >= n:
            break
        pool = []
        for path in files:
            try:
                requests = load(path)
            except Exception as exc:  # an unreadable source shrinks the pool, it does not stop the run
                print(f"distractors: skipping {path}: {exc}")
                continue
            for entry in kb_entries(requests, kb_key):
                if entry["id"] not in seen:
                    seen.add(entry["id"])
                    pool.append(entry)
        rng.shuffle(pool)
        chosen = pool[:n - len(taken)]
        taken.extend(chosen)
        if chosen:
            counts[tier] = len(chosen)
    if len(taken) < n:
        raise ValueError(f"only {len(taken)} distractor facts available, {n} needed")
    return taken, counts


# Worked examples for confirm_shots, about invented places so they cannot
# overlap any dataset: one relevant candidate, one not.
CONFIRM_EXAMPLES = (
    "Query: Who is the head of state of Veltria?\n"
    "Candidate fact: The head of state of Veltria is Mara Quill.\n"
    "Is the candidate fact relevant to answering the query? Answer Yes or No.\n"
    "Answer: Yes\n\n",
    "Query: What language is spoken in Ostravel?\n"
    "Candidate fact: The capital of Dunmarch is Selby Reach.\n"
    "Is the candidate fact relevant to answering the query? Answer Yes or No.\n"
    "Answer: No\n\n",
)

DEFAULTS = SCRHyperParams(alg_name="SCR", model_name="", device=0)


def _confirm_score(model, tok, query: str, candidate: str, device, shots: int = 0) -> float:
    """Yes logit minus No logit for "is this fact relevant to the query?"."""
    prompt = "".join(CONFIRM_EXAMPLES[:shots]) + (
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
    return float(logits[yes_id] - logits[no_id])


def _yes_no_confirm(model, tok, query: str, candidate: str, device) -> bool:
    return _confirm_score(model, tok, query, candidate, device) > 0


def select_facts(model, tok, query: str, kb: SCRIndex, device, k: int, hp=None) -> List[str]:
    """Retrieve and confirm: the facts that reach the answer, in the order
    they are shown to the model."""
    hp = hp or DEFAULTS
    candidates = kb.retrieve_scored(query, k, hp.min_similarity)  # most similar first
    if hp.confirm == "off":
        chosen = [(text, sim) for text, sim in candidates]
    elif hp.confirm == "each":
        scored = [(text, sim, _confirm_score(model, tok, query, text, device, hp.confirm_shots))
                  for text, sim in candidates]
        passed = [row for row in scored if row[2] > hp.confirm_margin]
        if hp.max_confirmed:
            keep = {row[0] for row in sorted(passed, key=lambda row: row[2], reverse=True)[:hp.max_confirmed]}
            passed = [row for row in passed if row[0] in keep]
        chosen = [(text, sim) for text, sim, _ in passed]
    else:
        raise ValueError(f"confirm must be each or off, not {hp.confirm!r}")
    if hp.confirm == "off" and hp.max_confirmed:
        chosen = chosen[:hp.max_confirmed]
    facts = [text for text, _ in chosen]
    if hp.fact_order == "most_similar_last":
        facts.reverse()
    elif hp.fact_order != "most_similar_first":
        raise ValueError(f"fact_order must be most_similar_first or most_similar_last, not {hp.fact_order!r}")
    return facts


def build_prompt(query: str, facts: List[str], hp=None) -> str:
    hp = hp or DEFAULTS
    if facts:
        context = "\n".join(f"Fact: {c}" for c in facts)
        instruction = "Use the facts above to answer the question when they apply.\n" \
            if hp.answer_template == "instructed" else ""
        return f"{context}\n{instruction}Question: {query}\nAnswer:"
    if hp.no_context_framing == "framed":
        return f"Question: {query}\nAnswer:"
    return query


def scr_answer(model, tok, query: str, kb: SCRIndex, device, k: int, max_new_tokens: int, hp=None) -> str:
    """Retrieve -> confirm -> answer for one query. Answers the query
    without injected context if nothing retrieved gets confirmed relevant -
    the gating the paper's whole point is built around. hp carries the
    swept settings (SCRHyperParams); left out, the original behaviour."""
    prompt = build_prompt(query, select_facts(model, tok, query, kb, device, k, hp), hp)

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
    record_scope: Optional[Callable[[int], object]] = None,
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

    record_scope(i), when given, is a context manager the record's probes
    are all answered inside: with --kb_size it adds record i's own fact to
    the distractors. Answers are then cached per record, since the same
    probe can get a different answer from a different knowledge base.
    """
    k, max_new_tokens = hparams.retrieval_k, hparams.max_new_tokens
    from semantic_evaluation import cached_answer
    cache = answer_cache if answer_cache is not None else {}
    current = {"i": None}

    def answer_query(query):
        key = query if record_scope is None else (current["i"], query)
        return cached_answer(cache, key, lambda: scr_answer(model, tok, query, kb, device, k, max_new_tokens, hparams))
    per_record = []
    answers_this_call: Dict[Tuple[int, str, int], str] = {}

    for i, record in enumerate(requests):
        current["i"] = i

        def generate(budget, prompt=record["prompt"]):
            return scr_answer(model, tok, prompt, kb, device, k, budget, hparams)

        with (record_scope(i) if record_scope else _no_scope()):
            per_record.append(_score_record(i, record, answer_query, answers_this_call, baseline_answers,
                                            tok, fluency, generate))
    return per_record, answers_this_call


@contextmanager
def _no_scope():
    yield


def _score_record(i, record, answer_query, answers_this_call, baseline_answers, tok, fluency, generate):
    """One record's metrics, in the per-record shape aggregate_metrics expects."""
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
        metrics["fluency"] = fluency_score(tok, record["prompt"], generate)
    return metrics
