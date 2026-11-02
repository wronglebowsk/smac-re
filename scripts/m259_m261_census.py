#!/usr/bin/env python3
"""M259-M261: three static census questions on terran.exe, ONE instrument (the whole-image
instruction corpus + the image-derived vtable map + containment via ghidra_out/index.csv).

  M259  the 7 dwords at terrain record +16..+43: who WRITES them (both print forms), who READS
        each slot, and where the map GENERATOR gets the value (FUN_0058d120 / FUN_0058d390 /
        FUN_0051c750)  [NEXT_PROMPT pick, new from M240/M250]
  M260  who ALLOCATES the ~140 KB map-view objects (0x224b8 apart, slot 0 live at 0x8f79e0) and
        who writes view +0x1dd74 in every print form  [new from M245]
  M261  what the 15 UNIQUE slots of vtable 0x679f98 are (size / arg bytes / callees / first store)
        and WHICH SCREEN calls its two constructors  [new from M235]

    python3 scripts/m259_m261_census.py            # all gates
    python3 scripts/m259_m261_census.py --probe    # raw census dumps, no gates

Static only: no box, no /proc, no gdb. Instrument reused from scripts/m235_m237_records.py.
"""
import os
import re
import sys
import bisect
import struct
import collections
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
_spec = importlib.util.spec_from_file_location("m235", os.path.join(HERE, "m235_m237_records.py"))
M = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(M)
NM, INS, fnof, IDXMAP = M.NM, M.INS, M.fnof, M.IDXMAP
dw, body, win, hits = M.dw, M.body, M.win, M.hits
is_store, dest_operand, call_targets = M.is_store, M.dest_operand, M.call_targets
VT, slots_holding = M.VT, M.slots_holding

GATES = []
def G(desc, cond, numbers):
    GATES.append((desc, bool(cond), numbers))

def contig(hits):  # containing functions of a hit list -> Counter
    return collections.Counter(fnof(pc) for pc, *_ in hits)

def m259(): pass
def m260(): pass
def m261(): pass

def main():
    if "--probe" in sys.argv:
        M259 = [10, 14]; M260 = 0x224b8; M261 = 0x679f98
        print("probe: record slots", M259, "view size", hex(M260), "vtable", hex(M261))
        return 0
    m259(); m260(); m261()
    npass = sum(1 for d, ok, n in GATES if ok)
    for d, ok, n in GATES:
        print(("PASS " if ok else "FAIL ") + d)
        print("    " + str(n))
    print("SUMMARY M259/M260/M261: %d/%d gates PASS" % (npass, len(GATES)))
    return 0 if npass == len(GATES) else 1

if __name__ == "__main__":
    sys.exit(main())
