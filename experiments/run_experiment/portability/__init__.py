"""Portability editors: methods built to carry an edit into what follows
from it, not just into the edited prompt.

The other locate-and-edit methods write one association, prompt -> target,
and are scored on whether related questions (multi-hop, other forms of the
same rule, logical consequences) change with it. These four make that
propagation part of the edit itself. Each is a parameter edit that uses
only the fact being edited plus the model's own knowledge or a logical
constraint: none retrieves from an external memory at edit or answer time.

    dmle   - rule-level editing: a rule's formula and description are
             written into early layers, its worked instances into middle
             layers, where causal tracing finds each form
             (arXiv:2604.08284, github.com/Pepper66/DMLE).
    ifmet  - a second, "furtherance" edit of deeper MLP layers at the last
             token of two-hop prompts, built by asking the model itself
             for another way to refer to the subject (ICML 2025,
             arXiv:2410.06331; no code released).
    lti    - MEMIT whose target vector is fitted to match how the unedited
             model *reasons* with the new fact in context, at the output
             and at a middle layer (ICLR 2025, arXiv:2410.07819,
             github.com/Acruxos/EVOKE).
    loco   - LoCo-LMs' semantic loss (ICLR 2025, arXiv:2409.13724,
             github.com/ddidacus/loco-llm), turned into an editor: the
             edited fact, its negation, the old answer and implications
             the model draws from the new fact are bound by a logical
             formula whose probability of holding is maximised.

All four keep EasyEdit's apply_<method>_to_model(model, tok, requests,
hparams, copy=..., return_orig_weights=...) -> (model, weights_copy)
contract, so they plug into run_experiment.py's LOCATE_AND_EDIT dispatch
and its weight restoration unchanged. What IFMET and LoCo generate from
the model for each fact is recorded through derived.py.
"""
