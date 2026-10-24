#!/usr/bin/env python3
"""M53l: read-only snapshot incl. production-input fields.
Columns: idx name fac pop f30 f3c f40 f44 f48 pending head f94 f98 fbc fc0 fcc fd0 fec fe0 ff0
Header: # year cur nb era mask pid."""
import struct, subprocess

p = int(subprocess.run(["pgrep","-x","terran.exe"],capture_output=True,text=True).stdout.split()[0])
f = open(f"/proc/{p}/mem","rb",0)
def rd(a,n):
    f.seek(a); return f.read(n)
year = struct.unpack("<I", rd(0x985b00,4))[0]
cur  = struct.unpack("<I", rd(0x985dcc,4))[0]
nb   = struct.unpack("<I", rd(0x985af4,4))[0]
era  = struct.unpack("<I", rd(0x985aec,4))[0]
mask = struct.unpack("<I", rd(0x985b10,4))[0]
print(f"# year={year} cur={cur} nb={nb} era={era} mask={mask:#x} pid={p}")
print("idx\tname\tfac\tpop\tf30\tf3c\tf40\tf44\tf48\tpending\thead\tf94\tf98\tfbc\tfc0\tfcc\tfd0\tfec\tfe0\tff0")
for i in range(nb):
    b = rd(0x95da10 + i*304, 304)
    name = b[19:59].split(b"\0")[0].decode("latin-1","replace")
    fac, pop = struct.unpack("<HH", b[4:8])
    a = struct.unpack("<9I", b[0x30:0x30+36])   # 30 34 38 3c 40 44 48 4c 50
    d = struct.unpack("<4I", b[0x94:0x94+16])   # 94 98 9c a0
    e = struct.unpack("<6I", b[0xbc:0xbc+24])   # bc c0 cc d0 e0 ec
    g = struct.unpack("<I",  b[0xf0:0xf4])      # f0
    print(f"{i}\t{name}\t{fac}\t{pop}\t{a[0]}\t{a[3]}\t{a[4]}\t{a[5]}\t{a[6]}\t{a[7]}\t{a[8]}\t{d[0]}\t{d[1]}\t{e[0]}\t{e[1]}\t{e[2]}\t{e[3]}\t{e[5]}\t{e[4]}\t{g[0]}")
