#!/usr/bin/env python3
"""Dump the middle-pass candidate table + AI-table (special) loop values for one base,
using the patched model's own scoring, so a swap the game skipped can be localised."""
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("m", "/home/n100/reverse/smac/scripts/m53p_recon_a.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
m.init()

for idx in [int(x) for x in sys.argv[1:]] or [2]:
    R = m.row(idx)
    o = m.rebuild(idx)
    fac, pop = R["fac"], R["pop"]
    fb = m.fac_bits(idx)
    d38 = m.base_dword(idx, 0x38)
    inmask = (m.u8("g985", 0x985b10) >> fac) & 1
    if inmask == 0 or (d38 & 0x80000000) == 0:
        if inmask == 0:
            l38, l28, l24, l3c = (m.frec(0x94D810, fac), m.frec(0x94D814, fac),
                                  m.frec(0x94D818, fac), m.frec(0x94D81C, fac))
            l18 = m.frec(0x94D80C, fac)
        else:
            l38 = l28 = l24 = l3c = l18 = 0
    else:
        l28, l38 = (d38 >> 0x18) & 2, (d38 >> 0x18) & 1
        l24, l3c = (d38 >> 0x19) & 2, (d38 >> 0x1A) & 2
        l18 = 2 if l3c else (0 if (l38 or l24) else (-2 if l28 else m.frec(0x94D80C, fac)))
    vec = [o["seed"][f][1] for f in range(4)]
    for t in o["trace"]:
        if not t[0].startswith("mp-"):
            for f in range(4):
                vec[f] += t[3] * t[2][f]
    mask = o["mask_in"]
    budget = o["budget0"] - bin(mask & ((1 << 21) - 1)).count("1")
    c80, c7c = R["d80"], R["d7c"]
    l5c = budget <= c80 + c7c
    print("== idx %d fac %d pop %d vec %s budget %d c80+c7c %d swapmode %s l18 %d l24 %d l28 %d l38 %d l3c %d"
          % (idx, fac, pop, vec, budget, c80 + c7c, l5c, l18, l24, l28, l38, l3c))
    l54 = 0 if l5c else mask
    gmax, gidx, lval, lidx, maxf0 = 0, 0, -1, 0x270F, 0
    for s in range(1, 21):
        bit = 1 << (s & 0x1F)
        if bit & (l54 | m.G["d30"]):
            print("   s%-3d skip (bit %s in %s|d30)" % (s, hex(bit), hex(l54)))
            continue
        x, y = R["x"] + m.XOFF[s], R["y"] + m.YOFF[s]
        if not (-1 < y < m.G["map_h"] and -1 < x < m.G["map_w"]):
            print("   s%-3d oob (%d,%d)" % (s, x, y))
            continue
        a, b, c = (m.disp(f, fac, idx, x, y, fb) for f in range(3))
        aa, bb, cc, l50 = a, b, c, 0
        if a > maxf0:
            maxf0 = a
        k2 = pop * m.G["k27c"]
        if m.sdiv(budget, m.G["k27c"]) + vec[0] < k2:
            l50 = 2 if (budget + vec[0] >= k2) else 8
            if aa < 0:
                pass
            elif aa <= l50:
                aa = m.s32(aa * 2)
            else:
                aa = m.s32(aa + l50)
        aa, bb, cc = m.s32(aa * 2), m.s32(bb * 2), m.s32(cc * 2)
        if vec[0] <= pop + k2 and aa == 0:
            bb, cc = m.sdiv(bb, 2), m.sdiv(cc, 2)
        if bb == 0 and l50 == 0:
            aa = m.sdiv(aa, 2)
        val = m.final_score(aa, bb, cc, l50, budget, vec, pop, l18, l24, l28, l38, l3c, idx)
        kind = "LOSS" if (mask & bit) else "gain"
        print("   s%-3d (%d,%d) y=%s aa %d bb %d cc %d l50 %d -> %-4d %s" % (s, x, y, (a, b, c), aa, bb, cc, l50, val, kind))
        if mask & bit:
            if val < lval:
                lval, lidx = val, s
        elif val > gmax:
            gmax, gidx = val, s
    print("   => gmax %d gidx %d lval %d lidx %d maxf0 %d" % (gmax, gidx, lval, lidx, maxf0))
    if o["flag"] and pop > 4 and (pop * m.G["k27c"] < vec[0] or maxf0 == 0) and m.G["k85afc"] > 100:
        gv, gi = gmax, gidx
        for k in range(-1, -8, -1):
            def ed(j, k=k):
                # asm:813 (0x4e834f) sets the cursor to 0x926cac, NOT 0x926cb4, so the
                # AI-table read is a direct 0x926cac + k*28 + j*4 (model rebuild does this).
                return m.struct.unpack_from("<i", m._blob["g926"][1],
                                            0x926cac - m.BLOB_BASE["g926"] + k * 28 + j * 4)[0]
            if not (m.tech_avail(ed(-1), fac) and not m.tech_avail(ed(0), fac)):
                continue
            d4 = m.clamp99(vec[2] + c80)
            v = m.s32(ed(2) * 0x40
                      + m.sdiv(m.s32(l24 + 2) * pop * ed(1) * 0x40, d4)
                      + m.sdiv(m.s32(l28 + 2) * pop * ed(3) * 0x40, m.clamp99(vec[2] + c80)))
            print("   AI k%-3d ed=%s v %d %s" % (k, [ed(j) for j in (-1, 0, 1, 2, 3)], v, "BEATS" if v > gv else ""))
            if v > gv:
                gv, gi = v, k
        print("   => after AI loop gmax %d gidx %d" % (gv, gi))
    print("   model trace mp:", [t[0] + "@" + str(t[1]) for t in o["trace"] if t[0].startswith("mp-")])
    print("   model vec %s obs-vec %s obs-ac %s" % (o["vec"], list(o["obs"]),
          m.row(idx)["raw_ac"]))
