#!/usr/bin/env python3
"""M244: the save tail - (1) the map-trailer/region-map LENGTH FORMULA, (2) what the
count-prefixed block holds, (3) who reads the tail's last blocks.

Static: no gdb, no box driving; /proc/<pid>/mem READS only, and only in gate 5.
Acceptance: `python3 scripts/m244_save_tail.py` prints `PASS M244: 5/5 gates`.

Gates
  region-formula  region_len(w,h) = (((w+4)//5 + 1)//2) * ((h+4)//5)  (FUN_00582000,
                  shard_014.c:27263-27265) closes planet.MP + planetx.MP on the byte and
                  puts the count u32 at the measured offset on all 17 saves.
  count-shape     the block after the u32 at DAT_00927538 is 8-B records
                  (type in {0,1,2}, faction <= 7, step non-decreasing and <= the header's
                  u32 at file 80, x < w, y < h); count == 8 * record count.
  replay-bases    replaying that log with FUN_0059bcb0's semantics (shard_015.c:13657-13708)
                  yields EXACTLY the (x, y, owner) of the 304-B base records, on every save.
  owner-byte      base +4 == the log's final faction for the site, base +5 == the founding
                  faction: the +4 != +5 bases are exactly the sites a type-1 record moved.
  tail-legs       the codec's four tail pushes are 0x100, 0x100, 0x98, 0x27a0
                  (shard_015.c:10654/10676/10698/10720) and NO 220- or 28-B leg exists; the
                  152-B leg is anchored by the unique [9999,9999,0,0,2100,2600] dword row.
"""
import glob
import os
import re
import struct
import subprocess
import sys

SAVE_DIR = "programs/saves"
MAP_FILES = ["programs/maps/planet.MP", "programs/maps/planetx.MP"]
SHARD15 = "ghidra_out/shard_015.c"
SHARD14 = "ghidra_out/shard_014.c"

MAP_HDR_OFF = 79372
MAP_HDR_LEN = 2724
CELL_LEN = 22
SEC16000 = 16000
UNIT_LEN = 52
BASE_LEN = 304
TAIL_LEN = 10800
MIDDLE = 3584 + 26624 + 4096
# SAVE_FORMAT.md's traced 80x80 save (n=119 m=37 count=328): units, bases, tail starts.
RECORDED_80 = (273660, 279848, 291096, 301896)


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def region_len(w, h):
    """FUN_00582000: DAT_0092ad9c=(W+4)/5, DAT_0092ada0=(H+4)/5,
    DAT_0092ada4=((DAT_0092ad9c+1)/2)*DAT_0092ada0."""
    rw = (w + 4) // 5
    rh = (h + 4) // 5
    return ((rw + 1) // 2) * rh


def saves():
    return sorted(glob.glob(os.path.join(SAVE_DIR, "**", "*.SAV"), recursive=True))


def load(path):
    with open(path, "rb") as fh:
        return fh.read()


def walk(d):
    """The B2 walk with the trailer length DERIVED instead of tabulated."""
    w, h = u32(d, MAP_HDR_OFF), u32(d, MAP_HDR_OFF + 4)
    grid = MAP_HDR_OFF + MAP_HDR_LEN
    reg = region_len(w, h)
    count_off = grid + w * h * CELL_LEN + reg + SEC16000
    n_units, n_bases = u32(d, 68), u32(d, 72)
    cnt = u32(d, count_off) if count_off + 4 <= len(d) else -1
    units = count_off + 4 + max(cnt, 0) + MIDDLE
    bases = units + UNIT_LEN * n_units
    tail = bases + BASE_LEN * n_bases
    return dict(w=w, h=h, reg=reg, grid=grid, count_off=count_off, cnt=cnt, n_units=n_units,
                n_bases=n_bases, units=units, bases=bases, tail=tail, block=count_off + 4)


def records(d, off, cnt):
    return [struct.unpack_from("<BBHHH", d, off + 8 * i) for i in range(cnt // 8)]


def replay(recs):
    """FUN_0059bcb0's semantics: type 0 appends (x, y, fac), type 1 rewrites the third word
    of the (x, y) entry, type 2 removes it. Returns (live, orphans)."""
    live, orphans = [], []
    for (t, fac, step, x, y) in recs:
        if t == 0:
            live.append([x, y, fac])
        elif t in (1, 2):
            hit = [i for i, e in enumerate(live) if e[0] == x and e[1] == y]
            if not hit:
                orphans.append((t, fac, step, x, y))
                continue
            if t == 1:
                live[hit[0]][2] = fac
            else:
                live.pop(hit[0])
        else:
            orphans.append((t, fac, step, x, y))
    return live, orphans


GATES = ["region-formula", "count-shape", "replay-bases", "owner-byte", "tail-legs"]


def main():
    print("M244 census skeleton - gates:", ",".join(GATES))
    return 2


if __name__ == "__main__":
    sys.exit(main())
