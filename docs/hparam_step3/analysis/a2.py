import pandas as pd, numpy as np, json, os, re
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 400)
T = os.environ.get("HP_ANALYSIS_DIR", "/tmp/hp_analysis") + "/"
df = pd.read_pickle(T + "runs2.pkl")
s3 = df[df.step == 3].copy()
s3["setting"] = s3.label.str.extract(r"round \d+[^(]*\(([a-z_A-Z0-9]+)")[0]
print(s3.setting.value_counts())
s3["val"] = s3.apply(lambda r: json.dumps(json.loads(r.overrides).get(r.setting)) if isinstance(json.loads(r.overrides).get(r.setting), list) else json.loads(r.overrides).get(r.setting), axis=1)
def num(v):
    if isinstance(v, str) and v.startswith("["):
        return json.loads(v)[0]
    return float(v)
s3["valn"] = s3.val.map(num)
s3.to_pickle(T + "s3.pkl")
rows = []
for (me, mo, se), g in s3.groupby(["method", "mm", "setting"]):
    g = g.sort_values("valn")
    p = g[g.passes]
    best = p.obj.max() if len(p) else np.nan
    rows.append(dict(method=me, model=mo, setting=se, n=len(g), npass=len(p),
                     obj_range_all=100 * (g.obj.max() - g.obj.min()),
                     obj_range_pass=100 * (p.obj.max() - p.obj.min()) if len(p) else np.nan,
                     plateau=int((p.obj >= best - .03).sum()) if len(p) else 0,
                     rw_range=100 * (g.rw.max() - g.rw.min()), spec_range=100 * (g.spec.max() - g.spec.min()),
                     fails=";".join(sorted({f for fs in g.fails for f in fs.split(",") if f}))))
S = pd.DataFrame(rows)
S.to_pickle(T + "sens.pkl")
print(S.round(1).to_string())
print("\nmedian per setting family")
S["fam"] = S.setting.map(lambda s: "where" if "layer" in s else ("signal" if "nll" in s else ("count" if s in ("neuron_num", "num_steps") else "strength")))
print(S.groupby("fam")[["obj_range_all", "obj_range_pass", "plateau", "npass", "n"]].median())
print(S.groupby("method")[["obj_range_all", "obj_range_pass", "plateau", "npass", "n"]].median())
print(S.groupby("model")[["obj_range_all", "obj_range_pass", "plateau", "npass", "n"]].median())
