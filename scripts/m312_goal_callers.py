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
    ys = [(0x47166C, "mov", "ecx,DWORD PTR [ebp+0xc]"), (0x47166F, "sub", "ecx,0x3"),
          (0x471672, "mov", "DWORD PTR [ebp-0x14],ecx"),
          (0x47185C, "mov", "edx,DWORD PTR [ebp+0xc]"), (0x47185F, "sub", "edx,0x3"),
          (0x471862, "mov", "DWORD PTR [ebp-0x14],edx"),
          (0x47178D, "mov", "ecx,DWORD PTR [ebp+0xc]"), (0x471790, "add", "ecx,DWORD PTR [ebp-0xc]"),
          (0x471793, "mov", "DWORD PTR [ebp-0x14],ecx"),
          (0x471958, "mov", "edx,DWORD PTR [ebp+0xc]"), (0x47195B, "add", "edx,DWORD PTR [ebp-0xc]"),
          (0x47195E, "mov", "DWORD PTR [ebp-0x14],edx")]
    ck("A5b_y_two_laws_all4", all(at(*t) for t in ys),
       "ALL FOUR y-slot stores: y = arg_y - 3 (direct sites + fwd 1/2) or arg_y + [ebp-0xc] (fwd 3 + loop)")
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

    xs = [0x471669, 0x4716AE, 0x4717C0, 0x471859, 0x471898, 0x47198B]
    ck("A5f_every_x_store_is_a_469010_result",
       all(ins[a] == ("mov", "DWORD PTR [ebp-0x10],eax") and
           ins[a - 8] == ("call", "0x469010") for a in xs),
       "all 6 x-slot stores are `mov [ebp-0x10],eax` exactly 8 B after a call to FUN_00469010")
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
       at(0x473769, "mov", "DWORD PTR [ebp-0x4],0x0") and
       at(0x473770, "jmp", "0x47377b") and
       at(0x47377B, "cmp", "DWORD PTR [ebp-0x4],0x8") and
       at(0x47377F, "jge", "0x4737cc") and
       at(0x473784, "cmp", "DWORD PTR [ecx*4+0x7cdecc],0x0") and
       at(0x47378C, "jne", "0x473790") and
       at(0x473790, "cmp", "DWORD PTR [ebp-0x4],0x0") and
       at(0x473794, "je", "0x4737ab") and
       at(0x4737A0, "cmp", "DWORD PTR [eax+0x1dd74],0x0") and
       at(0x4737A7, "jne", "0x4737ab") and
       at(0x4737A9, "jmp", "0x473772") and
       at(0x4737BE, "mov", "ecx,DWORD PTR [edx*4+0x7cdecc]") and
       at(0x4737C5, "call", "0x4725a0"),
       "8 entries (0..7; bound 8 EXCLUSIVE - the first cmp/jge precedes the body and the "
       "increment is on the back-edge); null-skip; i != 0 also requires element+0x1dd74 == 0; "
       "the element is loaded into ecx = the this-pointer of the call")
    stores_tbl = sorted(a for a, (b, ops) in ins.items()
                        if b == "mov" and firstop(ops) == "DWORD PTR ds:0x7cdecc")
    idx_st = sorted(a for a, (b, ops) in ins.items()
                    if b == "mov" and firstop(ops).endswith("*4+0x7cdecc]"))
    idx_ref = sum(1 for _, (_, ops) in ins.items() if "*4+0x7cdecc]" in ops)
    ck("A8b_entry0_store_and_zero_indexed_stores",
       stores_tbl == [0x5803E1] and idx_st == [] and
       ins[0x5803E1][1] == "DWORD PTR ds:0x7cdecc,0x8f79e0" and idx_ref > 0,
       "entry ZERO's only direct store is 0x5803E1 (in %s) <- 0x8f79e0 = the static MAIN VIEW "
       "(M262); 0 indexed stores name the band (%d band refs are all reads/cmps); entries 1..7 "
       "arrive via the pointer-arithmetic `mov [esi],eax` at 0x5803BB - M262 settled this" % (owner(0x5803E1), idx_ref))
    
    # ---- A9 the hub's 5 arms each compute the block law AND the param<0 flag
    # in an identical 16-instruction window; pin EVERY instruction (literals
    # generated from the real bytes, not hand-transcribed).
    ARM_WINDOWS = {
        0x473388: [
            (0x47334C, "mov", "ecx,DWORD PTR ds:0x985ae8"),
            (0x473352, "and", "ecx,0x80"),
            (0x473358, "test", "ecx,ecx"),
            (0x47335A, "je", "0x473368"),
            (0x47335C, "mov", "DWORD PTR [ebp-0xdc],0xffffffff"),
            (0x473366, "jmp", "0x473374"),
            (0x473368, "mov", "edx,DWORD PTR ds:0x91b5b4"),
            (0x47336E, "mov", "DWORD PTR [ebp-0xdc],edx"),
            (0x473374, "xor", "eax,eax"),
            (0x473376, "cmp", "DWORD PTR [ebp+0x8],0x0"),
            (0x47337A, "setl", "al"),
            (0x47337D, "push", "eax"),
            (0x47337E, "mov", "ecx,DWORD PTR [ebp-0xdc]"),
            (0x473384, "push", "ecx"),
            (0x473385, "mov", "ecx,DWORD PTR [ebp-0x4]"),
            (0x473388, "call", "0x471fd0"),
        ],
        0x4733F8: [
            (0x4733BD, "mov", "edx,DWORD PTR ds:0x985ae8"),
            (0x4733C3, "and", "edx,0x80"),
            (0x4733C9, "test", "edx,edx"),
            (0x4733CB, "je", "0x4733d9"),
            (0x4733CD, "mov", "DWORD PTR [ebp-0xe0],0xffffffff"),
            (0x4733D7, "jmp", "0x4733e4"),
            (0x4733D9, "mov", "eax,ds:0x91b5b4"),
            (0x4733DE, "mov", "DWORD PTR [ebp-0xe0],eax"),
            (0x4733E4, "xor", "ecx,ecx"),
            (0x4733E6, "cmp", "DWORD PTR [ebp+0x8],0x0"),
            (0x4733EA, "setl", "cl"),
            (0x4733ED, "push", "ecx"),
            (0x4733EE, "mov", "edx,DWORD PTR [ebp-0xe0]"),
            (0x4733F4, "push", "edx"),
            (0x4733F5, "mov", "ecx,DWORD PTR [ebp-0x4]"),
            (0x4733F8, "call", "0x471fd0"),
        ],
        0x473467: [
            (0x47342D, "mov", "eax,ds:0x985ae8"),
            (0x473432, "and", "eax,0x80"),
            (0x473437, "test", "eax,eax"),
            (0x473439, "je", "0x473447"),
            (0x47343B, "mov", "DWORD PTR [ebp-0xe4],0xffffffff"),
            (0x473445, "jmp", "0x473453"),
            (0x473447, "mov", "ecx,DWORD PTR ds:0x91b5b4"),
            (0x47344D, "mov", "DWORD PTR [ebp-0xe4],ecx"),
            (0x473453, "xor", "edx,edx"),
            (0x473455, "cmp", "DWORD PTR [ebp+0x8],0x0"),
            (0x473459, "setl", "dl"),
            (0x47345C, "push", "edx"),
            (0x47345D, "mov", "eax,DWORD PTR [ebp-0xe4]"),
            (0x473463, "push", "eax"),
            (0x473464, "mov", "ecx,DWORD PTR [ebp-0x4]"),
            (0x473467, "call", "0x471fd0"),
        ],
        0x4734F8: [
            (0x4734BE, "mov", "eax,ds:0x985ae8"),
            (0x4734C3, "and", "eax,0x80"),
            (0x4734C8, "test", "eax,eax"),
            (0x4734CA, "je", "0x4734d8"),
            (0x4734CC, "mov", "DWORD PTR [ebp-0xe8],0xffffffff"),
            (0x4734D6, "jmp", "0x4734e4"),
            (0x4734D8, "mov", "ecx,DWORD PTR ds:0x91b5b4"),
            (0x4734DE, "mov", "DWORD PTR [ebp-0xe8],ecx"),
            (0x4734E4, "xor", "edx,edx"),
            (0x4734E6, "cmp", "DWORD PTR [ebp+0x8],0x0"),
            (0x4734EA, "setl", "dl"),
            (0x4734ED, "push", "edx"),
            (0x4734EE, "mov", "eax,DWORD PTR [ebp-0xe8]"),
            (0x4734F4, "push", "eax"),
            (0x4734F5, "mov", "ecx,DWORD PTR [ebp-0x4]"),
            (0x4734F8, "call", "0x471fd0"),
        ],
        0x4735A4: [
            (0x47356A, "mov", "eax,ds:0x985ae8"),
            (0x47356F, "and", "eax,0x80"),
            (0x473574, "test", "eax,eax"),
            (0x473576, "je", "0x473584"),
            (0x473578, "mov", "DWORD PTR [ebp-0xec],0xffffffff"),
            (0x473582, "jmp", "0x473590"),
            (0x473584, "mov", "ecx,DWORD PTR ds:0x91b5b4"),
            (0x47358A, "mov", "DWORD PTR [ebp-0xec],ecx"),
            (0x473590, "xor", "edx,edx"),
            (0x473592, "cmp", "DWORD PTR [ebp+0x8],0x0"),
            (0x473596, "setl", "dl"),
            (0x473599, "push", "edx"),
            (0x47359A, "mov", "eax,DWORD PTR [ebp-0xec]"),
            (0x4735A0, "push", "eax"),
            (0x4735A1, "mov", "ecx,DWORD PTR [ebp-0x4]"),
            (0x4735A4, "call", "0x471fd0"),
        ],
    }
    bad = []
    for call, window in sorted(ARM_WINDOWS.items()):
        for a, b, ops in window:
            if not at(a, b, ops):
                bad.append((hex(call), hex(a), b, ops, ins.get(a)))
    ck("A9a_hub_arms_full_window", not bad,
       "5 arms x 16 pinned instructions: block law (ds:0x985ae8&0x80)?-1:ds:0x91b5b4, "
       "flag setl(param_1<0), pushed (flag, block), then call 00471fd0 - NOT coords")
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
