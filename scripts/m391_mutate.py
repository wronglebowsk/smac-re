#!/usr/bin/env python3
"""M391 mutation harness: every VERIFIED row names its mutant.

Baseline must be green, then each mutant must turn a NAMED gate red.  A mutant
that leaves the acceptance green is a defect in the gate, not a pass.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts/m391_blanket_clear.py")

MUTANTS = [
    ("MU1", {"M391_ALGO": "1"}, "G1.1", "the +0x94d468 sibling field counted as the pair"),
    ("MU2", {"M391_ALGO": "2"}, "G3.2", "cleared-bit test inverted (mask bit SET means cleared)"),
    ("MU3", {"M391_ALGO": "3"}, "G5.11", "the WAR arm's 0xfaeef378 clear dropped"),
    ("MU4", {"M391_ALGO": "4"}, "G2.2", "dominance gate skipped (no guard attributed)"),
    ("MU5", {"M391_ALGO": "5"}, "G4.4", "mask argument read at the wrong cdecl slot"),
    ("MU6", {"M391_PATCH": "0x551be6|or edx,edx"}, "G5.10", "the final mask restore neutralised"),
    ("MU7", {"M391_ALGO": "7"}, "G5.13", "apply_api ORs the mask before the ANDs"),
    ("MU8", {"M391_ALGO": "8"}, "G2.3", "third arm's gate read as test bl,0x7f"),
    ("MU9", {"M391_PATCH": "0x551b17|and edx,0xffffffff"}, "G3.2", "blanket row A neutralised"),
    ("MU10", {"M391_PATCH": "0x55538c|and ecx,0xffffffff"}, "G3.3", "the only bit-11-only bigger mask neutralised"),
    ("MU11", {"M391_PATCH": "0x551a35|test bl,0x0"}, "G2.1", "treaty-stage guard rewritten to 0x0"),
    ("MU12", {"M391_PATCH": "0x551a88|and edx,0xffffffff"}, "G1.2", "one of the 3 masks replaced by all-ones"),
]


def run(env_extra):
    env = dict(os.environ)
    env.update(env_extra)
    p = subprocess.run([sys.executable, "-u", SCRIPT], capture_output=True, text=True, env=env)
    return p.returncode, p.stdout + p.stderr


def main():
    print("M391 mutation harness - baseline then %d mutants" % len(MUTANTS))
    rc, out = run({})
    base = [l for l in out.splitlines() if l.startswith("PASS M391") or l.startswith("FAIL M391")]
    ok = rc == 0 and any(l.startswith("PASS M391") for l in base)
    print("  %-4s %-58s %s" % ("id", "mutation", "killed by"))
    print("  %-4s %-58s %s" % ("--", "baseline (no mutation)", "GREEN" if ok else "RED " + str(base)))
    rows = 0
    killed = 0
    if not ok:
        print("\nFAIL M391-mutate: baseline is not green")
        return 1
    for mid, env, gate, desc in MUTANTS:
        rc, out = run(env)
        red = [l for l in out.splitlines() if l.startswith("  FAIL ")]
        hit = any(("  FAIL " + gate + " ") in l or l.startswith("  FAIL " + gate + " ") for l in red)
        rows += 1
        if rc != 0 and hit:
            killed += 1
            print("  %-4s %-58s %s  (rc=%d, %d FAIL)" % (mid, desc, gate, rc, len(red)))
        else:
            print("  %-4s %-58s %s  SURVIVED (rc=%d) %s" % (mid, desc, gate, rc, red[:2]))
    print("\n%d/%d mutants killed" % (killed, rows))
    if killed != rows:
        print("FAIL M391-mutate: %d survivor(s)" % (rows - killed))
        return 1
    print("PASS M391-mutate: %d/%d killed, baseline green" % (killed, rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
