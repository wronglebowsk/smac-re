#!/usr/bin/env python3
"""Reconstruct FUN_004e78e0's rebuild of base+0xbc/0xc0/0xc4/0xc8 in Python.

    python3 scripts/m53o_recon.py            # the 7 pinned candidate bases
    python3 scripts/m53o_recon.py 70 4 10    # specific idxs
    python3 scripts/m53o_recon.py --stale-mask  # superseded model (entry mask = the dump's
                                               # global DAT_008f0d30; M53q computes it per base)
    python3 scripts/m53o_recon.py -v 70      # per-scan / per-term detail

Read-only: consumes evidence/m53o_mem/*.bin written by scripts/m53o_mem.py.
"""
import argparse
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MDIR = os.path.join(ROOT, "evidence", "m53o_mem")

# ---------------------------------------------------------------- live snapshot
BLOB_BASE = {"terrain": 0x40a6ba8, "bases": 0x95da10, "facrec": 0x94d400, "g926": 0x926b00,
             "g92a": 0x92a200, "g91c": 0x91c600, "g985": 0x985a00, "g8f0": 0x8f0c00,
             "offs": 0x678400, "tech": 0x92fd00, "units": 0x933200}
_blob = {}
_rows = {}


def load():
    for n, b in BLOB_BASE.items():
        with open(os.path.join(MDIR, n + ".bin"), "rb") as f:
            _blob[n] = (b, f.read())
    with open(os.path.join(MDIR, "rows.json")) as f:
        d = json.load(f)
    _rows["g"] = d["globals"]
    _rows["r"] = {r["idx"]: r for r in d["rows"]}


def blob_at(name, addr, n):
    b, data = _blob[name]
    off = addr - b
    return data[off:off + n]


def u8(name, addr):
    return blob_at(name, addr, 1)[0]


def u16s(name, addr):
    return struct.unpack_from("<h", blob_at(name, addr, 2), 0)[0]


def u32(name, addr):
    return struct.unpack_from("<I", blob_at(name, addr, 4), 0)[0]


def s32v(name, addr):
    return struct.unpack_from("<i", blob_at(name, addr, 4), 0)[0]


# ---------------------------------------------------------------- int helpers
def s32(v):
    v &= 0xFFFFFFFF
    return v - 0x100000000 if v >= 0x80000000 else v


def sdiv(a, b):
    """C signed division: truncate toward zero."""
    a, b = s32(a), s32(b)
    if b == 0:
        return 0
    q = abs(a) // abs(b)
    return q if (a < 0) == (b < 0) else -q


def clamp99(v):
    v = s32(v)
    return 1 if v < 1 else (99 if v > 99 else v)


def nibble(arr2, i):
    """16-nibble array: arr2 = [dword0, dword1] at base+0x84."""
    return (arr2[i >> 3] >> ((i & 7) * 4)) & 0xF


# ---------------------------------------------------------------- game state
G = {}          # globals cache, filled by init()
XOFF = YOFF = None
CONST = {}      # 0x926bd8..0x926c6c resource table (nutrient,mineral,energy,unused)


def init():
    load()
    g = _rows["g"]
    G.update({k: s32(v) for k, v in g.items()})
    ob = BLOB_BASE["offs"]
    offs = _blob["offs"][1]

    def tbl(addr, n):
        return list(struct.unpack_from("<%di" % n, offs, addr - ob))
    global XOFF, YOFF
    XOFF = tbl(0x67850c, 80)
    YOFF = tbl(0x678990, 80)
    for a in range(0x926bd8, 0x926c6c, 4):
        CONST[a] = s32v("g926", a)
    return g


def row(i):
    return _rows["r"][i]


# terrain record -------------------------------------------------------------
def tile_idx(x, y):
    return 40 * y + ashr(x, 1)


def ashr(v, n):
    return s32(v) >> n


def terr(t):
    d = blob_at("terrain", BLOB_BASE["terrain"] + t * 0x2c, 0x2c)
    return {"b": d, "cat": d[0] & 0xE0, "raw0": d[0], "lvl": d[2] & 0xF, "b5": d[5],
            "b7": struct.unpack_from("<b", d, 7)[0], "u9": struct.unpack_from("<I", d, 8)[0],
            "uc": struct.unpack_from("<I", d, 0xC)[0]}


# facility bitmap at base+0x8c (40 bits) -------------------------------------
def fac_bit(bidx, bit):
    d = blob_at("bases", BLOB_BASE["bases"] + bidx * 0x130 + 0x8c + (bit >> 3), 1)[0]
    return (d & (1 << (bit & 7))) != 0


def base_dword(bidx, off):
    return struct.unpack_from("<I", blob_at("bases", BLOB_BASE["bases"] + bidx * 0x130 + off, 4), 0)[0]


def base_short(bidx, off):
    return struct.unpack_from("<h", blob_at("bases", BLOB_BASE["bases"] + bidx * 0x130 + off, 2), 0)[0]


# tech availability, FUN_005a6cd0 -------------------------------------------
def tech_avail(tid, fac):
    if fac <= 0:
        return False
    if tid == -1:
        return True
    if not (-1 < tid < 0x58):
        return False
    d0 = s32v("tech", 0x92fdd4 + tid * 0x2c)
    d1 = s32v("tech", 0x92fdd8 + tid * 0x2c)
    if not (-2 < d0 and (-2 < d1 or d0 == -1)):
        return False
    return (u8("g985", 0x985c1c + tid) & (1 << (fac & 0x1F))) != 0


# per-faction record field --------------------------------------------------
def frec(off, fac):
    return s32v("facrec", off + fac * 0x20BC)


# ---------------------------------------------------------------- FUN_005831a0
def code5831a0(x, y):
    t = tile_idx(x, y)
    r = terr(t)
    u1 = r["u9"]
    b2 = r["raw0"] >> 5
    wind = G["wind"]
    if (u1 & 0x400) == 0:
        if wind == 0:
            return 0
        if b2 > 2 and (G["k85ac4"] & 0x2000) == 0:
            return 0
    u4 = ashr(y + x, 1)
    u5 = s32(x - u4)
    u4 = (u4 & 3) + (u5 & 3) * 4
    if (u1 & 0x400) == 0:
        v = ashr(y + x, 3) * -5 + ashr(u5, 2) * -3 + wind
        if u4 != (v & 0xF):
            return 0
    if b2 < 2:
        return 0
    if b2 < 3:
        u4 = u4 % 3 + 1
    else:
        u4 = u4 % 5 & 3
    if u4 == 0 or (u1 & 0x20000000):
        if u1 & 0x10000:
            return 3
        u4 = (1 if (u1 & 0x20000) else 0) + 1
    return u4


