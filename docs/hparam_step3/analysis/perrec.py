"""Per-record pass counts for step 2 and 3 runs -> perrec.pkl"""
import json, glob, os, collections
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
T = os.environ.get("HP_ANALYSIS_DIR", "/tmp/hp_analysis") + "/"
R = "/AAIL/msiddiqui146/knowledge-editing/results/investigations"
df = pd.read_pickle(T + "runs2.pkl")
df = df[df.step.isin([2, 3])]
MAP = {"direct": "rw", "paraphrase": "para", "cross_lingual": "xl", "propositional": "prop",
       "unrelated_near": "spec", "unrelated_far": "spec", "derived": "gen"}

def one(row):
    out = []
    d = f"{R}/{row.inv}/sweeps/{row.sweep}/runs/{row.run}/samples"
    seen = set()
    files = sorted(glob.glob(d + "/sid_step_*.json"))
    known = set()
    try:
        for rec in json.load(open(files[0]))["records"]:
            for key, q in rec["queries"].items():
                if isinstance(q, dict) and q.get("query_type") == "derived" and "worlds" not in q \
                        and (q.get("verdict") or {}).get("label") == "ORIGINAL":
                    known.add((rec["record_id"], key))
    except Exception:
        pass
    for f in files[1:]:
        try:
            js = json.load(open(f))
        except Exception:
            continue
        for rec in js.get("records", []):
            rid = rec["record_id"]
            if rid in seen:
                continue
            seen.add(rid)
            c = collections.defaultdict(lambda: [0, 0])
            for key, q in rec["queries"].items():
                if isinstance(q, dict) and q.get("query_type") == "derived" and (rid, key) not in known:
                    continue
                qs = q if isinstance(q, list) else [q]
                for qq in qs:
                    k = MAP.get(qq.get("query_type"))
                    if k is None or qq.get("score") is None:
                        continue
                    if k == "gen" and qq.get("expected", {}).get("rule") not in (None, "new", "original", "derived") and False:
                        continue
                    c[k][0] += qq["score"]; c[k][1] += 1
            for k, (p, n) in c.items():
                out.append((row.run, row.sweep, rid, k, p, n))
    return out

with ThreadPoolExecutor(16) as ex:
    res = list(ex.map(one, [r for r in df.itertuples()]))
P = pd.DataFrame([x for r in res for x in r], columns=["run", "sweep", "rid", "metric", "pass", "n"])
P.to_pickle(T + "perrec.pkl")
print(len(P), P.rid.nunique())
# validate against run-level scores
agg = P.groupby(["sweep", "run", "metric"])[["pass", "n"]].sum().reset_index()
agg["s"] = agg["pass"] / agg["n"]
w = agg.pivot_table(index=["sweep", "run"], columns="metric", values="s").reset_index()
m = w.merge(df, on=["sweep", "run"], suffixes=("_rec", ""))
for k in ["rw", "para", "gen", "xl", "prop", "spec"]:
    print(k, "corr %.3f  mean abs diff %.3f" % (m[k + "_rec"].corr(m[k]), (m[k + "_rec"] - m[k]).abs().mean()))
