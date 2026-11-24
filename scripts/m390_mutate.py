#!/usr/bin/env python3
"""M390 mutation harness - every VERIFIED row of scripts/m390_entry_noun.py names a mutant
here, and each mutant must REDDEN exactly the row(s) it names.

The base run must be green; each mutant is one env var, and the harness reports which
rows went red.  A mutant that leaves the row green is a DEAD mutant -> harness fails.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts/m390_entry_noun.py")
BASE = dict(os.environ)

# (id, env, rows that MUST go red, why it is a real mutation rather than a typo)
MUTANTS = [
    ("MU1", {"M390_PATCH": "4db0ce|call   0x4dabb0"},
     ["G2 zero direct `call` instructions reach 0x4dabb0"],
     "a real `call` to the target is injected (the called sibling 0x4dac30's site)"),
    ("MU2", {"M390_PATCH": "4dac17|je     0x4dabb0"},
     ["G2 zero `jmp`/`jcc` reach 0x4dabb0"],
     "a conditional jump into the target's entry is injected"),
    ("MU3", {"M390_ALGO": "9"},
     ["G3 zero occurrences of the 0x4dabb0 VA in the image",
      "G5 0x4dabb0 has zero of ALL FOUR mechanisms (calls/jumps/dwords/run)"],
     "the census is aimed at the live sibling 0x4dab90 (a stored VA must then be found)"),
    ("MU4", {"M390_ALGO": "1"},
     ["G3 CONTROL: the live sibling 0x4dab90 IS address-taken once, in .rdata"],
     "the byte census is restricted to .text, so the .rdata slot becomes invisible"),
    ("MU5", {"M390_ALGO": "2"},
     ["G1 the predecessor instruction is a `ret 4` (no fallthrough)",
      "R2 'code falls or jumps into the body: 0x4dabb0 is no entry at all' refuted"],
     "fallthrough is assumed through a `ret 4` boundary"),
    ("MU6", {"M390_ALGO": "3"},
     ["G0 image has NO DYNAMIC_BASE (never relocated)",
      "R3 'the relocations would fix up a pointer the byte search cannot see' refuted"],
     "the image is treated as rebasable, which would make the byte census incomplete"),
    ("MU7", {"M390_ALGO": "4"},
     ["R4 '0x4dabb0 is a COMDAT fold of the live sibling 0x4dac30' refuted"],
     "the body diff only looks at the 6-instruction prologue (which IS identical)"),
    ("MU8", {"M390_ALGO": "5"},
     ["G7 the branch tests the 4th arg [ebp+0x14]"],
     "the flag is read from arg3's slot [ebp+0x10] instead of arg4's"),
    ("MU9", {"M390_ALGO": "6"},
     ["G7 32 of 36 sites pass a literal bool; 4 pass a runtime register",
      "G7 M385's own gate corroborates: 0x4dad05 (bit CLEAR -> set) passes 1, "
      "0x4dad30 (bit SET -> clear) passes 0"],
     "the caller classifier takes the LAST push (arg1) instead of the 4th arg"),
    ("MU10", {"M390_ALGO": "7"},
     ["G7 noun = SET/CLEAR polarity, not 'arm the timer' (the 0x40 test is inside the SET side)"],
     "the SET/CLEAR polarity is flipped (the classifier's law), numbers unchanged"),
    ("MU11", {"M390_PATCH": "4dad00|push   0x0"},
     ["G7 32 of 36 sites pass a literal bool; 4 pass a runtime register",
      "G7 M385's own gate corroborates: 0x4dad05 (bit CLEAR -> set) passes 1, "
      "0x4dad30 (bit SET -> clear) passes 0"],
     "the real `push 0x1` at M385's set-site is rewritten to 0 in the dump"),
]

FAILS = 0


def run(env):
    e = dict(BASE)
    e.update(env)
    p = subprocess.run([sys.executable, "-u", SCRIPT], capture_output=True, text=True, env=e)
    red = [m.group(1).strip() for m in
           (re.match(r"^  FAIL (.*?)(?: - .*)?$", ln) for ln in p.stdout.splitlines()) if m]
    return p.returncode, red, p.stdout


print("M390 mutation harness - %d mutants" % len(MUTANTS))
rc, red, out = run({})
print("BASE  rc=%d  red=%d  %s" % (rc, len(red), [ln for ln in out.splitlines() if ln.startswith("PASS")]))
if rc != 0 or red:
    print("BASE RUN IS NOT GREEN - harness cannot judge mutants")
    sys.exit(1)

for mid, env, rows, why in MUTANTS:
    rc, red, _out = run(env)
    killed = [r for r in rows if any(r in x for x in red)]
    ok = rc != 0 and len(killed) == len(rows)
    print("%-5s %-6s rc=%d red=%d  %s" % (mid, "KILLED" if ok else "ALIVE", rc, len(red),
                                          " | ".join(r[:64] for r in red[:3])))
    print("      %s" % why)
    if not ok:
        FAILS += 1
print("\n%s M390 mutants: %d/%d killed" % ("PASS" if not FAILS else "FAIL",
                                           len(MUTANTS) - FAILS, len(MUTANTS)))
sys.exit(1 if FAILS else 0)
