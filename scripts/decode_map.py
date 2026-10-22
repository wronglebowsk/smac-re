#!/usr/bin/env python3
"""Parse an SMAC `.MP` map file (planet.MP / planetx.MP).

Layout verified against **both** shipped maps, which have different dimensions:

    offset 0        15 B    b"TERRANMAP\\0" + 0x1A + u32 version (=5)
    offset 15     2724 B    header struct; first two u32 = width, height
    offset 2739   W*H*22    one 22-byte record per cell, row-major
    +           128 B    trailer, begins b"????????"

    (15 + 2724 + W*H*22 + 128) == file size exactly, for 80x80 (143,667 B)
    and for 128x128 (363,525 B). See MAP_FORMAT.md.

Evidence for the field offsets is runtime, not guesswork: a gdb trace of
FUN_0064cc00 during "THE MAP OF PLANET" on the setup screen logged
    caller=0x5822ac size=2724      (FUN_00582260 -> table)
    caller=0x5822f7 size=140800    (FUN_00582260 -> grid, 6400 * 22)
    caller=0x58231d size=128       (trailer)
from one FILE*, totalling 143,652 with the 15-byte prefix.

    scripts/decode_map.py programs/maps/planet.MP [--json out.json] [--grid out.bin]
"""
import argparse
import json
import struct

MAGIC = b"TERRANMAP\x00"
TABLE_LEN = 2724
TRAILER_LEN = 128
CELL_LEN = 22


def parse(path):
    d = open(path, "rb").read()
    if not d.startswith(MAGIC):
        raise SystemExit(f"{path}: bad magic {d[:9]!r}")
    version = struct.unpack_from("<I", d, 11)[0]
    table = d[15:15 + TABLE_LEN]
    w, h = struct.unpack_from("<II", table, 0)
    cells = w * h
    grid_off = 15 + TABLE_LEN
    grid_end = grid_off + cells * CELL_LEN
    if grid_end > len(d):
        raise SystemExit(f"{path}: file too short for {w}x{h} ({cells} cells x {CELL_LEN} B)")
    trailer = d[grid_end:]
    if not trailer.startswith(b"????????"):
        raise SystemExit(f"{path}: trailer not at {grid_end} (got {trailer[:8]!r})")
    if len(trailer) < TRAILER_LEN:
        raise SystemExit(f"{path}: trailer only {len(trailer)} B (expected >= {TRAILER_LEN})")
    return {
        "path": path,
        "version": version,
        "width": w,
        "height": h,
        "cells": cells,
        "grid_offset": grid_off,
        "grid_end": grid_end,
        "table_words": list(struct.unpack(f"<{len(table)//4}I", table)),
        "grid": d[grid_off:grid_end],
        "trailer": trailer,
        "trailer_len": len(trailer),
        "size": len(d),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--json")
    ap.add_argument("--grid")
    ap.add_argument("--sample", type=int, default=4)
    a = ap.parse_args()

    m = parse(a.file)
    print(f"{a.file}: {m['width']}x{m['height']} = {m['cells']} cells, "
          f"version {m['version']}, size {m['size']}")
    print(f"  grid at {m['grid_offset']}..{m['grid_end']} ({m['cells']*CELL_LEN} B, "
          f"{CELL_LEN} B/cell)")
    print("  header words[0:12]:", " ".join(str(x) for x in m["table_words"][:12]))
    print("  first cells:")
    for i in range(a.sample):
        c = m["grid"][i * CELL_LEN:(i + 1) * CELL_LEN]
        print(f"    [{i:4d}] {c.hex(' ')}")
    print(f"  trailer ({m['trailer_len']} B, variable!):", m["trailer"][:24].hex(" "))

    if a.json:
        out = {k: v for k, v in m.items() if k not in ("grid", "trailer")}
        out["trailer_hex"] = m["trailer"].hex()
        json.dump(out, open(a.json, "w"), indent=1)
        print("wrote", a.json)
    if a.grid:
        open(a.grid, "wb").write(m["grid"])
        print("wrote", a.grid)


if __name__ == "__main__":
    main()
