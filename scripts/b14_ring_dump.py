#!/usr/bin/env python3
# B14: dump the hub scan ring tables (FUN_0055f650's 25-entry candidate ring,
# .rdata 0x67850c dx / 0x678990 dy) from the terran.exe FILE IMAGE into
# evidence/b14_ring_table.txt, so sim/podscan.py's literal ring constants have
# a recorded, file-readable provenance (the spine forbids sim/ loading the
# game binary). Address provenance: scripts/m291_pod_scan.py G5.
# Backslash-free ship form: byte literals are bytes([...]) lists (s238 rule).
import struct, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, "terran.exe")
d = open(EXE, "rb").read()
e = struct.unpack_from("<I", d, 0x3c)[0]
nsec = struct.unpack_from("<H", d, e + 6)[0]
optsz = struct.unpack_from("<H", d, e + 20)[0]
base = struct.unpack_from("<I", d, e + 52)[0]
o = e + 24 + optsz
secs = []
for i in range(nsec):
    name = d[o:o + 8].rstrip(bytes([0])).decode("latin1")
    vsize = struct.unpack_from("<I", d, o + 8)[0]
    vaddr = struct.unpack_from("<I", d, o + 12)[0]
    rsize = struct.unpack_from("<I", d, o + 16)[0]
    raddr = struct.unpack_from("<I", d, o + 20)[0]
    secs.append((name, base + vaddr, vsize, raddr, rsize))
    o += 40
def fbytes(va, n):
    for (name, sva, vsz, ra, rsz) in secs:
        if sva <= va < sva + vsz:
            off = va - sva
            if rsz and off + n <= rsz:
                return d[ra + off:ra + off + n], name
    raise SystemExit("no file bytes for " + hex(va))
bdx, sx = fbytes(0x67850c, 100)
bdy, sy = fbytes(0x678990, 100)
dx = struct.unpack("<25i", bdx)
dy = struct.unpack("<25i", bdy)
out = os.path.join(ROOT, "evidence", "b14_ring_table.txt")
NL = chr(10)
with open(out, "w") as f:
    f.write("# B14 ring-table provenance: terran.exe FILE IMAGE bytes, sections " + sx + "/" + sy + NL)
    f.write("# tables 0x67850c (dx) / 0x678990 (dy), FUN_0055f650 candidate ring" + NL)
    f.write("# idx dx dy" + NL)
    for i in range(25):
        f.write(str(i) + " " + str(dx[i]) + " " + str(dy[i]) + NL)
print("wrote " + out)
print("dx " + ",".join(str(v) for v in dx))
print("dy " + ",".join(str(v) for v in dy))
