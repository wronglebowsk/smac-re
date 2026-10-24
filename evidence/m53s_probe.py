#!/usr/bin/env python3
"""M53s probe: the 11 c4 residuals are POST-VISIT ENERGY ADDITIONS.

Facts this probe re-derives from one dump (evidence/m53o_mem, refreshed by
scripts/m53o_mem.py) + a census run (evidence/m53s_run0.txt):
  A. base+0xac..0xb8 is the rebuild's history shift (asm 0x4e8b39-0x4e8b54:
     ac<-bc, b0<-c0, b4<-c4, b8<-c8), so +0xac/0xb0/0xb4/0xb8 = the vector AT THE
     EXIT of the PREVIOUS visit, snapshotted before any later writer can touch it.
  B. model == [ac,b0,b4,b8] on 76/76 rows, all four fields  -> the rebuild model is
     exact for the visit; the residual is NOT a scan/yield rule gap.
  C. c4_now - c4_prev == -delta on exactly the 11 residual rows; bc/c0 never change
     visit->visit on any row  -> someone adds ENERGY to base+0xc4 after 4e78e0 exits.
This script tests candidate per-base fields for "value == gain on the 11 and 0 on the 65".
Usage: python3 evidence/m53s_probe.py [--dump DIR] [--detail]
"""
import json, os, struct, sys, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = sys.argv[sys.argv.index("--dump") + 1] if "--dump" in sys.argv else os.path.join(ROOT, "evidence", "m53o_mem")
RUN = os.path.join(ROOT, "evidence", "m53s_run0.txt")
BASES = 0x95DA10
STRIDE = 0x130

rows = {r["idx"]: r for r in json.load(open(os.path.join(D, "rows.json")))["rows"]}
blob = open(os.path.join(D, "bases.bin"), "rb").read()
meta = json.load(open(os.path.join(D, "meta.json")))


def dw(i, off):
    return struct.unpack_from("<i", blob, i * STRIDE + off)[0]


def u8(i, off):
    return blob[i * STRIDE + off]


model = {}
cur = None
for ln in open(RUN):
    m = re.match(r"idx (\d+) ", ln)
    if m:
        cur = int(m.group(1))
        continue
    m = re.match(r"\s+(bc|c0|c4|c8) model=(-?\d+)\s+obs=(-?\d+)", ln)
    if m and cur is not None:
        model.setdefault(cur, {})[m.group(1)] = (int(m.group(2)), int(m.group(3)))

NAMES = ["bc", "c0", "c4", "c8"]
res, gain, model_eq_prev = [], {}, 0
for i, r in sorted(rows.items()):
    prev, now = r["raw_ac"], r["vec"]
    if all(model[i][NAMES[f]][0] == prev[f] for f in range(4)):
        model_eq_prev += 1
    g = now[2] - prev[2]
    if g:
        res.append(i)
        gain[i] = g
print("dump: %s pid %s ; rows %d ; model==history(ac,b0,b4,b8) on %d rows"
      % (D, meta["pid"], len(rows), model_eq_prev))
print("c4-gain rows (%d): %s" % (len(res), sorted(res)))
print("gains: %s" % {i: gain[i] for i in sorted(res)})

exact = [i for i in rows if i not in gain]
OFFS = [x for x in range(0x2c, 0x130, 4)]
hits = []
for off in OFFS:
    vals = {i: dw(i, off) for i in rows}
    ok = all(vals[i] == gain[i] for i in res) and all(vals[i] == 0 for i in exact)
    if ok:
        hits.append(("==gain", off))
    nz_res = sum(1 for i in res if vals[i] != 0)
    nz_ex = sum(1 for i in exact if vals[i] != 0)
    if nz_res == len(res) and nz_ex == 0:
        hits.append(("nonzero-only-on-residual", off, sorted({vals[i] for i in res})))
    if nz_res == 0 and nz_ex == 0 and off not in (0xac, 0xb0, 0xb4, 0xb8):
        pass
print("candidate base-record fields matching the gain pattern:", hits)

# per-row detail: the fields the economy block is known to touch
if "--detail" in sys.argv:
    print("idx fac gain  d30        d34        d38        d40      d44    d48  d4c  d80  "
          "d84        d88        facbits  d94      d98      dAC      dC4  dCC     dD0    dE0  dE4  dE8  dEC  dF0")
    for i in sorted(res) + sorted(exact)[:6]:
        fb = int.from_bytes(blob[i * STRIDE + 0x8c: i * STRIDE + 0x91], "little")
        print("%3d  f%d  %d  %10x %10x %10x %8d %6d %4d %4d %4d %10x %10x %8d %10x %10x %8d %8d %9d %9d %4d %4d %4d %4d %4d %4d"
              % (i, rows[i]["fac"], gain.get(i, 0), dw(i, 0x30), dw(i, 0x34), dw(i, 0x38), dw(i, 0x40),
                 dw(i, 0x44), dw(i, 0x48), dw(i, 0x4c), dw(i, 0x80), dw(i, 0x84), dw(i, 0x88),
                 bin(fb).count("1"), dw(i, 0x94), dw(i, 0x98), dw(i, 0xac), dw(i, 0xc4), dw(i, 0xcc),
                 dw(i, 0xd0), dw(i, 0xe0), dw(i, 0xe4), dw(i, 0xe8), dw(i, 0xec), dw(i, 0xf0), dw(i, 0xf4)))
