#!/usr/bin/env python3
"""Drive the knowledge-editing dashboard from a shell: what an agent uses
instead of running experiments by hand, so every run shows on its
investigation's progress section. Standard library only. See
dashboard/AGENTS.md for the workflow and the rules.

    python scripts/dash.py types                      experiment types
    python scripts/dash.py fields neuron_tracing      a type's fields (= runner flags)
    python scripts/dash.py investigations             investigations and what runs now
    python scripts/dash.py launch neuron_tracing --label "Qwen3 neurons" --dry-run -- --model qwen3-4b
    python scripts/dash.py launch neuron_tracing --label "Qwen3 neurons" -- --model qwen3-4b
    python scripts/dash.py sweep spec.json --estimate  a hyperparameter sweep (dev records)
    python scripts/dash.py status                     active launches
    python scripts/dash.py status <launch-id> --wait  one launch, until it ends
    python scripts/dash.py cancel <launch-id>
    python scripts/dash.py get /api/hparams/results?investigation=edit_layers
    python scripts/dash.py post /api/hparams/sweeps/edit_layers/<sweep-id>/rerun-failed

Connection: KE_DASHBOARD_URL, else dashboard/backend/.backend_url (written
by the backend when it starts), else the node of your running ke_dashboard
SLURM job, else http://localhost:8000. Token: KE_DASHBOARD_TOKEN, else
dashboard/backend/.agent_token.
"""
import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "dashboard", "backend")
ACTIVE = {"PENDING", "RUNNING", "REQUEUED", "SUSPENDED", "CONFIGURING", "COMPLETING"}


