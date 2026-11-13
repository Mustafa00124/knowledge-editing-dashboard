import pandas as pd, numpy as np, json, os, re
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 400)
T = os.environ.get("HP_ANALYSIS_DIR", "/tmp/hp_analysis") + "/"
df = pd.read_pickle(T + "runs2.pkl")
M8 = ["rw", "para", "gen", "xl", "prop", "spec", "div", "gram"]
hp = [c for c in df if c.startswith("hp_") and c != "hp_seed"]

# ---- seed noise: step 2 configs run on seeds 0 and 1
s2 = df[df.step == 2].copy()
s2["cfg"] = s2[["method", "model", "overrides"]].astype(str).agg("|".join, axis=1)
pairs = s2.groupby("cfg").filter(lambda g: g.seed.nunique() == 2)
print("step-2 configs with 2 seeds:", pairs.cfg.nunique(), pairs.method.unique())
rows = []
for cfg, g in pairs.groupby("cfg"):
    a = g[g.seed == 0].iloc[0]; b = g[g.seed == 1].iloc[0]
    rows.append(dict(method=a.method, model=a.mm, **{m: abs(a[m] - b[m]) * 100 for m in M8 + ["obj"]},
                     gate_flip=bool(a.passes) != bool(b.passes)))
N = pd.DataFrame(rows)
print("mean |seed0 - seed1| (points); sd of one run = mean|d|/(2/sqrt(pi))/sqrt(2)")
print(N.groupby("method")[M8 + ["obj"]].mean().round(1))
print("overall", N[M8 + ["obj"]].mean().round(1).to_dict(), "gate flips", N.gate_flip.mean().round(2))
sd = N.obj.mean() / (2 / np.sqrt(np.pi)) / np.sqrt(2)
print("implied per-run sd of objective %.2f; expected range of 8 values of a flat setting %.1f; expected max optimism of best-of-8 %.1f" % (sd, 2.85 * sd, 1.42 * sd))

# ---- sampling error from 40 edits: question counts per metric
import glob
r = df[(df.step == 3)].iloc[0]
summ = json.load(open(f"/AAIL/msiddiqui146/knowledge-editing/results/investigations/{r.inv}/sweeps/{r.sweep}/runs/{r.run}/summary.json"))
m = summ["evaluations"]["sid"]["metrics"]
print({k: (v.get("scored"), v.get("total")) for k, v in m.items() if isinstance(v, dict) and "scored" in v})

# ---- step-3 gain: obj at the starting config (round 1 current) vs final
s3 = pd.read_pickle(T + "s3.pkl")
st = json.load(open("/AAIL/msiddiqui146/knowledge-editing/docs/hparam_step3/state.json"))
picks = st["picks"]
print(type(picks), list(picks)[:3] if isinstance(picks, dict) else picks[:2])
