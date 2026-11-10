#!/usr/bin/env python3
"""B15 (s243): record the pinned objdump windows that are the authority for
sim/gatetables.py -> evidence/b15_gate_window.txt. Static file-cache read
(scratch/m574/text.txt = the objdump -d .text cache of programs/terran.exe);
no box, no /proc, no gdb, no process attach."""
import hashlib
import os
import subprocess
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


def main():
    exe_sha = hashlib.sha256(open(EXE, "rb").read()).hexdigest()
    exe_sz = os.path.getsize(EXE)
    lines = []
    with open(TEXT, errors="replace") as f:
        src = f.readlines()
    import re
    addr = re.compile(r"^\s*([0-9a-f]{6,8}):")
    for name, lo, hi in WINDOWS:
        lines.append("## %s" % name)
        started = False
        for ln in src:
            m = addr.match(ln)
            if not m:
                continue
            a = int(m.group(1), 16)
            if lo <= a <= hi:
                lines.append(ln.rstrip("\n"))
                started = True
            elif started and a > hi:
                break
        if not started:
            print("WINDOW %s EMPTY" % name)
            return 1
    with open(OUT, "w") as f:
        f.write("# B15 recorded gate windows - authority for sim/gatetables.py\n")
        f.write("# produced by scripts/b15_gate_window.py from scratch/m574/text.txt\n")
        f.write("# terran.exe sha256=%s size=%d\n" % (exe_sha, exe_sz))
        f.write("\n".join(lines) + "\n")
    print("wrote %s (%d lines)" % (OUT, len(lines)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
