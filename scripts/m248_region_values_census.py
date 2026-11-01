#!/usr/bin/env python3
"""M248/M249: what the coarse region-map BYTES mean, and what terrain record +3 is.

M248  the region map (DAT_0092ae18, length ((Rw+1)/2)*Rh) is BUILT by FUN_0058ce00
      (shard_015.c:4707-4745): for each region (x = row&1 step 2 < Rw, y < Rh) it samples 9
      tiles (dx from DAT_0067850c[i], dy from DAT_00678990[i], i = 0..8, map coords x*5+dx,
      y*5+dy, wrapped mod DAT_0092a378/DAT_0092a37c unless _DAT_0092a394&1) and stores the
      terrain record +3 of the FIRST sample whose record +0 & 0xe0 > 0x5f (cat > 2, land);
      0 when no sample is land.  The map's ONLY reader is FUN_00556690 (2 sites), which uses
      the byte as a label filter before expanding to the fine grid.
      GATE G1: the builder's rule as read from the image (9 offsets, land test, +3, else 0).
      GATE G2: recompute the region map from each save's / each .MP's terrain grid by that
               rule -> byte-for-byte equal to the stored bytes (17 saves + 2 maps).
      GATE G3: reference census of DAT_0092ae18: exactly 1 writer function (the builder, via
               FUN_00582360), exactly 1 reader function (FUN_00556690, via FUN_00582340), the
               rest are alloc/free/file-I/O; no other function touches the array.
M249  terrain record +3 (the label the region map carries).
      GATE G4: image-wide store census of record+3: every reference is a READ (the value is
               map-file data, loaded verbatim by FUN_00582000) — with the read count + sites.
      GATE G5: the +3 values are a REGION LABEL: per save, the set of nonzero region bytes ==
               the set of +3 values on land tiles reached by the sampling, and the readers use
               it as an index into a per-faction byte array at DAT_0094eda8 (base + fac*0x20bc)
               and split it at 0x40 (shard_012.c:7331-7340).

  python3 scripts/m248_region_values_census.py   -> evidence/m248_region_values.txt
"""
import glob
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVE_DIR = os.path.join(ROOT, "programs", "saves")
MAPS = [os.path.join(ROOT, "programs/maps/planet.MP"),
        os.path.join(ROOT, "programs/maps/planetx.MP")]
SHARD12 = os.path.join(ROOT, "ghidra_out", "shard_012.c")
SHARD14 = os.path.join(ROOT, "ghidra_out", "shard_014.c")
SHARD15 = os.path.join(ROOT, "ghidra_out", "shard_015.c")
EVID = os.path.join(ROOT, "evidence", "m248_region_values.txt")
RECSZ = 0x2C
DX_VA, DY_VA = 0x67850C, 0x678990
GATES = [
    ("G1 builder rule (9 samples, land test, record+3, else 0)", None),
    ("G2 region map recomputed from the grid == stored bytes", None),
    ("G3 DAT_0092ae18 reference census (1 reader fn, 1 writer fn)", None),
    ("G4 record+3 has no in-image writer (reads only)", None),
    ("G5 +3 is a region label (value sets + reader tables)", None),
]


def saves():
    return sorted(glob.glob(os.path.join(SAVE_DIR, "**", "*.SAV"), recursive=True))


def main():
    lines = []
    ok = 0
    for i, (name, fn) in enumerate(GATES):
        if fn is None:
            lines.append("FAIL %s: not implemented\n" % name)
            continue
        try:
            out = fn()
        except Exception as exc:            # a broken gate is a FAIL, never a crash
            out = ["FAIL %s: %s\n" % (name, exc)]
        lines += out
        if out and out[0].startswith("PASS"):
            ok += 1
    lines.append("\nSUMMARY %d/%d gates on %d saves + 2 .MP\n" % (ok, len(GATES), len(saves())))
    os.makedirs(os.path.dirname(EVID), exist_ok=True)
    with open(EVID, "w") as fh:
        fh.write("".join(lines))
    for l in lines:
        if l.startswith(("PASS", "FAIL", "INFO", "SUMMARY")):
            print(l.rstrip())
    print("SUMMARY %d/%d" % (ok, len(GATES)))
    if ok == len(GATES):
        print("PASS M248: %d/%d gates" % (ok, len(GATES)))
    return 0 if ok == len(GATES) else 1


if __name__ == "__main__":
    sys.exit(main())
