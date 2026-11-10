#!/usr/bin/env python3
"""Advance step 3's coordinate descent by itself: run it every few minutes
(the dashboard backend does, see dashboard/backend/periodic.py). Each call
looks at every method x model and, when the sweep of its current setting has
finished:

  1. reruns failed runs once (rerun-failed), and waits for them;
  2. scores the setting's runs with the final selection rule (gates
     rewrite >= 0.9, answer diversity >= 0.8, grammar >= 0.9, specificity
     >= 0.7; objective = mean of paraphrase, generalizability, cross-lingual,
     logical consistency) and picks the value: among passing values within
     3 points of the best, the one closest to the current value; if nothing
     passes, the current value stays and the pick is flagged;
  3. if the pick sits at the edge of the values tried, sweeps once more past
     that edge (one extension per setting) before deciding;
  4. writes the pick to docs/hparam_step3/state.json and picks.md and
     launches the next setting (AlphaEdit layer/threshold settings after a
     projection warm-up sweep).

A method x model is done after its last setting. Idempotent and safe to run
twice: a lock file stops overlapping calls, and before launching it adopts
an existing sweep with the same label. Launch through the dashboard
(scripts/dash.py), run from the project root:

    python3 scripts/step3_advance.py            # one pass
    python3 scripts/step3_advance.py --dry-run  # report only
"""
import argparse
import fcntl
import json
import math
import re
import statistics as st
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import make_step3_specs as M  # noqa: E402

OUT = M.OUT
STATE = M.STATE
PICKS_MD = OUT / "picks.md"
LOCK = ROOT / "dashboard" / "logs" / "step3_advance.lock"
GATES = {"rw": 0.9, "div": 0.8, "gram": 0.9, "spec": 0.7}
OBJ = ["para", "gen", "xl", "prop"]
TIE = 0.03
MAX_EXT = 1
TERMINAL = {"COMPLETED", "FAILED", "CANCELLED", "TIMEOUT", "OUT_OF_MEMORY", "NODE_FAIL"}


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def log(msg):
    print(f"[{now()}] {msg}", flush=True)


def dash(*args):
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "dash.py"), *args], cwd=ROOT,
                       capture_output=True, text=True, timeout=300)
    if r.returncode:
        raise RuntimeError(f"dash.py {' '.join(args)}: {r.stderr.strip() or r.stdout.strip()}")
    return r.stdout


def dash_json(path):
    return json.loads(dash("--json", "get", path))


_sweeps = {}


def sweeps(inv):
    if inv not in _sweeps:
        _sweeps[inv] = dash_json(f"/api/hparams/sweeps?investigation={inv}")
    return _sweeps[inv]


def sweep_by_label(inv, label):
    hits = [s for s in sweeps(inv) if s.get("label") == label and not s.get("hidden")]
    return max(hits, key=lambda s: s["id"]) if hits else None


def sweep_by_id(inv, sid):
    return next((s for s in sweeps(inv) if s["id"] == sid), None)


def finished(s):
    states = s.get("states") or {}
    return s.get("active", 0) == 0 and sum(states.values()) == s.get("runs", 0) and \
        all(k in TERMINAL for k in states)


def launch(spec, name, subdir):
    d = OUT / subdir
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_text(json.dumps(spec, indent=1) + "\n")
    inv = spec["investigation"]
    existing = sweep_by_label(inv, spec["label"])
    if existing:
        log(f"adopt existing sweep {existing['id']}: {spec['label']}")
        return existing["id"]
    out = dash("sweep", str((d / name).relative_to(ROOT)))
    m = re.search(r"launched sweep (\S+):", out)
    if not m:
        raise RuntimeError(f"could not launch {name}: {out}")
    _sweeps.pop(inv, None)
    log(f"launched {m.group(1)}: {spec['label']}")
    return m.group(1)


# ---------------------------------------------------------------- scoring

def run_metrics(inv, row):
    summ = ROOT / "results" / "investigations" / inv / "sweeps" / row["sweep_id"] / "runs" / row["run"] / "summary.json"
    m = json.loads(summ.read_text())["evaluations"]["sid"]["metrics"]
    sc = lambda k: None if (m.get(k) or {}).get("score") is None else m[k]["score"] / 100
    s = row["scores"]
    return dict(rw=s.get("reliability"), para=s.get("paraphrase"), gen=s.get("generalizability"),
                xl=sc("cross_lingual"), prop=sc("logical_consistency"), div=s.get("fluency"),
                gram=s.get("well_formed"), spec=s.get("locality"))


def cells(inv, sweep_ids, setting):
    data = dash_json(f"/api/hparams/results?investigation={inv}")
    rows = data if isinstance(data, list) else data.get("rows") or data.get("results")
    out = {}
    for r in rows:
        if r.get("sweep_id") not in sweep_ids or r.get("state") != "COMPLETED" or setting not in (r.get("overrides") or {}):
            continue
        try:
            met = run_metrics(inv, r)
        except (OSError, KeyError, ValueError):
            continue
        if any(v is None for v in met.values()):
            continue
        out[json.dumps(r["overrides"][setting])] = met
    return out


