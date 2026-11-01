"""sim.map — the .MP tile grid as a state model (R1 rung B1).

Deliberately does NOT call scripts/decode_map.py: B1's acceptance is a parity check
between two independent decoders of the same bytes. The layout below is the one
established by the gdb read-trace recorded in MAP_FORMAT.md:

    0     15 B   b"TERRANMAP\\0" 0x1A u32 version(=5)
    15  2724 B   header struct, first two u32 = width, height
    2739 W*H*22  cell records, row-major
    +    var     trailer, starts b"????????"

Cell fields this module reads (MAP_FORMAT.md's cell table + the nibble split that
sim/selftest.py measures over BOTH shipped maps):

    +2 high nibble  terrain type index
    +2 low nibble   owner player index, 0xf = unowned (owner nibble pinned live by M43)
    +7 == 0xff      land cell (the count equals the header's land-cell word in both maps)

ASSUMED (open census pick): terrain-type cardinality is 16. The field is a nibble and
both shipped maps use every value 0..15; the exe's terrain-type table size has not been
pinned, so this is the smallest defensible bound, not a proven one.
"""

MAGIC = b"TERRANMAP\x00"
PREFIX_LEN = 15
TABLE_LEN = 2724
CELL_LEN = 22
TRAILER_LEN = 128
TRAILER_MARK = b"????????"

TERRAIN_BITS = 4
TERRAIN_CARDINALITY = 16          # ASSUMED, see module docstring
OWNER_MASK = 0x0F
OWNER_UNOWNED = 0x0F
LAND_MARK = 0xFF
HDR_LAND_WORD = 5                 # header u32 word 5 = land-cell count


class MapError(Exception):
    pass


class Map:
    """A parsed .MP grid: 22-byte cell records, row-major, width x height tiles."""

    def __init__(self, path, data):
        if not data.startswith(MAGIC):
            raise MapError(f"{path}: bad magic {data[:10]!r}")
        if data[10] != 0x1A:
            raise MapError(f"{path}: bad marker byte at 10: {data[10]:#04x}")
        self.path = path
        self.size = len(data)
        self._d = data
        self.version = int.from_bytes(data[11:15], "little")
        if self.version < 5:
            raise MapError(f"{path}: version {self.version} < 5")
        self.header = data[PREFIX_LEN:PREFIX_LEN + TABLE_LEN]
        if len(self.header) != TABLE_LEN:
            raise MapError(f"{path}: header only {len(self.header)} B")
        self.width, self.height = _u32(self.header, 0), _u32(self.header, 4)
        self.cells = self.width * self.height
        self.grid_off = PREFIX_LEN + TABLE_LEN
        self.grid_end = self.grid_off + self.cells * CELL_LEN
        if self.grid_end > self.size:
            raise MapError(
                f"{path}: file too short for {self.width}x{self.height} "
                f"({self.cells} cells x {CELL_LEN} B): {self.size} B")
        self.trailer = data[self.grid_end:]
        if not self.trailer.startswith(TRAILER_MARK):
            raise MapError(f"{path}: trailer not at {self.grid_end} "
                           f"(got {self.trailer[:8]!r})")
        if len(self.trailer) < TRAILER_LEN:
            raise MapError(f"{path}: trailer only {len(self.trailer)} B")
        if self.grid_end + len(self.trailer) != self.size:
            raise MapError(f"{path}: {self.grid_end}+{len(self.trailer)} != {self.size}")
        self.trailer_len = len(self.trailer)
        self.header_words = [_u32(self.header, 4 * i) for i in range(TABLE_LEN // 4)]

    # -- tile access -------------------------------------------------------
    def cell_index(self, x, y):
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise MapError(f"{self.path}: tile ({x},{y}) off grid "
                           f"{self.width}x{self.height}")
        return y * self.width + x

    def cell(self, x, y):
        o = self.grid_off + self.cell_index(x, y) * CELL_LEN
        return self._d[o:o + CELL_LEN]

    def terrain(self, x, y):
        return self.cell(x, y)[2] >> TERRAIN_BITS

    def owner(self, x, y):
        return self.cell(x, y)[2] & OWNER_MASK

    def is_land(self, x, y):
        return self.cell(x, y)[7] == LAND_MARK

    # -- whole-grid statistics (what the B1 gates measure) -----------------
    def stats(self):
        d, n = self._d, self.cells
        terrain = {}
        owner = {}
        cat = {}          # cell+0 >> 5 -> [cells, of-which-land]  (informational, gate-free)
        low5 = {}
        land = 0
        bad_terrain = 0
        bad_owner = 0
        for i in range(n):
            o = self.grid_off + i * CELL_LEN
            b2 = d[o + 2]
            t = b2 >> TERRAIN_BITS
            w = b2 & OWNER_MASK
            terrain[t] = terrain.get(t, 0) + 1
            owner[w] = owner.get(w, 0) + 1
            island = d[o + 7] == LAND_MARK
            k = d[o] >> 5
            r = cat.setdefault(k, [0, 0])
            r[0] += 1
            r[1] += island
            low5[d[o] & 0x1F] = low5.get(d[o] & 0x1F, 0) + 1
            if island:
                land += 1
            if t >= TERRAIN_CARDINALITY:
                bad_terrain += 1
            if not (w <= 7 or w == OWNER_UNOWNED):
                bad_owner += 1
        return {
            "cells": n,
            "terrain_used": sorted(terrain),
            "terrain_hist": terrain,
            "terrain_out_of_range": bad_terrain,
            "owner_hist": owner,
            "owner_invalid": bad_owner,
            "land_cells": land,
            "header_land_cells": self.header_words[HDR_LAND_WORD],
            "byte0_cat": {k: tuple(v) for k, v in sorted(cat.items())},
            "byte0_low5": sorted(low5),
        }


def _u32(b, off):
    return int.from_bytes(b[off:off + 4], "little")


def parse(path):
    """Parse a .MP file into a Map (raises MapError on any layout violation)."""
    with open(path, "rb") as f:
        return Map(path, f.read())
