#!/usr/bin/env python3
"""M379 mutation harness - every VERIFIED row names the mutant that reddens it.

Each mutant rewrites ONE instruction line of the disassembly text (the
instrument's only input for logic) or flips an algorithm law, and must make
`scripts/m379_field594.py` exit 1 with a FAIL line under the named gate.

    python3 scripts/m379_mutate.py
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "m379_field594.py")

# (id, env patch, gate that must fail, what it kills)
MUTANTS = [
    ("MU1", "0x5a1171|mov    edi,0x9280b0", "G3", "seed pointer 0x9280b8"),
    ("MU2", "0x5a1213|cmp    ebx,0x9", "G3", "bound 8 -> 9: 8 bodies, store span past the end"),
    ("MU3", "0x5a116a|mov    ebx,0x0", "G3", "start 1 -> 0: 8 bodies"),
    ("MU4", "0x5a11c5|dec    ebx", "G3", "step inc -> dec (the loop law)"),
    ("MU5", "0x5a120d|add    edi,0x5a0", "G3", "record stride 0x59c"),
    ("MU6", "0x5a1216|jg     0x5a1178", "G3", "the post-increment jl"),
    ("MU7", "0x5a1eac|mov    eax,DWORD PTR [eax+0x927b1c]", "G2", "reader A field displacement"),
    ("MU8", "0x54696c|mov    eax,DWORD PTR [edx+0x927b1c]", "G2", "reader B field displacement"),
    ("MU9", "0x5a1e62|shl    eax,0x4", "G1", "reader A stride chain"),
    ("MU10", "0x5468fc|shl    eax,0x4", "G1", "reader B stride chain"),
    ("MU11", "0x5a1ec8|shl    edx,0x3", "G1", "reader A weight-chain 0x82f"),
    ("MU12", "0x5a1eac|mov    DWORD PTR [eax+0x927b24],0x0", "G2", "reader A becomes a STORE"),
    ("MU13", "0x596ea4|push   0x2ce4", "G4", "save block size 0x2ce0 = 8*0x59c"),
    ("MU14", "0x596ea9|push   0x927594", "G4", "save block base 0x927590"),
    ("MU15", "0x6146c7|mov    ds:0x997c20,eax", "G2", "the 0x997b20 malloc array evidence"),
    ("MU16", "0x523e1a|cmp    esi,0x92a26c", "G4", "walk bound 0x92a270"),
    ("MU17", "0x5a1203|cmp    eax,0xc", "G2", "effect index bound 0xb = 11 keywords"),
    ("MU18", "0x5a1221|mov    eax,0x92a7fc", "G3", "'0x92a7fc never occurs as an immediate'"),
    ("MU19", "ALGO=1", "G3", "ALGORITHM: the interpreter's jl condition is inverted"),
    ("MU21", "ALGO=2", "G3", "ALGORITHM: the bound is treated as inclusive"),
    ("MU22", "0x5a1eac|add    DWORD PTR [eax+0x927b24],ecx", "G2", "an RMW store to the field"),
    ("MU20", "0x44947f|cmp    ebx,0x92a274", "G4", "second independent walk bound"),
]


def run(env_patch):
    env = dict(os.environ)
    env.pop("M379_PATCH", None)
    env.pop("M379_ALGO", None)
    if "=" in env_patch:
        k, v = env_patch.split("=", 1)
        env["M379_" + k] = v
    else:
        env["M379_PATCH"] = env_patch
    p = subprocess.run([sys.executable, "-u", SCRIPT], capture_output=True, text=True, env=env)
    return p.returncode, p.stdout


base_rc, base_out = run("")
m = re.search(r"PASS M379: (\d+)/\1", base_out)
base_ok = base_rc == 0 and bool(m)
print("baseline: rc=%d %s" % (base_rc, ("PASS %s gates" % m.group(1)) if base_ok else "UNEXPECTED"))
print("%-5s %-9s %-7s %s" % ("id", "expect", "killed", "mutant"))
print("-" * 100)

killed = 0
for mid, patch, gate, what in MUTANTS:
    rc, out = run(patch)
    red = rc != 0 and re.search(r"^\s+%s\s+FAIL" % gate, out, re.M) is not None
    killed += 1 if red else 0
    print("%-5s %-9s %-7s %s" % (mid, gate, "yes" if red else "NO", what))
    if not red:
        tail = "\n".join(out.strip().splitlines()[-4:])
        print("   !! not killed; rc=%d tail:\n%s" % (rc, tail))

print("-" * 100)
print("%s M379 harness: %d/%d killed%s" % (
    "PASS" if (base_ok and killed == len(MUTANTS)) else "FAIL",
    killed, len(MUTANTS), "" if base_ok else " (baseline broken)"))
sys.exit(0 if (base_ok and killed == len(MUTANTS)) else 1)
