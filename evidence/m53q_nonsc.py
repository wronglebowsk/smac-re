#!/usr/bin/env python3
"""M53q: characterize the non-self-consistent rows (mask_in != processed)."""
import importlib.util
spec = importlib.util.spec_from_file_location("m", "/home/n100/reverse/smac/scripts/m53p_recon_a.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m.init()
print("idx fac pop pool pc budget fresh_mask allowed scan_ran processed delta")
for i in range(76):
    o = m.rebuild(i)
    sc = o["mask_in"] == o["processed"]
    tbl, fresh = m.build_table(i)
    allowed = bin(((~fresh | 1) & 0x1FFFFF & o["mask_in"] | (o["mask_in"] if False else 0))).count("1")
    pool_pc = bin(o["mask_in"]).count("1")
    if not sc:
        obs = list(o["obs"])
        deltas = [(n, o["vec"][f] - obs[f]) for f, n in enumerate(["bc", "c0", "c4", "c8"])
                  if o["vec"][f] != obs[f]]
        print(f"idx {i:2d} fac {o['fac']} pop {o['pop']} pool {o['mask_in']:#x} pc {pool_pc} "
              f"budget {o['budget0']}-> {o['budget_end']} processed {o['processed']:#x} "
              f"proc_pc {bin(o['processed']).count('1')} deltas {deltas}")
print()
o31 = m.rebuild(31)
print("idx 31: mask_in", hex(o31["mask_in"]), "processed", hex(o31["processed"]),
      "sc:", o31["mask_in"] == o31["processed"], "deltas:",
      [(n, o31["vec"][f] - list(o31["obs"])[f]) for f, n in enumerate(["bc","c0","c4","c8"])])
