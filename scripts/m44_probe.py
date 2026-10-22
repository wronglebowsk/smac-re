#!/usr/bin/env python3
"""M44 live probes, consolidated — read-only /proc/<pid>/mem, no gdb, no state change.

Prints, in order:
  1. live state (year, cur, n_bases, our energy, tech bytes)
  2. our units with NAMES + class (type record base 0x98ad88: name +0, ability +32,
     domain +36, class +42 — the standing absolute addresses 0x98ada8/ac/b2 are
     +32/+36/+42 of THAT base, not the record base)
  3. terrain table 0x6938f0+k*32 SET/CLEAR/work x op-name strings 0x94d2f8
     (the tile-mask bit vocabulary)
  4. mask bit 0x2 == "unit standing on the record's tile pair" histogram test
  5. a chosen tile record: +0 elev, owner nibble, +8 mask, +0x18 second layer

Usage: python3 scripts/m44_probe.py [x y ...]      (default tiles 45 7 45 11 43 11)
"""
import struct
import subprocess
import sys

PID = subprocess.run(["pgrep", "-x", "terran.exe"], capture_output=True, text=True).stdout.split()[0]
F = open(f"/proc/{PID}/mem", "rb", 0)


def seek(a):
    F.seek(a)


def rd(a, n):
    F.seek(a); return F.read(n)


def u32(a):
    return struct.unpack("<I", rd(a, 4))[0]


def i32(a):
    return struct.unpack("<i", rd(a, 4))[0]


def cstr(a, n=40):
    return rd(a, n).split(b"\0", 1)[0].decode("latin1", "replace")


TYPE_BASE = 0x98ad88          # name at +0 (34 B); ability +32, domain +36, class +42
UNITS, TILE_PTR, FAC = 0x933278, 0x92ae14, 0x94d650
ME = 3


def tile(x, y):
    rec = u32(TILE_PTR) + (40 * y + (x >> 1)) * 0x2c
    r = rd(rec, 0x2c)
    return dict(idx=rec, elev=r[0] >> 5, owner=r[2] & 0xF,
                mask8=struct.unpack("<I", r[8:12])[0],
                mask18=struct.unpack("<I", r[0x18:0x1c])[0], raw=r)


def units():
    blob = rd(UNITS, 300 * 52)
    out = []
    for i in range(300):
        r = blob[i * 52:i * 52 + 52]
        if len(r) < 52:
            break
        x = struct.unpack("<h", r[0:2])[0]
        if x == -1 or x == 0xffff:
            continue
        if r[14] != ME:
            continue
        t = struct.unpack("<H", r[10:12])[0]
        out.append(dict(idx=i, x=r[0], y=r[2], type=t, cls=rd(TYPE_BASE + t * 52 + 42, 1)[0],
                        name=cstr(TYPE_BASE + t * 52), order=r[17], mpused=r[40], work37=r[37],
                        reserve=struct.unpack("<I", r[16:20])[0],
                        home=struct.unpack("<H", r[46:48])[0]))
    return out


print(f"pid {PID}")
print(f"1. year={u32(0x985b00)} cur={u32(0x985dcc)} n_bases={u32(0x985af4)} "
      f"difficulty={u32(0x985aec)} our_energy={i32(FAC + ME * 0x82f * 4)}")
tb = rd(0x985c1c, 64)
print(f"   tech bytes: 18={tb[18]:#04x} 59={tb[59]:#04x} 60={tb[60]:#04x} (bit = player&0x1f)")

print("2. our units")
for u in units():
    print(f"   idx {u['idx']:>3} ({u['x']},{u['y']}) {u['name']!r} type={u['type']} cls={u['cls']} "
          f"order={u['order']} mpused={u['mpused']} work37={u['work37']} reserve={u['reserve']} "
          f"home={u['home']:#x}")

print("3. terraform mask vocabulary (0x6938f0+k*32 SET/CLEAR/work x 0x94d2f8 names)")
for k in range(18):
    r = rd(0x6938f0 + k * 32, 32)
    setb, clr, work = struct.unpack("<III", r[0:12])
    nm = ""
    if k < 14:
        a, b, c = struct.unpack("<III", rd(0x94d2f8 + k * 12, 12))
        nm = f"{cstr(a)} / {cstr(b)} / key {cstr(c)!r}"
    print(f"   k={k:>2} SET={setb:#010x} CLEAR={clr:#010x} work={work:>3}  {nm}")

print("4. mask bit 1 (0x2) vs unit presence, whole map")
base = u32(TILE_PTR)
blob = rd(base, 3200 * 0x2c)
ub = rd(UNITS, 300 * 52)
occ = set()
for i in range(300):
    r = ub[i * 52:i * 52 + 52]
    if len(r) < 52:
        break
    x = struct.unpack("<h", r[0:2])[0]; y = struct.unpack("<h", r[2:4])[0]
    if x < 0 or y < 0:
        continue
    occ.add(40 * y + (x >> 1))
agree = fp = fn = 0
for i in range(3200):
    bit = bool(struct.unpack("<I", blob[i * 0x2c + 8: i * 0x2c + 12])[0] >> 1 & 1)
    o = i in occ
    if bit == o:
        agree += 1
    elif bit:
        fp += 1
    else:
        fn += 1
print(f"   agree {agree}/3200  bit-set-without-unit {fp}  unit-without-bit {fn}")

print("5. tiles")
args = [int(a) for a in sys.argv[1:]]
pairs = list(zip(args[::2], args[1::2])) or [(45, 7), (45, 11), (43, 11)]
for (x, y) in pairs:
    t = tile(x, y)
    print(f"   ({x},{y}) rec {t['idx']:#x} elev={t['elev']} owner={t['owner']:#x} "
          f"+8={t['mask8']:#x} +0x18={t['mask18']:#x}")
