#!/usr/bin/env python3
"""M118 — is the M89 second-ask gate SATISFIABLE at all? bit 0x40 of [f*8380+0x94d430], four independent checks.

M116/M117 showed the byte test at 0x5aaf7f is reached 17x a round and never taken, with bit 0x40 clear for all eight
factions. That is a statement about ONE state. This milestone asks the construction question instead, and it can be
answered without the game running:

  A  exactly one `test BYTE PTR [..+0x94d430],0x40` exists in the image (0x5aaf7f, FUN_005aadf0+0x18f)
  B  no `or` whose immediate is 0x40 writes the dword at that displacement (the 17 dword ORs set high bits only)
  C  the ONE low-byte `or al,0x40` that reaches a flag store (0x4dc226) writes a DERIVED copy: the store at 0x4dc296
     takes eax reloaded from the flag and masked with 0xfc3fffff, so the or'd bit never reaches the source; the
     derived value goes to ds:0x99aa38 and no instruction moves ds:0x99aa38 back into a +0x94d430 slot
  D  the bit is clear for all 8 factions in every save on disk (12 files) — block A is restored 1:1 (M114), so a save
     with the bit set would set it

PASS = A+B+C+D. Anything else means the bit is reachable and the "inert" reading is wrong.

    python3 scripts/m118_flag_never_set.py
"""
import argparse
import glob
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
DISP = "0x94d430"
STRIDE = 8380          # DECIMAL: NAMED's "f*8380" is 8,380 bytes = 0x20BC, not hex 0x8380
BLOCK_A_FILE = 800     # block A starts at file offset 800 and is restored to dest 0x94d430
GATE_PC = 0x5AAF7F
OR40_PC = 0x4DC226
STORE_PC = 0x4DC296
DERIVED = "0x99aa38"


def instructions():
    for line in open(TEXT, errors="replace"):
        m = re.match(r"\s*([0-9a-f]{6,8}):\s", line)
        if not m:
            continue
        p = line.rstrip("\n").split("\t")
        yield int(m.group(1), 16), (p[2].strip() if len(p) > 2 else "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--saves", default=None)
    a = ap.parse_args()

    ins = list(instructions())
    idx = {pc: i for i, (pc, _) in enumerate(ins)}
    low = lambda s: s.lower()
    ok = True
    lines = ["M118 — is bit 0x40 of [f*%d+%s] satisfiable?" % (STRIDE, DISP), ""]

    # A — the gate
    tests = [(pc, s) for pc, s in ins
             if re.search(r"test\s+byte ptr \[[^\]]*%s\],0x40\b" % DISP, low(s))]
    lines.append("A  byte tests of 0x40 at the displacement: %d  (%s)" %
                 (len(tests), ", ".join("0x%x" % pc for pc, _ in tests) or "none"))
    if len(tests) != 1 or tests[0][0] != GATE_PC:
        ok = False
        lines.append("   FAIL: expected exactly one at 0x%x" % GATE_PC)

    # B — dword ORs
    ors = []
    for pc, s in ins:
        if DISP not in low(s) or not low(s).startswith("or "):
            continue
        m = re.search(r",\s*(0x[0-9a-f]+)\s*$", low(s))
        ors.append((pc, int(m.group(1), 16) if m else None, s))
    bad = [o for o in ors if o[1] is not None and (o[1] & 0x40)]
    lines.append("B  dword OR sites: %d, of which set 0x40: %d" % (len(ors), len(bad)))
    if bad:
        ok = False
        lines.append("   FAIL: %s" % [(hex(p), hex(i)) for p, i, _ in bad])

    # C — the only low-byte or al,0x40 that reaches a flag store
    lows = [(pc, s) for pc, s in ins if re.match(r"or\s+al,0x40$", low(s).strip())]
    reaching = []
    for pc, s in lows:
        i = idx[pc]
        window = ins[i:i + 40]
        if any(re.search(r"mov\s+dword ptr \[[^\]]*%s\],eax" % DISP, low(t)) for _, t in window):
            reaching.append(pc)
    lines.append("C  low-byte `or al,0x40` sites: %d; of those reaching a flag store: %s" %
                 (len(lows), ", ".join("0x%x" % p for p in reaching) or "none"))
    if reaching != [OR40_PC]:
        ok = False
        lines.append("   FAIL: expected exactly 0x%x" % OR40_PC)
    # the store's value: eax reloaded from the flag and masked before the store
    i = idx[STORE_PC]
    pre = [t for _, t in ins[max(0, i - 4):i]]
    masked = any(re.search(r"and\s+eax,0xfc3fffff", low(t)) for t in pre)
    reloaded = any(re.search(r"mov\s+eax,dword ptr \[[^\]]*%s\]" % DISP, low(t)) for t in pre)
    lines.append("   store 0x%x: eax reloaded from the flag = %s, masked 0xfc3fffff = %s" % (STORE_PC, reloaded, masked))
    if not (masked and reloaded):
        ok = False
        lines.append("   FAIL: the derived value may reach the source")
    back = [(pc, s) for pc, s in ins
            if DERIVED in low(s) and DISP in low(s) and "mov" in low(s)]
    lines.append("   instructions moving %s back into a +%s slot: %d" % (DERIVED, DISP, len(back)))
    if back:
        ok = False
        lines.append("   FAIL: %s" % [(hex(p), s[:40]) for p, s in back])

    # D — every save on disk
    saves = sorted(glob.glob(os.path.join(ROOT, "programs/saves/*.SAV"))) + \
        sorted(glob.glob(os.path.join(ROOT, "programs/saves/auto/*.SAV")))
    if a.saves:
        saves = glob.glob(a.saves)
    lines.append("D  saves checked: %d" % len(saves))
    setany = []
    for f in saves:
        b = open(f, "rb").read()
        for fac in range(8):
            off = BLOCK_A_FILE + fac * STRIDE
            if off + 4 > len(b):
                continue
            if struct.unpack("<I", b[off:off + 4])[0] & 0x40:
                setany.append((os.path.basename(f), fac))
    lines.append("   (file, faction) with bit 0x40 SET: %s" % (setany or "none"))
    if setany:
        ok = False
        lines.append("   FAIL: a save carries the bit — the gate is satisfiable from data")

    verdict = ("PASS — bit 0x40 has no setter in the image and no save carries it: the M89 second ask is inert BY "
               "CONSTRUCTION on this build and this save version, not merely on the state M117 measured"
               if ok else "FAIL — the gate IS satisfiable somewhere above; the 'inert' reading does not hold")
    lines.append("VERDICT " + verdict)
    out = "\n".join(lines)
    print(out, flush=True)
    with open(os.path.join(ROOT, "evidence", "m118flag.log"), "w") as fh:
        fh.write(out + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