# ---------------------------------------------------------------- yield fns
def fac_bits(bidx):
    d = blob_at("bases", BLOB_BASE["bases"] + bidx * 0x130 + 0x8c, 5)
    bm = int.from_bytes(d, "little")
    return {b: (bm >> b) & 1 for b in range(40)}


def improved(fac, field):
    """(rec.u9 & 0x20) special-square table path; field selects 0x94d744/48/4c."""
    v = u32("facrec", 0x94D698 + fac * 0x20BC)
    if s32(v) < -3:
        v = 0xFFFFFFFD
    else:
        v = v & ((0 < s32(v)) - 1) & 0xFFFFFFFF
    v = s32(frec(0x94D744 + field * 4, fac) + s32(v))   # C clamps to 0..99 here, not 1..99
    return 0 if v < 0 else (99 if v > 99 else v)


def cc8(n):
    G["cc8_delta"] = G.get("cc8_delta", 0) + n


def y0(fac, bidx, x, y, extra, fb=None):
    """FUN_004e6960 -> field 0 (nutrient column of the 0x926bd8 table)."""
    r = terr(tile_idx(x, y))
    if fb is None:
        fb = fac_bits(bidx)
    p3, land, C = r["u9"], r["cat"] < 0x60, CONST
    b8 = code5831a0(x, y) == 1
    uc = r["uc"]
    bonus = 1 if (((uc & 0x80000004) == 4 and r["cat"] > 0x5F) or ((uc & 0x80) and land)) else 0
    b5c = r["b5"] >> 6
    if (r["b"][8] & 1) == 0 or r["lvl"] > 7:
        if (p3 & 0x1000000) == 0:
            if (p3 & 0x2000) == 0:
                if (p3 & 0x20) == 0 or extra != 0 or r["cat"] < 0x40:
                    if not land:
                        if (p3 & 0x200000) == 0:
                            v = (r["raw0"] & 0x18) >> 3
                            if b5c > 1:
                                v = 0
                            if b8:
                                v += C[0x926BF8]
                            if bonus:
                                v += 1
                            if s32(v) < 0:
                                v = 0
                            if (p3 & 0x8000) and b5c < 2:
                                v += C[0x926C28]
                            if (p3 & 0x10) and s32(v) > 1:
                                v += G["k2a0"]
                        else:
                            v = ((-(1 if b8 else 0) & 0xFFFFFFFF) & C[0x926BF8]) + C[0x926C08]
                            if bidx > -1:
                                if fb[0xE]:
                                    v += 1
                                if fb[0xD]:
                                    v += 1
                            if bonus:
                                v += 1
                    else:
                        v = C[0x926BD8]
                        if b8:
                            v = C[0x926BD8] + C[0x926BF8]
                        if bonus:
                            v += 1
                        if r["cat"] == 0x40:
                            if p3 & 0x8000:
                                v += C[0x926C38]
                            if (p3 & 0x10) and s32(v) > 1:
                                v += G["k2a0"]
                    if p3 & 0x80000:
                        v = s32(v) + sdiv(v, 2)
                    u4 = p3 & 0x400000
                    if u4:
                        v = s32(v) + sdiv(v, 2)
                    if s32(v) > 2 and not tech_avail(G["t_cap0"], fac) and not b8 and u4 == 0:
                        cc8(s32(v) - 2)
                        v = 2
                else:
                    v = improved(fac, 0)
            else:
                v = C[0x926C48]
                if b8:
                    v = C[0x926C48] + C[0x926BF8]
        else:
            v = C[0x926C58]
            if C[0x926C58] != 0:
                v = C[0x926C58] + C[0x926BF8]
    else:
        v = C[0x926BE8]
        if b8:
            v = C[0x926BE8] * 2
        if bonus:
            v += 1
        if bidx < 0:
            return s32(v)
        if not (fb[3] or fb[0x1A]):
            pass
        else:
            v += C[0x926C18]
    if bidx > -1:
        d = base_dword(bidx, 0x34)
        if d & 0x200:
            v += 1
        if (d & 0x400) and v != 0:
            v -= 1
    return s32(v)


def y1(fac, bidx, x, y, extra, fb=None):
    """FUN_004e6d40 -> field 1 (mineral column)."""
    r = terr(tile_idx(x, y))
    if fb is None:
        fb = fac_bits(bidx)
    C = CONST
    uc, elev, p4 = r["uc"], ashr(r["uc"], 0x18), r["u9"]
    b9 = code5831a0(x, y) == 2
    d1 = ((uc & 0x80000002) == 2 and elev < 9) or ((uc & 0x80000001) == 1 and elev < 9)
    bonus = 1 if (d1 or (uc & 0x80000200) == 0x200) else 0
    v = (-(1 if b9 else 0) & 0xFFFFFFFF) & C[0x926BFC]
    v = s32(v + bonus)

    def tail1(v):
        if bidx > -1:
            d = base_dword(bidx, 0x34)
            if d & 0x800:
                v += 1
            if (d & 0x1000) and v != 0:
                v -= 1
        return s32(v)

    def cap1(v):
        if s32(v) > 2 and not tech_avail(G["t_cap1"], fac) and not b9:
            cc8(s32(v) - 2)
            v = 2
        return tail1(v)

    if (r["b"][8] & 1) and r["lvl"] < 8:
        v += C[0x926BEC]
        if bidx < 0:
            return s32(v)
        if fb[3] or fb[0x1A]:
            v += C[0x926C1C]
        return tail1(v)
    if p4 & 0x2000:
        v = C[0x926C4C] + (C[0x926BFC] if b9 else 0)
        return tail1(v)
    if (p4 & 0x1000000) == 0:
        if (p4 & 0x20) and r["cat"] > 0x3F:
            return tail1(improved(fac, 1))
        if r["cat"] < 0x60:
            v += C[0x926BDC]
            if r["cat"] == 0x40 and ((p4 & 0x10) or extra):
                v += C[0x926C3C]
                if tech_avail(G["t_imps"], fac):
                    v += 1
        else:
            u4 = r["b5"] >> 6
            u5 = C[0x926C0C]
            if (p4 & 0x200000) == 0:
                if (p4 & 0x1000010) == 0 and extra == 0:
                    if u4:
                        v += 1
                    return cap1(v)
                v += u4
                if u4 == 0:
                    u4 = 1
                if b9 or bonus:
                    u4 += 1
                u5 = u4
                if (p4 & 4) == 0 and extra == 0 and G["k29c"] < s32(u4):
                    cc8(s32(u4 - G["k29c"]))
                    u5 = G["k29c"]
            v += u5
    else:
        v = C[0x926C5C] + (C[0x926BFC] if b9 else 0)
    return cap1(v)


