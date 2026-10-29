#!/usr/bin/env python3
"""M108 — who SETS the counted legs of the save chunk map, and a RETRACTION of M107's gate claim.

Reads the LIVE box only (`/proc/<pid>/mem`, no gdb, no poke, no relaunch): the load is already in
memory, so the two count globals the loader sized its arrays with are readable as loaded values.

    python3 scripts/m108_count_sources.py --tag m108c1     # gates -> evidence/<tag>.log

The counted legs (from M107's leg census, scripts/m107_chunkmap.py):
    0x597319  size = edx           = 52 * [0x985af0]  -> 0x933278
    0x59738b  size = eax           = 48 * [0x985af0]  -> malloc
    0x59751f  size = eax           = 304 * [0x985af4] -> 0x95da10
    0x5970e4  size = eax           = the u32 count prefix read just before it
    0x5979f8  size = edx           = the tail

Gates:
  G1  a live terran.exe at the HUD with m54b_clean loaded (year 2150 at header+0x54)
  G2  [0x985af0] and [0x985af4] hold the LIVE counts (printed), and the three leg sizes follow
  G3  static census: the two fields have 5 and 6 store sites in .text, and the LOAD-family pair
      0x598470/0x598476 is the one that lands them with the count from the record tables
  G4  RETRACTION: [0x985dbc] >= 3 live, so the STATIC 0x105e0 block-A leg runs — the same leg the
      r7 strace proves (a direct read at 0x94e104 of 0xf000 inside 0x94d430+0x105e0). M107's
      "u32@772 < 3 -> the malloc'd 0xe5e0 leg" is withdrawn: 0x985dbc is NOT file offset 772.
  G5  the closure arithmetic is printed exactly and the deficit is NOT zero (that is the finding)
  G6  read-back: the 304-byte array at 0x95da10 really holds [0x985af4] base records with names
"""
import argparse
import os
import re
import struct
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
HDR = 0x985ab8
CNT_U, CNT_B = 0x985af0, 0x985af4
GATE = 0x985dbc
SRC_U, SRC_B = 0x92a38c, 0x92ae14
BASES = 0x95da10
BASESZ = 304
SAV = "m54b_clean.SAV"


def d32(fd, addr):
    return struct.unpack("<I", os.pread(fd, 4, addr))[0]


def live_pid():
    out = subprocess.run("ps -eo pid,cmd | grep -E '^ *[0-9]+ .*terran\\.exe$'",
                         shell=True, capture_output=True, text=True).stdout
    return [int(l.split()[0]) for l in out.splitlines() if l.strip()]


def store_sites(field):
    """Every store instruction writing the absolute field, from the objdump of .text."""
    pat = re.compile(r"mov\s+(?:DWORD|WORD|BYTE) PTR ds:0x%x," % field)
    hits = []
    with open(TEXT, errors="replace") as f:
        for line in f:
            if "ds:0x%x," % field not in line:
                continue
            m = re.match(r"\s*([0-9a-f]{6,8}):\s", line)
            if m and pat.search(line):
                parts = line.rstrip("\n").split("\t")
                hits.append((int(m.group(1), 16), parts[2].strip() if len(parts) > 2 else ""))
    return hits


def prologue_starts():
    """function starts by the push ebp / mov ebp,esp prologue (ROADMAP: matched Ghidra on known pairs)."""
    starts, prev = [], None
    with open(TEXT, errors="replace") as f:
        for line in f:
            m = re.match(r"\s*([0-9a-f]{6,8}):\s", line)
            if not m:
                continue
            a = int(m.group(1), 16)
            parts = line.rstrip("\n").split("\t")
            asm = parts[2].strip() if len(parts) > 2 else ""
            if asm.startswith("push   ebp") or asm == "push ebp":
                prev = a
            elif prev is not None and re.match(r"mov\s+ebp,esp", asm) and a == prev + 1:
                starts.append(prev)
                prev = None
            else:
                prev = None
    return starts


