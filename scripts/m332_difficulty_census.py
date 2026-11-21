#!/usr/bin/env python3
"""M332 — SKELETON (branch committed BEFORE probing; see SESSION_CURSOR).

PICK: NEXT_PROMPT.md (x2) — `ds:0x985aec`: the difficulty dword's NOUN and its
complete STORE set.  Prior footing: `NAMED ## M308` row `:1075` (68 refs, 0
arithmetic, cmp-only {1,2,3,4}, "exactly 4 writers", 2 mirror `ds:0x92bde8`,
1 fed by `movsx eax, BYTE ds:0x8f0c11`, 0x4ddcf1 UNATTRIBUTED; "which option it
encodes: OPEN") and `NAMED ## B27`/`## M330` (the refund k-table reads it).

GATE PLAN (each gate is computed from the dump, printed FIRST, then asserted;
every gate gets a named mutant in scripts/m332_mutate.py):

  G1  reference census of ds:0x985aec in .text: total refs, and the exact
      partition LOAD / STORE / CMP / ARITHMETIC.  Re-measures M308's "68 refs,
      0 arithmetic" with the s310-review scanner (ALL store mnemonics + implicit
      writes), not a mov-only grep.
  G2  the STORE SET as an exact sorted address set + each store's containing
      function.  Rival: "the writer set is the 4 M308 names".
  G3  pointer-alias formation: any `lea reg, [ds:0x985aec]` / stos / xchg /
      swap that could write it without naming it.  This gate must be able to
      FAIL (if aliases exist the store set in G2 is incomplete).
  G4  value domain: every immediate the global is compared against, and every
      immediate stored into it.  Rival: the domain is {1,2,3,4} (M308).
  G5  the mirror: for every store, the def-chain origin (immediate / global
      load / unattributed), and whether `ds:0x92bde8` is really a *field* or
      the END OF AN ARRAY (the `add edi,0xd4 ; cmp edi,0x92bde8 ; jl` loop at
      0x579bc6 says the latter for at least one site).  Rival: M308's
      "2 stores mirror the field ds:0x92bde8".
  G6  the NOUN test: is there a data path from a CONTAINER field (save/scenario
      header) or from a labelled chooser into the global?  Measured, not
      asserted from a nearby menu literal.  If the noun cannot be pinned, the
      gate prints the ruled-out rivals and the claim stays INFERRED.

Acceptance: one invocation prints `PASS M332: <n>/<n> gates` and writes
evidence/m332_difficulty_census.txt; a second run must diff clean.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
IDXCSV = os.path.join(ROOT, "ghidra_out/index.csv")

ADDR = re.compile(r"\s*([0-9a-f]{6,8}):\t([0-9a-f ]+)\t(.*?)(?:\s*;|$)")


def load_insns():
    out = []
    with open(TEXT, "r", errors="replace") as f:
        for line in f:
            m = ADDR.match(line)
            if m:
                out.append((int(m.group(1), 16), m.group(3).strip()))
    return out


def main():
    print("M332 skeleton: instrument not yet measured")
    return 2


if __name__ == "__main__":
    sys.exit(main())
