"""Build one table of every tuning run (steps 0-3), with full hparams and the 8 scores."""
import json, subprocess, sys
from pathlib import Path
import yaml, pandas as pd

ROOT = Path("/AAIL/msiddiqui146/knowledge-editing")
TMP = Path(sys.argv[1])
INVS = ["locate_edit", "finetuning", "dynamic_locate_edit", "neuron_editors", "portability"]
SKIP = {"P_loc", "data_path", "evaluation_config", "evaluation_modes", "hparam_overrides", "device",
        "model_name", "stats_dir", "results_dir", "run_name", "output_dir"}
rows = []
for inv in INVS:
    f = TMP / f"{inv}.json"
    if not f.exists():
        out = subprocess.run([sys.executable, "scripts/dash.py", "--json", "get",
                              f"/api/hparams/results?investigation={inv}"], cwd=ROOT,
                             capture_output=True, text=True, timeout=300).stdout
        f.write_text(out)
    for r in json.loads(f.read_text()):
        if r.get("step") is None or r.get("state") != "COMPLETED" or r.get("kind") == "setup":
            continue
        rd = ROOT / "results/investigations" / inv / "sweeps" / r["sweep_id"] / "runs" / r["run"]
        try:
            summ = json.loads((rd / "summary.json").read_text())
            m = summ["evaluations"]["sid"]["metrics"]
            hp = yaml.safe_load((rd / "hparams.yaml").read_text())
        except Exception as e:
            continue
        sc = lambda k: None if (m.get(k) or {}).get("score") is None else m[k]["score"] / 100
        s = r["scores"]
        row = dict(inv=inv, sweep=r["sweep_id"], label=r.get("sweep_label"), run=r["run"], step=r["step"],
                   split=r.get("split"), method=r["method"], model=r["model"], nlayers=r.get("model_layers"),
                   seed=summ.get("seed"), ds=summ.get("ds_size"), edit_sec=r.get("edit_sec"),
                   total_sec=r.get("total_sec"), overrides=json.dumps(r.get("overrides")),
                   current=r.get("current_settings"), baseline_copy=r.get("baseline_copy"),
                   rw=s.get("reliability"), para=s.get("paraphrase"), gen=s.get("generalizability"),
                   xl=sc("cross_lingual"), prop=sc("logical_consistency"), div=s.get("fluency"),
                   gram=s.get("well_formed"), spec=s.get("locality"))
        for k, v in hp.items():
            if k in SKIP or isinstance(v, dict):
                continue
            row["hp_" + k] = json.dumps(v) if isinstance(v, list) else v
        rows.append(row)
df = pd.DataFrame(rows)
df.to_pickle(TMP / "runs.pkl")
print(len(df))
print(df.groupby(["step", "method"]).size().unstack(0))
