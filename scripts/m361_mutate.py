#!/usr/bin/env python3
"""M361 mutation harness — every VERIFIED claim row names the mutant that reddens it.

Two mutant families:
  * TEXT mutants rewrite ONE instruction line in a private copy of the objdump
    (or insert one synthetic line), then re-run the acceptance on it.
  * IMAGE mutants patch the dispatcher's jump table in a private copy of
    terran.exe (the only claim read straight out of the image).

A mutant is a NO-OP if its named gate still passes.

    python3 -u scripts/m361_mutate.py            # -> evidence/m361_mutate.txt
"""
import os
import re
import shutil
import struct
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
IMAGE = os.path.join(ROOT, "programs/terran.exe")
SCRIPT = os.path.join(ROOT, "scripts/m361_radio_flags.py")
OUT = os.path.join(ROOT, "scratch/m361_mut")
JT = 0x493FE0
IMAGE_BASE = 0x400000

# (id, gate, address, old substring, new substring, what it breaks)
MUTANTS = [
    ("MU1", "G1a", "493f9d", "[esi+0x136d4]", "[esi+0x136d8]", "one flag load loses its displacement -> census 15/15/12/12"),
    ("MU2", "G2c", "435538", "BYTE PTR [ecx+0x14220]", "DWORD PTR [ecx+0x14220]", "a loner byte store becomes a dword field -> not a different class"),
    ("MU5", "G4b", "493fd3", "call 0x5fa1e8", "call 0x5fa1e9", "one block's label setter call disappears"),
    ("MU6", "G4c", "493f7b", "[edx+0x10fc]", "[edx+0x10f8]", "one block reads a duplicate label id -> pair collapses"),
    ("MU7", "G5a", "493f8d", "lea ecx,[esi+0x14ea0]", "lea ecx,[esi+0x14ea4]", "one widget base shifts by 4 -> stride breaks"),
    ("MU8", "G4a", "493f5d", "[esi+0x158b8]", "[esi+0x158bc]", "flag-widget delta is no longer 0xa18"),
    ("MU9", "G5c", "491d9c", "lea ecx,[esi+0x14ea0]", "lea ecx,[esi+0x14ea1]", "one widget loses its vtable call (G5c lookback)"),
    ("MU11", "G7a", "492e02", "or ah,0x40", "or ah,0x20", "0x14d6c commits bit 0x2000 instead of 0x4000"),
    ("MU12", "G7d", "492d08", "mov ebx,0x400", "mov ebx,0x800", "def-use bit source of the 0x14220 commit (algorithm mutant)"),
    ("MU13", "G7a", "492e1b", "mov eax,DWORD PTR [esi+0x158b8]", "mov eax,DWORD PTR [esi+0x136d4]", "the master becomes a committed flag"),
    ("MU14", "G8a", "49217b", "DWORD PTR [esi+0x136d4],ebx", "DWORD PTR [esi+0x136d4],eax", "the aggregate's unconditional 0 becomes a 1"),
    ("MU15", "G8b", "492190", "cmp DWORD PTR [esi+0x14d6c],ebx", "cmp DWORD PTR [esi+0x14d60],ebx", "one 1-store loses its child guard"),
    ("MU16", "G9b", "49418d", "and ch,0xf3", "and ch,0xff", "master-off stops clearing bits 0x400|0x800"),
    ("MU17", "G9c", "494182", "mov ecx,DWORD PTR ds:0x985ab8", "mov ecx,DWORD PTR ds:0x985ab9", "the mask lands on a shifted global"),
    ("MU18", "G9d", "49404b", "DWORD PTR [esi+0x136d4],edi", "DWORD PTR [esi+0x136d8],edi", "one child stops propagating ON to the master"),
    ("MU21", "G10c", "5fa1f4", "cmp DWORD PTR [eax+0xa7c],0x0", "cmp DWORD PTR [eax+0xa78],0x0", "the setter touches a second field"),
    ("MU23", "G11e", "491cfc", "[edx+0x10f8]", "[edx+0x10f4]", "the ctor reads a duplicate label id"),
    ("MU24", "G12a", "49355f", "DWORD PTR [ebx+0x158b8],0x1", "DWORD PTR [ebx+0x158b9],0x1", "one seed store moves off the flag"),
    ("MU25", "G12b", "4934f9", "push 0x4d", "push 0x4c", "a seed store relabels the wrong widget"),
    ("MU26", "G3b", "493ecc", "cmp eax,0x3", "cmp eax,0x4", "the dispatcher's cmd guard widens to 5"),
    ("MU28", "G9e", "4941aa", "DWORD PTR [esi+0x136d4],edi", "DWORD PTR [esi+0x136d8],edi", "the master toggle stops writing the children"),
]

# image mutants: (id, gate, [4 dwords at 0x493fe0], what it breaks)
IMAGE_MUTANTS = [
    ("MU3", "G3a", [0x493F1C, 0x493F1C, 0x493EDC, 0x493F5D], "table entry 0 points at block 0x4c"),
    ("MU4", "G4a", [0x493EDC, 0x493F1C, 0x493F9D, 0x493F5D], "cmds 0x4b and 0x4d swap targets"),
]

