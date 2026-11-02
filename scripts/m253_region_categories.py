#!/usr/bin/env python3
"""M253-M255: what the region CATEGORY values MEAN, and who starts a NEW GAME.

Pick (NEXT_PROMPT, new from M251 / M250): (a) what NAMES the category bytes 0/2/7/8 at
DAT_0094eda8 — the shape, the 2 writers and the 4 effects are pinned, the names are not;
(b) which of FUN_005b2970's 4 callers is NEW GAME.

Static only: file image + ghidra_out. No box time, no /proc, no gdb.
Acceptance: ONE invocation prints PASS on every gate; an undecided gate prints FAIL with
its numbers.

Gates:
  G1  regression: DAT_0094eda8 reference census (refs / functions / stores / writers / values)
  G2  every READ site classified by test shape; the tested-value set and per-value site counts
  G3  the four effects re-pinned to a pc + owning function (<2 bonus, 7, 8+size, 2 block)
  G4  naming evidence: the string literals each consumer function references, read from the image
  G5  the six STORE sites: where each stored value comes from (immediate vs computed)
  G6  FUN_005b2970's 4 callers: their string literals (name the mode from the tokens)
  G7  the callers' own callers (one level up) + the gate each caller sits behind
  G8  exactly ONE caller attributed to NEW GAME, the others named by their own evidence
"""
import csv
import re
import struct
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXE = ROOT / "programs" / "terran.exe"
INDEX = ROOT / "ghidra_out" / "index.csv"
TEXT_BASE = 0x400000
CATEGORY = 0x94eda8

FUNCS = []
INSN = re.compile(r'^\s+([0-9a-f]{6,8}):\s+(?:[0-9a-f]{2} )*\s*(\S+)\s+(.*)$')
IMM = re.compile(r'0x([0-9a-f]+)')


def load_index():
    with INDEX.open() as f:
        for r in csv.DictReader(f):
            a = int(r['addr'], 16)
            FUNCS.append((a, a + int(r['size_bytes']), r['name']))
    FUNCS.sort()


def fn_of(pc):
    lo, hi = 0, len(FUNCS)
    while lo < hi:
        mid = (lo + hi) // 2
        if FUNCS[mid][0] <= pc:
            lo = mid + 1
        else:
            hi = mid
    i = lo - 1
    if i >= 0 and FUNCS[i][1] > pc:
        return FUNCS[i][2]
    return None


def disasm():
    out = subprocess.run(['objdump', '-d', '-M', 'intel', '--section=.text', str(EXE)],
                         capture_output=True, text=True).stdout
    return [(int(m.group(1), 16), m.group(2), m.group(3).strip())
            for m in (INSN.match(ln.replace('\\t', '\t')) for ln in out.splitlines()) if m]


def immediates(ops):
    return [int(t, 16) for t in IMM.findall(ops)]


def calls_to(ins, target):
    return [(pc, fn_of(pc)) for pc, mn, ops in ins
            if mn == 'call' and immediates(ops)[:1] == [target]]


def body(ins, addr):
    st = next(s for s, e, n in FUNCS if n == addr)
    en = next(e for s, e, n in FUNCS if n == addr)
    return st, en, [(pc, mn, ops) for pc, mn, ops in ins if st <= pc < en]


_IMG = None


def img():
    global _IMG
    if _IMG is None:
        _IMG = EXE.read_bytes()
    return _IMG


def cstr(va, cap=200):
    """NUL-terminated bytes at a VA -> printable str ('' if not printable)."""
    b = img()
    o = va - TEXT_BASE
    if o < 0 or o >= len(b):
        return ''
    z = b.find(b'\0', o, o + cap)
    if z < 0:
        return ''
    s = b[o:z]
    return s.decode('latin1') if all(32 <= c < 127 for c in s) else ''


_INS = None


def ins():
    global _INS
    if _INS is None:
        load_index()
        _INS = disasm()
    return _INS


def g1(): return False, "unimplemented"
def g2(): return False, "unimplemented"
def g3(): return False, "unimplemented"
def g4(): return False, "unimplemented"
def g5(): return False, "unimplemented"
def g6(): return False, "unimplemented"
def g7(): return False, "unimplemented"
def g8(): return False, "unimplemented"


def main():
    gates = []
    for name, fn in [("G1", g1), ("G2", g2), ("G3", g3), ("G4", g4),
                     ("G5", g5), ("G6", g6), ("G7", g7), ("G8", g8)]:
        try:
            ok, detail = fn()
        except Exception as exc:
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