def y2(fac, bidx, x, y, extra, fb=None):
    """FUN_004e7070 -> field 2 (energy column)."""
    r = terr(tile_idx(x, y))
    if fb is None:
        fb = fac_bits(bidx)
    C = CONST
    u9, uc, land = r["u9"], r["uc"], r["cat"] < 0x60
    i10 = s32v("terrain", BLOB_BASE["terrain"] + tile_idx(x, y) * 0x2c + 0xC)
    u6 = -1 if ((r["b"][8] & 1) == 0 or r["lvl"] > 7) else r["lvl"]
    z = code5831a0(x, y)
    b3 = bool(((uc & 0x80000002) == 2 and ashr(i10, 0x18) < 9) or (uc & 0x80000008) == 8
              or (uc & 0x80000400) == 0x400 or (uc & 0x80000800) == 0x800)

    def fin(v):
        """LAB_004e7586 final block."""
        if bidx > -1:
            d = base_dword(bidx, 0x34)
            if d & 0x2000:
                v += 1
            if (d & 0x4000) and v != 0:
                v -= 1
        if G["k85db8"] and v != 0:
            v -= 1
        sel = (G["k85dc4"] & 1) if G["g91c628"] == 0 else (G["k85dc4"] & 2)
        return s32(v * 3 if sel else v)

    def tail(v):
        if (u9 & 0x80) and not land:
            v += 1
        if z == 3:
            v += C[0x926C00]
        if b3:
            v += 1
        if bidx < 0:
            i = 0
        else:
            if G["k85b48"] == bidx:
                v += 1
            i = 1 if (base_dword(bidx, 0x30) & 4) else 0
        if frec(0x94D67C, fac) + i > 1:
            v += 1
        if u6 < 0:
            if s32(v) > 2 and not tech_avail(G["t_cap2"], fac) and z != 3:
                cc8(s32(v) - 2)
                v = 2
        else:
            if s32(v) < 0:
                v = 0
                G["c44_w"] = 0
            else:
                G["c44_w"] = v
                if s32(v) > 99:
                    v = 99
                    G["c44_w"] = 99
        return fin(v)

    if u6 < 0:
        if (u9 & 0x2000) == 0:
            if (u9 & 0x1000000) == 0:
                if (u9 & 0x20) and r["cat"] > 0x3F:
                    return fin(improved(fac, 2))
                if land:
                    v = C[0x926BE0]
                    if r["cat"] == 0x40 and ((u9 & 0x40) or extra):
                        v = C[0x926BE0] + C[0x926C40]
                    if u9 & 0x200000:
                        v -= 1
                elif (u9 & 0x200000) == 0:
                    u8v = (r["raw0"] >> 5) - 2
                    if (u9 & 0x1800040) != 0 or extra != 0:
                        v = s32(u8v & ((s32(u8v) < 0) - 1))
                    else:
                        v = 0
                    if u9 & 0x40:
                        for k in range(8):
                            nx = s32(x + struct.unpack_from("<i", _blob["offs"][1], 0x6784a0 - BLOB_BASE["offs"] + k * 4)[0])
                            if (G["wrap"] & 1) == 0:
                                if nx < 0:
                                    nx += G["map_w"]
                                elif nx >= G["map_w"]:
                                    nx -= G["map_w"]
                            ny = s32(y + struct.unpack_from("<i", _blob["offs"][1], 0x6784c4 - BLOB_BASE["offs"] + k * 4)[0])
                            if -1 < ny < G["map_h"] and -1 < nx < G["map_w"]:
                                rr = terr(tile_idx(nx, ny))
                                if (rr["u9"] & 0x800000) and rr["b7"] == fac:
                                    v += 1
                else:
                    v = C[0x926C10]
                    if bidx > -1 and fb[0xE]:
                        v = C[0x926C10] + 1
            else:
                v = C[0x926C60]
        else:
            v = C[0x926C50]
    else:
        loc = C[0x926BF0] + (1 if fb[1] else 0)
        if bidx < 0:
            i5 = 0
        else:
            if fb[3] or fb[0x1A]:
                loc = s32(loc + C[0x926C20])
            i5 = 1 if (base_dword(bidx, 0x30) & 4) else 0
            i5 = frec(0x94D67C, fac) + i5
            if i5 < 0:
                if (not fb[1]) or i5 < -1 or frec(0x94E488, fac) == 1:
                    i5 += 1
            elif i5 > 1:
                if i5 > 4:
                    i5 = 4
                i5 = i5 * 2 - 4
            loc = s32(loc + i5)
            if G["k85bc0"] == fac:
                loc += 1
        return tail(loc)
    return tail(v)


def disp(field, fac, bidx, x, y, fb=None):
    if field == 0:
        return y0(fac, bidx, x, y, 0, fb)
    if field == 1:
        return y1(fac, bidx, x, y, 0, fb)
    if field == 2:
        return y2(fac, bidx, x, y, 0, fb)
    return 0


# ---------------------------------------------------------------- list / chooser
def entry_dword(i, j):
    """entry i (stride 28 B from 0x926cb4), dword j."""
    return struct.unpack_from("<i", _blob["g926"][1], 0x926cb4 - BLOB_BASE["g926"] + i * 28 + j * 4)[0]


def chooser(idx):
    """FUN_004e3c80: argmax over the 7-entry list at 0x926cb4."""
    R = row(idx)
    fac, pop = R["fac"], R["pop"]
    best, arg, n = -999, 0, 0
    for i in range(7):
        tech = entry_dword(i - 1, 4) if i else s32v("g926", 0x926ca8)
        if not tech_avail(tech, fac):
            continue
        sc = entry_dword(i, 0) * 3
        if G["k2a4"] <= pop:
            sc += entry_dword(i - 1, 6) + entry_dword(i, 1)
        if sc > best:
            best, arg = sc, n
        n += 1
    return arg


def popcount(v):
    return bin(v & 0xFFFFFFFF).count("1")


def wrap_x(x):
    """asm:186-194 (0x4e7b51-0x4e7b62, scan loop), asm:375-383 (0x4e7deb-0x4e7dfc, scan-0
    special), asm:554-562 (0x4e803d-0x4e804d, middle-pass candidate loop), asm:939-947
    (0x4e8504-0x4e8515, add-best-gain) and asm:1045-1055/1119-1129/1210-1218/1282-1292
    (the four swap/undo blocks): every tile address is computed as
    `if ((DAT_0092a394 & 1) == 0) { if (x < 0) x += DAT_0092a378; else if (x >=
    DAT_0092a378) x -= DAT_0092a378; }` -- the x coordinate IS folded into the map when
    the wrap flag bit is CLEAR (live DAT_0092a394 = 0), and y is never folded.  The M53o
    model never folded, so every base within one spiral radius of the east/west map edge
    lost the wrapped tiles the game actually scanned."""
    if (G["wrap"] & 1) == 0:
        if x < 0:
            x += G["map_w"]
        elif x >= G["map_w"]:
            x -= G["map_w"]
    return x


