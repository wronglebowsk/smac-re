#!/usr/bin/env python3
"""Unit / base position snapshots out of live game memory (the C2 oracle).

Offsets verified in session 20 against a loaded Autosave 30 (`scripts/smac_records.py`):
  unit array  0x933278, 119 x 52 B   x @+0, y @+2, flags @+10, owner faction @+14
  base array  0x95da10,  n x 304 B   x @+0, y @+2, faction @+4, name @+19
  n = DAT_00985af4 (a BASE count, not a faction count)
Cross-check that ties them: four unit records sit on University Base's tile (20,50).

The count 119 is the record count this save loaded with; it is not read from a live
global (none found yet), so a different scenario can have a different number.

Usage:
  python3 scripts/smac_unitpos.py                 # table of units
  python3 scripts/smac_unitpos.py --json u_before.json
  python3 scripts/smac_unitpos.py --diff u_before.json    # who moved since that snapshot
"""
import argparse, json, os, struct, subprocess, sys

UNIT_BASE, UNIT_SIZE, UNIT_N = 0x933278, 52, 119
BASE_BASE, BASE_SIZE = 0x95DA10, 304


def pid():
    """pgrep -x, never -f: the Wine launcher's cmdline also contains terran.exe and
    reading ITS /proc/pid/mem gives a bogus EIO."""
    out = subprocess.run(["pgrep", "-x", "terran.exe"], capture_output=True, text=True).stdout.split()
    if not out:
        sys.exit("no terran.exe process (use `pgrep -x`, not -f)")
    return int(out[0])


class Mem:
    def __init__(self, p):
        self.f = open(f"/proc/{p}/mem", "rb", 0)     # mode 0: no ptrace needed

    def read(self, addr, n):
        self.f.seek(addr)
        b = self.f.read(n)
        if len(b) != n:
            raise OSError(f"short read at {addr:#x}: {len(b)}/{n} bytes")
        return b


def units(m, n=UNIT_N, raw=False):
    b = m.read(UNIT_BASE, UNIT_SIZE * n)
    out = []
    for i in range(n):
        r = b[i * UNIT_SIZE:(i + 1) * UNIT_SIZE]
        x, y = struct.unpack("<HH", r[0:4])
        flags = struct.unpack("<H", r[10:12])[0]
        owner = struct.unpack("<H", r[14:16])[0]
        rec = {"i": i, "x": x, "y": y, "flags": flags, "owner": owner}
        if raw:
            rec["hex"] = r.hex()
        out.append(rec)
    return out


def bases(m):
    n = struct.unpack("<I", m.read(0x985AF4, 4))[0]
    b = m.read(BASE_BASE, BASE_SIZE * n)
    out = []
    for i in range(n):
        r = b[i * BASE_SIZE:(i + 1) * BASE_SIZE]
        x, y = struct.unpack("<HH", r[0:4])
        name = r[19:51].split(b"\0")[0].decode("latin-1", "replace")
        out.append({"i": i, "x": x, "y": y, "faction": struct.unpack("<H", r[4:6])[0], "name": name})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=None, help="write the snapshot here")
    ap.add_argument("--diff", default=None, help="compare live memory against this snapshot")
    ap.add_argument("--bases", action="store_true", help="dump bases instead of units")
    ap.add_argument("--raw", action="store_true", help="include the full record bytes as hex")
    a = ap.parse_args()

    m = Mem(pid())
    live = bases(m) if a.bases else units(m, raw=a.raw)
    if a.json:
        with open(a.json, "w") as f:
            json.dump(live, f)
        print(f"wrote {len(live)} records -> {a.json}")
    if a.diff:
        old = json.load(open(a.diff))
        moved = [(o, n) for o, n in zip(old, live) if (o["x"], o["y"]) != (n["x"], n["y"])]
        dead = len(live) - len(old)
        print(f"records: was {len(old)} now {len(live)}" + (f" (delta {dead})" if dead else ""))
        print(f"moved: {len(moved)}")
        for o, n in moved[:40]:
            print(f"  unit {n['i']:3d}  ({o['x']:2d},{o['y']:2d}) -> ({n['x']:2d},{n['y']:2d})"
                  f"  owner {o['owner']}->{n['owner']}  flags {o['flags']:#x}->{n['flags']:#x}")
        if not a.json:
            return
    if not a.diff:
        for r in live[:40]:
            print(r)


if __name__ == "__main__":
    main()
