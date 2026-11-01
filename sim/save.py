"""sim.save - load an SMAC .SAV into the sim state model (BUILD_SPINE rung B2).

No /proc, no gdb, no Wine: every byte here comes from the file. Offsets come from recorded
evidence (SAVE_FORMAT.md / NAMED.md: M242 - the 796-B state block at file 12 IS DAT_00985ab8
verbatim, so a live global's value sits at file 12 + (addr - 0x985ab8); M243 - DAT_00985af0 /
DAT_00985af4 are the unit and base counts) or from the per-file walk measured in
evidence/b2_save_walk.txt.

  prefix 12 | state header 796 | own player 4 | block A 67,040 = 8 x 8,380 | block B 11,488
  | small table 32 | map header struct 2,724 (u32 W, u32 H at +0/+4) | grid W*H*22
  | map trailer = the coarse region map, ((Rw+1)/2)*Rh bytes, Rw=(W+4)/5, Rh=(H+4)/5 (M244)
  | u32 count + count bytes (176 / 192 / 208 measured) | 3,584 | 26,624 | 4,096
  | units 52*n | bases 304*m | tail 10,800 = 256+152+10,144+20+216+8+4 = EOF (M244)

The two record arrays are located by SHAPE (coords inside the dims, a NUL-terminated printable
name at base+19), never by the counts; the header counts are then compared with what the scan
found - that comparison is the rung's acceptance. The grid is addressed as 44-B terrain records
(M240) at ((W//2)*y + (x>>1))*44 + (x&1)*22, which is byte-identical to the 22-B cell view.
"""
import re
import struct

MAGIC = b"TERRAN\x00"
MARKER = 0x1A
VERSION = 86

DAT_STATE = 0x985AB8
HDR_OFF, HDR_LEN = 12, 796
G_UNITS = 0x985AF0          # u32 unit-record count
G_BASES = 0x985AF4          # u32 base-record count
G_YEAR = 0x985B00           # u16 mission year
G_FEAT = 0x985AE8           # u32 feature bits (M243 gate family 3 tests & 0x10)
G_FACTION_MASK = 0x985B11   # byte: one bit per faction in the game (0xff = 8)
G_HUMAN_MASK = 0x985B10     # byte: which factions a human drives