# ---------------------------------------------------------------- FUN_004e63b0
# The per-visit scan-pool builder.  Reads *(0x8f0d60) (no args passed at the call
# site 0x4e78e9); writes the 21-dword table 0x8f0ccc..0x8f0d1c and then, still
# inside itself (ret 0x4e6959), DAT_008f0d30 = {bit i : table[i] != 0} (0x4e6925-
# 0x4e694f).  Every predicate below is transcribed from evidence/m53j_text.txt.gz
# lines 298136-298619 (asm VAs in comments); see evidence/m53q_findings.md.
UNIT_BASE = 0x933278          # unit array, stride 52 (live count DAT_00985af0)


def unit(i):
    d = blob_at("units", UNIT_BASE + 52 * i, 52)
    return {"x": struct.unpack_from("<h", d, 0)[0], "y": struct.unpack_from("<h", d, 2)[0],
            "typ": d[4], "fac": struct.unpack_from("<b", d, 14)[0], "order": d[17],
            "w18": struct.unpack_from("<H", d, 24)[0], "b25": d[25],
            "l48": struct.unpack_from("<h", d, 48)[0], "l50": struct.unpack_from("<h", d, 50)[0]}


def unit_head(u):
    """Walk +50 prev-links to the stack head (asm 0x5ab223-37 / 0x5a5cad-bf, exit
    only on a NEGATIVE link; a self-link would spin -- guard with a step limit)."""
    seen = 0
    while seen < 4096:
        nxt = unit(u)["l50"]
        if nxt < 0:
            return u
        u, seen = nxt, seen + 1
    return u


def unit_at(x, y):
    """FUN_005ab130(x,y) -> FUN_005a5c00(u): the stack head of tile (x,y), or -1.
    Linear-scan path (asm 0x5ab17b-1a7: first record with +0==x and +2==y, then the
    +50 walk to the head; 0x5a5c00 re-derives the same head).  The tile-head path
    (tile mask dword +8 bit 1 -> read the record's list head) is equivalent while
    the occupancy bit is consistent; not modelled -- INFERRED-equivalent."""
    n = G["nunit"]
    for i in range(n):
        r = unit(i)
        if r["x"] == x and r["y"] == y:
            return unit_head(i)
    return -1


def hexdist(x0, y0, x1, y1):
    """asm 0x4e6733-0x4e6759: mx - (((manhattan>>1) - mn + 1) >> 1) over the WRAPPED
    deltas (wrap correction 0x4e6701-23 / 0x4e6834-56; DAT_00692184 = 40 half-width)."""
    dx = x0 - x1
    if (G["wrap"] & 1) == 0:
        ad = abs(dx)
        if ad > G["mapw_mult"]:
            dx = G["map_w"] - ad
    ax, ay = abs(dx), abs(y0 - y1)
    mx, mn = (ax, ay) if ax > ay else (ay, ax)
    return s32(mx - s32((s32((ax + ay) >> 1) - mn + 1) >> 1))


def relation(fac, other):
    """Stance byte DAT_0094d448 + fac*0x20bc + 4*other (0x4e6628 / 0x4e6675 test &3)."""
    return u8("facrec", 0x94D448 + fac * 0x20BC + 4 * other)


def _foreign_unit_flag(r, fac):
    """0x4e65d3-0x4e6635: a stack member of another faction that is NOT in the
    transport state (w18 & 0x440 == 0x440) AND whose +25 faction bit for US is
    CLEAR (0x4e660c `test [u+25],1<<fac / je skip` -- je fires when the bit IS set),
    combined with stance(fac, unit_fac) & 3 == 0 -> the |= 8 test."""
    vf = r["fac"]
    if vf < 0 or vf == fac:                            # 0x4e65e7-eb (unowned/ours: skip)
        return False
    if (r["w18"] & 0x440) == 0x440:                    # 0x4e65f1-0x4e6603: transport state
        return False                                   #   -> the +25 test is SKIPPED
    if (r["b25"] >> fac) & 1:                          # 0x4e660c: je -> skip when SET
        return False
    return relation(fac, vf) & 3 == 0                  # 0x4e6628


def build_table(idx, verbose=False):
    """FUN_004e63b0 for base idx -> (table[25], mask21).  table[21..24] are written
    by the dead 0x4e63e8 site (past the window the mask loop scans); mask21 models
    DAT_008f0d30.  Loop A = per-step reason codes; loop B/C = the 0x10 overlap OR."""
    R = row(idx)
    fac = R["fac"]
    bx, by = R["x"], R["y"]
    W, H, FLAT = G["map_w"], G["map_h"], (G["wrap"] & 1) != 0
    out = [0] * 25
    exempt = (frec(0x94D430, fac) & 0x200) != 0      # 0x4e64e8 test ah,0x2 on 0x94d430[fac]
    for s in range(21):
        tx = bx + XOFF[s]
        if not FLAT:                                  # 0x4e6407-23: fold x when wrap bit CLEAR
            if tx < 0:
                tx += W
            elif tx >= W:
                tx -= W
        ty = by + YOFF[s]
        if ty < 0 or ty >= H or tx < 0 or tx >= W:    # 0x4e6430-40
            out[s] = 2
            continue
        t = terr(tile_idx(tx, ty))
        m8 = t["u9"]                                  # record dword at +8 (terr's "u9")
        lvl = t["b"][2] & 0xF                         # 0x4e6554-5d: 0 <= b2&0xf < 8
        if not (exempt or (t["b"][4] >> fac) & 1):    # 0x4e650f test BYTE[tile+4],1<<fac
            out[s] = 2
            continue
        out[s] = 0                                    # 0x4e6533
        if (m8 & 1) and 0 <= lvl < 8:
            out[s] = 4                                # 0x4e6563
        u = unit_at(tx, ty)                           # 0x4e656f-7f (5ab130 -> 5a5c00)
        if u >= 0:
            if unit(u)["order"] == 3:                 # 0x4e6590 5a6330(u,9,3,-1,-1) case 9
                out[s] |= 8                           # 0x4e659f
            v = u                                     # 0x4e65ac-: +48 walk to the chain end
            for _ in range(4096):
                nxt = unit(v)["l48"]
                if nxt < 0:
                    break
                v = nxt
            w = v                                     # 0x4e663c: esi CARRIES OVER -- the +50
            for _ in range(4096):                     # walk starts at the +48 terminus and
                r = unit(w)                           # covers every member of the stack
                if _foreign_unit_flag(r, fac):
                    out[s] |= 8                       # 0x4e6635
                if r["l50"] < 0:
                    break
                w = r["l50"]
            o = t["b7"]                               # 0x4e6651 FUN_004e3b50(fac,x,y,0,0)
            if o >= 0 and o != fac and relation(fac, o) & 3 == 0:   # 0x4e6659-75
                if u < 0 or unit(u)["fac"] == fac:    # 0x4e667f-94
                    out[s] |= 0x20                    # 0x4e6699
    for s in range(21, 25):                           # 0x4e63e8 (dead for 0..20)
        out[s] = 1
    # ---- loop B/C: another base's processed step overlapping our spiral -> |= 0x10
    nb = G["nbases"]
    for n in range(nb):
        if n == idx:                                  # 0x4e66db cmp DAT_0068cbb0
            continue
        b = row(n)
        if hexdist(bx, by, b["x"], b["y"]) > 5:       # 0x4e6759 cmp ecx,5
            continue
        bmask = b["d78"]
        for s in range(21):                           # 0x4e6778-0x4e68fe
            if s and not ((bmask >> s) & 1):          # 0x4e6783 test [b+0x78],1<<s
                continue
            tx = wrap_x(b["x"] + XOFF[s])
            ty = b["y"] + YOFF[s]
            if ty < 0 or ty >= H or tx < 0 or tx >= W:    # 0x4e67c7-0x4e67e6
                continue
            if b["fac"] != fac:                       # 0x4e67f7
                if (terr(tile_idx(tx, ty))["cat"] & 0xE0) < 0x60:   # 0x4e681b-20 ocean pass
                    continue
            if hexdist(bx, by, tx, ty) > 2:           # 0x4e688f cmp ecx,2
                continue
            for k in range(21):                       # 0x4e68a5-0x4e68ea step match
                if wrap_x(bx + XOFF[k]) == tx and by + YOFF[k] == ty:
                    out[k] |= 0x10                    # 0x4e68d6-de
    mask = 0
    for k in range(21):                               # 0x4e6925-0x4e694f
        if out[k] != 0:
            mask |= 1 << k
    return out, mask & 0xFFFFFFFF


