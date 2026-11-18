#!/usr/bin/env python3
"""M317 (s288, STATIC zero-box): what does the goal engine FUN_00556690 DECIDE?

Pick (iii') post-M316 (NEXT_PROMPT OPEN shortlist). Settled footing - NAMED.md
## M250 / M252 / M274 / M275 / M276 / M310 (grep before re-deriving):
  - 14,349 B / 4,235 insns; called from exactly 2 sites: 0x52094f (FUN_005208f0)
    and 0x59dd43 (FUN_0059ce10, M94 per-player upkeep walker)      [M252 G7]
  - sole consumer of the coarse region map; FUN_00582340 called at 0x55878a +
    0x558812, both inside the engine                               [M252 G6/G7]
  - region-map stores: engine x5 (0x557fdf=8, 0x558516=dl, 0x558549=0,
    0x55855e=2, 0x55856b=7), values {0,2,7,8}                      [M250 G5]
  - ONE region bound cmp ecx,0x80 @0x558b1c; zero capacity clamps  [M274 G1]
  - ZERO indirect jumps -> CFG sound, reaching-defs decidable      [M275 G1]
  - entry fold edx = 8380*arg -> [ebp-0xc]; BYTE arrays e5a8/e628/eca8/ed28/eda8
    index block*8380 + region                                      [M276 G4]
  - goal band 0x94ee28, 75 x 16 B records; engine holds 35/65 band refs, is the
    ONLY +0C owner-field reader; knockout helper FUN_0056d690's ONLY caller is
    0x559e8e INSIDE the engine                                     [M310 A8/A11]

QUESTION (OPEN at NAMED ## M310): what the engine DECIDES. Method: census its
action vocabulary (call targets), its output vocabulary (memory stores), and
its decision inputs (conditional branches + the cmp/test that feeds each),
then the two caller contexts. Shared engine: m308_site_list.parse_text over
scratch/m574/text.txt (the m53j gz is pruned). Prints tables FIRST, asserts
every printed number. Skeleton stage: G1-G3 baseline + C1 call census.

    python3 -u scripts/m317_engine_decides.py   # stdout -> evidence/m317_engine_decides.txt
"""
import csv
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m308_site_list as M

ENG = 0x556690
SIZE = 14349
N_INSNS = 4235
N_CALLEES = 41
CALLERS_EXPECTED = {0x52094F: "FUN_005208f0", 0x59DD43: "FUN_0059ce10"}
HEXTOK = re.compile(r"0x[0-9a-f]+$")


def call_target(ops):
    """Direct target iff the FIRST operand token is a bare hex VA (far-call
    '0x43:0x...' and register/indirect forms fail fullmatch -> None)."""
    tok = ops.split()[0] if ops.split() else ""
    return int(tok, 16) if HEXTOK.fullmatch(tok) else None


def main():
    ins, order = M.parse_text()
    M._INS, M._ORDER = ins, order
    idx = M.load_index()
    with open(M.INDEX) as f:
        rows = {int(r["addr"], 16): r for r in csv.DictReader(f)}
    er = rows[ENG]
    lo, hi = ENG, ENG + int(er["size_bytes"])
    win = [(a, ins[a][0], ins[a][1]) for a in order if lo <= a < hi]

    print("== G1 baseline: containment / size / instruction coverage ==")
    print("index row: addr=0x%x name=%s size=%s n_insns=%s n_callers=%s n_callees=%s shard=%s"
          % (ENG, er["name"], er["size_bytes"], er["n_insns"], er["n_callers"],
             er["n_callees"], er["shard"]))
    print("parsed window [0x%x,0x%x): %d insns, first=%s last=%s"
          % (lo, hi, len(win), win[0][1] + " " + win[0][2], win[-1][1] + " " + win[-1][2]))
    assert er["name"] == "FUN_00556690"
    assert int(er["size_bytes"]) == SIZE, "size drift"
    assert int(er["n_insns"]) == N_INSNS, "index n_insns drift"
    assert len(win) == N_INSNS, "parsed coverage != index n_insns"
    assert win[0][0] == ENG and win[-1][0] < hi
    print("G1 PASS")

    print("\n== G2 control flow: indirect jmp/call census (M275 re-pin) ==")
    indirect = [(a, mn, ops) for a, mn, ops in win
                if mn in ("jmp", "call") and call_target(ops) is None]
    rets = [a for a, mn, ops in win if mn == "ret"]
    jcc = [(a, mn, ops) for a, mn, ops in win
           if mn.startswith("j") and mn not in ("jmp",)]
    print("indirect jmp/call: %d   ret sites: %d   conditional branches: %d"
          % (len(indirect), len(rets), len(jcc)))
    for a, mn, ops in indirect:
        print("  INDIRECT 0x%x: %s %s" % (a, mn, ops))
    assert not indirect, "M275 law broken: indirect control flow present"
    print("G2 PASS")

    print("\n== G3 caller census: every direct call to the engine in .text ==")
    callers = {}
    for a in order:
        mn, ops = ins[a]
        if mn == "call" and call_target(ops) == ENG:
            callers[a] = M.contain(idx, a)
    for a in sorted(callers):
        print("  call site 0x%x in %s" % (a, callers[a]))
    assert callers == CALLERS_EXPECTED, "caller set drift: %r" % callers
    print("G3 PASS")

    print("\n== C1 action vocabulary: every call site inside the engine ==")
    sites = []
    for a, mn, ops in win:
        if mn == "call":
            t = call_target(ops)
            assert t is not None  # G2 already proved all calls direct
            sites.append((a, t, M.contain(idx, t)))
    byname = {}
    for a, t, nm in sites:
        byname.setdefault((t, nm), []).append(a)
    print("%d call sites -> %d distinct callees" % (len(sites), len(byname)))
    for (t, nm), addrs in sorted(byname.items()):
        print("  0x%x %-16s x%-2d @ %s" % (t, nm, len(addrs),
              " ".join("0x%x" % a for a in addrs)))
    assert len(byname) == int(er["n_callees"]) == N_CALLEES, \
        "distinct callee count != index n_callees"
    print("C1 PASS")

    print("\nSKELETON GREEN: G1-G3 + C1 (store/decision/caller-context censuses next)")
    return 0


if __name__ == "__main__":
    sys.exit(main())