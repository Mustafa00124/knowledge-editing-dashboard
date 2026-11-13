import pandas as pd, numpy as np, json, os
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400); pd.set_option("display.max_columns", 40)
T = os.environ.get("HP_ANALYSIS_DIR", "/tmp/hp_analysis") + "/"
df = pd.read_pickle(T + "runs2.pkl")
s1 = df[df.step == 1].copy()
# latest step-1 sweep per method x model
last = s1.groupby(["method", "model"]).sweep.max().reset_index()
s1 = s1.merge(last, on=["method", "model", "sweep"])
rows = []
for (me, mo), g in s1.groupby(["method", "model"]):
    ov = g.overrides.map(json.loads)
    keys = sorted({k for o in ov for k in o})
    for k in keys:
        vals = ov.map(lambda o: json.dumps(o.get(k)))
        vc = vals.value_counts()
        if len(vc) < 2:
            continue
        top2 = vc.index[:2].tolist()  # the two corner levels (centre has 3 runs only)
        if vc.iloc[1] < 10:
            continue
        def num(s):
            v = json.loads(s)
            return v[0] if isinstance(v, list) else (v if isinstance(v, (int, float)) else str(v))
        lo, hi = sorted(top2, key=lambda s: (str(type(num(s))), num(s)))
        a = g[vals == hi]; b = g[vals == lo]
        r = dict(method=me, model=mo.split("-")[0], setting=k, lo=lo, hi=hi, n=len(a) + len(b))
        for m in ["obj", "rw", "para", "gen", "xl", "prop", "spec", "div", "gram"]:
            r[m] = 100 * (a[m].mean() - b[m].mean())
        r["pass"] = 100 * (a.passes.mean() - b.passes.mean())
        rows.append(r)
E = pd.DataFrame(rows)
E.to_pickle(T + "step1_effects.pkl")
agg = E.groupby(["method", "setting"]).agg(
    abs_obj=("obj", lambda x: x.abs().mean()), mean_obj=("obj", "mean"),
    sign_agree=("obj", lambda x: max((x > 1.5).sum(), (x < -1.5).sum())),
    abs_rw=("rw", lambda x: x.abs().mean()), abs_spec=("spec", lambda x: x.abs().mean()),
    abs_div=("div", lambda x: x.abs().mean()), d_pass=("pass", "mean"), nmodels=("obj", "size")).round(1)
print(agg.sort_values(["method", "abs_obj"], ascending=[True, False]).to_string())
E["fam"] = E.setting.map(lambda s: "where" if ("layer" in s or s == "target_modules") else
                          "signal" if (("nll" in s) or s in ("constraint", "completion_weight")) else
                          "strength" if s in ("lr", "v_lr", "num_steps", "v_num_grad_steps", "epochs", "lora_alpha",
                                              "early_stop_prob", "neuron_num", "clamp_norm_factor", "norm_constraint",
                                              "nullspace_threshold") else "other")
print(E.groupby("fam")[["obj", "rw", "spec", "div"]].agg(lambda x: x.abs().mean()).round(1))
print(E.groupby("fam").setting.unique())
