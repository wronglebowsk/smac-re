#!/usr/bin/env python3
"""M19: probe click->tile mapping by trial, with memory as the oracle.

Clicks a list of candidate screen points, and after each one prints the five
unit records that sit on University Base's tile (20,50) plus the screen class.
A point that makes any record's (x,y) change is a tile we moved onto; a point
that opens the base display is the base tile itself.

Usage: python3 scripts/m19_clickprobe.py 363,148 331,148 363,132 ...
"""
import struct
import subprocess
import sys
import time

UNIT_BASE, UNIT_SIZE, N = 0x933278, 52, 119
IDX = [0, 3, 4, 6, 61]


def pid():
    out = subprocess.run(["pgrep", "-x", "terran.exe"], capture_output=True, text=True).stdout.split()
    if not out:
        sys.exit("no terran.exe")
    return int(out[0])


def recs(p):
    f = open(f"/proc/{p}/mem", "rb", 0)
    f.seek(UNIT_BASE)
    b = f.read(UNIT_SIZE * N)
    f.close()
    out = []
    for i in IDX:
        r = b[i * UNIT_SIZE:(i + 1) * UNIT_SIZE]
        x, y = struct.unpack("<HH", r[0:4])
        out.append((i, x, y, r[10] | (r[11] << 8), r[17], r[28:30].hex()))
    return out


def screen():
    r = subprocess.run([sys.executable, "scripts/smac_probe.py", "--quiet"],
                       capture_output=True, text=True)
    first = r.stdout.strip().split("\n")[0] if r.stdout.strip() else "?"
    for tok in first.split():
        if tok.startswith("screen="):
            return tok
    return first[:60]


def main():
    p = pid()
    print("before:", recs(p), screen())
    for pt in sys.argv[1:]:
        x, y = pt.split(",")
        subprocess.run(["python3", "scripts/smac_probe.py", "--quiet", "--click", pt],
                       capture_output=True, text=True)
        time.sleep(1.4)
        now = recs(p)
        moved = [t for t in now if (t[1], t[2]) != (20, 50)]
        print(f"click {pt}: {screen()}  records={now}")
        if moved:
            print(f"  >>> MOVED: {moved}")
            return
        if "base" in screen():
            print("  >>> opened the base display (this point is the base tile)")
    print("no move observed")


if __name__ == "__main__":
    main()