# inserted synthetic instructions: (id, gate, after-address, text, what it breaks)
INSERT_MUTANTS = [
    ("MU10", "G6a", "494200", "test DWORD PTR [esi+0x14220],eax", "a fifth function reads a flag -> reader set grows"),
    ("MU19", "G10a", "494200", "call 0x5fa1e8", "an 11th setter caller in a fifth function"),
    ("MU20", "G10b", "5fa22a", "cmp DWORD PTR [esi+0x14220],0x0", "the setter becomes flag-aware"),
    ("MU22", "G11a", "50ab02", "mov eax,DWORD PTR [edx+0x10e0]", "a third function reads the label-id table"),
    ("MU27", "G2a", "4353b8", "mov BYTE PTR [ecx+0x14d6c],0x0", "a loner class gains a second flag -> family 8"),
    ("MU29", "G11a", "5fa22a", "cmp DWORD PTR [edx+0x10e4],0x0", "a cmp READ of the label-id table in a third function"),
    ("MU30", "G1b", "494200", "mov eax,DWORD PTR [ebp+0x136d4]", "a frame-relative form of a flag literal appears"),
]

INS = re.compile(r"^\s*([0-9a-f]{6,8}):\s+[0-9a-f ]+\t([a-z][a-z0-9]*)\s+(.*)$")


def norm(s):
    return re.sub(r"\s+", " ", s.strip())


def load_src():
    out = []
    for line in open(TEXT, "r", errors="replace"):
        m = INS.match(line)
        if m:
            out.append((int(m.group(1), 16), "%s %s" % (m.group(2), norm(m.group(3)))))
    return out


def write_listing(path, items):
    with open(path, "w") as f:
        for a, t in items:
            f.write("  %06x:\t00                    \t%s\n" % (a, t))


def run(env_extra, pref):
    env = dict(os.environ)
    env.pop("SMAC_M361_TEXT", None)
    env.pop("SMAC_M361_IMAGE", None)
    env.update(env_extra)
    p = subprocess.run([sys.executable, "-u", SCRIPT], env=env,
                       capture_output=True, text=True)
    gates = [l for l in p.stdout.splitlines() if l.startswith(("[PASS]", "[FAIL]"))]
    hit = [l for l in gates if l[7:].split()[0] == pref]
    return p.returncode, hit, [l for l in p.stdout.splitlines() if "gates" in l and "M361" in l]


def patch_image(path, dwords):
    shutil.copyfile(IMAGE, path)
    with open(path, "r+b") as f:
        for k, d in enumerate(dwords):
            f.seek(JT - IMAGE_BASE + k * 4)
            f.write(struct.pack("<I", d))


def main():
    os.makedirs(OUT, exist_ok=True)
    src = load_src()
    print("listing: %d instructions from %s" % (len(src), TEXT))

    rc, _hit, base = run({}, "G1")
    print("baseline rc=%d  %s" % (rc, base[-1] if base else "?"))
    if rc != 0:
        print("BASELINE FAILS - nothing to mutate")
        return 1

    noop = []
    total = 0
    print("\n %-5s %-4s %-10s %-7s %s" % ("id", "gate", "addr", "verdict", "what breaks"))
    for mid, pref, addr, old, new, why in MUTANTS:
        total += 1
        want, hit_line = int(addr, 16), None
        out = []
        for a, t in src:
            if a == want and old in t:
                t = t.replace(old, new, 1)
                hit_line = t
            out.append((a, t))
        if hit_line is None:
            noop.append(mid)
            print(" %-5s %-4s %-10s NO-LINE  %s" % (mid, pref, addr, why))
            continue
        path = os.path.join(OUT, "%s.txt" % mid)
        write_listing(path, out)
        rc, hit, _ = run({"SMAC_M361_TEXT": path}, pref)
        verdict = "RED" if any(l.startswith("[FAIL]") for l in hit) else "NO-OP"
        if verdict == "NO-OP":
            noop.append(mid)
        print(" %-5s %-4s %-10s %-7s %s" % (mid, pref, addr, verdict, why))
        for l in [x for x in hit if x.startswith("[FAIL]")][:2]:
            print("        %s" % l[:118])

    for mid, pref, dwords, why in IMAGE_MUTANTS:
        total += 1
        path = os.path.join(OUT, "%s.exe" % mid)
        patch_image(path, dwords)
        rc, hit, _ = run({"SMAC_M361_IMAGE": path}, pref)
        verdict = "RED" if any(l.startswith("[FAIL]") for l in hit) else "NO-OP"
        if verdict == "NO-OP":
            noop.append(mid)
        print(" %-5s %-4s %-10s %-7s %s" % (mid, pref, "image", verdict, why))
        for l in [x for x in hit if x.startswith("[FAIL]")][:2]:
            print("        %s" % l[:118])

    for mid, pref, addr, text, why in INSERT_MUTANTS:
        total += 1
        at = int(addr, 16)
        out = list(src)
        out.append((at, text))
        out.sort()
        path = os.path.join(OUT, "%s.txt" % mid)
        write_listing(path, out)
        rc, hit, _ = run({"SMAC_M361_TEXT": path}, pref)
        verdict = "RED" if any(l.startswith("[FAIL]") for l in hit) else "NO-OP"
        if verdict == "NO-OP":
            noop.append(mid)
        print(" %-5s %-4s %-10s %-7s %s" % (mid, pref, "+" + addr, verdict, why))
        for l in [x for x in hit if x.startswith("[FAIL]")][:2]:
            print("        %s" % l[:118])

    print("\n mutants %d, red %d, NO-OP %s" % (total, total - len(noop), noop or "none"))
    return 1 if noop else 0


if __name__ == "__main__":
    raise SystemExit(main())
