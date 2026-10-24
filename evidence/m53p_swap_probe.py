#!/usr/bin/env python3
"""For each residual base, ask: can the observed delta be produced by ONE legal
middle-pass action (add-best-gain of s, or swap lidx->gidx) over the legal
candidate set s=1..20, using the model's own per-tile yields?

Prints, per base: the mp state the model computed (budget, c80, c7c, swap-mode,
gmax/gidx, lval/lidx) and the list of candidate tiles that would close the delta.
"""
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("m", "/home/n100/reverse/smac/scripts/m53p_recon_a.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
m.init()

RES = [int(x) for x in sys.argv[1:]] or [1, 3, 6, 7, 9, 15, 16, 18, 31, 35, 47, 52, 61, 63, 70,
                                         2, 19, 23, 38, 41, 43, 45, 53, 58, 59, 60, 62, 65]
NAMES = ["bc", "c0", "c4", "c8"]


def tilev(idx, s):
    R = m.row(idx)
    x, y = R["x"] + m.XOFF[s], R["y"] + m.YOFF[s]
    if not (-1 < y < m.G["map_h"] and -1 < x < m.G["map_w"]):
        return None
    fb = m.fac_bits(idx)
    return [m.disp(f, R["fac"], idx, x, y, fb) for f in range(3)]


for idx in RES:
    R = m.row(idx)
    o = m.rebuild(idx)
    obs = list(o["obs"])
    delta = [o["vec"][f] - obs[f] for f in range(4)]
    d78 = R["d78"]
    mask = o["mask_in"]
    c7c, c80 = R["d7c"], R["d80"]
    print("== idx %d fac %d pop %d flag %d d7c %d d80 %d mask %s budget0 %d end %d c7c_end %d c80_end %d"
          % (idx, R["fac"], R["pop"], o["flag"], c7c, c80, hex(mask), o["budget0"], o["budget_end"],
             o["c7c_end"], o["c80_end"]))
    print("   delta", delta, "processed", hex(o["processed"]))
    # re-run the mp scoring to expose gmax/gidx/lval/lidx at entry state
    vec = list(o["vec"])
    # rebuild vec = seed+scan only (undo mp effects): recompute from trace
    for t in o["trace"]:
        if t[0].startswith("mp-"):
            for f in range(3):
                vec[f] -= t[3] * t[2][f]
    budget = o["budget_end"]
    # recompute scan-only vec properly: sum seed + scan tokens
    vec = [o["seed"][f][1] for f in range(4)]
    for t in o["trace"]:
        if not t[0].startswith("mp-"):
            for f in range(4):
                vec[f] += t[3] * t[2][f]
    processed = 0
    for t in o["trace"]:
        if t[0].startswith("scan"):
            pass
    # scan mask bits actually processed = mask bits 0..20 (scan loop)
    processed = mask & ((1 << 21) - 1)
    budget_scan = o["budget0"] - bin(processed).count("1")
    l5c = budget_scan <= c80 + c7c
    # faction modifier block (rebuild lines 635-650 of m53o_recon.py), replicated here
    d38 = m.base_dword(idx, 0x38)
    inmask = (m.u8("g985", 0x985b10) >> R["fac"]) & 1
    if inmask == 0 or (d38 & 0x80000000) == 0:
        if inmask == 0:
            l38, l28, l24, l3c = (m.frec(0x94D810, R["fac"]), m.frec(0x94D814, R["fac"]),
                                  m.frec(0x94D818, R["fac"]), m.frec(0x94D81C, R["fac"]))
            l18 = m.frec(0x94D80C, R["fac"])
        else:
            l38 = l28 = l24 = l3c = l18 = 0
    else:
        l28, l38 = (d38 >> 0x18) & 2, (d38 >> 0x18) & 1
        l24, l3c = (d38 >> 0x19) & 2, (d38 >> 0x1A) & 2
        if l3c:
            l18 = 2
        elif l38 == 0 and l24 == 0:
            l18 = -2 if l28 else m.frec(0x94D80C, R["fac"])
        else:
            l18 = 0
    gmax, gidx, lval, lidx, maxf0 = m.mp_best(budget_scan, c80, c7c, vec, processed,
                                              0 if l5c else processed, l18, l24, l28, l38, l3c,
                                              R["fac"], idx, R["pop"], m.fac_bits(idx))
    print("   scan-only: budget_after_scan %d c80+c7c %d swapmode %s gmax %d gidx %d lval %d lidx %d maxf0 %d"
          % (budget_scan, c80 + c7c, l5c, gmax, gidx, lval, lidx, maxf0))
    need = [-d for d in delta]
    print("   need (game minus model):", need)
    hits = []
    for s in range(1, 21):
        v = tilev(idx, s)
        if v is None:
            continue
        inmask = bool(processed & (1 << s))
        if tuple(v) == tuple(need[:3]):
            hits.append(("add", s, v, inmask))
        if inmask:
            continue
        for t in range(1, 21):
            w = tilev(idx, t)
            if w is None or not (processed & (1 << t)):
                continue
            net = [v[f] - w[f] for f in range(3)]
            if net == need[:3]:
                hits.append(("swap %d->%d" % (t, s), s, net, inmask))
    for h in hits[:12]:
        print("   candidate:", h)
    if not hits:
        print("   candidate: NONE reproduces the delta")
