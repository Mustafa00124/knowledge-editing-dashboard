import pandas as pd, numpy as np, json, os
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400)
T = os.environ.get("HP_ANALYSIS_DIR", "/tmp/hp_analysis") + "/"
rng = np.random.default_rng(0)
s3 = pd.read_pickle(T + "s3.pkl")
P = pd.read_pickle(T + "perrec.pkl")
st = json.load(open("/AAIL/msiddiqui146/knowledge-editing/docs/hparam_step3/state.json"))
MK = ["rw", "para", "gen", "xl", "prop", "spec"]
B = 400
out = []
for (me, mo, se), g in s3.groupby(["method", "model", "setting"]):
    g = g.drop_duplicates("val")
    pk = [p for p in st["picks"] if p["method"] == me and p["model"] == mo and p["setting"] == se]
    if not pk:
        continue
    pk = pk[-1]
    chosen = json.dumps(pk["now"]) if isinstance(pk["now"], list) else pk["now"]
    vals = g.val.tolist()
    sub = P[P.run.isin(g.run) & P.sweep.isin(g.sweep)]
    rids = sorted(sub.rid.unique())
    # arrays pass[v, r, m], n[v, r, m]
    V, R = len(vals), len(rids)
    pa = np.zeros((V, R, 6)); nn = np.zeros((V, R, 6))
    ri = {r: i for i, r in enumerate(rids)}
    run2v = dict(zip(g.run, range(V)))
    for row in sub.itertuples():
        if row.run in run2v and row.metric in MK:
            pa[run2v[row.run], ri[row.rid], MK.index(row.metric)] += row._5
            nn[run2v[row.run], ri[row.rid], MK.index(row.metric)] += row.n
    div = g["div"].values; gram = g["gram"].values
    def score(w):  # w: record weights (R,)
        s = (pa * w[None, :, None]).sum(1) / np.maximum((nn * w[None, :, None]).sum(1), 1e-9)
        obj = s[:, 1:5].mean(1)
        ok = (s[:, 0] >= .9) & (s[:, 5] >= .7) & (div >= .8) & (gram >= .9)
        return obj, ok
    def pickv(obj, ok):
        if not ok.any():
            return None
        return int(np.argmax(np.where(ok, obj, -1)))
    obj0, ok0 = score(np.ones(R))
    p0 = pickv(obj0, ok0)
    ci = vals.index(chosen) if chosen in vals else None
    same = near = none = 0
    for _ in range(B):
        w = np.bincount(rng.integers(0, R, R), minlength=R).astype(float)
        o, k = score(w)
        p = pickv(o, k)
        if p is None:
            none += 1; continue
        same += p == p0
        near += p0 is not None and abs(p - p0) <= 1
    # split-half optimism
    opt = []
    for _ in range(200):
        perm = rng.permutation(R); a = np.zeros(R); a[perm[:R // 2]] = 1; b = 1 - a
        oa, ka = score(a); ob, kb = score(b)
        p = pickv(oa, ka)
        if p is None:
            continue
        opt.append(oa[p] - ob[p])
    order = np.argsort(g.valn.values)
    out.append(dict(method=me, model=mo.split("-")[0], setting=se, V=V, p_same=same / B, p_within1=near / B,
                    p_none=none / B, optimism=100 * np.mean(opt) if opt else np.nan,
                    my_pick_matches=(p0 == ci)))
O = pd.DataFrame(out)
O.to_pickle(T + "boot.pkl")
print(O.round(2).to_string())
print(O[["p_same", "p_within1", "p_none", "optimism"]].describe().round(2))
print(O.groupby("method")[["p_same", "p_within1", "optimism"]].mean().round(2))
print("my rule reproduces state pick:", O.my_pick_matches.mean())