# ---------------------------------------------------------------- FUN_004e78e0
def rebuild(idx, stale_mask=False, verbose=False, pop_visit=None):
    R = row(idx)
    fac, pop, bx, by = R["fac"], (R["pop"] if pop_visit is None else pop_visit), R["x"], R["y"]
    G["cc8_delta"] = 0
    fb = fac_bits(idx)
    trace = []
    d38 = base_dword(idx, 0x38)
    inmask = (u8("g985", 0x985b10) >> fac) & 1
    flag = 0 if (inmask and not ((d38 & 0x40) and (d38 & 0x80000000))) else 1
    budget = pop + 1
    # asm:42-45 (0x4e796a-0x4e7972): base+0x78 &= (~DAT_008f0d30 | 1).  M53q: the
    # filter runs AFTER call 0x4e63b0 (0x4e78e9 < 0x4e796a), and 4e63b0 rebuilds
    # 0x8f0d30 FOR THIS BASE before returning -- so the mask is build_table(idx),
    # not the stale global left by whoever was processed last.  --stale-mask keeps
    # the superseded semantics (the global DAT_008f0d30 from the dump).
    tbl, fresh_mask = build_table(idx)
    mask_in = (R["d78"] if stale_mask else
               (R["d78"] & ((~fresh_mask | 1) & 0xFFFFFFFF))) & 0xFFFFFFFF
    c84 = [R["d84"], R["d88"]]
    c7c, c80 = R["d7c"], R["d80"]

    # ---- seed loop (asm:40-117): base+0xbc..0xc8 = 0x94dc34[fac*0x82f + field]
    vec = []
    seed_terms = []
    for f in range(4):
        v = s32v("facrec", 0x94DC34 + fac * 0x20BC + f * 4)
        raw = v
        if not fb[0x1D] and (G["spec_base"] < 0 or
                             blob_at("bases", BLOB_BASE["bases"] + G["spec_base"] * 0x130 + 4, 1)[0] != fac):
            v = sdiv(v + 1, 2)
        v = min(v, pop)
        seed_terms.append((raw, v))
        vec.append(v)

    processed = 0
    jump_tail = False
    scan_ran = [False]

    def add4(x, y, tag, sign=1):
        # asm:229-240 (0x4e7be9-0x4e7bf9): FUN_004e75f0(field, fac, DAT_0068cbb0, x, y).
        # DAT_0068cbb0 is the index of the base being rebuilt (the caller sets it per
        # base; live 70 = base 70 was the last one processed).  Tested: passing the
        # constant 70 regresses 49 bases, passing idx matches -- so bidx == idx here.
        d = [disp(f, fac, idx, x, y, fb) for f in range(4)]
        for f in range(4):
            vec[f] = s32(vec[f] + sign * d[f])
        trace.append((tag, (x, y), d, sign))
        return d

    def scan_pass():
        nonlocal budget, processed, jump_tail
        if popcount(mask_in) > budget:
            return
        scan_ran[0] = True
        for s in range(21):
            if s != 0 and not ((mask_in >> s) & 1):
                continue
            processed |= 1 << s
            x, y = wrap_x(bx + XOFF[s]), by + YOFF[s]
            if -1 < y < G["map_h"] and -1 < x < G["map_w"]:
                add4(x, y, "scan%d" % s)
            else:
                trace.append(("scan%d-oob" % s, (x, y), [0, 0, 0, 0], 1))
            budget -= 1
            if budget == 0:
                break
        if scan_ran[0] and budget == c80 + c7c:
            jump_tail = True

    # ---- skip-flag branches
    if flag == 0:
        scan_pass()
    else:
        if G["g91c628"] == 0:
            n = 0
            c80 = 0
            i = 0
            while i < c7c:
                nb = nibble(c84, i) if i < 16 else chooser(idx) + 1
                if entry_dword(nb, 0) == 0:
                    c80 += 1
                i += 1
            c7c -= c80
            scan_pass()
        if flag and c7c != 0 and (c80 + c7c) > 0 and not (scan_ran[0] and budget == c80 + c7c):
            i = 0
            while i < c80 + c7c:
                nb = nibble(c84, i) if i < 16 else chooser(idx) + 1
                if entry_dword(nb, 0) == 0:
                    j = i + 1
                    while j < c80 + c7c:
                        nb2 = nibble(c84, j) if j < 16 else chooser(idx) + 1
                        if i < 16:
                            w = (i >> 3) * 4
                            c84[i >> 3] = (c84[i >> 3] & ~(0xF << w)) | ((nb2 & 0xF) << w)
                        j += 1
                        nb = nibble(c84, i) if i < 16 else chooser(idx) + 1
                        if entry_dword(nb, 0) != 0:
                            break
                    if c80:
                        c80 -= 1
                i += 1
    if jump_tail:
        pass
    elif (processed & 1) == 0:
        x, y = wrap_x(bx + XOFF[0]), by + YOFF[0]
        if -1 < y < G["map_h"] and -1 < x < G["map_w"]:
            add4(x, y, "scan0-special")
        processed |= 1
        budget -= 1

    # ---- faction modifier block
    C = CONST
    if inmask == 0 or (d38 & 0x80000000) == 0:
        if inmask == 0:
            l38, l28, l24, l3c = (frec(0x94D810, fac), frec(0x94D814, fac),
                                  frec(0x94D818, fac), frec(0x94D81C, fac))
            l18 = frec(0x94D80C, fac)
        else:
            l38 = l28 = l24 = l3c = l18 = 0
    else:
        l28, l38 = (d38 >> 0x18) & 2, (d38 >> 0x18) & 1
        l24, l3c = (d38 >> 0x19) & 2, (d38 >> 0x1A) & 2
        if l3c:
            l18 = 2
        elif l38 == 0 and l24 == 0:
            l18 = -2 if l28 else frec(0x94D80C, fac)
        else:
            l18 = 0
    G["c30_w"] = 0

    def tile_add(s, sign, tag):
        x, y = wrap_x(bx + XOFF[s]), by + YOFF[s]
        if -1 < y < G["map_h"] and -1 < x < G["map_w"]:
            add4(x, y, tag, sign)

    # ---- middle pass (skipped entirely when the scan loop jumped to LAB_004e8a47)
    while not jump_tail:
        l5c = budget <= c80 + c7c
        l54 = 0 if l5c else processed
        gmax, gidx, lval, lidx, maxf0 = mp_best(budget, c80, c7c, vec, processed, l54,
                                                l18, l24, l28, l38, l3c, fac, idx, pop, fb)
        if G.get("dbg") == idx:
            print("  MP iter l5c=%d budget=%d c80=%d c7c=%d vec=%s gmax=%d gidx=%d lval=%d lidx=%d maxf0=%d processed=%s"
                  % (l5c, budget, c80, c7c, vec, gmax, gidx, lval, lidx, maxf0, hex(processed)))
        if flag and pop > 4 and (pop * G["k27c"] < vec[0] or maxf0 == 0) and G["k85afc"] > 100:
            gv, gi = gmax, gidx
            for k in range(-1, -8, -1):
                def ed(j, k=k):
                    return struct.unpack_from("<i", _blob["g926"][1],
                                              0x926cac - BLOB_BASE["g926"] + k * 28 + j * 4)[0]
                if not (tech_avail(ed(-1), fac) and not tech_avail(ed(0), fac)):
                    continue
                d4 = clamp99(vec[2] + c80)
                v = s32(ed(2) * 0x40
                        + sdiv(s32(l24 + 2) * pop * ed(1) * 0x40, d4)
                        + sdiv(s32(l28 + 2) * pop * ed(3) * 0x40, clamp99(vec[2] + c80)))
                if v > gv:
                    gv, gi = v, k
            gmax, gidx = gv, gi
        if l5c:
            if gidx > 0 and lval < gmax and lidx > 0:
                lbit = 1 << (lidx & 0x1F)
                gbit = 1 << (gidx & 0x1F)
                processed = (~lbit & processed) | gbit
                tile_add(lidx, -1, "mp-swap-out")
                tile_add(gidx, +1, "mp-swap-in")
                if vec[0] < (pop + 1) * G["k27c"]:
                    processed = (~gbit & processed) | lbit
                    tile_add(gidx, -1, "mp-undo")
                    tile_add(lidx, +1, "mp-back")
            break
        if gidx < 0:
            if c80 < 16:
                w = (c80 & 7) * 4
                c84[c80 >> 3] = (c84[c80 >> 3] & ~(0xF << w)) | (((-1 - gidx) & 0xF) << w)
            c80 += 1
            continue
        if gidx < 1:
            break
        processed |= 1 << (gidx & 0x1F)
        tile_add(gidx, +1, "mp-gain")
        budget -= 1
        if (c80 + c7c < budget) or ((pop + 1) * G["k27c"] < vec[0]):
            continue
        break

    # ---- LAB_004e8a47 nibble fill
    filled = []
    i = c7c
    while i < budget:
        arg = chooser(idx)
        if i < 16:
            w = (i & 7) * 4
            c84[i >> 3] = (c84[i >> 3] & ~(0xF << w)) | ((arg & 0xF) << w)
        filled.append((i, arg))
        i += 1

    out = {"idx": idx, "fac": fac, "pop": pop, "flag": flag, "budget0": pop + 1,
           "budget_end": budget, "mask_in": mask_in, "processed": processed,
           "mask_fresh": fresh_mask, "table": tbl, "mask_stale": G["d30"],
           "c7c_in": R["d7c"], "c7c_end": c7c, "c80_end": c80, "nib_out": c84,
           "pop_drift": 0 if pop_visit is None else 1, "pop_dump": R["pop"],
           "seed": seed_terms, "trace": trace, "vec": vec, "obs": R["vec"],
           "filled": filled, "cc8_delta": G["cc8_delta"]}
    if verbose:
        for t in trace:
            print("   ", t)
    return out


