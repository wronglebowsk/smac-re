#!/usr/bin/env python3
"""M250-M252: who generates the map's region labels, in what order, and who consumes them.

Pick (NEXT_PROMPT, new from M248/M249): who calls the generators FUN_0058d120 / FUN_0058d390
and in what order at NEW GAME (that is where region ids are assigned, and FUN_0058ce00 must run
after them); what the per-faction 0x20bc-byte block at DAT_0094eda8 indexed by region id holds;
what FUN_00556690's coarse-label search is FOR.

Static only: file image + ghidra_out. No box time, no /proc, no gdb.
Acceptance: ONE invocation must print PASS on every gate; a gate that cannot be decided
prints FAIL with its numbers.

Gates:
  G1  image-wide call census of FUN_0058d390 (sites, owning functions)
  G2  call census of FUN_0058d120 and FUN_0058ce00 (sites, owning functions)
  G3  ORDER inside FUN_0058d390: every d120 call pc vs the ce00 call pc, loop membership
  G4  what FUN_0058d120 writes (record +3 via FUN_00582d00) and where its value comes from
  G5  DAT_0094eda8 reference census classified by addressing shape (block field vs region index)
  G6  FUN_00556690's region-map loop: bounds, the label test, and what it accumulates
  G7  the two consumers of FUN_00556690 (callers, arg provenance)
"""
import re
import struct
import subprocess
import sys
from bisect import bisect_right
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXE = ROOT / "programs" / "terran.exe"
INDEX = ROOT / "ghidra_out" / "index.csv"
SHARD_DIR = ROOT / "ghidra_out"
TEXT_BASE = 0x400000

FUNCS = []  # (addr, name, size, shard) filled by load_index()


def load_index():
    raise NotImplementedError


def fn_of(addr):
    raise NotImplementedError


def shard_lines(shard):
    raise NotImplementedError


def call_sites(target_va):
    """All `call <target>` in the whole image -> [(pc, caller_fn_name)]."""
    raise NotImplementedError


def g1(): raise NotImplementedError
def g2(): raise NotImplementedError
def g3(): raise NotImplementedError
def g4(): raise NotImplementedError
def g5(): raise NotImplementedError
def g6(): raise NotImplementedError
def g7(): raise NotImplementedError


def main():
    gates = []
    for name, fn in [("G1", g1), ("G2", g2), ("G3", g3), ("G4", g4),
                     ("G5", g5), ("G6", g6), ("G7", g7)]:
        try:
            ok, detail = fn()
        except Exception as exc:  # a broken gate is a FAIL, never a crash
            ok, detail = False, "EXC %s: %s" % (type(exc).__name__, exc)
        gates.append((name, ok, detail))
        print("%s %s: %s" % (name, "PASS" if ok else "FAIL", detail))
    n_ok = sum(1 for _, ok, _ in gates if ok)
    print("SUMMARY %s: %d/%d gates on terran.exe (%s)"
          % ("PASS" if n_ok == len(gates) else "FAIL", n_ok, len(gates),
             "static image, no box"))
    return 0 if n_ok == len(gates) else 1


if __name__ == "__main__":
    sys.exit(main())
