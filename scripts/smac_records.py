"""Read SMAC runtime globals/arrays out of /proc/<pid>/mem and look for coordinate pairs.

The save-layout trace gave the destination addresses of two record families:
  0x933278  n x 52 B   (n from an unknown count)
  0x95da10  m x 304 B  (m = DAT_00985af4, which smac_state.py mislabels as 'n_factions')
If a record family is units or bases, its records should contain small u16 pairs (< map width).
"""
import re
import struct
import subprocess

# pgrep -x: the launcher (`wine explorer ... terran.exe`) also matches -f and reading ITS
# /proc/pid/mem gives a spurious EIO.
PID = int(subprocess.run(["pgrep", "-x", "terran.exe"], capture_output=True, text=True).stdout.split()[0])
MEM = open(f"/proc/{PID}/mem", "rb", 0)
MAPS = open(f"/proc/{PID}/maps").read()


def read(addr, n):
    MEM.seek(addr)
    return MEM.read(n)


def u16s(b):
    return struct.unpack(f"<{len(b)//2}H", b[:len(b)//2*2])


def scan(addr, rec, count, label, limit=80):
    b = read(addr, rec * count)
    print(f"=== {label}: {count} x {rec} B at {addr:#x}")
    for i in range(min(count, 6)):
        r = b[i*rec:(i+1)*rec]
        vals = u16s(r)
        small = [j for j, v in enumerate(vals) if 0 < v < limit and (j % 2 == 0)]
        print(f"  [{i:2d}] {r[:24].hex(' ')}  small-u16-at: {small[:10]}")
    return b


if __name__ == "__main__":
    year = struct.unpack("<I", read(0x985B00, 4))[0]
    cnt304 = struct.unpack("<I", read(0x985AF4, 4))[0]
    print(f"pid {PID}  year {year}  DAT_00985af4 = {cnt304}")
    scan(0x933278, 52, 119, "52-byte records")
    scan(0x95DA10, 304, cnt304, "304-byte records")
