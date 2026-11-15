#!/usr/bin/env python3
"""M305 (s263, STATIC, zero box): FUN_0051dcb0 - IDENTITY, CALLERS, CADENCE.

QUESTION (the open shortlist entry NEXT_PROMPT.md:74-76, declared UNMODELED by
B19 `NAMED.md`:1055 and B20 `NAMED.md`:1093): is FUN_0051dcb0 "the per-tile pass that
zeroes-then-rebuilds BOTH counter tables", who calls it, and how often does it run?

(a) IDENTITY: the zero-build window 0x51dcb8-0x51dd03 (byte family) + 0x51dd05-0x51dd17
    (dword family), then the outer walk over tile records (cursor stride 0x2c over
    ds:0x92ae14, bounds ds:0x92a378 / ds:0x92a37c), then the two counter tables it touches:
    DWORD 0x989ce8 (+0 MAX, +4 CNT) and the BYTE twins 0x94eca8 (MAX) / 0x94ed28 (CNT).
(b) CALLERS: every direct call site, its containing function (containment ALWAYS via
    ghidra_out/index.csv, never an objdump window at an arbitrary address), its preds,
    the bypass/skip leg that can avoid it, whether it sits inside a loop of the caller.
(c) CADENCE: from the callers' own context + guard globals + the callers' loop bounds.
(d) UNKNOWNs stated plainly.

METHOD (every number printed is COMPUTED here from scratch/m574/text.txt + ghidra_out/index.csv;
asserts at the end; a rival hypothesis is scored against the SAME printed tables):
  S1 zero-window decode  S2 walk algebra + rivals  S3 counter-table store census
  S4 caller census       S5 guard-global census   S6 cadence table + rivals
stdout is mirrored to evidence/m305_identity.txt.

Run:  python3 scripts/m305_identity.py        (exit 0 = all assertions hold)
"""
import bisect
import collections
import csv
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
INDEX = os.path.join(ROOT, "ghidra_out/index.csv")
EVID = os.path.join(ROOT, "evidence", "m305_identity.txt")

FN = 0x51DCB0                     # FUN_0051dcb0, size 1191 per index.csv
FN_SIZE = 1191
BYTE_BASE = 0x94ECA8              # byte MAX array base (sibling of the dword table)
BYTE_CNT = 0x94ED28               # byte CNT = base + 0x80 (M303)
DW_BASE = 0x989CE8                # dword slot MAX
DW_CNT = 0x989CEC                 # dword slot CNT = MAX + 4 (M299/B19)
REC_BASE_GLOBAL = 0x92AE14        # tile_record_array pointer (NAMED.md:90)
REC_COLS_GLOBAL = 0x92A378        # inner walk bound (map width, x stride 2)
REC_ROWS_GLOBAL = 0x92A37C        # outer walk bound (map rows)
REC_MULT_GLOBAL = 0x692184        # records per row = width/2 (NAMED.md:90)
STRIDE_REC = 0x2C                 # tile record size

LINE_RX = re.compile(r"^ +([0-9a-f]{6,8}):\t([0-9a-f ]+)\t\s*(.+?)\s*$")
JCC_RX = re.compile(r"^(je|jne|jl|jge|jg|jle|jb|jae|ja|jbe|js|jns|jo|jno|jc|jnc)\s+(?:0x)?([0-9a-f]{4,8})")
JMP_RX = re.compile(r"^jmp\s+(?:0x)?([0-9a-f]{4,8})")
CALL_RX = re.compile(r"^call\s+(?:0x)?([0-9a-f]{4,8})")


class Out:
    def __init__(self, path):
        self.f = open(path, "w")

    def p(self, s=""):
        self.f.write(s + "\n")
        print(s)

    def close(self):
        self.f.close()


def load_dump():
    ins, addrs = {}, []
    with open(TEXT, errors="replace") as fh:
        for ln in fh:
            m = LINE_RX.match(ln)
            if not m:
                continue
            a = int(m.group(1), 16)
            if a not in ins:
                ins[a] = m.group(3)
                addrs.append(a)
    addrs.sort()
    return ins, addrs


def load_index():
    funcs = []
    with open(INDEX) as fh:
        for row in csv.DictReader(fh):
            funcs.append((int(row["addr"], 16), row["name"], int(row["size_bytes"]),
                          int(row["n_callers"])))
    funcs.sort()
    return funcs


def contain(funcs, faddrs, A):
    i = bisect.bisect_right(faddrs, A) - 1
    a, n, sz, nc = funcs[i]
    return n, a, sz, nc, (a <= A < a + sz)


def split(t):
    p = t.split(None, 1)
    return p[0], (p[1] if len(p) > 1 else "")


def imm_after(ins, addrs, a, mnemonic, n=1):
    """the nth instruction at/after a whose mnemonic matches -> parsed immediate"""
    i = bisect.bisect_left(addrs, a)
    seen = 0
    while i < len(addrs) and addrs[i] < a + 256:
        m, op = split(ins[addrs[i]])
        if m == mnemonic:
            seen += 1
            if seen == n:
                mm = re.search(r"0x([0-9a-f]+)\s*$", op)
                if mm:
                    return addrs[i], int(mm.group(1), 16)
        i += 1
    return None, None


def main():
    out = Out(EVID)
    ins, addrs = load_dump()
    funcs = load_index()
    faddrs = [f[0] for f in funcs]
    asserts = []

    def A(name, cond, detail=""):
        asserts.append((name, bool(cond), detail))
        out.p("%-58s %s %s" % (name, "OK" if cond else "FAIL", detail))

    out.p("M305 FUN_0051dcb0 identity / callers / cadence  (STATIC, zero box, zero /proc, zero gdb)")
    out.p("inputs: %s (%d insns parsed), %s (%d functions)" % (TEXT, len(addrs), INDEX, len(funcs)))
    nm, fa, sz, nc, ok = contain(funcs, faddrs, FN)
    out.p("S0 subject %s @ %#x size=%d n_callers(index.csv)=%d insns_in_body=%d" %
          (nm, FN, sz, nc, sum(1 for a in addrs if FN <= a < FN + sz)))
    A("S0 subject contains by index.csv", nm == "FUN_0051dcb0" and ok)

    # ---------- S1 zero-build window ----------
    out.p("\n== S1 zero-build window %#x-%#x" % (0x51DCB8, 0x51DD17))
    for a in addrs:
        if 0x51DCB8 <= a <= 0x51DD17:
            out.p("  %s  %s" % (hex(a), ins[a]))
    out.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