def mp_best(budget, c80, c7c, vec, processed, l54, l18, l24, l28, l38, l3c, fac, idx, pop, fb):
    """recompute the 1..79 best-gain / best-loss scan indices (score() logic inlined)."""
    R = row(idx)
    bx, by = R["x"], R["y"]
    gidx, gmax, lidx, lval, maxf0 = 0, 0, -1, 0x270F, 0
    # asm:789-796 (0x4e82ef-0x4e8302): the candidate table pointer [ebp-0x2c] starts at 0
    # (asm:539), reads XOFF at [ptr+0x678510] (asm:551) = XOFF[s] with s = ptr/4+1, is
    # post-incremented by 4 (asm:791) and the loop runs while ptr < 0x50 (asm:793) ->
    # ptr = 0x00..0x4c, i.e. s = 1..20 ONLY (the same 20 spiral neighbours the scan loop
    # covers), NOT 1..79.
    for s in range(1, 21):
        bit = 1 << (s & 0x1F)
        if bit & (l54 | G["d30"]):
            if G.get("dbg") == idx:
                print("  cand %d skip-gate" % s)
            continue
        x, y = wrap_x(bx + XOFF[s]), by + YOFF[s]
        if not (-1 < y < G["map_h"] and -1 < x < G["map_w"]):
            if G.get("dbg") == idx:
                print("  cand %d skip-oob" % s)
            continue
        a = y0(fac, idx, x, y, 0, fb)
        b = y1(fac, idx, x, y, 0, fb)
        c = y2(fac, idx, x, y, 0, fb)
        aa, bb, cc, l50 = a, b, c, 0
        if a > maxf0:
            maxf0 = a
        k2 = pop * G["k27c"]
        if sdiv(budget, G["k27c"]) + vec[0] < k2:
            l50 = 2 if (budget + vec[0] >= k2) else 8
            if aa < 0:
                aa = s32(aa + 0)                       # u14 = 0 path
            elif aa <= l50:
                aa = s32(aa * 2)                       # goto LAB_004e815d: skip the += u14
            else:
                aa = s32(aa + l50)                     # fall through: y0 += local_50
        else:
            G["c30_w"] = 1
        # LAB_004e815d: all three doubled, then the two corrections, for BOTH paths.
        # asm:658-683 (0x4e817f-0x4e81b6): the corrections are plain trunc(x/2), NOT
        # subtract-then-sar. `lea edx,[ecx+edi]` at 0x4e817f sets edx = pop+k2 for the
        # 0x4e8182 `cmp ebx,edx` guard ONLY; each correction is the canonical signed
        # div-by-2 idiom `cdq ; sub eax,edx ; sar eax,1` (0x4e818d-90, 0x4e8198-9b,
        # 0x4e81b1-b4) and cdq clobbers that edx, so the machine halves the doubled
        # value (trunc toward 0) -- i.e. undoes the doubling. M/E get it when
        # base+0xbc <= pop+k2 and F==0; F gets it when (post-correction) M==0 and
        # local_4c==0.
        aa, bb, cc = s32(aa * 2), s32(bb * 2), s32(cc * 2)
        pk1 = pop + k2
        if vec[0] <= pk1 and aa == 0:
            bb, cc = sdiv(bb, 2), sdiv(cc, 2)
        if bb == 0 and l50 == 0:
            aa = sdiv(aa, 2)
        val = final_score(aa, bb, cc, l50, budget, vec, pop, l18, l24, l28, l38, l3c, idx)
        if G.get("dbg") == idx:
            print("  cand %d pair=%s val=%d raw=(%d,%d,%d) l50=%d" %
                  (s, "swap" if processed & bit else "add", val, a, b, c, l50))
        if processed & bit:
            if val < lval:
                lval, lidx = val, s
        elif val > gmax:
            gmax, gidx = val, s
    return gmax, gidx, lval, lidx, maxf0


