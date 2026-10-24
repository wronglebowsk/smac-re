#!/usr/bin/env python3
"""Debug build_table(69) against the live table: print per-step inputs."""
import importlib.util, struct
spec = importlib.util.spec_from_file_location("m", "/home/n100/reverse/smac/scripts/m53p_recon_a.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m.init()
tbl, mask = m.build_table(69)
print("computed table:", tbl)
print("computed mask :", hex(mask), " live d30:", hex(m.G["d30"]))
R = m.row(69); fac = R["fac"]
print("fac", fac, "x", R["x"], "y", R["y"], "nunit", m.G.get("nunit"))
# step 8 by hand
s = 8
tx, ty = R["x"] + m.XOFF[s], R["y"] + m.YOFF[s]
print("step8 tile", tx, ty)
u = m.unit_at(tx, ty)
print("unit_at ->", u)
if u >= 0:
    r = m.unit(u)
    print("head", r)
    v = u
    while True:
        rr = m.unit(v)
        print("  +48 walk v=", v, "l48", rr["l48"], "fac", rr["fac"], "xy", rr["x"], rr["y"])
        if rr["l48"] < 0: break
        v = rr["l48"]
    w = v if m.unit(v)["l50"] < 0 else m.unit_head(v)
    print("stack start w=", w)
    while True:
        rr = m.unit(w)
        print("  walk w=", w, "fac", rr["fac"], "w18", hex(rr["w18"]), "b25", hex(rr["b25"]),
              "flag", m._foreign_unit_flag(rr, fac), "rel", hex(m.relation(fac, rr["fac"]) if rr["fac"] >= 0 else -1),
              "l50", rr["l50"])
        if rr["l50"] < 0: break
        w = rr["l50"]
# sanity: unit 106 raw
for uu in (106, 107, 147, 256):
    print("unit", uu, m.unit(uu))
