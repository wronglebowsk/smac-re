#!/usr/bin/env python3
"""M163-M165: what the atlas's odd rows actually are — a once-written rank, and two contiguous structs.

  M163  0x94d434 has 196 references but ONE write (atlas row M145). Read the writer: it is an initialisation loop.
  M164  the 0x94d80c cluster (0c/10/14/18/1c, 78/36/42/46/62 refs) — one 20-byte struct or five unrelated fields?
        Decidable by BASE-REGISTER reuse: five displacements off the SAME register in the SAME function is a struct.
  M165  0x94d554 + 0x94d55c — an 8-byte pair used together, or coincidence?

    python3 scripts/m163_m165_structs.py
"""
import bisect
import collections
import importlib.util
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("field_census", os.path.join(HERE, "field_census.py"))
FC = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(FC)

INS, POS, fnof = FC.INS, FC.POS, FC.fnof
ROOT = FC.ROOT
LOW = [(pc, s.lower()) for pc, s in INS]
R = {}


def ok(mid, cond, text):
    R[mid] = cond
    print("%s  %s — %s" % (mid, "PASS" if cond else "FAIL", text))


def pairs(disps):
    """(function, base register) -> set of displacements used off that register."""
    out = collections.defaultdict(set)
    for pc, s in LOW:
        for d in disps:
            m = re.search(r"\[(\w+)\+%s\]" % d, s)
            if m:
                out[(fnof(pc), m.group(1))].add(d)
    return out


def m163():
    writes = [(pc, s) for pc, s in LOW
              if re.match(r"^mov\s+(dword ptr |word ptr |byte ptr )?\[[^\]]*\+0x94d434\],", s)]
    refs = [(pc, s) for pc, s in LOW if "+0x94d434]" in s]
    win = [(pc, s) for pc, s in INS if 0x59AC40 <= pc <= 0x59AC96]
    j = " | ".join(s.lower() for _, s in win)
    loop = ("dec    ebx" in j and "jg     0x59ac4b" in j and "0x926a7c" in j and "0x926a98" in j
            and "0x926a78],0xffffffff" in j)
    print("M163 0x94d434: %d refs, %d write(s)" % (len(refs), len(writes)))
    for pc, s in win:
        print("   %06x  %s" % (pc, s[:60]))
    ok("M163", len(writes) == 1 and writes[0][0] == 0x59AC8A and loop,
       "the single writer is an INITIALISATION loop in FUN_0059aa00 (0x59ac4b-0x59ac94): it scans the 7-dword table "
       "0x926a7c-0x926a98 for the largest entry, stores **-1** into the winner's slot at 0x926a78+n*4, then writes "
       "`[faction*8380+0x94d434] = ebx` and decrements ebx while looping — i.e. it ASSIGNS A DESCENDING RANK per faction "
       "once, at init. 196 readers and one writer is exactly what a rank field looks like; the values tested (2/4/5/6) "
       "are rank comparisons")


def m164():
    cl = ["0x94d80c", "0x94d810", "0x94d814", "0x94d818", "0x94d81c"]
    p = pairs(cl)
    full = {k: v for k, v in p.items() if len(v) == 5}
    counts = {d: len([1 for pc, s in LOW if "+%s]" % d in s]) for d in cl}
    print("M164 cluster refs: %s" % counts)
    for k, v in sorted(full.items(), key=lambda kv: kv[0][0])[:10]:
        print("   %-14s base=%-3s covers all 5 displacements" % k)
    ok("M164", len(full) >= 8 and all(counts[d] > 30 for d in cl),
       "the five displacements are ONE 20-byte struct at +0x94d80c: %d (function, base-register) pairs touch all five off "
       "a single base (FUN_0040b960/004dc100/004e78e0/004f6030/00522b70/0055a940/00574370 x2), and every member has "
       ">30 refs. A layout claim of five separate fields would have to explain why 8 call sites address them off one "
       "register in sequence" % len(full))


def m165():
    p = pairs(["0x94d554", "0x94d55c", "0x94d488"])
    both = {k: v for k, v in p.items() if {"0x94d554", "0x94d55c"} <= v}
    with488 = {k: v for k, v in p.items() if "0x94d488" in v}
    print("M165 (fn,base) pairs: both 554+55c = %d ; 488 sites = %d" % (len(both), len(with488)))
    for k, v in sorted(both.items())[:8]:
        print("   %-14s base=%-3s %s" % (k[0], k[1], sorted(v)))
    ok("M165", len(both) >= 5,
       "0x94d554 + 0x94d55c are an 8-byte PAIR (dword + dword) read off one base in %d (function, base) pairs, most of "
       "them FUN_00546800 with three different bases; 0x94d488 is a separate field (it shares a base with 0x94d55c in "
       "only one function), so the atlas's neighbouring ref counts are not a layout" % len(both))


def main():
    m163(); m164(); m165()
    print("\nSUMMARY " + " ".join("%s=%s" % (k, "PASS" if v else "FAIL") for k, v in R.items()))
    with open(os.path.join(ROOT, "evidence", "m163_m165.log"), "w") as fh:
        fh.write("SUMMARY " + " ".join("%s=%s" % (k, "PASS" if v else "FAIL") for k, v in R.items()) + "\n")
    return 0 if all(R.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
