#!/usr/bin/env python3
"""M245/M246/M247: what the save tail's last three legs are (static + one /proc read).

M245  the 216-B leg = 9 rows x 6 dwords of per-window map-view state. The codec's loop
      (shard_015.c) walks the 8 pointers DAT_007cdecc..DAT_007cdee8 (bound `< 0x7cdeec`) and
      then the inline object &DAT_008cda4c; FUN_00596620 moves the six fields
      +0x1dd78 +0x1dd74 +0x1dd70 +0x1dd98 +0x1dd9c +0x1dda0 of each. Read back live.
M246  the final 4 B = the timeGetTime() dword FUN_00597ce0 writes AFTER the codec returns.
M247  the region map's row stride: the only two element accessors of DAT_0092ae18 index with
      DAT_0092ad9c>>1 while the malloc/file length is ((DAT_0092ad9c+1)/2)*Rh.

  python3 scripts/m245_tail_legs_census.py   -> evidence/m245_tail_legs.txt, PASS line, rc
"""
import os
import struct
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVE_DIR = os.path.join(ROOT, "programs", "saves")
SHARD14 = os.path.join(ROOT, "ghidra_out", "shard_014.c")
SHARD15 = os.path.join(ROOT, "ghidra_out", "shard_015.c")
EVID = os.path.join(ROOT, "evidence", "m245_tail_legs.txt")
GAME_PID = 0  # filled by proc_base()

OFFS = [0x1dd78, 0x1dd74, 0x1dd70, 0x1dd98, 0x1dd9c, 0x1dda0]


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def saves():
    return sorted(subprocess.run(["find", SAVE_DIR, "-name", "*.SAV"], capture_output=True,
                                 text=True).stdout.split())


def shard(path):
    return open(path, errors="replace").read().splitlines()


def g1_codec_leg():
    return False, "TODO"


def g2_live_readback():
    return False, "TODO"


def g3_tail_timestamp():
    return False, "TODO"


def g4_stride_sites():
    return False, "TODO"


def g5_residue():
    return False, "TODO"


GATES = [("G1 216-B leg = 9 rows x 6 view fields (codec loop + FUN_00596620 offsets)", g1_codec_leg),
         ("G2 live view objects == one save's 216 B byte for byte", g2_live_readback),
         ("G3 trailing dword == timeGetTime written after the codec", g3_tail_timestamp),
         ("G4 every DAT_0092ae18 accessor uses Rw>>1, none uses (Rw+1)/2", g4_stride_sites),
         ("G5 builder write set = 0..78 at 64x64; 79..90 are residue in 17/17 saves", g5_residue)]


def main():
    lines, ok = [], 0
    for name, fn in GATES:
        try:
            good, detail = fn()
        except Exception as exc:  # a broken gate is a failing gate, never a crash
            good, detail = False, "EXC %s: %s" % (type(exc).__name__, exc)
        ok += 1 if good else 0
        lines.append("%s %s\n    %s" % ("PASS" if good else "FAIL", name, detail))
        print(lines[-1])
    lines.append("\nSUMMARY %d/%d gates on %d saves\n" % (ok, len(GATES), len(saves())))
    os.makedirs(os.path.dirname(EVID), exist_ok=True)
    with open(EVID, "w") as f:
        f.write("\n".join(lines))
    print("SUMMARY %d/%d" % (ok, len(GATES)))
    if ok == len(GATES):
        print("PASS M245: %d/%d gates" % (ok, len(GATES)))
    return 0 if ok == len(GATES) else 1


if __name__ == "__main__":
    sys.exit(main())
