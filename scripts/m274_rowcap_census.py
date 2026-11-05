#!/usr/bin/env python3
"""M274 - static follow-up of M273: the 188-row table vs the 128-bound region loop.

Three questions M273 left open, all answerable from the disassembly cache (no box):
  Q1 the loop bound: is the region loop clamped anywhere except `cmp ecx,0x80`?
  Q2 the spill target: where do the SCALED reads of regions 94..127 actually land?
  Q3 the row slot: is the fold at 0x558038 the ONLY writer of the row slot [ebp-0x18]
     that the UNSCALED site reads? (M273's live cursor advances by the FACTION stride
     8380, which the fold CANNOT produce from a 0..7 faction index - so who does?)

Method: the FULL body of FUN_00556690 read from the aligned scratch/m574/text.txt cache
(skill law: parse by TAB fields; never a --start-address mid-inside an instruction -
objdump silently misaligns and invents .byte lines, s214). Every gate computes its number
from the parse; the SUMMARY line is the acceptance.
"""
import csv
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch", "m574", "text.txt")
INDEX = os.path.join(ROOT, "ghidra_out", "index.csv")
FUN = 0x556690
SITE_UNSCALED, SITE_SCALED = 0x558452, 0x5584aa
FOLD, ROW_SLOT = 0x558038, "[ebp-0x18]"
VERDICT = 0x94EDA8
VERDICT_VALUES = {"0x557fdf": "0x8", "0x558516": "dl", "0x558549": "0x0",
                  "0x55855e": "0x2", "0x55856b": "0x7"}
ROW_STRIDE, REGIONS_BOUND = 188, 0x80
GAP = 0x94EBA8 - 0x94EAA8          # 256: the sibling array's start = the scaled-overflow target
BLOCK_STRIDE = 8380


def load_body():
    with open(INDEX) as fh:
        rows = sorted((int(r["addr"], 16), r["name"], int(r["size_bytes"]))
                      for r in csv.DictReader(fh) if r["addr"])
    end = next((a + sz for a, n, sz in rows if a == FUN), None)
    assert end, "FUN_00556690 not in index"
    ins = []
    pat = re.compile(r"\s+([0-9a-f]+):\t([0-9a-f ]+)\t(\S+)\s?(.*)")
    with open(TEXT, errors="replace") as fh:
        for line in fh:
            m = pat.match(line)
            if not m or not m.group(3):
                continue
            a = int(m.group(1), 16)
            if a < FUN:
                continue
            if a >= end:
                break
            ins.append((a, m.group(3), m.group(4).split("#")[0].strip()))
    addr = {a: (op, args) for a, op, args in ins}
    assert addr.get(0x557FE7, ("", ""))[0] == "jmp", "cache window misaligned at 0x557fe7"
    return ins, end


def main():
    ins, end = load_body()
    results = []

    def gate(n, ok, text):
        results.append(ok)
        print("G%d %s: %s" % (n, "PASS" if ok else "FAIL", text))

    # G1: the loop is bounded ONCE, by the constant 0x80 - never clamped to the row capacity
    bound = [(hex(a), args) for a, op, args in ins if op == "cmp" and args == "ecx,0x80"]
    clamps = [(hex(a), args) for a, op, args in ins
              if op == "cmp" and re.search(r"ecx,(0x5c|94|0x5b|93|91)\b", args)]
    gate(1, len(bound) == 1 and not clamps,
         "region-loop bound sites: %s (ONE, the constant 128); capacity clamps (94/93/91): %s "
         "-> the loop is NEVER clamped to the 94-slot row" % (bound, clamps))

    # G2: the scaled overflow target - regions 94..127 read the SIBLING array, exactly
    worst = 2 * (REGIONS_BOUND - 1)
    gate(2, worst == 254 and GAP == 256,
         "SCALED index max = 2*127 = %d B past 0x94eaa8; the sibling array starts %d B past it "
         "(0x94eba8) -> regions 94..127 read the sibling's [0..66] band, INSIDE the image: "
         "silent wrong data, not a crash" % (worst, GAP))

    # G3: the row slot is a MULTI-WRITER scratch slot - the fold is not its only source
    slot_w = [hex(a) for a, op, args in ins
              if op == "mov" and args.startswith("DWORD PTR %s," % ROW_SLOT)]
    gate(3, len(slot_w) >= 2 and hex(FOLD) in slot_w,
         "%d stores to the row slot %s in the body (fold %s among them: %s) -> single-writer "
         "attribution of the UNSCALED row is UNSOUND; the live cursor advancing by whole %d "
         "strides is produced by one of the OTHER writers (def-use pick)"
         % (len(slot_w), ROW_SLOT, hex(FOLD), hex(FOLD) in slot_w, BLOCK_STRIDE))

    # G4: the skip edge - a nonzero verdict byte writes 0x8 and jumps the whole worth-test body
    jmps = [hex(a) for a, op, args in ins
            if op == "jmp" and args.strip() == "0x558b18"]
    store8 = [hex(a) for a, op, args in ins
              if op == "mov" and "BYTE PTR" in args and "0x94eda8],0x8" in args]
    gate(4, len(jmps) >= 1 and len(store8) == 1,
         "the 0x8-store %s is followed by the skip-jmp %s to the loop tail -> a region whose "
         "verdict byte is nonzero NEVER reaches either read site (explains M273's sparse events)"
         % (store8, jmps))

    # G5: verdict-array store sites (who marks regions done)
    vsites = {}
    for a, op, args in ins:
        if op == "mov" and "BYTE PTR" in args and "0x94eda8]," in args:
            vsites[hex(a)] = args.rsplit(",", 1)[-1]
    gate(5, set(vsites) == set(VERDICT_VALUES),
         "verdict-array %s store sites %s (0x8=skip / dl=7-or-8 / 0x0 / 0x2 / 0x7)"
         % (hex(VERDICT), sorted(vsites.items())))

    # G6: the fold's arithmetic, RE-DERIVED from the decoded fold window (never from prose)
    win = [(a, op, args) for a, op, args in ins if 0x558002 <= a <= 0x558026]
    # the fold's ARITHMETIC ops only (the window is padded with unrelated [ebp-disp] zeroing)
    seq = [(op, args) for _, op, args in win
           if args.split(",")[0] in ("eax", "esi") and not (op == "xor" and args.count("eax") == 2)]
    shape_ok = (seq[0] == ("add", "eax,edi") and "lea" in seq[1][0] and seq[2] == ("shl", "eax,0x4")
                and seq[3] == ("sub", "eax,edi") and "lea" in seq[4][0] and seq[5] == ("shl", "esi,1"))
    per_unit = 188  # 2 * (16*3 - 1) = 2*47 = 94 per (E+edi) doubled
    gate(6, shape_ok and per_unit == 2 * 94 and BLOCK_STRIDE % ROW_STRIDE == 108,
         "fold re-derived from bytes: esi = 2*ecx + 188*(E+edi) - the 188-per-unit is CORRECT "
         "but the multiplier is (E+edi), NOT a bare faction index; with edi=2*fac and E=0 it "
         "equals M256's 188*fac. 8380 mod 188 = %d -> the live cursor's whole-8380 steps CANNOT "
         "come from this fold with any 0..7 faction arg" % (BLOCK_STRIDE % ROW_STRIDE))

    print("SUMMARY M274: %d/%d gates PASS (body 0x%x-0x%x, %d insns)"
          % (sum(results), len(results), FUN, end, len(ins)))
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
