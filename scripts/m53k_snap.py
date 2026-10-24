#!/usr/bin/env python3
"""M53k: read-only snapshot of per-base economy fields -> TSV on stdout.
Fields (dword offsets in base record): 0x30 0x3c 0x40 0x44 0x4c 0x50 0x98 0xcc 0xd0.
Name at record+19 (40B). Header line: # year cur nb pid."""
import struct, subprocess, sys

p = int(subprocess.run(["pgrep","-x","terran.exe"],capture_output=True,text=True).stdout.split()[0])
f = open(f"/proc/{p}/mem","rb",0)
def rd(a,n):
    f.seek(a); return f.read(n)
year = struct.unpack("<I", rd(0x985b00,4))[0]
cur  = struct.unpack("<I", rd(0x985dcc,4))[0]
nb   = struct.unpack("<I", rd(0x985af4,4))[0]
print(f"# year={year} cur={cur} nb={nb} pid={p}")
print("idx\tname\tfac\tx\tpop\tf30\tf3c\tf40\tf44\tpending\thead\tf98\tfcc\tfd0")
for i in range(nb):
    b = rd(0x95da10 + i*304, 304)
    name = b[19:59].split(b"\0")[0].decode("latin-1","replace")
    x = struct.unpack("<H", b[0:2])[0]
    fac, pop = struct.unpack("<HH", b[4:8])
    d = struct.unpack("<9I", b[0x30:0x30+36])  # 0x30,0x34,0x38,0x3c,0x40,0x44,0x48,0x4c,0x50
    d2 = struct.unpack("<3I", b[0x98:0x98+12])  # 0x98,0x9c,0xa0
    d3 = struct.unpack("<2I", b[0xcc:0xcc+8])   # 0xcc,0xd0
    print(f"{i}\t{name}\t{fac}\t{x}\t{pop}\t{d[0]}\t{d[3]}\t{d[4]}\t{d[5]}\t{d[7]}\t{d[8]}\t{d2[0]}\t{d3[0]}\t{d3[1]}")