def distance(a, b):
    if isinstance(a, list):
        return abs(a[0] - b[0])
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and a > 0 and b > 0:
        return abs(math.log(a / b))
    return 0 if a == b else 1


def order_key(v):
    return v[0] if isinstance(v, list) else v


def pick(C, cur):
    """(value, info) by the final rule; value None when nothing passes."""
    scored = []
    for k, met in C.items():
        obj = st.mean(met[x] for x in OBJ)
        fails = [g for g, t in GATES.items() if met[g] < t]
        scored.append(dict(value=json.loads(k), obj=obj, fails=fails, met=met))
    passing = [c for c in scored if not c["fails"]]
    if not passing:
        return None, dict(scored=scored, npass=0)
    best = max(c["obj"] for c in passing)
    near = [c for c in passing if c["obj"] >= best - TIE]
    chosen = min(near, key=lambda c: (distance(c["value"], cur), -c["obj"]))
    return chosen["value"], dict(scored=scored, npass=len(passing), chosen=chosen, best=best)


def extension_values(method, model, setting, chosen, tried):
    """Values past the edge the pick sits on, or [] if it is not at an edge
    (or the edge is the end of the model)."""
    tried_sorted = sorted(tried, key=order_key)
    lo, hi = tried_sorted[0], tried_sorted[-1]
    if chosen not in (lo, hi) or len(tried) < 3:
        return []
    up = chosen == hi
    seen = {json.dumps(v) for v in tried}
    n = M.N_LAYERS[M.SHORT[model]]
    if isinstance(chosen, list):
        width = len(chosen)
        step = 2 if method == "lora" else 1
        starts = [chosen[0] + (i if up else -i) * step for i in range(1, 5)]
        vals = [M.w(s, s + width - 1) for s in starts if 0 <= s and s + width - 1 <= n - 1]
    else:
        ks = range(1, 5) if up else range(-4, 0)
        vals = [M.sig(chosen * 1.5 ** k) for k in ks]
        if setting in M.INTEGER:
            vals = [max(1, round(v)) for v in vals]
    out = []
    for v in vals:
        if json.dumps(v) not in seen and v not in out:
            out.append(v)
    return out


# ---------------------------------------------------------------- state

def load():
    state = M.load_state()
    state.setdefault("progress", {})
    state.setdefault("picks", [])
    return state


def save(state):
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=1) + "\n")
    tmp.replace(STATE)


def fmt(v):
    return M.fmt(v)


