#!/usr/bin/env python3
"""Dump the 304-byte base records at 0x95da10 (count DAT_00985af4)."""
import struct, subprocess, sys, json

def pid():
    return int(subprocess.run(["pgrep","-x","terran.exe"],capture_output=True,text=True).stdout.split()[0])

def main():
    p = pid(); f = open(f"/proc/{p}/mem","rb",0)
    def rd(a,n):
        f.seek(a); return f.read(n)
    n = struct.unpack("<I", rd(0x985AF4,4))[0]
    want = int(sys.argv[1]) if len(sys.argv)>1 else None
    out=[]
    for i in range(n):
        b = rd(0x95DA10 + i*304, 304)
        name = b[19:19+40].split(b"\0")[0].decode("latin-1", "replace")
        x, y = struct.unpack("<hh", b[0:4])
        fac = struct.unpack("<i", b[4:8])[0]
        rec = {"i": i, "name": name, "x": x, "y": y, "fac": fac}
        if want is None or fac == want:
            out.append(rec)
    if len(sys.argv)>2 and sys.argv[2]=="fields":
        i = out[0]["i"]; b = rd(0x95DA10 + i*304, 304)
        print(f"base {i} {out[0]['name']!r} raw u16x24:")
        for off in range(0, 240, 24):
            print(f"  +{off:3d}: " + " ".join(f"{v:5d}" for v in struct.unpack("<12H", b[off:off+24])))
    print(json.dumps(out, indent=1))
main()
