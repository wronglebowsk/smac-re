#!/usr/bin/env python3
"""M53q: per-row comparison of the fresh per-base mask (build_table) vs the dump's
global DAT_008f0d30, and whether either actually clears a bit of the stored pool."""
import importlib.util
spec = importlib.util.spec_from_file_location("m", "/home/n100/reverse/smac/scripts/m53p_recon_a.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m.init()
live_i = m.G["base_idx"]
print("live cur base idx", live_i, " live d30", hex(m.G["d30"]))
n_fresh_ne_stale = n_clear_fresh = n_clear_stale = 0
for i in range(76):
    R = m.row(i)
    tbl, fresh = m.build_table(i)
    stale = m.G["d30"]
    pool = R["d78"]
    cleared_fresh = pool & fresh & ~1
    cleared_stale = pool & stale & ~1
    if fresh != stale:
        n_fresh_ne_stale += 1
    if cleared_fresh:
        n_clear_fresh += 1
    if cleared_stale:
        n_clear_stale += 1
    flag = ""
    if i == live_i:
        flag = " <== LIVE CUR BASE"
    if cleared_fresh or cleared_stale or i == live_i:
        print(f"idx {i:2d} fac {R['fac']} pool {pool:#010x} fresh {fresh:#010x} stale {stale:#010x} "
              f"fresh_clears {cleared_fresh:#x} stale_clears {cleared_stale:#x}{flag}")
print(f"\nrows where fresh != stale: {n_fresh_ne_stale}/76")
print(f"rows where the fresh filter clears a pool bit: {n_clear_fresh}/76")
print(f"rows where the stale filter clears a pool bit: {n_clear_stale}/76")