OWN_OFF = 808               # u32 own player, DAT_0091b5b4
BLOCK_A_OFF, BLOCK_A_LEN, BLOCK_A_REC = 812, 67040, 8380
BLOCK_B_OFF, BLOCK_B_LEN = 67852, 11488
SMALL_OFF, SMALL_LEN = 79340, 32
MAP_HDR_OFF, MAP_HDR_LEN = 79372, 2724
CELL_LEN, REC_LEN = 22, 44
# The map trailer IS the coarse region map FUN_00582000 allocates: DAT_0092ada4 =
# ((DAT_0092ad9c + 1)/2) * DAT_0092ada0 with DAT_0092ad9c = (W+4)/5 and DAT_0092ada0 =
# (H+4)/5 (shard_014.c:27263-27265). M244: this closes planet.MP (80x80 -> 128) and
# planetx.MP (128x128 -> 338) on the byte and puts the count u32 at 188,299 on all 17
# 64x64 saves (91). No table needed.
def region_len(w, h):
    return (((w + 4) // 5 + 1) // 2) * ((h + 4) // 5)
SEC16000_LEN = 16000
MIDDLE_SECTIONS = 3584 + 26624 + 4096
UNIT_LEN, BASE_LEN = 52, 304
UNIT_TYPE_BAND = 64         # +10 >= 64: production-queue band record, not a unit (OPEN)
BASE_NAME_OFF = 19
TAIL_LEN = 256 + 152 + 10144 + 28 + 220   # 10,800, measured constant on 14 saves


class SaveError(Exception):
    pass


def mem2file(addr):
    return addr - DAT_STATE + HDR_OFF


def _u32(b, off):
    return struct.unpack_from("<I", b, off)[0]


def _u16(b, off):
    return struct.unpack_from("<H", b, off)[0]


def _unit_ok(d, o, w, h):
    """A 52-B record is shape-valid if its owner byte is a faction id and - for a record whose
    +10 type is < 64, i.e. a unit rather than one of the production-queue bands (trap 14 names
    128/194/322/323) - its +0/+2 pair is inside the map. Band records' +0/+2 are not tile
    coords (m113map.SAV has 3076/56832 in one), so they are not coord-checked."""
    if o < 0 or o + UNIT_LEN > len(d):
        return False
    if d[o + 14] >= 24:
        return False
    if _u16(d, o + 10) < UNIT_TYPE_BAND:
        x, y = struct.unpack_from("<HH", d, o)
        return x < w and y < h
    return True


def _base_ok(d, o, w, h):
    if o < 0 or o + BASE_LEN > len(d):
        return False
    x, y = struct.unpack_from("<HH", d, o)
    if not (x < w and y < h):
        return False
    return bool(re.match(rb"[ -~]{3,30}\x00", d[o + BASE_NAME_OFF:o + BASE_NAME_OFF + 32]))


def _locate_bases(d, w, h):
    """First offset starting a run of 3 shape-valid 304-B records, widened both ways."""
    start = None
    for o in range(MAP_HDR_OFF, len(d) - 3 * BASE_LEN):
        if _base_ok(d, o, w, h) and _base_ok(d, o + BASE_LEN, w, h) \
           and _base_ok(d, o + 2 * BASE_LEN, w, h):
            start = o
            break
    if start is None:
        raise SaveError("no 304-B base array (shape scan found nothing)")
    bs = start
    while _base_ok(d, bs - BASE_LEN, w, h):
        bs -= BASE_LEN
    m = 0
    while _base_ok(d, bs + BASE_LEN * m, w, h):
        m += 1
    return bs, m


class Save:
    def __init__(self, path, data):
        if not data.startswith(MAGIC):
            raise SaveError("%s: not a save (magic %r)" % (path, data[:6]))
        if data[7] != MARKER:
            raise SaveError("%s: marker %#x != 0x1a" % (path, data[7]))
        self.path = path
        self.data = data
        self.size = len(data)
        self.version = _u32(data, 8)
        if self.version < VERSION:
            raise SaveError("%s: version %d < %d" % (path, self.version, VERSION))
        self.header = data[HDR_OFF:HDR_OFF + HDR_LEN]
        if len(self.header) != HDR_LEN:
            raise SaveError("%s: state header only %d B" % (path, len(self.header)))
        self.year = _u16(data, mem2file(G_YEAR))
        self.n_units = _u32(data, mem2file(G_UNITS))
        self.n_bases = _u32(data, mem2file(G_BASES))
        self.feature_bits = _u32(data, mem2file(G_FEAT))
        self.own_player = _u32(data, OWN_OFF)
        self.human_mask = data[mem2file(G_HUMAN_MASK)]
        self.faction_mask = data[mem2file(G_FACTION_MASK)]
        self.faction_slots = BLOCK_A_LEN // BLOCK_A_REC
        self.mask_factions = bin(self.faction_mask).count("1")

        self.width, self.height = _u32(data, MAP_HDR_OFF), _u32(data, MAP_HDR_OFF + 4)
        dims = (self.width, self.height)
        self.region_bytes = region_len(*dims)
        if self.region_bytes <= 0:
            raise SaveError("%s: region map length %d at %dx%d" % (path, self.region_bytes,
                                                                   *dims))
        self.grid_off = MAP_HDR_OFF + MAP_HDR_LEN
        self.grid_len = self.width * self.height * CELL_LEN
        self.trailer_off = self.grid_off + self.grid_len
        self.sec_off = self.trailer_off + self.region_bytes
        self.count_off = self.sec_off + SEC16000_LEN
        if self.count_off + 4 > self.size:
            raise SaveError("%s: count prefix at %d runs past EOF (%d)" % (path, self.count_off,
                                                                           self.size))
        self.count_len = _u32(data, self.count_off)        # DAT_00927538, 176/192/208 measured
        self.units_pred = self.count_off + 4 + self.count_len + MIDDLE_SECTIONS
        self.bases_pred = self.units_pred + UNIT_LEN * self.n_units
        self.tail_pred = self.bases_pred + BASE_LEN * self.n_bases

        self.bases_off, self.found_bases = _locate_bases(data, self.width, self.height)
        self.units_off = self.bases_off - UNIT_LEN * self.n_units
        self.found_units = 0
        while _unit_ok(data, self.bases_off - UNIT_LEN * (self.found_units + 1),
                       self.width, self.height):
            self.found_units += 1
        self.units = [self.unit(i) for i in range(self.n_units)]
        self.bases = [self.base(i) for i in range(self.n_bases)]
        self.tail_off = self.bases_off + BASE_LEN * self.n_bases
        self.tail_len = self.size - self.tail_off
        self.closes = (self.units_pred == self.units_off and self.bases_pred == self.bases_off
                       and self.tail_off + TAIL_LEN == self.size and self.tail_len == TAIL_LEN)
        owners = {u["owner"] for u in self.units} | {b["fac"] for b in self.bases}
        self.owner_ids = sorted(owners)
        self.faction_count = self.mask_factions

    def unit(self, i):
        o = self.units_off + UNIT_LEN * i
        d = self.data
        return {"i": i, "off": o, "x": _u16(d, o), "y": _u16(d, o + 2),
                "flag": _u32(d, o + 4), "type": _u16(d, o + 10), "owner": d[o + 14]}

    def base(self, i):
        o = self.bases_off + BASE_LEN * i
        d = self.data
        raw = d[o + BASE_NAME_OFF:o + BASE_NAME_OFF + 32].split(b"\0")[0]
        return {"i": i, "off": o, "x": _u16(d, o), "y": _u16(d, o + 2),
                "own4": d[o + 4], "fac": d[o + 5],
                "name": raw.decode("latin-1")}

    def tile(self, x, y):
        """The (x,y) terrain record: 44-B-record view (M240), 22 B per column."""
        rec = (self.width // 2) * y + (x >> 1)
        off = self.grid_off + REC_LEN * rec + (x & 1) * CELL_LEN
        return self.data[off:off + CELL_LEN]


def parse(path):
    with open(path, "rb") as fh:
        return Save(path, fh.read())
