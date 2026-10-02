"""Per-step losses a method already computes, saved as it runs.

Writes runs/<run>/loss.jsonl, one line per step, flushed immediately so a
run that crashes keeps everything up to the crash. Nothing is computed for
it: every value is one the method had in hand anyway.

Two kinds of record:
  train         FT, LoRA, CaKE, FiNE: the training loss at each step
                (FT/LoRA: the average over that step's batches; FiNE: per
                epoch of its per-fact optimisation)
  value_vector  ROME, MEMIT, PMET, AlphaEdit, NMKE, WilKE, FiDAL: the
                target-vector optimisation inside EasyEdit, one record per
                gradient step per fact, with its parts and the new answer's
                probability. EasyEdit prints these lines and does not
                return them, so they are read off stdout (see _Tap) rather
                than by patching EasyEdit.
"""
import json
import math
import re
import sys

_handle = None
_fact = {"index": -1, "step": 0}

# EasyEdit's compute_v / compute_z line:
#   loss 3.512 = 3.4 + 0.1 + 0.012 avg prob of [ Rome] 0.0331
_VALUE_LINE = re.compile(
    r"^loss (\S+) = (\S+) \+ (\S+) \+ (\S+) avg prob of \[(.*)\] (\S+)\s*$")
_NEW_FACT = ("Computing right vector", "Computing z")


def _number(text):
    try:
        value = float(text)
    except ValueError:
        return None
    return value if math.isfinite(value) else str(value)


def record(kind, step, loss, **extra):
    if _handle is None:
        return
    # Logging must never take a run down, whatever it is handed.
    try:
        value = loss.item() if hasattr(loss, "item") else loss
        if isinstance(value, float) and not math.isfinite(value):
            value = str(value)  # "nan"/"inf": JSON has no spelling for them
        entry = {"kind": kind, "step": step, "loss": value}
        entry.update(extra)
        _handle.write(json.dumps(entry) + "\n")
        _handle.flush()
    except Exception:
        pass


def new_fact():
    """For methods that optimise one fact at a time (CaKE, FiNE): the index
    to tag that fact's records with."""
    _fact["index"] += 1
    _fact["step"] = 0
    return _fact["index"]


class _Tap:
    """Passes stdout through untouched and records EasyEdit's loss lines."""

    def __init__(self, stream):
        self._stream = stream
        self._pending = ""

    def write(self, text):
        self._stream.write(text)
        self._pending += text
        while "\n" in self._pending:
            line, self._pending = self._pending.split("\n", 1)
            self._line(line)
        return len(text)

    def _line(self, line):
        try:
            self._parse(line)
        except Exception:
            pass  # never break the run's own output

    def _parse(self, line):
        if line.startswith(_NEW_FACT):
            _fact["index"] += 1
            _fact["step"] = 0
            return
        match = _VALUE_LINE.match(line.strip())
        if match:
            _fact["step"] += 1
            loss, nll, kl, decay, target, prob = match.groups()
            record("value_vector", _fact["step"], _number(loss), fact=max(_fact["index"], 0),
                   nll=_number(nll), kl=_number(kl), weight_decay=_number(decay), target_prob=_number(prob))

    def flush(self):
        self._stream.flush()

    def __getattr__(self, name):
        return getattr(self._stream, name)


def start(path):
    """Open the run's loss.jsonl and start reading EasyEdit's loss lines."""
    global _handle
    try:
        _handle = open(path, "w")
    except OSError as exc:
        print(f"[loss_log] not recording losses: {exc}")
        return
    if not isinstance(sys.stdout, _Tap):
        sys.stdout = _Tap(sys.stdout)
