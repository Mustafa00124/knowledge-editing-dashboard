import pandas as pd, numpy as np, json, os
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400); pd.set_option("display.max_columns", 40)
T = os.environ.get("HP_ANALYSIS_DIR", "/tmp/hp_analysis") + "/"
st = json.load(open("/AAIL/msiddiqui146/knowledge-editing/docs/hparam_step3/state.json"))
key = lambda v: json.dumps(v) if isinstance(v, list) else None
rows = []
by = {}
for p in st["picks"]:
    by.setdefault((p["method"], p["model"]), []).append(p)
for (me, mo), ps in by.items():
    f = ps[0]
    start = None
    for k, v in f["all"].items():
        if json.loads(k) == f["was"]:
            start = v
    last = [p for p in ps if p.get("obj") is not None][-1]
    nchg = sum(1 for p in ps if p["was"] != p["now"])
    rows.append(dict(method=me, model=mo.split("-")[0], start_obj=100 * start["obj"] if start else np.nan,
                     start_fails=",".join(start["fails"]) if start else "?", final=100 * last["obj"],
                     changed=f"{nchg}/{len(ps)}"))
D = pd.DataFrame(rows)
D["gain"] = D.final - D.start_obj
print(D.round(1).to_string())
print("median gain where start passed:", D[D.start_fails == ""].gain.median().round(1),
      " mean", D[D.start_fails == ""].gain.mean().round(1), " n", (D.start_fails == "").sum())
print(D.groupby("method").gain.mean().round(1))
D.to_pickle(T + "gain.pkl")
