"""sim.savewriter - rung B8: write a .SAV-shaped image back from the sim state model.

BUILD_SPINE.md rung B8 (R2's save leg). Every layout constant is RECOMPUTED here (imported
from sim.save, applied independently): prefix 12 | state header 796 | own player 4 | block A
67,040 | block B 11,488 | small 32 | map-header struct 2,724 | grid W*H*22 | coarse region map
| 16,000 section | u32 count + count bytes | 3,584+26,624+4,096 | units 52n | bases 304m |
tail-to-EOF. A byte is either MODELED - composed from the state model: version word, record
counts, year@84, cur_player@800 (0x985DCC through the M242 block identity), turn_flags@60 bit 1
(the remaining bits are declared pass-through), own player@808, map dims inside the 2,724-B
struct, and each unit record's x/y - or a DECLARED PASS-THROUGH (blocks A/B, the small table,
the 16,000 section, the middles, the tail incl. the M-format trailer, the grid, the region map,
and the un-modeled bytes inside modeled records).

The rung's acceptance (sim.selftest --b8) arbitrates the two classes on the real bytes:
identity round-trip, the repo's own decoder re-reading the written image, mutation diffs that
land only in modeled spans at model values, and two rival writers that FAIL the same fit.
NO /proc, NO gdb, NO Wine.
"""
import argparse
import hashlib
import os
import struct
import sys

from . import save as so

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Modeled header fields, file offsets (M242: value at file 12 + (addr - 0x985ab8);
# addresses from scripts/smac_state.py: cur_player 0x985DCC, turn_flags 0x985AE8,
# year 0x985B00; the counts are sim.save's own constants).
OFF_TF = so.mem2file(0x985AE8)
OFF_COUNTS = so.mem2file(so.G_UNITS)
OFF_YEAR = so.mem2file(so.G_YEAR)
OFF_CUR = so.mem2file(0x985DCC)
OWN_OFF = so.OWN_OFF

TF_MODEL_BIT = 2  # the engine owns only "end-turn in progress" in that dword

MODELED_SPANS = None  # built at first use


def _u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def modeled_spans():
    """Byte ranges the writer composes from the model (inside the header/own word)."""
    return [(OFF_TF, OFF_TF + 4), (OFF_COUNTS, OFF_COUNTS + 8), (OFF_YEAR, OFF_YEAR + 2),
            (OFF_CUR, OFF_CUR + 4), (OWN_OFF, OWN_OFF + 4),
            (so.MAP_HDR_OFF, so.MAP_HDR_OFF + 8)]


def build_image(sv, year=None, cur=None, tf=None, moves=None, unit_len=None,
                lift_all=False):
    """Recompose the container. Defaults are the model values read from the loaded image,
    so an unmutated build is the identity map iff every layout constant is right.
    lift_all=True builds the rival 'pure re-emitter' (composes regions, lifts every byte);
    unit_len= is the rival with a perturbed record stride."""
    d = sv.data
    ulen = so.UNIT_LEN if unit_len is None else unit_len
    n_units, n_bases = sv.n_units, sv.n_bases
    year = sv.year if year is None else year
    cur = _u32(d, OFF_CUR) if cur is None else cur
    tf = _u32(d, OFF_TF) if tf is None else tf
    out = bytearray()
    # prefix 12 B, composed from constants
    out += so.MAGIC + bytes([so.MARKER]) + struct.pack("<I", sv.version)
    # state header 796 B: pass-through body, modeled fields composed from the model
    hdr = bytearray(d[so.HDR_OFF:so.HDR_OFF + so.HDR_LEN])
    if not lift_all:
        struct.pack_into("<II", hdr, OFF_COUNTS - so.HDR_OFF, n_units, n_bases)
        struct.pack_into("<H", hdr, OFF_YEAR - so.HDR_OFF, year)
        struct.pack_into("<I", hdr, OFF_CUR - so.HDR_OFF, cur)
        old = _u32(bytes(hdr), OFF_TF - so.HDR_OFF)
        struct.pack_into("<I", hdr, OFF_TF - so.HDR_OFF,
                         (old & ~TF_MODEL_BIT) | (tf & TF_MODEL_BIT))
    out += hdr
    # own player
    out += (struct.pack("<I", sv.own_player) if not lift_all
            else d[OWN_OFF:OWN_OFF + 4])
    # block A / block B / small table / map-header struct (dims modeled)
    out += d[so.BLOCK_A_OFF:so.BLOCK_A_OFF + so.BLOCK_A_LEN]
    out += d[so.BLOCK_B_OFF:so.BLOCK_B_OFF + so.BLOCK_B_LEN]
    out += d[so.SMALL_OFF:so.SMALL_OFF + so.SMALL_LEN]
    mh = bytearray(d[so.MAP_HDR_OFF:so.MAP_HDR_OFF + so.MAP_HDR_LEN])
    if not lift_all:
        struct.pack_into("<II", mh, 0, sv.width, sv.height)
    out += mh
    # grid (read-only model), coarse region map, 16,000 section, count + bytes, middles
    out += d[sv.grid_off:sv.grid_off + sv.grid_len]
    out += d[sv.trailer_off:sv.trailer_off + sv.region_bytes]
    out += d[sv.sec_off:sv.sec_off + so.SEC16000_LEN]
    out += struct.pack("<I", sv.count_len) + d[sv.count_off + 4:sv.count_off + 4
                                               + sv.count_len]
    mid = 3584 + 26624 + 4096
    m0 = sv.count_off + 4 + sv.count_len
    out += d[m0:m0 + mid]
    # unit array: lift each record, patch the modeled x/y from the model (+ moves)
    uoff = sv.units_off
    for i in range(n_units):
        rec = bytearray(d[uoff + ulen * i:uoff + ulen * (i + 1)])
        if not lift_all:
            x, y = rec[0:2], rec[2:4]
            if moves and i in moves:
                x, y = struct.pack("<H", moves[i][0]), struct.pack("<H", moves[i][1])
            rec[0:4] = x + y
        out += rec
    # base array (pass-through bodies today), tail to EOF
    out += d[sv.bases_off:sv.bases_off + so.BASE_LEN * n_bases]
    out += d[sv.bases_off + so.BASE_LEN * n_bases:]
    return bytes(out)


def diff_offsets(a, b):
    return {i for i in range(max(len(a), len(b)))
            if (a[i] if i < len(a) else None) != (b[i] if i < len(b) else None)}


def modeled_diff_check(orig, mutated):
    """Every differing byte sits in a modeled span (header fields or a unit record's x/y)."""
    sv_spans = modeled_spans()
    bad = []
    for i in diff_offsets(orig, mutated):
        if not any(lo <= i < hi for lo, hi in sv_spans):
            bad.append(i)
    return bad


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sim.savewriter")
    ap.add_argument("--sav", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    sv = so.parse(a.sav)
    img = build_image(sv)
    with open(a.out, "wb") as fh:
        fh.write(img)
    print("wrote %s (%d B, sha256 %s, identical=%s)"
          % (a.out, len(img), hashlib.sha256(img).hexdigest()[:16], img == sv.data))
    return 0


if __name__ == "__main__":
    sys.exit(main())
