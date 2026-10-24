#!/usr/bin/env python3
"""Test A: is the live vector exactly seed + sum of per-tile yields over the LIVE d78 mask?

If yes for a base, the game's rebuild scanned exactly the live-mask steps and the
model's per-tile yield functions (disp) are correct: the divergence is purely about
WHICH spiral steps are in the mask (the DAT_008f0d30 blocked-step rule).

    python3 scripts/m53p_j_testa.py            # all bases
    python3 scripts/m53p_j_testa.py 1 70       # subset
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m53p_recon_a as M


def main():
    idxs = [int(a) for a in sys.argv[1:] if a.isdigit()]
    M.init()
    nb = M.G["nbases"]
    if not idxs:
        idxs = list(range(nb))
    hits = 0
    rows = []
    for i in idxs:
        R = M.row(i)
        fac, pop = R["fac"], R["pop"]
        fb = M.fac_bits(i)
        bx, by = R["x"], R["y"]
        # seed exactly as the model's rebuild does
        vec = []
        for f in range(4):
            v = M.s32v("facrec", 0x94DC34 + fac * 0x20BC + f * 4)
            if not fb[0x1D] and (M.G["spec_base"] < 0 or
                                 M.blob_at("bases", M.BLOB_BASE["bases"] + M.G["spec_base"] * 0x130 + 4, 1)[0] != fac):
                v = M.sdiv(v + 1, 2)
            vec.append(min(v, pop))
        mask = R["d78"] & 0xFFFFF  # steps 0..19 only (scan cap is 21 -> 0..20)
        extra = 0
        per = {}
        for s in range(21):
            if not (R["d78"] >> s) & 1:
                continue
            x, y = M.wrap_x(bx + M.XOFF[s]), by + M.YOFF[s]
            if -1 < y < M.G["map_h"] and -1 < x < M.G["map_w"]:
                d = [M.disp(f, fac, i, x, y, fb) for f in range(4)]
                for f in range(4):
                    vec[f] += d[f]
                per[s] = d
            else:
                per[s] = "oob"
        obs = R["vec"]
        ok = all(vec[f] == obs[f] for f in range(4))
        hits += ok
        rows.append((i, fac, pop, hex(R["d78"]), "OK " if ok else "DIFF", vec, obs,
                     sum(1 for s in per if per[s] != "oob"), sum(1 for s in per if per[s] == "oob")))
        print("idx %2d fac %d pop %2d mask %s steps %d/%s %s pred %s obs %s" %
              (i, fac, pop, hex(R["d78"]), sum(1 for s in per if per[s] != "oob"),
               bin(R["d78"]).count("1"), "OK " if ok else "DIFF", vec, obs))
    print("== seed+yield(live mask) reproduces the live vector on %d/%d bases" % (hits, len(idxs)))
    return rows


main()
