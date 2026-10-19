"""LoCo: LoCo-LMs' neuro-symbolic consistency loss used as an editor
(Calanzone, Teso & Vergari, "Logically Consistent Language Models via
Neuro-Symbolic Integration", ICLR 2025, arXiv:2409.13724; adapted from
github.com/ddidacus/loco-llm, which has no licence, so nothing is copied).

LoCo-LMs fine-tunes a model so its beliefs satisfy logical constraints.
A fact's belief is the probability the model answers "true" when asked
whether the fact is true. For a formula over facts (an implication A -> B,
a negation A xor not-A), the semantic loss is minus the log of the
probability that the formula holds, summing over every assignment of
truth values that satisfies it, each weighted by the product of the
beliefs (weighted model counting). Upstream fine-tunes on BeliefBank's
facts and rules. Here the facts and constraints come from the edit:

    A    the edited fact ("The capital of Spain is Lisbon."), grounded true
    O    the old fact, where the record has the original answer; a single-
         valued relation cannot hold both, so A and O are exclusive
    N    A's negation ("It is not true that ..."), A xor N
    B_i  implications of the new fact, written by the unedited model
         itself, few-shot, with only the new fact to go on; A -> B_i

    constraint "implication": A and every (A -> B_i)
    constraint "negation":    A, not (A and O), and (A xor N)
    constraint "all":         both

The model is trained to make that formula true, so the edit has to come
with its consequences and without the old answer, rather than as one more
association. LoRA on every linear projection (upstream's r=128, alpha=16,
dropout 0.05), merged into the weights after each call.

What is faithful to upstream:
  - Beliefs as P(label | "... Is the fact true? Fact: <f> Answer: "),
    averaged over LoCo's first two prompt formats ("true"/"false",
    "yes"/"no"); upstream picks one at random per step, which this makes
    deterministic.
  - The semantic loss: -log of the summed probability of the satisfying
    assignments, with a grounded literal fixed to its truth value.
  - LoRA's rank, alpha and dropout, and the learning rate.

What differs:
  - The constraints come from the edit and the model rather than a
    knowledge base of facts and rules: the implications are the model's
    own, and nothing is retrieved at edit or answer time.
  - completion_weight adds FT-M's loss on the edit prompt (cross-entropy on
    the new answer's tokens). LoCo only ever trains truth judgements, and
    an editor is scored on producing the new answer; 0 gives pure LoCo.
  - The negation sentence is a template, where BeliefBank stores a
    hand-written negation of each fact.
  - Upstream loads the model in 4-bit for training; it is trained here in
    the runner's bfloat16.
"""
import itertools
from copy import deepcopy
from dataclasses import asdict, dataclass, field

import torch

from dynamic import hparams_yaml

from . import base, derived

# LoCo-LMs' FORMATS[0] and FORMATS[1] (models/loco/prompts.py).
BELIEF_FORMATS = (
    ('You can answer only with "true" or "false". Is the fact true? Fact: {fact} Answer:', " true"),
    ('You can answer only with "yes" or "no". Is the fact true? Fact: {fact} Answer:', " yes"),
)
NEGATION = "It is not true that {fact}"
IMPLICATIONS = (
    "Each fact is followed by statements that must also be true if the fact is true.\n"
    "Fact: The Eiffel Tower is located in Rome.\n"
    "Implications: The Eiffel Tower is in Italy. | To see the Eiffel Tower you travel to Rome. | "
    "The Eiffel Tower is not in Paris.\n"
    "Fact: Lionel Messi plays for the Chicago Bulls.\n"
    "Implications: Lionel Messi is a basketball player. | Lionel Messi plays in the NBA. | "
    "Lionel Messi's team is based in Chicago.\n"
    "Fact: {fact}\nImplications:"
)
CONSTRAINTS = ("implication", "negation", "all")


@dataclass
class LoCoHyperParams:
    alg_name: str
    model_name: str
    device: int
    constraint: str = "all"
    n_implications: int = 3
    implication_max_new_tokens: int = 60
    completion_weight: float = 1.0
    rank: int = 128
    lora_alpha: int = 16
    lora_dropout: float = 0.05
    target_modules: list = field(default_factory=lambda: [
        "q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"])
    lr: float = 3e-4
    num_steps: int = 25
    seed: int = 0
    max_length: int = 40  # read by EasyEdit's evaluator

    @classmethod
    def from_hparams(cls, path):
        if not str(path).endswith(".yaml"):
            path = f"{path}.yaml"
        config = hparams_yaml.load(path)
        assert config.get("alg_name") == "LoCo", f"not a LoCo hparams file: {path}"
        if config.get("constraint", "all") not in CONSTRAINTS:
            raise ValueError(f"constraint must be one of {CONSTRAINTS}, got {config['constraint']!r}")
        return cls(**config)

    def to_dict(self):
        return asdict(self)


def implications(model, tok, requests, hparams):
    """The unedited model's implications of each new fact, as sentences."""
    if hparams.n_implications < 1:
        return [[] for _ in requests]
    prompts = [IMPLICATIONS.format(fact=base.fact_sentence(r)) for r in requests]
    out = []
    for request, (text,) in zip(requests, base.generate(model, tok, prompts, hparams.implication_max_new_tokens)):
        parts = [p.strip() for p in text.split("|")]
        fact = base.fact_sentence(request).lower()
        found = []
        for part in parts:
            if len(part.split()) < 3 or part.lower() == fact:
                continue
            found.append(part if part.endswith((".", "!", "?")) else part + ".")
        out.append(found[:hparams.n_implications])
    return out


