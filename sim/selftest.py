"""sim.selftest — the runnable acceptance for the R1 build track (BUILD_SPINE.md).

    python3 -m sim.selftest --map programs/maps/planet.MP --rules data/alpha.json   # B1
    python3 -m sim.selftest --sav <save>                                            # B2 (later rung)

B1 gates, in order. Every one is a comparison against an independent source
(scripts/decode_map.py's own numbers, the header's own land-cell word, the JSON the
parser produced) — nothing here is graded against a value this file invented.

    1  sim.map's dims/cells/size/offsets == decode_map.py's for the same file
    2  both shipped dimensions (80x80 and 128x128) were actually checked
    3  every tile's terrain index is < TERRAIN_CARDINALITY and the used set has no gaps
    4  every tile's owner nibble is 0..7 or 0xf
    5  land cells (cell+7 == 0xff) == header word 5, per map
    6  every alpha.json section loaded with a non-zero record count

Exit 0 and print PASS only if every gate passes on the real bytes.
"""

import argparse
import os
import sys

from . import map as somap
from . import rules as sorules

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
import decode_map  # noqa: E402  (allowed by BUILD_SPINE grading rule 4)

EXPECTED_DIMS = {(80, 80), (128, 128)}
SIBLING = {"planet.MP": "planetx.MP", "planetx.MP": "planet.MP"}


def fail(msg):
    print("FAIL " + msg)
    return 1


def check_map(path, results):
    """Gates 1, 3, 4, 5 for one map file; returns the dims it checked."""
    m = somap.parse(path)
    ref = decode_map.parse(path)
    mine = (m.width, m.height, m.cells, m.size, m.grid_off, m.trailer_len, m.version)
    theirs = (ref["width"], ref["height"], ref["cells"], ref["size"],
              ref["grid_offset"], ref["trailer_len"], ref["version"])
    results.append(("parity %-16s sim=%s decode_map=%s" % (os.path.basename(path), mine, theirs),
                    mine == theirs))
    st = m.stats()
    used = st["terrain_used"]
    contiguous = used == list(range(len(used)))
    results.append(("terrain-range %-12s used=%d..%d (%d values) out_of_range=%d gaps=%s" % (
        os.path.basename(path), used[0], used[-1], len(used), st["terrain_out_of_range"],
        "none" if contiguous else "YES"),
        st["terrain_out_of_range"] == 0 and contiguous and used[-1] < somap.TERRAIN_CARDINALITY))
    results.append(("owner-nibble %-11s hist=%s invalid=%d" % (
        os.path.basename(path), sorted(st["owner_hist"].items()), st["owner_invalid"]),
        st["owner_invalid"] == 0))
    results.append(("land-count %-14s cells+7=0xff:%d header word5:%d" % (
        os.path.basename(path), st["land_cells"], st["header_land_cells"]),
        st["land_cells"] == st["header_land_cells"]))
    return (m.width, m.height)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sim.selftest")
    ap.add_argument("--map", action="append", default=[], help="a .MP file (repeatable)")
    ap.add_argument("--rules", help="path to data/alpha.json")
    ap.add_argument("--sav")
    ap.add_argument("--replay")
    args = ap.parse_args(argv)

    results = []
    maps = list(args.map)
    if len(maps) == 1:
        sibs = SIBLING.get(os.path.basename(maps[0]))
        if sibs:
            cand = os.path.join(os.path.dirname(maps[0]), sibs)
            if os.path.exists(cand):
                maps.append(cand)
                print("note: --map expanded to %s (rung B1 requires parity for both "
                      "the 80x80 and the 128x128 grid)" % cand)
    if not maps:
        return fail("no --map given")
    dims = set()
    for p in maps:
        if not os.path.exists(p):
            return fail(f"map file not found: {p}")
        dims.add(check_map(p, results))

    # gate 2: both shipped dimensions must have been checked
    results.append(("dims-checked %s covers %s" % (sorted(dims), sorted(EXPECTED_DIMS)),
                    EXPECTED_DIMS.issubset(dims)))

    # gate 6: rules tables
    if args.rules:
        if not os.path.exists(args.rules):
            return fail(f"rules file not found: {args.rules}")
        r = sorules.load(args.rules)
        raw = sorules.json.load(open(args.rules, encoding="utf-8"))
        results.append(("rules-sections %s sections=%d records=%d empty=%s" % (
            os.path.basename(args.rules), len(r.counts), r.total_records, r.empty_sections),
            len(r.counts) == len(raw) and not r.empty_sections
            and all(r.counts[k] == len(raw[k]) for k in raw)))
    else:
        results.append(("rules-sections (no --rules given; B1 acceptance requires it)", False))

    bad = [n for n, ok in results if not ok]
    for name, ok in results:
        print(("  ok   " if ok else "  BAD  ") + name)
    if bad:
        return fail("B1: %d/%d gates failed: %s" % (len(bad), len(results), "; ".join(bad)))
    print("PASS B1: %d/%d gates on %s" % (len(results), len(results),
                                          ", ".join(os.path.basename(p) for p in maps)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
