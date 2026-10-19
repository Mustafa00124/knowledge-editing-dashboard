"""IFMET: Interpretability-guided Furtherance Model Editing in a Transformer
(Zhang et al., "Locate-then-edit for Multi-hop Factual Recall under
Knowledge Editing", ICML 2025, arXiv:2410.06331).

Reimplemented from the paper: no code was released (the authors' page
lists "[Code]" with no link, and GitHub has nothing under the title).

The paper's interpretability finding: in a single-hop query ("The capital
of Spain is") the model recalls the fact at the subject in shallow MLP
layers, which is where locate-then-edit methods write. In a multi-hop query
("The capital of the country Picasso was a citizen of is") the subject is
implicit, resolved mid-sentence, and the fact is read at the *last token*
from *deeper* MLP layers, which those methods never touch. So IFMET edits
twice (Algorithm 1):

    first edit        the edit prompt, at the subject's last token, into the
                      base editor's own shallow layers
    furtherance edit  two-hop prompts that name the subject only through
                      another entity, at the last token, into deep_layers

The two-hop prompts need a "supporting fact" (s', r', s): another entity
s' and a relation r' that lead to the subject s. The paper builds them
either from WikiData or from the model itself (its Appendix D.1 and
Table 8, "w Multimodel"). This uses the model itself, so the edit depends
on nothing but the fact and the model's own knowledge:

  1. Ask the unedited model, few-shot, for a description of the subject
     through another entity ("the country of citizenship of Pablo
     Picasso"), sampling up to n_support distinct candidates.
  2. With verify_support (on by default), ask the model what each
     description refers to and keep only those it resolves to the subject,
     the counterpart of the paper filtering WikiData triples to those the
     model can answer.
  3. Put the description in place of the subject in the edit prompt:
     "The capital of the country of citizenship of Pablo Picasso is" ->
     the new target.

What is faithful: PMET as the base editor, the first edit at the subject
on the base layers, the furtherance edit at the last token of the two-hop
prompts on deeper layers, each a joint closed-form solve over the batch,
1 to 5 two-hop prompts per edit.

What differs:
  - The furtherance edit's last-token position: EasyEdit's MEMIT/PMET
    raise on fact_token "last" ("This is definitely bugged"), so each
    two-hop prompt is passed as its own subject with the template "{}";
    "subject_last" then lands on the prompt's last token.
  - The few-shot prompt and the verification question are this project's
    (the paper's Table 13 prompt fills a <mask> in a two-hop sentence,
    which needs a relation template per dataset that most of ours lack).
  - deep_layers per model: the paper gives GPT-J's [16..20] of 28 layers;
    other depths keep the same relative position (see the hparams files).
"""
from copy import deepcopy
from dataclasses import dataclass, field

from . import base, derived

OWN_KEYS = {"alg_name", "model_name", "device", "deep_layers", "n_support", "verify_support",
            "support_temperature", "support_max_new_tokens", "seed"}

FEW_SHOT = (
    "Each entity is described through another entity it is linked to.\n"
    "Entity: Spain\nDescription: the country of citizenship of Pablo Picasso\n"
    "Entity: Microsoft\nDescription: the company founded by Bill Gates\n"
    "Entity: Paris\nDescription: the capital of France\n"
    "Entity: Michelle Obama\nDescription: the spouse of Barack Obama\n"
    "Entity: Python\nDescription: the programming language created by Guido van Rossum\n"
    "Entity: {subject}\nDescription:"
)
VERIFY = "Q: What is {description}?\nA:"


