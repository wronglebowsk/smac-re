#!/usr/bin/env python3
"""m53q_livelock.py — detect (and optionally repair) the unit-chain livelock (M53Q0).

The end-of-turn unit walkers
  FUN_005ab130  loop 0x5ab223-37, reads unit+50
  FUN_005a6330  loop 0x5a6945-55, reads unit+48
advance by an INDEX field (13*index*4 = the 52-byte unit stride) and exit only on a
NEGATIVE link. The two fields are per-tile prev/next indices written by
  0x5ab240  unit_remove_from_map : sentinel 0xffff + compaction
  0x5ab320  unit_set_position    : +50 = 0xffff, +48 = FUN_005ab130(x, y)
so a stale index (e.g. left behind by compaction after a unit dies) can make record i
point at itself and the walk never terminates: the game pegs a core with
turn_flags bit 1 set and the driver reports STUCK with no pane on screen.

    python3 scripts/m53q_livelock.py            # census only, read-only
    python3 scripts/m53q_livelock.py --fix      # break detected cycles (0xFFFF, read back)

Background / cited evidence: evidence/m53p_livelock_findings.md (session 68).
"""
import argparse
import struct
import subprocess
import sys

UNIT_BASE = 0x933278
STRIDE = 52
N_UNITS = 0x985af0
TURN_FLAGS = 0x985ae8
YEAR = 0x985b00
CUR = 0x985dcc
LINK48, LINK50 = 48, 50
FIXED = 0xFFFF


def find_pid():
    out = subprocess.run(["pgrep", "-x", "terran.exe"], capture_output=True, text=True).stdout.split()
    if not out:
        sys.exit("terran.exe is not running")
    return int(out[0])


def tracer_pid(pid):
    try:
        with open(f"/proc/{pid}/status") as fh:
            for ln in fh:
                if ln.startswith("TracerPid:"):
                    return int(ln.split()[1])
    except OSError:
        pass
    return -1


def read(mem, off, n):
    mem.seek(off)
    b = mem.read(n)
    if len(b) != n:
        raise SystemExit(f"short read at {off:#x}")
    return b


def u32(mem, off):
    return struct.unpack("<I", read(mem, off, 4))[0]


def links(mem, n):
    buf = read(mem, UNIT_BASE, n * STRIDE)
    l48, l50 = [], []
    for i in range(n):
        o = i * STRIDE
        l48.append(struct.unpack_from("<h", buf, o + LINK48)[0])
        l50.append(struct.unpack_from("<h", buf, o + LINK50)[0])
    return l48, l50


def census(link):
    n = len(link)
    terms = sum(1 for x in link if x < 0)
    selfl = [i for i, x in enumerate(link) if x == i]
    outofrange = [i for i, x in enumerate(link) if x >= n]
    cycles, state = [], [0] * n
    for start in range(n):
        if state[start]:
            continue
        path, cur = [], start
        while 0 <= cur < n and state[cur] == 0:
            state[cur] = 1
            path.append(cur)
            nxt = link[cur]
            cur = -1 if nxt < 0 else nxt
        if 0 <= cur < n and state[cur] == 1:
            cycles.append(path[path.index(cur):])
        for x in path:
            state[x] = 2
    return terms, selfl, outofrange, cycles


def poke(mem, idx, off):
    addr = UNIT_BASE + idx * STRIDE + off
    mem.seek(addr)
    mem.write(struct.pack("<H", FIXED))
    mem.flush()
    mem.seek(addr)
    return mem.read(2) == b"\xff\xff"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pid", type=int)
    ap.add_argument("--fix", action="store_true", help="break detected cycles (writes 0xFFFF)")
    args = ap.parse_args()
    pid = args.pid or find_pid()
    tp = tracer_pid(pid)
    if args.fix and tp != 0:
        sys.exit(f"refusing --fix: TracerPid={tp} (attach would race a debugger)")
    with open(f"/proc/{pid}/mem", "rb") as mem:
        year, cur, tf = u32(mem, YEAR), u32(mem, CUR), u32(mem, TURN_FLAGS)
        n = u32(mem, N_UNITS)
        if not 0 < n < 4096:
            sys.exit(f"implausible unit count {n} at {N_UNITS:#x}")
        l48, l50 = links(mem, n)
    print(f"pid {pid} year {year} cur {cur} units {n} turn_flags 0x{tf:08x} "
          f"(end-turn-in-flight bit: {1 if tf & 2 else 0})")
    bad = 0
    for name, link in (("+48", l48), ("+50", l50)):
        terms, selfl, oor, cycles = census(link)
        print(f"  {name}: {terms} terminator(s), {len(selfl)} self-link(s)"
              f"{' ' + str(selfl[:6]) if selfl else ''}, "
              f"{len(oor)} out-of-range, {len(cycles)} cycle(s)"
              f"{' ' + str([c[:6] for c in cycles]) if cycles else ''}")
        bad += len(cycles) + (0 if cycles else len(selfl))
    if not bad:
        print("verdict: CLEAN" + ("" if tf & 2 else " (turn_flags bit 1 already clear)"))
        return 0
    print(f"verdict: LIVELOCK — {bad} broken chain(s); "
          f"{'repairing' if args.fix else 're-run with --fix to repair'}")
    if not args.fix:
        return 2
    with open(f"/proc/{pid}/mem", "r+b") as mem:
        for name, off, link in (("+48", LINK48, l48), ("+50", LINK50, l50)):
            _, selfl, _, cycles = census(link)
            for cyc in cycles:
                j = cyc[-1]
                ok = poke(mem, j, off)
                print(f"  poke {name} unit {j} -> 0xFFFF: {'OK' if ok else 'FAILED'}")
    with open(f"/proc/{pid}/mem", "rb") as mem:
        l48, l50 = links(mem, u32(mem, N_UNITS))
        tf = u32(mem, TURN_FLAGS)
    for name, link in (("+48", l48), ("+50", l50)):
        print(f"  post {name}: {len(census(link)[3])} cycle(s)")
    print(f"post turn_flags 0x{tf:08x}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
