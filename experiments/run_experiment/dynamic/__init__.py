"""Dynamic locate-and-edit methods: the editing site is chosen per fact.

Every method registered in run_experiment.py's LOCATE_AND_EDIT table so
far (ROME/MEMIT/PMET/AlphaEdit) edits a layer set fixed in
hparams/<METHOD>/<model>.yaml - the same layers for every fact in the
run. The four methods here instead decide *where* to write separately
for each fact:

    wilke  - scans candidate layers, picks the one whose ROME-style
             rank-one update is smallest relative to the layer's own
             weight norm (ACL Findings 2024, arXiv:2402.10987).
    fine   - scores individual FFN neurons across all layers by their
             contribution to the target token, edits the top-k
             (ICLR 2025, arXiv:2503.01090).
    nmke   - AlphaEdit's closed-form update, masked down to the neurons
             an entropy-adaptive attribution rule keeps
             (NeurIPS 2025, arXiv:2510.22139).
    fidal  - a *locator*, not an editor: probes candidate weight
             matrices with low-rank modulation, ranks them by Fisher
             Information, and hands the top-K to an existing closed-form
             editor (ACL 2026, aclanthology.org/2026.acl-long.957).

All four expose the same apply_<method>_to_model(model, tok, requests,
hparams, copy=..., return_orig_weights=...) -> (model, weights_copy)
contract EasyEdit uses, so they plug into LOCATE_AND_EDIT unchanged and
the runner restores weights between edit groups exactly as before.

Where each method's reference implementation depended on a patched
transformers modeling file (FiNE's model.set_get_activations(), NMKE's
modeling_llama.py), capture.py reproduces the same quantities with
forward hooks instead - see that module for why.
"""
