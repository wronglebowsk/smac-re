#!/usr/bin/env python3
"""M386 mutation harness - every VERIFIED row of scripts/m386_marker_pair.py names its mutant.

Each mutant rewrites ONE instruction line in the parsed dump (env M386_PATCH) or flips an
algorithm law (M386_ALGO), re-runs the acceptance instrument, and requires BOTH a non-zero exit
and the named gate in the FAIL line.  A mutant that leaves the run green is SURVIVED and fails
this harness.

    python3 scripts/m386_mutate.py            # run all
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(ROOT, "scripts", "m386_marker_pair.py")

MUTANTS = [
    ("MU1", "0x55fce0 clear-sentinel: X=-1 -> 0",
     "0x55fce0|mov    DWORD PTR [eax+0x94d820],0x0", "G2"),
    ("MU2", "0x558e12 unit-Y store retargeted to the wrong dword",
     "0x558e12|mov    DWORD PTR [ecx+0x94d81c],eax", "G1"),
    ("MU3", "0x557d43 tile stride x5 -> x3",
     "0x557d43|lea    edx,[ecx+ecx*2]", "G3"),
    ("MU4", "0x55531d guard base 131*esi -> 66*esi",
     "0x55531d|lea    ebx,[esi+edx*1]", "G4"),
    ("MU5", "0x557cf6 X load -> RMW add",
     "0x557cf6|add    eax,DWORD PTR [ebx+0x94d820]", "G1"),
    ("MU6", "0x557d0b `test eax,eax` -> compare against the turn counter",
     "0x557d0b|cmp    eax,DWORD PTR ds:0x985afc", "G5"),
    ("MU7", "0x5553e7 treaty AND no longer clears 0x20000",
     "0x5553e7|and    edx,0xfffffbff", "G7"),
    ("MU8", "ALGO1: guard base read as a faction id (stride 4)",
     None, "G4"),
    ("MU9", "0x4e3501 callee bounds-check Y -> X bound",
     "0x4e3501|cmp    edi,DWORD PTR ds:0x92a378", "G3"),
    ("MU10", "0x558dfe unit-X load -> +0x95da14",
     "0x558dfe|movsx  edx,WORD PTR [eax+0x95da14]", "G2"),
    ("MU11", "0x5a5786 sentinel -1 -> -2 on the clear pair",
     "0x5a5786|or     esi,0xfffffffe", "G2"),
    ("MU12", "0x557a5f base-relative load -> absolute ds form",
     "0x557a5f|mov    ecx,DWORD PTR ds:0x94d820", "G6"),
    ("MU13", "0x5552ff -> a REAL 0x20000 reader on the relations dword",
     "0x5552ff|test   DWORD PTR [edi+0x94d448],0x20000", "G7"),
    ("MU14", "0x557cf6 base register dropped -> [0x94d820] absolute bracket",
     "0x557cf6|mov    eax,DWORD PTR [0x94d820]", "G6"),
    ("MU15", "0x558e0c stores the Y register into X (operand swap)",
     "0x558e0c|mov    DWORD PTR [ecx+0x94d820],eax", "G2"),
]


def run(patch=None, algo="0"):
    env = dict(os.environ)
    env["M386_ALGO"] = algo
    if patch:
        env["M386_PATCH"] = patch
    p = subprocess.run([sys.executable, "-u", TOOL], capture_output=True, text=True, env=env)
    return p.returncode, p.stdout + p.stderr


def main():
    print("M386 mutation harness - %d mutants against scripts/m386_marker_pair.py" % len(MUTANTS))
    print("%-5s %-62s %-4s %-4s %s" % ("id", "mutation", "rc", "want", "verdict"))
    bad = []
    for mid, desc, patch, want in MUTANTS:
        algo = "1" if mid == "MU8" else "0"
        rc, out = run(patch, algo)
        red = re.findall(r'^FAIL (G\d)', out, re.M)
        base = re.search(r'^FAIL M386: .*red: (.*)$', out, re.M)
        ok = rc != 0 and want in red
        print("%-5s %-62s %-4d %-4s %s%s"
              % (mid, desc[:62], rc, want, "KILLED" if ok else "SURVIVED",
                 "" if ok else "  red=%s" % (sorted(set(red)) or base.group(1) if base else "none")))
        if not ok:
            bad.append(mid)
    print("")
    if bad:
        print("FAIL m386_mutate: %d/%d killed, survivors %s" % (len(MUTANTS) - len(bad), len(MUTANTS), bad))
        return 1
    print("PASS m386_mutate: %d/%d killed" % (len(MUTANTS), len(MUTANTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
