#!/usr/bin/env python3
"""M312 (s276, STATIC, zero box): WHO fires the selection check that
FUN_00470b90 implements, and what the (p1,p2) pair it matches against
GOAL entry+4/+8 actually IS, traced to its writers.

Gates print a table then assert. Census digest at the end; two runs must be
byte-identical (A-DIG). Mutation harness: scripts/m312_mutate.py.
"""
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import m308_site_list as E  # shared .text engine (parse_text/load_index)

IDX = os.path.join(REPO, "ghidra_out", "index.csv")
TEXT = os.path.join(REPO, "scratch", "m574", "text.txt")

# function names of interest
F_B90 = 0x470B90   # the goal duplicate-invalidator (M310)
F_FE0 = 0x470FE0   # thin forwarder, thiscall (raw pair) -> invalidator
F_15D = 0x4715D0   # caller cluster A (3 forwarder sites + 3 direct sites)
F_1FD = 0x471FD0   # caller cluster B (1 forwarder site + 1 direct site)
F_25A = 0x4725A0   # sole caller of FUN_004715d0
F_281 = 0x472810   # the big hub: all 5 callers of FUN_00471fd0 live in it

checks = []
def ck(name, ok, detail=""):
    checks.append((name, bool(ok), detail))
    print("OK " if ok else "FAIL")
    print(f"  {name}: {detail}")

def main():
    idx = E.load_index()
    addrs = [a for a, _ in idx]
    names = dict(idx)
    def owner(va):
        import bisect
        return names[addrs[max(0, bisect.bisect_right(addrs, va) - 1)]]
    def span(nm):
        want = "FUN_%08x" % nm
        i = [k for k, (a, n) in enumerate(idx) if n == want]
        assert len(i) == 1, want
        k = i[0]
        end = idx[k + 1][0] if k + 1 < len(idx) else None
        assert end is not None, want
        return idx[k][0], end

    # A1 boundaries (exact sizes from ghidra_out/index.csv)
    SIZES = {F_FE0: 192, F_15D: 1088, F_1FD: 1344, F_25A: 544, F_281: 3696}
    sizes = {nm: span(nm)[1] - span(nm)[0] for nm in SIZES}
    ck("A1_spans", sizes == SIZES, str({hex(k): v for k, v in sizes.items()}))

    ins, _order = E.parse_text()
    def calls_to(t):
        return sorted(a for a, (b, ops) in ins.items() if b == "call"
                      and ops.split(",")[0].strip() == "0x%x" % t)

    # A2 exact call-site census (addr + owner), 5/4/1/5/3
    CALLS = {
        F_B90: [(0x471086, F_FE0), (0x471884, F_15D), (0x4718BA, F_15D),
                (0x4719C7, F_15D), (0x4724BD, F_1FD)],
        F_FE0: [(0x47169A, F_15D), (0x4716D6, F_15D), (0x471802, F_15D),
                (0x472151, F_1FD)],
        F_15D: [(0x4725E9, F_25A)],
        F_1FD: [(0x473388, F_281), (0x4733F8, F_281), (0x473467, F_281),
                (0x4734F8, F_281), (0x4735A4, F_281)],
        F_25A: [(0x4727F5, 0x4727C0), (0x4737C5, 0x473760), (0x47474B, 0x473D00)],
    }
    for t, want in CALLS.items():
        got = [(a, owner(a)) for a in calls_to(t)]
        exp = [(a, "FUN_%08x" % nm) for a, nm in want]
        ck("A2_calls_%06x" % t, got == exp, f"{len(got)} sites")

    # A3 FUN_00470fe0 callee law: exactly 5 calls in fixed order, and the
    # invalidator call forwards the function's OWN incoming pair ([ebp+8],[ebp+c])
    seq = [(a, ins[a][1]) for a in sorted(calls_to(F_FE0))]
    ORDER = [0x46A1B0, 0x4710A0, 0x469060, 0x46EBD0, 0x470B90]
    got = [int(ops.split(",")[0], 16) for _, ops in seq]
    ck("A3_fe0_callees", got == ORDER, str([hex(x) for x in got]))
    lo, hi = span(F_FE0)
    body = [(a, ins[a][0], ins[a][1]) for a in sorted(x for x in ins if lo <= x < hi)]
    fwd = [(hex(a), b, ops) for a, b, ops in body
           if b == "mov" and ("[ebp+0x8]" in ops or "[ebp+0xc]" in ops)
           and ops.startswith(("ecx", "edx", "eax"))]
    # the two forwarded args: loaded at 0x47107b/0x47107f, pushed, then the call
    ck("A3b_fe0_pair_is_own_args", [f[0] for f in fwd[-2:]] == ["0x47107b", "0x47107f"],
       str([(f[0], f[2]) for f in fwd[-2:]]))
    # and neither arg slot is ever written inside the function (args pass through):
    # a store's DESTINATION is the first operand, "DWORD PTR [ebp+0x8]"
    writes = [(hex(a), ops) for a, b, ops in body
              if ops.split(",")[0].strip() in
              ("DWORD PTR [ebp+0x8]", "DWORD PTR [ebp+0xc]",
               "DWORD PTR [ebp+0x10]", "DWORD PTR [ebp+0x14]")]
    ck("A3c_fe0_args_never_written", writes == [], str(writes))

    print("digest", hashlib.sha256(
        "".join(f"{n}={ok}" for n, ok, _ in checks).encode()).hexdigest()[:16])
    nfail = sum(1 for _, ok, _ in checks if not ok)
    print(f"== M312: {len(checks) - nfail}/{len(checks)} ==")
    return 1 if nfail else 0

if __name__ == "__main__":
    sys.exit(main())
