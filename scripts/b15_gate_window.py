#!/usr/bin/env python3
"""B15 (s243): record the pinned objdump windows that are the authority for
sim/gatetables.py -> evidence/b15_gate_window.txt. Static file-cache read
(scratch/m574/text.txt = the objdump -d .text cache of programs/terran.exe);
EVERY recorded instruction line's bytes are verified against terran.exe via
the PE section table (Greptile P2 s243: a stale cache must never carry a new
exe's hash). No box, no /proc, no gdb, no process attach."""
import hashlib
import os
import re
import struct
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(REPO, "scratch", "m574", "text.txt")
OUT = os.path.join(REPO, "evidence", "b15_gate_window.txt")
EXE = os.path.join(REPO, "programs", "terran.exe")

WINDOWS = [
    ("prologue msg-gate 0x55f6b0-0x55f6dc", 0x55F6B0, 0x55F6DC),
    ("prologue case 0x55f730-0x55f750", 0x55F730, 0x55F750),
    ("prologue region/block/verdict 0x55f79f-0x55f820", 0x55F79F, 0x55F820),
    ("scan gate window 0x563bf7-0x563cbf", 0x563BF7, 0x563CBF),
    ("writer FUN_0051dcb0 zero sweep 0x51dcb0-0x51dcea", 0x51DCB0, 0x51DCEA),
    ("writer FUN_0051dcb0 lea-copy store 0x51df35-0x51dffa", 0x51DF35, 0x51DFFA),
]

FULL = re.compile(r"^\s*([0-9a-f]{6,8}):\s+((?:[0-9a-f]{2} )+)\s*([a-z][a-z0-9]*)\s*(.*)$")
CONT = re.compile(r"^\s*([0-9a-f]{6,8}):\s+((?:[0-9a-f]{2} )+)\s+(.*)$")
ADDR = re.compile(r"^\s*([0-9a-f]{6,8}):")


def verify_map(exe, pairs):
    """terran.exe is a dump-style image: file offset = VA + delta (delta ==
    -ImageBase). Derive the delta from the window bytes themselves (anchor on
    a long line, keep the candidate that verifies EVERY window line), so a
    stale cache can never carry this exe's hash (Greptile P2, s243).
    Returns the single verified delta, or None."""
    anchor_va, anchor_hex = max(((a, hx) for (a, hx) in pairs if len(hx) >= 14),
                                key=lambda p: len(p[1]), default=pairs[0])
    pat = bytes.fromhex(anchor_hex)
    cands, pos = [], 0
    while True:
        p = exe.find(pat, pos)
        if p < 0:
            break
        cands.append(p - anchor_va)
        pos = p + 1
    good = [d for d in sorted(set(cands))
            if all(exe[d + a:d + a + len(bytes.fromhex(hx))] == bytes.fromhex(hx)
                   for (a, hx) in pairs)]
    return good[0] if len(good) == 1 else None


def main():
    exe = open(EXE, "rb").read()
    exe_sha = hashlib.sha256(exe).hexdigest()
    exe_sz = len(exe)
    with open(TEXT, errors="replace") as f:
        src = f.readlines()
    out_lines = []
    pairs = []
    for name, lo, hi in WINDOWS:
        out_lines.append("## %s" % name)
        started = False
        for ln in src:
            ma = ADDR.match(ln)
            if not ma:
                continue
            a = int(ma.group(1), 16)
            if not (lo <= a <= hi):
                if started and a > hi:
                    break
                continue
            hm = CONT.match(ln)
            if not hm:
                print("unparsable cache line %r" % ln[:60])
                return 1
            hx = hm.group(2).replace(" ", "")
            pairs.append((a, hx))
            out_lines.append(ln.rstrip("\n"))
            started = True
        if not started:
            print("WINDOW %s EMPTY" % name)
            return 1
    delta = verify_map(exe, pairs)
    if delta is None:
        print("NO UNIQUE VERIFIED MAPPING - cache vs terran.exe refused")
        return 1
    with open(OUT, "w") as f:
        f.write("# B15 recorded gate windows - authority for sim/gatetables.py\n")
        f.write("# produced by scripts/b15_gate_window.py from scratch/m574/text.txt\n")
        f.write("# terran.exe sha256=%s size=%d\n" % (exe_sha, exe_sz))
        f.write("# all %d instruction lines byte-verified against terran.exe at VA->file delta %s\n"
                % (len(pairs), hex(delta)))
        f.write("\n".join(out_lines) + "\n")
    print("wrote %s (%d lines, %d instruction lines byte-verified at delta %s)"
          % (OUT, len(out_lines), len(pairs), hex(delta)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
