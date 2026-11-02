"""sim.base - the 304-byte base record, decoded (BUILD_SPINE rung B4).

Every offset below is recorded evidence (docs/named-archive-m32-m84e.md, M46/M47/M51b/M52a/M52b
rows).  The whole record as 76 signed dwords is dumped by the live harness at
evidence/m46e_econ.json:16215; rung B4's gate re-reads that dump against these offsets, so the
map is checked against a recorded read and not against this file's own words.

  +4   owner byte        +6 pop byte        +7 growth countdown byte (ticked by 0x4f5a70)
  +19..+38 name, NUL-terminated printable  (sim.save.BASE_NAME_OFF, the shape the array scan uses)
  +0x40 mineral storage   (only writers: SPENDA 0x4efee0 and CLAMP 0x4eff23, M51b/M52a)
  +0x50 queued production item id (>=0 id, 0xffffffda empty, sentinel -39; M52b)
  +0x8c..+0x8f completed-facility bitmap: byte item>>3, bit 1<<(item&7)  (0x421fe0, M46)
  +0xc4 c4  +0xd4 d4  +0xe4 e4  +0xf4 f4    production totals (split by 0x4eaa10, M46)
  +0xfc GROSS energy bucket: the field the economy aggregator sums into the HUD Gross row
        (0x445900 -> 0x745734) and the field the income store adds to faction energy
        (0x4f5c8c `mov 0xfc(%ecx),%edx; add %edx,%eax`, M47)
  +0x100 +0x104 +0x108 the other three split buckets

No /proc, no gdb, no Wine: the bytes come from a .SAV (via sim.save) or from a recorded live read.
OPEN: only the four bytes at +0x8c are pinned by a recorded read, so ids 32..38 of the 39-row item
table cannot yet be set by this decoder (FAC_MAX below is the confirmed width, not the table width).
"""
import struct

from .save import BASE_LEN, BASE_NAME_OFF

ITEM_COUNT = 39              # runtime item table = 39 rows x 0x30 B (m32-m84e.md:270)
FAC_MAX = 32                 # confirmed bitmap width (the recorded read is the dword at +0x8c)
OWNER, POP, GROWTH = 4, 6, 7
NAME_OFF, NAME_LEN = BASE_NAME_OFF, 32   # NUL-terminated inside 32 B: names run to 22 chars
                                         # ("Morgan Energy Monopoly", "U.N. Court of Justice")
STORAGE, QUEUE, FAC_BYTES = 0x40, 0x50, 0x8C
DOFFS = {"c4": 0xC4, "d4": 0xD4, "e4": 0xE4, "f4": 0xF4,
         "gross": 0xFC, "b100": 0x100, "b104": 0x104, "b108": 0x108}


class BaseError(Exception):
    pass


def _i32(b, off):
    return struct.unpack_from("<i", b, off)[0]


def facilities(rec):
    """Completed facility ids from the +0x8c bitmap (0x421fe0's own addressing form)."""
    return [by * 8 + bit
            for by in range(4)
            for bit in range(8)
            if rec[FAC_BYTES + by] >> bit & 1]


def decode(data, off, i=None):
    """Decode one 304-B base record at `off` in `data`."""
    rec = data[off:off + BASE_LEN]
    if len(rec) != BASE_LEN:
        raise BaseError("record at %d is %d B, need %d" % (off, len(rec), BASE_LEN))
    d = {"i": i, "off": off, "owner": rec[OWNER], "pop": rec[POP], "growth": rec[GROWTH],
         "name": rec[NAME_OFF:NAME_OFF + NAME_LEN].split(b"\0")[0].decode("latin-1"),
         "storage": _i32(rec, STORAGE), "queue": _i32(rec, QUEUE),
         "facilities": facilities(rec)}
    d.update({k: _i32(rec, o) for k, o in DOFFS.items()})
    return d


def decode_dwords(words):
    """The same record in the shape the live harness records it: 76 signed dwords."""
    if len(words) != BASE_LEN // 4:
        raise BaseError("record is %d dwords, need %d" % (len(words), BASE_LEN // 4))
    return decode(struct.pack("<%di" % len(words), *words), 0)


def from_save(save):
    """Every base record of a loaded save (sim.save locates the array by shape, B2)."""
    return [decode(save.data, save.bases_off + BASE_LEN * i, i) for i in range(save.n_bases)]


def gross(rec):
    """The per-round energy income of one base: base+0xfc (M47 income store)."""
    return rec["gross"]