def write_picks_md(state):
    lines = ["# Step 3 picks (coordinate descent)", "",
             "Written by `scripts/step3_advance.py` after each setting. Rule: gates (rewrite >= 0.9, answer",
             "diversity >= 0.8, grammar >= 0.9, specificity >= 0.7), then the objective (mean of paraphrase,",
             "generalizability, cross-lingual, logical consistency); within 3 points, the value closest to the",
             "current one. Objective and scores in %.", "",
             "| When | Method | Model | Setting | Was | Now | Objective | Rw | Para | Gen | Xling | Logic | Div | Gram | Spec | Passing | Note |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for p in state["picks"]:
        m = p.get("met") or {}
        g = lambda k: f"{m[k] * 100:.0f}" if k in m else ""
        obj = f"{p['obj'] * 100:.1f}" if p.get("obj") is not None else ""
        lines.append(f"| {p['when']} | {M.LABEL[p['method']]} | {M.SHORT[p['model']]} | `{p['setting']}` | "
                     f"{fmt(p['was'])} | {fmt(p['now'])} | {obj} | {g('rw')} | {g('para')} | {g('gen')} | {g('xl')} | "
                     f"{g('prop')} | {g('div')} | {g('gram')} | {g('spec')} | {p['npass']}/{p['ntried']} | {p.get('note', '')} |")
    done = [f"{M.LABEL[m]} {M.SHORT[md]}" for m, d in state["progress"].items() for md, p in d.items() if p.get("done")]
    lines += ["", f"Done: {len(done)} of {len(M.LABEL) * len(M.MODELS)} method x model pairs.", ""]
    PICKS_MD.write_text("\n".join(lines))


# ---------------------------------------------------------------- advance

def start_setting(state, method, model, idx, ext=0, ext_vals=None):
    """Launch the sweep (and AlphaEdit warm-up) for setting number idx."""
    p = state["progress"][method][model]
    setting = M.order(method, model)[idx]
    cur = state["values"][method][model]
    r = idx + 1
    vals = ext_vals if ext else M.values(method, model, setting, cur[setting])
    p.update(idx=idx, setting=setting, ext=ext, vals=vals, warmup=None, retried=False)
    if not ext:
        p["sweeps"] = []
    if M.needs_warmup(method, setting):
        wspec, wname = M.build_warmup(model, r, M.warmup_swept(setting, vals, cur), ext)
        p["warmup"] = launch(wspec, wname, f"round{r}/warmup")
        p["waiting_for_warmup"] = True
        return
    launch_main(state, method, model)


def launch_main(state, method, model):
    p = state["progress"][method][model]
    r = p["idx"] + 1
    spec, name = M.build_spec(method, model, r, p["setting"], p["vals"], state["values"][method][model], p["ext"])
    p["sweeps"].append(launch(spec, name, f"round{r}/specs"))
    p["waiting_for_warmup"] = False


def init_progress(state):
    """Adopt round 1, launched by make_step3_specs.py --round 1."""
    for method in M.LABEL:
        for model in M.MODELS:
            d = state["progress"].setdefault(method, {})
            if model in d:
                continue
            setting = M.order(method, model)[0]
            cur = state["values"][method][model]
            label = M.label_of(method, model, 1, setting)
            s = sweep_by_label(M.INVESTIGATION[method], label)
            if not s:
                raise RuntimeError(f"round 1 sweep not found: {label}")
            d[model] = dict(idx=0, setting=setting, ext=0, vals=M.values(method, model, setting, cur[setting]),
                            sweeps=[s["id"]], warmup=None, waiting_for_warmup=False, retried=False, done=False)


def step(state, method, model, dry):
    p = state["progress"][method][model]
    if p.get("done"):
        return False
    inv = M.INVESTIGATION[method]
    if p.get("waiting_for_warmup"):
        w = sweep_by_id("locate_edit", p["warmup"])
        if w and finished(w):
            if not dry:
                launch_main(state, method, model)
            return True
        return False
    ss = [sweep_by_id(inv, sid) for sid in p["sweeps"]]
    if any(s is None or not finished(s) for s in ss):
        return False
    failed = sum((s.get("states") or {}).get("FAILED", 0) for s in ss)
    if failed and not p.get("retried"):
        if not dry:
            for s in ss:
                if (s.get("states") or {}).get("FAILED"):
                    dash("--json", "post", f"/api/hparams/sweeps/{inv}/{s['id']}/rerun-failed")
            p["retried"] = True
            _sweeps.pop(inv, None)
            log(f"rerun failed runs: {method} {model} {p['setting']} ({failed})")
        return True
    setting = p["setting"]
    cur = state["values"][method][model][setting]
    C = cells(inv, set(p["sweeps"]), setting)
    chosen, info = pick(C, cur)
    tried = [json.loads(k) for k in C]
    note = []
    if failed:
        note.append(f"{failed} runs failed twice")
    if chosen is not None and p["ext"] < MAX_EXT:
        ext_vals = extension_values(method, model, setting, chosen, tried)
        if ext_vals:
            log(f"{method} {model} {setting}: pick {fmt(chosen)} at the edge, extending with {ext_vals}")
            if not dry:
                start_setting(state, method, model, p["idx"], ext=p["ext"] + 1, ext_vals=ext_vals)
            return True
    if chosen is None:
        note.append("nothing passed the gates: kept the current value")
        chosen = cur
    elif chosen in (min(tried, key=order_key), max(tried, key=order_key)) and len(tried) >= 3:
        note.append("still at the edge after the extension" if p["ext"] else "at the end of the usable range")
    ch = info.get("chosen")
    rec = dict(when=now(), method=method, model=model, setting=setting, round=p["idx"] + 1, was=cur, now=chosen,
               obj=ch["obj"] if ch else None, met=ch["met"] if ch else None, npass=info["npass"], ntried=len(C),
               best_obj=info.get("best"), sweeps=list(p["sweeps"]), note="; ".join(note),
               all={json.dumps(c["value"]): dict(obj=round(c["obj"], 4), fails=c["fails"]) for c in info["scored"]})
    log(f"pick {method} {model} {setting}: {fmt(cur)} -> {fmt(chosen)} ({info['npass']}/{len(C)} pass) {rec['note']}")
    if dry:
        return False
    state["values"][method][model][setting] = chosen
    state["picks"].append(rec)
    nxt = p["idx"] + 1
    if nxt >= len(M.order(method, model)):
        p["done"] = True
        log(f"done: {method} {model}")
    else:
        start_setting(state, method, model, nxt)
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    dry = ap.parse_args().dry_run
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    with open(LOCK, "w") as fh:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            log("another advance is running; skip")
            return
        state = load()
        if state.get("all_done"):
            return
        init_progress(state)
        if not dry:
            save(state)
        changed = False
        for method in M.LABEL:
            for model in M.MODELS:
                try:
                    changed |= step(state, method, model, dry)
                except Exception as e:  # one pair's problem must not stop the others
                    log(f"ERROR {method} {model}: {e!r}")
                if changed and not dry:
                    save(state)
        if all(p.get("done") for d in state["progress"].values() for p in d.values()):
            state["all_done"] = True
            log("step 3 finished for every method and model")
        if not dry:
            save(state)
            write_picks_md(state)


if __name__ == "__main__":
    main()
