import pandas as pd, numpy as np, json, os
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400); pd.set_option("display.max_columns", 40)
T = os.environ.get("HP_ANALYSIS_DIR", "/tmp/hp_analysis") + "/"
df = pd.read_pickle(T + "runs2.pkl")
st = json.load(open("/AAIL/msiddiqui146/knowledge-editing/docs/hparam_step3/state.json"))
M8 = ["rw", "para", "gen", "xl", "prop", "spec", "div", "gram"]
# final metrics per pair = last pick with metrics
F = {}
for p in st["picks"]:
    if p.get("met"):
        F[(p["method"], p["model"].split("-")[0])] = p["met"]
F = pd.DataFrame([dict(method=k[0], model=k[1], **{m: 100 * v for m, v in d.items()}) for k, d in F.items()])
F["obj"] = F[["para", "gen", "xl", "prop"]].mean(1)
print("== final metrics, mean over models, per method"); print(F.groupby("method")[M8 + ["obj"]].mean().round(1).sort_values("obj", ascending=False))
print("== per model"); print(F.groupby("model")[M8 + ["obj"]].mean().round(1))
# two-way variance decomposition (no replication): method, model, interaction(residual)
print("== variance shares of final scores (36 cells): method / model / method x model")
for m in M8 + ["obj"]:
    y = F.pivot(index="method", columns="model", values=m)
    y = y.dropna()
    g = y.values.mean(); a = y.mean(1).values - g; b = y.mean(0).values - g
    tot = ((y.values - g) ** 2).sum(); sa = (a ** 2).sum() * y.shape[1]; sb = (b ** 2).sum() * y.shape[0]
    print(f"{m:5s} method {sa/tot:.2f}  model {sb/tot:.2f}  interaction {(tot-sa-sb)/tot:.2f}   sd(cells) {y.values.std():.1f}")
F.to_pickle(T + "final.pkl")

# ---- trade-offs: within method x model correlations over step 2+3 runs (40 edits)
d = df[df.step.isin([2, 3])].copy()
for m in M8 + ["obj"]:
    d[m + "_c"] = d[m] - d.groupby(["method", "model"])[m].transform("mean")
C = d[[m + "_c" for m in M8]].corr().round(2); C.index = C.columns = M8
print("== within-pair correlation of metrics (step 2+3 runs, n=%d)" % len(d)); print(C)
# per family
fam = {"ft": "train", "lora": "train", "loco": "train", "fine": "neuron", "rome": "locate", "alphaedit": "locate",
       "fidal": "locate", "ifmet": "locate", "lti": "locate"}
d["fam"] = d.method.map(fam)
for f, g in d.groupby("fam"):
    c = g[[m + "_c" for m in M8]].corr().round(2); c.index = c.columns = M8
    print("--", f, len(g)); print(c.loc[["rw", "para", "gen", "xl", "prop"], ["rw", "spec", "div", "gram", "prop", "xl"]])
# ---- which gate binds
print("== share of step 2+3 runs failing each gate, and share failing ONLY that gate")
G = {"rw": .9, "div": .8, "gram": .9, "spec": .7}
rows = []
for me, g in d.groupby("method"):
    r = dict(method=me, n=len(g), pass_all=g.passes.mean())
    for k, t in G.items():
        fk = g[k] < t
        others = np.logical_or.reduce([g[o] < tt for o, tt in G.items() if o != k])
        r[k] = fk.mean(); r[k + "_only"] = (fk & ~others).mean()
    rows.append(r)
print(pd.DataFrame(rows).round(2).to_string())
