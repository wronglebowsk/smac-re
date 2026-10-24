#!/usr/bin/env python3
"""Live read-only probe: everything FUN_004e63b0 reads, around the current base.

Prints, for the base in DAT_008f0d60:
  * the 21 spiral tiles with the fields 4e63b0 tests (seen byte+4, mask dword+8,
    level nibble byte+2&0xf, owner byte+7, category byte+0&0xe0, +0xc list head)
  * every unit whose (x,y) is one of those tiles, with +4 type, +14 fac, +17 order,
    +24/+25 (the 0x440 test + fac-bit test), +48/+50 chain links
  * every base within hex-dist 5 (with its +0x78 processed mask) -- the loop-B feed
  * the live 25-slot table 0x8f0ccc + DAT_008f0d30 + the base's own +0x78
Ground truth for scripts/m53p_recon_a.py build_table().
"""
import struct, subprocess, sys

p = subprocess.run(["pgrep", "-x", "terran.exe"], capture_output=True, text=True).stdout.split()
if not p:
    sys.exit("no terran.exe")
f = open(f"/proc/{p[0]}/mem", "rb")
def rd(a, n):
    f.seek(a); return f.read(n)
def u32(a): return struct.unpack("<I", rd(a, 4))[0]
def s32(a): return struct.unpack("<i", rd(a, 4))[0]
def u16(a): return struct.unpack("<H", rd(a, 2))[0]
def i16(a): return struct.unpack("<h", rd(a, 2))[0]
def u8(a): return rd(a, 1)[0]

TERR = u32(0x92ae14); W = u32(0x92a378); H = u32(0x92a37c); WRAP = u8(0x92a394) & 1
STRIDE = u32(0x692184)
NB = u32(0x985af4); NUNIT = u32(0x985af0)
CURB = u32(0x8f0d60); CURI = s32(0x68cbb0); D64 = s32(0x8f0d64); D30 = u32(0x8f0d30)
solo = u32(0x920434)
DX = list(struct.unpack("<25i", rd(0x67850c, 100)))
DY = list(struct.unpack("<25i", rd(0x678990, 100)))
bx, by, fac = i16(CURB), i16(CURB + 2), u8(CURB + 4)
print(f"cur idx {CURI} ptr {CURB:#x} x {bx} y {by} fac {fac} pop {u8(CURB+6)} "
      f"nb {NB} nunit {NUNIT} wrap {WRAP} solo {solo} d64 {D64}")
print("base+0x78 (processed) =", hex(u32(CURB + 0x78)), " +0x7c", s32(CURB + 0x7c), " +0x80", s32(CURB + 0x80))
print("live table:", [s32(0x8f0ccc + 4 * i) for i in range(25)])
print("live DAT_008f0d30:", hex(D30))

def rec(x, y):
    return TERR + (STRIDE * y + (x >> 1 if x >= 0 else -((-x) >> 1))) * 0x2c

def tile(x, y):
    d = rec(x, y); r = rd(d, 0x2c)
    return dict(cat=r[0] & 0xE0, b0=r[0], b2lo=r[2] & 0xF, b2hi=r[2] >> 4, seen=r[4],
                b5=r[5], b7=struct.unpack_from("<b", r, 7)[0], m8=struct.unpack_from("<I", r, 8)[0],
                c0c=struct.unpack_from("<I", r, 0xC)[0])

print("\n== 21 spiral tiles (step: x,y cat b0 lvl(b2lo) hi seen mask8 owner +0xc) ==")
for i in range(21):
    tx, ty = bx + DX[i], by + DY[i]
    tw = tx
    if not WRAP:
        if tw < 0: tw += W
        elif tw >= W: tw -= W
    o = f"OOB(x={tx},y={ty})"
    if 0 <= ty < H and 0 <= tw < W:
        t = tile(tw, ty)
        o = (f"{tw},{ty} cat{t['cat']:#04x} b0 {t['b0']:#04x} lvl {t['b2lo']} hi {t['b2hi']:#04x} "
             f"seen {t['seen']:#04x} mask8 {t['m8']:#010x} own {t['b7']:#x} c {t['c0c']:#x}")
    print(f"  {i:2d} d({DX[i]:2d},{DY[i]:2d}) {o}")

print("\n== units on/near the 21 tiles (+48/+50 links) ==")
tiles = set()
for i in range(21):
    tx, ty = bx + DX[i], by + DY[i]
    tw = tx
    if not WRAP:
        if tw < 0: tw += W
        elif tw >= W: tw -= W
    if 0 <= ty < H and 0 <= tw < W: tiles.add((tw, ty))
for u in range(NUNIT):
    a = 0x933278 + 52 * u
    ux, uy = i16(a), i16(a + 2)
    if (ux, uy) in tiles:
        print(f"  unit {u:3d} ({ux},{uy}) type {u8(a+4)} fac {u8(a+14)} order {u8(a+17)} "
              f"w25 {u8(a+25):#04x} w18 {u16(a+24):#06x} +48 {i16(a+48)} +50 {i16(a+50)}")

print("\n== bases with hexdist<=5 of the current base (loop-B feed) ==")
def abs_(v): return -v if v < 0 else v
def hexd(x0, y0, x1, y1):
    dx = x0 - x1
    if not WRAP:
        ad = abs_(dx); c = u32(0x692184)
        if ad > c: dx = W - ad
    ax, ay = abs_(dx), abs_(y0 - y1)
    mx, mn = (ax, ay) if ax > ay else (ay, ax)
    t = ((ax + ay) >> 1) - mn + 1
    return mx - (t >> 1)
for n in range(NB):
    b = 0x95da10 + 0x130 * n
    d = hexd(bx, by, i16(b), i16(b + 2))
    if d <= 5:
        print(f"  base {n:2d} ({i16(b)},{i16(b+2)}) fac {u8(b+4)} pop {u8(b+6)} hexd {d} "
              f"+0x78 {u32(b+0x78):#010x}")

print("\n== relation bytes 0x94d448[fac*0x20bc + 4*o] for all o ==")
for o in range(8):
    v = u8(0x94d448 + fac * 0x20BC + 4 * o)
    print(f"  o {o}: {v:#04x}  (&3 -> {v & 3})")
print("facrec 0x94d430[fac] dword:", hex(u32(0x94d430 + fac * 0x20BC)),
      "(bit9 set ->", bool(u32(0x94d430 + fac * 0x20BC) & 0x200), ")")