def containing(starts, pc):
    lo = [s for s in starts if s <= pc]
    return lo[-1] if lo else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="")
    a = ap.parse_args()
    gates = []

    pids = live_pid()
    if not pids:
        print("no live terran.exe — refusing to measure nothing")
        return 2
    pid = pids[-1]
    fd = os.open("/proc/%d/mem" % pid, os.O_RDONLY)
    try:
        year = struct.unpack("<H", os.pread(fd, 2, HDR + 0x54))[0]
        nu, nb = d32(fd, CNT_U), d32(fd, CNT_B)
        gate, src_u, src_b = d32(fd, GATE), d32(fd, SRC_U), d32(fd, SRC_B)
        recs = []
        for i in range(min(nb, 64)):
            base = BASES + i * BASESZ
            name = b""
            for k in range(28):
                c = os.pread(fd, 1, base + 19 + k)
                if c == b"\x00":
                    break
                name += c
            recs.append(name)
        cnts = [d32(fd, 0x927a9c + f * 1436) for f in range(8)]
    finally:
        os.close(fd)

    gates.append(("G1", f"terran.exe pid {pid}; record-block counts {cnts} (header-year field "
                        f"{year} is not the mission year in memory) = the m54b_clean image",
                  cnts == [0, 6, 5, 4, 3, 4, 5, 3]))

    s52, s48, s304 = 52 * nu, 48 * nu, BASESZ * nb
    gates.append(("G2", f"[0x985af0]={nu} units -> 52n={s52:,} 48p={s48:,}; "
                        f"[0x985af4]={nb} bases -> 304m={s304:,}",
                  nu > 0 and nb > 0))

    su, sb = store_sites(CNT_U), store_sites(CNT_B)
    starts = prologue_starts()
    fn = containing(starts, 0x598476)
    pair_ok = any(p == 0x598476 for p, _ in su) and any(p == 0x598470 for p, _ in sb)
    where = ("0x%x" % fn) if fn is not None else "?"
    gates.append(("G3", f"{len(su)} stores to 0x985af0, {len(sb)} to 0x985af4; the load pair "
                        f"0x598470/0x598476 (6 B apart, one basic block) sits in the function "
                        f"starting {where}",
                  len(su) == 5 and len(sb) == 6 and pair_ok and fn == 0x598340))

    gates.append(("G4", f"RETRACT M107: [0x985dbc]={gate} >= 3 -> the STATIC 0x105e0 block-A leg "
                        f"runs (r7 strace: direct read 0x94e104+0xf000 inside 0x94d430+0x105e0)",
                  gate >= 3))

    file_size = os.path.getsize(os.path.join(ROOT, "programs/saves", SAV))
    fixed = 204504            # every immediate leg (M107 G6)
    resid = file_size - fixed
    counted = s52 + s48 + s304
    gates.append(("G5", f"m54b_clean {file_size:,} - immediate legs {fixed:,} = residual {resid:,}; "
                        f"counted legs {counted:,} -> DEFICIT {resid - counted:,} (the finding)",
                  resid > 0 and resid - counted > 0))

    named = [r for r in recs if r and all(32 <= c < 127 for c in r)]
    gates.append(("G6", f"read-back: {len(named)}/{nb} base records at 0x95da10 carry printable "
                        f"names (first {named[0].decode() if named else '-'!r})",
                  len(named) == len(recs) and len(recs) == nb))

    lines = [f"M108 counted legs — pid {pid}, {SAV}",
             f"  [0x985af0] units={nu}   52n={s52:,}  48p={s48:,}",
             f"  [0x985af4] bases={nb}   304m={s304:,}",
             f"  [0x92a38c]={src_u}  [0x92ae14]=0x{src_b:x}  [0x985dbc]={gate}",
             f"  immediate legs {fixed:,}  residual {resid:,}  counted {counted:,}  "
             f"deficit {resid - counted:,}",
             "  store sites 0x985af0: " + ", ".join(f"0x{p:x}({t.split()[1] if ' ' in t else t})"
                                                  for p, t in su),
             "  store sites 0x985af4: " + ", ".join(f"0x{p:x}" for p, _ in sb),
             "  base names: " + ", ".join(r.decode() for r in named[:8]),
             ""]
    lines += [f"  [{g}] {'PASS' if ok else 'FAIL'}  {msg}" for g, msg, ok in gates]
    npass = sum(1 for _, _, ok in gates if ok)
    verdict = f"VERDICT {'PASS' if npass == len(gates) else 'FAIL'} {npass}/{len(gates)}"
    lines.append("  " + verdict)
    text = "\n".join(lines)
    print(text)
    if a.tag:
        os.makedirs(os.path.join(ROOT, "evidence"), exist_ok=True)
        with open(os.path.join(ROOT, "evidence", f"{a.tag}.log"), "w") as f:
            f.write(text + "\n")
    return 0 if npass == len(gates) else 1


if __name__ == "__main__":
    sys.exit(main())
