#!/usr/bin/env python3
"""M26: read / poke the SELECTED unit record straight through /proc/<pid>/mem (no tracer).

Usage:
  scripts/m26_poke.py show
  scripts/m26_poke.py poke [sel|<idx>] order=0x18 dx=43 dy=11 flags4=0 mpused=0 ...
"""
import struct
import subprocess
import sys

UNIT = 0x933278
SEL = 0x91b5BC
FIELDS = {  # name -> (offset, struct fmt, width)
    "x": (0, "<h"), "y": (2, "<h"), "flags4": (4, "<I"), "type": (10, "<H"),
    "owner": (14, "<B"), "order": (17, "<B"), "nlegs": (18, "<B"), "leg": (19, "<B"),
    "dx": (20, "<h"), "dy": (28, "<h"), "mpused": (40, "<B"), "dir": (41, "<B"),
    "prev": (48, "<h"), "next": (50, "<h"),
}


def pid():
    return int(subprocess.run(["pgrep", "-x", "terran.exe"], capture_output=True,
                              text=True).stdout.split()[0])


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "show"
    f = open(f"/proc/{pid()}/mem", "r+b", 0)
    f.seek(SEL)
    sel = struct.unpack("<I", f.read(4))[0]

    def rec(idx):
        f.seek(UNIT + idx * 52)
        return f.read(52)

    def dump(idx, label):
        d = rec(idx)
        out = [f"{label} rec{idx}"]
        for name, (off, fmt) in FIELDS.items():
            w = struct.calcsize(fmt)
            out.append(f"{name}={struct.unpack(fmt, d[off:off+w])[0]}")
        print(" ".join(out), flush=True)

    if mode == "show":
        for i in {sel, 117, 118, 119}:
            dump(i, "sel" if i == sel else "  ")
        return
    # poke
    args = sys.argv[2:]
    idx = sel
    if args and not args[0].startswith(("order", "dx", "dy", "flags", "mp", "leg", "nlegs", "dir")):
        idx = sel if args[0] == "sel" else int(args[0])
        args = args[1:]
    base = UNIT + idx * 52
    for a in args:
        name, val = a.split("=")
        off, fmt = FIELDS[name]
        v = int(val, 0)
        f.seek(base + off)
        f.write(struct.pack(fmt, v))
        print(f"poked rec{idx} +{off} {name}={v}", flush=True)
    f.flush()
    dump(idx, "after")


if __name__ == "__main__":
    main()