def final_score(aa, bb, cc, l50, budget, vec, pop, l18, l24, l28, l38, l3c, idx):
    k2 = pop * G["k27c"]
    d1 = clamp99(((budget - sdiv(pop, 3)) - k2 + vec[0]) * 2 - 2)
    m1 = (l38 + 4) * aa
    # asm:713-719 (0x4e820b-0x4e821d): `mov eax,[esi+0x50]` is a DWORD read of base+0x50
    # compared against 0xffffffd9 (-0x27) with jge -> m2 = -l28, else m2 = 2.  (The M53o
    # model read a short there; the high half matters when base+0x50 >= 0x10000.)
    m2 = 2 if s32(base_dword(idx, 0x50)) < -0x27 else -l28
    d2 = clamp99(sdiv(vec[1] - G["c4c"] + 1, 2))
    n1 = clamp99(pop - l3c)
    d3 = clamp99(vec[2])
    t1 = sdiv(m1 * 0x100, d1)
    t2 = sdiv(s32(s32(s32(s32(m2) + l18) + l3c) + 6 + l24) * pop * bb * 0x40, d2)
    t3 = sdiv(s32(l24 + 1 + l28 * 2) * n1 * cc * 0x40, d3)
    return s32(t1 + t2 + t3)


def recover_pop(idx, stale_mask=False, verbose=False):
    """M53r: budget0 = pop+1 AT VISIT TIME (asm 0x4e7904) and base+0x7c published at exit
    == DAT_008f0c68 (asm 0x4e8b28).  The dump's pop byte@6 is the pop AFTER the visit; a
    base that lost a point (attrition/combat) after its rebuild visit makes the plain
    replay fall into the middle pass the game skipped (game: scan ends with
    budget == c80+c7c -> je 0x4e8a47 skips scan-0 special AND middle pass).  Retry with
    pop_visit = dump+1; accept only when that reproduces the stored mask AND the stored
    carry -- the extra budget unit is then independently confirmed by two outputs."""
    o = rebuild(idx, stale_mask, verbose)
    if (o["processed"] == o["mask_in"] and o["budget_end"] == o["c7c_in"]
            and list(o["vec"]) == list(o["obs"])):
        return o
    o1 = rebuild(idx, stale_mask, verbose, pop_visit=row(idx)["pop"] + 1)
    if o1["processed"] == o1["mask_in"] and o1["budget_end"] == o1["c7c_in"]:
        return o1
    return o


# ------------------------------------------------ FUN_004eaa10 allied-energy fold (M53t)
FACR = 0x94d734          # faction record array, stride 0x20bc (asm 0x4eab18-0x4eab29)
STANCE = 0x94d448        # dword matrix [fac][other]; low byte bit2 = allied, bit1 = full share
NBMAX = 76


def fac_u32(f, off):
    return u32("facrec", FACR + f * 0x20bc + off)


def fac_s32(f, off):
    return s32v("facrec", FACR + f * 0x20bc + off)


def stance(f, other):
    """[0x94d448 + f*0x20bc + other*4] — f's stance toward other (asm 0x4eab1d-0x4eab36)."""
    return u32("facrec", STANCE + f * 0x20bc + other * 4)


def base_energy(i):
    """base+0xb4.  4e78e0's exit shift copies +0xc4 down to +0xb4 (asm 0x4e8b39-0x4e8b54),
    so by the time 4eaa10 runs this holds the energy the fold reads for both ends."""
    return s32v("bases", BLOB_BASE["bases"] + i * 0x130 + 0xb4)


def energy_rank(idx):
    """0-based rank of base idx among its owner's bases, 0 = highest.
    key = energy<<9 + idx, compared against energy<<9 + DAT_0068cbb0 (the LIVE cur-base
    index, asm 0x4eaac0-0x4eaad4) — hence the tie-break is the global, not this base's idx."""
    fac, me = row(idx)["fac"], base_energy(idx)
    key = (me << 9) + idx          # DAT_0068cbb0 == THIS base's index inside 4f5a70 (0x4f5a7c)
    return sum(1 for b in range(min(G["nbases"], NBMAX))
               if row(b)["fac"] == fac and (base_energy(b) << 9) + b > key)


def kth_energy_base(fac, k):
    """FUN_004ea940: the k-th HIGHEST-ENERGY base of fac — no distance is ever computed.
    key = energy<<9 | idx, bubble-sorted descending (asm 0x4ea95e-0x4eaa00);
    returns -1 when k >= count, else the base index (low 9 bits of the key)."""
    keys = sorted(((base_energy(b) << 9) + b for b in range(min(G["nbases"], NBMAX))
                   if row(b)["fac"] == fac), reverse=True)
    return -1 if k >= len(keys) else (keys[k] & 0x1FF)


