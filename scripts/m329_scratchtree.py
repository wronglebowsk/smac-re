#!/usr/bin/env python3
"""M329 - pick (viii): NAME FUN_0041a8f0 and the ds:0x99aa38 scratch tree behind it.

Footing it stands on (do NOT re-derive, only re-measure what is cited):
  * M178/M179 (s174, `docs/named-archive-m89-m221.md:414-424`): FUN_0041a8f0's 0x41a9xx block
    is a 19-bit pack/unpack through the staging dword ds:0x99aa38, `and ecx,0xf000000` keeps
    bits 24-27, and the rebuilt dword is published to [fac*8380+0x94d600] at 0x41ad94.
  * M321 (s297, `NAMED ## M321`, `evidence/m321_memo_owners.txt:47-81`): the field is
    base_array+0x38; the only OR-setter of bit 6 image-wide is 0x41ac34 inside this tree;
    FUN_0041a8f0 is one of the 3 "arrival" sites of `test BYTE PTR [reg+0x38],0x40`; and the
    47 whole-dword stores to +0x38 have UNTRACED sources.
  * s109/s110 + skill `references/production-queue.md:305,613`: the queue widget singleton is
    the static BSS object 0x6a9480; `[+0x3ff3c]` = the index the pane SHOWS, `[+0x3ff5c]` = the
    cursor row (18 writers).
  * M143-M162 (`docs/field-atlas-faction.md`): the per-faction block is 8,380 B at 0x94d104, and
    the folded `[reg*4+0x94dXXX]` idiom carries reg = f*2095.

STATIC, ZERO BOX. Everything is COMPUTED from scratch/m574/text.txt (objdump .text) +
ghidra_out/index.csv (function bounds); the binary is never run. Tables print FIRST, then the
gates assert the numbers just printed. Every gate names the mutant in scripts/m329_mutate.py
that reddens it.

  T1 callers     every `call 0x41a8f0` in .text (rel32-decoded, not grepped), with the owner fn,
                 the this-pointer producer, the pushed arg, and what happens to the return value.
  T2 the object  the two queue-widget displacements read inside the function, from the ENCODINGS.
  T3 row->record the multiply-chain fold (must evaluate to 304), the two record displacements
                 it addresses, and the owner gate that returns 1.
  T4 the tree    all stores to ds:0x99aa38 inside the frame, the extraction masks on [rec+0x38],
                 the scratch bits, the record-bit <-> scratch-bit permutation, the destroy mask.
  T5 the field   image-wide census of 0x94d600 (writers/readers, the two faction-create consts).
  T6 mode split  the [ebp+8] branch, the second phase's arrival test, the trio it zeroes, the
                 callees it makes in that phase.
  T7 cross-check M178's destroyed-bit list and M179's tag association, re-measured here.

  python3 -u scripts/m329_scratchtree.py
"""
import hashlib
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("M329_TEXT", os.path.join(REPO, "scratch", "m574", "text.txt"))
IDX = os.environ.get("M329_INDEX", os.path.join(REPO, "ghidra_out", "index.csv"))
OUT = os.environ.get("M329_OUT", os.path.join(REPO, "evidence", "m329_scratchtree.txt"))

FN = 0x41A8F0                     # the function under study
SEL = 0x99AA38                    # the scratch/staging dword
FIELD = 0x94D600                  # the published per-faction dword
WIDGET = 0x6A9480                 # the queue widget singleton
SHOW = 0x3FF3C                    # widget: index the pane shows
CURSOR = 0x3FF5C                  # widget: cursor row
BASEARRAY = 0x95DA10              # 304-B records (M321)
FACTIONBLK = 0x94D104             # 8380-B per-faction block (atlas)
TAGWRITER = 0x6267A5              # the tagged save-record writer (M179)
ARRIVE_BIT = 0x40                 # M321's bit 6 of [rec+0x38]

ADDR_RE = re.compile(r"^\s*([0-9a-f]{6,8}):\t([0-9a-f ]*?)\t(\S.*?)\s*$")
CONT_RE = re.compile(r"^\s*([0-9a-f]{6,8}):\t([0-9a-f ]+?)\s*$")

LINES = []


def load():
    """addr -> (idx, mnemonic, operands) over the whole .text dump."""
    insns = []
    addrs = []
    with open(TEXT) as f:
        for line in f:
            m = ADDR_RE.match(line)
            if m:
                addrs.append(int(m.group(1), 16))
                insns.append((m.group(2).strip(), m.group(3).strip()))
                continue
            c = CONT_RE.match(line)
            if c:
                addrs.append(int(c.group(1), 16))
                insns.append(("", ""))
    return addrs, insns


def fn_bounds():
    """name -> (start, size) from the Ghidra batch index."""
    out = {}
    with open(IDX) as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            p = line.rstrip("\n").split(",")
            if len(p) < 3 or not p[0].startswith("0x"):
                continue
            try:
                out[p[1]] = (int(p[0], 16), int(p[2]))
            except ValueError:
                pass
    return out


def owner_of(fnmap, addr):
    best = None
    for _n, (start, size) in fnmap.items():
        if start <= addr < start + size:
            if best is None or start > best[1]:
                best = (_n, start)
    return best


def main():
    addrs, insns = load()
    pos = {a: i for i, a in enumerate(addrs)}
    fnmap = fn_bounds()
    lo, hi = FN, FN + dict((n, s) for n, (a, s) in fnmap.items() if n == "FUN_0041a8f0")["FUN_0041a8f0"]
    print("== M329 scratch-tree census ==")
    print("text=%s insns=%d frame=%#x-%#x" % (os.path.relpath(TEXT, REPO), len(addrs), lo, hi))
    print("TODO T1..T7")
    print("== M329: NOT YET GATED ==")
    return 1


if __name__ == "__main__":
    sys.exit(main())
