#!/usr/bin/env python3
"""M51a read-only base-record scanner: identity is by NAME, not by index.

The base array slides (records compact when bases are destroyed) and the owner byte
changes (captures), so a bare index or a bare owner test is not a stable identity
anchor. This dumps every record with the fields the M51a question turns on:
idx, address, owner byte, NAME, +0x38 (flag const), +0x3c, +0x40, +0xd0, +0xcc, pop.

Usage: python3 scripts/m51a_scan.py [--name-sub Climactic] [--owner 3]
"""
import argparse, os, struct, subprocess
from collections import Counter

BASE_ARR, STRIDE = 0x95da10, 0x130


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name-sub", default="")
    ap.add_argument("--owner", type=int, default=-1)
    ap.add_argument("--pid", type=int, default=0)
    a = ap.parse_args()
    pid = a.pid or int(subprocess.run(["pgrep", "-x", "terran.exe"],
                                      capture_output=True, text=True).stdout.split()[0])
    tracer = int(subprocess.run(["grep", "TracerPid", f"/proc/{pid}/status"],
                                capture_output=True, text=True).stdout.split()[-1])
    ro = os.open(f"/proc/{pid}/mem", os.O_RDONLY)

    def i32(addr):
        return struct.unpack("<i", os.pread(ro, 4, addr))[0]

    nb = i32(0x985af4)
    blob = os.pread(ro, nb * STRIDE, BASE_ARR)
    print(f"pid={pid} tracer={tracer} year={i32(0x985b00)} turn={i32(0x985afc)} "
          f"cur={i32(0x985dcc)} nb={nb} mask={i32(0x985b10):#x}")
    rows = []
    for i in range(nb):
        r = blob[i * STRIDE:(i + 1) * STRIDE]
        g = lambda o: struct.unpack("<i", r[o:o + 4])[0]
        name = r[19:39].split(b"\0")[0].decode("latin1", "replace")
        rows.append(dict(idx=i, addr=BASE_ARR + i * STRIDE, owner=r[4], name=name,
                         f38=g(0x38), f3c=g(0x3c), min40=g(0x40), d0=g(0xd0), cc=g(0xcc),
                         pop=r[6], fc=g(0xfc), q50=g(0x50), f30=g(0x30)))
    hdr = ("idx addr      own name                    f38        f3c  min40   d0 "
           "cc  pop  fc  q50  f30")
    print(hdr)
    for row in rows:
        if a.owner >= 0 and row["owner"] != a.owner:
            continue
        if a.name_sub and a.name_sub not in row["name"]:
            continue
        print(f"{row['idx']:3d} {row['addr']:#09x} {row['owner']:3d} {row['name']:<24s} "
              f"{row['f38']:#010x} {row['f3c']:5d} {row['min40']:6d} {row['d0']:5d} "
              f"{row['cc']:4d} {row['pop']:4d} {row['fc']:4d} {row['q50']:5d} {row['f30']:#x}")
    print("owner histogram:", dict(Counter(r["owner"] for r in rows)))
    names = Counter(r["name"] for r in rows)
    dupes = {n: c for n, c in names.items() if c > 1}
    print("duplicate names:", dupes if dupes else "none")


if __name__ == "__main__":
    main()
