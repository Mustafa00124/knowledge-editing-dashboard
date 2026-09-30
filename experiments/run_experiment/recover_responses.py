"""Recover qualitative samples only; never overwrite metrics or summaries.

Run without --run to process completed runs in isolated subprocesses (context
methods first). Each run uses its recorded hyperparameters. Existing samples
are backed up before replacement; recovered text is explicitly marked.
"""
import argparse
import dataclasses
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RESULTS = ROOT / "results/main/run_experiment"


def needed(run_dir, summary):
    method = summary["method"]
    if method not in ("ike", "scr", "rome", "memit", "pmet", "alphaedit"):
        return False
    path = run_dir / "samples" / f"step_{summary['num_steps']:06d}.json"
    if not path.exists():
        return True
    if method in ("ike", "scr"):
        samples = json.loads(path.read_text())
        return not samples or any(s.get("sampling_version") != 2 for s in samples)
    return False


def recover(run_dir):
    import torch
    import yaml
    from transformers import AutoModelForCausalLM, AutoTokenizer

    sys.path.insert(0, str(ROOT / "external/EasyEdit"))
    from run_experiment import LOCATE_AND_EDIT, _import
    from eval_utils import load_requests
    from response_samples import method_samples

    summary = json.loads((run_dir / "summary.json").read_text())
    if not needed(run_dir, summary):
        return
    cfg = yaml.safe_load((run_dir / "hparams.yaml").read_text())
    method = summary["method"]
    if method == "ike":
        from ike import IKEHyperParams as cls
    elif method == "scr":
        from scr import SCRHyperParams as cls
    else:
        spec = LOCATE_AND_EDIT[method]
        cls = _import(spec["hparams_module"], spec["hparams_class"])
    fields = {f.name for f in dataclasses.fields(cls)}
    hp = cls(**{k: v for k, v in cfg.items() if k in fields})
    hp.device = 0
    torch.manual_seed(cfg["seed"])
    requests = load_requests(cfg["data_path"], cfg["ds_size"])
    step = int(summary["num_steps"])
    if step > len(requests):
        raise ValueError("Recorded final step exceeds available edit records")
    tok = AutoTokenizer.from_pretrained(hp.model_name)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(hp.model_name, torch_dtype=torch.bfloat16).to("cuda:0")
    model.eval()
    index = None
    if method in ("ike", "scr"):
        from scr import SCRIndex, build_kb

        index = SCRIndex(hp.sentence_model_name, "cuda:0")
        if method == "scr":
            for text in build_kb(requests)[:step]:
                index.grow([text])
        else:
            from ike import build_demo_sentences

            demo_path = cfg["data_path"].replace("test", "train")
            if not os.path.exists(demo_path):
                demo_path = cfg["data_path"]
            demos = load_requests(demo_path, cfg["ds_size"])
            if len(demos) < step:
                raise ValueError("Not enough demonstration records to replay final step")
            for record in demos[:step]:
                index.grow(build_demo_sentences([record]))
    else:
        apply_fn = _import(spec["apply_module"], spec["apply_fn"])
        interval = cfg["checkpoint_every"]
        for start in range(0, step, interval):
            batch = requests[start:min(start + interval, step)]
            if spec["mode"] == "single":
                for record in batch:
                    model, _ = apply_fn(model, tok, [record], hp, copy=False)
            else:
                model, _ = apply_fn(model, tok, batch, hp, copy=False)
    samples = method_samples(model, tok, requests, "cuda:0", method, step, hp, index)
    stamp = datetime.now(timezone.utc).isoformat()
    for sample in samples:
        sample["recovered_at"] = stamp
        sample["recovery"] = "replayed recorded configuration; not an original-run capture"
    destination = run_dir / "samples" / f"step_{step:06d}.json"
    destination.parent.mkdir(exist_ok=True)
    if destination.exists():
        backup_dir = run_dir / "sample_backups"
        backup_dir.mkdir(exist_ok=True)
        shutil.copy2(destination, backup_dir / (destination.name + "." + str(os.getpid())))
    temporary = destination.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(samples, indent=2))
    temporary.replace(destination)
    print(f"RECOVERED {run_dir.name} step={step}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--run")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.run:
        recover(args.out_root / "runs" / args.run)
        return
    summaries = [json.loads(p.read_text()) for p in (args.out_root / "runs").glob("*/summary.json")]
    summaries.sort(key=lambda r: (r["method"] not in ("ike", "scr"), r["run"]))
    report = []
    for summary in summaries:
        run = summary["run"]
        if not needed(args.out_root / "runs" / run, summary):
            continue
        print(f"RECOVERY TARGET {run}", flush=True)
        if args.dry_run:
            continue
        result = subprocess.run([sys.executable, __file__, "--out-root", str(args.out_root), "--run", run])
        report.append({"run": run, "exit_code": result.returncode})
        # One report per recovery job; leave prior reports intact.
        (args.out_root / f"response_recovery_{os.environ.get('SLURM_JOB_ID', os.getpid())}.json").write_text(json.dumps(report, indent=2))
    if any(row["exit_code"] for row in report):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
