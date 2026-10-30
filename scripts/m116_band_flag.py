#!/usr/bin/env python3
"""M116 — the M89 second-ask gate: is bit 0x40 of [f*8380+0x94d430] ever SET?

NAMED.md has carried "bit 0x40 = 0 for all 8 factions at r66 -> the M89 second-ask never ran" as an INFERRED/OPEN
row. This milestone tests both halves of that sentence:

  static  the gate is a BYTE test — `test BYTE PTR [esi+0x94d430],0x40` inside FUN_005aadf0 (+0x18f) — and NO
          instruction in the image ORs 0x40 into that byte/dword (the 17 `or` sites set 0x200000..0x80000000 and
          0x2), so the bit can only arrive through a whole-dword store.
  live    the eight faction words, and which of them carry 0x40 right now.

    python3 scripts/m116_band_flag.py            # static + live
    python3 scripts/m116_band_flag.py --static   # static only (no box)

PASS requires: exactly one 0x40 byte test at that displacement, ZERO 0x40-setting ORs, and eight words read. It
does NOT require the bit to be zero anywhere — the point of the milestone is to stop assuming that.
"""
import argparse
import csv
import os
import re
import struct
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
INDEX = os.path.join(ROOT, "ghidra_out/index.csv")
DISP = "0x94d430"
STRIDE = 8380          # NAMED writes f*8380: that is DECIMAL 8,380 = 0x20BC, not hex 0x8380 (M117 caught this)
BASE = 0x94D430
GATE_PC = 0x5AAF7F


def instructions():
    for line in open(TEXT, errors="replace"):
        m = re.match(r"\s*([0-9a-f]{6,8}):\s", line)
        if not m:
            continue
        p = line.rstrip("\n").split("\t")
        yield int(m.group(1), 16), (p[2].strip() if len(p) > 2 else "")


def containing(addr):
    rows = [r for r in csv.DictReader(open(INDEX))]
    fn = sorted((int(r["addr"], 16), int(r["size_bytes"]), r["name"]) for r in rows)
    lo, hi = 0, len(fn) - 1
    best = None
    for a, s, n in fn:
        if a <= addr < a + s:
            best = "%s+0x%x (size %d)" % (n, addr - a, s)
    return best or "(no containment)"


def static_facts():
    touching, ors, byte40 = [], [], []
    for a, asm in instructions():
        low = asm.lower()
        if DISP not in low:
            continue
        touching.append((a, asm))
        if low.startswith("or "):
            imm = re.search(r",\s*(0x[0-9a-f]+)\s*$", low)
            ors.append((a, asm, int(imm.group(1), 16) if imm else None))
        if re.search(r"test\s+byte ptr \[[^\]]*%s\],0x40\b" % DISP, low):
            byte40.append((a, asm))
    return touching, ors, byte40


def live_flags():
    try:
        pid = int(subprocess.check_output(["pgrep", "-x", "terran.exe"], text=True).split()[0])
    except Exception:
        return None, None
    fd = os.open("/proc/%d/mem" % pid, os.O_RDONLY)
    try:
        vals = [struct.unpack("<I", os.pread(fd, 4, BASE + f * STRIDE))[0] for f in range(8)]
    finally:
        os.close(fd)
    return pid, vals


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--static", action="store_true")
    a = ap.parse_args()

    touching, ors, byte40 = static_facts()
    lines = ["M116 band-flag gate — [f*0x8380+0x94d430] bit 0x40",
             "  stride %d (0x%x) per faction — NAMED's 'f*8380' is DECIMAL" % (STRIDE, STRIDE),
             "  instructions touching %s: %d   (reads+tests+stores)" % (DISP, len(touching)),
             "  OR sites: %d — immediates %s" % (len(ors), ", ".join("0x%x" % i for _, _, i in ors if i is not None))]
    or40 = [s for s in ors if s[2] is not None and (s[2] & 0x40)]
    lines.append("  OR sites that set 0x40: %d%s" % (len(or40), "" if not or40 else "  <-- CONTRADICTS the claim"))
    lines.append("  BYTE tests of 0x40 at that displacement: %d" % len(byte40))
    for pc, asm in byte40:
        lines.append("    0x%x  %s   in %s" % (pc, asm, containing(pc)))

    ok = True
    if len(byte40) != 1 or byte40[0][0] != GATE_PC:
        ok = False
        lines.append("  FAIL: expected exactly one such test at 0x%x" % GATE_PC)
    if or40:
        ok = False

    if not a.static:
        pid, vals = live_flags()
        if not vals:
            ok = False
            lines.append("  FAIL: no live terran.exe — the live half did not run")
        else:
            lines.append("  live words (pid %d): %s" % (pid, " ".join("0x%08x" % v for v in vals)))
            bits = [(v & 0x40) != 0 for v in vals]
            lines.append("  bit 0x40 set: %s  -> %d of 8 factions" % ("".join("Y" if b else "." for b in bits), sum(bits)))
            if sum(bits) == 0:
                lines.append("  (matches NAMED's 'bit 0x40 = 0 for all 8')")
            else:
                who = ",".join(str(f) for f, b in enumerate(bits) if b)
                lines.append("  **CONTRADICTS NAMED's 'bit 0x40 = 0 for all 8 factions at r66'** — set for faction(s) "
                             "%s, so the bit is not globally zero. CAUTION: that faction's whole dword (and +4) is "
                             "0xffffffff, which is also the shape of a -1-filled/uninitialised record, so 'the gate "
                             "MEANS second-ask enabled' is an INFERENCE, not this measurement. Decide it with a "
                             "controlled poke: clear the bit and count hits at 0x5aaf88." % who)
    lines.append("  VERDICT " + ("PASS" if ok else "FAIL"))
    out = "\n".join(lines)
    print(out, flush=True)
    with open(os.path.join(ROOT, "evidence", "m116flag.log"), "w") as f:
        f.write(out + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