def formula(variables, constraint):
    """The constraint as a predicate over a truth assignment {name: bool}.

    Variables: "A" (the edit, grounded true), optional "O" (old fact),
    "N" (A's negation) and "B0".."Bk" (implications).
    """
    implied = [v for v in variables if v.startswith("B")]

    def holds(world):
        ok = world["A"]  # grounded: the edit is true
        if constraint in ("implication", "all"):
            ok = ok and all((not world["A"]) or world[b] for b in implied)
        if constraint in ("negation", "all"):
            if "O" in world:
                ok = ok and not (world["A"] and world["O"])
            if "N" in world:
                ok = ok and (world["A"] != world["N"])
        return ok
    return holds


def semantic_loss(beliefs, holds):
    """-log sum over satisfying assignments of prod(p or 1-p): LoCo's
    weighted model count, by enumeration (at most a handful of variables)."""
    names = list(beliefs)
    p = torch.stack([beliefs[n] for n in names])
    total = p.new_zeros(())
    for values in itertools.product((False, True), repeat=len(names)):
        world = dict(zip(names, values))
        if holds(world):
            mask = torch.tensor(values, device=p.device)
            total = total + torch.where(mask, p, 1 - p).prod()
    return -torch.log(total + 1e-10)


def _label_probability(model, tok, prompts, label):
    """P(label's first token | prompt), batched, right-padded."""
    device = next(model.parameters()).device
    label_id = tok.encode(label, add_special_tokens=False)[0]
    with base.padding(tok, "right"):
        inputs = tok(prompts, return_tensors="pt", padding=True).to(device)
    logits = model(**inputs).logits.float()
    last = inputs["attention_mask"].sum(1) - 1
    probs = logits[torch.arange(len(prompts), device=device), last].softmax(-1)
    return probs[:, label_id]


def beliefs(model, tok, statements):
    """{name: P(true)} averaged over the belief formats."""
    names = list(statements)
    per_format = []
    for template, label in BELIEF_FORMATS:
        prompts = [template.format(fact=statements[n]) for n in names]
        per_format.append(_label_probability(model, tok, prompts, label))
    mean = torch.stack(per_format).mean(0)
    return {n: mean[i] for i, n in enumerate(names)}


def completion_loss(model, tok, requests):
    """FT-M's loss: cross-entropy on the new answer after the edit prompt."""
    device = next(model.parameters()).device
    total = 0.0
    for request in requests:
        prompt_ids = tok.encode(base.filled_prompt(request), return_tensors="pt").to(device)
        target = str(request["target_new"])
        target_ids = tok.encode(target if target.startswith(" ") else " " + target,
                                add_special_tokens=False, return_tensors="pt").to(device)
        ids = torch.cat([prompt_ids, target_ids], dim=-1)
        logits = model(input_ids=ids).logits.float()
        n = target_ids.shape[-1]
        total = total + torch.nn.functional.cross_entropy(logits[0, -n - 1:-1], target_ids[0])
    return total / len(requests)


def statements_for(request, implied):
    out = {"A": base.fact_sentence(request), "N": NEGATION.format(fact=base.fact_sentence(request))}
    old = request.get("ground_truth")
    if old and str(old).strip() and str(old).strip() != str(request["target_new"]).strip():
        out["O"] = base.fact_sentence({**request, "target_new": old})
    for i, sentence in enumerate(implied):
        out[f"B{i}"] = sentence
    return out


def apply_loco_to_model(model, tok, requests, hparams, copy=False, return_orig_weights=False, **kwargs):
    from peft import LoraConfig, TaskType, get_peft_model

    import loss_log

    if copy:
        model = deepcopy(model)
    requests = requests if isinstance(requests, (list, tuple)) else [requests]

    implied = implications(model, tok, requests, hparams)
    problems = []
    for request, sentences in zip(requests, implied):
        statements = statements_for(request, sentences)
        problems.append((statements, formula(statements, hparams.constraint)))
        derived.record("loco", prompt=base.filled_prompt(request), subject=request.get("subject"),
                       statements=statements, constraint=hparams.constraint)

    originals = {}
    if return_orig_weights:
        suffixes = tuple(f"{module}.weight" for module in hparams.target_modules)
        originals = {name: param.detach().to("cpu", copy=True)
                     for name, param in model.named_parameters() if name.endswith(suffixes)}

    peft_model = get_peft_model(model, LoraConfig(
        r=hparams.rank, lora_alpha=hparams.lora_alpha, lora_dropout=hparams.lora_dropout, bias="none",
        target_modules=list(hparams.target_modules), task_type=TaskType.CAUSAL_LM))
    trainable = [p for p in peft_model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(trainable, lr=hparams.lr, weight_decay=0.0)
    torch.manual_seed(hparams.seed)
    peft_model.train()
    fact_index = loss_log.new_fact()
    for step in range(1, hparams.num_steps + 1):
        sl = torch.stack([semantic_loss(beliefs(peft_model, tok, s), holds) for s, holds in problems]).mean()
        loss = sl
        if hparams.completion_weight:
            loss = loss + hparams.completion_weight * completion_loss(peft_model, tok, requests)
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(trainable, 1.0)
        optimizer.step()
        loss_log.record("train", step, loss, fact=fact_index, semantic=sl.item())
        print(f"[LoCo] step {step}/{hparams.num_steps} loss={loss.item():.4f} semantic={sl.item():.4f}")
    peft_model.eval()
    return peft_model.merge_and_unload(), originals
