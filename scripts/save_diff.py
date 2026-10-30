#!/usr/bin/env python3
"""Region-aware .SAV <-> memory diff. Refuses a range that straddles a region boundary.

Why this exists: M114 claimed two "rewritten tails" (block A 67,080..67,143 and the map header 81,408..82,100)
and merged that claim; both ranges straddle a k-change (67,072 and 82,074) and had been diffed with ONE region's
mapping constant, so they "differed" by construction. A diff is only meaningful wholly inside one region, so the
tool computes the regions from the poke anchors and REFUSES anything that crosses a boundary instead of printing a
number that looks like evidence.

    python3 scripts/save_diff.py --save m54b_clean.SAV --range 66048-67840          # memory of the live game
    python3 scripts/save_diff.py --save m54b_clean.SAV --range 66048-67840 --pid 1234
    python3 scripts/save_diff.py --regions                                          # just print the region table
"""
import argparse
import os
import re
import struct
import subprocess
import sys

# (file_offset, destination) anchors measured by scripts/m113_save_map.py (m113map1/2/3, a poke-and-scan).
ANCHORS = [
    (16384, 0x951104), (32768, 0x955104), (49152, 0x959104), (65536, 0x95D104), (66048, 0x95D304),
    (68096, 0x927684), (80384, 0x92A76C), (81920, 0x92AD6C), (82432, 0x40A67B0), (98304, 0x40AA5B0),
    (114688, 0x40AE5B0), (131072, 0x40B25B0), (147456, 0x40B65B0), (163000, 0x40BA268), (171192, 0x40BC268),
    (172287, 0x15E2BAF), (173240, 0x986209), (174000, 0x986501), (180144, 0x987D01), (188291, 0x989CD4),
    (188467, 0x930E20), (196608, 0x98BF49), (212992, 0x98FF49), (218675, 0x99157C), (221000, 0x92C8F9),
    (222896, 0x9332E9), (223024, 0x933369), (225096, 0x933B81), (227144, 0x95DD7D), (229192, 0x95E57D),
]


def regions(anchors=ANCHORS):
    """Group consecutive equal-k anchors; return [(lo_off, hi_off, k, n_anchors)] with hi exclusive."""
    out = []
    for off, dest in sorted(anchors):
        k = dest - off
        if out and out[-1][2] == k:
            out[-1][1] = off + 1
            out[-1][3] += 1
        else:
            if out:
                out[-1][1] = off          # the next anchor with a different k closes this run
            out.append([off, off + 1, k, 1])
    return [tuple(r) for r in out]


# Boundaries derived exactly (each from an anchor plus its section's documented destination base), NOT midpoints:
#   67,852 = 68,096 - (0x927684 - 0x927590)   block B starts at dest 0x927590
#   82,088 = 82,432 - (0x40A67B0 - 0x40A6660) the grid starts at dest 0x40A6660
#   172,291 = 173,240 - (0x986209 - 0x985E5C) the 16,000-B section starts at dest 0x985E5C
#   172,200 = the 91-B map trailer (3-leg map: 2,724 + 90,112 + 91)
#   222,783 = 222,896 - (0x9332E9 - 0x933278) the 52-B record array starts at dest 0x933278
KNOWN_BOUNDARIES = [67852, 82088, 172200, 172291, 222783]


def check_range(lo, hi, anchors=ANCHORS):
    """Return (k, region) for a range wholly inside ONE region, else raise naming what it crosses.

    Two independent guards, because either alone let M114 through: the anchors give a k-run, and the KNOWN
    boundaries give the exact ends of the sections whose destination base is documented.
    """
    for b in KNOWN_BOUNDARIES:
        if lo < b < hi:   # a half-open range [lo, hi) may END exactly on a boundary
            raise SystemExit(
                "REFUSED: range %d..%d crosses the exact section boundary %d. A window that straddles a k-change "
                "diffed with one region's constant manufactures diffs that look exactly like rewriting (M114). "
                "Split the range at %d and run it per region." % (lo, hi, b, b))
    rs = regions(anchors)
    for rlo, rhi, k, _ in rs:
        if rlo <= lo and hi <= rhi:
            return k, (rlo, rhi)
    # name the boundary the range crosses
    bounds = []
    for (alo, _), (bhi, _) in zip(sorted(anchors), sorted(anchors)[1:]):
        ka, kb = dict((o, d) for o, d in anchors)[alo] - alo, dict((o, d) for o, d in anchors)[bhi] - bhi
        if ka != kb:
            bounds.append((alo + bhi) // 2)
    crossing = [b for b in bounds if lo <= b <= hi]
    raise SystemExit(
        "REFUSED: range %d..%d is not inside one region (boundary at %s). A window that straddles a k-change "
        "diffed with one region's constant manufactures diffs that look exactly like rewriting (M114). Split the "
        "range at %s and run it per region." %
        (lo, hi, ", ".join(str(b) for b in crossing) or "unknown", crossing[0] if crossing else "that offset"))


def pid_of(name="terran.exe"):
    try:
        return int(subprocess.check_output(["pgrep", "-x", name], text=True).split()[0])
    except Exception:
        raise SystemExit("no live %s — pass --pid" % name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--save", default="m54b_clean.SAV")
    ap.add_argument("--range", default=None, help="LO-HI file offsets (decimal or 0x)")
    ap.add_argument("--pid", type=int, default=None)
    ap.add_argument("--regions", action="store_true")
    ap.add_argument("--show", type=int, default=0, help="print up to N differing offsets")
    a = ap.parse_args()

    if a.regions or not a.range:
        print("region                       span (file offsets)        k            anchors")
        for rlo, rhi, k, n in regions():
            print("  0x%08x..0x%08x  %8d..%-8d  0x%x  %d" % (k, k, rlo, rhi - 1, k, n))
        return 0

    lo_s, _, hi_s = a.range.replace("0x", "").partition("-")
    lo, hi = int(lo_s, 16) if "0x" in a.range else int(lo_s), int(hi_s, 16) if "0x" in a.range else int(hi_s)
    k, (rlo, rhi) = check_range(lo, hi)
    pid = a.pid or pid_of()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = a.save if os.path.isabs(a.save) else os.path.join(root, "programs/saves", a.save)
    f = open(path, "rb").read()[lo:hi]
    fd = os.open("/proc/%d/mem" % pid, os.O_RDONLY)
    try:
        m = os.pread(fd, len(f), lo + k)
    finally:
        os.close(fd)
    if len(m) != len(f):
        raise SystemExit("short read at 0x%x (region %d..%d)" % (lo + k, rlo, rhi))
    diffs = [i for i in range(len(f)) if f[i] != m[i]]
    print("%s range %d..%d (k=0x%x, region %d..%d, pid %d): %d differing byte(s) of %d"
          % (os.path.basename(path), lo, hi, k, rlo, rhi - 1, pid, len(diffs), len(f)))
    for i in diffs[:a.show]:
        fo = lo + i
        print("  file %d  0x%02x -> 0x%02x" % (fo, f[i], m[i]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
