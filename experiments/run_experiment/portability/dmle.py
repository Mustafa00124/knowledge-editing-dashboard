"""DMLE: Distributed Multi-Layer Editing for rule-level knowledge
(arXiv:2604.08284), ported from github.com/Pepper66/DMLE (run_new.py at
commit 9d8415b).

A rule (a rectangle's area is x * y) appears in three forms: a formula, a
verbal description, and worked instances. The paper's causal tracing finds
formula and description stored together in early layers and instances in
middle layers, so one MEMIT edit over a single band of layers cannot reach
all three. DMLE runs MEMIT twice, cumulatively:

    stage f_d  the formula and description records, jointly, into
               formula_description_layers (the paper's shared update)
    stage ins  the instance records into instance_layers

What is faithful to upstream:
  - MEMIT's closed-form update for both stages, with the base config
    unchanged apart from `layers` (run_new.py sets hparams.layers per
    stage and calls EasyEdit's apply_algo once per stage).
  - Stage order f_d then ins, the second applied on top of the first.
  - Which records go to which stage: upstream reads f_d.json and ins.json
    per rule; datasets/RuleEdit-200/build_editing_set.py keeps that split
    as each record's `form`.

What differs:
  - Upstream edits one rule per run. Here a call edits whatever records
    the edit protocol hands it: a batch of 3 is exactly one rule, a single
    edit is one form of a rule on its own layer group.
  - Upstream leaves the layer groups to a config.json the user writes; the
    paper reports the traced peaks for GPT-J, Qwen2, Qwen2.5 and Llama-3.
    Each hparams file says where its groups come from.
"""
from copy import deepcopy
from dataclasses import dataclass

from . import base

FORMULA_DESCRIPTION = ("formula", "description")
INSTANCE = ("instance",)
OWN_KEYS = {"alg_name", "model_name", "device", "formula_description_layers", "instance_layers"}


@dataclass
class DMLEHyperParams:
    alg_name: str
    model_name: str
    device: int
    base_method: str
    formula_description_layers: list
    instance_layers: list
    base_config: dict = None
    max_length: int = 40  # read by EasyEdit's evaluator

    @classmethod
    def from_hparams(cls, path):
        own, base_method, base_config = base.load_config(path, "DMLE", OWN_KEYS)
        if base_method != "memit":
            raise ValueError("DMLE is MEMIT's update applied per layer group; base_method must be memit")
        base_config.update(model_name=own["model_name"], device=own["device"])
        return cls(base_method=base_method, base_config=base_config, **own)

    def to_dict(self):
        fields = dict(self.__dict__)
        fields["base_config"] = dict(self.base_config or {})
        return fields


def stages(requests, hparams):
    """[(stage name, layers, records)] in upstream's order, empty stages left out."""
    unknown = [r for r in requests if r.get("form") not in FORMULA_DESCRIPTION + INSTANCE]
    if unknown:
        raise ValueError(
            "DMLE edits rule-level knowledge by form (formula, description, instance), and these records "
            f"carry no form: {[r.get('prompt') for r in unknown[:3]]}. Only RuleEdit-200 provides forms.")
    plan = [("f_d", hparams.formula_description_layers, [r for r in requests if r["form"] in FORMULA_DESCRIPTION]),
            ("ins", hparams.instance_layers, [r for r in requests if r["form"] in INSTANCE])]
    return [stage for stage in plan if stage[2]]


def apply_dmle_to_model(model, tok, requests, hparams, copy=False, return_orig_weights=False, **kwargs):
    if copy:
        model = deepcopy(model)
    requests = requests if isinstance(requests, (list, tuple)) else [requests]
    weights_copy = {}
    for name, layers, records in stages(requests, hparams):
        print(f"[DMLE] stage {name}: {len(records)} record(s) into layers {list(layers)}")
        stage_hparams = base.base_hparams("memit", hparams.base_config, layers=list(layers))
        model = base.apply_base("memit", model, tok, records, stage_hparams, return_orig_weights, weights_copy)
    return model, weights_copy
