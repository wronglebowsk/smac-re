#!/usr/bin/env python3
"""M359 mutation harness - every VERIFIED claim row names the mutant that reddens it.

Each mutant rewrites ONE instruction in a private copy of the objdump listing and
re-runs the acceptance on it.  A mutant is a NO-OP if its gate still passes.

    python3 -u scripts/m359_mutate.py            # -> evidence/m359_mutate.txt
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch", "m574", "text.txt")
SCRIPT = os.path.join(ROOT, "scripts", "m359_design_record.py")
OUT = os.path.join(ROOT, "scratch", "m359_mut")

# (id, gate prefix, address, old substring, new substring, what it breaks)
MUTANTS = [
    ("MU1", "G1", "40f420", "0x98adaf", "0x98adae", "a +0x27 load becomes +0x26 -> census 134"),
    ("MU2", "G2", "595cc3", "0x98adaf", "0x98adae", "builder stores +0x27 into +0x26 -> map"),
    ("MU3", "G3", "57a014", "push 0x1", "push 0x2", "loader's constant field becomes 2"),
    ("MU4", "G4", "579f9d", "mov esi,0x98adba", "mov esi,0x98adbb", "loader base shifts by 1"),
    ("MU5", "G5", "57a041", "[esi-0xa]", "[esi-0xb]", "loader Carry store moves to +0x2b"),
    ("MU6", "G6", "595cf8", ",0x7", ",0x8", "Transport Mode gate 7 -> 8"),
    ("MU7", "G7", "57087f", "imul eax,DWORD PTR [ebp+0x10]",
     "add eax,DWORD PTR [ebp+0x10]", "carry formula multiply -> add (algorithm mutant)"),
    ("MU8", "G8", "40f42d", "cmp eax,0x3", "cmp eax,0x4", "clamp ceiling 3 -> 4"),
    ("MU9", "G9", "40f441", "shl ecx,1", "shl ecx,2", "10*v -> 20*v in the HP-thirds chain"),
    ("MU10", "G10", "595d3a", ",0x5", ",0x6", "Planet-Buster plan override 5 -> 6"),
    ("MU11", "G11", "40f40e", ",0xc", ",0xb", "one plan==12 compare becomes 11"),
    ("MU12", "G5", "595d1c", "0x98adb0", "0x98adb1", "literal +0x28 writer disappears"),
    ("MU13", "G2", "595cb7", "[ebp+0x18]", "[ebp+0x14]",
     "ability arg re-pointed (arg-resolution algorithm mutant)"),
]


def run(text, gate_prefix):
    env = dict(os.environ, SMAC_M359_TEXT=text)
    p = subprocess.run([sys.executable, "-u", SCRIPT], env=env,
                       capture_output=True, text=True)
    lines = [l for l in p.stdout.splitlines() if l.startswith(("PASS", "FAIL"))]
    hit = [l for l in lines if l[5:].split()[0] == gate_prefix]
    passed = bool(hit) and all(l.startswith("PASS") for l in hit)
    return p.returncode, hit, lines


INS = __import__("re").compile(r"^\s*([0-9a-f]{6,8}):\t([0-9a-f ]+)\t(.*)$")


def norm(s):
    return __import__("re").sub(r"\s+", " ", s.strip())


def main():
    os.makedirs(OUT, exist_ok=True)
    src = []
    for line in open(TEXT, "r", errors="replace"):
        m = INS.match(line)
        if m:
            src.append((int(m.group(1), 16), norm(m.group(3))))


    rc, _hit, lines = run(TEXT, "")
    base = [l for l in lines if "gates" in l]
    print("baseline rc=%d  %s" % (rc, base[-1] if base else "?"))
    if rc != 0:
        print("BASELINE FAILS - nothing to mutate")
        return 1

    noop = []
    print("\n %-5s %-4s %-8s %-7s %-10s %s" % ("id", "gate", "addr", "verdict", "rc", "what breaks"))
    for mid, pref, addr, old, new, why in MUTANTS:
        patched = os.path.join(OUT, "%s.txt" % mid)
        hit_line = None
        out = []
        want = int(addr, 16)
        for a, t in src:
            if a == want and old in t:
                t = t.replace(old, new, 1)
                hit_line = t
            out.append("  %06x:\t00\t%s" % (a, t))
        if hit_line is None:
            print(" %-5s %-4s %-8s %-7s %-10s %s" % (mid, pref, addr, "NO-LINE", "-", why))
            noop.append(mid)
            continue
        open(patched, "w").write("\n".join(out) + "\n")
        rc, hit, _ = run(patched, pref)
        verdict = "RED" if (hit and all(l.startswith("FAIL") for l in hit)) else "NO-OP"
        if verdict == "NO-OP":
            noop.append(mid)
        print(" %-5s %-4s %-8s %-7s rc=%-7d %s" % (mid, pref, addr, verdict, rc, why))
        for l in hit:
            print("        %s" % l[:110])

    print("\n mutants %d, red %d, NO-OP %s"
          % (len(MUTANTS), len(MUTANTS) - len(noop), noop or "none"))
    return 1 if noop else 0


if __name__ == "__main__":
    raise SystemExit(main())
