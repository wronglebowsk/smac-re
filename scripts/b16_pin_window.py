#!/usr/bin/env python3
"""B16 pin transcriber: the scan-loop PRE-CHECK byte windows from terran.exe.

objdump runs from the FUNCTION ENTRY (0x55f650) - never from an arbitrary
address (mid-instruction start misaligns the whole window) - and the two
ranges the B16 pin gate reads are filtered out of that aligned stream:

  0x55f650-0x55f7c0  FUN_0055f650 prologue: pod x/y, owner, type-required
                     class, pod tileview (the record formula), pod region
  0x5637d0-0x563990  the loop prelude (the [ebp-0x58]/[ebp-0x74] class gate)
                     and the 7 loop-head pre-checks

Writes evidence/b16_precheck_window.txt: 'PC<TAB>mnemonic' lines.
"""
import os
import re
import subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(REPO, "terran.exe")
OUT = os.path.join(REPO, "evidence", "b16_precheck_window.txt")
LO, HI = 0x55f650, 0x55f7c0
LO2, HI2 = 0x5637d0, 0x563990
LINE = re.compile(r"^\s+([0-9a-f]{6,8}):\t([0-9a-f ]{2,23})\t(.*)$")


def main():
    r = subprocess.run(["objdump", "-d", "-M", "intel", "--start-address=0x55f650",
                        "--stop-address=0x563990", EXE],
                       capture_output=True, text=True)
    if r.returncode:
        raise SystemExit("objdump failed: " + r.stderr[:200])
    rows = []
    for ln in r.stdout.splitlines():
        m = LINE.match(ln)
        if not m:
            continue
        pc = int(m.group(1), 16)
        if LO <= pc <= HI or LO2 <= pc <= HI2:
            rows.append((pc, " ".join(m.group(3).split())))
    with open(OUT, "w") as f:
        f.write("# B16 pin window: FUN_0055f650 prologue 0x55f650-0x55f7c0 and\n")
        f.write("# the scan-loop pre-check chain 0x5637d0-0x563990 (terran.exe .text,\n")
        f.write("# objdump from the function entry). Format: PC<TAB>mnemonic\n")
        for pc, t in rows:
            f.write("%08x\t%s\n" % (pc, t))
    print("wrote %s: %d instructions" % (os.path.relpath(OUT, REPO), len(rows)))


if __name__ == "__main__":
    main()
