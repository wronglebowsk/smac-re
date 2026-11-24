#!/usr/bin/env python3
"""M389 mutation harness - every VERIFIED row names the mutant that reddens it.

Each mutant rewrites one instruction line (M389_PATCH='addr|text') or flips one
algorithm law (M389_ALGO=n), re-runs the instrument, and requires (a) non-zero
exit and (b) the named failing check to appear among the FAIL lines.  A green
mutant is a hole in the claim it names.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "m389_family_mask.py")

MUTANTS = [
    ("MU1", "G1 every def is a `mov reg,imm`",
     {"M389_PATCH": "0x4daea3|mov    ebx,DWORD PTR [esi+0x8]"},
     "G1 every def is a `mov reg,imm`"),
    ("MU2", "G1 the resolved masks are {0x4,0x2,0x1000,0x2000}",
     {"M389_PATCH": "0x4db035|mov    edi,0x3000"}, "G1 the resolved masks are"),
    ("MU3", "G1 all four register masks resolve to a literal",
     {"M389_PATCH": "0x4dafcf|mov    edi,DWORD PTR [ebp+0x8]"},
     "G1 all four register masks resolve"),
    ("MU4", "G1 the four pushed masks are {0x20,0x2000000,0x400,0x40000}",
     {"M389_PATCH": "0x4db0aa|push   0x410"}, "G1 the four pushed masks are"),
    ("MU5", "G2 seven guarded arms",
     {"M389_PATCH": "0x4dae43|call   0x551a20"}, "G2 seven guarded arms"),
    ("MU6", "G2 the ladder is exactly the seven lows",
     {"M389_PATCH": "0x4daea3|mov    ebx,0x400"}, "G2 the ladder is"),
    ("MU7", "G2 no arm asks 0x400",
     {"M389_PATCH": "0x4daea3|mov    ebx,0x400"}, "G2 no arm asks 0x400"),
    ("MU8", "G2 every arm witnesses one SET and one CLEAR",
     {"M389_PATCH": "0x4dae13|call   0x5518f0"}, "G2 every arm witnesses"),
    ("MU9", "G2 the SET witness precedes the je target",
     {"M389_PATCH": "0x4dadf4|je     0x4daddf"},
     "G2 in every arm the SET witness precedes"),
    ("MU10", "G3 FUN_004dacc0 has two 0x551cf0 arms",
     {"M389_PATCH": "0x4dad05|call   0x551a20"},
     "G3 FUN_004dacc0 has two 0x551cf0 arms"),
    ("MU11", "G3 0x551cf0 reads a flag argument ([ebp+0x14])",
     {"M389_PATCH": "0x551cf3|mov    eax,DWORD PTR [ebp+0x18]"},
     "G3 0x551cf0 reads the flag from [ebp+0x14]"),
    ("MU12", "G4 the family pushes 0x400 exactly once",
     {"M389_PATCH": "0x4db0aa|push   0x800"},
     "G4 the family pushes 0x400 exactly once"),
    ("MU13", "G5 FUN_004dadd0 has exactly two direct callers",
     {"M389_PATCH": "0x4dab96|call   0x4dabb0"},
     "G5 FUN_004dadd0 has exactly two direct callers"),
    ("MU14", "G7 digest pins the verdict table",
     {"M389_PATCH": "0x4db035|mov    edi,0x3000"}, "G7 digest matches the pin"),
    ("MA1", "ALGO: calls clobber callee-saved ebx/edi (def tracer)",
     {"M389_ALGO": "1"}, "G1 all four register masks resolve"),
    ("MA2", "ALGO: SET/CLEAR regions swapped (direction classifier)",
     {"M389_ALGO": "2"}, "G2 in every arm the SET witness precedes"),
    ("MA3", "ALGO: 0x5518f0's NOT+AND unwitnessed (verb classifier)",
     {"M389_ALGO": "3"}, "G3 0x5518f0 loads the MASK into edx"),
    ("MA4", "ALGO: a 0x400 arm admitted (bit classifier)",
     {"M389_ALGO": "4"}, "R3 'the ladder can ask 0x400"),
    ("MA5", "ALGO: first `mov reg,imm` from function start (no dominance)",
     {"M389_ALGO": "5"}, "G1 the defs are"),
    ("MA6", "ALGO: the guard call ignored (arm builder)",
     {"M389_ALGO": "6"}, "G2 seven guarded arms"),
    ("MA7", "ALGO: a data reference read as a call (reachability census)",
     {"M389_ALGO": "7"}, "G5 FUN_004dab90 has no direct call site"),
    ("MU15", "G1 0x4dad30's mask operand IS edi",
     {"M389_PATCH": "0x4dad2d|push   esi"},
     "G1 at the CLEAR arm 0x4dad30 the mask operand IS edi"),
    ("MU16", "G2 exactly one push in the 3 insns before each guard",
     {"M389_PATCH": "0x4dadd5|nop"},
     "G2 exactly one push in the 3 insns before each guard call"),
    ("MU17", "G2 the fall-through block jmps PAST the CLEAR witness",
     {"M389_PATCH": "0x4dae18|jmp    0x4dae1a"},
     "G2 the fall-through block ends in a `jmp` past the CLEAR witness"),
    ("MU18", "G3 0x551a20 loads the MASK from [ebp+0x10]",
     {"M389_PATCH": "0x551a2a|mov    ebx,DWORD PTR [ebp+0x14]"},
     "G3 0x551a20 loads the MASK into ebx from [ebp+0x10]"),
    ("MU19", "G3 the je target separates the OR block from the AND block",
     {"M389_PATCH": "0x551cf8|je     0x551cfa"},
     "G3 flag!=0 falls through"),
    ("MU20", "G2 big arms: the 2nd push feeding 0x551cf0 is edi",
     {"M389_PATCH": "0x4db02a|push   ebx"},
     "G2 big arms: 4 pushes feed 0x551cf0"),
]


def run(env):
    e = dict(os.environ)
    e.pop("M389_PATCH", None)
    e.pop("M389_ALGO", None)
    e.update(env)
    p = subprocess.run([sys.executable, "-u", SCRIPT], capture_output=True, text=True, env=e)
    return p.returncode, p.stdout + p.stderr


print("M389 mutation harness: %d mutants" % len(MUTANTS))
bad = []
for mid, claim, env, expect in MUTANTS:
    rc, out = run(env)
    fails = [l for l in out.splitlines() if l.startswith("  FAIL ")]
    hit = any(expect in l for l in fails)
    ok = rc != 0 and hit
    print("  %-4s %-4s %-58s rc=%d %s" % (mid, "KILL" if ok else "LIVE", claim[:58], rc,
                                          env.get("M389_PATCH") or ("ALGO=" + env.get("M389_ALGO", ""))))
    if not ok:
        bad.append((mid, claim, fails[:3], rc))
print("\n%d/%d killed" % (len(MUTANTS) - len(bad), len(MUTANTS)))
if bad:
    print("FAIL M389 mutants survived:")
    for mid, claim, f, rc in bad:
        print("  %s %s rc=%d fails=%s" % (mid, claim, rc, f))
    sys.exit(1)
print("PASS M389 mutants: %d/%d" % (len(MUTANTS), len(MUTANTS)))
