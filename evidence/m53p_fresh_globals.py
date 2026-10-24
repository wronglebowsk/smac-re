#!/usr/bin/env python3
"""Read-only: DAT_008f0d30, 21 dwords @0x8f0ccc, DAT_0068cbb0. Prints one line each."""
import struct, subprocess, sys
p = int(subprocess.run(["pgrep", "-x", "terran.exe"], capture_output=True, text=True).stdout.split()[0])
with open(f"/proc/{p}/mem", "rb") as f:
    def rd(a, n):
        f.seek(a); return f.read(n)
    d30 = struct.unpack("<I", rd(0x8f0d30, 4))[0]
    tbl = struct.unpack("<21I", rd(0x8f0ccc, 84))
    bidx = struct.unpack("<I", rd(0x68cbb0, 4))[0]
print("pid", p)
print("DAT_008f0d30 = 0x%x (%d)" % (d30, d30))
print("8f0ccc[0..20] =", " ".join("0x%08x" % v for v in tbl))
print("DAT_0068cbb0 =", bidx)
