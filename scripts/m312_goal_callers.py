#!/usr/bin/env python3
"""M312 (s276, STATIC, zero box): WHO fires the selection check that
FUN_00470b90 implements, and what the (p1,p2) pair it matches against
GOAL entry+4/+8 actually IS, traced to its writers.

Gates print a table then assert. Census digest at the end; two runs must be
byte-identical (A10). Mutation harness: scripts/m312_mutate.py.
"""
import bisect
import collections
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import m308_site_list as E  # shared .text engine (parse_text/load_index)

IDX = os.path.join(REPO, "ghidra_out", "index.csv")
TEXT = os.path.join(REPO, "scratch", "m574", "text.txt")

F_B90 = 0x470B90   # the goal duplicate-invalidator (M310)
F_FE0 = 0x470FE0   # thin forwarder, thiscall (raw pair) -> invalidator
F_15D = 0x4715D0   # caller cluster A: the cursor-tile neighbourhood sweep
F_1FD = 0x471FD0   # caller cluster B: block-parameterized sweep
F_25A = 0x4725A0   # sole caller of FUN_004715d0; computes the block law
F_7C0 = 0x4727C0   # 80-B guarded wrapper -> 004725a0
F_281 = 0x472810   # the big hub: all 5 callers of FUN_00471fd0 live in it
F_6A0 = 0x4736A0   # cursor thunk: pushes cursor_x_list[idx], cursor_y_list[idx], 2
F_760 = 0x473760   # fan-out over the view-instance table ds:0x7cdecc[0..8]
F_D00 = 0x473D00   # view-move caller, kind=2

checks = []
def ck(name, ok, detail=""):
    checks.append((name, bool(ok), detail))
    print(("OK   " if ok else "FAIL ") + name + ": " + detail)

