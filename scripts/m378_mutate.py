#!/usr/bin/env python3
"""m378_mutate.py - mutation harness for M378.  Each mutant rewrites one instruction of
the parsed dump and must redden at least the gates it names; the identity run must redden
none.  `want` is a gate subset: a mutant may redden MORE (a real state change), never fewer.

    python3 scripts/m378_mutate.py            # run all
    M378_TEXT=... python3 scripts/m378_mutate.py
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "m378_bit_nouns.py")

MUTANTS = [
    ("MU1", {"M378_PATCH": "5553ed|or     edx,0x800"}, {"G1"},
     "arm A's OR loses 0x40: the set algebra no longer reads 0x840"),
    ("MU2", {"M378_PATCH": "5553e7|and    edx,0xfffdf7ff"}, {"G1"},
     "arm A's AND spares 0x400: the clear algebra is no longer 0x20400"),
    ("MU3", {"M378_PATCH": "5553f3|mov    DWORD PTR [edi+0x94d468],edx"}, {"G0"},
     "arm A's store re-pointed at the sibling field"),
    ("MU4", {"M378_PATCH": "555405|or     eax,0x400"}, {"G2"},
     "arm B sets 0x400 instead of 0x20000"),
    ("MU5", {"M378_PATCH": "5553ac|jl     0x555405"}, {"G2"},
     "the guard's direction inverted: the arm would be the < 0 leg"),
    ("MU6", {"M378_PATCH": "55538c|and    ecx,0xfffff3ff"}, {"G3"},
     "the PACT path spares 0x20000 (clears only 0xc00)"),
    ("MU7", {"M378_PATCH": "555371|test   al,0x2"}, {"G3"},
     "the PACT path gated on bit 1 instead of bit 0"),
    ("MU8", {"M378_PATCH": "5552ff|test   ah,0x8"}, {"G4"},
     "the 0x400 reader re-pointed one bit up"),
    ("MU9", {"M378_PATCH": "552ce4|or     al,0x8"}, {"G5"},
     "FUN_00552970's arm sets 0x8: its 0x40 signature disappears"),
    ("MU10", {"M378_PATCH": "552cbc|mov    DWORD PTR [ebx+0x94d448],edx"}, {"G5"},
     "the sibling 0xc00 clear re-pointed at the relations dword"),
    ("MU11", {"M378_PATCH": "4ec9c3|test   DWORD PTR [edx*4+0x94d448],0x10"}, {"G4"},
     "one of the five 0x400-carrying sites reduced to 0x10: the count and the rival move"),
    ("MU13", {"M378_PATCH": "4ec9c3|test   DWORD PTR [edx*4+0x94d448],0x20c30"}, {"G6"},
     "a 0x20000 bit smuggled into a test mask: the zero-reader negative reddens"),
    ("MU12", {"M378_PATCH": "5553f9|mov    DWORD PTR [edi+0x94d448],0x32"}, {"G1"},
     "the lease store redirected into the relations dword itself"),
    ("MU14", {"M378_PATCH": "5553f9|mov    DWORD PTR [edi+0x94d4c8],0x33"}, {"G1"},
     "the lease value moved 0x32 -> 0x33: G1 now reads the immediate, not just the address"),
    ("MU15", {"M378_PATCH": "555371|test   cl,0x1"}, {"G3"},
     "the PACT gate moved to another register: the `test al,0x1` shape reddens"),
    ("MU16", {"M378_PATCH": "5553a4|mov    ecx,DWORD PTR [ebx+0x94d824]"}, {"G2"},
     "the guard's source field shifted: the provenance chain reddens"),
    ("NOOP", {}, set(), "identity: nothing may redden"),
]


def run(env_extra):
    env = dict(os.environ)
    env.update(env_extra)
    p = subprocess.run([sys.executable, "-u", SCRIPT], capture_output=True, text=True, env=env)
    out = p.stdout
    m = re.search(r"^FAIL M378: .*?red: (.+)$", out, re.M)
    if m:
        red = {g.strip() for g in m.group(1).split(",")}
    elif "PASS M378:" in out:
        red = set()
    else:
        red = {"NOPARSE"}
    return red, p.returncode


def main():
    bad = 0
    for name, env, want, text in MUTANTS:
        red, rc = run(env)
        ok = (want <= red) if want else (red == set())
        if not ok:
            bad += 1
        print("%-5s %s  red=%-28s want=%-14s %s"
              % (name, "ok  " if ok else "FAIL", sorted(red), sorted(want), text))
    print("")
    print("%s %d mutants, %d unexpected" %
          ("RUN PASS" if bad == 0 else "RUN FAIL", len(MUTANTS), bad))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
