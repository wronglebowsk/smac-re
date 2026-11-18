#!/usr/bin/env python3
"""M318 (s289, STATIC zero-box): NAME the selection-refresh pair.

Pick (iv) post-M317. M315 proved ds:0x68cbb4 is the REFRESH MEMO ("the index
the pair already ran for") and explicitly NOT-CLAIMED what the pair DOES.
The pair = FUN_004e8d60 then FUN_004e78e0, called back-to-back from the same
12 sites in 8 owners (M315's 12 memo sites; REFRESH tuple at
scripts/m315_bb4_census.py:31 holds TARGETS). Skeleton stage: G1 baseline,
G2 pair-site census (adjacency + owner set), G3 memo-store reach re-pin.

    python3 -u scripts/m318_refresh_pair.py  # stdout -> evidence/m318_refresh_pair.txt
"""
import csv
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m308_site_list as M

A, B = 0x4E8D60, 0x4E78E0
MEMO = "ds:0x68cbb4"
PAIR_REACH = 17  # M315 A3 measured worst gap store -> second callee
HEXTOK = re.compile(r"0x[0-9a-f]+$")
OWNERS = {"FUN_004e47d0", "FUN_004eb6b0", "FUN_004ee410", "FUN_004ef6d0",
          "FUN_004f34b0", "FUN_004f41f0", "FUN_004f5a70"}


def call_target(ops):
    tok = ops.split()[0] if ops.split() else ""
    return int(tok, 16) if HEXTOK.fullmatch(tok) else None


def main():
    ins, order = M.parse_text()
    M._INS, M._ORDER = ins, order
    idx = M.load_index()
    with open(M.INDEX) as f:
        rows = {int(r["addr"], 16): r for r in csv.DictReader(f)}

    print("== G1 baseline: the two callees ==")
    for t, size, n in ((A, 1331, 408), (B, 5237, 1589)):
        r = rows[t]
        lo, hi = t, t + int(r["size_bytes"])
        win = [a for a in order if lo <= a < hi]
        print("%s: size=%s n_insns=%s n_callers=%s n_callees=%s n_strings=%s shard=%s | parsed %d insns"
              % (r["name"], r["size_bytes"], r["n_insns"], r["n_callers"],
                 r["n_callees"], r["n_strings"], r["shard"], len(win)))
        assert int(r["size_bytes"]) == size and int(r["n_insns"]) == n
        assert len(win) == n, "parsed coverage drift for 0x%x" % t
    print("G1 PASS")

    print("\n== G2 pair-site census: adjacency + owner set ==")

    def sites(t):
        return [a for a in order if ins[a][0] == "call" and call_target(ins[a][1]) == t]

    sa, sb = sites(A), sites(B)
    print("sites: %d x %s, %d x %s" % (len(sa), rows[A]["name"], len(sb), rows[B]["name"]))
    for a, b in zip(sa, sb):
        print("  0x%x -> 0x%x  (gap %d)  in %s" % (a, b, b - a, M.contain(idx, a)))
    assert len(sa) == len(sb) == 12
    assert [b - a for a, b in zip(sa, sb)] == [5] * 12, "pair not back-to-back"
    oa = {M.contain(idx, a) for a in sa}
    ob = {M.contain(idx, b) for b in sb}
    assert oa == ob == OWNERS, "owner set drift: %r / %r" % (oa, ob)
    print("G2 PASS (12 back-to-back pairs, 7 distinct owners)")

    print("\n== G3 memo-store reach: a ds:0x68cbb4 store precedes each pair ==")
    pos = {a: i for i, a in enumerate(order)}
    found = []
    for a in sa:
        i = pos[a]
        store = None
        for j in range(i - 1, max(i - 12, -1), -1):
            pa = order[j]
            if a - pa > PAIR_REACH:
                break
            mn, ops = ins[pa]
            if mn == "mov" and MEMO in M.split_ops(ops)[0]:
                store = pa
                break
        found.append(store)
        print("  pair @0x%x: memo store %s" % (a, "0x%x" % store if store else "NONE"))
    assert all(s is not None for s in found), "memo store missing before a pair site"
    print("G3 PASS (all 12 pairs follow a memo store within %d B)" % PAIR_REACH)

    print("\nSKELETON GREEN: G1-G3 (identity censuses next)")
    return 0


if __name__ == "__main__":
    sys.exit(main())