def alliance_fold(idx, verbose=False):
    """The share FUN_004eaa10 adds to base+0xc4 AFTER 4e78e0 (0x4eac57-0x4eac62), summed over
    every OTHER faction allied with the owner in either direction.  Machine-pinned in
    evidence/m53t_fold.md; per-ally term:
        n  = ceil((energy[ally_base[k]] + energy[me]) / 8)   (+= itself if 0x985bd4 < 0x985bd0)
        s  = ((faction[owner].+0 + 1) * n + D/2) / D          D = [0x92a274] + 1
        s /= 2 unless stance[owner][other] bit 1
        s += 1 if [0x985bc0] == owner
        s  = 0 if [0x94d4f0 + owner*0x20bc] or [0x94d4f0 + other*0x20bc]
    The value is gated AFTER being published to DAT_008f0d40[other-1] (0x4eac27), so the
    published copy keeps the ungated share."""
    fac = row(idx)["fac"]
    D = u32("g92a", 0x92a274) + 1
    rnd = D >> 1
    me = base_energy(idx)
    k = energy_rank(idx)
    total, detail = 0, []
    for other in range(1, 8):
        if other == fac:
            continue
        if not (stance(fac, other) & 2 or stance(other, fac) & 2):
            continue
        if fac_u32(other, 0xd54) == 0:
            continue
        ab = kth_energy_base(other, k)
        if ab < 0:
            continue
        n = ashr(base_energy(ab) + me + 7, 3)
        if u32("g985", 0x985bd0) > u32("g985", 0x985bd4):
            n *= 2
        s = sdiv((fac_s32(fac, 0) + 1) * n + rnd, D)
        if not (stance(fac, other) & 1):
            s = ashr(s, 1)
        if u32("g985", 0x985bc0) == fac:
            s += 1
        if fac_u32(fac, -0x244) or fac_u32(other, -0x244):
            s = 0
        detail.append((other, ab, n, s))
        total += s
    if verbose:
        print("  fold: rank %d D %d rnd %d  %s  = %+d" % (k, D, rnd, detail, total))
    return total, detail


def compare(idx, recover=True, fold=True, verbose=False):
    """(ok, ok_before_fold, vec_after, obs, fold_total, detail) for one base."""
    o = recover_pop(idx, False, verbose) if recover else rebuild(idx, False, verbose)
    obs = list(o["obs"])
    if idx == 70:
        obs[0] -= G["c6c"]
    vec = list(o["vec"])
    f, det = alliance_fold(idx, verbose) if fold else (0, [])
    vec[2] += f
    ok_before = all(o["vec"][j] == obs[j] for j in range(4))
    return (all(vec[j] == obs[j] for j in range(4)), ok_before, vec, obs, f, det, o)


def census(recover=True, fold=True, verbose=False):
    n = len(_rows["r"])
    selfc = exact = folded = 0
    bad = []
    for i in range(n):
        ok, ok_before, vec, obs, f, det, o = compare(i, recover, fold)
        selfc += (o["processed"] == o["mask_in"] and o["budget_end"] == o["c7c_in"])
        exact += ok_before
        folded += ok
        if not ok:
            bad.append((i, [vec[j] - obs[j] for j in range(4)], f, det))
    print("census: rows %d  self-consistent %d  exact-before %d  exact-after-fold %d"
          % (n, selfc, exact, folded))
    for i, d, f, det in bad:
        print("  residual idx %-3d delta %s  fold %+d %s" % (i, d, f, det))
    return folded


def show(idx, stale_mask=False, verbose=False, recover=True):
    o = recover_pop(idx, stale_mask, verbose) if recover else rebuild(idx, stale_mask, verbose)
    obs = list(o["obs"])
    obs[0] -= G["c6c"] if idx == 70 else 0
    print("idx %d fac %d pop %d flag %d budget %d->%d mask_in %s processed %s mask %s%s%s"
          % (idx, o["fac"], o["pop"], o["flag"], o["budget0"], o["budget_end"],
             hex(o["mask_in"]), hex(o["processed"]), hex(o["mask_fresh"]),
             " (live d30 %s)" % hex(o["mask_stale"]) if idx == G["base_idx"] else "",
             " pop-drift=+1(pop %d->%d)" % (o["pop_dump"], o["pop"]) if o["pop_drift"] else ""))
    names = ["bc", "c0", "c4", "c8"]
    for f in range(4):
        terms = [(t[0], t[1][0], t[1][1], t[2][f] * t[3]) for t in o["trace"]]
        s = sum(t[3] for t in terms)
        tot = o["vec"][f]
        tgt = obs[f]
        print("  %s model=%-4d obs=%-4d delta=%-3d  seed=%s  sum=%s %s"
              % (names[f], tot, tgt, tot - tgt, o["seed"][f][1], s,
                 " ".join("%s@%s:%+d" % (t[0], t[1], t[3]) for t in terms if t[3])))
    f, det = alliance_fold(idx, verbose)
    print("  4eaa10 fold %+d %s  => c4 model+fold %d  obs %d"
          % (f, det, o["vec"][2] + f, obs[2]))
    return o, obs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("idx", nargs="*", type=int)
    ap.add_argument("--stale-mask", action="store_true", dest="stale_mask",
                    help="superseded M53p semantics: entry mask from the dump's global DAT_008f0d30")
    ap.add_argument("--no-pop-recover", action="store_true", dest="no_pop_recover",
                    help="report the plain pop=dump replay only (no pop-drift probe)")
    ap.add_argument("--mem-dir", dest="mem_dir",
                    help="snapshot dir (default evidence/m53o_mem; session-75 PRE-DRIVE dump is "
                         "evidence/m53s_dump1)")
    ap.add_argument("--census", action="store_true",
                    help="all rows: self-consistency + exactness before/after the 4eaa10 fold")
    ap.add_argument("--no-fold", action="store_true", dest="no_fold",
                    help="census without FUN_004eaa10's allied-energy share")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args()
    if a.mem_dir:
        global MDIR
        MDIR = os.path.abspath(a.mem_dir)
    init()
    if a.census:
        census(recover=not a.no_pop_recover, fold=not a.no_fold, verbose=a.verbose)
        return
    idxs = a.idx or [70, 0, 3, 4, 6, 10, 23]
    full = []
    for i in idxs:
        o, obs = show(i, a.stale_mask, a.verbose, recover=not a.no_pop_recover)
        if all(o["vec"][f] == obs[f] for f in range(4)):
            full.append(i)
    print("full-match:", full, "facs:", sorted({row(i)["fac"] for i in full}))


if __name__ == "__main__":
    main()
