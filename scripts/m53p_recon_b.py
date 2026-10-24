#!/usr/bin/env python3
"""Reconstruct FUN_004e78e0's rebuild of base+0xbc/0xc0/0xc4/0xc8 in Python.

m53p_recon_b = partial-vector-hypothesis variant. ASM VERIFIED: the middle-pass score
reads the record in place (0x4e821f [esi+0xc0], 0x4e828c [esi+0xc4], ecx from [esi+0xbc]
at 0x4e810c; shortage test 0x4e8328 [esi+0xbc]) with no snapshot copy, so the game scores
against the partial in-place vector. Model audit: mp_best/final_score already receive the
running partial vec (seed line 576, scan add4 line 605, commits via tile_add); they never
read R["vec"] (live /proc record values). The hypothesis change is therefore a NO-OP here;
this copy exists to prove the numbers are unchanged.

    python3 scripts/m53o_recon.py            # the 7 pinned candidate bases
    python3 scripts/m53o_recon.py 70 4 10    # specific idxs
    python3 scripts/m53o_recon.py --legacy   # pre-fix model (scan-mask input = raw post-state)
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


# ---------------------------------------------------------------- FUN_004e78e0
def rebuild(idx, legacy=False, verbose=False):
    R = row(idx)
    fac, pop, bx, by = R["fac"], R["pop"], R["x"], R["y"]
    G["cc8_delta"] = 0
    fb = fac_bits(idx)
    trace = []
    d38 = base_dword(idx, 0x38)
    inmask = (u8("g985", 0x985b10) >> fac) & 1
    flag = 0 if (inmask and not ((d38 & 0x40) and (d38 & 0x80000000))) else 1
    budget = pop + 1
    # asm:42-45 (0x4e796a-0x4e7972): base+0x78 &= (~DAT_008f0d30 | 1)  [NOT ~(pop|1)]
    mask_in = R["d78"] if legacy else (R["d78"] & ((~G["d30"] | 1) & 0xFFFFFFFF))
    mask_in &= 0xFFFFFFFF
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
           "c7c_in": R["d7c"], "c7c_end": c7c, "c80_end": c80, "nib_out": c84,
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
        # asm:681-697 (0x4e817f-0x4e81b6): the corrections are NOT plain halvings --
        # when nutrient <= pop*(K+1) and F==0, M and E become ashr(2M - pop*(K+1), 1)
        # (`sub eax,edx ; sar eax,1`, edx = pop + pop*K set at 0x4e817f); F gets the
        # same subtract-then-sar when (post-correction) M==0 and local_50==0.
        aa, bb, cc = s32(aa * 2), s32(bb * 2), s32(cc * 2)
        pk1 = pop + k2
        if vec[0] <= pk1 and aa == 0:
            bb, cc = ashr(bb - pk1, 1), ashr(cc - pk1, 1)
        if bb == 0 and l50 == 0:
            aa = ashr(aa - pk1, 1)
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


def show(idx, legacy=False, verbose=False):
    o = rebuild(idx, legacy, verbose)
    obs = list(o["obs"])
    obs[0] -= G["c6c"] if idx == 70 else 0
    print("idx %d fac %d pop %d flag %d budget %d->%d mask_in %s processed %s"
          % (idx, o["fac"], o["pop"], o["flag"], o["budget0"], o["budget_end"],
             hex(o["mask_in"]), hex(o["processed"])))
    names = ["bc", "c0", "c4", "c8"]
    for f in range(4):
        terms = [(t[0], t[1][0], t[1][1], t[2][f] * t[3]) for t in o["trace"]]
        s = sum(t[3] for t in terms)
        tot = o["vec"][f]
        tgt = obs[f]
        print("  %s model=%-4d obs=%-4d delta=%-3d  seed=%s  sum=%s %s"
              % (names[f], tot, tgt, tot - tgt, o["seed"][f][1], s,
                 " ".join("%s@%s:%+d" % (t[0], t[1], t[3]) for t in terms if t[3])))
    return o, obs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("idx", nargs="*", type=int)
    ap.add_argument("--legacy", action="store_true")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args()
    init()
    idxs = a.idx or [70, 0, 3, 4, 6, 10, 23]
    full = []
    for i in idxs:
        o, obs = show(i, a.legacy, a.verbose)
        if all(o["vec"][f] == obs[f] for f in range(4)):
            full.append(i)
    print("full-match:", full, "facs:", sorted({row(i)["fac"] for i in full}))


if __name__ == "__main__":
    main()
