#!/usr/bin/env python3
"""M388 mutation harness - every VERIFIED row names the mutant that reddens it.

Each case rewrites ONE instruction line of the disassembly (M388_PATCH) or flips the
instrument's algorithm (M388_ALGO) and requires a non-zero exit AND the named gate to
appear in the FAIL list.  A mutant that leaves the gate green is itself a defect.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts/m388_agenda_slot0.py")

CASES = [
    # (id, env, gate substring that must appear)
    ("MU1", {"M388_PATCH": "0x5a1171|mov    edi,0x9286b8"}, "G1 seed imm"),
    ("MU2", {"M388_PATCH": "0x5a120d|add    edi,0x5a0"}, "G1 stride"),
    ("MU3", {"M388_ALGO": "1"}, "G1 loop starts at 1"),                     # ALGORITHM: walk starts at slot 0
    ("MU4", {"M388_PATCH": "0x5a1213|cmp    ebx,0x9"}, "G1 7 records walked"),
    ("MU5", {"M388_PATCH": "0x5a116a|mov    ebx,0x2"}, "G1 loop starts at 1"),
    ("MU6", {"M388_PATCH": "0x5a119d|mov    ecx,0x4"}, "G4 choice modulus is 3"),
    ("MU7", {"M388_PATCH": "0x5a11a6|dec    edx"}, "G4 choice is b+1"),
    ("MU8", {"M388_PATCH": "0x4b2715|mov    DWORD PTR [eax+ecx*4+0x927b14],edx"}, "G3 commit never writes the block"),
    ("MU9", {"M388_PATCH": "0x4b26ba|imul   eax,eax,0x59c"}, "G3 grid stride"),
    ("MU10", {"M388_PATCH": "0x4b2715|mov    DWORD PTR [eax+ecx*4+0x94d650],edx"}, "G3 commit store base is the grid"),
    ("MU11", {"M388_PATCH": "0x5bee99|mov    DWORD PTR [ecx+0x927590],0x0"}, "G2 (b) block stores are the 2 rec+0 stores"),
    ("MU12", {"M388_PATCH": "0x579e9c|mov    esi,0x927b2c"}, "G2 (d) the only slot0 seed is skip-guarded"),
    ("MU13", {"M388_ALGO": "2"}, "G2 (a) none of them sits in a record context"),  # ALGORITHM: ctor stores count
    ("MU14", {"M388_PATCH": "0x596ea4|push   0x2ce1"}, "G1 block size imm"),
    ("MU15", {"M388_PATCH": "0x5a11d1|mov    DWORD PTR [edi-0x4],esi"}, "G1 slot0 pair = 0x927b14/0x927b1c"),
]

bad = 0
print("%-5s %-4s %-52s %s" % ("id", "rc", "gate that must redden", "verdict"))
for cid, env, gate in CASES:
    e = dict(os.environ)
    e.update(env)
    p = subprocess.run([sys.executable, "-u", SCRIPT], capture_output=True, text=True, env=e, timeout=900)
    red = gate in p.stdout
    ok = p.returncode != 0 and red
    if not ok:
        bad += 1
    print("%-5s %-4d %-52s %s" % (cid, p.returncode, gate, "KILLED" if ok else "SURVIVED"))

print()
print("HARNESS %d/%d killed" % (len(CASES) - bad, len(CASES)))
sys.exit(1 if bad else 0)
