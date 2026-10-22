#!/usr/bin/env python3
"""Inspect an SMAC `.SAV` save file.

What this does NOT do: parse units, bases or factions. The section sizes are computed by the
loader from counts in the header and those formulas are not recovered yet (see SAVE_FORMAT.md).
Claiming otherwise would be the kind of guess that has burned this project before.

What it does:
  * validates magic + version (86)
  * reads the mission year (u16 at 0x54)
  * optionally checks a file against the section table recovered from the gdb read trace of
    Autosave 30 (80x80 map), including the 300 bytes of sub-threshold reads

    scripts/decode_save.py <file.SAV> [--trace-check]
"""
import argparse
import struct
import sys

MAGIC = b"TERRAN\x00"
MARKER = 0x1A
MIN_VERSION = 86
HEADER_LEN = 796

# caller -> size, in read order, from evidence/readtrace_m11c.log (Autosave 30, 301,896 B)
TRACED_SECTIONS = [
    ("0x59688f", 796, "save header"),
    ("0x596a96", 67040, "block"),
    ("0x596edb", 11488, "block"),
    ("0x5822ac", 2724, "map header struct"),
    ("0x5822f7", 140800, "map grid 80x80x22"),
    ("0x58231d", 128, "map trailer"),
    ("0x597032", 16000, "section"),
    ("0x5970e9", 328, "section"),
    ("0x597146", 3584, "section"),
    ("0x5971b1", 26624, "section"),
    ("0x597299", 4096, "section"),
    ("0x59731e", 6188, "section"),
    ("0x597524", 11248, "section"),
    ("0x5976a3", 256, "section"),
    ("0x59771b", 152, "section"),
    ("0x597786", 10144, "section"),
]
TRACED_FILE_SIZE = 301896
SUB_THRESHOLD = 300  # reads under the 64-byte gdb logging threshold
INTERLEAVED_BEFORE_MAP = 48  # of that 300, before the map table

# Content anchors: unique signatures that land on the same offset in every 80x80 save.
DIMS_SIG = b"\x50\x00\x00\x00\x50\x00\x00\x00"   # u32 80, u32 80
TRAILER_SIG = b"????????"
DIMS_OFF = 796 + 67040 + 11488 + INTERLEAVED_BEFORE_MAP   # 79,372
MAP_SECTIONS = 2724 + 140800
TRAILER_OFF = DIMS_OFF + MAP_SECTIONS                     # 222,896


# Fixed-size sections, in file order, after the 12-byte magic+marker+version prefix.
# Sizes recovered from the push immediates at the read sites inside FUN_00596850; the map
# sections come from FUN_00582260. Verified against the runtime read trace (evidence/
# readtrace_m12.log) and against two saves of different ages.
SECTIONS = [
    (796,    "state header",            "DAT_00985ab8"),
    (4,      "own player",              "DAT_0091b5b4"),
    (67040,  "block A",                 "0x94d430"),
    (11488,  "block B",                 "0x927590"),
    (32,     "small table",             "DAT_00926a78"),
    ("MAP",  "map header + grid + trailer", "FUN_00582260"),
    (16000,  "section",                 "0x985e5c"),
    ("COUNT","count-prefixed section",  "0x930d7c"),
    (3584,   "section",                 "0x989ce0"),
    (26624,  "section",                 "0x98ad88"),
    (4096,   "section",                 "0x92bff0"),
    ("52",   "52-byte records",         "0x933278"),
    ("304",  "304-byte records",        "0x95da10"),
    (256,    "section",                 "0x991598"),
    (152,    "section",                 "0x92bf58"),
    (10144,  "section",                 "0x92d4a0"),
    (28,     "7 x u32 tail values",     "DAT_0091b5b8..DAT_0091b700"),
    (220,    "55 x u32 (5 x 11 records)", "unattributed reader"),
]
TAIL_AFTER_RECORDS = 256 + 152 + 10144 + 28 + 220


def zeros_frac(b):
    return b.count(0) / len(b) if b else 0.0


