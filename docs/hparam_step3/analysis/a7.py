import pandas as pd, numpy as np, json, os
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400); pd.set_option("display.max_columns", 40)
T = os.environ.get("HP_ANALYSIS_DIR", "/tmp/hp_analysis") + "/"
s3 = pd.read_pickle(T + "s3.pkl")
rows = []
for (me, se), g in s3.groupby(["method", "setting"]):
    models = sorted(g.mm.unique())
    islayer = "layer" in se
    cands = sorted(g.valn.unique())
    best = {m: g[(g.mm == m) & g.passes].obj.max() for m in models}
    res = []
    for v in cands:
        per = {}
        for m in models:
            h = g[g.mm == m]
            if islayer:
                h = h[h.valn == v]
            else:
                d = np.abs(np.log(h.valn / v)); h = h[d <= np.log(1.23)]
                h = h.loc[[d[h.index].idxmin()]] if len(h) else h
            if not len(h):
                per[m] = None; continue
            r = h.iloc[0]
            per[m] = (bool(r.passes), 100 * (best[m] - r.obj) if r.passes and not np.isnan(best[m]) else np.nan)
        cov = [m for m in models if per[m] is not None]
        npass = sum(per[m][0] for m in cov)
        regs = [per[m][1] for m in cov if per[m][0]]
        res.append(dict(v=v, covered=len(cov), npass=npass, max_regret=max(regs) if regs else np.nan,
                        mean_regret=np.mean(regs) if regs else np.nan, detail={m: per[m] for m in cov}))
    R = pd.DataFrame(res)
    full = R[R.covered == len(models)]
    if len(full):
        top = full.sort_values(["npass", "max_regret"], ascending=[False, True]).iloc[0]
        picks = {m: g[(g.mm == m)].valn.iloc[0] for m in models}
        rows.append(dict(method=me, setting=se, models=len(models), shared_value=top.v, passes_on=f"{top.npass}/{len(models)}",
                         max_regret=round(top.max_regret, 1), mean_regret=round(top.mean_regret, 1),
                         detail={m: (p[0], round(p[1], 1) if p[1] == p[1] else None) for m, p in top.detail.items()}))
    else:
        rows.append(dict(method=me, setting=se, models=len(models), shared_value=None, passes_on="no common value tried"))
C = pd.DataFrame(rows)
print(C.to_string())
C.to_pickle(T + "compromise.pkl")
