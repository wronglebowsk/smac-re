#!/usr/bin/env python3
"""M363 mutation harness — every VERIFIED claim row names the mutant that reddens it.

Families:
  * TEXT mutants rewrite ONE instruction line in a private listing of the objdump
    (or insert one synthetic line), then re-run the acceptance on it.
  * IMAGE mutants patch the handler's jump table (0x4941ec) in a private copy of
    terran.exe — the only claim read straight out of the image.

A mutant is a NO-OP if its named gate still passes.

    python3 -u scripts/m363_mutate.py            # -> evidence/m363_mutate.txt
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
SCRIPT = os.path.join(ROOT, "scripts/m363_audio_callees.py")
OUT = os.path.join(ROOT, "scratch/m363_mut")
JT = 0x4941EC
IMAGE_BASE = 0x400000

# (id, gate, address, old substring, new substring, what it breaks)
MUTANTS = [
    ("MU1", "G2", "4b8808", "[ecx+0x14]", "ds:0x985ab8", "a body loses its this-relative load for a pref cell"),
    ("MU3", "G5", "494193", "ds:0x985ab8,ecx", "ds:0x985ab9,ecx", "a cell store lands one byte off -> census drops to 120"),
    ("MU4", "G6b", "49418d", "and ch,0xf3", "and ch,0xff", "master-off stops clearing bits 0x400|0x800"),
    ("MU5", "G6a", "494129", "DWORD PTR ds:0x985ab8,esi", "esi,DWORD PTR ds:0x985ab8", "a cell store becomes a load -> 2 loads + 4 stores"),
    ("MU6", "G7", "49405c", "call 0x4b8a60", "call 0x4b8a61", "one row start call disappears from the census"),
    ("MU8", "G8", "494057", "ecx,0x8a7920", "ecx,0x8a7924", "the `this` passed to one audio call shifts by 4"),
    ("MU9", "G9b", "4b8ad9", "PTR [ecx+eax*1+0x24],0x1", "PTR [ecx+eax*1+0x24],0x0", "start and stop both write flag 0"),
    ("MU10", "G9", "4b8a6c", "[ebp+0x8],0xf", "[ebp+0x8],0xe", "the voice index bound narrows to 15 slots"),
    ("MU11", "G10", "4b8813", "[edx+0x60]", "[edx+0x61]", "one enable/disable thunk calls a shifted vtable slot"),
    ("MU13", "G13", "494020", "[esi+0x14d6c],ebx", "[esi+0x14d6c],edi", "the stop arm pairs with a turn-ON row store"),
    ("MU18", "G9c", "4b8b29", "[ecx+eax*1+0x2c]", "[ecx+eax*1+0x30]", "one arm's slot lea moves off +0x2c -> the arms stop being symmetric"),
    ("MU19", "G13b", "49412f", "call 0x446490", "call 0x4b8a60", "the 0x4e row becomes wired to the audio object"),
]

# inserted synthetic instructions: (id, gate, address-free slot, text, what it breaks)
INSERT_MUTANTS = [
    ("MU2", "G4", "4b9462", "mov eax,ds:0x985abc", "a closure leaf gains an absolute pref-cell load"),
    ("MU7", "G7", "4469a3", "call 0x4b87f0", "a ninth caller of 0x4b87f0 appears outside the handler"),
    ("MU12", "G11", "4b9332", "call DWORD PTR ds:0x9b0e30", "a closure member gains an import-form call"),
    ("MU16", "G1", "4b87f4", "int3", "a target extent gains one instruction -> count != index"),
    ("MU17", "G3", "4b9463", "call 0x4b8b80", "a closure leaf gains a callee -> the closure is no longer the measured 8"),
]

# image mutants: (id, gate, [4 dwords at 0x4941ec], what it breaks)
IMAGE_MUTANTS = [
    ("MU14", "G13", [0x494154, 0x4940C3, 0x49400E, 0x494068], "cmds 0x4c and 0x4e swap case blocks"),
    ("MU15", "G12", [0x494154, 0x494068, 0x49400E, 0x49400E], "cmd 0x4e falls into the 0x4d block"),
    ("MU21", "G12", [0x494154, 0x49400E, 0x494068, 0x4940C3], "cmds 0x4c and 0x4d swap (the middle two entries)"),
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
    env.pop("SMAC_M363_TEXT", None)
    env.pop("SMAC_M363_IMAGE", None)
    env.update(env_extra)
    p = subprocess.run([sys.executable, "-u", SCRIPT], env=env, capture_output=True, text=True)
    gates = [l for l in p.stdout.splitlines() if l.startswith(("[PASS]", "[FAIL]"))]
    hit = [l for l in gates if l[7:].split()[0] == pref]
    return p.returncode, hit, [l for l in p.stdout.splitlines() if "gates" in l and "M363" in l]


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
        rc, hit, _ = run({"SMAC_M363_TEXT": path}, pref)
        verdict = "RED" if any(l.startswith("[FAIL]") for l in hit) else "NO-OP"
        if verdict == "NO-OP":
            noop.append(mid)
        print(" %-5s %-4s %-10s %-7s %s" % (mid, pref, addr, verdict, why))
        for l in [x for x in hit if x.startswith("[FAIL]")][:1]:
            print("        %s" % l[:118])

    for mid, pref, after, text, why in INSERT_MUTANTS:
        total += 1
        want = int(after, 16)
        out = list(src)
        idx = None
        for k, (a, _t) in enumerate(out):
            if a > want:
                idx = k
                break
        out.insert(idx if idx is not None else len(out), (want, text))
        path = os.path.join(OUT, "%s.txt" % mid)
        write_listing(path, out)
        rc, hit, _ = run({"SMAC_M363_TEXT": path}, pref)
        verdict = "RED" if any(l.startswith("[FAIL]") for l in hit) else "NO-OP"
        if verdict == "NO-OP":
            noop.append(mid)
        print(" %-5s %-4s +%s       %-7s %s" % (mid, pref, after, verdict, why))
        for l in [x for x in hit if x.startswith("[FAIL]")][:1]:
            print("        %s" % l[:118])

    for mid, pref, dwords, why in IMAGE_MUTANTS:
        total += 1
        path = os.path.join(OUT, "%s.exe" % mid)
        patch_image(path, dwords)
        rc, hit, _ = run({"SMAC_M363_IMAGE": path}, pref)
        verdict = "RED" if any(l.startswith("[FAIL]") for l in hit) else "NO-OP"
        if verdict == "NO-OP":
            noop.append(mid)
        print(" %-5s %-4s jumptable  %-7s %s" % (mid, pref, verdict, why))
        for l in [x for x in hit if x.startswith("[FAIL]")][:1]:
            print("        %s" % l[:118])

    print("\nRUN %s  %d mutants, NO-OP %s" % ("PASS" if not noop else "FAIL", total, noop))
    return 0 if not noop else 1


if __name__ == "__main__":
    sys.exit(main())
