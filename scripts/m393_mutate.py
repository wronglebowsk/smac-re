#!/usr/bin/env python3
"""M393 mutation harness - every VERIFIED row of the acceptance names its mutant here.

Each case runs scripts/m393_pair2_writer.py with one lever and asserts that a NAMED
check (or set of checks) reddens, that the run prints FAIL, and that stdout differs
from the clean run.  A mutant that leaves the run green is a defect in the instrument,
not a pass.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(HERE, "scripts/m393_pair2_writer.py")

# (id, env, checks that MUST appear in the failure line)
CASES = [
    ("MU1", "field map shifted (+8 store -> +0x590)", {"M393_ALGO": "1"},
     ["G3 no folded store on cat2/choice2"]),
    ("MU2", "the block byte copy counts as a producer", {"M393_ALGO": "2"},
     ["G5 zero producers"]),
    ("MU3", "naive census only (no offset folding)", {"M393_ALGO": "3"},
     ["G3 control finds the first-pair writer"]),
    ("MU4", "the image carries static init bytes", {"M393_ALGO": "4"},
     ["G5 block is loader-zero (no static init)", "G7 RIVAL-2 fails"]),
    ("MU5", "the roll keeps no +1 (choice1 0..2)", {"M393_ALGO": "5"},
     ["G6 choice1 is 1..3"]),
    ("MU6", "the picker's zero-choice skip is dropped", {"M393_ALGO": "6"},
     ["G7 R2 cannot fire"]),
    ("MU7", "choice2 inherits pair1's 1..3 range", {"M393_ALGO": "7"},
     ["G7 R3 cannot fire"]),
    ("MU8", "a reader's cat2 becomes cat1",
     {"M393_PATCH": "5a1a88|mov    esi,DWORD PTR [eax+0x927b14]"},
     ["G6 eight references, 4 per field", "G6 every reference is a load/cmp"]),
    ("MU9", "the scorer's zero-cell guard is inverted",
     {"M393_PATCH": "522e47|jne    0x522e5f"},
     ["G6 scorer guard skips a zero grid cell"]),
    ("MU10", "the load transfer becomes the save transfer",
     {"M393_PATCH": "596ed6|call   0x64c9a0"},
     ["G5 only byte writer is the load transport"]),
    ("MU11", "the transfer is handed the pair, not the block",
     {"M393_PATCH": "596ec8|push   0x927b18"},
     ["G5 only byte writer is the load transport"]),
    ("MU12", "an anonymous store is aimed at cat2",
     {"M393_PATCH": "4dd996|mov    DWORD PTR [esi+0x927b18],eax"},
     ["G2 naive block stores == 2 at +0", "G3 no folded store on cat2/choice2"]),
    ("MU13", "the picker's zero-choice skip is nop'ed",
     {"M393_PATCH": "5a1dc1|nop"},
     ["G7 R2 cannot fire"]),
    ("MU14", "a reader's choice2 becomes choice1",
     {"M393_PATCH": "5a1a96|mov    edi,DWORD PTR [eax+0x927b1c]"},
     ["G6 eight references, 4 per field"]),
    ("MU15", "the block size push is wrong (4 slots)",
     {"M393_PATCH": "596ea4|push   0x1670"},
     ["G1 block size 8*stride"]),
]


def run(env_extra):
    env = dict(os.environ)
    env.pop("M393_ALGO", None)
    env.pop("M393_PATCH", None)
    env.update(env_extra)
    p = subprocess.run([sys.executable, "-u", SCRIPT], capture_output=True, text=True, env=env)
    return p.returncode, p.stdout


base_rc, base_out = run({})
print("clean run rc=%d  %s" % (base_rc, base_out.strip().splitlines()[-1]))
assert base_rc == 0, "clean run must be green"

killed = 0
for mu, name, env, must in CASES:
    rc, out = run(env)
    last = out.strip().splitlines()[-1] if out.strip() else "<no output>"
    named = [m for m in must if m in last]
    red = rc != 0 and last.startswith("FAIL")
    same = out == base_out
    ok = red and len(named) == len(must) and not same
    print("%-4s %-48s rc=%d red=%-5s named=%d/%d same=%s  %s" %
          (mu, name, rc, red, len(named), len(must), same, "KILLED" if ok else "SURVIVED"))
    if not ok:
        print("    last: %s" % last)
        for m in must:
            if m not in last:
                print("    missing named check: %s" % m)
    killed += ok

print("")
print("M393 MUTANTS: %d/%d killed" % (killed, len(CASES)))
sys.exit(0 if killed == len(CASES) else 1)