@dataclass
class IFMETHyperParams:
    alg_name: str
    model_name: str
    device: int
    base_method: str
    deep_layers: list = field(default_factory=list)
    n_support: int = 3
    verify_support: bool = True
    support_temperature: float = 0.7
    support_max_new_tokens: int = 16
    seed: int = 0
    base_config: dict = None
    max_length: int = 40  # read by EasyEdit's evaluator

    @classmethod
    def from_hparams(cls, path):
        own, base_method, base_config = base.load_config(path, "IFMET", OWN_KEYS)
        base_config.update(model_name=own["model_name"], device=own["device"])
        return cls(base_method=base_method, base_config=base_config, **own)

    def to_dict(self):
        fields_ = dict(self.__dict__)
        fields_["base_config"] = dict(self.base_config or {})
        return fields_


def _clean(description, subject):
    description = description.strip().rstrip(".").strip()
    if not description or subject.lower() in description.lower() or len(description.split()) < 3:
        return None  # empty, circular, or too short to name another entity
    return description


def support_descriptions(model, tok, subjects, hparams):
    """{subject: [descriptions]} from the unedited model, verified if asked."""
    prompts = [FEW_SHOT.format(subject=s) for s in subjects]
    sampled = base.generate(model, tok, prompts, hparams.support_max_new_tokens,
                            num_return_sequences=hparams.n_support * 2,
                            temperature=hparams.support_temperature, seed=hparams.seed)
    found = {}
    for subject, candidates in zip(subjects, sampled):
        seen = []
        for text in candidates:
            description = _clean(text, subject)
            if description and description.lower() not in {d.lower() for d in seen}:
                seen.append(description)
        found[subject] = seen
    checked = {s: [] for s in subjects}
    if hparams.verify_support:
        pairs = [(s, d) for s, ds in found.items() for d in ds]
        if pairs:
            answers = base.generate(model, tok, [VERIFY.format(description=d) for _, d in pairs],
                                    hparams.support_max_new_tokens)
            for (subject, description), (answer,) in zip(pairs, answers):
                if subject.lower() in answer.lower():
                    checked[subject].append(description)
    else:
        checked = found
    return {s: checked[s][:hparams.n_support] for s in subjects}, found


def two_hop_prompt(request, description):
    """The edit prompt with the subject replaced by its description."""
    prompt = base.filled_prompt(request)
    subject = request["subject"]
    at = prompt.find(subject)
    phrase = description[0].upper() + description[1:] if at == 0 else description
    return prompt[:at] + phrase + prompt[at + len(subject):]


def apply_ifmet_to_model(model, tok, requests, hparams, copy=False, return_orig_weights=False, **kwargs):
    if copy:
        model = deepcopy(model)
    requests = requests if isinstance(requests, (list, tuple)) else [requests]
    weights_copy = {}

    # Supporting facts come from the model before any edit in this call.
    subjects = list(dict.fromkeys(r["subject"] for r in requests))
    kept, sampled = support_descriptions(model, tok, subjects, hparams)

    first = base.base_hparams(hparams.base_method, hparams.base_config)
    print(f"[IFMET] first edit: {len(requests)} fact(s) into layers {list(first.layers)}")
    model = base.apply_base(hparams.base_method, model, tok, requests, first, return_orig_weights, weights_copy)

    furtherance = []
    for request in requests:
        prompts = [two_hop_prompt(request, d) for d in kept[request["subject"]]]
        furtherance += [{"prompt": "{}", "subject": p, "target_new": request["target_new"]} for p in prompts]
        derived.record("ifmet", prompt=base.filled_prompt(request), subject=request["subject"],
                       sampled=sampled[request["subject"]], kept=kept[request["subject"]], two_hop_prompts=prompts)
    if furtherance:
        deep = base.base_hparams(hparams.base_method, hparams.base_config,
                                 layers=list(hparams.deep_layers), fact_token="subject_last")
        print(f"[IFMET] furtherance edit: {len(furtherance)} two-hop prompt(s) into layers {list(hparams.deep_layers)}")
        model = base.apply_base(hparams.base_method, model, tok, furtherance, deep, return_orig_weights, weights_copy)
    else:
        print("[IFMET] no supporting fact the model could resolve; furtherance edit skipped")
    return model, weights_copy
