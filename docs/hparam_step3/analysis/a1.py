import pandas as pd, numpy as np, json, os, re
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 400)
T = os.environ.get("HP_ANALYSIS_DIR", "/tmp/hp_analysis") + "/"
df = pd.read_pickle(T + "runs.pkl")
G = {"rw": .9, "div": .8, "gram": .9, "spec": .7}
OBJ = ["para", "gen", "xl", "prop"]
M8 = ["rw", "para", "gen", "xl", "prop", "spec", "div", "gram"]
df["obj"] = df[OBJ].mean(axis=1)
df["passes"] = np.logical_and.reduce([df[g] >= t for g, t in G.items()])
df["fails"] = df.apply(lambda r: ",".join(g for g, t in G.items() if r[g] < t), axis=1)
df["mm"] = df.model.str.split("-").str[0]
df.to_pickle(T + "runs2.pkl")

s3 = df[df.step == 3].copy()
# parse which setting each step-3 sweep varied, from label
print(s3.label.drop_duplicates().head(8).tolist())
