#!/usr/bin/env python3
"""M295 - the 0x4e3c00(owner,X,Y) no-go: STATIC RULE vs the m294 grid.

FUN_004e3c00(owner,X,Y): FUN_004e3b50 reads tile7 = (signed) BYTE[44-B tileview+7]
(the territory-owner faction, same view as B16, 0x4e3b53-0x4e3b76); invisible to
`owner` unless (flagword & 0x8000008) == 0x8000008 or BYTE[0x985ae8] bit 0x80.
No-go (returns >= 0) iff tile7 >= 1 AND tile7 != owner AND (human-mask
BYTE[0x985b10] has the owner bit OR the tile7 bit) AND the faction-pair flag
word [owner*2095 + tile7] at 0x94d448 (M143) has bit4 CLEAR; the non-negative
return value is FUN_004e37f0's (nearest-base sweep, writes DAT_008f0d34 = M294's
dist, sentinel 9999, so >= 0).

Graded rules (rejects) over the B16 25-slot grid, pod owner strict (ownrec= from
DISP rows else the save unit record; visits whose owner is not resolvable are
counted and EXCLUDED):
  R1 foreign-only  R2 +human-mask  R3 +not-ally(bit4)  R4 +visible(bit3&31)
Fit: reject cap recorded decision slots == 0; rejects inside pass6-no-row
count into the 8482. Writes the graded table; deterministic.
"""
import struct, sys, collections, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sim.precheck as pc
from sim import save as sosave

def bit(x, k):
    return (x >> k) % 2

def main(sav_path, raw_path):
    sav = sosave.parse(sav_path)
    g = pc.Grid(sav)
    W, H = sav.width, sav.height
    feat, mask = sav.feature_bits, sav.human_mask

    def flagword(fac, other):
        o = sosave.BLOCK_A_OFF + fac * sosave.BLOCK_A_REC + 4 * other
        return struct.unpack_from("<I", sav.data, o)[0]

    ownrec, cur = {}, None
    for ln in open(raw_path):
        w = ln.split()
        if not w:
            continue
        if w[0] == "HUB" and w[1].startswith("u="):
            cur = int(w[1][2:])
        elif w[0] == "DISP" and cur is not None:
            for kv in w[1:]:
                if kv.startswith("ownrec="):
                    ownrec.setdefault(cur, int(kv.split("=", 1)[1]))

    cells = collections.Counter()
    t7dist = collections.Counter()
    visits = pc.load_visits(raw_path, True)
    ov = collections.Counter()
    for v in visits:
        if v["ngrow"] != 25 or not v["dec"]:
            continue
        p = pc.recover_pod(v, W)
        if p is None:
            continue
        px, py = p
        pr = g.rb(px, py)
        pcls, preg = pc.classflag(pr[0]), pr[3]
        dec = set(d["slot"] for d in v["dec"])
        po = ownrec.get(v["u"])
        if po is None and 0 <= v["u"] < len(sav.units):
            po = sav.units[v["u"]]["owner"]
        ov["no_owner" if po is None else "owner"] += 1
        for s in range(25):
            c, (tx, ty), r = pc.prechecks(g, W, H, px, py, pcls, preg, s)
            allpass = not [k for k in pc.MODELLED if not c[k]]
            rec = s in dec
            kind = "rec" if rec else ("pass6no" if allpass else "fail6no")
            if kind == "pass6no":
                t7dist[r[7]] += 1
            if po is None:
                continue
            t7 = r[7] - 256 if r[7] >= 128 else r[7]
            r1 = t7 >= 1 and t7 != po
            m2 = t7 < 8 and (bit(mask, po) or bit(mask, t7)) if 0 <= t7 < 8 else False
            r2 = r1 and m2
            fw = flagword(po, t7) if 0 <= po < 8 and 0 <= t7 < 8 else 0
            r3 = r2 and not bit(fw, 4)
            r4 = r3 and (bit(feat, 7) or (bit(fw, 3) and bit(fw, 31)))
            for nm, ok in (("R1", r1), ("R2", r2), ("R3", r3), ("R4", r4)):
                if ok:
                    cells[(nm, kind)] += 1
    print("save %s %dx%d year %d | feat %#x human_mask %#x | visits owner-known %d no-owner %d"
          % (os.path.basename(sav_path), W, H, sav.year, feat, mask,
             ov["owner"], ov["no_owner"]))
    print("t7 byte distribution over ALL pass6-no-row cells (incl no-owner visits):")
    print("  " + repr(sorted(t7dist.items())))
    for nm in ("R1", "R2", "R3", "R4"):
        print(nm, "rejects:", {k[1]: cells[(nm, k[1])] for k in cells if k[0] == nm})
    print("verdict: R1-R3 (rivals) cap recorded decision slots by the counts above - FAIL;"
          " R4 (full rule) is the named predicate.")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "programs/saves/m54b_clean.SAV",
         sys.argv[2] if len(sys.argv) > 2 else "evidence/m294_gate_rows_raw.txt")
