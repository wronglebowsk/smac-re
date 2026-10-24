#!/usr/bin/env python3
"""Read-only pread snapshot for the M53p Class-J hunt. Writes evidence/m53p_j_live.tsv.

    python3 scripts/m53p_j_snap.py            # all 76 bases + globals
Never writes to /proc/<pid>/mem.
"""
import os
import struct
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "evidence", "m53p_j_live.tsv")
BASES = 0x95da10
STRIDE = 0x130
GL = {"budget008f0c68": 0x8f0c68, "d30_008f0d30": 0x8f0d30, "cc8_008f0cc8": 0x8f0cc8,
      "baseidx_0068cbb0": 0x68cbb0, "curbase_008f0d60": 0x8f0d60, "k27c": 0x92a27c,
      "k2a4": 0x92a2a4, "mapw": 0x92a378, "maph": 0x92a37c, "terr": 0x92ae14,
      "mask985b10": 0x985b10, "k85b48": 0x985b48, "k85bc0": 0x985bc0, "g91c628": 0x91c628,
      "k85afc": 0x985afc, "wrap": 0x92a394, "t_cap2": 0x92a2cc}


def pid():
    r = subprocess.run(["pgrep", "-x", "terran.exe"], capture_output=True, text=True)
    pids = [int(x) for x in r.stdout.split()]
    if not pids:
        sys.exit("no terran.exe running")
    return pids[0]


def main():
    p = pid()
    f = open(f"/proc/{p}/mem", "rb")

    def rd(a, n):
        f.seek(a)
        d = f.read(n)
        if len(d) != n:
            raise SystemExit("short read at %x" % a)
        return d

    def u32(a):
        return struct.unpack_from("<I", rd(a, 4), 0)[0]

    lines = []
    hdr = ["idx", "fac", "pop", "x", "y", "d30", "d34", "d38", "d78", "d7c", "d80",
           "nib0", "nib1", "fac_bits_lo", "fac_bits_hi", "bc", "c0", "c4", "c8"]
    lines.append("#globals " + " ".join("%s=0x%x" % (k, u32(v)) for k, v in sorted(GL.items())))
    lines.append("\t".join(hdr))
    nb = u32(0x985af4)
    for i in range(nb):
        b = BASES + i * STRIDE
        d = rd(b, STRIDE)
        g = lambda off, fmt: struct.unpack_from(fmt, d, off)[0]
        row = [i, g(4, "<B"), g(6, "<B"), g(0, "<H"), g(2, "<H"),
               "0x%x" % g(0x30, "<I"), "0x%x" % g(0x34, "<I"), "0x%x" % g(0x38, "<I"),
               "0x%x" % g(0x78, "<I"), g(0x7c, "<i"), g(0x80, "<i"),
               "0x%x" % g(0x84, "<I"), "0x%x" % g(0x88, "<I"),
               "0x%x" % g(0x8c, "<I"), "0x%x" % g(0x90, "<I"),
               g(0xbc, "<i"), g(0xc0, "<i"), g(0xc4, "<i"), g(0xc8, "<i")]
        lines.append("\t".join(str(x) for x in row))
    txt = "\n".join(lines) + "\n"
    open(OUT, "w").write(txt)
    print("wrote", OUT, "pid", p)
    print(lines[0])
    # distribution of c7c/c80
    import collections
    c7c = collections.Counter()
    c80 = collections.Counter()
    for ln in lines[2:]:
        p = ln.split("\t")
        c7c[p[9]] += 1
        c80[p[10]] += 1
    print("c7c values:", dict(c7c))
    print("c80 values:", dict(c80))


main()