def _read(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return ""


def _slurm_url():
    if not shutil.which("squeue"):
        return ""
    try:
        out = subprocess.run(["squeue", "-h", "--me", "-n", "ke_dashboard", "-t", "RUNNING", "-o", "%N"],
                             capture_output=True, text=True, timeout=10).stdout.split()
    except (OSError, subprocess.SubprocessError):
        return ""
    return f"http://{out[0]}:8000" if out else ""


def base_url():
    return (os.environ.get("KE_DASHBOARD_URL") or _read(os.path.join(BACKEND, ".backend_url"))
            or _slurm_url() or "http://localhost:8000").rstrip("/")


def token():
    value = os.environ.get("KE_DASHBOARD_TOKEN") or _read(os.path.join(BACKEND, ".agent_token"))
    if not value:
        sys.exit("no agent token: set KE_DASHBOARD_TOKEN or start the dashboard backend once "
                 "(it writes dashboard/backend/.agent_token)")
    return value


def call(method, path, body=None, query=None):
    url = base_url() + (path if path.startswith("/api") else "/api" + path)
    if query:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode({k: v for k, v in query.items() if v is not None})
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"x-dashboard-token": token(), "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as res:
            text = res.read().decode()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        try:
            detail = json.loads(detail).get("detail", detail)
        except ValueError:
            pass
        sys.exit(f"{exc.code} from {method} {path}: {detail}")
    except urllib.error.URLError as exc:
        sys.exit(f"cannot reach the dashboard at {base_url()} ({exc.reason}). Is the backend running? "
                 "Set KE_DASHBOARD_URL if it is somewhere else.")
    return json.loads(text) if text else None


def show(value):
    print(json.dumps(value, indent=1, default=str))


# ---------------------------------------------------------------- commands

def cmd_types(args):
    types = call("GET", "/experiment-types")
    if args.json:
        return show([{k: t.get(k) for k in ("name", "label", "description", "script", "out_root")} for t in types])
    for t in types:
        print(f"{t['name']:<18} {t.get('label', '')}  ({t.get('script')})")


def _choices(field):
    if field.get("options"):
        return [o.get("value") for o in field["options"]]
    if field.get("categories"):
        return [m.get("value") for c in field["categories"] for m in c.get("methods", [])]
    if field.get("benchmarks"):
        return [s.get("value") for b in field["benchmarks"] for s in b.get("subsets", [])]
    return None


def cmd_fields(args):
    t = next((t for t in call("GET", "/experiment-types") if t["name"] == args.type), None)
    if not t:
        sys.exit(f"no experiment type {args.type}; see: dash.py types")
    if args.json:
        return show(t["fields"])
    print(f"{t['name']}: {t.get('description', '')}\n")
    for f in t["fields"]:
        line = f"--{f['name']:<18} {f.get('type', ''):<7} default {f.get('default')!r}"
        if f.get("show_when"):
            line += f"  (only when {f['show_when']})"
        print(line)
        if f.get("label"):
            print(f"    {f['label']}" + (f": {f['note']}" if f.get("note") else ""))
        if f.get("cli") is False:
            print("    (recorded with the run, not passed to the runner)")
        choices = _choices(f)
        if choices:
            shown = ", ".join(str(c) for c in choices[:12])
            print(f"    one of: {shown}{' …' if len(choices) > 12 else ''}")


def cmd_investigations(args):
    catalog = call("GET", "/hparams/investigations")
    running = call("GET", "/launches/summary")
    if args.json:
        return show({"investigations": catalog, "running": running})
    for inv in catalog:
        now = running.get(inv["id"])
        busy = f"  [{now['running']} running, {now['waiting']} waiting]" if now else ""
        status = " (planned)" if inv.get("status") == "planned" else " (earlier, results only)" if inv.get("legacy") else ""
        how = "sweep" if inv.get("methods") else "launch"
        print(f"{inv['id']:<20} {inv.get('group', ''):<12} {how:<6} {inv['label']}{status}{busy}")
    for key, label in (("main", "main experiments"), ("in_context", "in-context experiment")):
        if running.get(key):
            print(f"{key:<20} {label}  [{running[key]['running']} running, {running[key]['waiting']} waiting]")


def cmd_launch(args):
    body = {"experiment_type": args.type, "label": args.label or "", "note": args.note or "",
            "args": shlex.join(args.runner_args), "extra_args": args.extra or [],
            "dry_run": args.dry_run, "save_results": not args.trial, "after_ok": args.after or []}
    if args.investigation:
        body["investigation"] = args.investigation
    result = call("POST", "/experiments", body)
    if args.json:
        return show(result)
    if args.dry_run:
        print(f"investigation: {result.get('investigation') or 'main experiments'}")
        print(f"{len(result['runs'])} run(s), {result['gpu_jobs']} on GPU; {result['note']}")
        if result.get("skipped_combinations"):
            print(f"{result['skipped_combinations']} combination(s) skipped (duplicates or unsupported pairings)")
        for run in result["runs"]:
            print(f"\n  {run['run_name']}\n    {run['command']}")
            for b in run.get("blockers") or []:
                print(f"    BLOCKED: {b}")
            if run.get("warning"):
                print(f"    note: {run['warning']}")
        return
    print(f"launched {len(result['jobs'])} job(s) as {result['launch_id']} "
          f"for {result.get('investigation') or 'main experiments'}")
    for job in result["jobs"]:
        print(f"  {job['job_id']}  {job['run_name']}")
    print(f"follow it with: python scripts/dash.py status {result['launch_id']} --wait")


def cmd_sweep(args):
    spec = json.load(sys.stdin if args.spec == "-" else open(args.spec))
    if args.label:
        spec["label"] = args.label
    if args.note:
        spec["note"] = args.note
    if args.estimate:
        return show(call("POST", "/hparams/estimate", spec))
    result = call("POST", "/hparams/sweeps", spec)
    if args.json:
        return show(result)
    print(f"launched sweep {result['sweep_id']}: {result['submitted']} run(s)"
          + (f", {len(result['skipped'])} skipped" if result.get("skipped") else ""))
    for e in result.get("errors") or []:
        print(f"  not submitted: {e['run_name']}: {e['error']}")
    print(f"follow it with: python scripts/dash.py status {result['sweep_id']} --wait")


def _line(launch):
    by = " [agent]" if launch.get("launched_by") == "agent" else ""
    pct = f"{round(launch['overall'] * 100)}%"
    states = ", ".join(f"{n} {s.lower()}" for s, n in sorted(launch["states"].items()))
    return (f"{launch['id']}  {launch.get('investigation') or 'main'}  {launch.get('label') or '(no label)'}{by}\n"
            f"    {launch['finished']}/{launch['runs']} finished, {pct}: {states}")


def _print_launch(launch):
    print(_line(launch))
    for run in launch.get("running", []):
        print(f"    running: {run.get('what') or run['run']} ({run.get('activity') or ''})")
    for w in launch.get("waiting", []):
        print(f"    waiting: {w['count']} x {w['text']}")


def cmd_status(args):
    if not args.launch:
        rows = call("GET", "/launches", query={"investigation": args.investigation, "active": str(not args.all).lower(),
                                                "days": args.days, "limit": 50})
        if args.json:
            return show(rows)
        if not rows:
            print("nothing active" if not args.all else "no launches")
        for launch in rows:
            _print_launch(launch)
        return
    while True:
        detail = call("GET", f"/launches/{urllib.parse.quote(args.launch)}")
        launch = detail.get("launch") or {}
        if args.json and not args.wait:
            return show(detail)
        if not args.wait or not launch.get("active"):
            break
        _print_launch(launch)
        time.sleep(args.interval)
    if args.json:
        return show(detail)
    _print_launch(launch)
    for run in detail.get("runs", []):
        state = run.get("state")
        print(f"  {run.get('job_id')}  {str(state).lower():<10} {run.get('run')}")
        if run.get("err_tail"):
            print("      " + "\n      ".join(run["err_tail"].strip().splitlines()[-8:]))
        if run.get("error"):
            print(f"      {run['error']}")
    if args.wait and launch.get("failed"):
        sys.exit(1)


def cmd_cancel(args):
    show(call("POST", f"/launches/{urllib.parse.quote(args.launch)}/cancel"))


def cmd_get(args):
    show(call("GET", args.path))


def cmd_post(args):
    show(call("POST", args.path, json.loads(args.body) if args.body else None))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--json", action="store_true", help="print the raw API response")
    # --json also works after the subcommand.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help="print the raw API response")
    sub = p.add_subparsers(dest="command", required=True)
    _add = sub.add_parser
    sub.add_parser = lambda *a, **k: _add(*a, parents=[common], **k)

    sub.add_parser("whoami").set_defaults(fn=lambda a: show(call("GET", "/whoami")))
    sub.add_parser("types").set_defaults(fn=cmd_types)
    s = sub.add_parser("fields")
    s.add_argument("type")
    s.set_defaults(fn=cmd_fields)
    sub.add_parser("investigations").set_defaults(fn=cmd_investigations)

    s = sub.add_parser("launch", help="launch runs of an experiment type; runner flags go after --",
                       usage="dash.py launch TYPE --label LABEL [options] -- --flag value ...")
    s.add_argument("type")
    s.add_argument("--label", help="what this launch is for (required)")
    s.add_argument("--note", help="why, in a sentence; shown on the progress card")
    s.add_argument("--investigation", help="defaults from the experiment type")
    s.add_argument("--dry-run", action="store_true", help="show the runs and commands without submitting")
    s.add_argument("--trial", action="store_true", help="write to results/main/trial_runs instead of the real results")
    s.add_argument("--extra", action="append", help='a flag the type has no field for, e.g. --extra "--foo 3"')
    s.add_argument("--after", action="append", help="SLURM job id these runs must wait for (succeeded)")
    s.set_defaults(fn=cmd_launch)

    s = sub.add_parser("sweep", help="launch a hyperparameter sweep from a JSON spec (dev records only)")
    s.add_argument("spec", help="JSON file, or - for stdin")
    s.add_argument("--label")
    s.add_argument("--note")
    s.add_argument("--estimate", action="store_true", help="runs and cost, without launching")
    s.set_defaults(fn=cmd_sweep)

    s = sub.add_parser("status")
    s.add_argument("launch", nargs="?")
    s.add_argument("--investigation")
    s.add_argument("--all", action="store_true", help="finished launches too (last --days days)")
    s.add_argument("--days", type=int, default=7)
    s.add_argument("--wait", action="store_true", help="poll until the launch ends; exit 1 if any run failed")
    s.add_argument("--interval", type=int, default=60, help="seconds between polls with --wait")
    s.set_defaults(fn=cmd_status)

    s = sub.add_parser("cancel")
    s.add_argument("launch")
    s.set_defaults(fn=cmd_cancel)

    s = sub.add_parser("get", help="GET any API path and print the JSON")
    s.add_argument("path")
    s.set_defaults(fn=cmd_get)

    s = sub.add_parser("post", help="POST to any API path (optional JSON body) and print the JSON")
    s.add_argument("path")
    s.add_argument("body", nargs="?")
    s.set_defaults(fn=cmd_post)

    # Everything after the first bare -- is the runner's own arguments.
    argv = list(sys.argv[1:] if argv is None else argv)
    runner_args = argv[argv.index("--") + 1:] if "--" in argv else []
    argv = argv[:argv.index("--")] if "--" in argv else argv
    args = p.parse_args(argv)
    args.runner_args = runner_args
    args.fn(args)


if __name__ == "__main__":
    main()
