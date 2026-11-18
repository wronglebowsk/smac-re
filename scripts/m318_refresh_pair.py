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
    patch = os.environ.get("M318_PATCH", "")
    if patch:
        n = 0
        for spec in patch.split(";"):
            if not spec.strip():
                continue
            addr_s, repl = spec.split("|", 1)
            a = int(addr_s, 16)
            assert a in ins, "patch target 0x%x does not exist (vacuous mutant)" % a
            mn, _, ops = repl.partition(" ")
            ins[a] = (mn, ops)
            n += 1
        print("patches applied: %d/%d" % (n, len([s for s in patch.split(";") if s.strip()])))
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
        assert int(r["size_bytes"]) == size and int(r["n_insns"]) == n, "index row drift for 0x%x" % t
        assert len(win) == n, "parsed coverage drift for 0x%x" % t
    print("G1 PASS")

    print("\n== G2 pair-site census: adjacency + owner set ==")

    def sites(t):
        return [a for a in order if ins[a][0] == "call" and call_target(ins[a][1]) == t]

    sa, sb = sites(A), sites(B)
    print("sites: %d x %s, %d x %s" % (len(sa), rows[A]["name"], len(sb), rows[B]["name"]))
    for a, b in zip(sa, sb):
        print("  0x%x -> 0x%x  (gap %d)  in %s" % (a, b, b - a, M.contain(idx, a)))
    assert len(sa) == len(sb) == 12, "pair count drift"
    assert [b - a for a, b in zip(sa, sb)] == [5] * 12, "pair not back-to-back"
    oa = {M.contain(idx, a) for a in sa}
    ob = {M.contain(idx, b) for b in sb}
    assert oa == ob == OWNERS, "owner set drift: %r / %r" % (oa, ob)
    print("G2 PASS (12 back-to-back pairs, 7 distinct owners)")

    print("\n== G3 memo-store reach: a ds:0x68cbb4 store precedes each pair ==")
    pos = {a: i for i, a in enumerate(order)}
    found = []
    maxd = 0
    for a, b in zip(sa, sb):
        i = pos[a]
        store = None
        for j in range(i - 1, max(i - 12, -1), -1):
            pa = order[j]
            if b - pa > PAIR_REACH:
                break
            mn, ops = ins[pa]
            if mn == "mov" and MEMO in M.split_ops(ops)[0]:
                store = pa
                break
        found.append(store)
        # M315's 17 B reach is store -> SECOND callee (#311 P2: measuring to
        # the first call accepted up to 22 B). Gap is pinned 5 by G2.
        d = b - store if store else -1
        maxd = max(maxd, d)
        print("  pair @0x%x: memo store %s (->first %d, ->second %d)"
              % (a, "0x%x" % store if store else "NONE", a - store if store else -1, d))
    assert all(s is not None for s in found), "memo store missing before a pair site"
    assert maxd <= PAIR_REACH
    print("G3 PASS (all 12 pairs follow a memo store; worst store->second = %d B <= %d)" % (maxd, PAIR_REACH))

    print("\n== C1 callee census: the pair's action vocabulary ==")

    def callsites(lo, hi):
        out = []
        for a in order:
            if lo <= a < hi and ins[a][0] == "call":
                t = call_target(ins[a][1])
                assert t is not None, "indirect call at 0x%x" % a
                out.append((a, t))
        return out

    ca = callsites(A, A + 1331)
    cb = callsites(B, B + 5237)
    print("A (%s): %d call sites" % (rows[A]["name"], len(ca)))
    for a, t in ca:
        print("  0x%x -> 0x%x %s" % (a, t, M.contain(idx, t)))
    A_CALLS = {0x4E91F5: 0x4E3B50, 0x4E8EFA: 0x4E6960, 0x4E8F0B: 0x4E6D40, 0x4E8F1C: 0x4E7070}
    assert dict(ca) == A_CALLS, "A call map drift"
    mult = {}
    for a, t in cb:
        mult[t] = mult.get(t, 0) + 1
    print("B (%s): %d call sites, %d callees" % (rows[B]["name"], len(cb), len(mult)))
    for t, n in sorted(mult.items()):
        print("  -> 0x%x %s x%d" % (t, M.contain(idx, t), n))
    B_MULT = {0x4E3C80: 3, 0x4E63B0: 1, 0x4E6960: 1, 0x4E6D40: 1, 0x4E7070: 1,
              0x4E75F0: 7, 0x507410: 5, 0x507440: 2, 0x5A6CD0: 3}
    assert len(cb) == 24 and mult == B_MULT, "B callee multiset drift"
    assert cb[0] == (0x4E78E9, 0x4E63B0), "B first call != scan-pool rebuild (M53q)"
    assert len(ca) == int(rows[A]["n_callees"]) == 4
    assert len(mult) == int(rows[B]["n_callees"]) == 9
    print("C1 PASS (A: tile-owner + yield triad; B: rebuild-first, dispatcher x7, region bits x5)")

    print("\n== C2 A = unit-support census: walk / filter / flags / bank ==")
    PINS_A = {
        0x4E8DFC: ("mov", "eax,ds:0x985af0"),          # unit count
        0x4E9277: ("mov", "ecx,DWORD PTR ds:0x985af0"),  # loop bound re-load
        0x4E927E: ("add", "esi,0x34"),                  # unit stride 52 B
        0x4E8E2B: ("mov", "edi,DWORD PTR ds:0x68cbb0"),  # selected-base index
        0x4E8FA5: ("and", "edx,0xff9fffef"),            # clear 0x10/200000/400000
        0x4E90D8: ("or", "edx,0x10"),                   # over-capacity flag
        0x4E9260: ("or", "eax,0x400000"),               # foreign-tile first flag
        0x4E926C: ("or", "eax,0x200000"),               # foreign-tile rest flag
    }
    for a, want in PINS_A.items():
        print("  0x%x: %s %s" % (a, ins[a][0], ins[a][1]))
        assert ins[a] == want, "A structure drift at 0x%x" % a
    # the CONDITIONS that make the loads a filter / a capacity check (#311 P2)
    PINS_A2 = {
        0x4E8E34: ("cmp", "eax,edi"),                          # home-base == selection
        0x4E8E3A: ("je", "0x4e8e8e"),                          # match -> process
        0x4E9094: ("mov", "edi,DWORD PTR [ecx*4+0x94d684]"),   # faction support limit
        0x4E90A0: ("jl", "0x4e90ae"),                          # lower clamp branch
        0x4E90A2: ("cmp", "eax,0x7"),                          # upper clamp bound
        0x4E90A5: ("jle", "0x4e90b0"),
        0x4E90A7: ("mov", "eax,0x7"),                          # clamp to 7
        0x4E90B6: ("cmp", "ecx,DWORD PTR [ebp+eax*4-0x30]"),   # count vs local_34[clamp]
        0x4E90BA: ("jle", "0x4e90e6"),                         # under capacity -> no flag
        0x4E90C4: ("cmp", "edi,0xfffffffc"),                   # limit <= -4 branch
    }
    for a, want in PINS_A2.items():
        print("  0x%x: %s %s" % (a, ins[a][0], ins[a][1]))
        assert ins[a] == want, "A condition drift at 0x%x" % a
    astore = [(a, ins[a][1]) for a in order if A <= a < A + 1331
              and ins[a][0] == "mov" and ins[a][1].startswith("ds:0x")]
    A_BANK = {0x4E8D74: "ds:0x8f0c6c,eax", 0x4E8D7B: "ds:0x8f0c70,eax",
              0x4E8D86: "ds:0x8f0c74,eax", 0x4E8D92: "ds:0x8f0c78,eax",
              0x4E8F28: "ds:0x8f0cc8,eax", 0x4E9080: "ds:0x8f0c2c,eax"}
    assert dict(astore) == A_BANK, "A direct-global store set drift"
    print("  A direct-global stores: %d (summary bank 8f0c2c..8f0cc8)" % len(astore))
    print("C2 PASS (52-B unit walk, count 985af0, home-base filter 68cbb0, flag masks, 6-store bank)")

    print("\n== C3 B = pane refresh: row copy / selection / base flags ==")
    PINS_B = {
        0x4E799B: ("mov", "ecx,DWORD PTR [eax*4+0x94dc34]"),  # faction row array
        0x4E79B3: ("push", "0x1d"),                            # region query 0x1d
        0x4E79C9: ("mov", "dl,BYTE PTR [eax+ecx*1+0x95da9c]"),  # base+0x8c flags
        0x4E7904: ("mov", "DWORD PTR ds:0x8f0c68,ecx"),
        0x4E7C36: ("mov", "ds:0x8f0c68,eax"),
        0x4E7ECD: ("mov", "ds:0x8f0c68,eax"),
        0x4E85D8: ("dec", "DWORD PTR ds:0x8f0c68"),
    }
    for a, want in PINS_B.items():
        print("  0x%x: %s %s" % (a, ins[a][0], ins[a][1]))
        assert ins[a] == want, "B structure drift at 0x%x" % a
    bwin = [(a, ins[a][0], ins[a][1]) for a in order if B <= a < B + 5237]
    sel_loads = [a for a, mn, ops in bwin if "ds:0x68cbb0" in ops and mn == "mov"
                 and not ops.startswith("ds:")]
    flag_reads = [a for a, mn, ops in bwin if "0x95da9c]" in ops and mn == "mov"
                  and not ops.startswith("BYTE PTR ds:")]
    print("  B reads of the selection index ds:0x68cbb0: %d; base-flag reads +0x95da9c: %d"
          % (len(sel_loads), len(flag_reads)))
    assert len(sel_loads) == 15 and len(flag_reads) == 5, "B read-count drift"
    assert ins[0x4E79B5] == ("call", "0x507410"), "region-query call drift"
    print("C3 PASS (rows from 94dc34, 15 selection reads, 5 base-flag reads, 8f0c68 countdown)")

    print("\n== C4 the shared kind law: dispatcher FUN_004e75f0 ==")
    D = 0x4E75F0
    dwin = [(a, ins[a][0], ins[a][1]) for a in order if D <= a < D + 116]
    dcalls = {a: call_target(ops) for a, mn, ops in dwin if mn == "call"}
    print("  dispatcher calls: %s" % " ".join("0x%x->0x%x" % (a, t) for a, t in sorted(dcalls.items())))
    assert dcalls == {0x4E7614: 0x4E6960, 0x4E7630: 0x4E6D40, 0x4E764C: 0x4E7070}, "dispatcher call map drift"
    assert ins[0x4E75F6] == ("cmp", "eax,0x3"), "dispatcher bound drift"
    # the switch IS its jump table behind the bound check (code-atlas law):
    # pin the bound branch, the indirect form, and the table BYTES from the PE
    assert ins[0x4E75F9] == ("ja", "0x4e7660"), "dispatcher bound branch drift"
    assert ins[0x4E75FB] == ("jmp", "DWORD PTR [eax*4+0x4e7664]"), "dispatcher jump form drift"
    import struct
    blob = open(os.path.join(M.ROOT, "terran.exe"), "rb").read()
    _, secs = M.pe_sections(blob)
    off, secname = M.va2off(secs, 0x4E7664)
    assert off is not None, "jump table not in file bytes"
    table = struct.unpack_from("<4I", blob, off)
    print("  jump table @0x4e7664 (%s): %s" % (secname, " ".join("0x%x" % t for t in table)))
    assert table == (0x4E7602, 0x4E761E, 0x4E763A, 0x4E7656), "dispatcher table drift"
    assert ins[0x4E7656] == ("mov", "DWORD PTR ds:0x8f0cc8,0x0"), "case-3 effect drift"
    print("C4 PASS (bound cmp 3 + ja default + jump table -> same triad + case-3 zero as A's inline switch)")

    print("\n== C5 signatures: both pair members are void(void) ==")
    shard = open(os.path.join(M.ROOT, "ghidra_out", "shard_012.c")).read()
    for sig in ("void FUN_004e8d60(void)", "void FUN_004e78e0(void)"):
        assert sig in shard, "signature drift: %s" % sig
        print("  %s" % sig)
    print("C5 PASS (no arguments: the pair reads the CURRENT selection, not a passed index)")

    print("\n== PIN ==")
    assert len(ca) == 4 and len(cb) == 24 and len(astore) == 6, "PIN totals drift"
    print("PIN PASS: A 4 calls / 6 bank stores; B 24 calls / 9 callees / 15 sel-loads / 5 flag-reads")
    import hashlib
    rows = [
        ("G1", "PASS", "A:1331/408 B:5237/1589"),
        ("G2", "PASS", "12 pairs gap5 owners7"),
        ("G3", "PASS", "max store->second %d" % maxd),
        ("C1", "PASS", repr(sorted(dict(ca).items())) + repr(sorted(mult.items()))),
        ("C2", "PASS", repr(sorted(PINS_A.items())) + repr(sorted(PINS_A2.items())) + repr(sorted(astore))),
        ("C3", "PASS", repr(sorted(PINS_B.items())) + " sel15 flag5"),
        ("C4", "PASS", repr(sorted(dcalls.items())) + repr(table)),
        ("C5", "PASS", "void(void) x2"),
        ("PIN", "PASS", "4/24/6"),
    ]
    digest = hashlib.sha256("".join("%s|%s|%s\n" % r for r in rows).encode()).hexdigest()[:16]
    print("== digest: %s ==" % digest)
    print("\nM318 CENSUS GREEN: G1-G3 + C1-C5 + PIN")
    print("NAMES (structure V, game nouns INFERRED): FUN_004e8d60 = selected-base UNIT-SUPPORT")
    print("CENSUS (per-kind yield totals, over-capacity + foreign-tile unit flags, summary bank);")
    print("FUN_004e78e0 = selected-base PANE REFRESH (scan-pool rebuild first, then display rows).")
    return 0


if __name__ == "__main__":
    sys.exit(main())