def solve_records(blob):
    """Split the region between the fixed 4,096 and 256 sections into 52-byte and 304-byte
    records. The Diophantine equation 52n + 304m = len(blob) can have several solutions; the
    right one is picked on content, because 304-byte records are ~80% zero and 52-byte records
    are ~40% zero. Returns (n, m, split_offset, score)."""
    R = len(blob)
    out = []
    for n in range(R // 52 + 1):
        rest = R - 52 * n
        if rest % 304:
            continue
        m = rest // 304
        head, tail = blob[:52 * n], blob[52 * n:]
        if not tail or (n and zeros_frac(head) > 0.6):
            continue
        out.append((n, m, 52 * n, zeros_frac(tail) - zeros_frac(head) if n else zeros_frac(tail)))
    if not out:
        raise SystemExit(f"no 52/304 split of a {R}-byte region")
    out.sort(key=lambda t: -t[3])
    return out[0], out


def parse(path):
    d = open(path, "rb").read()
    if not d.startswith(MAGIC):
        raise SystemExit(f"{path}: not a save (magic {d[:6]!r})")
    if d[7] != MARKER:
        raise SystemExit(f"{path}: marker {d[7]:#x} != 0x1a")
    version = struct.unpack_from("<I", d, 8)[0]
    if version < MIN_VERSION:
        raise SystemExit(f"{path}: version {version} < {MIN_VERSION}")
    year = struct.unpack_from("<H", d, 0x54)[0]
    return {"path": path, "size": len(d), "version": version, "year": year,
            "header": d[:HEADER_LEN], "data": d}


def walk(d):
    """Split a save into its sections. Returns (rows, problems). sizes for the three
    variable sections come from the file itself: one is a u32 prefix, the other two are
    resolved by solve_records()."""
    off, rows, notes = 12, [], []
    for size, label, dest in SECTIONS:
        if isinstance(size, int):
            rows.append((off, size, label, dest))
            off += size
        elif size == "MAP":
            w, h = struct.unpack_from("<II", d, off)
            grid = w * h * 22
            rows.append((off, 2724, f"map header struct ({w}x{h})", dest))
            rows.append((off + 2724, grid, "map grid (W*H*22)", dest))
            rows.append((off + 2724 + grid, 128, "map trailer", dest))
            off += 2724 + grid + 128
        elif size == "COUNT":
            c = struct.unpack_from("<I", d, off)[0]
            rows.append((off, 4, "u32 count prefix", dest))
            rows.append((off + 4, c, "count-prefixed section", dest))
            off += 4 + c
        elif size == "52":
            blob = d[off:len(d) - TAIL_AFTER_RECORDS]
            (n, m, split, score), alts = solve_records(blob)
            rows.append((off, 52 * n, f"52-byte records x {n}", dest))
            rows.append((off + split, 304 * m, f"304-byte records x {m}", dest))
            if len(alts) > 1:
                notes.append(f"record split had {len(alts)} arithmetic solutions "
                             f"{[(a,b) for a,b,_,_ in alts]}; chose ({n},{m}) on record content")
            off = off + len(blob)
    if off != len(d):
        notes.append(f"walk ended at {off:,} but file is {len(d):,}")
    return rows, notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--trace-check", action="store_true")
    ap.add_argument("--sections", action="store_true",
                    help="split the whole file into sections and verify it sums to the file size")
    ap.add_argument("--anchors", action="store_true",
                    help="verify the map-dims and map-trailer signatures")
    ap.add_argument("--hexdump-header", type=int, default=0)
    a = ap.parse_args()

    m = parse(a.file)
    print(f"{a.file}")
    print(f"  size      {m['size']:,} B")
    print(f"  version   {m['version']}")
    print(f"  year      {m['year']} (u16 at 0x54)")
    if a.hexdump_header:
        h = m["header"][:a.hexdump_header]
        for i in range(0, len(h), 16):
            print(f"  {i:04x}  {h[i:i+16].hex(' ')}")

    if a.sections:
        rows, notes = walk(m["data"])
        print(f"  {len(rows)} sections, {sum(s for _, s, _, _ in rows) + 12:,} B total")
        for off, size, label, dest in rows:
            print(f"    {off:>7,}  {size:>7,}  {label:<34} {dest}")
        for nline in notes:
            print("  note:", nline)

    if a.anchors:
        d = m["data"]
        for label, sig, exp in (("map dims 80,80", DIMS_SIG, DIMS_OFF),
                                ("map trailer", TRAILER_SIG, TRAILER_OFF)):
            hits = []
            pos = d.find(sig)
            while pos != -1 and len(hits) < 4:
                hits.append(pos)
                pos = d.find(sig, pos + 1)
            state = "OK" if hits == [exp] else ("MISSING" if not hits else
                    ("OK-unique" if hits[0] == exp else f"WRONG (at {hits})"))
            print(f"  anchor {label}: expected {exp:,} -> found {hits} {state}")
        gap = d.find(TRAILER_SIG) - d.find(DIMS_SIG)
        print(f"  dims->trailer gap {gap:,} (expect {MAP_SECTIONS:,}) "
              f"{'OK' if gap == MAP_SECTIONS else 'MISMATCH'}")

    if a.trace_check:
        total = sum(s for _, s, _ in TRACED_SECTIONS) + SUB_THRESHOLD
        ok = total == m["size"] == TRACED_FILE_SIZE
        print(f"  traced sections + {SUB_THRESHOLD} B sub-threshold = {total:,} B")
        print(f"  file {m['size']:,} B -> {'MATCH' if ok else 'MISMATCH'}")
        if not ok:
            print("  (expected: this check only applies to Autosave 30 / any 80x80 save "
                  "with the same entity counts)")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
