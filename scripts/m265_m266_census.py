#!/usr/bin/env python3
"""M265: what the 7 allocated 0x22480 view-table blocks ARE.
M266: why FUN_00583c70 exists with ZERO references.

Instrument = three sources, one run, no box time:
  (a) the whole-image .text disassembly corpus scratch/m574/text.txt,
  (b) the raw PE image programs/terran.exe (section map from objdump -h),
  (c) ghidra_out/index.csv function containment (addr,name,size).

Acceptance: ONE real invocation prints `SUMMARY M265/M266: 11/11 gates PASS`.
"""
import os
import re
import struct
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(REPO, "scratch/m574/text.txt")
EXE = os.path.join(REPO, "programs/terran.exe")
INDEX = os.path.join(REPO, "ghidra_out/index.csv")

LINE = re.compile(r"^\s+([0-9a-f]{6,8}):\t((?:[0-9a-f]{2} ){0,7}[0-9a-f]{2} )?\t?(\S+) ?(.*)$")


def insns(lo, hi):
    """(pc, mnemonic, operands) for every corpus line in [lo,hi]."""
    out = []
    with open(TEXT, "r", errors="replace") as f:
        for line in f:
            m = LINE.match(line.replace("\\t", "\t"))
            if not m:
                continue
            a = int(m.group(1), 16)
            if a > hi:
                break
            if a >= lo:
                out.append((a, m.group(3).lower(), m.group(4).strip()))
    return out


# ---- filled in by the probe pass -------------------------------------------------
FUNCS = []      # (addr, name, size) from index.csv
SECS = []       # (name, vma, size, file_off) from objdump -h
IMG = b""       # the raw file image


def fn_of(addr):
    raise NotImplementedError


def dword_at(va):
    raise NotImplementedError


def raw_dword_hits(value):
    """Every file offset whose LE dword == value."""
    raise NotImplementedError


GATES = []


def gate(name, ok, detail):
    GATES.append((name, ok, detail))
    print("%s %s | %s" % ("PASS" if ok else "FAIL", name, detail))


# G1..G7 = M265, G8..G11 = M266  (bodies appended by the implementation pass)
print("SUMMARY M265/M266: %d/%d gates PASS" % (sum(1 for g in GATES if g[1]), len(GATES)))
