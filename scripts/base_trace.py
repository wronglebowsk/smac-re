#!/usr/bin/env python3
"""Snapshot the 304-byte base records once per turn while the driver advances turns.

Record layout so far (SAVE_FORMAT.md, corrected in M30/M31):
  +0  int16 x      +2 int16 y      +4 u8 flag     +5 u8 faction
  +19 char[40] name
Count = u32 at 0x985AF4, array at 0x95DA10.

Usage:
  python3 scripts/base_trace.py --turns 10 [--base 0] [--interval 0.2]
Writes evidence/m31_bases.json (per-year u16 field table) and evidence/m31_bases_<year>.bin
(whole array), then prints which u16 offsets changed for the tracked base.
"""
import argparse, json, os, struct, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVID = os.path.join(ROOT, "evidence")
YEAR, NB, ARR = 0x985B00, 0x985AF4, 0x95DA10
STRIDE = 304


def pid():
    out = subprocess.run(["pgrep", "-x", "terran.exe"], capture_output=True, text=True).stdout.split()
    return int(out[0]) if out else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--turns", type=int, default=10)
    ap.add_argument("--base", type=int, default=0)
    ap.add_argument("--interval", type=float, default=0.2)
    ap.add_argument("--timeout", type=float, default=100)
    a = ap.parse_args()

    p = pid()
    if not p:
        sys.exit("no terran.exe")
    f = open(f"/proc/{p}/mem", "rb", 0)

    def u32(addr):
        f.seek(addr); return struct.unpack("<I", f.read(4))[0]

    def snap():
        n = u32(NB)
        f.seek(ARR); buf = f.read(n * STRIDE)
        return n, buf

    os.makedirs(EVID, exist_ok=True)
    drv = subprocess.Popen([sys.executable, os.path.join(ROOT, "scripts", "smac_play.py"),
                            "--turns", str(a.turns), "--timeout", str(a.timeout)],
                           cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    frames = {}
    y = u32(YEAR)
    n, buf = snap()
    frames[y] = (n, buf)
    open(os.path.join(EVID, f"m31_bases_{y}.bin"), "wb").write(buf)
    while drv.poll() is None:
        yy = u32(YEAR)
        if yy != y:
            n, buf = snap()
            frames[yy] = (n, buf)
            open(os.path.join(EVID, f"m31_bases_{yy}.bin"), "wb").write(buf)
            y = yy
        time.sleep(a.interval)
    log = drv.stdout.read(); drv.wait()
    print(log.rstrip())

    years = sorted(frames)
    idx = a.base
    table = {}
    for yy in years:
        n, buf = frames[yy]
        if idx >= n:
            continue
        b = buf[idx * STRIDE:(idx + 1) * STRIDE]
        name = b[19:59].split(b"\0")[0].decode("latin-1", "replace")
        table[yy] = {"name": name, "x": struct.unpack("<h", b[0:2])[0],
                     "y": struct.unpack("<h", b[2:4])[0], "fac": b[5],
                     "u16": list(struct.unpack("<152H", b[:304]))}
    json.dump(table, open(os.path.join(EVID, "m31_bases.json"), "w"), indent=1)

    print(f"\nbase {idx} over {len(years)} years ({years[0]}..{years[-1]})")
    changed = []
    for off in range(152):
        vals = [table[yy]["u16"][off] for yy in years if yy in table]
        if len(set(vals)) > 1:
            changed.append((off, vals))
    for off, vals in changed:
        print(f"  +{off*2:3d} u16: " + " ".join(f"{v:6d}" for v in vals))
    print(f"{len(changed)} of 152 u16 lanes changed")


if __name__ == "__main__":
    main()
