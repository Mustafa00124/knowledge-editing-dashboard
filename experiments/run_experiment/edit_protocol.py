"""Grouping and aggregation for independent, sequential, and batch edit runs."""

WEIGHT_EDIT_METHODS = {
    "ft", "lora", "rome", "memit", "pmet", "alphaedit",
    # Dynamic locate-and-edit (dynamic/): they change weights like the
    # rest, they just choose where per fact.
    "wilke", "fine", "nmke", "fidal",
}
# Everything whose apply call solves for several facts at once. ROME is
# excluded because it hard-codes request[0]; wilke and fidal because
# their site selection is per fact, so batching would pick one location
# for facts that disagree about where they belong; fine because it has
# no joint solve at all. This mirrors the "mode" field of
# run_experiment.py's LOCATE_AND_EDIT table - test_dynamic_methods.py
# asserts the two do not drift apart.
# Knowledge Neurons and CaKE edit weights one fact per call.
WEIGHT_EDIT_METHODS = WEIGHT_EDIT_METHODS | {"kn", "cake"}
JOINT_BATCH_METHODS = WEIGHT_EDIT_METHODS - {"rome", "wilke", "fine", "fidal", "kn", "cake"}

# Two independent choices, spelled as four modes because that is how a run
# is actually described ("sequential batch of 10, reset every 1000"):
#
#   how many facts per edit call   one (single, sequential)
#                                  many (batch, sequential batch)
#   how much accumulates before
#   the original weights return    one call (single, batch)
#                                  reset_every facts (the sequential pair)
#
# So `single` and `batch` measure an edit in isolation, differing only in
# whether the facts are solved for one at a time or jointly, and the
# sequential pair measure what happens as edits pile up on each other.
EDIT_MODES = {"single", "batch", "sequential", "sequential_batch"}
# Modes whose edit call carries several facts at once, so they need a
# method that can actually solve for several facts at once.
JOINT_MODES = {"batch", "sequential_batch"}
# Modes that accumulate across calls, so `reset_every` means something.
# For the other two the reset is implied by the mode: after every fact for
# single, after every batch for batch.
SEQUENTIAL_MODES = {"sequential", "sequential_batch"}


def validate_protocol(method, mode, reset_every, batch_size):
    if mode is None:
        return  # Preserve the old CLI protocol for historical/manual jobs.
    if method not in WEIGHT_EDIT_METHODS:
        raise ValueError(f"{method} does not edit model weights; choose no edit mode")
    if mode not in EDIT_MODES:
        raise ValueError(f"unknown edit mode: {mode}")
    if mode in JOINT_MODES and method not in JOINT_BATCH_METHODS:
        raise ValueError(f"{method} cannot jointly batch edit facts")
    if mode in JOINT_MODES and batch_size < 1:
        raise ValueError("batch size must be positive")
    if mode in SEQUENTIAL_MODES and reset_every < 1:
        raise ValueError("reset interval must be positive")
    # Only meaningful where both exist: `batch` has no reset interval to
    # exceed, since it resets after every call by definition.
    if mode == "sequential_batch" and batch_size > reset_every:
        raise ValueError("batch size cannot exceed the reset interval")


def edit_groups(request_count, mode, reset_every, batch_size):
    """Yield (start, stop, calls); all indices are zero-based, stop exclusive.

    A group is one span of facts that shares a set of weights: it starts
    from the original model and ends when those weights are restored. The
    calls inside it are the individual apply invocations.
    """
    if mode == "single":
        width = 1
    elif mode == "batch":
        width = batch_size  # one joint call, evaluated, then reset
    else:
        width = reset_every
    call_width = batch_size if mode in JOINT_MODES else 1
    for start in range(0, request_count, width):
        stop = min(start + width, request_count)
        calls = [(i, min(i + call_width, stop)) for i in range(start, stop, call_width)]
        yield start, stop, calls


def average_group_evaluations(rows):
    """Average per-group scores, weighting by the number of edited facts."""
    result = {}
    modes = {mode for row in rows for mode in row.get("evaluations", {})}
    for mode in modes:
        scores = [row["evaluations"][mode] for row in rows if mode in row.get("evaluations", {})]
        values = {}
        for metric in ("edit_succ", "portability", "locality", "fluency"):
            pairs = [(row["group_size"], row["evaluations"][mode].get(metric))
                     for row in rows if mode in row.get("evaluations", {})]
            pairs = [(weight, value) for weight, value in pairs if value is not None]
            values[metric] = sum(weight * value for weight, value in pairs) / sum(weight for weight, _ in pairs) if pairs else None
        if any("coverage" in score for score in scores):
            values["coverage"] = {
                metric: {key: sum(score.get("coverage", {}).get(metric, {}).get(key, 0) for score in scores)
                         for key in ("scored", "total")}
                for metric in ("edit_succ", "portability", "locality")
            }
        result[mode] = values
    return result
