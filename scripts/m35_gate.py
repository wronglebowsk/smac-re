#!/usr/bin/env python3
"""M35: read the terraform PAYMENT-path gates straight out of live memory (no tracer).

Why: the TERRAPAY picker ("Cancel action. / Expend $NUM0 credits.") is reached inside
the terraform setter FUN_004d44d0 ONLY from the mode 0x10/0x11 (Raise/Lower Land) case
(shard_012.c case labels 0x4d5466..LAB_004d5496; asm-pinned below). Before the payment
path the setter must survive FUN_005a7520(player-flag table) — the TECH-UNLOCK check
(NOTUNTILTECH / HASFARM / HASROAD advisor) — and the payment path itself needs
cost != 0 and energy >= cost.

Statics this reads (all asm/pseudocode-pinned, see notes in NAMED.md M35 block):
  DAT_006938e8[mode*8 + domain]  -> required tech id (-1 = none, < -1 = never)
                                     (FUN_005a7520 shard_015.c:20594)
  0x985c1c + tech_id             -> byte of per-player "has this tech" bits
                                     bit (player & 0x1f)   (shard_015.c:20612)
  DAT_00985ac4 & 0x800000       -> kills raise/lower entirely (shard_015.c:20598)
  DAT_00985b44                  -> "current base" idx used by the 0xb<mode<0x13 bypass
  unit record +17               -> order byte; FUN_005a6330(unit,9,mode+4,-1,-1) != 0
                                     means "already this order" -> NO pay prompt
Usage: m35_gate.py [unit_idx]
"""
import os
import struct
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smac_play as P

TECH_REQ_TBL = 0x6938E8        # DAT_006938e8, stride 8 dwords per mode (land/sea slots)
TECH_BITS = 0x985C1C           # per-tech byte, bit = player & 0x1f
FLAG_DWORD = 0x985AC4          # DAT_00985ac4 game-mode flags (0x800000 = no raise/lower)
CUR_BASE = 0x985B44            # DAT_00985b44
UNIT_ARR, SEL, YEAR = 0x933278, 0x91B5BC, 0x985B00
TILE_BASE, ROW_PITCH, TILE_SZ = 0x92AE14, 40, 0x2c
ENERGY_G, ENERGY_STRIDE = 0x94D650, 0x82F
MODES = {"f Farm": 0, "SoilEnricher(remap)": 1, "Mine": 2, "Solar": 3, "Forest": 4,
         "Road": 5, "MagTube": 6, "Bunker": 7, "Airbase": 8, "Sensor": 9,
         "RemoveFungus(remap)": 0xa, "PlantFungus": 0xb, "Condenser": 0xc,
         "EchelonMirror": 0xd, "ThermalBorehole": 0xe, "Aquifer": 0xf,
         "RAISE LAND": 0x10, "LOWER LAND": 0x11, "LevelTerrain": 0x12}


def tile_addr(f, x, y):
    """0x92ae14 holds a POINTER to the tile array (`mov esi,[ds:92ae14]`, M35); indexing
    off 0x92ae14 itself (M33/M34) reads the pointer slot region, not tiles."""
    base = struct.unpack("<I", P.rd(f, TILE_BASE, 4))[0]
    return base + (ROW_PITCH * y + (x >> 1)) * TILE_SZ


def main():
    pid = int(subprocess.run("pgrep -x terran.exe | head -1", shell=True,
                             capture_output=True, text=True).stdout.split()[0])
    tracer = subprocess.run(f"grep TracerPid /proc/{pid}/status", shell=True,
                            capture_output=True, text=True).stdout
    print(f"pid={pid} {tracer.strip()}")
    _, f = P.mem()
    me = struct.unpack("<I", P.rd(f, 0x91B5B4, 4))[0]
    sel = struct.unpack("<i", P.rd(f, SEL, 4))[0]
    year = struct.unpack("<I", P.rd(f, YEAR, 4))[0]
    flags = struct.unpack("<I", P.rd(f, FLAG_DWORD, 4))[0]
    curbase = struct.unpack("<i", P.rd(f, CUR_BASE, 4))[0]
    energy = struct.unpack("<i", P.rd(f, ENERGY_G + me * ENERGY_STRIDE * 4, 4))[0]
    print(f"year={year} player={me} sel={sel} energy={energy} "
          f"DAT_00985ac4={flags:#x} (0x800000 bit: {bool(flags & 0x800000)}) "
          f"DAT_00985b44={curbase}")

    print("\n-- terraform mode gates (required tech id, tech bit for our player) --")
    for name, mode in MODES.items():
        # dword index = mode*8 + domain  (NOT a byte offset: the first version of this
        # script forgot the *4 and printed garbage — see M35 pitfall)
        req = [struct.unpack("<i", P.rd(f, TECH_REQ_TBL + (mode * 8 + d) * 4, 4))[0]
               for d in (0, 1)]
        bits = []
        for r in req:
            if 0 <= r < 0x58:
                b = P.rd(f, TECH_BITS + r, 1)[0]
                bits.append(bool(b >> (me & 0x1f) & 1))
            else:
                bits.append(None)
        print(f"  mode {mode:#04x} {name:22s} req_tech(land,sea)={req} unlocked={bits}")

    units = P.rd(f, UNIT_ARR, 300 * 52)
    classes = P.rd(f, 0x98ADB2, 1024 * 52)
    print("\n-- our units (order byte matters: FUN_005a6330(unit,9,mode+4,-1,-1)) --")
    for i in range(300):
        d = units[i * 52:(i + 1) * 52]
        if d[14] == 0xFF:
            continue
        typ = struct.unpack("<H", d[10:12])[0]
        cls = classes[typ * 52] & 0xFF
        if d[14] != me:
            continue
        x, y = struct.unpack("<H", d[0:2])[0], struct.unpack("<H", d[2:4])[0]
        ta, t = tile_addr(f, x, y), None
        t = P.rd(f, ta, TILE_SZ)
        height = t[0] >> 5
        print(f"  rec{i:3d} cls={cls} ({x},{y}) order={d[17]:#04x} mpused={d[40]} "
              f"tile+0={t[0]:#04x} elev={height} tile+8={struct.unpack('<I', t[8:12])[0]:#010x}")


if __name__ == "__main__":
    main()
