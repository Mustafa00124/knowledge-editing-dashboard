"""Where each dynamic method decided to write, recorded per fact.

For the fixed-layer methods the edit site is a run-level constant, so
hparams.yaml already records it. For these four it is an *outcome* -
arguably the outcome worth studying, since it is what separates them
from ROME/MEMIT - so it has to be recorded per fact rather than per run.

run_experiment.py drains this after every edit group and appends the
records to <run_dir>/locations.jsonl, and folds a per-checkpoint layer
histogram into checkpoints.jsonl. That makes it directly comparable with
results/causal_tracing/traced_layers.json, which records the peak-AIE
layer causal tracing finds for the same model: whether a method's
per-fact choices cluster around the traced layer, and whether the ones
that do not are the edits that fail, is a question the runner can now
answer from its own outputs.

A module-level sink rather than a return value because the apply_*
functions have to keep EasyEdit's (model, weights_copy) signature to
stay drop-in compatible with the LOCATE_AND_EDIT dispatch.
"""
import threading

_LOCK = threading.Lock()
_RECORDS = []


def record(method, prompt, subject, **fields):
    """Log one fact's chosen edit site.

    `fields` is method-specific and deliberately unconstrained: WilKE
    records a single layer plus the scan it rejected, FiNE a list of
    (layer, neuron) pairs, NMKE per-layer kept-neuron counts, FiDAL the
    selected matrices and their Fisher scores.
    """
    with _LOCK:
        _RECORDS.append({"method": method, "prompt": prompt, "subject": subject, **fields})


def drain():
    with _LOCK:
        records = list(_RECORDS)
        _RECORDS.clear()
    return records


def layer_histogram(records):
    """{layer: count} over whatever layers the drained records touched.

    Counts each record once per distinct layer it wrote to, so a FiNE
    record that edited 20 neurons spread over 3 layers contributes 1 to
    each of those 3 - the question being asked is which layers a method
    chooses, not how many parameters it changed there.
    """
    histogram = {}
    for record_ in records:
        layers = record_.get("layers")
        if layers is None:
            layer = record_.get("layer")
            layers = [] if layer is None else [layer]
        for layer in sorted({int(layer) for layer in layers}):
            histogram[layer] = histogram.get(layer, 0) + 1
    return dict(sorted(histogram.items()))