def main():
    idx = E.load_index()
    addrs = [a for a, _ in idx]
    names = dict(idx)
    def owner(va):
        return names[addrs[max(0, bisect.bisect_right(addrs, va) - 1)]]
    def span(nm):
        want = "FUN_%08x" % nm
        k = [i for i, (a, n) in enumerate(idx) if n == want][0]
        end = idx[k + 1][0] if k + 1 < len(idx) else None
        assert end is not None, want
        return idx[k][0], end

    # ---- A1 boundaries (exact sizes from ghidra_out/index.csv)
    SIZES = {F_FE0: 192, F_15D: 1088, F_1FD: 1344, F_25A: 544,
             F_7C0: 80, F_281: 3696, F_6A0: 64, F_760: 128, F_D00: 2864}
    sizes = {nm: span(nm)[1] - span(nm)[0] for nm in SIZES}
    ck("A1_spans", sizes == SIZES, str({hex(k): v for k, v in sizes.items()}))

    ins, _order = E.parse_text()
    def at(a, b, ops):
        return ins.get(a) == (b, ops)
    def calls_to(t):
        return sorted(a for a, (b, ops) in ins.items() if b == "call"
                      and ops.split(",")[0].strip() == "0x%x" % t)

    # ---- A2 exact call-site census (addr + owner)
    CALLS = {
        F_B90: [(0x471086, F_FE0), (0x471884, F_15D), (0x4718BA, F_15D),
                (0x4719C7, F_15D), (0x4724BD, F_1FD)],
        F_FE0: [(0x47169A, F_15D), (0x4716D6, F_15D), (0x471802, F_15D),
                (0x472151, F_1FD)],
        F_15D: [(0x4725E9, F_25A)],
        F_1FD: [(0x473388, F_281), (0x4733F8, F_281), (0x473467, F_281),
                (0x4734F8, F_281), (0x4735A4, F_281)],
        F_25A: [(0x4727F5, F_7C0), (0x4737C5, F_760), (0x47474B, F_D00)],
    }
    for t, want in sorted(CALLS.items()):
        got = [(a, owner(a)) for a in calls_to(t)]
        exp = [(a, "FUN_%08x" % nm) for a, nm in want]
        ck("A2_calls_%06x" % t, got == exp, "%d sites" % len(got))

    # ---- A3 FUN_00470fe0 laws (forwarder)
    lo0, hi0 = span(F_FE0)
    seq = sorted(a for a in range(lo0, hi0) if a in ins and ins[a][0] == "call")
    ORDER = [0x46A1B0, 0x4710A0, 0x469060, 0x46EBD0, 0x470B90]
    got = [int(ins[a][1].split(",")[0], 16) for a in seq]
    ck("A3a_fe0_callee_order", got == ORDER, str([hex(x) for x in got]))
    lo, hi = span(F_FE0)
    body = [(a, ins[a][0], ins[a][1]) for a in sorted(x for x in ins if lo <= x < hi)]
    def firstop(ops):
        return ops.split(",")[0].strip()
    ARGS = ("DWORD PTR [ebp+0x8]", "DWORD PTR [ebp+0xc]",
            "DWORD PTR [ebp+0x10]", "DWORD PTR [ebp+0x14]")
    writes = [hex(a) for a, b, ops in body if b == "mov" and firstop(ops) in ARGS]
    nonmov = [(a, b) for a, b, ops in body if b != "mov" and firstop(ops) in ARGS]
    ck("A3b_fe0_argpair_never_written", writes == [], str(writes))
    ck("A3c_fe0_arg_nonmov_uses", nonmov == [(0x471050, "cmp")], str(nonmov))
    ck("A3d_fe0_pair_is_own_args",
       at(0x47107B, "mov", "ecx,DWORD PTR [ebp+0xc]") and
       at(0x47107F, "mov", "edx,DWORD PTR [ebp+0x8]") and
       at(0x471086, "call", "0x470b90"),
       "tail pushes load the function's own arg slots")

    # ---- A4 THE 4TH-ARG LAW: fe0's invalidator tail is guarded on arg4 != 0,
    # and ALL FOUR forwarder sites push literal 0 -> from every real caller
    # the forwarding path can NEVER reach the invalidator.
    ck("A4a_fe0_tail_guard",
       at(0x471050, "cmp", "DWORD PTR [ebp+0x14],0x0") and
       at(0x471054, "je", "0x47108b"),
       "cmp arg4; je epilogue (skips the only call to 470b90 in fe0)")
    fwd_pat = {  # absolute (addr, mnemonic, operands) windows before each call
        0x47169A: [(0x471689, "push", "0x0"), (0x47168e, "push", "ecx"),
                   (0x471692, "push", "edx"), (0x471696, "push", "eax"),
                   (0x471697, "mov", "ecx,DWORD PTR [ebp-0x4]")],
        0x4716D6: [(0x4716c5, "push", "0x0"), (0x4716ca, "push", "ecx"),
                   (0x4716ce, "push", "edx"), (0x4716d2, "push", "eax"),
                   (0x4716d3, "mov", "ecx,DWORD PTR [ebp-0x4]")],
        0x471802: [(0x4717f1, "push", "0x0"), (0x4717f6, "push", "ecx"),
                   (0x4717fa, "push", "edx"), (0x4717fe, "push", "eax"),
                   (0x4717ff, "mov", "ecx,DWORD PTR [ebp-0x4]")],
        0x472151: [(0x472140, "push", "0x0"), (0x472145, "push", "edx"),
                   (0x472149, "push", "eax"), (0x47214d, "push", "ecx"),
                   (0x47214e, "mov", "ecx,DWORD PTR [ebp-0x4]")],
    }
    bad = []
    for s, pat in sorted(fwd_pat.items()):
        for a, b, ops in pat:
            if not at(a, b, ops):
                bad.append((hex(s), hex(a), b, ops, ins.get(a)))
    ck("A4b_all4_forwarders_pass_literal0", not bad, str(bad))

    # ---- A5 FUN_004715d0 sweep law
    st10 = sorted(a for a, b, ops in [(x, ins[x][0], ins[x][1]) for x in
                 range(0x4715D0, 0x471A10) if x in ins]
                 if b == "mov" and firstop(ops) == "DWORD PTR [ebp-0x10]")
    st14 = sorted(a for a, b, ops in [(x, ins[x][0], ins[x][1]) for x in
                 range(0x4715D0, 0x471A10) if x in ins]
                 if b == "mov" and firstop(ops) == "DWORD PTR [ebp-0x14]")
    ck("A5a_slot_store_sets", st10 == [0x471669, 0x4716AE, 0x4717C0, 0x471859, 0x471898, 0x47198B]
       and st14 == [0x471672, 0x471793, 0x471862, 0x47195E],
       "x-slot %d + y-slot %d stores" % (len(st10), len(st14)))
    ck("A5b_y_minus_3_law",
       at(0x47185C, "mov", "edx,DWORD PTR [ebp+0xc]") and
       at(0x47185F, "sub", "edx,0x3") and at(0x471862, "mov", "DWORD PTR [ebp-0x14],edx") and
       at(0x47166C, "mov", "ecx,DWORD PTR [ebp+0xc]") and
       at(0x47166F, "sub", "ecx,0x3") and at(0x471672, "mov", "DWORD PTR [ebp-0x14],ecx"),
       "y = arg_y - 3 (two sites); loop site adds [ebp-0xc] at 0x47195E")
    ck("A5c_x_clamp_law",
       at(0x47165A, "mov", "eax,DWORD PTR [ebp+0x8]") and at(0x47165D, "sub", "eax,0x1") and
       at(0x471661, "call", "0x469010") and at(0x471669, "mov", "DWORD PTR [ebp-0x10],eax") and
       at(0x47169F, "mov", "ecx,DWORD PTR [ebp+0x8]") and at(0x4716A2, "add", "ecx,0x1") and
       at(0x4716A6, "call", "0x469010") and at(0x4716AE, "mov", "DWORD PTR [ebp-0x10],eax"),
       "x in {arg_x-1, arg_x+1} clamped through FUN_00469010")
    ck("A5d_0x2000_pregate_skips_all3_direct_sites",
       at(0x471831, "mov", "eax,DWORD PTR [edx+0x1dd70]") and
       at(0x471837, "and", "eax,0x2000") and at(0x47183C, "test", "eax,eax") and
       at(0x47183E, "je", "0x4719d3"),
       "je 0x4719d3 lands past every direct call site (0x471884/8ba/9c7)")
    ck("A5e_loop_site_gated_on_FUN_00422060_nonzero",
       at(0x4719AE, "mov", "ecx,DWORD PTR [ebp-0x4]") and
       at(0x4719B1, "call", "0x422060") and at(0x4719B6, "test", "eax,eax") and
       at(0x4719B8, "jne", "0x4719bc") and at(0x4719BA, "jmp", "0x47196b"),
       "loop candidate fires only when 422060(this,x,y,0) != 0")

    # ---- A6 FUN_004725a0: the block law, in the same encoding as M310's filter
    ck("A6a_block_law",
       at(0x4725AC, "mov", "eax,ds:0x985ae8") and at(0x4725B1, "and", "eax,0x80") and
       at(0x4725B8, "je", "0x4725c3") and at(0x4725BA, "mov", "DWORD PTR [ebp-0x18],0xffffffff") and
       at(0x4725C3, "mov", "ecx,DWORD PTR ds:0x91b5b4") and
       at(0x4725C9, "mov", "DWORD PTR [ebp-0x18],ecx"),
       "block = (ds:0x985ae8 & 0x80) ? -1 : ds:0x91b5b4 (M310's filter, same law)")
    ck("A6b_sweep_call_args",
       at(0x4725CC, "xor", "edx,edx") and at(0x4725CE, "cmp", "DWORD PTR [ebp+0x14],0x0") and
       at(0x4725D2, "setl", "dl") and at(0x4725D5, "push", "edx") and
       at(0x4725D6, "mov", "eax,DWORD PTR [ebp-0x18]") and at(0x4725D9, "push", "eax") and
       at(0x4725E9, "call", "0x4715d0"),
       "5th arg = setl(kind < 0), 4th = block")
    ck("A6c_cursor_recheck_same_pair_law",
       at(0x47268C, "push", "0x0") and
       at(0x47268E, "mov", "edx,DWORD PTR ds:0x91b5e8") and
       at(0x472694, "mov", "eax,DWORD PTR [edx*4+0x91b670]") and at(0x47269B, "push", "eax") and
       at(0x47269C, "mov", "ecx,DWORD PTR ds:0x91b5e8") and
       at(0x4726A2, "mov", "edx,DWORD PTR [ecx*4+0x91b5f0]") and at(0x4726A9, "push", "edx") and
       at(0x4726AD, "call", "0x422060"),
       "assert-gate reads cursor_x_list[idx], cursor_y_list[idx] before FUN_00422060")

    # ---- A7 FUN_004736a0: THE CURSOR THUNK. Exactly one call; its args are the
    # two cursor lists indexed by the cursor slot (NAMED.md global ledger row).
    ck("A7a_thunk_encoding",
       at(0x4736AC, "push", "0x2") and at(0x4736AE, "mov", "eax,ds:0x91b5e8") and
       at(0x4736B3, "mov", "ecx,DWORD PTR [eax*4+0x91b670]") and at(0x4736BA, "push", "ecx") and
       at(0x4736BB, "mov", "edx,DWORD PTR ds:0x91b5e8") and
       at(0x4736C1, "mov", "eax,DWORD PTR [edx*4+0x91b5f0]") and at(0x4736C8, "push", "eax") and
       at(0x4736CC, "call", "0x4727c0"),
       "(x,y) = cursor_x_list[cursor], cursor_y_list[cursor]; kind=2")
    ck("A7b_thunk_single_call_and_15_callers",
       calls_to(F_6A0) and len(calls_to(F_6A0)) == 15 and len(calls_to(F_7C0)) == 2,
       "15 dump-wide call sites of 004736a0; 2 of 004727c0 (004736a0 + FUN_005010d0)")

    # ---- A8 FUN_00473760: fan-out over the view-instance table ds:0x7cdecc
    ck("A8a_fanout_law",
       at(0x473769, "mov", "DWORD PTR [ebp-0x4],0x0") and at(0x47377B, "cmp", "DWORD PTR [ebp-0x4],0x8") and
       at(0x47377F, "jge", "0x4737cc") and at(0x473784, "cmp", "DWORD PTR [ecx*4+0x7cdecc],0x0") and
       at(0x4737A0, "cmp", "DWORD PTR [eax+0x1dd74],0x0") and at(0x4737C5, "call", "0x4725a0"),
       "i in 0..8; skip null; i != 0 also requires element+0x1dd74 == 0; element IS the this-pointer")
    stores_tbl = sorted(a for a, (b, ops) in ins.items()
                        if b == "mov" and firstop(ops) == "DWORD PTR ds:0x7cdecc")
    ck("A8b_view_table_single_store", stores_tbl == [0x5803E1]
       and ins[0x5803E1][1] == "DWORD PTR ds:0x7cdecc,0x8f79e0",
       "exactly 1 store cache-wide (in %s): the slots point at one static array" % owner(0x5803E1))

    # ---- A9 the hub's 5 arms each re-compute the block law and hand 00471fd0
    # (block, param_1 < 0) - NOT a coordinate pair.
    arms = {0x473388: (0x47334C, 0x473368), 0x4733F8: (0x4733BD, 0x4733D9),
            0x473467: (0x47342D, 0x473447), 0x4734F8: (0x4734BE, 0x4734D8),
            0x4735A4: (0x47356A, 0x473584)}
    bad = []
    for s, (g, c) in sorted(arms.items()):
        if not (ins.get(g, ("", ""))[1].startswith(("eax,ds:0x985ae8", "ecx,DWORD PTR ds:0x985ae8",
                                                    "edx,DWORD PTR ds:0x985ae8"))
                and ins.get(c, ("", ""))[1].endswith("ds:0x91b5b4")
                and ins[s][1] == "0x471fd0"):
            bad.append(hex(s))
    ck("A9a_hub_arms_block_not_coords", not bad,
       "5 arms at %s compute (ds:0x985ae8&0x80)?-1:ds:0x91b5b4 inline"
       % [hex(s) for s in sorted(arms)])
    n281 = len(calls_to(F_281))
    grp = collections.Counter(owner(a) for a in calls_to(F_281))
    ck("A9b_hub_53_sites_28_owners", n281 == 53 and len(grp) == 28,
       "%d call sites in %d functions (view/refresh families; naming them = follow-up pick)"
       % (n281, len(grp)))

    # ---- A10 digest (must be byte-identical across two runs)
    blob = "".join("%s=%d|%s;" % (n, ok, d[:80]) for n, ok, d in checks)
    print("digest", hashlib.sha256(blob.encode()).hexdigest()[:16])
    nfail = sum(1 for _, ok, _ in checks if not ok)
    print("== M312: %d/%d ==" % (len(checks) - nfail, len(checks)))
    return 1 if nfail else 0

if __name__ == "__main__":
    sys.exit(main())
