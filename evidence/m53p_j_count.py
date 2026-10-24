import sys, importlib
sys.path.insert(0, "scripts")
M = importlib.import_module(sys.argv[1])
M.init()
cnt = {"bc": 0, "c0": 0, "c4": 0, "c8": 0}
full = []; d4 = {}; drow = {}
for i in range(76):
    o = M.rebuild(i)
    ob = list(o["obs"]); ob[0] -= M.G["c6c"] if i == 70 else 0
    ds = {}
    for f, nm in enumerate(["bc", "c0", "c4", "c8"]):
        d = o["vec"][f] - ob[f]; ds[nm] = d
        if d: cnt[nm] += 1
    if ds["c4"]: d4[i] = ds["c4"]
    drow[i] = ds
    if all(v == 0 for v in ds.values()): full.append(i)
print("counts", cnt, "full", len(full))
print("full_list", full)
print("c4 deltas", d4)
j = [i for i, d in drow.items() if d["bc"] == 0 and d["c0"] == 0 and d["c8"] == 0 and d["c4"] != 0]
print("energy-only rows", {i: drow[i]["c4"] for i in sorted(j)})
