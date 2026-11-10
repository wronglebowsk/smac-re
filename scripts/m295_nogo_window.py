#!/usr/bin/env python3
"""M295 pin transcriber: the 0x4e3c00 no-go CHAIN bytes from terran.exe.

objdump runs from the entry of FUN_004e3b50 (0x4e3b50) - never mid-instruction
(TRAP 16 law) - covering both functions of the no-go chain:
  0x4e3b50-0x4e3bfa  FUN_004e3b50 owner_of_tile_visible: the 44-B tileview form
                     (0x692184*Y + X>>1, *44, +ds:0x92ae14), movsx BYTE[+7],
                     the 0x985ae8 bit-0x80 override, the flagword bits 3|31
                     visibility test, the FUN_004e37f0 out-param call
  0x4e3c00-0x4e3c76  FUN_004e3c00 territory_nogo: the -1 test, the owner
                     compare, the human-mask byte 0x985b10 (& 0xff) bit tests,
                     the flagword bit-4 alliance test, the param_3 return
Writes evidence/m295_nogo_window.txt: 'PC<TAB>mnemonic' lines.
"""
import os
import re
import subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(REPO, "terran.exe")
OUT = os.path.join(REPO, "evidence", "m295_nogo_window.txt")
LINE = re.compile(r"^\s+([0-9a-f]{6,8}):\t([0-9a-f ]{2,23})\t(.*)$")


def main():
    r = subprocess.run(["objdump", "-d", "-M", "intel", "--start-address=0x4e3b50",
                        "--stop-address=0x4e3c77", EXE],
                       capture_output=True, text=True)
    if r.returncode:
        raise SystemExit("objdump failed: " + r.stderr[:200])
    rows = []
    for ln in r.stdout.splitlines():
        m = LINE.match(ln)
        if not m:
            continue
        rows.append((int(m.group(1), 16), " ".join(m.group(3).split())))
    with open(OUT, "w") as f:
        f.write("# M295 no-go chain: FUN_004e3b50 (owner_of_tile_visible) +\n")
        f.write("# FUN_004e3c00 (territory_nogo) 0x4e3b50-0x4e3c76 (terran.exe .text,\n")
        f.write("# objdump from the 0x4e3b50 entry). Format: PC<TAB>mnemonic\n")
        for pc, t in rows:
            f.write("%08x\t%s\n" % (pc, t))
    print("wrote %s: %d instructions" % (os.path.relpath(OUT, REPO), len(rows)))


if __name__ == "__main__":
    main()
