#!/usr/bin/env python3
"""M256-M258: the worth test's operands, and the sibling per-region arrays named by their census.

Static only: terran.exe's .text via objdump + ghidra_out/index.csv containment. No box, no /proc, no gdb.

Subject (from M253): FUN_00556690's upkeep stage stores the verdict byte
DAT_0094eda8[region + fac*0x20bc] and the 7-vs-8 arm is `sete dl; add dl,0x7` at 0x558516 —
i.e. the boolean of a WORTH TEST whose operands were left unnamed. The same block also holds
the per-region siblings 0x94e4a8 / 0x94e628 / 0x94e7a8 / 0x94eaa8 (0x94e5a8 = the multiplier
byte array, M94/M253).

Gates (each prints its own numbers; the SUMMARY line is the acceptance):
  G1  the worth-test boolean's producer chain is pinned to pcs inside the verdict window
  G2  operand A resolves: which loads feed the subtraction, and what they read
  G3  operand B resolves: which loads feed it, their widths and displacements
  G4  0x94e4a8 census: refs / stores / functions / value shapes, extent vs 0x94e5a8
  G5  0x94e628 census: same
  G6  0x94e7a8 census: same
  G7  0x94eaa8 census: same
  G8  the region loop's index domain matches the arrays' extents (the arrays are per-region)
"""
import subprocess, sys, csv, re, bisect, collections
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXE = ROOT / "programs" / "terran.exe"
INDEX = ROOT / "ghidra_out" / "index.csv"
OUTFILE = ROOT / "evidence" / "m256_worth_operands.txt"

FUN = 0x556690            # the per-faction upkeep stage
VERDICT_BASE = 0x94eda8   # DAT_0094eda8, block offset of the verdict byte array
FAC_STRIDE = 0x20BC       # faction block, 8380 dwords folded to bytes
ARRAYS = [0x94e4a8, 0x94e5a8, 0x94e628, 0x94e7a8, 0x94eaa8]

results = []


def gate(name, ok, text):
    results.append(ok)
    print("G%d %s: %s" % (name, "PASS" if ok else "FAIL", text))
    return ok


def load_index():
    raise SystemExit("not implemented")


def fn_of(pc):
    raise SystemExit("not implemented")


def disasm():
    out = subprocess.run(['objdump', '-d', '-M', 'intel', '--section=.text', str(EXE)],
                         capture_output=True, text=True).stdout
    return out


def ins():
    raise SystemExit("not implemented")


def window(pc, back=0, fwd=0):
    raise SystemExit("not implemented")


def census(token):
    raise SystemExit("not implemented")


def g1(): gate(1, False, "skeleton")
def g2(): gate(2, False, "skeleton")
def g3(): gate(3, False, "skeleton")
def g4(): gate(4, False, "skeleton")
def g5(): gate(5, False, "skeleton")
def g6(): gate(6, False, "skeleton")
def g7(): gate(7, False, "skeleton")
def g8(): gate(8, False, "skeleton")


def main():
    for f in (g1, g2, g3, g4, g5, g6, g7, g8):
        f()
    n_ok = sum(1 for r in results if r)
    verdict = "PASS" if n_ok == len(results) else "FAIL"
    print("SUMMARY %s: %d/%d gates on terran.exe (static image, no box)" % (verdict, n_ok, len(results)))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
