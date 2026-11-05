"""Re-run only the judge's form pass (well-formed English or not) on runs that
are already finished, from the answers they saved, and rewrite the scores that
come from it. Used when the form rubric changes (sid-form-v1 -> v2, 2026-11-04)
or for runs judged before the form pass existed. Nothing is generated again
and no other verdict changes.

    python rejudge_form.py <run_dir> [<run_dir> ...]

Writes, per run: each English answer's "form" in samples/sid_step_*.json, and
the well-formed score in every place the run's other sid scores live (each
sample's metrics, each checkpoints.jsonl row, summary.json's evaluations.sid
and group_results). A run already judged with the current rubric is skipped.
"""
import glob
import json
import os
import sys
import time

import sid_evaluation as SE

J = SE.J


def _set(sid, wf):
    if not sid:
        return
    sid.setdefault("metrics", {})["well_formed"] = wf
    sid["well_formed"] = (wf or {}).get("score")


def rejudge(run_dir, judge):
    summary_path = os.path.join(run_dir, "summary.json")
    with open(summary_path) as f:
        summary = json.load(f)
    info = summary.get("sid_evaluation") or {}
    if info.get("form_rubric") == J.FORM_RUBRIC_VERSION:
        return "already current"
    paths = sorted(glob.glob(os.path.join(run_dir, "samples", SE.SAMPLE_PREFIX + "*.json")))
    if not paths or not (summary.get("evaluations") or {}).get("sid"):
        return "no sid samples"
    payloads = []
    for p in paths:
        with open(p) as f:
            payloads.append(json.load(f))

    jobs, pending = {}, []
    for payload in payloads:
        for entry in payload["records"]:
            for a in entry["queries"].values():
                if a.get("query_type") in SE.ENGLISH and isinstance(a.get("response"), str) and a.get("question"):
                    job = (a["question"], a["response"])
                    jobs.setdefault(job, None)
                    pending.append((a, job))
    keys = list(jobs)
    got = dict(zip(keys, judge.label_form(keys))) if keys else {}
    for a, job in pending:
        a["form"] = dict(got[job])

    ckpt_path = os.path.join(run_dir, "checkpoints.jsonl")
    with open(ckpt_path) as f:
        rows = [json.loads(line) for line in f if line.strip()]
    by_step = {p["step"]: p for p in payloads}
    # group_results hold copies of checkpoint rows' sid blocks: match them by content, before changing any.
    step_of = {json.dumps(r.get("evaluations", {}).get("sid"), sort_keys=True): r["step"]
               for r in rows if r.get("evaluations", {}).get("sid")}

    for path, payload in zip(paths, payloads):
        wf = SE.well_formed([payload])
        _set(payload.get("metrics"), wf)
        with open(path, "w") as f:
            json.dump(payload, f, indent=1, ensure_ascii=False)
    for row in rows:
        sid = row.get("evaluations", {}).get("sid")
        if sid and row["step"] in by_step:
            wf = SE.well_formed([by_step[row["step"]]])
            _set(sid, wf)
            row["well_formed"] = sid["well_formed"]
    with open(ckpt_path, "w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")

    for group in summary.get("group_results") or []:
        sid = group.get("evaluations", {}).get("sid")
        step = step_of.get(json.dumps(sid, sort_keys=True)) if sid else None
        if step in by_step:
            _set(sid, SE.well_formed([by_step[step]]))
    # As finalize: under an edit protocol every group's answers pooled, otherwise the last step's.
    pool = [p for p in payloads if p["step"] != 0] if summary.get("edit_mode") else [payloads[-1]]
    _set(summary["evaluations"]["sid"], SE.well_formed(pool))
    info.update(form_rubric=J.FORM_RUBRIC_VERSION, form_calls=len(keys),
                form_rejudged_at=time.strftime("%Y-%m-%dT%H:%M:%S"))
    summary["sid_evaluation"] = info
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    return f"{len(keys)} answers, well-formed {summary['evaluations']['sid']['well_formed']}"


def main(run_dirs):
    import torch
    judge = SE.load_judge("cuda" if torch.cuda.is_available() else "cpu")
    t0 = time.time()
    for i, run_dir in enumerate(run_dirs, 1):
        try:
            result = rejudge(run_dir, judge)
        except Exception as exc:  # keep going; report at the end of the line
            result = f"ERROR {type(exc).__name__}: {exc}"
        print(f"[{i}/{len(run_dirs)} {time.time() - t0:.0f}s] {run_dir}: {result}", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
