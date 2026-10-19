"""What a portability editor generated from the model for each fact.

IFMET asks the model for another way to refer to the subject, and LoCo
asks it what follows from the new fact. Those generations decide what the
edit is trained on, so they are part of the result: run_experiment.py
drains this after every edit group into <run_dir>/derived.jsonl, one line
per fact, the same way dynamic/locations.py records edit sites.

A module-level sink for the same reason as locations.py: the apply_*
functions keep EasyEdit's (model, weights_copy) signature.
"""
import threading

_LOCK = threading.Lock()
_RECORDS = []


def record(method, prompt, subject, **fields):
    with _LOCK:
        _RECORDS.append({"method": method, "prompt": prompt, "subject": subject, **fields})


def drain():
    with _LOCK:
        records = list(_RECORDS)
        _RECORDS.clear()
    return records
