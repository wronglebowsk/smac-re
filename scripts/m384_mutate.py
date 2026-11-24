#!/usr/bin/env python3
"""M384 mutation harness: every VERIFIED row of the M384 block must have a
mutant that turns the acceptance run red. Each mutant rewrites one instruction
(M384_PATCH) or flips one dataflow law (M384_ALGO); the harness asserts the
BASELINE is green and EVERY mutant is red, and prints the failing check name.

  python3 scripts/m384_mutate.py
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts/m384_bit400_writer.py")

# (id, env, expected substring of the failing check)
MUTANTS = [
    ("MU1",  {"M384_PATCH": "555a6b|or ah,0x8"},
     "G3 exactly 2 hardcoded 0x400 setters"),          # the 0x555a6e setter -> 0x800
    ("MU2",  {"M384_PATCH": "5534ae|or ch,0x8"},
     "G3 exactly 2 hardcoded 0x400 setters"),          # FUN_00553350 setter -> 0x800
    ("MU3",  {"M384_PATCH": "5534ae|or ch,0x40"},
     "G3 both OR exactly 0x400"),                      # right instruction, wrong bit
    ("MU4",  {"M384_PATCH": "41b2c8|push 0x800"},
     "G4 the five are"),                               # one API setter mask loses 0x400
    ("MU5",  {"M384_PATCH": "594cf0|push 0x20"},
     "G4 the five are"),                               # 0x420 -> 0x20
    ("MU6",  {"M384_PATCH": "4db11b|push 0x400"},
     "G4 the two clearers are"),                # a clearer becomes a third clearer
    ("MU7",  {"M384_PATCH": "551d1d|or edx,0x800"},
     "G3 exactly 3 parameterised OR writers"),         # the param OR becomes an imm OR
    ("MU8",  {"M384_PATCH": "555394|and DWORD PTR [edi+0x94d448],ecx"},
     "G1 every direct store is a whole-dword mov"),    # a field and-op a disp grep would see
    ("MU9",  {"M384_PATCH": "555a38|mov eax,DWORD PTR [ebx]"},
     "G3 the only OPAQUE pair writes"),                # setter loses its field provenance
    ("MU10", {"M384_PATCH": "55336d|lea eax,[ecx*4+0x94d44c]"},
     "G2 15 pointer stores"),                          # the pair pointer is gone
    ("MU11", {"M384_PATCH": "553374|mov DWORD PTR [ebp+0xc],eax"},
     "G2 15 pointer stores"),                          # the pair pointer lands in the wrong slot
    ("MU12", {"M384_PATCH": "555a50|test ah,0x4"},
     "G5 1. the pair test"),                           # gate test no longer names both bits
    ("MU13", {"M384_PATCH": "555a5b|je 0x555a5d"},
     "G5 3. bit 5 present"),                           # the 0x20 arm no longer jumps to the setter
    ("MU14", {"M384_ALGO": "15"},
     "G2 15 pointer stores"),                          # lea scale law: *4 is not the fold
    ("MU15", {"M384_ALGO": "16"},
     "G4 the five are"),                               # cdecl arg order flipped
    ("MU16", {"M384_ALGO": "10"},
     "G3 both OR exactly 0x400"),                      # high-byte shift law off
    ("MU17", {"M384_PATCH": "555a6e|or DWORD PTR [ebx+0x94d448],eax"},
     "G1 zero and/or/xor/add at the direct displacement"),  # an inline OR the census exists to catch
    ("MU18", {"M384_ALGO": "12"},
     "G2 15 pointer stores"),                          # tags kept across calls
    ("MU19", {"M384_PATCH": "555a6e|mov DWORD PTR [ebx+0x94d44c],eax"},
     "G3 42 pair writes"),                             # the setter's store leaves the field
    ("MU21", {"M384_PATCH": "551b11|or ebx,0x80000100"},
     "G4 FUN_00551a20 also ORs the fixed 0x80000108"),   # the API's fixed OR changes
    ("MU22", {"M384_PATCH": "551d1d|or edx,esi"},
     "G4 FUN_00551cf0 takes mask=arg2"),                 # the OR source is no longer arg2
    ("MU23", {"M384_PATCH": "519bae|push 0xc10"},
     "G4 the two clearers are"),                         # a clearer's mask changes
    ("MU20", {"M384_PATCH": "551b17|and edx,0xffffffff"},
     "G3 FUN_00551a20's clear arm ANDs 0xfaeef378"),  # the API no longer wipes 0x400 first
]


def run(env):
    e = dict(os.environ)
    e.pop("M384_PATCH", None)
    e.pop("M384_ALGO", None)
    e.update(env)
    p = subprocess.run([sys.executable, "-u", SCRIPT], capture_output=True, text=True, env=e)
    return p.returncode, p.stdout + p.stderr


def main():
    rc, out = run({})
    base_ok = rc == 0 and "PASS M384:" in out
    line = [l for l in out.splitlines() if l.startswith(("PASS", "FAIL"))][-1]
    print("baseline: rc=%d %s" % (rc, line))
    if not base_ok:
        print(out[-2000:])
        print("BASELINE RED — abort")
        return 1
    killed = 0
    for mid, env, expect in MUTANTS:
        rc, out = run(env)
        red = rc != 0 and "FAIL" in out
        named = expect in out
        status = "KILLED" if (red and named) else ("RED-but-other" if red else "SURVIVED")
        if red and named:
            killed += 1
        what = env.get("M384_PATCH") or ("ALGO=" + env.get("M384_ALGO", "?"))
        print("%-5s %-10s %-58s %s" % (mid, status, what, expect))
        if not red:
            print("      !! SURVIVED: " + env.__str__())
    print("\nM384 mutation: %d/%d killed, baseline green" % (killed, len(MUTANTS)))
    return 0 if killed == len(MUTANTS) else 1


if __name__ == "__main__":
    sys.exit(main())
